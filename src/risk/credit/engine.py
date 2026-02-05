"""
Credit rating engine with enhanced death spiral detection and modular assessment.

This module provides a sophisticated credit rating assessment system specifically
designed for climate risk analysis, including:
- Extended rating scale (AAA to D)
- Death spiral detection and modeling
- Counterfactual-based climate risk pricing
- Monte Carlo rating migration analysis
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Union
from enum import Enum
import numpy as np
import pandas as pd

from ..core import (
    RiskMetrics,
    PlantCharacteristics,
    ScenarioParameters,
    ValidationResult,
    calculate_probability_of_default,
    calculate_recovery_rate,
    calculate_credit_var,
    validate_financial_inputs,
    log_risk_assessment,
)


class Rating(Enum):
    """
    Extended credit rating scale for climate risk assessment.
    
    Investment Grade: AAA, AA, A, BBB
    Speculative Grade: BB, B
    Distressed/Default: CCC, CC, C, D
    
    This extended scale allows proper differentiation when entities have
    negative EBITDA or severe financial distress due to climate impacts.
    """
    AAA = 1   # Prime
    AA = 2    # High Grade
    A = 3     # Upper Medium Grade
    BBB = 4   # Lower Medium Grade (lowest investment grade)
    BB = 5    # Non-Investment Speculative
    B = 6     # Highly Speculative
    CCC = 7   # Substantial Risk
    CC = 8    # Very High Risk / Default imminent
    C = 9     # Near Default
    D = 10    # In Default

    def __str__(self) -> str:
        return self.name

    def to_spread_bps(self) -> float:
        """
        Convert rating to typical spread over risk-free rate (basis points).
        
        Based on historical corporate bond spreads and distressed debt trading levels.
        Enhanced for climate risk pricing with wider spreads for distressed ratings.
        """
        spread_map = {
            Rating.AAA: 50,
            Rating.AA: 100,
            Rating.A: 150,
            Rating.BBB: 250,
            Rating.BB: 400,
            Rating.B: 600,
            Rating.CCC: 900,    # Substantial risk
            Rating.CC: 1500,   # Very high risk - distressed debt
            Rating.C: 2500,    # Near default - deep distress
            Rating.D: 5000,    # Default - recovery value pricing
        }
        return spread_map[self]

    @property
    def numeric_score(self) -> int:
        """Numeric score for rating (1=best, 10=worst)."""
        return self.value

    @property
    def is_investment_grade(self) -> bool:
        """Check if rating is investment grade (BBB or better)."""
        return self.value <= 4

    @property
    def is_distressed(self) -> bool:
        """Check if rating indicates financial distress (CCC or worse)."""
        return self.value >= 7

    @property
    def category(self) -> str:
        """Get rating category description."""
        if self.value <= 4:
            return "Investment Grade"
        elif self.value <= 6:
            return "Speculative Grade"
        elif self.value <= 9:
            return "Distressed"
        else:
            return "Default"


@dataclass
class RatingMetrics:
    """
    Financial metrics used for credit rating assessment.
    
    Enhanced with climate-specific metrics and death spiral indicators.
    """
    # Core financial metrics
    capacity_mw: float
    ebitda_to_fixed_assets: float
    ebitda_to_interest: float
    net_debt_to_ebitda: float
    debt_to_equity: float
    debt_to_assets: float
    
    # Project finance metrics
    dscr: float = 1.0
    cfads_to_debt_service: float = 1.0  # Alternative coverage metric
    
    # Climate risk indicators
    climate_cost_ratio: float = 0.0  # Climate costs / EBITDA
    physical_risk_score: float = 0.0  # 0-1 scale
    transition_risk_score: float = 0.0  # 0-1 scale
    
    # Distress indicators
    is_ebitda_negative: bool = False
    consecutive_loss_years: int = 0
    trend_indicator: str = "stable"  # "improving", "stable", "deteriorating"


@dataclass
class RatingComponent:
    """Individual rating component with weight and rationale."""
    name: str
    rating: Rating
    weight: float
    rationale: str
    is_critical: bool = False  # Critical components can trigger distress overrides


@dataclass
class RatingAssessment:
    """
    Comprehensive credit rating assessment result.
    
    Includes detailed component breakdown, death spiral analysis,
    and climate risk impact assessment.
    """
    overall_rating: Rating
    components: List[RatingComponent]
    metrics: RatingMetrics
    assessment_date: str
    model_version: str
    
    # Death spiral analysis
    death_spiral_detected: bool = False
    spiral_drivers: List[str] = field(default_factory=list)
    projected_trajectory: List[Rating] = field(default_factory=list)
    
    # Climate risk impact
    climate_notch_deterioration: int = 0
    climate_spread_increase_bps: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to comprehensive dictionary for serialization."""
        return {
            "overall_rating": str(self.overall_rating),
            "rating_numeric": self.overall_rating.numeric_score,
            "spread_bps": self.overall_rating.to_spread_bps(),
            "category": self.overall_rating.category,
            "is_investment_grade": self.overall_rating.is_investment_grade,
            "is_distressed": self.overall_rating.is_distressed,
            "components": [
                {
                    "name": comp.name,
                    "rating": str(comp.rating),
                    "weight": comp.weight,
                    "rationale": comp.rationale,
                    "is_critical": comp.is_critical,
                }
                for comp in self.components
            ],
            "metrics": {
                "capacity_mw": self.metrics.capacity_mw,
                "ebitda_to_fixed_assets": self.metrics.ebitda_to_fixed_assets,
                "ebitda_to_interest": self.metrics.ebitda_to_interest,
                "dscr": self.metrics.dscr,
                "net_debt_to_ebitda": self.metrics.net_debt_to_ebitda,
                "debt_to_equity": self.metrics.debt_to_equity,
                "debt_to_assets": self.metrics.debt_to_assets,
                "climate_cost_ratio": self.metrics.climate_cost_ratio,
                "physical_risk_score": self.metrics.physical_risk_score,
                "transition_risk_score": self.metrics.transition_risk_score,
                "is_ebitda_negative": self.metrics.is_ebitda_negative,
                "consecutive_loss_years": self.metrics.consecutive_loss_years,
            },
            "death_spiral_analysis": {
                "detected": self.death_spiral_detected,
                "drivers": self.spiral_drivers,
                "projected_ratings": [str(r) for r in self.projected_trajectory],
            },
            "climate_impact": {
                "notch_deterioration": self.climate_notch_deterioration,
                "spread_increase_bps": self.climate_spread_increase_bps,
            },
            "assessment_date": self.assessment_date,
            "model_version": self.model_version,
        }


class DeathSpiralDetector:
    """Detects and analyzes death spiral scenarios in credit ratings."""
    
    def __init__(self):
        self.spiral_thresholds = {
            "dscr_decline_rate": 0.15,  # 15% annual DSCR decline
            "ebitda_decline_rate": 0.20,  # 20% annual EBITDA decline
            "leverage_increase_rate": 0.25,  # 25% annual leverage increase
            "rating_velocity": 2,  # Notches per year deterioration
        }
    
    def detect_death_spiral(
        self,
        current_metrics: RatingMetrics,
        historical_metrics: List[RatingMetrics],
        current_assessment: RatingAssessment,
    ) -> Tuple[bool, List[str], List[Rating]]:
        """
        Detect death spiral conditions based on metric trajectories.
        
        Args:
            current_metrics: Current financial metrics
            historical_metrics: Historical metrics for trend analysis
            current_assessment: Current rating assessment
            
        Returns:
            Tuple of (death_spiral_detected, drivers, projected_trajectory)
        """
        drivers = []
        trajectory = []
        
        if len(historical_metrics) < 2:
            return False, drivers, trajectory
        
        # Analyze trends
        recent_metrics = historical_metrics[-3:]  # Last 3 periods
        
        # DSCR deterioration
        dscr_trend = self._analyze_metric_trend([m.dscr for m in recent_metrics])
        if dscr_trend < -self.spiral_thresholds["dscr_decline_rate"]:
            drivers.append("Rapid DSCR deterioration")
        
        # EBITDA decline
        ebitda_trend = self._analyze_metric_trend([m.ebitda_to_fixed_assets for m in recent_metrics])
        if ebitda_trend < -self.spiral_thresholds["ebitda_decline_rate"]:
            drivers.append("Accelerating EBITDA decline")
        
        # Leverage increase
        leverage_trend = self._analyze_metric_trend([m.net_debt_to_ebitda for m in recent_metrics])
        if leverage_trend > self.spiral_thresholds["leverage_increase_rate"]:
            drivers.append("Rapid leverage increase")
        
        # Project rating trajectory
        if drivers:
            trajectory = self._project_rating_path(current_assessment.overall_rating, years=5)
        
        # Check for spiral conditions
        death_spiral_detected = (
            len(drivers) >= 2 and  # Multiple deteriorating trends
            current_assessment.overall_rating.value >= 6  # Already in speculative territory
        )
        
        return death_spiral_detected, drivers, trajectory
    
    def _analyze_metric_trend(self, values: List[float]) -> float:
        """Analyze trend in metric values (rate of change per period)."""
        if len(values) < 2:
            return 0.0
        
        # Simple linear trend estimation
        x = np.arange(len(values))
        y = np.array(values)
        
        # Calculate slope (trend rate)
        slope = np.polyfit(x, y, 1)[0]
        
        # Normalize by average value to get rate of change
        avg_value = np.mean(np.abs(y))
        return slope / avg_value if avg_value > 0 else 0.0
    
    def _project_rating_path(self, current_rating: Rating, years: int = 5) -> List[Rating]:
        """Project potential rating deterioration path."""
        trajectory = [current_rating]
        
        for year in range(1, years + 1):
            current_score = trajectory[-1].value
            
            # Deterioration rate increases in distress
            if current_score <= 6:  # Investment grade
                deterioration = 0.5  # 0.5 notches per year
            elif current_score <= 8:  # Speculative
                deterioration = 1.0  # 1 notch per year
            else:  # Distressed
                deterioration = 1.5  # 1.5 notches per year
            
            new_score = min(10, current_score + deterioration)
            trajectory.append(Rating(round(new_score)))
            
            # Stop if reach default
            if trajectory[-1] == Rating.D:
                break
        
        return trajectory


class RatingEngine:
    """
    Main credit rating engine with climate risk integration.
    
    Implements KIS (Korea Investors Service) methodology enhanced for
    climate risk assessment and death spiral detection.
    """
    
    def __init__(self):
        self.death_spiral_detector = DeathSpiralDetector()
        self.component_weights = self._get_component_weights()
    
    def assess_credit_rating(
        self,
        metrics: RatingMetrics,
        historical_metrics: Optional[List[RatingMetrics]] = None,
        scenario: Optional[ScenarioParameters] = None,
    ) -> RatingAssessment:
        """
        Perform comprehensive credit rating assessment.
        
        Args:
            metrics: Current financial metrics
            historical_metrics: Historical metrics for trend analysis
            scenario: Climate risk scenario
            
        Returns:
            Comprehensive rating assessment with death spiral analysis
        """
        # Calculate component ratings
        components = self._calculate_component_ratings(metrics)
        
        # Apply distress overrides if needed
        overall_rating = self._apply_distress_overrides(metrics, components)
        
        # Create assessment
        assessment = RatingAssessment(
            overall_rating=overall_rating,
            components=components,
            metrics=metrics,
            assessment_date=pd.Timestamp.now().strftime("%Y-%m-%d"),
            model_version="2.0.0",
        )
        
        # Death spiral analysis
        if historical_metrics:
            death_spiral, drivers, trajectory = self.death_spiral_detector.detect_death_spiral(
                metrics, historical_metrics, assessment
            )
            assessment.death_spiral_detected = death_spiral
            assessment.spiral_drivers = drivers
            assessment.projected_trajectory = trajectory
        
        # Climate impact analysis
        if scenario:
            assessment.climate_notch_deterioration = self._calculate_climate_impact_notches(
                metrics, scenario
            )
            # Calculate spread increase relative to baseline A rating
            baseline_spread = Rating.A.to_spread_bps()
            current_spread = assessment.overall_rating.to_spread_bps()
            assessment.climate_spread_increase_bps = max(0, current_spread - baseline_spread)
        
        return assessment
    
    def _get_component_weights(self) -> Dict[str, float]:
        """Get component weights for project finance credit assessment."""
        return {
            "capacity": 0.05,        # Business scale
            "profitability": 0.10,   # Operating efficiency
            "coverage": 0.15,        # Interest coverage
            "dscr": 0.35,           # PRIMARY: Debt service coverage
            "net_debt_leverage": 0.15,  # Leverage
            "equity_leverage": 0.10,   # Capital structure
            "asset_leverage": 0.10,    # Balance sheet strength
        }
    
    def _calculate_component_ratings(self, metrics: RatingMetrics) -> List[RatingComponent]:
        """Calculate individual component ratings."""
        components = []
        weights = self.component_weights
        
        # Capacity rating
        capacity_rating = self._rate_capacity(metrics.capacity_mw)
        components.append(RatingComponent(
            name="capacity",
            rating=capacity_rating,
            weight=weights["capacity"],
            rationale=f"Capacity: {metrics.capacity_mw:.0f} MW",
            is_critical=False,
        ))
        
        # Profitability rating
        profitability_rating = self._rate_profitability(
            metrics.ebitda_to_fixed_assets, metrics.is_ebitda_negative
        )
        components.append(RatingComponent(
            name="profitability",
            rating=profitability_rating,
            weight=weights["profitability"],
            rationale=(
                f"EBITDA/Fixed Assets: {metrics.ebitda_to_fixed_assets:.1f}%"
                f"{' (negative)' if metrics.is_ebitda_negative else ''}"
            ),
            is_critical=True,
        ))
        
        # Coverage rating
        coverage_rating = self._rate_coverage(metrics.ebitda_to_interest)
        components.append(RatingComponent(
            name="coverage",
            rating=coverage_rating,
            weight=weights["coverage"],
            rationale=f"EBITDA/Interest: {metrics.ebitda_to_interest:.1f}x",
            is_critical=True,
        ))
        
        # DSCR rating (most important for project finance)
        dscr_rating = self._rate_dscr(metrics.dscr)
        components.append(RatingComponent(
            name="dscr",
            rating=dscr_rating,
            weight=weights["dscr"],
            rationale=f"DSCR: {metrics.dscr:.2f}x",
            is_critical=True,
        ))
        
        # Leverage ratings
        net_debt_rating = self._rate_net_debt_leverage(
            metrics.net_debt_to_ebitda, metrics.is_ebitda_negative
        )
        components.append(RatingComponent(
            name="net_debt_leverage",
            rating=net_debt_rating,
            weight=weights["net_debt_leverage"],
            rationale=f"Net Debt/EBITDA: {metrics.net_debt_to_ebitda:.1f}x",
            is_critical=False,
        ))
        
        equity_rating = self._rate_equity_leverage(metrics.debt_to_equity)
        components.append(RatingComponent(
            name="equity_leverage",
            rating=equity_rating,
            weight=weights["equity_leverage"],
            rationale=f"Debt/Equity: {metrics.debt_to_equity:.0f}%",
            is_critical=False,
        ))
        
        asset_rating = self._rate_asset_leverage(metrics.debt_to_assets)
        components.append(RatingComponent(
            name="asset_leverage",
            rating=asset_rating,
            weight=weights["asset_leverage"],
            rationale=f"Debt/Assets: {metrics.debt_to_assets:.0f}%",
            is_critical=False,
        ))
        
        return components
    
    def _apply_distress_overrides(
        self,
        metrics: RatingMetrics,
        components: List[RatingComponent],
    ) -> Rating:
        """Apply distress overrides to ensure rating reflects critical metric deterioration."""
        # Calculate weighted average
        weighted_score = sum(comp.rating.value * comp.weight for comp in components)
        rounded_score = round(weighted_score)
        rounded_score = max(1, min(10, rounded_score))
        
        # Check for critical metric distress
        critical_components = [c for c in components if c.is_critical]
        distress_ratings = [c.rating for c in critical_components if c.rating.value >= 7]
        
        if distress_ratings:
            # At least one critical metric is distressed
            worst_distress = max(distress_ratings, key=lambda r: r.value)
            # Weighted score cannot be better than worst distressed critical metric
            rounded_score = max(rounded_score, worst_distress.value)
        
        # Additional distress check: if EBITDA is negative or very poor
        if metrics.is_ebitda_negative or metrics.ebitda_to_fixed_assets < -5:
            # Ensure rating reflects financial distress
            profitability_comp = next((c for c in components if c.name == "profitability"), None)
            if profitability_comp and profitability_comp.rating.value >= 6:
                rounded_score = max(rounded_score, 7)  # At least CCC
        
        return Rating(rounded_score)
    
    def _rate_capacity(self, capacity_mw: float) -> Rating:
        """Rate based on installed capacity."""
        if capacity_mw >= 2000:
            return Rating.AAA
        elif capacity_mw >= 800:
            return Rating.AA
        elif capacity_mw >= 400:
            return Rating.A
        elif capacity_mw >= 100:
            return Rating.BBB
        elif capacity_mw >= 20:
            return Rating.BB
        else:
            return Rating.B
    
    def _rate_profitability(self, ebitda_to_fixed_assets: float, is_negative: bool) -> Rating:
        """Rate based on EBITDA/Fixed Assets with negative EBITDA handling."""
        if is_negative:
            if ebitda_to_fixed_assets <= -20:
                return Rating.CC
            elif ebitda_to_fixed_assets <= -10:
                return Rating.CCC
            elif ebitda_to_fixed_assets < 0:
                return Rating.B
            else:
                return Rating.B
        elif ebitda_to_fixed_assets >= 15:
            return Rating.AAA
        elif ebitda_to_fixed_assets >= 11:
            return Rating.AA
        elif ebitda_to_fixed_assets >= 8:
            return Rating.A
        elif ebitda_to_fixed_assets >= 4:
            return Rating.BBB
        elif ebitda_to_fixed_assets >= 1:
            return Rating.BB
        else:
            return Rating.B
    
    def _rate_coverage(self, ebitda_to_interest: float) -> Rating:
        """Rate based on EBITDA/Interest coverage."""
        if ebitda_to_interest < -5:
            return Rating.D
        elif ebitda_to_interest < -2:
            return Rating.C
        elif ebitda_to_interest < 0:
            return Rating.CC
        elif ebitda_to_interest < 0.5:
            return Rating.CCC
        elif ebitda_to_interest >= 12:
            return Rating.AAA
        elif ebitda_to_interest >= 6:
            return Rating.AA
        elif ebitda_to_interest >= 4:
            return Rating.A
        elif ebitda_to_interest >= 2:
            return Rating.BBB
        elif ebitda_to_interest >= 1:
            return Rating.BB
        else:
            return Rating.B
    
    def _rate_dscr(self, dscr: float) -> Rating:
        """Rate based on Debt Service Coverage Ratio."""
        if dscr < 0:
            return Rating.D
        elif dscr < 0.5:
            return Rating.C
        elif dscr < 0.8:
            return Rating.CC
        elif dscr < 1.0:
            return Rating.CCC
        elif dscr >= 2.5:
            return Rating.AAA
        elif dscr >= 2.0:
            return Rating.AA
        elif dscr >= 1.6:
            return Rating.A
        elif dscr >= 1.3:
            return Rating.BBB
        elif dscr >= 1.1:
            return Rating.BB
        else:
            return Rating.B
    
    def _rate_net_debt_leverage(self, net_debt_to_ebitda: float, is_ebitda_negative: bool) -> Rating:
        """Rate based on Net Debt/EBITDA."""
        if is_ebitda_negative:
            return Rating.CC
        elif net_debt_to_ebitda < 0:
            return Rating.AAA
        elif net_debt_to_ebitda > 20:
            return Rating.CCC
        elif net_debt_to_ebitda <= 1:
            return Rating.AAA
        elif net_debt_to_ebitda <= 4:
            return Rating.AA
        elif net_debt_to_ebitda <= 7:
            return Rating.A
        elif net_debt_to_ebitda <= 10:
            return Rating.BBB
        elif net_debt_to_ebitda <= 12:
            return Rating.BB
        else:
            return Rating.B
    
    def _rate_equity_leverage(self, debt_to_equity: float) -> Rating:
        """Rate based on Debt-to-Equity Ratio."""
        if debt_to_equity <= 80:
            return Rating.AAA
        elif debt_to_equity <= 150:
            return Rating.AA
        elif debt_to_equity <= 250:
            return Rating.A
        elif debt_to_equity <= 300:
            return Rating.BBB
        elif debt_to_equity <= 400:
            return Rating.BB
        else:
            return Rating.B
    
    def _rate_asset_leverage(self, debt_to_assets: float) -> Rating:
        """Rate based on Debt-to-Assets Ratio."""
        if debt_to_assets <= 20:
            return Rating.AAA
        elif debt_to_assets <= 40:
            return Rating.AA
        elif debt_to_assets <= 60:
            return Rating.A
        elif debt_to_assets <= 80:
            return Rating.BBB
        elif debt_to_assets <= 90:
            return Rating.BB
        else:
            return Rating.B
    
    def _calculate_climate_impact_notches(self, metrics: RatingMetrics, scenario: ScenarioParameters) -> int:
        """Calculate climate-related rating deterioration."""
        base_notch = 3  # Assume A rating baseline
        
        # Climate cost impact
        if metrics.climate_cost_ratio > 0.5:  # Climate costs > 50% of EBITDA
            return 4  # 4-notch deterioration (A to BBB)
        elif metrics.climate_cost_ratio > 0.3:  # Climate costs > 30% of EBITDA
            return 3  # 3-notch deterioration (A to BB)
        elif metrics.climate_cost_ratio > 0.1:  # Climate costs > 10% of EBITDA
            return 2  # 2-notch deterioration (A to BBB)
        else:
            return 1  # 1-notch deterioration (A to A-)


# Global rating engine instance
_rating_engine = RatingEngine()


def get_rating_engine() -> RatingEngine:
    """Get the global rating engine instance."""
    return _rating_engine


def assess_credit_rating(
    metrics: RatingMetrics,
    historical_metrics: Optional[List[RatingMetrics]] = None,
    scenario: Optional[ScenarioParameters] = None,
) -> RatingAssessment:
    """
    Assess credit rating using the global rating engine.
    
    This is the main entry point for credit rating assessment with
    death spiral detection and climate risk integration.
    """
    assessment = _rating_engine.assess_credit_rating(metrics, historical_metrics, scenario)
    
    # Log assessment for audit trail
    log_risk_assessment(
        plant_id="unknown",  # Will be set by caller
        scenario_name=scenario.name if scenario else "baseline",
        baseline_rating=str(Rating.A),  # Counterfactual baseline
        risk_rating=str(assessment.overall_rating),
        crp_bps=assessment.climate_spread_increase_bps,
    )
    
    return assessment
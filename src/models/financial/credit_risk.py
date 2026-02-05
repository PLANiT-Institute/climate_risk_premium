"""
Credit Risk Translation Module.

Translates physical climate risk to credit risk metrics following:
- Moody's ESG methodology
- S&P Climate Risk framework
- NGFS credit risk guidance
- Basel Committee climate principles

Key relationships:
1. Physical damage → DSCR reduction → Default probability
2. Generation loss → Revenue → Interest coverage
3. Asset impairment → Collateral value → LGD
4. Climate exposure → Credit spread adjustment

Sources:
- Moody's (2021) "General Principles for Assessing ESG Risks"
- S&P (2022) "Climate Risk in Credit Ratings"
- NGFS (2022) "Climate-related litigation"
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import math


class CreditRating(Enum):
    """Credit rating scale."""
    AAA = "AAA"
    AA_PLUS = "AA+"
    AA = "AA"
    AA_MINUS = "AA-"
    A_PLUS = "A+"
    A = "A"
    A_MINUS = "A-"
    BBB_PLUS = "BBB+"
    BBB = "BBB"
    BBB_MINUS = "BBB-"
    BB_PLUS = "BB+"
    BB = "BB"
    BB_MINUS = "BB-"
    B_PLUS = "B+"
    B = "B"
    B_MINUS = "B-"
    CCC = "CCC"
    D = "D"


# Rating to numeric score mapping
RATING_SCORE = {
    CreditRating.AAA: 1,
    CreditRating.AA_PLUS: 2,
    CreditRating.AA: 3,
    CreditRating.AA_MINUS: 4,
    CreditRating.A_PLUS: 5,
    CreditRating.A: 6,
    CreditRating.A_MINUS: 7,
    CreditRating.BBB_PLUS: 8,
    CreditRating.BBB: 9,
    CreditRating.BBB_MINUS: 10,
    CreditRating.BB_PLUS: 11,
    CreditRating.BB: 12,
    CreditRating.BB_MINUS: 13,
    CreditRating.B_PLUS: 14,
    CreditRating.B: 15,
    CreditRating.B_MINUS: 16,
    CreditRating.CCC: 17,
    CreditRating.D: 18,
}

# Score back to rating
SCORE_RATING = {v: k for k, v in RATING_SCORE.items()}


@dataclass
class SpreadCurve:
    """
    Credit spread curve mapping ratings/DSCR to spreads.

    Based on market data and rating agency methodologies.
    """
    # Rating to spread (bps over risk-free)
    RATING_SPREADS = {
        CreditRating.AAA: 20,
        CreditRating.AA_PLUS: 35,
        CreditRating.AA: 50,
        CreditRating.AA_MINUS: 65,
        CreditRating.A_PLUS: 80,
        CreditRating.A: 100,
        CreditRating.A_MINUS: 120,
        CreditRating.BBB_PLUS: 150,
        CreditRating.BBB: 180,
        CreditRating.BBB_MINUS: 220,
        CreditRating.BB_PLUS: 300,
        CreditRating.BB: 400,
        CreditRating.BB_MINUS: 500,
        CreditRating.B_PLUS: 600,
        CreditRating.B: 750,
        CreditRating.B_MINUS: 900,
        CreditRating.CCC: 1200,
        CreditRating.D: 2000,
    }

    # DSCR to spread (for project finance)
    DSCR_SPREADS = {
        2.5: 50,
        2.0: 80,
        1.8: 100,
        1.5: 150,
        1.3: 220,
        1.2: 300,
        1.1: 450,
        1.0: 650,
        0.9: 900,
        0.8: 1200,
    }

    def get_spread_by_rating(self, rating: CreditRating) -> int:
        """Get spread for a rating."""
        return self.RATING_SPREADS.get(rating, 500)

    def get_spread_by_dscr(self, dscr: float) -> int:
        """Get spread for a DSCR level."""
        # Find closest DSCR
        sorted_dscrs = sorted(self.DSCR_SPREADS.keys(), reverse=True)
        for threshold in sorted_dscrs:
            if dscr >= threshold:
                return self.DSCR_SPREADS[threshold]
        return 1500  # Below all thresholds


@dataclass
class DSCRModel:
    """
    Debt Service Coverage Ratio model.

    Calculates DSCR impact from physical risk.
    """
    # Physical risk sensitivities
    CF_REDUCTION_TO_DSCR = -0.015      # -1.5% DSCR per 1% CF reduction
    ASSET_DAMAGE_TO_DSCR = -0.020      # -2% DSCR per 1% asset damage
    REVENUE_LOSS_TO_DSCR = -0.012      # -1.2% DSCR per 1% revenue loss

    def calculate_dscr_impact(
        self,
        baseline_dscr: float,
        cf_reduction_pct: float,
        asset_damage_pct: float = 0.0,
        revenue_loss_pct: float = 0.0,
    ) -> Tuple[float, float]:
        """
        Calculate DSCR impact from physical risk.

        Args:
            baseline_dscr: Current DSCR
            cf_reduction_pct: Capacity factor reduction (%)
            asset_damage_pct: Asset damage (%)
            revenue_loss_pct: Revenue loss (%)

        Returns:
            Tuple of (adjusted DSCR, DSCR change)
        """
        dscr_change = (
            cf_reduction_pct * self.CF_REDUCTION_TO_DSCR +
            asset_damage_pct * self.ASSET_DAMAGE_TO_DSCR +
            revenue_loss_pct * self.REVENUE_LOSS_TO_DSCR
        )

        adjusted_dscr = baseline_dscr * (1 + dscr_change)
        adjusted_dscr = max(0.5, adjusted_dscr)  # Floor at 0.5

        return adjusted_dscr, dscr_change


@dataclass
class CreditImpact:
    """
    Credit risk impact from physical climate risk.
    """
    asset_id: str
    scenario: str
    year: int

    # Baseline credit metrics
    baseline_rating: CreditRating
    baseline_dscr: float
    baseline_spread_bps: int

    # Physical risk inputs
    physical_risk_pct: float
    cf_reduction_pct: float
    asset_damage_pct: float = 0.0

    # Adjusted credit metrics
    adjusted_dscr: float = 0.0
    adjusted_rating: CreditRating = None
    adjusted_spread_bps: int = 0
    spread_widening_bps: int = 0

    # Probability impacts
    baseline_pd: float = 0.0           # Probability of default
    adjusted_pd: float = 0.0
    pd_increase_bps: float = 0.0

    # Rating impact
    rating_notches_change: int = 0

    # Financial impact
    additional_interest_cost_usd: float = 0.0
    debt_value_change_usd: float = 0.0

    def __post_init__(self):
        """Calculate derived values."""
        self.spread_widening_bps = self.adjusted_spread_bps - self.baseline_spread_bps
        if self.baseline_rating and self.adjusted_rating:
            self.rating_notches_change = (
                RATING_SCORE.get(self.adjusted_rating, 10) -
                RATING_SCORE.get(self.baseline_rating, 10)
            )


# Probability of default by rating (10-year cumulative)
RATING_PD_10Y = {
    CreditRating.AAA: 0.0007,    # 0.07%
    CreditRating.AA_PLUS: 0.0015,
    CreditRating.AA: 0.0030,
    CreditRating.AA_MINUS: 0.0050,
    CreditRating.A_PLUS: 0.0080,
    CreditRating.A: 0.0120,
    CreditRating.A_MINUS: 0.0180,
    CreditRating.BBB_PLUS: 0.0280,
    CreditRating.BBB: 0.0420,
    CreditRating.BBB_MINUS: 0.0650,
    CreditRating.BB_PLUS: 0.1000,
    CreditRating.BB: 0.1500,
    CreditRating.BB_MINUS: 0.2200,
    CreditRating.B_PLUS: 0.3000,
    CreditRating.B: 0.4000,
    CreditRating.B_MINUS: 0.5000,
    CreditRating.CCC: 0.6500,
    CreditRating.D: 1.0000,
}


class CreditRiskModel:
    """
    Credit risk translation model.

    Translates physical climate risk to credit metrics.
    """

    def __init__(self):
        self.spread_curve = SpreadCurve()
        self.dscr_model = DSCRModel()

    def calculate(
        self,
        asset_id: str,
        baseline_rating: CreditRating,
        baseline_dscr: float,
        total_debt_usd: float,
        annual_debt_service_usd: float,
        physical_risk_pct: float,
        cf_reduction_pct: float,
        asset_damage_pct: float = 0.0,
        scenario: str = "RCP8.5",
        year: int = 2050,
    ) -> CreditImpact:
        """
        Calculate credit impact from physical risk.

        Args:
            asset_id: Asset identifier
            baseline_rating: Current credit rating
            baseline_dscr: Current DSCR
            total_debt_usd: Outstanding debt
            annual_debt_service_usd: Annual P&I
            physical_risk_pct: Physical risk (%)
            cf_reduction_pct: Capacity factor reduction (%)
            asset_damage_pct: Asset damage (%)
            scenario: Climate scenario
            year: Target year

        Returns:
            CreditImpact with all credit metrics
        """
        # Calculate DSCR impact
        adjusted_dscr, dscr_change = self.dscr_model.calculate_dscr_impact(
            baseline_dscr=baseline_dscr,
            cf_reduction_pct=cf_reduction_pct,
            asset_damage_pct=asset_damage_pct,
        )

        # Determine rating impact
        # Rule: 10% DSCR reduction = 1 notch downgrade
        notches = int(abs(dscr_change) * 100 / 10)
        if dscr_change < 0:
            notches = min(notches, 5)  # Cap at 5 notches
        else:
            notches = 0

        baseline_score = RATING_SCORE.get(baseline_rating, 10)
        adjusted_score = min(17, baseline_score + notches)
        adjusted_rating = SCORE_RATING.get(adjusted_score, CreditRating.BB)

        # Get spreads
        baseline_spread = self.spread_curve.get_spread_by_rating(baseline_rating)
        adjusted_spread = self.spread_curve.get_spread_by_rating(adjusted_rating)

        # Also check DSCR-based spread
        dscr_spread = self.spread_curve.get_spread_by_dscr(adjusted_dscr)
        adjusted_spread = max(adjusted_spread, dscr_spread)

        # Calculate PD
        baseline_pd = RATING_PD_10Y.get(baseline_rating, 0.05)
        adjusted_pd = RATING_PD_10Y.get(adjusted_rating, 0.10)

        # Financial impact
        spread_widening = adjusted_spread - baseline_spread
        additional_interest = total_debt_usd * spread_widening / 10000  # bps to decimal

        # Debt value change (duration approximation)
        duration = 5.0  # Assume 5-year modified duration
        debt_value_change = -total_debt_usd * (spread_widening / 10000) * duration

        return CreditImpact(
            asset_id=asset_id,
            scenario=scenario,
            year=year,
            baseline_rating=baseline_rating,
            baseline_dscr=baseline_dscr,
            baseline_spread_bps=baseline_spread,
            physical_risk_pct=physical_risk_pct,
            cf_reduction_pct=cf_reduction_pct,
            asset_damage_pct=asset_damage_pct,
            adjusted_dscr=adjusted_dscr,
            adjusted_rating=adjusted_rating,
            adjusted_spread_bps=adjusted_spread,
            baseline_pd=baseline_pd,
            adjusted_pd=adjusted_pd,
            pd_increase_bps=(adjusted_pd - baseline_pd) * 10000,
            additional_interest_cost_usd=additional_interest,
            debt_value_change_usd=debt_value_change,
        )

    def calculate_portfolio(
        self,
        assets: List[Dict],
        scenario: str = "RCP8.5",
        year: int = 2050,
    ) -> Dict[str, CreditImpact]:
        """Calculate credit impact for portfolio."""
        results = {}
        for asset in assets:
            result = self.calculate(
                asset_id=asset["asset_id"],
                baseline_rating=asset.get("rating", CreditRating.AA),
                baseline_dscr=asset.get("dscr", 1.5),
                total_debt_usd=asset.get("debt_usd", 0),
                annual_debt_service_usd=asset.get("debt_service_usd", 0),
                physical_risk_pct=asset.get("physical_risk_pct", 2.0),
                cf_reduction_pct=asset.get("cf_reduction_pct", 2.0),
                scenario=scenario,
                year=year,
            )
            results[asset["asset_id"]] = result
        return results


def calculate_climate_credit_adjustment(
    physical_risk_pct: float,
    baseline_spread_bps: int = 100,
) -> Dict[str, float]:
    """
    Quick calculation of credit spread adjustment from physical risk.

    Rule of thumb from literature:
    - 1% physical risk ≈ 5-10 bps spread widening
    """
    # Conservative estimate: 7 bps per 1% physical risk
    spread_adjustment = physical_risk_pct * 7

    return {
        "physical_risk_pct": physical_risk_pct,
        "baseline_spread_bps": baseline_spread_bps,
        "spread_adjustment_bps": spread_adjustment,
        "adjusted_spread_bps": baseline_spread_bps + spread_adjustment,
        "relative_increase_pct": (spread_adjustment / baseline_spread_bps) * 100,
    }

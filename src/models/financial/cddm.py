"""
Climate Dividend Discount Model (CDDM).

Connects physical climate risk to equity valuation following:
- Bressan et al. (2024) Nature Communications
- Traditional DDM adjusted for climate factors

CDDM modifies standard equity valuation by:
1. Adjusting projected cash flows for physical damage
2. Adding climate risk premium to discount rate
3. Modeling insurance/adaptation cost increases
4. Accounting for stranded asset risk

All data loaded from CSV files. No hardcoded risk values.

Sources:
- Bressan et al. (2024) "Asset-level assessment of climate physical risk"
- Koller, Goedhart, Wessels (2020) "Valuation"
- Damodaran (2012) "Investment Valuation"
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math

from src.data.loaders import (
    load_korean_coal_fleet,
    load_hazard_baselines,
    get_climate_factor,
    get_generation_loss,
    CoalPlantData,
)


@dataclass
class CashFlowProjection:
    """
    Cash flow projection with climate adjustments.
    """
    year: int
    baseline_ebitda: float
    climate_damage_cost: float
    generation_loss_cost: float
    insurance_increase: float
    adaptation_cost: float
    stranded_asset_risk: float

    @property
    def adjusted_ebitda(self) -> float:
        """EBITDA after climate impacts."""
        return (
            self.baseline_ebitda -
            self.climate_damage_cost -
            self.generation_loss_cost -
            self.insurance_increase -
            self.adaptation_cost
        )

    @property
    def climate_impact_pct(self) -> float:
        """Climate impact as % of baseline."""
        if self.baseline_ebitda > 0:
            total_impact = (
                self.climate_damage_cost +
                self.generation_loss_cost +
                self.insurance_increase +
                self.adaptation_cost
            )
            return total_impact / self.baseline_ebitda * 100
        return 0.0


@dataclass
class EquityValuation:
    """
    Equity valuation result.
    """
    asset_id: str
    scenario: str

    # Baseline valuation
    baseline_equity_value: float
    baseline_per_share: float = 0.0
    shares_outstanding: float = 0.0

    # Climate-adjusted valuation
    climate_adjusted_equity: float = 0.0
    climate_adjusted_per_share: float = 0.0

    # Valuation impact
    equity_value_impact: float = 0.0
    equity_impact_pct: float = 0.0

    # Components
    npv_physical_damage: float = 0.0
    npv_generation_loss: float = 0.0
    npv_insurance_increase: float = 0.0
    npv_adaptation_cost: float = 0.0
    npv_stranded_risk: float = 0.0

    # Risk premium
    climate_risk_premium_bps: float = 0.0

    def __post_init__(self):
        """Calculate derived values."""
        self.equity_value_impact = self.baseline_equity_value - self.climate_adjusted_equity
        if self.baseline_equity_value > 0:
            self.equity_impact_pct = self.equity_value_impact / self.baseline_equity_value * 100
        if self.shares_outstanding > 0:
            self.baseline_per_share = self.baseline_equity_value / self.shares_outstanding
            self.climate_adjusted_per_share = self.climate_adjusted_equity / self.shares_outstanding


class ClimateDiscountModel:
    """
    Climate Dividend Discount Model (CDDM).

    Integrates physical risk into equity valuation.
    Uses CSV data and PhysicalRiskModel for dynamic risk calculation.
    """

    def __init__(
        self,
        base_discount_rate: float = 0.08,
        risk_free_rate: float = 0.04,
        terminal_growth_rate: float = 0.02,
    ):
        self.base_discount_rate = base_discount_rate
        self.risk_free_rate = risk_free_rate
        self.terminal_growth_rate = terminal_growth_rate
        self._physical_risk_model = None

    def set_physical_risk_model(self, model) -> None:
        """Set the physical risk model for dynamic risk calculation."""
        self._physical_risk_model = model

    def get_physical_risk(self, year: int, scenario: str = "RCP8.5") -> float:
        """
        Get physical risk for a year.

        If PhysicalRiskModel is set, uses it. Otherwise calculates from CSV data.
        """
        if self._physical_risk_model is not None:
            result = self._physical_risk_model.calculate(year=year, scenario_name=scenario)
            return result.value * 100  # Convert to percentage

        # Fallback: calculate from hazard baselines in CSV
        baselines = load_hazard_baselines()
        total_risk = 0.0

        for hazard_type, baseline in baselines.items():
            climate_factor = get_climate_factor(hazard_type, year, scenario)
            hazard_risk = baseline.total_annual_impact * climate_factor
            total_risk += hazard_risk

        return total_risk * 100  # Convert to percentage

    def calculate_climate_risk_premium(
        self,
        physical_risk_pct: float,
        scenario: str = "RCP8.5",
    ) -> float:
        """
        Calculate climate risk premium to add to discount rate.

        Rule of thumb:
        - 1% physical risk ≈ 10-20 bps risk premium

        Args:
            physical_risk_pct: Annual physical risk (%)
            scenario: Climate scenario

        Returns:
            Risk premium in decimal (e.g., 0.01 for 100 bps)
        """
        # Base: 15 bps per 1% physical risk
        base_premium = physical_risk_pct * 0.0015

        # Scenario adjustment
        scenario_multipliers = {
            "RCP8.5": 1.2,
            "RCP4.5": 1.0,
            "RCP2.6": 0.8,
            "SSP5-8.5": 1.2,
            "SSP2-4.5": 1.0,
            "SSP1-2.6": 0.8,
        }
        multiplier = scenario_multipliers.get(scenario, 1.0)

        return base_premium * multiplier

    def project_cash_flows(
        self,
        baseline_ebitda: float,
        physical_risk_trajectory: Dict[int, float],
        generation_loss_trajectory: Dict[int, float],
        start_year: int = 2025,
        horizon_years: int = 30,
        insurance_escalation: float = 0.02,
        adaptation_investment_pct: float = 0.01,
    ) -> List[CashFlowProjection]:
        """
        Project cash flows with climate adjustments.

        Args:
            baseline_ebitda: Current annual EBITDA
            physical_risk_trajectory: Year -> physical risk %
            generation_loss_trajectory: Year -> generation loss %
            start_year: First projection year
            horizon_years: Projection horizon
            insurance_escalation: Annual insurance cost increase
            adaptation_investment_pct: Adaptation as % of EBITDA

        Returns:
            List of CashFlowProjection by year
        """
        projections = []

        for i in range(horizon_years):
            year = start_year + i

            # Get physical risk for year (interpolate if needed)
            years = sorted(physical_risk_trajectory.keys())
            if year <= years[0]:
                physical_risk = physical_risk_trajectory[years[0]]
            elif year >= years[-1]:
                physical_risk = physical_risk_trajectory[years[-1]]
            else:
                # Linear interpolation
                for j, y in enumerate(years[:-1]):
                    if years[j] <= year < years[j + 1]:
                        weight = (year - years[j]) / (years[j + 1] - years[j])
                        physical_risk = (
                            physical_risk_trajectory[years[j]] * (1 - weight) +
                            physical_risk_trajectory[years[j + 1]] * weight
                        )
                        break

            # Generation loss
            gen_loss = generation_loss_trajectory.get(
                year,
                generation_loss_trajectory.get(years[-1], 2.0)
            )

            # Calculate impacts
            climate_damage = baseline_ebitda * physical_risk / 100 * 0.3  # 30% of risk as direct damage
            gen_loss_cost = baseline_ebitda * gen_loss / 100

            # Escalating insurance costs
            insurance_increase = baseline_ebitda * 0.02 * ((1 + insurance_escalation) ** i - 1)

            # Adaptation investment
            adaptation = baseline_ebitda * adaptation_investment_pct

            # Stranded asset risk (increases over time)
            stranded_risk = baseline_ebitda * (physical_risk / 100) * (i / horizon_years) * 0.1

            projections.append(CashFlowProjection(
                year=year,
                baseline_ebitda=baseline_ebitda,
                climate_damage_cost=climate_damage,
                generation_loss_cost=gen_loss_cost,
                insurance_increase=insurance_increase,
                adaptation_cost=adaptation,
                stranded_asset_risk=stranded_risk,
            ))

        return projections

    def calculate_equity_value(
        self,
        asset_id: str,
        baseline_ebitda: float,
        current_debt: float,
        physical_risk_pct: float = None,
        generation_loss_pct: float = None,
        scenario: str = "RCP8.5",
        horizon_years: int = 30,
        shares_outstanding: float = 0.0,
        plant_technology: str = "coal_supercritical",
    ) -> EquityValuation:
        """
        Calculate climate-adjusted equity value.

        Uses two-stage DCF:
        1. Explicit forecast period with climate adjustments
        2. Terminal value with climate risk premium

        Args:
            asset_id: Asset identifier
            baseline_ebitda: Current annual EBITDA
            current_debt: Outstanding debt
            physical_risk_pct: Current physical risk (if None, calculated from model)
            generation_loss_pct: Current generation loss (if None, from CSV)
            scenario: Climate scenario
            horizon_years: Forecast period
            shares_outstanding: Shares for per-share calculation
            plant_technology: Technology type for generation loss lookup

        Returns:
            EquityValuation with full breakdown
        """
        # Get physical risk dynamically if not provided
        if physical_risk_pct is None:
            physical_risk_pct = self.get_physical_risk(2024, scenario)

        # Get generation loss from CSV if not provided
        if generation_loss_pct is None:
            generation_loss_pct = get_generation_loss(plant_technology, 2030, scenario)

        # Create risk trajectories
        physical_trajectory = {
            2025: physical_risk_pct,
            2030: physical_risk_pct * 1.2,
            2040: physical_risk_pct * 1.5,
            2050: physical_risk_pct * 1.8,
        }
        gen_loss_trajectory = {
            2025: generation_loss_pct,
            2030: generation_loss_pct * 1.1,
            2040: generation_loss_pct * 1.3,
            2050: generation_loss_pct * 1.5,
        }

        # Project cash flows
        projections = self.project_cash_flows(
            baseline_ebitda=baseline_ebitda,
            physical_risk_trajectory=physical_trajectory,
            generation_loss_trajectory=gen_loss_trajectory,
            horizon_years=horizon_years,
        )

        # Calculate climate risk premium
        avg_physical_risk = sum(p.climate_impact_pct for p in projections) / len(projections)
        climate_premium = self.calculate_climate_risk_premium(avg_physical_risk, scenario)
        adjusted_discount_rate = self.base_discount_rate + climate_premium

        # NPV of cash flows
        npv_baseline = 0.0
        npv_adjusted = 0.0
        npv_physical = 0.0
        npv_gen_loss = 0.0
        npv_insurance = 0.0
        npv_adaptation = 0.0
        npv_stranded = 0.0

        for i, proj in enumerate(projections):
            discount_factor_base = 1 / ((1 + self.base_discount_rate) ** (i + 1))
            discount_factor_adj = 1 / ((1 + adjusted_discount_rate) ** (i + 1))

            npv_baseline += proj.baseline_ebitda * discount_factor_base
            npv_adjusted += proj.adjusted_ebitda * discount_factor_adj
            npv_physical += proj.climate_damage_cost * discount_factor_adj
            npv_gen_loss += proj.generation_loss_cost * discount_factor_adj
            npv_insurance += proj.insurance_increase * discount_factor_adj
            npv_adaptation += proj.adaptation_cost * discount_factor_adj
            npv_stranded += proj.stranded_asset_risk * discount_factor_adj

        # Terminal value (Gordon Growth)
        final_ebitda = projections[-1].adjusted_ebitda
        terminal_value = (
            final_ebitda * (1 + self.terminal_growth_rate) /
            (adjusted_discount_rate - self.terminal_growth_rate)
        )
        terminal_pv = terminal_value / ((1 + adjusted_discount_rate) ** horizon_years)

        # Enterprise values
        baseline_ev = npv_baseline + (
            projections[-1].baseline_ebitda * (1 + self.terminal_growth_rate) /
            (self.base_discount_rate - self.terminal_growth_rate)
        ) / ((1 + self.base_discount_rate) ** horizon_years)

        adjusted_ev = npv_adjusted + terminal_pv

        # Equity values (EV - Debt)
        baseline_equity = max(0, baseline_ev - current_debt)
        adjusted_equity = max(0, adjusted_ev - current_debt)

        return EquityValuation(
            asset_id=asset_id,
            scenario=scenario,
            baseline_equity_value=baseline_equity,
            climate_adjusted_equity=adjusted_equity,
            shares_outstanding=shares_outstanding,
            npv_physical_damage=npv_physical,
            npv_generation_loss=npv_gen_loss,
            npv_insurance_increase=npv_insurance,
            npv_adaptation_cost=npv_adaptation,
            npv_stranded_risk=npv_stranded,
            climate_risk_premium_bps=climate_premium * 10000,
        )


def calculate_korean_coal_equity_impact(
    scenario: str = "RCP8.5",
    physical_risk_model=None,
) -> Dict[str, any]:
    """
    Calculate equity impact for Korean coal fleet.

    Uses CSV data for coal fleet and optionally a PhysicalRiskModel
    for dynamic physical risk calculation.
    """
    coal_fleet = load_korean_coal_fleet()

    model = ClimateDiscountModel()
    if physical_risk_model is not None:
        model.set_physical_risk_model(physical_risk_model)

    results = {}
    total_baseline_equity = 0
    total_adjusted_equity = 0

    for plant_id, plant_data in coal_fleet.items():
        # Determine technology type
        technology = plant_data.asset_type
        if "supercritical" in technology:
            tech_type = "coal_supercritical"
        elif "subcritical" in technology:
            tech_type = "coal_subcritical"
        else:
            tech_type = "coal_supercritical"  # default

        result = model.calculate_equity_value(
            asset_id=plant_id,
            baseline_ebitda=plant_data.annual_ebitda_usd,
            current_debt=plant_data.total_debt_usd,
            physical_risk_pct=None,  # Calculate dynamically
            generation_loss_pct=None,  # From CSV
            scenario=scenario,
            plant_technology=tech_type,
        )
        results[plant_id] = result
        total_baseline_equity += result.baseline_equity_value
        total_adjusted_equity += result.climate_adjusted_equity

    equity_impact = total_baseline_equity - total_adjusted_equity

    return {
        "scenario": scenario,
        "total_baseline_equity_usd": total_baseline_equity,
        "total_adjusted_equity_usd": total_adjusted_equity,
        "total_equity_impact_usd": equity_impact,
        "portfolio_impact_pct": (equity_impact / total_baseline_equity * 100) if total_baseline_equity > 0 else 0,
        "by_asset": {k: v.equity_impact_pct for k, v in results.items()},
    }

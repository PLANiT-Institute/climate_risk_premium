"""
Cash-flow engine for baseline vs risk-adjusted scenarios.

Supports:
- Year-by-year physical risk evolution (CLIMADA hazards)
- Proper outage modeling (reduces revenue, not adds cost)
- Efficiency loss from physical risks

Note: Carbon pricing has been archived. This model focuses on dispatch and physical risks.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, TYPE_CHECKING
import numpy as np
import numpy_financial as npf

from src.risk import TransitionAdjustments, PhysicalAdjustments
from src.scenarios import TransitionScenario, MarketScenario

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.risk.physical import YearlyPhysicalAdjustments
    from src.risk.transition import YearlyTransitionAdjustments


@dataclass
class CashFlowTimeSeries:
    """Time-series cash flow projections."""

    years: np.ndarray
    revenue: np.ndarray
    fuel_costs: np.ndarray
    variable_opex: np.ndarray
    fixed_opex: np.ndarray
    lost_revenue_from_outages: np.ndarray
    total_costs: np.ndarray
    ebitda: np.ndarray
    depreciation: np.ndarray
    ebit: np.ndarray
    interest_expense: np.ndarray
    tax_expense: np.ndarray
    net_income: np.ndarray
    capex: np.ndarray
    free_cash_flow: np.ndarray
    capacity_factor: np.ndarray
    final_cf: np.ndarray
    carbon_costs: np.ndarray = field(default=None)  # type: ignore[arg-type]
    dscr: np.ndarray = field(default=None)  # type: ignore[arg-type]

    def __post_init__(self) -> None:
        if self.carbon_costs is None:
            self.carbon_costs = np.zeros_like(self.years, dtype=float)
        if self.dscr is None:
            self.dscr = np.zeros_like(self.years, dtype=float)

    def to_dict(self) -> Dict[str, List[float]]:
        """Convert to dict for CSV export."""
        return {
            "year": self.years.tolist(),
            "revenue": self.revenue.tolist(),
            "fuel_costs": self.fuel_costs.tolist(),
            "variable_opex": self.variable_opex.tolist(),
            "fixed_opex": self.fixed_opex.tolist(),
            "lost_revenue_from_outages": self.lost_revenue_from_outages.tolist(),
            "total_costs": self.total_costs.tolist(),
            "ebitda": self.ebitda.tolist(),
            "depreciation": self.depreciation.tolist(),
            "ebit": self.ebit.tolist(),
            "interest_expense": self.interest_expense.tolist(),
            "tax_expense": self.tax_expense.tolist(),
            "net_income": self.net_income.tolist(),
            "capex": self.capex.tolist(),
            "free_cash_flow": self.free_cash_flow.tolist(),
            "capacity_factor": self.capacity_factor.tolist(),
            "final_cf": self.final_cf.tolist(),
            "carbon_costs": self.carbon_costs.tolist(),
            "dscr": self.dscr.tolist(),
        }


def compute_cashflows_timeseries(
    plant_params: Dict[str, Any],
    transition_scenario: TransitionScenario,
    transition_adj: TransitionAdjustments,
    physical_adj: PhysicalAdjustments,
    market_scenario: MarketScenario | None = None,
    start_year: int = 2025,
    yearly_physical_adj: Optional["YearlyPhysicalAdjustments"] = None,
    yearly_transition_adj: Optional["YearlyTransitionAdjustments"] = None,
) -> CashFlowTimeSeries:
    """
    Compute annual cash flows over the plant's operating life.

    Args:
        plant_params: Plant design parameters
        transition_scenario: Transition risk scenario (dispatch penalties)
        transition_adj: Static transition adjustments
        physical_adj: Static physical adjustments (used if yearly_physical_adj is None)
        market_scenario: Optional market scenario
        start_year: First year of operation
        yearly_physical_adj: Optional year-by-year physical adjustments for dynamic climate risk

    Physical Risk Modeling:
        - If yearly_physical_adj is provided, uses dynamic year-by-year hazards
        - Otherwise, uses static physical_adj for all years
        - Outages REDUCE revenue (lost sales), not add costs
        - Efficiency loss reduces effective heat rate
    """
    # Extract plant parameters
    # Extract plant parameters (Assumes defaults are merged by caller)
    capacity_mw = float(plant_params["capacity_mw"])
    price = float(plant_params["power_price_per_mwh"])
    heat_rate = float(plant_params["heat_rate_mmbtu_mwh"])
    fuel_price = float(plant_params["fuel_price_per_mmbtu"])
    fixed_opex_per_kw = float(
        plant_params.get("fixed_opex_per_kw_year", plant_params.get("fixed_opex_per_kw", 35.0))
    )
    variable_opex_per_mwh = float(plant_params["variable_opex_per_mwh"])

    # Financial params for concretization
    total_capex = float(plant_params["total_capex_million"]) * 1e6
    useful_life = int(plant_params.get("useful_life", plant_params.get("operating_years", 40)))
    tax_rate = float(plant_params["tax_rate"])
    debt_fraction = float(plant_params["debt_fraction"])
    debt_interest = float(plant_params["debt_interest_rate"])
    debt_tenor = int(plant_params["debt_tenor_years"])

    # Operating years
    n_years = transition_adj.operating_years
    years = np.arange(start_year, start_year + n_years)

    # === PHYSICAL RISK: Get year-by-year or static adjustments ===
    if yearly_physical_adj is not None:
        # Dynamic year-by-year physical risks (climate change progression)
        outage_rates = np.array(
            [yearly_physical_adj.get_adjustment_for_year(int(y)).outage_rate for y in years]
        )
        capacity_derates = np.array(
            [yearly_physical_adj.get_adjustment_for_year(int(y)).capacity_derate for y in years]
        )
        efficiency_losses = np.array(
            [yearly_physical_adj.get_adjustment_for_year(int(y)).efficiency_loss for y in years]
        )
        water_constraints = np.array(
            [
                yearly_physical_adj.get_adjustment_for_year(int(y)).water_constrained_capacity
                for y in years
            ]
        )
    else:
        # Static physical risks (same for all years)
        outage_rates = np.full(n_years, physical_adj.outage_rate)
        capacity_derates = np.full(n_years, physical_adj.capacity_derate)
        efficiency_losses = np.full(n_years, physical_adj.efficiency_loss)
        water_constraints = np.full(
            n_years, getattr(physical_adj, "water_constrained_capacity", 1.0)
        )

    # === CAPACITY FACTOR CALCULATION ===
    if yearly_transition_adj is not None:
        # Year-by-year CF from enhanced transition trajectory
        base_cf_series = np.array([yearly_transition_adj.get_cf_for_year(int(y)) for y in years])
    else:
        base_cf = transition_adj.capacity_factor
        base_cf_series = np.full(n_years, base_cf)

    # Apply Market Demand factor if market scenario exists
    if market_scenario:
        demand_factors = np.array(
            [market_scenario.get_demand_factor(int(year), start_year) for year in years]
        )
        base_cf_series = np.minimum(1.0, base_cf_series * demand_factors)

    # Apply capacity derates (year-by-year)
    cf_series = base_cf_series * (1 - capacity_derates)

    # Apply water constraints (year-by-year hard cap)
    cf_series = np.minimum(cf_series, water_constraints)
    cf_series = np.maximum(cf_series, 0.0)

    # === GENERATION AND REVENUE ===
    # Potential generation (before outages)
    potential_mwh = capacity_mw * 8760 * cf_series

    # Actual generation (after outages reduce availability)
    # Outage = fraction of time plant is unavailable
    actual_mwh = potential_mwh * (1 - outage_rates)

    # Revenue is based on ACTUAL generation (outages reduce revenue)
    if market_scenario:
        prices = np.array(
            [market_scenario.get_power_price(int(year), start_year) for year in years]
        )
    else:
        prices = np.full(n_years, price)

    revenue = actual_mwh * prices

    # === COSTS ===
    # Fuel costs: affected by efficiency loss (higher heat rate = more fuel)
    effective_heat_rates = heat_rate * (1 + efficiency_losses)
    fuel_costs = actual_mwh * effective_heat_rates * fuel_price

    # Variable O&M: based on actual generation
    variable_opex = actual_mwh * variable_opex_per_mwh

    # Fixed O&M: constant regardless of generation
    fixed_opex = np.full(n_years, capacity_mw * 1000 * fixed_opex_per_kw)

    # Carbon costs (K-ETS)
    if yearly_transition_adj is not None:
        carbon_cost_per_mwh = np.array(
            [yearly_transition_adj.get_carbon_cost_per_mwh_for_year(int(y)) for y in years]
        )
        carbon_costs = actual_mwh * carbon_cost_per_mwh
    else:
        carbon_costs = np.zeros(n_years)

    # Outage costs: Now represents LOST REVENUE (for reporting), not an actual cash cost
    # This is the revenue we would have earned but didn't due to outages
    # We track this separately for transparency, but it's already reflected in reduced revenue
    lost_revenue_from_outages = potential_mwh * outage_rates * prices  # Lost revenue from outages

    total_costs = fuel_costs + variable_opex + fixed_opex + carbon_costs
    # Note: lost_revenue_from_outages NOT included in total_costs - it's informational only

    # --- Financial Calculations ---

    # 1. EBITDA Calculation
    # EBITDA = Revenue - Total Costs (Fuel + O&M)
    ebitda = revenue - total_costs

    negative_years = years[ebitda < 0]
    if len(negative_years) > 0:
        logger.warning(
            f"Negative EBITDA detected in {len(negative_years)} year(s): "
            f"{negative_years.tolist()}"
        )

    # 2. Depreciation (Non-cash expense)
    # Straight-line depreciation over useful life
    # Assumption: Capex is fully depreciable, no salvage value
    annual_depreciation = total_capex / useful_life
    depreciation = np.full(n_years, annual_depreciation)

    # 3. EBIT (Earnings Before Interest and Taxes)
    # EBIT = EBITDA - Depreciation
    ebit = ebitda - depreciation

    # 4. Debt Service (Interest & Principal)
    # Calculate amortization schedule for the debt portion
    debt_amount = total_capex * debt_fraction
    interest_expense = np.zeros(n_years)
    balance = debt_amount

    annual_ds = 0.0
    if debt_interest > 0 and debt_tenor > 0:
        # Calculate level annual payment (Annuity)
        annual_ds = -npf.pmt(debt_interest, debt_tenor, debt_amount)

        for i in range(min(n_years, debt_tenor)):
            # Interest component
            interest = balance * debt_interest
            # Principal component
            principal = annual_ds - interest

            interest_expense[i] = interest

            # Update balance
            balance -= principal
            if balance < 0:
                balance = 0

    # 5. Tax Calculation
    # Corporate Tax is applied to Earnings Before Tax (EBT)
    # EBT = EBIT - Interest Expense
    # Tax Shield: Interest expense reduces taxable income
    taxable_income = ebit - interest_expense
    # Tax cannot be negative (no carry-forward modeled for simplicity)
    tax_expense = np.maximum(0.0, taxable_income * tax_rate)

    # 6. Net Income
    # Net Income = EBT - Tax
    net_income = ebit - interest_expense - tax_expense

    # 7. Free Cash Flow (FCFF - Free Cash Flow to Firm)
    # FCFF represents cash available to all capital providers (Debt + Equity)
    # Formula: FCFF = EBIT * (1 - Tax Rate) + Depreciation - Capex - Change in WC
    # Note: Interest tax shield is captured in WACC for NPV, so we use EBIT*(1-t)
    # However, for consistency with the previous model which might have used a different definition,
    # let's stick to the standard FCFF definition:
    # FCFF = NOPAT + Depreciation - Capex
    # NOPAT = EBIT * (1 - Tax Rate)
    nopat = ebit * (1 - tax_rate)

    # Capex (sustaining capex only, construction already completed)
    capex = np.zeros(n_years)

    fcf = nopat + depreciation - capex

    # DSCR (second pass, after tax_expense and capex are both defined)
    cfads = ebitda - tax_expense - capex
    dscr_series = np.zeros(n_years)
    if annual_ds > 0:
        n_debt = min(n_years, debt_tenor)
        dscr_series[:n_debt] = cfads[:n_debt] / annual_ds

    final_cf_series = cf_series * (1 - outage_rates)

    return CashFlowTimeSeries(
        years=years,
        revenue=revenue,
        fuel_costs=fuel_costs,
        variable_opex=variable_opex,
        fixed_opex=fixed_opex,
        lost_revenue_from_outages=lost_revenue_from_outages,
        total_costs=total_costs,
        ebitda=ebitda,
        depreciation=depreciation,
        ebit=ebit,
        interest_expense=interest_expense,
        tax_expense=tax_expense,
        net_income=net_income,
        capex=capex,
        free_cash_flow=fcf,
        capacity_factor=cf_series,
        final_cf=final_cf_series,
        carbon_costs=carbon_costs,
        dscr=dscr_series,
    )


# Keep old function for backward compatibility
@dataclass
class CashFlowResult:
    annual_revenue: float
    annual_costs: float
    ebitda: float
    free_cash_flow: float
    notes: str


def compute_cashflows(
    plant_params: Dict[str, Any],
    transition: TransitionAdjustments,
    physical: PhysicalAdjustments,
) -> CashFlowResult:
    """
    Legacy single-period calculator. Use compute_cashflows_timeseries instead.
    """
    capacity_mw = float(plant_params.get("capacity_mw", 2000))
    price = float(plant_params.get("power_price_per_mwh", 80))
    heat_rate = float(plant_params.get("heat_rate_mmbtu_mwh", 8.8))
    fuel_price = float(plant_params.get("fuel_price_per_mmbtu", 3.2))
    fixed_opex = float(plant_params.get("fixed_opex_per_kw_year", 42))
    variable_opex = float(plant_params.get("variable_opex_per_mwh", 4.5))
    cf = max(0.0, transition.capacity_factor * (1 - physical.capacity_derate))

    annual_mwh = capacity_mw * 8760 * cf
    fuel_cost = annual_mwh * heat_rate * fuel_price
    variable_costs = annual_mwh * variable_opex
    fixed_costs = capacity_mw * 1000 * fixed_opex
    outage_penalty = annual_mwh * physical.outage_rate * price

    revenue = annual_mwh * price
    costs = fuel_cost + variable_costs + fixed_costs + outage_penalty
    ebitda = revenue - costs
    fcf = ebitda
    notes = "Legacy single-period; use compute_cashflows_timeseries instead."
    return CashFlowResult(
        annual_revenue=revenue,
        annual_costs=costs,
        ebitda=ebitda,
        free_cash_flow=fcf,
        notes=notes,
    )

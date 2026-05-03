"""Cash-flow engine — transition risk and optional wildfire physical risk.

Computes year-by-year free cash flows for a power plant under a transition
policy scenario, with an optional wildfire physical risk overlay.

Key assumptions
---------------
- Capacity factor is first reduced by the dispatch penalty (transition), then
  further multiplied by (1 − wildfire_outage_rate) when wildfire_adj is given.
- Fuel costs are scaled by (1 + efficiency_loss) when wildfire_adj is given,
  reflecting thermal efficiency degradation from smoke/particulate fouling.
- Carbon costs (K-ETS) are computed from ``YearlyTransitionAdjustments``.
- Debt service uses a level-annuity schedule (standard project finance).
- Depreciation is straight-line over ``useful_life`` years.
- Free Cash Flow = NOPAT + Depreciation.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, TYPE_CHECKING

import numpy as np
import numpy_financial as npf

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.risk.physical import YearlyPhysicalAdjustments
    from src.risk.transition import YearlyTransitionAdjustments


# ---------------------------------------------------------------------------
# Output container
# ---------------------------------------------------------------------------

@dataclass
class CashFlowTimeSeries:
    """Annual cash-flow projections for the plant's operating life.

    All monetary arrays are in USD (not millions).  Convert at the output
    layer if needed.
    """

    years: np.ndarray
    revenue: np.ndarray
    fuel_costs: np.ndarray
    variable_opex: np.ndarray
    fixed_opex: np.ndarray
    carbon_costs: np.ndarray
    total_costs: np.ndarray
    ebitda: np.ndarray
    depreciation: np.ndarray
    ebit: np.ndarray
    interest_expense: np.ndarray
    tax_expense: np.ndarray
    net_income: np.ndarray
    capex: np.ndarray             # maintenance / replacement capex (zero for now)
    free_cash_flow: np.ndarray
    capacity_factor: np.ndarray   # effective CF after dispatch penalty
    dscr: np.ndarray = field(default_factory=lambda: np.array([]))

    def __post_init__(self) -> None:
        if self.dscr is None or len(self.dscr) == 0:
            self.dscr = np.zeros_like(self.years, dtype=float)

    def to_dict(self) -> Dict[str, List[float]]:
        """Flatten to a dict of lists (for CSV export)."""
        return {
            "year": self.years.tolist(),
            "revenue": self.revenue.tolist(),
            "fuel_costs": self.fuel_costs.tolist(),
            "variable_opex": self.variable_opex.tolist(),
            "fixed_opex": self.fixed_opex.tolist(),
            "carbon_costs": self.carbon_costs.tolist(),
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
            "dscr": self.dscr.tolist(),
        }


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def compute_cashflows(
    plant_params: Dict[str, Any],
    yearly_transition_adj: "YearlyTransitionAdjustments",
    yearly_physical_adj: "YearlyPhysicalAdjustments | None" = None,
    start_year: int = 2025,
) -> CashFlowTimeSeries:
    """Compute annual cash flows over the plant's operating life.

    When ``yearly_physical_adj`` is provided the capacity factor for each year
    is further reduced by ``(1 − outage_rate)`` and fuel costs are scaled by
    ``(1 + efficiency_loss)`` to reflect wildfire-driven unavailability and
    thermal efficiency degradation from smoke/particulate fouling.

    Args:
        plant_params: Flat dict from ``load_plant_params()``.
        yearly_transition_adj: Per-year CFs and carbon costs from
            ``build_yearly_transition_adjustments()``.
        yearly_physical_adj: Optional per-year physical risk adjustments from
            ``build_physical_adjustments()``.  Pass ``None`` to run
            transition-risk only.
        start_year: First calendar year of operations (unused here; years
            come from ``yearly_transition_adj.years``).

    Returns:
        ``CashFlowTimeSeries`` spanning the scenario's retirement horizon.
    """
    # --- Plant parameters ---
    capacity_mw = float(plant_params["capacity_mw"])
    price = float(plant_params["power_price_per_mwh"])
    heat_rate = float(plant_params["heat_rate_mmbtu_mwh"])
    fuel_price = float(plant_params["fuel_price_per_mmbtu"])
    fixed_opex_per_kw = float(plant_params["fixed_opex_per_kw"])
    variable_opex_per_mwh = float(plant_params["variable_opex_per_mwh"])
    total_capex = float(plant_params["total_capex_million"]) * 1e6
    useful_life = int(plant_params["useful_life"])
    tax_rate = float(plant_params["tax_rate"])
    debt_fraction = float(plant_params["debt_fraction"])
    debt_interest = float(plant_params["debt_interest_rate"])
    debt_tenor = int(plant_params["debt_tenor_years"])

    # --- Time axis ---
    years = yearly_transition_adj.years.copy()
    n_years = len(years)

    # --- Capacity factors: transition × physical overlay ---
    cf_series = np.array(
        [yearly_transition_adj.get_cf_for_year(int(y)) for y in years]
    )
    if yearly_physical_adj is not None:
        phys_adj_list = [
            yearly_physical_adj.get_adjustment_for_year(int(y)) for y in years
        ]
        # Wildfire outage reduces available generation hours
        cf_series = cf_series * np.array(
            [1.0 - a.outage_rate for a in phys_adj_list]
        )
        # Drought/temperature capacity derate (zero until activated)
        cf_series = cf_series * np.array(
            [1.0 - a.capacity_derate for a in phys_adj_list]
        )
        # Water availability hard cap (1.0 until activated)
        cf_series = np.minimum(
            cf_series,
            np.array([a.water_constrained_capacity for a in phys_adj_list]),
        )

    # --- Generation (MWh/year) ---
    annual_mwh = capacity_mw * 8760 * cf_series

    # --- Revenue ---
    revenue = annual_mwh * price

    # --- Operating costs ---
    # Efficiency loss raises effective heat rate (smoke fouling, thermal stress)
    if yearly_physical_adj is not None:
        eff_loss = np.array([a.efficiency_loss for a in phys_adj_list])
        fuel_costs = annual_mwh * heat_rate * (1.0 + eff_loss) * fuel_price
    else:
        fuel_costs = annual_mwh * heat_rate * fuel_price
    variable_opex = annual_mwh * variable_opex_per_mwh
    fixed_opex = np.full(n_years, capacity_mw * 1000 * fixed_opex_per_kw)

    # Carbon costs (K-ETS): interpolated from policy anchor years
    carbon_cost_per_mwh = np.array(
        [yearly_transition_adj.get_carbon_cost_per_mwh_for_year(int(y)) for y in years]
    )
    carbon_costs = annual_mwh * carbon_cost_per_mwh

    total_costs = fuel_costs + variable_opex + fixed_opex + carbon_costs

    # --- EBITDA ---
    ebitda = revenue - total_costs

    negative_yrs = years[ebitda < 0]
    if len(negative_yrs) > 0:
        logger.warning(
            "Scenario '%s': negative EBITDA in %d year(s): %s",
            yearly_transition_adj.scenario_name,
            len(negative_yrs),
            negative_yrs.tolist(),
        )

    # --- Depreciation (straight-line) ---
    annual_dep = total_capex / useful_life
    depreciation = np.full(n_years, annual_dep)

    # --- EBIT ---
    ebit = ebitda - depreciation

    # --- Debt service (level annuity) ---
    debt_amount = total_capex * debt_fraction
    interest_expense = np.zeros(n_years)
    annual_ds = 0.0

    if debt_interest > 0 and debt_tenor > 0:
        annual_ds = float(-npf.pmt(debt_interest, debt_tenor, debt_amount))
        balance = debt_amount
        for i in range(min(n_years, debt_tenor)):
            interest = balance * debt_interest
            principal = annual_ds - interest
            interest_expense[i] = interest
            balance = max(0.0, balance - principal)

    # --- Tax (no carry-forward) ---
    taxable_income = ebit - interest_expense
    tax_expense = np.maximum(0.0, taxable_income * tax_rate)

    # --- Net income ---
    net_income = ebit - interest_expense - tax_expense

    # --- Free Cash Flow (FCFF) ---
    # FCFF = NOPAT + Depreciation  (maintenance capex is zero at this stage)
    nopat = ebit * (1.0 - tax_rate)
    capex = np.zeros(n_years)
    free_cash_flow = nopat + depreciation - capex

    # --- DSCR (CFADS / debt service) ---
    # NaN for post-debt years — DSCR is undefined once the loan is fully repaid.
    cfads = ebitda - tax_expense
    dscr_series = np.full(n_years, np.nan)
    if annual_ds > 0:
        n_debt = min(n_years, debt_tenor)
        dscr_series[:n_debt] = cfads[:n_debt] / annual_ds

    return CashFlowTimeSeries(
        years=years,
        revenue=revenue,
        fuel_costs=fuel_costs,
        variable_opex=variable_opex,
        fixed_opex=fixed_opex,
        carbon_costs=carbon_costs,
        total_costs=total_costs,
        ebitda=ebitda,
        depreciation=depreciation,
        ebit=ebit,
        interest_expense=interest_expense,
        tax_expense=tax_expense,
        net_income=net_income,
        capex=capex,
        free_cash_flow=free_cash_flow,
        capacity_factor=cf_series,
        dscr=dscr_series,
    )

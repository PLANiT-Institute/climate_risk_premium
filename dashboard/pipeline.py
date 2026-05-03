"""Cached pipeline wrapper for the Streamlit dashboard.

Calls the src/ modules directly — no HTTP, no JSON serialization.
Results are cached with @st.cache_data so the pipeline only runs once per session.

Scenario structure
------------------
The pipeline is driven entirely by CSVs — no scenario definitions live in code:

  data/scenarios/climate_scenarios.csv
      climate_scenario, transition_scenario, physical_scenario, physical_weight
      One row per (climate, transition, physical) triplet.
      Multiple rows with the same climate_scenario blend physical scenarios by weight.

  data/transition/scenarios.csv      — transition policy definitions
  data/physical/scenarios.csv        — physical risk scenario definitions
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import streamlit as st

# Ensure repo root is importable regardless of working directory
_REPO = Path(__file__).parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.data.loaders import (
    load_climate_scenarios,
    load_model_assumptions,
    load_physical_scenarios,
    load_plant_params,
    load_rating_spreads,
    load_transition_scenarios,
)
from src.financials.cashflow import compute_cashflows
from src.financials.metrics import calculate_debt_service, calculate_metrics
from src.risk.credit_rating import (
    Rating,
    assess_credit_rating,
    calculate_crp_from_ratings,
    calculate_rating_metrics_from_financials,
    get_counterfactual_baseline_rating,
)
from src.risk.financing import calculate_financing_with_counterfactual
from src.risk.physical import YearlyPhysicalAdjustments, build_physical_adjustments
from src.risk.transition import build_yearly_transition_adjustments
from src.scenarios.base import TransitionScenario


def _float(v: Any) -> float:
    """Cast numpy scalar → plain Python float, safe for display."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return 0.0
    return float(v)


def _float_or_none(v: Any) -> float | None:
    """Like _float but returns None for NaN/None — use for IRR and other metrics
    that are mathematically undefined when all cashflows are negative."""
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if np.isnan(f) else f


def _build_blended_physical(
    physical_rows: list[dict],
    start_year: int,
    n_years: int,
) -> YearlyPhysicalAdjustments:
    """Build a weight-blended YearlyPhysicalAdjustments from one or more physical scenarios.

    When a climate scenario has multiple physical scenario rows (weights < 1.0),
    the outage and other arrays are linearly blended by normalised weight.
    """
    total_weight = sum(float(r["physical_weight"]) for r in physical_rows)

    blended_outage    = None
    blended_tx        = None
    blended_derate    = None
    blended_eff       = None
    blended_water     = None
    blended_capex     = None
    ref_years         = None
    scenario_label    = "+".join(
        f"{r['physical_scenario']}×{r['physical_weight'] / total_weight:.2f}"
        for r in physical_rows
    )

    for row in physical_rows:
        w   = float(row["physical_weight"]) / total_weight
        adj = build_physical_adjustments(
            start_year=start_year,
            n_years=n_years,
            physical_scenario=row["physical_scenario"],
        )
        if blended_outage is None:
            ref_years      = adj.years
            blended_outage = adj.outage_rates * w
            blended_tx     = adj.transmission_outage_rates * w
            blended_derate = adj.capacity_derates * w
            blended_eff    = adj.efficiency_losses * w
            blended_water  = (1.0 - adj.water_constraints) * w   # blend the deficit
            blended_capex  = adj.asset_capex_loss_rates * w
        else:
            blended_outage += adj.outage_rates * w
            blended_tx     += adj.transmission_outage_rates * w
            blended_derate += adj.capacity_derates * w
            blended_eff    += adj.efficiency_losses * w
            blended_water  += (1.0 - adj.water_constraints) * w
            blended_capex  += adj.asset_capex_loss_rates * w

    return YearlyPhysicalAdjustments(
        years=ref_years,
        outage_rates=blended_outage,
        transmission_outage_rates=blended_tx,
        capacity_derates=blended_derate,
        efficiency_losses=blended_eff,
        water_constraints=1.0 - blended_water,   # convert deficit back
        asset_capex_loss_rates=blended_capex,
        scenario_name=scenario_label,
    )


# All recognised physical channel names (used for validation + defaults)
ALL_PHYSICAL_CHANNELS: tuple[str, ...] = (
    "wildfire_outage",
    "drought_derate",
    "water_constraint",
    "efficiency_loss",
)


@st.cache_data
def run_pipeline(
    active_physical_channels: tuple[str, ...] = ALL_PHYSICAL_CHANNELS,
) -> dict:
    """Run all climate scenarios and return results as plain Python dicts/lists.

    Args:
        active_physical_channels: Tuple of channel names to include in the
            cashflow calculation.  Default is all channels.  Pass ``()`` to
            disable all physical risk.  Valid names:
            ``"wildfire_outage"``, ``"drought_derate"``,
            ``"water_constraint"``, ``"efficiency_loss"``.

    Returns
    -------
    dict with keys:
      plant               — plant parameters (dict)
      scenarios           — list of scenario summary dicts, keyed by climate_scenario
      cashflows           — {climate_scenario: [row_dict, ...]}
      ratings             — list of year-by-year rating dicts
      physical_meta       — list of physical scenario dicts from data/physical/scenarios.csv
      climate_scenario_meta — list of climate scenario definition rows
      active_physical_channels — tuple of active channel names (echoed back)
    """
    plant       = load_plant_params()
    assumptions = load_model_assumptions()
    spreads     = load_rating_spreads()

    total_capex        = float(plant["total_capex_million"]) * 1e6
    debt_fraction      = float(plant["debt_fraction"])
    debt_interest      = float(plant["debt_interest_rate"])
    debt_tenor         = int(plant["debt_tenor_years"])
    depreciation_years = int(plant["depreciation_years"])
    capacity_mw        = float(plant["capacity_mw"])
    base_cf            = float(plant["capacity_factor"])
    emissions          = float(plant["emissions_tCO2_per_mwh"])
    risk_free          = float(plant["risk_free_rate"])
    equity_fraction    = float(plant["equity_fraction"])
    start_year         = int(assumptions["start_year"])
    base_rate          = float(assumptions["base_rate"])
    cash_ratio         = float(assumptions["cash_ratio"])
    plant_name         = str(plant["plant_name"])

    rating_order = [r.name for r in sorted(Rating, key=lambda r: r.value)]
    counterfactual = get_counterfactual_baseline_rating()
    debt_struct = calculate_debt_service(total_capex, debt_fraction, debt_interest, debt_tenor)
    cumulative_principal = debt_struct.principal_schedule.cumsum()

    financing_params = {
        "risk_free_rate": risk_free,
        "debt_fraction": debt_fraction,
        "equity_fraction": equity_fraction,
    }

    # --- Load scenario definitions from CSVs ---
    physical_meta      = load_physical_scenarios()
    climate_rows_all   = load_climate_scenarios()
    transition_rows_by_name = {r["scenario"]: r for r in load_transition_scenarios()}

    # Group climate scenario rows by climate_scenario name (for blending)
    climate_groups: dict[str, list[dict]] = defaultdict(list)
    for row in climate_rows_all:
        climate_groups[row["climate_scenario"]].append(row)

    # Max retirement horizon across all transition scenarios used
    all_retirement_years = [
        int(transition_rows_by_name[g[0]["transition_scenario"]]["retirement_years"])
        for g in climate_groups.values()
        if g[0]["transition_scenario"] in transition_rows_by_name
    ]
    max_retirement = max(all_retirement_years) if all_retirement_years else 40

    # --- Run one cashflow per climate scenario ---
    scenario_comparison: list[dict] = []
    cashflows: dict[str, list[dict]] = {}
    yearly_ratings: list[dict] = []

    for climate_name, group in climate_groups.items():
        # All rows in a group share the same transition scenario
        trans_name  = group[0]["transition_scenario"]
        trans_row   = transition_rows_by_name.get(trans_name)
        if trans_row is None:
            continue   # skip if transition scenario not defined

        scenario = TransitionScenario.from_policy_row(trans_row)

        yearly_adj = build_yearly_transition_adjustments(
            scenario=scenario,
            base_capacity_factor=base_cf,
            emissions_tco2_per_mwh=emissions,
        )

        # Build blended physical adjustment for this climate scenario
        physical_adj = _build_blended_physical(group, start_year, max_retirement)

        cf_ts   = compute_cashflows(
            plant_params=plant,
            yearly_transition_adj=yearly_adj,
            yearly_physical_adj=physical_adj,
            active_physical_channels=frozenset(active_physical_channels),
        )
        metrics = calculate_metrics(cf_ts, plant)

        avg_ebitda   = _float(cf_ts.ebitda.mean())
        avg_interest = _float(cf_ts.interest_expense.mean())
        debt_mid         = total_capex * debt_fraction * 0.5
        fixed_assets_avg = total_capex * 0.5
        total_equity_avg = max(0.0, fixed_assets_avg - debt_mid)

        rating_metrics = calculate_rating_metrics_from_financials(
            capacity_mw=capacity_mw,
            ebitda=avg_ebitda,
            fixed_assets=total_capex,
            interest_expense=avg_interest,
            total_debt=debt_mid,
            cash_and_equivalents=0.0,
            total_equity=total_equity_avg,
            total_assets=total_capex,
            dscr=metrics.avg_dscr,
            consecutive_loss_years=int((cf_ts.ebitda < 0).sum()),
        )
        assessment     = assess_credit_rating(rating_metrics)
        scenario_rating = assessment.overall_rating
        crp_bps = calculate_crp_from_ratings(
            baseline_rating=counterfactual,
            scenario_rating=scenario_rating,
            risk_free_rate=risk_free,
            debt_fraction=debt_fraction,
        )
        notch_change = scenario_rating.value - counterfactual.value
        financing = calculate_financing_with_counterfactual(
            scenario_spread_bps=scenario_rating.to_spread_bps(),
            counterfactual_spread_bps=counterfactual.to_spread_bps(),
            npv_loss=0.0,
            total_capex=total_capex,
            params=financing_params,
            scenario_notch=scenario_rating.value,
            counterfactual_notch=counterfactual.value,
        )

        rd = assessment.to_dict()
        # Collect the first description; for blends, note the blend
        description = group[0].get("description", climate_name)

        scenario_comparison.append({
            "scenario": climate_name,
            "transition_scenario": trans_name,
            "physical_scenario": physical_adj.scenario_name,
            "description": description,
            "dispatch_penalty_pct": scenario.dispatch_penalty * 100,
            "retirement_years": scenario.retirement_years,
            "carbon_price_2025": scenario.carbon_prices.get(2025, 0.0),
            "carbon_price_2030": scenario.carbon_prices.get(2030, 0.0),
            "carbon_price_2040": scenario.carbon_prices.get(2040, 0.0),
            "carbon_price_2050": scenario.carbon_prices.get(2050, 0.0),
            "npv_million": _float(metrics.npv / 1e6),
            "irr_pct": (
                None if metrics.irr is None else _float_or_none(metrics.irr * 100)
            ),
            "avg_dscr": _float(metrics.avg_dscr),
            "min_dscr": _float(metrics.min_dscr),
            "llcr": _float(metrics.llcr),
            "payback_years": (
                _float(metrics.payback_years) if metrics.payback_years is not None else None
            ),
            "crp_bps": _float(crp_bps),
            "wacc_baseline_pct": _float(financing.wacc_baseline_pct),
            "wacc_adjusted_pct": _float(financing.wacc_adjusted_pct),
            "overall_rating": rd["overall_rating"],
            "spread_bps": rd["spread_bps"],
            "is_investment_grade": rd["is_investment_grade"],
            "is_distressed": rd["is_distressed"],
            "profitability_rating": rd["profitability_rating"],
            "coverage_rating": rd["coverage_rating"],
            "dscr_rating": rd["dscr_rating"],
            "equity_leverage_rating": rd["equity_leverage_rating"],
            "avg_ebitda_million": avg_ebitda / 1e6,
            "total_carbon_cost_million": _float(cf_ts.carbon_costs.sum()) / 1e6,
            "counterfactual_rating": str(counterfactual),
            "notch_change": notch_change,
        })

        # Per-year cashflow rows
        cf_rows: list[dict] = []
        for i, year in enumerate(cf_ts.years):
            dscr_val = cf_ts.dscr[i]
            cf_rows.append({
                "year": int(year),
                "revenue":          _float(cf_ts.revenue[i]),
                "fuel_costs":       _float(cf_ts.fuel_costs[i]),
                "variable_opex":    _float(cf_ts.variable_opex[i]),
                "fixed_opex":       _float(cf_ts.fixed_opex[i]),
                "carbon_costs":     _float(cf_ts.carbon_costs[i]),
                "total_costs":      _float(cf_ts.total_costs[i]),
                "ebitda":           _float(cf_ts.ebitda[i]),
                "depreciation":     _float(cf_ts.depreciation[i]),
                "ebit":             _float(cf_ts.ebit[i]),
                "interest_expense": _float(cf_ts.interest_expense[i]),
                "tax_expense":      _float(cf_ts.tax_expense[i]),
                "net_income":       _float(cf_ts.net_income[i]),
                "free_cash_flow":   _float(cf_ts.free_cash_flow[i]),
                "capacity_factor":  _float(cf_ts.capacity_factor[i]),
                "dscr": (
                    None if (dscr_val is None or np.isnan(dscr_val)) else float(dscr_val)
                ),
            })
        cashflows[climate_name] = cf_rows

        # Year-by-year credit ratings
        for i, year in enumerate(cf_ts.years):
            raw_dscr = cf_ts.dscr[i]
            dscr_i   = float(raw_dscr) if (raw_dscr is not None and not np.isnan(raw_dscr)) else None
            ebitda_i   = _float(cf_ts.ebitda[i])
            interest_i = _float(cf_ts.interest_expense[i])

            if i < debt_tenor:
                debt_out = total_capex * debt_fraction - (
                    _float(cumulative_principal[i - 1]) if i > 0 else 0.0
                )
            else:
                debt_out = 0.0

            fixed_assets_i = total_capex * max(0.0, 1 - i / depreciation_years)
            total_equity_i = max(0.0, fixed_assets_i - debt_out)
            total_assets_i = max(fixed_assets_i, debt_out)

            rm = calculate_rating_metrics_from_financials(
                capacity_mw=capacity_mw,
                ebitda=ebitda_i,
                fixed_assets=total_assets_i if total_assets_i > 0 else total_capex,
                interest_expense=interest_i,
                total_debt=debt_out,
                cash_and_equivalents=max(0.0, ebitda_i * cash_ratio),
                total_equity=total_equity_i,
                total_assets=total_assets_i if total_assets_i > 0 else total_capex,
                dscr=dscr_i,
            )
            yr_assessment = assess_credit_rating(rm)
            rating_str    = yr_assessment.overall_rating.name

            if dscr_i is not None:
                if dscr_i < 0:
                    rating_str = "D"
                elif dscr_i < 1.0:
                    idx = rating_order.index(rating_str)
                    rating_str = rating_order[min(idx + 1, len(rating_order) - 1)]

            spread = spreads.get(rating_str, spreads.get("CCC", 900))
            yearly_ratings.append({
                "scenario":      climate_name,
                "year":          int(year),
                "dscr":          round(dscr_i, 3) if dscr_i is not None else None,
                "rating":        rating_str,
                "spread_bps":    spread,
                "cost_of_debt":  round(base_rate + spread / 10000, 6),
                "ebitda":        round(ebitda_i / 1e6, 2),
            })

    plant_out = {
        "name":                   plant_name,
        "capacity_mw":            float(plant["capacity_mw"]),
        "capacity_factor":        float(plant["capacity_factor"]),
        "total_capex_million":    float(plant["total_capex_million"]),
        "debt_fraction":          float(plant["debt_fraction"]),
        "equity_fraction":        float(plant["equity_fraction"]),
        "operating_years":        int(plant["operating_years"]),
        "useful_life":            int(plant["useful_life"]),
        "discount_rate":          float(plant["discount_rate"]),
        "debt_tenor_years":       debt_tenor,
        "debt_payoff_year":       start_year + debt_tenor - 1,
        "emissions_tco2_per_mwh": float(plant["emissions_tCO2_per_mwh"]),
        "heat_rate_mmbtu_per_mwh":float(plant["heat_rate_mmbtu_mwh"]),
        "power_price_usd_per_mwh":float(plant["power_price_per_mwh"]),
        "rating_spreads":         {k: int(v) for k, v in spreads.items()},
    }

    return {
        "plant":                    plant_out,
        "scenarios":                scenario_comparison,
        "cashflows":                cashflows,
        "ratings":                  yearly_ratings,
        "physical_meta":            physical_meta,
        "climate_scenario_meta":    climate_rows_all,
        "active_physical_channels": active_physical_channels,
    }

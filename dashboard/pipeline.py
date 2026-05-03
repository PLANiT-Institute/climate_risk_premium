"""Cached pipeline wrapper for the Streamlit dashboard.

Calls the src/ modules directly — no HTTP, no JSON serialization.
Results are cached with @st.cache_data so the pipeline only runs once per session.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np
import streamlit as st

# Ensure repo root is importable regardless of working directory
_REPO = Path(__file__).parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.data.loaders import (
    load_model_assumptions,
    load_physical_scenarios,
    load_plant_params,
    load_policy_scenarios,
    load_rating_spreads,
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


@st.cache_data
def run_pipeline(
    risk_mode: str = "all",
    physical_scenario: str = "high_physical",
    outage_hours_override: dict | None = None,
) -> dict:
    """Run all transition scenarios and return results as plain Python dicts/lists.

    Args:
        risk_mode: Which risks to include.  One of:
            ``"all"``        — transition + wildfire physical risk
            ``"transition"`` — transition risk only (no physical)
            ``"wildfire"``   — wildfire physical risk only (no transition policy)
        physical_scenario: Physical risk scenario to use when risk_mode includes
            wildfire.  One of the entries in ``physical_scenarios.csv``
            (baseline / moderate_physical / high_physical / severe_drought).
        outage_hours_override: Optional ``{"plant": h, "transmission": h}``
            overriding default restoration durations from the assumptions CSV.

    Returns
    -------
    dict with keys:
      plant           — plant parameters (dict)
      scenarios       — list of scenario summary dicts
      cashflows       — dict {scenario_name: [row_dict, ...]}
      ratings         — list of year-by-year rating dicts
      physical        — YearlyPhysicalAdjustments or None
      physical_meta   — list of physical scenario dicts from physical_scenarios.csv
    """
    plant = load_plant_params()
    policy_rows = load_policy_scenarios()
    assumptions = load_model_assumptions()
    spreads = load_rating_spreads()

    total_capex = float(plant["total_capex_million"]) * 1e6
    debt_fraction = float(plant["debt_fraction"])
    debt_interest = float(plant["debt_interest_rate"])
    debt_tenor = int(plant["debt_tenor_years"])
    depreciation_years = int(plant["depreciation_years"])
    capacity_mw = float(plant["capacity_mw"])
    base_cf = float(plant["capacity_factor"])
    emissions = float(plant["emissions_tCO2_per_mwh"])
    risk_free = float(plant["risk_free_rate"])
    equity_fraction = float(plant["equity_fraction"])
    start_year = int(assumptions["start_year"])
    base_rate = float(assumptions["base_rate"])
    cash_ratio = float(assumptions["cash_ratio"])
    plant_name = str(plant["plant_name"])

    # Rating scale ordered from best to worst (derived from Rating enum)
    rating_order = [r.name for r in sorted(Rating, key=lambda r: r.value)]

    counterfactual = get_counterfactual_baseline_rating()
    debt_struct = calculate_debt_service(total_capex, debt_fraction, debt_interest, debt_tenor)
    cumulative_principal = debt_struct.principal_schedule.cumsum()

    financing_params = {
        "risk_free_rate": risk_free,
        "debt_fraction": debt_fraction,
        "equity_fraction": equity_fraction,
    }

    # --- Physical risk (built once, shared across all transition scenarios) ---
    physical_meta = load_physical_scenarios()
    max_retirement = max(int(r["retirement_years"]) for r in policy_rows)
    physical_adj: YearlyPhysicalAdjustments | None = None
    if risk_mode in ("all", "wildfire"):
        physical_adj = build_physical_adjustments(
            start_year=start_year,
            n_years=max_retirement,
            physical_scenario=physical_scenario,
            outage_hours_override=outage_hours_override,
        )

    scenario_comparison: list[dict] = []
    cashflows: dict[str, list[dict]] = {}
    yearly_ratings: list[dict] = []

    for row in policy_rows:
        scenario = TransitionScenario.from_policy_row(row)

        yearly_adj = build_yearly_transition_adjustments(
            scenario=scenario,
            base_capacity_factor=base_cf,
            emissions_tco2_per_mwh=emissions,
        )

        # For "wildfire" mode, suppress the transition policy effects by
        # zeroing the dispatch penalty and carbon price
        if risk_mode == "wildfire":
            from src.risk.transition import build_yearly_transition_adjustments as _byta
            from src.scenarios.base import TransitionScenario as _TS
            neutral = _TS(
                name=scenario.name,
                dispatch_penalty=0.0,
                retirement_years=scenario.retirement_years,
                carbon_prices={y: 0.0 for y in scenario.carbon_prices},
                carbon_scenario="none",
                description="wildfire-only (transition suppressed)",
            )
            yearly_adj = _byta(
                scenario=neutral,
                base_capacity_factor=base_cf,
                emissions_tco2_per_mwh=emissions,
            )

        cf_ts = compute_cashflows(
            plant_params=plant,
            yearly_transition_adj=yearly_adj,
            yearly_physical_adj=physical_adj,
        )
        metrics = calculate_metrics(cf_ts, plant)

        avg_ebitda = _float(cf_ts.ebitda.mean())
        avg_interest = _float(cf_ts.interest_expense.mean())
        debt_mid = total_capex * debt_fraction * 0.5
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
        assessment = assess_credit_rating(rating_metrics)
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
        scenario_comparison.append({
            "scenario": scenario.name,
            "description": scenario.description,
            "dispatch_penalty_pct": scenario.dispatch_penalty * 100,
            "retirement_years": scenario.retirement_years,
            "carbon_price_2025": scenario.carbon_prices.get(2025, 0.0),
            "carbon_price_2030": scenario.carbon_prices.get(2030, 0.0),
            "carbon_price_2040": scenario.carbon_prices.get(2040, 0.0),
            "carbon_price_2050": scenario.carbon_prices.get(2050, 0.0),
            "npv_million": _float(metrics.npv / 1e6),
            "irr_pct": _float(metrics.irr * 100),
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
                "revenue": _float(cf_ts.revenue[i]),
                "fuel_costs": _float(cf_ts.fuel_costs[i]),
                "variable_opex": _float(cf_ts.variable_opex[i]),
                "fixed_opex": _float(cf_ts.fixed_opex[i]),
                "carbon_costs": _float(cf_ts.carbon_costs[i]),
                "total_costs": _float(cf_ts.total_costs[i]),
                "ebitda": _float(cf_ts.ebitda[i]),
                "depreciation": _float(cf_ts.depreciation[i]),
                "ebit": _float(cf_ts.ebit[i]),
                "interest_expense": _float(cf_ts.interest_expense[i]),
                "tax_expense": _float(cf_ts.tax_expense[i]),
                "net_income": _float(cf_ts.net_income[i]),
                "free_cash_flow": _float(cf_ts.free_cash_flow[i]),
                "capacity_factor": _float(cf_ts.capacity_factor[i]),
                # None for post-debt years so charts don't draw a false zero line
                "dscr": (
                    None if (dscr_val is None or np.isnan(dscr_val)) else float(dscr_val)
                ),
            })
        cashflows[scenario.name] = cf_rows

        # Year-by-year credit ratings
        for i, year in enumerate(cf_ts.years):
            raw_dscr = cf_ts.dscr[i]
            dscr_i = float(raw_dscr) if (raw_dscr is not None and not np.isnan(raw_dscr)) else None
            ebitda_i = _float(cf_ts.ebitda[i])
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
                # Cash buffer: fraction of EBITDA loaded from model_assumptions
                cash_and_equivalents=max(0.0, ebitda_i * cash_ratio),
                total_equity=total_equity_i,
                total_assets=total_assets_i if total_assets_i > 0 else total_capex,
                dscr=dscr_i,
            )
            yr_assessment = assess_credit_rating(rm)
            rating_str = yr_assessment.overall_rating.name

            # Post-debt DSCR is None (no debt service → metric N/A)
            if dscr_i is not None:
                if dscr_i < 0:
                    rating_str = "D"
                elif dscr_i < 1.0:
                    idx = rating_order.index(rating_str)
                    rating_str = rating_order[min(idx + 1, len(rating_order) - 1)]

            spread = spreads.get(rating_str, spreads.get("CCC", 900))
            yearly_ratings.append({
                "scenario": scenario.name,
                "year": int(year),
                "dscr": round(dscr_i, 3) if dscr_i is not None else None,
                "rating": rating_str,
                "spread_bps": spread,
                "cost_of_debt": round(base_rate + spread / 10000, 6),
                "ebitda": round(ebitda_i / 1e6, 2),
            })

    plant_out = {
        "name": plant_name,
        "capacity_mw": float(plant["capacity_mw"]),
        "capacity_factor": float(plant["capacity_factor"]),
        "total_capex_million": float(plant["total_capex_million"]),
        "debt_fraction": float(plant["debt_fraction"]),
        "equity_fraction": float(plant["equity_fraction"]),
        "operating_years": int(plant["operating_years"]),
        "useful_life": int(plant["useful_life"]),
        "discount_rate": float(plant["discount_rate"]),
        "debt_tenor_years": debt_tenor,
        "debt_payoff_year": start_year + debt_tenor - 1,
        "emissions_tco2_per_mwh": float(plant["emissions_tCO2_per_mwh"]),
        "heat_rate_mmbtu_per_mwh": float(plant["heat_rate_mmbtu_mwh"]),
        "power_price_usd_per_mwh": float(plant["power_price_per_mwh"]),
        # Pass rating spread map to UI so it can render without hardcoding
        "rating_spreads": {k: int(v) for k, v in spreads.items()},
    }

    # Serialise physical adjustments for the dashboard physical risk page
    physical_out: dict | None = None
    if physical_adj is not None:
        physical_out = {
            "scenario": physical_adj.scenario_name,
            "years": physical_adj.years.tolist(),
            "plant_outage_rate": physical_adj.outage_rates.tolist(),
            "transmission_outage_rate": physical_adj.transmission_outage_rates.tolist(),
            "capacity_derate": physical_adj.capacity_derates.tolist(),
            "efficiency_loss": physical_adj.efficiency_losses.tolist(),
            "water_constrained_capacity": physical_adj.water_constraints.tolist(),
            "asset_capex_loss_rate": physical_adj.asset_capex_loss_rates.tolist(),
        }

    return {
        "plant": plant_out,
        "scenarios": scenario_comparison,
        "cashflows": cashflows,
        "ratings": yearly_ratings,
        "physical": physical_out,
        "physical_meta": physical_meta,
    }

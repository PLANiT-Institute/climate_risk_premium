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

from src.data.loaders import load_plant_params, load_policy_scenarios
from src.scenarios.base import TransitionScenario
from src.risk.transition import build_yearly_transition_adjustments
from src.financials.cashflow import compute_cashflows
from src.financials.metrics import calculate_metrics, calculate_debt_service
from src.risk.credit_rating import (
    calculate_rating_metrics_from_financials,
    assess_credit_rating,
    get_counterfactual_baseline_rating,
    calculate_crp_from_ratings,
)
from src.risk.financing import calculate_financing_with_counterfactual


def _float(v: Any) -> float:
    """Cast numpy scalar → plain Python float, safe for display."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return 0.0
    return float(v)


@st.cache_data
def run_pipeline() -> dict:
    """Run all scenarios and return results as plain Python dicts/lists.

    Returns
    -------
    dict with keys:
      plant      — plant parameters (dict)
      scenarios  — list of scenario summary dicts
      cashflows  — dict {scenario_name: [row_dict, ...]}
      ratings    — list of year-by-year rating dicts
    """
    plant = load_plant_params()
    policy_rows = load_policy_scenarios()

    total_capex = float(plant["total_capex_million"]) * 1e6
    debt_fraction = float(plant["debt_fraction"])
    debt_interest = float(plant["debt_interest_rate"])
    debt_tenor = int(plant["debt_tenor_years"])
    depreciation_years = int(plant["depreciation_years"])
    capacity_mw = float(plant["capacity_mw"])
    base_cf = float(plant["capacity_factor"])
    emissions = float(
        plant.get("emissions_tCO2_per_mwh", plant.get("emissions_tco2_per_mwh", 0.82))
    )
    risk_free = float(plant.get("risk_free_rate", 0.035))
    equity_fraction = float(plant["equity_fraction"])

    counterfactual = get_counterfactual_baseline_rating()
    debt_struct = calculate_debt_service(total_capex, debt_fraction, debt_interest, debt_tenor)
    cumulative_principal = debt_struct.principal_schedule.cumsum()

    RATING_ORDER = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "CC", "C", "D"]
    SPREAD_MAP: dict[str, int] = {
        "AAA": 50, "AA": 100, "A": 150, "BBB": 250,
        "BB": 400, "B": 600, "CCC": 900, "CC": 1500, "C": 2500, "D": 5000,
    }
    BASE_RATE = 0.0675

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
        cf_ts = compute_cashflows(plant_params=plant, yearly_transition_adj=yearly_adj)
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
            params={
                "risk_free_rate": risk_free,
                "debt_fraction": debt_fraction,
                "equity_fraction": equity_fraction,
            },
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
            "payback_years": _float(metrics.payback_years) if metrics.payback_years is not None else None,
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
                "dscr": None if (dscr_val is None or np.isnan(dscr_val)) else float(dscr_val),
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
                principal_i = _float(debt_struct.principal_schedule[i])
                debt_svc_i = interest_i + principal_i
            else:
                debt_out = 0.0
                debt_svc_i = 0.0

            fixed_assets_i = total_capex * max(0.0, 1 - i / depreciation_years)
            total_equity_i = max(0.0, fixed_assets_i - debt_out)
            total_assets_i = max(fixed_assets_i, debt_out)

            rm = calculate_rating_metrics_from_financials(
                capacity_mw=capacity_mw,
                ebitda=ebitda_i,
                fixed_assets=total_assets_i if total_assets_i > 0 else total_capex,
                interest_expense=interest_i,
                total_debt=debt_out,
                cash_and_equivalents=max(0.0, ebitda_i * 0.1),
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
                    idx = RATING_ORDER.index(rating_str)
                    rating_str = RATING_ORDER[min(idx + 1, len(RATING_ORDER) - 1)]

            spread = SPREAD_MAP.get(rating_str, 900)
            yearly_ratings.append({
                "scenario": scenario.name,
                "year": int(year),
                "dscr": round(dscr_i, 3) if dscr_i is not None else None,
                "rating": rating_str,
                "spread_bps": spread,
                "cost_of_debt": round(BASE_RATE + spread / 10000, 6),
                "ebitda": round(ebitda_i / 1e6, 2),
            })

    plant_out = {
        "name": "Samcheok Blue Power",
        "capacity_mw": float(plant["capacity_mw"]),
        "capacity_factor": float(plant["capacity_factor"]),
        "total_capex_million": float(plant["total_capex_million"]),
        "debt_fraction": float(plant["debt_fraction"]),
        "equity_fraction": float(plant["equity_fraction"]),
        "operating_years": int(plant["operating_years"]),
        "useful_life": int(plant["useful_life"]),
        "discount_rate": float(plant["discount_rate"]),
        "debt_tenor_years": debt_tenor,
        "debt_payoff_year": 2025 + debt_tenor - 1,   # last year with debt service
        "emissions_tco2_per_mwh": float(
            plant.get("emissions_tCO2_per_mwh", plant.get("emissions_tco2_per_mwh", 0.82))
        ),
        "heat_rate_mmbtu_per_mwh": float(plant.get("heat_rate_mmbtu_per_mwh", 8.8)),
        "power_price_usd_per_mwh": float(plant.get("power_price_usd_per_mwh", 80)),
    }

    return {
        "plant": plant_out,
        "scenarios": scenario_comparison,
        "cashflows": cashflows,
        "ratings": yearly_ratings,
    }

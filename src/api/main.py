"""FastAPI backend — serves transition risk pipeline results as JSON.

Runs the full pipeline for all policy scenarios on startup, caches results
in memory, and exposes them via REST endpoints.  The Next.js frontend fetches
from these endpoints at request time — no pre-generated TypeScript files.

Endpoints
---------
GET /api/plant          → plant parameters dict
GET /api/scenarios      → list of ScenarioResult objects
GET /api/cashflows      → dict {scenario: [CashflowRow, ...]}
GET /api/cashflows/{s}  → list of CashflowRow for one scenario
GET /api/ratings        → list of CreditRatingRow (year-by-year)
GET /api/health         → {"status": "ok"}
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import numpy_financial as npf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Make repo root importable when run directly
_REPO = Path(__file__).parent.parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.data.loaders import load_plant_params, load_policy_scenarios
from src.scenarios.base import TransitionScenario
from src.risk.transition import build_yearly_transition_adjustments
from src.risk.credit_rating import (
    Rating,
    calculate_rating_metrics_from_financials,
    assess_credit_rating,
    get_counterfactual_baseline_rating,
    calculate_crp_from_ratings,
    assess_rating_with_counterfactual,
)
from src.risk.financing import calculate_financing_with_counterfactual
from src.financials.cashflow import compute_cashflows
from src.financials.metrics import calculate_metrics, calculate_debt_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(title="CRP API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory cache — populated at startup
# ---------------------------------------------------------------------------

_cache: Dict[str, Any] = {}


def _float(v: Any) -> float:
    """Cast numpy scalar → plain Python float, safe for JSON."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return 0.0
    return float(v)


def _build_cache() -> None:
    plant = load_plant_params()
    policy_rows = load_policy_scenarios()
    total_capex = float(plant["total_capex_million"]) * 1e6
    debt_fraction = float(plant["debt_fraction"])
    debt_interest = float(plant["debt_interest_rate"])
    debt_tenor = int(plant["debt_tenor_years"])
    depreciation_years = int(plant["depreciation_years"])
    capacity_mw = float(plant["capacity_mw"])
    base_cf = float(plant["capacity_factor"])
    emissions = float(plant.get("emissions_tCO2_per_mwh", plant.get("emissions_tco2_per_mwh", 0.82)))
    risk_free = float(plant.get("risk_free_rate", 0.035))
    equity_fraction = float(plant["equity_fraction"])

    counterfactual = get_counterfactual_baseline_rating()
    debt_struct = calculate_debt_service(total_capex, debt_fraction, debt_interest, debt_tenor)
    cumulative_principal = debt_struct.principal_schedule.cumsum()

    scenario_comparison: List[Dict] = []
    cashflows: Dict[str, List[Dict]] = {}
    yearly_ratings: List[Dict] = []

    for row in policy_rows:
        scenario = TransitionScenario.from_policy_row(row)
        logger.info("Building cache for: %s", scenario.name)

        yearly_adj = build_yearly_transition_adjustments(
            scenario=scenario,
            base_capacity_factor=base_cf,
            emissions_tco2_per_mwh=emissions,
        )
        cf_ts = compute_cashflows(plant_params=plant, yearly_transition_adj=yearly_adj)
        metrics = calculate_metrics(cf_ts, plant)

        # --- Scenario-level credit rating (average EBITDA) ---
        avg_ebitda = float(cf_ts.ebitda.mean())
        avg_interest = float(cf_ts.interest_expense.mean())
        debt_mid = total_capex * debt_fraction * 0.5  # midlife balance
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

        # Financing impact (for WACC spread reporting)
        counterfactual_npv = 0.0  # placeholder; CRP is rating-driven not NPV-driven
        scenario_npv_loss = max(0.0, counterfactual_npv - metrics.npv)
        params = {
            "risk_free_rate": risk_free,
            "debt_fraction": debt_fraction,
            "equity_fraction": equity_fraction,
        }
        financing = calculate_financing_with_counterfactual(
            scenario_spread_bps=scenario_rating.to_spread_bps(),
            counterfactual_spread_bps=counterfactual.to_spread_bps(),
            npv_loss=scenario_npv_loss,
            total_capex=total_capex,
            params=params,
            scenario_notch=scenario_rating.value,
            counterfactual_notch=counterfactual.value,
        )

        rd = assessment.to_dict()
        scenario_comparison.append({
            "scenario": scenario.name,
            "npv_million": _float(metrics.npv / 1e6),
            "irr_pct": _float(metrics.irr * 100),
            "avg_dscr": _float(metrics.avg_dscr),
            "min_dscr": _float(metrics.min_dscr),
            "llcr": _float(metrics.llcr),
            "payback_years": _float(metrics.payback_years) if metrics.payback_years is not None else None,
            "expected_loss_pct": _float(financing.expected_loss_pct),
            "npv_loss_million": _float(financing.npv_loss_million),
            "debt_spread_bps": _float(financing.debt_spread_bps),
            "equity_premium_pct": _float(financing.equity_premium_pct),
            "crp_bps": _float(crp_bps),
            "climate_risk_premium_bps": _float(crp_bps),
            "wacc_baseline_pct": _float(financing.wacc_baseline_pct),
            "wacc_adjusted_pct": _float(financing.wacc_adjusted_pct),
            "overall_rating": rd["overall_rating"],
            "rating_numeric": rd["rating_numeric"],
            "spread_bps": rd["spread_bps"],
            "is_investment_grade": rd["is_investment_grade"],
            "is_distressed": rd["is_distressed"],
            "capacity_rating": "AA",  # per KIS methodology: 2100MW → AAA but capped at AA in rating grid
            "profitability_rating": rd["profitability_rating"],
            "coverage_rating": rd["coverage_rating"],
            "dscr_rating": rd["dscr_rating"],
            "net_debt_leverage_rating": rd["net_debt_leverage_rating"],
            "equity_leverage_rating": rd["equity_leverage_rating"],
            "asset_leverage_rating": rd["asset_leverage_rating"],
            "capacity_mw": rd["capacity_mw"],
            "ebitda_to_fixed_assets": rd["ebitda_to_fixed_assets"],
            "ebitda_to_interest": rd["ebitda_to_interest"],
            "dscr": rd["dscr"],
            "net_debt_to_ebitda": rd["net_debt_to_ebitda"],
            "debt_to_equity": rd["debt_to_equity"],
            "debt_to_assets": rd["debt_to_assets"],
            "is_ebitda_negative": rd["is_ebitda_negative"],
            "rating_rationale": rd["rating_rationale"],
            "counterfactual_rating": str(counterfactual),
            "counterfactual_spread_bps": counterfactual.to_spread_bps(),
            "scenario_rating_new": str(scenario_rating),
            "scenario_spread_bps_new": scenario_rating.to_spread_bps(),
            "rating_migration": f"Downgrade by {notch_change} notch(es)" if notch_change > 0
                               else ("No change" if notch_change == 0
                               else f"Upgrade by {abs(notch_change)} notch(es)"),
            "notch_change": notch_change,
            "counterfactual_crp_bps": _float(crp_bps),
        })

        # --- Per-year cashflow rows ---
        cf_rows: List[Dict] = []
        for i, year in enumerate(cf_ts.years):
            cf_rows.append({
                "scenario": scenario.name,
                "year": int(year),
                "revenue": _float(cf_ts.revenue[i]),
                "fuel_costs": _float(cf_ts.fuel_costs[i]),
                "variable_opex": _float(cf_ts.variable_opex[i]),
                "fixed_opex": _float(cf_ts.fixed_opex[i]),
                "outage_costs": 0.0,  # transition-only; physical risk not included yet
                "carbon_costs": _float(cf_ts.carbon_costs[i]),
                "total_costs": _float(cf_ts.total_costs[i]),
                "ebitda": _float(cf_ts.ebitda[i]),
                "depreciation": _float(cf_ts.depreciation[i]),
                "ebit": _float(cf_ts.ebit[i]),
                "interest_expense": _float(cf_ts.interest_expense[i]),
                "tax_expense": _float(cf_ts.tax_expense[i]),
                "net_income": _float(cf_ts.net_income[i]),
                "capex": 0.0,
                "free_cash_flow": _float(cf_ts.free_cash_flow[i]),
                "capacity_factor": _float(cf_ts.capacity_factor[i]),
                "dscr": _float(cf_ts.dscr[i]),
            })
        cashflows[scenario.name] = cf_rows

        # --- Year-by-year credit ratings ---
        RATING_ORDER = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "CC", "C", "D"]
        BASE_RATE = 0.0675
        SPREAD_MAP = {
            "AAA": 50, "AA": 100, "A": 150, "BBB": 250,
            "BB": 400, "B": 600, "CCC": 900, "CC": 1500, "C": 2500, "D": 5000,
        }

        for i, year in enumerate(cf_ts.years):
            dscr_i = _float(cf_ts.dscr[i])
            ebitda_i = _float(cf_ts.ebitda[i])
            interest_i = _float(cf_ts.interest_expense[i])

            if i < debt_tenor:
                debt_out = total_capex * debt_fraction - (_float(cumulative_principal[i - 1]) if i > 0 else 0.0)
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

            if dscr_i < 0:
                rating_str = "D"
            elif dscr_i < 1.0 and dscr_i >= 0:
                idx = RATING_ORDER.index(rating_str)
                rating_str = RATING_ORDER[min(idx + 1, len(RATING_ORDER) - 1)]

            spread = SPREAD_MAP.get(rating_str, 900)
            yearly_ratings.append({
                "scenario": scenario.name,
                "display_name": scenario.name.replace("_", " ").title(),
                "year": int(year),
                "dscr": round(dscr_i, 3),
                "rating": rating_str,
                "spread_bps": spread,
                "cost_of_debt": round(BASE_RATE + spread / 10000, 6),
                "ebitda": round(ebitda_i, 2),
                "debt_service": round(debt_svc_i, 2),
            })

    _cache["plant"] = {
        "name": "Samcheok Blue Power",
        "capacity_mw": float(plant["capacity_mw"]),
        "capacity_factor": float(plant["capacity_factor"]),
        "total_capex_million": float(plant["total_capex_million"]),
        "debt_fraction": float(plant["debt_fraction"]),
        "equity_fraction": float(plant["equity_fraction"]),
        "operating_years": int(plant["operating_years"]),
        "useful_life": int(plant["useful_life"]),
        "discount_rate": float(plant["discount_rate"]),
    }
    _cache["scenarios"] = scenario_comparison
    _cache["cashflows"] = cashflows
    _cache["ratings"] = yearly_ratings
    logger.info("Cache built: %d scenarios, %d rating rows", len(scenario_comparison), len(yearly_ratings))


@app.on_event("startup")
def startup():
    _build_cache()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok", "scenarios": len(_cache.get("scenarios", []))}


@app.get("/api/plant")
def get_plant():
    return _cache.get("plant", {})


@app.get("/api/scenarios")
def get_scenarios():
    return _cache.get("scenarios", [])


@app.get("/api/cashflows")
def get_all_cashflows():
    return _cache.get("cashflows", {})


@app.get("/api/cashflows/{scenario}")
def get_cashflows(scenario: str):
    cf = _cache.get("cashflows", {}).get(scenario)
    if cf is None:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario}' not found")
    return cf


@app.get("/api/ratings")
def get_ratings():
    return _cache.get("ratings", [])

#!/usr/bin/env python3
"""
Regenerate dashboard TypeScript data from the Python model.

Runs CRPModelRunner and writes all results as TypeScript constants directly
into crp-dashboard/src/lib/generated/data.ts — no JSON intermediate files.

Usage:
    python3 scripts/regenerate_dashboard_data.py
"""

import csv
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.runner import CRPModelRunner
from src.financials import calculate_debt_service
from src.risk import assess_credit_rating, calculate_rating_metrics_from_financials


RATING_SPREAD_MAP = {
    "AAA": 50, "AA": 100, "A": 150, "BBB": 250,
    "BB": 400, "B": 600, "CCC": 900, "CC": 1500, "C": 2500, "D": 5000,
}

SCENARIO_DISPLAY = {
    "baseline": "Baseline",
    "moderate_transition": "Moderate Transition",
    "aggressive_transition": "Aggressive Transition",
    "moderate_physical": "Moderate Physical",
    "high_physical": "High Physical",
    "combined_moderate": "Combined Moderate",
    "combined_aggressive": "Combined Aggressive",
    "low_demand": "Low Demand",
    "severe_drought": "Severe Drought",
    "enhanced_11th_plan": "Enhanced 11th Plan",
    "enhanced_combined": "Enhanced Combined",
}

BASE_RATE = 0.0675

# Maps the three dashboard display scenarios to (climate_factors_scenario, year)
DISPLAY_SCENARIO_MAP = {
    "baseline":    ("SSP1-2.6", 2024),
    "ssp126_2040": ("SSP1-2.6", 2040),
    "ssp585_2050": ("SSP5-8.5", 2050),
}

# Maps hazard type to the hazard_baselines.csv row and climate_factors.csv column
HAZARD_MAP = {
    "wildfire":  ("wildfire",       "wildfire"),
    "drought":   ("drought",        "drought"),
    "waterRisk": ("coastal_flood",  "coastal_flood"),
}


def load_climate_factors(project_root: Path) -> dict:
    """Load climate_factors.csv as {(scenario, year): {hazard: factor}}."""
    path = project_root / "data" / "physical" / "climate_factors.csv"
    cols = ["wildfire", "tropical_cyclone", "river_flood", "coastal_flood", "drought", "heat_stress"]
    factors = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            key = (row["scenario"], int(row["year"]))
            factors[key] = {c: float(row.get(c, 1.0)) for c in cols}
    return factors


def load_hazard_baselines(project_root: Path) -> dict:
    """Load hazard_baselines.csv as {hazard_type: {col: float, ...}}."""
    path = project_root / "data" / "physical" / "hazard_baselines.csv"
    baselines = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            baselines[row["hazard_type"]] = {
                "base_frequency": float(row["base_frequency"]),
                "outage_rate":    float(row["outage_rate"]),
                "capacity_derate": float(row["capacity_derate"]),
                "efficiency_loss": float(row["efficiency_loss"]),
                "damage_ratio":   float(row["damage_ratio"]),
            }
    return baselines


def load_transmission_params(project_root: Path) -> dict:
    """Load transmission.csv {param: value}."""
    path = project_root / "data" / "raw" / "transmission.csv"
    if not path.exists():
        return {}
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                out[row["param_name"]] = float(row["value"])
            except (ValueError, KeyError):
                pass
    return out


def interpolate_factor(factors: dict, scenario: str, year: int, hazard_col: str) -> float:
    """Linearly interpolate a climate factor for a given scenario and year."""
    available = sorted(
        (y for (s, y) in factors if s == scenario),
    )
    if not available:
        return 1.0
    if year <= available[0]:
        return factors[(scenario, available[0])][hazard_col]
    if year >= available[-1]:
        return factors[(scenario, available[-1])][hazard_col]
    # Linear interpolation between surrounding anchor years
    for i in range(len(available) - 1):
        y0, y1 = available[i], available[i + 1]
        if y0 <= year <= y1:
            f0 = factors[(scenario, y0)][hazard_col]
            f1 = factors[(scenario, y1)][hazard_col]
            t = (year - y0) / (y1 - y0)
            return f0 + t * (f1 - f0)
    return 1.0


def calculate_scenario_risks(project_root: Path) -> dict:
    """Compute the SCENARIO_RISKS summary surfaced on the physical-risk page.

    Six channels, each in fraction-of-year units (or fraction-of-CF for derate):
        wildfire     — plant outage from direct fire damage
        drought      — capacity derate from cooling water shortage
        heat         — efficiency loss from heat stress
        transmission — line outage (wildfire + typhoon + heat-sag + sub flood)
        capex_loss   — annual fraction of total replacement value destroyed
        total        — sum (rough magnitude indicator)

    All channels derived from data/physical/hazard_baselines.csv,
    data/physical/climate_factors.csv, and data/raw/transmission.csv.
    """
    factors = load_climate_factors(project_root)
    baselines = load_hazard_baselines(project_root)
    line_params = load_transmission_params(project_root)

    wf = baselines.get("wildfire", {})
    tc = baselines.get("tropical_cyclone", {})
    dr = baselines.get("drought", {})
    hs = baselines.get("heat_stress", {})
    cfd = baselines.get("coastal_flood", {})

    plant_wf_p = 0.10
    plant_wf_dur = 24.0

    def _outage(freq, p, dur):
        return max(0.0, freq) * max(0.0, min(1.0, p)) * max(0.0, dur) / 8760.0

    result = {}
    for display_key, (cf_scenario, year) in DISPLAY_SCENARIO_MAP.items():
        f_wf   = interpolate_factor(factors, cf_scenario, year, "wildfire")
        f_tc   = interpolate_factor(factors, cf_scenario, year, "tropical_cyclone") if "tropical_cyclone" in next(iter(factors.values()), {}) else f_wf
        f_dr   = interpolate_factor(factors, cf_scenario, year, "drought")
        f_hs   = interpolate_factor(factors, cf_scenario, year, "heat_stress")
        f_flood = interpolate_factor(factors, cf_scenario, year, "coastal_flood")

        # Plant outage: wildfire + tropical cyclone direct hits
        plant = _outage(wf.get("base_frequency", 0) * f_wf, plant_wf_p, plant_wf_dur)
        plant += tc.get("outage_rate", 0) * f_tc

        # Drought capacity derate, heat stress efficiency loss
        drought = dr.get("capacity_derate", 0) * f_dr
        heat = hs.get("efficiency_loss", 0) * f_hs

        # Transmission outage: wildfire/typhoon/heat on line + flood on substation
        wf_freq_line = wf.get("base_frequency", 0) * f_wf
        tc_freq_line = tc.get("base_frequency", 0) * f_tc
        heat_freq    = hs.get("base_frequency", 0) * f_hs
        flood_freq   = cfd.get("base_frequency", 0) * f_flood
        transmission = (
            _outage(wf_freq_line, line_params.get("line_wildfire_outage_probability", 0.20),
                    line_params.get("line_wildfire_outage_duration_hours", 12))
            + _outage(tc_freq_line, line_params.get("line_typhoon_outage_probability", 0.30),
                      line_params.get("line_typhoon_outage_duration_hours", 8))
            + _outage(heat_freq, line_params.get("line_heat_sag_probability", 0.05),
                      line_params.get("line_heat_sag_duration_hours", 2))
            + _outage(flood_freq, line_params.get("substation_flood_outage_probability", 0.40),
                      line_params.get("substation_flood_outage_duration_hours", 72))
        )

        # Annual capex destruction (plant damage_ratio + line annual fraction)
        capex_loss = (
            wf.get("damage_ratio", 0) * wf.get("base_frequency", 0) * f_wf
            + tc.get("damage_ratio", 0) * tc.get("base_frequency", 0) * f_tc
            + line_params.get("line_annual_damage_fraction", 0) * f_wf
        )

        plant = round(plant, 6)
        drought = round(drought, 6)
        heat = round(heat, 6)
        transmission = round(transmission, 6)
        capex_loss = round(capex_loss, 6)
        total = round(plant + drought + heat + transmission + capex_loss, 6)

        result[display_key] = {
            "wildfire":     plant,
            "drought":      drought,
            "heat":         heat,
            "transmission": transmission,
            "capexLoss":    capex_loss,
            "waterRisk":    0.0,  # legacy field for backward compat with frontend
            "total":        total,
        }
    return result


def build_yearly_ratings(results: dict, plant_params: dict) -> list:
    """Build yearly credit rating rows — same logic as before but returns Python list."""
    total_capex = float(plant_params["total_capex_million"]) * 1e6
    debt_fraction = float(plant_params["debt_fraction"])
    debt_rate = float(plant_params["debt_interest_rate"])
    debt_tenor = int(plant_params["debt_tenor_years"])
    depreciation_years = int(plant_params["depreciation_years"])
    capacity_mw = float(plant_params["capacity_mw"])

    debt_struct = calculate_debt_service(total_capex, debt_fraction, debt_rate, debt_tenor)
    cumulative_principal = debt_struct.principal_schedule.cumsum()

    RATING_ORDER = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "CC", "C", "D"]
    rows = []

    for scenario_name, result in results.items():
        if result.cashflow is None:
            continue
        cf = result.cashflow
        display_name = SCENARIO_DISPLAY.get(scenario_name, scenario_name)

        for i, year in enumerate(cf.years):
            dscr_i   = float(cf.dscr[i]) if i < len(cf.dscr) else 0.0
            ebitda   = float(cf.ebitda[i]) if i < len(cf.ebitda) else 0.0
            interest = float(cf.interest_expense[i]) if i < len(cf.interest_expense) else 0.0

            if i < debt_tenor:
                debt_out = total_capex * debt_fraction - (cumulative_principal[i - 1] if i > 0 else 0.0)
                # Full debt service = interest + scheduled principal repayment
                principal_this_year = float(debt_struct.principal_schedule[i])
                full_debt_svc = interest + principal_this_year
            else:
                debt_out = 0.0
                full_debt_svc = 0.0

            fixed_assets = total_capex * max(0.0, 1 - i / depreciation_years)
            total_equity = max(0.0, fixed_assets - debt_out)
            total_assets = max(fixed_assets, debt_out)

            rating_metrics = calculate_rating_metrics_from_financials(
                capacity_mw=capacity_mw, ebitda=ebitda, fixed_assets=total_assets,
                interest_expense=interest, total_debt=debt_out,
                cash_and_equivalents=max(0.0, ebitda * 0.1),
                total_equity=total_equity, total_assets=total_assets, dscr=dscr_i,
            )
            assessment = assess_credit_rating(rating_metrics)
            rating = assessment.overall_rating.name

            spread_bps = RATING_SPREAD_MAP.get(rating, 900)

            rows.append({
                "scenario":     scenario_name,
                "display_name": display_name,
                "year":         int(year),
                "dscr":         round(dscr_i, 3),
                "rating":       rating,
                "spread_bps":   spread_bps,
                "cost_of_debt": round(BASE_RATE + spread_bps / 10000, 6),
                "ebitda":       round(ebitda, 2),
                "debt_service": round(full_debt_svc, 2),
            })

    return rows


def build_scenario_comparison(results: dict) -> list:
    """Build scenario comparison rows from runner results."""
    rows = []
    for name, result in results.items():
        row = {"scenario": name}
        row.update(result.metrics.to_dict())
        if result.financing:
            row.update(result.financing.to_dict())
        if result.credit_rating:
            row.update(result.credit_rating.to_dict())
        if result.counterfactual_crp:
            crp = result.counterfactual_crp
            row["counterfactual_rating"]    = crp.get("counterfactual_rating")
            row["counterfactual_spread_bps"]= crp.get("counterfactual_spread_bps")
            row["scenario_rating_new"]      = crp.get("scenario_rating")
            row["scenario_spread_bps_new"]  = crp.get("scenario_spread_bps")
            row["rating_migration"]         = crp.get("rating_migration")
            row["notch_change"]             = crp.get("notch_change")
            row["counterfactual_crp_bps"]   = crp.get("crp_bps")
            row["is_investment_grade"]      = crp.get("is_investment_grade")
            row["is_distressed"]            = crp.get("is_distressed")
        rows.append(row)
    return rows


def build_cashflows(results: dict) -> dict:
    """Build cashflow dict keyed by scenario name."""
    cashflows = {}
    for name, result in results.items():
        if result.cashflow is None:
            continue
        cf = result.cashflow
        rows = []
        for i, year in enumerate(cf.years):
            rows.append({
                "scenario":                    name,
                "year":                        int(year),
                "revenue":                     float(cf.revenue[i]),
                "fuel_costs":                  float(cf.fuel_costs[i]),
                "variable_opex":               float(cf.variable_opex[i]),
                "fixed_opex":                  float(cf.fixed_opex[i]),
                "outage_costs":                float(cf.outage_costs[i]) if hasattr(cf, "outage_costs") else float(cf.lost_revenue_from_outages[i]) if hasattr(cf, "lost_revenue_from_outages") else 0.0,
                "total_costs":                 float(cf.total_costs[i]),
                "ebitda":                      float(cf.ebitda[i]),
                "depreciation":                float(cf.depreciation[i]),
                "ebit":                        float(cf.ebit[i]),
                "interest_expense":            float(cf.interest_expense[i]),
                "tax_expense":                 float(cf.tax_expense[i]),
                "net_income":                  float(cf.net_income[i]),
                "capex":                       float(cf.capex[i]) if hasattr(cf, "capex") else 0.0,
                "free_cash_flow":              float(cf.free_cash_flow[i]),
                "capacity_factor":             float(cf.capacity_factor[i]) if hasattr(cf, "capacity_factor") else float(cf.final_cf[i]),
                "carbon_costs":                float(cf.carbon_costs[i]) if hasattr(cf, "carbon_costs") else 0.0,
                "dscr":                        float(cf.dscr[i]) if hasattr(cf, "dscr") else 0.0,
            })
        cashflows[name] = rows
    return cashflows


def _ts_value(v) -> str:
    """Format a Python value as a TypeScript literal."""
    if v is None:
        return "null"
    # bool must come before int (bool is a subclass of int)
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        escaped = v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'
    # Cast to plain Python float/int first — np.float64 repr() writes 'np.float64(x)'
    if isinstance(v, float):
        return repr(float(v))
    if isinstance(v, int):
        return repr(int(v))
    # numpy integer types (np.int64 is not a subclass of int in Python 3)
    try:
        import numpy as np
        if isinstance(v, np.integer):
            return repr(int(v))
        if isinstance(v, np.floating):
            return repr(float(v))
        if isinstance(v, np.bool_):
            return "true" if bool(v) else "false"
    except ImportError:
        pass
    raise TypeError(f"Unsupported type: {type(v)}")


def _ts_object(obj: dict, indent: int = 2) -> str:
    pad = " " * indent
    inner_pad = " " * (indent + 2)
    lines = ["{"]
    for k, v in obj.items():
        lines.append(f"{inner_pad}{k}: {_ts_value(v)},")
    lines.append(f"{pad}}}")
    return "\n".join(lines)


def generate_typescript(
    scenario_comparison: list,
    yearly_ratings: list,
    cashflows: dict,
    scenario_risks: dict,
    plant_params: dict,
    output_path: Path,
) -> None:
    """Write all data as TypeScript constants to a single file."""
    lines = [
        "// AUTO-GENERATED by scripts/regenerate_dashboard_data.py",
        "// DO NOT EDIT MANUALLY — run: python scripts/regenerate_dashboard_data.py",
        "",
        'import type { ScenarioResult, CreditRatingRow, CashflowRow } from "@/lib/types";',
        'import type { HazardRisk, RiskScenario } from "@/lib/geo/types";',
        "",
    ]

    # PLANT — input parameters surfaced for display
    plant_export = {
        "name": "Samcheok Blue Power",
        "capacity_mw": float(plant_params["capacity_mw"]),
        "capacity_factor": float(plant_params["capacity_factor"]),
        "total_capex_million": float(plant_params["total_capex_million"]),
        "debt_fraction": float(plant_params["debt_fraction"]),
        "equity_fraction": float(plant_params["equity_fraction"]),
        "operating_years": int(plant_params["operating_years"]),
        "useful_life": int(plant_params["useful_life"]),
        "discount_rate": float(plant_params["discount_rate"]),
    }
    lines.append(f"export const PLANT = {_ts_object(plant_export, indent=0)} as const;")
    lines.append("")

    # SCENARIO_COMPARISON
    lines.append("export const SCENARIO_COMPARISON: ScenarioResult[] = [")
    for row in scenario_comparison:
        lines.append(f"  {_ts_object(row, indent=2)},")
    lines.append("] as const as unknown as ScenarioResult[];")
    lines.append("")

    # YEARLY_RATINGS
    lines.append("export const YEARLY_RATINGS: CreditRatingRow[] = [")
    for row in yearly_ratings:
        lines.append(f"  {_ts_object(row, indent=2)},")
    lines.append("] as const as unknown as CreditRatingRow[];")
    lines.append("")

    # CASHFLOWS
    lines.append("export const CASHFLOWS: Record<string, CashflowRow[]> = {")
    for scenario, rows in cashflows.items():
        lines.append(f'  "{scenario}": [')
        for row in rows:
            lines.append(f"    {_ts_object(row, indent=4)},")
        lines.append("  ],")
    lines.append("};")
    lines.append("")

    # SCENARIO_RISKS — six channels per scenario
    lines.append("export const SCENARIO_RISKS: Record<RiskScenario, HazardRisk> = {")
    for key, vals in scenario_risks.items():
        lines.append(
            f"  {key}: {{ "
            f"wildfire: {vals['wildfire']}, "
            f"drought: {vals['drought']}, "
            f"heat: {vals['heat']}, "
            f"transmission: {vals['transmission']}, "
            f"capexLoss: {vals['capexLoss']}, "
            f"waterRisk: {vals['waterRisk']}, "
            f"total: {vals['total']} "
            f"}},"
        )
    lines.append("};")
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Written: {output_path.relative_to(PROJECT_ROOT)}")


def main():
    print("=" * 60)
    print("CRP Dashboard Data Regeneration")
    print("=" * 60)

    print("\n1. Initializing CRPModelRunner...")
    runner = CRPModelRunner(PROJECT_ROOT)

    print("\n2. Running all scenarios...")
    results = runner.run_multi_scenario()
    for name in results:
        print(f"   - {name}")

    print("\n3. Exporting CSV results (for paper/analysis)...")
    processed_dir = PROJECT_ROOT / "data" / "processed"
    runner.export_results(results, processed_dir)

    plant_params = runner._get_plant_params()

    print("\n4. Calculating SCENARIO_RISKS from source data (no hardcoding)...")
    scenario_risks = calculate_scenario_risks(PROJECT_ROOT)
    for k, v in scenario_risks.items():
        print(f"   {k}: wildfire={v['wildfire']}, drought={v['drought']}, waterRisk={v['waterRisk']}")

    print("\n5. Building TypeScript data...")
    scenario_comparison = build_scenario_comparison(results)
    yearly_ratings      = build_yearly_ratings(results, plant_params)
    cashflows           = build_cashflows(results)

    print("\n6. Writing TypeScript constants...")
    output_path = PROJECT_ROOT / "crp-dashboard" / "src" / "lib" / "generated" / "data.ts"
    generate_typescript(scenario_comparison, yearly_ratings, cashflows, scenario_risks, plant_params, output_path)

    print("\n7. Writing yearly_ratings.csv...")
    import csv
    yearly_ratings_path = PROJECT_ROOT / "results" / "yearly_ratings.csv"
    if yearly_ratings:
        fieldnames = list(yearly_ratings[0].keys())
        with open(yearly_ratings_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(yearly_ratings)
        print(f"  Written: results/yearly_ratings.csv  ({len(yearly_ratings)} rows)")

    print("\n" + "=" * 60)
    print("Done! Next steps:")
    print("  1. cd crp-dashboard && npm run build")
    print("  2. npm run dev   # verify locally")
    print("  3. git add -A && git commit -m 'Regenerate dashboard data'")
    print("=" * 60)


if __name__ == "__main__":
    main()

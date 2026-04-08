#!/usr/bin/env python3
"""
Regenerate dashboard JSON data from updated Python model.

This script runs the CRPModelRunner with 9 scenarios using the enhanced
11th Basic Plan (2040 coal phase-out) and exports results to the
crp-dashboard/src/data/ directory.

Usage:
    source .venv/bin/activate
    python3 scripts/regenerate_dashboard_data.py
"""

import json
import csv
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.runner import CRPModelRunner
from src.financials import calculate_debt_service
from src.risk import assess_credit_rating, calculate_rating_metrics_from_financials


def csv_to_json(csv_path: Path, json_path: Path) -> None:
    """Convert CSV to JSON with automatic numeric type conversion."""
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data = list(reader)

    # Fields that should be numeric (set to 0 if empty)
    numeric_fields = {
        "payback_years", "npv_million", "irr_pct", "avg_dscr", "min_dscr",
        "llcr", "expected_loss_pct", "npv_loss_million", "debt_spread_bps",
        "equity_premium_pct", "crp_bps", "climate_risk_premium_bps",
        "wacc_baseline_pct", "wacc_adjusted_pct", "rating_numeric", "spread_bps",
        "capacity_mw", "counterfactual_spread_bps", "notch_change", "counterfactual_crp_bps"
    }

    # Fields that should be boolean
    boolean_fields = {"is_investment_grade", "is_distressed", "is_ebitda_negative"}

    # Convert fields
    for row in data:
        for key, value in list(row.items()):
            if value is None or value == "":
                # Set numeric fields to 0, boolean fields to False
                if key in numeric_fields:
                    row[key] = 0
                elif key in boolean_fields:
                    row[key] = False
                continue

            # Convert boolean fields
            if key in boolean_fields:
                row[key] = value.lower() in ("true", "1", "yes")
                continue

            # Convert numeric fields
            try:
                if "." in value:
                    row[key] = float(value)
                else:
                    row[key] = int(value)
            except (ValueError, TypeError):
                pass

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  Converted: {csv_path.name} -> {json_path.name}")


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

BASE_RATE = 0.0675  # 6.75% base interest rate


def generate_yearly_ratings(results: dict, output_path: Path, plant_params: dict) -> None:
    """Generate yearly ratings data from scenario results.

    Produces fields matching the CreditRatingRow TypeScript interface:
      scenario, display_name, year, dscr, rating, spread_bps,
      cost_of_debt, ebitda, debt_service

    Uses full assess_credit_rating() per year with a 1-year timelag override:
      - If previous year DSCR < 0  → force current year to D
      - If previous year DSCR 0–1  → downgrade current year by 1 notch
      - If previous year DSCR >= 1 → no override
    """
    total_capex = float(plant_params.get("total_capex_million", 3550)) * 1e6
    debt_fraction = float(plant_params.get("debt_fraction", 0.80))
    debt_rate = float(plant_params.get("debt_interest_rate", 0.05))
    debt_tenor = int(plant_params.get("debt_tenor_years", 20))
    depreciation_years = int(plant_params.get("depreciation_years", 20))
    capacity_mw = float(plant_params.get("capacity_mw", 2100))

    # Pre-compute amortisation schedule once (principal paid each year)
    debt_struct = calculate_debt_service(total_capex, debt_fraction, debt_rate, debt_tenor)
    # Cumulative principal repaid after year i (0-indexed)
    cumulative_principal = debt_struct.principal_schedule.cumsum()

    RATING_ORDER = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "CC", "C", "D"]

    yearly_data = []

    for scenario_name, result in results.items():
        if result.cashflow is None:
            continue

        cf = result.cashflow
        years = cf.years

        display_name = SCENARIO_DISPLAY.get(scenario_name, scenario_name)

        prev_dscr = None

        for i, year in enumerate(years):
            dscr_i = float(cf.dscr[i]) if i < len(cf.dscr) else 0.0
            ebitda = float(cf.ebitda[i]) if i < len(cf.ebitda) else 0.0
            debt_service = float(cf.interest_expense[i]) if i < len(cf.interest_expense) else 0.0

            # Per-year balance sheet reconstruction
            if i < debt_tenor:
                debt_outstanding_i = (total_capex * debt_fraction
                                      - (cumulative_principal[i - 1] if i > 0 else 0.0))
            else:
                debt_outstanding_i = 0.0

            fixed_assets_i = total_capex * max(0.0, 1 - i / depreciation_years)
            total_equity_i = max(0.0, fixed_assets_i - debt_outstanding_i)
            total_assets_i = max(fixed_assets_i, debt_outstanding_i)

            rating_metrics = calculate_rating_metrics_from_financials(
                capacity_mw=capacity_mw,
                ebitda=ebitda,
                fixed_assets=total_assets_i,
                interest_expense=debt_service,
                total_debt=debt_outstanding_i,
                cash_and_equivalents=max(0.0, ebitda * 0.1),
                total_equity=total_equity_i,
                total_assets=total_assets_i,
                dscr=dscr_i,
            )
            assessment = assess_credit_rating(rating_metrics)
            rating = assessment.overall_rating.name

            # 1-year timelag override: previous year's DSCR affects this year's rating
            if prev_dscr is not None:
                if prev_dscr < 0:
                    rating = "D"
                elif prev_dscr < 1.0:
                    idx = RATING_ORDER.index(rating)
                    rating = RATING_ORDER[min(idx + 1, len(RATING_ORDER) - 1)]

            prev_dscr = dscr_i

            spread_bps = RATING_SPREAD_MAP.get(rating, 900)
            cost_of_debt = round(BASE_RATE + spread_bps / 10000, 6)

            yearly_data.append({
                "scenario": scenario_name,
                "display_name": display_name,
                "year": int(year),
                "dscr": round(dscr_i, 3),
                "rating": rating,
                "spread_bps": spread_bps,
                "cost_of_debt": cost_of_debt,
                "ebitda": round(ebitda, 2),
                "debt_service": round(debt_service, 2),
            })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(yearly_data, f, indent=2, ensure_ascii=False)

    print(f"  Generated: {output_path.name} (full assess_credit_rating() per year)")


def main():
    print("=" * 60)
    print("CRP Dashboard Data Regeneration")
    print("=" * 60)
    print()

    # Initialize runner
    print("1. Initializing CRPModelRunner...")
    runner = CRPModelRunner(PROJECT_ROOT)
    print("   Done.")
    print()

    # Use all 11 default scenarios (includes enhanced 11th plan)
    print("2. Running all 11 default scenarios...")
    results = runner.run_multi_scenario()
    for name in results:
        print(f"   - {name}")
    print("   All scenarios completed.")
    print()

    # Export to CSV first
    processed_dir = PROJECT_ROOT / "data/processed"
    print(f"3. Exporting results to CSV ({processed_dir})...")
    runner.export_results(results, processed_dir)
    print("   Done.")
    print()

    # Convert CSV to JSON for dashboard
    dashboard_data_dir = PROJECT_ROOT / "crp-dashboard/src/data"
    dashboard_data_dir.mkdir(parents=True, exist_ok=True)

    print(f"4. Converting CSV to JSON ({dashboard_data_dir})...")

    # Main comparison file
    scenario_csv = processed_dir / "scenario_comparison.csv"
    if scenario_csv.exists():
        csv_to_json(scenario_csv, dashboard_data_dir / "scenario_comparison.json")

    # Credit ratings file
    ratings_csv = processed_dir / "credit_ratings.csv"
    if ratings_csv.exists():
        csv_to_json(ratings_csv, dashboard_data_dir / "credit_ratings.json")

    plant_params = runner._get_plant_params()

    # Generate yearly ratings data
    generate_yearly_ratings(results, dashboard_data_dir / "yearly_ratings.json", plant_params)

    # Cashflow files
    cashflows_dir = dashboard_data_dir / "cashflows"
    cashflows_dir.mkdir(exist_ok=True)

    for csv_file in processed_dir.glob("cashflow_*.csv"):
        scenario = csv_file.stem.replace("cashflow_", "")
        csv_to_json(csv_file, cashflows_dir / f"{scenario}.json")

    print()
    print("=" * 60)
    print("Dashboard data regenerated successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. cd crp-dashboard && npm run build")
    print("  2. npm run dev  # to verify locally")
    print("  3. git add -A && git commit -m 'Update dashboard with 2040 coal phase-out data'")
    print()


if __name__ == "__main__":
    main()

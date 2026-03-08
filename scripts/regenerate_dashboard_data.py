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


def generate_yearly_ratings(results: dict, output_path: Path) -> None:
    """Generate yearly ratings data from scenario results.

    Produces fields matching the CreditRatingRow TypeScript interface:
      scenario, display_name, year, dscr, rating, spread_bps,
      cost_of_debt, ebitda, debt_service

    Note:
        This output is dashboard-only and uses an approximate DSCR-to-rating
        mapping. Paper-grade ratings should be taken from frozen scenario
        outputs (`scenario_comparison.csv` / `credit_ratings.csv`).
    """
    yearly_data = []

    for scenario_name, result in results.items():
        if result.cashflow is None:
            continue

        cf = result.cashflow
        years = cf.years
        dscr_values = (
            cf.dscr
            if hasattr(cf, "dscr")
            else [result.metrics.avg_dscr] * len(years)
        )

        display_name = SCENARIO_DISPLAY.get(scenario_name, scenario_name)

        for i, year in enumerate(years):
            # Approximate rating from DSCR
            dscr = dscr_values[i] if i < len(dscr_values) else result.metrics.avg_dscr

            # Simple rating approximation based on DSCR
            if dscr >= 2.0:
                rating = "A"
            elif dscr >= 1.5:
                rating = "BBB"
            elif dscr >= 1.2:
                rating = "BB"
            elif dscr >= 1.0:
                rating = "B"
            else:
                rating = "CCC"

            spread_bps = RATING_SPREAD_MAP.get(rating, 900)
            cost_of_debt = round(BASE_RATE + spread_bps / 10000, 6)

            ebitda = float(cf.ebitda[i]) if i < len(cf.ebitda) else 0.0
            debt_service = float(cf.interest_expense[i]) if i < len(cf.interest_expense) else 0.0

            yearly_data.append({
                "scenario": scenario_name,
                "display_name": display_name,
                "year": int(year),
                "dscr": round(float(dscr), 3),
                "rating": rating,
                "spread_bps": spread_bps,
                "cost_of_debt": cost_of_debt,
                "ebitda": round(ebitda, 2),
                "debt_service": round(debt_service, 2),
            })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(yearly_data, f, indent=2, ensure_ascii=False)

    print(f"  Generated: {output_path.name} (dashboard approximation only)")


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

    # Generate yearly ratings data
    generate_yearly_ratings(results, dashboard_data_dir / "yearly_ratings.json")

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

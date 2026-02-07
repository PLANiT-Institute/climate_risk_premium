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


def generate_yearly_ratings(results: dict, output_path: Path) -> None:
    """Generate yearly ratings data from scenario results."""
    yearly_data = []

    for scenario_name, result in results.items():
        if result.cashflow is None:
            continue

        years = result.cashflow.years
        dscr_values = result.cashflow.dscr if hasattr(result.cashflow, 'dscr') else [result.metrics.avg_dscr] * len(years)

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

            yearly_data.append({
                "scenario": scenario_name,
                "year": int(year),
                "dscr": round(float(dscr), 3),
                "rating": rating
            })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(yearly_data, f, indent=2, ensure_ascii=False)

    print(f"  Generated: {output_path.name}")


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

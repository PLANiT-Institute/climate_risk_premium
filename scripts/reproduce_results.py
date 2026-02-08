#!/usr/bin/env python3
"""
Reproduce all canonical results for the Climate Risk Premium model.

Runs the full 11-scenario pipeline and exports results to:
  - results/scenario_comparison.csv
  - results/credit_ratings.csv
  - results/cashflow_*.csv

Usage:
    source .venv/bin/activate
    python scripts/reproduce_results.py
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.runner import CRPModelRunner


def main():
    print("=" * 70)
    print("Climate Risk Premium -- Canonical Result Reproduction")
    print("=" * 70)
    print()

    # Output directory
    results_dir = PROJECT_ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Initialize runner
    print("1. Initializing CRPModelRunner ...")
    runner = CRPModelRunner(PROJECT_ROOT)
    print("   Done.")
    print()

    # Run all 11 default scenarios
    print("2. Running 11 default scenarios ...")
    results = runner.run_multi_scenario()
    print(f"   Completed {len(results)} scenarios.")
    print()

    # Print summary table
    print("3. Scenario summary")
    print("-" * 90)
    print(f"{'Scenario':<28} {'NPV ($M)':>10} {'IRR':>8} {'MinDSCR':>8} {'Rating':>7} {'CRP(bps)':>9}")
    print("-" * 90)

    for name, result in results.items():
        npv_m = result.metrics.npv / 1e6
        irr_pct = result.metrics.irr * 100
        min_dscr = result.metrics.min_dscr

        rating_str = "N/A"
        if result.credit_rating:
            rating_str = str(result.credit_rating.overall_rating.name)

        crp_bps = 0.0
        if result.counterfactual_crp:
            crp_bps = result.counterfactual_crp.get("crp_bps", 0.0)

        print(
            f"{name:<28} {npv_m:>10,.1f} {irr_pct:>7.2f}% {min_dscr:>8.2f} {rating_str:>7} {crp_bps:>9.0f}"
        )

    print("-" * 90)
    print()

    # Export to results/
    print(f"4. Exporting results to {results_dir} ...")
    paths = runner.export_results(results, results_dir)
    for label, p in paths.items():
        print(f"   {label}: {p.name}")
    print("   Done.")
    print()

    print("=" * 70)
    print("Reproduction complete. Results written to results/")
    print("=" * 70)


if __name__ == "__main__":
    main()

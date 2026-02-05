#!/usr/bin/env python3
"""
Quick runner script for Climate Risk Premium analysis.
"""
from pathlib import Path
from src.pipeline.runner import CRPModelRunner


def main():
    print("=" * 70)
    print("Climate Risk Premium Analysis - Samcheok Power Plant")
    print("=" * 70)
    print()

    # Initialize runner
    base_dir = Path(__file__).parent
    runner = CRPModelRunner(base_dir)

    print("Running multi-scenario analysis...")
    print()

    # Run all default scenarios
    results = runner.run_multi_scenario()

    print(f"✓ Completed {len(results)} scenarios:")
    for name in results.keys():
        npv = results[name].metrics.npv / 1e6
        print(f"  - {name:25s} NPV: ${npv:,.1f}M")

    print()

    # Export results
    output_dir = base_dir / "data" / "processed"
    paths = runner.export_results(results, output_dir)

    print(f"✓ Exported results to {output_dir}/")
    print()

    # Display key findings
    baseline = results.get("baseline")
    combined_agg = results.get("combined_aggressive")

    if baseline and combined_agg and combined_agg.financing:
        print("=" * 70)
        print("KEY FINDINGS")
        print("=" * 70)
        print()
        print(f"Baseline NPV:          ${baseline.metrics.npv / 1e6:,.1f}M")
        print(f"Baseline IRR:          {baseline.metrics.irr * 100:.2f}%")
        print(f"Baseline Avg DSCR:     {baseline.metrics.avg_dscr:.2f}")
        print()
        print(f"Worst-Case NPV:        ${combined_agg.metrics.npv / 1e6:,.1f}M")
        print(f"NPV Loss:              ${combined_agg.financing.npv_loss_million:,.1f}M ({combined_agg.financing.expected_loss_pct:.1f}%)")
        print(f"Climate Risk Premium:  {combined_agg.financing.crp_bps:.0f} bps")
        print(f"WACC Impact:           {combined_agg.financing.wacc_baseline_pct:.2f}% → {combined_agg.financing.wacc_adjusted_pct:.2f}%")
        print()

    print("=" * 70)
    print("Next steps:")
    print("  1. View detailed results: jupyter notebook notebooks/01_explore_crp_model.ipynb")
    print("  2. Launch interactive app: streamlit run src/app/streamlit_app.py")
    print("  3. Review CSV outputs in data/processed/")
    print("=" * 70)


if __name__ == "__main__":
    main()

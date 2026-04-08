"""
Run all 11 default scenarios and export results to results/.

Run from repo root:
    python scripts/run_all_scenarios.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)

from src.pipeline.runner import CRPModelRunner

def main() -> None:
    print("Initialising CRPModelRunner …", flush=True)
    runner = CRPModelRunner(Path("."))

    print("Running 11 scenarios …", flush=True)
    results = runner.run_multi_scenario()

    print(f"\nExporting results to results/ …", flush=True)
    paths = runner.export_results(results, Path("results"))

    print(f"\nExported {len(paths)} files.")
    for key, path in sorted(paths.items()):
        print(f"  {path}")

    # Quick summary table
    print("\n" + "=" * 90)
    print(f"{'Scenario':<26} {'NPV (M KRW)':>14} {'IRR':>7} {'Avg DSCR':>10} {'Credit Rating':>14}")
    print("-" * 90)
    for name, result in results.items():
        m = result.metrics
        rating = result.credit_rating.overall_rating.name if result.credit_rating else "N/A"
        print(
            f"{name:<26} {m.npv/1e6:>14,.1f} {m.irr*100:>6.2f}% {m.avg_dscr:>10.3f} {rating:>14}"
        )
    print("=" * 90)


if __name__ == "__main__":
    main()

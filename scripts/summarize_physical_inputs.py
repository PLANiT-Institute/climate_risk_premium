"""
Summarize the exact PhysicalAdjustments values each scenario feeds into the cashflow engine.

Run from repo root:
    python scripts/summarize_physical_inputs.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline.runner import CRPModelRunner, PHYSICAL_SCENARIO_SSP_MAP

SCENARIOS = [
    {"name": "baseline",              "transition": "baseline",              "physical": "baseline"},
    {"name": "moderate_transition",   "transition": "moderate_transition",   "physical": "baseline"},
    {"name": "aggressive_transition", "transition": "aggressive_transition", "physical": "baseline"},
    {"name": "moderate_physical",     "transition": "baseline",              "physical": "moderate_physical"},
    {"name": "high_physical",         "transition": "baseline",              "physical": "high_physical"},
    {"name": "combined_moderate",     "transition": "moderate_transition",   "physical": "moderate_physical"},
    {"name": "combined_aggressive",   "transition": "aggressive_transition", "physical": "high_physical"},
    {"name": "low_demand",            "transition": "baseline",              "physical": "baseline",        "market": "low_demand"},
    {"name": "severe_drought",        "transition": "baseline",              "physical": "severe_drought",  "market": "baseline"},
    {"name": "enhanced_11th_plan",    "transition": "moderate_transition",   "physical": "baseline",        "use_enhanced": True},
    {"name": "enhanced_combined",     "transition": "moderate_transition",   "physical": "moderate_physical","use_enhanced": True},
]

def main() -> None:
    print("Initialising CRPModelRunner …", flush=True)
    runner = CRPModelRunner(Path("."))

    rows = []
    for spec in SCENARIOS:
        phys_name = spec.get("physical", "baseline")
        ssp, target_year = PHYSICAL_SCENARIO_SSP_MAP.get(phys_name, ("ssp126", 2024))
        adj = runner._load_physical_scenario(phys_name)
        rows.append({
            "scenario_name":         spec["name"],
            "physical_scenario":     phys_name,
            "ssp":                   ssp,
            "target_year":           target_year,
            "outage_rate":           adj.outage_rate,
            "efficiency_loss":       adj.efficiency_loss,
            "water_temp_disruption": adj.water_temp_disruption,
            "notes":                 adj.notes[:80],
        })

    # --- Console table ---
    col_widths = {
        "scenario_name":         22,
        "physical_scenario":     20,
        "ssp":                    8,
        "target_year":           11,
        "outage_rate":           12,
        "efficiency_loss":       16,
        "water_temp_disruption": 22,
        "notes":                 82,
    }
    header = "  ".join(k.ljust(v) for k, v in col_widths.items())
    sep    = "  ".join("-" * v for v in col_widths.values())
    print("\n" + header)
    print(sep)
    for r in rows:
        line = "  ".join([
            r["scenario_name"].ljust(col_widths["scenario_name"]),
            r["physical_scenario"].ljust(col_widths["physical_scenario"]),
            r["ssp"].ljust(col_widths["ssp"]),
            str(r["target_year"]).ljust(col_widths["target_year"]),
            f"{r['outage_rate']:.6f}".ljust(col_widths["outage_rate"]),
            f"{r['efficiency_loss']:.6f}".ljust(col_widths["efficiency_loss"]),
            f"{r['water_temp_disruption']:.6f}".ljust(col_widths["water_temp_disruption"]),
            r["notes"].ljust(col_widths["notes"]),
        ])
        print(line)

    # --- CSV export ---
    import csv, os
    os.makedirs("results", exist_ok=True)
    csv_path = Path("results/physical_risk_inputs.csv")
    fieldnames = list(col_widths.keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved → {csv_path}")


if __name__ == "__main__":
    main()

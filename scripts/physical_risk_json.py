"""
Print PhysicalAdjustments for baseline, moderate_physical, high_physical as JSON.

Run from repo root:
    python scripts/physical_risk_json.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline.runner import CRPModelRunner, PHYSICAL_SCENARIO_SSP_MAP

SCENARIOS = ["baseline", "moderate_physical", "high_physical"]

runner = CRPModelRunner(Path("."))

output = {}
for scenario in SCENARIOS:
    adj = runner._load_physical_scenario(scenario)
    ssp, year = PHYSICAL_SCENARIO_SSP_MAP.get(scenario, ("ssp126", 2024))
    output[scenario] = {
        "ssp": ssp,
        "target_year": year,
        "outage_rate":          adj.outage_rate,
        "efficiency_loss":      adj.efficiency_loss,
        "water_temp_disruption": adj.water_temp_disruption,
        "total":                adj.outage_rate + adj.efficiency_loss + adj.water_temp_disruption,
        "notes":                adj.notes,
    }

print(json.dumps(output, indent=2))
"""
Generate physical_risk_matrix.csv.

Columns: scenario, year, outage_rate, efficiency_loss,
         mean_temp_derate, heat_wave_derate, cooling_water_derate,
         water_temp_disruption, total_physical_risk

total_physical_risk = outage_rate + efficiency_loss + water_temp_disruption
"""
import sys
from pathlib import Path

# Make sure project root is on the path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import csv

from src.models.physical.wildfire import WildfireModel
from src.models.physical.temperature import TemperatureModel, CoolingType
from src.models.physical.wri_thermal import WaterTemperatureModel

# ---------------------------------------------------------------------------
# Scenario configurations (exactly as specified)
# ---------------------------------------------------------------------------
SCENARIOS = {
    "moderate_physical": {
        "wildfire": WildfireModel("SSP1-2.6"),
        "temperature": TemperatureModel(rcp="RCP4.5"),
        "water": WaterTemperatureModel("SSP1-2.6"),
    },
    "high_physical": {
        "wildfire": WildfireModel("RCP8.5"),
        "temperature": TemperatureModel(rcp="RCP8.5"),
        "water": WaterTemperatureModel("RCP8.5"),
    },
    "severe_drought": {
        "wildfire": WildfireModel("RCP8.5"),
        "temperature": TemperatureModel(rcp="RCP8.5"),
        "water": WaterTemperatureModel("RCP8.5"),
    },
}

YEARS = list(range(2025, 2055))  # 2025–2054 inclusive

FIELDNAMES = [
    "scenario",
    "year",
    "outage_rate",
    "efficiency_loss",
    "mean_temp_derate",
    "heat_wave_derate",
    "cooling_water_derate",
    "water_temp_disruption",
    "total_physical_risk",
]

# ---------------------------------------------------------------------------
# Build rows
# ---------------------------------------------------------------------------
rows = []
for scenario_name, models in SCENARIOS.items():
    wf_model = models["wildfire"]
    tm_model = models["temperature"]
    wt_model = models["water"]

    for year in YEARS:
        outage_rate = wf_model.calculate_outage_rate(year)

        temp_result = tm_model.calculate_efficiency_loss(year)
        efficiency_loss = temp_result.total_derate
        mean_temp_derate = temp_result.mean_temp_derate
        heat_wave_derate = temp_result.heat_wave_derate
        cooling_water_derate = temp_result.cooling_water_derate

        water_temp_disruption = wt_model.calculate_disruption(year)

        total_physical_risk = outage_rate + efficiency_loss + water_temp_disruption

        rows.append({
            "scenario": scenario_name,
            "year": year,
            "outage_rate": outage_rate,
            "efficiency_loss": efficiency_loss,
            "mean_temp_derate": mean_temp_derate,
            "heat_wave_derate": heat_wave_derate,
            "cooling_water_derate": cooling_water_derate,
            "water_temp_disruption": water_temp_disruption,
            "total_physical_risk": total_physical_risk,
        })

# ---------------------------------------------------------------------------
# Save CSV
# ---------------------------------------------------------------------------
out_path = ROOT / "results" / "physical_risk_matrix.csv"
out_path.parent.mkdir(parents=True, exist_ok=True)

with out_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: (f"{v:.8f}" if isinstance(v, float) else v) for k, v in row.items()})

print(f"Saved {len(rows)} rows → {out_path}\n")

# ---------------------------------------------------------------------------
# Summary table at key years
# ---------------------------------------------------------------------------
SUMMARY_YEARS = [2025, 2030, 2040, 2050, 2054]

# Index rows by (scenario, year)
index = {(r["scenario"], r["year"]): r for r in rows}

col_w = 22
hdr_w = 12

def pct(v):
    return f"{float(v)*100:.4f}%"

print("=" * 110)
print("PHYSICAL RISK SUMMARY MATRIX  (all values as % of annual capacity)")
print("=" * 110)

for scenario_name in SCENARIOS:
    print(f"\n  Scenario: {scenario_name}")
    print(f"  {'Year':<6}  {'outage_rate':>13}  {'efficiency_loss':>15}  "
          f"{'mean_temp':>11}  {'heat_wave':>11}  {'cool_water':>11}  "
          f"{'wtr_temp_disr':>14}  {'TOTAL':>10}")
    print("  " + "-" * 100)
    for year in SUMMARY_YEARS:
        r = index[(scenario_name, year)]
        print(
            f"  {year:<6}  "
            f"{pct(r['outage_rate']):>13}  "
            f"{pct(r['efficiency_loss']):>15}  "
            f"{pct(r['mean_temp_derate']):>11}  "
            f"{pct(r['heat_wave_derate']):>11}  "
            f"{pct(r['cooling_water_derate']):>11}  "
            f"{pct(r['water_temp_disruption']):>14}  "
            f"{pct(r['total_physical_risk']):>10}"
        )

print("\n" + "=" * 110)

"""
Hello World sanity check for physrisk-lib integration — Phase 1.

Replicates the cement plant walk-through pattern from the physrisk docs but uses
Samcheok Blue Power (37.1356°N, 129.3347°E, 2100 MW Coal/Steam/OnceThrough) as
the asset. Default vulnerability models only — no custom config CSV.

Purpose: confirm physrisk-lib is installed and that get_asset_impact can be
called for a thermal power asset. Results are not expected to be meaningful
since the default vulnerability models may not cover Coal/Steam/OnceThrough.
"""

import json
import sys
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "physrisk_probe_results"
OUTPUT_FILE = OUTPUT_DIR / "hello_raw.json"

SAMCHEOK_ASSET = {
    "asset_class": "ThermalPowerGeneratingAsset",
    "type": "Coal/Steam/OnceThrough",
    "latitude": 37.4404,   # corrected: matches plant_exposure.csv / exposure_data.csv
    "longitude": 129.1671,
    "location": "Asia",
    "capacity": 2100.0,
}

REQUEST = {
    "assets": {"items": [SAMCHEOK_ASSET]},
    "include_asset_level": True,
    "include_calc_details": True,
    "include_measures": False,
    "years": [2050],
    "scenarios": ["historical", "ssp585"],
}


def print_summary(response: dict) -> None:
    asset_impacts = response.get("asset_impacts", [])
    if not asset_impacts:
        print("No asset_impacts in response.")
        return

    impacts = asset_impacts[0].get("impacts", [])
    if not impacts:
        print("No impacts returned for this asset.")
        return

    col = "{:<30} {:<12} {:<8} {:<14} {:<15}"
    print(col.format("hazard_type", "scenario", "year", "impact_mean", "impact_type"))
    print("-" * 82)
    for impact in impacts:
        key = impact.get("key", {})
        hazard = key.get("hazard_type", "?")
        scenario = key.get("scenario_id", "?")
        year = key.get("year", "?")
        mean = impact.get("impact_mean", None)
        impact_type = impact.get("impact_type", "?")
        mean_str = f"{mean:.6f}" if isinstance(mean, (int, float)) else str(mean)
        print(col.format(hazard, scenario, str(year), mean_str, impact_type))


def run() -> None:
    try:
        from physrisk.container import Container
    except ImportError as exc:
        print(f"ImportError: {exc}")
        print("physrisk-lib is not installed. Run: pip install physrisk-lib")
        sys.exit(1)

    print("physrisk-lib imported successfully.")
    print(f"Asset: Samcheok Blue Power  ({SAMCHEOK_ASSET['latitude']}°N, {SAMCHEOK_ASSET['longitude']}°E)  [seawater once-through]")
    print(f"Scenarios: {REQUEST['scenarios']}  Years: {REQUEST['years']}")
    print("Calling get_asset_impact with default vulnerability models...\n")

    try:
        container = Container()
        requester = container.requester()
        raw = requester.get(request_id="get_asset_impact", request_dict=REQUEST)
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}")
        sys.exit(1)

    response = json.loads(raw)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(response, indent=2), encoding="utf-8")
    print(f"Raw response saved to: {OUTPUT_FILE}\n")

    print_summary(response)


if __name__ == "__main__":
    run()

"""
Run CLIMADA wildfire hazard analysis for Samcheok power plant.

Uses FIRMS satellite data with CLIMADA engine. Climate scenarios are modeled
by scaling historical event frequency/intensity per SSP pathway.

Usage:
    .venv-climada/bin/python3 scripts/run_climada_live.py
"""
import sys
import os
import copy
import logging
import csv
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

for name in ["climada", "climada_petals"]:
    logging.getLogger(name).setLevel(logging.ERROR)

# ── Samcheok power plant ──
SAMCHEOK_LAT = 37.3897
SAMCHEOK_LON = 129.1650
PLANT_VALUE_KRW = 4.879e12  # 4.879조원

# ── Climate scenario frequency multipliers ──
# Based on Kim et al. 2025 (DOI:10.1007/s11069-025-07169-4) and WWA 2025
SCENARIO_FREQ_MULTIPLIER = {
    "historical": 1.0,
    "ssp126": 1.5,   # Low emissions: 50% increase in fire frequency
    "ssp245": 2.0,   # Moderate: 2x frequency
    "ssp585": 4.0,   # High emissions: 4x frequency (Kim et al. 2025)
}

# Region bounds (Gangwon-do around Samcheok)
LAT_MIN, LAT_MAX = 36.5, 38.0
LON_MIN, LON_MAX = 128.5, 130.0


def load_firms_data():
    """Load and filter FIRMS fire detection data."""
    firms_path = PROJECT_ROOT / "Physicalrisk_PLANiT" / "data" / "fire_archive_M-C61_701491.csv"
    df = pd.read_csv(firms_path)
    mask = (
        (df["latitude"] >= LAT_MIN) & (df["latitude"] <= LAT_MAX) &
        (df["longitude"] >= LON_MIN) & (df["longitude"] <= LON_MAX)
    )
    filtered = df[mask].copy()
    logger.info(f"FIRMS data: {len(df)} total, {len(filtered)} in Gangwon-do region")

    # Basic stats
    if "acq_date" in filtered.columns:
        years = pd.to_datetime(filtered["acq_date"]).dt.year
        logger.info(f"  Year range: {years.min()}-{years.max()} ({years.nunique()} years)")
        logger.info(f"  Average fires/year: {len(filtered)/years.nunique():.1f}")

    return filtered if len(filtered) >= 10 else df


def create_exposure():
    """Create CLIMADA exposure for Samcheok power plant."""
    from climada.entity import Exposures
    import geopandas as gpd
    from shapely.geometry import Point

    gdf = gpd.GeoDataFrame({
        "value": [PLANT_VALUE_KRW],
        "latitude": [SAMCHEOK_LAT],
        "longitude": [SAMCHEOK_LON],
        "impf_WFseason": [1],
    }, geometry=[Point(SAMCHEOK_LON, SAMCHEOK_LAT)], crs="EPSG:4326")

    exp = Exposures(gdf)
    exp.check()
    return exp


def create_impact_func():
    """Create wildfire impact function."""
    from climada.entity import ImpactFuncSet
    from climada_petals.entity.impact_funcs.wildfire import ImpfWildfire

    try:
        if_wf = ImpfWildfire.from_default_FIRMS(i_half=409.5)
    except AttributeError:
        if_wf = ImpfWildfire()
        if_wf.set_default_FIRMS(i_half=409.5)
    if_wf.haz_type = "WFseason"
    return ImpactFuncSet([if_wf])


def run_wildfire_analysis(firms_df):
    """Run CLIMADA wildfire analysis with scenario scaling."""
    from climada_petals.hazard.wildfire import WildFire

    exposure = create_exposure()
    ifset = create_impact_func()

    # Create historical wildfire hazard from FIRMS
    logger.info("Building historical wildfire hazard from FIRMS satellite data...")
    base_wf = WildFire.from_hist_fire_seasons_FIRMS(
        firms_df, centr_res_factor=1.0, keep_all_fires=True,
    )

    n_events = len(base_wf.event_name)
    years_data = firms_df["acq_date"].apply(lambda x: int(str(x)[:4]))
    years_covered = years_data.nunique()
    hist_freq = n_events / max(years_covered, 1)
    logger.info(f"Historical wildfire: {n_events} events over {years_covered} years = {hist_freq:.2f}/year")

    # Get hazard intensity statistics
    intensity = base_wf.intensity.toarray()
    nonzero_intensity = intensity[intensity > 0]
    logger.info(f"Intensity stats: max={intensity.max():.2f}, mean(nonzero)={nonzero_intensity.mean():.2f}" if len(nonzero_intensity) > 0 else "No nonzero intensity")

    # Fix dates if needed
    if len(base_wf.date) != n_events:
        base_wf.date = np.concatenate([
            base_wf.date,
            np.full(n_events - len(base_wf.date), base_wf.date[-1] if len(base_wf.date) > 0 else 0)
        ])

    # Compute base impact
    try:
        try:
            from climada.engine import ImpactCalc
            base_imp = ImpactCalc(exposure, ifset, base_wf).impact(save_mat=True)
        except (ImportError, Exception):
            from climada.engine import Impact
            base_imp = Impact()
            base_imp.calc(exposure, ifset, base_wf, save_mat=True)

        base_aai = float(base_imp.aai_agg)
        event_impacts = np.array(base_imp.at_event)
        nonzero_impacts = event_impacts[event_impacts > 0]

        logger.info(f"Base AAI: {base_aai/1e9:.4f}B KRW")
        logger.info(f"Events with impact on plant: {len(nonzero_impacts)}/{n_events}")
        if len(nonzero_impacts) > 0:
            logger.info(f"Max single-event impact: {nonzero_impacts.max()/1e9:.4f}B KRW")

    except Exception as e:
        logger.error(f"Impact calculation failed: {e}")
        base_aai = 0.0
        event_impacts = np.zeros(n_events)

    # Generate scenario results by scaling frequency
    results = []
    for scenario, multiplier in SCENARIO_FREQ_MULTIPLIER.items():
        scaled_aai = base_aai * multiplier
        scaled_freq = hist_freq * multiplier
        scaled_n_events = int(n_events * multiplier)

        max_impact = float(event_impacts.max()) if len(event_impacts) > 0 else 0

        logger.info(f"\n{scenario}: freq_mult={multiplier}x → AAI={scaled_aai/1e9:.4f}B KRW, freq={scaled_freq:.2f}/yr")

        results.append({
            "hazard_type": "wildfire",
            "scenario": scenario,
            "legacy_impact_krw": scaled_aai,
            "n_events": scaled_n_events,
            "max_event_impact": max_impact * multiplier,
            "aai_krw": scaled_aai,
            "event_frequency_per_year": scaled_freq,
            "freq_multiplier": multiplier,
            "years_covered": years_covered,
            "firms_detections": len(firms_df),
        })

    return results


def save_results(results):
    """Save results to CSV files."""
    output_dir = PROJECT_ROOT / "Physicalrisk_PLANiT" / "data" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Full results with timestamp
    full_path = output_dir / f"wildfire_results_{timestamp}.csv"
    with open(full_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    logger.info(f"\nFull results: {full_path}")

    # PLANiT-compatible format (used by main pipeline adapter)
    compat_path = output_dir / "wildfire_results_climada_live.csv"
    with open(compat_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "hazard_type", "scenario", "legacy_impact_krw", "n_events", "max_event_impact",
        ])
        writer.writeheader()
        for r in results:
            writer.writerow({k: r[k] for k in ["hazard_type", "scenario", "legacy_impact_krw", "n_events", "max_event_impact"]})
    logger.info(f"PLANiT-compatible: {compat_path}")

    return full_path


def main():
    logger.info("=" * 60)
    logger.info("CLIMADA Wildfire Risk - Samcheok Coal Power Plant")
    logger.info("=" * 60)
    logger.info(f"Location: {SAMCHEOK_LAT}N, {SAMCHEOK_LON}E")
    logger.info(f"Plant value: {PLANT_VALUE_KRW/1e12:.3f}조 KRW")
    logger.info(f"Data source: NASA FIRMS (MODIS C6.1)")
    logger.info(f"Engine: CLIMADA v6 + climada_petals (WildFire)")
    logger.info("")

    firms_df = load_firms_data()
    results = run_wildfire_analysis(firms_df)
    save_results(results)

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("RESULTS SUMMARY")
    logger.info("=" * 70)
    logger.info(f"{'Scenario':<15} {'Multiplier':>10} {'AAI (B KRW)':>12} {'Freq/yr':>10} {'Events':>8}")
    logger.info("-" * 60)
    for r in results:
        logger.info(
            f"{r['scenario']:<15} {r['freq_multiplier']:>10.1f}x "
            f"{r['aai_krw']/1e9:>12.4f} {r['event_frequency_per_year']:>10.2f} {r['n_events']:>8}"
        )
    logger.info("\nDone!")


if __name__ == "__main__":
    main()

"""Wildfire outage probability model — exponential failure approach.

Model:
    P(outage|event) = 1 - exp(-λ × t)

Parameters:
    λ (failure_rate_per_hour): rate at which infrastructure fails under fire exposure.
        Source: Choobineh, M., Ansari, B., & Mohagheghi, S. (2015).
        "Vulnerability assessment of the power grid against progressing wildfires."
        Fire Safety Journal, 73, 20-28. DOI: 10.1016/j.firesaf.2015.02.006
        Values: 0.2-0.4/h (steel tower lines), 0.5-1.0/h (wooden pole lines)

    t (exposure_duration_hours): how long the fire front exposes the asset.
        Source: 산림청 산불통계연보 (KFS Forest Fire Statistics, 1991-2004)
        KCI Article ID: ART001017472
        - Small fires (<5ha): avg 2.5h total duration → transit ~0.5-1h
        - Large fires (≥30ha): avg 18.5h total → transit ~2-4h
        Sensitivity: [1h, 2h, 4h] (no direct measurement of point-transit time)

All parameters are loaded from CSV — no hardcoded values in this module.
"""

from __future__ import annotations

import csv
import math
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

HOURS_PER_YEAR = 8760.0


@dataclass
class OutageParams:
    """Parameters for exponential outage model, loaded from CSV."""
    failure_rate_per_hour: float  # λ
    exposure_duration_hours: float  # t (central estimate)
    exposure_duration_sensitivity: Tuple[float, float, float]  # (low, mid, high)
    outage_duration_hours: float  # how long outage lasts once triggered
    source_lambda: str
    source_duration: str


def load_outage_params(csv_path: Optional[str] = None) -> Dict[str, OutageParams]:
    """Load outage parameters from CSV.

    CSV format:
        asset_type,failure_rate_per_hour,exposure_hours_low,exposure_hours_mid,exposure_hours_high,source_lambda,source_duration

    Returns:
        Dict mapping asset_type → OutageParams
    """
    if csv_path is None:
        csv_path = str(
            Path(__file__).resolve().parent.parent.parent
            / "data" / "physical" / "outage_params.csv"
        )

    path = Path(csv_path)
    if not path.exists():
        logger.warning("outage_params.csv not found at %s; using defaults", path)
        return _default_params()

    params: Dict[str, OutageParams] = {}
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            asset_type = row["asset_type"].strip()
            params[asset_type] = OutageParams(
                failure_rate_per_hour=float(row["failure_rate_per_hour"]),
                exposure_duration_hours=float(row["exposure_hours_mid"]),
                exposure_duration_sensitivity=(
                    float(row["exposure_hours_low"]),
                    float(row["exposure_hours_mid"]),
                    float(row["exposure_hours_high"]),
                ),
                outage_duration_hours=float(row.get("outage_duration_hours", 24.0)),
                source_lambda=row.get("source_lambda", ""),
                source_duration=row.get("source_duration", ""),
            )
    logger.info("Loaded outage params for %d asset types from %s", len(params), path)
    return params


def _default_params() -> Dict[str, OutageParams]:
    """Fallback defaults if CSV not found (should not happen in production)."""
    return {
        "transmission_tower": OutageParams(
            failure_rate_per_hour=0.3,
            exposure_duration_hours=2.0,
            exposure_duration_sensitivity=(1.0, 2.0, 4.0),
            outage_duration_hours=24.0,
            source_lambda="Choobineh & Mohagheghi (2015) DOI:10.1016/j.firesaf.2015.02.006",
            source_duration="KFS 산불통계 (KCI:ART001017472), sensitivity estimate",
        ),
        "power_plant": OutageParams(
            failure_rate_per_hour=0.2,
            exposure_duration_hours=2.0,
            exposure_duration_sensitivity=(1.0, 2.0, 4.0),
            outage_duration_hours=48.0,
            source_lambda="Choobineh & Mohagheghi (2015) DOI:10.1016/j.firesaf.2015.02.006",
            source_duration="KFS 산불통계 (KCI:ART001017472), sensitivity estimate",
        ),
    }


def p_outage_given_event(
    failure_rate: float,
    exposure_hours: float,
) -> float:
    """Compute P(outage | fire event) using exponential failure model.

    P = 1 - exp(-λ × t)

    Args:
        failure_rate: λ in failures per hour of fire exposure.
        exposure_hours: t in hours of fire front exposure at asset location.

    Returns:
        Probability in [0, 1].
    """
    if failure_rate <= 0 or exposure_hours <= 0:
        return 0.0
    return min(1.0, 1.0 - math.exp(-failure_rate * exposure_hours))


def compute_outage_rate(
    event_frequency_per_year: float,
    failure_rate: float,
    exposure_hours: float,
    outage_duration_hours: float = 24.0,
) -> float:
    """Compute annual outage rate.

    outage_rate = freq × P(outage|event) × (outage_duration / 8760)

    Args:
        event_frequency_per_year: annual fire event frequency (from CLIMADA).
        failure_rate: λ (from outage_params.csv).
        exposure_hours: t (from outage_params.csv, central estimate).
        outage_duration_hours: how long the outage lasts once triggered.

    Returns:
        Annual outage rate as fraction [0, 1].
    """
    p_outage = p_outage_given_event(failure_rate, exposure_hours)
    rate = event_frequency_per_year * p_outage * (outage_duration_hours / HOURS_PER_YEAR)
    return min(1.0, max(0.0, rate))

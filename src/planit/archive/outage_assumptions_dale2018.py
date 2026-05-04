"""Wildfire event-frequency to outage-rate assumptions.

The central values are modeling assumptions, not directly observed Korea plant
statistics. They are kept explicit because reviewer-facing results should be
shown with the sensitivity ranges below.
"""
from __future__ import annotations

from typing import Tuple


OUTAGE_RATE_PER_EVENT = 0.10
OUTAGE_RATE_PER_EVENT_SENSITIVITY: Tuple[float, float, float] = (0.05, 0.10, 0.20)

OUTAGE_DURATION_HOURS = 24.0
OUTAGE_DURATION_HOURS_SENSITIVITY: Tuple[float, float, float] = (12.0, 24.0, 72.0)

HOURS_PER_YEAR = 8760.0

# Source notes:
# - Probability: Dale et al. (2018), CCCA4-CEC-2018-002, Table 5 reports that
#   most wildfires near transmission paths have little/no grid impact. The 10%
#   central value is therefore an assumption within sensitivity range [5%, 20%],
#   not a directly observed Samcheok or KEPCO fire-to-outage statistic.
#   https://www.energy.ca.gov/sites/default/files/2019-11/Energy_CCCA4-CEC-2018-002_ADA.pdf
# - Duration: PG&E 2025 Transmission Availability Report to CAISO reports 2025
#   mean forced-outage durations by voltage class around 12h (115kV) and 24-25h
#   (230/500kV), with outage durations capped at 72h for reporting.
#   https://www.caiso.com/documents/pgae-transmission-availability-report.pdf
OUTAGE_PROBABILITY_SOURCE = (
    "Dale et al. (2018), Assessing the Impact of Wildfires on the California "
    "Electricity Grid, CCCA4-CEC-2018-002; central assumption, sensitivity "
    "range [0.05, 0.20]. "
    "https://www.energy.ca.gov/sites/default/files/2019-11/"
    "Energy_CCCA4-CEC-2018-002_ADA.pdf"
)
OUTAGE_DURATION_SOURCE = (
    "PG&E (2026), 2025 Electric Transmission Annual Availability Performance "
    "Report to CAISO; mean forced outage durations support 24h central value, "
    "sensitivity range [12, 72] hours. "
    "https://www.caiso.com/documents/pgae-transmission-availability-report.pdf"
)


def event_freq_to_outage_rate(
    freq: float,
    outage_probability: float = OUTAGE_RATE_PER_EVENT,
    outage_duration_hours: float = OUTAGE_DURATION_HOURS,
    hours_per_year: float = HOURS_PER_YEAR,
) -> float:
    """Convert annual event frequency to annual outage-rate fraction."""
    annual_frequency = max(0.0, float(freq))
    probability = min(1.0, max(0.0, float(outage_probability)))
    duration = max(0.0, float(outage_duration_hours))
    denominator = max(1.0, float(hours_per_year))
    outage_rate = annual_frequency * probability * duration / denominator
    return min(1.0, max(0.0, outage_rate))

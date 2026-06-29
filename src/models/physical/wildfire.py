"""
Wildfire Outage Model for Samcheok Blue Power.

Estimates the annual fraction of operating time lost due to wildfire events
causing grid disruption, emergency shutdowns, or forced outages.

Calibration
-----------
Baseline outage rate sourced from CLIMADA WildFire + Korea Forest Service
historical records (2001–2023):

    data/physical/hazard_baselines.csv  →  outage_rate = 0.000034
    (30 events / 40 years × P(outage|fire) × duration / 8760, Gangwon coast)

Climate scaling factors sourced from Korea Forest Service Climate Assessment
(2021), reported as multipliers relative to the 2001–2023 historical baseline:

    data/physical_risk_inputs/climate_factors.csv  →  wildfire rows
    RCP4.5: 2030=1.15×, 2050=1.35×, 2100=1.60×
    RCP8.5: 2030=1.20×, 2050=1.50×, 2100=2.20×

Methodology
-----------
    projected_outage_rate(scenario, year)
        = BASELINE_OUTAGE_RATE × climate_factor(scenario, year)

    climate_factor is linearly interpolated between anchor years.
    Years before 2024 return the baseline factor (1.0).
    Years beyond 2100 return the 2100 factor.

SSP–RCP mapping
---------------
The runner works in SSP space (ssp126, ssp585). The climate factors are
calibrated against RCP scenarios. Mapping used throughout CRP model:

    SSP1-2.6  →  RCP4.5  (both ≈2.6 W/m²; conservative choice for this scenario)
    RCP4.5    →  RCP4.5
    RCP8.5    →  RCP8.5

References
----------
- Korea Forest Service (KFS) Climate Assessment, 2021
- CLIMADA WildFire module (ETH Zürich / petals)
- van Wagner (1987), Canadian FWI System
- Vitolo et al. (2019), ERA5-based global wildfire danger maps
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Calibration constants (sourced from data/physical/hazard_baselines.csv)
# ---------------------------------------------------------------------------

#: Annual outage rate at the 2001–2023 historical baseline.
#: Derived: CLIMADA WildFire + KFS records, Gangwon coastal site.
#: Source: data/physical/hazard_baselines.csv, row wildfire
BASELINE_OUTAGE_RATE: float = 0.000034

# ---------------------------------------------------------------------------
# Climate scaling factors
# Source: data/physical_risk_inputs/climate_factors.csv, wildfire rows
# Korea Forest Service Climate Assessment (2021)
# Format: {anchor_year: scaling_factor} — 2024 anchored to 1.0 (historical mean)
# ---------------------------------------------------------------------------

_CLIMATE_FACTORS_RCP45: Dict[int, float] = {
    2024: 1.00,   # baseline (KFS historical 2001-2023)
    2030: 1.15,   # KFS RCP4.5 near-term
    2050: 1.35,   # KFS RCP4.5 mid-century
    2100: 1.60,   # KFS RCP4.5 end-century
}

_CLIMATE_FACTORS_RCP85: Dict[int, float] = {
    2024: 1.00,   # baseline (KFS historical 2001-2023)
    2030: 1.20,   # KFS RCP8.5 near-term
    2050: 1.50,   # KFS RCP8.5 mid-century
    2100: 2.20,   # KFS RCP8.5 end-century
}

# All scenarios keyed by canonical RCP label
_ALL_CLIMATE_FACTORS: Dict[str, Dict[int, float]] = {
    "RCP4.5": _CLIMATE_FACTORS_RCP45,
    "RCP8.5": _CLIMATE_FACTORS_RCP85,
}

# Mapping from CRP/SSP scenario labels → canonical RCP key
# SSP1-2.6 ≈ RCP4.5 (both ~2.6 W/m² forcing); conservative choice.
_SCENARIO_TO_RCP: Dict[str, str] = {
    "SSP1-2.6": "RCP4.5",
    "ssp126":   "RCP4.5",
    "RCP4.5":   "RCP4.5",
    "ssp245":   "RCP4.5",
    "RCP8.5":   "RCP8.5",
    "ssp585":   "RCP8.5",
}


@dataclass
class WildfireOutageResult:
    """Result from a single WildfireModel calculation.

    Attributes:
        year: Projection year.
        scenario: Canonical RCP scenario label used.
        climate_factor: Scaling factor applied to the baseline.
        outage_rate: Annual outage rate fraction [0, 1].
        baseline_outage_rate: Unscaled historical baseline.
        source: Citation string for the calibration data.
    """
    year: int
    scenario: str
    climate_factor: float
    outage_rate: float
    baseline_outage_rate: float
    source: str


def _interpolate(anchors: Dict[int, float], year: int) -> float:
    """Linearly interpolate a value from an {year: value} anchor dict.

    Years before the first anchor return the first anchor value.
    Years after the last anchor return the last anchor value.
    """
    years: List[int] = sorted(anchors)
    if year <= years[0]:
        return anchors[years[0]]
    if year >= years[-1]:
        return anchors[years[-1]]
    for i in range(len(years) - 1):
        y0, y1 = years[i], years[i + 1]
        if y0 <= year < y1:
            t = (year - y0) / (y1 - y0)
            return anchors[y0] + t * (anchors[y1] - anchors[y0])
    return anchors[years[-1]]


class WildfireModel:
    """Self-contained parametric wildfire outage model.

    Produces scenario- and year-differentiated annual outage rates for
    Samcheok Blue Power (Gangwon coastal site) based on:

    1. CLIMADA WildFire + Korea Forest Service historical baseline outage rate.
    2. Korea Forest Service RCP-based climate scaling factors (2021).

    Usage
    -----
    >>> model = WildfireModel("RCP8.5")
    >>> model.calculate_outage_rate(2050)   # doctest: +SKIP
    5.1e-05

    >>> result = model.calculate(2050)
    >>> result.climate_factor
    1.5
    """

    def __init__(self, scenario: str = "RCP8.5") -> None:
        """Initialise the wildfire model.

        Args:
            scenario: Climate scenario. Accepted values (case-sensitive):
                ``"RCP8.5"``, ``"RCP4.5"``, ``"SSP1-2.6"``, ``"ssp126"``,
                ``"ssp585"``, ``"ssp245"``.
                Unknown scenarios fall back to ``"RCP4.5"`` (conservative).
        """
        self._rcp = _SCENARIO_TO_RCP.get(scenario, "RCP4.5")
        self._factors = _ALL_CLIMATE_FACTORS[self._rcp]

    @property
    def scenario(self) -> str:
        """Canonical RCP scenario label."""
        return self._rcp

    def get_climate_factor(self, year: int) -> float:
        """Return the climate scaling factor for the given year.

        Linearly interpolated between KFS anchor years.
        """
        return _interpolate(self._factors, year)

    def calculate(self, year: int) -> WildfireOutageResult:
        """Full result object with breakdown.

        Args:
            year: Projection year.

        Returns:
            WildfireOutageResult with outage_rate and diagnostics.
        """
        factor = self.get_climate_factor(year)
        outage_rate = min(1.0, max(0.0, BASELINE_OUTAGE_RATE * factor))
        return WildfireOutageResult(
            year=year,
            scenario=self._rcp,
            climate_factor=factor,
            outage_rate=outage_rate,
            baseline_outage_rate=BASELINE_OUTAGE_RATE,
            source=(
                "Baseline: CLIMADA WildFire + KFS (2001-2023), "
                "data/physical/hazard_baselines.csv; "
                f"Scaling: KFS Climate Assessment (2021) {self._rcp}, "
                "data/physical_risk_inputs/climate_factors.csv"
            ),
        )

    def calculate_outage_rate(self, year: int) -> float:
        """Convenience method — returns only the outage rate fraction.

        Args:
            year: Projection year.

        Returns:
            Annual outage rate in [0.0, 1.0].
        """
        return self.calculate(year).outage_rate

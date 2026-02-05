"""
Physical Hazard Definitions and Baseline Data.

Comprehensive hazard modeling for power plant risk assessment.
All data loaded from CSV files - no hardcoded values.

Hazard Types:
- Wildfire: Forest fires affecting transmission/plant operations
- Tropical Cyclone: Typhoons causing wind damage and outages
- River Flood: Riverine flooding from precipitation
- Coastal Flood: Storm surge and coastal inundation
- Drought: Water scarcity affecting cooling capacity
- Heat Stress: Extreme heat reducing efficiency
- Sea Level Rise: Long-term coastal exposure

Data Sources (from CSV):
- CLIMADA Python library (ETH Zurich)
- Korea Meteorological Administration (KMA)
- Korea Forest Service (KFS)
- IPCC AR6 Working Group I
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, List, Tuple
import math

from src.data.loaders import (
    load_hazard_baselines,
    load_climate_factors,
    get_climate_factor as _get_climate_factor,
    HazardBaseline,
    ClimateFactor,
)


class HazardType(Enum):
    """Types of physical hazards affecting power plants."""
    WILDFIRE = "wildfire"
    TROPICAL_CYCLONE = "tropical_cyclone"
    RIVER_FLOOD = "river_flood"
    COASTAL_FLOOD = "coastal_flood"
    DROUGHT = "drought"
    HEAT_STRESS = "heat_stress"
    SEA_LEVEL_RISE = "sea_level_rise"


class ImpactType(Enum):
    """Types of impacts on power plant operations."""
    OUTAGE = "outage"              # Forced shutdown (hours/year)
    CAPACITY_DERATE = "derate"     # Reduced output capacity
    EFFICIENCY_LOSS = "efficiency" # Reduced thermal efficiency
    DAMAGE = "damage"              # Physical asset damage


@dataclass
class HazardParameters:
    """
    Physical parameters for a hazard type.

    Attributes:
        intensity_unit: Unit of hazard intensity (e.g., "m/s", "mm", "°C")
        threshold_low: Intensity below which no impact
        threshold_high: Intensity at which maximum impact
        return_period_years: Statistical return period for extreme events
    """
    intensity_unit: str
    threshold_low: float
    threshold_high: float
    return_period_years: float = 100.0


@dataclass
class HazardResult:
    """
    Result from hazard analysis.

    Attributes:
        hazard_type: Type of hazard
        base_frequency: Annual event frequency (events/year)
        base_intensity: Average event intensity
        intensity_unit: Unit of intensity measurement
        outage_rate: Annual outage rate (fraction, 0-1)
        capacity_derate: Capacity reduction (fraction, 0-1)
        efficiency_loss: Efficiency reduction (fraction, 0-1)
        damage_ratio: Asset damage ratio (fraction, 0-1)
        confidence_low: Lower bound (10th percentile)
        confidence_high: Upper bound (90th percentile)
        source: Data source citation
        methodology: Calculation methodology
        climada_events: Number of events from CLIMADA
        climada_years: Years covered by CLIMADA data
    """
    hazard_type: HazardType
    base_frequency: float
    base_intensity: float
    intensity_unit: str
    outage_rate: float
    capacity_derate: float
    efficiency_loss: float
    damage_ratio: float = 0.0
    confidence_low: float = 0.0
    confidence_high: float = 0.0
    source: str = ""
    methodology: str = ""
    climada_events: int = 0
    climada_years: int = 40

    @property
    def total_annual_impact(self) -> float:
        """Combined annual impact (outage + derate + efficiency loss)."""
        return self.outage_rate + self.capacity_derate + self.efficiency_loss


# =============================================================================
# HAZARD PARAMETERS (Physical thresholds) - These are physical constants
# =============================================================================

HAZARD_PARAMETERS: Dict[HazardType, HazardParameters] = {
    HazardType.WILDFIRE: HazardParameters(
        intensity_unit="FWI",  # Fire Weather Index
        threshold_low=15.0,    # FWI below 15 = low risk
        threshold_high=50.0,   # FWI above 50 = extreme
        return_period_years=10.0,
    ),
    HazardType.TROPICAL_CYCLONE: HazardParameters(
        intensity_unit="m/s",  # Maximum sustained wind
        threshold_low=17.0,    # Tropical storm threshold
        threshold_high=50.0,   # Category 3+ equivalent
        return_period_years=25.0,
    ),
    HazardType.RIVER_FLOOD: HazardParameters(
        intensity_unit="m",    # Flood depth
        threshold_low=0.5,     # 50cm starts causing issues
        threshold_high=3.0,    # 3m = severe damage
        return_period_years=100.0,
    ),
    HazardType.COASTAL_FLOOD: HazardParameters(
        intensity_unit="m",    # Storm surge height
        threshold_low=1.0,     # 1m surge
        threshold_high=5.0,    # 5m surge = catastrophic
        return_period_years=100.0,
    ),
    HazardType.DROUGHT: HazardParameters(
        intensity_unit="SPI",  # Standardized Precipitation Index
        threshold_low=-1.0,    # Moderate drought
        threshold_high=-2.0,   # Extreme drought
        return_period_years=20.0,
    ),
    HazardType.HEAT_STRESS: HazardParameters(
        intensity_unit="°C",   # Temperature
        threshold_low=35.0,    # Heat wave threshold
        threshold_high=45.0,   # Extreme heat
        return_period_years=5.0,
    ),
    HazardType.SEA_LEVEL_RISE: HazardParameters(
        intensity_unit="m",    # SLR in meters
        threshold_low=0.3,     # 30cm SLR
        threshold_high=1.0,    # 1m SLR
        return_period_years=0.0,  # Not event-based
    ),
}


# =============================================================================
# DATA ACCESS FUNCTIONS (Load from CSV)
# =============================================================================

def _convert_baseline_to_result(baseline: HazardBaseline) -> HazardResult:
    """Convert CSV HazardBaseline to HazardResult."""
    hazard_type = HazardType(baseline.hazard_type)
    return HazardResult(
        hazard_type=hazard_type,
        base_frequency=baseline.base_frequency,
        base_intensity=baseline.base_intensity,
        intensity_unit=baseline.intensity_unit,
        outage_rate=baseline.outage_rate,
        capacity_derate=baseline.capacity_derate,
        efficiency_loss=baseline.efficiency_loss,
        damage_ratio=baseline.damage_ratio,
        confidence_low=baseline.confidence_low,
        confidence_high=baseline.confidence_high,
        source=baseline.source,
        methodology=baseline.methodology,
        climada_events=baseline.climada_events,
        climada_years=baseline.climada_years,
    )


def get_hazard_baselines() -> Dict[HazardType, HazardResult]:
    """
    Get hazard baselines loaded from CSV.

    Returns:
        Dict mapping HazardType to HazardResult
    """
    csv_baselines = load_hazard_baselines()
    return {
        HazardType(k): _convert_baseline_to_result(v)
        for k, v in csv_baselines.items()
    }


# Legacy compatibility: HAZARD_BASELINES as a property-like access
class _HazardBaselineDict(dict):
    """Lazy-loading dict for hazard baselines."""
    _loaded = False

    def _ensure_loaded(self):
        if not self._loaded:
            self.update(get_hazard_baselines())
            self._loaded = True

    def get(self, key, default=None):
        self._ensure_loaded()
        return super().get(key, default)

    def __getitem__(self, key):
        self._ensure_loaded()
        return super().__getitem__(key)

    def keys(self):
        self._ensure_loaded()
        return super().keys()

    def values(self):
        self._ensure_loaded()
        return super().values()

    def items(self):
        self._ensure_loaded()
        return super().items()

    def __iter__(self):
        self._ensure_loaded()
        return super().__iter__()

    def __contains__(self, key):
        self._ensure_loaded()
        return super().__contains__(key)


HAZARD_BASELINES = _HazardBaselineDict()


# =============================================================================
# CLIMATE CHANGE FACTORS (Load from CSV)
# =============================================================================

@dataclass
class ClimateFactorSet:
    """Climate change factors for all hazards at a given year."""
    year: int
    scenario: str
    wildfire: float = 1.0
    tropical_cyclone: float = 1.0
    river_flood: float = 1.0
    coastal_flood: float = 1.0
    drought: float = 1.0
    heat_stress: float = 1.0
    slr_meters: float = 0.0
    source: str = ""

    def get_factor(self, hazard: HazardType) -> float:
        """Get climate factor for a specific hazard."""
        mapping = {
            HazardType.WILDFIRE: self.wildfire,
            HazardType.TROPICAL_CYCLONE: self.tropical_cyclone,
            HazardType.RIVER_FLOOD: self.river_flood,
            HazardType.COASTAL_FLOOD: self.coastal_flood,
            HazardType.DROUGHT: self.drought,
            HazardType.HEAT_STRESS: self.heat_stress,
            HazardType.SEA_LEVEL_RISE: 1.0,  # SLR uses absolute value
        }
        return mapping.get(hazard, 1.0)


# Backward compatibility: CLIMATE_FACTORS as lazy-loading dict
class _ClimateFactorsDict(dict):
    """Lazy-loading dict for climate factors, backwards compatible."""
    _loaded = False

    def _ensure_loaded(self):
        if not self._loaded:
            all_factors = load_climate_factors()
            # Convert to the old format: {scenario: {year: ClimateFactorSet}}
            for scenario, year_factors in all_factors.items():
                self[scenario] = {}
                for year, factor in year_factors.items():
                    self[scenario][year] = ClimateFactorSet(
                        year=year,
                        scenario=scenario,
                        wildfire=factor.wildfire,
                        tropical_cyclone=factor.tropical_cyclone,
                        river_flood=factor.river_flood,
                        coastal_flood=factor.coastal_flood,
                        drought=factor.drought,
                        heat_stress=factor.heat_stress,
                        slr_meters=factor.slr_meters,
                        source=factor.source,
                    )
            self._loaded = True

    def get(self, key, default=None):
        self._ensure_loaded()
        return super().get(key, default)

    def __getitem__(self, key):
        self._ensure_loaded()
        return super().__getitem__(key)

    def keys(self):
        self._ensure_loaded()
        return super().keys()

    def values(self):
        self._ensure_loaded()
        return super().values()

    def items(self):
        self._ensure_loaded()
        return super().items()

    def __contains__(self, key):
        self._ensure_loaded()
        return super().__contains__(key)


CLIMATE_FACTORS = _ClimateFactorsDict()


def get_climate_factor(
    hazard: HazardType,
    year: int,
    rcp: str = "RCP8.5"
) -> float:
    """
    Get climate change factor for a hazard at a given year.

    Args:
        hazard: Type of hazard
        year: Target year
        rcp: RCP/SSP scenario (e.g., "RCP4.5", "RCP8.5", "SSP5-8.5")

    Returns:
        Climate change multiplier (1.0 = no change from baseline)
    """
    hazard_str = hazard.value if isinstance(hazard, HazardType) else hazard
    return _get_climate_factor(hazard_str, year, rcp)


def get_slr_projection(year: int, rcp: str = "RCP8.5") -> float:
    """
    Get sea level rise projection in meters.

    Args:
        year: Target year
        rcp: RCP scenario

    Returns:
        SLR in meters above 2024 baseline
    """
    all_factors = load_climate_factors()

    if rcp not in all_factors:
        rcp = "RCP8.5"

    factors = all_factors[rcp]
    years = sorted(factors.keys())

    if year <= years[0]:
        return factors[years[0]].slr_meters
    if year >= years[-1]:
        return factors[years[-1]].slr_meters

    # Linear interpolation
    for i, y in enumerate(years[:-1]):
        if years[i] <= year < years[i + 1]:
            y0, y1 = years[i], years[i + 1]
            s0 = factors[y0].slr_meters
            s1 = factors[y1].slr_meters
            return s0 + (s1 - s0) * (year - y0) / (y1 - y0)

    return 0.0


def get_climate_factor_set(year: int, rcp: str = "RCP8.5") -> ClimateFactorSet:
    """
    Get complete climate factor set for a year.

    Args:
        year: Target year
        rcp: RCP scenario

    Returns:
        ClimateFactorSet with all hazard factors
    """
    all_factors = load_climate_factors()

    if rcp not in all_factors:
        rcp = "RCP8.5"

    factors = all_factors[rcp]
    years = sorted(factors.keys())

    # Exact match
    if year in factors:
        f = factors[year]
        return ClimateFactorSet(
            year=year,
            scenario=rcp,
            wildfire=f.wildfire,
            tropical_cyclone=f.tropical_cyclone,
            river_flood=f.river_flood,
            coastal_flood=f.coastal_flood,
            drought=f.drought,
            heat_stress=f.heat_stress,
            slr_meters=f.slr_meters,
            source=f.source,
        )

    if year <= years[0]:
        f = factors[years[0]]
        return ClimateFactorSet(
            year=year, scenario=rcp,
            wildfire=f.wildfire, tropical_cyclone=f.tropical_cyclone,
            river_flood=f.river_flood, coastal_flood=f.coastal_flood,
            drought=f.drought, heat_stress=f.heat_stress,
            slr_meters=f.slr_meters, source=f.source,
        )

    if year >= years[-1]:
        f = factors[years[-1]]
        return ClimateFactorSet(
            year=year, scenario=rcp,
            wildfire=f.wildfire, tropical_cyclone=f.tropical_cyclone,
            river_flood=f.river_flood, coastal_flood=f.coastal_flood,
            drought=f.drought, heat_stress=f.heat_stress,
            slr_meters=f.slr_meters, source=f.source,
        )

    # Interpolate all values
    for i, y in enumerate(years[:-1]):
        if years[i] <= year < years[i + 1]:
            y0, y1 = years[i], years[i + 1]
            f0, f1 = factors[y0], factors[y1]
            weight = (year - y0) / (y1 - y0)

            return ClimateFactorSet(
                year=year,
                scenario=rcp,
                wildfire=f0.wildfire + weight * (f1.wildfire - f0.wildfire),
                tropical_cyclone=f0.tropical_cyclone + weight * (f1.tropical_cyclone - f0.tropical_cyclone),
                river_flood=f0.river_flood + weight * (f1.river_flood - f0.river_flood),
                coastal_flood=f0.coastal_flood + weight * (f1.coastal_flood - f0.coastal_flood),
                drought=f0.drought + weight * (f1.drought - f0.drought),
                heat_stress=f0.heat_stress + weight * (f1.heat_stress - f0.heat_stress),
                slr_meters=f0.slr_meters + weight * (f1.slr_meters - f0.slr_meters),
                source=f"Interpolated from {y0} and {y1}",
            )

    f = factors[years[-1]]
    return ClimateFactorSet(
        year=year, scenario=rcp,
        wildfire=f.wildfire, tropical_cyclone=f.tropical_cyclone,
        river_flood=f.river_flood, coastal_flood=f.coastal_flood,
        drought=f.drought, heat_stress=f.heat_stress,
        slr_meters=f.slr_meters, source=f.source,
    )


# =============================================================================
# PROJECTED HAZARD CALCULATION
# =============================================================================

def calculate_projected_hazard(
    hazard: HazardType,
    year: int,
    rcp: str = "RCP8.5",
) -> HazardResult:
    """
    Calculate projected hazard for a given year and scenario.

    Applies climate change factors to baseline hazard data.

    Args:
        hazard: Type of hazard
        year: Target year
        rcp: RCP scenario

    Returns:
        HazardResult with projected values
    """
    baseline = HAZARD_BASELINES.get(hazard)
    if not baseline:
        raise ValueError(f"No baseline data for hazard: {hazard}")

    climate_factor = get_climate_factor(hazard, year, rcp)

    # Project outage rate
    projected_outage = baseline.outage_rate * climate_factor

    # Project capacity derate
    projected_derate = baseline.capacity_derate * climate_factor

    # Project efficiency loss
    projected_efficiency = baseline.efficiency_loss * climate_factor

    # Project damage ratio
    projected_damage = baseline.damage_ratio * climate_factor

    # Adjust confidence intervals
    conf_low = baseline.confidence_low * climate_factor
    conf_high = baseline.confidence_high * climate_factor

    return HazardResult(
        hazard_type=hazard,
        base_frequency=baseline.base_frequency * math.sqrt(climate_factor),
        base_intensity=baseline.base_intensity,
        intensity_unit=baseline.intensity_unit,
        outage_rate=projected_outage,
        capacity_derate=projected_derate,
        efficiency_loss=projected_efficiency,
        damage_ratio=projected_damage,
        confidence_low=conf_low,
        confidence_high=conf_high,
        source=f"{baseline.source} + {rcp} {year} projection",
        methodology=baseline.methodology,
        climada_events=baseline.climada_events,
        climada_years=baseline.climada_years,
    )

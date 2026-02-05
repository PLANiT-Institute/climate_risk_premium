"""
Korea-Specific Climate Data and Projections.

Official data sources from Korean government agencies and research institutions:
- KMA (Korea Meteorological Administration / 기상청)
- NIMS (National Institute of Meteorological Sciences / 국립기상과학원)
- NIER (National Institute of Environmental Research / 국립환경과학원)
- KFS (Korea Forest Service / 산림청)
- KHOA (Korea Hydrographic and Oceanographic Agency / 국립해양조사원)

Literature Sources:
- KMA Climate Change Scenarios for Korea (2020)
- IPCC AR6 East Asia Regional Assessment
- National Climate Change Adaptation Plans (2nd, 3rd)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class KoreaRegion(Enum):
    """Administrative regions of Korea for climate analysis."""
    NATIONAL = "national"
    SEOUL = "seoul"
    GANGWON = "gangwon"           # East coast (Samcheok)
    CHUNGNAM = "chungnam"         # West coast (Dangjin, Taean, Boryeong)
    GYEONGNAM = "gyeongnam"       # South coast (Hadong)
    JEJU = "jeju"


@dataclass
class KoreaClimateProjection:
    """
    Korea-specific climate projection data.

    All values are projections from KMA/NIMS climate scenarios.

    Attributes:
        region: Administrative region
        year: Target year
        scenario: RCP or SSP scenario
        temp_increase_c: Temperature increase from 1991-2020 baseline (°C)
        precip_change_pct: Precipitation change from baseline (%)
        extreme_heat_days: Days with Tmax > 33°C
        tropical_nights: Days with Tmin > 25°C
        heavy_rain_days: Days with precip > 80mm
        drought_frequency: Drought events per decade
        source: Data source citation
    """
    region: KoreaRegion
    year: int
    scenario: str
    temp_increase_c: float
    precip_change_pct: float
    extreme_heat_days: float
    tropical_nights: float
    heavy_rain_days: float
    drought_frequency: float
    source: str


@dataclass
class KoreaSeaLevelProjection:
    """
    Korea coastal sea level rise projections.

    Sources: KHOA, IPCC AR6, NASA/GSFC

    Attributes:
        region: Coastal region
        year: Target year
        scenario: RCP or SSP scenario
        slr_cm: Sea level rise in centimeters from 1995-2014 baseline
        slr_low_cm: Low estimate (17th percentile)
        slr_high_cm: High estimate (83rd percentile)
        source: Data source citation
    """
    region: str
    year: int
    scenario: str
    slr_cm: float
    slr_low_cm: float
    slr_high_cm: float
    source: str


@dataclass
class KoreaTyphoonProjection:
    """
    Korea typhoon (tropical cyclone) projections.

    Based on KMA analysis and IPCC AR6 projections.

    Attributes:
        region: Coastal region
        year: Target year
        scenario: RCP or SSP scenario
        frequency_change_pct: Change in annual typhoon frequency (%)
        intensity_change_pct: Change in max wind speed (%)
        precip_intensity_change_pct: Change in associated rainfall (%)
        track_shift_km: Northward shift in median track (km)
        source: Data source citation
    """
    region: str
    year: int
    scenario: str
    frequency_change_pct: float
    intensity_change_pct: float
    precip_intensity_change_pct: float
    track_shift_km: float
    source: str


@dataclass
class KoreaWildfireProjection:
    """
    Korea wildfire risk projections.

    Source: Korea Forest Service (KFS) forest fire statistics
    and climate-fire modeling.

    Attributes:
        region: Administrative region
        year: Target year
        scenario: RCP or SSP scenario
        fire_risk_index_change: FWI change from baseline
        fire_days_change_pct: Change in high-risk fire days (%)
        area_burned_change_pct: Change in expected burned area (%)
        source: Data source citation
    """
    region: KoreaRegion
    year: int
    scenario: str
    fire_risk_index_change: float
    fire_days_change_pct: float
    area_burned_change_pct: float
    source: str


# =============================================================================
# KOREA CLIMATE PROJECTIONS (KMA/NIMS Data)
# =============================================================================
# Source: KMA Climate Change Scenarios for Korean Peninsula (2020)
# Baseline: 1991-2020 average

KOREA_CLIMATE_PROJECTIONS: Dict[str, Dict[int, KoreaClimateProjection]] = {
    # RCP4.5 scenario (moderate mitigation)
    "RCP4.5": {
        2024: KoreaClimateProjection(
            region=KoreaRegion.NATIONAL, year=2024, scenario="RCP4.5",
            temp_increase_c=0.0,       # Baseline
            precip_change_pct=0.0,
            extreme_heat_days=11.8,    # Current average
            tropical_nights=8.4,
            heavy_rain_days=2.8,
            drought_frequency=2.0,
            source="KMA Climate Normal 1991-2020",
        ),
        2030: KoreaClimateProjection(
            region=KoreaRegion.NATIONAL, year=2030, scenario="RCP4.5",
            temp_increase_c=0.6,
            precip_change_pct=3.0,
            extreme_heat_days=14.2,
            tropical_nights=11.5,
            heavy_rain_days=3.1,
            drought_frequency=2.2,
            source="KMA Climate Projection Report 2020",
        ),
        2050: KoreaClimateProjection(
            region=KoreaRegion.NATIONAL, year=2050, scenario="RCP4.5",
            temp_increase_c=1.4,
            precip_change_pct=6.0,
            extreme_heat_days=22.5,
            tropical_nights=23.4,
            heavy_rain_days=3.8,
            drought_frequency=2.5,
            source="KMA Climate Projection Report 2020",
        ),
        2100: KoreaClimateProjection(
            region=KoreaRegion.NATIONAL, year=2100, scenario="RCP4.5",
            temp_increase_c=2.3,
            precip_change_pct=9.0,
            extreme_heat_days=35.1,
            tropical_nights=42.6,
            heavy_rain_days=4.6,
            drought_frequency=3.0,
            source="KMA Climate Projection Report 2020",
        ),
    },
    # RCP8.5 scenario (high emissions)
    "RCP8.5": {
        2024: KoreaClimateProjection(
            region=KoreaRegion.NATIONAL, year=2024, scenario="RCP8.5",
            temp_increase_c=0.0,       # Baseline
            precip_change_pct=0.0,
            extreme_heat_days=11.8,
            tropical_nights=8.4,
            heavy_rain_days=2.8,
            drought_frequency=2.0,
            source="KMA Climate Normal 1991-2020",
        ),
        2030: KoreaClimateProjection(
            region=KoreaRegion.NATIONAL, year=2030, scenario="RCP8.5",
            temp_increase_c=0.8,
            precip_change_pct=4.0,
            extreme_heat_days=16.5,
            tropical_nights=14.2,
            heavy_rain_days=3.3,
            drought_frequency=2.4,
            source="KMA Climate Projection Report 2020",
        ),
        2050: KoreaClimateProjection(
            region=KoreaRegion.NATIONAL, year=2050, scenario="RCP8.5",
            temp_increase_c=2.0,
            precip_change_pct=10.0,
            extreme_heat_days=35.5,
            tropical_nights=37.2,
            heavy_rain_days=4.5,
            drought_frequency=3.2,
            source="KMA Climate Projection Report 2020",
        ),
        2100: KoreaClimateProjection(
            region=KoreaRegion.NATIONAL, year=2100, scenario="RCP8.5",
            temp_increase_c=4.7,
            precip_change_pct=18.0,
            extreme_heat_days=67.4,
            tropical_nights=85.2,
            heavy_rain_days=6.8,
            drought_frequency=4.5,
            source="KMA Climate Projection Report 2020",
        ),
    },
}

# Regional projections for Gangwon (East coast - Samcheok area)
GANGWON_PROJECTIONS: Dict[str, Dict[int, KoreaClimateProjection]] = {
    "RCP8.5": {
        2030: KoreaClimateProjection(
            region=KoreaRegion.GANGWON, year=2030, scenario="RCP8.5",
            temp_increase_c=0.7,       # Slightly lower than national (coastal moderation)
            precip_change_pct=5.0,
            extreme_heat_days=8.5,     # Less extreme heat (coastal)
            tropical_nights=6.2,
            heavy_rain_days=3.8,       # More heavy rain (coastal)
            drought_frequency=2.0,
            source="KMA Regional Projection - Gangwon 2020",
        ),
        2050: KoreaClimateProjection(
            region=KoreaRegion.GANGWON, year=2050, scenario="RCP8.5",
            temp_increase_c=1.8,
            precip_change_pct=12.0,
            extreme_heat_days=22.3,
            tropical_nights=18.5,
            heavy_rain_days=5.2,
            drought_frequency=2.8,
            source="KMA Regional Projection - Gangwon 2020",
        ),
    },
}


# =============================================================================
# KOREA SEA LEVEL RISE PROJECTIONS
# =============================================================================
# Source: KHOA (Korea Hydrographic and Oceanographic Agency)
# and IPCC AR6 East Asia regional assessment

KOREA_SLR_PROJECTIONS: Dict[str, Dict[int, KoreaSeaLevelProjection]] = {
    "RCP4.5": {
        2030: KoreaSeaLevelProjection(
            region="East Coast (Gangwon)", year=2030, scenario="RCP4.5",
            slr_cm=8.0, slr_low_cm=5.0, slr_high_cm=12.0,
            source="KHOA Sea Level Bulletin 2023 + IPCC AR6",
        ),
        2050: KoreaSeaLevelProjection(
            region="East Coast (Gangwon)", year=2050, scenario="RCP4.5",
            slr_cm=20.0, slr_low_cm=14.0, slr_high_cm=28.0,
            source="KHOA + IPCC AR6 (2021)",
        ),
        2100: KoreaSeaLevelProjection(
            region="East Coast (Gangwon)", year=2100, scenario="RCP4.5",
            slr_cm=48.0, slr_low_cm=32.0, slr_high_cm=68.0,
            source="KHOA + IPCC AR6 (2021)",
        ),
    },
    "RCP8.5": {
        2030: KoreaSeaLevelProjection(
            region="East Coast (Gangwon)", year=2030, scenario="RCP8.5",
            slr_cm=10.0, slr_low_cm=6.0, slr_high_cm=15.0,
            source="KHOA + IPCC AR6 (2021)",
        ),
        2050: KoreaSeaLevelProjection(
            region="East Coast (Gangwon)", year=2050, scenario="RCP8.5",
            slr_cm=28.0, slr_low_cm=19.0, slr_high_cm=40.0,
            source="KHOA + IPCC AR6 (2021)",
        ),
        2100: KoreaSeaLevelProjection(
            region="East Coast (Gangwon)", year=2100, scenario="RCP8.5",
            slr_cm=82.0, slr_low_cm=55.0, slr_high_cm=120.0,
            source="KHOA + IPCC AR6 (2021)",
        ),
    },
}


# =============================================================================
# KOREA TYPHOON PROJECTIONS
# =============================================================================
# Source: KMA Typhoon Analysis Center, IPCC AR6

KOREA_TYPHOON_PROJECTIONS: Dict[str, Dict[int, KoreaTyphoonProjection]] = {
    "RCP4.5": {
        2030: KoreaTyphoonProjection(
            region="Korean Peninsula", year=2030, scenario="RCP4.5",
            frequency_change_pct=-5.0,      # Slight decrease in frequency
            intensity_change_pct=+5.0,      # But increased intensity
            precip_intensity_change_pct=+10.0,
            track_shift_km=50.0,            # Northward shift
            source="KMA Typhoon Analysis + IPCC AR6",
        ),
        2050: KoreaTyphoonProjection(
            region="Korean Peninsula", year=2050, scenario="RCP4.5",
            frequency_change_pct=-10.0,
            intensity_change_pct=+10.0,
            precip_intensity_change_pct=+15.0,
            track_shift_km=100.0,
            source="KMA Typhoon Analysis + IPCC AR6",
        ),
        2100: KoreaTyphoonProjection(
            region="Korean Peninsula", year=2100, scenario="RCP4.5",
            frequency_change_pct=-15.0,
            intensity_change_pct=+15.0,
            precip_intensity_change_pct=+25.0,
            track_shift_km=200.0,
            source="KMA Typhoon Analysis + IPCC AR6",
        ),
    },
    "RCP8.5": {
        2030: KoreaTyphoonProjection(
            region="Korean Peninsula", year=2030, scenario="RCP8.5",
            frequency_change_pct=-3.0,
            intensity_change_pct=+8.0,
            precip_intensity_change_pct=+12.0,
            track_shift_km=60.0,
            source="KMA Typhoon Analysis + IPCC AR6 (2021)",
        ),
        2050: KoreaTyphoonProjection(
            region="Korean Peninsula", year=2050, scenario="RCP8.5",
            frequency_change_pct=-8.0,
            intensity_change_pct=+15.0,
            precip_intensity_change_pct=+25.0,
            track_shift_km=150.0,
            source="KMA Typhoon Analysis + IPCC AR6 (2021)",
        ),
        2100: KoreaTyphoonProjection(
            region="Korean Peninsula", year=2100, scenario="RCP8.5",
            frequency_change_pct=-15.0,
            intensity_change_pct=+25.0,
            precip_intensity_change_pct=+40.0,
            track_shift_km=350.0,
            source="KMA Typhoon Analysis + IPCC AR6 (2021)",
        ),
    },
}


# =============================================================================
# KOREA WILDFIRE PROJECTIONS
# =============================================================================
# Source: Korea Forest Service (KFS) statistics
# Historical: 1980-2023 fire statistics
# Projections: Climate-fire modeling based on KMA scenarios

KOREA_WILDFIRE_PROJECTIONS: Dict[str, Dict[int, KoreaWildfireProjection]] = {
    "RCP4.5": {
        2030: KoreaWildfireProjection(
            region=KoreaRegion.GANGWON, year=2030, scenario="RCP4.5",
            fire_risk_index_change=+3.0,       # FWI increase
            fire_days_change_pct=+15.0,        # More high-risk days
            area_burned_change_pct=+20.0,
            source="KFS Forest Fire Statistics + KMA projections",
        ),
        2050: KoreaWildfireProjection(
            region=KoreaRegion.GANGWON, year=2050, scenario="RCP4.5",
            fire_risk_index_change=+8.0,
            fire_days_change_pct=+35.0,
            area_burned_change_pct=+50.0,
            source="KFS Forest Fire Statistics + KMA projections",
        ),
        2100: KoreaWildfireProjection(
            region=KoreaRegion.GANGWON, year=2100, scenario="RCP4.5",
            fire_risk_index_change=+12.0,
            fire_days_change_pct=+55.0,
            area_burned_change_pct=+85.0,
            source="KFS Forest Fire Statistics + KMA projections",
        ),
    },
    "RCP8.5": {
        2030: KoreaWildfireProjection(
            region=KoreaRegion.GANGWON, year=2030, scenario="RCP8.5",
            fire_risk_index_change=+5.0,
            fire_days_change_pct=+25.0,
            area_burned_change_pct=+35.0,
            source="KFS + KMA RCP8.5 scenario (2020)",
        ),
        2050: KoreaWildfireProjection(
            region=KoreaRegion.GANGWON, year=2050, scenario="RCP8.5",
            fire_risk_index_change=+15.0,
            fire_days_change_pct=+75.0,
            area_burned_change_pct=+120.0,
            source="KFS + KMA RCP8.5 scenario (2020)",
        ),
        2100: KoreaWildfireProjection(
            region=KoreaRegion.GANGWON, year=2100, scenario="RCP8.5",
            fire_risk_index_change=+30.0,
            fire_days_change_pct=+200.0,
            area_burned_change_pct=+350.0,
            source="KFS + KMA RCP8.5 scenario (2020)",
        ),
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_korea_climate_projection(
    year: int,
    scenario: str = "RCP8.5",
    region: KoreaRegion = KoreaRegion.NATIONAL,
) -> Dict[str, Any]:
    """
    Get Korea-specific climate projection for a year.

    Args:
        year: Target year
        scenario: RCP or SSP scenario
        region: Administrative region

    Returns:
        Dict with climate projection values
    """
    if scenario not in KOREA_CLIMATE_PROJECTIONS:
        scenario = "RCP8.5"

    projections = KOREA_CLIMATE_PROJECTIONS[scenario]
    years = sorted(projections.keys())

    # Find bracketing years
    if year <= years[0]:
        proj = projections[years[0]]
    elif year >= years[-1]:
        proj = projections[years[-1]]
    else:
        # Linear interpolation
        for i, y in enumerate(years[:-1]):
            if years[i] <= year < years[i + 1]:
                y0, y1 = years[i], years[i + 1]
                p0, p1 = projections[y0], projections[y1]
                weight = (year - y0) / (y1 - y0)

                # Interpolate key values
                return {
                    "year": year,
                    "scenario": scenario,
                    "temp_increase_c": p0.temp_increase_c + weight * (p1.temp_increase_c - p0.temp_increase_c),
                    "precip_change_pct": p0.precip_change_pct + weight * (p1.precip_change_pct - p0.precip_change_pct),
                    "extreme_heat_days": p0.extreme_heat_days + weight * (p1.extreme_heat_days - p0.extreme_heat_days),
                    "tropical_nights": p0.tropical_nights + weight * (p1.tropical_nights - p0.tropical_nights),
                    "heavy_rain_days": p0.heavy_rain_days + weight * (p1.heavy_rain_days - p0.heavy_rain_days),
                    "drought_frequency": p0.drought_frequency + weight * (p1.drought_frequency - p0.drought_frequency),
                    "source": p0.source,
                }

        proj = projections[years[-1]]

    return {
        "year": proj.year,
        "scenario": proj.scenario,
        "temp_increase_c": proj.temp_increase_c,
        "precip_change_pct": proj.precip_change_pct,
        "extreme_heat_days": proj.extreme_heat_days,
        "tropical_nights": proj.tropical_nights,
        "heavy_rain_days": proj.heavy_rain_days,
        "drought_frequency": proj.drought_frequency,
        "source": proj.source,
    }


def get_korea_slr_projection(
    year: int,
    scenario: str = "RCP8.5",
) -> Dict[str, Any]:
    """
    Get Korea sea level rise projection for a year.

    Args:
        year: Target year
        scenario: RCP scenario

    Returns:
        Dict with SLR values in cm
    """
    if scenario not in KOREA_SLR_PROJECTIONS:
        scenario = "RCP8.5"

    projections = KOREA_SLR_PROJECTIONS[scenario]
    years = sorted(projections.keys())

    # Baseline (2024)
    if year <= 2024:
        return {
            "year": year,
            "scenario": scenario,
            "slr_cm": 0.0,
            "slr_low_cm": 0.0,
            "slr_high_cm": 0.0,
            "source": "Baseline (2024)",
        }

    if year >= years[-1]:
        proj = projections[years[-1]]
    else:
        # Linear interpolation
        for i, y in enumerate(years[:-1]):
            if years[i] <= year < years[i + 1]:
                y0, y1 = years[i], years[i + 1]
                p0, p1 = projections[y0], projections[y1]
                weight = (year - y0) / (y1 - y0)

                return {
                    "year": year,
                    "scenario": scenario,
                    "slr_cm": p0.slr_cm + weight * (p1.slr_cm - p0.slr_cm),
                    "slr_low_cm": p0.slr_low_cm + weight * (p1.slr_low_cm - p0.slr_low_cm),
                    "slr_high_cm": p0.slr_high_cm + weight * (p1.slr_high_cm - p0.slr_high_cm),
                    "source": p0.source,
                }

        proj = projections[years[-1]]

    return {
        "year": proj.year,
        "scenario": proj.scenario,
        "slr_cm": proj.slr_cm,
        "slr_low_cm": proj.slr_low_cm,
        "slr_high_cm": proj.slr_high_cm,
        "source": proj.source,
    }


def get_korea_climate_factor(
    hazard_type: str,
    year: int,
    scenario: str = "RCP8.5",
) -> float:
    """
    Get Korea-specific climate change factor for a hazard.

    Converts KMA projections to multiplicative factors for risk models.

    Args:
        hazard_type: Type of hazard (wildfire, flood, tc, etc.)
        year: Target year
        scenario: RCP scenario

    Returns:
        Multiplicative climate change factor (1.0 = baseline)
    """
    climate = get_korea_climate_projection(year, scenario)

    # Convert projections to multiplicative factors
    if hazard_type == "wildfire":
        # Wildfire scales with temperature and drought
        temp_factor = 1.0 + 0.15 * climate["temp_increase_c"]  # +15% per degree
        return temp_factor

    elif hazard_type == "tropical_cyclone":
        # TC intensity increases with warming
        tc_proj = KOREA_TYPHOON_PROJECTIONS.get(scenario, {}).get(
            min(2100, max(2030, (year // 10) * 10)),
            None
        )
        if tc_proj:
            return 1.0 + tc_proj.intensity_change_pct / 100
        return 1.0 + 0.05 * climate["temp_increase_c"]

    elif hazard_type == "flood" or hazard_type == "river_flood":
        # Flood scales with heavy rain days
        baseline_rain = 2.8  # 2024 baseline
        return climate["heavy_rain_days"] / baseline_rain

    elif hazard_type == "drought":
        # Drought scales with frequency
        baseline_drought = 2.0
        return climate["drought_frequency"] / baseline_drought

    elif hazard_type == "heat_stress":
        # Heat stress scales with extreme heat days
        baseline_heat = 11.8
        return climate["extreme_heat_days"] / baseline_heat

    elif hazard_type == "coastal_flood":
        # Coastal flood scales with SLR
        slr = get_korea_slr_projection(year, scenario)
        # Each 10cm SLR increases coastal flood risk by ~20%
        return 1.0 + (slr["slr_cm"] / 10) * 0.2

    else:
        # Default: scale with temperature
        return 1.0 + 0.1 * climate["temp_increase_c"]


def get_korea_summary(year: int, scenario: str = "RCP8.5") -> Dict[str, Any]:
    """
    Get comprehensive Korea climate summary for a year.

    Args:
        year: Target year
        scenario: RCP scenario

    Returns:
        Dict with all climate projections
    """
    climate = get_korea_climate_projection(year, scenario)
    slr = get_korea_slr_projection(year, scenario)

    # Get typhoon projection for nearest decade
    decade = min(2100, max(2030, (year // 10) * 10))
    tc_proj = KOREA_TYPHOON_PROJECTIONS.get(scenario, {}).get(decade)

    # Get wildfire projection
    fire_proj = KOREA_WILDFIRE_PROJECTIONS.get(scenario, {}).get(decade)

    return {
        "year": year,
        "scenario": scenario,
        "temperature": {
            "increase_c": climate["temp_increase_c"],
            "extreme_heat_days": climate["extreme_heat_days"],
            "tropical_nights": climate["tropical_nights"],
        },
        "precipitation": {
            "change_pct": climate["precip_change_pct"],
            "heavy_rain_days": climate["heavy_rain_days"],
        },
        "drought": {
            "frequency_per_decade": climate["drought_frequency"],
        },
        "sea_level": {
            "rise_cm": slr["slr_cm"],
            "rise_low_cm": slr["slr_low_cm"],
            "rise_high_cm": slr["slr_high_cm"],
        },
        "typhoon": {
            "frequency_change_pct": tc_proj.frequency_change_pct if tc_proj else 0.0,
            "intensity_change_pct": tc_proj.intensity_change_pct if tc_proj else 0.0,
        },
        "wildfire": {
            "fire_days_change_pct": fire_proj.fire_days_change_pct if fire_proj else 0.0,
            "area_burned_change_pct": fire_proj.area_burned_change_pct if fire_proj else 0.0,
        },
        "climate_factors": {
            "wildfire": get_korea_climate_factor("wildfire", year, scenario),
            "tropical_cyclone": get_korea_climate_factor("tropical_cyclone", year, scenario),
            "flood": get_korea_climate_factor("flood", year, scenario),
            "drought": get_korea_climate_factor("drought", year, scenario),
            "heat_stress": get_korea_climate_factor("heat_stress", year, scenario),
            "coastal_flood": get_korea_climate_factor("coastal_flood", year, scenario),
        },
        "sources": [
            climate["source"],
            slr["source"],
            tc_proj.source if tc_proj else "N/A",
            fire_proj.source if fire_proj else "N/A",
        ],
    }

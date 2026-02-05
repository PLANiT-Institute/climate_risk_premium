"""
Physical Risk Module.

Handles climate hazards, scenarios, and damage functions.
All climate-related risk modeling is centralized here.

Structure:
- model.py: PhysicalRiskModel class
- hazards.py: Hazard definitions and CLIMADA baselines
- climada_api.py: CLIMADA interface and data fetching
- temperature.py: Temperature efficiency model
- scenarios/: Climate scenarios (RCP, SSP)
- damage_functions/: Selectable damage functions by hazard type
"""

from .model import PhysicalRiskModel
from .hazards import (
    HazardType,
    HazardResult,
    HazardParameters,
    HAZARD_BASELINES,
    HAZARD_PARAMETERS,
    CLIMATE_FACTORS,
    ClimateFactorSet,
    get_climate_factor,
    get_climate_factor_set,
    get_slr_projection,
    calculate_projected_hazard,
)
from .climada_api import (
    CLIMADAInterface,
    CLIMADAConfig,
    CLIMADASource,
    LocationQuery,
    HazardDataset,
    KOREA_LOCATIONS,
    get_climada_data,
    get_korea_power_plant_hazards,
    check_climada_installation,
)
from .compound_risk import (
    CompoundRiskModel,
    CompoundEventType,
    CompoundEventConfig,
    CompoundRiskResult,
    COMPOUND_EVENTS,
    calculate_portfolio_compound_risk,
)
from .korea_climate import (
    KoreaRegion,
    KoreaClimateProjection,
    KoreaSeaLevelProjection,
    KoreaTyphoonProjection,
    KoreaWildfireProjection,
    KOREA_CLIMATE_PROJECTIONS,
    KOREA_SLR_PROJECTIONS,
    KOREA_TYPHOON_PROJECTIONS,
    KOREA_WILDFIRE_PROJECTIONS,
    get_korea_climate_projection,
    get_korea_slr_projection,
    get_korea_climate_factor,
    get_korea_summary,
)
from .exposure import (
    PlantType,
    CoolingSystem,
    VulnerabilityClass,
    AssetValue,
    GeographicExposure,
    OperationalExposure,
    PhysicalVulnerability,
    AdaptiveCapacity,
    PowerPlantExposure,
    SAMCHEOK_BLUE_POWER,
    KOREA_COAL_PLANTS,
    calculate_vulnerability_factor,
    calculate_expected_damage,
    get_korea_total_coal_exposure,
)
from .temperature import TemperatureModel, TEMPERATURE_PROJECTIONS

# Climate scenarios
from .scenarios import (
    ClimateScenario,
    RCPScenario,
    SSPScenario,
    RCP_SCENARIOS,
    SSP_SCENARIOS,
)

# Damage functions
from .damage_functions import (
    DamageFunctionRegistry,
    FWILinearFunction,
    FWIExponentialFunction,
    KoreaForestServiceFunction,
    DepthDamageFunction,
    DurationDamageFunction,
    WindSpeedPowerFunction,
    HollandWindFunction,
)

__all__ = [
    # Model
    "PhysicalRiskModel",
    # Hazards
    "HazardType",
    "HazardResult",
    "HazardParameters",
    "HAZARD_BASELINES",
    "HAZARD_PARAMETERS",
    "CLIMATE_FACTORS",
    "ClimateFactorSet",
    "get_climate_factor",
    "get_climate_factor_set",
    "get_slr_projection",
    "calculate_projected_hazard",
    # CLIMADA API
    "CLIMADAInterface",
    "CLIMADAConfig",
    "CLIMADASource",
    "LocationQuery",
    "HazardDataset",
    "KOREA_LOCATIONS",
    "get_climada_data",
    "get_korea_power_plant_hazards",
    "check_climada_installation",
    # Compound Risk
    "CompoundRiskModel",
    "CompoundEventType",
    "CompoundEventConfig",
    "CompoundRiskResult",
    "COMPOUND_EVENTS",
    "calculate_portfolio_compound_risk",
    # Korea Climate
    "KoreaRegion",
    "KoreaClimateProjection",
    "KoreaSeaLevelProjection",
    "KoreaTyphoonProjection",
    "KoreaWildfireProjection",
    "KOREA_CLIMATE_PROJECTIONS",
    "KOREA_SLR_PROJECTIONS",
    "KOREA_TYPHOON_PROJECTIONS",
    "KOREA_WILDFIRE_PROJECTIONS",
    "get_korea_climate_projection",
    "get_korea_slr_projection",
    "get_korea_climate_factor",
    "get_korea_summary",
    # Exposure and Vulnerability
    "PlantType",
    "CoolingSystem",
    "VulnerabilityClass",
    "AssetValue",
    "GeographicExposure",
    "OperationalExposure",
    "PhysicalVulnerability",
    "AdaptiveCapacity",
    "PowerPlantExposure",
    "SAMCHEOK_BLUE_POWER",
    "KOREA_COAL_PLANTS",
    "calculate_vulnerability_factor",
    "calculate_expected_damage",
    "get_korea_total_coal_exposure",
    # Temperature
    "TemperatureModel",
    "TEMPERATURE_PROJECTIONS",
    # Scenarios
    "ClimateScenario",
    "RCPScenario",
    "SSPScenario",
    "RCP_SCENARIOS",
    "SSP_SCENARIOS",
    # Damage functions
    "DamageFunctionRegistry",
    "FWILinearFunction",
    "FWIExponentialFunction",
    "KoreaForestServiceFunction",
    "DepthDamageFunction",
    "DurationDamageFunction",
    "WindSpeedPowerFunction",
    "HollandWindFunction",
]

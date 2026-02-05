"""
Damage Function Module.

Provides selectable damage functions for each hazard type.
All functions are backed by literature sources.

Available damage functions by hazard:
- Wildfire: FWI-based (linear, exponential), Korea Forest Service
- Flood: Depth-damage (HAZUS), Duration-weighted
- Tropical Cyclone: Wind power law, Holland profile, Korea typhoon
- Drought: SPEI-based, Water stress, Korea drought
- Heat Stress: Temperature-efficiency, Heat wave capacity, Korea heat

See docs/sources/DAMAGE_FUNCTIONS.md for full citations.
"""

from .base import (
    DamageFunctionRegistry,
    SigmoidDamageFunction,
    EmanuelWindDamage,
    CLIMADAWildfireDamage,
    CLIMADAFloodDamage,
    SIGMOID_CALIBRATION_PARAMS,
)
from .wildfire import (
    WildfireDamageFunction,
    FWILinearFunction,
    FWIExponentialFunction,
    KoreaForestServiceFunction,
)
from .flood import (
    FloodDamageFunction,
    DepthDamageFunction,
    DurationDamageFunction,
    SamcheokFloodFunction,
)
from .tropical_cyclone import (
    TCDamageFunction,
    WindSpeedPowerFunction,
    HollandWindFunction,
    KoreaTyphooneFunction,
)
from .drought import (
    DroughtDamageFunction,
    SPEIDamageFunction,
    WaterStressDamageFunction,
    KoreaDroughtFunction,
    DROUGHT_PARAMETER_UNCERTAINTY,
)
from .heat_stress import (
    HeatStressDamageFunction,
    TemperatureEfficiencyFunction,
    HeatWaveCapacityFunction,
    AnnualizedHeatImpactFunction,
    KoreaHeatStressFunction,
    HEAT_STRESS_PARAMETER_UNCERTAINTY,
)

__all__ = [
    # Base and Sigmoid
    "DamageFunctionRegistry",
    "SigmoidDamageFunction",
    "EmanuelWindDamage",
    "CLIMADAWildfireDamage",
    "CLIMADAFloodDamage",
    "SIGMOID_CALIBRATION_PARAMS",
    # Wildfire
    "WildfireDamageFunction",
    "FWILinearFunction",
    "FWIExponentialFunction",
    "KoreaForestServiceFunction",
    # Flood
    "FloodDamageFunction",
    "DepthDamageFunction",
    "DurationDamageFunction",
    "SamcheokFloodFunction",
    # Tropical Cyclone
    "TCDamageFunction",
    "WindSpeedPowerFunction",
    "HollandWindFunction",
    "KoreaTyphooneFunction",
    # Drought
    "DroughtDamageFunction",
    "SPEIDamageFunction",
    "WaterStressDamageFunction",
    "KoreaDroughtFunction",
    "DROUGHT_PARAMETER_UNCERTAINTY",
    # Heat Stress
    "HeatStressDamageFunction",
    "TemperatureEfficiencyFunction",
    "HeatWaveCapacityFunction",
    "AnnualizedHeatImpactFunction",
    "KoreaHeatStressFunction",
    "HEAT_STRESS_PARAMETER_UNCERTAINTY",
]

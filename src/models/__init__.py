"""
Climate Risk Premium Models.

Class-based architecture for transition and physical risk modeling.

Structure:
- transition/: Korea Power Plan-based dispatch reductions
- physical/: Climate hazards, scenarios, and damage functions

Usage:
    >>> from src.models import ClimateRiskAPI
    >>> api = ClimateRiskAPI()
    >>> api.configure(
    ...     climate_scenario="RCP8.5",
    ...     power_plan="10th_basic_plan"
    ... )
    >>> result = api.calculate(year=2050)
"""

from .base import BaseRiskModel, BaseScenario, BaseDamageFunction, RiskResult, RiskType
from .api import ClimateRiskAPI, CombinedRiskResult

# Transition risk (Korea Power Plan)
from .transition import (
    TransitionRiskModel,
    KoreaPowerPlan,
    KOREA_POWER_PLANS,
)

# Physical risk (temperature model only)
from .physical import TemperatureModel

__all__ = [
    # Base classes
    "BaseRiskModel",
    "BaseScenario",
    "BaseDamageFunction",
    "RiskResult",
    "RiskType",
    # API
    "ClimateRiskAPI",
    "CombinedRiskResult",
    # Transition (Korea Power Plan)
    "TransitionRiskModel",
    "KoreaPowerPlan",
    "KOREA_POWER_PLANS",
    # Physical
    "TemperatureModel",
]

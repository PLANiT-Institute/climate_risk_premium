"""
Transition Risk Module.

Handles policy-driven dispatch reductions based on Korea Basic Power Plan (전력수급기본계획).
"""

from .model import TransitionRiskModel
from .korea_power_plan import (
    KoreaPowerPlan,
    KOREA_POWER_PLANS,
    load_korea_power_plan_from_csv,
)

__all__ = [
    "TransitionRiskModel",
    "KoreaPowerPlan",
    "KOREA_POWER_PLANS",
    "load_korea_power_plan_from_csv",
]

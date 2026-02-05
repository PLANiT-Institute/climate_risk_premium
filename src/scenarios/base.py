"""
Scenario definitions for transition and physical risks.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class TransitionScenario:
    """
    Transition risk scenario for dispatch constraints.

    Attributes:
        name: Scenario identifier
        dispatch_priority_penalty: Percentage point reduction to capacity factor (0-1)
        retirement_years: Years until enforced retirement
    """
    name: str
    dispatch_priority_penalty: float  # percentage point reduction to capacity factor
    retirement_years: int             # years until enforced retirement


@dataclass
class PhysicalScenario:
    name: str
    wildfire_outage_rate: float       # annual outage probability
    drought_derate: float             # capacity derate percentage
    cooling_temp_penalty: float       # efficiency loss percentage
    water_availability_pct: float = 100.0  # % of normal water supply available


@dataclass
class ScenarioSet:
    baseline_years: int
    transition: Optional[TransitionScenario]
    physical: Optional[PhysicalScenario]

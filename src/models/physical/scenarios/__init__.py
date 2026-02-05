"""
Climate Scenario Module.

Provides RCP/SSP climate pathways from CLIMADA data.
"""

from .climate_scenario import ClimateScenario, RCPScenario, SSPScenario
from .rcp import RCP_SCENARIOS
from .ssp import SSP_SCENARIOS

__all__ = [
    "ClimateScenario",
    "RCPScenario",
    "SSPScenario",
    "RCP_SCENARIOS",
    "SSP_SCENARIOS",
]

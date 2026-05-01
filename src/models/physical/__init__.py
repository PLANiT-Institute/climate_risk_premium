"""
Physical Risk Module — Temperature Model.

Only temperature.py is actively used by the pipeline
(via src/risk/physical/__init__.py for efficiency loss calculation).
"""

from .temperature import TemperatureModel, TEMPERATURE_PROJECTIONS

__all__ = [
    "TemperatureModel",
    "TEMPERATURE_PROJECTIONS",
]

"""
Compatibility module - re-exports from archive/hazards.py.

This module was moved to archive/hazards.py but is still imported by
src/pipeline/runner.py.
"""

from .archive.hazards import (
    load_climada_hazards,
    CLIMADAHazardData,
    calculate_compound_risk,
    interpolate_hazard_by_year,
    calculate_economic_impact,
    get_hazard_description,
    create_corrected_baseline,
)

__all__ = [
    'load_climada_hazards',
    'CLIMADAHazardData',
    'calculate_compound_risk',
    'interpolate_hazard_by_year',
    'calculate_economic_impact',
    'get_hazard_description',
    'create_corrected_baseline',
]

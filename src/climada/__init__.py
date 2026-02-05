"""
CLIMADA Physical Risk Model for Samcheok Blue Power Plant.

Reads ALL inputs from CSV files:
- input/climada_data.csv: CLIMADA API outputs
- input/literature_data.csv: Verified literature values
- input/model_assumptions.csv: Modeling assumptions

Run:
    python -m src.climada.climada_physical_risk_model

Version: 2.0 (CSV-based pipeline)
Date: December 29, 2024
"""

from .climada_physical_risk_model import (
    # Main functions
    run_full_analysis,
    calculate_physical_risk,
    calculate_temperature_impact,
    calculate_base_outage_rates,
    # Data loading
    load_climada_data,
    load_literature_data,
    load_assumptions,
    # Data classes
    PhysicalRiskSummary,
    HazardResult,
    TemperatureResult,
    # Constants
    SAMCHEOK_LAT,
    SAMCHEOK_LON,
)

# Re-export from archive/hazards.py for backwards compatibility
from .archive.hazards import (
    load_climada_hazards,
    CLIMADAHazardData,
    calculate_compound_risk,
    interpolate_hazard_by_year,
    calculate_economic_impact,
)

__all__ = [
    'run_full_analysis',
    'calculate_physical_risk',
    'calculate_temperature_impact',
    'calculate_base_outage_rates',
    'load_climada_data',
    'load_literature_data',
    'load_assumptions',
    'PhysicalRiskSummary',
    'HazardResult',
    'TemperatureResult',
    'SAMCHEOK_LAT',
    'SAMCHEOK_LON',
    # From archive/hazards.py
    'load_climada_hazards',
    'CLIMADAHazardData',
    'calculate_compound_risk',
    'interpolate_hazard_by_year',
    'calculate_economic_impact',
]

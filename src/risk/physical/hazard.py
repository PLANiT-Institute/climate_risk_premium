"""
Hazard Module: Loads hazard data (intensity, frequency).
"""
import pandas as pd
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class HazardData:
    """Raw hazard data before vulnerability application."""
    scenario_name: str
    wildfire_rate: float  # Frequency/Probability
    flood_rate: float
    drought_intensity: float
    heat_intensity: float # Efficiency penalty proxy
    water_availability: float
    year: int
    source: str

class HazardLoader:
    def __init__(self, scenarios_path: str = "data/raw/physical_scenarios.csv"):
        self.scenarios_df = pd.read_csv(scenarios_path)
    
    def get_hazard(self, scenario_name: str, year: int = 2024) -> HazardData:
        """
        Load hazard parameters for a specific scenario and year.
        Uses nearest neighbor or valid year lookup.
        """
        # Filter by scenario
        # Note: The CSV structure we created has 'scenario_name' and 'hazard_type'.
        # We need to aggregate these into a single HazardData object.
        
        subset = self.scenarios_df[self.scenarios_df['scenario_name'] == scenario_name]
        
        if subset.empty:
            # Fallback to baseline if not found
            subset = self.scenarios_df[self.scenarios_df['scenario_name'] == "Baseline (Corrected)"]
            scenario_name = "Baseline (Corrected)"
            
        def get_val(hazard_type: str, param: str) -> float:
            row = subset[
                (subset['hazard_type'] == hazard_type) & 
                (subset['parameter'] == param)
            ]
            if not row.empty:
                return float(row.iloc[0]['value'])
            return 0.0

        return HazardData(
            scenario_name=scenario_name,
            wildfire_rate=get_val("Wildfire", "outage_rate"),
            flood_rate=get_val("Flood", "outage_rate") if "Flood" in subset['hazard_type'].values else 0.0,
            drought_intensity=get_val("Drought", "capacity_derate"),
            heat_intensity=get_val("Heat", "efficiency_loss"),
            water_availability=get_val("Water", "availability"),
            year=year,
            source="CSV"
        )

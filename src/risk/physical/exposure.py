"""
Exposure Module: Defines what assets are exposed and their location/characteristics.
"""
from dataclasses import dataclass

@dataclass
class AssetExposure:
    """
    Asset characteristics that determine exposure to hazards.
    """
    location: str
    asset_type: str  # e.g., "Coal Plant", "Transmission Line"
    value_at_risk: float # e.g., Replacement cost or Revenue
    sensitivity_wildfire: float = 1.0 # Multiplier
    sensitivity_flood: float = 1.0
    sensitivity_heat: float = 1.0
    sensitivity_drought: float = 1.0

class ExposureMapper:
    def __init__(self):
        # In a real system, this would load from a plant database
        pass
    
    def get_exposure(self, plant_params: dict) -> AssetExposure:
        """
        Create exposure profile from plant parameters.
        """
        return AssetExposure(
            location=plant_params.get("location", "Samcheok"),
            asset_type=plant_params.get("type", "Coal Power Plant"),
            value_at_risk=float(plant_params.get("total_capex_million", 3200)) * 1e6
        )

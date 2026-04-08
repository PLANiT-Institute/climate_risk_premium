"""
Physical Risk Module Orchestrator

Integrates:
1. Hazard (Scenario data)
2. Exposure (Asset data)
3. Vulnerability (Damage functions)
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import numpy as np

# Export new submodules
from .hazard import HazardLoader, HazardData
from .exposure import ExposureMapper, AssetExposure
from .vulnerability import VulnerabilityModel, PhysicalImpact


@dataclass
class PhysicalAdjustments:
    outage_rate: float
    efficiency_loss: float
    water_temp_disruption: float = 0.0
    notes: str = ""


@dataclass
class YearlyPhysicalAdjustments:
    years: np.ndarray
    outage_rates: np.ndarray
    efficiency_losses: np.ndarray
    water_temp_disruptions: np.ndarray = field(default_factory=lambda: np.array([]))
    scenario_name: str = ""

    def get_adjustment_for_year(self, year: int) -> PhysicalAdjustments:
        if year in self.years:
            idx = np.where(self.years == year)[0][0]
            wt = float(self.water_temp_disruptions[idx]) if idx < len(self.water_temp_disruptions) else 0.0
            return PhysicalAdjustments(
                outage_rate=self.outage_rates[idx],
                efficiency_loss=self.efficiency_losses[idx],
                water_temp_disruption=wt,
                notes=f"{self.scenario_name} year {year}"
            )
        return PhysicalAdjustments(0.0, 0.0, 0.0, "Out of range")


class PhysicalRiskEngine:
    def __init__(self):
        self.hazard_loader = HazardLoader()
        self.exposure_mapper = ExposureMapper()
        self.vulnerability_model = VulnerabilityModel()

    def calculate_adjustments(self, plant_params: Dict[str, Any], scenario_name: str, year: int = 2024) -> PhysicalAdjustments:
        hazard = self.hazard_loader.get_hazard(scenario_name, year)
        exposure = self.exposure_mapper.get_exposure(plant_params)
        impact = self.vulnerability_model.calculate_impact(hazard, exposure)
        return PhysicalAdjustments(
            outage_rate=impact.outage_rate,
            efficiency_loss=impact.efficiency_loss,
            notes=impact.description
        )


# Global instance for easier access
_ENGINE = PhysicalRiskEngine()

def get_physical_risk_engine() -> PhysicalRiskEngine:
    return _ENGINE


def get_physical_risk_scenario(scenario_name: str) -> PhysicalAdjustments:
    """
    Get physical risk adjustments for a named scenario level.

    Args:
        scenario_name: One of "low", "medium", "high", "extreme" (case insensitive)

    Returns:
        PhysicalAdjustments with appropriate risk values
    """
    scenario_lower = scenario_name.lower()

    scenarios = {
        "low": PhysicalAdjustments(
            outage_rate=0.005,
            efficiency_loss=0.005,
            notes="Low physical risk (baseline conditions)"
        ),
        "medium": PhysicalAdjustments(
            outage_rate=0.015,
            efficiency_loss=0.010,
            notes="Medium physical risk (moderate climate change)"
        ),
        "high": PhysicalAdjustments(
            outage_rate=0.030,
            efficiency_loss=0.020,
            notes="High physical risk (RCP8.5 mid-century)"
        ),
        "extreme": PhysicalAdjustments(
            outage_rate=0.050,
            efficiency_loss=0.035,
            notes="Extreme physical risk (RCP8.5 late-century)"
        ),
    }

    if scenario_lower in scenarios:
        return scenarios[scenario_lower]

    return scenarios["low"]


def apply_physical(
    plant_params: Dict[str, Any],
    scenario_name: str = "Baseline (Corrected)",
    year: int = 2024
) -> PhysicalAdjustments:
    """Apply physical risk assumptions using the Hazard→Exposure→Vulnerability engine."""
    return _ENGINE.calculate_adjustments(plant_params, scenario_name, year)


def create_yearly_physical_adjustments(
    climada_hazards: Any,  # Kept for signature compatibility but ignored
    scenario_prefix: str,
    start_year: int = 2024,
    end_year: int = 2060
) -> YearlyPhysicalAdjustments:
    """Create year-by-year physical adjustments using the engine."""
    scenario_map = {
        "baseline": "Baseline (Corrected)",
        "moderate_physical": "Moderate Physical Risk (Corrected)",
        "high_physical": "High Physical Risk (Corrected)",
        "extreme_physical": "Extreme Physical Risk (Corrected)"
    }
    name = scenario_map.get(scenario_prefix, scenario_prefix)

    years = np.arange(start_year, end_year + 1)
    n = len(years)

    outage_rates = np.zeros(n)
    efficiency_losses = np.zeros(n)

    default_plant = {"type": "Coal", "location": "Samcheok"}

    for i, year in enumerate(years):
        adj = _ENGINE.calculate_adjustments(default_plant, name, int(year))
        outage_rates[i] = adj.outage_rate
        efficiency_losses[i] = adj.efficiency_loss

    return YearlyPhysicalAdjustments(
        years=years,
        outage_rates=outage_rates,
        efficiency_losses=efficiency_losses,
        scenario_name=name
    )

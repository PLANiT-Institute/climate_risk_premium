"""
Physical Risk Module Orchestrator

Integrates:
1. Hazard (Scenario data)
2. Exposure (Asset data)
3. Vulnerability (Damage functions)
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
import numpy as np

# Export new submodules
from .hazard import HazardLoader, HazardData
from .exposure import ExposureMapper, AssetExposure
from .vulnerability import VulnerabilityModel, PhysicalImpact

# Legacy support for existing references
@dataclass
class PhysicalAdjustments:
    outage_rate: float
    capacity_derate: float
    efficiency_loss: float
    water_constrained_capacity: float = 1.0
    notes: str = ""

@dataclass
class YearlyPhysicalAdjustments:
    years: np.ndarray
    outage_rates: np.ndarray
    capacity_derates: np.ndarray
    efficiency_losses: np.ndarray
    water_constraints: np.ndarray
    scenario_name: str = ""

    def get_adjustment_for_year(self, year: int) -> PhysicalAdjustments:
        if year in self.years:
            idx = np.where(self.years == year)[0][0]
            return PhysicalAdjustments(
                outage_rate=self.outage_rates[idx],
                capacity_derate=self.capacity_derates[idx],
                efficiency_loss=self.efficiency_losses[idx],
                water_constrained_capacity=self.water_constraints[idx],
                notes=f"{self.scenario_name} year {year}"
            )
        # Fallback/Interpolation logic could go here
        return PhysicalAdjustments(0, 0, 0, 1.0, "Out of range")

class PhysicalRiskEngine:
    def __init__(self):
        self.hazard_loader = HazardLoader()
        self.exposure_mapper = ExposureMapper()
        self.vulnerability_model = VulnerabilityModel()

    def calculate_adjustments(self, plant_params: Dict[str, Any], scenario_name: str, year: int = 2024) -> PhysicalAdjustments:
        # 1. Load Hazard
        hazard = self.hazard_loader.get_hazard(scenario_name, year)
        
        # 2. Map Exposure
        exposure = self.exposure_mapper.get_exposure(plant_params)
        
        # 3. Calculate Vulnerability/Impact
        impact = self.vulnerability_model.calculate_impact(hazard, exposure)
        
        return PhysicalAdjustments(
            outage_rate=impact.outage_rate,
            capacity_derate=impact.capacity_derate,
            efficiency_loss=impact.efficiency_loss,
            water_constrained_capacity=impact.water_constrained_capacity,
            notes=impact.description
        )

# ---------------------------------------------------------------------------
# PLANiT integration functions
# ---------------------------------------------------------------------------
import logging as _logging

_planit_logger = _logging.getLogger(__name__)


def get_physical_risk_from_planit(
    year: int = 2040,
    scenario: str = "RCP8.5",
    config=None,
    base_dir: Optional[str] = None,
) -> PhysicalAdjustments:
    """Get physical risk adjustments using PLANiT CLIMADA Wildfire + TemperatureModel.

    HYBRID MODE (as of 2026-02-05)
    ------------------------------
    Combines:
    - PLANiT CLIMADA wildfire → outage_rate (explicit ImpfWildfire sigmoid)
    - Internal TemperatureModel → efficiency_loss (dominant factor ~0.78% for 2050/RCP8.5)

    Other hazards (drought, flood, water_risk) removed due to PhysRisk API
    being black-box without explicit vulnerability formulas.

    Returns
    -------
    PhysicalAdjustments with:
    - outage_rate: from CLIMADA wildfire event frequency
    - capacity_derate: 0.0 (drought removed)
    - efficiency_loss: from TemperatureModel (temperature + heat waves)
    - water_constrained_capacity: 1.0 (water_risk removed)
    """
    # Import TemperatureModel for efficiency loss calculation
    from src.models.physical.temperature import TemperatureModel, CoolingType

    try:
        from src.planit import (
            PLANiTIntegrationConfig,
            PLANiTRunner,
            PLANiTAdapter,
            map_scenario,
        )
    except ImportError:
        _planit_logger.warning(
            "PLANiT package not available, falling back to engine-based physical risk"
        )
        return apply_physical({}, scenario, year)

    if config is None:
        config = PLANiTIntegrationConfig()

    # Calculate temperature efficiency loss (always runs, even if PLANiT disabled)
    temp_model = TemperatureModel(rcp=scenario, cooling_type=CoolingType.ONCE_THROUGH)
    temp_result = temp_model.calculate_efficiency_loss(year)
    efficiency_loss = temp_result.total_derate

    if not config.enabled:
        engine_adj = apply_physical({}, scenario, year)
        return PhysicalAdjustments(
            outage_rate=engine_adj.outage_rate,
            capacity_derate=0.0,
            efficiency_loss=efficiency_loss,
            water_constrained_capacity=1.0,
            notes=f"PLANiT disabled, temp_eff={efficiency_loss:.4f} ({scenario} y{year})",
        )

    # Simplified baseline: only outage_rate used for wildfire fallback
    engine_adj = apply_physical({}, scenario, year)
    csv_baseline = {
        "outage_rate": engine_adj.outage_rate,
    }

    try:
        ssp = map_scenario(scenario)
        runner = PLANiTRunner(config, base_dir=base_dir)
        all_results = []

        # Only run wildfire (config.planit_hazards is now ["wildfire"] only)
        for hazard in config.planit_hazards:
            try:
                all_results.extend(runner.run_hazard(hazard, scenarios=[ssp]))
            except Exception as e:
                _planit_logger.warning(
                    f"PLANiT hazard '{hazard}' failed, using fallback: {e}"
                )

        if not all_results:
            # No wildfire data, return minimal defaults with temperature efficiency
            return PhysicalAdjustments(
                outage_rate=csv_baseline.get("outage_rate", 0.0),
                capacity_derate=0.0,
                efficiency_loss=efficiency_loss,
                water_constrained_capacity=1.0,
                notes=f"PLANiT wildfire unavailable, csv_fallback, temp_eff={efficiency_loss:.4f} ({scenario} y{year})",
            )

        adapter = PLANiTAdapter(config)
        adj = adapter.convert(all_results, year, scenario, csv_baseline)

        return PhysicalAdjustments(
            outage_rate=adj["outage_rate"],
            capacity_derate=adj["capacity_derate"],  # Always 0.0
            efficiency_loss=efficiency_loss,  # FROM TEMPERATURE MODEL
            water_constrained_capacity=adj["water_constrained_capacity"],  # Always 1.0
            notes=f"{adj['notes']} | temp_eff={efficiency_loss:.4f}",
        )

    except Exception as e:
        _planit_logger.error(f"PLANiT integration failed, full fallback: {e}")
        return PhysicalAdjustments(
            outage_rate=engine_adj.outage_rate,
            capacity_derate=0.0,
            efficiency_loss=efficiency_loss,
            water_constrained_capacity=1.0,
            notes=f"PLANiT error fallback, temp_eff={efficiency_loss:.4f}: {e}",
        )


def create_yearly_physical_adjustments_from_planit(
    start_year: int = 2024,
    end_year: int = 2060,
    scenario: str = "RCP8.5",
    config=None,
    base_dir: Optional[str] = None,
) -> YearlyPhysicalAdjustments:
    """Create year-by-year physical adjustments from PLANiT CLIMADA Wildfire + TemperatureModel.

    HYBRID MODE (as of 2026-02-05)
    ------------------------------
    Combines:
    - PLANiT CLIMADA wildfire → outage_rates (explicit ImpfWildfire sigmoid)
    - Internal TemperatureModel → efficiency_losses (temperature + heat waves)

    Other hazards removed; capacity_derate returns 0.0,
    water_constrained_capacity returns 1.0 for all years.
    """
    # Import TemperatureModel for efficiency loss calculation
    from src.models.physical.temperature import TemperatureModel, CoolingType

    try:
        from src.planit import (
            PLANiTIntegrationConfig,
            PLANiTRunner,
            PLANiTAdapter,
            map_scenario,
        )
    except ImportError:
        _planit_logger.warning("PLANiT not available for yearly adjustments")
        return create_yearly_physical_adjustments(None, scenario, start_year, end_year)

    if config is None:
        config = PLANiTIntegrationConfig()

    # Calculate temperature efficiency losses for all years (always runs)
    temp_model = TemperatureModel(rcp=scenario, cooling_type=CoolingType.ONCE_THROUGH)
    years = np.arange(start_year, end_year + 1)
    efficiency_losses = np.array([
        temp_model.calculate_efficiency_loss(int(y)).total_derate
        for y in years
    ])

    if not config.enabled:
        engine_yearly = create_yearly_physical_adjustments(None, scenario, start_year, end_year)
        return YearlyPhysicalAdjustments(
            years=engine_yearly.years,
            outage_rates=engine_yearly.outage_rates,
            capacity_derates=np.zeros(len(years)),
            efficiency_losses=efficiency_losses,  # FROM TEMPERATURE MODEL
            water_constraints=np.ones(len(years)),
            scenario_name=f"PLANiT disabled, TemperatureModel ({scenario})",
        )

    # Simplified baseline: only outage_rate used for wildfire fallback
    engine_adj = apply_physical({}, scenario, start_year)
    csv_baseline = {
        "outage_rate": engine_adj.outage_rate,
    }

    try:
        ssp = map_scenario(scenario)
        runner = PLANiTRunner(config, base_dir=base_dir)
        all_results = []

        # Only run wildfire (config.planit_hazards is now ["wildfire"] only)
        for hazard in config.planit_hazards:
            try:
                all_results.extend(runner.run_hazard(hazard, scenarios=[ssp]))
            except Exception as e:
                _planit_logger.warning(f"PLANiT hazard '{hazard}' failed for yearly: {e}")

        adapter = PLANiTAdapter(config)
        arrays = adapter.convert_yearly(
            all_results, start_year, end_year, scenario, csv_baseline
        )

        return YearlyPhysicalAdjustments(
            years=arrays["years"],
            outage_rates=arrays["outage_rates"],
            capacity_derates=arrays["capacity_derates"],  # All zeros
            efficiency_losses=efficiency_losses,  # FROM TEMPERATURE MODEL
            water_constraints=arrays["water_constraints"],  # All ones
            scenario_name=f"CLIMADA wildfire + TemperatureModel ({ssp})",
        )

    except Exception as e:
        _planit_logger.error(f"PLANiT yearly failed, fallback: {e}")
        fallback = create_yearly_physical_adjustments(None, scenario, start_year, end_year)
        return YearlyPhysicalAdjustments(
            years=fallback.years,
            outage_rates=fallback.outage_rates,
            capacity_derates=np.zeros(len(years)),
            efficiency_losses=efficiency_losses,  # FROM TEMPERATURE MODEL
            water_constraints=np.ones(len(years)),
            scenario_name=f"PLANiT fallback + TemperatureModel ({scenario})",
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

    # Predefined scenario levels based on CLIMADA/literature calibration
    scenarios = {
        "low": PhysicalAdjustments(
            outage_rate=0.005,
            capacity_derate=0.001,
            efficiency_loss=0.005,
            water_constrained_capacity=0.995,
            notes="Low physical risk (baseline conditions)"
        ),
        "medium": PhysicalAdjustments(
            outage_rate=0.015,
            capacity_derate=0.005,
            efficiency_loss=0.010,
            water_constrained_capacity=0.985,
            notes="Medium physical risk (moderate climate change)"
        ),
        "high": PhysicalAdjustments(
            outage_rate=0.030,
            capacity_derate=0.010,
            efficiency_loss=0.020,
            water_constrained_capacity=0.970,
            notes="High physical risk (RCP8.5 mid-century)"
        ),
        "extreme": PhysicalAdjustments(
            outage_rate=0.050,
            capacity_derate=0.020,
            efficiency_loss=0.035,
            water_constrained_capacity=0.950,
            notes="Extreme physical risk (RCP8.5 late-century)"
        ),
    }

    if scenario_lower in scenarios:
        return scenarios[scenario_lower]

    # Fallback to low if not recognized
    return scenarios["low"]

def apply_physical(
    plant_params: Dict[str, Any],
    scenario_name: str = "Baseline (Corrected)",
    year: int = 2024
) -> PhysicalAdjustments:
    """
    Apply physical risk assumptions using the new Hazard->Exposure->Vulnerability engine.
    """
    return _ENGINE.calculate_adjustments(plant_params, scenario_name, year)

def create_yearly_physical_adjustments(
    climada_hazards: Any, # Kept for signature compatibility but ignored
    scenario_prefix: str,
    start_year: int = 2024,
    end_year: int = 2060
) -> YearlyPhysicalAdjustments:
    """
    Create year-by-year physical adjustments using the new engine.
    """
    # Note: climada_hazards is ignored as we now load from CSV via HazardLoader
    # scenario_prefix maps to scenario_name
    
    # Simple mapping from old prefixes to new names if needed, or assume direct match
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
    capacity_derates = np.zeros(n)
    efficiency_losses = np.zeros(n)
    water_constraints = np.zeros(n)
    
    # We need plant params here for exposure, but the old signature didn't verify it.
    # We'll assume default plant params for now or update the signature if possible.
    # For backward partial compatibility, we default to generic plant params.
    default_plant = {"type": "Coal", "location": "Samcheok"}
    
    for i, year in enumerate(years):
        adj = _ENGINE.calculate_adjustments(default_plant, name, int(year))
        outage_rates[i] = adj.outage_rate
        capacity_derates[i] = adj.capacity_derate
        efficiency_losses[i] = adj.efficiency_loss
        water_constraints[i] = adj.water_constrained_capacity
        
    return YearlyPhysicalAdjustments(
        years=years,
        outage_rates=outage_rates,
        capacity_derates=capacity_derates,
        efficiency_losses=efficiency_losses,
        water_constraints=water_constraints,
        scenario_name=name
    )

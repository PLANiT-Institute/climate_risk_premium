"""
Physical risk adjustments (wildfire, water stress, temperature).

Updated to integrate CLIMADA hazard data (wildfire, flood, sea level rise).
Supports year-by-year hazard evolution for dynamic climate risk modeling.

CORRECTED (2024 Review):
- Physical risk values updated based on Korea-specific literature
- Original values were overestimated by 10-50x
- See docs/literature_review/ for detailed methodology corrections
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import numpy as np

from src.scenarios import PhysicalScenario

from src.climada.hazards import CLIMADAHazardData, interpolate_hazard_by_year, create_corrected_baseline
from src.climada.literature_parameters import (
    calculate_wildfire_outage_rate,
    calculate_flood_outage_rate,
    get_corrected_baseline_values,
)
CLIMADA_AVAILABLE = True


@dataclass
class PhysicalAdjustments:
    """
    Physical risk adjustments to plant operations.

    Attributes:
        outage_rate: Annual forced outage rate (0-1)
        capacity_derate: Capacity derating factor (0-1)
        efficiency_loss: Efficiency penalty (0-1)
        water_constrained_capacity: Max CF allowed by water (0-1)
        notes: Description of adjustments applied
    """
    outage_rate: float
    capacity_derate: float
    efficiency_loss: float
    water_constrained_capacity: float = 1.0
    notes: str = ""


@dataclass
class YearlyPhysicalAdjustments:
    """
    Year-by-year physical risk adjustments for dynamic climate modeling.

    Attributes:
        years: Array of years
        outage_rates: Annual outage rate for each year
        capacity_derates: Capacity derating for each year
        efficiency_losses: Efficiency loss for each year
        water_constraints: Water constraint for each year
        scenario_name: Name of the physical scenario
    """
    years: np.ndarray
    outage_rates: np.ndarray
    capacity_derates: np.ndarray
    efficiency_losses: np.ndarray
    water_constraints: np.ndarray
    scenario_name: str = ""

    def get_adjustment_for_year(self, year: int) -> PhysicalAdjustments:
        """Get PhysicalAdjustments for a specific year."""
        if year in self.years:
            idx = np.where(self.years == year)[0][0]
            return PhysicalAdjustments(
                outage_rate=self.outage_rates[idx],
                capacity_derate=self.capacity_derates[idx],
                efficiency_loss=self.efficiency_losses[idx],
                water_constrained_capacity=self.water_constraints[idx],
                notes=f"{self.scenario_name} year {year}"
            )
        # Interpolate if exact year not found
        if year < self.years[0]:
            return PhysicalAdjustments(
                outage_rate=self.outage_rates[0],
                capacity_derate=self.capacity_derates[0],
                efficiency_loss=self.efficiency_losses[0],
                water_constrained_capacity=self.water_constraints[0],
                notes=f"{self.scenario_name} (extrapolated)"
            )
        if year > self.years[-1]:
            return PhysicalAdjustments(
                outage_rate=self.outage_rates[-1],
                capacity_derate=self.capacity_derates[-1],
                efficiency_loss=self.efficiency_losses[-1],
                water_constrained_capacity=self.water_constraints[-1],
                notes=f"{self.scenario_name} (extrapolated)"
            )
        # Linear interpolation
        idx = np.searchsorted(self.years, year)
        y0, y1 = self.years[idx-1], self.years[idx]
        weight = (year - y0) / (y1 - y0)
        return PhysicalAdjustments(
            outage_rate=self.outage_rates[idx-1] + weight * (self.outage_rates[idx] - self.outage_rates[idx-1]),
            capacity_derate=self.capacity_derates[idx-1] + weight * (self.capacity_derates[idx] - self.capacity_derates[idx-1]),
            efficiency_loss=self.efficiency_losses[idx-1] + weight * (self.efficiency_losses[idx] - self.efficiency_losses[idx-1]),
            water_constrained_capacity=self.water_constraints[idx-1] + weight * (self.water_constraints[idx] - self.water_constraints[idx-1]),
            notes=f"{self.scenario_name} (interpolated)"
        )

    @property
    def average_outage_rate(self) -> float:
        """Average outage rate over all years."""
        return float(np.mean(self.outage_rates))

    @property
    def average_capacity_derate(self) -> float:
        """Average capacity derate over all years."""
        return float(np.mean(self.capacity_derates))


def apply_physical(
    plant_params: Dict[str, Any],
    scenario: PhysicalScenario,
    climada_hazard: Optional['CLIMADAHazardData'] = None
) -> PhysicalAdjustments:
    """
    Apply physical risk assumptions.

    Can use either traditional PhysicalScenario (simple parameters) or
    CLIMADA hazard data (spatially-explicit climate hazards).

    Args:
        plant_params: Plant design parameters
        scenario: Physical risk scenario (traditional)
        climada_hazard: Optional CLIMADA hazard data (overrides scenario if provided)

    Returns:
        PhysicalAdjustments with applied risk factors

    Priority order (if both provided):
        1. CLIMADA hazard data (most detailed)
        2. PhysicalScenario parameters (simple)
        3. Plant baseline parameters
    """
    # Use CLIMADA data if available
    if climada_hazard is not None and CLIMADA_AVAILABLE:
        return apply_climada_physical_risk(plant_params, climada_hazard)

    # Otherwise use traditional scenario-based approach
    base_outage = float(plant_params.get("base_outage_rate", 0.05))
    outage = max(0.0, base_outage + scenario.wildfire_outage_rate)

    # General derate (e.g., heat efficiency loss)
    derate = scenario.drought_derate
    eff_loss = scenario.cooling_temp_penalty

    # Water constraint (hard limit on capacity factor)
    # If water availability < required, capacity must be derated
    water_availability = getattr(scenario, "water_availability_pct", 100.0) / 100.0

    # Linear constraint: 80% water availability → max 80% capacity factor
    # (Assumes linear relationship between load and cooling water use)
    water_constrained_cap = min(1.0, water_availability)

    return PhysicalAdjustments(
        outage_rate=outage,
        capacity_derate=derate,
        efficiency_loss=eff_loss,
        water_constrained_capacity=water_constrained_cap,
        notes=f"Scenario-based: {scenario.name}"
    )


def apply_climada_physical_risk(
    plant_params: Dict[str, Any],
    climada_hazard: 'CLIMADAHazardData'
) -> PhysicalAdjustments:
    """
    Apply CLIMADA-based physical risk adjustments.

    CLIMADA provides spatially-explicit hazard modeling:
    - Wildfire: Fire Weather Index → transmission outages
    - Flood: Riverine + coastal flooding → equipment damage
    - Sea Level Rise: Cooling water intake disruption

    Args:
        plant_params: Plant design parameters
        climada_hazard: CLIMADA hazard data

    Returns:
        PhysicalAdjustments based on CLIMADA hazards
    """
    # CLIMADA outage rates (wildfire + flood)
    # These are already combined in climada_hazard.total_outage_rate
    outage_rate = climada_hazard.total_outage_rate

    # CLIMADA capacity derating (primarily from sea level rise)
    capacity_derate = climada_hazard.total_capacity_derate

    # Efficiency loss - can be added separately if heat wave data available
    # For now, included in capacity derate
    efficiency_loss = 0.0

    # Water constraint - CLIMADA SLR affects cooling water intake
    # If SLR exceeds design tolerance, cooling capacity is reduced
    # This is captured in capacity_derate, so water constraint remains 1.0
    # (Unless separate drought module is added to CLIMADA)
    water_constrained_capacity = 1.0

    notes = (
        f"CLIMADA-based: Wildfire {climada_hazard.wildfire_outage_rate:.2%}, "
        f"Flood {climada_hazard.flood_outage_rate:.2%}, "
        f"SLR {climada_hazard.slr_capacity_derate:.2%}, "
        f"Compound {climada_hazard.compound_multiplier:.2f}x | "
        f"{climada_hazard.data_source}"
    )

    return PhysicalAdjustments(
        outage_rate=outage_rate,
        capacity_derate=capacity_derate,
        efficiency_loss=efficiency_loss,
        water_constrained_capacity=water_constrained_capacity,
        notes=notes
    )


def create_yearly_physical_adjustments(
    climada_hazards: Dict[str, CLIMADAHazardData],
    scenario_prefix: str,
    start_year: int = 2024,
    end_year: int = 2060
) -> YearlyPhysicalAdjustments:
    """
    Create year-by-year physical adjustments from CLIMADA hazard data.

    This enables dynamic climate risk modeling where physical risks
    increase over time as climate change progresses.

    Args:
        climada_hazards: Dict of all loaded CLIMADA hazards
        scenario_prefix: Scenario type (e.g., "moderate_physical", "high_physical")
        start_year: First year of analysis
        end_year: Last year of analysis

    Returns:
        YearlyPhysicalAdjustments with arrays for each year

    Example:
        >>> hazards = load_climada_hazards('data/raw/climada_hazards.csv')
        >>> yearly = create_yearly_physical_adjustments(hazards, "high_physical", 2024, 2060)
        >>> adj_2040 = yearly.get_adjustment_for_year(2040)
    """
    years = np.arange(start_year, end_year + 1)
    n_years = len(years)

    outage_rates = np.zeros(n_years)
    capacity_derates = np.zeros(n_years)
    efficiency_losses = np.zeros(n_years)
    water_constraints = np.ones(n_years)

    for i, year in enumerate(years):
        try:
            # Interpolate hazard for this year
            hazard = interpolate_hazard_by_year(climada_hazards, year, scenario_prefix)
            outage_rates[i] = hazard.total_outage_rate
            capacity_derates[i] = hazard.total_capacity_derate
            # Efficiency loss approximated from compound multiplier effect
            efficiency_losses[i] = (hazard.compound_multiplier - 1.0) * 0.02  # ~2% per 1.0x compound
        except (ValueError, KeyError):
            # If interpolation fails, use baseline values
            if "baseline" in climada_hazards:
                baseline = climada_hazards["baseline"]
                outage_rates[i] = baseline.total_outage_rate
                capacity_derates[i] = baseline.total_capacity_derate
                efficiency_losses[i] = 0.0

    return YearlyPhysicalAdjustments(
        years=years,
        outage_rates=outage_rates,
        capacity_derates=capacity_derates,
        efficiency_losses=efficiency_losses,
        water_constraints=water_constraints,
        scenario_name=scenario_prefix
    )


def get_physical_risk_scenario(level: str) -> PhysicalScenario:
    """
    Get physical risk scenario by severity level.

    CORRECTED (2024): Values updated based on Korea-specific literature.
    Original values were overestimated by 10-50x.

    Corrected values (for Samcheok):
    - Baseline wildfire: ~0.05% (was 1-5%)
    - Baseline flood: ~0.003% (was 1-3%)
    - Compound multiplier: 1.0-1.25x (was 1.2-2.0x)

    Args:
        level: "Low", "Medium", "High", "Extreme"

    Returns:
        PhysicalScenario with appropriate risk parameters
    """
    level = level.lower()

    # Get corrected baseline values
    baseline = get_corrected_baseline_values()
    wildfire_base = baseline["wildfire_outage_rate"]  # ~0.0005

    if level == "low" or level == "baseline":
        # Baseline 2024 - corrected Korea values
        return PhysicalScenario(
            name="Baseline (Corrected)",
            wildfire_outage_rate=wildfire_base,  # ~0.05%
            drought_derate=0.0,
            cooling_temp_penalty=0.0,
            water_availability_pct=100.0
        )
    elif level == "medium" or level == "moderate":
        # RCP4.5 2040-ish - mild climate change
        return PhysicalScenario(
            name="Moderate Physical Risk (Corrected)",
            wildfire_outage_rate=wildfire_base * 1.5,  # ~0.08%
            drought_derate=0.005,  # 0.5% derate
            cooling_temp_penalty=0.002,  # 0.2% efficiency loss
            water_availability_pct=98.0
        )
    elif level == "high":
        # RCP8.5 2050-ish - significant climate change
        return PhysicalScenario(
            name="High Physical Risk (Corrected)",
            wildfire_outage_rate=wildfire_base * 2.0,  # ~0.1%
            drought_derate=0.01,  # 1% derate
            cooling_temp_penalty=0.005,  # 0.5% efficiency loss
            water_availability_pct=95.0
        )
    elif level == "extreme":
        # RCP8.5 2060+ - severe climate change
        return PhysicalScenario(
            name="Extreme Physical Risk (Corrected)",
            wildfire_outage_rate=wildfire_base * 4.0,  # ~0.2%
            drought_derate=0.02,  # 2% derate
            cooling_temp_penalty=0.01,  # 1% efficiency loss
            water_availability_pct=90.0
        )
    else:
        # Default to baseline
        return PhysicalScenario(
            name="Baseline (Corrected)",
            wildfire_outage_rate=wildfire_base,
            drought_derate=0.0,
            cooling_temp_penalty=0.0,
            water_availability_pct=100.0
        )


def get_physical_risk_from_climada(
    target_year: int = 2024,
    rcp: str = "current"
) -> PhysicalAdjustments:
    """
    Get physical risk adjustments using corrected CLIMADA-style calculations.

    This is the RECOMMENDED way to get physical risk for Samcheok.
    Uses Korea-specific literature values, not California data.

    Args:
        target_year: Target year for projections
        rcp: RCP scenario ("current", "RCP4.5", "RCP8.5")

    Returns:
        PhysicalAdjustments with corrected values
    """
    hazard = create_corrected_baseline(target_year, rcp)
    return PhysicalAdjustments(
        outage_rate=hazard.total_outage_rate,
        capacity_derate=hazard.total_capacity_derate,
        efficiency_loss=0.0,
        water_constrained_capacity=1.0,
        notes=f"Corrected CLIMADA ({rcp} {target_year}): "
              f"Wildfire {hazard.wildfire_outage_rate:.4%}, "
              f"Flood {hazard.flood_outage_rate:.4%}, "
              f"SLR {hazard.slr_capacity_derate:.4%}"
    )


# ---------------------------------------------------------------------------
# PLANiT integration (Stage 1 of CRP pipeline)
# ---------------------------------------------------------------------------

def get_physical_risk_from_planit(
    year: int = 2040,
    scenario: str = "RCP8.5",
    config: Optional['_PLANiTIntegrationConfig'] = None,
    base_dir: Optional[str] = None,
) -> PhysicalAdjustments:
    """Get physical risk adjustments using PLANiT (CLIMADA + PhysRisk).

    Falls back to ``get_physical_risk_from_climada()`` when PLANiT
    is unavailable or encounters errors.

    Args:
        year: Target projection year.
        scenario: CRP scenario label (e.g. "RCP4.5", "RCP8.5", "SSP1-2.6").
        config: Optional PLANiTIntegrationConfig (uses defaults if None).
        base_dir: Project root directory.

    Returns:
        PhysicalAdjustments with PLANiT-derived values.
    """
    try:
        from src.planit import (
            PLANiTIntegrationConfig,
            PLANiTRunner,
            PLANiTAdapter,
            map_scenario,
        )
    except ImportError:
        import logging
        logging.getLogger(__name__).warning(
            "PLANiT package not available, falling back to CSV-based CLIMADA"
        )
        rcp = "RCP8.5" if "8.5" in scenario or "585" in scenario else "RCP4.5"
        return get_physical_risk_from_climada(year, rcp)

    if config is None:
        config = PLANiTIntegrationConfig()

    if not config.enabled:
        rcp = "RCP8.5" if "8.5" in scenario or "585" in scenario else "RCP4.5"
        return get_physical_risk_from_climada(year, rcp)

    # CSV baseline for fallback/blending
    rcp_label = "RCP8.5" if "8.5" in scenario or "585" in scenario else "RCP4.5"
    csv_adj = get_physical_risk_from_climada(year, rcp_label)
    csv_baseline = {
        "outage_rate": csv_adj.outage_rate,
        "capacity_derate": csv_adj.capacity_derate,
        "efficiency_loss": csv_adj.efficiency_loss,
        "water_constrained_capacity": csv_adj.water_constrained_capacity,
    }

    try:
        ssp = map_scenario(scenario)
        runner = PLANiTRunner(config, base_dir=base_dir)
        all_results = []
        for hazard in config.planit_hazards:
            try:
                all_results.extend(runner.run_hazard(hazard, scenarios=[ssp]))
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    f"PLANiT hazard '{hazard}' failed, using CSV fallback: {e}"
                )

        if not all_results:
            return csv_adj

        adapter = PLANiTAdapter(config)
        adj = adapter.convert(all_results, year, scenario, csv_baseline)

        return PhysicalAdjustments(
            outage_rate=adj["outage_rate"],
            capacity_derate=adj["capacity_derate"],
            efficiency_loss=adj["efficiency_loss"],
            water_constrained_capacity=adj["water_constrained_capacity"],
            notes=adj["notes"],
        )

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(
            f"PLANiT integration failed, full CSV fallback: {e}"
        )
        return csv_adj


def create_yearly_physical_adjustments_from_planit(
    start_year: int = 2024,
    end_year: int = 2060,
    scenario: str = "RCP8.5",
    config: Optional['_PLANiTIntegrationConfig'] = None,
    base_dir: Optional[str] = None,
) -> YearlyPhysicalAdjustments:
    """Create year-by-year physical adjustments from PLANiT.

    Falls back to ``create_yearly_physical_adjustments()`` if PLANiT
    is not available.

    Args:
        start_year: First year of the projection window.
        end_year: Last year of the projection window.
        scenario: CRP scenario label.
        config: Optional PLANiTIntegrationConfig.
        base_dir: Project root directory.

    Returns:
        YearlyPhysicalAdjustments with arrays for each year.
    """
    try:
        from src.planit import (
            PLANiTIntegrationConfig,
            PLANiTRunner,
            PLANiTAdapter,
            map_scenario,
        )
    except ImportError:
        import logging
        logging.getLogger(__name__).warning(
            "PLANiT not available for yearly adjustments, using CSV fallback"
        )
        # Construct year-by-year from CSV baseline
        years = np.arange(start_year, end_year + 1)
        n = len(years)
        rcp = "RCP8.5" if "8.5" in scenario or "585" in scenario else "RCP4.5"
        adj = get_physical_risk_from_climada(start_year, rcp)
        return YearlyPhysicalAdjustments(
            years=years,
            outage_rates=np.full(n, adj.outage_rate),
            capacity_derates=np.full(n, adj.capacity_derate),
            efficiency_losses=np.full(n, adj.efficiency_loss),
            water_constraints=np.full(n, adj.water_constrained_capacity),
            scenario_name=f"CSV-fallback ({rcp})",
        )

    if config is None:
        config = PLANiTIntegrationConfig()

    if not config.enabled:
        rcp = "RCP8.5" if "8.5" in scenario or "585" in scenario else "RCP4.5"
        years = np.arange(start_year, end_year + 1)
        n = len(years)
        adj = get_physical_risk_from_climada(start_year, rcp)
        return YearlyPhysicalAdjustments(
            years=years,
            outage_rates=np.full(n, adj.outage_rate),
            capacity_derates=np.full(n, adj.capacity_derate),
            efficiency_losses=np.full(n, adj.efficiency_loss),
            water_constraints=np.full(n, adj.water_constrained_capacity),
            scenario_name=f"CSV-fallback ({rcp})",
        )

    # CSV baseline for blending
    rcp_label = "RCP8.5" if "8.5" in scenario or "585" in scenario else "RCP4.5"
    csv_adj = get_physical_risk_from_climada(start_year, rcp_label)
    csv_baseline = {
        "outage_rate": csv_adj.outage_rate,
        "capacity_derate": csv_adj.capacity_derate,
        "efficiency_loss": csv_adj.efficiency_loss,
        "water_constrained_capacity": csv_adj.water_constrained_capacity,
    }

    try:
        ssp = map_scenario(scenario)
        runner = PLANiTRunner(config, base_dir=base_dir)
        all_results = []
        for hazard in config.planit_hazards:
            try:
                all_results.extend(runner.run_hazard(hazard, scenarios=[ssp]))
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    f"PLANiT hazard '{hazard}' failed for yearly: {e}"
                )

        adapter = PLANiTAdapter(config)
        arrays = adapter.convert_yearly(
            all_results, start_year, end_year, scenario, csv_baseline
        )

        return YearlyPhysicalAdjustments(
            years=arrays["years"],
            outage_rates=arrays["outage_rates"],
            capacity_derates=arrays["capacity_derates"],
            efficiency_losses=arrays["efficiency_losses"],
            water_constraints=arrays["water_constraints"],
            scenario_name=f"PLANiT ({ssp})",
        )

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(
            f"PLANiT yearly failed, CSV fallback: {e}"
        )
        years = np.arange(start_year, end_year + 1)
        n = len(years)
        return YearlyPhysicalAdjustments(
            years=years,
            outage_rates=np.full(n, csv_adj.outage_rate),
            capacity_derates=np.full(n, csv_adj.capacity_derate),
            efficiency_losses=np.full(n, csv_adj.efficiency_loss),
            water_constraints=np.full(n, csv_adj.water_constrained_capacity),
            scenario_name=f"CSV-fallback ({rcp_label})",
        )

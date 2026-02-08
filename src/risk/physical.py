"""
Physical risk adjustments (wildfire, drought, water risk).

PLANiT is the sole physical risk source.  CLIMADA (wildfire AAI) and
PhysRisk (drought/water_risk impact_mean) results are loaded from
pre-computed CSVs and converted via the PLANiT adapter.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import numpy as np

from src.scenarios import PhysicalScenario


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
) -> PhysicalAdjustments:
    """Apply physical risk from a PhysicalScenario object.

    Args:
        plant_params: Plant design parameters.
        scenario: Physical risk scenario.

    Returns:
        PhysicalAdjustments with applied risk factors.
    """
    base_outage = float(plant_params.get("base_outage_rate", 0.05))
    outage = max(0.0, base_outage + scenario.wildfire_outage_rate)
    derate = scenario.drought_derate
    eff_loss = scenario.cooling_temp_penalty
    water_availability = getattr(scenario, "water_availability_pct", 100.0) / 100.0
    water_constrained_cap = min(1.0, water_availability)

    return PhysicalAdjustments(
        outage_rate=outage,
        capacity_derate=derate,
        efficiency_loss=eff_loss,
        water_constrained_capacity=water_constrained_cap,
        notes=f"Scenario-based: {scenario.name}"
    )


def get_physical_risk_scenario(level: str) -> PhysicalScenario:
    """Get physical risk scenario by severity level.

    Korea-specific baseline wildfire outage rate: 0.055%
    (Kim et al 2025, DOI:10.1007/s11069-025-07169-4).

    Args:
        level: "Low", "Medium", "High", "Extreme"

    Returns:
        PhysicalScenario with appropriate risk parameters.
    """
    level = level.lower()
    wildfire_base = 0.00055  # Korea baseline (Kim et al 2025)

    if level in ("low", "baseline"):
        return PhysicalScenario(
            name="Baseline",
            wildfire_outage_rate=wildfire_base,
            drought_derate=0.0,
            cooling_temp_penalty=0.0,
            water_availability_pct=100.0,
        )
    elif level in ("medium", "moderate"):
        return PhysicalScenario(
            name="Moderate Physical Risk",
            wildfire_outage_rate=wildfire_base * 1.5,
            drought_derate=0.005,
            cooling_temp_penalty=0.002,
            water_availability_pct=98.0,
        )
    elif level == "high":
        return PhysicalScenario(
            name="High Physical Risk",
            wildfire_outage_rate=wildfire_base * 2.0,
            drought_derate=0.01,
            cooling_temp_penalty=0.005,
            water_availability_pct=95.0,
        )
    elif level == "extreme":
        return PhysicalScenario(
            name="Extreme Physical Risk",
            wildfire_outage_rate=wildfire_base * 4.0,
            drought_derate=0.02,
            cooling_temp_penalty=0.01,
            water_availability_pct=90.0,
        )
    else:
        return PhysicalScenario(
            name="Baseline",
            wildfire_outage_rate=wildfire_base,
            drought_derate=0.0,
            cooling_temp_penalty=0.0,
            water_availability_pct=100.0,
        )


def get_physical_risk_from_planit(
    year: int = 2040,
    scenario: str = "RCP8.5",
    config: Optional[Any] = None,
    base_dir: Optional[str] = None,
) -> PhysicalAdjustments:
    """Get physical risk adjustments using PLANiT (CLIMADA + PhysRisk).

    Loads pre-computed result CSVs and converts via the PLANiT adapter.

    Args:
        year: Target projection year.
        scenario: CRP scenario label (e.g. "RCP4.5", "RCP8.5", "SSP1-2.6").
        config: Optional PLANiTIntegrationConfig (uses defaults if None).
        base_dir: Project root directory.

    Returns:
        PhysicalAdjustments with PLANiT-derived values.
    """
    from src.planit import PLANiTIntegrationConfig, PLANiTRunner, PLANiTAdapter

    if config is None:
        config = PLANiTIntegrationConfig()

    results_dir = str(config.get_results_dir(base_dir))
    results = PLANiTRunner.load_results_from_csv(results_dir)
    adapter = PLANiTAdapter(config)
    adj = adapter.convert(results, year, scenario)

    return PhysicalAdjustments(
        outage_rate=adj["outage_rate"],
        capacity_derate=adj["capacity_derate"],
        efficiency_loss=adj["efficiency_loss"],
        water_constrained_capacity=adj["water_constrained_capacity"],
        notes=adj["notes"],
    )


def create_yearly_physical_adjustments_from_planit(
    start_year: int = 2024,
    end_year: int = 2060,
    scenario: str = "RCP8.5",
    config: Optional[Any] = None,
    base_dir: Optional[str] = None,
) -> YearlyPhysicalAdjustments:
    """Create year-by-year physical adjustments from PLANiT.

    Args:
        start_year: First year of the projection window.
        end_year: Last year of the projection window.
        scenario: CRP scenario label.
        config: Optional PLANiTIntegrationConfig.
        base_dir: Project root directory.

    Returns:
        YearlyPhysicalAdjustments with arrays for each year.
    """
    from src.planit import PLANiTIntegrationConfig, PLANiTRunner, PLANiTAdapter

    if config is None:
        config = PLANiTIntegrationConfig()

    results_dir = str(config.get_results_dir(base_dir))
    results = PLANiTRunner.load_results_from_csv(results_dir)
    adapter = PLANiTAdapter(config)
    arrays = adapter.convert_yearly(results, start_year, end_year, scenario)

    return YearlyPhysicalAdjustments(
        years=arrays["years"],
        outage_rates=arrays["outage_rates"],
        capacity_derates=arrays["capacity_derates"],
        efficiency_losses=arrays["efficiency_losses"],
        water_constraints=arrays["water_constraints"],
        scenario_name=f"PLANiT ({scenario})",
    )

"""
Power Generation Loss Model.

Based on WRI-EBRD methodology from:
"Assessing Physical Climate Risks for the European Bank for
Reconstruction and Development's Power Generation Project
Investment Portfolio" (Luo et al., 2021)

Key findings:
- Coal plants lose 1.7% generation by 2030, 2.4% by 2040
- CCGT plants lose 0.8% by 2030, 1.1% by 2040
- Coal is 2× more vulnerable than CCGT

Loss drivers:
1. Water stress → Cooling water shortage
2. Water temperature → Cooling efficiency loss
3. Air temperature → Thermal efficiency loss
4. Drought → Forced outages

Sources:
- Luo et al. (2021) WRI Working Paper
- Van Vliet et al. (2016) Nature Climate Change
- IEA World Energy Outlook
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class PlantTechnology(Enum):
    """Power plant technology types."""
    COAL_SUBCRITICAL = "coal_subcritical"
    COAL_SUPERCRITICAL = "coal_supercritical"
    COAL_USC = "coal_usc"
    CCGT = "ccgt"
    OCGT = "ocgt"
    NUCLEAR = "nuclear"
    HYDRO = "hydro"


class CoolingType(Enum):
    """Cooling system types."""
    ONCE_THROUGH_SEA = "once_through_sea"
    ONCE_THROUGH_RIVER = "once_through_river"
    COOLING_TOWER_WET = "cooling_tower_wet"
    COOLING_TOWER_DRY = "cooling_tower_dry"
    HYBRID = "hybrid"
    AIR_COOLED = "air_cooled"


@dataclass
class WaterStressImpact:
    """
    Water stress impact on generation.

    From WRI-EBRD methodology and Aqueduct data.
    """
    baseline_wsi: float                  # Baseline water stress index (0-5)
    projected_wsi: float                 # Projected WSI
    generation_loss_pct: float           # Generation loss (%)
    curtailment_days: float              # Expected curtailment days/year
    confidence_interval: Tuple[float, float]  # CI for loss

    @property
    def wsi_change(self) -> float:
        """Change in water stress index."""
        return self.projected_wsi - self.baseline_wsi


@dataclass
class TemperatureImpact:
    """
    Temperature impact on generation.

    Based on thermodynamic efficiency relationships.
    """
    baseline_temp_c: float               # Baseline ambient temp
    projected_temp_c: float              # Projected temp
    efficiency_loss_pct: float           # Efficiency loss (%)
    capacity_derate_pct: float           # Capacity derate (%)
    heat_wave_days: float                # Days > threshold
    heat_wave_loss_pct: float            # Additional heat wave loss

    @property
    def temp_increase_c(self) -> float:
        """Temperature increase."""
        return self.projected_temp_c - self.baseline_temp_c


@dataclass
class GenerationLossResult:
    """
    Complete generation loss assessment.

    Combines all loss drivers following WRI-EBRD methodology.
    """
    plant_id: str
    plant_name: str
    technology: PlantTechnology
    scenario: str
    year: int

    # Baseline generation
    capacity_mw: float
    capacity_factor_baseline: float
    annual_generation_twh_baseline: float

    # Loss components (% of generation)
    water_stress_loss_pct: float = 0.0
    water_temp_loss_pct: float = 0.0
    air_temp_loss_pct: float = 0.0
    drought_loss_pct: float = 0.0
    heat_wave_loss_pct: float = 0.0

    # Totals
    total_loss_pct: float = 0.0
    total_loss_twh: float = 0.0

    # Financial impact
    electricity_price_usd_mwh: float = 60.0
    revenue_loss_usd: float = 0.0

    # Confidence
    loss_low_pct: float = 0.0
    loss_high_pct: float = 0.0

    def __post_init__(self):
        """Calculate derived values."""
        self.total_loss_pct = (
            self.water_stress_loss_pct +
            self.water_temp_loss_pct +
            self.air_temp_loss_pct +
            self.drought_loss_pct +
            self.heat_wave_loss_pct
        )
        self.total_loss_twh = self.annual_generation_twh_baseline * self.total_loss_pct / 100
        self.revenue_loss_usd = self.total_loss_twh * 1e6 * self.electricity_price_usd_mwh


# =============================================================================
# WRI-EBRD GENERATION LOSS FACTORS
# =============================================================================

# From Luo et al. (2021) WRI Working Paper, Table 5
GENERATION_LOSS_FACTORS = {
    # Coal plants
    PlantTechnology.COAL_SUBCRITICAL: {
        "baseline": {
            "water_stress_sensitivity": 0.015,   # 1.5% per unit WSI increase
            "temp_efficiency_coef": 0.0035,      # 0.35%/°C
            "drought_sensitivity": 0.020,        # 2% per drought month
            "heat_wave_derate": 0.02,            # 2% per heat wave day
        },
        2030: {
            "water_stress_loss_pct": 1.7,
            "total_loss_pct": 2.3,
            "confidence_interval": (1.2, 3.5),
        },
        2040: {
            "water_stress_loss_pct": 2.4,
            "total_loss_pct": 3.5,
            "confidence_interval": (1.8, 5.2),
        },
    },
    PlantTechnology.COAL_SUPERCRITICAL: {
        "baseline": {
            "water_stress_sensitivity": 0.012,
            "temp_efficiency_coef": 0.0030,
            "drought_sensitivity": 0.018,
            "heat_wave_derate": 0.018,
        },
        2030: {
            "water_stress_loss_pct": 1.5,
            "total_loss_pct": 2.0,
            "confidence_interval": (1.0, 3.0),
        },
        2040: {
            "water_stress_loss_pct": 2.1,
            "total_loss_pct": 3.0,
            "confidence_interval": (1.5, 4.5),
        },
    },
    PlantTechnology.COAL_USC: {
        "baseline": {
            "water_stress_sensitivity": 0.010,
            "temp_efficiency_coef": 0.0025,
            "drought_sensitivity": 0.015,
            "heat_wave_derate": 0.015,
        },
        2030: {
            "water_stress_loss_pct": 1.2,
            "total_loss_pct": 1.7,
            "confidence_interval": (0.8, 2.5),
        },
        2040: {
            "water_stress_loss_pct": 1.8,
            "total_loss_pct": 2.5,
            "confidence_interval": (1.2, 3.8),
        },
    },
    # CCGT plants (more resilient)
    PlantTechnology.CCGT: {
        "baseline": {
            "water_stress_sensitivity": 0.008,   # Less water-intensive
            "temp_efficiency_coef": 0.0020,      # Better heat tolerance
            "drought_sensitivity": 0.010,
            "heat_wave_derate": 0.010,
        },
        2030: {
            "water_stress_loss_pct": 0.8,
            "total_loss_pct": 1.1,
            "confidence_interval": (0.5, 1.8),
        },
        2040: {
            "water_stress_loss_pct": 1.1,
            "total_loss_pct": 1.6,
            "confidence_interval": (0.8, 2.5),
        },
    },
    # Nuclear
    PlantTechnology.NUCLEAR: {
        "baseline": {
            "water_stress_sensitivity": 0.012,
            "temp_efficiency_coef": 0.0030,
            "drought_sensitivity": 0.015,
            "heat_wave_derate": 0.020,
        },
        2030: {
            "water_stress_loss_pct": 1.4,
            "total_loss_pct": 1.9,
            "confidence_interval": (1.0, 2.8),
        },
        2040: {
            "water_stress_loss_pct": 2.0,
            "total_loss_pct": 2.8,
            "confidence_interval": (1.4, 4.2),
        },
    },
}

# Cooling system adjustments
COOLING_TYPE_FACTORS = {
    CoolingType.ONCE_THROUGH_SEA: {
        "water_stress_multiplier": 0.3,     # Seawater not affected by drought
        "temp_multiplier": 1.0,             # Sea temp rising
        "drought_multiplier": 0.2,          # Minimal impact
    },
    CoolingType.ONCE_THROUGH_RIVER: {
        "water_stress_multiplier": 1.5,     # Very vulnerable
        "temp_multiplier": 1.2,             # River temps higher
        "drought_multiplier": 2.0,          # Major impact
    },
    CoolingType.COOLING_TOWER_WET: {
        "water_stress_multiplier": 1.0,     # Baseline
        "temp_multiplier": 0.8,
        "drought_multiplier": 1.2,
    },
    CoolingType.COOLING_TOWER_DRY: {
        "water_stress_multiplier": 0.1,     # No water needed
        "temp_multiplier": 1.5,             # But more temp sensitive
        "drought_multiplier": 0.1,
    },
}


class GenerationLossModel:
    """
    WRI-EBRD Power Generation Loss Model.

    Calculates climate-related generation losses for power plants.
    """

    def __init__(
        self,
        scenario: str = "RCP8.5",
        electricity_price_usd_mwh: float = 60.0,
    ):
        self.scenario = scenario
        self.electricity_price = electricity_price_usd_mwh

    def calculate(
        self,
        plant_id: str,
        plant_name: str,
        technology: PlantTechnology,
        capacity_mw: float,
        capacity_factor: float,
        year: int,
        cooling_type: CoolingType = CoolingType.ONCE_THROUGH_SEA,
        water_stress_index: float = 2.0,
        baseline_temp_c: float = 25.0,
        temp_increase_c: float = 2.0,
        drought_months: float = 1.0,
        heat_wave_days: float = 15.0,
    ) -> GenerationLossResult:
        """
        Calculate generation loss for a power plant.

        Args:
            plant_id: Unique identifier
            plant_name: Plant name
            technology: Plant technology type
            capacity_mw: Installed capacity
            capacity_factor: Baseline capacity factor
            year: Target year
            cooling_type: Cooling system type
            water_stress_index: WRI Aqueduct WSI (0-5)
            baseline_temp_c: Baseline ambient temperature
            temp_increase_c: Temperature increase from climate change
            drought_months: Expected drought months per year
            heat_wave_days: Days with extreme heat per year

        Returns:
            GenerationLossResult with all loss components
        """
        # Get technology parameters
        tech_params = GENERATION_LOSS_FACTORS.get(technology, {})
        baseline_params = tech_params.get("baseline", {})

        # Get cooling type adjustments
        cooling_factors = COOLING_TYPE_FACTORS.get(
            cooling_type,
            COOLING_TYPE_FACTORS[CoolingType.ONCE_THROUGH_SEA]
        )

        # Calculate baseline generation
        annual_hours = 8760
        baseline_generation_twh = (
            capacity_mw * annual_hours * capacity_factor / 1e6
        )

        # Water stress loss
        water_stress_sensitivity = baseline_params.get("water_stress_sensitivity", 0.01)
        water_stress_loss = (
            water_stress_index *
            water_stress_sensitivity *
            cooling_factors["water_stress_multiplier"] *
            100  # Convert to %
        )

        # Water temperature loss (assume water temp tracks air temp)
        # Not explicitly modeled in WRI, but included for completeness
        water_temp_loss = temp_increase_c * 0.1 * cooling_factors["temp_multiplier"]

        # Air temperature / efficiency loss
        temp_coef = baseline_params.get("temp_efficiency_coef", 0.003)
        air_temp_loss = temp_increase_c * temp_coef * 100

        # Drought loss
        drought_sensitivity = baseline_params.get("drought_sensitivity", 0.015)
        drought_loss = (
            drought_months *
            drought_sensitivity *
            cooling_factors["drought_multiplier"] *
            100
        )

        # Heat wave loss
        heat_wave_derate = baseline_params.get("heat_wave_derate", 0.015)
        heat_wave_loss = heat_wave_days * heat_wave_derate * 100 / 365  # Annualize

        # Use WRI-EBRD lookup values if available for this year
        year_key = 2030 if year <= 2035 else 2040
        if year_key in tech_params:
            # Override with WRI-EBRD values as benchmark
            wri_total = tech_params[year_key].get("total_loss_pct", 0)
            loss_low, loss_high = tech_params[year_key].get(
                "confidence_interval", (wri_total * 0.7, wri_total * 1.5)
            )
        else:
            # Extrapolate
            wri_total = None
            loss_low = 0
            loss_high = 0

        return GenerationLossResult(
            plant_id=plant_id,
            plant_name=plant_name,
            technology=technology,
            scenario=self.scenario,
            year=year,
            capacity_mw=capacity_mw,
            capacity_factor_baseline=capacity_factor,
            annual_generation_twh_baseline=baseline_generation_twh,
            water_stress_loss_pct=water_stress_loss,
            water_temp_loss_pct=water_temp_loss,
            air_temp_loss_pct=air_temp_loss,
            drought_loss_pct=drought_loss,
            heat_wave_loss_pct=heat_wave_loss,
            electricity_price_usd_mwh=self.electricity_price,
            loss_low_pct=loss_low,
            loss_high_pct=loss_high,
        )

    def calculate_portfolio(
        self,
        plants: List[Dict],
        year: int,
    ) -> Dict[str, GenerationLossResult]:
        """
        Calculate generation losses for a portfolio of plants.

        Args:
            plants: List of plant dictionaries
            year: Target year

        Returns:
            Dict mapping plant_id to GenerationLossResult
        """
        results = {}
        for plant in plants:
            result = self.calculate(
                plant_id=plant["plant_id"],
                plant_name=plant["plant_name"],
                technology=plant.get("technology", PlantTechnology.COAL_SUPERCRITICAL),
                capacity_mw=plant["capacity_mw"],
                capacity_factor=plant.get("capacity_factor", 0.80),
                year=year,
                cooling_type=plant.get("cooling_type", CoolingType.ONCE_THROUGH_SEA),
                water_stress_index=plant.get("water_stress_index", 2.0),
                temp_increase_c=plant.get("temp_increase_c", 2.0),
            )
            results[plant["plant_id"]] = result
        return results


# =============================================================================
# KOREAN COAL FLEET ANALYSIS
# =============================================================================

def analyze_korean_coal_fleet(
    year: int = 2050,
    scenario: str = "RCP8.5",
) -> Dict[str, any]:
    """
    Analyze climate risk for Korean coal fleet.

    Returns portfolio-level generation loss assessment.
    """
    from .asset_exposure import KOREAN_COAL_FLEET

    model = GenerationLossModel(scenario=scenario)

    results = {}
    total_baseline_twh = 0
    total_loss_twh = 0
    total_revenue_loss = 0

    for plant_id, exposure in KOREAN_COAL_FLEET.items():
        # Map asset type to technology
        tech_map = {
            "coal_subcritical": PlantTechnology.COAL_SUBCRITICAL,
            "coal_supercritical": PlantTechnology.COAL_SUPERCRITICAL,
            "coal_usc": PlantTechnology.COAL_USC,
        }
        technology = tech_map.get(
            exposure.asset_type.value,
            PlantTechnology.COAL_SUPERCRITICAL
        )

        result = model.calculate(
            plant_id=plant_id,
            plant_name=exposure.asset_name,
            technology=technology,
            capacity_mw=exposure.capacity_mw,
            capacity_factor=exposure.capacity_factor,
            year=year,
            cooling_type=CoolingType.ONCE_THROUGH_SEA,  # All Korean coastal
            water_stress_index=1.5,  # Korea moderate water stress
            temp_increase_c=2.0 if "RCP8.5" in scenario else 1.5,
            drought_months=0.5,
            heat_wave_days=20,
        )

        results[plant_id] = result
        total_baseline_twh += result.annual_generation_twh_baseline
        total_loss_twh += result.total_loss_twh
        total_revenue_loss += result.revenue_loss_usd

    return {
        "scenario": scenario,
        "year": year,
        "num_plants": len(results),
        "total_capacity_mw": sum(r.capacity_mw for r in results.values()),
        "total_baseline_generation_twh": total_baseline_twh,
        "total_generation_loss_twh": total_loss_twh,
        "total_loss_pct": (total_loss_twh / total_baseline_twh * 100) if total_baseline_twh > 0 else 0,
        "total_revenue_loss_usd": total_revenue_loss,
        "by_plant": {k: v.total_loss_pct for k, v in results.items()},
        "wri_ebrd_benchmark": {
            "coal_2030": "1.7% generation loss",
            "coal_2040": "2.4% generation loss",
            "ccgt_2030": "0.8% generation loss",
        },
    }

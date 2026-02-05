"""
Temperature Efficiency Model.

Calculates thermal efficiency loss from:
1. Mean temperature increase (ambient + cooling water)
2. Heat wave events (extreme temperature days)
3. Cooling water temperature changes (for coastal plants)
4. Thermal gradient changes (intake vs. outlet temperature)

Data sources:
- KMA: Korea Meteorological Administration temperature projections
- KHOA: Korea Hydrographic and Oceanographic Agency SST data
- IPCC AR6: Global and East Asia temperature pathways
- Maulbetsch & DiFilippo (2006): Power plant efficiency vs temperature
- EPRI (2011): Power plant cooling system performance
- Loew et al. (2020): Climate change impacts on thermal power

Literature references:
- Maulbetsch, J.S. & DiFilippo, M.N. (2006). Cost and value of water use
  at combined-cycle power plants. California Energy Commission.
- van Vliet et al. (2012). Vulnerability of US and European electricity
  supply to climate change. Nature Climate Change.
- Zhou et al. (2018). Climate change impacts on thermal power production.
  Applied Energy.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any
from enum import Enum
import math


class CoolingType(Enum):
    """Power plant cooling system types."""
    ONCE_THROUGH = "once_through"     # Seawater once-through (coastal)
    COOLING_TOWER = "cooling_tower"   # Evaporative cooling tower
    DRY_COOLING = "dry_cooling"       # Air-cooled condenser
    HYBRID = "hybrid"                 # Combined wet/dry


@dataclass
class TemperatureProjection:
    """
    Temperature projection for a given year.

    Attributes:
        year: Target year
        scenario: RCP or SSP scenario
        delta_t_air: Air temperature change from baseline (°C)
        delta_t_sst: Sea surface temperature change (°C)
        heat_wave_days: Annual days with Tmax > 33°C
        tropical_nights: Annual nights with Tmin > 25°C
        max_temp_increase: Change in annual maximum temperature (°C)
        source: Data source citation
        confidence_low: Lower bound (10th percentile)
        confidence_high: Upper bound (90th percentile)
    """
    year: int
    scenario: str
    delta_t_air: float
    delta_t_sst: float
    heat_wave_days: float
    tropical_nights: float
    max_temp_increase: float
    source: str
    confidence_low: float = 0.0
    confidence_high: float = 0.0


@dataclass
class EfficiencyParameters:
    """
    Parameters for efficiency loss calculations.

    Based on literature values with Korea-specific calibration.
    All values are fraction per degree Celsius.

    Sources:
    - Maulbetsch & DiFilippo (2006): General efficiency relationships
    - EPRI (2011): Cooling system performance
    - Zhou et al. (2018): Korean coal plant specific data
    """
    # Ambient temperature effects
    air_temp_efficiency_coef: float = 0.0010     # 0.10%/°C turbine efficiency
    condenser_vacuum_coef: float = 0.0005        # 0.05%/°C condenser vacuum loss

    # Cooling water effects (once-through)
    cooling_water_coef: float = 0.0015           # 0.15%/°C cooling water
    min_delta_t_condenser: float = 10.0          # °C minimum temperature diff

    # Heat wave effects
    heat_wave_derate: float = 0.05               # 5% derate during heat waves
    extreme_heat_derate: float = 0.08            # 8% derate during extreme heat (>40°C)

    # Cooling tower specific
    wet_bulb_coef: float = 0.0012                # 0.12%/°C wet bulb temperature

    # Sources
    source: str = "Maulbetsch & DiFilippo (2006), EPRI (2011)"


@dataclass
class EfficiencyLossResult:
    """
    Result from efficiency loss calculation.

    Attributes:
        year: Target year
        scenario: RCP scenario
        delta_t: Temperature change (°C)
        mean_temp_derate: Efficiency loss from mean temperature
        heat_wave_derate: Efficiency loss from heat wave events
        cooling_water_derate: Efficiency loss from cooling water temp
        total_derate: Combined efficiency loss (fraction)
        capacity_factor_impact: Impact on capacity factor
        confidence_low: Lower bound estimate
        confidence_high: Upper bound estimate
        sources: List of data sources
    """
    year: int
    scenario: str
    delta_t: float
    mean_temp_derate: float
    heat_wave_derate: float
    cooling_water_derate: float
    total_derate: float
    capacity_factor_impact: float
    confidence_low: float
    confidence_high: float
    sources: List[str]


# =============================================================================
# TEMPERATURE PROJECTIONS BY SCENARIO
# =============================================================================

# RCP4.5 projections (moderate mitigation)
TEMPERATURE_PROJECTIONS_RCP45: Dict[int, TemperatureProjection] = {
    2024: TemperatureProjection(
        year=2024, scenario="RCP4.5",
        delta_t_air=0.0, delta_t_sst=0.0,
        heat_wave_days=7.0, tropical_nights=8.4,
        max_temp_increase=0.0,
        source="KMA baseline (1991-2020 average)",
        confidence_low=-0.2, confidence_high=0.2,
    ),
    2030: TemperatureProjection(
        year=2030, scenario="RCP4.5",
        delta_t_air=0.6, delta_t_sst=0.4,
        heat_wave_days=10.0, tropical_nights=11.5,
        max_temp_increase=0.5,
        source="KMA RCP4.5 near-term",
        confidence_low=0.3, confidence_high=0.9,
    ),
    2050: TemperatureProjection(
        year=2050, scenario="RCP4.5",
        delta_t_air=1.4, delta_t_sst=1.0,
        heat_wave_days=18.0, tropical_nights=23.4,
        max_temp_increase=1.2,
        source="KMA RCP4.5 mid-century",
        confidence_low=0.8, confidence_high=2.0,
    ),
    2100: TemperatureProjection(
        year=2100, scenario="RCP4.5",
        delta_t_air=2.3, delta_t_sst=1.8,
        heat_wave_days=30.0, tropical_nights=42.6,
        max_temp_increase=2.0,
        source="KMA RCP4.5 end-century",
        confidence_low=1.5, confidence_high=3.2,
    ),
}

# RCP8.5 projections (high emissions)
TEMPERATURE_PROJECTIONS_RCP85: Dict[int, TemperatureProjection] = {
    2024: TemperatureProjection(
        year=2024, scenario="RCP8.5",
        delta_t_air=0.0, delta_t_sst=0.0,
        heat_wave_days=7.0, tropical_nights=8.4,
        max_temp_increase=0.0,
        source="KMA baseline (1991-2020 average)",
        confidence_low=-0.2, confidence_high=0.2,
    ),
    2030: TemperatureProjection(
        year=2030, scenario="RCP8.5",
        delta_t_air=0.8, delta_t_sst=0.5,
        heat_wave_days=12.0, tropical_nights=14.2,
        max_temp_increase=0.7,
        source="KMA RCP8.5 near-term",
        confidence_low=0.4, confidence_high=1.2,
    ),
    2050: TemperatureProjection(
        year=2050, scenario="RCP8.5",
        delta_t_air=2.0, delta_t_sst=1.4,
        heat_wave_days=25.0, tropical_nights=37.2,
        max_temp_increase=1.8,
        source="KMA RCP8.5 mid-century",
        confidence_low=1.2, confidence_high=2.8,
    ),
    2100: TemperatureProjection(
        year=2100, scenario="RCP8.5",
        delta_t_air=4.7, delta_t_sst=3.5,
        heat_wave_days=50.0, tropical_nights=85.2,
        max_temp_increase=4.2,
        source="KMA RCP8.5 end-century",
        confidence_low=3.2, confidence_high=6.2,
    ),
}

# Combined projections dict
TEMPERATURE_PROJECTIONS: Dict[int, TemperatureProjection] = TEMPERATURE_PROJECTIONS_RCP85

ALL_TEMPERATURE_PROJECTIONS: Dict[str, Dict[int, TemperatureProjection]] = {
    "RCP4.5": TEMPERATURE_PROJECTIONS_RCP45,
    "RCP8.5": TEMPERATURE_PROJECTIONS_RCP85,
}


# =============================================================================
# COOLING WATER TEMPERATURE DATA
# =============================================================================
# Source: KHOA Korea Sea Surface Temperature observations

@dataclass
class SeaWaterTemperature:
    """Sea water temperature data for coastal power plants."""
    location: str
    month: int
    mean_temp_c: float
    max_temp_c: float
    delta_from_1990s: float
    source: str


# East coast summer SST data (July-August average at Samcheok)
SAMCHEOK_SST = {
    "annual_mean": 14.5,            # °C
    "summer_mean": 22.0,            # July-August
    "summer_max": 26.5,             # Peak temperature
    "warming_rate": 0.04,           # °C/year since 1990
    "source": "KHOA East Sea SST data (1990-2023)",
}


class TemperatureModel:
    """
    Enhanced temperature efficiency impact model.

    Calculates efficiency loss from temperature changes
    for coastal thermal power plants.

    Features:
    - Multiple RCP scenarios (4.5, 8.5)
    - Air and sea water temperature impacts
    - Heat wave and extreme heat events
    - Cooling type specific calculations
    - Confidence intervals

    Example:
        >>> model = TemperatureModel("RCP8.5")
        >>> result = model.calculate_efficiency_loss(2050)
        >>> print(f"Total derate: {result.total_derate:.2%}")
    """

    # Physical constants
    HOURS_PER_YEAR = 8760
    HOURS_PER_DAY = 24

    def __init__(
        self,
        rcp: str = "RCP8.5",
        cooling_type: CoolingType = CoolingType.ONCE_THROUGH,
        location: str = "samcheok",
    ):
        """
        Initialize temperature model.

        Args:
            rcp: RCP scenario ("RCP4.5" or "RCP8.5")
            cooling_type: Type of cooling system
            location: Plant location name
        """
        self.rcp = rcp
        self.cooling_type = cooling_type
        self.location = location
        self.params = EfficiencyParameters()

        # Set projections based on scenario
        if rcp in ALL_TEMPERATURE_PROJECTIONS:
            self.projections = ALL_TEMPERATURE_PROJECTIONS[rcp]
        else:
            self.projections = TEMPERATURE_PROJECTIONS_RCP85

    def set_scenario(self, rcp: str) -> None:
        """Set RCP scenario."""
        self.rcp = rcp
        if rcp in ALL_TEMPERATURE_PROJECTIONS:
            self.projections = ALL_TEMPERATURE_PROJECTIONS[rcp]

    def _interpolate_projection(self, year: int) -> TemperatureProjection:
        """Get interpolated projection for a given year."""
        years = sorted(self.projections.keys())

        if year <= years[0]:
            return self.projections[years[0]]
        if year >= years[-1]:
            return self.projections[years[-1]]

        # Find bracketing years
        for i, y in enumerate(years[:-1]):
            if years[i] <= year < years[i + 1]:
                y0, y1 = years[i], years[i + 1]
                p0, p1 = self.projections[y0], self.projections[y1]
                weight = (year - y0) / (y1 - y0)

                return TemperatureProjection(
                    year=year,
                    scenario=self.rcp,
                    delta_t_air=p0.delta_t_air + weight * (p1.delta_t_air - p0.delta_t_air),
                    delta_t_sst=p0.delta_t_sst + weight * (p1.delta_t_sst - p0.delta_t_sst),
                    heat_wave_days=p0.heat_wave_days + weight * (p1.heat_wave_days - p0.heat_wave_days),
                    tropical_nights=p0.tropical_nights + weight * (p1.tropical_nights - p0.tropical_nights),
                    max_temp_increase=p0.max_temp_increase + weight * (p1.max_temp_increase - p0.max_temp_increase),
                    source=f"Interpolated from {y0} and {y1}",
                    confidence_low=p0.confidence_low + weight * (p1.confidence_low - p0.confidence_low),
                    confidence_high=p0.confidence_high + weight * (p1.confidence_high - p0.confidence_high),
                )

        return self.projections[years[-1]]

    def get_delta_t(self, year: int) -> float:
        """Get air temperature change for a given year."""
        proj = self._interpolate_projection(year)
        return proj.delta_t_air

    def get_delta_t_sst(self, year: int) -> float:
        """Get sea surface temperature change for a given year."""
        proj = self._interpolate_projection(year)
        return proj.delta_t_sst

    def get_heat_wave_days(self, year: int) -> float:
        """Get annual heat wave days for a given year."""
        proj = self._interpolate_projection(year)
        return proj.heat_wave_days

    def calculate_mean_temp_derate(
        self,
        delta_t_air: float,
        delta_t_sst: float,
    ) -> float:
        """
        Calculate efficiency loss from mean temperature increase.

        Args:
            delta_t_air: Air temperature change (°C)
            delta_t_sst: Sea surface temperature change (°C)

        Returns:
            Efficiency loss fraction
        """
        # Air temperature effect on turbine and condenser
        air_effect = delta_t_air * (
            self.params.air_temp_efficiency_coef +
            self.params.condenser_vacuum_coef
        )

        # Cooling water temperature effect
        if self.cooling_type == CoolingType.ONCE_THROUGH:
            # Direct impact of SST on condenser
            cooling_effect = delta_t_sst * self.params.cooling_water_coef
        elif self.cooling_type == CoolingType.COOLING_TOWER:
            # Wet bulb temperature approximation
            wet_bulb_delta = delta_t_air * 0.7  # Approximate
            cooling_effect = wet_bulb_delta * self.params.wet_bulb_coef
        elif self.cooling_type == CoolingType.DRY_COOLING:
            # Air temperature directly affects cooling
            cooling_effect = delta_t_air * self.params.air_temp_efficiency_coef * 1.5
        else:
            cooling_effect = delta_t_sst * self.params.cooling_water_coef * 0.5

        return air_effect + cooling_effect

    def calculate_heat_wave_derate(
        self,
        heat_wave_days: float,
        max_temp_increase: float = 0.0,
    ) -> float:
        """
        Calculate efficiency loss from heat wave events.

        Args:
            heat_wave_days: Annual days with extreme heat
            max_temp_increase: Increase in maximum temperatures

        Returns:
            Efficiency loss fraction (annualized)
        """
        # Normal heat wave derate
        hw_hours = heat_wave_days * self.HOURS_PER_DAY
        normal_derate = (hw_hours / self.HOURS_PER_YEAR) * self.params.heat_wave_derate

        # Additional extreme heat effect (>40°C days)
        # Estimate: ~10% of heat wave days are extreme
        extreme_days = heat_wave_days * 0.1 * (1 + max_temp_increase * 0.2)
        extreme_hours = extreme_days * self.HOURS_PER_DAY
        extreme_derate = (extreme_hours / self.HOURS_PER_YEAR) * self.params.extreme_heat_derate

        return normal_derate + extreme_derate

    def calculate_efficiency_loss(self, year: int) -> EfficiencyLossResult:
        """
        Calculate comprehensive efficiency loss from temperature.

        Args:
            year: Target year

        Returns:
            EfficiencyLossResult with full breakdown
        """
        proj = self._interpolate_projection(year)

        # Mean temperature derate
        mean_temp_derate = self.calculate_mean_temp_derate(
            proj.delta_t_air,
            proj.delta_t_sst,
        )

        # Heat wave derate
        heat_wave_derate = self.calculate_heat_wave_derate(
            proj.heat_wave_days,
            proj.max_temp_increase,
        )

        # Cooling water specific derate (for once-through)
        if self.cooling_type == CoolingType.ONCE_THROUGH:
            # Additional effect from reduced thermal gradient
            summer_sst_increase = proj.delta_t_sst * 1.2  # Summer warming higher
            gradient_reduction = summer_sst_increase / self.params.min_delta_t_condenser
            cooling_water_derate = gradient_reduction * 0.002  # 0.2% per degree
        else:
            cooling_water_derate = 0.0

        # Total derate
        total_derate = mean_temp_derate + heat_wave_derate + cooling_water_derate

        # Capacity factor impact (slightly higher than efficiency)
        cf_impact = total_derate * 1.1

        # Confidence intervals
        # Scale with temperature uncertainty
        temp_uncertainty = (proj.confidence_high - proj.confidence_low) / proj.delta_t_air if proj.delta_t_air > 0 else 0.5
        confidence_low = total_derate * (1 - temp_uncertainty * 0.3)
        confidence_high = total_derate * (1 + temp_uncertainty * 0.5)

        sources = [
            proj.source,
            self.params.source,
            SAMCHEOK_SST["source"],
        ]

        return EfficiencyLossResult(
            year=year,
            scenario=self.rcp,
            delta_t=proj.delta_t_air,
            mean_temp_derate=mean_temp_derate,
            heat_wave_derate=heat_wave_derate,
            cooling_water_derate=cooling_water_derate,
            total_derate=total_derate,
            capacity_factor_impact=cf_impact,
            confidence_low=max(0, confidence_low),
            confidence_high=confidence_high,
            sources=sources,
        )

    def get_trajectory(
        self,
        start_year: int,
        end_year: int,
    ) -> Dict[int, EfficiencyLossResult]:
        """Get efficiency loss trajectory over time."""
        return {
            year: self.calculate_efficiency_loss(year)
            for year in range(start_year, end_year + 1)
        }

    def get_summary_table(self, years: List[int] = None) -> Dict[int, Dict[str, float]]:
        """
        Get summary table of temperature impacts.

        Args:
            years: List of years (default: [2024, 2030, 2050, 2100])

        Returns:
            Dict mapping year to impact values
        """
        if years is None:
            years = [2024, 2030, 2050, 2100]

        table = {}
        for year in years:
            result = self.calculate_efficiency_loss(year)
            table[year] = {
                "delta_t_air": self._interpolate_projection(year).delta_t_air,
                "delta_t_sst": self._interpolate_projection(year).delta_t_sst,
                "heat_wave_days": self._interpolate_projection(year).heat_wave_days,
                "mean_temp_derate": result.mean_temp_derate,
                "heat_wave_derate": result.heat_wave_derate,
                "cooling_water_derate": result.cooling_water_derate,
                "total_derate": result.total_derate,
                "confidence_low": result.confidence_low,
                "confidence_high": result.confidence_high,
            }

        return table

    def compare_scenarios(self, year: int) -> Dict[str, EfficiencyLossResult]:
        """
        Compare efficiency loss across RCP scenarios.

        Args:
            year: Target year

        Returns:
            Dict mapping scenario to result
        """
        results = {}
        original_rcp = self.rcp

        for rcp in ["RCP4.5", "RCP8.5"]:
            self.set_scenario(rcp)
            results[rcp] = self.calculate_efficiency_loss(year)

        self.set_scenario(original_rcp)
        return results


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def calculate_cooling_water_impact(
    sst_increase: float,
    cooling_type: CoolingType = CoolingType.ONCE_THROUGH,
) -> Dict[str, float]:
    """
    Calculate cooling water temperature impact on power plant.

    Args:
        sst_increase: Sea surface temperature increase (°C)
        cooling_type: Type of cooling system

    Returns:
        Dict with efficiency and capacity impacts
    """
    if cooling_type == CoolingType.ONCE_THROUGH:
        efficiency_loss = sst_increase * 0.0015  # 0.15%/°C
        capacity_derate = sst_increase * 0.002   # 0.2%/°C (summer curtailment)
    elif cooling_type == CoolingType.COOLING_TOWER:
        efficiency_loss = sst_increase * 0.0012
        capacity_derate = sst_increase * 0.001
    else:
        efficiency_loss = sst_increase * 0.002
        capacity_derate = sst_increase * 0.003

    return {
        "efficiency_loss": efficiency_loss,
        "capacity_derate": capacity_derate,
        "total_impact": efficiency_loss + capacity_derate,
    }


def get_korea_sst_projection(year: int, scenario: str = "RCP8.5") -> float:
    """
    Get Korea East Sea SST projection.

    Args:
        year: Target year
        scenario: RCP scenario

    Returns:
        Temperature increase from baseline (°C)
    """
    if scenario == "RCP8.5":
        projections = TEMPERATURE_PROJECTIONS_RCP85
    else:
        projections = TEMPERATURE_PROJECTIONS_RCP45

    years = sorted(projections.keys())

    if year <= years[0]:
        return projections[years[0]].delta_t_sst
    if year >= years[-1]:
        return projections[years[-1]].delta_t_sst

    for i, y in enumerate(years[:-1]):
        if years[i] <= year < years[i + 1]:
            y0, y1 = years[i], years[i + 1]
            t0 = projections[y0].delta_t_sst
            t1 = projections[y1].delta_t_sst
            return t0 + (t1 - t0) * (year - y0) / (y1 - y0)

    return 0.0

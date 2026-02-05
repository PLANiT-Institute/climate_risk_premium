"""
Heat Stress Damage Functions.

Maps extreme heat events to power plant efficiency and capacity impacts.

Heat stress affects thermal power plants through:
1. Reduced Carnot efficiency (higher condenser temperature)
2. Increased auxiliary power load (fans, pumps)
3. Derating to prevent equipment damage
4. Potential forced outages during extreme events

Sources:
- Maulbetsch & DiFilippo (2006): Power plant cooling performance
- EPRI (2011): Cooling system performance under climate change
- Miara et al. (2017): Climate change impacts on thermal power
- Loew et al. (2020): European power plant climate risk
- Bartos & Chester (2015): US thermoelectric vulnerability

See docs/sources/DAMAGE_FUNCTIONS.md for full citations.
"""
from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Dict
import math

from src.models.base import BaseDamageFunction


class HeatStressDamageFunction(BaseDamageFunction, ABC):
    """Base class for heat stress damage functions."""

    @property
    def hazard_type(self) -> str:
        return "heat_stress"


@dataclass
class TemperatureEfficiencyFunction(HeatStressDamageFunction):
    """
    Temperature-efficiency relationship function.

    Based on thermodynamic principles and empirical observations.

    For a Rankine cycle, efficiency decreases as condenser temperature increases:
    - ΔEff ≈ 0.10-0.15% per °C increase in condenser temperature
    - Condenser temp ≈ ambient/cooling water temp + approach temperature

    Parameters:
        efficiency_coef_per_c: Efficiency loss per degree C
        approach_temp_c: Approach temperature (condenser - cooling water)
        reference_temp_c: Reference ambient temperature

    Literature:
        Maulbetsch & DiFilippo (2006): 0.10-0.15%/°C
        EPRI (2011): 0.12%/°C average for coal plants
    """
    efficiency_coef_per_c: float = 0.0012    # 0.12%/°C (EPRI 2011)
    approach_temp_c: float = 10.0             # Typical approach temperature
    reference_temp_c: float = 15.0            # Reference ambient (15°C)
    max_efficiency_loss: float = 0.08         # 8% max loss

    @property
    def name(self) -> str:
        return "temperature_efficiency"

    @property
    def source(self) -> str:
        return "EPRI (2011), Maulbetsch & DiFilippo (2006) CEC Report"

    @property
    def parameters(self) -> Dict[str, float]:
        return {
            "efficiency_coef_per_c": self.efficiency_coef_per_c,
            "approach_temp_c": self.approach_temp_c,
            "reference_temp_c": self.reference_temp_c,
            "max_efficiency_loss": self.max_efficiency_loss,
        }

    def calculate(self, intensity: float, **kwargs) -> float:
        """
        Calculate efficiency loss from ambient temperature.

        Args:
            intensity: Ambient temperature (°C)
            cooling_water_temp: Cooling water inlet temp (optional)

        Returns:
            Efficiency loss fraction (0-1)
        """
        cooling_water_temp = kwargs.get("cooling_water_temp", None)

        # If cooling water temp provided, use it
        if cooling_water_temp is not None:
            temp_above_ref = cooling_water_temp - self.reference_temp_c
        else:
            # Estimate from ambient
            temp_above_ref = intensity - self.reference_temp_c

        if temp_above_ref <= 0:
            return 0.0

        efficiency_loss = temp_above_ref * self.efficiency_coef_per_c

        return min(self.max_efficiency_loss, efficiency_loss)


@dataclass
class HeatWaveCapacityFunction(HeatStressDamageFunction):
    """
    Heat wave capacity derate function.

    During heat waves, plants may need to derate to:
    1. Prevent equipment overheating
    2. Comply with thermal discharge limits
    3. Reduce auxiliary power consumption

    Parameters:
        threshold_temp_c: Temperature threshold for derating
        derate_per_c: Capacity derate per degree above threshold
        max_derate: Maximum capacity derate
        discharge_limit_c: Thermal discharge temperature limit

    Literature:
        Bartos & Chester (2015): 4-16% capacity reduction during heat waves
        Miara et al. (2017): 2-6% average, up to 15% extreme
    """
    threshold_temp_c: float = 35.0       # Heat wave threshold
    derate_per_c: float = 0.015          # 1.5% per degree above threshold
    max_derate: float = 0.15             # 15% maximum derate
    discharge_limit_c: float = 30.0      # Typical thermal discharge limit

    @property
    def name(self) -> str:
        return "heat_wave_capacity"

    @property
    def source(self) -> str:
        return "Bartos & Chester (2015), Miara et al. (2017)"

    @property
    def parameters(self) -> Dict[str, float]:
        return {
            "threshold_temp_c": self.threshold_temp_c,
            "derate_per_c": self.derate_per_c,
            "max_derate": self.max_derate,
            "discharge_limit_c": self.discharge_limit_c,
        }

    def calculate(self, intensity: float, **kwargs) -> float:
        """
        Calculate capacity derate during heat wave.

        Args:
            intensity: Ambient temperature (°C)
            duration_hours: Duration of heat event (optional)

        Returns:
            Capacity derate fraction (0-1)
        """
        duration_hours = kwargs.get("duration_hours", 24.0)

        if intensity < self.threshold_temp_c:
            return 0.0

        # Temperature-based derate
        temp_excess = intensity - self.threshold_temp_c
        temp_derate = temp_excess * self.derate_per_c

        # Duration factor (sustained heat is worse)
        if duration_hours > 72:  # 3+ days
            duration_factor = 1.3
        elif duration_hours > 24:  # 1-3 days
            duration_factor = 1.1
        else:
            duration_factor = 1.0

        total_derate = temp_derate * duration_factor

        return min(self.max_derate, total_derate)


@dataclass
class AnnualizedHeatImpactFunction(HeatStressDamageFunction):
    """
    Annualized heat stress impact function.

    Converts heat wave statistics to annual average impact.

    Parameters:
        baseline_heat_days: Baseline extreme heat days per year
        efficiency_loss_per_heat_day: Annualized efficiency loss
        capacity_loss_per_heat_day: Annualized capacity loss

    Literature:
        Loew et al. (2020): European power plant analysis
    """
    baseline_heat_days: float = 7.0        # Days > 35°C
    efficiency_loss_per_heat_day: float = 0.0001  # 0.01% per day
    capacity_loss_per_heat_day: float = 0.0002    # 0.02% per day

    @property
    def name(self) -> str:
        return "annualized_heat_impact"

    @property
    def source(self) -> str:
        return "Loew et al. (2020) Environmental Research Letters"

    @property
    def parameters(self) -> Dict[str, float]:
        return {
            "baseline_heat_days": self.baseline_heat_days,
            "efficiency_loss_per_heat_day": self.efficiency_loss_per_heat_day,
            "capacity_loss_per_heat_day": self.capacity_loss_per_heat_day,
        }

    def calculate(self, intensity: float = None, **kwargs) -> float:
        """
        Calculate annualized heat impact.

        Args:
            intensity: Heat days per year (optional, uses baseline if None)
            climate_factor: Climate change multiplier

        Returns:
            Annual average impact fraction (0-1)
        """
        climate_factor = kwargs.get("climate_factor", 1.0)

        # Heat days, either from input or baseline scaled by climate
        if intensity is not None:
            heat_days = intensity
        else:
            heat_days = self.baseline_heat_days * climate_factor

        # Combined impact
        total_loss = heat_days * (
            self.efficiency_loss_per_heat_day +
            self.capacity_loss_per_heat_day
        )

        return min(0.10, total_loss)  # Cap at 10%


@dataclass
class KoreaHeatStressFunction(HeatStressDamageFunction):
    """
    Korea-specific heat stress damage function.

    Based on KMA heat wave statistics and KEPCO operational data.

    Korean heat wave definition: Tmax ≥ 33°C
    Extreme heat: Tmax ≥ 38°C

    Historical (1991-2020):
    - Average heat wave days: 11.8 days/year
    - Extreme heat days: ~2 days/year
    - Longest heat wave: 2018 (31 days in Seoul)
    """
    # KMA baseline statistics
    baseline_heat_days: float = 11.8      # Days with Tmax ≥ 33°C
    baseline_extreme_days: float = 2.0    # Days with Tmax ≥ 38°C
    baseline_tropical_nights: float = 8.4 # Nights with Tmin ≥ 25°C

    # Impact coefficients
    heat_day_efficiency_loss: float = 0.002   # 0.2% per heat day (annualized)
    extreme_day_capacity_loss: float = 0.005  # 0.5% per extreme day (annualized)
    night_efficiency_penalty: float = 0.001   # 0.1% per tropical night

    @property
    def name(self) -> str:
        return "korea_heat_stress"

    @property
    def source(self) -> str:
        return "KMA Climate Data (1991-2020), KEPCO operational statistics"

    @property
    def parameters(self) -> Dict[str, float]:
        return {
            "baseline_heat_days": self.baseline_heat_days,
            "baseline_extreme_days": self.baseline_extreme_days,
            "baseline_tropical_nights": self.baseline_tropical_nights,
            "heat_day_efficiency_loss": self.heat_day_efficiency_loss,
            "extreme_day_capacity_loss": self.extreme_day_capacity_loss,
            "night_efficiency_penalty": self.night_efficiency_penalty,
        }

    def calculate(self, intensity: float = None, **kwargs) -> float:
        """
        Calculate annual heat stress impact for Korean plant.

        Args:
            intensity: Heat wave days (optional)
            climate_factor: Climate change multiplier
            year: Target year

        Returns:
            Annual impact fraction (0-1)
        """
        climate_factor = kwargs.get("climate_factor", 1.0)
        year = kwargs.get("year", 2024)

        # Project heat days with climate change
        # ~3x increase by 2100 under RCP8.5
        heat_days = self.baseline_heat_days * climate_factor
        extreme_days = self.baseline_extreme_days * (climate_factor ** 1.5)  # More extreme
        tropical_nights = self.baseline_tropical_nights * climate_factor

        # Calculate impacts
        efficiency_impact = (
            heat_days * self.heat_day_efficiency_loss +
            tropical_nights * self.night_efficiency_penalty
        )

        capacity_impact = extreme_days * self.extreme_day_capacity_loss

        total_impact = efficiency_impact + capacity_impact

        # Annualize (divide by 365)
        annual_impact = total_impact / 365

        return min(0.05, annual_impact)  # Cap at 5% annual average


# Parameter uncertainty ranges from literature
HEAT_STRESS_PARAMETER_UNCERTAINTY = {
    "temperature_efficiency": {
        "efficiency_coef_per_c": (0.0010, 0.0015),  # 0.10-0.15%/°C
        "source": "Maulbetsch & DiFilippo (2006): 0.10-0.15%/°C",
    },
    "heat_wave_capacity": {
        "derate_per_c": (0.01, 0.02),              # 1-2%/°C
        "max_derate": (0.10, 0.20),                # 10-20%
        "source": "Bartos & Chester (2015): 4-16% during heat waves",
    },
}

"""
Drought Damage Functions.

Maps drought indices to power plant capacity impacts.

Drought affects thermal power plants through:
1. Reduced cooling water availability
2. Water use restrictions (environmental regulations)
3. Increased cooling water temperature

Sources:
- van Vliet et al. (2012): Vulnerability of electricity supply to climate change
- Zhou et al. (2018): Climate change impacts on thermal power
- Byers et al. (2014): Electricity generation and cooling water use
- SPEI: Standardized Precipitation-Evapotranspiration Index
- Korean Ministry of Environment water stress data

See docs/sources/DAMAGE_FUNCTIONS.md for full citations.
"""
from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Dict, Optional
import math

from src.models.base import BaseDamageFunction


class DroughtDamageFunction(BaseDamageFunction, ABC):
    """Base class for drought damage functions."""

    @property
    def hazard_type(self) -> str:
        return "drought"


@dataclass
class SPEIDamageFunction(DroughtDamageFunction):
    """
    SPEI-based drought damage function.

    Uses Standardized Precipitation-Evapotranspiration Index (SPEI)
    to estimate capacity reductions.

    SPEI Scale:
    - SPEI > 0: Wet conditions
    - SPEI 0 to -1: Near normal to mildly dry
    - SPEI -1 to -1.5: Moderate drought
    - SPEI -1.5 to -2: Severe drought
    - SPEI < -2: Extreme drought

    Parameters:
        threshold_spei: SPEI threshold for impacts (default: -1.0)
        max_derate: Maximum capacity derate (fraction)
        extreme_spei: SPEI value at which max derate is reached
        cooling_type: Type of cooling (once_through, cooling_tower)

    Literature:
        van Vliet et al. (2012) Nature Climate Change: 5-10% capacity reduction
        during severe droughts for once-through cooling
    """
    threshold_spei: float = -1.0       # Moderate drought threshold
    max_derate: float = 0.10           # 10% max capacity reduction
    extreme_spei: float = -2.5         # Extreme drought
    cooling_type: str = "once_through"

    @property
    def name(self) -> str:
        return "spei_drought"

    @property
    def source(self) -> str:
        return "van Vliet et al. (2012) Nature Climate Change + SPEI database"

    @property
    def parameters(self) -> Dict[str, float]:
        return {
            "threshold_spei": self.threshold_spei,
            "max_derate": self.max_derate,
            "extreme_spei": self.extreme_spei,
            "cooling_type": 0.0 if self.cooling_type == "once_through" else 1.0,
        }

    def calculate(self, intensity: float, **kwargs) -> float:
        """
        Calculate capacity derate from SPEI value.

        Args:
            intensity: SPEI value (negative = dry)
            climate_factor: Climate change multiplier (optional)
            duration_months: Drought duration in months (optional)

        Returns:
            Capacity derate fraction (0-1)
        """
        climate_factor = kwargs.get("climate_factor", 1.0)
        duration_months = kwargs.get("duration_months", 3.0)

        # No impact if not in drought
        if intensity > self.threshold_spei:
            return 0.0

        # Adjust SPEI with climate factor (droughts become more severe)
        effective_spei = intensity * climate_factor

        # Linear interpolation between threshold and extreme
        drought_severity = (self.threshold_spei - effective_spei) / (self.threshold_spei - self.extreme_spei)
        drought_severity = min(1.0, max(0.0, drought_severity))

        # Duration factor (longer droughts have more impact)
        duration_factor = min(1.5, 1.0 + (duration_months - 3) * 0.1)

        # Cooling type adjustment
        if self.cooling_type == "cooling_tower":
            # Cooling towers less affected by drought
            cooling_factor = 0.5
        else:
            cooling_factor = 1.0

        derate = self.max_derate * drought_severity * duration_factor * cooling_factor

        return min(self.max_derate, derate)


@dataclass
class WaterStressDamageFunction(DroughtDamageFunction):
    """
    Water stress-based damage function.

    Uses water withdrawal as fraction of available water resources.

    Water Stress Index (WSI):
    - WSI < 0.1: Low stress
    - WSI 0.1-0.2: Low-medium stress
    - WSI 0.2-0.4: Medium-high stress
    - WSI > 0.4: High stress
    - WSI > 0.8: Extremely high stress

    Parameters:
        baseline_wsi: Baseline water stress index
        threshold_wsi: WSI threshold for curtailment
        curtailment_rate: Curtailment per unit WSI above threshold

    Literature:
        Byers et al. (2014): 2-15% capacity at risk during water stress
    """
    baseline_wsi: float = 0.15         # Korea average
    threshold_wsi: float = 0.40        # High stress threshold
    curtailment_rate: float = 0.20     # 20% curtailment per 0.1 WSI above threshold

    @property
    def name(self) -> str:
        return "water_stress"

    @property
    def source(self) -> str:
        return "Byers et al. (2014) Nature Climate Change, WRI Aqueduct data"

    @property
    def parameters(self) -> Dict[str, float]:
        return {
            "baseline_wsi": self.baseline_wsi,
            "threshold_wsi": self.threshold_wsi,
            "curtailment_rate": self.curtailment_rate,
        }

    def calculate(self, intensity: float, **kwargs) -> float:
        """
        Calculate curtailment from water stress index.

        Args:
            intensity: Water stress index (0-1)
            climate_factor: Climate change multiplier (optional)

        Returns:
            Capacity curtailment fraction (0-1)
        """
        climate_factor = kwargs.get("climate_factor", 1.0)

        # Effective WSI with climate factor
        effective_wsi = intensity * climate_factor

        if effective_wsi <= self.threshold_wsi:
            return 0.0

        # Linear curtailment above threshold
        excess_stress = effective_wsi - self.threshold_wsi
        curtailment = self.curtailment_rate * (excess_stress / 0.1)

        return min(0.50, curtailment)  # Cap at 50%


@dataclass
class KoreaDroughtFunction(DroughtDamageFunction):
    """
    Korea-specific drought damage function.

    Accounts for:
    - Coastal plants using seawater (less affected)
    - Inland plants with freshwater cooling (more affected)
    - Korean water management regulations

    Based on Korean Ministry of Environment drought response data.
    """
    # Korean drought statistics
    drought_frequency_per_decade: float = 2.0  # ~2 significant droughts per decade
    avg_drought_duration_months: float = 4.0   # Average duration
    coastal_plant: bool = True                  # Samcheok uses seawater
    max_curtailment: float = 0.05              # 5% max for coastal plants

    @property
    def name(self) -> str:
        return "korea_drought"

    @property
    def source(self) -> str:
        return "Korean Ministry of Environment, KMA drought records (1991-2023)"

    @property
    def parameters(self) -> Dict[str, float]:
        return {
            "drought_frequency_per_decade": self.drought_frequency_per_decade,
            "avg_drought_duration_months": self.avg_drought_duration_months,
            "coastal_plant": float(self.coastal_plant),
            "max_curtailment": self.max_curtailment,
        }

    def calculate(self, intensity: float = None, **kwargs) -> float:
        """
        Calculate annual drought impact for Korean plant.

        Args:
            intensity: SPEI or drought index (optional)
            climate_factor: Climate change multiplier
            year: Target year

        Returns:
            Annual capacity derate fraction (0-1)
        """
        climate_factor = kwargs.get("climate_factor", 1.0)
        year = kwargs.get("year", 2024)

        # Drought frequency increases with climate change
        # ~10% more droughts per degree warming
        drought_freq = self.drought_frequency_per_decade * climate_factor

        # Probability of drought in any given year
        annual_drought_prob = drought_freq / 10

        # Expected drought months per year
        expected_drought_months = annual_drought_prob * self.avg_drought_duration_months

        # Coastal plants use seawater - much less affected
        if self.coastal_plant:
            # Seawater availability not affected by drought
            # Minor impacts from warmer intake water
            derate = self.max_curtailment * (expected_drought_months / 12) * 0.3
        else:
            # Inland plants significantly affected
            derate = self.max_curtailment * (expected_drought_months / 12)

        return min(self.max_curtailment, derate)


# Parameter uncertainty ranges from literature
DROUGHT_PARAMETER_UNCERTAINTY = {
    "spei_drought": {
        "threshold_spei": (-0.8, -1.2),      # Range of thresholds in literature
        "max_derate": (0.05, 0.15),          # 5-15% from van Vliet et al.
        "source": "van Vliet et al. (2012): 5-12% reduction during severe droughts",
    },
    "water_stress": {
        "threshold_wsi": (0.3, 0.5),
        "curtailment_rate": (0.10, 0.30),
        "source": "Byers et al. (2014): 2-15% capacity at risk",
    },
}

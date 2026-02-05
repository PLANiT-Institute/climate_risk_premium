"""
Wildfire Damage Functions.

Maps Fire Weather Index (FWI) to outage rates for power infrastructure.

Sources:
- van Wagner (1987): Fire Weather Index system
- Korea Forest Service: Korean fire statistics
- World Weather Attribution: Climate change multipliers
- Syphard et al. (2017): Infrastructure vulnerability

See docs/sources/DAMAGE_FUNCTIONS.md for full citations.
"""
from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Dict
import math

from src.models.base import BaseDamageFunction


class WildfireDamageFunction(BaseDamageFunction, ABC):
    """Base class for wildfire damage functions."""

    @property
    def hazard_type(self) -> str:
        return "wildfire"


@dataclass
class FWILinearFunction(WildfireDamageFunction):
    """
    Linear FWI to outage rate function.

    Simple linear relationship between Fire Weather Index and outage probability.
    Suitable for moderate FWI ranges (10-40).

    Parameters:
        base_rate: Baseline outage rate at FWI=0
        slope: Outage rate increase per FWI unit
    """
    base_rate: float = 0.00001  # 0.001% baseline
    slope: float = 0.000002    # 0.0002% per FWI unit

    @property
    def name(self) -> str:
        return "fwi_linear"

    @property
    def source(self) -> str:
        return "van Wagner (1987), calibrated to Korea Forest Service data"

    @property
    def parameters(self) -> Dict[str, float]:
        return {
            "base_rate": self.base_rate,
            "slope": self.slope,
        }

    def calculate(self, intensity: float, **kwargs) -> float:
        """
        Calculate outage rate from FWI.

        Args:
            intensity: Fire Weather Index value
            climate_factor: Climate change multiplier (optional)

        Returns:
            Annual outage rate (0-1)
        """
        climate_factor = kwargs.get("climate_factor", 1.0)
        return self.base_rate + self.slope * intensity * climate_factor


@dataclass
class FWIExponentialFunction(WildfireDamageFunction):
    """
    Exponential FWI to outage rate function.

    Better for high FWI values where risk increases non-linearly.

    Parameters:
        a: Base coefficient
        b: Exponential rate
        threshold: FWI threshold for damage to start
    """
    a: float = 0.000001     # Coefficient
    b: float = 0.1          # Exponential rate
    threshold: float = 15   # FWI threshold

    @property
    def name(self) -> str:
        return "fwi_exponential"

    @property
    def source(self) -> str:
        return "Syphard et al. (2017), adapted for power infrastructure"

    @property
    def parameters(self) -> Dict[str, float]:
        return {
            "a": self.a,
            "b": self.b,
            "threshold": self.threshold,
        }

    def calculate(self, intensity: float, **kwargs) -> float:
        """
        Calculate outage rate from FWI using exponential model.

        Args:
            intensity: Fire Weather Index value
            climate_factor: Climate change multiplier (optional)

        Returns:
            Annual outage rate (0-1)
        """
        climate_factor = kwargs.get("climate_factor", 1.0)
        if intensity < self.threshold:
            return 0.0

        effective_fwi = (intensity - self.threshold) * climate_factor
        return self.a * math.exp(self.b * effective_fwi)


@dataclass
class KoreaForestServiceFunction(WildfireDamageFunction):
    """
    Korea-specific wildfire damage function.

    Based on Korea Forest Service fire statistics (2001-2023)
    and power grid outage correlations.

    Uses regional fire frequency data for Gangwon Province
    (where Samcheok is located).
    """
    # Calibrated from KFS data
    fires_per_year_baseline: float = 0.75  # Historical average near Samcheok
    outage_prob_per_fire: float = 0.005    # 0.5% chance of outage per nearby fire
    outage_duration_hours: float = 12       # Average outage duration

    @property
    def name(self) -> str:
        return "korea_forest_service"

    @property
    def source(self) -> str:
        return "Korea Forest Service Fire Statistics (2001-2023), KEPCO outage data"

    @property
    def parameters(self) -> Dict[str, float]:
        return {
            "fires_per_year_baseline": self.fires_per_year_baseline,
            "outage_prob_per_fire": self.outage_prob_per_fire,
            "outage_duration_hours": self.outage_duration_hours,
        }

    def calculate(self, intensity: float = None, **kwargs) -> float:
        """
        Calculate outage rate from Korean fire statistics.

        Args:
            intensity: Not used (uses statistical approach)
            climate_factor: Climate change multiplier (optional)
            year: Target year (optional, for trend adjustment)

        Returns:
            Annual outage rate (0-1)
        """
        climate_factor = kwargs.get("climate_factor", 1.0)
        year = kwargs.get("year", 2024)

        # Trend: fires increasing ~3% per year since 2000
        years_since_baseline = max(0, year - 2010)
        trend_factor = 1.0 + 0.03 * years_since_baseline

        # Adjusted fire frequency
        fires_per_year = self.fires_per_year_baseline * trend_factor * climate_factor

        # Expected outage hours per year
        expected_outage_hours = (
            fires_per_year *
            self.outage_prob_per_fire *
            self.outage_duration_hours
        )

        # Convert to annual rate
        hours_per_year = 8760
        return expected_outage_hours / hours_per_year

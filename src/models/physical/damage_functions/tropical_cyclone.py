"""
Tropical Cyclone Damage Functions.

Maps wind speed to damage for power infrastructure.

Sources:
- Emanuel (2011): TC damage as power function of wind
- Knutson et al. (2020): TC climate change projections
- CLIMADA TropCyclone module
- Holland (1980): Wind profile model

See docs/sources/DAMAGE_FUNCTIONS.md for full citations.
"""
from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Dict
import math

from src.models.base import BaseDamageFunction


class TCDamageFunction(BaseDamageFunction, ABC):
    """Base class for tropical cyclone damage functions."""

    @property
    def hazard_type(self) -> str:
        return "tropical_cyclone"


@dataclass
class WindSpeedPowerFunction(TCDamageFunction):
    """
    Power-law wind speed damage function.

    Based on Emanuel (2011): Damage ~ v^n where n ≈ 3.

    Parameters:
        threshold_ms: Wind speed threshold for damage (m/s)
        exponent: Power law exponent (typically 3)
        normalization: Normalization wind speed (m/s)
    """
    threshold_ms: float = 20.0   # ~40 knots, tropical storm
    exponent: float = 3.0        # Cubic relationship
    normalization_ms: float = 60.0  # ~120 knots, major hurricane

    @property
    def name(self) -> str:
        return "wind_power_law"

    @property
    def source(self) -> str:
        return "Emanuel (2011), Nature. Calibrated for power infrastructure."

    @property
    def parameters(self) -> Dict[str, float]:
        return {
            "threshold_ms": self.threshold_ms,
            "exponent": self.exponent,
            "normalization_ms": self.normalization_ms,
        }

    def calculate(self, intensity: float, **kwargs) -> float:
        """
        Calculate damage from wind speed.

        Args:
            intensity: Maximum sustained wind speed (m/s)
            climate_factor: Climate change multiplier (optional)

        Returns:
            Damage fraction (0-1)
        """
        climate_factor = kwargs.get("climate_factor", 1.0)

        if intensity < self.threshold_ms:
            return 0.0

        # Effective wind with climate factor (affects intensity, not frequency here)
        effective_wind = intensity * (climate_factor ** 0.5)  # Intensity scales slower

        # Power law damage
        normalized = (effective_wind - self.threshold_ms) / (self.normalization_ms - self.threshold_ms)
        damage = min(1.0, normalized ** self.exponent)

        return damage


@dataclass
class HollandWindFunction(TCDamageFunction):
    """
    Holland wind profile-based damage function.

    Uses the Holland (1980) parametric wind profile to estimate
    damage from cyclone parameters.

    Parameters:
        B: Holland B parameter (shape)
        rmax_km: Radius of maximum winds (km)
        vmax_threshold: Threshold for damage (m/s)
    """
    B: float = 1.5              # Typical Holland B
    rmax_km: float = 50.0       # Typical Rmax
    vmax_threshold: float = 25.0  # m/s

    @property
    def name(self) -> str:
        return "holland_profile"

    @property
    def source(self) -> str:
        return "Holland (1980), CLIMADA TropCyclone implementation"

    @property
    def parameters(self) -> Dict[str, float]:
        return {
            "B": self.B,
            "rmax_km": self.rmax_km,
            "vmax_threshold": self.vmax_threshold,
        }

    def calculate(self, intensity: float, **kwargs) -> float:
        """
        Calculate damage using Holland profile.

        Args:
            intensity: Maximum sustained wind speed at Rmax (m/s)
            distance_km: Distance from storm center (km)

        Returns:
            Damage fraction (0-1)
        """
        distance_km = kwargs.get("distance_km", self.rmax_km)

        if intensity < self.vmax_threshold:
            return 0.0

        # Wind at distance using Holland profile (simplified)
        r_ratio = self.rmax_km / max(distance_km, 1.0)
        exp_term = math.exp(-(r_ratio ** self.B))
        wind_at_distance = intensity * math.sqrt(r_ratio ** self.B * exp_term)

        if wind_at_distance < self.vmax_threshold:
            return 0.0

        # Damage from local wind
        normalized = (wind_at_distance - self.vmax_threshold) / (60.0 - self.vmax_threshold)
        return min(1.0, normalized ** 3)


@dataclass
class KoreaTyphooneFunction(TCDamageFunction):
    """
    Korea-specific typhoon damage function.

    Based on historical typhoon impacts in Korea:
    - IBTrACS data for Korean peninsula
    - KEPCO outage statistics
    - Climate change projections from Knutson et al. (2020)

    Note: Korea experiences weaker typhoons than tropical regions,
    but infrastructure may be less hardened.
    """
    # Calibrated from IBTrACS + KEPCO data
    events_per_year_baseline: float = 0.15   # ~6 damaging events / 40 years
    outage_prob_per_event: float = 0.01      # 1% chance of significant outage
    outage_duration_hours: float = 24         # Average outage

    @property
    def name(self) -> str:
        return "korea_typhoon"

    @property
    def source(self) -> str:
        return "IBTrACS + KEPCO data (1980-2023), Knutson et al. (2020) for projections"

    @property
    def parameters(self) -> Dict[str, float]:
        return {
            "events_per_year_baseline": self.events_per_year_baseline,
            "outage_prob_per_event": self.outage_prob_per_event,
            "outage_duration_hours": self.outage_duration_hours,
        }

    def calculate(self, intensity: float = None, **kwargs) -> float:
        """
        Calculate outage rate from Korean typhoon statistics.

        Args:
            intensity: Not used (statistical approach)
            climate_factor: Climate change multiplier (optional)
            year: Target year (optional)

        Returns:
            Annual outage rate (0-1)
        """
        climate_factor = kwargs.get("climate_factor", 1.0)

        # Knutson et al. (2020): TC intensity increases ~5% per degree warming
        # But frequency may decrease slightly
        # Net effect: intensity-weighted frequency roughly constant to +10%

        # Adjusted event rate
        events_per_year = self.events_per_year_baseline * climate_factor

        # Expected outage hours per year
        expected_outage_hours = (
            events_per_year *
            self.outage_prob_per_event *
            self.outage_duration_hours
        )

        # Convert to annual rate
        hours_per_year = 8760
        return expected_outage_hours / hours_per_year

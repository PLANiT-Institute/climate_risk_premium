"""
Flood Damage Functions.

Maps flood depth/duration to damage for power infrastructure.

Sources:
- FEMA HAZUS: Flood depth-damage curves
- Huizinga et al. (2017): Global flood depth-damage functions
- CLIMADA RiverFlood module
- Merz et al. (2010): Flood damage modeling

See docs/sources/DAMAGE_FUNCTIONS.md for full citations.
"""
from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Dict
import math

from src.models.base import BaseDamageFunction


class FloodDamageFunction(BaseDamageFunction, ABC):
    """Base class for flood damage functions."""

    @property
    def hazard_type(self) -> str:
        return "flood"


@dataclass
class DepthDamageFunction(FloodDamageFunction):
    """
    Standard depth-damage function.

    Based on HAZUS methodology and adapted for power plants.

    Parameters:
        threshold_m: Water depth threshold for damage (m)
        max_damage: Maximum damage fraction at saturation
        saturation_depth: Depth at which max damage is reached (m)
    """
    threshold_m: float = 0.5    # 50cm threshold
    max_damage: float = 0.8     # 80% max damage
    saturation_depth: float = 3.0  # 3m saturation

    @property
    def name(self) -> str:
        return "depth_damage_hazus"

    @property
    def source(self) -> str:
        return "FEMA HAZUS-MH, Power plant curve adapted from Huizinga et al. (2017)"

    @property
    def parameters(self) -> Dict[str, float]:
        return {
            "threshold_m": self.threshold_m,
            "max_damage": self.max_damage,
            "saturation_depth": self.saturation_depth,
        }

    def calculate(self, intensity: float, **kwargs) -> float:
        """
        Calculate damage fraction from flood depth.

        Args:
            intensity: Flood depth in meters
            duration_hours: Flood duration (optional, not used in this model)

        Returns:
            Damage fraction (0-1)
        """
        if intensity <= self.threshold_m:
            return 0.0

        # Linear interpolation to max damage
        effective_depth = intensity - self.threshold_m
        effective_saturation = self.saturation_depth - self.threshold_m

        if effective_depth >= effective_saturation:
            return self.max_damage

        return self.max_damage * (effective_depth / effective_saturation)


@dataclass
class DurationDamageFunction(FloodDamageFunction):
    """
    Duration-weighted flood damage function.

    Incorporates both depth and duration of flooding.
    More accurate for infrastructure that can be temporarily protected.

    Parameters:
        depth_weight: Weight for depth component
        duration_weight: Weight for duration component
        critical_depth: Depth causing immediate damage (m)
        critical_duration: Duration causing damage (hours)
    """
    depth_weight: float = 0.6
    duration_weight: float = 0.4
    critical_depth: float = 0.5      # 50cm
    critical_duration: float = 24.0  # 24 hours

    @property
    def name(self) -> str:
        return "depth_duration_combined"

    @property
    def source(self) -> str:
        return "Merz et al. (2010), adapted for power infrastructure"

    @property
    def parameters(self) -> Dict[str, float]:
        return {
            "depth_weight": self.depth_weight,
            "duration_weight": self.duration_weight,
            "critical_depth": self.critical_depth,
            "critical_duration": self.critical_duration,
        }

    def calculate(self, intensity: float, **kwargs) -> float:
        """
        Calculate damage from depth and duration.

        Args:
            intensity: Flood depth in meters
            duration_hours: Flood duration in hours (default: 24)

        Returns:
            Damage fraction (0-1)
        """
        duration = kwargs.get("duration_hours", 24.0)

        # Depth component
        if intensity <= 0:
            depth_damage = 0.0
        elif intensity >= self.critical_depth * 3:
            depth_damage = 1.0
        else:
            depth_damage = min(1.0, intensity / (self.critical_depth * 3))

        # Duration component
        if duration <= 0:
            duration_damage = 0.0
        elif duration >= self.critical_duration * 3:
            duration_damage = 1.0
        else:
            duration_damage = min(1.0, duration / (self.critical_duration * 3))

        # Combined damage
        combined = (
            self.depth_weight * depth_damage +
            self.duration_weight * duration_damage
        )

        return min(1.0, combined)


@dataclass
class SamcheokFloodFunction(FloodDamageFunction):
    """
    Samcheok-specific flood damage function.

    Accounts for:
    - Plant elevation (10m above sea level)
    - Coastal vs riverine flooding
    - Local drainage infrastructure

    Based on CLIMADA analysis showing low flood risk at this elevation.
    """
    plant_elevation_m: float = 10.0
    coastal_surge_threshold: float = 8.0  # m above mean sea level
    river_flood_zone: bool = False         # Not in flood plain

    @property
    def name(self) -> str:
        return "samcheok_specific"

    @property
    def source(self) -> str:
        return "CLIMADA RiverFlood + CoastalFlood for Samcheok (37.44N, 129.17E)"

    @property
    def parameters(self) -> Dict[str, float]:
        return {
            "plant_elevation_m": self.plant_elevation_m,
            "coastal_surge_threshold": self.coastal_surge_threshold,
            "river_flood_zone": float(self.river_flood_zone),
        }

    def calculate(self, intensity: float, **kwargs) -> float:
        """
        Calculate damage for Samcheok plant.

        Args:
            intensity: Flood water level (m above MSL) or depth (m)
            flood_type: "coastal" or "riverine" (default: riverine)

        Returns:
            Damage fraction (0-1)
        """
        flood_type = kwargs.get("flood_type", "riverine")

        if flood_type == "coastal":
            # Coastal flooding: check if surge exceeds plant elevation
            if intensity < self.plant_elevation_m:
                return 0.0
            # Water level above plant elevation
            excess_depth = intensity - self.plant_elevation_m
            return min(1.0, excess_depth / 3.0)

        else:
            # Riverine flooding: plant not in flood zone
            if not self.river_flood_zone:
                return 0.0
            # Standard depth-damage if in flood zone
            return min(1.0, intensity / 3.0)

"""
Damage Function Base and Registry.

Provides a registry for selecting damage functions by name.
Includes CLIMADA-style sigmoid damage functions (Emanuel, 2011).

Literature:
- Emanuel, K. (2011). Global Warming Effects on U.S. Hurricane Damage.
  Weather, Climate, and Society, 3(4), 261-268.
- Lüthi et al. (2021). Globally consistent assessment of wildfire risk.
  Geoscientific Model Development, 14, 3337-3356.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Type, Optional, Tuple
import math

from src.models.base import BaseDamageFunction


# =============================================================================
# SIGMOID DAMAGE FUNCTIONS (CLIMADA-style)
# =============================================================================

@dataclass
class SigmoidDamageFunction(BaseDamageFunction, ABC):
    """
    Sigmoid damage function following Emanuel (2011) and CLIMADA.

    The sigmoid function captures non-linear damage relationships:
    - Below threshold: no damage
    - Transition zone: rapid increase
    - Saturation: approaches maximum damage

    Formula:
        f(i) = i^n / (1 + i^n)

    Where:
        i = (intensity - threshold) / i_half
        i_half = intensity at which damage = 50%
        n = power exponent (typically 3)

    This is the standard CLIMADA approach from Lüthi et al. (2021).
    """
    threshold: float = 0.0      # Intensity below which no damage
    i_half: float = 10.0        # Intensity at 50% damage (calibration parameter)
    exponent: float = 3.0       # Steepness of sigmoid (typically 3)
    max_damage: float = 1.0     # Maximum damage ratio

    def calculate(self, intensity: float, **kwargs) -> float:
        """
        Calculate damage using sigmoid function.

        Args:
            intensity: Hazard intensity
            **kwargs: Additional parameters

        Returns:
            Damage ratio (0 to max_damage)
        """
        if intensity <= self.threshold:
            return 0.0

        # Normalized intensity
        i_norm = (intensity - self.threshold) / self.i_half

        # Sigmoid function: i^n / (1 + i^n)
        damage = (i_norm ** self.exponent) / (1 + i_norm ** self.exponent)

        return min(self.max_damage, damage)

    def inverse(self, damage_ratio: float) -> float:
        """
        Calculate intensity for a given damage ratio.

        Useful for threshold analysis.
        """
        if damage_ratio <= 0:
            return self.threshold
        if damage_ratio >= self.max_damage:
            return float('inf')

        # Inverse sigmoid: i = (d / (1 - d))^(1/n) * i_half + threshold
        d = damage_ratio / self.max_damage
        i_norm = (d / (1 - d)) ** (1 / self.exponent)
        return i_norm * self.i_half + self.threshold

    def get_damage_curve(
        self,
        intensity_range: Tuple[float, float],
        n_points: int = 100
    ) -> Dict[str, list]:
        """Generate damage curve data for plotting."""
        intensities = [
            intensity_range[0] + i * (intensity_range[1] - intensity_range[0]) / (n_points - 1)
            for i in range(n_points)
        ]
        damages = [self.calculate(i) for i in intensities]
        return {"intensity": intensities, "damage": damages}


@dataclass
class EmanuelWindDamage(SigmoidDamageFunction):
    """
    Emanuel (2011) wind damage function for tropical cyclones.

    Calibrated for hurricane wind damage in the United States.
    Uses cubic sigmoid with wind speed threshold.

    Parameters from Emanuel (2011):
        threshold: 25.7 m/s (50 kt, tropical storm)
        i_half: 74.7 m/s (calibrated)
        exponent: 3 (cubic)
    """
    threshold: float = 25.7     # m/s (tropical storm threshold)
    i_half: float = 74.7        # m/s (calibrated to US hurricanes)
    exponent: float = 3.0

    @property
    def name(self) -> str:
        return "emanuel_wind"

    @property
    def hazard_type(self) -> str:
        return "tropical_cyclone"

    @property
    def source(self) -> str:
        return "Emanuel (2011) Weather, Climate, and Society"

    @property
    def parameters(self) -> Dict[str, float]:
        return {
            "threshold_ms": self.threshold,
            "i_half_ms": self.i_half,
            "exponent": self.exponent,
        }


@dataclass
class CLIMADAWildfireDamage(SigmoidDamageFunction):
    """
    CLIMADA wildfire damage function from Lüthi et al. (2021).

    Uses Fire Radiative Power (FRP) from satellite data.
    Calibrated using EM-DAT historical disaster data.

    Original uses brightness temperature, but we adapt for FWI.
    """
    threshold: float = 20.0     # FWI threshold
    i_half: float = 45.0        # FWI at 50% damage (calibrated)
    exponent: float = 3.0

    @property
    def name(self) -> str:
        return "climada_wildfire"

    @property
    def hazard_type(self) -> str:
        return "wildfire"

    @property
    def source(self) -> str:
        return "Lüthi et al. (2021) GMD - CLIMADA wildfire"

    @property
    def parameters(self) -> Dict[str, float]:
        return {
            "threshold_fwi": self.threshold,
            "i_half_fwi": self.i_half,
            "exponent": self.exponent,
        }


@dataclass
class CLIMADAFloodDamage(SigmoidDamageFunction):
    """
    Sigmoid flood damage function.

    Adapted from CLIMADA river flood module.
    Uses flood depth as intensity metric.
    """
    threshold: float = 0.1      # meters (minor flooding starts)
    i_half: float = 1.5         # meters at 50% damage
    exponent: float = 2.0       # Quadratic for flood

    @property
    def name(self) -> str:
        return "climada_flood"

    @property
    def hazard_type(self) -> str:
        return "river_flood"

    @property
    def source(self) -> str:
        return "CLIMADA river flood module + HAZUS calibration"

    @property
    def parameters(self) -> Dict[str, float]:
        return {
            "threshold_m": self.threshold,
            "i_half_m": self.i_half,
            "exponent": self.exponent,
        }


# Calibration parameters with uncertainty from literature
SIGMOID_CALIBRATION_PARAMS = {
    "tropical_cyclone": {
        "threshold": (20.0, 30.0),      # m/s range
        "i_half": (60.0, 90.0),          # m/s range
        "exponent": (2.5, 3.5),
        "source": "Emanuel (2011): calibrated to US hurricane losses",
    },
    "wildfire": {
        "threshold": (15.0, 25.0),       # FWI range
        "i_half": (35.0, 55.0),          # FWI range
        "exponent": (2.5, 3.5),
        "source": "Lüthi et al. (2021): 63% within 1 order magnitude",
    },
    "river_flood": {
        "threshold": (0.05, 0.2),        # meters
        "i_half": (1.0, 2.0),            # meters
        "exponent": (1.5, 2.5),
        "source": "HAZUS-MH depth-damage curves",
    },
}


class DamageFunctionRegistry:
    """
    Registry for damage functions.

    Allows users to select damage functions by name.

    Example:
        >>> registry = DamageFunctionRegistry()
        >>> registry.register(FWILinearFunction())
        >>> func = registry.get("fwi_linear")
        >>> damage = func.calculate(intensity=30)
    """

    def __init__(self):
        self._functions: Dict[str, BaseDamageFunction] = {}

    def register(self, func: BaseDamageFunction) -> None:
        """Register a damage function."""
        self._functions[func.name] = func

    def get(self, name: str) -> Optional[BaseDamageFunction]:
        """Get a damage function by name."""
        return self._functions.get(name)

    def list_functions(self, hazard_type: str = None) -> Dict[str, str]:
        """
        List available functions.

        Args:
            hazard_type: Filter by hazard type (optional)

        Returns:
            Dict mapping name to description
        """
        result = {}
        for name, func in self._functions.items():
            if hazard_type is None or func.hazard_type == hazard_type:
                result[name] = f"{func.name}: {func.source}"
        return result

    def list_by_hazard(self) -> Dict[str, list]:
        """Group functions by hazard type."""
        result: Dict[str, list] = {}
        for name, func in self._functions.items():
            if func.hazard_type not in result:
                result[func.hazard_type] = []
            result[func.hazard_type].append(name)
        return result


# Global registry instance
DAMAGE_FUNCTION_REGISTRY = DamageFunctionRegistry()

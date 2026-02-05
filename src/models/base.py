"""
Base classes for Climate Risk Premium Model.

All risk models, scenarios, and damage functions inherit from these base classes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum


class RiskType(Enum):
    """Types of climate risk."""
    TRANSITION = "transition"
    PHYSICAL = "physical"


@dataclass
class RiskResult:
    """
    Standard result from any risk calculation.

    Attributes:
        risk_type: Type of risk (transition or physical)
        value: Primary risk value (e.g., outage rate, capacity derate)
        unit: Unit of the value (e.g., "fraction", "percent", "USD/MWh")
        year: Target year for this result
        scenario: Scenario name used
        components: Breakdown of contributing factors
        sources: List of data sources used
        notes: Additional context
    """
    risk_type: RiskType
    value: float
    unit: str
    year: int
    scenario: str
    components: Dict[str, float] = field(default_factory=dict)
    sources: List[str] = field(default_factory=list)
    notes: str = ""


class BaseScenario(ABC):
    """
    Abstract base class for all scenarios.

    Scenarios define the future pathway assumptions (climate, policy, market).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Scenario identifier."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""
        pass

    @property
    @abstractmethod
    def source(self) -> str:
        """Data source citation."""
        pass

    @abstractmethod
    def get_value(self, year: int) -> float:
        """Get scenario value for a given year."""
        pass


class BaseDamageFunction(ABC):
    """
    Abstract base class for damage functions.

    Damage functions map hazard intensity to infrastructure impact.
    Each function has a documented literature source.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Function identifier."""
        pass

    @property
    @abstractmethod
    def hazard_type(self) -> str:
        """Type of hazard this function handles."""
        pass

    @property
    @abstractmethod
    def source(self) -> str:
        """Literature source citation."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, float]:
        """Function parameters with documentation."""
        pass

    @abstractmethod
    def calculate(self, intensity: float, **kwargs) -> float:
        """
        Calculate damage from hazard intensity.

        Args:
            intensity: Hazard intensity (e.g., wind speed, flood depth)
            **kwargs: Additional context (year, location, etc.)

        Returns:
            Damage value (0-1 for fractional damage)
        """
        pass


class BaseRiskModel(ABC):
    """
    Abstract base class for risk models.

    Risk models combine scenarios and damage functions to calculate
    the financial impact of climate risks on infrastructure.
    """

    def __init__(self, name: str):
        self._name = name
        self._scenarios: Dict[str, BaseScenario] = {}
        self._damage_functions: Dict[str, BaseDamageFunction] = {}

    @property
    def name(self) -> str:
        """Model identifier."""
        return self._name

    @property
    @abstractmethod
    def risk_type(self) -> RiskType:
        """Type of risk this model calculates."""
        pass

    def register_scenario(self, scenario: BaseScenario) -> None:
        """Register a scenario for use in calculations."""
        self._scenarios[scenario.name] = scenario

    def register_damage_function(self, func: BaseDamageFunction) -> None:
        """Register a damage function for use in calculations."""
        self._damage_functions[func.name] = func

    def list_scenarios(self) -> List[str]:
        """List available scenario names."""
        return list(self._scenarios.keys())

    def list_damage_functions(self) -> List[str]:
        """List available damage function names."""
        return list(self._damage_functions.keys())

    @abstractmethod
    def calculate(
        self,
        year: int,
        scenario_name: str,
        damage_function_name: Optional[str] = None,
        **kwargs
    ) -> RiskResult:
        """
        Calculate risk for a given year and scenario.

        Args:
            year: Target year for calculation
            scenario_name: Name of registered scenario to use
            damage_function_name: Optional specific damage function
            **kwargs: Additional parameters (plant specs, location, etc.)

        Returns:
            RiskResult with calculated values
        """
        pass

    @abstractmethod
    def calculate_trajectory(
        self,
        start_year: int,
        end_year: int,
        scenario_name: str,
        **kwargs
    ) -> Dict[int, RiskResult]:
        """
        Calculate risk trajectory over time.

        Args:
            start_year: First year
            end_year: Last year
            scenario_name: Scenario to use
            **kwargs: Additional parameters

        Returns:
            Dict mapping year to RiskResult
        """
        pass

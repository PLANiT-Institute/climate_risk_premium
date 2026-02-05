"""
Core types and interfaces for risk modeling modules.

This module provides the foundational data structures and protocols
used across all risk assessment components to ensure consistency
and enable modular development.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Dict, Any, Optional, Union, List
from enum import Enum
import numpy as np


class RiskType(Enum):
    """Types of climate-related financial risks."""
    PHYSICAL = "physical"
    TRANSITION = "transition"
    COMPOUND = "compound"


class RatingCategory(Enum):
    """Credit rating categories following major rating agency scales."""
    INVESTMENT_GRADE = "investment_grade"
    SPECULATIVE_GRADE = "speculative_grade"
    DISTRESSED = "distressed"
    DEFAULT = "default"


@dataclass
class RiskMetrics:
    """Container for normalized risk metrics across different risk types."""
    expected_loss_pct: float
    probability_of_default: float
    loss_given_default: float
    credit_vaR_95: float  # Value at Risk at 95% confidence
    credit_vaR_99: float  # Value at Risk at 99% confidence
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for serialization."""
        return {
            "expected_loss_pct": self.expected_loss_pct,
            "probability_of_default": self.probability_of_default,
            "loss_given_default": self.loss_given_default,
            "credit_vaR_95": self.credit_vaR_95,
            "credit_vaR_99": self.credit_vaR_99,
        }


@dataclass
class PlantCharacteristics:
    """Standardized plant characteristics for risk assessment."""
    capacity_mw: float
    plant_type: str  # "Coal", "Gas", "Renewable", etc.
    location: str
    construction_cost_million: float
    base_capacity_factor: float
    operating_years: int
    efficiency_rate: float
    fuel_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "capacity_mw": self.capacity_mw,
            "plant_type": self.plant_type,
            "location": self.location,
            "construction_cost_million": self.construction_cost_million,
            "base_capacity_factor": self.base_capacity_factor,
            "operating_years": self.operating_years,
            "efficiency_rate": self.efficiency_rate,
            "fuel_type": self.fuel_type,
        }


@dataclass
class ScenarioParameters:
    """Parameters defining a climate risk scenario."""
    name: str
    risk_type: RiskType
    description: str
    severity_score: float  # 0-1 scale
    
    # Scenario-specific parameters
    carbon_price_per_ton: Optional[float] = None
    temperature_change_celsius: Optional[float] = None
    sea_level_rise_meters: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "risk_type": self.risk_type.value,
            "description": self.description,
            "severity_score": self.severity_score,
            "carbon_price_per_ton": self.carbon_price_per_ton,
            "temperature_change_celsius": self.temperature_change_celsius,
            "sea_level_rise_meters": self.sea_level_rise_meters,
        }


class RiskModel(Protocol):
    """Protocol for all risk model implementations."""
    
    def assess_risk(
        self,
        plant: PlantCharacteristics,
        scenario: ScenarioParameters,
        year: int = 2024
    ) -> RiskMetrics:
        """Assess risk for given plant and scenario."""
        ...
    
    def get_confidence_intervals(
        self,
        plant: PlantCharacteristics,
        scenario: ScenarioParameters,
        confidence_levels: List[float] = [0.5, 0.9, 0.95, 0.99]
    ) -> Dict[float, float]:
        """Get confidence intervals for risk metrics."""
        ...


@dataclass
class RiskAssessmentResult:
    """Complete risk assessment result with metadata."""
    plant: PlantCharacteristics
    scenario: ScenarioParameters
    baseline_metrics: RiskMetrics
    risk_adjusted_metrics: RiskMetrics
    assessment_year: int
    model_version: str
    
    @property
    def impact(self) -> RiskMetrics:
        """Calculate the impact (difference) between risk and baseline."""
        return RiskMetrics(
            expected_loss_pct=(
                self.risk_adjusted_metrics.expected_loss_pct - 
                self.baseline_metrics.expected_loss_pct
            ),
            probability_of_default=(
                self.risk_adjusted_metrics.probability_of_default - 
                self.baseline_metrics.probability_of_default
            ),
            loss_given_default=(
                self.risk_adjusted_metrics.loss_given_default - 
                self.baseline_metrics.loss_given_default
            ),
            credit_vaR_95=(
                self.risk_adjusted_metrics.credit_vaR_95 - 
                self.baseline_metrics.credit_vaR_95
            ),
            credit_vaR_99=(
                self.risk_adjusted_metrics.credit_vaR_99 - 
                self.baseline_metrics.credit_vaR_99
            ),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to comprehensive dictionary for serialization."""
        return {
            "plant": self.plant.to_dict(),
            "scenario": self.scenario.to_dict(),
            "baseline_metrics": self.baseline_metrics.to_dict(),
            "risk_adjusted_metrics": self.risk_adjusted_metrics.to_dict(),
            "impact": self.impact.to_dict(),
            "assessment_year": self.assessment_year,
            "model_version": self.model_version,
        }


# Type aliases for better readability
Numeric = Union[int, float]
Probability = float  # 0-1 scale
Percentage = float  # 0-100 scale
BasisPoints = float  # basis points
CurrencyAmount = float  # in specified currency (typically USD or KRW)
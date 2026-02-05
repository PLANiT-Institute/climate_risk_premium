"""
Core module for risk modeling infrastructure.

Provides foundational types, utilities, and validation functions
used across all risk assessment components.
"""

from .types import (
    RiskType,
    RatingCategory,
    RiskMetrics,
    PlantCharacteristics,
    ScenarioParameters,
    RiskModel,
    RiskAssessmentResult,
    Numeric,
    Probability,
    Percentage,
    BasisPoints,
    CurrencyAmount,
)

from .utils import (
    validate_financial_inputs,
    interpolate_linear,
    calculate_probability_of_default,
    calculate_recovery_rate,
    calculate_credit_var,
    monte_carlo_rating_migration,
    format_financial_value,
    calculate_stress_factor,
    validate_scenario_consistency,
    log_risk_assessment,
    ValidationResult,
)

__all__ = [
    # Types
    "RiskType",
    "RatingCategory",
    "RiskMetrics",
    "PlantCharacteristics",
    "ScenarioParameters",
    "RiskModel",
    "RiskAssessmentResult",
    "Numeric",
    "Probability",
    "Percentage",
    "BasisPoints",
    "CurrencyAmount",
    
    # Utilities
    "validate_financial_inputs",
    "interpolate_linear",
    "calculate_probability_of_default",
    "calculate_recovery_rate",
    "calculate_credit_var",
    "monte_carlo_rating_migration",
    "format_financial_value",
    "calculate_stress_factor",
    "validate_scenario_consistency",
    "log_risk_assessment",
    "ValidationResult",
]
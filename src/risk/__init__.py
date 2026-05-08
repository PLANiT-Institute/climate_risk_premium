"""Risk adjustment modules."""

from .transition import TransitionAdjustments, apply_transition, YearlyTransitionAdjustments, create_yearly_transition_adjustments
from .physical import (
    PhysicalAdjustments,
    YearlyPhysicalAdjustments,
    load_yearly_from_output_csv,
)
from .financing import (
    FinancingImpact,
    map_expected_loss_to_spreads,
    calculate_expected_loss,
    calculate_financing_from_rating
)
from .credit_rating import (
    Rating,
    RatingMetrics,
    RatingAssessment,
    assess_credit_rating,
    calculate_rating_metrics_from_financials,
)
from .attribution import decompose_risk_shapley

__all__ = [
    "TransitionAdjustments",
    "apply_transition",
    "YearlyTransitionAdjustments",
    "create_yearly_transition_adjustments",
    "PhysicalAdjustments",
    "YearlyPhysicalAdjustments",
    "load_yearly_from_output_csv",
    "FinancingImpact",
    "map_expected_loss_to_spreads",
    "calculate_expected_loss",
    "calculate_financing_from_rating",
    "Rating",
    "RatingMetrics",
    "RatingAssessment",
    "assess_credit_rating",
    "calculate_rating_metrics_from_financials",
    "decompose_risk_shapley",
]

"""Risk adjustment modules."""

from .transition import TransitionAdjustments, apply_transition, YearlyTransitionAdjustments, create_yearly_transition_adjustments
from .physical import (
    PhysicalAdjustments,
    YearlyPhysicalAdjustments,
    apply_physical,
)

# Optional imports for PLANiT integration
try:
    from .physical import get_physical_risk_from_planit, create_yearly_physical_adjustments_from_planit
except ImportError:
    get_physical_risk_from_planit = None
    create_yearly_physical_adjustments_from_planit = None
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
    rating_migration_analysis,
)
from .attribution import decompose_risk_shapley

__all__ = [
    "TransitionAdjustments",
    "apply_transition",
    "YearlyTransitionAdjustments",
    "create_yearly_transition_adjustments",
    "PhysicalAdjustments",
    "YearlyPhysicalAdjustments",
    "apply_physical",
    "get_physical_risk_from_planit",
    "create_yearly_physical_adjustments_from_planit",
    "FinancingImpact",
    "map_expected_loss_to_spreads",
    "calculate_expected_loss",
    "calculate_financing_from_rating",
    "Rating",
    "RatingMetrics",
    "RatingAssessment",
    "assess_credit_rating",
    "calculate_rating_metrics_from_financials",
    "rating_migration_analysis",
    "decompose_risk_shapley",
]

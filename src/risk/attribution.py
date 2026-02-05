"""
Shapley-value based risk attribution for CRP decomposition.

Decomposes the combined Climate Risk Premium into:
- Transition risk contribution
- Physical risk contribution
- Interaction (non-linear cross) effect

Reference: Shapley, L.S. (1953). "A Value for n-Person Games."
For two players, the Shapley value has a closed-form solution.
"""
from __future__ import annotations


def decompose_risk_shapley(
    baseline_crp: float,
    transition_only_crp: float,
    physical_only_crp: float,
    combined_crp: float,
) -> dict:
    """
    Decompose CRP into risk factor contributions using Shapley values.

    For two players (transition T, physical P), the Shapley value is:

        φ(T) = 0.5 * [ (combined - physical_only) + (transition_only - baseline) ]
        φ(P) = 0.5 * [ (combined - transition_only) + (physical_only - baseline) ]

    The interaction effect captures the non-additive (superadditive or subadditive)
    component:

        interaction = combined - transition_only - physical_only + baseline

    Consistency check:
        φ(T) + φ(P) = combined - baseline  (efficiency property)

    Args:
        baseline_crp: CRP with no risk adjustments applied.
        transition_only_crp: CRP with only transition risk.
        physical_only_crp: CRP with only physical risk.
        combined_crp: CRP with both risks applied.

    Returns:
        Dict with transition_contribution_bps, physical_contribution_bps,
        interaction_effect_bps.
    """
    # Marginal contributions
    # T joining empty coalition: transition_only - baseline
    # T joining {P}: combined - physical_only
    transition_contribution = 0.5 * (
        (combined_crp - physical_only_crp) + (transition_only_crp - baseline_crp)
    )

    # P joining empty coalition: physical_only - baseline
    # P joining {T}: combined - transition_only
    physical_contribution = 0.5 * (
        (combined_crp - transition_only_crp) + (physical_only_crp - baseline_crp)
    )

    # Interaction: non-additive residual
    interaction = (
        combined_crp - transition_only_crp - physical_only_crp + baseline_crp
    )

    return {
        "transition_contribution_bps": transition_contribution,
        "physical_contribution_bps": physical_contribution,
        "interaction_effect_bps": interaction,
    }

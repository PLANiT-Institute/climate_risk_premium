"""
Tests for risk attribution (Shapley decomposition) and decompose mode.
"""
import pytest
from src.risk.attribution import decompose_risk_shapley


# ── Unit tests for Shapley decomposition ──────────────────────────────────────

class TestDecomposeRiskShapley:
    """Pure math tests for the Shapley value function."""

    def test_shapley_sum_equals_total_minus_baseline(self):
        """φ(T) + φ(P) must equal combined - baseline (efficiency property)."""
        baseline, trans, phys, combined = 10.0, 30.0, 25.0, 55.0
        result = decompose_risk_shapley(baseline, trans, phys, combined)
        total = result["transition_contribution_bps"] + result["physical_contribution_bps"]
        assert pytest.approx(total) == combined - baseline

    def test_single_risk_no_interaction(self):
        """When one risk is zero, interaction effect should be zero."""
        # Only transition risk (physical_only == baseline)
        baseline, trans, phys, combined = 10.0, 30.0, 10.0, 30.0
        result = decompose_risk_shapley(baseline, trans, phys, combined)
        assert pytest.approx(result["interaction_effect_bps"]) == 0.0
        assert pytest.approx(result["transition_contribution_bps"]) == 20.0
        assert pytest.approx(result["physical_contribution_bps"]) == 0.0

    def test_single_risk_physical_only(self):
        """When only physical risk exists, transition contribution is zero."""
        baseline, trans, phys, combined = 5.0, 5.0, 20.0, 20.0
        result = decompose_risk_shapley(baseline, trans, phys, combined)
        assert pytest.approx(result["transition_contribution_bps"]) == 0.0
        assert pytest.approx(result["physical_contribution_bps"]) == 15.0
        assert pytest.approx(result["interaction_effect_bps"]) == 0.0

    def test_both_zero_risk(self):
        """All contributions zero when no risks are applied."""
        v = 10.0
        result = decompose_risk_shapley(v, v, v, v)
        assert pytest.approx(result["transition_contribution_bps"]) == 0.0
        assert pytest.approx(result["physical_contribution_bps"]) == 0.0
        assert pytest.approx(result["interaction_effect_bps"]) == 0.0

    def test_superadditive_interaction(self):
        """Positive interaction when combined > sum of individual effects."""
        baseline, trans, phys, combined = 0.0, 10.0, 15.0, 35.0
        result = decompose_risk_shapley(baseline, trans, phys, combined)
        # interaction = 35 - 10 - 15 + 0 = 10
        assert pytest.approx(result["interaction_effect_bps"]) == 10.0
        # Shapley sum still holds
        total = result["transition_contribution_bps"] + result["physical_contribution_bps"]
        assert pytest.approx(total) == 35.0

    def test_subadditive_interaction(self):
        """Negative interaction when combined < sum of individual effects."""
        baseline, trans, phys, combined = 0.0, 20.0, 15.0, 30.0
        result = decompose_risk_shapley(baseline, trans, phys, combined)
        # interaction = 30 - 20 - 15 + 0 = -5
        assert pytest.approx(result["interaction_effect_bps"]) == -5.0

    def test_symmetry(self):
        """With symmetric risks, contributions should be equal."""
        baseline, combined = 0.0, 40.0
        # Both individual risks are 20
        result = decompose_risk_shapley(baseline, 20.0, 20.0, combined)
        assert pytest.approx(result["transition_contribution_bps"]) == result["physical_contribution_bps"]

    def test_negative_baseline(self):
        """Handles negative CRP values (risk reduction scenarios)."""
        result = decompose_risk_shapley(-5.0, 0.0, -2.0, 8.0)
        total = result["transition_contribution_bps"] + result["physical_contribution_bps"]
        assert pytest.approx(total) == 8.0 - (-5.0)

    def test_return_keys(self):
        """Verify the function returns the expected keys."""
        result = decompose_risk_shapley(0, 10, 10, 20)
        assert set(result.keys()) == {
            "transition_contribution_bps",
            "physical_contribution_bps",
            "interaction_effect_bps",
        }

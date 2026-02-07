"""
Tests for Shapley-value risk attribution (src/risk/attribution.py).

Tests cover:
- Efficiency property (contributions sum to total)
- Single-risk scenarios
- Interaction effects (super/subadditive)
- Symmetry
- Edge cases
"""
import pytest
from src.risk.attribution import decompose_risk_shapley


class TestShapleyDecomposition:
    """Test Shapley value risk decomposition."""

    def test_efficiency_property(self):
        """Shapley values must sum to combined - baseline."""
        result = decompose_risk_shapley(
            baseline_crp=0,
            transition_only_crp=100,
            physical_only_crp=80,
            combined_crp=200,
        )
        total = result["transition_contribution_bps"] + result["physical_contribution_bps"]
        assert abs(total - 200) < 1e-9

    def test_transition_only_no_physical(self):
        """When only transition risk is present, it gets full attribution."""
        result = decompose_risk_shapley(
            baseline_crp=0,
            transition_only_crp=150,
            physical_only_crp=0,
            combined_crp=150,
        )
        assert result["transition_contribution_bps"] == 150
        assert result["physical_contribution_bps"] == 0
        assert result["interaction_effect_bps"] == 0

    def test_physical_only_no_transition(self):
        """When only physical risk is present, it gets full attribution."""
        result = decompose_risk_shapley(
            baseline_crp=0,
            transition_only_crp=0,
            physical_only_crp=200,
            combined_crp=200,
        )
        assert result["transition_contribution_bps"] == 0
        assert result["physical_contribution_bps"] == 200
        assert result["interaction_effect_bps"] == 0

    def test_superadditive_interaction(self):
        """When combined > sum of individual, interaction is positive."""
        result = decompose_risk_shapley(
            baseline_crp=0,
            transition_only_crp=100,
            physical_only_crp=80,
            combined_crp=220,
        )
        assert result["interaction_effect_bps"] > 0  # 220 - 100 - 80 = 40

    def test_subadditive_interaction(self):
        """When combined < sum of individual, interaction is negative."""
        result = decompose_risk_shapley(
            baseline_crp=0,
            transition_only_crp=100,
            physical_only_crp=80,
            combined_crp=150,
        )
        assert result["interaction_effect_bps"] < 0  # 150 - 100 - 80 = -30

    def test_additive_no_interaction(self):
        """When combined = sum of individual, no interaction."""
        result = decompose_risk_shapley(
            baseline_crp=0,
            transition_only_crp=100,
            physical_only_crp=80,
            combined_crp=180,
        )
        assert abs(result["interaction_effect_bps"]) < 1e-9

    def test_nonzero_baseline(self):
        """Test with non-zero baseline CRP."""
        result = decompose_risk_shapley(
            baseline_crp=50,
            transition_only_crp=150,
            physical_only_crp=130,
            combined_crp=250,
        )
        # Total attribution = 250 - 50 = 200
        total = result["transition_contribution_bps"] + result["physical_contribution_bps"]
        assert abs(total - 200) < 1e-9

    def test_symmetry_equal_risks(self):
        """Equal marginal contributions should give equal Shapley values."""
        result = decompose_risk_shapley(
            baseline_crp=0,
            transition_only_crp=100,
            physical_only_crp=100,
            combined_crp=200,
        )
        assert abs(result["transition_contribution_bps"] - result["physical_contribution_bps"]) < 1e-9

    def test_all_zero(self):
        """Zero risk everywhere."""
        result = decompose_risk_shapley(0, 0, 0, 0)
        assert result["transition_contribution_bps"] == 0
        assert result["physical_contribution_bps"] == 0
        assert result["interaction_effect_bps"] == 0

    def test_return_keys(self):
        result = decompose_risk_shapley(0, 100, 50, 160)
        assert "transition_contribution_bps" in result
        assert "physical_contribution_bps" in result
        assert "interaction_effect_bps" in result

    def test_negative_crp_values(self):
        """Shapley should handle negative CRP values."""
        result = decompose_risk_shapley(
            baseline_crp=-50,
            transition_only_crp=-30,
            physical_only_crp=-20,
            combined_crp=0,
        )
        total = result["transition_contribution_bps"] + result["physical_contribution_bps"]
        assert abs(total - 50) < 1e-9  # 0 - (-50) = 50

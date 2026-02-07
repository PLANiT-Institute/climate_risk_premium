"""
Tests for financing impact module (src/risk/financing.py).

Tests cover:
- Expected loss calculation
- Spread mapping from expected loss
- WACC calculation
- CRP (Climate Risk Premium) calculation
- Rating-based financing
- Counterfactual-based financing
"""
import pytest
from src.risk.financing import (
    FinancingImpact,
    calculate_expected_loss,
    map_expected_loss_to_spreads,
    calculate_financing_from_rating,
    calculate_financing_with_counterfactual,
)


class TestExpectedLoss:
    """Test expected loss percentage calculation."""

    def test_basic_calculation(self):
        el = calculate_expected_loss(1000e6, 700e6, 3200e6)
        expected = (1000e6 - 700e6) / 3200e6 * 100
        assert abs(el - expected) < 0.001

    def test_floor_at_zero(self):
        el = calculate_expected_loss(500e6, 600e6, 1000e6)
        assert el == 0.0

    def test_zero_capex(self):
        el = calculate_expected_loss(1000e6, 500e6, 0)
        assert el == 0.0

    def test_equal_npv(self):
        el = calculate_expected_loss(1000e6, 1000e6, 2000e6)
        assert el == 0.0

    def test_total_loss(self):
        el = calculate_expected_loss(1000e6, 0, 1000e6)
        assert abs(el - 100.0) < 0.001


class TestMapExpectedLossToSpreads:
    """Test spread mapping from expected loss."""

    @pytest.fixture
    def financing_params(self):
        return {
            "spread_slope_bps_per_pct": 50,
            "equity_slope_pct_per_pct": 0.8,
            "baseline_spread_bps": 150,
            "risk_free_rate": 0.03,
            "debt_fraction": 0.70,
            "equity_fraction": 0.30,
        }

    def test_debt_spread_increases_with_loss(self, financing_params):
        impact = map_expected_loss_to_spreads(10.0, 300e6, financing_params)
        # 150 + 10 * 50 = 650
        assert impact.debt_spread_bps == 650

    def test_equity_premium(self, financing_params):
        impact = map_expected_loss_to_spreads(10.0, 300e6, financing_params)
        # 10 * 0.8 = 8%
        assert impact.equity_premium_pct == 8.0

    def test_crp_positive(self, financing_params):
        impact = map_expected_loss_to_spreads(10.0, 300e6, financing_params)
        assert impact.crp_bps > 0

    def test_wacc_increased(self, financing_params):
        impact = map_expected_loss_to_spreads(10.0, 300e6, financing_params)
        assert impact.wacc_adjusted_pct > impact.wacc_baseline_pct

    def test_zero_loss_minimal_crp(self, financing_params):
        impact = map_expected_loss_to_spreads(0.0, 0.0, financing_params)
        assert abs(impact.crp_bps) < 0.01

    def test_rating_spread_override(self, financing_params):
        impact = map_expected_loss_to_spreads(
            10.0, 300e6, financing_params, rating_spread_bps=500
        )
        assert impact.debt_spread_bps == 500

    def test_to_dict(self, financing_params):
        impact = map_expected_loss_to_spreads(5.0, 100e6, financing_params)
        d = impact.to_dict()
        assert "crp_bps" in d
        assert "climate_risk_premium_bps" in d
        assert "wacc_baseline_pct" in d
        assert "wacc_adjusted_pct" in d

    def test_climate_risk_premium_alias(self, financing_params):
        impact = map_expected_loss_to_spreads(5.0, 100e6, financing_params)
        assert impact.climate_risk_premium_bps == impact.crp_bps


class TestCalculateFinancingFromRating:
    """Test rating-based financing calculation."""

    def test_basic_rating_financing(self):
        params = {
            "equity_slope_pct_per_pct": 0.8,
            "risk_free_rate": 0.03,
            "debt_fraction": 0.70,
            "equity_fraction": 0.30,
        }
        impact = calculate_financing_from_rating(
            rating_spread_bps=400,
            baseline_spread_bps=150,
            npv_loss=200e6,
            total_capex=2000e6,
            params=params,
        )
        assert impact.debt_spread_bps == 400
        assert impact.crp_bps > 0
        assert impact.wacc_adjusted_pct > impact.wacc_baseline_pct


class TestCalculateFinancingWithCounterfactual:
    """Test counterfactual-based CRP calculation."""

    def test_downgrade_produces_positive_crp(self):
        params = {
            "risk_free_rate": 0.03,
            "debt_fraction": 0.70,
            "equity_fraction": 0.30,
        }
        impact = calculate_financing_with_counterfactual(
            scenario_spread_bps=600,      # B-rated
            counterfactual_spread_bps=150, # A-rated
            npv_loss=500e6,
            total_capex=3000e6,
            params=params,
            scenario_notch=6,
            counterfactual_notch=3,
        )
        assert impact.crp_bps > 0

    def test_same_rating_zero_crp(self):
        params = {
            "risk_free_rate": 0.03,
            "debt_fraction": 0.70,
            "equity_fraction": 0.30,
        }
        impact = calculate_financing_with_counterfactual(
            scenario_spread_bps=150,
            counterfactual_spread_bps=150,
            npv_loss=0,
            total_capex=3000e6,
            params=params,
            scenario_notch=3,
            counterfactual_notch=3,
        )
        assert abs(impact.crp_bps) < 0.01

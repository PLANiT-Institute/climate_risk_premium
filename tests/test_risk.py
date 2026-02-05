"""
Unit tests for risk adjustment modules.
"""
import pytest
from src.scenarios import TransitionScenario, PhysicalScenario
from src.risk import apply_transition, apply_physical, calculate_expected_loss, map_expected_loss_to_spreads


@pytest.fixture
def plant_params():
    """Sample plant parameters."""
    return {
        'capacity_mw': 1000,
        'capacity_factor': 0.50,
        'operating_years': 30,
        'base_outage_rate': 0.03,
    }


def test_transition_adjustments(plant_params):
    """Test transition risk adjustments."""
    scenario = TransitionScenario(
        name="aggressive",
        dispatch_priority_penalty=0.20,
        retirement_years=25,
    )

    adj = apply_transition(plant_params, scenario)

    # Capacity factor should be reduced
    assert adj.capacity_factor == plant_params['capacity_factor'] - 0.20

    # Operating years should be capped
    assert adj.operating_years == 25


def test_physical_adjustments(plant_params):
    """Test physical risk adjustments."""
    scenario = PhysicalScenario(
        name="high_physical",
        wildfire_outage_rate=0.05,
        drought_derate=0.08,
        cooling_temp_penalty=0.05,
    )

    adj = apply_physical(plant_params, scenario)

    # Outage rate should increase
    base_outage = plant_params['base_outage_rate']
    assert adj.outage_rate == base_outage + 0.05

    # Derate and efficiency loss should be set
    assert adj.capacity_derate == 0.08
    assert adj.efficiency_loss == 0.05


def test_expected_loss_calculation():
    """Test expected loss percentage calculation."""
    baseline_npv = 1000e6  # $1B
    risk_npv = 700e6       # $700M
    total_capex = 3200e6   # $3.2B

    el_pct = calculate_expected_loss(baseline_npv, risk_npv, total_capex)

    # Expected loss = (1000 - 700) / 3200 * 100 = 9.375%
    assert abs(el_pct - 9.375) < 0.01


def test_expected_loss_floor():
    """Test that expected loss is floored at zero."""
    baseline_npv = 500e6
    risk_npv = 600e6  # Risk scenario better than baseline
    total_capex = 1000e6

    el_pct = calculate_expected_loss(baseline_npv, risk_npv, total_capex)

    # Should be floored at 0
    assert el_pct == 0.0


def test_financing_impact():
    """Test financing impact calculation."""
    expected_loss_pct = 10.0
    npv_loss = 300e6

    params = {
        'spread_slope_bps_per_pct': 50,
        'equity_slope_pct_per_pct': 0.8,
        'baseline_spread_bps': 150,
        'risk_free_rate': 0.03,
        'debt_fraction': 0.70,
        'equity_fraction': 0.30,
    }

    impact = map_expected_loss_to_spreads(expected_loss_pct, npv_loss, params)

    # Check debt spread increase
    expected_spread = 150 + (10 * 50)  # 650 bps
    assert impact.debt_spread_bps == expected_spread

    # Check equity premium
    expected_equity_premium = 10 * 0.8  # 8%
    assert impact.equity_premium_pct == expected_equity_premium

    # Check CRP is positive
    assert impact.crp_bps > 0

    # Check WACC increased
    assert impact.wacc_adjusted_pct > impact.wacc_baseline_pct

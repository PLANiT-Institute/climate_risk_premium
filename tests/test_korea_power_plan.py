"""
Unit tests for Korea Power Supply Plan integration.
"""
import pytest
from pathlib import Path
from src.scenarios.korea_power_plan import (
    KoreaPowerPlanScenario,
    load_korea_power_plan_scenarios,
    calculate_revenue_impact
)


def test_korea_power_plan_scenario_creation():
    """Test basic scenario creation."""
    scenario = KoreaPowerPlanScenario(
        name='test_scenario',
        cf_trajectory={2024: 0.60, 2030: 0.45, 2050: 0.05},
        early_retirement_year=2050,
        policy_reference='Test Policy',
        description='Test scenario'
    )

    assert scenario.name == 'test_scenario'
    assert scenario.cf_trajectory[2024] == 0.60
    assert scenario.early_retirement_year == 2050


def test_capacity_factor_exact_year():
    """Test CF retrieval for exact years in trajectory."""
    scenario = KoreaPowerPlanScenario(
        name='test',
        cf_trajectory={2024: 0.40, 2030: 0.35, 2040: 0.25},
        early_retirement_year=None,
        policy_reference='Test'
    )

    # Without baseline_cf specified, default is 0.50 (caps at this)
    assert scenario.get_capacity_factor(2024) == 0.40
    assert scenario.get_capacity_factor(2030) == 0.35
    assert scenario.get_capacity_factor(2040) == 0.25

    # With high baseline_cf, should return trajectory value
    assert scenario.get_capacity_factor(2024, baseline_cf=0.80) == 0.40
    assert scenario.get_capacity_factor(2030, baseline_cf=0.80) == 0.35


def test_capacity_factor_interpolation():
    """Test linear interpolation between years."""
    scenario = KoreaPowerPlanScenario(
        name='test',
        cf_trajectory={2024: 0.45, 2030: 0.35},
        early_retirement_year=None,
        policy_reference='Test'
    )

    # 2027 is midpoint between 2024 and 2030 (3 years out of 6)
    cf_2027 = scenario.get_capacity_factor(2027, baseline_cf=0.60)
    expected = 0.45 - (0.45 - 0.35) * (3 / 6)  # 3 years out of 6
    assert abs(cf_2027 - expected) < 0.001

    # 2028 is 2/3 of the way from 2024 to 2030 (4 years out of 6)
    cf_2028 = scenario.get_capacity_factor(2028, baseline_cf=0.60)
    expected = 0.45 - (0.45 - 0.35) * (4 / 6)
    assert abs(cf_2028 - expected) < 0.001


def test_capacity_factor_baseline_cap():
    """Test that CF never exceeds baseline."""
    scenario = KoreaPowerPlanScenario(
        name='test',
        cf_trajectory={2024: 0.70, 2030: 0.60},  # Higher than baseline
        early_retirement_year=None,
        policy_reference='Test'
    )

    # Should be capped at baseline_cf = 0.50 (default)
    assert scenario.get_capacity_factor(2024, baseline_cf=0.50) == 0.50
    assert scenario.get_capacity_factor(2030, baseline_cf=0.50) == 0.50


def test_early_retirement():
    """Test early retirement returns zero CF."""
    scenario = KoreaPowerPlanScenario(
        name='test',
        cf_trajectory={2024: 0.60, 2030: 0.45, 2040: 0.25},
        early_retirement_year=2045,
        policy_reference='Test'
    )

    # Before retirement
    assert scenario.get_capacity_factor(2040) == 0.25

    # At and after retirement
    assert scenario.get_capacity_factor(2045) == 0.0
    assert scenario.get_capacity_factor(2050) == 0.0


def test_operating_years_calculation():
    """Test operating years with early retirement."""
    scenario = KoreaPowerPlanScenario(
        name='test',
        cf_trajectory={2024: 0.60},
        early_retirement_year=2045,
        policy_reference='Test'
    )

    # Plant starts 2024, retires 2045 -> 21 years
    assert scenario.get_operating_years(start_year=2024, design_life=40) == 21

    # No early retirement -> full design life
    scenario_no_retirement = KoreaPowerPlanScenario(
        name='test',
        cf_trajectory={2024: 0.60},
        early_retirement_year=None,
        policy_reference='Test'
    )
    assert scenario_no_retirement.get_operating_years(start_year=2024, design_life=40) == 40


def test_load_korea_power_plan_scenarios():
    """Test loading scenarios from CSV file."""
    # This requires the actual CSV file to exist
    base_dir = Path(__file__).parent.parent
    csv_path = base_dir / 'data' / 'raw' / 'korea_power_plan.csv'

    if not csv_path.exists():
        pytest.skip("korea_power_plan.csv not found")

    scenarios = load_korea_power_plan_scenarios(str(csv_path))

    # Check that scenarios were loaded
    assert len(scenarios) > 0
    assert 'official_10th_plan' in scenarios
    assert 'netzero_2050' in scenarios

    # Check official scenario has expected years (CSV starts from 2025 in projection rows)
    official = scenarios['official_10th_plan']
    assert 2025 in official.cf_trajectory or 2024 in official.cf_trajectory  # Either is fine
    assert 2030 in official.cf_trajectory
    assert 2036 in official.cf_trajectory

    # Check NDC target year (2030) has CF around 45%
    cf_2030 = official.get_capacity_factor(2030, baseline_cf=0.70)
    assert 0.40 < cf_2030 < 0.50  # Should be around 45%


def test_revenue_impact_calculation():
    """Test revenue impact calculation."""
    scenario = KoreaPowerPlanScenario(
        name='test',
        cf_trajectory={2024: 0.50, 2030: 0.30},
        early_retirement_year=None,
        policy_reference='Test'
    )

    impact = calculate_revenue_impact(
        scenario=scenario,
        capacity_mw=2100,
        power_price=80,
        start_year=2024,
        end_year=2030,
        baseline_cf=0.50
    )

    # Should have cumulative revenue loss
    assert impact['cumulative_revenue_loss'] > 0
    assert impact['avg_annual_loss'] > 0
    assert impact['npv_loss'] > 0
    assert impact['npv_loss_pct'] > 0

    # NPV loss should be less than cumulative (due to discounting)
    assert impact['npv_loss'] < impact['cumulative_revenue_loss']


def test_revenue_impact_no_loss_baseline():
    """Test that baseline scenario has no revenue loss."""
    scenario = KoreaPowerPlanScenario(
        name='test',
        cf_trajectory={2024: 0.50, 2030: 0.50},  # Constant at baseline
        early_retirement_year=None,
        policy_reference='Test'
    )

    impact = calculate_revenue_impact(
        scenario=scenario,
        capacity_mw=2100,
        power_price=80,
        start_year=2024,
        end_year=2030,
        baseline_cf=0.50
    )

    # No loss if CF equals baseline
    assert abs(impact['cumulative_revenue_loss']) < 1.0
    assert abs(impact['npv_loss']) < 1.0
    assert abs(impact['npv_loss_pct']) < 0.1


def test_extrapolation_beyond_trajectory():
    """Test behavior for years beyond trajectory."""
    scenario = KoreaPowerPlanScenario(
        name='test',
        cf_trajectory={2024: 0.45, 2030: 0.35},
        early_retirement_year=2050,
        policy_reference='Test'
    )

    # Year before first data point - should use first available
    cf_2020 = scenario.get_capacity_factor(2020, baseline_cf=0.70)
    assert cf_2020 == 0.45  # Should use first available

    # Year after last data point but before retirement
    # Should extrapolate linear decline to retirement
    cf_2040 = scenario.get_capacity_factor(2040, baseline_cf=0.70)
    assert 0 < cf_2040 < 0.35  # Should be declining

    # After retirement
    cf_2051 = scenario.get_capacity_factor(2051)
    assert cf_2051 == 0.0

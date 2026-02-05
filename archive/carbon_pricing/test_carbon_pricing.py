"""
Unit tests for carbon pricing scenarios.
"""
import pytest
from pathlib import Path

from src.scenarios.carbon_pricing import (
    CarbonPricingScenario,
    create_korea_ets_current_policy,
    create_korea_ets_ndc_aligned,
    create_korea_net_zero_2050,
    create_delayed_action_scenario,
    create_high_ambition_scenario,
    create_no_policy_baseline,
    get_all_carbon_scenarios,
    get_carbon_scenario,
    load_carbon_scenarios_from_csv,
    compare_scenarios,
    calculate_cumulative_carbon_cost,
)
from src.scenarios.base import TransitionScenario


class TestCarbonPricingScenario:
    """Tests for CarbonPricingScenario class."""

    def test_basic_creation(self):
        """Test basic scenario creation."""
        scenario = CarbonPricingScenario(
            name="test",
            price_trajectory={2024: 10, 2030: 50, 2040: 100},
            description="Test scenario",
        )
        assert scenario.name == "test"
        assert scenario.price_trajectory[2024] == 10
        assert scenario.price_trajectory[2030] == 50

    def test_get_carbon_price_exact_year(self):
        """Test getting price for exact year in trajectory."""
        scenario = CarbonPricingScenario(
            name="test",
            price_trajectory={2024: 10, 2030: 50, 2040: 100},
        )
        assert scenario.get_carbon_price(2024) == 10
        assert scenario.get_carbon_price(2030) == 50
        assert scenario.get_carbon_price(2040) == 100

    def test_get_carbon_price_interpolation(self):
        """Test linear interpolation between years."""
        scenario = CarbonPricingScenario(
            name="test",
            price_trajectory={2024: 10, 2030: 70},
        )
        # 2027 is midpoint between 2024 and 2030
        price_2027 = scenario.get_carbon_price(2027)
        expected = 10 + (70 - 10) * (3 / 6)  # 40
        assert abs(price_2027 - expected) < 0.01

    def test_get_carbon_price_before_first_year(self):
        """Test price before first year returns first year value."""
        scenario = CarbonPricingScenario(
            name="test",
            price_trajectory={2025: 20, 2030: 50},
        )
        assert scenario.get_carbon_price(2020) == 20
        assert scenario.get_carbon_price(2024) == 20

    def test_get_carbon_price_extrapolation(self):
        """Test extrapolation beyond last year."""
        scenario = CarbonPricingScenario(
            name="test",
            price_trajectory={2040: 100, 2050: 200},
        )
        # Should extrapolate with growth rate
        price_2055 = scenario.get_carbon_price(2055)
        # Growth rate is (200/100)^(1/10) - 1 ≈ 7.18%/year
        assert price_2055 > 200  # Should be higher than 2050

    def test_trajectory_array(self):
        """Test getting trajectory as numpy array."""
        scenario = CarbonPricingScenario(
            name="test",
            price_trajectory={2024: 10, 2030: 50},
        )
        arr = scenario.get_trajectory_array(2024, 2026)
        assert len(arr) == 3
        assert arr[0] == 10  # 2024

    def test_to_dict(self):
        """Test export to dictionary."""
        scenario = CarbonPricingScenario(
            name="test",
            price_trajectory={2024: 10},
            description="Test",
            source="Unit test",
        )
        d = scenario.to_dict()
        assert d['name'] == "test"
        assert d['description'] == "Test"
        assert 2024 in d['price_trajectory']


class TestPredefinedScenarios:
    """Tests for predefined Korea ETS scenarios."""

    def test_korea_ets_current_policy(self):
        """Test Korea ETS current policy scenario (conservative baseline)."""
        scenario = create_korea_ets_current_policy()
        assert scenario.name == "korea_ets_current_policy"
        assert scenario.get_carbon_price(2024) == 8
        assert scenario.get_carbon_price(2030) == 20  # Conservative baseline
        assert scenario.get_carbon_price(2050) == 75  # Well below net-zero level
        # Should increase over time
        assert scenario.get_carbon_price(2030) > scenario.get_carbon_price(2024)
        assert scenario.get_carbon_price(2050) > scenario.get_carbon_price(2030)

    def test_korea_ets_ndc_aligned(self):
        """Test Korea ETS NDC-aligned scenario."""
        scenario = create_korea_ets_ndc_aligned()
        assert scenario.name == "korea_ets_ndc_aligned"
        # NDC scenario should have higher prices than current policy
        current = create_korea_ets_current_policy()
        assert scenario.get_carbon_price(2030) > current.get_carbon_price(2030)

    def test_korea_net_zero_2050(self):
        """Test Korea Net Zero 2050 scenario."""
        scenario = create_korea_net_zero_2050()
        assert scenario.name == "korea_net_zero_2050"
        # Net zero should have highest prices
        ndc = create_korea_ets_ndc_aligned()
        assert scenario.get_carbon_price(2050) > ndc.get_carbon_price(2050)

    def test_delayed_action_scenario(self):
        """Test delayed action scenario."""
        scenario = create_delayed_action_scenario()
        assert scenario.name == "delayed_action"
        # Delayed should have low prices early, high later
        current = create_korea_ets_current_policy()
        # Early years similar or lower
        assert scenario.get_carbon_price(2025) <= current.get_carbon_price(2025) + 1
        # Later years much higher due to catch-up
        assert scenario.get_carbon_price(2050) > current.get_carbon_price(2050)

    def test_high_ambition_scenario(self):
        """Test high ambition 1.5C scenario."""
        scenario = create_high_ambition_scenario()
        assert scenario.name == "high_ambition_1.5c"
        # Should have highest prices of all
        net_zero = create_korea_net_zero_2050()
        assert scenario.get_carbon_price(2030) > net_zero.get_carbon_price(2030)

    def test_no_policy_baseline(self):
        """Test no policy baseline."""
        scenario = create_no_policy_baseline()
        assert scenario.name == "no_policy_baseline"
        # All prices should be zero
        assert scenario.get_carbon_price(2024) == 0
        assert scenario.get_carbon_price(2030) == 0
        assert scenario.get_carbon_price(2050) == 0


class TestScenarioLoaders:
    """Tests for scenario loading functions."""

    def test_get_all_carbon_scenarios(self):
        """Test loading all predefined scenarios."""
        scenarios = get_all_carbon_scenarios()
        assert len(scenarios) >= 6
        assert "korea_ets_current" in scenarios
        assert "korea_ets_ndc" in scenarios
        assert "korea_net_zero" in scenarios
        assert "no_policy" in scenarios

    def test_get_carbon_scenario(self):
        """Test getting specific scenario by name."""
        scenario = get_carbon_scenario("korea_ets_current")
        assert scenario.name == "korea_ets_current_policy"

    def test_get_carbon_scenario_invalid(self):
        """Test error on invalid scenario name."""
        with pytest.raises(ValueError):
            get_carbon_scenario("nonexistent_scenario")

    def test_load_from_csv(self):
        """Test loading scenarios from CSV file."""
        base_dir = Path(__file__).parent.parent
        csv_path = base_dir / "data/raw/carbon_prices.csv"

        if not csv_path.exists():
            pytest.skip("carbon_prices.csv not found")

        scenarios = load_carbon_scenarios_from_csv(str(csv_path))
        assert len(scenarios) > 0
        assert "korea_ets_current" in scenarios


class TestComparisonAndAnalysis:
    """Tests for analysis utilities."""

    def test_compare_scenarios(self):
        """Test scenario comparison."""
        scenarios = {
            "current": create_korea_ets_current_policy(),
            "ndc": create_korea_ets_ndc_aligned(),
        }
        comparison = compare_scenarios(scenarios, years=[2024, 2030, 2050])

        assert "current" in comparison
        assert "ndc" in comparison
        assert 2024 in comparison["current"]
        assert 2030 in comparison["current"]
        assert 2050 in comparison["current"]

    def test_calculate_cumulative_carbon_cost(self):
        """Test cumulative carbon cost calculation."""
        scenario = create_korea_ets_current_policy()

        # Samcheok emissions: ~2100 MW * 8760 h * 0.85 CF * 0.95 tCO2/MWh
        annual_emissions = 2100 * 8760 * 0.85 * 0.95 / 1e6  # Million tonnes
        annual_emissions_tonnes = annual_emissions * 1e6

        result = calculate_cumulative_carbon_cost(
            scenario,
            annual_emissions_tonnes,
            start_year=2024,
            end_year=2030,
            discount_rate=0.08
        )

        assert result['cumulative_undiscounted'] > 0
        assert result['cumulative_npv'] > 0
        assert result['avg_annual_cost'] > 0
        # NPV should be less than undiscounted
        assert result['cumulative_npv'] < result['cumulative_undiscounted']


class TestTransitionScenarioIntegration:
    """Tests for TransitionScenario with carbon pricing integration."""

    def test_transition_scenario_with_carbon_scenario(self):
        """Test TransitionScenario linked to CarbonPricingScenario."""
        carbon = create_korea_ets_ndc_aligned()

        transition = TransitionScenario(
            name="test",
            dispatch_priority_penalty=0.10,
            retirement_years=30,
            carbon_price_2025=0,  # Will be overridden
            carbon_price_2030=0,
            carbon_price_2040=0,
            carbon_price_2050=0,
            carbon_scenario_name="korea_ets_ndc",
        )
        transition.set_carbon_scenario(carbon)

        # Should use carbon scenario prices, not zeros
        assert transition.get_carbon_price(2030) == carbon.get_carbon_price(2030)
        assert transition.get_carbon_price(2050) == carbon.get_carbon_price(2050)

    def test_transition_scenario_fallback_to_anchors(self):
        """Test TransitionScenario falls back to anchor points."""
        transition = TransitionScenario(
            name="test",
            dispatch_priority_penalty=0.10,
            retirement_years=30,
            carbon_price_2025=10,
            carbon_price_2030=50,
            carbon_price_2040=100,
            carbon_price_2050=200,
        )
        # No carbon scenario set, should use anchor interpolation
        assert transition.get_carbon_price(2025) == 10
        assert transition.get_carbon_price(2030) == 50
        # Test interpolation
        price_2027 = transition.get_carbon_price(2027)
        assert 10 < price_2027 < 50

    def test_carbon_price_trajectory(self):
        """Test getting full trajectory."""
        transition = TransitionScenario(
            name="test",
            dispatch_priority_penalty=0.10,
            retirement_years=30,
            carbon_price_2025=10,
            carbon_price_2030=50,
            carbon_price_2040=100,
            carbon_price_2050=200,
        )
        trajectory = transition.get_carbon_price_trajectory(2024, 2030)
        assert len(trajectory) == 7
        assert 2024 in trajectory
        assert 2030 in trajectory


class TestRealisticScenarioValues:
    """Tests to validate realistic carbon price ranges."""

    def test_korea_ets_2024_price_realistic(self):
        """Test 2024 price is realistic (~$8-15/tCO2 for K-ETS)."""
        scenario = create_korea_ets_current_policy()
        price_2024 = scenario.get_carbon_price(2024)
        assert 5 <= price_2024 <= 20  # K-ETS typically $8-15

    def test_korea_ets_2030_price_realistic(self):
        """Test 2030 price is realistic for NDC alignment."""
        ndc = create_korea_ets_ndc_aligned()
        price_2030 = ndc.get_carbon_price(2030)
        # IEA suggests $50-100 for NDC alignment in 2030
        assert 50 <= price_2030 <= 150

    def test_net_zero_2050_price_realistic(self):
        """Test 2050 price is realistic for net zero."""
        net_zero = create_korea_net_zero_2050()
        price_2050 = net_zero.get_carbon_price(2050)
        # IEA NZE suggests $250-450 by 2050
        assert 200 <= price_2050 <= 600

    def test_scenario_ordering(self):
        """Test scenarios are ordered by ambition level."""
        no_policy = create_no_policy_baseline()
        current = create_korea_ets_current_policy()
        ndc = create_korea_ets_ndc_aligned()
        net_zero = create_korea_net_zero_2050()
        high = create_high_ambition_scenario()

        # At 2050, should be: no_policy < current < ndc < net_zero < high
        assert no_policy.get_carbon_price(2050) < current.get_carbon_price(2050)
        assert current.get_carbon_price(2050) < ndc.get_carbon_price(2050)
        assert ndc.get_carbon_price(2050) < net_zero.get_carbon_price(2050)
        assert net_zero.get_carbon_price(2050) < high.get_carbon_price(2050)

"""
Tests for scenario definitions and market scenario module.

Tests cover:
- TransitionScenario creation
- PhysicalScenario creation
- ScenarioSet creation
- MarketScenario demand and price calculations
"""
import pytest
from src.scenarios.base import TransitionScenario, PhysicalScenario, ScenarioSet
from src.scenarios.market import MarketScenario


class TestTransitionScenario:
    """Test TransitionScenario dataclass."""

    def test_creation(self):
        s = TransitionScenario("aggressive", 0.20, 25)
        assert s.name == "aggressive"
        assert s.dispatch_priority_penalty == 0.20
        assert s.retirement_years == 25

    def test_zero_penalty(self):
        s = TransitionScenario("baseline", 0.0, 40)
        assert s.dispatch_priority_penalty == 0.0


class TestPhysicalScenario:
    """Test PhysicalScenario dataclass."""

    def test_creation(self):
        s = PhysicalScenario("high", 0.05, 0.08, 0.05)
        assert s.name == "high"
        assert s.wildfire_outage_rate == 0.05
        assert s.drought_derate == 0.08
        assert s.cooling_temp_penalty == 0.05

    def test_default_water_availability(self):
        s = PhysicalScenario("baseline", 0.0, 0.0, 0.0)
        assert s.water_availability_pct == 100.0

    def test_water_availability_custom(self):
        s = PhysicalScenario("drought", 0.0, 0.0, 0.0, water_availability_pct=70.0)
        assert s.water_availability_pct == 70.0


class TestScenarioSet:
    """Test ScenarioSet dataclass."""

    def test_creation_with_both(self):
        t = TransitionScenario("t", 0.1, 30)
        p = PhysicalScenario("p", 0.02, 0.05, 0.03)
        ss = ScenarioSet(baseline_years=40, transition=t, physical=p)
        assert ss.baseline_years == 40
        assert ss.transition is not None
        assert ss.physical is not None

    def test_creation_with_none(self):
        ss = ScenarioSet(baseline_years=40, transition=None, physical=None)
        assert ss.transition is None
        assert ss.physical is None


class TestMarketScenario:
    """Test MarketScenario demand/price calculations."""

    def test_default_values(self):
        m = MarketScenario("base")
        assert m.demand_growth_pct == 1.0
        assert m.price_sensitivity == 0.5
        assert m.base_power_price == 80.0

    def test_demand_factor_base_year(self):
        m = MarketScenario("base", demand_growth_pct=2.0)
        factor = m.get_demand_factor(2025, 2025)
        assert factor == 1.0

    def test_demand_factor_future_year(self):
        m = MarketScenario("growth", demand_growth_pct=5.0)
        factor = m.get_demand_factor(2026, 2025)
        assert abs(factor - 1.05) < 1e-9

    def test_demand_factor_compounds(self):
        m = MarketScenario("growth", demand_growth_pct=10.0)
        factor = m.get_demand_factor(2027, 2025)
        expected = 1.10 ** 2
        assert abs(factor - expected) < 1e-9

    def test_demand_factor_negative_growth(self):
        m = MarketScenario("decline", demand_growth_pct=-5.0)
        factor = m.get_demand_factor(2026, 2025)
        assert factor < 1.0

    def test_power_price_at_base_year(self):
        m = MarketScenario("base", base_power_price=100.0)
        price = m.get_power_price(2025, 2025)
        assert price == 100.0

    def test_power_price_increases_with_demand(self):
        m = MarketScenario("growth", demand_growth_pct=5.0, price_sensitivity=1.0, base_power_price=100.0)
        price = m.get_power_price(2026, 2025)
        assert price > 100.0

    def test_power_price_sensitivity(self):
        m_low = MarketScenario("low", demand_growth_pct=5.0, price_sensitivity=0.5, base_power_price=100.0)
        m_high = MarketScenario("high", demand_growth_pct=5.0, price_sensitivity=2.0, base_power_price=100.0)

        p_low = m_low.get_power_price(2030, 2025)
        p_high = m_high.get_power_price(2030, 2025)

        assert p_high > p_low

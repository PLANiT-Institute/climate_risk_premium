"""
Comprehensive tests for the cash flow engine (src/financials/cashflow.py).

Tests cover:
- Revenue calculation with capacity factors
- Fuel cost calculation with heat rates
- Physical risk adjustments (outages, derates, efficiency loss)
- Financial calculations (depreciation, debt service, tax, net income)
- Free cash flow computation
- Year-by-year physical and transition adjustments
- Market scenario integration
- Edge cases (zero values, extreme inputs)
"""
import pytest
import numpy as np
from src.financials.cashflow import (
    compute_cashflows_timeseries,
    compute_cashflows,
    CashFlowTimeSeries,
    CashFlowResult,
)
from src.risk import TransitionAdjustments, PhysicalAdjustments
from src.risk.transition import YearlyTransitionAdjustments
from src.risk.physical import YearlyPhysicalAdjustments
from src.scenarios import TransitionScenario, MarketScenario


@pytest.fixture
def base_plant_params():
    """Standard plant parameters for testing."""
    return {
        "capacity_mw": 1000,
        "capacity_factor": 0.5,
        "power_price_per_mwh": 100,
        "heat_rate_mmbtu_mwh": 9.5,
        "fuel_price_per_mmbtu": 3.0,
        "fixed_opex_per_kw_year": 35.0,
        "variable_opex_per_mwh": 4.5,
        "total_capex_million": 2000,
        "useful_life": 30,
        "tax_rate": 0.25,
        "debt_fraction": 0.70,
        "debt_interest_rate": 0.05,
        "debt_tenor_years": 15,
        "operating_years": 30,
    }


@pytest.fixture
def zero_cost_plant():
    """Plant with zero opex/fuel for isolated testing."""
    return {
        "capacity_mw": 1000,
        "capacity_factor": 0.5,
        "power_price_per_mwh": 100,
        "heat_rate_mmbtu_mwh": 9.5,
        "fuel_price_per_mmbtu": 0,
        "fixed_opex_per_kw_year": 0,
        "variable_opex_per_mwh": 0,
        "total_capex_million": 1000,
        "useful_life": 20,
        "tax_rate": 0.25,
        "debt_fraction": 0.5,
        "debt_interest_rate": 0.05,
        "debt_tenor_years": 10,
    }


@pytest.fixture
def baseline_scenario():
    """No-risk baseline scenario."""
    trans = TransitionScenario("Baseline", 0.0, 40)
    trans_adj = TransitionAdjustments(0.5, 30)
    phys_adj = PhysicalAdjustments(0.0, 0.0)
    return trans, trans_adj, phys_adj


class TestRevenueCalculation:
    """Test revenue computation in cash flow engine."""

    def test_revenue_with_no_outages(self, zero_cost_plant, baseline_scenario):
        trans, trans_adj, phys_adj = baseline_scenario
        cf = compute_cashflows_timeseries(zero_cost_plant, trans, trans_adj, phys_adj)

        # Revenue = 1000 MW * 8760 h * 0.5 CF * $100/MWh = $438M/yr
        expected_revenue = 1000 * 8760 * 0.5 * 100
        assert np.allclose(cf.revenue, expected_revenue)

    def test_revenue_reduced_by_outages(self, zero_cost_plant, baseline_scenario):
        trans, trans_adj, _ = baseline_scenario
        phys_adj = PhysicalAdjustments(0.10, 0.0)
        cf = compute_cashflows_timeseries(zero_cost_plant, trans, trans_adj, phys_adj)

        # Revenue should be 90% of full (10% outage)
        full_revenue = 1000 * 8760 * 0.5 * 100
        expected_revenue = full_revenue * 0.90
        assert np.allclose(cf.revenue, expected_revenue)

    def test_capacity_factor_array(self, zero_cost_plant, baseline_scenario):
        trans, trans_adj, phys_adj = baseline_scenario
        cf = compute_cashflows_timeseries(zero_cost_plant, trans, trans_adj, phys_adj)

        assert len(cf.capacity_factor) == 30
        assert np.allclose(cf.capacity_factor, 0.5)

    def test_lost_revenue_from_outages_tracking(self, zero_cost_plant, baseline_scenario):
        trans, trans_adj, _ = baseline_scenario
        phys_adj = PhysicalAdjustments(0.10, 0.0)
        cf = compute_cashflows_timeseries(zero_cost_plant, trans, trans_adj, phys_adj)

        # Lost revenue = potential_mwh * outage_rate * price
        potential_mwh = 1000 * 8760 * 0.5
        expected_lost = potential_mwh * 0.10 * 100
        assert np.allclose(cf.lost_revenue_from_outages, expected_lost)


class TestCostCalculation:
    """Test cost computation."""

    def test_fuel_costs(self, base_plant_params, baseline_scenario):
        trans, trans_adj, phys_adj = baseline_scenario
        cf = compute_cashflows_timeseries(base_plant_params, trans, trans_adj, phys_adj)

        actual_mwh = 1000 * 8760 * 0.5  # no outages
        expected_fuel = actual_mwh * 9.5 * 3.0
        assert np.allclose(cf.fuel_costs, expected_fuel)

    def test_fuel_costs_increase_with_efficiency_loss(self, base_plant_params, baseline_scenario):
        trans, trans_adj, _ = baseline_scenario
        phys_adj_no_loss = PhysicalAdjustments(0.0, 0.0)
        phys_adj_with_loss = PhysicalAdjustments(0.0, 0.10)

        cf_no_loss = compute_cashflows_timeseries(base_plant_params, trans, trans_adj, phys_adj_no_loss)
        cf_with_loss = compute_cashflows_timeseries(base_plant_params, trans, trans_adj, phys_adj_with_loss)

        # 10% efficiency loss means 10% more fuel per MWh
        assert np.all(cf_with_loss.fuel_costs > cf_no_loss.fuel_costs)
        ratio = cf_with_loss.fuel_costs[0] / cf_no_loss.fuel_costs[0]
        assert np.isclose(ratio, 1.10, rtol=1e-6)

    def test_fixed_opex_constant(self, base_plant_params, baseline_scenario):
        trans, trans_adj, phys_adj = baseline_scenario
        cf = compute_cashflows_timeseries(base_plant_params, trans, trans_adj, phys_adj)

        expected_fixed = 1000 * 1000 * 35.0  # capacity_mw * 1000 kW/MW * $/kW-yr
        assert np.allclose(cf.fixed_opex, expected_fixed)

    def test_variable_opex(self, base_plant_params, baseline_scenario):
        trans, trans_adj, phys_adj = baseline_scenario
        cf = compute_cashflows_timeseries(base_plant_params, trans, trans_adj, phys_adj)

        actual_mwh = 1000 * 8760 * 0.5
        expected_var = actual_mwh * 4.5
        assert np.allclose(cf.variable_opex, expected_var)

    def test_total_costs_sum_correctly(self, base_plant_params, baseline_scenario):
        trans, trans_adj, phys_adj = baseline_scenario
        cf = compute_cashflows_timeseries(base_plant_params, trans, trans_adj, phys_adj)

        expected_total = cf.fuel_costs + cf.variable_opex + cf.fixed_opex + cf.carbon_costs
        assert np.allclose(cf.total_costs, expected_total)


class TestFinancialCalculations:
    """Test depreciation, debt, tax, and FCF."""

    def test_depreciation_straight_line(self, zero_cost_plant, baseline_scenario):
        trans, trans_adj, phys_adj = baseline_scenario
        cf = compute_cashflows_timeseries(zero_cost_plant, trans, trans_adj, phys_adj)

        expected_depr = 1000e6 / 20  # $50M/yr
        assert np.allclose(cf.depreciation, expected_depr)

    def test_ebitda_equals_revenue_minus_costs(self, base_plant_params, baseline_scenario):
        trans, trans_adj, phys_adj = baseline_scenario
        cf = compute_cashflows_timeseries(base_plant_params, trans, trans_adj, phys_adj)

        expected_ebitda = cf.revenue - cf.total_costs
        assert np.allclose(cf.ebitda, expected_ebitda)

    def test_ebit_equals_ebitda_minus_depreciation(self, base_plant_params, baseline_scenario):
        trans, trans_adj, phys_adj = baseline_scenario
        cf = compute_cashflows_timeseries(base_plant_params, trans, trans_adj, phys_adj)

        expected_ebit = cf.ebitda - cf.depreciation
        assert np.allclose(cf.ebit, expected_ebit)

    def test_interest_expense_decreases_over_time(self, zero_cost_plant, baseline_scenario):
        trans, trans_adj, phys_adj = baseline_scenario
        cf = compute_cashflows_timeseries(zero_cost_plant, trans, trans_adj, phys_adj)

        # Amortizing loan: interest should decrease
        debt_years = cf.interest_expense[:10]  # 10-year tenor
        for i in range(1, len(debt_years)):
            if debt_years[i] > 0:
                assert debt_years[i] <= debt_years[i - 1]

        # After tenor, interest should be zero
        assert np.allclose(cf.interest_expense[10:], 0.0)

    def test_tax_non_negative(self, base_plant_params, baseline_scenario):
        trans, trans_adj, phys_adj = baseline_scenario
        cf = compute_cashflows_timeseries(base_plant_params, trans, trans_adj, phys_adj)

        assert np.all(cf.tax_expense >= 0)

    def test_net_income_calculation(self, zero_cost_plant, baseline_scenario):
        trans, trans_adj, phys_adj = baseline_scenario
        cf = compute_cashflows_timeseries(zero_cost_plant, trans, trans_adj, phys_adj)

        expected_net = cf.ebit - cf.interest_expense - cf.tax_expense
        assert np.allclose(cf.net_income, expected_net)

    def test_free_cash_flow_nopat_based(self, base_plant_params, baseline_scenario):
        trans, trans_adj, phys_adj = baseline_scenario
        cf = compute_cashflows_timeseries(base_plant_params, trans, trans_adj, phys_adj)

        # FCF = NOPAT + Depreciation - Capex
        nopat = cf.ebit * (1 - 0.25)
        expected_fcf = nopat + cf.depreciation - cf.capex
        assert np.allclose(cf.free_cash_flow, expected_fcf)


class TestYearlyAdjustments:
    """Test year-by-year physical and transition adjustments."""

    def test_yearly_physical_adjustments(self, zero_cost_plant):
        trans = TransitionScenario("Test", 0, 40)
        trans_adj = TransitionAdjustments(0.5, 5)
        phys_adj = PhysicalAdjustments(0, 0)

        years = np.arange(2025, 2030)
        outage_rates = np.array([0.01, 0.02, 0.03, 0.04, 0.05])

        yearly = YearlyPhysicalAdjustments(
            years=years,
            outage_rates=outage_rates,
            efficiency_losses=np.zeros(5),
            scenario_name="test",
        )

        cf = compute_cashflows_timeseries(
            zero_cost_plant, trans, trans_adj, phys_adj,
            start_year=2025, yearly_physical_adj=yearly,
        )

        # Revenue should decrease each year as outage rate grows
        for i in range(1, len(cf.revenue)):
            assert cf.revenue[i] < cf.revenue[i - 1]

    def test_yearly_transition_adjustments(self, zero_cost_plant):
        trans = TransitionScenario("Test", 0, 40)
        trans_adj = TransitionAdjustments(0.5, 5)
        phys_adj = PhysicalAdjustments(0, 0)

        years = np.arange(2025, 2030)
        cfs = np.array([0.80, 0.70, 0.60, 0.50, 0.40])
        carbon_costs = np.array([5.0, 10.0, 15.0, 20.0, 25.0])

        yearly_trans = YearlyTransitionAdjustments(
            years=years,
            capacity_factors=cfs,
            carbon_costs_per_mwh=carbon_costs,
            scenario_name="declining_cf",
        )

        cf = compute_cashflows_timeseries(
            zero_cost_plant, trans, trans_adj, phys_adj,
            start_year=2025, yearly_transition_adj=yearly_trans,
        )

        # Revenue should decrease as CF declines
        for i in range(1, len(cf.revenue)):
            assert cf.revenue[i] < cf.revenue[i - 1]

        # Carbon costs should be non-zero
        assert np.all(cf.carbon_costs > 0)


class TestMarketScenario:
    """Test market scenario integration."""

    def test_market_scenario_affects_price(self, zero_cost_plant, baseline_scenario):
        trans, trans_adj, phys_adj = baseline_scenario
        market = MarketScenario("growing_demand", demand_growth_pct=5.0, price_sensitivity=1.0, base_power_price=100.0)

        cf = compute_cashflows_timeseries(
            zero_cost_plant, trans, trans_adj, phys_adj,
            market_scenario=market,
        )

        # Prices should increase over time with 5% demand growth
        for i in range(1, len(cf.revenue)):
            assert cf.revenue[i] > cf.revenue[i - 1]


class TestCashFlowTimeSeriesDataclass:
    """Test CashFlowTimeSeries dataclass methods."""

    def test_to_dict(self, zero_cost_plant, baseline_scenario):
        trans, trans_adj, phys_adj = baseline_scenario
        cf = compute_cashflows_timeseries(zero_cost_plant, trans, trans_adj, phys_adj)

        d = cf.to_dict()
        assert "year" in d
        assert "revenue" in d
        assert "free_cash_flow" in d
        assert "carbon_costs" in d
        assert len(d["year"]) == 30
        assert all(isinstance(v, list) for v in d.values())

    def test_carbon_costs_default_to_zero(self, zero_cost_plant, baseline_scenario):
        trans, trans_adj, phys_adj = baseline_scenario
        cf = compute_cashflows_timeseries(zero_cost_plant, trans, trans_adj, phys_adj)

        assert np.allclose(cf.carbon_costs, 0.0)


class TestLegacyCashflows:
    """Test the legacy single-period cash flow function."""

    def test_compute_cashflows_returns_result(self):
        plant = {"capacity_mw": 1000, "power_price_per_mwh": 80}
        trans = TransitionAdjustments(0.5, 30)
        phys = PhysicalAdjustments(0.02, 0.0)

        result = compute_cashflows(plant, trans, phys)
        assert isinstance(result, CashFlowResult)
        assert result.annual_revenue > 0
        assert result.ebitda > 0
        assert "Legacy" in result.notes

    def test_legacy_outage_reduces_revenue(self):
        plant = {"capacity_mw": 1000, "power_price_per_mwh": 80}
        trans = TransitionAdjustments(0.5, 30)

        phys_no_outage = PhysicalAdjustments(0.0, 0.0)
        phys_with_outage = PhysicalAdjustments(0.10, 0.0)

        r1 = compute_cashflows(plant, trans, phys_no_outage)
        r2 = compute_cashflows(plant, trans, phys_with_outage)

        assert r2.ebitda < r1.ebitda

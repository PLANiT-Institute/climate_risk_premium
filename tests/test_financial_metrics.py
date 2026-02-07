"""
Comprehensive tests for financial metrics (src/financials/metrics.py).

Tests cover:
- NPV calculation
- IRR calculation
- DSCR (Debt Service Coverage Ratio)
- LLCR (Loan Life Coverage Ratio)
- Payback period
- Debt service schedule
- Edge cases
"""
import pytest
import numpy as np
import numpy_financial as npf
from src.financials.metrics import (
    calculate_metrics,
    calculate_debt_service,
    FinancialMetrics,
    DebtStructure,
)
from src.financials.cashflow import compute_cashflows_timeseries
from src.risk import TransitionAdjustments, PhysicalAdjustments
from src.scenarios import TransitionScenario


@pytest.fixture
def standard_plant():
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
        "debt_fraction": 0.70,
        "debt_interest_rate": 0.05,
        "debt_tenor_years": 15,
        "discount_rate": 0.08,
        "operating_years": 20,
    }


class TestDebtService:
    """Test debt service schedule calculation."""

    def test_annual_payment_matches_npf(self):
        ds = calculate_debt_service(1000e6, 0.70, 0.05, 15)
        expected = -npf.pmt(0.05, 15, 700e6)
        assert np.isclose(ds.annual_debt_service, expected, rtol=1e-6)

    def test_total_principal_equals_debt(self):
        ds = calculate_debt_service(2000e6, 0.60, 0.04, 20)
        assert np.isclose(np.sum(ds.principal_schedule), 1200e6, rtol=1e-6)

    def test_interest_decreases_over_time(self):
        ds = calculate_debt_service(1000e6, 0.70, 0.05, 15)
        for i in range(1, len(ds.interest_schedule)):
            assert ds.interest_schedule[i] < ds.interest_schedule[i - 1]

    def test_principal_increases_over_time(self):
        ds = calculate_debt_service(1000e6, 0.70, 0.05, 15)
        for i in range(1, len(ds.principal_schedule)):
            assert ds.principal_schedule[i] > ds.principal_schedule[i - 1]

    def test_interest_plus_principal_equals_payment(self):
        ds = calculate_debt_service(500e6, 0.80, 0.06, 10)
        total_each_period = ds.interest_schedule + ds.principal_schedule
        assert np.allclose(total_each_period, ds.annual_debt_service, rtol=1e-6)

    def test_debt_structure_fields(self):
        ds = calculate_debt_service(1000e6, 0.50, 0.05, 10)
        assert ds.debt_amount == 500e6
        assert ds.interest_rate == 0.05
        assert ds.tenor_years == 10
        assert len(ds.principal_schedule) == 10
        assert len(ds.interest_schedule) == 10


class TestFinancialMetrics:
    """Test NPV, IRR, DSCR, LLCR calculation."""

    def test_npv_positive_for_profitable_plant(self, standard_plant):
        trans = TransitionScenario("Test", 0, 40)
        trans_adj = TransitionAdjustments(0.5, 20)
        phys_adj = PhysicalAdjustments(0, 0, 0, 1.0)

        cf = compute_cashflows_timeseries(standard_plant, trans, trans_adj, phys_adj)
        metrics = calculate_metrics(cf, standard_plant)

        assert metrics.npv > 0

    def test_irr_positive_for_profitable_plant(self, standard_plant):
        trans = TransitionScenario("Test", 0, 40)
        trans_adj = TransitionAdjustments(0.5, 20)
        phys_adj = PhysicalAdjustments(0, 0, 0, 1.0)

        cf = compute_cashflows_timeseries(standard_plant, trans, trans_adj, phys_adj)
        metrics = calculate_metrics(cf, standard_plant)

        assert metrics.irr > 0

    def test_dscr_above_one_for_healthy_plant(self, standard_plant):
        trans = TransitionScenario("Test", 0, 40)
        trans_adj = TransitionAdjustments(0.5, 20)
        phys_adj = PhysicalAdjustments(0, 0, 0, 1.0)

        cf = compute_cashflows_timeseries(standard_plant, trans, trans_adj, phys_adj)
        metrics = calculate_metrics(cf, standard_plant)

        assert metrics.avg_dscr > 1.0
        assert metrics.min_dscr > 0.0

    def test_payback_period_exists(self, standard_plant):
        trans = TransitionScenario("Test", 0, 40)
        trans_adj = TransitionAdjustments(0.5, 20)
        phys_adj = PhysicalAdjustments(0, 0, 0, 1.0)

        cf = compute_cashflows_timeseries(standard_plant, trans, trans_adj, phys_adj)
        metrics = calculate_metrics(cf, standard_plant)

        assert metrics.payback_years is not None
        assert metrics.payback_years > 0
        assert metrics.payback_years <= 20

    def test_metrics_to_dict(self, standard_plant):
        trans = TransitionScenario("Test", 0, 40)
        trans_adj = TransitionAdjustments(0.5, 20)
        phys_adj = PhysicalAdjustments(0, 0, 0, 1.0)

        cf = compute_cashflows_timeseries(standard_plant, trans, trans_adj, phys_adj)
        metrics = calculate_metrics(cf, standard_plant)

        d = metrics.to_dict()
        assert "npv_million" in d
        assert "irr_pct" in d
        assert "avg_dscr" in d
        assert "min_dscr" in d
        assert "llcr" in d
        assert "payback_years" in d

    def test_llcr_positive_for_healthy_plant(self, standard_plant):
        trans = TransitionScenario("Test", 0, 40)
        trans_adj = TransitionAdjustments(0.5, 20)
        phys_adj = PhysicalAdjustments(0, 0, 0, 1.0)

        cf = compute_cashflows_timeseries(standard_plant, trans, trans_adj, phys_adj)
        metrics = calculate_metrics(cf, standard_plant)

        assert metrics.llcr > 0


class TestMetricsWithRisk:
    """Test how risk affects financial metrics."""

    def test_physical_risk_reduces_npv(self, standard_plant):
        trans = TransitionScenario("Test", 0, 40)
        trans_adj = TransitionAdjustments(0.5, 20)

        phys_safe = PhysicalAdjustments(0, 0, 0, 1.0)
        phys_risky = PhysicalAdjustments(0.10, 0.05, 0.05, 0.9)

        cf_safe = compute_cashflows_timeseries(standard_plant, trans, trans_adj, phys_safe)
        cf_risky = compute_cashflows_timeseries(standard_plant, trans, trans_adj, phys_risky)

        m_safe = calculate_metrics(cf_safe, standard_plant)
        m_risky = calculate_metrics(cf_risky, standard_plant)

        assert m_risky.npv < m_safe.npv

    def test_shorter_life_reduces_npv(self, standard_plant):
        trans = TransitionScenario("Test", 0, 40)
        phys = PhysicalAdjustments(0, 0, 0, 1.0)

        long_adj = TransitionAdjustments(0.5, 20)
        short_adj = TransitionAdjustments(0.5, 10)

        cf_long = compute_cashflows_timeseries(standard_plant, trans, long_adj, phys)
        cf_short = compute_cashflows_timeseries(standard_plant, trans, short_adj, phys)

        m_long = calculate_metrics(cf_long, standard_plant)
        m_short = calculate_metrics(cf_short, standard_plant)

        assert m_short.npv < m_long.npv

"""
Unit tests for financial logic.
"""
import pytest
import numpy as np
from src.financials.cashflow import compute_cashflows_timeseries, CashFlowTimeSeries
from src.financials.metrics import calculate_metrics, calculate_debt_service
from src.risk import TransitionAdjustments, PhysicalAdjustments
from src.scenarios import TransitionScenario

@pytest.fixture
def sample_plant_params():
    return {
        "capacity_mw": 1000,
        "capacity_factor": 0.5,
        "total_capex_million": 1000, # $1B
        "useful_life": 20,
        "tax_rate": 0.25,
        "debt_fraction": 0.5, # $500M Debt
        "debt_interest_rate": 0.05,
        "debt_tenor_years": 10,
        "power_price_per_mwh": 100,
        "fixed_opex_per_kw_year": 0, # Simplify
        "variable_opex_per_mwh": 0, # Simplify
        "fuel_price_per_mmbtu": 0, # Simplify
    }

@pytest.fixture
def dummy_scenarios():
    trans = TransitionScenario("Test", 0, 40)
    trans_adj = TransitionAdjustments(0.5, 40)
    phys_adj = PhysicalAdjustments(0, 0, 0, 1.0)
    return trans, trans_adj, phys_adj

def test_depreciation(sample_plant_params, dummy_scenarios):
    trans, trans_adj, phys_adj = dummy_scenarios
    cf = compute_cashflows_timeseries(sample_plant_params, trans, trans_adj, phys_adj)
    
    # Capex = 1B, Life = 20y -> Depr = 50M/yr
    expected_depr = 1000e6 / 20
    assert np.allclose(cf.depreciation, expected_depr)

def test_debt_service(sample_plant_params):
    # Debt = 500M, 5%, 10y
    ds = calculate_debt_service(1000e6, 0.5, 0.05, 10)
    
    # Annual Payment (PMT)
    # 500M * 0.05 / (1 - (1.05)^-10) ~= 64.75M
    expected_pmt = 64.752e6
    assert np.isclose(ds.annual_debt_service, expected_pmt, rtol=1e-3)
    
    # Total Principal Repaid should be 500M
    assert np.isclose(np.sum(ds.principal_schedule), 500e6)

def test_tax_calculation(sample_plant_params, dummy_scenarios):
    trans, trans_adj, phys_adj = dummy_scenarios
    cf = compute_cashflows_timeseries(sample_plant_params, trans, trans_adj, phys_adj)
    
    # Revenue = 1000MW * 8760 * 0.5 * 100 = 438M
    # Costs = 0
    # EBITDA = 438M
    # Depr = 50M
    # EBIT = 388M
    # Interest (Year 1) = 500M * 0.05 = 25M
    # EBT = 363M
    # Tax = 363M * 0.25 = 90.75M
    
    assert np.isclose(cf.ebitda[0], 438e6)
    assert np.isclose(cf.ebit[0], 388e6)
    assert np.isclose(cf.interest_expense[0], 25e6)
    assert np.isclose(cf.tax_expense[0], 90.75e6)
    
    # Net Income = 363M - 90.75M = 272.25M
    assert np.isclose(cf.net_income[0], 272.25e6)

def test_metrics_integration(sample_plant_params, dummy_scenarios):
    trans, trans_adj, phys_adj = dummy_scenarios
    cf = compute_cashflows_timeseries(sample_plant_params, trans, trans_adj, phys_adj)
    metrics = calculate_metrics(cf, sample_plant_params)
    
    # DSCR = (EBITDA - Tax) / Debt Service
    # EBITDA = 438M, Tax = 90.75M -> CFADS = 347.25M
    # DS = 64.75M
    # DSCR = 5.36
    
    assert metrics.avg_dscr > 5.0

"""
Shared pytest fixtures for the Climate Risk Premium test suite.

Provides reusable plant parameters, scenario objects, and helper factories
so individual test files can focus on testing specific behavior.
"""
from pathlib import Path
import sys

import pytest
import numpy as np

# Ensure `src` imports resolve when running plain `pytest` from repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.risk import TransitionAdjustments, PhysicalAdjustments
from src.risk.transition import YearlyTransitionAdjustments
from src.risk.physical import YearlyPhysicalAdjustments
from src.scenarios import TransitionScenario, MarketScenario


# ---------------------------------------------------------------------------
# Plant parameter fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def samcheok_plant_params():
    """Samcheok Blue Power Plant (2100 MW supercritical coal) parameters."""
    return {
        "capacity_mw": 2100,
        "capacity_factor": 0.85,
        "power_price_per_mwh": 80,
        "heat_rate_mmbtu_mwh": 8.8,
        "fuel_price_per_mmbtu": 3.2,
        "fixed_opex_per_kw_year": 35,
        "variable_opex_per_mwh": 4.5,
        "total_capex_million": 3550,
        "useful_life": 40,
        "tax_rate": 0.25,
        "debt_fraction": 0.70,
        "debt_interest_rate": 0.061,
        "debt_tenor_years": 20,
        "operating_years": 40,
        "discount_rate": 0.08,
        "emissions_tCO2_per_mwh": 0.82,
    }


@pytest.fixture
def simple_plant_params():
    """Simplified plant with zero opex/fuel for isolated financial tests."""
    return {
        "capacity_mw": 1000,
        "capacity_factor": 0.5,
        "power_price_per_mwh": 100,
        "heat_rate_mmbtu_mwh": 8.8,
        "fuel_price_per_mmbtu": 0,
        "fixed_opex_per_kw_year": 0,
        "variable_opex_per_mwh": 0,
        "total_capex_million": 1000,
        "useful_life": 20,
        "tax_rate": 0.25,
        "debt_fraction": 0.5,
        "debt_interest_rate": 0.05,
        "debt_tenor_years": 10,
        "operating_years": 20,
        "discount_rate": 0.08,
    }


# ---------------------------------------------------------------------------
# Scenario fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def baseline_transition_scenario():
    """No-penalty transition scenario."""
    return TransitionScenario("Baseline", 0.0, 40)


@pytest.fixture
def aggressive_transition_scenario():
    """Aggressive coal phase-out scenario."""
    return TransitionScenario("Aggressive", 0.20, 25)


@pytest.fixture
def no_risk_adjustments():
    """Baseline adjustments with zero risk."""
    trans_adj = TransitionAdjustments(0.85, 40)
    phys_adj = PhysicalAdjustments(0.0, 0.0)
    return trans_adj, phys_adj


@pytest.fixture
def moderate_risk_adjustments():
    """Moderate risk adjustments."""
    trans_adj = TransitionAdjustments(0.65, 30)
    phys_adj = PhysicalAdjustments(0.02, 0.005)
    return trans_adj, phys_adj


@pytest.fixture
def high_risk_adjustments():
    """High risk adjustments."""
    trans_adj = TransitionAdjustments(0.45, 20)
    phys_adj = PhysicalAdjustments(0.05, 0.015)
    return trans_adj, phys_adj


# ---------------------------------------------------------------------------
# Financing parameter fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def financing_params():
    """Standard financing parameters for CRP calculation."""
    return {
        "spread_slope_bps_per_pct": 50,
        "equity_slope_pct_per_pct": 0.8,
        "baseline_spread_bps": 150,
        "risk_free_rate": 0.035,
        "debt_fraction": 0.70,
        "equity_fraction": 0.30,
    }

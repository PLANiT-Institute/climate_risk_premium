"""
Tests for compound risk calculation (corrected multiplier range 1.0-1.25).
"""
import pytest
from src.climada.hazards import calculate_compound_risk, CLIMADAHazardData


def test_compound_risk_baseline_severity():
    """Test baseline severity returns 1.0x multiplier."""
    hazard = calculate_compound_risk(
        wildfire_outage=0.005,
        flood_outage=0.001,
        slr_derate=0.0,
        scenario_severity="baseline"
    )
    assert hazard.compound_multiplier == 1.0
    assert "System Stress" in hazard.notes


def test_compound_risk_moderate_severity():
    """Test moderate severity returns 1.05x multiplier."""
    hazard = calculate_compound_risk(
        wildfire_outage=0.05,
        flood_outage=0.02,
        slr_derate=0.05,
        scenario_severity="moderate"
    )
    assert hazard.compound_multiplier == 1.05


def test_compound_risk_extreme_severity():
    """Test extreme severity returns 1.15x multiplier."""
    hazard = calculate_compound_risk(
        wildfire_outage=0.05,
        flood_outage=0.02,
        slr_derate=0.05,
        scenario_severity="extreme"
    )
    assert hazard.compound_multiplier == 1.15
    expected_outage = (0.05 + 0.02) * 1.15
    assert abs(hazard.total_outage_rate - expected_outage) < 1e-9


def test_compound_risk_zero():
    """Test zero risk case."""
    hazard = calculate_compound_risk(0, 0, 0)
    assert hazard.compound_multiplier == 1.0
    assert hazard.total_outage_rate == 0.0


def test_compound_risk_catastrophic():
    """Test catastrophic severity returns 1.25x multiplier."""
    hazard = calculate_compound_risk(
        wildfire_outage=0.1,
        flood_outage=0.05,
        slr_derate=0.1,
        scenario_severity="catastrophic"
    )
    assert hazard.compound_multiplier == 1.25

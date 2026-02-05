import pytest
from src.climada.hazards import calculate_compound_risk, CLIMADAHazardData

def test_compound_risk_low():
    """Test that low risks have minimal amplification."""
    hazard = calculate_compound_risk(
        wildfire_outage=0.005, # 0.5%
        flood_outage=0.001,    # 0.1%
        slr_derate=0.0         # 0%
    )
    # Total base risk = 0.6%
    # Risk factor = 0.006 * 10 = 0.06
    # Amplification = 1.2 + (0.8 * 0.06) = 1.248
    
    assert hazard.compound_multiplier > 1.2
    assert hazard.compound_multiplier < 1.3
    assert "System Stress" in hazard.notes

def test_compound_risk_high():
    """Test that high risks have significant amplification."""
    hazard = calculate_compound_risk(
        wildfire_outage=0.05, # 5%
        flood_outage=0.02,    # 2%
        slr_derate=0.05       # 5%
    )
    # Total base risk = 12%
    # Risk factor = min(1.0, 0.12 * 10) = 1.0
    # Amplification = 1.2 + (0.8 * 1.0) = 2.0
    
    assert hazard.compound_multiplier == 2.0
    assert hazard.total_outage_rate == (0.05 + 0.02) * 2.0

def test_compound_risk_zero():
    """Test zero risk case."""
    hazard = calculate_compound_risk(0, 0, 0)
    assert hazard.compound_multiplier == 1.2 # Base amplification applies even at zero (theoretical minimum)
    assert hazard.total_outage_rate == 0.0

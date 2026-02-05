"""
Unit tests for CLIMADA hazard integration.
"""
import pytest
from pathlib import Path
from src.climada.hazards import (
    CLIMADAHazardData,
    load_climada_hazards,
    calculate_compound_risk,
    interpolate_hazard_by_year,
    calculate_economic_impact
)


def test_climada_hazard_data_creation():
    """Test basic hazard data creation."""
    hazard = CLIMADAHazardData(
        wildfire_outage_rate=0.025,
        flood_outage_rate=0.003,
        slr_capacity_derate=0.020,
        compound_multiplier=1.15,
        fwi_index=35.0,
        flood_return_period=50.0,
        slr_meters=0.35,
        data_source='Test data'
    )

    assert hazard.wildfire_outage_rate == 0.025
    assert hazard.flood_outage_rate == 0.003
    assert hazard.slr_capacity_derate == 0.020
    assert hazard.compound_multiplier == 1.15


def test_total_outage_rate():
    """Test combined outage rate calculation."""
    hazard = CLIMADAHazardData(
        wildfire_outage_rate=0.025,
        flood_outage_rate=0.003,
        slr_capacity_derate=0.020,
        compound_multiplier=1.15
    )

    # Total outage = (wildfire + flood) × compound
    expected_outage = (0.025 + 0.003) * 1.15
    assert abs(hazard.total_outage_rate - expected_outage) < 0.0001


def test_total_capacity_derate():
    """Test capacity derating calculation."""
    hazard = CLIMADAHazardData(
        wildfire_outage_rate=0.025,
        flood_outage_rate=0.003,
        slr_capacity_derate=0.030,
        compound_multiplier=1.2
    )

    # Total derate = slr_derate × compound
    expected_derate = 0.030 * 1.2
    assert abs(hazard.total_capacity_derate - expected_derate) < 0.0001


def test_effective_capacity_factor_multiplier():
    """Test combined CF impact."""
    hazard = CLIMADAHazardData(
        wildfire_outage_rate=0.020,
        flood_outage_rate=0.005,
        slr_capacity_derate=0.030,
        compound_multiplier=1.0  # No compounding for this test
    )

    # CF_effective = (1 - derate) × (1 - outage)
    expected_cf_mult = (1 - 0.030) * (1 - 0.025)
    assert abs(hazard.effective_capacity_factor_multiplier - expected_cf_mult) < 0.0001


def test_calculate_compound_risk():
    """Test compound risk calculation with dynamic amplification."""
    hazard = calculate_compound_risk(
        wildfire_outage=0.025,
        flood_outage=0.003,
        slr_derate=0.020,
        base_amplification=1.2
    )

    assert hazard.wildfire_outage_rate == 0.025
    assert hazard.flood_outage_rate == 0.003
    assert hazard.slr_capacity_derate == 0.020

    # Compound multiplier is calculated dynamically based on total risk
    # total_base_risk = 0.025 + 0.003 + 0.020 = 0.048
    # risk_factor = min(1.0, 0.048 * 10) = 0.48
    # final_multiplier = 1.2 + (0.8 * 0.48) = 1.584
    expected_multiplier = 1.2 + (0.8 * min(1.0, 0.048 * 10))
    assert abs(hazard.compound_multiplier - expected_multiplier) < 0.001

    # Total outage should include compound multiplier
    expected_outage = (0.025 + 0.003) * expected_multiplier
    assert abs(hazard.total_outage_rate - expected_outage) < 0.0001


def test_load_climada_hazards():
    """Test loading CLIMADA hazards from CSV."""
    base_dir = Path(__file__).parent.parent
    csv_path = base_dir / 'data' / 'raw' / 'climada_hazards.csv'

    if not csv_path.exists():
        pytest.skip("climada_hazards.csv not found")

    hazards = load_climada_hazards(str(csv_path))

    # Check that hazards were loaded
    assert len(hazards) > 0
    assert 'baseline' in hazards

    # Check baseline has minimal risks (literature-backed values)
    baseline = hazards['baseline']
    assert baseline.wildfire_outage_rate <= 0.02  # 1-2% from CAISO data
    assert baseline.flood_outage_rate <= 0.02     # 1-2% from Seoul flood standards
    assert baseline.slr_capacity_derate < 0.01

    # Check high physical scenarios exist
    high_scenarios = [k for k in hazards.keys() if 'high_physical' in k]
    assert len(high_scenarios) > 0


def test_load_climada_hazards_filter():
    """Test loading specific scenario."""
    base_dir = Path(__file__).parent.parent
    csv_path = base_dir / 'data' / 'raw' / 'climada_hazards.csv'

    if not csv_path.exists():
        pytest.skip("climada_hazards.csv not found")

    hazards = load_climada_hazards(str(csv_path), scenario_name='baseline')

    # Should only have baseline
    assert len(hazards) == 1
    assert 'baseline' in hazards


def test_interpolate_hazard_by_year():
    """Test hazard interpolation between years."""
    # Create mock hazards for different years
    hazards = {
        'test_2030': CLIMADAHazardData(
            wildfire_outage_rate=0.020,
            flood_outage_rate=0.003,
            slr_capacity_derate=0.015,
            compound_multiplier=1.1,
            fwi_index=30.0,
            slr_meters=0.20
        ),
        'test_2050': CLIMADAHazardData(
            wildfire_outage_rate=0.040,
            flood_outage_rate=0.005,
            slr_capacity_derate=0.035,
            compound_multiplier=1.2,
            fwi_index=50.0,
            slr_meters=0.50
        )
    }

    # Interpolate to 2040 (midpoint)
    hazard_2040 = interpolate_hazard_by_year(hazards, 2040, 'test')

    # Check interpolated values
    assert 0.025 < hazard_2040.wildfire_outage_rate < 0.035  # Between 0.02 and 0.04
    assert 0.020 < hazard_2040.slr_capacity_derate < 0.030   # Between 0.015 and 0.035
    assert 35.0 < hazard_2040.fwi_index < 45.0              # Between 30 and 50


def test_calculate_economic_impact():
    """Test economic impact calculation."""
    hazard = CLIMADAHazardData(
        wildfire_outage_rate=0.025,
        flood_outage_rate=0.003,
        slr_capacity_derate=0.030,
        compound_multiplier=1.0
    )

    impact = calculate_economic_impact(
        hazard=hazard,
        capacity_mw=2100,
        power_price=80,
        annual_fixed_costs=88_200_000  # $42/kW-year for 2100 MW
    )

    # Should have positive losses
    assert impact['annual_generation_loss_mwh'] > 0
    assert impact['annual_revenue_loss'] > 0
    assert impact['outage_generation_loss_mwh'] > 0
    assert impact['derate_generation_loss_mwh'] > 0

    # CF reduction should be reasonable (< 10% for moderate risks)
    assert 0 < impact['capacity_factor_reduction_pct'] < 15

    # Cost per MWh increase should be positive
    assert impact['cost_per_mwh_increase'] > 0


def test_economic_impact_baseline():
    """Test economic impact for baseline (minimal risk)."""
    hazard = CLIMADAHazardData(
        wildfire_outage_rate=0.001,
        flood_outage_rate=0.0002,
        slr_capacity_derate=0.0,
        compound_multiplier=1.0
    )

    impact = calculate_economic_impact(
        hazard=hazard,
        capacity_mw=2100,
        power_price=80
    )

    # Baseline should have minimal losses
    assert impact['annual_generation_loss_mwh'] < 200_000  # < 1% of annual gen
    assert impact['capacity_factor_reduction_pct'] < 2


def test_hazard_to_dict():
    """Test hazard data export to dictionary."""
    hazard = CLIMADAHazardData(
        wildfire_outage_rate=0.025,
        flood_outage_rate=0.003,
        slr_capacity_derate=0.020,
        compound_multiplier=1.15,
        fwi_index=35.0
    )

    data_dict = hazard.to_dict()

    # Check all fields present
    assert 'wildfire_outage_rate' in data_dict
    assert 'flood_outage_rate' in data_dict
    assert 'slr_capacity_derate' in data_dict
    assert 'total_outage_rate' in data_dict
    assert 'total_capacity_derate' in data_dict
    assert 'effective_cf_multiplier' in data_dict
    assert 'fwi_index' in data_dict

    # Check calculated fields
    assert data_dict['total_outage_rate'] > 0
    assert data_dict['effective_cf_multiplier'] < 1.0


def test_extreme_hazard_capping():
    """Test that extreme hazards don't exceed 100%."""
    hazard = CLIMADAHazardData(
        wildfire_outage_rate=0.80,  # Very high
        flood_outage_rate=0.50,     # Very high
        slr_capacity_derate=0.90,   # Very high
        compound_multiplier=2.0      # Extreme compound
    )

    # Total outage should be capped at 100%
    assert hazard.total_outage_rate <= 1.0

    # Total derate should be capped at 100%
    assert hazard.total_capacity_derate <= 1.0

    # Effective CF multiplier should be >= 0
    assert hazard.effective_capacity_factor_multiplier >= 0.0

"""
Tests for WildfireModel (src/models/physical/wildfire.py).

Validates calibration against data/physical/hazard_baselines.csv
and data/physical_risk_inputs/climate_factors.csv.
"""
import pytest
from src.models.physical.wildfire import (
    WildfireModel,
    WildfireOutageResult,
    BASELINE_OUTAGE_RATE,
    _CLIMATE_FACTORS_RCP45,
    _CLIMATE_FACTORS_RCP85,
    _interpolate,
)


# ---------------------------------------------------------------------------
# Baseline calibration
# ---------------------------------------------------------------------------

class TestBaselineCalibration:
    def test_baseline_outage_rate_matches_csv(self):
        """BASELINE_OUTAGE_RATE must equal hazard_baselines.csv value."""
        assert BASELINE_OUTAGE_RATE == pytest.approx(0.000034, rel=1e-6)

    def test_baseline_year_returns_unscaled_rate(self):
        """Year 2024 is the calibration anchor — factor 1.0, rate = baseline."""
        for scenario in ("RCP4.5", "RCP8.5", "SSP1-2.6", "ssp126", "ssp585"):
            model = WildfireModel(scenario)
            assert model.calculate_outage_rate(2024) == pytest.approx(
                BASELINE_OUTAGE_RATE, rel=1e-9
            ), f"Baseline mismatch for scenario={scenario}"

    def test_pre_baseline_year_returns_baseline(self):
        """Years before 2024 extrapolate to the 2024 anchor (no negative scaling)."""
        model = WildfireModel("RCP8.5")
        assert model.calculate_outage_rate(2010) == pytest.approx(BASELINE_OUTAGE_RATE)
        assert model.calculate_outage_rate(2000) == pytest.approx(BASELINE_OUTAGE_RATE)


# ---------------------------------------------------------------------------
# Climate factor anchor values (from climate_factors.csv)
# ---------------------------------------------------------------------------

class TestClimateFactorAnchors:
    @pytest.mark.parametrize("year,expected", [
        (2024, 1.00),
        (2030, 1.15),
        (2050, 1.35),
        (2100, 1.60),
    ])
    def test_rcp45_anchors(self, year, expected):
        model = WildfireModel("RCP4.5")
        assert model.get_climate_factor(year) == pytest.approx(expected, rel=1e-9)

    @pytest.mark.parametrize("year,expected", [
        (2024, 1.00),
        (2030, 1.20),
        (2050, 1.50),
        (2100, 2.20),
    ])
    def test_rcp85_anchors(self, year, expected):
        model = WildfireModel("RCP8.5")
        assert model.get_climate_factor(year) == pytest.approx(expected, rel=1e-9)


# ---------------------------------------------------------------------------
# Scenario differentiation
# ---------------------------------------------------------------------------

class TestScenarioDifferentiation:
    def test_rcp85_higher_than_rcp45_at_2040(self):
        """RCP8.5 must project higher outage risk than RCP4.5 by 2040."""
        r45 = WildfireModel("RCP4.5").calculate_outage_rate(2040)
        r85 = WildfireModel("RCP8.5").calculate_outage_rate(2040)
        assert r85 > r45

    def test_rcp85_higher_than_rcp45_at_2050(self):
        r45 = WildfireModel("RCP4.5").calculate_outage_rate(2050)
        r85 = WildfireModel("RCP8.5").calculate_outage_rate(2050)
        assert r85 > r45

    def test_ssp126_maps_to_rcp45(self):
        """SSP1-2.6 and ssp126 should produce identical results to RCP4.5."""
        rcp45 = WildfireModel("RCP4.5").calculate_outage_rate(2050)
        ssp126 = WildfireModel("SSP1-2.6").calculate_outage_rate(2050)
        ssp126b = WildfireModel("ssp126").calculate_outage_rate(2050)
        assert ssp126 == pytest.approx(rcp45)
        assert ssp126b == pytest.approx(rcp45)

    def test_ssp585_maps_to_rcp85(self):
        """ssp585 should produce identical results to RCP8.5."""
        rcp85 = WildfireModel("RCP8.5").calculate_outage_rate(2050)
        ssp585 = WildfireModel("ssp585").calculate_outage_rate(2050)
        assert ssp585 == pytest.approx(rcp85)

    def test_unknown_scenario_falls_back_to_rcp45(self):
        """Unknown scenario labels should not crash and return conservative values."""
        model = WildfireModel("UNKNOWN_SCENARIO")
        rate = model.calculate_outage_rate(2050)
        rcp45 = WildfireModel("RCP4.5").calculate_outage_rate(2050)
        assert rate == pytest.approx(rcp45)


# ---------------------------------------------------------------------------
# Temporal progression
# ---------------------------------------------------------------------------

class TestTemporalProgression:
    @pytest.mark.parametrize("scenario", ["RCP4.5", "RCP8.5"])
    def test_outage_rate_increases_over_time(self, scenario):
        """Later years must produce higher outage rates than earlier ones."""
        model = WildfireModel(scenario)
        r2030 = model.calculate_outage_rate(2030)
        r2050 = model.calculate_outage_rate(2050)
        r2080 = model.calculate_outage_rate(2080)
        assert r2050 > r2030, f"{scenario}: 2050 not > 2030"
        assert r2080 > r2050, f"{scenario}: 2080 not > 2050"

    def test_interpolation_between_2030_and_2050_rcp85(self):
        """2040 value should be between 2030 and 2050 anchor values."""
        model = WildfireModel("RCP8.5")
        r2030 = model.calculate_outage_rate(2030)
        r2040 = model.calculate_outage_rate(2040)
        r2050 = model.calculate_outage_rate(2050)
        assert r2030 < r2040 < r2050

    def test_post_2100_extrapolation_capped(self):
        """Years beyond 2100 should return the 2100 value, not extrapolate upward."""
        model = WildfireModel("RCP8.5")
        r2100 = model.calculate_outage_rate(2100)
        r2120 = model.calculate_outage_rate(2120)
        assert r2120 == pytest.approx(r2100)


# ---------------------------------------------------------------------------
# Bounds and output contract
# ---------------------------------------------------------------------------

class TestOutputBounds:
    @pytest.mark.parametrize("year", [2010, 2024, 2030, 2040, 2050, 2075, 2100, 2150])
    @pytest.mark.parametrize("scenario", ["RCP4.5", "RCP8.5"])
    def test_outage_rate_in_unit_interval(self, scenario, year):
        model = WildfireModel(scenario)
        rate = model.calculate_outage_rate(year)
        assert 0.0 <= rate <= 1.0, f"Out of bounds: {scenario}/{year} → {rate}"

    def test_calculate_returns_result_object(self):
        model = WildfireModel("RCP8.5")
        result = model.calculate(2050)
        assert isinstance(result, WildfireOutageResult)
        assert result.year == 2050
        assert result.scenario == "RCP8.5"
        assert result.baseline_outage_rate == pytest.approx(BASELINE_OUTAGE_RATE)
        assert result.outage_rate == pytest.approx(result.baseline_outage_rate * result.climate_factor)
        assert result.source != ""


# ---------------------------------------------------------------------------
# Interpolation helper
# ---------------------------------------------------------------------------

class TestInterpolate:
    def test_exact_anchor(self):
        anchors = {2024: 1.0, 2050: 1.5, 2100: 2.0}
        assert _interpolate(anchors, 2024) == pytest.approx(1.0)
        assert _interpolate(anchors, 2050) == pytest.approx(1.5)
        assert _interpolate(anchors, 2100) == pytest.approx(2.0)

    def test_midpoint(self):
        anchors = {2024: 1.0, 2050: 1.5}
        mid = _interpolate(anchors, 2037)
        assert mid == pytest.approx(1.25, abs=0.01)

    def test_before_first_anchor(self):
        anchors = {2024: 1.0, 2050: 1.5}
        assert _interpolate(anchors, 2010) == pytest.approx(1.0)

    def test_after_last_anchor(self):
        anchors = {2024: 1.0, 2050: 1.5}
        assert _interpolate(anchors, 2080) == pytest.approx(1.5)

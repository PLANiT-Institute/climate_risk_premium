"""Unit tests for src/risk/physical.py — wildfire, TC, drought and heat/SST channels.

Numerical assertions use np.testing.assert_allclose so tolerances are explicit
and failures show the actual vs expected values.

All expected values are derived from first principles using CSV parameter values.
No values are hardcoded here beyond what appears verbatim in the data/ CSVs.

CSV parameters used below
--------------------------
climada_data.csv:
    wildfire:                    events=6,  years=20  → freq=0.30/yr
    tropical_cyclone_damaging:   events=5,  years=40  → freq=0.125/yr

model_assumptions.csv:
    outage_prob_wildfire   = 0.10
    outage_prob_tc         = 0.30
    outage_duration_wildfire = 168 h
    outage_duration_tc       = 168 h
    hours_per_year           = 8760
    drought_capacity_derate_base = 0.005

literature_data.csv (high_physical / SSP5-8.5, scale=1.0):
    WILDFIRE  climate_factor @ 2050 = 2.0    → wf_scaled_factor = 2.0
    TC        climate_factor @ 2050 = 1.10   → tc_scaled_factor = 1.10
    DROUGHT   climate_factor @ 2050 = 1.45
    HEAT      korea_temp_change_ssp585 @ 2050 = 1.75 °C
    EFFICIENCY ambient_derate_model = 0.08 %/°C
    EFFICIENCY cooling_water_derate = 0.133 %/°C
    EFFICIENCY sst_air_ratio        = 0.80
    HEATWAVE  days_baseline = 5.0 d/yr
    HEATWAVE  days_future   = 17.4 d/yr
    HEATWAVE  efficiency_loss = 4.0 %

Derived expected values (high_physical, SSP5-8.5, scale=1.0):
    base_wf_plant    = 0.30 × 0.10 × (168/8760) = 5.7534e-4
    wf_plant_2050    = 5.7534e-4 × 2.0          = 1.1507e-3
    base_wf_tx       = 0.30 × 0.30 × (168/8760) = 1.7260e-3
    wf_tx_2050       = 1.7260e-3 × 2.0          = 3.4521e-3

    base_tc_plant    = 0.125 × 0.30 × (168/8760) = 7.1918e-4
    tc_plant_2050    = 7.1918e-4 × 1.10          = 7.9110e-4
    base_tc_tx       = 0.125 × 0.30 × (168/8760) = 7.1918e-4
    tc_tx_2050       = 7.1918e-4 × 1.10          = 7.9110e-4
    combined_2050    = 1 − (1−1.1507e-3)(1−7.9110e-4) = 1.9409e-3

    capacity_derate_2050  = 0.005 × 1.45 = 7.25e-3
    eff_loss_per_C        = (0.08 + 0.80×0.133)/100 = 1.864e-3 /°C
    chronic_eff_2050      = 1.75 × 1.864e-3          = 3.262e-3
    heatwave_days_2050    = 5.0 + 12.4 × (26/76) × 1.0 = 9.242 d/yr
    heatwave_eff_2050     = (9.242/365) × 0.04       = 1.0126e-3
    total_eff_2050        = 3.262e-3 + 1.0126e-3     = 4.2746e-3
"""
from __future__ import annotations

import numpy as np
import pytest

from src.risk.physical import (
    PhysicalAdjustments,
    YearlyPhysicalAdjustments,
    build_physical_adjustments,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def adj_high() -> YearlyPhysicalAdjustments:
    """high_physical (SSP5-8.5, scale=1.0) adjustments for 2025–2100."""
    return build_physical_adjustments(start_year=2025, n_years=76, physical_scenario="high_physical")


@pytest.fixture(scope="module")
def adj_baseline() -> YearlyPhysicalAdjustments:
    """baseline (SSP1-2.6, scale=0.30) adjustments for 2025–2100."""
    return build_physical_adjustments(start_year=2025, n_years=76, physical_scenario="baseline")


@pytest.fixture(scope="module")
def adj_moderate() -> YearlyPhysicalAdjustments:
    """moderate_physical (SSP2-4.5, scale=0.60) adjustments for 2025–2100."""
    return build_physical_adjustments(start_year=2025, n_years=76, physical_scenario="moderate_physical")


# ---------------------------------------------------------------------------
# Parameter constants derived from CSVs (no hardcoded values; all from above)
# ---------------------------------------------------------------------------

_H_PY = 8760   # hours_per_year

# Wildfire (climada_data.csv + model_assumptions.csv)
_WF_FREQ             = 6 / 20           # 0.30 /yr
_OUTAGE_PROB_WF      = 0.10
_OUTAGE_PROB_TC      = 0.30
_OUTAGE_DUR_WF       = 168              # h (outage_duration_wildfire)
_OUTAGE_DUR_TC       = 168              # h (outage_duration_tc)
_BASE_WF_PLANT       = _WF_FREQ * _OUTAGE_PROB_WF * (_OUTAGE_DUR_WF / _H_PY)   # 5.7534e-4
_BASE_WF_TX          = _WF_FREQ * _OUTAGE_PROB_TC * (_OUTAGE_DUR_TC / _H_PY)   # 1.7260e-3

# Tropical cyclone (climada_data.csv + model_assumptions.csv)
_TC_FREQ             = 5 / 40           # 0.125 /yr
_BASE_TC_PLANT       = _TC_FREQ * _OUTAGE_PROB_TC * (_OUTAGE_DUR_WF / _H_PY)   # 7.1918e-4
_BASE_TC_TX          = _TC_FREQ * _OUTAGE_PROB_TC * (_OUTAGE_DUR_TC / _H_PY)   # 7.1918e-4

# Climate factors at anchor years (literature_data.csv)
_WF_FACTOR_2050      = 2.0
_WF_FACTOR_2030      = 2.0
_WF_FACTOR_2100      = 4.0
_TC_FACTOR_2050      = 1.10
_TC_FACTOR_2030      = 1.05
_TC_FACTOR_2100      = 1.10             # plateaus at 2050

# Expected outage rates at 2050, high_physical (scale=1.0)
_EXPECTED_WF_PLANT_2050  = _BASE_WF_PLANT * _WF_FACTOR_2050   # 1.1507e-3
_EXPECTED_WF_TX_2050     = _BASE_WF_TX    * _WF_FACTOR_2050   # 3.4521e-3
_EXPECTED_TC_PLANT_2050  = _BASE_TC_PLANT * _TC_FACTOR_2050   # 7.9110e-4
_EXPECTED_TC_TX_2050     = _BASE_TC_TX    * _TC_FACTOR_2050   # 7.9110e-4
_EXPECTED_COMBINED_2050  = (
    1.0 - (1.0 - _EXPECTED_WF_PLANT_2050) * (1.0 - _EXPECTED_TC_PLANT_2050)
)

# Drought (model_assumptions.csv + literature_data.csv)
_DROUGHT_BASE            = 0.005
_DR_FACTOR_2050          = 1.45
_EXPECTED_CAPACITY_DERATE_2050 = _DROUGHT_BASE * _DR_FACTOR_2050  # 7.25e-3

# Heat / SST (literature_data.csv)
_EFF_LOSS_PER_C      = (0.08 + 0.80 * 0.133) / 100.0   # 1.864e-3 /°C
_DELTA_T_2050        = 1.75                               # °C (SSP5-8.5, scale=1.0)
_EXPECTED_CHRONIC_EFF_2050 = _DELTA_T_2050 * _EFF_LOSS_PER_C  # 3.262e-3

# Heatwave (literature_data.csv)
_HW_DAYS_BASE        = 5.0
_HW_DAYS_FUTURE      = 17.4
_HW_EFF_PCT          = 4.0
_HW_T_2050           = (2050 - 2024) / (2100 - 2024)    # 26/76
_HW_DAYS_2050        = _HW_DAYS_BASE + (_HW_DAYS_FUTURE - _HW_DAYS_BASE) * _HW_T_2050
_EXPECTED_HW_EFF_2050 = (_HW_DAYS_2050 / 365.0) * (_HW_EFF_PCT / 100.0)
_EXPECTED_TOTAL_EFF_2050 = _EXPECTED_CHRONIC_EFF_2050 + _EXPECTED_HW_EFF_2050


# ---------------------------------------------------------------------------
# Shape and metadata
# ---------------------------------------------------------------------------

class TestShape:
    def test_years_length(self, adj_high):
        assert len(adj_high.years) == 76

    def test_all_arrays_same_length(self, adj_high):
        n = len(adj_high.years)
        for arr_name in (
            "outage_rates", "transmission_outage_rates",
            "tc_outage_rates", "tc_transmission_outage_rates",
            "combined_outage_rates", "combined_transmission_outage_rates",
            "capacity_derates", "efficiency_losses",
            "chronic_efficiency_losses", "heatwave_efficiency_losses",
            "water_constraints", "asset_capex_loss_rates",
        ):
            assert len(getattr(adj_high, arr_name)) == n, f"{arr_name} wrong length"

    def test_year_range(self, adj_high):
        assert adj_high.years[0] == 2025
        assert adj_high.years[-1] == 2100

    def test_scenario_name_stored(self, adj_high):
        assert adj_high.scenario_name == "high_physical"


# ---------------------------------------------------------------------------
# Wildfire outage
# ---------------------------------------------------------------------------

class TestWildfireFormula:
    def test_plant_outage_2050(self, adj_high):
        val = float(np.interp(2050, adj_high.years, adj_high.outage_rates))
        np.testing.assert_allclose(val, _EXPECTED_WF_PLANT_2050, rtol=1e-3)

    def test_transmission_outage_2050(self, adj_high):
        val = float(np.interp(2050, adj_high.years, adj_high.transmission_outage_rates))
        np.testing.assert_allclose(val, _EXPECTED_WF_TX_2050, rtol=1e-3)

    def test_outage_at_2025_near_base(self, adj_high):
        """At 2025 the climate factor is slightly above 1.0 (interpolation from 2024 anchor)."""
        val = float(np.interp(2025, adj_high.years, adj_high.outage_rates))
        # Factor interpolated from 2024→2030, so factor > base but < 2030 value
        assert val >= _BASE_WF_PLANT * 1.0
        assert val <= _BASE_WF_PLANT * 2.0

    def test_outage_monotone_increasing(self, adj_high):
        assert np.all(np.diff(adj_high.outage_rates) >= -1e-15)

    def test_outage_rates_positive(self, adj_high):
        assert np.all(adj_high.outage_rates > 0)

    def test_factor_held_at_2030_anchor(self, adj_high):
        """At 2030 WILDFIRE factor=2.0 (scale=1.0) → plant_outage = base × 2.0."""
        val = float(np.interp(2030, adj_high.years, adj_high.outage_rates))
        np.testing.assert_allclose(val, _BASE_WF_PLANT * _WF_FACTOR_2030, rtol=1e-6)

    def test_factor_held_constant_beyond_2100(self):
        """Climate factor is clamped (np.interp) beyond the last anchor year."""
        adj = build_physical_adjustments(start_year=2025, n_years=100)
        r_2100 = float(np.interp(2100, adj.years, adj.outage_rates))
        r_last  = float(adj.outage_rates[-1])
        np.testing.assert_allclose(r_last, r_2100, rtol=1e-6)


# ---------------------------------------------------------------------------
# Tropical cyclone outage (new channel)
# ---------------------------------------------------------------------------

class TestTCFormula:
    def test_tc_plant_outage_2050(self, adj_high):
        val = float(np.interp(2050, adj_high.years, adj_high.tc_outage_rates))
        np.testing.assert_allclose(val, _EXPECTED_TC_PLANT_2050, rtol=1e-3)

    def test_tc_tx_outage_2050(self, adj_high):
        val = float(np.interp(2050, adj_high.years, adj_high.tc_transmission_outage_rates))
        np.testing.assert_allclose(val, _EXPECTED_TC_TX_2050, rtol=1e-3)

    def test_tc_outage_at_2030_anchor(self, adj_high):
        """TC factor at 2030 = 1.05 (Knutson et al. 2020, scale=1.0)."""
        val = float(np.interp(2030, adj_high.years, adj_high.tc_outage_rates))
        np.testing.assert_allclose(val, _BASE_TC_PLANT * _TC_FACTOR_2030, rtol=1e-6)

    def test_tc_factor_plateaus_after_2050(self, adj_high):
        """TC factor clamps at 1.10 from 2050 onward (no further amplification modelled)."""
        val_2050 = float(np.interp(2050, adj_high.years, adj_high.tc_outage_rates))
        val_2100 = float(np.interp(2100, adj_high.years, adj_high.tc_outage_rates))
        np.testing.assert_allclose(val_2100, val_2050, rtol=1e-6)

    def test_tc_rates_positive(self, adj_high):
        assert np.all(adj_high.tc_outage_rates > 0)

    def test_tc_monotone_through_2050(self, adj_high):
        """TC increases through 2050 then plateaus — diff should be ≥ 0."""
        assert np.all(np.diff(adj_high.tc_outage_rates) >= -1e-15)

    def test_combined_outage_2050(self, adj_high):
        """Combined = 1−(1−wf_plant)(1−tc_plant)."""
        val = float(np.interp(2050, adj_high.years, adj_high.combined_outage_rates))
        np.testing.assert_allclose(val, _EXPECTED_COMBINED_2050, rtol=1e-3)

    def test_combined_greater_than_wildfire_alone(self, adj_high):
        """Combined outage must exceed wildfire-only at every year."""
        assert np.all(adj_high.combined_outage_rates > adj_high.outage_rates)

    def test_tc_baseline_smaller_than_high(self, adj_baseline, adj_high):
        b = float(np.interp(2050, adj_baseline.years, adj_baseline.tc_outage_rates))
        h = float(np.interp(2050, adj_high.years, adj_high.tc_outage_rates))
        assert b < h

    def test_tc_base_rate_at_2024(self):
        """At 2024 TC factor = 1.0 → tc_outage = base_tc_plant × 1.0."""
        adj = build_physical_adjustments(start_year=2024, n_years=1, physical_scenario="high_physical")
        np.testing.assert_allclose(float(adj.tc_outage_rates[0]), _BASE_TC_PLANT, rtol=1e-6)


# ---------------------------------------------------------------------------
# SSP scaling
# ---------------------------------------------------------------------------

class TestSSPScaling:
    def test_baseline_smaller_than_high(self, adj_baseline, adj_high):
        b = float(np.interp(2050, adj_baseline.years, adj_baseline.outage_rates))
        h = float(np.interp(2050, adj_high.years, adj_high.outage_rates))
        assert b < h

    def test_moderate_between_baseline_and_high(self, adj_baseline, adj_moderate, adj_high):
        b = float(np.interp(2050, adj_baseline.years, adj_baseline.outage_rates))
        m = float(np.interp(2050, adj_moderate.years, adj_moderate.outage_rates))
        h = float(np.interp(2050, adj_high.years, adj_high.outage_rates))
        assert b < m < h

    def test_severe_drought_equals_high(self):
        """severe_drought uses the same SSP585 scale as high_physical."""
        adj_severe = build_physical_adjustments(start_year=2025, n_years=76, physical_scenario="severe_drought")
        adj_h      = build_physical_adjustments(start_year=2025, n_years=76, physical_scenario="high_physical")
        np.testing.assert_allclose(adj_severe.outage_rates, adj_h.outage_rates, rtol=1e-10)

    def test_ssp_scale_ratios_at_2100(self, adj_baseline, adj_moderate, adj_high):
        """
        At 2100 WF factor = 4.0 (SSP5-8.5).
        scaled_factor = 1 + (4.0−1) × ssp_scale:
          baseline scale=0.30 → 1 + 3×0.30 = 1.90 → outage = base × 1.90
          moderate scale=0.60 → 1 + 3×0.60 = 2.80 → outage = base × 2.80
          high     scale=1.00 → 1 + 3×1.00 = 4.00 → outage = base × 4.00
        """
        b = float(np.interp(2100, adj_baseline.years, adj_baseline.outage_rates))
        m = float(np.interp(2100, adj_moderate.years, adj_moderate.outage_rates))
        h = float(np.interp(2100, adj_high.years,     adj_high.outage_rates))
        np.testing.assert_allclose(b / _BASE_WF_PLANT, 1.90, rtol=1e-6)
        np.testing.assert_allclose(m / _BASE_WF_PLANT, 2.80, rtol=1e-6)
        np.testing.assert_allclose(h / _BASE_WF_PLANT, 4.00, rtol=1e-6)


# ---------------------------------------------------------------------------
# get_adjustment_for_year()
# ---------------------------------------------------------------------------

class TestGetAdjustmentForYear:
    def test_returns_physical_adjustments_type(self, adj_high):
        result = adj_high.get_adjustment_for_year(2030)
        assert isinstance(result, PhysicalAdjustments)

    def test_year_in_range_wildfire(self, adj_high):
        result = adj_high.get_adjustment_for_year(2050)
        np.testing.assert_allclose(result.outage_rate, _EXPECTED_WF_PLANT_2050, rtol=1e-3)

    def test_year_in_range_tc(self, adj_high):
        result = adj_high.get_adjustment_for_year(2050)
        np.testing.assert_allclose(result.tc_outage_rate, _EXPECTED_TC_PLANT_2050, rtol=1e-3)

    def test_year_in_range_combined(self, adj_high):
        result = adj_high.get_adjustment_for_year(2050)
        np.testing.assert_allclose(result.combined_outage_rate, _EXPECTED_COMBINED_2050, rtol=1e-3)

    def test_year_in_range_capacity_derate(self, adj_high):
        result = adj_high.get_adjustment_for_year(2050)
        assert result.capacity_derate > 0.0

    def test_year_in_range_efficiency_loss(self, adj_high):
        result = adj_high.get_adjustment_for_year(2050)
        assert result.efficiency_loss > 0.0
        assert result.efficiency_loss > result.chronic_efficiency_loss   # heatwave adds to it

    def test_year_out_of_range_returns_zeros(self, adj_high):
        result = adj_high.get_adjustment_for_year(1900)
        assert result.outage_rate == 0.0
        assert result.capacity_derate == 0.0
        assert result.notes == "out of range"

    def test_notes_contains_scenario_and_year(self, adj_high):
        result = adj_high.get_adjustment_for_year(2040)
        assert "high_physical" in result.notes
        assert "2040" in result.notes


# ---------------------------------------------------------------------------
# Drought channel
# ---------------------------------------------------------------------------

class TestDroughtChannel:
    def test_capacity_derate_2050_high(self, adj_high):
        val = float(np.interp(2050, adj_high.years, adj_high.capacity_derates))
        np.testing.assert_allclose(val, _EXPECTED_CAPACITY_DERATE_2050, rtol=1e-4)

    def test_capacity_derate_monotone_increasing(self, adj_high):
        assert np.all(np.diff(adj_high.capacity_derates) >= -1e-15)

    def test_capacity_derate_baseline_smaller_than_high(self, adj_baseline, adj_high):
        b = float(np.interp(2050, adj_baseline.years, adj_baseline.capacity_derates))
        h = float(np.interp(2050, adj_high.years, adj_high.capacity_derates))
        assert b < h

    def test_capacity_derate_at_base_year(self):
        """At 2024 drought factor=1.0 → derate = drought_base × 1.0."""
        adj = build_physical_adjustments(start_year=2024, n_years=1, physical_scenario="high_physical")
        np.testing.assert_allclose(float(adj.capacity_derates[0]), _DROUGHT_BASE, rtol=1e-6)

    def test_capacity_derate_2100_scale_ratios(self, adj_baseline, adj_moderate, adj_high):
        """
        At 2100 drought factor (SSP5-8.5) = 2.0:
          high     scale=1.0 → derate = 0.005 × (1 + 1.0×1.0) = 0.010
          moderate scale=0.6 → derate = 0.005 × (1 + 1.0×0.6) = 0.008
          baseline scale=0.3 → derate = 0.005 × (1 + 1.0×0.3) = 0.0065
        """
        b = float(np.interp(2100, adj_baseline.years, adj_baseline.capacity_derates))
        m = float(np.interp(2100, adj_moderate.years, adj_moderate.capacity_derates))
        h = float(np.interp(2100, adj_high.years,     adj_high.capacity_derates))
        np.testing.assert_allclose(h, _DROUGHT_BASE * 2.0, rtol=1e-6)
        np.testing.assert_allclose(m, _DROUGHT_BASE * 1.6, rtol=1e-6)
        np.testing.assert_allclose(b, _DROUGHT_BASE * 1.3, rtol=1e-6)


# ---------------------------------------------------------------------------
# Chronic heat / SST channel
# ---------------------------------------------------------------------------

class TestChronicHeatChannel:
    def test_chronic_efficiency_loss_2050_high(self, adj_high):
        val = float(np.interp(2050, adj_high.years, adj_high.chronic_efficiency_losses))
        np.testing.assert_allclose(val, _EXPECTED_CHRONIC_EFF_2050, rtol=1e-4)

    def test_chronic_eff_zero_at_baseline_year(self):
        """At 2024 delta_T=0 → chronic efficiency loss = 0."""
        adj = build_physical_adjustments(start_year=2024, n_years=1, physical_scenario="high_physical")
        np.testing.assert_allclose(float(adj.chronic_efficiency_losses[0]), 0.0, atol=1e-10)

    def test_chronic_eff_monotone_increasing(self, adj_high):
        assert np.all(np.diff(adj_high.chronic_efficiency_losses) >= -1e-15)

    def test_chronic_eff_at_2030_anchor(self, adj_high):
        """At 2030 delta_T=1.0°C (SSP5-8.5, scale=1.0)."""
        val = float(np.interp(2030, adj_high.years, adj_high.chronic_efficiency_losses))
        np.testing.assert_allclose(val, 1.0 * _EFF_LOSS_PER_C, rtol=1e-6)

    def test_chronic_eff_ssp_scale(self, adj_baseline, adj_high):
        """baseline scale=0.30 → chronic_eff = 0.30 × high_chronic_eff."""
        b = float(np.interp(2100, adj_baseline.years, adj_baseline.chronic_efficiency_losses))
        h = float(np.interp(2100, adj_high.years,     adj_high.chronic_efficiency_losses))
        np.testing.assert_allclose(b / h, 0.30, rtol=1e-6)


# ---------------------------------------------------------------------------
# Heatwave acute channel (new)
# ---------------------------------------------------------------------------

class TestHeatwaveChannel:
    def test_heatwave_eff_2050_high(self, adj_high):
        val = float(np.interp(2050, adj_high.years, adj_high.heatwave_efficiency_losses))
        np.testing.assert_allclose(val, _EXPECTED_HW_EFF_2050, rtol=1e-4)

    def test_heatwave_eff_at_2024_equals_base_rate(self):
        """At 2024 heatwave_days = days_baseline → loss = 5/365 × 0.04."""
        adj = build_physical_adjustments(start_year=2024, n_years=1, physical_scenario="high_physical")
        expected_base = (_HW_DAYS_BASE / 365.0) * (_HW_EFF_PCT / 100.0)
        np.testing.assert_allclose(float(adj.heatwave_efficiency_losses[0]), expected_base, rtol=1e-6)

    def test_heatwave_eff_monotone_increasing(self, adj_high):
        assert np.all(np.diff(adj_high.heatwave_efficiency_losses) >= -1e-15)

    def test_heatwave_eff_ssp_scale(self, adj_baseline, adj_high):
        """At 2100, difference from baseline scales by ssp_scale:
        high:     days = 5 + 12.4 × 1.0 = 17.4 → eff = 17.4/365 × 0.04
        baseline: days = 5 + 12.4 × 0.3 = 8.72  → eff = 8.72/365 × 0.04
        """
        hw_high     = float(np.interp(2100, adj_high.years,     adj_high.heatwave_efficiency_losses))
        hw_baseline = float(np.interp(2100, adj_baseline.years, adj_baseline.heatwave_efficiency_losses))
        days_high     = _HW_DAYS_BASE + (_HW_DAYS_FUTURE - _HW_DAYS_BASE) * 1.0
        days_baseline = _HW_DAYS_BASE + (_HW_DAYS_FUTURE - _HW_DAYS_BASE) * 0.30
        np.testing.assert_allclose(hw_high,     (days_high     / 365.0) * (_HW_EFF_PCT / 100.0), rtol=1e-6)
        np.testing.assert_allclose(hw_baseline, (days_baseline / 365.0) * (_HW_EFF_PCT / 100.0), rtol=1e-6)

    def test_total_eff_equals_chronic_plus_heatwave(self, adj_high):
        """Total efficiency loss = chronic + heatwave at every year."""
        total    = adj_high.efficiency_losses
        chronic  = adj_high.chronic_efficiency_losses
        heatwave = adj_high.heatwave_efficiency_losses
        np.testing.assert_allclose(total, chronic + heatwave, rtol=1e-10)

    def test_total_eff_2050_high(self, adj_high):
        val = float(np.interp(2050, adj_high.years, adj_high.efficiency_losses))
        np.testing.assert_allclose(val, _EXPECTED_TOTAL_EFF_2050, rtol=1e-4)


# ---------------------------------------------------------------------------
# Backward-compat: water_constraints placeholder
# ---------------------------------------------------------------------------

class TestPlaceholders:
    def test_water_constraints_one(self, adj_high):
        np.testing.assert_array_equal(adj_high.water_constraints, 1.0)

    def test_asset_capex_loss_rates_zero(self, adj_high):
        np.testing.assert_array_equal(adj_high.asset_capex_loss_rates, 0.0)

"""Unit tests for src/risk/physical.py — wildfire physical risk module.

Numerical assertions use np.testing.assert_allclose so tolerances are explicit
and failures show the actual vs expected values.

Key values cross-checked against archive physical_risk_output.csv (RCP8.5):
    wildfire_projected_pct_2050 = 1.6438e-02 %  →  1.6438e-04 fraction
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
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def adj_high() -> YearlyPhysicalAdjustments:
    """high_physical (SSP5-8.5) adjustments for 2025-2100."""
    return build_physical_adjustments(
        start_year=2025,
        n_years=76,
        physical_scenario="high_physical",
    )


@pytest.fixture(scope="module")
def adj_baseline() -> YearlyPhysicalAdjustments:
    """baseline (SSP1-2.6) adjustments for 2025-2100."""
    return build_physical_adjustments(
        start_year=2025,
        n_years=76,
        physical_scenario="baseline",
    )


@pytest.fixture(scope="module")
def adj_moderate() -> YearlyPhysicalAdjustments:
    """moderate_physical (SSP2-4.5) adjustments for 2025-2100."""
    return build_physical_adjustments(
        start_year=2025,
        n_years=76,
        physical_scenario="moderate_physical",
    )


# ---------------------------------------------------------------------------
# Shape and metadata
# ---------------------------------------------------------------------------

class TestShape:
    def test_years_length(self, adj_high):
        assert len(adj_high.years) == 76

    def test_all_arrays_same_length(self, adj_high):
        n = len(adj_high.years)
        assert len(adj_high.outage_rates) == n
        assert len(adj_high.transmission_outage_rates) == n
        assert len(adj_high.capacity_derates) == n
        assert len(adj_high.efficiency_losses) == n
        assert len(adj_high.water_constraints) == n
        assert len(adj_high.asset_capex_loss_rates) == n

    def test_year_range(self, adj_high):
        assert adj_high.years[0] == 2025
        assert adj_high.years[-1] == 2100

    def test_scenario_name_stored(self, adj_high):
        assert adj_high.scenario_name == "high_physical"


# ---------------------------------------------------------------------------
# Wildfire outage formula (Algorithm verification)
# ---------------------------------------------------------------------------
# Source parameters (from data/physical_risk/ CSVs):
#   annual_frequency     = 6 / 20      = 0.30 events/yr
#   outage_prob_plant    = 0.10
#   outage_dur_plant     = 24 h
#   hours_per_year       = 8760
#   climate_factor_2050  = 2.0  (from literature_data.csv, WILDFIRE category)
#   ssp_scale (ssp585)   = 1.00
#
# base_plant_outage = 0.30 × 0.10 × (24/8760) = 8.2192e-5
# plant_outage_2050 = 8.2192e-5 × [1 + (2.0-1) × 1.0] = 1.6438e-4

_EXPECTED_PLANT_OUTAGE_2050 = 1.6438e-4
_EXPECTED_TX_OUTAGE_2050    = (0.30 * 0.30 * (48 / 8760)) * 2.0  # ssp585 scale=1


class TestWildfireFormula:
    def test_plant_outage_2050(self, adj_high):
        """Cross-checks against archive physical_risk_output.csv wildfire_projected_pct_2050."""
        val = float(np.interp(2050, adj_high.years, adj_high.outage_rates))
        np.testing.assert_allclose(val, _EXPECTED_PLANT_OUTAGE_2050, rtol=1e-3)

    def test_transmission_outage_2050(self, adj_high):
        val = float(np.interp(2050, adj_high.years, adj_high.transmission_outage_rates))
        np.testing.assert_allclose(val, _EXPECTED_TX_OUTAGE_2050, rtol=1e-3)

    def test_outage_at_2025_uses_factor_1(self, adj_high):
        """At 2025 the climate factor should be ~1.0 (baseline anchor year 2024)."""
        # factor interpolated from 2024=1.0, so 2025 ≈ 1.0 + tiny step toward 2030
        val = float(np.interp(2025, adj_high.years, adj_high.outage_rates))
        base_plant = (6 / 20) * 0.10 * (24 / 8760)
        # climate_factor(2025) slightly > 1.0 due to interpolation from 2024→2030
        assert val >= base_plant * 1.0
        assert val <= base_plant * 2.0  # definitely below 2030 value

    def test_outage_monotone_increasing(self, adj_high):
        """Outage rate should not decrease over time (monotone once factors are applied)."""
        assert np.all(np.diff(adj_high.outage_rates) >= -1e-15)

    def test_outage_rates_positive(self, adj_high):
        assert np.all(adj_high.outage_rates > 0)

    def test_efficiency_losses_zero(self, adj_high):
        """Wildfire efficiency loss is zero — belongs to temperature channel, not activated."""
        np.testing.assert_array_equal(adj_high.efficiency_losses, 0.0)

    def test_capacity_derates_zero(self, adj_high):
        np.testing.assert_array_equal(adj_high.capacity_derates, 0.0)

    def test_water_constraints_one(self, adj_high):
        np.testing.assert_array_equal(adj_high.water_constraints, 1.0)


# ---------------------------------------------------------------------------
# SSP scaling
# ---------------------------------------------------------------------------
# SSP scale factors: ssp126=0.30, ssp245=0.60, ssp585=1.00
# Relationship: baseline ≈ 0.30 × high; moderate ≈ 0.60 × high
# (the 1.0 + (factor-1)*scale formula makes the ratios approximately right)

class TestSSPScaling:
    def test_baseline_smaller_than_high(self, adj_baseline, adj_high):
        yr = 2050
        base_val  = float(np.interp(yr, adj_baseline.years, adj_baseline.outage_rates))
        high_val  = float(np.interp(yr, adj_high.years, adj_high.outage_rates))
        assert base_val < high_val

    def test_moderate_between_baseline_and_high(self, adj_baseline, adj_moderate, adj_high):
        yr = 2050
        b = float(np.interp(yr, adj_baseline.years, adj_baseline.outage_rates))
        m = float(np.interp(yr, adj_moderate.years, adj_moderate.outage_rates))
        h = float(np.interp(yr, adj_high.years, adj_high.outage_rates))
        assert b < m < h

    def test_severe_drought_equals_high(self):
        """severe_drought uses the same SSP585 scale as high_physical."""
        adj_severe = build_physical_adjustments(
            start_year=2025, n_years=76, physical_scenario="severe_drought"
        )
        adj_h = build_physical_adjustments(
            start_year=2025, n_years=76, physical_scenario="high_physical"
        )
        np.testing.assert_allclose(
            adj_severe.outage_rates, adj_h.outage_rates, rtol=1e-10
        )

    def test_ssp_scale_ratios_approx(self, adj_baseline, adj_moderate, adj_high):
        """
        At 2100 the climate factor is 4.0 (scale = 1 + 3*ssp_scale).
        baseline scale=0.30 → factor ≈ 1 + 3*0.30 = 1.90
        moderate scale=0.60 → factor ≈ 1 + 3*0.60 = 2.80
        high     scale=1.00 → factor ≈ 1 + 3*1.00 = 4.00
        """
        yr = 2100
        b = float(np.interp(yr, adj_baseline.years, adj_baseline.outage_rates))
        m = float(np.interp(yr, adj_moderate.years, adj_moderate.outage_rates))
        h = float(np.interp(yr, adj_high.years, adj_high.outage_rates))
        base_rate = (6 / 20) * 0.10 * (24 / 8760)
        np.testing.assert_allclose(b / base_rate, 1.90, rtol=1e-6)
        np.testing.assert_allclose(m / base_rate, 2.80, rtol=1e-6)
        np.testing.assert_allclose(h / base_rate, 4.00, rtol=1e-6)


# ---------------------------------------------------------------------------
# get_adjustment_for_year()
# ---------------------------------------------------------------------------

class TestGetAdjustmentForYear:
    def test_returns_physical_adjustments_type(self, adj_high):
        result = adj_high.get_adjustment_for_year(2030)
        assert isinstance(result, PhysicalAdjustments)

    def test_year_in_range(self, adj_high):
        result = adj_high.get_adjustment_for_year(2050)
        np.testing.assert_allclose(result.outage_rate, _EXPECTED_PLANT_OUTAGE_2050, rtol=1e-3)
        assert result.capacity_derate == 0.0
        assert result.efficiency_loss == 0.0
        assert result.water_constrained_capacity == 1.0

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
# Climate factor interpolation
# ---------------------------------------------------------------------------

class TestClimateFactorInterpolation:
    def test_factor_at_2030_anchor(self, adj_high):
        """At 2030 the WILDFIRE climate factor anchor is 2.0 (ssp585 scale=1.0).
        Scaled factor = 1 + (2.0-1)*1.0 = 2.0
        plant_outage(2030) = base_plant * 2.0
        """
        base_plant = (6 / 20) * 0.10 * (24 / 8760)
        val = float(np.interp(2030, adj_high.years, adj_high.outage_rates))
        np.testing.assert_allclose(val, base_plant * 2.0, rtol=1e-6)

    def test_factor_held_constant_beyond_2100(self):
        """Climate factor is held constant (np.interp clamps) beyond the last anchor."""
        adj = build_physical_adjustments(start_year=2025, n_years=100)
        # Rate at 2100 and 2124 should be the same
        r_2100 = float(np.interp(2100, adj.years, adj.outage_rates))
        r_2124 = float(adj.outage_rates[-1])
        np.testing.assert_allclose(r_2124, r_2100, rtol=1e-6)

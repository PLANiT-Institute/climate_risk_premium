"""Tests for PLANiT → CRP pipeline integration."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from src.planit.config import PLANiTIntegrationConfig
from src.planit.cache import PLANiTResultCache
from src.planit.runner import PLANiTHazardResult
from src.planit.adapter import PLANiTAdapter, map_scenario, SCENARIO_MAP


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def default_config():
    return PLANiTIntegrationConfig()


@pytest.fixture
def adapter(default_config):
    return PLANiTAdapter(default_config)


def _make_result(hazard, scenario, year, value, unit="fraction", source="physrisk", **extra):
    return PLANiTHazardResult(
        hazard_type=hazard,
        scenario=scenario,
        year=year,
        asset="삼척화력발전소",
        value=value,
        std=0.0,
        unit=unit,
        source=source,
        **extra,
    )


# ===========================================================================
# Scenario Mapping Tests
# ===========================================================================

class TestScenarioMapping:
    def test_rcp85_maps_to_ssp585(self):
        assert map_scenario("RCP8.5") == "ssp585"

    def test_rcp45_maps_to_ssp245(self):
        assert map_scenario("RCP4.5") == "ssp245"

    def test_ssp126(self):
        assert map_scenario("SSP1-2.6") == "ssp126"

    def test_ssp245_passthrough(self):
        assert map_scenario("ssp245") == "ssp245"

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown scenario"):
            map_scenario("RCP2.6")

    def test_case_insensitive(self):
        assert map_scenario("rcp8.5") == "ssp585"
        assert map_scenario("Rcp4.5") == "ssp245"


class TestPlanitConfigEnvOverrides:
    def test_wildfire_probability_env_override(self, monkeypatch):
        monkeypatch.setenv("CRP_WILDFIRE_OUTAGE_PROBABILITY", "0.25")
        cfg = PLANiTIntegrationConfig()
        assert abs(cfg.wildfire_outage_probability - 0.25) < 1e-12


# ===========================================================================
# Conversion Formula Tests
# ===========================================================================

class TestConversionFormulas:
    """Test multi-hazard conversion (wildfire + drought + water_risk)."""

    def test_wildfire_event_probability_to_outage_rate(self, adapter, default_config):
        """Wildfire outage uses event-frequency probability method when metadata exists."""
        results = [
            _make_result(
                "wildfire",
                "ssp585",
                2050,
                1e9,
                unit="krw",
                source="climada",
                event_frequency_per_year=1.2,
            )
        ]
        adj = adapter.convert(results, 2050, "RCP8.5")
        expected = (
            1.2
            * default_config.wildfire_outage_probability
            * (default_config.wildfire_outage_duration_hours / default_config.hours_per_year)
        )
        assert abs(adj["outage_rate"] - expected) < 1e-12
        assert "wildfire_event_freq=1.200000/yr" in adj["notes"]

    def test_wildfire_event_count_infers_frequency(self, adapter, default_config):
        """Wildfire event_count/reference_years can infer annual frequency."""
        results = [
            _make_result(
                "wildfire",
                "ssp585",
                2050,
                1e9,
                unit="krw",
                source="climada",
                event_count=10,
                reference_years=20,
            )
        ]
        adj = adapter.convert(results, 2050, "RCP8.5")
        expected_freq = 0.5
        expected = (
            expected_freq
            * default_config.wildfire_outage_probability
            * (default_config.wildfire_outage_duration_hours / default_config.hours_per_year)
        )
        assert abs(adj["outage_rate"] - expected) < 1e-12
        assert "wildfire_freq_source=event_count/reference_years" in adj["notes"]

    def test_wildfire_requires_frequency_metadata(self, adapter):
        """Wildfire returns zero when frequency metadata is unavailable."""
        results = [_make_result("wildfire", "ssp585", 2050, 1e9, unit="krw", source="climada")]
        adj = adapter.convert(results, 2050, "RCP8.5")
        assert adj["outage_rate"] == 0.0
        assert "wildfire_frequency_missing" in adj["notes"]

    def test_drought_converts_to_capacity_derate(self, adapter):
        """Drought impact_mean → capacity_derate."""
        results = [_make_result("drought", "ssp585", 2050, 0.05)]
        adj = adapter.convert(results, 2050, "RCP8.5")
        assert abs(adj["capacity_derate"] - 0.05) < 1e-12

    def test_drought_distribution_expected_overrides_mean(self, adapter):
        """If distribution is present, drought uses probability-weighted expected impact."""
        results = [
            _make_result(
                "drought",
                "ssp585",
                2050,
                0.05,
                impact_bin_edges=[0.0, 0.2, 0.4],
                impact_probabilities=[0.5, 0.5],
            )
        ]
        adj = adapter.convert(results, 2050, "RCP8.5")
        # Expected = 0.1*0.5 + 0.3*0.5 = 0.2
        assert abs(adj["capacity_derate"] - 0.2) < 1e-12
        assert "drought_metric=distribution_expected" in adj["notes"]

    def test_water_risk_converts_to_water_constraint(self, adapter):
        """Water risk impact_mean → water_constrained_capacity = 1 - impact."""
        results = [_make_result("water_risk", "ssp585", 2050, 0.1)]
        adj = adapter.convert(results, 2050, "RCP8.5")
        assert abs(adj["water_constrained_capacity"] - 0.9) < 1e-12

    def test_water_distribution_expected_overrides_mean(self, adapter):
        """If distribution is present, water risk uses probability-weighted expected impact."""
        results = [
            _make_result(
                "water_risk",
                "ssp585",
                2050,
                0.1,
                impact_bin_edges=[0.0, 0.1, 0.3],
                impact_probabilities=[0.25, 0.75],
            )
        ]
        adj = adapter.convert(results, 2050, "RCP8.5")
        # Expected = 0.05*0.25 + 0.2*0.75 = 0.1625
        assert abs(adj["water_constrained_capacity"] - (1 - 0.1625)) < 1e-12
        assert "water_risk_metric=distribution_expected" in adj["notes"]

    def test_heatwave_not_active(self, adapter):
        """Heatwave not in active hazards - efficiency_loss stays 0.0."""
        results = [_make_result("heatwave", "ssp585", 2050, 0.02)]
        adj = adapter.convert(results, 2050, "RCP8.5")
        assert adj["efficiency_loss"] == 0.0

    def test_flood_not_active(self, adapter):
        """Flood not in active hazards - does not add to outage_rate."""
        results = [_make_result("flood", "ssp585", 2050, 0.01)]
        adj = adapter.convert(results, 2050, "RCP8.5")
        assert adj["outage_rate"] == 0.0

    def test_multi_hazard_conversion(self, adapter, default_config):
        """All active hazards are processed together."""
        wf_freq = 1.4
        results = [
            _make_result(
                "wildfire", "ssp585", 2050, 0.0, unit="krw", source="climada",
                event_frequency_per_year=wf_freq,
            ),
            _make_result("flood", "ssp585", 2050, 0.003),
            _make_result("drought", "ssp585", 2050, 0.01),
            _make_result("heatwave", "ssp585", 2050, 0.005),
            _make_result("water_risk", "ssp585", 2050, 0.08),
        ]
        adj = adapter.convert(results, 2050, "RCP8.5")

        expected_outage = (
            wf_freq
            * default_config.wildfire_outage_probability
            * (default_config.wildfire_outage_duration_hours / default_config.hours_per_year)
        )
        assert abs(adj["outage_rate"] - expected_outage) < 1e-10
        assert abs(adj["capacity_derate"] - 0.01) < 1e-12  # drought
        assert adj["efficiency_loss"] == 0.0  # heatwave not active
        assert abs(adj["water_constrained_capacity"] - 0.92) < 1e-12  # 1 - 0.08

    def test_notes_indicate_planit_source(self, adapter):
        """Notes indicate PLANiT source."""
        results = [
            _make_result(
                "wildfire", "ssp585", 2050, 0.0, unit="krw", source="climada",
                event_frequency_per_year=1.0,
            )
        ]
        adj = adapter.convert(results, 2050, "RCP8.5")
        assert "PLANiT" in adj["notes"]
        assert "ssp585" in adj["notes"]


# ===========================================================================
# Year Interpolation Tests (using wildfire - the only active hazard)
# ===========================================================================

class TestYearInterpolation:

    def test_exact_anchor_year(self, adapter, default_config):
        """Exact anchor year returns that value for wildfire."""
        wf_freq = 0.8
        results = [
            _make_result(
                "wildfire", "ssp585", 2050, 0.0, unit="krw", source="climada",
                event_frequency_per_year=wf_freq,
            )
        ]
        adj = adapter.convert(results, 2050, "RCP8.5")
        expected = (
            wf_freq
            * default_config.wildfire_outage_probability
            * (default_config.wildfire_outage_duration_hours / default_config.hours_per_year)
        )
        assert abs(adj["outage_rate"] - expected) < 1e-12

    def test_between_anchors(self, adapter, default_config):
        """Interpolates linearly between anchors for wildfire."""
        f_2030 = 0.5
        f_2050 = 1.5
        results = [
            _make_result(
                "wildfire", "ssp585", 2030, 0.0, unit="krw", source="climada",
                event_frequency_per_year=f_2030,
            ),
            _make_result(
                "wildfire", "ssp585", 2050, 0.0, unit="krw", source="climada",
                event_frequency_per_year=f_2050,
            ),
        ]
        adj = adapter.convert(results, 2040, "RCP8.5")
        expected_freq = 1.0
        expected = (
            expected_freq
            * default_config.wildfire_outage_probability
            * (default_config.wildfire_outage_duration_hours / default_config.hours_per_year)
        )
        assert abs(adj["outage_rate"] - expected) < 1e-12

    def test_before_first_anchor_blends_from_baseline(self, adapter, default_config):
        """Year before first anchor blends from baseline (2024) to first anchor."""
        f_2030 = 1.2
        results = [
            _make_result(
                "wildfire", "ssp585", 2030, 0.0, unit="krw", source="climada",
                event_frequency_per_year=f_2030,
            )
        ]
        csv_baseline = {"outage_rate": 0.0}
        adj = adapter.convert(results, 2027, "RCP8.5", csv_baseline)
        expected_freq = 0.6  # half-way from 0.0 to 1.2
        expected = (
            expected_freq
            * default_config.wildfire_outage_probability
            * (default_config.wildfire_outage_duration_hours / default_config.hours_per_year)
        )
        assert abs(adj["outage_rate"] - expected) < 1e-12

    def test_at_2024_returns_zero_baseline(self, adapter):
        """Year 2024 returns zero (PLANiT blending starts from 0 at 2024)."""
        results = [
            _make_result(
                "wildfire", "ssp585", 2030, 0.0, unit="krw", source="climada",
                event_frequency_per_year=1.0,
            )
        ]
        adj = adapter.convert(results, 2024, "RCP8.5")
        assert adj["outage_rate"] == 0.0

    def test_after_last_anchor_holds(self, adapter, default_config):
        """Year after last anchor holds the last value."""
        wf_freq = 1.7
        results = [
            _make_result(
                "wildfire", "ssp585", 2060, 0.0, unit="krw", source="climada",
                event_frequency_per_year=wf_freq,
            )
        ]
        adj = adapter.convert(results, 2070, "RCP8.5")
        expected = (
            wf_freq
            * default_config.wildfire_outage_probability
            * (default_config.wildfire_outage_duration_hours / default_config.hours_per_year)
        )
        assert abs(adj["outage_rate"] - expected) < 1e-12

    def test_yearly_arrays(self, adapter, default_config):
        """convert_yearly produces correct length and interpolated arrays."""
        f_2030 = 1.0
        f_2050 = 2.0
        results = [
            _make_result(
                "wildfire", "ssp585", 2030, 0.0, unit="krw", source="climada",
                event_frequency_per_year=f_2030,
            ),
            _make_result(
                "wildfire", "ssp585", 2050, 0.0, unit="krw", source="climada",
                event_frequency_per_year=f_2050,
            ),
        ]
        arrays = adapter.convert_yearly(results, 2024, 2060, "RCP8.5")
        assert len(arrays["years"]) == 37  # 2024..2060 inclusive
        assert arrays["outage_rates"][0] == 0.0  # baseline at 2024
        expected_freq = 1.5
        expected = (
            expected_freq
            * default_config.wildfire_outage_probability
            * (default_config.wildfire_outage_duration_hours / default_config.hours_per_year)
        )
        assert abs(arrays["outage_rates"][16] - expected) < 1e-12

    def test_duplicate_year_rows_are_averaged(self, default_config):
        """When multiple assets share same year/scenario, values are averaged."""
        cfg = PLANiTIntegrationConfig(**default_config.__dict__)
        cfg.target_asset = ""  # include all assets
        adapter = PLANiTAdapter(cfg)
        results = [
            _make_result("drought", "ssp585", 2050, 0.01),
            _make_result("drought", "ssp585", 2050, 0.03),
        ]
        adj = adapter.convert(results, 2050, "RCP8.5")
        assert abs(adj["capacity_derate"] - 0.02) < 1e-12


# ===========================================================================
# Fallback Behavior Tests
# ===========================================================================

class TestFallback:

    def test_no_wildfire_uses_csv_outage_fallback(self, adapter):
        """If no wildfire data, CSV baseline outage_rate is used."""
        results = []  # No PLANiT data
        csv_baseline = {
            "outage_rate": 0.001,
        }
        adj = adapter.convert(results, 2050, "RCP8.5", csv_baseline)
        # Only outage_rate uses CSV fallback
        assert adj["outage_rate"] == 0.001
        # Other fields always return defaults (removed hazards)
        assert adj["capacity_derate"] == 0.0
        assert adj["efficiency_loss"] == 0.0
        assert adj["water_constrained_capacity"] == 1.0

    def test_no_data_returns_defaults(self, adapter):
        """No PLANiT data and no CSV baseline returns default values."""
        results = []  # No PLANiT data
        adj = adapter.convert(results, 2050, "RCP8.5")
        assert adj["outage_rate"] == 0.0
        assert adj["capacity_derate"] == 0.0
        assert adj["efficiency_loss"] == 0.0
        assert adj["water_constrained_capacity"] == 1.0

    def test_wildfire_scenario_mismatch_uses_fallback(self, adapter):
        """Wildfire scenario mismatch uses deterministic fallback SSP."""
        results = [
            _make_result(
                "wildfire", "ssp245", 2050, 0.0, unit="krw", source="climada",
                event_frequency_per_year=1.0,
            )
        ]
        adj = adapter.convert(results, 2050, "RCP8.5")
        assert adj["outage_rate"] > 0.0
        assert "wildfire_scenario_fallback=ssp245" in adj["notes"]
        assert "wildfire_source_scenario=ssp245" in adj["notes"]

    def test_non_wildfire_scenario_mismatch_keeps_defaults(self, adapter):
        """Drought and water_risk do not use cross-SSP fallback."""
        results = [_make_result("drought", "ssp245", 2050, 0.2)]
        adj = adapter.convert(results, 2050, "RCP8.5")
        assert adj["capacity_derate"] == 0.0

    def test_notes_indicate_csv_fallback(self, adapter):
        """Notes indicate csv_fallback when no wildfire data."""
        results = []  # No wildfire data
        csv_baseline = {"outage_rate": 0.001}
        adj = adapter.convert(results, 2050, "RCP8.5", csv_baseline)
        assert "wildfire=csv_fallback" in adj["notes"]


# ===========================================================================
# Cache Tests
# ===========================================================================

class TestCache:

    def test_put_and_get(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = PLANiTResultCache(cache_dir=tmpdir, ttl_hours=1.0)
            data = {"value": 42, "unit": "krw"}
            cache.put("wildfire", "ssp585", 2050, data)
            result = cache.get("wildfire", "ssp585", 2050)
            assert result == data

    def test_miss_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = PLANiTResultCache(cache_dir=tmpdir, ttl_hours=1.0)
            assert cache.get("wildfire", "ssp585", 2050) is None

    def test_invalidate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = PLANiTResultCache(cache_dir=tmpdir, ttl_hours=1.0)
            cache.put("wildfire", "ssp585", 2050, {"v": 1})
            cache.put("drought", "ssp585", 2050, {"v": 2})
            count = cache.invalidate(hazard="wildfire")
            assert count == 1
            assert cache.get("wildfire", "ssp585", 2050) is None
            assert cache.get("drought", "ssp585", 2050) is not None

    def test_stale_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = PLANiTResultCache(cache_dir=tmpdir, ttl_hours=0.0)  # instant expiry
            cache.put("wildfire", "ssp585", 2050, {"v": 1})
            # TTL=0 means it's already stale
            assert cache.get("wildfire", "ssp585", 2050) is None


# ===========================================================================
# Config Tests
# ===========================================================================

class TestConfig:

    def test_defaults_all_hazards(self):
        """Config defaults to all available hazards."""
        cfg = PLANiTIntegrationConfig()
        assert cfg.target_asset == "삼척화력발전소"
        assert cfg.planit_hazards == ["wildfire", "drought", "water_risk"]
        assert cfg.csv_fallback_hazards == []
        assert cfg.wildfire_outage_method == "event_probability"

    def test_custom_config(self):
        cfg = PLANiTIntegrationConfig(
            wildfire_outage_probability=0.2,
        )
        assert cfg.wildfire_outage_probability == 0.2

    def test_wildfire_with_custom_probability(self):
        """Wildfire conversion respects custom outage probability."""
        config = PLANiTIntegrationConfig(wildfire_outage_probability=0.25)
        adapter = PLANiTAdapter(config)
        results = [
            _make_result(
                "wildfire", "ssp585", 2050, 0.0, unit="krw", source="climada",
                event_frequency_per_year=1.0,
            )
        ]
        adj = adapter.convert(results, 2050, "RCP8.5")
        expected = 0.25 * (config.wildfire_outage_duration_hours / config.hours_per_year)
        assert abs(adj["outage_rate"] - expected) < 1e-12


# ===========================================================================
# PLANiTHazardResult Tests
# ===========================================================================

class TestHazardResult:

    def test_to_dict_roundtrip(self):
        r = _make_result("wildfire", "ssp585", 2050, 1e9, unit="krw", source="climada")
        d = r.to_dict()
        r2 = PLANiTHazardResult(**d)
        assert r2.hazard_type == r.hazard_type
        assert r2.value == r.value


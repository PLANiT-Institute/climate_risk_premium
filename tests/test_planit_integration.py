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


def _make_result(hazard, scenario, year, value, unit="fraction", source="physrisk"):
    return PLANiTHazardResult(
        hazard_type=hazard,
        scenario=scenario,
        year=year,
        asset="삼척화력발전소",
        value=value,
        std=0.0,
        unit=unit,
        source=source,
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


# ===========================================================================
# Conversion Formula Tests
# ===========================================================================

class TestConversionFormulas:
    """Test multi-hazard conversion (wildfire + drought + water_risk)."""

    def test_wildfire_aai_to_outage_rate(self, adapter, default_config):
        """Wildfire AAI (KRW) → outage_rate = AAI / total_asset_value."""
        aai = 1e9  # 1 billion KRW
        results = [_make_result("wildfire", "ssp585", 2050, aai, unit="krw", source="climada")]
        adj = adapter.convert(results, 2050, "RCP8.5")
        expected = aai / default_config.total_asset_value_krw
        assert abs(adj["outage_rate"] - expected) < 1e-12

    def test_drought_converts_to_capacity_derate(self, adapter):
        """Drought impact_mean → capacity_derate."""
        results = [_make_result("drought", "ssp585", 2050, 0.05)]
        adj = adapter.convert(results, 2050, "RCP8.5")
        assert abs(adj["capacity_derate"] - 0.05) < 1e-12

    def test_water_risk_converts_to_water_constraint(self, adapter):
        """Water risk impact_mean → water_constrained_capacity = 1 - impact."""
        results = [_make_result("water_risk", "ssp585", 2050, 0.1)]
        adj = adapter.convert(results, 2050, "RCP8.5")
        assert abs(adj["water_constrained_capacity"] - 0.9) < 1e-12

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
        aai = 2e9
        results = [
            _make_result("wildfire", "ssp585", 2050, aai, unit="krw", source="climada"),
            _make_result("flood", "ssp585", 2050, 0.003),
            _make_result("drought", "ssp585", 2050, 0.01),
            _make_result("heatwave", "ssp585", 2050, 0.005),
            _make_result("water_risk", "ssp585", 2050, 0.08),
        ]
        adj = adapter.convert(results, 2050, "RCP8.5")

        expected_outage = aai / default_config.total_asset_value_krw
        assert abs(adj["outage_rate"] - expected_outage) < 1e-10
        assert abs(adj["capacity_derate"] - 0.01) < 1e-12  # drought
        assert adj["efficiency_loss"] == 0.0  # heatwave not active
        assert abs(adj["water_constrained_capacity"] - 0.92) < 1e-12  # 1 - 0.08

    def test_notes_indicate_planit_source(self, adapter):
        """Notes indicate PLANiT source."""
        aai = 1e9
        results = [_make_result("wildfire", "ssp585", 2050, aai, unit="krw", source="climada")]
        adj = adapter.convert(results, 2050, "RCP8.5")
        assert "PLANiT" in adj["notes"]
        assert "ssp585" in adj["notes"]


# ===========================================================================
# Year Interpolation Tests (using wildfire - the only active hazard)
# ===========================================================================

class TestYearInterpolation:

    def test_exact_anchor_year(self, adapter, default_config):
        """Exact anchor year returns that value for wildfire."""
        aai = 2e9  # 2 billion KRW
        results = [_make_result("wildfire", "ssp585", 2050, aai, unit="krw", source="climada")]
        adj = adapter.convert(results, 2050, "RCP8.5")
        expected = aai / default_config.total_asset_value_krw
        assert abs(adj["outage_rate"] - expected) < 1e-12

    def test_between_anchors(self, adapter, default_config):
        """Interpolates linearly between anchors for wildfire."""
        aai_2030 = 1e9
        aai_2050 = 3e9
        results = [
            _make_result("wildfire", "ssp585", 2030, aai_2030, unit="krw", source="climada"),
            _make_result("wildfire", "ssp585", 2050, aai_2050, unit="krw", source="climada"),
        ]
        adj = adapter.convert(results, 2040, "RCP8.5")
        # midpoint: (1e9 + 3e9) / 2 = 2e9
        expected = 2e9 / default_config.total_asset_value_krw
        assert abs(adj["outage_rate"] - expected) < 1e-12

    def test_before_first_anchor_blends_from_baseline(self, adapter, default_config):
        """Year before first anchor blends from baseline (2024) to first anchor."""
        aai_2030 = 1.2e9
        results = [_make_result("wildfire", "ssp585", 2030, aai_2030, unit="krw", source="climada")]
        csv_baseline = {"outage_rate": 0.0}
        adj = adapter.convert(results, 2027, "RCP8.5", csv_baseline)
        # weight = (2027 - 2024) / (2030 - 2024) = 3/6 = 0.5
        # value = 0.0 + 0.5 * (aai_2030 - 0.0) = 0.6e9
        expected = 0.6e9 / default_config.total_asset_value_krw
        assert abs(adj["outage_rate"] - expected) < 1e-12

    def test_at_2024_returns_zero_baseline(self, adapter):
        """Year 2024 returns zero (PLANiT blending starts from 0 at 2024)."""
        aai = 1e9
        results = [_make_result("wildfire", "ssp585", 2030, aai, unit="krw", source="climada")]
        adj = adapter.convert(results, 2024, "RCP8.5")
        assert adj["outage_rate"] == 0.0

    def test_after_last_anchor_holds(self, adapter, default_config):
        """Year after last anchor holds the last value."""
        aai = 4e9
        results = [_make_result("wildfire", "ssp585", 2060, aai, unit="krw", source="climada")]
        adj = adapter.convert(results, 2070, "RCP8.5")
        expected = aai / default_config.total_asset_value_krw
        assert abs(adj["outage_rate"] - expected) < 1e-12

    def test_yearly_arrays(self, adapter, default_config):
        """convert_yearly produces correct length and interpolated arrays."""
        aai_2030 = 1e9
        aai_2050 = 2e9
        results = [
            _make_result("wildfire", "ssp585", 2030, aai_2030, unit="krw", source="climada"),
            _make_result("wildfire", "ssp585", 2050, aai_2050, unit="krw", source="climada"),
        ]
        arrays = adapter.convert_yearly(results, 2024, 2060, "RCP8.5")
        assert len(arrays["years"]) == 37  # 2024..2060 inclusive
        assert arrays["outage_rates"][0] == 0.0  # baseline at 2024
        # 2040 is index 16 (2040 - 2024), midpoint value = 1.5e9
        expected = 1.5e9 / default_config.total_asset_value_krw
        assert abs(arrays["outage_rates"][16] - expected) < 1e-12


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

    def test_scenario_mismatch_falls_through(self, adapter):
        """Results for wrong scenario are ignored."""
        results = [_make_result("wildfire", "ssp245", 2050, 1e9, unit="krw", source="climada")]
        adj = adapter.convert(results, 2050, "RCP8.5")
        # ssp245 doesn't match RCP8.5 → ssp585, so no data → defaults to 0
        assert adj["outage_rate"] == 0.0

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
        assert cfg.total_asset_value_krw == 4.879e12
        assert cfg.target_asset == "삼척화력발전소"
        assert cfg.planit_hazards == ["wildfire", "drought", "water_risk"]
        assert cfg.csv_fallback_hazards == []

    def test_custom_config(self):
        cfg = PLANiTIntegrationConfig(
            total_asset_value_krw=1e12,
        )
        assert cfg.total_asset_value_krw == 1e12

    def test_wildfire_with_custom_asset_value(self, default_config):
        """Wildfire conversion respects custom asset value."""
        config = PLANiTIntegrationConfig(total_asset_value_krw=1e12)
        adapter = PLANiTAdapter(config)
        aai = 1e9  # 1 billion KRW
        results = [_make_result("wildfire", "ssp585", 2050, aai, unit="krw", source="climada")]
        adj = adapter.convert(results, 2050, "RCP8.5")
        expected = aai / 1e12  # 0.001
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


# ===========================================================================
# Integration: physical.py functions (import test only — PLANiT not installed)
# ===========================================================================

class TestPhysicalIntegration:

    def test_get_physical_risk_from_planit_fallback(self):
        """Without PLANiT runner, should fall back to engine-based risk."""
        from src.risk.physical import get_physical_risk_from_planit
        from src.planit.config import PLANiTIntegrationConfig
        # Disable PLANiT to force fallback
        cfg = PLANiTIntegrationConfig(enabled=False)
        adj = get_physical_risk_from_planit(year=2040, scenario="RCP8.5", config=cfg)
        assert adj.outage_rate >= 0
        assert 0 <= adj.water_constrained_capacity <= 1.0

    def test_create_yearly_from_planit_fallback(self):
        """With PLANiT disabled, returns engine-based yearly adjustments."""
        from src.risk.physical import create_yearly_physical_adjustments_from_planit
        from src.planit.config import PLANiTIntegrationConfig
        cfg = PLANiTIntegrationConfig(enabled=False)
        yearly = create_yearly_physical_adjustments_from_planit(
            2024, 2060, "RCP8.5", config=cfg
        )
        assert len(yearly.years) == 37
        assert all(yearly.outage_rates >= 0)
        assert all(yearly.water_constraints <= 1.0)


# ===========================================================================
# Vulnerability Function Tests (explicit damage formulas)
# ===========================================================================

class TestWildfireVulnerability:
    """Test explicit wildfire vulnerability function (CLIMADA ImpfWildfire)."""

    def test_damage_ratio_at_zero_fwi(self):
        """FWI=0 should give 0 damage."""
        from src.planit.vulnerability import WildfireVulnerability
        vuln = WildfireVulnerability()
        assert vuln.calculate_damage_ratio(0) == 0.0

    def test_damage_ratio_at_i_half(self):
        """FWI=i_half should give 50% damage."""
        from src.planit.vulnerability import WildfireVulnerability
        vuln = WildfireVulnerability(i_half=409.5)
        damage = vuln.calculate_damage_ratio(409.5)
        assert abs(damage - 0.5) < 0.01

    def test_damage_ratio_increases_with_fwi(self):
        """Higher FWI should give higher damage."""
        from src.planit.vulnerability import WildfireVulnerability
        vuln = WildfireVulnerability()
        d100 = vuln.calculate_damage_ratio(100)
        d500 = vuln.calculate_damage_ratio(500)
        d1000 = vuln.calculate_damage_ratio(1000)
        assert d100 < d500 < d1000

    def test_damage_ratio_approaches_one(self):
        """Very high FWI should approach 100% damage."""
        from src.planit.vulnerability import WildfireVulnerability
        vuln = WildfireVulnerability()
        assert vuln.calculate_damage_ratio(10000) > 0.99

    def test_aai_calculation(self):
        """AAI calculation with event distribution."""
        from src.planit.vulnerability import WildfireVulnerability
        vuln = WildfireVulnerability()
        # 10% chance of FWI=500 event
        aai = vuln.calculate_aai(1e12, {500: 0.10})
        # damage_ratio at FWI=500 ≈ 0.60
        expected = 1e12 * vuln.calculate_damage_ratio(500) * 0.10
        assert abs(aai - expected) < 1e-6

    def test_aai_to_outage_rate_conversion(self):
        """AAI to outage_rate conversion."""
        from src.planit.vulnerability import wildfire_aai_to_outage_rate
        rate = wildfire_aai_to_outage_rate(1e9, 4.879e12)
        expected = 1e9 / 4.879e12
        assert abs(rate - expected) < 1e-15

    def test_aai_to_outage_rate_zero_asset_value(self):
        """Zero asset value should return 0."""
        from src.planit.vulnerability import wildfire_aai_to_outage_rate
        assert wildfire_aai_to_outage_rate(1e9, 0) == 0.0

    def test_damage_curve_output(self):
        """Damage curve returns valid data points."""
        from src.planit.vulnerability import WildfireVulnerability
        vuln = WildfireVulnerability()
        curve = vuln.get_damage_curve()
        assert "fwi" in curve
        assert "damage_ratio" in curve
        assert len(curve["fwi"]) == len(curve["damage_ratio"])
        assert all(0 <= d <= 1 for d in curve["damage_ratio"])


class TestCSVLoader:
    """Test PLANiTRunner.load_results_from_csv()."""

    def test_loads_results_from_csv(self):
        """Loads wildfire, drought, and water_risk from PLANiT result CSVs."""
        from src.planit.runner import PLANiTRunner
        from pathlib import Path
        results_dir = str(Path(__file__).parent.parent / "Physicalrisk_PLANiT/data/results")
        results = PLANiTRunner.load_results_from_csv(results_dir)
        hazard_types = {r.hazard_type for r in results}
        assert "wildfire" in hazard_types
        assert "drought" in hazard_types
        assert "water_risk" in hazard_types
        assert len(results) > 0

    def test_wildfire_has_krw_unit(self):
        """Wildfire results use KRW units."""
        from src.planit.runner import PLANiTRunner
        from pathlib import Path
        results_dir = str(Path(__file__).parent.parent / "Physicalrisk_PLANiT/data/results")
        results = PLANiTRunner.load_results_from_csv(results_dir)
        wildfire = [r for r in results if r.hazard_type == "wildfire"]
        assert all(r.unit == "krw" for r in wildfire)
        assert all(r.source == "climada" for r in wildfire)

    def test_drought_has_fraction_unit(self):
        """Drought results use fraction units."""
        from src.planit.runner import PLANiTRunner
        from pathlib import Path
        results_dir = str(Path(__file__).parent.parent / "Physicalrisk_PLANiT/data/results")
        results = PLANiTRunner.load_results_from_csv(results_dir)
        drought = [r for r in results if r.hazard_type == "drought"]
        assert all(r.unit == "fraction" for r in drought)
        assert all(r.source == "physrisk" for r in drought)

    def test_wildfire_replicated_across_anchors(self):
        """Wildfire AAI replicated across all anchor years."""
        from src.planit.runner import PLANiTRunner
        from pathlib import Path
        results_dir = str(Path(__file__).parent.parent / "Physicalrisk_PLANiT/data/results")
        results = PLANiTRunner.load_results_from_csv(results_dir)
        wf_ssp126 = [r for r in results if r.hazard_type == "wildfire" and r.scenario == "ssp126"]
        years = {r.year for r in wf_ssp126}
        assert years == {2030, 2040, 2050, 2060}


# ===========================================================================
# Hybrid Temperature Model Integration Tests
# ===========================================================================

class TestHybridTemperatureIntegration:
    """Test hybrid mode with TemperatureModel for efficiency_loss."""

    def test_efficiency_loss_nonzero_for_rcp85_2050(self):
        """RCP8.5 2050 should have efficiency_loss > 0 from TemperatureModel."""
        from src.risk.physical import get_physical_risk_from_planit
        from src.planit.config import PLANiTIntegrationConfig
        cfg = PLANiTIntegrationConfig(enabled=False)  # Use fallback
        adj = get_physical_risk_from_planit(year=2050, scenario="RCP8.5", config=cfg)
        # Temperature model for RCP8.5 2050: ~0.78% efficiency loss
        assert adj.efficiency_loss > 0.005, f"Expected efficiency_loss > 0.5%, got {adj.efficiency_loss:.4f}"
        assert "temp_eff=" in adj.notes

    def test_efficiency_loss_nonzero_for_rcp45_2050(self):
        """RCP4.5 2050 should also have nonzero efficiency_loss."""
        from src.risk.physical import get_physical_risk_from_planit
        from src.planit.config import PLANiTIntegrationConfig
        cfg = PLANiTIntegrationConfig(enabled=False)
        adj = get_physical_risk_from_planit(year=2050, scenario="RCP4.5", config=cfg)
        # Temperature model for RCP4.5 2050: lower than RCP8.5 but still > 0
        assert adj.efficiency_loss > 0.003, f"Expected efficiency_loss > 0.3%, got {adj.efficiency_loss:.4f}"

    def test_efficiency_loss_increases_with_year(self):
        """Efficiency loss should increase over time (more warming)."""
        from src.risk.physical import get_physical_risk_from_planit
        from src.planit.config import PLANiTIntegrationConfig
        cfg = PLANiTIntegrationConfig(enabled=False)
        adj_2030 = get_physical_risk_from_planit(year=2030, scenario="RCP8.5", config=cfg)
        adj_2050 = get_physical_risk_from_planit(year=2050, scenario="RCP8.5", config=cfg)
        assert adj_2050.efficiency_loss > adj_2030.efficiency_loss, \
            f"Expected 2050 ({adj_2050.efficiency_loss:.4f}) > 2030 ({adj_2030.efficiency_loss:.4f})"

    def test_rcp85_higher_than_rcp45(self):
        """RCP8.5 should have higher efficiency_loss than RCP4.5 for same year."""
        from src.risk.physical import get_physical_risk_from_planit
        from src.planit.config import PLANiTIntegrationConfig
        cfg = PLANiTIntegrationConfig(enabled=False)
        adj_rcp45 = get_physical_risk_from_planit(year=2050, scenario="RCP4.5", config=cfg)
        adj_rcp85 = get_physical_risk_from_planit(year=2050, scenario="RCP8.5", config=cfg)
        assert adj_rcp85.efficiency_loss > adj_rcp45.efficiency_loss, \
            f"Expected RCP8.5 ({adj_rcp85.efficiency_loss:.4f}) > RCP4.5 ({adj_rcp45.efficiency_loss:.4f})"

    def test_baseline_year_has_minimal_efficiency_loss(self):
        """2024 baseline should have near-zero efficiency loss."""
        from src.risk.physical import get_physical_risk_from_planit
        from src.planit.config import PLANiTIntegrationConfig
        cfg = PLANiTIntegrationConfig(enabled=False)
        adj = get_physical_risk_from_planit(year=2024, scenario="RCP8.5", config=cfg)
        # Baseline has delta_t_air=0, so efficiency loss should be minimal
        assert adj.efficiency_loss < 0.002, f"Expected baseline efficiency_loss < 0.2%, got {adj.efficiency_loss:.4f}"

    def test_yearly_adjustments_have_nonzero_efficiency_losses(self):
        """Yearly adjustments should have increasing efficiency_losses from TemperatureModel."""
        from src.risk.physical import create_yearly_physical_adjustments_from_planit
        from src.planit.config import PLANiTIntegrationConfig
        cfg = PLANiTIntegrationConfig(enabled=False)
        yearly = create_yearly_physical_adjustments_from_planit(
            2024, 2060, "RCP8.5", config=cfg
        )
        # Check that efficiency_losses are non-zero for later years
        assert yearly.efficiency_losses[-1] > yearly.efficiency_losses[0], \
            "Expected efficiency_losses to increase over time"
        # 2050 is index 26 (2050 - 2024)
        assert yearly.efficiency_losses[26] > 0.005, \
            f"Expected 2050 efficiency_loss > 0.5%, got {yearly.efficiency_losses[26]:.4f}"

    def test_yearly_scenario_name_mentions_temperature_model(self):
        """Scenario name should indicate TemperatureModel is used."""
        from src.risk.physical import create_yearly_physical_adjustments_from_planit
        from src.planit.config import PLANiTIntegrationConfig
        cfg = PLANiTIntegrationConfig(enabled=False)
        yearly = create_yearly_physical_adjustments_from_planit(
            2024, 2060, "RCP8.5", config=cfg
        )
        assert "TemperatureModel" in yearly.scenario_name

    def test_temperature_model_direct_calculation(self):
        """Verify TemperatureModel directly returns expected values."""
        from src.models.physical.temperature import TemperatureModel, CoolingType
        model = TemperatureModel(rcp="RCP8.5", cooling_type=CoolingType.ONCE_THROUGH)
        result = model.calculate_efficiency_loss(2050)
        # Expected: ~0.78% total derate for RCP8.5 2050 (based on KMA projections)
        assert 0.005 < result.total_derate < 0.02, \
            f"Expected total_derate ~0.78%, got {result.total_derate:.4f}"
        assert result.mean_temp_derate > 0
        assert result.heat_wave_derate > 0

"""
Tests for TemperatureModel (src/models/physical/temperature.py).

Migrated from test_planit_integration.py::TestHybridTemperatureIntegration
and rewritten to test TemperatureModel directly (PLANiT wrapper removed).
"""
import pytest
from src.models.physical.temperature import (
    TemperatureModel,
    CoolingType,
    ALL_TEMPERATURE_PROJECTIONS,
    TEMPERATURE_PROJECTIONS_RCP45,
    TEMPERATURE_PROJECTIONS_RCP85,
)


class TestTemperatureModelEfficiencyLoss:
    """Core efficiency-loss calculations for once-through coastal plant."""

    def test_rcp85_2050_efficiency_loss_in_expected_range(self):
        """RCP8.5 2050: total derate ~0.78% (KMA projections, ONCE_THROUGH)."""
        model = TemperatureModel(rcp="RCP8.5", cooling_type=CoolingType.ONCE_THROUGH)
        result = model.calculate_efficiency_loss(2050)
        assert 0.005 < result.total_derate < 0.02, (
            f"Expected total_derate ~0.78%, got {result.total_derate:.4f}"
        )
        assert result.mean_temp_derate > 0
        assert result.heat_wave_derate > 0

    def test_efficiency_loss_nonzero_rcp85_2050(self):
        """RCP8.5 2050 efficiency_loss must exceed 0.5%."""
        model = TemperatureModel(rcp="RCP8.5", cooling_type=CoolingType.ONCE_THROUGH)
        result = model.calculate_efficiency_loss(2050)
        assert result.total_derate > 0.005, (
            f"Expected efficiency_loss > 0.5%, got {result.total_derate:.4f}"
        )

    def test_efficiency_loss_nonzero_rcp45_2050(self):
        """RCP4.5 2050 efficiency_loss must exceed 0.3%."""
        model = TemperatureModel(rcp="RCP4.5", cooling_type=CoolingType.ONCE_THROUGH)
        result = model.calculate_efficiency_loss(2050)
        assert result.total_derate > 0.003, (
            f"Expected efficiency_loss > 0.3%, got {result.total_derate:.4f}"
        )

    def test_baseline_year_minimal_efficiency_loss(self):
        """2024 baseline: delta_t_air=0 → efficiency loss should be near-zero."""
        model = TemperatureModel(rcp="RCP8.5", cooling_type=CoolingType.ONCE_THROUGH)
        result = model.calculate_efficiency_loss(2024)
        assert result.total_derate < 0.002, (
            f"Expected baseline efficiency_loss < 0.2%, got {result.total_derate:.4f}"
        )


class TestTemperatureModelScenarioDifferentiation:
    """Scenario and temporal ordering properties."""

    def test_efficiency_loss_increases_over_time(self):
        """2050 derate must exceed 2030 derate under RCP8.5."""
        model = TemperatureModel(rcp="RCP8.5", cooling_type=CoolingType.ONCE_THROUGH)
        loss_2030 = model.calculate_efficiency_loss(2030).total_derate
        loss_2050 = model.calculate_efficiency_loss(2050).total_derate
        assert loss_2050 > loss_2030, (
            f"Expected 2050 ({loss_2050:.4f}) > 2030 ({loss_2030:.4f})"
        )

    def test_rcp85_higher_than_rcp45_at_2050(self):
        """RCP8.5 must give higher efficiency loss than RCP4.5 at 2050."""
        loss_rcp45 = TemperatureModel("RCP4.5", CoolingType.ONCE_THROUGH).calculate_efficiency_loss(2050).total_derate
        loss_rcp85 = TemperatureModel("RCP8.5", CoolingType.ONCE_THROUGH).calculate_efficiency_loss(2050).total_derate
        assert loss_rcp85 > loss_rcp45, (
            f"Expected RCP8.5 ({loss_rcp85:.4f}) > RCP4.5 ({loss_rcp45:.4f})"
        )

    def test_rcp85_higher_than_rcp45_at_2030(self):
        """RCP8.5 must give higher efficiency loss than RCP4.5 at 2030."""
        loss_rcp45 = TemperatureModel("RCP4.5", CoolingType.ONCE_THROUGH).calculate_efficiency_loss(2030).total_derate
        loss_rcp85 = TemperatureModel("RCP8.5", CoolingType.ONCE_THROUGH).calculate_efficiency_loss(2030).total_derate
        assert loss_rcp85 > loss_rcp45

    @pytest.mark.parametrize("scenario", ["RCP4.5", "RCP8.5"])
    def test_monotonic_increase_across_decades(self, scenario):
        """Efficiency loss must be monotonically increasing across anchor years."""
        model = TemperatureModel(rcp=scenario, cooling_type=CoolingType.ONCE_THROUGH)
        years = [2024, 2030, 2050, 2100]
        losses = [model.calculate_efficiency_loss(y).total_derate for y in years]
        for i in range(len(losses) - 1):
            assert losses[i + 1] > losses[i], (
                f"{scenario}: loss[{years[i+1]}]={losses[i+1]:.4f} not > "
                f"loss[{years[i]}]={losses[i]:.4f}"
            )


class TestTemperatureModelResultFields:
    """Output contract: result fields, types, and bounds."""

    def test_result_has_expected_fields(self):
        model = TemperatureModel("RCP8.5", CoolingType.ONCE_THROUGH)
        result = model.calculate_efficiency_loss(2050)
        assert hasattr(result, "total_derate")
        assert hasattr(result, "mean_temp_derate")
        assert hasattr(result, "heat_wave_derate")
        assert hasattr(result, "cooling_water_derate")
        assert hasattr(result, "year")
        assert hasattr(result, "scenario")

    def test_total_derate_is_sum_of_components(self):
        model = TemperatureModel("RCP8.5", CoolingType.ONCE_THROUGH)
        result = model.calculate_efficiency_loss(2050)
        expected = result.mean_temp_derate + result.heat_wave_derate + result.cooling_water_derate
        assert result.total_derate == pytest.approx(expected, rel=1e-6)

    @pytest.mark.parametrize("year", [2024, 2030, 2050, 2100])
    @pytest.mark.parametrize("scenario", ["RCP4.5", "RCP8.5"])
    def test_total_derate_non_negative(self, scenario, year):
        model = TemperatureModel(rcp=scenario, cooling_type=CoolingType.ONCE_THROUGH)
        result = model.calculate_efficiency_loss(year)
        assert result.total_derate >= 0.0

    def test_unknown_scenario_falls_back_gracefully(self):
        """Unknown RCP falls back to RCP8.5 projections (TemperatureModel default)."""
        model_unknown = TemperatureModel(rcp="UNKNOWN", cooling_type=CoolingType.ONCE_THROUGH)
        model_rcp85 = TemperatureModel(rcp="RCP8.5", cooling_type=CoolingType.ONCE_THROUGH)
        assert model_unknown.calculate_efficiency_loss(2050).total_derate == pytest.approx(
            model_rcp85.calculate_efficiency_loss(2050).total_derate
        )


class TestTemperatureModelProjectionData:
    """Sanity-check projection anchor data (KMA-sourced)."""

    def test_rcp85_2050_delta_t_air_positive(self):
        model = TemperatureModel("RCP8.5")
        assert model.get_delta_t(2050) > 0

    def test_rcp85_delta_t_increases_over_time(self):
        model = TemperatureModel("RCP8.5")
        assert model.get_delta_t(2050) > model.get_delta_t(2030)
        assert model.get_delta_t(2100) > model.get_delta_t(2050)

    def test_all_projections_dict_contains_both_scenarios(self):
        assert "RCP4.5" in ALL_TEMPERATURE_PROJECTIONS
        assert "RCP8.5" in ALL_TEMPERATURE_PROJECTIONS

    def test_projections_have_four_anchors(self):
        for scenario, projections in ALL_TEMPERATURE_PROJECTIONS.items():
            assert len(projections) == 4, (
                f"{scenario}: expected 4 anchor years, got {len(projections)}"
            )

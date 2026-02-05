"""
Comprehensive test suite for enhanced physical risk engine.

Tests cover:
- Hazard intensity calculations
- Damage function applications
- Vulnerability assessment
- Physical impact calculations
- Time series analysis
- Edge cases and error handling
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from src.risk.physical.enhanced_engine import (
    HazardType,
    HazardIntensity,
    AssetExposure,
    DamageFunction,
    PhysicalImpact,
    HazardModel,
    VulnerabilityModel,
    EnhancedPhysicalRiskEngine,
    get_enhanced_physical_risk_engine,
)
from src.risk.core import PlantCharacteristics, ScenarioParameters, RiskType


class TestHazardType:
    """Test HazardType enum functionality."""
    
    def test_hazard_type_properties(self):
        """Test hazard type enumeration."""
        assert HazardType.WILDFIRE.value == "wildfire"
        assert HazardType.FLOOD.value == "flood"
        assert HazardType.DROUGHT.value == "drought"
        assert HazardType.HEAT.value == "heat"
        assert HazardType.WATER_SCARCITY.value == "water_scarcity"


class TestHazardIntensity:
    """Test HazardIntensity dataclass."""
    
    def test_severity_score_calculation(self):
        """Test severity score conversion for different hazard types."""
        # Wildfire severity (0-10 scale)
        wildfire = HazardIntensity(
            hazard_type=HazardType.WILDFIRE,
            intensity_value=5.0,
            intensity_unit="index",
            frequency=0.1
        )
        assert wildfire.get_severity_score() == 0.5  # 5/10
        
        # Flood depth (meters)
        flood = HazardIntensity(
            hazard_type=HazardType.FLOOD,
            intensity_value=2.5,
            intensity_unit="meters",
            frequency=0.05
        )
        assert flood.get_severity_score() == 0.5  # 2.5/5
        
        # Heat temperature (above 20°C baseline)
        heat = HazardIntensity(
            hazard_type=HazardType.HEAT,
            intensity_value=35.0,  # 35°C = 15°C above baseline
            intensity_unit="celsius",
            frequency=0.2
        )
        expected_severity = min(1.0, 15.0 / 30.0)  # 15°C above 20°C baseline / 30°C range
        assert abs(heat.get_severity_score() - expected_severity) < 0.01
        
        # Water scarcity (availability fraction)
        water = HazardIntensity(
            hazard_type=HazardType.WATER_SCARCITY,
            intensity_value=0.7,  # 70% availability
            intensity_unit="fraction",
            frequency=0.4
        )
        assert abs(water.get_severity_score() - 0.3) < 1e-10  # 1 - 0.7


class TestAssetExposure:
    """Test AssetExposure dataclass and methods."""
    
    @pytest.fixture
    def sample_plant(self):
        """Sample plant characteristics."""
        return PlantCharacteristics(
            capacity_mw=1000,
            plant_type="Coal",
            location="Test Location",
            construction_cost_million=3000,
            base_capacity_factor=0.75,
            operating_years=40,
            efficiency_rate=0.35,
        )
    
    @pytest.fixture
    def sample_exposure(self, sample_plant):
        """Sample asset exposure characteristics."""
        return AssetExposure(
            plant=sample_plant,
            latitude=37.5,
            longitude=127.0,
            elevation_m=50,
            distance_to_coast_km=5,
            distance_to_water_body_km=2,
            foundation_type="deep",
            cooling_system_type="recirculating",
            construction_material="concrete",
            protection_measures=["flood_wall"],
            water_requirements_m3_per_hour=8000,
            temperature_sensitivity_celsius=0.5,
            flood_criticality="high",
        )
    
    def test_hazard_sensitivity_calculation(self, sample_exposure):
        """Test hazard sensitivity calculations."""
        # Wildfire sensitivity (based on cooling system)
        wildfire_sens = sample_exposure.get_hazard_sensitivity(HazardType.WILDFIRE)
        expected_wildfire = 0.4  # recirculating base
        assert wildfire_sens == pytest.approx(expected_wildfire, rel=0.1)
        
        # Flood sensitivity (based on foundation type)
        flood_sens = sample_exposure.get_hazard_sensitivity(HazardType.FLOOD)
        expected_flood = 0.5  # deep foundation
        # Adjust for flood wall protection
        assert flood_sens == pytest.approx(0.2, rel=0.1)  # 0.5 - 0.3 protection
        
        # Drought sensitivity (based on cooling system)
        drought_sens = sample_exposure.get_hazard_sensitivity(HazardType.DROUGHT)
        expected_drought = 0.6  # recirculating
        assert drought_sens == pytest.approx(expected_drought, rel=0.1)
        
        # Heat sensitivity (based on cooling system)
        heat_sens = sample_exposure.get_hazard_sensitivity(HazardType.HEAT)
        expected_heat = 0.8  # recirculating
        assert heat_sens == pytest.approx(expected_heat, rel=0.1)


class TestDamageFunction:
    """Test DamageFunction calculations."""
    
    def test_linear_damage_function(self):
        """Test linear damage curve."""
        damage_func = DamageFunction(
            hazard_type=HazardType.WILDFIRE,
            asset_type="Coal",
            intensity_threshold=0.2,
            damage_curve_params={
                "curve_type": "linear",
                "slope": 0.1,
            },
        )
        
        # Below threshold - no damage
        intensity_low = HazardIntensity(
            hazard_type=HazardType.WILDFIRE,
            intensity_value=0.1,
            intensity_unit="index",
            frequency=0.05
        )
        assert damage_func.calculate_damage_ratio(intensity_low) == 0.0
        
        # Above threshold - linear damage
        intensity_high = HazardIntensity(
            hazard_type=HazardType.WILDFIRE,
            intensity_value=0.5,
            intensity_unit="index",
            frequency=0.1
        )
        expected_damage = 0.1 * (0.5 - 0.2)  # slope * excess_intensity
        assert damage_func.calculate_damage_ratio(intensity_high) == pytest.approx(expected_damage)
        
        # Capped at 1.0
        intensity_extreme = HazardIntensity(
            hazard_type=HazardType.WILDFIRE,
            intensity_value=15.0,
            intensity_unit="index",
            frequency=0.2
        )
        assert damage_func.calculate_damage_ratio(intensity_extreme) == 1.0
    
    def test_exponential_damage_function(self):
        """Test exponential damage curve."""
        damage_func = DamageFunction(
            hazard_type=HazardType.FLOOD,
            asset_type="Coal",
            intensity_threshold=0.1,
            damage_curve_params={
                "curve_type": "exponential",
                "k": 0.8,
            },
        )
        
        intensity = HazardIntensity(
            hazard_type=HazardType.FLOOD,
            intensity_value=0.5,
            intensity_unit="meters",
            frequency=0.1
        )
        
        expected_damage = 1 - np.exp(-0.8 * (0.5 - 0.1))
        actual_damage = damage_func.calculate_damage_ratio(intensity)
        assert actual_damage == pytest.approx(expected_damage, rel=0.01)
    
    def test_logistic_damage_function(self):
        """Test logistic damage curve."""
        damage_func = DamageFunction(
            hazard_type=HazardType.HEAT,
            asset_type="Coal",
            intensity_threshold=35.0,
            damage_curve_params={
                "curve_type": "logistic",
                "max_damage": 0.8,
                "steepness": 2.0,
                "inflection_point": 38.0,
            },
        )
        
        # At inflection point, damage should be half of maximum
        intensity_inflection = HazardIntensity(
            hazard_type=HazardType.HEAT,
            intensity_value=38.0,
            intensity_unit="celsius",
            frequency=0.2
        )
        
        expected_damage = 0.8 / 2  # L/2 at inflection point
        actual_damage = damage_func.calculate_damage_ratio(intensity_inflection)
        assert actual_damage == pytest.approx(expected_damage, rel=0.01)


class TestHazardModel:
    """Test HazardModel functionality."""
    
    @pytest.fixture
    def hazard_model(self):
        """Get hazard model instance."""
        return HazardModel()
    
    @pytest.fixture
    def sample_exposure(self):
        """Sample asset exposure."""
        plant = PlantCharacteristics(
            capacity_mw=1000,
            plant_type="Coal",
            location="Test Location",
            construction_cost_million=3000,
            base_capacity_factor=0.75,
            operating_years=40,
            efficiency_rate=0.35,
        )
        
        return AssetExposure(
            plant=plant,
            latitude=37.5,
            longitude=127.0,
            elevation_m=50,
            distance_to_coast_km=5,
            distance_to_water_body_km=2,
            foundation_type="deep",
            cooling_system_type="recirculating",
            construction_material="concrete",
            water_requirements_m3_per_hour=8000,
        )
    
    @pytest.fixture
    def moderate_scenario(self):
        """Moderate climate scenario."""
        return ScenarioParameters(
            name="Moderate Scenario",
            risk_type=RiskType.PHYSICAL,
            description="Moderate physical risks",
            severity_score=0.5,
            temperature_change_celsius=1.5,
            sea_level_rise_meters=0.3,
        )
    
    def test_wildfire_intensity_calculation(self, hazard_model, sample_exposure, moderate_scenario):
        """Test wildfire intensity calculation."""
        intensity = hazard_model._calculate_wildfire_intensity(
            sample_exposure, moderate_scenario, 2030
        )
        
        if intensity:
            assert isinstance(intensity, HazardIntensity)
            assert intensity.hazard_type == HazardType.WILDFIRE
            assert intensity.intensity_value > 0
            assert intensity.frequency > 0
            assert intensity.duration_days > 0
    
    def test_flood_intensity_calculation(self, hazard_model, sample_exposure, moderate_scenario):
        """Test flood intensity calculation."""
        intensity = hazard_model._calculate_flood_intensity(
            sample_exposure, moderate_scenario, 2030
        )
        
        if intensity:
            assert isinstance(intensity, HazardIntensity)
            assert intensity.hazard_type == HazardType.FLOOD
            assert intensity.intensity_value > 0
            assert intensity.intensity_unit == "depth_meters"
    
    def test_heat_intensity_calculation(self, hazard_model, sample_exposure, moderate_scenario):
        """Test heat intensity calculation."""
        intensity = hazard_model._calculate_heat_intensity(
            sample_exposure, moderate_scenario, 2030
        )
        
        if intensity:
            assert isinstance(intensity, HazardIntensity)
            assert intensity.hazard_type == HazardType.HEAT
            assert intensity.intensity_value > 20  # Should be above baseline
            assert intensity.intensity_unit == "degrees_celsius"
    
    def test_water_scarcity_intensity_calculation(self, hazard_model, sample_exposure, moderate_scenario):
        """Test water scarcity intensity calculation."""
        intensity = hazard_model._calculate_water_scarcity_intensity(
            sample_exposure, moderate_scenario, 2030
        )
        
        if intensity:
            assert isinstance(intensity, HazardIntensity)
            assert intensity.hazard_type == HazardType.WATER_SCARCITY
            assert 0 <= intensity.intensity_value <= 1  # Availability fraction
            assert intensity.intensity_unit == "availability_fraction"
    
    def test_complete_hazard_assessment(self, hazard_model, sample_exposure, moderate_scenario):
        """Test complete hazard intensity assessment."""
        intensities = hazard_model.calculate_hazard_intensity(
            sample_exposure, moderate_scenario, 2030
        )
        
        assert isinstance(intensities, list)
        assert len(intensities) > 0
        
        # Check all intensities are valid
        for intensity in intensities:
            assert isinstance(intensity, HazardIntensity)
            assert intensity.intensity_value >= 0
            assert intensity.frequency >= 0


class TestVulnerabilityModel:
    """Test VulnerabilityModel functionality."""
    
    @pytest.fixture
    def vulnerability_model(self):
        """Get vulnerability model instance."""
        hazard_model = HazardModel()
        return VulnerabilityModel(hazard_model)
    
    @pytest.fixture
    def sample_exposure(self):
        """Sample asset exposure."""
        plant = PlantCharacteristics(
            capacity_mw=1000,
            plant_type="Coal",
            location="Test Location",
            construction_cost_million=3000,
            base_capacity_factor=0.75,
            operating_years=40,
            efficiency_rate=0.35,
        )
        
        return AssetExposure(
            plant=plant,
            latitude=37.5,
            longitude=127.0,
            elevation_m=50,
            distance_to_coast_km=5,
            distance_to_water_body_km=2,
            foundation_type="deep",
            cooling_system_type="recirculating",
            construction_material="concrete",
            protection_measures=["flood_wall"],
            water_requirements_m3_per_hour=8000,
        )
    
    @pytest.fixture
    def high_severity_scenario(self):
        """High severity climate scenario."""
        return ScenarioParameters(
            name="High Severity",
            risk_type=RiskType.PHYSICAL,
            description="High physical risks",
            severity_score=0.9,
            temperature_change_celsius=3.0,
            sea_level_rise_meters=1.0,
        )
    
    def test_single_hazard_impact_calculation(self, vulnerability_model, sample_exposure):
        """Test impact calculation for single hazard."""
        # Create test intensity
        intensity = HazardIntensity(
            hazard_type=HazardType.FLOOD,
            intensity_value=1.0,  # 1 meter flood
            intensity_unit="depth_meters",
            frequency=0.1,
            duration_days=3.0,
        )
        
        impact = vulnerability_model._calculate_hazard_impact(sample_exposure, intensity)
        
        assert isinstance(impact, PhysicalImpact)
        assert impact.outage_probability >= 0
        assert impact.outage_duration_hours >= 0
        assert impact.capacity_derate_fraction >= 0
        assert impact.repair_cost_ratio >= 0
        assert impact.cumulative_annual_impact_days >= 0
    
    def test_impact_aggregation(self, vulnerability_model):
        """Test aggregation of multiple hazard impacts."""
        # First impact
        impact1 = PhysicalImpact(
            outage_probability=0.1,
            outage_duration_hours=48,
            capacity_derate_fraction=0.05,
            efficiency_loss_fraction=0.02,
            repair_cost_ratio=0.1,
            water_constraint_factor=1.0,
            cumulative_annual_impact_days=30,
            component_damages={"turbine": 0.3},
            operational_restrictions=["restriction1"],
        )
        
        # Second impact
        impact2 = PhysicalImpact(
            outage_probability=0.2,
            outage_duration_hours=72,
            capacity_derate_fraction=0.1,
            efficiency_loss_fraction=0.05,
            repair_cost_ratio=0.15,
            water_constraint_factor=0.8,
            cumulative_annual_impact_days=60,
            component_damages={"electrical": 0.4},
            operational_restrictions=["restriction2"],
        )
        
        # Aggregate impacts
        vulnerability_model._aggregate_impacts(impact1, impact2)
        
        # Check aggregation results
        assert impact1.outage_probability == pytest.approx(0.3, rel=0.1)  # Union bound
        assert impact1.outage_duration_hours == 72  # Maximum
        assert abs(impact1.capacity_derate_fraction - 0.15) < 1e-10  # Additive
        assert impact1.efficiency_loss_fraction == 0.07  # Additive
        assert impact1.repair_cost_ratio == 0.25  # Additive
        assert impact1.water_constraint_factor == 0.8  # Minimum (most restrictive)
        assert impact1.cumulative_annual_impact_days == 90  # Additive
        
        # Check component damage aggregation
        assert "turbine" in impact1.component_damages
        assert "electrical" in impact1.component_damages
        
        # Check operational restrictions
        assert "restriction1" in impact1.operational_restrictions
        assert "restriction2" in impact1.operational_restrictions
    
    def test_mitigation_effects_application(self, vulnerability_model):
        """Test application of mitigation effects."""
        # Create impact without mitigation
        original_impact = PhysicalImpact(
            outage_probability=0.3,
            outage_duration_hours=96,
            capacity_derate_fraction=0.2,
            efficiency_loss_fraction=0.1,
            repair_cost_ratio=0.25,
            water_constraint_factor=0.7,
            cumulative_annual_impact_days=90,
        )
        
        # Create exposure with protection measures
        plant = PlantCharacteristics(
            capacity_mw=1000, plant_type="Coal", location="Test",
            construction_cost_million=3000, base_capacity_factor=0.75,
            operating_years=40, efficiency_rate=0.35,
        )
        
        protected_exposure = AssetExposure(
            plant=plant,
            latitude=37.5, longitude=127.0, elevation_m=50,
            distance_to_coast_km=5, distance_to_water_body_km=2,
            foundation_type="deep", cooling_system_type="recirculating",
            construction_material="concrete",
            protection_measures=["flood_wall", "backup_cooling", "heat_resistant_design"],
        )
        
        mitigated_impact = vulnerability_model._apply_mitigation_effects(
            protected_exposure, original_impact
        )
        
        # Check that mitigation reduced impacts
        assert mitigated_impact.outage_probability < original_impact.outage_probability
        assert mitigated_impact.repair_cost_ratio < original_impact.repair_cost_ratio
        assert mitigated_impact.capacity_derate_fraction < original_impact.capacity_derate_fraction
        assert mitigated_impact.efficiency_loss_fraction < original_impact.efficiency_loss_fraction
        assert mitigated_impact.water_constraint_factor > original_impact.water_constraint_factor
    
    def test_complete_vulnerability_assessment(self, vulnerability_model, sample_exposure, high_severity_scenario):
        """Test complete vulnerability assessment."""
        impact = vulnerability_model.assess_vulnerability(
            sample_exposure, high_severity_scenario, 2030
        )
        
        assert isinstance(impact, PhysicalImpact)
        
        # High severity scenario should produce some impacts
        assert (
            impact.outage_probability > 0 or
            impact.capacity_derate_fraction > 0 or
            impact.efficiency_loss_fraction > 0 or
            impact.repair_cost_ratio > 0 or
            impact.water_constraint_factor < 1.0
        )


class TestPhysicalImpact:
    """Test PhysicalImpact functionality."""
    
    def test_financial_impact_calculation(self):
        """Test financial impact calculation."""
        impact = PhysicalImpact(
            outage_probability=0.1,
            outage_duration_hours=168,  # 1 week
            capacity_derate_fraction=0.05,
            efficiency_loss_fraction=0.02,
            repair_cost_ratio=0.1,
            water_constraint_factor=0.9,
            cumulative_annual_impact_days=60,
        )
        
        annual_revenue = 500_000_000  # $500M
        fixed_costs = 100_000_000     # $100M
        replacement_cost = 3_000_000_000  # $3B
        
        financial_impact = impact.get_financial_impact(
            annual_revenue, fixed_costs, replacement_cost
        )
        
        assert isinstance(financial_impact, dict)
        assert "total_annual_impact" in financial_impact
        
        # Check that impact components are positive
        for key, value in financial_impact.items():
            assert value >= 0, f"{key} should be non-negative"
        
        # Total should be sum of components
        expected_total = sum(financial_impact.values()) - financial_impact["total_annual_impact"]
        assert financial_impact["total_annual_impact"] == pytest.approx(expected_total)


class TestEnhancedPhysicalRiskEngine:
    """Test EnhancedPhysicalRiskEngine functionality."""
    
    @pytest.fixture
    def engine(self):
        """Get enhanced physical risk engine instance."""
        return EnhancedPhysicalRiskEngine()
    
    @pytest.fixture
    def sample_plant(self):
        """Sample plant characteristics."""
        return PlantCharacteristics(
            capacity_mw=2100,  # Samcheok-sized plant
            plant_type="Coal",
            location="Samcheok",
            construction_cost_million=3200,
            base_capacity_factor=0.85,
            operating_years=40,
            efficiency_rate=0.40,
            fuel_type="bituminous",
        )
    
    @pytest.fixture
    def samcheok_exposure(self, sample_plant):
        """Samcheok plant exposure characteristics."""
        return AssetExposure(
            plant=sample_plant,
            latitude=37.45,  # Approximate Samcheok coordinates
            longitude=129.17,
            elevation_m=30,
            distance_to_coast_km=2,
            distance_to_water_body_km=0.5,  # Near water for cooling
            foundation_type="piled",
            cooling_system_type="once_through",
            construction_material="steel_concrete",
            protection_measures=["flood_wall"],
            water_requirements_m3_per_hour=15000,  # Large coal plant
            temperature_sensitivity_celsius=0.3,
            flood_criticality="critical",
        )
    
    @pytest.fixture
    def extreme_scenario(self):
        """Extreme climate scenario."""
        return ScenarioParameters(
            name="Extreme Physical Risk",
            risk_type=RiskType.PHYSICAL,
            description="Extreme physical climate risks for stress testing",
            severity_score=1.0,
            temperature_change_celsius=4.0,
            sea_level_rise_meters=2.0,
        )
    
    def test_single_year_assessment(self, engine, sample_plant, samcheok_exposure, extreme_scenario):
        """Test single year physical risk assessment."""
        impact = engine.assess_physical_risk(
            sample_plant, samcheok_exposure, extreme_scenario, 2050
        )
        
        assert isinstance(impact, PhysicalImpact)
        
        # Extreme scenario should produce significant impacts
        assert (
            impact.outage_probability > 0 or
            impact.capacity_derate_fraction > 0 or
            impact.efficiency_loss_fraction > 0 or
            impact.repair_cost_ratio > 0 or
            impact.water_constraint_factor < 1.0
        )
        
        # Validate impact ranges
        assert 0 <= impact.outage_probability <= 1
        assert 0 <= impact.capacity_derate_fraction <= 1
        assert 0 <= impact.efficiency_loss_fraction <= 1
        assert 0 <= impact.repair_cost_ratio <= 1
        assert 0 <= impact.water_constraint_factor <= 1
    
    def test_time_series_assessment(self, engine, sample_plant, samcheok_exposure, extreme_scenario):
        """Test time series physical risk assessment."""
        time_series = engine.create_time_series_assessment(
            sample_plant, samcheok_exposure, extreme_scenario, 2024, 2030
        )
        
        assert isinstance(time_series, dict)
        assert len(time_series) == 7  # 2024-2030 inclusive
        
        # Check that all years have impacts
        for year, impact in time_series.items():
            assert isinstance(year, int)
            assert isinstance(impact, PhysicalImpact)
            assert 2024 <= year <= 2030
        
        # Check trend: impacts should generally increase over time
        early_impact = time_series[2024]
        late_impact = time_series[2030]
        
        # Later years should have equal or greater impacts
        late_total_impact = (
            late_impact.outage_probability +
            late_impact.capacity_derate_fraction +
            late_impact.efficiency_loss_fraction +
            late_impact.repair_cost_ratio
        )
        
        early_total_impact = (
            early_impact.outage_probability +
            early_impact.capacity_derate_fraction +
            early_impact.efficiency_loss_fraction +
            early_impact.repair_cost_ratio
        )
        
        assert late_total_impact >= early_total_impact
    
    def test_input_validation(self, engine, sample_plant, samcheok_exposure, extreme_scenario):
        """Test input validation."""
        # Test invalid capacity
        invalid_plant = PlantCharacteristics(
            capacity_mw=-100,  # Invalid negative capacity
            plant_type="Coal",
            location="Test",
            construction_cost_million=3000,
            base_capacity_factor=0.75,
            operating_years=40,
            efficiency_rate=0.35,
        )
        
        with pytest.raises(ValueError, match="Plant capacity must be positive"):
            engine.assess_physical_risk(invalid_plant, samcheok_exposure, extreme_scenario)
        
        # Test invalid latitude
        invalid_exposure = AssetExposure(
            plant=sample_plant,
            latitude=100,  # Invalid latitude
            longitude=127.0,
            elevation_m=50,
            distance_to_coast_km=5,
            distance_to_water_body_km=2,
            foundation_type="deep",
            cooling_system_type="recirculating",
            construction_material="concrete",
        )
        
        with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
            engine.assess_physical_risk(sample_plant, invalid_exposure, extreme_scenario)
        
        # Test invalid scenario severity
        invalid_scenario = ScenarioParameters(
            name="Invalid",
            risk_type=RiskType.PHYSICAL,
            description="Invalid scenario",
            severity_score=1.5,  # Invalid > 1.0
        )
        
        with pytest.raises(ValueError, match="Scenario severity score must be between 0 and 1"):
            engine.assess_physical_risk(sample_plant, samcheok_exposure, invalid_scenario)


class TestGlobalInterface:
    """Test global interface functions."""
    
    def test_get_enhanced_physical_risk_engine(self):
        """Test global engine access."""
        engine = get_enhanced_physical_risk_engine()
        assert isinstance(engine, EnhancedPhysicalRiskEngine)
        
        # Should return same instance
        engine2 = get_enhanced_physical_risk_engine()
        assert engine is engine2


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_zero_impact_scenario(self):
        """Test scenario with minimal expected impacts."""
        engine = EnhancedPhysicalRiskEngine()
        
        plant = PlantCharacteristics(
            capacity_mw=100,
            plant_type="Gas",
            location="Protected Area",
            construction_cost_million=500,
            base_capacity_factor=0.5,
            operating_years=30,
            efficiency_rate=0.5,
        )
        
        exposure = AssetExposure(
            plant=plant,
            latitude=0,  # Equatorial (less extreme weather)
            longitude=0,
            elevation_m=1000,  # High elevation (flood safe)
            distance_to_coast_km=1000,  # Far from coast
            distance_to_water_body_km=500,  # Far from water
            foundation_type="deep",
            cooling_system_type="dry_cooled",  # Minimal water use
            construction_material="concrete",
            protection_measures=["flood_wall", "firebreak", "backup_cooling"],
        )
        
        minimal_scenario = ScenarioParameters(
            name="Minimal Risk",
            risk_type=RiskType.PHYSICAL,
            description="Minimal physical risks",
            severity_score=0.0,  # No additional climate risk
            temperature_change_celsius=0.0,
            sea_level_rise_meters=0.0,
        )
        
        impact = engine.assess_physical_risk(plant, exposure, minimal_scenario, 2024)
        
        # Should have minimal impacts due to protected location and minimal scenario
        assert impact.outage_probability < 0.1
        assert impact.capacity_derate_fraction < 0.1
        assert impact.efficiency_loss_fraction < 0.1
        assert impact.repair_cost_ratio < 0.05


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])
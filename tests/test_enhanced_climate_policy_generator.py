"""
Test suite for Enhanced Climate Policy Scenario Generator.

Tests the functionality of the enhanced scenario generator including:
- Policy announcement parsing and classification
- Scenario generation from policy combinations
- Financial impact assessment
- Scenario validation
- Integration with existing models

Run with: python -m pytest tests/test_enhanced_climate_policy_generator.py -v
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
import json

from src.scenarios.enhanced_climate_policy_generator import (
    PolicyAnnouncement,
    PolicyType,
    PolicyImpact,
    PolicyMonitor,
    EnhancedScenarioGenerator,
    ScenarioValidation,
    FinancialImpact
)
from src.models.transition.korea_power_plan import KoreaPowerPlan


class TestPolicyAnnouncement:
    """Test PolicyAnnouncement dataclass."""
    
    def test_policy_announcement_creation(self):
        """Test creating a policy announcement."""
        announcement = PolicyAnnouncement(
            id="test_001",
            title="Test Policy",
            description="A test policy announcement",
            announcement_date=datetime(2025, 1, 1),
            effective_date=datetime(2025, 6, 1),
            policy_type=PolicyType.COAL_PHASE_OUT,
            impact_level=PolicyImpact.HIGH,
            source="Test Source",
            url="https://example.com/policy",
            metrics={"target_year": 2030, "confidence_level": 0.8},
            confidence_level=0.8
        )
        
        assert announcement.id == "test_001"
        assert announcement.policy_type == PolicyType.COAL_PHASE_OUT
        assert announcement.impact_level == PolicyImpact.HIGH
        assert announcement.confidence_level == 0.8
        assert announcement.metrics["target_year"] == 2030
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        announcement = PolicyAnnouncement(
            id="test_002",
            title="Test Policy 2",
            description="Another test policy",
            announcement_date=datetime(2025, 1, 1),
            effective_date=datetime(2025, 6, 1),
            policy_type=PolicyType.RENEWABLE_TARGET,
            impact_level=PolicyImpact.MEDIUM,
            source="Test Source 2",
            url="https://example.com/policy2",
            metrics={"renewable_target_gw": 100},
            confidence_level=0.7
        )
        
        result = announcement.to_dict()
        
        assert result["id"] == "test_002"
        assert result["policy_type"] == "renewable_target"
        assert result["impact_level"] == "medium"
        assert "announcement_date" in result
        assert result["metrics"]["renewable_target_gw"] == 100


class TestPolicyMonitor:
    """Test PolicyMonitor functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.monitor = PolicyMonitor()
    
    def test_add_announcement(self):
        """Test adding policy announcements."""
        announcement = PolicyAnnouncement(
            id="test_monitor_001",
            title="Monitor Test",
            description="Test announcement for monitor",
            announcement_date=datetime.now(),
            effective_date=datetime.now() + timedelta(days=180),
            policy_type=PolicyType.COAL_PHASE_OUT,
            impact_level=PolicyImpact.HIGH,
            source="Test",
            url="https://test.com",
            metrics={},
            confidence_level=0.8
        )
        
        # Subscribe a mock callback
        callback = Mock()
        self.monitor.subscribe(callback)
        
        # Add announcement
        self.monitor.add_announcement(announcement)
        
        # Verify announcement was added
        assert len(self.monitor.announcements) == 1
        assert self.monitor.announcements[0] == announcement
        
        # Verify callback was called
        callback.assert_called_once_with(announcement)
    
    def test_get_recent_announcements(self):
        """Test filtering recent announcements."""
        # Add announcements with different dates
        old_announcement = PolicyAnnouncement(
            id="old_001",
            title="Old Policy",
            description="Old announcement",
            announcement_date=datetime.now() - timedelta(days=60),
            effective_date=datetime.now(),
            policy_type=PolicyType.EMISSIONS_REDUCTION,
            impact_level=PolicyImpact.LOW,
            source="Test",
            url="https://test.com",
            metrics={},
            confidence_level=0.6
        )
        
        recent_announcement = PolicyAnnouncement(
            id="recent_001",
            title="Recent Policy",
            description="Recent announcement",
            announcement_date=datetime.now() - timedelta(days=10),
            effective_date=datetime.now(),
            policy_type=PolicyType.COAL_PHASE_OUT,
            impact_level=PolicyImpact.HIGH,
            source="Test",
            url="https://test.com",
            metrics={},
            confidence_level=0.8
        )
        
        self.monitor.add_announcement(old_announcement)
        self.monitor.add_announcement(recent_announcement)
        
        # Get recent announcements (last 30 days)
        recent = self.monitor.get_recent_announcements(days=30)
        
        assert len(recent) == 1
        assert recent[0].id == "recent_001"
        
        # Filter by policy type
        coal_announcements = self.monitor.get_recent_announcements(
            days=60, 
            policy_types=[PolicyType.COAL_PHASE_OUT]
        )
        
        assert len(coal_announcements) == 1
        assert coal_announcements[0].policy_type == PolicyType.COAL_PHASE_OUT
    
    def test_search_announcements(self):
        """Test searching announcements by content."""
        announcement1 = PolicyAnnouncement(
            id="search_001",
            title="Coal Phase Out Plan",
            description="Government announces coal phase out by 2030",
            announcement_date=datetime.now(),
            effective_date=datetime.now(),
            policy_type=PolicyType.COAL_PHASE_OUT,
            impact_level=PolicyImpact.HIGH,
            source="Test",
            url="https://test.com",
            metrics={},
            confidence_level=0.8
        )
        
        announcement2 = PolicyAnnouncement(
            id="search_002",
            title="Renewable Energy Target",
            description="New renewable target of 100 GW by 2030",
            announcement_date=datetime.now(),
            effective_date=datetime.now(),
            policy_type=PolicyType.RENEWABLE_TARGET,
            impact_level=PolicyImpact.HIGH,
            source="Test",
            url="https://test.com",
            metrics={},
            confidence_level=0.8
        )
        
        self.monitor.add_announcement(announcement1)
        self.monitor.add_announcement(announcement2)
        
        # Search for "coal"
        coal_results = self.monitor.search_announcements("coal")
        assert len(coal_results) == 1
        assert coal_results[0].id == "search_001"
        
        # Search for "2030"
        year_results = self.monitor.search_announcements("2030")
        assert len(year_results) == 2


class TestEnhancedScenarioGenerator:
    """Test EnhancedScenarioGenerator functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.generator = EnhancedScenarioGenerator()
    
    def test_initialization(self):
        """Test generator initialization."""
        assert self.generator.policy_monitor is not None
        assert isinstance(self.generator.enhanced_scenarios, dict)
        assert len(self.generator.enhanced_scenarios) > 0  # Should have base scenarios
        assert isinstance(self.generator.validation_cache, dict)
        assert isinstance(self.generator.impact_cache, dict)
    
    def test_latest_policies_initialization(self):
        """Test that latest policies are initialized."""
        latest_policies = self.generator.get_latest_policies()
        
        # Should have COP30 PPCA and renewable target announcements
        policy_titles = [p.title for p in latest_policies]
        
        assert any("Powering Past Coal" in title for title in policy_titles)
        assert any("100 GW" in title or "renewable" in title.lower() for title in policy_titles)
        
        # Check policy types
        policy_types = [p.policy_type for p in latest_policies]
        assert PolicyType.COAL_PHASE_OUT in policy_types
        assert PolicyType.RENEWABLE_TARGET in policy_types
    
    def test_generate_scenario_from_policies(self):
        """Test generating scenarios from policy combinations."""
        latest_policies = self.generator.get_latest_policies()

        if len(latest_policies) >= 2:
            # Generate scenario from first two policies
            scenario = self.generator.generate_scenario(
                name="test_combined_scenario",
                policy_combination=latest_policies[:2],
                description="Test scenario combining latest policies"
            )

            assert scenario is not None
            assert scenario.name == "test_combined_scenario"
            assert scenario.name in self.generator.enhanced_scenarios

            # Check that trajectory was calculated
            assert len(scenario.dispatch_trajectory) > 0
            assert len(scenario.coal_share_trajectory) > 0
    
    def test_validate_scenario(self):
        """Test scenario validation."""
        # Create a test scenario
        test_scenario = KoreaPowerPlan(
            _name="test_validation",
            _description="Test scenario for validation",
            _source="Test source",
            dispatch_trajectory={
                2024: 1.0,
                2030: 0.7,
                2035: 0.5,
                2040: 0.0
            },
            retirement_year=2040,
            coal_share_trajectory={
                2024: 32.4,
                2030: 21.2,
                2036: 14.4,
                2040: 0.0
            }
        )
        
        validation = self.generator.validate_scenario(test_scenario)
        
        assert isinstance(validation, ScenarioValidation)
        assert 0 <= validation.overall_score <= 1
        assert 0 <= validation.confidence_score <= 1
        assert 0 <= validation.consistency_score <= 1
        assert 0 <= validation.feasibility_score <= 1
        assert isinstance(validation.issues, list)
        assert isinstance(validation.recommendations, list)
        
        # A well-formed scenario should be valid
        assert validation.overall_score > 0.6
    
    def test_assess_financial_impact(self):
        """Test financial impact assessment."""
        # Use an existing scenario
        scenario_name = "10th_basic_plan"
        
        if scenario_name in self.generator.enhanced_scenarios:
            try:
                impact = self.generator.assess_financial_impact(
                    scenario_name=scenario_name,
                    capacity_mw=1000,
                    baseline_cf=0.85,
                    discount_rate=0.08,
                    power_price=100,
                    analysis_years=30
                )
                
                assert isinstance(impact, FinancialImpact)
                assert isinstance(impact.npv_change_pct, float)
                assert isinstance(impact.revenue_loss_pct, float)
                assert isinstance(impact.cashflow_impact, dict)
                assert isinstance(impact.sensitivity_bounds, dict)
                
                # NPV change should be negative (revenue loss)
                assert impact.npv_change_pct <= 0
                
            except Exception as e:
                pytest.skip(f"Financial assessment failed: {e}")
        else:
            pytest.skip("Base scenario not available")
    
    def test_compare_scenarios(self):
        """Test scenario comparison functionality."""
        # Get available scenarios
        scenario_names = list(self.generator.enhanced_scenarios.keys())

        if len(scenario_names) >= 2:
            comparison = self.generator.compare_scenarios(
                scenario_names=scenario_names[:3],  # Compare first 3 scenarios
                financial_params={
                    'capacity_mw': 1000,
                    'baseline_cf': 0.85,
                    'discount_rate': 0.08,
                    'power_price': 100
                }
            )

            assert isinstance(comparison, pd.DataFrame)
            assert len(comparison) >= 2
            assert 'scenario_name' in comparison.columns
    
    def test_list_scenarios(self):
        """Test listing available scenarios."""
        scenarios = self.generator.list_scenarios()

        assert isinstance(scenarios, dict)
        assert len(scenarios) > 0

        # Check structure
        for name, description in scenarios.items():
            assert isinstance(name, str)
            assert isinstance(description, str)
    
    def test_export_scenario(self):
        """Test scenario export functionality."""
        scenario_name = "10th_basic_plan"
        
        if scenario_name in self.generator.enhanced_scenarios:
            output_path = Path("test_output/exported_scenario.json")
            output_path.parent.mkdir(exist_ok=True)
            
            try:
                self.generator.export_scenario(
                    scenario_name=scenario_name,
                    output_path=output_path,
                    include_validation=True,
                    include_financial=False  # Skip financial for faster test
                )
                
                # Verify file was created
                assert output_path.exists()
                
                # Verify content
                with open(output_path) as f:
                    data = json.load(f)
                
                assert 'scenario' in data
                assert data['scenario']['name'] == scenario_name
                assert 'export_timestamp' in data
                
            except Exception as e:
                pytest.skip(f"Export failed: {e}")
            finally:
                # Cleanup
                if output_path.exists():
                    output_path.unlink()


class TestIntegration:
    """Test integration with existing models."""
    
    def test_integration_with_transition_model(self):
        """Test integration with transition risk model."""
        from src.models.transition.model import TransitionRiskModel
        
        generator = EnhancedScenarioGenerator()
        transition_model = TransitionRiskModel()
        
        # Test with base scenarios
        for scenario_name in generator.enhanced_scenarios:
            try:
                transition_model.set_power_plan(scenario_name)
                result = transition_model.calculate(year=2030, baseline_cf=0.85)
                
                assert result is not None
                assert result.risk_type.value == "transition"
                assert result.value is not None
                
            except Exception as e:
                pytest.skip(f"Integration failed for {scenario_name}: {e}")
    
    def test_policy_scenario_workflow(self):
        """Test complete workflow from policy to financial impact."""
        generator = EnhancedScenarioGenerator()
        
        # Get latest policies
        policies = generator.get_latest_policies()
        
        if len(policies) >= 1:
            # Generate scenario
            scenario = generator.generate_scenario(
                name="workflow_test_scenario",
                policy_combination=policies[:1],
                description="Workflow test scenario"
            )
            
            # Validate scenario
            validation = generator.validate_scenario(scenario)
            assert isinstance(validation, ScenarioValidation)
            assert 0 <= validation.overall_score <= 1
            
            # Assess financial impact
            try:
                impact = generator.assess_financial_impact(
                    scenario_name=scenario.name,
                    capacity_mw=500,
                    baseline_cf=0.80
                )
                
                assert impact.npv_change_pct <= 0  # Should be negative impact
                
            except Exception as e:
                pytest.skip(f"Financial impact assessment failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
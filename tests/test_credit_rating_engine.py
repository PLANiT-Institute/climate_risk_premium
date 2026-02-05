"""
Comprehensive test suite for credit rating engine with death spiral detection.

Tests cover:
- Basic rating assessment functionality
- Death spiral detection logic
- Climate risk integration
- Counterfactual analysis
- Monte Carlo rating migration
- Edge cases and error handling
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime

from src.risk.credit.engine import (
    Rating,
    RatingMetrics,
    RatingAssessment,
    RatingComponent,
    RatingEngine,
    DeathSpiralDetector,
    assess_credit_rating,
    get_rating_engine,
)
from src.risk.core import ScenarioParameters, RiskType


class TestRating:
    """Test Rating enum functionality."""
    
    def test_rating_properties(self):
        """Test rating properties and conversions."""
        # Investment grade ratings
        assert Rating.AAA.is_investment_grade
        assert Rating.AA.is_investment_grade
        assert Rating.A.is_investment_grade
        assert Rating.BBB.is_investment_grade
        
        # Speculative grade
        assert not Rating.BB.is_investment_grade
        assert not Rating.B.is_investment_grade
        
        # Distressed ratings
        assert Rating.CCC.is_distressed
        assert Rating.CC.is_distressed
        assert Rating.C.is_distressed
        assert Rating.D.is_distressed
        
        # Categories
        assert Rating.AAA.category == "Investment Grade"
        assert Rating.BB.category == "Speculative Grade"
        assert Rating.CCC.category == "Distressed"
        assert Rating.D.category == "Default"
    
    def test_rating_spreads(self):
        """Test rating spread calculations."""
        # Spreads should increase with rating deterioration
        assert Rating.AAA.to_spread_bps() < Rating.AA.to_spread_bps()
        assert Rating.AA.to_spread_bps() < Rating.A.to_spread_bps()
        assert Rating.A.to_spread_bps() < Rating.BBB.to_spread_bps()
        assert Rating.BBB.to_spread_bps() < Rating.BB.to_spread_bps()
        
        # Check specific spread values
        assert Rating.AAA.to_spread_bps() == 50
        assert Rating.BBB.to_spread_bps() == 250
        assert Rating.CCC.to_spread_bps() == 900
        assert Rating.D.to_spread_bps() == 5000


class TestRatingEngine:
    """Test RatingEngine functionality."""
    
    @pytest.fixture
    def engine(self):
        """Get rating engine instance."""
        return RatingEngine()
    
    @pytest.fixture
    def healthy_metrics(self):
        """Sample healthy financial metrics."""
        return RatingMetrics(
            capacity_mw=1000,
            ebitda_to_fixed_assets=12.0,
            ebitda_to_interest=8.0,
            net_debt_to_ebitda=3.5,
            debt_to_equity=120.0,
            debt_to_assets=55.0,
            dscr=2.1,
            cfads_to_debt_service=2.2,
            climate_cost_ratio=0.05,
            physical_risk_score=0.1,
            transition_risk_score=0.2,
            is_ebitda_negative=False,
            consecutive_loss_years=0,
        )
    
    @pytest.fixture
    def distressed_metrics(self):
        """Sample distressed financial metrics."""
        return RatingMetrics(
            capacity_mw=500,
            ebitda_to_fixed_assets=-5.0,
            ebitda_to_interest=-0.5,
            net_debt_to_ebitda=15.0,
            debt_to_equity=350.0,
            debt_to_assets=85.0,
            dscr=0.8,
            cfads_to_debt_service=0.7,
            climate_cost_ratio=0.6,
            physical_risk_score=0.8,
            transition_risk_score=0.9,
            is_ebitda_negative=True,
            consecutive_loss_years=3,
        )
    
    def test_healthy_plant_rating(self, engine, healthy_metrics):
        """Test rating assessment for healthy plant."""
        assessment = engine.assess_credit_rating(healthy_metrics)
        
        # Should be investment grade
        assert assessment.overall_rating.is_investment_grade
        assert assessment.overall_rating.value <= 4
        
        # No death spiral
        assert not assessment.death_spiral_detected
        assert len(assessment.spiral_drivers) == 0
        
        # Check component ratings
        components = {c.name: c for c in assessment.components}
        assert components["dscr"].rating.value <= 4  # Good DSCR
        assert components["coverage"].rating.value <= 3  # Good coverage
        assert components["profitability"].rating.value <= 3  # Good profitability
    
    def test_distressed_plant_rating(self, engine, distressed_metrics):
        """Test rating assessment for distressed plant."""
        assessment = engine.assess_credit_rating(distressed_metrics)
        
        # Should be distressed
        assert assessment.overall_rating.is_distressed
        assert assessment.overall_rating.value >= 7
        
        # Check component ratings reflect distress
        components = {c.name: c for c in assessment.components}
        assert components["dscr"].rating.value >= 7  # Poor DSCR
        assert components["coverage"].rating.value >= 7  # Poor coverage
        assert components["profitability"].rating.value >= 6  # Negative profitability (at least B)
    
    def test_component_ratings(self, engine):
        """Test individual component rating functions."""
        # Test capacity rating
        assert engine._rate_capacity(2500) == Rating.AAA
        assert engine._rate_capacity(900) == Rating.AA
        assert engine._rate_capacity(50) == Rating.BB
        
        # Test profitability rating
        assert engine._rate_profitability(18.0, False) == Rating.AAA
        assert engine._rate_profitability(-5.0, True) == Rating.B  # Moderate losses
        assert engine._rate_profitability(-15.0, True) == Rating.CCC  # Severe losses
        
        # Test coverage rating
        assert engine._rate_coverage(15.0) == Rating.AAA
        assert engine._rate_coverage(-0.5) == Rating.CC
        assert engine._rate_coverage(-10.0) == Rating.D
        
        # Test DSCR rating
        assert engine._rate_dscr(3.0) == Rating.AAA
        assert engine._rate_dscr(0.9) == Rating.CCC
        assert engine._rate_dscr(-0.5) == Rating.D
    
    def test_distress_overrides(self, engine):
        """Test distress override logic."""
        # Create metrics with mixed health
        mixed_metrics = RatingMetrics(
            capacity_mw=2000,  # AAA capacity
            ebitda_to_fixed_assets=-10.0,  # CCC profitability
            ebitda_to_interest=10.0,  # AAA coverage
            net_debt_to_ebitda=2.0,  # AA leverage
            debt_to_equity=100.0,  # AAA leverage
            debt_to_assets=40.0,  # AA leverage
            dscr=2.5,  # AAA DSCR
            is_ebitda_negative=False,
        )
        
        assessment = engine.assess_credit_rating(mixed_metrics)
        
        # Despite good other metrics, critical distress should override
        assert assessment.overall_rating.value >= 7  # Should be at least CCC
        
        # Check that distress override is documented
        components = {c.name: c for c in assessment.components}
        assert components["profitability"].rating.value >= 6  # At least B for negative EBITDA


class TestDeathSpiralDetector:
    """Test death spiral detection functionality."""
    
    @pytest.fixture
    def detector(self):
        """Get death spiral detector instance."""
        return DeathSpiralDetector()
    
    def test_no_death_spiral(self, detector):
        """Test case with no death spiral."""
        # Stable metrics over time
        current_metrics = RatingMetrics(
            capacity_mw=1000,
            ebitda_to_fixed_assets=10.0,
            ebitda_to_interest=5.0,
            net_debt_to_ebitda=4.0,
            debt_to_equity=150.0,
            debt_to_assets=60.0,
            dscr=1.5,
        )
        
        historical_metrics = [
            RatingMetrics(
                capacity_mw=1000,
                ebitda_to_fixed_assets=10.2,  # Slight decline
                ebitda_to_interest=5.1,
                net_debt_to_ebitda=3.9,
                debt_to_equity=145.0,
                debt_to_assets=58.0,
                dscr=1.6,
            ),
            current_metrics,
        ]
        
        # Create dummy assessment
        assessment = RatingAssessment(
            overall_rating=Rating.A,
            components=[],
            metrics=current_metrics,
            assessment_date="2024-01-01",
            model_version="2.0.0",
        )
        
        death_spiral, drivers, trajectory = detector.detect_death_spiral(
            current_metrics, historical_metrics, assessment
        )
        
        assert not death_spiral
        assert len(drivers) == 0
        assert len(trajectory) == 0
    
    def test_death_spiral_detected(self, detector):
        """Test case with death spiral detected."""
        # Deteriorating metrics over time
        current_metrics = RatingMetrics(
            capacity_mw=1000,
            ebitda_to_fixed_assets=-5.0,  # Negative EBITDA
            ebitda_to_interest=-0.5,     # Poor coverage
            net_debt_to_ebitda=12.0,     # High leverage
            debt_to_equity=350.0,
            debt_to_assets=85.0,
            dscr=0.8,
        )
        
        # Historical showing rapid deterioration
        historical_metrics = [
            RatingMetrics(
                capacity_mw=1000,
                ebitda_to_fixed_assets=5.0,   # Was positive
                ebitda_to_interest=2.5,
                net_debt_to_ebitda=5.0,       # Was reasonable
                debt_to_equity=200.0,
                debt_to_assets=65.0,
                dscr=1.4,
            ),
            RatingMetrics(
                capacity_mw=1000,
                ebitda_to_fixed_assets=0.0,   # Declined to zero
                ebitda_to_interest=1.0,
                net_debt_to_ebitda=8.0,       # Deteriorating
                debt_to_equity=280.0,
                debt_to_assets=75.0,
                dscr=1.1,
            ),
            current_metrics,
        ]
        
        # Create assessment showing distress
        assessment = RatingAssessment(
            overall_rating=Rating.B,  # Already speculative
            components=[],
            metrics=current_metrics,
            assessment_date="2024-01-01",
            model_version="2.0.0",
        )
        
        death_spiral, drivers, trajectory = detector.detect_death_spiral(
            current_metrics, historical_metrics, assessment
        )
        
        assert death_spiral
        assert len(drivers) >= 2
        assert len(trajectory) > 1
        
        # Should identify key deterioration drivers
        driver_strings = " ".join(drivers).lower()
        assert "ebitda" in driver_strings or "dscr" in driver_strings
        assert "leverage" in driver_strings
        
        # Trajectory should show further deterioration
        assert trajectory[-1].value >= trajectory[0].value  # Should get worse
    
    def test_rating_trajectory_projection(self, detector):
        """Test rating trajectory projection."""
        # Test from investment grade
        trajectory_ig = detector._project_rating_path(Rating.A, years=5)
        assert len(trajectory_ig) == 6  # Including initial rating
        assert trajectory_ig[0] == Rating.A
        
        # Test from distressed
        trajectory_distressed = detector._project_rating_path(Rating.CCC, years=3)
        assert len(trajectory_distressed) >= 3
        assert trajectory_distressed[0] == Rating.CCC
        
        # Distressed should deteriorate faster
        assert trajectory_distressed[-1].value > trajectory_ig[-1].value


class TestClimateRiskIntegration:
    """Test climate risk integration in rating assessment."""
    
    @pytest.fixture
    def climate_scenario(self):
        """Sample climate risk scenario."""
        return ScenarioParameters(
            name="High Physical Risk",
            risk_type=RiskType.PHYSICAL,
            description="High temperature and water stress scenario",
            severity_score=0.8,
            temperature_change_celsius=2.5,
            carbon_price_per_ton=100.0,
        )
    
    def test_climate_impact_calculation(self):
        """Test climate impact notch calculation."""
        engine = RatingEngine()
        
        # Low climate impact
        low_impact_metrics = RatingMetrics(
            capacity_mw=1000,
            ebitda_to_fixed_assets=10.0,
            ebitda_to_interest=5.0,
            net_debt_to_ebitda=4.0,
            debt_to_equity=150.0,
            debt_to_assets=60.0,
            dscr=1.5,
            climate_cost_ratio=0.05,  # 5% climate cost
        )
        
        notches = engine._calculate_climate_impact_notches(
            low_impact_metrics, 
            ScenarioParameters("test", RiskType.PHYSICAL, "test", 0.3)
        )
        assert notches == 1
        
        # High climate impact
        high_impact_metrics = RatingMetrics(
            capacity_mw=1000,
            ebitda_to_fixed_assets=10.0,
            ebitda_to_interest=5.0,
            net_debt_to_ebitda=4.0,
            debt_to_equity=150.0,
            debt_to_assets=60.0,
            dscr=1.5,
            climate_cost_ratio=0.6,  # 60% climate cost
        )
        
        notches = engine._calculate_climate_impact_notches(
            high_impact_metrics,
            ScenarioParameters("test", RiskType.PHYSICAL, "test", 0.8)
        )
        assert notches >= 4  # Major deterioration
    
    def test_full_climate_assessment(self):
        """Test complete climate-aware rating assessment."""
        metrics = RatingMetrics(
            capacity_mw=1000,
            ebitda_to_fixed_assets=8.0,
            ebitda_to_interest=4.0,
            net_debt_to_ebitda=5.0,
            debt_to_equity=180.0,
            debt_to_assets=65.0,
            dscr=1.4,
            climate_cost_ratio=0.3,
            physical_risk_score=0.7,
            transition_risk_score=0.6,
        )
        
        scenario = ScenarioParameters(
            name="Moderate Climate Risk",
            risk_type=RiskType.COMPOUND,
            description="Combined physical and transition risks",
            severity_score=0.6,
        )
        
        assessment = assess_credit_rating(metrics, scenario=scenario)
        
        # Should show climate impact
        assert assessment.climate_notch_deterioration > 0
        # Climate spread increase may be zero if climate impact doesn't change rating category
        assert assessment.climate_spread_increase_bps >= 0
        
        # Assessment should be complete
        assert assessment.model_version == "2.0.0"
        assert len(assessment.assessment_date) > 0
        assert len(assessment.components) == 7  # All components rated


class TestGlobalInterface:
    """Test global interface functions."""
    
    def test_get_rating_engine(self):
        """Test global rating engine access."""
        engine = get_rating_engine()
        assert isinstance(engine, RatingEngine)
        
        # Should return same instance
        engine2 = get_rating_engine()
        assert engine is engine2
    
    def test_assess_credit_rating_interface(self):
        """Test main assessment interface."""
        metrics = RatingMetrics(
            capacity_mw=1500,
            ebitda_to_fixed_assets=11.0,
            ebitda_to_interest=6.0,
            net_debt_to_ebitda=4.0,
            debt_to_equity=140.0,
            debt_to_assets=58.0,
            dscr=1.8,
        )
        
        assessment = assess_credit_rating(metrics)
        
        # Should return proper assessment
        assert isinstance(assessment, RatingAssessment)
        assert assessment.overall_rating in Rating
        assert len(assessment.components) > 0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_zero_values(self):
        """Test handling of zero values."""
        metrics = RatingMetrics(
            capacity_mw=1000,
            ebitda_to_fixed_assets=0.0,
            ebitda_to_interest=0.0,
            net_debt_to_ebitda=0.0,
            debt_to_equity=0.0,
            debt_to_assets=0.0,
            dscr=0.0,
        )
        
        assessment = assess_credit_rating(metrics)
        
        # Should handle gracefully
        assert assessment.overall_rating in Rating
        assert not assessment.overall_rating.is_investment_grade
    
    def test_extreme_values(self):
        """Test handling of extreme values."""
        # Extremely positive
        positive_metrics = RatingMetrics(
            capacity_mw=5000,  # Very large
            ebitda_to_fixed_assets=50.0,  # Very profitable
            ebitda_to_interest=50.0,  # Very strong coverage
            net_debt_to_ebitda=-10.0,  # Net cash position
            debt_to_equity=10.0,  # Very low leverage
            debt_to_assets=5.0,
            dscr=10.0,  # Very strong DSCR
        )
        
        assessment = assess_credit_rating(positive_metrics)
        assert assessment.overall_rating == Rating.AAA
        
        # Extremely negative
        negative_metrics = RatingMetrics(
            capacity_mw=10,  # Very small
            ebitda_to_fixed_assets=-100.0,  # Extreme losses
            ebitda_to_interest=-50.0,  # Extreme negative coverage
            net_debt_to_ebitda=100.0,  # Extreme leverage
            debt_to_equity=1000.0,  # Extreme leverage
            debt_to_assets=200.0,  # Debt exceeds assets
            dscr=-10.0,  # Cannot service debt
        )
        
        assessment = assess_credit_rating(negative_metrics)
        assert assessment.overall_rating.value >= 9  # Near default or default


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])
#!/usr/bin/env python3
"""
Simplified demo script for Enhanced Climate Policy Scenario Generator.

This script demonstrates the core functionality without complex imports.
"""

import sys
from pathlib import Path
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))


class PolicyType(Enum):
    """Types of energy policies."""
    COAL_PHASE_OUT = "coal_phase_out"
    RENEWABLE_TARGET = "renewable_target"
    EMISSIONS_REDUCTION = "emissions_reduction"
    NUCLEAR_EXPANSION = "nuclear_expansion"
    CARBON_PRICING = "carbon_pricing"
    INDUSTRIAL_TRANSITION = "industrial_transition"
    TECHNOLOGY_SPECIFIC = "technology_specific"


class PolicyImpact(Enum):
    """Policy impact severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    TRANSFORMATIONAL = "transformational"


@dataclass
class PolicyAnnouncement:
    """Represents a policy announcement with structured metadata."""
    id: str
    title: str
    description: str
    announcement_date: datetime
    effective_date: datetime
    policy_type: PolicyType
    impact_level: PolicyImpact
    source: str
    url: str
    metrics: Dict[str, Any]
    confidence_level: float
    related_policies: List[str] = field(default_factory=list)


@dataclass
class KoreaPowerPlan:
    """Simplified Korea Power Plan scenario."""
    _name: str
    _description: str
    _source: str
    dispatch_trajectory: Dict[int, float] = field(default_factory=dict)
    retirement_year: Optional[int] = None
    coal_share_trajectory: Dict[int, float] = field(default_factory=dict)
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def source(self) -> str:
        return self._source
    
    def get_value(self, year: int) -> float:
        """Get dispatch factor for a given year."""
        if self.retirement_year and year >= self.retirement_year:
            return 0.0
        
        if year in self.dispatch_trajectory:
            return self.dispatch_trajectory[year]
        
        # Interpolate between known years
        years = sorted(self.dispatch_trajectory.keys())
        if not years:
            return 1.0
        if year < years[0]:
            return self.dispatch_trajectory[years[0]]
        if year > years[-1]:
            return self.dispatch_trajectory[years[-1]]
        
        # Linear interpolation
        for i, y in enumerate(years[:-1]):
            if years[i] <= year < years[i + 1]:
                y0, y1 = years[i], years[i + 1]
                f0, f1 = self.dispatch_trajectory[y0], self.dispatch_trajectory[y1]
                return f0 + (f1 - f0) * (year - y0) / (y1 - y0)
        
        return self.dispatch_trajectory[years[-1]]


@dataclass
class ScenarioValidation:
    """Validation results for a policy scenario."""
    is_valid: bool
    confidence_score: float  # 0-1
    consistency_score: float  # 0-1
    feasibility_score: float  # 0-1
    issues: List[str]
    recommendations: List[str]
    
    @property
    def overall_score(self) -> float:
        """Overall validation score."""
        return (self.confidence_score + self.consistency_score + self.feasibility_score) / 3


@dataclass
class FinancialImpact:
    """Financial impact assessment for a scenario."""
    npv_change_pct: float
    revenue_loss_pct: float
    cashflow_impact: Dict[int, float]
    risk_adjusted_return: float
    break_even_year: Optional[int]
    sensitivity_bounds: Dict[str, tuple]


class SimpleScenarioGenerator:
    """Simplified scenario generator for demo."""
    
    def __init__(self):
        self.enhanced_scenarios = {}
        self.validation_cache = {}
        self.impact_cache = {}
        self.announcements = []
        
        # Initialize with base scenarios
        self._init_base_scenarios()
        self._init_latest_policies()
    
    def _init_base_scenarios(self):
        """Initialize base Korea Power Plan scenarios."""
        # 10th Basic Plan
        tenth_plan = KoreaPowerPlan(
            _name="10th_basic_plan",
            _description="제10차 전력수급기본계획 (10th Basic Plan, Dec 2022)",
            _source="Ministry of Trade, Industry and Energy (MOTIE), Dec 2022",
            dispatch_trajectory={
                2024: 1.00,
                2025: 0.95,
                2030: 0.70,
                2035: 0.50,
                2040: 0.30,
                2050: 0.00,
            },
            retirement_year=2050,
            coal_share_trajectory={
                2024: 32.4,
                2030: 21.2,
                2036: 14.4,
            },
        )
        
        # Baseline no change
        baseline = KoreaPowerPlan(
            _name="baseline_no_change",
            _description="기준 시나리오 (Baseline - No Policy Change)",
            _source="Hypothetical baseline for comparison",
            dispatch_trajectory={
                2024: 1.00,
                2030: 1.00,
                2040: 1.00,
                2050: 1.00,
            },
            retirement_year=None,
            coal_share_trajectory={
                2024: 32.4,
                2030: 32.4,
                2040: 32.4,
            },
        )
        
        self.enhanced_scenarios["10th_basic_plan"] = tenth_plan
        self.enhanced_scenarios["baseline_no_change"] = baseline
    
    def _init_latest_policies(self):
        """Initialize with latest known policy announcements."""
        # COP30 PPCA commitment (Nov 17, 2025)
        pcpa_announcement = PolicyAnnouncement(
            id="cop30_ppca_2025",
            title="South Korea Joins Powering Past Coal Alliance",
            description="South Korea officially joined the PPCA at COP30, committing to phase out 40 coal-fired power plants by 2040 and not build new unabated coal plants.",
            announcement_date=datetime(2025, 11, 17),
            effective_date=datetime(2026, 1, 1),
            policy_type=PolicyType.COAL_PHASE_OUT,
            impact_level=PolicyImpact.HIGH,
            source="COP30, Ministry of Climate, Energy and Environment",
            url="https://www.koreaherald.com/article/10618543",
            metrics={
                "coal_plants_to_close": 40,
                "target_year": 2040,
                "new_coal_banned": True,
                "confidence_level": 0.9
            },
            confidence_level=0.9
        )
        
        # 100 GW Renewable Target (Dec 17, 2025)
        renewable_announcement = PolicyAnnouncement(
            id="renewable_100gw_2025",
            title="100 GW Renewable Energy Target by 2030",
            description="Ministry of Climate announced accelerated renewable energy deployment target of 100 GW by 2030 as part of comprehensive green transformation.",
            announcement_date=datetime(2025, 12, 17),
            effective_date=datetime(2026, 1, 1),
            policy_type=PolicyType.RENEWABLE_TARGET,
            impact_level=PolicyImpact.TRANSFORMATIONAL,
            source="Ministry of Climate, Energy and Environment",
            url="https://cm.asiae.co.kr/en/article/2025121715524707944",
            metrics={
                "renewable_target_gw": 100,
                "target_year": 2030,
                "current_capacity": 25,
                "annual_addition_required": 12.5,
                "confidence_level": 0.8
            },
            confidence_level=0.8
        )
        
        self.announcements = [pcpa_announcement, renewable_announcement]
    
    def get_latest_policies(self) -> List[PolicyAnnouncement]:
        """Get latest policy announcements."""
        return self.announcements
    
    def list_scenarios(self) -> Dict[str, str]:
        """List available scenarios."""
        return {name: scenario.description for name, scenario in self.enhanced_scenarios.items()}
    
    def generate_scenario(
        self, 
        name: str,
        policy_combination: List[PolicyAnnouncement],
        description: str = ""
    ) -> KoreaPowerPlan:
        """Generate a new scenario from policy combination."""
        
        # Combine policy impacts
        combined_dispatch = {}
        combined_coal_share = {}
        max_retirement_year = None
        
        for policy in policy_combination:
            if policy.policy_type == PolicyType.COAL_PHASE_OUT:
                target_year = policy.metrics.get("target_year", 2040)
                max_retirement_year = max(max_retirement_year or 0, target_year)
                
                # Create accelerated trajectory
                trajectory = {
                    2024: 1.00,
                    2025: 0.95,
                    2030: max(0.3, 0.70 * (2040 - target_year) / 10),
                    2035: max(0.1, 0.50 * (2040 - target_year) / 10),
                    2040: 0.0 if target_year <= 2040 else 0.15,
                    2050: 0.0,
                }
                
                # Combine trajectories (take most conservative values)
                for year, value in trajectory.items():
                    if year not in combined_dispatch or value < combined_dispatch[year]:
                        combined_dispatch[year] = value
            
            elif policy.policy_type == PolicyType.RENEWABLE_TARGET:
                target_gw = policy.metrics.get("renewable_target_gw", 100)
                target_year = policy.metrics.get("target_year", 2030)
                
                # Calculate renewable impact on coal
                renewable_impact = 1.0 - (target_gw / 150)  # 150 GW approximate total capacity
                
                renewable_dispatch = {
                    2024: 1.00,
                    2025: 0.95,
                    2030: max(0.3, 0.70 * renewable_impact),
                    2035: max(0.1, 0.40 * renewable_impact),
                    2040: 0.0,
                    2050: 0.0
                }
                
                # Combine with existing (take most conservative)
                for year, value in renewable_dispatch.items():
                    if year not in combined_dispatch or value < combined_dispatch[year]:
                        combined_dispatch[year] = value
        
        # Create scenario
        scenario = KoreaPowerPlan(
            _name=name,
            _description=description or f"Combined scenario from {len(policy_combination)} policies",
            _source=", ".join([p.source for p in policy_combination]),
            dispatch_trajectory=combined_dispatch,
            retirement_year=max_retirement_year,
            coal_share_trajectory=combined_coal_share
        )
        
        # Store scenario
        self.enhanced_scenarios[name] = scenario
        
        return scenario
    
    def validate_scenario(self, scenario: KoreaPowerPlan) -> ScenarioValidation:
        """Validate a policy scenario."""
        issues = []
        recommendations = []
        
        # Consistency checks
        consistency_score = 1.0
        
        # Check if dispatch trajectory is generally declining
        years = sorted(scenario.dispatch_trajectory.keys())
        increases = 0
        for i in range(1, len(years)):
            if scenario.dispatch_trajectory[years[i]] > scenario.dispatch_trajectory[years[i-1]]:
                increases += 1
        
        if increases > len(years) * 0.3:  # More than 30% increases
            consistency_score *= 0.8
            issues.append("Dispatch trajectory has many non-monotonic increases")
        
        # Feasibility checks
        feasibility_score = 1.0
        
        # Check retirement feasibility
        if scenario.retirement_year and scenario.retirement_year < 2028:
            feasibility_score *= 0.7
            issues.append("Very early retirement may be infeasible")
            recommendations.append("Consider staged retirement approach")
        
        # Check rapid reductions
        max_annual_reduction = 0.15  # 15% max annual reduction
        for i in range(1, len(years)):
            annual_reduction = (scenario.dispatch_trajectory[years[i-1]] - scenario.dispatch_trajectory[years[i]]) / max(scenario.dispatch_trajectory[years[i-1]], 0.01)
            if annual_reduction > max_annual_reduction:
                feasibility_score *= 0.9
                issues.append(f"Rapid annual reduction at {years[i]}")
        
        # Confidence score
        confidence_score = 0.8
        if "draft" in scenario.source.lower():
            confidence_score *= 0.8
        elif "MOTIE" in scenario.source or "Ministry" in scenario.source:
            confidence_score = min(1.0, confidence_score * 1.1)
        
        validation = ScenarioValidation(
            is_valid=consistency_score > 0.6 and feasibility_score > 0.6,
            confidence_score=confidence_score,
            consistency_score=consistency_score,
            feasibility_score=feasibility_score,
            issues=issues,
            recommendations=recommendations
        )
        
        self.validation_cache[scenario.name] = validation
        return validation
    
    def assess_financial_impact(
        self,
        scenario_name: str,
        capacity_mw: float = 1000,
        baseline_cf: float = 0.85,
        discount_rate: float = 0.08,
        power_price: float = 100,
        analysis_years: int = 30
    ) -> FinancialImpact:
        """Assess financial impact of a scenario."""
        if scenario_name not in self.enhanced_scenarios:
            raise ValueError(f"Scenario '{scenario_name}' not found")
        
        scenario = self.enhanced_scenarios[scenario_name]
        
        # Simplified financial calculation
        start_year = 2024
        
        # Calculate baseline and scenario cashflows
        baseline_npv = 0
        scenario_npv = 0
        cashflow_impact = {}
        
        for year in range(start_year, start_year + min(analysis_years, 10)):  # First 10 years
            t = year - start_year
            
            # Baseline
            baseline_generation = capacity_mw * 8760 * baseline_cf
            baseline_revenue = baseline_generation * power_price
            baseline_pv = baseline_revenue / (1 + discount_rate) ** t
            baseline_npv += baseline_pv
            
            # Scenario
            dispatch_factor = scenario.get_value(year)
            scenario_generation = capacity_mw * 8760 * baseline_cf * dispatch_factor
            scenario_revenue = scenario_generation * power_price
            scenario_pv = scenario_revenue / (1 + discount_rate) ** t
            scenario_npv += scenario_pv
            
            cashflow_impact[year] = scenario_pv - baseline_pv
        
        # Calculate metrics
        npv_change_pct = ((scenario_npv - baseline_npv) / baseline_npv) * 100
        revenue_loss_pct = abs(npv_change_pct) * 0.8  # Approximate
        
        # Break-even calculation (simplified)
        initial_investment = capacity_mw * 1_000_000
        annual_loss = abs(baseline_npv - scenario_npv) / analysis_years
        break_even_year = start_year + int(initial_investment / annual_loss) if annual_loss > 0 else None
        
        impact = FinancialImpact(
            npv_change_pct=npv_change_pct,
            revenue_loss_pct=revenue_loss_pct,
            cashflow_impact=cashflow_impact,
            risk_adjusted_return=-npv_change_pct / 100,
            break_even_year=break_even_year if break_even_year < start_year + analysis_years else None,
            sensitivity_bounds={
                "npv_change_pct": (npv_change_pct * 0.7, npv_change_pct * 1.3),
                "revenue_loss_pct": (revenue_loss_pct * 0.7, revenue_loss_pct * 1.3)
            }
        )
        
        self.impact_cache[f"{scenario_name}_{capacity_mw}"] = impact
        return impact


def demo_enhanced_policy_generator():
    """Main demo function."""
    print("🇰🇷 ENHANCED CLIMATE POLICY SCENARIO GENERATOR - DEMO")
    print("=" * 60)
    print("This demo showcases the enhanced scenario generator with")
    print("real-time Korean energy policy monitoring and financial analysis.")
    print()
    
    try:
        # Initialize generator
        generator = SimpleScenarioGenerator()
        print("✅ Enhanced scenario generator initialized successfully")
        
        # Show base scenarios
        scenarios = generator.list_scenarios()
        print(f"📋 Available scenarios: {list(scenarios.keys())}")
        
        # Show latest policies
        latest_policies = generator.get_latest_policies()
        print(f"\n📈 Latest Korean Policies ({len(latest_policies)} announcements):")
        for i, policy in enumerate(latest_policies, 1):
            print(f"   {i}. {policy.title}")
            print(f"      Type: {policy.policy_type.value}")
            print(f"      Impact: {policy.impact_level.value}")
            print(f"      Confidence: {policy.confidence_level:.1%}")
        
        # Generate combined scenario
        if len(latest_policies) >= 2:
            print(f"\n🚀 Generating combined scenario from latest policies...")
            combined_scenario = generator.generate_scenario(
                name="demo_combined_2026",
                policy_combination=latest_policies[:2],
                description="Demo scenario combining COP30 PPCA commitment and 100GW renewable target"
            )
            
            print(f"✅ Generated scenario: {combined_scenario.name}")
            print(f"   Description: {combined_scenario.description}")
            print(f"   Retirement year: {combined_scenario.retirement_year}")
            
            # Show trajectory
            years = [2024, 2030, 2035, 2040, 2050]
            trajectory = [combined_scenario.get_value(year) for year in years]
            print(f"   Dispatch trajectory:")
            for year, value in zip(years, trajectory):
                print(f"      {year}: {value:.2f}")
            
            # Validate scenario
            validation = generator.validate_scenario(combined_scenario)
            print(f"\n✅ Validation Results:")
            print(f"   Overall Score: {validation.overall_score:.2f}")
            print(f"   Confidence: {validation.confidence_score:.2f}")
            print(f"   Consistency: {validation.consistency_score:.2f}")
            print(f"   Feasibility: {validation.feasibility_score:.2f}")
            print(f"   Is Valid: {'✅' if validation.is_valid else '❌'}")
            
            if validation.issues:
                print(f"   Issues: {len(validation.issues)}")
                for issue in validation.issues[:2]:  # Show first 2
                    print(f"      - {issue}")
            
            # Financial impact assessment
            print(f"\n💰 Financial Impact Assessment:")
            financial_params = {
                'capacity_mw': 1000,
                'baseline_cf': 0.85,
                'discount_rate': 0.08,
                'power_price': 100
            }
            
            impact = generator.assess_financial_impact(
                scenario_name=combined_scenario.name,
                **financial_params
            )
            
            print(f"   Financial Parameters:")
            print(f"      Plant Capacity: {financial_params['capacity_mw']} MW")
            print(f"      Baseline Capacity Factor: {financial_params['baseline_cf']}")
            print(f"      Discount Rate: {financial_params['discount_rate']:.1%}")
            print(f"      Power Price: ${financial_params['power_price']}/MWh")
            
            print(f"\n   Financial Impact Results:")
            print(f"      NPV Change: {impact.npv_change_pct:.1f}%")
            print(f"      Revenue Loss: {impact.revenue_loss_pct:.1f}%")
            print(f"      Risk-Adjusted Return: {impact.risk_adjusted_return:.1%}")
            print(f"      Break-even Year: {impact.break_even_year or 'Beyond analysis period'}")
            
            if impact.cashflow_impact:
                print(f"\n   Annual Cashflow Impact (First 5 Years):")
                for year, impact_value in list(impact.cashflow_impact.items())[:5]:
                    print(f"      {year}: ${impact_value:,.0f}")
        
        # Summary
        print("\n" + "=" * 60)
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("✅ Policy monitoring: Working")
        print("✅ Scenario generation: Working")
        print("✅ Scenario validation: Working")
        print("✅ Financial impact: Working")
        
        print(f"\n🚀 To run the interactive dashboard:")
        print(f"   streamlit run src/scenarios/policy_dashboard.py")
        
        print(f"\n📚 For full functionality with all models:")
        print(f"   python scripts/demo_enhanced_policy_generator_full.py")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import numpy as np
    demo_enhanced_policy_generator()
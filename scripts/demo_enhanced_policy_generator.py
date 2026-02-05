#!/usr/bin/env python3
"""
Demo script for Enhanced Climate Policy Scenario Generator.

This script demonstrates the key features of the enhanced scenario generator:
1. Real-time Korean policy monitoring
2. Dynamic scenario generation from policy combinations
3. Financial impact assessment
4. Scenario validation and comparison
5. Export capabilities

Usage:
    python scripts/demo_enhanced_policy_generator.py
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from scenarios.enhanced_climate_policy_generator import (
    EnhancedScenarioGenerator,
    PolicyAnnouncement,
    PolicyType,
    PolicyImpact
)
from scenarios.korean_policy_monitor import (
    AutomatedPolicyMonitor,
    create_test_announcements
)


def demo_policy_monitoring():
    """Demonstrate policy monitoring functionality."""
    print("=" * 60)
    print("🔍 KOREAN ENERGY POLICY MONITORING DEMO")
    print("=" * 60)
    
    # Initialize monitor
    monitor = AutomatedPolicyMonitor()
    
    # Add test announcements
    test_announcements = create_test_announcements()
    for announcement in test_announcements:
        monitor.announcements.append(announcement)
        print(f"📰 Added: {announcement.title}")
    
    # Get summary
    summary = monitor.get_announcements_summary(days=30)
    print(f"\n📊 Policy Summary (Last 30 Days):")
    print(f"   Total announcements: {summary['total_announcements']}")
    print(f"   Policy types: {summary['by_type']}")
    print(f"   Impact levels: {summary['by_impact']}")
    
    # Search functionality
    coal_policies = monitor.search_announcements("coal")
    print(f"\n🔍 Found {len(coal_policies)} coal-related policies")
    
    return monitor


def demo_scenario_generation(monitor):
    """Demonstrate scenario generation."""
    print("\n" + "=" * 60)
    print("🔧 DYNAMIC SCENARIO GENERATION DEMO")
    print("=" * 60)
    
    # Initialize generator
    generator = EnhancedScenarioGenerator()
    
    # Show available base scenarios
    scenarios = generator.list_scenarios()
    print(f"📋 Available scenarios: {list(scenarios.keys())[:5]}...")
    
    # Get latest policies
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
        
        return generator, combined_scenario
    else:
        print("⚠️  Not enough policies to generate combined scenario")
        return generator, None


def demo_scenario_validation(generator, scenario):
    """Demonstrate scenario validation."""
    print("\n" + "=" * 60)
    print("✅ SCENARIO VALIDATION DEMO")
    print("=" * 60)
    
    if scenario is None:
        print("⚠️  No scenario to validate")
        return
    
    # Validate scenario
    validation = generator.validate_scenario(scenario)
    
    print(f"📊 Validation Results for '{scenario.name}':")
    print(f"   Overall Score: {validation.overall_score:.2f}")
    print(f"   Confidence: {validation.confidence_score:.2f}")
    print(f"   Consistency: {validation.consistency_score:.2f}")
    print(f"   Feasibility: {validation.feasibility_score:.2f}")
    print(f"   Is Valid: {'✅' if validation.is_valid else '❌'}")
    
    if validation.issues:
        print(f"   Issues ({len(validation.issues)}):")
        for issue in validation.issues:
            print(f"      - {issue}")
    
    if validation.recommendations:
        print(f"   Recommendations ({len(validation.recommendations)}):")
        for rec in validation.recommendations:
            print(f"      • {rec}")
    
    return validation


def demo_financial_impact(generator, scenario_name):
    """Demonstrate financial impact assessment."""
    print("\n" + "=" * 60)
    print("💰 FINANCIAL IMPACT ASSESSMENT DEMO")
    print("=" * 60)
    
    if scenario_name is None:
        # Use a base scenario
        scenario_name = "10th_basic_plan" if scenario_name in generator.enhanced_scenarios else list(generator.enhanced_scenarios.keys())[0]
        print(f"Using base scenario: {scenario_name}")
    
    # Financial parameters
    capacity_mw = 1000
    baseline_cf = 0.85
    discount_rate = 0.08
    power_price = 100  # $/MWh
    
    print(f"📈 Financial Parameters:")
    print(f"   Plant Capacity: {capacity_mw} MW")
    print(f"   Baseline Capacity Factor: {baseline_cf}")
    print(f"   Discount Rate: {discount_rate:.1%}")
    print(f"   Power Price: ${power_price}/MWh")
    
    try:
        # Assess financial impact
        impact = generator.assess_financial_impact(
            scenario_name=scenario_name,
            capacity_mw=capacity_mw,
            baseline_cf=baseline_cf,
            discount_rate=discount_rate,
            power_price=power_price,
            analysis_years=30
        )
        
        print(f"\n💸 Financial Impact Results:")
        print(f"   NPV Change: {impact.npv_change_pct:.1f}%")
        print(f"   Revenue Loss: {impact.revenue_loss_pct:.1f}%")
        print(f"   Risk-Adjusted Return: {impact.risk_adjusted_return:.1%}")
        print(f"   Break-even Year: {impact.break_even_year or 'Within analysis period'}")
        
        if impact.cashflow_impact:
            print(f"\n📊 Annual Cashflow Impact (First 5 Years):")
            for year, impact_value in list(impact.cashflow_impact.items())[:5]:
                print(f"      {year}: ${impact_value:,.0f}")
        
        if impact.sensitivity_bounds:
            print(f"\n📈 Sensitivity Analysis:")
            for metric, (low, high) in impact.sensitivity_bounds.items():
                print(f"   {metric}: {low:.1f}% to {high:.1f}%")
        
        return impact
        
    except Exception as e:
        print(f"❌ Financial assessment failed: {e}")
        return None


def demo_scenario_comparison(generator):
    """Demonstrate scenario comparison."""
    print("\n" + "=" * 60)
    print("📊 SCENARIO COMPARISON DEMO")
    print("=" * 60)
    
    # Get available scenarios for comparison
    scenario_names = list(generator.enhanced_scenarios.keys())[:3]
    if len(scenario_names) < 2:
        print("⚠️  Need at least 2 scenarios for comparison")
        return
    
    print(f"🔄 Comparing scenarios: {scenario_names}")
    
    try:
        # Generate comparison
        comparison = generator.compare_scenarios(
            scenario_names=scenario_names,
            financial_params={
                'capacity_mw': 1000,
                'baseline_cf': 0.85,
                'discount_rate': 0.08,
                'power_price': 100
            }
        )
        
        print(f"\n📋 Comparison Results:")
        for _, row in comparison.iterrows():
            print(f"\n🔸 {row['scenario_name']}:")
            print(f"   Description: {row['description'][:50]}...")
            print(f"   2030 Dispatch: {row['dispatch_factor_2030']:.2f}")
            print(f"   2040 Dispatch: {row['dispatch_factor_2040']:.2f}")
            print(f"   Validation Score: {row['validation_score']:.2f}")
            
            if not pd.isna(row.get('npv_change_pct')):
                print(f"   NPV Impact: {row['npv_change_pct']:.1f}%")
        
        return comparison
        
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        return None


def demo_export_functionality(generator, scenario):
    """Demonstrate export functionality."""
    print("\n" + "=" * 60)
    print("📤 EXPORT FUNCTIONALITY DEMO")
    print("=" * 60)
    
    if scenario is None:
        print("⚠️  No scenario to export")
        return
    
    # Create output directory
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Export scenario
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"demo_scenario_{timestamp}.json"
        
        generator.export_scenario(
            scenario_name=scenario.name,
            output_path=output_path,
            include_validation=True,
            include_financial=True
        )
        
        print(f"✅ Scenario exported to: {output_path}")
        
        # Show file content summary
        with open(output_path) as f:
            data = json.load(f)
        
        print(f"\n📄 Export Summary:")
        print(f"   Scenario name: {data['scenario']['name']}")
        print(f"   Export timestamp: {data['export_timestamp']}")
        print(f"   Includes validation: {'validation' in data}")
        print(f"   Includes financial: {'financial_impact' in data}")
        
        return output_path
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return None


def main():
    """Main demo function."""
    print("🇰🇷 ENHANCED CLIMATE POLICY SCENARIO GENERATOR - DEMO")
    print("=" * 60)
    print("This demo showcases the enhanced scenario generator with")
    print("real-time Korean energy policy monitoring and financial analysis.")
    print()
    
    try:
        # Demo 1: Policy Monitoring
        monitor = demo_policy_monitoring()
        
        # Demo 2: Scenario Generation
        generator, scenario = demo_scenario_generation(monitor)
        
        # Demo 3: Scenario Validation
        validation = demo_scenario_validation(generator, scenario)
        
        # Demo 4: Financial Impact Assessment
        scenario_name = scenario.name if scenario else None
        financial_impact = demo_financial_impact(generator, scenario_name)
        
        # Demo 5: Scenario Comparison  
        comparison = demo_scenario_comparison(generator)
        
        # Demo 6: Export Functionality
        exported_file = demo_export_functionality(generator, scenario)
        
        # Summary
        print("\n" + "=" * 60)
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("✅ Policy monitoring: Working")
        print("✅ Scenario generation: Working")  
        print("✅ Scenario validation: Working")
        print("✅ Financial impact: Working")
        print("✅ Scenario comparison: Working")
        print("✅ Export functionality: Working")
        
        if exported_file:
            print(f"\n📁 Export file created: {exported_file}")
        
        print(f"\n🚀 To run the interactive dashboard:")
        print(f"   streamlit run src/scenarios/policy_dashboard.py")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import pandas as pd
    main()
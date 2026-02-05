"""
Enhanced Climate Policy Dashboard with Real-time Monitoring and Scenario Analysis.

This Streamlit dashboard provides a comprehensive interface for:
- Real-time Korean energy policy monitoring
- Dynamic scenario generation and validation
- Financial impact assessment
- Interactive scenario comparison
- Policy announcement tracking

Features:
- Live policy feed from Korean sources
- Interactive scenario builder
- Financial impact visualization
- Scenario validation dashboard
- Export capabilities

Usage:
    streamlit run src/scenarios/policy_dashboard.py
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Dict, List, Optional, Any
import asyncio

# Add src to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.scenarios.enhanced_climate_policy_generator import (
    EnhancedScenarioGenerator, 
    PolicyAnnouncement, 
    PolicyType, 
    PolicyImpact,
    FinancialImpact
)
from src.scenarios.korean_policy_monitor import AutomatedPolicyMonitor


def setup_page_config():
    """Setup Streamlit page configuration."""
    st.set_page_config(
        page_title="Korean Climate Policy Dashboard",
        page_icon="🇰🇷",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def create_scenario_generator():
    """Initialize or get scenario generator from session state."""
    if 'scenario_generator' not in st.session_state:
        st.session_state.scenario_generator = EnhancedScenarioGenerator()
        st.session_state.policy_monitor = AutomatedPolicyMonitor()
    
    return st.session_state.scenario_generator


def create_policy_monitor():
    """Initialize or get policy monitor from session state."""
    if 'policy_monitor' not in st.session_state:
        st.session_state.policy_monitor = AutomatedPolicyMonitor()
    
    return st.session_state.policy_monitor


def render_policy_feed():
    """Render the real-time policy feed section."""
    st.header("📰 Real-time Policy Feed")
    
    monitor = create_policy_monitor()
    
    # Get recent announcements
    days = st.slider("Show announcements from last N days:", 1, 90, 30)
    policy_types = st.multiselect(
        "Filter by policy type:",
        options=[pt.value for pt in PolicyType],
        default=[]
    )
    
    try:
        announcements = monitor.get_announcements_summary(days)
        recent_announcements = monitor.policy_monitor.get_recent_announcements(
            days=days,
            policy_types=[PolicyType(pt) for pt in policy_types] if policy_types else None
        )
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Announcements", announcements['total_announcements'])
        with col2:
            st.metric("Sources Monitored", len(announcements['sources']))
        with col3:
            high_impact = sum(announcements['by_impact'].get(level, 0) 
                            for level in ['high', 'transformational'])
            st.metric("High Impact", high_impact)
        with col4:
            st.metric("Last Update", datetime.now().strftime("%H:%M"))
        
        # Announcements table
        if recent_announcements:
            st.subheader("Recent Policy Announcements")
            
            for i, announcement in enumerate(recent_announcements):
                with st.expander(f"📄 {announcement.title} ({announcement.announcement_date.strftime('%Y-%m-%d')})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Description:** {announcement.description}")
                        st.write(f"**Source:** {announcement.source}")
                        st.write(f"**URL:** [{announcement.url}]({announcement.url})")
                    
                    with col2:
                        st.write(f"**Type:** {announcement.policy_type.value}")
                        st.write(f"**Impact:** {announcement.impact_level.value}")
                        st.write(f"**Confidence:** {announcement.confidence_level:.1%}")
                        
                        if announcement.metrics:
                            st.write("**Key Metrics:**")
                            for key, value in announcement.metrics.items():
                                if key != 'confidence_level':
                                    st.write(f"- {key}: {value}")
        else:
            st.info("No recent announcements found.")
    
    except Exception as e:
        st.error(f"Error loading policy feed: {e}")


def render_scenario_builder():
    """Render the scenario builder section."""
    st.header("🔧 Dynamic Scenario Builder")
    
    generator = create_scenario_generator()
    monitor = create_policy_monitor()
    
    # Get available policies
    latest_policies = monitor.get_announcements_summary(90)
    recent_policies = monitor.policy_monitor.get_recent_announcements(days=90)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Create New Scenario")
        
        # Scenario name
        scenario_name = st.text_input("Scenario Name:", "custom_scenario_2026")
        
        # Policy selection
        if recent_policies:
            selected_policies = st.multiselect(
                "Select Policies to Include:",
                options=recent_policies,
                format_func=lambda x: f"{x.title} ({x.policy_type.value})",
                default=recent_policies[:2] if len(recent_policies) >= 2 else recent_policies
            )
        else:
            st.warning("No recent policies available. Using default policies.")
            selected_policies = []
        
        # Description
        description = st.text_area(
            "Scenario Description:",
            "Custom scenario combining selected policy announcements"
        )
        
        # Generate button
        if st.button("🚀 Generate Scenario") and scenario_name:
            try:
                if selected_policies:
                    scenario = generator.generate_scenario(
                        name=scenario_name,
                        policy_combination=selected_policies,
                        description=description
                    )
                    st.success(f"Scenario '{scenario.name}' generated successfully!")
                    
                    # Store in session state
                    if 'generated_scenarios' not in st.session_state:
                        st.session_state.generated_scenarios = []
                    st.session_state.generated_scenarios.append(scenario)
                else:
                    st.error("Please select at least one policy.")
            except Exception as e:
                st.error(f"Error generating scenario: {e}")
    
    with col2:
        st.subheader("Policy Statistics")
        
        if recent_policies:
            # Policy type distribution
            type_counts = {}
            for policy in recent_policies:
                pt = policy.policy_type.value
                type_counts[pt] = type_counts.get(pt, 0) + 1
            
            fig = px.pie(
                values=list(type_counts.values()),
                names=list(type_counts.keys()),
                title="Policy Types"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Show generated scenarios
    if 'generated_scenarios' in st.session_state and st.session_state.generated_scenarios:
        st.subheader("Generated Scenarios")
        
        for scenario in st.session_state.generated_scenarios:
            with st.expander(f"📊 {scenario.name}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Description:** {scenario.description}")
                    st.write(f"**Retirement Year:** {scenario.retirement_year}")
                    
                    # Trajectory preview
                    years = list(range(2024, 2051, 5))
                    trajectory = [scenario.get_value(year) for year in years]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=years,
                        y=trajectory,
                        mode='lines+markers',
                        name='Dispatch Factor'
                    ))
                    fig.update_layout(
                        title="Dispatch Factor Trajectory",
                        xaxis_title="Year",
                        yaxis_title="Dispatch Factor",
                        height=300
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Validation results
                    validation = generator.validate_scenario(scenario)
                    
                    st.metric("Overall Score", f"{validation.overall_score:.2f}")
                    st.metric("Confidence", f"{validation.confidence_score:.2f}")
                    st.metric("Consistency", f"{validation.consistency_score:.2f}")
                    st.metric("Feasibility", f"{validation.feasibility_score:.2f}")
                    
                    if validation.issues:
                        st.write("**Issues:**")
                        for issue in validation.issues:
                            st.write(f"• {issue}")


def render_financial_impact():
    """Render the financial impact assessment section."""
    st.header("💰 Financial Impact Assessment")
    
    generator = create_scenario_generator()
    
    # Get available scenarios
    all_scenarios = generator.list_scenarios()
    if 'generated_scenarios' in st.session_state:
        for scenario in st.session_state.generated_scenarios:
            all_scenarios[scenario.name] = scenario.description
    
    if not all_scenarios:
        st.warning("No scenarios available. Please generate scenarios first.")
        return
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Analysis Parameters")
        
        # Scenario selection
        selected_scenario = st.selectbox(
            "Select Scenario:",
            options=list(all_scenarios.keys()),
            help="Choose scenario to analyze"
        )
        
        # Financial parameters
        capacity_mw = st.number_input(
            "Plant Capacity (MW):",
            min_value=100,
            max_value=5000,
            value=1000,
            step=100
        )
        
        baseline_cf = st.slider(
            "Baseline Capacity Factor:",
            min_value=0.3,
            max_value=0.95,
            value=0.85,
            step=0.05
        )
        
        discount_rate = st.slider(
            "Discount Rate:",
            min_value=0.03,
            max_value=0.15,
            value=0.08,
            step=0.01
        )
        
        power_price = st.number_input(
            "Power Price ($/MWh):",
            min_value=50,
            max_value=200,
            value=100,
            step=10
        )
        
        analysis_years = st.slider(
            "Analysis Period (years):",
            min_value=10,
            max_value=40,
            value=30,
            step=5
        )
        
        # Calculate button
        if st.button("📊 Calculate Impact"):
            try:
                with st.spinner("Calculating financial impact..."):
                    impact = generator.assess_financial_impact(
                        scenario_name=selected_scenario,
                        capacity_mw=capacity_mw,
                        baseline_cf=baseline_cf,
                        discount_rate=discount_rate,
                        power_price=power_price,
                        analysis_years=analysis_years
                    )
                
                st.session_state.current_impact = impact
                st.success("Financial impact calculated!")
                
            except Exception as e:
                st.error(f"Error calculating impact: {e}")
    
    with col2:
        st.subheader("Impact Results")
        
        if 'current_impact' in st.session_state:
            impact = st.session_state.current_impact
            
            # Key metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "NPV Change",
                    f"{impact.npv_change_pct:.1f}%",
                    delta=f"{impact.npv_change_pct:.1f}%"
                )
            with col2:
                st.metric(
                    "Revenue Loss",
                    f"{impact.revenue_loss_pct:.1f}%"
                )
            with col3:
                st.metric(
                    "Risk-Adjusted Return",
                    f"{impact.risk_adjusted_return:.1%}"
                )
            
            # Cashflow impact chart
            if impact.cashflow_impact:
                years = list(impact.cashflow_impact.keys())
                cashflows = list(impact.cashflow_impact.values())
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=years,
                    y=cashflows,
                    name='Annual Cashflow Impact',
                    marker_color='red' if cashflows[0] < 0 else 'green'
                ))
                fig.update_layout(
                    title="Annual Cashflow Impact (First 10 Years)",
                    xaxis_title="Year",
                    yaxis_title="Cashflow Change ($)",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Sensitivity bounds
            if impact.sensitivity_bounds:
                st.subheader("Sensitivity Analysis")
                
                for metric, (low, high) in impact.sensitivity_bounds.items():
                    st.write(f"**{metric}:** {low:.1f}% to {high:.1f}%")
            
            # Break-even analysis
            if impact.break_even_year:
                st.info(f"💡 Break-even year: {impact.break_even_year}")
            else:
                st.info("💡 No break-even within analysis period")
        else:
            st.info("Select a scenario and click 'Calculate Impact' to see results.")


def render_scenario_comparison():
    """Render the scenario comparison section."""
    st.header("📈 Scenario Comparison")
    
    generator = create_scenario_generator()
    
    # Get all scenarios
    all_scenarios = generator.list_scenarios()
    if 'generated_scenarios' in st.session_state:
        for scenario in st.session_state.generated_scenarios:
            all_scenarios[scenario.name] = scenario.description
    
    if len(all_scenarios) < 2:
        st.warning("Need at least 2 scenarios for comparison.")
        return
    
    # Scenario selection
    selected_scenarios = st.multiselect(
        "Select Scenarios to Compare:",
        options=list(all_scenarios.keys()),
        default=list(all_scenarios.keys())[:3] if len(all_scenarios) >= 3 else list(all_scenarios.keys()),
        max_selections=5
    )
    
    if len(selected_scenarios) < 2:
        st.warning("Please select at least 2 scenarios for comparison.")
        return
    
    # Analysis parameters
    with st.expander("Analysis Parameters"):
        col1, col2 = st.columns(2)
        with col1:
            capacity_mw = st.number_input("Capacity (MW):", value=1000, step=100)
            baseline_cf = st.slider("Baseline CF:", value=0.85, step=0.05)
        with col2:
            discount_rate = st.slider("Discount Rate:", value=0.08, step=0.01)
            power_price = st.number_input("Power Price ($/MWh):", value=100, step=10)
    
    # Generate comparison
    if st.button("🔄 Generate Comparison"):
        try:
            with st.spinner("Comparing scenarios..."):
                comparison = generator.compare_scenarios(
                    scenario_names=selected_scenarios,
                    financial_params={
                        'capacity_mw': capacity_mw,
                        'baseline_cf': baseline_cf,
                        'discount_rate': discount_rate,
                        'power_price': power_price
                    }
                )
            
            st.session_state.comparison_data = comparison
            st.success("Comparison completed!")
            
        except Exception as e:
            st.error(f"Error generating comparison: {e}")
    
    # Display comparison
    if 'comparison_data' in st.session_state:
        comparison = st.session_state.comparison_data
        
        # Summary table
        st.subheader("Comparison Summary")
        
        # Format columns for display
        display_df = comparison.copy()
        display_df['description'] = display_df['description'].str[:50] + '...'
        
        if 'npv_change_pct' in display_df.columns:
            display_df['npv_change_pct'] = display_df['npv_change_pct'].round(1)
        if 'revenue_loss_pct' in display_df.columns:
            display_df['revenue_loss_pct'] = display_df['revenue_loss_pct'].round(1)
        
        st.dataframe(display_df, use_container_width=True)
        
        # Visualization
        col1, col2 = st.columns(2)
        
        with col1:
            if 'npv_change_pct' in comparison.columns:
                fig = px.bar(
                    comparison,
                    x='scenario_name',
                    y='npv_change_pct',
                    title="NPV Impact Comparison",
                    labels={'npv_change_pct': 'NPV Change (%)', 'scenario_name': 'Scenario'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'validation_score' in comparison.columns:
                fig = px.scatter(
                    comparison,
                    x='npv_change_pct' if 'npv_change_pct' in comparison.columns else 'dispatch_factor_2030',
                    y='validation_score',
                    size='is_valid',
                    hover_name='scenario_name',
                    title="Risk vs Validation Score",
                    labels={
                        'x': 'Financial Impact (%)',
                        'y': 'Validation Score',
                        'is_valid': 'Valid'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)


def render_export_section():
    """Render the export functionality section."""
    st.header("📤 Export Results")
    
    generator = create_scenario_generator()
    
    export_type = st.selectbox(
        "Select Export Type:",
        ["Individual Scenario", "Scenario Comparison", "Policy Feed", "All Results"]
    )
    
    if export_type == "Individual Scenario":
        all_scenarios = generator.list_scenarios()
        if 'generated_scenarios' in st.session_state:
            for scenario in st.session_state.generated_scenarios:
                all_scenarios[scenario.name] = scenario.description
        
        selected_scenario = st.selectbox("Select Scenario:", options=list(all_scenarios.keys()))
        
        include_validation = st.checkbox("Include validation results", value=True)
        include_financial = st.checkbox("Include financial analysis", value=True)
        
        if st.button("Export Scenario"):
            try:
                output_path = Path(f"output/{selected_scenario}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                generator.export_scenario(
                    selected_scenario,
                    output_path,
                    include_validation=include_validation,
                    include_financial=include_financial
                )
                st.success(f"Scenario exported to {output_path}")
            except Exception as e:
                st.error(f"Export failed: {e}")
    
    elif export_type == "Scenario Comparison":
        if 'comparison_data' in st.session_state:
            if st.button("Export Comparison"):
                try:
                    output_path = Path(f"output/comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                    st.session_state.comparison_data.to_csv(output_path, index=False)
                    st.success(f"Comparison exported to {output_path}")
                except Exception as e:
                    st.error(f"Export failed: {e}")
        else:
            st.warning("No comparison data available. Generate a comparison first.")
    
    elif export_type == "Policy Feed":
        if st.button("Export Policy Feed"):
            try:
                monitor = create_policy_monitor()
                announcements = monitor.policy_monitor.announcements
                
                export_data = {
                    'export_timestamp': datetime.now().isoformat(),
                    'total_announcements': len(announcements),
                    'announcements': [a.to_dict() for a in announcements]
                }
                
                output_path = Path(f"output/policy_feed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                output_path.parent.mkdir(exist_ok=True)
                
                with open(output_path, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                
                st.success(f"Policy feed exported to {output_path}")
            except Exception as e:
                st.error(f"Export failed: {e}")


def main():
    """Main dashboard function."""
    setup_page_config()
    
    # Sidebar navigation
    st.sidebar.title("🇰🇷 Korean Climate Policy Dashboard")
    st.sidebar.markdown("Real-time monitoring and scenario analysis")
    
    page = st.sidebar.selectbox(
        "Navigate:",
        ["📰 Policy Feed", "🔧 Scenario Builder", "💰 Financial Impact", "📈 Comparison", "📤 Export"]
    )
    
    # Initialize components
    generator = create_scenario_generator()
    monitor = create_policy_monitor()
    
    # Sidebar info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### System Status")
    
    try:
        # System status indicators
        policies_count = len(monitor.policy_monitor.announcements)
        scenarios_count = len(generator.enhanced_scenarios)
        
        st.sidebar.metric("Policies Tracked", policies_count)
        st.sidebar.metric("Scenarios Available", scenarios_count)
        
        if 'generated_scenarios' in st.session_state:
            st.sidebar.metric("Custom Scenarios", len(st.session_state.generated_scenarios))
        
        # Last update time
        st.sidebar.write(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        st.sidebar.error(f"Status check failed: {e}")
    
    # Main content
    if page == "📰 Policy Feed":
        render_policy_feed()
    elif page == "🔧 Scenario Builder":
        render_scenario_builder()
    elif page == "💰 Financial Impact":
        render_financial_impact()
    elif page == "📈 Comparison":
        render_scenario_comparison()
    elif page == "📤 Export":
        render_export_section()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        **About:**  
        Enhanced climate policy scenario generator with real-time Korean energy policy monitoring.
        
        **Data Sources:**  
        - MOTIE (Ministry of Trade, Industry & Energy)  
        - Climate Ministry  
        - Korea Herald  
        - Official government announcements
        """
    )


if __name__ == "__main__":
    main()
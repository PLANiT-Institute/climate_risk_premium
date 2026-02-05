"""
Revenue Impact Analysis: 11th Basic Plan + Physical Risk
"""
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.scenarios.korea_power_plan import load_korea_power_plan_scenarios
from src.risk.physical import get_physical_risk_scenario, apply_physical
from src.risk.transition import apply_transition
from src.financials.cashflow import compute_cashflows_timeseries
from src.scenarios import TransitionScenario

def run_analysis():
    print("=" * 70)
    print("Revenue Impact Analysis: 11th Basic Plan & Physical Risk")
    print("=" * 70)

    # 1. Setup Scenarios
    # Load power plan scenarios
    power_plans = load_korea_power_plan_scenarios(project_root / "data/raw/korea_power_plan.csv")
    
    # Define scenarios to compare
    scenarios = {
        "Baseline (10th Plan)": {
            "plan": power_plans["official_10th_plan"],
            "physical": "Low"
        },
        "11th Plan (Policy Only)": {
            "plan": power_plans["official_11th_plan"],
            "physical": "Low"
        },
        "11th Plan + High Physical Risk": {
            "plan": power_plans["official_11th_plan"],
            "physical": "High"
        },
        "11th Plan + Extreme Physical Risk": {
            "plan": power_plans["official_11th_plan"],
            "physical": "Extreme"
        }
    }

    # Plant Parameters (Samcheok Blue Power)
    plant_params = {
        "capacity_mw": 2100,
        "capacity_factor": 0.85, # Design max
        "operating_years": 30,
        "cod_year": 2024,
        "power_price_per_mwh": 120, # Long-term assumption
        "fixed_opex_per_kw_year": 45,
        "variable_opex_per_mwh": 5.0,
    }

    # Dummy Transition Scenario (needed for carbon price, but we focus on revenue)
    dummy_transition = TransitionScenario(
        name="Base",
        dispatch_priority_penalty=0.0,
        retirement_years=30,
        carbon_price_2025=20,
        carbon_price_2030=40,
        carbon_price_2040=80,
        carbon_price_2050=120
    )

    results = {}

    # 2. Calculate Cash Flows
    for name, config in scenarios.items():
        print(f"Analyzing: {name}...")
        
        # Get Physical Scenario
        phys_scenario = get_physical_risk_scenario(config["physical"])
        phys_adj = apply_physical(plant_params, phys_scenario)
        
        # Get Transition Adjustments (Power Plan)
        trans_adj = apply_transition(
            plant_params, 
            dummy_transition, 
            korea_plan_scenario=config["plan"]
        )

        # Compute Cash Flows
        cf = compute_cashflows_timeseries(
            plant_params,
            dummy_transition,
            trans_adj,
            phys_adj,
            start_year=2024
        )
        
        # Store total revenue (NPV at 0% for simplicity, or just sum)
        # Let's use Sum of Revenue for the waterfall
        results[name] = np.sum(cf.revenue) / 1e9 # Billions KRW (assuming price is KRW/USD mixed, let's say USD for now, so Millions USD)
        # Wait, price is 120. If USD, 1e9 is Billions.
        # If KRW, 120 is too low. 120 USD/MWh is reasonable.
        # So results are in Billion USD.

    # 3. Visualize (Waterfall Chart)
    print("\nGenerating Waterfall Chart...")
    
    # Prepare Data
    baseline_rev = results["Baseline (10th Plan)"]
    plan_11_rev = results["11th Plan (Policy Only)"]
    phys_high_rev = results["11th Plan + High Physical Risk"]
    phys_ext_rev = results["11th Plan + Extreme Physical Risk"]

    # Deltas
    delta_policy = plan_11_rev - baseline_rev
    delta_phys_high = phys_high_rev - plan_11_rev
    # For the chart, we want to show: Baseline -> Policy Impact -> Physical Impact -> Final
    
    # Let's show "11th Plan + High Risk" as the final target for the main waterfall
    
    labels = ['Baseline\n(10th Plan)', '11th Plan\nImpact', 'Physical Risk\n(High)', 'Final\nRevenue']
    values = [baseline_rev, delta_policy, delta_phys_high, phys_high_rev]
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Cumulative sum for waterfall
    # Step 1: Baseline (Bar)
    # Step 2: Policy Impact (Red Bar, starting from Baseline)
    # Step 3: Physical Impact (Red Bar, starting from Baseline + Policy)
    # Step 4: Final (Bar)
    
    # Positions
    x = np.arange(len(labels))
    
    # Bar 1: Baseline
    ax.bar(x[0], values[0], color='lightgray', edgecolor='black')
    
    # Bar 2: Policy Impact
    # Bottom is Baseline + Delta (since delta is negative, bottom is lower? No.)
    # If delta is negative, we want bar from Baseline down to Baseline+Delta.
    # Bottom = Baseline + Delta, Height = -Delta
    ax.bar(x[1], -values[1], bottom=values[0] + values[1], color='#ff9999', edgecolor='black', label='Loss')
    
    # Bar 3: Physical Impact
    # Start from (Baseline + Delta_Policy)
    current_level = values[0] + values[1]
    ax.bar(x[2], -values[2], bottom=current_level + values[2], color='#ff4444', edgecolor='black')
    
    # Bar 4: Final
    ax.bar(x[3], values[3], color='skyblue', edgecolor='black')
    
    # Connectors
    # Plot lines connecting bars
    
    # Add labels
    for i, v in enumerate(values):
        if i == 0 or i == 3:
            height = v
            ax.text(i, height + 0.1, f"${height:,.1f}B", ha='center', va='bottom', fontweight='bold')
        else:
            # For negative deltas
            loss = -v
            # Position text in the middle of the red bar
            # bottom is (prev_level - loss)
            # top is prev_level
            # mid = prev_level - loss/2
            
            # Need to calculate prev level dynamically
            if i == 1: prev = values[0]
            elif i == 2: prev = values[0] + values[1]
            
            mid = prev + v/2 # v is negative
            ax.text(i, mid, f"-${loss:,.1f}B", ha='center', va='center', color='white', fontweight='bold')

    ax.set_ylabel("Total Lifetime Revenue (Billion USD)")
    ax.set_title("Revenue Impact: 11th Basic Plan & Physical Risk (High)")
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save
    output_path = project_root / "data/processed/revenue_waterfall.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    print(f"Chart saved to: {output_path}")
    
    # Print Summary Table
    print("\n" + "="*40)
    print("SUMMARY (Lifetime Revenue)")
    print("="*40)
    print(f"{'Scenario':<35} | {'Revenue ($B)':<12} | {'Change':<10}")
    print("-" * 65)
    for name, rev in results.items():
        change = rev - baseline_rev
        pct = (change / baseline_rev) * 100
        print(f"{name:<35} | ${rev:,.1f}       | {pct:+.1f}%")
    print("="*40)

if __name__ == "__main__":
    run_analysis()

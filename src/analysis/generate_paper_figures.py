
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
from src.pipeline.runner import CRPModelRunner
from src.risk.credit_rating import calculate_rating_metrics_from_financials, assess_credit_rating

# Set professional style
plt.style.use('seaborn-v0_8-paper')
sns.set_context("paper", font_scale=1.4)
sns.set_style("whitegrid")

# Custom colors
COLORS = {
    "Baseline": "#2c3e50",
    "Transition": "#e74c3c",
    "Physical": "#f39c12",
    "Combined": "#c0392b",
    "Positive": "#27ae60",
    "Negative": "#c0392b",
    "Neutral": "#95a5a6"
}

def setup_runner():
    base_dir = Path(".")
    runner = CRPModelRunner(base_dir)
    return runner

def run_scenarios(runner):
    scenarios = [
        {"name": "Baseline (10th Plan)", "transition": "baseline", "physical": "baseline", "power_plan": "official_10th_plan"},
        {"name": "11th Plan Only", "transition": "baseline", "physical": "baseline", "power_plan": "official_11th_plan"},
        {"name": "11th Plan + High Physical", "transition": "baseline", "physical": "high_physical", "power_plan": "official_11th_plan"},
        {"name": "11th Plan + Extreme Physical", "transition": "baseline", "physical": "extreme_physical", "power_plan": "official_11th_plan"},
    ]
    return runner.run_multi_scenario(scenarios)

def plot_npv_comparison(results, output_dir):
    """Figure 1: NPV Comparison across scenarios."""
    data = []
    for name, res in results.items():
        data.append({"Scenario": name, "NPV ($B)": res.metrics.npv / 1e9})
    
    df = pd.DataFrame(data)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Color mapping
    colors = [COLORS["Baseline"] if "Baseline" in x else 
              COLORS["Transition"] if "Only" in x else 
              COLORS["Combined"] for x in df["Scenario"]]
    
    bars = ax.bar(df["Scenario"], df["NPV ($B)"], color=colors, width=0.6)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + (0.1 if height > 0 else -0.3),
                f'${height:.1f}B',
                ha='center', va='bottom' if height > 0 else 'top', fontsize=12, fontweight='bold')
    
    ax.axhline(0, color='black', linewidth=1)
    ax.set_ylabel("Net Present Value (Billions USD)", fontweight='bold')
    ax.set_title("Figure 1: Impact of Policy and Physical Risks on Project NPV", fontweight='bold', pad=20)
    
    # Formatting
    plt.xticks(rotation=15, ha='right')
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.xaxis.grid(False)
    
    plt.tight_layout()
    plt.savefig(output_dir / "fig1_npv_comparison.png", dpi=300, bbox_inches='tight')
    plt.close()

def plot_waterfall(results, output_dir):
    """Figure 2: Cash Flow Waterfall for Combined Scenario."""
    # Use "11th Plan + Extreme Physical"
    target_scenario = "11th Plan + Extreme Physical"
    if target_scenario not in results:
        return
        
    res = results[target_scenario]
    cf = res.cashflow
    
    # Aggregate lifetime values
    revenue = cf.revenue.sum() / 1e9
    fuel = -cf.fuel_costs.sum() / 1e9
    opex = -(cf.variable_opex.sum() + cf.fixed_opex.sum()) / 1e9
    carbon = -cf.carbon_costs.sum() / 1e9
    outage = -cf.lost_revenue_from_outages.sum() / 1e9 # Physical risk impact
    ebitda = cf.ebitda.sum() / 1e9
    depr = -cf.depreciation.sum() / 1e9
    interest = -cf.interest_expense.sum() / 1e9
    tax = -cf.tax_expense.sum() / 1e9
    net_income = cf.net_income.sum() / 1e9
    
    # Waterfall data
    steps = ["Revenue", "Fuel Costs", "O&M Costs", "Carbon Costs", "Physical Outage", "EBITDA", 
             "Depreciation", "Interest", "Tax", "Net Income"]
    values = [revenue, fuel, opex, carbon, outage, 0, depr, interest, tax, 0]
    
    # Calculate subtotals
    # EBITDA is a subtotal, Net Income is a final total
    # We need to structure it for a waterfall chart
    # Start -> Changes -> Subtotal -> Changes -> Final
    
    # Let's simplify: Revenue -> Costs -> EBITDA -> Financials -> Net Income
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Cumulative sum for positioning
    # We need to handle "total" bars differently
    
    # Custom waterfall logic
    running_total = 0
    x_pos = np.arange(len(steps))
    
    for i, (step, val) in enumerate(zip(steps, values)):
        if step == "EBITDA":
            # Subtotal bar
            total = revenue + fuel + opex + carbon + outage
            ax.bar(i, total, color=COLORS["Baseline"], label="Subtotal")
            ax.text(i, total + 0.5, f"${total:.1f}B", ha='center', va='bottom', fontweight='bold')
            running_total = total
        elif step == "Net Income":
            # Final bar
            total = running_total + depr + interest + tax
            ax.bar(i, total, color=COLORS["Baseline"], label="Total")
            ax.text(i, total + 0.5, f"${total:.1f}B", ha='center', va='bottom', fontweight='bold')
        else:
            # Change bar
            color = COLORS["Positive"] if val >= 0 else COLORS["Negative"]
            ax.bar(i, val, bottom=running_total, color=color)
            # Label
            label_y = running_total + val + (0.5 if val > 0 else -1.5)
            ax.text(i, label_y, f"{val:+.1f}", ha='center', va='bottom' if val > 0 else 'top', fontsize=10)
            running_total += val
            
    ax.set_xticks(x_pos)
    ax.set_xticklabels(steps, rotation=30, ha='right')
    ax.set_ylabel("Lifetime Value (Billions USD)", fontweight='bold')
    ax.set_title(f"Figure 2: Lifetime Cash Flow Waterfall ({target_scenario})", fontweight='bold', pad=20)
    
    ax.axhline(0, color='black', linewidth=0.8)
    ax.yaxis.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(output_dir / "fig2_waterfall.png", dpi=300, bbox_inches='tight')
    plt.close()

def plot_rating_migration(results, output_dir):
    """Figure 3: Credit Rating Migration."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    rating_map = {"AAA": 1, "AA": 2, "A": 3, "BBB": 4, "BB": 5, "B": 6, "CCC": 7}
    reverse_map = {v: k for k, v in rating_map.items()}
    
    for name, res in results.items():
        cf = res.cashflow
        years = cf.years
        
        # Filter years to 2024-2040
        mask = (years >= 2024) & (years <= 2040)
        years_plot = years[mask]
        
        ratings_vals = []
        
        # Plant params (simplified retrieval)
        # In a real script we'd pass these properly, but here we estimate
        capacity_mw = 2100
        total_capex = 4.9e9 # $4.9B
        debt_fraction = 0.7
        equity_fraction = 0.3
        debt_interest = 0.06 # 6%
        
        total_debt = total_capex * debt_fraction
        total_equity = total_capex * equity_fraction
        
        # Calculate rating for each year
        for i, year in enumerate(years):
            if not mask[i]: continue
            
            ebitda = cf.ebitda[i]
            interest = cf.interest_expense[i]
            
            # Amortize debt
            # Simplified: assume linear paydown for leverage ratio calculation
            # (This is an approximation for the plot)
            current_debt = total_debt * (1 - (i / 30)) 
            if current_debt < 0: current_debt = 0
            
            # Metrics
            metrics = calculate_rating_metrics_from_financials(
                capacity_mw=capacity_mw,
                ebitda=ebitda,
                fixed_assets=total_capex, # Gross fixed assets
                interest_expense=interest if interest > 0 else 1e-6,
                total_debt=current_debt,
                cash_and_equivalents=ebitda * 0.1,
                total_equity=total_equity,
                total_assets=total_capex
            )
            
            assessment = assess_credit_rating(metrics)
            ratings_vals.append(assessment.overall_rating.numeric_score)
        
        # Style
        linestyle = '-'
        if "Baseline" in name:
            color = COLORS["Baseline"]
            linewidth = 3
        elif "Extreme" in name:
            color = COLORS["Combined"]
            linewidth = 3
        else:
            color = COLORS["Neutral"]
            linewidth = 1.5
            linestyle = '--'
            
        ax.step(years_plot, ratings_vals, where='post', label=name, color=color, linewidth=linewidth, linestyle=linestyle)
    
    # Investment Grade Line
    ax.axhline(4.5, color='black', linestyle=':', linewidth=1, label="Investment Grade Threshold")
    
    # Formatting
    ax.set_yticks(list(reverse_map.keys()))
    ax.set_yticklabels(list(reverse_map.values()))
    ax.invert_yaxis() # AAA at top
    
    ax.set_xlabel("Year", fontweight='bold')
    ax.set_ylabel("Credit Rating (KIS Scale)", fontweight='bold')
    ax.set_title("Figure 3: Credit Rating Migration Paths", fontweight='bold', pad=20)
    
    ax.legend(loc='lower left')
    ax.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(output_dir / "fig3_rating_migration.png", dpi=300, bbox_inches='tight')
    plt.close()

def main():
    output_dir = Path("data/processed/figures")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Setting up model...")
    runner = setup_runner()
    
    print("Running scenarios...")
    results = run_scenarios(runner)
    
    print("Generating Figure 1: NPV Comparison...")
    plot_npv_comparison(results, output_dir)
    
    print("Generating Figure 2: Waterfall...")
    plot_waterfall(results, output_dir)
    
    print("Generating Figure 3: Rating Migration...")
    plot_rating_migration(results, output_dir)
    
    print(f"Done! Figures saved to {output_dir}")

if __name__ == "__main__":
    main()

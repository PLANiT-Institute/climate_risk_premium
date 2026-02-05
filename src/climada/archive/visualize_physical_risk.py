"""
Physical Risk Model Visualization.

Creates visualizations of model inputs and outputs for the
Samcheok Blue Power Plant physical risk assessment.

Run: python -m src.climada.visualize_physical_risk
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from pathlib import Path

from .literature_parameters import (
    WILDFIRE_BASE_RATE,
    FLOOD_BASE_RATE,
    SLR_DERATE_PER_METER,
    PROJECTIONS,
    calculate_physical_risk,
)


def create_input_visualization(save_path: str = None):
    """
    Visualize model INPUTS: baseline parameters and climate projections.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Physical Risk Model INPUTS\nSamcheok Blue Power Plant',
                 fontsize=14, fontweight='bold')

    # =========================================================================
    # Panel 1: Baseline Parameters (Top Left)
    # =========================================================================
    ax1 = axes[0, 0]
    params = {
        'Wildfire\n(0.055%)': WILDFIRE_BASE_RATE * 100,
        'Flood\n(0.003%)': FLOOD_BASE_RATE * 100,
        'SLR Derate\n(per 1m)': SLR_DERATE_PER_METER * 100,
    }
    colors = ['#ff6b6b', '#4dabf7', '#69db7c']
    bars = ax1.bar(params.keys(), params.values(), color=colors, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Annual Rate (%)', fontsize=11)
    ax1.set_title('Baseline Parameters (2024)', fontsize=12, fontweight='bold')
    ax1.set_ylim(0, max(params.values()) * 1.3)

    # Add value labels on bars
    for bar, val in zip(bars, params.values()):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002,
                f'{val:.4f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Add source annotations
    sources = ['Kim et al. (2025)\nNatural Hazards',
               'Kim et al. (2024)\nWater',
               'Van Vliet (2016)\nNature Clim. Change']
    for i, (bar, src) in enumerate(zip(bars, sources)):
        ax1.text(bar.get_x() + bar.get_width()/2, -0.008, src,
                ha='center', va='top', fontsize=8, color='gray')

    # =========================================================================
    # Panel 2: Climate Multipliers (Top Right)
    # =========================================================================
    ax2 = axes[0, 1]
    years = [2024, 2030, 2040, 2050, 2060]

    # Extract wildfire multipliers
    rcp45_wild = [1.0, 1.2, 1.5, 1.5, 2.0]
    rcp85_wild = [1.0, 1.3, 2.0, 2.0, 4.0]

    x = np.arange(len(years))
    width = 0.35

    bars1 = ax2.bar(x - width/2, rcp45_wild, width, label='RCP4.5',
                    color='#74c0fc', edgecolor='black', linewidth=1)
    bars2 = ax2.bar(x + width/2, rcp85_wild, width, label='RCP8.5',
                    color='#ff8787', edgecolor='black', linewidth=1)

    ax2.set_xlabel('Year', fontsize=11)
    ax2.set_ylabel('Wildfire Multiplier', fontsize=11)
    ax2.set_title('Climate Change Multipliers for Wildfire', fontsize=12, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(years)
    ax2.legend()
    ax2.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, label='Baseline')
    ax2.set_ylim(0, 4.5)

    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f'{bar.get_height():.1f}x', ha='center', va='bottom', fontsize=9)

    # =========================================================================
    # Panel 3: Sea Level Rise Projections (Bottom Left)
    # =========================================================================
    ax3 = axes[1, 0]
    slr_data = {
        'Year': [2024, 2030, 2040, 2050, 2060],
        'RCP4.5': [0.0, 0.10, 0.19, 0.19, 0.19],
        'RCP8.5': [0.0, 0.10, 0.25, 0.25, 0.73],
    }

    ax3.plot(slr_data['Year'], slr_data['RCP4.5'], 'o-', color='#74c0fc',
             linewidth=2, markersize=8, label='RCP4.5')
    ax3.plot(slr_data['Year'], slr_data['RCP8.5'], 's-', color='#ff8787',
             linewidth=2, markersize=8, label='RCP8.5')

    ax3.set_xlabel('Year', fontsize=11)
    ax3.set_ylabel('Sea Level Rise (meters)', fontsize=11)
    ax3.set_title('Sea Level Rise Projections (IPCC AR6)', fontsize=12, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0, 0.85)

    # =========================================================================
    # Panel 4: Compound Multiplier (Bottom Right)
    # =========================================================================
    ax4 = axes[1, 1]
    compound_data = {
        'Year': [2024, 2030, 2040, 2050, 2060],
        'RCP4.5': [1.0, 1.0, 1.0, 1.05, 1.05],
        'RCP8.5': [1.0, 1.05, 1.05, 1.10, 1.15],
    }

    ax4.plot(compound_data['Year'], compound_data['RCP4.5'], 'o-', color='#74c0fc',
             linewidth=2, markersize=8, label='RCP4.5')
    ax4.plot(compound_data['Year'], compound_data['RCP8.5'], 's-', color='#ff8787',
             linewidth=2, markersize=8, label='RCP8.5')

    ax4.set_xlabel('Year', fontsize=11)
    ax4.set_ylabel('Compound Multiplier', fontsize=11)
    ax4.set_title('Compound Risk Multiplier', fontsize=12, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(0.95, 1.25)
    ax4.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)
    ax4.axhline(y=1.25, color='red', linestyle=':', alpha=0.5, label='Max (1.25x)')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved input visualization to: {save_path}")

    return fig


def create_output_visualization(save_path: str = None):
    """
    Visualize model OUTPUTS: calculated physical risk by scenario and year.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Physical Risk Model OUTPUTS\nSamcheok Blue Power Plant',
                 fontsize=14, fontweight='bold')

    # Calculate risk for all scenarios
    scenarios = [
        ("baseline", 2024, "current"),
        ("rcp45_2030", 2030, "RCP4.5"),
        ("rcp45_2040", 2040, "RCP4.5"),
        ("rcp45_2050", 2050, "RCP4.5"),
        ("rcp45_2060", 2060, "RCP4.5"),
        ("rcp85_2030", 2030, "RCP8.5"),
        ("rcp85_2040", 2040, "RCP8.5"),
        ("rcp85_2050", 2050, "RCP8.5"),
        ("rcp85_2060", 2060, "RCP8.5"),
    ]

    results = []
    for name, year, rcp in scenarios:
        r = calculate_physical_risk(year, rcp)
        results.append({
            'name': name,
            'year': year,
            'rcp': rcp,
            'wildfire': r.wildfire_rate * 100,
            'flood': r.flood_rate * 100,
            'slr': r.slr_derate * 100,
            'compound': r.compound_mult,
            'total_outage': r.total_outage * 100,
            'total_derate': r.total_derate * 100,
            'cf_reduction': r.cf_reduction * 100,
        })

    df = pd.DataFrame(results)

    # =========================================================================
    # Panel 1: Total CF Reduction by Scenario (Top Left)
    # =========================================================================
    ax1 = axes[0, 0]

    rcp45_data = df[df['rcp'].isin(['current', 'RCP4.5'])]
    rcp85_data = df[df['rcp'].isin(['current', 'RCP8.5'])]

    ax1.plot(rcp45_data['year'], rcp45_data['cf_reduction'], 'o-',
             color='#74c0fc', linewidth=2, markersize=10, label='RCP4.5')
    ax1.plot(rcp85_data['year'], rcp85_data['cf_reduction'], 's-',
             color='#ff8787', linewidth=2, markersize=10, label='RCP8.5')

    ax1.set_xlabel('Year', fontsize=11)
    ax1.set_ylabel('Capacity Factor Reduction (%)', fontsize=11)
    ax1.set_title('Total Physical Risk Impact on Capacity Factor', fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 0.5)

    # Add annotations for key points
    max_risk = df[df['cf_reduction'] == df['cf_reduction'].max()].iloc[0]
    ax1.annotate(f'{max_risk["cf_reduction"]:.3f}%\n(max)',
                xy=(max_risk['year'], max_risk['cf_reduction']),
                xytext=(max_risk['year']-5, max_risk['cf_reduction']+0.08),
                fontsize=9, ha='center',
                arrowprops=dict(arrowstyle='->', color='gray'))

    # =========================================================================
    # Panel 2: Stacked Hazard Breakdown (Top Right)
    # =========================================================================
    ax2 = axes[0, 1]

    # Use only RCP8.5 for clarity
    rcp85_only = df[df['rcp'] == 'RCP8.5'].sort_values('year')
    if len(rcp85_only) == 0:
        rcp85_only = df[df['rcp'] == 'current']

    years = rcp85_only['year'].values
    wildfire = rcp85_only['wildfire'].values
    flood = rcp85_only['flood'].values
    slr = rcp85_only['slr'].values

    x = np.arange(len(years))
    width = 0.6

    ax2.bar(x, wildfire, width, label='Wildfire', color='#ff6b6b', edgecolor='black')
    ax2.bar(x, flood, width, bottom=wildfire, label='Flood', color='#4dabf7', edgecolor='black')
    ax2.bar(x, slr, width, bottom=wildfire+flood, label='SLR Derate', color='#69db7c', edgecolor='black')

    ax2.set_xlabel('Year', fontsize=11)
    ax2.set_ylabel('Risk Rate (%)', fontsize=11)
    ax2.set_title('Hazard Breakdown (RCP8.5 Scenario)', fontsize=12, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(years)
    ax2.legend(loc='upper left')

    # =========================================================================
    # Panel 3: Comparison Table (Bottom Left)
    # =========================================================================
    ax3 = axes[1, 0]
    ax3.axis('off')

    # Create a summary table
    table_data = []
    for _, row in df.iterrows():
        table_data.append([
            row['name'],
            f"{row['wildfire']:.4f}%",
            f"{row['flood']:.5f}%",
            f"{row['slr']:.4f}%",
            f"{row['compound']:.2f}x",
            f"{row['cf_reduction']:.4f}%",
        ])

    columns = ['Scenario', 'Wildfire', 'Flood', 'SLR', 'Compound', 'Total CF Reduction']

    table = ax3.table(cellText=table_data, colLabels=columns,
                      loc='center', cellLoc='center',
                      colColours=['#e9ecef']*6)
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.5)

    # Color the header row
    for i in range(len(columns)):
        table[(0, i)].set_facecolor('#4dabf7')
        table[(0, i)].set_text_props(fontweight='bold', color='white')

    ax3.set_title('Physical Risk Summary Table', fontsize=12, fontweight='bold', y=0.98)

    # =========================================================================
    # Panel 4: Key Insights (Bottom Right)
    # =========================================================================
    ax4 = axes[1, 1]
    ax4.axis('off')

    insights = """
    KEY FINDINGS
    ════════════════════════════════════════

    BASELINE 2024:
      Total Physical Risk: ~0.06%
      (Negligible impact on capacity factor)

    RCP4.5 2060 (Moderate Climate):
      Total Physical Risk: ~0.16%
      Wildfire dominates, SLR minor

    RCP8.5 2060 (High Climate):
      Total Physical Risk: ~0.44%
      Wildfire 4x baseline, SLR significant

    ════════════════════════════════════════

    IMPORTANT CONTEXT:
    • Physical risk is MODEST (<0.5% even worst-case)
    • Transition risk (policy phase-out) is far greater
    • Values are Korea-specific (not California)
<<<<<<< HEAD
    • All citations verified
=======
    • All citations verified December 2024
>>>>>>> 7b1507166a09149c835e7a055a114db44cb2809e
    """

    ax4.text(0.05, 0.95, insights, transform=ax4.transAxes,
             fontsize=10, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='#f8f9fa', edgecolor='#dee2e6'))

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved output visualization to: {save_path}")

    return fig


def create_combined_visualization(save_dir: str = None):
    """
    Create both input and output visualizations.

    Args:
        save_dir: Directory to save figures (optional)
    """
    if save_dir:
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        input_path = str(save_path / "physical_risk_inputs.png")
        output_path = str(save_path / "physical_risk_outputs.png")
    else:
        input_path = None
        output_path = None

    print("=" * 60)
    print("PHYSICAL RISK MODEL VISUALIZATION")
    print("Samcheok Blue Power Plant - Korea")
    print("=" * 60)

    print("\nCreating INPUT visualization...")
    fig1 = create_input_visualization(input_path)

    print("Creating OUTPUT visualization...")
    fig2 = create_output_visualization(output_path)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    # Print summary
    print("\nBASELINE PARAMETERS (2024):")
    print(f"  Wildfire outage rate: {WILDFIRE_BASE_RATE:.5f} ({WILDFIRE_BASE_RATE*100:.4f}%)")
    print(f"  Flood outage rate:    {FLOOD_BASE_RATE:.6f} ({FLOOD_BASE_RATE*100:.5f}%)")
    print(f"  SLR derate per meter: {SLR_DERATE_PER_METER:.4f} ({SLR_DERATE_PER_METER*100:.3f}%)")

    print("\nPHYSICAL RISK BY SCENARIO:")
    for name, year, rcp in [
        ("Baseline", 2024, "current"),
        ("RCP4.5 2050", 2050, "RCP4.5"),
        ("RCP8.5 2060", 2060, "RCP8.5"),
    ]:
        r = calculate_physical_risk(year, rcp)
        print(f"  {name}: {r.cf_reduction*100:.4f}% CF reduction")

    return fig1, fig2


if __name__ == "__main__":
    # Run visualization
    import os

    # Determine output directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    output_dir = project_root / "outputs" / "visualizations"

    create_combined_visualization(str(output_dir))
    plt.show()

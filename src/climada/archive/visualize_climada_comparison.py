"""
Visualization comparing CLIMADA vs Literature-based physical risk.

Creates comparison charts for the Samcheok Blue Power Plant analysis.

Run: python -m src.climada.visualize_climada_comparison
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path


def create_comparison_visualization(save_path: str = None):
    """
    Create visualization comparing CLIMADA and Literature risk estimates.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('CLIMADA vs Literature: Physical Risk Comparison\nSamcheok Blue Power Plant (37.44°N, 129.17°E)',
                 fontsize=14, fontweight='bold')

    # Data
    hazards = ['Wildfire', 'Flood', 'Tropical\nCyclone', 'TOTAL']
    climada_values = [0.0082, 0.0000, 0.0205, 0.0288]  # percentages
    literature_values = [0.0550, 0.0030, 0.0000, 0.0580]  # percentages

    # =========================================================================
    # Panel 1: Bar Chart Comparison (Top Left)
    # =========================================================================
    ax1 = axes[0, 0]
    x = np.arange(len(hazards))
    width = 0.35

    bars1 = ax1.bar(x - width/2, climada_values, width, label='CLIMADA',
                    color='#4dabf7', edgecolor='black', linewidth=1.5)
    bars2 = ax1.bar(x + width/2, literature_values, width, label='Literature',
                    color='#ff8787', edgecolor='black', linewidth=1.5)

    ax1.set_ylabel('Annual Outage Rate (%)', fontsize=11)
    ax1.set_title('Physical Risk by Source', fontsize=12, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(hazards)
    ax1.legend()
    ax1.set_ylim(0, 0.08)

    # Add value labels
    for bar in bars1:
        if bar.get_height() > 0:
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002,
                    f'{bar.get_height():.3f}%', ha='center', va='bottom', fontsize=9)
    for bar in bars2:
        if bar.get_height() > 0:
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002,
                    f'{bar.get_height():.3f}%', ha='center', va='bottom', fontsize=9)

    # =========================================================================
    # Panel 2: Data Source Info (Top Right)
    # =========================================================================
    ax2 = axes[0, 1]
    ax2.axis('off')

    info_text = """
    CLIMADA DATA SOURCES
    ════════════════════════════════════════

    Resolution: ~4.5 km (150 arcsec)
    Location:   37.4404°N, 129.1671°E

    ┌─────────────────────────────────────────┐
    │ WILDFIRE                                │
    │ Source: NASA FIRMS (MODIS/VIIRS)        │
    │ Period: 2001-2020                       │
    │ Events at Samcheok: 6 / 20              │
    │ Max Fire Radiative Power: 310 MW        │
    └─────────────────────────────────────────┘

    ┌─────────────────────────────────────────┐
    │ RIVER FLOOD                             │
    │ Source: ISIMIP / GloFAS                 │
    │ Scenario: RCP8.5 (2030-2050)            │
    │ Events at Samcheok: 0 / 480             │
    │ Plant elevation: 10m (no flood risk)   │
    └─────────────────────────────────────────┘

    ┌─────────────────────────────────────────┐
    │ TROPICAL CYCLONE                        │
    │ Source: IBTrACS (observed)              │
    │ Period: 1980-2020                       │
    │ Events at Samcheok: 15 / 3890           │
    │ Max wind speed: 48.8 m/s                │
    └─────────────────────────────────────────┘
    """

    ax2.text(0.05, 0.95, info_text, transform=ax2.transAxes,
             fontsize=9, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='#f8f9fa', edgecolor='#dee2e6'))

    # =========================================================================
    # Panel 3: Pie Charts (Bottom Left)
    # =========================================================================
    ax3 = axes[1, 0]

    # Create two pie charts side by side
    fig3, (ax3a, ax3b) = plt.subplots(1, 2, figsize=(8, 4))

    # CLIMADA breakdown
    climada_sizes = [0.0082, 0.0000, 0.0205]
    climada_labels = ['Wildfire\n0.008%', 'Flood\n0%', 'TC\n0.021%']
    climada_colors = ['#ff6b6b', '#4dabf7', '#69db7c']
    climada_explode = (0.05, 0, 0.05)

    # Filter out zero values for pie
    climada_nonzero = [(s, l, c) for s, l, c in zip(climada_sizes, climada_labels, climada_colors) if s > 0]
    if climada_nonzero:
        sizes, labels, colors = zip(*climada_nonzero)
        ax3.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                startangle=90, explode=[0.05]*len(sizes))

    ax3.set_title('CLIMADA Hazard Breakdown\n(Total: 0.029%)', fontsize=11, fontweight='bold')

    # =========================================================================
    # Panel 4: Key Findings (Bottom Right)
    # =========================================================================
    ax4 = axes[1, 1]
    ax4.axis('off')

    findings_text = """
    KEY FINDINGS
    ════════════════════════════════════════

    CLIMADA TOTAL:      0.029% annual outage
    LITERATURE TOTAL:   0.058% annual outage
    RATIO:              0.50x (CLIMADA is lower)

    ════════════════════════════════════════

    WHY THE DIFFERENCE?

    1. WILDFIRE (CLIMADA 0.008% vs Lit 0.055%)
       - CLIMADA counts only 6 fire events in 20 yrs
       - Literature uses broader transmission impact
       - Both are in same order of magnitude

    2. FLOOD (CLIMADA 0% vs Lit 0.003%)
       - CLIMADA: No riverine flooding at 10m elev
       - Literature: Includes coastal storm surge
       - CLIMADA doesn't model surge separately

    3. TROPICAL CYCLONE (CLIMADA 0.021%)
       - Not included in literature estimate
       - Adds meaningful risk component
       - 5 damaging events (>30 m/s) in 40 yrs

    ════════════════════════════════════════

    RECOMMENDATION:
    Use LITERATURE values (0.058%) as they include
    coastal storm surge not captured by CLIMADA
    river flood model. Add TC risk (+0.02%) from
    CLIMADA for completeness.

    COMBINED ESTIMATE: ~0.08% annual outage rate
    """

    ax4.text(0.05, 0.98, findings_text, transform=ax4.transAxes,
             fontsize=9, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='#e7f5ff', edgecolor='#74c0fc'))

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved comparison visualization to: {save_path}")

    return fig


def create_summary_table():
    """Print summary comparison table."""
    print("\n" + "=" * 70)
    print("CLIMADA vs LITERATURE COMPARISON SUMMARY")
    print("=" * 70)

    print(f"""
┌─────────────────────────────────────────────────────────────────────┐
│                    PHYSICAL RISK COMPARISON                         │
│                 Samcheok Blue Power Plant (2.1 GW)                 │
├─────────────────────────────────────────────────────────────────────┤
│ Source         │ Resolution │ Wildfire │  Flood  │   TC    │ TOTAL │
├─────────────────────────────────────────────────────────────────────┤
│ CLIMADA        │   4.5 km   │  0.008%  │  0.00%  │ 0.021%  │ 0.03% │
│ Literature     │     N/A    │  0.055%  │ 0.003%  │   N/A   │ 0.06% │
├─────────────────────────────────────────────────────────────────────┤
│ Ratio (C/L)    │     -      │   0.15x  │   N/A   │   N/A   │ 0.50x │
└─────────────────────────────────────────────────────────────────────┘

CLIMADA DATA QUALITY:
  ✓ Wildfire: 6 events in 20 years at exact location (2km grid)
  ✓ Flood: 0 events (plant at 10m elevation, no riverine flood)
  ✓ TC: 15 events in 40 years, 5 with damaging winds (>30 m/s)

RECOMMENDATION:
  Combined estimate = Literature (0.058%) + TC from CLIMADA (0.021%)
                    = ~0.08% annual outage rate

  This is MODEST physical risk - transition risk dominates for coal.
    """)


if __name__ == "__main__":
    # Create visualization
    output_dir = Path("outputs/visualizations")
    output_dir.mkdir(parents=True, exist_ok=True)

    create_comparison_visualization(str(output_dir / "climada_vs_literature.png"))
    create_summary_table()

    plt.show()

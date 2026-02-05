"""
Generate publication-quality figures for the Climate Risk Premium paper.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
from pathlib import Path

# Set up output directory
OUTPUT_DIR = Path("data/processed/figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Professional color palette
COLORS = {
    'physical': '#f39c12',      # Orange - Physical risks
    'transition': '#e74c3c',    # Red - Transition risks
    'financial': '#3498db',     # Blue - Financial metrics
    'output': '#27ae60',        # Green - Output/NPV
    'neutral': '#2c3e50',       # Dark gray - Neutral
    'background': '#ecf0f1',    # Light gray - Background
    'text': '#2c3e50',          # Dark gray - Text
}


def create_model_architecture_diagram():
    """Create the model logic flow diagram (Figure 4)."""
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Title
    ax.text(7, 9.7, 'Climate Risk Premium Model Architecture',
            fontsize=16, fontweight='bold', ha='center', va='top')

    # Helper function for boxes
    def add_box(x, y, width, height, text, color, fontsize=9, text_color='white'):
        box = FancyBboxPatch((x - width/2, y - height/2), width, height,
                             boxstyle="round,pad=0.05,rounding_size=0.2",
                             facecolor=color, edgecolor='none', alpha=0.9)
        ax.add_patch(box)
        ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
                fontweight='bold', color=text_color, wrap=True)
        return (x, y)

    # Helper function for arrows
    def add_arrow(start, end, color='#7f8c8d', style='->', label=''):
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle=style, color=color, lw=2))
        if label:
            mid = ((start[0] + end[0])/2, (start[1] + end[1])/2)
            ax.text(mid[0], mid[1] + 0.2, label, fontsize=7, ha='center', color=color)

    # Section backgrounds
    sections = [
        (1, 8.5, 6, 1.8, 'External Risk Inputs', '#fadbd8'),
        (9, 8.5, 4, 1.8, 'Data Sources', '#d5f5e3'),
        (1, 6, 6, 2, 'Operational Impact', '#fdebd0'),
        (9, 6, 4, 2, 'Financial Model', '#d6eaf8'),
        (5.5, 2.5, 7, 2.5, 'Credit Rating & Valuation', '#e8daef'),
    ]

    for x, y, w, h, label, color in sections:
        rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                              boxstyle="round,pad=0.1,rounding_size=0.3",
                              facecolor=color, edgecolor='#bdc3c7', alpha=0.5, lw=1)
        ax.add_patch(rect)
        ax.text(x, y + h/2 - 0.2, label, fontsize=10, fontweight='bold',
                ha='center', va='top', color=COLORS['text'])

    # External Risk Inputs
    phys_pos = add_box(0.5, 8.5, 2.2, 0.9, 'Physical Hazards\n(CLIMADA)', COLORS['physical'])
    trans_pos = add_box(3.5, 8.5, 2.2, 0.9, 'Transition Policy\n(Korea Power Plan)', COLORS['transition'])

    # Data Sources
    data_sources = add_box(9, 8.5, 3.2, 1.2,
                           'Plant Parameters\nKIS Rating Grid\nDebt Schedule',
                           COLORS['neutral'], fontsize=8)

    # Operational Impact Layer
    gen_pos = add_box(1, 6, 2.2, 1, 'Generation\nVolume (MWh)', COLORS['physical'], fontsize=8)
    carbon_pos = add_box(3.5, 6, 2, 0.8, 'Carbon\nCosts', COLORS['transition'], fontsize=8)

    # Physical risk details
    ax.text(0.5, 7.4, 'Wildfire Outage\nFlood Risk\nSLR Derating', fontsize=7,
            ha='center', va='center', style='italic', color=COLORS['physical'])

    # Transition risk details
    ax.text(3.5, 7.4, 'Dispatch Caps\nCarbon Price\nPhase-out', fontsize=7,
            ha='center', va='center', style='italic', color=COLORS['transition'])

    # Financial Model
    rev_pos = add_box(7.5, 6.5, 1.8, 0.7, 'Revenue', COLORS['financial'], fontsize=8)
    ebitda_pos = add_box(9, 5.5, 1.8, 0.7, 'EBITDA', COLORS['financial'], fontsize=8)
    cfads_pos = add_box(10.5, 6.5, 1.8, 0.7, 'CFADS', COLORS['financial'], fontsize=8)

    # Credit Rating & Valuation
    dscr_pos = add_box(4, 2.5, 2, 0.9, 'DSCR / LLCR\n(Coverage Ratios)', COLORS['financial'], fontsize=8)
    rating_pos = add_box(7, 2.5, 2.2, 0.9, 'Credit Rating\n(AAA → B)', '#9b59b6')
    cod_pos = add_box(10, 2.5, 2, 0.9, 'Cost of Debt\n(Spread)', '#9b59b6', fontsize=8)

    # Final output
    npv_pos = add_box(7, 0.8, 2.5, 1, 'NPV\n(Project Value)', COLORS['output'])

    # Draw arrows
    # Physical → Generation
    add_arrow((0.5, 8), (1, 6.5))
    # Transition → Generation
    add_arrow((3.5, 8), (1.5, 6.5))
    # Transition → Carbon
    add_arrow((3.5, 8), (3.5, 6.4))

    # Generation → Revenue
    add_arrow((2.1, 6), (6.6, 6.5))
    # Carbon → EBITDA
    add_arrow((4.5, 6), (8.1, 5.5))
    # Revenue → EBITDA
    add_arrow((7.5, 6.1), (8.5, 5.9))
    # EBITDA → CFADS
    add_arrow((9.9, 5.5), (10.5, 6.1))

    # Data → Financial Model
    add_arrow((9, 7.9), (9, 7))

    # CFADS → DSCR
    add_arrow((10.5, 6.1), (10.5, 4.5), color='#7f8c8d')
    ax.annotate('', xy=(5, 2.9), xytext=(10.5, 4.5),
               arrowprops=dict(arrowstyle='->', color='#7f8c8d', lw=2,
                              connectionstyle='arc3,rad=0.3'))

    # DSCR → Rating
    add_arrow((5, 2.5), (5.9, 2.5), label='KIS Method')

    # Rating → Cost of Debt
    add_arrow((8.1, 2.5), (9, 2.5), label='Spread Matrix')

    # Cost of Debt → NPV (via WACC)
    ax.annotate('', xy=(8.25, 1.3), xytext=(10, 2),
               arrowprops=dict(arrowstyle='->', color='#9b59b6', lw=2,
                              connectionstyle='arc3,rad=-0.3'))
    ax.text(9.5, 1.5, 'WACC', fontsize=7, ha='center', color='#9b59b6')

    # CFADS → NPV (cash flows)
    ax.annotate('', xy=(7.5, 1.3), xytext=(10.5, 5.5),
               arrowprops=dict(arrowstyle='->', color=COLORS['financial'], lw=2,
                              connectionstyle='arc3,rad=0.4'))
    ax.text(10, 3.5, 'Cash Flows', fontsize=7, ha='center', color=COLORS['financial'])

    # Add feedback loop indicator
    ax.annotate('', xy=(9, 3), xytext=(9, 4),
               arrowprops=dict(arrowstyle='<->', color='#c0392b', lw=1.5, ls='--'))
    ax.text(8.2, 3.5, 'Death\nSpiral', fontsize=7, ha='center', color='#c0392b', fontweight='bold')

    # Legend
    legend_items = [
        (COLORS['physical'], 'Physical Risk'),
        (COLORS['transition'], 'Transition Risk'),
        (COLORS['financial'], 'Financial Metrics'),
        ('#9b59b6', 'Credit/Cost of Capital'),
        (COLORS['output'], 'Output (NPV)'),
    ]

    for i, (color, label) in enumerate(legend_items):
        ax.add_patch(plt.Rectangle((11.5, 0.3 + i*0.35), 0.3, 0.25,
                                   facecolor=color, edgecolor='none'))
        ax.text(12, 0.42 + i*0.35, label, fontsize=8, va='center')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'fig4_model_architecture.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.savefig(OUTPUT_DIR / 'fig4_model_architecture.pdf', bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"Saved: {OUTPUT_DIR / 'fig4_model_architecture.png'}")


def create_credit_death_spiral_diagram():
    """Create the credit rating death spiral feedback loop diagram (Figure 5)."""
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Title
    ax.text(5, 9.5, 'The Credit Rating Death Spiral',
            fontsize=14, fontweight='bold', ha='center')
    ax.text(5, 9.1, 'Non-linear feedback loop between climate risks and financing costs',
            fontsize=10, ha='center', style='italic', color='#7f8c8d')

    # Central cycle - positioned as a diamond
    center_x, center_y = 5, 5
    radius = 2.5

    # Four main nodes
    positions = {
        'climate': (center_x, center_y + radius),      # Top
        'cashflow': (center_x + radius, center_y),     # Right
        'rating': (center_x, center_y - radius),       # Bottom
        'cost': (center_x - radius, center_y),         # Left
    }

    # Node styling
    def add_node(pos, text, subtext, color):
        circle = plt.Circle(pos, 0.8, facecolor=color, edgecolor='white',
                           linewidth=3, alpha=0.9)
        ax.add_patch(circle)
        ax.text(pos[0], pos[1] + 0.1, text, ha='center', va='center',
               fontsize=10, fontweight='bold', color='white')
        ax.text(pos[0], pos[1] - 0.25, subtext, ha='center', va='center',
               fontsize=7, color='white')

    add_node(positions['climate'], 'Climate', 'Risks', COLORS['physical'])
    add_node(positions['cashflow'], 'Cash', 'Flow ↓', COLORS['financial'])
    add_node(positions['rating'], 'Credit', 'Rating ↓', '#9b59b6')
    add_node(positions['cost'], 'Cost of', 'Debt ↑', COLORS['transition'])

    # Curved arrows connecting nodes
    arrow_style = dict(arrowstyle='->', color='#2c3e50', lw=2.5,
                      connectionstyle='arc3,rad=0.3')

    # Climate → Cash Flow
    ax.annotate('', xy=(7, 5.5), xytext=(5.5, 7),
               arrowprops=arrow_style)
    ax.text(6.7, 6.5, 'Reduces\nRevenue', fontsize=8, ha='center', color='#7f8c8d')

    # Cash Flow → Rating
    ax.annotate('', xy=(5.5, 3), xytext=(7, 4.5),
               arrowprops=arrow_style)
    ax.text(6.7, 3.5, 'DSCR\nFalls', fontsize=8, ha='center', color='#7f8c8d')

    # Rating → Cost
    ax.annotate('', xy=(3, 4.5), xytext=(4.5, 3),
               arrowprops=arrow_style)
    ax.text(3.3, 3.5, 'Spread\nWidens', fontsize=8, ha='center', color='#7f8c8d')

    # Cost → Cash Flow (feedback!)
    ax.annotate('', xy=(6.8, 5), xytext=(3.3, 5),
               arrowprops=dict(arrowstyle='->', color='#c0392b', lw=3,
                              connectionstyle='arc3,rad=-0.4', linestyle='--'))
    ax.text(5, 3.8, 'Higher Interest\nExpense', fontsize=8, ha='center',
           color='#c0392b', fontweight='bold')

    # Feedback loop label
    ax.text(5, 5, 'FEEDBACK\nLOOP', ha='center', va='center', fontsize=9,
           fontweight='bold', color='#c0392b',
           bbox=dict(boxstyle='round', facecolor='white', edgecolor='#c0392b', alpha=0.9))

    # Example pathway with numbers
    ax.text(0.5, 8.5, 'Example Death Spiral Pathway:', fontsize=11, fontweight='bold')

    steps = [
        ('T=0', 'A Rating, 6.1% yield', COLORS['output']),
        ('T=5', 'DSCR < 2.0 → BBB (250 bps)', COLORS['financial']),
        ('T=6', 'Higher interest → DSCR < 1.5 → BB (400 bps)', COLORS['physical']),
        ('T=7', 'EBITDA negative → B (600 bps)', COLORS['transition']),
        ('T=8', 'Refinancing impossible → Technical Default', '#c0392b'),
    ]

    for i, (time, desc, color) in enumerate(steps):
        y_pos = 8 - i * 0.5
        ax.plot([0.5, 0.8], [y_pos, y_pos], color=color, lw=3)
        ax.text(0.9, y_pos, f'{time}:', fontsize=9, fontweight='bold', va='center')
        ax.text(1.6, y_pos, desc, fontsize=9, va='center')

    # Investment grade threshold
    ax.axhline(y=1.2, xmin=0.05, xmax=0.95, color='#c0392b', linestyle='--', lw=1.5)
    ax.text(5, 1.4, 'Investment Grade Threshold (BBB-)', fontsize=9,
           ha='center', color='#c0392b', style='italic')

    # Key insight box
    insight_text = ("Once DSCR falls below 1.0×, the project cannot service debt.\n"
                   "The 300% jump in spread (150→600 bps) creates\n"
                   "mathematically unfinanceable conditions.")
    ax.text(5, 0.6, insight_text, ha='center', va='center', fontsize=9,
           bbox=dict(boxstyle='round', facecolor='#fdf2e9', edgecolor='#e67e22', alpha=0.9))

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'fig5_death_spiral.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.savefig(OUTPUT_DIR / 'fig5_death_spiral.pdf', bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"Saved: {OUTPUT_DIR / 'fig5_death_spiral.png'}")


def create_data_flow_diagram():
    """Create the data sources and integration diagram (Figure 6)."""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Title
    ax.text(6, 7.7, 'Data Integration Framework',
            fontsize=14, fontweight='bold', ha='center')

    # Three data sources at top
    sources = [
        (2, 6.5, 'Korea Power\nSupply Plan\n(MOTIE)', COLORS['transition'],
         '• 10th/11th Basic Plan\n• Coal dispatch trajectory\n• Capacity factors 2024-2050'),
        (6, 6.5, 'CLIMADA\nHazard Data\n(ETH Zurich)', COLORS['physical'],
         '• Wildfire (FWI Index)\n• Flood (GLOFAS)\n• Sea Level Rise (IPCC AR6)'),
        (10, 6.5, 'KIS Credit\nMethodology\n(Korea Investors Service)', '#9b59b6',
         '• Rating thresholds\n• DSCR/LLCR criteria\n• Spread matrix'),
    ]

    for x, y, title, color, details in sources:
        # Main box
        box = FancyBboxPatch((x-1.5, y-0.8), 3, 1.6,
                             boxstyle="round,pad=0.05,rounding_size=0.2",
                             facecolor=color, edgecolor='none', alpha=0.9)
        ax.add_patch(box)
        ax.text(x, y, title, ha='center', va='center', fontsize=10,
                fontweight='bold', color='white')

        # Details box below
        detail_box = FancyBboxPatch((x-1.5, y-2.3), 3, 1.3,
                                    boxstyle="round,pad=0.05,rounding_size=0.1",
                                    facecolor='white', edgecolor=color, alpha=0.9, lw=2)
        ax.add_patch(detail_box)
        ax.text(x, y-1.6, details, ha='center', va='center', fontsize=8, color=COLORS['text'])

    # Central integration box
    int_box = FancyBboxPatch((3.5, 1.8), 5, 1.4,
                             boxstyle="round,pad=0.05,rounding_size=0.2",
                             facecolor=COLORS['financial'], edgecolor='none', alpha=0.9)
    ax.add_patch(int_box)
    ax.text(6, 2.5, 'CRP Model Integration Layer', ha='center', va='center',
           fontsize=12, fontweight='bold', color='white')
    ax.text(6, 2.1, 'Scenario Runner | Cash Flow Engine | Credit Assessment',
           ha='center', va='center', fontsize=9, color='white')

    # Output
    out_box = FancyBboxPatch((4, 0.3), 4, 0.9,
                             boxstyle="round,pad=0.05,rounding_size=0.2",
                             facecolor=COLORS['output'], edgecolor='none', alpha=0.9)
    ax.add_patch(out_box)
    ax.text(6, 0.75, 'NPV | IRR | DSCR | Credit Rating | CRP', ha='center', va='center',
           fontsize=10, fontweight='bold', color='white')

    # Arrows from sources to integration
    for x in [2, 6, 10]:
        ax.annotate('', xy=(6, 3.2), xytext=(x, 4),
                   arrowprops=dict(arrowstyle='->', color='#7f8c8d', lw=2,
                                  connectionstyle='arc3,rad=0'))

    # Arrow from integration to output
    ax.annotate('', xy=(6, 1.2), xytext=(6, 1.8),
               arrowprops=dict(arrowstyle='->', color='#7f8c8d', lw=2))

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'fig6_data_integration.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.savefig(OUTPUT_DIR / 'fig6_data_integration.pdf', bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"Saved: {OUTPUT_DIR / 'fig6_data_integration.png'}")


if __name__ == '__main__':
    print("Generating publication figures...")
    create_model_architecture_diagram()
    create_credit_death_spiral_diagram()
    create_data_flow_diagram()
    print("\nAll figures generated successfully!")
    print(f"Output directory: {OUTPUT_DIR.absolute()}")

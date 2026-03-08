#!/usr/bin/env python3
"""Generate investor-focused CRP Model Explainer PDF.

Output: docs/CRP_Model_Explainer.pdf (~10 pages, landscape letter)
Dependencies: matplotlib, numpy (standard scientific Python stack)
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.image as mpimg
import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PDF = PROJECT_ROOT / "docs" / "CRP_Model_Explainer.pdf"

# Existing figure paths
FIG_ARCHITECTURE = PROJECT_ROOT / "results" / "figures" / "fig4_model_architecture.png"
FIG_NPV = PROJECT_ROOT / "paper_dev" / "03_figures" / "fig_npv_frozen.png"
FIG_CRP = PROJECT_ROOT / "paper_dev" / "03_figures" / "fig_crp_frozen.png"
FIG_TORNADO = PROJECT_ROOT / "paper_dev" / "03_figures" / "fig_robustness_tornado.png"

# Color palette
NAVY = "#1B2838"
WHITE = "#FFFFFF"
LIGHT_GRAY = "#F4F6F7"
ACCENT_RED = "#C0392B"
DARK_GRAY = "#2C3E50"
MID_GRAY = "#7F8C8D"
ACCENT_BLUE = "#2980B9"

PAGE_W, PAGE_H = 11, 8.5  # landscape letter


def _new_figure():
    """Create a fresh landscape-letter figure."""
    fig = plt.figure(figsize=(PAGE_W, PAGE_H))
    fig.patch.set_facecolor(WHITE)
    return fig


def _header_band(fig, title, subtitle=None, y_top=0.95, height=0.10):
    """Draw a dark navy header band across the top of the page."""
    from matplotlib.patches import FancyBboxPatch
    ax_bg = fig.add_axes([0, y_top - height, 1, height])
    ax_bg.set_xlim(0, 1)
    ax_bg.set_ylim(0, 1)
    ax_bg.set_facecolor(NAVY)
    ax_bg.axis("off")
    ax_bg.text(0.05, 0.55, title, color=WHITE, fontsize=16,
               fontweight="bold", va="center", ha="left")
    if subtitle:
        ax_bg.text(0.95, 0.55, subtitle, color=MID_GRAY, fontsize=9,
                   va="center", ha="right")


def _footer(fig, text="PLANiT Institute  |  Climate Risk Premium Model  |  February 2026"):
    """Small footer at the bottom."""
    fig.text(0.5, 0.02, text, fontsize=7, color=MID_GRAY, ha="center")


def _embed_image(fig, path, rect):
    """Embed a PNG into the figure at the given rect [left, bottom, w, h]."""
    ax = fig.add_axes(rect)
    img = mpimg.imread(str(path))
    ax.imshow(img, aspect="auto")
    ax.axis("off")
    return ax


# ===== PAGE BUILDERS ========================================================

def page_cover(pdf):
    """Page 1 — Cover."""
    fig = _new_figure()
    fig.patch.set_facecolor(NAVY)

    fig.text(0.5, 0.62, "Climate Risk Premium Model",
             fontsize=36, fontweight="bold", color=WHITE, ha="center")
    fig.text(0.5, 0.53, "Samcheok Coal Asset",
             fontsize=28, color=WHITE, ha="center", fontstyle="italic")

    fig.text(0.5, 0.40,
             "Quantifying transition and physical climate risk\nfor project finance",
             fontsize=14, color=MID_GRAY, ha="center", linespacing=1.6)

    fig.text(0.5, 0.22, "PLANiT Institute", fontsize=13, color=WHITE,
             ha="center", fontweight="bold")
    fig.text(0.5, 0.17, "February 2026", fontsize=11, color=MID_GRAY,
             ha="center")

    # Decorative line
    ax_line = fig.add_axes([0.3, 0.30, 0.4, 0.002])
    ax_line.set_facecolor(ACCENT_RED)
    ax_line.axis("off")

    pdf.savefig(fig)
    plt.close(fig)


def page_executive_summary(pdf):
    """Page 2 — Executive Summary."""
    fig = _new_figure()
    _header_band(fig, "Executive Summary")
    _footer(fig)

    findings = [
        ("1", "Baseline NPV: $4,629M",
         "Under current policy, the Samcheok asset is rated AA with strong debt service coverage (DSCR 2.56)."),
        ("2", "Enhanced phase-down: \u2013$1,891M  (CC rated)",
         "Korea\u2019s 11th Basic Plan for Electricity triggers a $6.5 billion value swing \u2014 the single largest risk driver."),
        ("3", "Climate risk premium: up to 1,020 bps",
         "Under aggressive transition, lenders would demand 10.2% additional yield over risk-free benchmarks."),
        ("4", "Transition risk dominates physical risk by 103:1",
         "Policy-driven cash flow erosion overwhelms direct physical damage across every scenario tested."),
        ("5", "Results robust across 100% of stress grid",
         "All 648 deterministic grid points confirm transition dominance; no reversal found."),
    ]

    y = 0.78
    for num, headline, detail in findings:
        # Number circle
        fig.text(0.06, y, num, fontsize=22, fontweight="bold",
                 color=WHITE, ha="center", va="center",
                 bbox=dict(boxstyle="circle,pad=0.3", fc=ACCENT_RED, ec="none"))
        fig.text(0.10, y + 0.005, headline, fontsize=14, fontweight="bold",
                 color=DARK_GRAY, va="center")
        fig.text(0.10, y - 0.035, detail, fontsize=10, color=MID_GRAY,
                 va="center", wrap=True)
        y -= 0.135

    pdf.savefig(fig)
    plt.close(fig)


def page_the_asset(pdf):
    """Page 3 — The Asset."""
    fig = _new_figure()
    _header_band(fig, "The Asset", "Samcheok Blue Power Plant")
    _footer(fig)

    # Description
    desc = (
        "Samcheok Blue Power Plant is a 2.1 GW supercritical coal-fired generation facility\n"
        "located in Gangwon Province, South Korea. Commissioned in 2017 with a 30-year design\n"
        "life, the plant is one of the youngest and most efficient coal assets in Korea\u2019s fleet.\n"
        "It represents a critical test case for stranded-asset risk under the national energy\n"
        "transition framework."
    )
    fig.text(0.06, 0.74, desc, fontsize=11, color=DARK_GRAY,
             va="top", linespacing=1.6)

    # Financial parameters table
    ax_t = fig.add_axes([0.06, 0.12, 0.88, 0.38])
    ax_t.axis("off")

    col_labels = ["Parameter", "Value", "Parameter", "Value"]
    table_data = [
        ["Capacity",       "2,100 MW",         "CAPEX",            "$3,550 M"],
        ["Technology",     "Supercritical coal","Debt / Equity",    "70% / 30%"],
        ["Heat rate",      "8.8 MMBtu/MWh",    "Interest rate",    "5.0%"],
        ["Capacity factor","85%",               "Tax rate",         "25%"],
        ["Emissions",      "0.82 tCO\u2082/MWh",   "Design life",      "30 years"],
        ["Efficiency",     "39%",               "Base electricity price","$65/MWh"],
    ]

    table = ax_t.table(cellText=table_data, colLabels=col_labels,
                       loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 1.8)

    # Style header row
    for j in range(4):
        cell = table[0, j]
        cell.set_facecolor(NAVY)
        cell.set_text_props(color=WHITE, fontweight="bold")
    # Style data rows
    for i in range(1, len(table_data) + 1):
        for j in range(4):
            cell = table[i, j]
            cell.set_facecolor(LIGHT_GRAY if i % 2 == 0 else WHITE)
            if j in (0, 2):  # parameter name columns
                cell.set_text_props(fontweight="bold", color=DARK_GRAY)

    pdf.savefig(fig)
    plt.close(fig)


def page_architecture(pdf):
    """Page 4 — Model Architecture."""
    fig = _new_figure()
    _header_band(fig, "Model Architecture")
    _footer(fig)

    if FIG_ARCHITECTURE.exists():
        _embed_image(fig, FIG_ARCHITECTURE, [0.05, 0.10, 0.90, 0.70])
    else:
        fig.text(0.5, 0.45, "[Architecture figure not found]",
                 fontsize=14, color=ACCENT_RED, ha="center")

    fig.text(0.5, 0.06,
             "Scenario Inputs  \u2192  Operational Impact  \u2192  Financial Model  "
             "\u2192  Credit Rating  \u2192  Climate Risk Premium",
             fontsize=10, color=DARK_GRAY, ha="center",
             bbox=dict(boxstyle="round,pad=0.4", fc=LIGHT_GRAY, ec=MID_GRAY, lw=0.5))

    pdf.savefig(fig)
    plt.close(fig)


def page_scenarios(pdf):
    """Page 5 — Scenario Design."""
    fig = _new_figure()
    _header_band(fig, "Scenario Design", "11 deterministic scenarios")
    _footer(fig)

    col_labels = ["Scenario", "Type", "Key Driver", "NPV ($M)", "Rating"]
    table_data = [
        ["Baseline",              "Reference",   "Current policy",            "4,629",  "AA"],
        ["Moderate transition",   "Transition",  "Dispatch penalty 15%",      "3,534",  "AA"],
        ["Aggressive transition", "Transition",  "Dispatch penalty 40%",      "1,369",  "A"],
        ["Moderate physical",     "Physical",    "1.5\u00d7 climate mult.",       "4,599",  "AA"],
        ["High physical",         "Physical",    "2.5\u00d7 climate mult.",       "4,566",  "AA"],
        ["Combined moderate",     "Combined",    "Trans. + phys. moderate",   "3,513",  "AA"],
        ["Combined aggressive",   "Combined",    "Trans. + phys. aggressive", "1,330",  "A"],
        ["Low demand",            "Stress",      "Demand shock \u221225%",        "1,994",  "A"],
        ["Severe drought",        "Stress",      "Water stress penalty",      "4,609",  "AA"],
        ["Enhanced 11th Plan",    "Enhanced",    "Full phase-down schedule",  "\u20131,891", "CC"],
        ["Enhanced combined",     "Enhanced",    "Phase-down + phys. high",   "\u20131,896", "CC"],
    ]

    ax_t = fig.add_axes([0.04, 0.08, 0.92, 0.72])
    ax_t.axis("off")

    table = ax_t.table(cellText=table_data, colLabels=col_labels,
                       loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)
    table.scale(1.0, 1.65)

    # Style header
    for j in range(5):
        cell = table[0, j]
        cell.set_facecolor(NAVY)
        cell.set_text_props(color=WHITE, fontweight="bold")

    # Style data rows — highlight CC-rated rows
    for i in range(1, len(table_data) + 1):
        row_data = table_data[i - 1]
        is_distressed = row_data[4] in ("CC", "CCC")
        for j in range(5):
            cell = table[i, j]
            if is_distressed:
                cell.set_facecolor("#FADBD8")
                cell.set_text_props(color=ACCENT_RED, fontweight="bold")
            else:
                cell.set_facecolor(LIGHT_GRAY if i % 2 == 0 else WHITE)
                if j == 0:
                    cell.set_text_props(fontweight="bold")

    pdf.savefig(fig)
    plt.close(fig)


def page_npv(pdf):
    """Page 6 — Key Results: NPV Comparison."""
    fig = _new_figure()
    _header_band(fig, "Key Results: NPV Comparison")
    _footer(fig)

    if FIG_NPV.exists():
        _embed_image(fig, FIG_NPV, [0.05, 0.08, 0.90, 0.72])
    else:
        fig.text(0.5, 0.45, "[NPV figure not found]",
                 fontsize=14, color=ACCENT_RED, ha="center")

    # Annotation callouts
    fig.text(0.15, 0.06, "Baseline: $4,629M (AA)",
             fontsize=10, fontweight="bold", color=ACCENT_BLUE,
             bbox=dict(boxstyle="round,pad=0.3", fc="#EBF5FB", ec=ACCENT_BLUE, lw=0.8))
    fig.text(0.65, 0.06, "Enhanced 11th Plan: \u2013$1,891M (CC)",
             fontsize=10, fontweight="bold", color=ACCENT_RED,
             bbox=dict(boxstyle="round,pad=0.3", fc="#FADBD8", ec=ACCENT_RED, lw=0.8))

    pdf.savefig(fig)
    plt.close(fig)


def page_crp(pdf):
    """Page 7 — Climate Risk Premium."""
    fig = _new_figure()
    _header_band(fig, "Climate Risk Premium")
    _footer(fig)

    if FIG_CRP.exists():
        _embed_image(fig, FIG_CRP, [0.05, 0.18, 0.90, 0.62])
    else:
        fig.text(0.5, 0.50, "[CRP figure not found]",
                 fontsize=14, color=ACCENT_RED, ha="center")

    # Definition text box
    definition = (
        "CRP = the additional cost of capital demanded by lenders to compensate for\n"
        "climate-related credit deterioration, measured as the spread differential\n"
        "between the climate-adjusted and baseline credit ratings."
    )
    fig.text(0.5, 0.12, definition, fontsize=10, color=DARK_GRAY, ha="center",
             va="center", linespacing=1.5,
             bbox=dict(boxstyle="round,pad=0.5", fc=LIGHT_GRAY, ec=MID_GRAY, lw=0.5))

    fig.text(0.5, 0.04,
             "Peak CRP: 1,020 bps = 10.2% additional financing cost",
             fontsize=12, fontweight="bold", color=ACCENT_RED, ha="center")

    pdf.savefig(fig)
    plt.close(fig)


def page_credit_rating(pdf):
    """Page 8 — Credit Rating Transition."""
    fig = _new_figure()
    _header_band(fig, "Credit Rating Transition", "From AA to CC: the death spiral")
    _footer(fig)

    # --- Rating waterfall chart ---
    ax = fig.add_axes([0.06, 0.30, 0.55, 0.50])

    ratings = ["AA", "A", "BBB", "BB", "B", "CCC", "CC"]
    spreads = [100, 150, 250, 400, 650, 1000, 1500]
    scenarios = [
        "Baseline",
        "Aggressive\ntransition",
        "",
        "",
        "",
        "",
        "Enhanced\n11th Plan",
    ]

    colors = [ACCENT_BLUE, ACCENT_BLUE, "#F39C12", "#F39C12",
              ACCENT_RED, ACCENT_RED, ACCENT_RED]

    bars = ax.barh(range(len(ratings)), spreads, color=colors, edgecolor="white", height=0.6)
    ax.set_yticks(range(len(ratings)))
    ax.set_yticklabels(ratings, fontsize=11, fontweight="bold")
    ax.set_xlabel("Credit Spread (bps)", fontsize=10)
    ax.set_title("Rating Scale & Indicative Spreads", fontsize=12, fontweight="bold",
                 color=DARK_GRAY, pad=10)
    ax.invert_yaxis()
    ax.set_xlim(0, 1800)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Add spread labels
    for i, (bar, spread, scen) in enumerate(zip(bars, spreads, scenarios)):
        ax.text(spread + 30, i, f"{spread} bps", va="center", fontsize=9, color=DARK_GRAY)
        if scen:
            ax.text(spread + 200, i, scen, va="center", fontsize=8,
                    color=ACCENT_RED if i >= 4 else ACCENT_BLUE, fontweight="bold")

    # --- Explanation text ---
    explanation = (
        "The \u2018death spiral\u2019 mechanism:\n\n"
        "1. Carbon pricing & dispatch penalties\n"
        "   erode operating margins\n\n"
        "2. Negative EBITDA triggers credit\n"
        "   downgrade (AA \u2192 CC)\n\n"
        "3. Higher spreads increase financing\n"
        "   costs, further eroding cash flow\n\n"
        "4. Refinancing becomes prohibitively\n"
        "   expensive or impossible"
    )
    fig.text(0.70, 0.58, explanation, fontsize=10, color=DARK_GRAY,
             va="center", ha="left", linespacing=1.4,
             bbox=dict(boxstyle="round,pad=0.6", fc=LIGHT_GRAY, ec=MID_GRAY, lw=0.5))

    # Spread table at bottom
    ax_t = fig.add_axes([0.06, 0.06, 0.88, 0.15])
    ax_t.axis("off")
    spread_labels = ["AA", "A", "BBB", "BB", "B", "CCC", "CC"]
    spread_vals = ["100", "150", "250", "400", "650", "1,000", "1,500"]
    tbl = ax_t.table(
        cellText=[spread_vals],
        colLabels=spread_labels,
        loc="center", cellLoc="center"
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1.0, 1.6)
    for j in range(7):
        tbl[0, j].set_facecolor(NAVY)
        tbl[0, j].set_text_props(color=WHITE, fontweight="bold")
        tbl[1, j].set_facecolor(LIGHT_GRAY)

    pdf.savefig(fig)
    plt.close(fig)


def page_robustness(pdf):
    """Page 9 — Robustness."""
    fig = _new_figure()
    _header_band(fig, "Robustness Analysis", "648-point deterministic stress grid")
    _footer(fig)

    if FIG_TORNADO.exists():
        _embed_image(fig, FIG_TORNADO, [0.05, 0.18, 0.60, 0.62])
    else:
        fig.text(0.35, 0.50, "[Tornado figure not found]",
                 fontsize=14, color=ACCENT_RED, ha="center")

    # Key stats on the right
    stats = [
        ("Stress Range", "\u2013$3,091M to \u2013$691M"),
        ("Best Case", "\u2013$691M (still negative)"),
        ("Worst Case", "\u2013$3,091M"),
        ("Dominance Ratio", "103:1 (trans. vs phys.)"),
        ("Grid Coverage", "100% transition dominance"),
    ]
    y = 0.74
    for label, value in stats:
        fig.text(0.70, y, label, fontsize=10, fontweight="bold", color=DARK_GRAY)
        fig.text(0.70, y - 0.03, value, fontsize=11, color=ACCENT_RED)
        y -= 0.105

    fig.text(0.70, 0.18,
             "Physical damage multiplier\nis the smallest sensitivity\nbar in every test.",
             fontsize=9, color=MID_GRAY, linespacing=1.5,
             bbox=dict(boxstyle="round,pad=0.4", fc=LIGHT_GRAY, ec=MID_GRAY, lw=0.5))

    pdf.savefig(fig)
    plt.close(fig)


def page_takeaways(pdf):
    """Page 10 — Key Takeaways."""
    fig = _new_figure()
    fig.patch.set_facecolor(NAVY)

    fig.text(0.5, 0.88, "Key Takeaways", fontsize=28, fontweight="bold",
             color=WHITE, ha="center")

    # Decorative line
    ax_line = fig.add_axes([0.3, 0.83, 0.4, 0.002])
    ax_line.set_facecolor(ACCENT_RED)
    ax_line.axis("off")

    takeaways = [
        ("1", "Transition-policy clarity is financially consequential\nat the project level.",
         "A single regulatory decision (the 11th Basic Plan) drives a $6.5B value swing.\n"
         "Investors need scenario-conditioned risk metrics, not point estimates."),
        ("2", "Disclosure governance matters as much as\nmodel sophistication.",
         "Credit rating transitions from AA to CC are driven by policy assumptions,\n"
         "not model complexity. Transparent scenario design is essential."),
        ("3", "Transition planning and financing design\nshould be discussed jointly.",
         "The \u2018death spiral\u2019 from carbon costs to distressed ratings to prohibitive spreads\n"
         "means energy transition policy and financial structuring are inseparable."),
    ]

    y = 0.72
    for num, headline, detail in takeaways:
        fig.text(0.08, y, num, fontsize=24, fontweight="bold", color=NAVY,
                 ha="center", va="center",
                 bbox=dict(boxstyle="circle,pad=0.3", fc=ACCENT_RED, ec="none"))
        fig.text(0.13, y + 0.005, headline, fontsize=14, fontweight="bold",
                 color=WHITE, va="center", linespacing=1.4)
        fig.text(0.13, y - 0.065, detail, fontsize=10, color=MID_GRAY,
                 va="center", linespacing=1.4)
        y -= 0.22

    # Footer
    fig.text(0.5, 0.06,
             "github.com/jinsu/climate_risk_premium  |  PLANiT Institute  |  February 2026",
             fontsize=9, color=MID_GRAY, ha="center")

    pdf.savefig(fig)
    plt.close(fig)


# ===== MAIN =================================================================

def main():
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)

    # Check for required figures
    missing = []
    for path in [FIG_ARCHITECTURE, FIG_NPV, FIG_CRP, FIG_TORNADO]:
        if not path.exists():
            missing.append(str(path.relative_to(PROJECT_ROOT)))
    if missing:
        print(f"WARNING: Missing figures (will show placeholders): {missing}")

    print(f"Generating {OUTPUT_PDF.relative_to(PROJECT_ROOT)} ...")

    with PdfPages(str(OUTPUT_PDF)) as pdf:
        page_cover(pdf)
        print("  [1/10] Cover")
        page_executive_summary(pdf)
        print("  [2/10] Executive Summary")
        page_the_asset(pdf)
        print("  [3/10] The Asset")
        page_architecture(pdf)
        print("  [4/10] Model Architecture")
        page_scenarios(pdf)
        print("  [5/10] Scenario Design")
        page_npv(pdf)
        print("  [6/10] NPV Comparison")
        page_crp(pdf)
        print("  [7/10] Climate Risk Premium")
        page_credit_rating(pdf)
        print("  [8/10] Credit Rating Transition")
        page_robustness(pdf)
        print("  [9/10] Robustness")
        page_takeaways(pdf)
        print("  [10/10] Key Takeaways")

    print(f"\nDone. Output: {OUTPUT_PDF}")
    print(f"File size: {OUTPUT_PDF.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()

"""Scenario comparison figures: heatmap, EBITDA, DSCR, spread_bps.

Produces seven publication-quality figures for four target scenarios:
  baseline, moderate_transition, aggressive_transition, enhanced_11th_plan.

Outputs (results/figures/):
  fig_credit_rating_heatmap.png   ← from yearly_ratings.csv
  fig_spread_bps_line.png         ← from yearly_ratings.csv
  fig_ebitda_line.png
  fig_ebitda_bar.png
  fig_dscr_line.png
  fig_dscr_bar.png
"""

from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DATA_PATH = BASE_DIR / "results" / "yearly_financial_ratios.csv"
RATINGS_PATH = BASE_DIR / "results" / "yearly_ratings.csv"
FIGURE_DIR = BASE_DIR / "results" / "figures"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

# ─── Constants ────────────────────────────────────────────────────────────────
TARGET_SCENARIOS = [
    "baseline",
    "moderate_transition",
    "aggressive_transition",
    "enhanced_11th_plan",
]
SCENARIO_LABELS = {
    "baseline": "Baseline",
    "moderate_transition": "Moderate Transition",
    "aggressive_transition": "Aggressive Transition",
    "enhanced_11th_plan": "Enhanced 11th Plan",
}
SCENARIO_COLORS = {
    "baseline": "#1565C0",
    "moderate_transition": "#E65100",
    "aggressive_transition": "#B71C1C",
    "enhanced_11th_plan": "#2E7D32",
}
SCENARIO_MARKERS = {
    "baseline": "o",
    "moderate_transition": "s",
    "aggressive_transition": "^",
    "enhanced_11th_plan": "D",
}

# ── Rating palette for yearly_ratings.csv (A > BBB > BB > D) ──────────────────
RATING_ORDER = ["A", "BBB", "BB", "D"]
RATING_NUMERIC = {r: i for i, r in enumerate(RATING_ORDER)}
RATING_PALETTE = [
    "#2E7D32",  # A    dark green
    "#A5D6A7",  # BBB  light green
    "#FFB300",  # BB   amber
    "#B71C1C",  # D    dark red
]
# Spread reference lines per rating (bps)
RATING_SPREAD_REF = {"A": 150, "BBB": 250, "BB": 400}


def _rating_num(val: object) -> float:
    """Map a rating string to its numeric rank (0=A, 1=BBB, 2=BB, 3=D; NaN if missing)."""
    s = str(val).strip() if pd.notna(val) else ""
    return float(RATING_NUMERIC[s]) if s in RATING_NUMERIC else float("nan")


# ─── Data Loading ─────────────────────────────────────────────────────────────
def load_financial_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df = df[df["scenario"].isin(TARGET_SCENARIOS)].copy()
    df["ebitda_100m"] = df["ebitda"] / 1e8  # unit: ×10⁸ KRW
    return df


def load_ratings_data() -> pd.DataFrame:
    df = pd.read_csv(RATINGS_PATH)
    return df[df["scenario"].isin(TARGET_SCENARIOS)].copy()


# ─── Figure 1: Credit Rating Heatmap (from yearly_ratings.csv) ───────────────
_NOTES = (
    "Note:  ① Baseline — Investment-grade (A) for most of operational life; temporarily BBB (2026–2033) as leverage peaks; "
    "recovers to A and returns to BBB after 2051 as debt amortises.\n"
    "          ② Moderate Transition — Opens at BBB (2025); deteriorates to sub-investment grade BB (2026–2040) under "
    "moderate carbon regulation; partially recovers to BBB from 2041 as debt amortises.\n"
    "          ③ Aggressive Transition — Sub-investment grade (BB) throughout entire operational life (2025–2049); "
    "no recovery to investment grade under stringent decarbonisation policy.\n"
    "          ④ Enhanced 11th Plan — Directly reflects Korea's 11th Basic Plan for Electricity Supply and Demand; "
    "accelerated utilisation decline erodes cash flows; default (D) in 2039–2040; early project termination in 2040."
)

_GRAY = "#C8C8C8"  # colour for post-termination / no-data cells


def plot_credit_rating_heatmap(df_ratings: pd.DataFrame) -> None:
    """4-scenario × year heatmap styled to match figure1_credit_ratings_en.png."""
    all_years = list(range(int(df_ratings["year"].min()), 2054))

    pivot_str = df_ratings.pivot_table(
        index="scenario", columns="year", values="rating", aggfunc="first"
    ).reindex(TARGET_SCENARIOS).reindex(columns=all_years)

    # Numeric matrix: known ratings → rank; NaN → sentinel for gray
    pivot_num = pivot_str.copy().astype(object)
    for col in pivot_num.columns:
        pivot_num[col] = pivot_str[col].map(_rating_num)
    pivot_num = pivot_num.astype(float)

    # Build colormap: ratings + 1 extra "gray" level at index len(RATING_ORDER)
    n_grades = len(RATING_ORDER)
    palette_with_gray = RATING_PALETTE + [_GRAY]
    cmap = mcolors.ListedColormap(palette_with_gray)
    bounds = np.arange(-0.5, n_grades + 1.5, 1)
    norm = mcolors.BoundaryNorm(bounds, cmap.N)

    # Replace NaN with gray sentinel index
    display_matrix = np.where(np.isnan(pivot_num.values), float(n_grades), pivot_num.values)

    # ── Figure layout: heatmap (upper) + notes (lower) ──────────────────────
    fig = plt.figure(figsize=(18, 5.0))
    ax = fig.add_axes([0.13, 0.38, 0.85, 0.50])

    ax.imshow(
        display_matrix,
        aspect="auto",
        cmap=cmap,
        norm=norm,
        interpolation="nearest",
    )

    # White grid lines between cells
    ax.set_xticks(np.arange(len(all_years) + 1) - 0.5, minor=True)
    ax.set_yticks(np.arange(len(TARGET_SCENARIOS) + 1) - 0.5, minor=True)
    ax.grid(which="minor", color="white", linewidth=1.2)
    ax.tick_params(which="minor", bottom=False, left=False)

    # x-axis: label every 2 years, no major tick marks
    ax.set_xticks(range(len(all_years)))
    ax.set_xticklabels(
        [str(y) if y % 2 == 0 else "" for y in all_years],
        fontsize=7.5, rotation=0,
    )
    ax.tick_params(axis="x", length=0)

    # y-axis: scenario labels
    ax.set_yticks(range(len(TARGET_SCENARIOS)))
    ax.set_yticklabels(
        [SCENARIO_LABELS[s] + " Scenario" for s in TARGET_SCENARIOS],
        fontsize=9.5,
    )
    ax.tick_params(axis="y", length=0)

    # Remove all spines
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Annotate every cell with its rating string
    for row_i, scenario in enumerate(TARGET_SCENARIOS):
        for col_j, year in enumerate(all_years):
            raw = pivot_str.at[scenario, year] if year in pivot_str.columns else None
            if pd.isna(raw):
                continue
            num = _rating_num(raw)
            text_color = "white" if num >= 2 else "#1A1A1A"
            ax.text(
                col_j, row_i, str(raw),
                ha="center", va="center",
                fontsize=6.8, fontweight="bold",
                color=text_color,
            )

    # ── Inline legend (top-right, matching target style) ────────────────────
    legend_patches = [
        Patch(facecolor=RATING_PALETTE[i], label=r, linewidth=0)
        for i, r in enumerate(RATING_ORDER)
    ]
    ax.legend(
        handles=legend_patches,
        ncol=len(RATING_ORDER),
        fontsize=8.5,
        loc="upper right",
        bbox_to_anchor=(1.0, 1.18),
        frameon=False,
        handlelength=1.3,
        handletextpad=0.4,
        columnspacing=0.8,
    )

    # ── Title ────────────────────────────────────────────────────────────────
    yr_min = all_years[0]
    yr_max = all_years[-1]
    ax.set_title(
        f"Annual Credit Rating by Scenario ({yr_min}–{yr_max})",
        fontsize=12, fontweight="bold", pad=22, loc="center",
    )

    # ── Notes section (bottom) ───────────────────────────────────────────────
    fig.text(
        0.02, 0.01, _NOTES,
        fontsize=7.5, va="bottom", color="#333333",
        linespacing=1.6,
        wrap=False,
    )

    _save(fig, "fig_credit_rating_heatmap.png")


# ─── Figure 2: Credit Spread (%p) Line Chart — broken y-axis ─────────────────
def plot_spread_bps_line(df_ratings: pd.DataFrame) -> None:
    """Annual credit spread (%p) line chart with broken y-axis and rating threshold references.

    The y-axis is broken between 10 %p and 47 %p so that both the main scenario
    lines (≤ ~10 %p) and the Default-rating spike (50 %p) are legible.
    Spread values are converted from bps to percentage points (1 bps = 0.01 %p).
    """
    BPS_TO_PP = 1 / 100  # 1 bps = 0.01 percentage point

    df = df_ratings.copy()
    df["spread_pp"] = df["spread_bps"] * BPS_TO_PP

    LOWER_YLIM = (-0.3, 11.0)  # covers 0–1100 bps
    UPPER_YLIM = (47.0, 52.5)  # covers the 5000 bps Default spike

    fig, (ax_top, ax_bot) = plt.subplots(
        2, 1,
        sharex=True,
        figsize=(12, 6),
        gridspec_kw={"height_ratios": [1, 3], "hspace": 0.08},
    )

    # ── Plot lines on both panels (limits clip what's visible in each) ───────
    for scenario in TARGET_SCENARIOS:
        sub = df[df["scenario"] == scenario].sort_values("year")
        kw = dict(
            color=SCENARIO_COLORS[scenario],
            linewidth=2.0,
            marker=SCENARIO_MARKERS[scenario],
            markersize=4,
            zorder=3,
        )
        ax_top.plot(sub["year"], sub["spread_pp"], **kw)
        ax_bot.plot(sub["year"], sub["spread_pp"], label=SCENARIO_LABELS[scenario], **kw)

    # ── Rating threshold reference lines (lower panel only) ──────────────────
    ref_styles = {"A": ("--", "#2E7D32"), "BBB": ("--", "#7CB342"), "BB": ("--", "#F9A825")}
    for rating, (ls, color) in ref_styles.items():
        pp = RATING_SPREAD_REF[rating] * BPS_TO_PP
        ax_bot.axhline(pp, linestyle=ls, color=color, linewidth=1.0, alpha=0.7)
        ax_bot.text(
            2064.3, pp, f"{rating} ({pp:.2f} %p)",
            va="center", fontsize=8, color=color,
        )

    # ── D-rating spike annotation (upper panel) ──────────────────────────────
    d_data = df[(df["scenario"] == "enhanced_11th_plan") & (df["rating"] == "D")]
    if not d_data.empty:
        spike_year = d_data["year"].iloc[0]
        spike_pp = d_data["spread_pp"].iloc[0]
        ax_top.annotate(
            f"Default (D)\n{spike_pp:.0f} %p",
            xy=(spike_year, spike_pp),
            xytext=(spike_year - 4, spike_pp - 1.5),
            fontsize=8.5,
            color=SCENARIO_COLORS["enhanced_11th_plan"],
            arrowprops=dict(
                arrowstyle="->",
                color=SCENARIO_COLORS["enhanced_11th_plan"],
                lw=1.2,
            ),
        )

    # ── Axis limits ──────────────────────────────────────────────────────────
    ax_top.set_ylim(*UPPER_YLIM)
    ax_bot.set_ylim(*LOWER_YLIM)

    # ── Break markers — diagonal slashes at the axis gap ─────────────────────
    d_m = 0.015
    kw_brk = dict(color="k", clip_on=False, linewidth=1.0)
    ax_top.plot((-d_m, +d_m), (-d_m, +d_m), transform=ax_top.transAxes, **kw_brk)
    ax_top.plot((1 - d_m, 1 + d_m), (-d_m, +d_m), transform=ax_top.transAxes, **kw_brk)
    ax_bot.plot((-d_m, +d_m), (1 - d_m, 1 + d_m), transform=ax_bot.transAxes, **kw_brk)
    ax_bot.plot((1 - d_m, 1 + d_m), (1 - d_m, 1 + d_m), transform=ax_bot.transAxes, **kw_brk)

    # ── Hide inner spines and ticks at the gap ───────────────────────────────
    ax_top.spines["bottom"].set_visible(False)
    ax_bot.spines["top"].set_visible(False)
    ax_top.tick_params(axis="x", which="both", bottom=False)

    # ── Labels, title, legend, grid ──────────────────────────────────────────
    ax_top.set_title("Annual Credit Spread by Scenario", fontsize=13)
    ax_bot.set_xlabel("Year", fontsize=11)
    ax_bot.set_ylabel("Credit Spread (%p)", fontsize=11)
    ax_bot.legend(fontsize=10, loc="upper left")
    ax_bot.grid(axis="y", linestyle="--", alpha=0.4)
    ax_top.grid(axis="y", linestyle="--", alpha=0.4)

    ax_bot.set_xlim(2024, 2067)
    ax_bot.set_xticks(range(2025, 2065, 5))

    fig.subplots_adjust(left=0.09, right=0.88, top=0.93, bottom=0.10)
    _save(fig, "fig_spread_bps_line.png")


# ─── Figure 3a: EBITDA Line ───────────────────────────────────────────────────
def plot_ebitda_line(df: pd.DataFrame) -> None:
    """Annual EBITDA line chart for all four scenarios."""
    fig, ax = plt.subplots(figsize=(12, 4.8))

    for scenario in TARGET_SCENARIOS:
        sub = df[df["scenario"] == scenario].sort_values("year")
        ax.plot(
            sub["year"],
            sub["ebitda_100m"],
            label=SCENARIO_LABELS[scenario],
            color=SCENARIO_COLORS[scenario],
            linewidth=2.0,
            marker=SCENARIO_MARKERS[scenario],
            markersize=4,
        )

    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("EBITDA (×10⁸ KRW)", fontsize=11)
    ax.set_title("Annual EBITDA by Scenario", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.45)
    ax.set_xlim(2024, 2065)
    ax.set_xticks(range(2025, 2065, 5))

    plt.tight_layout()
    _save(fig, "fig_ebitda_line.png")


# ─── Figure 3b: EBITDA Bar (5-year intervals) ────────────────────────────────
def plot_ebitda_bar(df: pd.DataFrame) -> None:
    """Grouped bar chart of EBITDA at 5-year milestones."""
    milestones = list(range(2025, 2065, 5))
    sub = df[df["year"].isin(milestones)].copy()

    n_s = len(TARGET_SCENARIOS)
    width = 0.8 / n_s
    x = np.arange(len(milestones))

    fig, ax = plt.subplots(figsize=(14, 5))

    for idx, scenario in enumerate(TARGET_SCENARIOS):
        s = sub[sub["scenario"] == scenario].set_index("year")
        vals = [
            s.loc[y, "ebitda_100m"] if y in s.index else 0.0
            for y in milestones
        ]
        offset = (idx - n_s / 2 + 0.5) * width
        ax.bar(
            x + offset, vals,
            width=width * 0.92,
            label=SCENARIO_LABELS[scenario],
            color=SCENARIO_COLORS[scenario],
            alpha=0.88,
            edgecolor="white",
            linewidth=0.5,
        )

    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in milestones], fontsize=9)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("EBITDA (×10⁸ KRW)", fontsize=11)
    ax.set_title("EBITDA by Scenario — 5-Year Intervals", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.45)

    plt.tight_layout()
    _save(fig, "fig_ebitda_bar.png")


# ─── Figure 3a: DSCR Line ────────────────────────────────────────────────────
def plot_dscr_line(df: pd.DataFrame) -> None:
    """Annual DSCR line chart for all four scenarios."""
    fig, ax = plt.subplots(figsize=(12, 4.8))

    for scenario in TARGET_SCENARIOS:
        sub = df[df["scenario"] == scenario].sort_values("year")
        # Exclude zero-DSCR tail (plant already decommissioned)
        sub = sub[sub["dscr"] > 0]
        ax.plot(
            sub["year"],
            sub["dscr"],
            label=SCENARIO_LABELS[scenario],
            color=SCENARIO_COLORS[scenario],
            linewidth=2.0,
            marker=SCENARIO_MARKERS[scenario],
            markersize=4,
        )

    ax.axhline(
        1.0, color="black", linestyle="--", linewidth=1.2,
        alpha=0.65, label="DSCR = 1.0 (break-even)"
    )

    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("DSCR", fontsize=11)
    ax.set_title("Debt Service Coverage Ratio (DSCR) by Scenario", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.45)
    ax.set_xlim(2024, 2065)
    ax.set_xticks(range(2025, 2065, 5))
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    _save(fig, "fig_dscr_line.png")


# ─── Figure 3b: DSCR Bar (5-year intervals) ──────────────────────────────────
def plot_dscr_bar(df: pd.DataFrame) -> None:
    """Grouped bar chart of DSCR at 5-year milestones."""
    milestones = list(range(2025, 2065, 5))
    sub = df[df["year"].isin(milestones)].copy()

    n_s = len(TARGET_SCENARIOS)
    width = 0.8 / n_s
    x = np.arange(len(milestones))

    fig, ax = plt.subplots(figsize=(14, 5))

    for idx, scenario in enumerate(TARGET_SCENARIOS):
        s = sub[sub["scenario"] == scenario].set_index("year")
        vals = [
            s.loc[y, "dscr"] if y in s.index else 0.0
            for y in milestones
        ]
        offset = (idx - n_s / 2 + 0.5) * width
        ax.bar(
            x + offset, vals,
            width=width * 0.92,
            label=SCENARIO_LABELS[scenario],
            color=SCENARIO_COLORS[scenario],
            alpha=0.88,
            edgecolor="white",
            linewidth=0.5,
        )

    ax.axhline(
        1.0, color="black", linestyle="--", linewidth=1.2,
        alpha=0.65, label="DSCR = 1.0"
    )
    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in milestones], fontsize=9)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("DSCR", fontsize=11)
    ax.set_title("DSCR by Scenario — 5-Year Intervals", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.45)
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    _save(fig, "fig_dscr_bar.png")


# ─── Helper ───────────────────────────────────────────────────────────────────
def _save(fig: plt.Figure, filename: str) -> None:
    path = FIGURE_DIR / filename
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {path}")


# ─── Entry Point ──────────────────────────────────────────────────────────────
def main() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.spines.top": False,
        "axes.spines.right": False,
    })

    df_fin = load_financial_data()
    df_rat = load_ratings_data()
    print(f"Financial rows: {len(df_fin)} | Rating rows: {len(df_rat)}")

    plot_credit_rating_heatmap(df_rat)
    plot_spread_bps_line(df_rat)
    plot_ebitda_line(df_fin)
    plot_ebitda_bar(df_fin)
    plot_dscr_line(df_fin)
    plot_dscr_bar(df_fin)

    print(f"\nAll figures → {FIGURE_DIR}")


if __name__ == "__main__":
    main()

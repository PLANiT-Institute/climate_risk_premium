"""
Generate Figure 1 (credit rating trajectories) and Figure 2 (utilization rate trajectories)
for the Samcheok Blue Power climate risk article — English version.

Output: results/figures/figure1_credit_ratings_en.png
        results/figures/figure2_utilization_en.png
        results/figures/figure2b_actual_utilization_en.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

BASE = Path(__file__).parent.parent
RESULTS = BASE / "results"
FIGURES = RESULTS / "figures"
FIGURES.mkdir(exist_ok=True)

SCENARIOS = {
    "combined_moderate":   "Combined Moderate Scenario",
    "combined_aggressive": "Combined Aggressive Scenario",
    "enhanced_11th_plan":  "11th Basic Plan Scenario",
}
COLORS = {
    "combined_moderate":   "#2196F3",
    "combined_aggressive": "#FF5722",
    "enhanced_11th_plan":  "#9C27B0",
}
RATING_ORDER = ["D", "BB", "BBB", "A"]
RATING_NUM = {r: i + 1 for i, r in enumerate(RATING_ORDER)}


def _setup_font() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.unicode_minus": False,
    })


def plot_figure1() -> None:
    """Credit rating heatmap — year × scenario colour map (2027–2050)."""
    import numpy as np
    from matplotlib.colors import BoundaryNorm, ListedColormap

    df = pd.read_csv(RESULTS / "yearly_ratings.csv")
    df = df[df["scenario"].isin(SCENARIOS)].copy()

    RATING_TO_NUM = {"D": 0, "BB": 1, "BBB": 2, "A": 3}
    TEXT_COLORS   = {0: "white", 1: "white", 2: "#333333", 3: "white"}
    df["rating_num"] = df["rating"].map(RATING_TO_NUM)

    scenarios = list(SCENARIOS.keys())
    all_years  = list(range(2027, 2051))
    n_sc, n_yr = len(scenarios), len(all_years)

    matrix = np.full((n_sc, n_yr), np.nan)
    for i, sc in enumerate(scenarios):
        yr_to_rating = {int(r["year"]): r["rating_num"]
                        for _, r in df[df["scenario"] == sc].iterrows()}
        for j, yr in enumerate(all_years):
            if yr in yr_to_rating:
                matrix[i, j] = yr_to_rating[yr]

    CELL_COLORS = {0: "#E53935", 1: "#FB8C00", 2: "#FDD835", 3: "#43A047"}
    cmap = ListedColormap([CELL_COLORS[k] for k in range(4)])
    cmap.set_bad(color="#E0E0E0")
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], ncolors=4)

    fig, ax = plt.subplots(figsize=(13, 7.0))
    plt.subplots_adjust(top=0.90, bottom=0.52, left=0.15, right=0.97)

    X = np.arange(2027, 2052, dtype=float)
    Y = np.arange(n_sc + 1, dtype=float)
    ax.pcolormesh(X, Y, np.ma.masked_invalid(matrix),
                  cmap=cmap, norm=norm, edgecolors="white", linewidth=0.5)

    ax.set_ylim(n_sc, 0)
    ax.set_yticks(np.arange(n_sc) + 0.5)
    ax.set_yticklabels([SCENARIOS[sc] for sc in scenarios], fontsize=10.5)

    ax.set_xlim(2027, 2051)
    ax.set_xticks([yr + 0.5 for yr in range(2027, 2051, 2)])
    ax.set_xticklabels([str(y) for y in range(2027, 2051, 2)], fontsize=9)

    yr_to_rating_str = {sc: {int(r["year"]): r["rating"]
                             for _, r in df[df["scenario"] == sc].iterrows()}
                        for sc in scenarios}
    for i, sc in enumerate(scenarios):
        for j, yr in enumerate(all_years):
            rating = yr_to_rating_str[sc].get(yr)
            if rating is not None:
                ax.text(yr + 0.5, i + 0.5, rating,
                        ha="center", va="center", fontsize=8, fontweight="bold",
                        color=TEXT_COLORS[RATING_TO_NUM[rating]])

    ax.set_title("Annual Credit Rating by Scenario (2027–2050)",
                 fontsize=13, fontweight="bold", pad=10)

    NOTES = [
        ("①", "Combined Moderate Scenario",
         "Moderate decarbonisation policy with low physical risk applied in combination.\n"
         "       Starts at BB (sub-investment grade); recovers to BBB from 2041 as debt amortises."),
        ("②", "Combined Aggressive Scenario",
         "Strengthened carbon regulation with high physical risk applied in combination.\n"
         "       BB sub-investment grade persists through 2049; investment-grade recovery is structurally unlikely."),
        ("③", "11th Basic Plan Scenario",
         "Directly reflects coal phase-out targets of Korea's 11th Basic Plan for Electricity Supply and Demand.\n"
         "       Sharp utilisation decline erodes cash flows; default (D) in 2039, early project termination in 2040."),
    ]
    y_start = 0.44
    for k, (num, name, body) in enumerate(NOTES):
        prefix = "Note: " if k == 0 else "      "
        fig.text(0.05, y_start - k * 0.085,
                 f"{prefix}{num} {name} — {body}",
                 fontsize=13, ha="left", va="top",
                 linespacing=1.5, transform=fig.transFigure)

    out = FIGURES / "figure1_credit_ratings_en.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


def plot_figure2() -> None:
    """Capacity factor — actual (monthly solid line) + scenario forecast (annual dashed) combined."""
    ACTUAL = [
        (2025,  1,  0.000),
        (2025,  2,  9.666),
        (2025,  3, 14.216),
        (2025,  4, 10.211),
        (2025,  5, 12.542),
        (2025,  6, 34.862),
        (2025,  7, 45.242),
        (2025,  8, 40.604),
        (2025,  9, 21.576),
        (2025, 10, 18.173),
        (2025, 11, 23.989),
        (2025, 12,  6.250),
        (2026,  1, 14.588),
        (2026,  2, 20.702),
    ]
    actual_x = list(range(len(ACTUAL)))
    actual_y = [util for _, _, util in ACTUAL]

    cf_files = {
        "combined_moderate":   "cashflow_combined_moderate.csv",
        "combined_aggressive": "cashflow_combined_aggressive.csv",
        "enhanced_11th_plan":  "cashflow_enhanced_11th_plan.csv",
    }

    fig, ax = plt.subplots(figsize=(13, 5))

    ax.plot(actual_x, actual_y,
            color="#333333", linewidth=2, marker="o", markersize=4,
            label="Actual (monthly, EPSIS/KPX)", zorder=5)

    N_ACTUAL = len(ACTUAL)
    FORECAST_START = N_ACTUAL + 1

    def year_to_idx(year: int) -> int:
        return FORECAST_START + (year - 2027)

    LABELS = {
        "combined_moderate":   "Moderate transition scenario",
        "combined_aggressive": "Aggressive transition scenario",
        "enhanced_11th_plan":  "11th Basic Plan Scenario",
    }

    for sc, label in LABELS.items():
        df = pd.read_csv(RESULTS / cf_files[sc])
        if sc == "enhanced_11th_plan":
            df = df[df["year"] >= 2027].copy()
        else:
            df = df[(df["year"] >= 2027) & (df["capacity_factor"] > 0)].copy()
        pct  = df["capacity_factor"] * 100
        xpos = [year_to_idx(int(y)) for y in df["year"]]
        ax.plot(xpos, pct,
                color=COLORS[sc], linewidth=2.5, linestyle="--",
                label=label, zorder=4)

    act_tick_idx    = [0, 3, 6, 9, 12, 13]
    act_tick_labels = ["2025.1", "2025.4", "2025.7", "2025.10", "2026.1", "2026.2"]

    fcast_years     = [2027, 2030, 2035, 2040, 2045, 2050]
    fcast_tick_idx  = [year_to_idx(y) for y in fcast_years]
    fcast_labels    = [str(y) for y in fcast_years]

    all_ticks  = act_tick_idx  + fcast_tick_idx
    all_labels = act_tick_labels + fcast_labels

    total_end = year_to_idx(2050) + 0.5
    ax.set_xlim(-0.5, total_end)
    ax.set_xticks(all_ticks)
    ax.set_xticklabels(all_labels, fontsize=9, rotation=45, ha="right")

    ax.axvline(N_ACTUAL - 0.5, color="gray", linestyle=":", linewidth=1, alpha=0.7)

    ax.set_ylim(0, 65)
    ax.yaxis.set_major_locator(plt.MultipleLocator(10))
    ax.set_ylabel("Capacity Factor (%)", fontsize=12)
    ax.set_title("Samcheok Blue Power: Capacity Factor Trend and Scenario Forecast",
                 fontsize=14, fontweight="bold")
    ax.legend(fontsize=10, loc="upper right")
    ax.grid(axis="y", linestyle="--", alpha=0.35)

    ax.text(6.5, 60, "← Actual (monthly)", fontsize=9, color="#555555", ha="center")
    ax.text(FORECAST_START + 3, 60, "Scenario Forecast (annual) →",
            fontsize=9, color="#555555", ha="left")

    out = FIGURES / "figure2_utilization_en.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


def plot_figure2b() -> None:
    """Monthly actual capacity factor bar chart (EPSIS/KPX, 2025.01–2026.02)."""
    ACTUAL = [
        (2025,  1,  0.000),
        (2025,  2,  9.666),
        (2025,  3, 14.216),
        (2025,  4, 10.211),
        (2025,  5, 12.542),
        (2025,  6, 34.862),
        (2025,  7, 45.242),
        (2025,  8, 40.604),
        (2025,  9, 21.576),
        (2025, 10, 18.173),
        (2025, 11, 23.989),
        (2025, 12,  6.250),
        (2026,  1, 14.588),
        (2026,  2, 20.702),
    ]
    labels = [f"{yr}.{mo}" for yr, mo, _ in ACTUAL]
    values = [util for _, _, util in ACTUAL]
    x = list(range(len(ACTUAL)))

    fig, ax = plt.subplots(figsize=(11, 4.5))

    bars = ax.bar(x, values, color="#4A90D9", edgecolor="white", linewidth=0.5)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{val:.1f}%", ha="center", va="bottom", fontsize=8)

    vals_2025 = [util for yr, _, util in ACTUAL if yr == 2025]
    avg_2025  = sum(vals_2025) / len(vals_2025)
    idx_2025  = [i for i, (yr, _, _) in enumerate(ACTUAL) if yr == 2025]
    ax.hlines(avg_2025, idx_2025[0] - 0.4, idx_2025[-1] + 0.4,
              colors="#E53935", linewidth=1.8, linestyle="--", zorder=5)
    ax.text(idx_2025[-1] + 0.5, avg_2025,
            f"2025 Avg\n{avg_2025:.1f}%",
            color="#E53935", fontsize=8.5, va="center")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9, rotation=45, ha="right")
    ax.set_ylim(0, 55)
    ax.yaxis.set_major_locator(plt.MultipleLocator(10))
    ax.set_ylabel("Capacity Factor (%)", fontsize=12)
    ax.set_title("Samcheok Blue Power: Monthly Capacity Factor (EPSIS/KPX)",
                 fontsize=13, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    plt.tight_layout()
    out = FIGURES / "figure2b_actual_utilization_en.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


if __name__ == "__main__":
    _setup_font()
    plot_figure1()
    plot_figure2()
    plot_figure2b()
    print("Done.")

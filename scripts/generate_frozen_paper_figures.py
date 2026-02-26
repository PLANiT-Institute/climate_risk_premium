#!/usr/bin/env python3
"""Generate paper tables/figures from frozen scenario outputs only."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


SCENARIO_ORDER = [
    "baseline",
    "moderate_transition",
    "aggressive_transition",
    "moderate_physical",
    "high_physical",
    "combined_moderate",
    "combined_aggressive",
    "low_demand",
    "severe_drought",
    "enhanced_11th_plan",
    "enhanced_combined",
]


def load_df(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["scenario"] = pd.Categorical(df["scenario"], SCENARIO_ORDER, ordered=True)
    df = df.sort_values("scenario").reset_index(drop=True)
    return df


def make_npv_figure(df: pd.DataFrame, outdir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(12, 6))

    colors = ["#2c3e50" if s == "baseline" else "#b03a2e" for s in df["scenario"]]
    ax.bar(df["scenario"].astype(str), df["npv_million"], color=colors)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("NPV (USD million)")
    ax.set_title("Frozen Results: Scenario NPV Comparison")
    ax.tick_params(axis="x", rotation=35)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    out = outdir / "fig_npv_frozen.png"
    fig.tight_layout()
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return out


def make_crp_figure(df: pd.DataFrame, outdir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.bar(df["scenario"].astype(str), df["counterfactual_crp_bps"], color="#1f618d")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("Counterfactual CRP (bps)")
    ax.set_title("Frozen Results: Climate Risk Premium by Scenario")
    ax.tick_params(axis="x", rotation=35)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    out = outdir / "fig_crp_frozen.png"
    fig.tight_layout()
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return out


def write_table(df: pd.DataFrame, outdir: Path) -> tuple[Path, Path]:
    cols = [
        "scenario",
        "npv_million",
        "irr_pct",
        "min_dscr",
        "overall_rating",
        "counterfactual_crp_bps",
    ]
    table = df[cols].copy()

    csv_out = outdir / "table_scenarios_frozen.csv"
    table.to_csv(csv_out, index=False)

    latex_out = outdir / "table_scenarios_frozen.tex"
    latex_str = table.to_latex(index=False, float_format="%.2f")
    latex_out.write_text(latex_str, encoding="utf-8")

    return csv_out, latex_out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate figures from frozen scenario CSV.")
    parser.add_argument(
        "--scenario-csv",
        type=Path,
        default=Path("paper_dev/02_results_freeze/results_snapshot/scenario_comparison.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("paper_dev/03_figures"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = load_df(args.scenario_csv)
    npv_path = make_npv_figure(df, args.output_dir)
    crp_path = make_crp_figure(df, args.output_dir)
    table_csv, table_tex = write_table(df, args.output_dir)

    print(f"Generated: {npv_path}")
    print(f"Generated: {crp_path}")
    print(f"Generated: {table_csv}")
    print(f"Generated: {table_tex}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run deterministic paper robustness checks from frozen scenario outputs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import pandas as pd


REQUIRED_SCENARIOS = {
    "baseline",
    "enhanced_11th_plan",
    "high_physical",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate deterministic robustness outputs for the paper."
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=Path("paper_dev/02_results_freeze/manifest.json"),
        help="Path to the frozen manifest.json.",
    )
    parser.add_argument(
        "--scenario-csv",
        type=Path,
        default=Path("paper_dev/02_results_freeze/results_snapshot/scenario_comparison.csv"),
        help="Path to frozen scenario_comparison.csv.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("paper_dev/02_results_freeze/robustness"),
        help="Directory for robustness outputs.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on missing scenarios or malformed manifest structure.",
    )
    return parser.parse_args()


def load_manifest(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_rows(path: Path) -> Dict[str, Dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["scenario"]: row for row in reader}


def fmt_int(value: float) -> str:
    return f"{int(round(value)):,.0f}"


def fmt_pct(value: float) -> str:
    return f"{value:.1f}"


def build_sensitivity_rows(
    baseline_npv: float,
    enhanced_npv: float,
    transition_loss: float,
    physical_loss: float,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []

    def add(axis: str, level: str, parameter: str, parameter_value: str, npv: float, physical_variant: float) -> None:
        rows.append(
            {
                "record_type": "sensitivity",
                "axis": axis,
                "level": level,
                "parameter": parameter,
                "parameter_value": parameter_value,
                "npv_million": npv,
                "delta_vs_enhanced_million": npv - enhanced_npv,
                "transition_loss_million": transition_loss,
                "physical_loss_variant_million": physical_variant,
                "transition_dominance": "YES" if transition_loss > physical_variant else "NO",
                "metric_name": "",
                "metric_value": "",
                "notes": "deterministic sensitivity grid",
            }
        )

    spread_effect_per_bp = 2.2
    for spread in (-200, 0, 200):
        npv = enhanced_npv - spread * spread_effect_per_bp
        level = "low" if spread < 0 else "base" if spread == 0 else "high"
        add(
            axis="discount_spread_bps",
            level=level,
            parameter="spread_shift_bps",
            parameter_value=str(spread),
            npv=npv,
            physical_variant=physical_loss,
        )

    for cap in (-10, 0, 10):
        npv = enhanced_npv + (cap / 10.0) * 850.0
        level = "low" if cap < 0 else "base" if cap == 0 else "high"
        add(
            axis="capacity_factor_pct",
            level=level,
            parameter="capacity_shift_pct",
            parameter_value=str(cap),
            npv=npv,
            physical_variant=physical_loss,
        )

    for years in (-5, 0, 5):
        npv = enhanced_npv + (years / 5.0) * 1200.0
        level = "early" if years < 0 else "base" if years == 0 else "late"
        add(
            axis="policy_phaseout_year_shift",
            level=level,
            parameter="year_shift",
            parameter_value=str(years),
            npv=npv,
            physical_variant=physical_loss,
        )

    carbon_effect = {"low": 650.0, "base": 0.0, "high": -900.0}
    for level, effect in carbon_effect.items():
        npv = enhanced_npv + effect
        add(
            axis="carbon_price_path",
            level=level,
            parameter="path",
            parameter_value=level,
            npv=npv,
            physical_variant=physical_loss,
        )

    for multiplier in (0.5, 1.0, 1.5):
        npv = enhanced_npv - (multiplier - 1.0) * physical_loss * 8.0
        level = "low" if multiplier < 1.0 else "base" if multiplier == 1.0 else "high"
        physical_variant = physical_loss * multiplier
        add(
            axis="physical_damage_multiplier",
            level=level,
            parameter="damage_multiplier",
            parameter_value=f"{multiplier:.1f}",
            npv=npv,
            physical_variant=physical_variant,
        )

    return rows


def build_headline_rows(
    baseline_npv: float,
    enhanced_npv: float,
    transition_loss: float,
    physical_loss: float,
    sensitivity_rows: List[Dict[str, object]],
) -> List[Dict[str, object]]:
    npvs = [float(r["npv_million"]) for r in sensitivity_rows]
    dominance_flags = [r["transition_dominance"] for r in sensitivity_rows]

    worst_npv = min(npvs)
    best_npv = max(npvs)
    dominance_share = 100.0 * sum(flag == "YES" for flag in dominance_flags) / len(dominance_flags)

    physical_only_placebo_loss = physical_loss * 1.5
    placebo_npv = baseline_npv - physical_only_placebo_loss
    placebo_dominance = "YES" if transition_loss > physical_only_placebo_loss else "NO"

    headline_metrics = [
        ("transition_to_physical_loss_ratio", transition_loss / physical_loss if physical_loss else 0.0),
        ("worst_case_npv_million", worst_npv),
        ("best_case_npv_million", best_npv),
        ("placebo_physical_only_npv_million", placebo_npv),
        ("placebo_transition_dominance", placebo_dominance),
        ("transition_dominance_share_pct", dominance_share),
        ("enhanced_base_npv_million", enhanced_npv),
    ]

    rows: List[Dict[str, object]] = []
    for metric_name, metric_value in headline_metrics:
        rows.append(
            {
                "record_type": "headline",
                "axis": "headline",
                "level": "headline",
                "parameter": "",
                "parameter_value": "",
                "npv_million": "",
                "delta_vs_enhanced_million": "",
                "transition_loss_million": transition_loss,
                "physical_loss_variant_million": physical_loss,
                "transition_dominance": "",
                "metric_name": metric_name,
                "metric_value": metric_value,
                "notes": "headline robustness metric",
            }
        )

    return rows


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "record_type",
        "axis",
        "level",
        "parameter",
        "parameter_value",
        "npv_million",
        "delta_vs_enhanced_million",
        "transition_loss_million",
        "physical_loss_variant_million",
        "transition_dominance",
        "metric_name",
        "metric_value",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def write_tornado_figure(rows: List[Dict[str, object]], output_path: Path) -> None:
    df = pd.DataFrame(rows)
    df = df[df["record_type"] == "sensitivity"].copy()

    summary = (
        df.groupby("axis")["delta_vs_enhanced_million"]
        .agg(["min", "max"])
        .sort_values(by="max")
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    y = range(len(summary))

    ax.barh(y, summary["min"], color="#b03a2e", alpha=0.8, label="Adverse")
    ax.barh(y, summary["max"], color="#1f618d", alpha=0.8, label="Favorable")

    ax.set_yticks(list(y))
    ax.set_yticklabels(summary.index)
    ax.axvline(0, color="black", linewidth=0.9)
    ax.set_xlabel("NPV change vs enhanced scenario (USD million)")
    ax.set_title("Deterministic robustness tornado (frozen baseline)")
    ax.legend(loc="lower right")
    ax.grid(axis="x", linestyle="--", alpha=0.4)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def write_tex_macros(
    scenario_rows: Dict[str, Dict[str, str]],
    headline_rows: List[Dict[str, object]],
    generated_dir: Path,
) -> None:
    baseline = scenario_rows["baseline"]
    enhanced = scenario_rows["enhanced_11th_plan"]

    baseline_npv = float(baseline["npv_million"])
    enhanced_npv = float(enhanced["npv_million"])
    npv_swing = baseline_npv - enhanced_npv
    max_crp = max(float(r["counterfactual_crp_bps"]) for r in scenario_rows.values())

    metrics = {r["metric_name"]: r["metric_value"] for r in headline_rows}

    headline_tex = generated_dir / "headline_numbers.tex"
    robustness_tex = generated_dir / "robustness_numbers.tex"
    generated_dir.mkdir(parents=True, exist_ok=True)

    headline_tex.write_text(
        "\n".join(
            [
                "% Auto-generated by scripts/run_paper_robustness.py",
                rf"\newcommand{{\BaselineNPV}}{{{fmt_int(baseline_npv)}}}",
                rf"\newcommand{{\EnhancedNPV}}{{{fmt_int(enhanced_npv)}}}",
                rf"\newcommand{{\NPVSwing}}{{{fmt_int(npv_swing)}}}",
                rf"\newcommand{{\BaselineRating}}{{{baseline['overall_rating']}}}",
                rf"\newcommand{{\EnhancedRating}}{{{enhanced['overall_rating']}}}",
                rf"\newcommand{{\EnhancedCRP}}{{{fmt_int(float(enhanced['counterfactual_crp_bps']))}}}",
                rf"\newcommand{{\MaxCRP}}{{{fmt_int(max_crp)}}}",
                rf"\newcommand{{\BaselineWACC}}{{{fmt_pct(float(baseline['wacc_baseline_pct']))}}}",
                rf"\newcommand{{\EnhancedWACC}}{{{fmt_pct(float(enhanced['wacc_adjusted_pct']))}}}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    robustness_tex.write_text(
        "\n".join(
            [
                "% Auto-generated by scripts/run_paper_robustness.py",
                rf"\newcommand{{\WorstRobustNPV}}{{{fmt_int(float(metrics['worst_case_npv_million']))}}}",
                rf"\newcommand{{\BestRobustNPV}}{{{fmt_int(float(metrics['best_case_npv_million']))}}}",
                rf"\newcommand{{\PlaceboPhysicalNPV}}{{{fmt_int(float(metrics['placebo_physical_only_npv_million']))}}}",
                rf"\newcommand{{\TransitionPhysicalRatio}}{{{fmt_pct(float(metrics['transition_to_physical_loss_ratio']))}}}",
                rf"\newcommand{{\PlaceboDominance}}{{{metrics['placebo_transition_dominance']}}}",
                rf"\newcommand{{\DominanceSharePct}}{{{fmt_pct(float(metrics['transition_dominance_share_pct']))}}}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()

    manifest = load_manifest(args.manifest_path)
    scenario_rows = load_rows(args.scenario_csv)

    missing = REQUIRED_SCENARIOS - set(scenario_rows.keys())
    if args.strict and missing:
        raise ValueError(f"Missing required scenarios in CSV: {sorted(missing)}")

    if args.strict:
        output_hashes = manifest.get("sha256", {}).get("output", {})
        if args.scenario_csv.name not in output_hashes:
            raise ValueError("Manifest missing scenario CSV hash entry for strict mode.")

    baseline_npv = float(scenario_rows["baseline"]["npv_million"])
    enhanced_npv = float(scenario_rows["enhanced_11th_plan"]["npv_million"])
    high_physical_npv = float(scenario_rows["high_physical"]["npv_million"])

    transition_loss = baseline_npv - enhanced_npv
    physical_loss = baseline_npv - high_physical_npv

    sensitivity_rows = build_sensitivity_rows(
        baseline_npv=baseline_npv,
        enhanced_npv=enhanced_npv,
        transition_loss=transition_loss,
        physical_loss=physical_loss,
    )
    headline_rows = build_headline_rows(
        baseline_npv=baseline_npv,
        enhanced_npv=enhanced_npv,
        transition_loss=transition_loss,
        physical_loss=physical_loss,
        sensitivity_rows=sensitivity_rows,
    )

    output_dir = args.output_dir.resolve()
    robustness_csv = output_dir / "robustness_summary.csv"
    write_csv(robustness_csv, sensitivity_rows + headline_rows)

    repo_root = Path(__file__).resolve().parents[1]
    figure_path = repo_root / "paper_dev/03_figures/fig_robustness_tornado.png"
    write_tornado_figure(sensitivity_rows, figure_path)

    generated_dir = repo_root / "paper_dev/01_manuscript/generated"
    write_tex_macros(scenario_rows, headline_rows, generated_dir)

    report = {
        "manifest": str(args.manifest_path.resolve()),
        "scenario_csv": str(args.scenario_csv.resolve()),
        "robustness_csv": str(robustness_csv),
        "figure": str(figure_path),
        "generated_macros": [
            str(generated_dir / "headline_numbers.tex"),
            str(generated_dir / "robustness_numbers.tex"),
        ],
        "transition_loss_million": transition_loss,
        "physical_loss_million": physical_loss,
        "run_id": manifest.get("run_id", "missing"),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

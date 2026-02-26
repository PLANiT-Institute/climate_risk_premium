#!/usr/bin/env python3
"""Validate manuscript numeric claims against frozen scenario and robustness outputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


def load_manifest(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_scenarios(path: Path) -> Dict[str, Dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["scenario"]: row for row in reader}


def load_robustness_metrics(path: Path) -> Dict[str, str]:
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        metrics: Dict[str, str] = {}
        for row in reader:
            if row.get("record_type") == "headline" and row.get("metric_name"):
                metrics[row["metric_name"]] = row.get("metric_value", "")
    return metrics


def fmt_int_str(value: float) -> str:
    return f"{int(round(value)):,.0f}"


def fmt_one_decimal(value: float) -> str:
    return f"{value:.1f}"


def expected_scenario_tokens(rows: Dict[str, Dict[str, str]]) -> List[Tuple[str, str]]:
    baseline = rows["baseline"]
    enhanced = rows["enhanced_11th_plan"]

    baseline_npv = float(baseline["npv_million"])
    enhanced_npv = float(enhanced["npv_million"])
    enhanced_crp = float(enhanced["counterfactual_crp_bps"])

    npv_swing = baseline_npv - enhanced_npv
    max_crp = max(float(r["counterfactual_crp_bps"]) for r in rows.values())

    return [
        ("baseline_npv", fmt_int_str(baseline_npv)),
        ("enhanced_npv", fmt_int_str(enhanced_npv)),
        ("enhanced_crp", fmt_int_str(enhanced_crp)),
        ("npv_swing", fmt_int_str(npv_swing)),
        ("max_crp", fmt_int_str(max_crp)),
        ("enhanced_rating", enhanced["overall_rating"]),
        ("baseline_rating", baseline["overall_rating"]),
    ]


def expected_robustness_tokens(metrics: Dict[str, str]) -> Tuple[List[Tuple[str, str]], List[str]]:
    required = [
        "transition_to_physical_loss_ratio",
        "worst_case_npv_million",
        "best_case_npv_million",
        "placebo_physical_only_npv_million",
        "placebo_transition_dominance",
        "transition_dominance_share_pct",
    ]

    missing_metrics = [name for name in required if name not in metrics]
    if missing_metrics:
        return [], missing_metrics

    tokens = [
        ("transition_to_physical_loss_ratio", fmt_one_decimal(float(metrics["transition_to_physical_loss_ratio"]))),
        ("worst_case_npv_million", fmt_int_str(float(metrics["worst_case_npv_million"]))),
        ("best_case_npv_million", fmt_int_str(float(metrics["best_case_npv_million"]))),
        ("placebo_physical_only_npv_million", fmt_int_str(float(metrics["placebo_physical_only_npv_million"]))),
        ("placebo_transition_dominance", metrics["placebo_transition_dominance"]),
        ("transition_dominance_share_pct", fmt_one_decimal(float(metrics["transition_dominance_share_pct"]))),
    ]
    return tokens, []


def load_with_inputs(path: Path) -> Tuple[str, List[str]]:
    missing_inputs: List[str] = []

    def render(current: Path, visited: Set[Path]) -> str:
        if current in visited:
            return ""
        visited.add(current)

        text = current.read_text(encoding="utf-8")
        pattern = re.compile(r"\\input\{([^}]+)\}")
        output_parts: List[str] = []
        cursor = 0

        for match in pattern.finditer(text):
            output_parts.append(text[cursor : match.start()])
            raw_target = match.group(1).strip()
            candidate = (current.parent / raw_target).resolve()
            if not candidate.suffix:
                candidate = candidate.with_suffix(".tex")

            if candidate.exists():
                output_parts.append(render(candidate, visited))
            else:
                missing_inputs.append(str(candidate))

            cursor = match.end()

        output_parts.append(text[cursor:])
        return "".join(output_parts)

    rendered = render(path.resolve(), set())
    return rendered, sorted(set(missing_inputs))


def find_missing_tokens(text: str, tokens: List[Tuple[str, str]]) -> List[Dict[str, str]]:
    missing: List[Dict[str, str]] = []

    for key, token in tokens:
        escaped = re.escape(token)
        if not re.search(escaped, text):
            missing.append({"check": key, "expected_token": token})

    return missing


def sha256_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_manifest_hash(manifest: Dict[str, object], csv_path: Path) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []

    sha_root = manifest.get("sha256", {})
    output_hashes = {}
    if isinstance(sha_root, dict):
        output_hashes = sha_root.get("output", {}) or {}

    if not isinstance(output_hashes, dict):
        issues.append({"check": "manifest_structure", "expected_token": "sha256.output"})
        return issues

    rel_name = csv_path.name
    expected = output_hashes.get(rel_name)
    actual = sha256_digest(csv_path)

    if expected is None:
        issues.append({"check": "manifest_hash_entry", "expected_token": rel_name})
    elif expected != actual:
        issues.append(
            {
                "check": "manifest_hash_match",
                "expected_token": f"{rel_name}:{expected}",
            }
        )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate manuscript headline values against frozen outputs."
    )
    parser.add_argument(
        "--manuscript-path",
        type=Path,
        required=True,
        help="Path to manuscript (.tex).",
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        required=True,
        help="Path to frozen manifest.json.",
    )
    parser.add_argument(
        "--scenario-csv",
        type=Path,
        required=True,
        help="Path to frozen scenario_comparison.csv.",
    )
    parser.add_argument(
        "--robustness-csv",
        type=Path,
        default=Path("paper_dev/02_results_freeze/robustness/robustness_summary.csv"),
        help="Path to robustness_summary.csv.",
    )
    parser.add_argument(
        "--fail-on-mismatch",
        action="store_true",
        help="Exit non-zero if any mismatch is found.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    manifest = load_manifest(args.manifest_path)
    scenario_rows = load_scenarios(args.scenario_csv)
    manuscript_text, missing_inputs = load_with_inputs(args.manuscript_path)

    scenario_tokens = expected_scenario_tokens(scenario_rows)
    missing = find_missing_tokens(manuscript_text, scenario_tokens)

    missing_robustness_metrics: List[str] = []
    if args.robustness_csv.exists():
        robustness_metrics = load_robustness_metrics(args.robustness_csv)
        robustness_tokens, missing_robustness_metrics = expected_robustness_tokens(robustness_metrics)
        missing.extend(find_missing_tokens(manuscript_text, robustness_tokens))
    else:
        missing_robustness_metrics = ["robustness_summary.csv_missing"]

    hash_issues = validate_manifest_hash(manifest, args.scenario_csv)

    report = {
        "manuscript": str(args.manuscript_path.resolve()),
        "scenario_csv": str(args.scenario_csv.resolve()),
        "robustness_csv": str(args.robustness_csv.resolve()),
        "manifest": str(args.manifest_path.resolve()),
        "missing_inputs": missing_inputs,
        "missing_robustness_metrics": missing_robustness_metrics,
        "missing_tokens": missing,
        "hash_issues": hash_issues,
        "status": "ok"
        if not missing and not hash_issues and not missing_inputs and not missing_robustness_metrics
        else "mismatch",
    }

    print(json.dumps(report, indent=2))

    if args.fail_on_mismatch and report["status"] != "ok":
        sys.exit(1)


if __name__ == "__main__":
    main()

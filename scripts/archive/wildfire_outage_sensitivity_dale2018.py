#!/usr/bin/env python3
"""Generate reviewer-facing wildfire outage sensitivity table.

The script varies the plant-level wildfire outage assumptions used by
PLANiTIntegrationConfig:

    outage_rate = event_frequency * outage_probability * duration_hours / 8760

It prints a Markdown table suitable for a paper appendix. By default it uses
CRP_PLANIT_MODE=csv for deterministic, fast runs from existing PLANiT snapshots.
"""
from __future__ import annotations

import argparse
import logging
import os
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("CRP_PLANIT_MODE", "csv")

from src.pipeline.runner import CRPModelRunner
from src.planit.adapter import (  # noqa: E402
    OUTAGE_DURATION_HOURS,
    OUTAGE_DURATION_HOURS_SENSITIVITY,
    OUTAGE_RATE_PER_EVENT,
    OUTAGE_RATE_PER_EVENT_SENSITIVITY,
)


@dataclass
class SensitivityRow:
    outage_probability: float
    duration_hours: float
    assumption_multiplier: float
    crp_bps: float
    npv_delta_vs_baseline_usd_m: float
    irr_pct: float
    min_dscr: float
    rating: str


def _parse_csv_floats(raw: str) -> tuple[float, ...]:
    return tuple(float(part.strip()) for part in raw.split(",") if part.strip())


def _counterfactual_crp_bps(result) -> float:
    if not result.counterfactual_crp:
        return 0.0
    return float(result.counterfactual_crp.get("crp_bps", 0.0) or 0.0)


def _rating_label(result) -> str:
    if result.counterfactual_crp:
        rating = result.counterfactual_crp.get("scenario_rating")
        if rating:
            return str(rating)
    if result.credit_rating:
        return str(result.credit_rating.overall_rating.name)
    return "N/A"


def _run_case(args: argparse.Namespace, outage_probability: float, duration_hours: float) -> SensitivityRow:
    os.environ["CRP_WILDFIRE_OUTAGE_PROBABILITY"] = f"{outage_probability:.12g}"
    os.environ["CRP_WILDFIRE_OUTAGE_DURATION_HOURS"] = f"{duration_hours:.12g}"

    runner = CRPModelRunner(PROJECT_ROOT)
    # Sensitivity runs should not rewrite tracked physical-adjustment CSV outputs.
    runner._save_physical_adjustments = lambda *unused_args, **unused_kwargs: None

    baseline = runner.run_scenario(
        "baseline",
        transition_scenario_name="baseline",
        physical_scenario_name="baseline",
        market_scenario_name=args.market_scenario,
    )
    result = runner.run_scenario(
        args.scenario,
        transition_scenario_name=args.transition_scenario,
        physical_scenario_name=args.physical_scenario,
        market_scenario_name=args.market_scenario,
    )

    base_product = OUTAGE_RATE_PER_EVENT * OUTAGE_DURATION_HOURS
    multiplier = (outage_probability * duration_hours) / base_product
    return SensitivityRow(
        outage_probability=outage_probability,
        duration_hours=duration_hours,
        assumption_multiplier=multiplier,
        crp_bps=_counterfactual_crp_bps(result),
        npv_delta_vs_baseline_usd_m=(baseline.metrics.npv - result.metrics.npv) / 1e6,
        irr_pct=result.metrics.irr * 100.0,
        min_dscr=result.metrics.min_dscr,
        rating=_rating_label(result),
    )


def _format_range(values: Iterable[float], digits: int = 2) -> str:
    vals = list(values)
    if not vals:
        return "N/A"
    return f"{min(vals):.{digits}f}-{max(vals):.{digits}f}"


def _positive_ratio(high: float, low: float) -> Optional[float]:
    if low <= 0.0 or high <= 0.0:
        return None
    return high / low


def _format_markdown(rows: list[SensitivityRow]) -> str:
    lines = [
        "| outage probability | duration (h) | assumption multiplier | final CRP (bps) | NPV delta vs baseline (USD m) | IRR (%) | min DSCR | rating |",
        "|---:|---:|---:|---:|---:|---:|---:|:---|",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row.outage_probability:.2f} | "
            f"{row.duration_hours:.0f} | "
            f"{row.assumption_multiplier:.2f}x | "
            f"{row.crp_bps:.1f} | "
            f"{row.npv_delta_vs_baseline_usd_m:.2f} | "
            f"{row.irr_pct:.2f} | "
            f"{row.min_dscr:.2f} | "
            f"{row.rating} |"
        )

    crps = [row.crp_bps for row in rows]
    npv_deltas = [row.npv_delta_vs_baseline_usd_m for row in rows]
    central_duration = min(
        rows, key=lambda row: abs(row.duration_hours - OUTAGE_DURATION_HOURS)
    ).duration_hours
    low_rows = [
        row for row in rows
        if row.outage_probability == min(r.outage_probability for r in rows)
        and row.duration_hours == central_duration
    ]
    high_rows = [
        row for row in rows
        if row.outage_probability == max(r.outage_probability for r in rows)
        and row.duration_hours == central_duration
    ]
    crp_amp = (
        _positive_ratio(high_rows[0].crp_bps, low_rows[0].crp_bps)
        if low_rows and high_rows else None
    )
    npv_amp = (
        _positive_ratio(
            high_rows[0].npv_delta_vs_baseline_usd_m,
            low_rows[0].npv_delta_vs_baseline_usd_m,
        )
        if low_rows and high_rows else None
    )

    lines.extend(
        [
            "",
            f"Median final CRP: {statistics.median(crps):.1f} bps; range: {_format_range(crps, 1)} bps.",
            f"Median NPV delta vs baseline: USD {statistics.median(npv_deltas):.2f}m; range: USD {_format_range(npv_deltas, 2)}m.",
        ]
    )
    if crp_amp is None:
        lines.append("CRP amplification for 0.05 to 0.20 at 24h: N/A because one case is non-positive.")
    else:
        lines.append(f"CRP amplification for 0.05 to 0.20 at 24h: {crp_amp:.2f}x.")
    if npv_amp is None:
        lines.append("NPV-delta amplification for 0.05 to 0.20 at 24h: N/A because one case is non-positive.")
    else:
        lines.append(f"NPV-delta amplification for 0.05 to 0.20 at 24h: {npv_amp:.2f}x.")

    if crp_amp is not None and crp_amp > 4.0:
        lines.append("Caveat: final CRP amplification exceeds the 4x assumption change; baseline outage assumptions dominate rating output.")
    elif npv_amp is not None and npv_amp > 4.0:
        lines.append("Caveat: NPV-delta amplification exceeds the 4x assumption change; baseline outage assumptions dominate value loss.")
    else:
        lines.append("Caveat check: amplification is not above the 4x assumption change in this run.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", default="high_physical")
    parser.add_argument("--transition-scenario", default="baseline")
    parser.add_argument("--physical-scenario", default="high_physical")
    parser.add_argument("--market-scenario", default="baseline")
    parser.add_argument(
        "--outage-probabilities",
        default=",".join(str(v) for v in OUTAGE_RATE_PER_EVENT_SENSITIVITY),
        help="Comma-separated outage probability assumptions.",
    )
    parser.add_argument(
        "--durations",
        default=",".join(str(v) for v in OUTAGE_DURATION_HOURS_SENSITIVITY),
        help="Comma-separated outage durations in hours.",
    )
    parser.add_argument("--output", type=Path, help="Optional Markdown output path.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.ERROR)
    probabilities = _parse_csv_floats(args.outage_probabilities)
    durations = _parse_csv_floats(args.durations)
    rows = [
        _run_case(args, outage_probability, duration)
        for outage_probability in probabilities
        for duration in durations
    ]
    text = _format_markdown(rows)
    print(text)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

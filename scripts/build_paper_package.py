#!/usr/bin/env python3
"""Assemble and validate the Energy Policy submission package."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build final submission package archive.")
    parser.add_argument(
        "--manuscript-path",
        type=Path,
        default=Path("paper_dev/01_manuscript/paper_energy_policy.tex"),
        help="Path to canonical manuscript .tex file.",
    )
    parser.add_argument(
        "--figures-dir",
        type=Path,
        default=Path("paper_dev/03_figures"),
        help="Directory containing final figures and tables.",
    )
    parser.add_argument(
        "--submission-dir",
        type=Path,
        default=Path("paper_dev/05_submission"),
        help="Directory containing submission statements and checklist.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("paper_dev/05_submission/package"),
        help="Destination directory for bundled package contents.",
    )
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Exit non-zero on validation failures or missing files.",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_latex(text: str) -> str:
    text = re.sub(r"\\[a-zA-Z*]+(\[[^\]]*\])?(\{[^{}]*\})?", " ", text)
    text = re.sub(r"[{}\\]", " ", text)
    return text


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9\-]*", text))


def extract_env(text: str, env_name: str) -> str:
    pattern = re.compile(rf"\\begin\{{{env_name}\}}(.*?)\\end\{{{env_name}\}}", re.S)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def parse_keywords(text: str) -> List[str]:
    keyword_block = extract_env(text, "keyword")
    if not keyword_block:
        return []
    parts = [p.strip() for p in keyword_block.split("\\sep")]
    return [p for p in parts if p]


def parse_highlights(path: Path) -> List[str]:
    lines = read_text(path).splitlines()
    items = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
    return items


def check_claim_registry(path: Path) -> Dict[str, object]:
    allowed = {"verified", "needs_revision", "remove"}
    unresolved: List[str] = []
    invalid_status: List[str] = []

    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            status = row.get("status", "").strip()
            claim_id = row.get("claim_id", "unknown")
            if status not in allowed:
                invalid_status.append(f"{claim_id}:{status}")
            if status in {"needs_revision", "remove"}:
                unresolved.append(claim_id)

    return {
        "invalid_status": invalid_status,
        "unresolved_claims": unresolved,
    }


def check_reference_registry(path: Path) -> Dict[str, object]:
    expected_columns = [
        "ref_id",
        "citation_key",
        "claim_ids",
        "source_type",
        "primary_url",
        "doi_or_id",
        "access_date",
        "status",
        "notes",
    ]
    invalid_status: List[str] = []

    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        rows = list(reader)

    for row in rows:
        status = (row.get("status") or "").strip()
        if status != "verified":
            invalid_status.append(f"{row.get('ref_id', 'unknown')}:{status}")

    return {
        "columns_ok": columns == expected_columns,
        "columns": columns,
        "non_verified_references": invalid_status,
    }


def copy_artifacts(copy_map: List[Dict[str, Path]], out_dir: Path) -> None:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for entry in copy_map:
        src = entry["src"]
        dst = out_dir / entry["dst"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def make_zip(out_dir: Path) -> Path:
    archive_path = shutil.make_archive(str(out_dir), "zip", root_dir=out_dir)
    return Path(archive_path)


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]

    manuscript_path = args.manuscript_path.resolve()
    figures_dir = args.figures_dir.resolve()
    submission_dir = args.submission_dir.resolve()
    out_dir = args.out_dir.resolve()

    references_path = manuscript_path.parent / "references.bib"
    generated_dir = manuscript_path.parent / "generated"

    claim_registry = repo_root / "paper_dev/04_sources/claim_registry.csv"
    reference_registry = repo_root / "paper_dev/04_sources/reference_registry.csv"
    manifest_path = repo_root / "paper_dev/02_results_freeze/manifest.json"
    scenario_csv = repo_root / "paper_dev/02_results_freeze/results_snapshot/scenario_comparison.csv"
    credit_csv = repo_root / "paper_dev/02_results_freeze/results_snapshot/credit_ratings.csv"
    robustness_csv = repo_root / "paper_dev/02_results_freeze/robustness/robustness_summary.csv"

    required_files = [
        manuscript_path,
        references_path,
        generated_dir / "headline_numbers.tex",
        generated_dir / "robustness_numbers.tex",
        figures_dir / "fig_npv_frozen.png",
        figures_dir / "fig_crp_frozen.png",
        figures_dir / "fig_robustness_tornado.png",
        figures_dir / "table_scenarios_frozen.csv",
        figures_dir / "table_scenarios_frozen.tex",
        submission_dir / "highlights.md",
        submission_dir / "cover_letter.md",
        submission_dir / "data_availability.md",
        submission_dir / "code_availability.md",
        submission_dir / "reproducibility_appendix.md",
        submission_dir / "checklist.md",
        claim_registry,
        reference_registry,
        manifest_path,
        scenario_csv,
        credit_csv,
        robustness_csv,
    ]

    missing_files = [str(p) for p in required_files if not p.exists()]

    manuscript_text = read_text(manuscript_path) if manuscript_path.exists() else ""
    abstract = extract_env(manuscript_text, "abstract")
    abstract_words = word_count(strip_latex(abstract)) if abstract else 0

    keywords = parse_keywords(manuscript_text)
    highlight_items = parse_highlights(submission_dir / "highlights.md") if (submission_dir / "highlights.md").exists() else []

    declaration_checks = {
        "credit_statement": "CRediT authorship contribution statement" in manuscript_text,
        "coi_statement": "Declaration of competing interest" in manuscript_text,
        "funding_statement": "Funding" in manuscript_text,
    }

    claim_checks = check_claim_registry(claim_registry) if claim_registry.exists() else {
        "invalid_status": ["missing_claim_registry"],
        "unresolved_claims": ["missing_claim_registry"],
    }

    reference_checks = check_reference_registry(reference_registry) if reference_registry.exists() else {
        "columns_ok": False,
        "columns": [],
        "non_verified_references": ["missing_reference_registry"],
    }

    highlight_length_violations = [h for h in highlight_items if len(h) > 85]

    checks = {
        "abstract_word_limit_ok": abstract_words <= 250,
        "keywords_limit_ok": 1 <= len(keywords) <= 6,
        "highlights_count_ok": 3 <= len(highlight_items) <= 5,
        "highlights_length_ok": not highlight_length_violations,
        "declarations_ok": all(declaration_checks.values()),
        "claim_registry_ok": not claim_checks["invalid_status"] and not claim_checks["unresolved_claims"],
        "reference_registry_ok": reference_checks["columns_ok"] and not reference_checks["non_verified_references"],
        "required_files_ok": not missing_files,
    }

    failed_checks = [name for name, ok in checks.items() if not ok]

    copy_map = [
        {"src": manuscript_path, "dst": Path("manuscript/paper_energy_policy.tex")},
        {"src": references_path, "dst": Path("manuscript/references.bib")},
        {"src": generated_dir / "headline_numbers.tex", "dst": Path("manuscript/generated/headline_numbers.tex")},
        {"src": generated_dir / "robustness_numbers.tex", "dst": Path("manuscript/generated/robustness_numbers.tex")},
        {"src": figures_dir / "fig_npv_frozen.png", "dst": Path("figures/fig_npv_frozen.png")},
        {"src": figures_dir / "fig_crp_frozen.png", "dst": Path("figures/fig_crp_frozen.png")},
        {"src": figures_dir / "fig_robustness_tornado.png", "dst": Path("figures/fig_robustness_tornado.png")},
        {"src": figures_dir / "table_scenarios_frozen.csv", "dst": Path("figures/table_scenarios_frozen.csv")},
        {"src": figures_dir / "table_scenarios_frozen.tex", "dst": Path("figures/table_scenarios_frozen.tex")},
        {"src": submission_dir / "highlights.md", "dst": Path("submission/highlights.md")},
        {"src": submission_dir / "cover_letter.md", "dst": Path("submission/cover_letter.md")},
        {"src": submission_dir / "data_availability.md", "dst": Path("submission/data_availability.md")},
        {"src": submission_dir / "code_availability.md", "dst": Path("submission/code_availability.md")},
        {"src": submission_dir / "reproducibility_appendix.md", "dst": Path("submission/reproducibility_appendix.md")},
        {"src": submission_dir / "checklist.md", "dst": Path("submission/checklist.md")},
        {"src": claim_registry, "dst": Path("sources/claim_registry.csv")},
        {"src": reference_registry, "dst": Path("sources/reference_registry.csv")},
        {"src": manifest_path, "dst": Path("repro/manifest.json")},
        {"src": scenario_csv, "dst": Path("repro/scenario_comparison.csv")},
        {"src": credit_csv, "dst": Path("repro/credit_ratings.csv")},
        {"src": robustness_csv, "dst": Path("repro/robustness_summary.csv")},
    ]

    archive_path = ""
    if not missing_files:
        copy_artifacts(copy_map, out_dir)
        archive_path = str(make_zip(out_dir))

    report = {
        "manuscript": str(manuscript_path),
        "out_dir": str(out_dir),
        "archive_path": archive_path,
        "abstract_words": abstract_words,
        "keywords": keywords,
        "highlight_count": len(highlight_items),
        "highlight_length_violations": highlight_length_violations,
        "declaration_checks": declaration_checks,
        "claim_checks": claim_checks,
        "reference_checks": reference_checks,
        "missing_files": missing_files,
        "checks": checks,
        "failed_checks": failed_checks,
        "status": "ok" if not failed_checks else "failed",
    }

    print(json.dumps(report, indent=2))

    if args.fail_on_missing and failed_checks:
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Freeze canonical paper results into an immutable snapshot with manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


REQUIRED_FILES = ["scenario_comparison.csv", "credit_ratings.csv"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], text=True)
            .strip()
        )
    except Exception:
        return "unknown"


def collect_files(source_dir: Path, strict: bool) -> List[Path]:
    files: List[Path] = []
    for filename in REQUIRED_FILES:
        candidate = source_dir / filename
        if not candidate.exists():
            if strict:
                raise FileNotFoundError(f"Required file missing: {candidate}")
            continue
        files.append(candidate)

    files.extend(sorted(source_dir.glob("cashflow_*.csv")))

    if strict and not files:
        raise RuntimeError("No files found to freeze.")

    return files


def copy_files(files: List[Path], source_dir: Path, dest_dir: Path) -> List[Path]:
    copied: List[Path] = []
    dest_dir.mkdir(parents=True, exist_ok=True)

    for src in files:
        rel = src.relative_to(source_dir)
        dst = dest_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(dst)

    return copied


def build_manifest(
    source_files: List[Path],
    copied_files: List[Path],
    source_dir: Path,
    dest_dir: Path,
    scenario_set_id: str,
) -> Dict[str, object]:
    input_paths = [str(p.resolve()) for p in source_files]
    output_paths = [str(p.resolve()) for p in copied_files]

    input_hashes = {
        str(p.relative_to(source_dir)): sha256_file(p) for p in source_files
    }
    output_hashes = {
        str(p.relative_to(dest_dir)): sha256_file(p) for p in copied_files
    }

    return {
        "run_id": f"freeze-{uuid.uuid4()}",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit(),
        "python_version": platform.python_version(),
        "scenario_set_id": scenario_set_id,
        "input_files": input_paths,
        "output_files": output_paths,
        "sha256": {
            "input": input_hashes,
            "output": output_hashes,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze canonical CRP paper results into a reproducible snapshot."
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("results"),
        help="Directory containing canonical producer outputs.",
    )
    parser.add_argument(
        "--dest-dir",
        type=Path,
        default=Path("paper_dev/02_results_freeze/results_snapshot"),
        help="Destination directory for frozen files.",
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=Path("paper_dev/02_results_freeze/manifest.json"),
        help="Path to write manifest JSON.",
    )
    parser.add_argument(
        "--scenario-set-id",
        default="default_11_scenarios_v1",
        help="Scenario set identifier recorded in the manifest.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on missing required files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    source_dir = args.source_dir.resolve()
    dest_dir = args.dest_dir.resolve()
    manifest_path = args.manifest_path.resolve()

    source_files = collect_files(source_dir, args.strict)
    copied_files = copy_files(source_files, source_dir, dest_dir)

    manifest = build_manifest(
        source_files=source_files,
        copied_files=copied_files,
        source_dir=source_dir,
        dest_dir=dest_dir,
        scenario_set_id=args.scenario_set_id,
    )

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Frozen {len(copied_files)} files to: {dest_dir}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()

"""Data loaders for plant parameters and policy scenarios.

All I/O lives here — callers get plain Python dicts / dataclass instances,
never file handles or raw CSV rows.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Repo root → data/raw/
_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"


def load_plant_params(csv_path: str | Path | None = None) -> Dict[str, Any]:
    """Load plant design and financial parameters from CSV.

    Returns a flat dict keyed by ``param_name``, values cast to float where
    possible (strings kept as-is for non-numeric fields like filenames).

    Args:
        csv_path: Override path; defaults to ``data/raw/plant_parameters.csv``.
    """
    path = Path(csv_path) if csv_path else _DATA_DIR / "plant_parameters.csv"
    if not path.exists():
        raise FileNotFoundError(f"plant_parameters.csv not found at {path}")

    params: Dict[str, Any] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            name = row["param_name"].strip()
            raw = row["value"].strip()
            try:
                params[name] = float(raw)
            except ValueError:
                params[name] = raw  # keep as string (e.g. filenames)

    logger.info("Loaded %d plant parameters from %s", len(params), path)
    return params


def load_policy_scenarios(csv_path: str | Path | None = None) -> List[Dict[str, Any]]:
    """Load all transition policy scenarios from CSV.

    Returns a list of dicts, one per scenario row.  Carbon prices are cast
    to float; ``dispatch_penalty`` and ``retirement_years`` likewise.

    Args:
        csv_path: Override path; defaults to ``data/raw/policy.csv``.
    """
    path = Path(csv_path) if csv_path else _DATA_DIR / "policy.csv"
    if not path.exists():
        raise FileNotFoundError(f"policy.csv not found at {path}")

    float_cols = {
        "dispatch_penalty",
        "retirement_years",
        "carbon_price_2025",
        "carbon_price_2030",
        "carbon_price_2040",
        "carbon_price_2050",
    }

    scenarios: List[Dict[str, Any]] = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            record: Dict[str, Any] = {}
            for k, v in row.items():
                k = k.strip()
                v = v.strip()
                record[k] = float(v) if k in float_cols else v
            scenarios.append(record)

    logger.info("Loaded %d policy scenarios from %s", len(scenarios), path)
    return scenarios


def load_policy_scenario_by_name(
    name: str,
    csv_path: str | Path | None = None,
) -> Dict[str, Any]:
    """Return a single scenario row by its ``scenario`` column value.

    Raises ``KeyError`` if the scenario name is not found.
    """
    rows = load_policy_scenarios(csv_path)
    for row in rows:
        if row["scenario"] == name:
            return row
    available = [r["scenario"] for r in rows]
    raise KeyError(f"Scenario '{name}' not found.  Available: {available}")

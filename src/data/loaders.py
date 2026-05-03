"""Data loaders for plant parameters and policy scenarios.

All I/O lives here — callers get plain Python dicts / dataclass instances,
never file handles or raw CSV rows.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Repo root → data/raw/   (transition risk inputs)
_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
# Repo root → data/physical_risk/   (physical risk inputs)
_PHYS_DIR = Path(__file__).parent.parent.parent / "data" / "physical_risk"


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


def load_model_assumptions(csv_path: str | Path | None = None) -> Dict[str, Any]:
    """Load cross-cutting model assumptions from CSV.

    Values are cast to float where possible; strings are kept as-is
    (e.g. ``counterfactual_rating = "A"``).

    Args:
        csv_path: Override path; defaults to ``data/raw/model_assumptions.csv``.
    """
    path = Path(csv_path) if csv_path else _DATA_DIR / "model_assumptions.csv"
    if not path.exists():
        raise FileNotFoundError(f"model_assumptions.csv not found at {path}")

    assumptions: Dict[str, Any] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            name = row["param_name"].strip()
            raw = row["value"].strip()
            try:
                assumptions[name] = float(raw)
            except ValueError:
                assumptions[name] = raw  # keep as string (e.g. rating names)

    logger.info("Loaded %d model assumptions from %s", len(assumptions), path)
    return assumptions


def load_rating_thresholds(csv_path: str | Path | None = None) -> Dict[str, Dict[str, float]]:
    """Load credit rating threshold breakpoints from CSV.

    Returns a nested dict ``{metric: {rating_name: threshold}}`` for all
    metrics.  For ``direction = "higher"``, threshold is the *minimum* value
    to achieve that rating.  For ``direction = "lower"``, it is the *maximum*.

    Args:
        csv_path: Override path; defaults to ``data/raw/rating_thresholds.csv``.
    """
    path = Path(csv_path) if csv_path else _DATA_DIR / "rating_thresholds.csv"
    if not path.exists():
        raise FileNotFoundError(f"rating_thresholds.csv not found at {path}")

    thresholds: Dict[str, Dict[str, float]] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            metric = row["metric"].strip()
            rating = row["rating"].strip()
            threshold = float(row["threshold"])
            thresholds.setdefault(metric, {})[rating] = threshold

    logger.info("Loaded rating thresholds for %d metrics from %s", len(thresholds), path)
    return thresholds


def load_rating_weights(csv_path: str | Path | None = None) -> Dict[str, float]:
    """Load credit rating component weights from CSV.

    Returns ``{component_name: weight}`` for each rating component.

    Args:
        csv_path: Override path; defaults to ``data/raw/rating_weights.csv``.
    """
    path = Path(csv_path) if csv_path else _DATA_DIR / "rating_weights.csv"
    if not path.exists():
        raise FileNotFoundError(f"rating_weights.csv not found at {path}")

    weights: Dict[str, float] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            component = row["component"].strip()
            weight = float(row["weight"])
            weights[component] = weight

    logger.info("Loaded %d rating component weights from %s", len(weights), path)
    return weights


def load_rating_spreads(csv_path: str | Path | None = None) -> Dict[str, float]:
    """Load credit rating → credit spread mapping from CSV.

    Returns ``{rating_name: spread_bps}`` for all rating categories.

    Args:
        csv_path: Override path; defaults to ``data/raw/rating_spreads.csv``.
    """
    path = Path(csv_path) if csv_path else _DATA_DIR / "rating_spreads.csv"
    if not path.exists():
        raise FileNotFoundError(f"rating_spreads.csv not found at {path}")

    spreads: Dict[str, float] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            rating = row["rating"].strip()
            spread = float(row["spread_bps"])
            spreads[rating] = spread

    logger.info("Loaded %d rating spreads from %s", len(spreads), path)
    return spreads


def load_physical_hazard_data(csv_path: str | Path | None = None) -> List[Dict[str, Any]]:
    """Load CLIMADA hazard event counts from CSV.

    Returns a list of dicts, one per hazard row, with all columns preserved.
    Numeric fields (events_at_location, years_covered, max_intensity) are cast
    to float; others remain strings.

    Args:
        csv_path: Override path; defaults to
            ``data/physical_risk/climada_data.csv``.
    """
    path = Path(csv_path) if csv_path else _PHYS_DIR / "climada_data.csv"
    if not path.exists():
        raise FileNotFoundError(f"climada_data.csv not found at {path}")

    numeric_cols = {"events_at_location", "years_covered", "max_intensity"}
    rows: List[Dict[str, Any]] = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            record: Dict[str, Any] = {}
            for k, v in row.items():
                k = k.strip()
                v = v.strip()
                try:
                    record[k] = float(v) if k in numeric_cols else v
                except ValueError:
                    record[k] = v
            rows.append(record)

    logger.info("Loaded %d hazard rows from %s", len(rows), path)
    return rows


def load_physical_literature_data(csv_path: str | Path | None = None) -> List[Dict[str, Any]]:
    """Load verified literature values for physical risk parameters.

    Returns a list of dicts, one per row, with the ``value`` field cast to
    float and all other fields preserved as strings.

    Args:
        csv_path: Override path; defaults to
            ``data/physical_risk/literature_data.csv``.
    """
    path = Path(csv_path) if csv_path else _PHYS_DIR / "literature_data.csv"
    if not path.exists():
        raise FileNotFoundError(f"literature_data.csv not found at {path}")

    rows: List[Dict[str, Any]] = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            record: Dict[str, Any] = {k.strip(): v.strip() for k, v in row.items()}
            try:
                record["value"] = float(record["value"])
            except (ValueError, KeyError):
                pass
            if record.get("year", "all") not in ("all",):
                try:
                    record["year"] = int(str(record["year"]).split("-")[0])
                except ValueError:
                    pass
            rows.append(record)

    logger.info("Loaded %d literature rows from %s", len(rows), path)
    return rows


def load_physical_model_assumptions(csv_path: str | Path | None = None) -> Dict[str, float]:
    """Load physical risk modelling assumptions (probabilities, durations, etc.).

    Returns ``{parameter: value}`` with all values cast to float.

    Args:
        csv_path: Override path; defaults to
            ``data/physical_risk/model_assumptions.csv``.
    """
    path = Path(csv_path) if csv_path else _PHYS_DIR / "model_assumptions.csv"
    if not path.exists():
        raise FileNotFoundError(f"physical risk model_assumptions.csv not found at {path}")

    assumptions: Dict[str, float] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            assumptions[row["parameter"].strip()] = float(row["value"])

    logger.info("Loaded %d physical risk assumptions from %s", len(assumptions), path)
    return assumptions


def load_physical_risk_output(
    csv_path: str | Path | None = None,
    scenario: str = "RCP8.5",
) -> List[Dict[str, Any]]:
    """Load pre-computed physical risk anchor rows from CSV.

    Returns a list of dicts (one per anchor year) for the requested scenario,
    filtered and stripped of comment lines.  All numeric columns are cast to
    float; the ``year`` and ``scenario`` fields are kept as-is.

    Args:
        csv_path: Override path; defaults to
            ``data/physical_risk/physical_risk_output.csv``.
        scenario: Scenario label to filter on (default ``"RCP8.5"``).
    """
    path = Path(csv_path) if csv_path else _PHYS_DIR / "physical_risk_output.csv"
    if not path.exists():
        raise FileNotFoundError(f"physical_risk_output.csv not found at {path}")

    import io as _io
    str_cols = {"scenario"}
    rows: List[Dict[str, Any]] = []
    with open(path, newline="") as f:
        data_lines = [line for line in f if not line.startswith("#")]

    for row in csv.DictReader(_io.StringIO("".join(data_lines))):
        record: Dict[str, Any] = {}
        for k, v in row.items():
            k = k.strip()
            v = v.strip()
            if k in str_cols or k == "year":
                record[k] = int(v) if k == "year" else v
            else:
                try:
                    record[k] = float(v)
                except ValueError:
                    record[k] = v
        if str(record.get("scenario", "")) == scenario:
            rows.append(record)

    logger.info(
        "Loaded %d physical risk anchor rows (scenario=%s) from %s",
        len(rows), scenario, path,
    )
    return rows


def load_physical_scenarios(csv_path: str | Path | None = None) -> List[Dict[str, Any]]:
    """Load physical risk scenario definitions from CSV.

    Returns a list of dicts with keys ``scenario``, ``ssp``, ``description``.

    Args:
        csv_path: Override path; defaults to
            ``data/raw/physical_scenarios.csv``.
    """
    path = Path(csv_path) if csv_path else _PHYS_DIR / "physical_scenarios.csv"
    if not path.exists():
        raise FileNotFoundError(f"physical_scenarios.csv not found at {path}")

    rows: List[Dict[str, Any]] = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            rows.append({k.strip(): v.strip() for k, v in row.items()})

    logger.info("Loaded %d physical scenarios from %s", len(rows), path)
    return rows

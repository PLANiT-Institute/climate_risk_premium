"""Data loaders for all CSV inputs.

All I/O lives here — callers get plain Python dicts, never file handles or
raw CSV rows.

Directory layout
----------------
data/
  plant_parameters.csv       — plant design and financial parameters
  model_assumptions.csv      — cross-cutting model assumptions
  rating_thresholds.csv      — KIS credit rating metric thresholds
  rating_weights.csv         — KIS rating component weights
  rating_spreads.csv         — rating → credit spread mapping
  credit_rating_grid.csv     — compact rating grid (reference)

  transition/
    scenarios.csv            — transition policy scenarios (dispatch, carbon)

  physical/
    scenarios.csv            — physical risk scenarios (ssp, wildfire_scale)
    climada_data.csv         — CLIMADA hazard event counts (NASA FIRMS)
    literature_data.csv      — climate amplification factors (WWA 2025)
    model_assumptions.csv    — outage probabilities and durations

  scenarios/
    climate_scenarios.csv    — combined climate scenarios
                               (transition_scenario × physical_scenario × weight)
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_ROOT     = Path(__file__).parent.parent.parent
_DATA_DIR = _ROOT / "data"
_TRANS_DIR = _DATA_DIR / "transition"
_PHYS_DIR  = _DATA_DIR / "physical"
_SCEN_DIR  = _DATA_DIR / "scenarios"


# ---------------------------------------------------------------------------
# Plant & model parameters
# ---------------------------------------------------------------------------

def load_plant_params(csv_path: str | Path | None = None) -> Dict[str, Any]:
    """Load plant design and financial parameters from ``data/plant_parameters.csv``.

    Returns a flat dict keyed by ``param_name``.  Values are cast to float
    where possible; strings are kept as-is (e.g. ``plant_name``).
    """
    path = Path(csv_path) if csv_path else _DATA_DIR / "plant_parameters.csv"
    if not path.exists():
        raise FileNotFoundError(f"plant_parameters.csv not found at {path}")

    params: Dict[str, Any] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            name = row["param_name"].strip()
            raw  = row["value"].strip()
            try:
                params[name] = float(raw)
            except ValueError:
                params[name] = raw
    logger.info("Loaded %d plant parameters from %s", len(params), path)
    return params


def load_model_assumptions(csv_path: str | Path | None = None) -> Dict[str, Any]:
    """Load cross-cutting model assumptions from ``data/model_assumptions.csv``.

    Values are cast to float where possible; strings are kept as-is
    (e.g. ``counterfactual_rating = "A"``).
    """
    path = Path(csv_path) if csv_path else _DATA_DIR / "model_assumptions.csv"
    if not path.exists():
        raise FileNotFoundError(f"model_assumptions.csv not found at {path}")

    assumptions: Dict[str, Any] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            name = row["param_name"].strip()
            raw  = row["value"].strip()
            try:
                assumptions[name] = float(raw)
            except ValueError:
                assumptions[name] = raw
    logger.info("Loaded %d model assumptions from %s", len(assumptions), path)
    return assumptions


# ---------------------------------------------------------------------------
# Transition risk
# ---------------------------------------------------------------------------

def load_transition_scenarios(csv_path: str | Path | None = None) -> List[Dict[str, Any]]:
    """Load all transition policy scenarios from ``data/transition/scenarios.csv``.

    Returns a list of dicts, one per row.  Numeric columns
    (dispatch_penalty, retirement_years, carbon_price_*) are cast to float.
    """
    path = Path(csv_path) if csv_path else _TRANS_DIR / "scenarios.csv"
    if not path.exists():
        raise FileNotFoundError(f"transition scenarios not found at {path}")

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
    logger.info("Loaded %d transition scenarios from %s", len(scenarios), path)
    return scenarios


# Keep old name as alias so existing callers don't break immediately
def load_policy_scenarios(csv_path: str | Path | None = None) -> List[Dict[str, Any]]:
    """Deprecated alias for :func:`load_transition_scenarios`."""
    return load_transition_scenarios(csv_path)


def load_transition_scenario_by_name(
    name: str,
    csv_path: str | Path | None = None,
) -> Dict[str, Any]:
    """Return a single transition scenario row by its ``scenario`` column value.

    Raises ``KeyError`` if the name is not found.
    """
    rows = load_transition_scenarios(csv_path)
    for row in rows:
        if row["scenario"] == name:
            return row
    available = [r["scenario"] for r in rows]
    raise KeyError(f"Transition scenario '{name}' not found. Available: {available}")


# ---------------------------------------------------------------------------
# Credit rating
# ---------------------------------------------------------------------------

def load_rating_thresholds(csv_path: str | Path | None = None) -> Dict[str, Dict[str, float]]:
    """Load KIS credit rating metric thresholds from ``data/rating_thresholds.csv``.

    Returns ``{metric: {rating_name: threshold}}``.  For ``direction = "higher"``
    the threshold is the *minimum* to achieve that rating; for ``"lower"`` it
    is the *maximum*.
    """
    path = Path(csv_path) if csv_path else _DATA_DIR / "rating_thresholds.csv"
    if not path.exists():
        raise FileNotFoundError(f"rating_thresholds.csv not found at {path}")

    thresholds: Dict[str, Dict[str, float]] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            metric    = row["metric"].strip()
            rating    = row["rating"].strip()
            threshold = float(row["threshold"])
            thresholds.setdefault(metric, {})[rating] = threshold
    logger.info("Loaded rating thresholds for %d metrics from %s", len(thresholds), path)
    return thresholds


def load_rating_weights(csv_path: str | Path | None = None) -> Dict[str, float]:
    """Load KIS rating component weights from ``data/rating_weights.csv``.

    Returns ``{component_name: weight}``.
    """
    path = Path(csv_path) if csv_path else _DATA_DIR / "rating_weights.csv"
    if not path.exists():
        raise FileNotFoundError(f"rating_weights.csv not found at {path}")

    weights: Dict[str, float] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            weights[row["component"].strip()] = float(row["weight"])
    logger.info("Loaded %d rating component weights from %s", len(weights), path)
    return weights


def load_rating_spreads(csv_path: str | Path | None = None) -> Dict[str, float]:
    """Load rating → credit spread mapping from ``data/rating_spreads.csv``.

    Returns ``{rating_name: spread_bps}``.
    """
    path = Path(csv_path) if csv_path else _DATA_DIR / "rating_spreads.csv"
    if not path.exists():
        raise FileNotFoundError(f"rating_spreads.csv not found at {path}")

    spreads: Dict[str, float] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            spreads[row["rating"].strip()] = float(row["spread_bps"])
    logger.info("Loaded %d rating spreads from %s", len(spreads), path)
    return spreads


# ---------------------------------------------------------------------------
# Physical risk
# ---------------------------------------------------------------------------

def load_physical_scenarios(csv_path: str | Path | None = None) -> List[Dict[str, Any]]:
    """Load physical risk scenario definitions from ``data/physical/scenarios.csv``.

    Returns a list of dicts with keys:
      - ``scenario``      — unique identifier
      - ``ssp``           — SSP pathway label
      - ``wildfire_scale``— float in [0, 1]; fraction of RCP8.5 wildfire intensity
      - ``description``   — human-readable label
    """
    path = Path(csv_path) if csv_path else _PHYS_DIR / "scenarios.csv"
    if not path.exists():
        raise FileNotFoundError(f"physical scenarios not found at {path}")

    rows: List[Dict[str, Any]] = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            record = {k.strip(): v.strip() for k, v in row.items()}
            if "wildfire_scale" in record:
                record["wildfire_scale"] = float(record["wildfire_scale"])
            rows.append(record)
    logger.info("Loaded %d physical scenarios from %s", len(rows), path)
    return rows


def load_physical_hazard_data(csv_path: str | Path | None = None) -> List[Dict[str, Any]]:
    """Load CLIMADA hazard event counts from ``data/physical/climada_data.csv``.

    Numeric fields (events_at_location, years_covered, max_intensity) are
    cast to float; others remain strings.
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
    """Load climate amplification factors from ``data/physical/literature_data.csv``.

    The ``value`` field is cast to float; ``year`` is cast to int (taking the
    first component of hyphenated ranges like ``"2024-2030"``).
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
    """Load physical risk modelling assumptions from ``data/physical/model_assumptions.csv``.

    Returns ``{parameter: float}`` — outage probabilities, durations, etc.
    """
    path = Path(csv_path) if csv_path else _PHYS_DIR / "model_assumptions.csv"
    if not path.exists():
        raise FileNotFoundError(f"physical model_assumptions.csv not found at {path}")

    assumptions: Dict[str, float] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            assumptions[row["parameter"].strip()] = float(row["value"])
    logger.info("Loaded %d physical risk assumptions from %s", len(assumptions), path)
    return assumptions


# ---------------------------------------------------------------------------
# Combined climate scenarios
# ---------------------------------------------------------------------------

def load_climate_scenarios(csv_path: str | Path | None = None) -> List[Dict[str, Any]]:
    """Load combined climate scenario definitions from ``data/scenarios/climate_scenarios.csv``.

    Each row defines one (climate_scenario, transition_scenario, physical_scenario)
    combination.  Multiple rows with the same ``climate_scenario`` value indicate
    a probability-weighted blend of physical scenarios: weights are normalised to
    sum to 1.0 before use.

    Returns a list of dicts with keys:
      - ``climate_scenario``   — unique combined scenario name
      - ``transition_scenario``— name matching a row in ``data/transition/scenarios.csv``
      - ``physical_scenario``  — name matching a row in ``data/physical/scenarios.csv``
      - ``physical_weight``    — float weight for this physical scenario in the blend
      - ``description``        — human-readable label
    """
    path = Path(csv_path) if csv_path else _SCEN_DIR / "climate_scenarios.csv"
    if not path.exists():
        raise FileNotFoundError(f"climate_scenarios.csv not found at {path}")

    rows: List[Dict[str, Any]] = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            record = {k.strip(): v.strip() for k, v in row.items()}
            record["physical_weight"] = float(record.get("physical_weight", 1.0))
            rows.append(record)
    logger.info("Loaded %d climate scenario rows from %s", len(rows), path)
    return rows

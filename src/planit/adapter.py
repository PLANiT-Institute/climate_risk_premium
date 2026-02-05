"""PLANiT → PhysicalAdjustments adapter with conversion, interpolation, and fallback."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np

from .config import PLANiTIntegrationConfig
from .runner import PLANiTHazardResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scenario mapping: CRP scenario string → PLANiT SSP id
# ---------------------------------------------------------------------------
SCENARIO_MAP: Dict[str, str] = {
    "rcp4.5": "ssp245",
    "rcp45": "ssp245",
    "ssp2-4.5": "ssp245",
    "ssp245": "ssp245",
    "rcp8.5": "ssp585",
    "rcp85": "ssp585",
    "ssp5-8.5": "ssp585",
    "ssp585": "ssp585",
    "ssp1-2.6": "ssp126",
    "ssp126": "ssp126",
}

# Reverse: PLANiT SSP → canonical CRP label
SSP_TO_CRP: Dict[str, str] = {
    "ssp126": "SSP1-2.6",
    "ssp245": "RCP4.5",
    "ssp585": "RCP8.5",
}


def map_scenario(crp_scenario: str) -> str:
    """Map a CRP scenario string to PLANiT SSP identifier.

    >>> map_scenario("RCP8.5")
    'ssp585'
    """
    key = crp_scenario.lower().replace(" ", "")
    mapped = SCENARIO_MAP.get(key)
    if mapped is None:
        raise ValueError(
            f"Unknown scenario '{crp_scenario}'. "
            f"Supported: {list(SCENARIO_MAP.keys())}"
        )
    return mapped


class PLANiTAdapter:
    """Converts PLANiT hazard results to PhysicalAdjustments fields.

    WILDFIRE-ONLY MODE (as of 2026-02-05)
    -------------------------------------
    Only wildfire is converted using CLIMADA's explicit damage function.
    Other hazards (drought, flood, heatwave, water_risk) removed due to
    PhysRisk API being a black-box without explicit vulnerability formulas.

    Conversion formula
    ------------------
    * Wildfire ``aai_krw`` → ``outage_rate = aai / total_asset_value``

    Other fields return default values:
    * ``capacity_derate = 0.0`` (drought removed)
    * ``efficiency_loss = 0.0`` (heatwave removed)
    * ``water_constrained_capacity = 1.0`` (water_risk removed)

    Year interpolation
    ------------------
    Linear between PLANiT anchor years (2030, 2040, 2050, 2060).
    Years before the first anchor blend linearly from a *baseline* value
    (CSV or zero) to the first anchor value.
    """

    def __init__(self, config: Optional[PLANiTIntegrationConfig] = None):
        self._config = config or PLANiTIntegrationConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def convert(
        self,
        results: List[PLANiTHazardResult],
        target_year: int,
        crp_scenario: str,
        csv_baseline: Optional[Dict[str, float]] = None,
    ) -> Dict[str, float]:
        """Convert PLANiT results → dict of PhysicalAdjustments fields.

        Args:
            results: All PLANiTHazardResult entries (multiple hazards/years).
            target_year: The year for which adjustments are needed.
            crp_scenario: CRP-side scenario label (e.g. "RCP8.5").
            csv_baseline: Optional dict of CSV baseline values keyed by
                field name (outage_rate, capacity_derate, efficiency_loss,
                water_constrained_capacity) used for pre-anchor blending
                and per-hazard fallback.

        Returns:
            Dict with keys: outage_rate, capacity_derate, efficiency_loss,
            water_constrained_capacity, notes.
        """
        ssp = map_scenario(crp_scenario)
        baseline = csv_baseline or {}

        # Group results by hazard → list of (year, value)
        by_hazard: Dict[str, List[Tuple[int, float]]] = {}
        for r in results:
            if r.scenario != ssp:
                continue
            by_hazard.setdefault(r.hazard_type, []).append((r.year, r.value))

        outage_rate = 0.0
        capacity_derate = 0.0
        efficiency_loss = 0.0
        water_constrained_capacity = 1.0
        notes_parts: List[str] = []

        # --- Wildfire → outage_rate (ONLY HAZARD WITH EXPLICIT FORMULA) ---
        # CLIMADA ImpfWildfire uses sigmoid: damage_ratio = 1 / (1 + (i_half / FWI)²)
        wf_val = self._interpolate_hazard(
            by_hazard.get("wildfire", []), target_year, baseline.get("outage_rate", 0.0)
        )
        if wf_val is not None:
            outage_rate = wf_val / self._config.total_asset_value_krw
            notes_parts.append(f"wildfire_aai={wf_val:.0f}")
        elif "outage_rate" in baseline:
            outage_rate = baseline["outage_rate"]
            notes_parts.append("wildfire=csv_fallback")

        # --- Removed hazards (PhysRisk black-box) ---
        # Flood, Drought, Water Risk, Heatwave all removed as of 2026-02-05
        # Returning default values: capacity_derate=0, efficiency_loss=0, water=1.0
        notes_parts.append("other_hazards=removed(no_explicit_formula)")

        return {
            "outage_rate": outage_rate,
            "capacity_derate": capacity_derate,  # 0.0 (drought removed)
            "efficiency_loss": efficiency_loss,  # 0.0 (heatwave removed)
            "water_constrained_capacity": water_constrained_capacity,  # 1.0 (water_risk removed)
            "notes": f"CLIMADA wildfire only ({ssp} y{target_year}): " + ", ".join(notes_parts),
        }

    def convert_yearly(
        self,
        results: List[PLANiTHazardResult],
        start_year: int,
        end_year: int,
        crp_scenario: str,
        csv_baseline: Optional[Dict[str, float]] = None,
    ) -> Dict[str, np.ndarray]:
        """Convert PLANiT results to year-by-year arrays.

        Returns dict with keys: years, outage_rates, capacity_derates,
        efficiency_losses, water_constraints — matching YearlyPhysicalAdjustments.
        """
        years = np.arange(start_year, end_year + 1)
        outage_rates = np.zeros(len(years))
        capacity_derates = np.zeros(len(years))
        efficiency_losses = np.zeros(len(years))
        water_constraints = np.ones(len(years))

        for i, year in enumerate(years):
            adj = self.convert(results, int(year), crp_scenario, csv_baseline)
            outage_rates[i] = adj["outage_rate"]
            capacity_derates[i] = adj["capacity_derate"]
            efficiency_losses[i] = adj["efficiency_loss"]
            water_constraints[i] = adj["water_constrained_capacity"]

        return {
            "years": years,
            "outage_rates": outage_rates,
            "capacity_derates": capacity_derates,
            "efficiency_losses": efficiency_losses,
            "water_constraints": water_constraints,
        }

    # ------------------------------------------------------------------
    # Interpolation
    # ------------------------------------------------------------------

    def _interpolate_hazard(
        self,
        year_values: List[Tuple[int, float]],
        target_year: int,
        baseline_value: float,
    ) -> Optional[float]:
        """Linear interpolation between PLANiT anchor points.

        For years before the first anchor, blends from *baseline_value*
        (at the implicit baseline year, taken as 2024) to the first anchor.

        Returns None if no data points are available (triggers fallback).
        """
        if not year_values:
            return None

        # Sort by year
        sorted_pts = sorted(year_values, key=lambda x: x[0])
        yrs = [p[0] for p in sorted_pts]
        vals = [p[1] for p in sorted_pts]

        # Before first anchor → blend from baseline
        if target_year <= 2024:
            return baseline_value
        if target_year < yrs[0]:
            # Linear blend: baseline@2024 → first_anchor@yrs[0]
            weight = (target_year - 2024) / (yrs[0] - 2024)
            return baseline_value + weight * (vals[0] - baseline_value)

        # After last anchor → hold constant
        if target_year >= yrs[-1]:
            return vals[-1]

        # Between anchors → linear interpolation
        for j in range(len(yrs) - 1):
            if yrs[j] <= target_year <= yrs[j + 1]:
                w = (target_year - yrs[j]) / (yrs[j + 1] - yrs[j])
                return vals[j] + w * (vals[j + 1] - vals[j])

        return vals[-1]

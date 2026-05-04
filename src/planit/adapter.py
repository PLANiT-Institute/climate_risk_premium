"""PLANiT → PhysicalAdjustments adapter with conversion, interpolation, and fallback."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np

from .config import PLANiTIntegrationConfig
from .outage_assumptions import (
    OUTAGE_DURATION_HOURS,
    OUTAGE_DURATION_HOURS_SENSITIVITY,
    OUTAGE_RATE_PER_EVENT,
    OUTAGE_RATE_PER_EVENT_SENSITIVITY,
    event_freq_to_outage_rate,
)
from .runner import PLANiTHazardResult
from ..data.loaders import get_climate_factor

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

    Conversion formulas
    -------------------
    * Wildfire (CLIMADA event probability):
        ``outage_rate = annual_event_frequency × outage_probability × (outage_duration_hours / hours_per_year)``
    * Drought (PhysRisk impact_mean):
        ``capacity_derate = impact_mean × drought_severity_scale``
    * Water Risk (PhysRisk impact_mean):
        ``water_constrained_capacity = max(0, 1 − impact_mean)``

    Year interpolation
    ------------------
    Linear between PLANiT anchor years (2030, 2040, 2050, 2060).
    Years before the first anchor blend linearly from a *baseline* value
    (or zero) to the first anchor value.
    """

    def __init__(self, config: Optional[PLANiTIntegrationConfig] = None):
        self._config = config or PLANiTIntegrationConfig()
        self._efficiency_channel_warning_emitted = False

    @staticmethod
    def _normalize_scenario(crp_scenario: str) -> str:
        """Normalize scenario string to lower case, no spaces."""
        return crp_scenario.lower().replace(" ", "")

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
            csv_baseline: Optional dict of baseline values keyed by
                field name used for pre-anchor blending and fallback.

        Returns:
            Dict with keys: outage_rate, capacity_derate, efficiency_loss,
            water_constrained_capacity, notes.
        """
        ssp = map_scenario(crp_scenario)
        baseline = csv_baseline or {}

        # Group results by hazard/scenario → list of (year, value)
        by_hazard_scenario: Dict[str, Dict[str, List[Tuple[int, float]]]] = {}
        # Wildfire-specific frequency metadata for probability-based outage.
        wf_frequency_rows: Dict[str, List[Tuple[int, float]]] = {}
        wf_frequency_source: Dict[str, str] = {}
        # PhysRisk distribution-derived expected impacts and disruption probabilities.
        dist_expected_rows: Dict[str, Dict[str, List[Tuple[int, float]]]] = {
            "drought": {},
            "water_risk": {},
        }
        dist_prob_rows: Dict[str, Dict[str, List[Tuple[int, float]]]] = {
            "drought": {},
            "water_risk": {},
        }
        target_asset = self._config.target_asset
        for r in results:
            if target_asset and r.asset:
                if target_asset not in r.asset and r.asset not in target_asset:
                    continue
            hmap = by_hazard_scenario.setdefault(r.hazard_type, {})
            hmap.setdefault(r.scenario, []).append((r.year, r.value))
            if r.hazard_type == "wildfire":
                wf_freq, wf_freq_source = self._extract_wildfire_frequency(r)
                if wf_freq is not None:
                    wf_frequency_rows.setdefault(r.scenario, []).append((r.year, wf_freq))
                    wf_frequency_source.setdefault(r.scenario, wf_freq_source)
            if r.hazard_type in dist_expected_rows:
                d_expected, d_prob_nonzero = self._distribution_expected_and_prob_nonzero(r)
                if d_expected is not None:
                    dist_expected_rows[r.hazard_type].setdefault(r.scenario, []).append((r.year, d_expected))
                if d_prob_nonzero is not None:
                    dist_prob_rows[r.hazard_type].setdefault(r.scenario, []).append((r.year, d_prob_nonzero))

        outage_rate = 0.0
        capacity_derate = 0.0
        efficiency_loss = 0.0
        water_constrained_capacity = 1.0
        notes_parts: List[str] = []
        self._warn_if_efficiency_channel_disabled()

        # --- Wildfire (CLIMADA) → outage_rate ---
        wf_rows = by_hazard_scenario.get("wildfire", {})
        wf_val = None
        wf_freq = None
        wf_source_scenario = ssp
        wf_freq_source = None

        # If requested SSP wildfire is missing, use deterministic fallback order.
        if wf_rows:
            for alt in self._wildfire_fallback_order(ssp):
                alt_wf_val = self._interpolate_hazard(
                    wf_rows.get(alt, []), target_year, baseline.get("outage_rate", 0.0)
                )
                alt_wf_freq = self._interpolate_hazard(
                    wf_frequency_rows.get(alt, []), target_year, 0.0
                )
                if alt_wf_freq is None:
                    continue
                wf_val = alt_wf_val
                wf_freq = alt_wf_freq
                wf_source_scenario = alt
                wf_freq_source = wf_frequency_source.get(alt)
                if alt == ssp:
                    break
                notes_parts.append(f"wildfire_scenario_fallback={alt}")
                logger.warning(
                    "Wildfire scenario %s missing; using fallback scenario %s for year %s",
                    ssp, alt, target_year,
                )
                break

        logger.debug(f"[WILDFIRE] Computing outage rate: freq={wf_freq}, scenario={crp_scenario}, year={target_year}")
        wf_outage_rate, wf_method = self._compute_wildfire_outage_rate(
            wf_val, wf_freq, target_year=target_year, crp_scenario=crp_scenario
        )
        logger.debug(f"[WILDFIRE] Computed outage_rate={wf_outage_rate}")
        if wf_outage_rate is not None:
            outage_rate = wf_outage_rate
            if wf_method == "event_probability":
                notes_parts.append(f"wildfire_event_freq={wf_freq:.6f}/yr")
                notes_parts.append(
                    f"wildfire_outage_prob={self._config.wildfire_outage_probability:.3f}"
                )
                notes_parts.append(
                    f"wildfire_outage_duration_h={self._config.wildfire_outage_duration_hours:.1f}"
                )
                if wf_freq_source:
                    notes_parts.append(f"wildfire_freq_source={wf_freq_source}")
            if wf_source_scenario != ssp:
                notes_parts.append(f"wildfire_source_scenario={wf_source_scenario}")
            # Add climate factor note
            try:
                climate_factor = get_climate_factor("wildfire", target_year, crp_scenario)
                if abs(climate_factor - 1.0) > 0.001:
                    notes_parts.append(f"wildfire_climate_factor={climate_factor:.3f}")
            except Exception:
                pass
        elif "outage_rate" in baseline:
            # Apply climate factor to baseline fallback value
            outage_rate = baseline["outage_rate"]
            logger.debug(f"[WILDFIRE] CSV fallback: baseline={outage_rate}, scenario={crp_scenario}, year={target_year}")
            try:
                climate_factor = get_climate_factor("wildfire", target_year, crp_scenario)
                outage_rate_before = outage_rate
                outage_rate = outage_rate * climate_factor
                logger.debug(f"[WILDFIRE] Applied climate_factor={climate_factor}: {outage_rate_before} → {outage_rate}")
                notes_parts.append(f"wildfire=csv_fallback_with_climate_factor={climate_factor:.3f}")
            except Exception as e:
                logger.debug(f"[WILDFIRE] Climate factor lookup failed: {e}")
                notes_parts.append("wildfire=csv_fallback")
        else:
            notes_parts.append("wildfire_frequency_missing")

        # --- Drought (PhysRisk) → capacity_derate ---
        dr_rows = by_hazard_scenario.get("drought", {})
        dr_mean = self._interpolate_hazard(
            dr_rows.get(ssp, []), target_year, baseline.get("capacity_derate", 0.0)
        )
        dr_dist = self._interpolate_hazard(
            dist_expected_rows["drought"].get(ssp, []), target_year, baseline.get("capacity_derate", 0.0)
        )
        dr_prob_nonzero = self._interpolate_hazard(
            dist_prob_rows["drought"].get(ssp, []), target_year, 0.0
        )
        dr_val = dr_mean
        if self._config.drought_use_distribution and dr_dist is not None:
            dr_val = dr_dist
            notes_parts.append("drought_metric=distribution_expected")
            if dr_prob_nonzero is not None:
                notes_parts.append(f"drought_prob_nonzero={dr_prob_nonzero:.4f}")
        elif dr_mean is not None:
            notes_parts.append("drought_metric=impact_mean")
        if dr_val is not None:
            capacity_derate = dr_val * self._config.drought_severity_scale
            notes_parts.append(f"drought_impact={dr_val:.6f}")

        # --- Water Risk (PhysRisk) → water_constrained_capacity ---
        wr_rows = by_hazard_scenario.get("water_risk", {})
        wr_mean = self._interpolate_hazard(
            wr_rows.get(ssp, []), target_year, baseline.get("water_constrained_capacity_loss", 0.0)
        )
        wr_dist = self._interpolate_hazard(
            dist_expected_rows["water_risk"].get(ssp, []),
            target_year,
            baseline.get("water_constrained_capacity_loss", 0.0),
        )
        wr_prob_nonzero = self._interpolate_hazard(
            dist_prob_rows["water_risk"].get(ssp, []), target_year, 0.0
        )
        wr_val = wr_mean
        if self._config.water_risk_use_distribution and wr_dist is not None:
            wr_val = wr_dist
            notes_parts.append("water_risk_metric=distribution_expected")
            if wr_prob_nonzero is not None:
                notes_parts.append(f"water_risk_prob_nonzero={wr_prob_nonzero:.4f}")
        elif wr_mean is not None:
            notes_parts.append("water_risk_metric=impact_mean")
        if wr_val is not None:
            water_constrained_capacity = max(0.0, 1.0 - wr_val)
            notes_parts.append(f"water_risk_impact={wr_val:.6f}")

        return {
            "outage_rate": outage_rate,
            "capacity_derate": capacity_derate,
            "efficiency_loss": efficiency_loss,
            "water_constrained_capacity": water_constrained_capacity,
            "notes": f"PLANiT ({ssp} y{target_year}): " + ", ".join(notes_parts),
        }

    def _extract_wildfire_frequency(
        self, row: PLANiTHazardResult
    ) -> Tuple[Optional[float], Optional[str]]:
        """Extract annual wildfire event frequency per year from row metadata."""
        if row.event_frequency_per_year is not None:
            return max(0.0, float(row.event_frequency_per_year)), "annual_frequency_per_year"

        if row.event_count is None:
            return None, None

        reference_years = row.reference_years
        if reference_years is not None and reference_years > 0:
            freq = float(row.event_count) / float(reference_years)
            return max(0.0, freq), "event_count/reference_years"

        fallback_years = float(self._config.wildfire_frequency_reference_years)
        if fallback_years > 0:
            freq = float(row.event_count) / fallback_years
            return max(0.0, freq), f"event_count/{fallback_years:g}y"

        return None, None

    def _compute_wildfire_outage_rate(
        self,
        _wildfire_legacy_value: Optional[float],
        event_frequency_per_year: Optional[float],
        target_year: Optional[int] = None,
        crp_scenario: Optional[str] = None,
    ) -> Tuple[Optional[float], Optional[str]]:
        """Compute wildfire outage_rate using event-frequency probability method.

        Formula:
            outage_rate = freq × P(outage|event) × (duration_h / 8760) × climate_factor

        - freq: from CLIMADA (identical across SSPs since fire_prop=0.21 for all)
        - P(outage|event): from outage_assumptions.py (Dale et al. 2018, sensitivity [0.05, 0.20])
        - climate_factor: from climate_factors.csv (IPCC AR6) — sole source of SSP differentiation
        """
        method = str(self._config.wildfire_outage_method).strip().lower()

        if method == "event_probability" and event_frequency_per_year is not None:
            outage_prob = min(1.0, max(0.0, float(self._config.wildfire_outage_probability)))
            outage_hours = max(0.0, float(self._config.wildfire_outage_duration_hours))
            hours_per_year = max(1.0, float(self._config.hours_per_year))
            outage_rate = event_freq_to_outage_rate(
                event_frequency_per_year,
                outage_probability=outage_prob,
                outage_duration_hours=outage_hours,
                hours_per_year=hours_per_year,
            )

            # Apply climate factor — sole source of SSP differentiation.
            # CLIMADA fire_prop_probability is 0.21 for all SSPs (no SSP-specific scaling).
            if target_year is not None and crp_scenario is not None:
                try:
                    climate_factor = get_climate_factor("wildfire", target_year, crp_scenario)
                    outage_rate = outage_rate * climate_factor
                except Exception as e:
                    logger.warning(
                        "Failed to apply climate factor for wildfire: %s. Using unadjusted rate.", e
                    )

            return min(1.0, max(0.0, outage_rate)), "event_probability"

        return None, None

    @staticmethod
    def _distribution_expected_and_prob_nonzero(
        row: PLANiTHazardResult,
    ) -> Tuple[Optional[float], Optional[float]]:
        """Return expected impact and non-zero disruption probability from bins."""
        edges = row.impact_bin_edges
        probs = row.impact_probabilities
        if not edges or not probs:
            return None, None
        n = min(len(probs), len(edges) - 1)
        if n <= 0:
            return None, None

        expected = 0.0
        prob_nonzero = 0.0
        for i in range(n):
            try:
                p = max(0.0, float(probs[i]))
                lo = float(edges[i])
                hi = float(edges[i + 1])
            except (ValueError, TypeError, IndexError):
                return None, None
            mid = 0.5 * (lo + hi)
            expected += mid * p
            if hi > 0.0:
                prob_nonzero += p

        return max(0.0, expected), min(1.0, max(0.0, prob_nonzero))

    @staticmethod
    def _wildfire_fallback_order(ssp: str) -> List[str]:
        """Fallback order for missing wildfire SSP rows.

        Rationale:
        - Keep requested scenario first.
        - Prefer adjacent/nearby SSP paths before historical.
        - Avoid zeroing wildfire when CSV snapshots are sparse.
        """
        if ssp == "ssp585":
            return ["ssp585", "ssp245", "ssp126", "historical"]
        if ssp == "ssp245":
            return ["ssp245", "ssp126", "historical"]
        if ssp == "ssp126":
            return ["ssp126", "historical"]
        return [ssp, "ssp585", "ssp245", "ssp126", "historical"]

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

        # Sort and aggregate duplicate years (e.g., multiple grid assets).
        buckets: Dict[int, List[float]] = {}
        for year, value in year_values:
            buckets.setdefault(int(year), []).append(float(value))
        yrs = sorted(buckets.keys())
        vals = [float(np.mean(buckets[y])) for y in yrs]

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

    def _warn_if_efficiency_channel_disabled(self) -> None:
        """Warn once when the heat-derate channel is intentionally disabled."""
        enabled = bool(getattr(self._config.efficiency_channel, "enabled", False))
        if enabled or self._efficiency_channel_warning_emitted:
            return
        logger.warning(
            "Heat-derate channel is disabled. Total physical risk is "
            "underestimated; reported risk premium is conservative."
        )
        self._efficiency_channel_warning_emitted = True

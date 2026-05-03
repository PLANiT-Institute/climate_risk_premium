"""Physical risk module — wildfire, tropical cyclone, drought, and heat channels.

Computes year-by-year physical risk adjustments for a coal power plant by
reading CSV inputs from ``data/physical/`` and linearly interpolating to
every operating year.

Active channels
---------------
- **Wildfire outage** (plant + transmission) — wildfire damage to equipment/lines.
- **Tropical cyclone outage** (plant + transmission) — structural damage from
  damaging TCs (wind > 30 m/s); combined independently with wildfire.
- **Drought capacity derate** — reduced CF from cooling constraints under drought.
- **Chronic heat + SST efficiency loss** — raised heat-rate from warmer ambient
  air and seawater (continuous, every year).
- **Heatwave acute efficiency loss** — additional heat-rate increase during
  extreme heat events; folded into ``efficiency_losses``.

Data sources (all in ``data/physical/``)
-----------------------------------------
- ``climada_data.csv``       — CLIMADA event counts (NASA FIRMS, IBTrACS, ISIMIP)
- ``literature_data.csv``    — Verified climate factors and parameters
- ``model_assumptions.csv``  — Outage probabilities, durations, base derate/loss rates
- ``scenarios.csv``          — Physical scenario definitions incl. ``wildfire_scale``

Physical scenario → SSP mapping and scenario scale
---------------------------------------------------
Defined in ``data/physical/scenarios.csv`` (no hardcoded values in code):
  baseline          → ssp126, wildfire_scale = 0.30
  moderate_physical → ssp245, wildfire_scale = 0.60
  high_physical     → ssp585, wildfire_scale = 1.00
  severe_drought    → ssp585, wildfire_scale = 1.00

The ``wildfire_scale`` is reused as a universal SSP intensity scalar for all
hazard channels — drought factors, temperature change, and heatwave days — since
all are driven by the same greenhouse-gas trajectory.

Algorithm (wildfire, outage_rate channel)
-----------------------------------------
1.  annual_frequency_wf = events_at_location / years_covered
        (hazard == "wildfire" row in climada_data.csv; 6/20 = 0.30 events/yr)
2.  base_outage_wf(asset) = annual_frequency_wf
                           × outage_prob(asset)
                           × (outage_hours(asset) / hours_per_year)
3.  wildfire_factor(year) = np.interp(year, anchor_years, factors)
        (category WILDFIRE, from literature_data.csv)
4.  wf_scaled(year) = 1 + (wildfire_factor(year) − 1) × wildfire_scale
5.  projected_wf_outage(asset, year) = base_outage_wf(asset) × wf_scaled(year)

Algorithm (tropical cyclone, tc_outage_rate channel)
------------------------------------------------------
1.  annual_frequency_tc = events_at_location / years_covered
        (hazard == "tropical_cyclone_damaging" row; 5/40 = 0.125 events/yr;
         damaging = wind > 30 m/s per IBTrACS, NOAA/WMO 1980–2020)
2.  base_outage_tc(asset) = annual_frequency_tc
                           × outage_prob_tc
                           × (outage_duration_tc / hours_per_year)
        (outage_prob_tc and outage_duration_tc from model_assumptions.csv)
3.  tc_factor(year) = np.interp(year, anchor_years, factors)
        (category TC, from literature_data.csv;
         Knutson et al. 2020: +5% intensity per 1 °C, plateauing at +10%)
4.  tc_scaled(year) = 1 + (tc_factor(year) − 1) × wildfire_scale
5.  projected_tc_outage(asset, year) = base_outage_tc(asset) × tc_scaled(year)
6.  combined_outage(year) = 1 − (1 − wf_outage(year)) × (1 − tc_outage(year))
        (independent hazards; combined < 0.5%, so ≈ sum to < 0.01% error)

Algorithm (drought, capacity_derate channel)
---------------------------------------------
1.  drought_factor(year) = np.interp(year, anchor_years, factors)
        (category DROUGHT, from literature_data.csv; SSP5-8.5 full scale)
2.  drought_factor_scaled = 1 + (drought_factor − 1) × wildfire_scale
3.  drought_scenario_mult = drought_severe_multiplier   if scenario == "severe_drought"
                          = 1.0                         otherwise
        (drought_severe_multiplier from model_assumptions.csv; default 2.4)
4.  capacity_derate(year) = drought_base × drought_factor_scaled(year) × drought_scenario_mult
        (drought_base = 0.5 % from model_assumptions.csv)

Samcheok Blue Power uses seawater cooling, so drought impact is lower than for
inland plants; the 0.5 % base reflects auxiliary-system constraints only.

Algorithm (heat/SST, efficiency_loss channel — two additive components)
------------------------------------------------------------------------
Component A — chronic ambient + SST warming:
1.  delta_T(year) = np.interp(year, anchor_years, temp_changes) × wildfire_scale
        (category HEAT, parameter korea_temp_change_ssp585)
2.  eff_loss_per_C = (ambient_derate_model + sst_air_ratio × cooling_water_derate) / 100
        (from EFFICIENCY rows in literature_data.csv)
        = (0.08 + 0.80 × 0.133) / 100 = 1.864e-3 /°C
3.  chronic_efficiency_loss(year) = delta_T(year) × eff_loss_per_C

Component B — heatwave acute:
4.  heatwave_days(year) = days_baseline
                        + (days_future − days_baseline)
                          × (year − 2024) / (2100 − 2024) × wildfire_scale
        (category HEATWAVE; days_baseline=5.0, days_future=17.4 d/yr from WWA 2025)
5.  heatwave_efficiency_loss(year) = (heatwave_days(year) / 365)
                                    × efficiency_loss_per_event_pct / 100
        (efficiency_loss_per_event_pct = 4.0 %, from HEATWAVE rows)

Total:
6.  efficiency_loss(year) = chronic_efficiency_loss(year) + heatwave_efficiency_loss(year)

Both sub-mechanisms raise the effective heat rate and are applied in the
cashflow engine as: fuel_cost × (1 + efficiency_loss).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from src.data.loaders import (
    load_physical_hazard_data,
    load_physical_literature_data,
    load_physical_model_assumptions,
    load_physical_scenarios,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PhysicalAdjustments:
    """Physical risk adjustments for a single year.

    Attributes
    ----------
    outage_rate : float
        Wildfire-only plant unavailability fraction.
    capacity_derate : float
        Chronic CF reduction from drought (and temperature via seawater cooling).
    efficiency_loss : float
        Total fractional heat-rate increase (chronic heat/SST + heatwave acute).
    water_constrained_capacity : float
        Maximum effective CF from water availability constraint.  1.0 until
        water-risk channel is activated.
    transmission_outage_rate : float
        Wildfire-only transmission unavailability fraction.
    tc_outage_rate : float
        Tropical-cyclone-only plant unavailability fraction.
    tc_transmission_outage_rate : float
        Tropical-cyclone-only transmission unavailability fraction.
    combined_outage_rate : float
        Combined plant unavailability (wildfire + TC, independent events).
        = 1 − (1 − outage_rate) × (1 − tc_outage_rate)
    combined_transmission_outage_rate : float
        Combined transmission unavailability (wildfire + TC, independent).
    chronic_efficiency_loss : float
        Chronic component of efficiency loss (delta_T × eff_loss_per_C).
    heatwave_efficiency_loss : float
        Acute heatwave component of efficiency loss (days/365 × 4%).
    asset_capex_loss_rate : float
        Annual fraction of replacement value destroyed.  Placeholder; 0.0
        until asset damage model is activated.
    notes : str
        Provenance label for debugging.
    """

    outage_rate: float
    capacity_derate: float
    efficiency_loss: float
    water_constrained_capacity: float = 1.0
    transmission_outage_rate: float = 0.0
    tc_outage_rate: float = 0.0
    tc_transmission_outage_rate: float = 0.0
    combined_outage_rate: float = 0.0
    combined_transmission_outage_rate: float = 0.0
    chronic_efficiency_loss: float = 0.0
    heatwave_efficiency_loss: float = 0.0
    asset_capex_loss_rate: float = 0.0
    notes: str = ""


@dataclass
class YearlyPhysicalAdjustments:
    """Year-by-year physical risk adjustments spanning the plant operating life.

    All rate arrays are dimensionless fractions in [0, 1] unless noted.

    Attributes
    ----------
    years : np.ndarray
        Calendar years, shape (n,).
    outage_rates : np.ndarray
        Wildfire-only plant unavailability fraction.
    capacity_derates : np.ndarray
        Chronic CF reduction — drought (active).
    efficiency_losses : np.ndarray
        Total fractional fuel heat-rate increase (chronic + heatwave).
    water_constraints : np.ndarray
        Max CF from water availability (1.0 until water channel active).
    transmission_outage_rates : np.ndarray
        Wildfire-only transmission unavailability fraction.
    tc_outage_rates : np.ndarray
        Tropical-cyclone-only plant unavailability fraction.
    tc_transmission_outage_rates : np.ndarray
        Tropical-cyclone-only transmission unavailability fraction.
    combined_outage_rates : np.ndarray
        Combined plant unavailability (wildfire + TC, independent events).
    combined_transmission_outage_rates : np.ndarray
        Combined transmission unavailability (wildfire + TC, independent).
    chronic_efficiency_losses : np.ndarray
        Chronic heat/SST component of efficiency loss.
    heatwave_efficiency_losses : np.ndarray
        Acute heatwave component of efficiency loss.
    asset_capex_loss_rates : np.ndarray
        Annual asset replacement loss fraction (placeholder zeros).
    scenario_name : str
        Physical scenario label (baseline / moderate_physical / high_physical …).
    """

    years: np.ndarray
    outage_rates: np.ndarray
    capacity_derates: np.ndarray
    efficiency_losses: np.ndarray
    water_constraints: np.ndarray
    transmission_outage_rates: np.ndarray
    asset_capex_loss_rates: np.ndarray
    scenario_name: str = ""

    # New fields — TC and heatwave channels
    tc_outage_rates: np.ndarray = field(default_factory=lambda: np.array([]))
    tc_transmission_outage_rates: np.ndarray = field(default_factory=lambda: np.array([]))
    combined_outage_rates: np.ndarray = field(default_factory=lambda: np.array([]))
    combined_transmission_outage_rates: np.ndarray = field(default_factory=lambda: np.array([]))
    chronic_efficiency_losses: np.ndarray = field(default_factory=lambda: np.array([]))
    heatwave_efficiency_losses: np.ndarray = field(default_factory=lambda: np.array([]))

    def __post_init__(self) -> None:
        """Back-fill new fields with zeros if not supplied (backward compat)."""
        n = len(self.years)
        for attr in (
            "tc_outage_rates",
            "tc_transmission_outage_rates",
            "combined_outage_rates",
            "combined_transmission_outage_rates",
            "chronic_efficiency_losses",
            "heatwave_efficiency_losses",
        ):
            arr = getattr(self, attr)
            if len(arr) == 0:
                setattr(self, attr, np.zeros(n))

    def get_adjustment_for_year(self, year: int) -> PhysicalAdjustments:
        """Return a ``PhysicalAdjustments`` snapshot for *year*.

        Returns zero-risk adjustments for years outside the modelled range.
        """
        mask = self.years == year
        if not mask.any():
            return PhysicalAdjustments(0.0, 0.0, 0.0, 1.0, 0.0, notes="out of range")
        idx = int(np.where(mask)[0][0])
        return PhysicalAdjustments(
            outage_rate=float(self.outage_rates[idx]),
            capacity_derate=float(self.capacity_derates[idx]),
            efficiency_loss=float(self.efficiency_losses[idx]),
            water_constrained_capacity=float(self.water_constraints[idx]),
            transmission_outage_rate=float(self.transmission_outage_rates[idx]),
            tc_outage_rate=float(self.tc_outage_rates[idx]),
            tc_transmission_outage_rate=float(self.tc_transmission_outage_rates[idx]),
            combined_outage_rate=float(self.combined_outage_rates[idx]),
            combined_transmission_outage_rate=float(self.combined_transmission_outage_rates[idx]),
            chronic_efficiency_loss=float(self.chronic_efficiency_losses[idx]),
            heatwave_efficiency_loss=float(self.heatwave_efficiency_losses[idx]),
            asset_capex_loss_rate=float(self.asset_capex_loss_rates[idx]),
            notes=f"{self.scenario_name} y{year}",
        )


# ---------------------------------------------------------------------------
# Factory — reads archive CSVs, interpolates, applies scenario scaling
# ---------------------------------------------------------------------------

def build_physical_adjustments(
    start_year: int,
    n_years: int,
    physical_scenario: str = "high_physical",
    outage_hours_override: Optional[Dict[str, float]] = None,
) -> YearlyPhysicalAdjustments:
    """Build year-by-year physical risk adjustments from archive CSV data.

    Active channels: wildfire outage, TC outage, drought capacity derate,
    chronic heat/SST efficiency loss, heatwave acute efficiency loss.

    See module docstring for the full algorithm for each channel.

    Args:
        start_year: First calendar year of the modelled operating life.
        n_years: Number of years to model.
        physical_scenario: One of the scenarios in ``physical_scenarios.csv``
            (baseline / moderate_physical / high_physical / severe_drought).
        outage_hours_override: Optional ``{"plant": hours, "transmission": hours}``
            that overrides the CSV default restoration durations for both wildfire
            and TC.  Used by the dashboard slider without changing any file on disk.

    Returns:
        ``YearlyPhysicalAdjustments`` with arrays of length *n_years*.
    """
    years = np.arange(start_year, start_year + n_years, dtype=float)

    # --- Load inputs from CSVs ---
    hazard_rows     = load_physical_hazard_data()
    literature_rows = load_physical_literature_data()
    assumptions     = load_physical_model_assumptions()

    # --- SSP & wildfire scale from data/physical/scenarios.csv ---
    phys_scenarios = load_physical_scenarios()
    sc_row = next(
        (r for r in phys_scenarios if r["scenario"] == physical_scenario), None
    )
    if sc_row is None:
        available = [r["scenario"] for r in phys_scenarios]
        raise ValueError(
            f"Physical scenario '{physical_scenario}' not found in scenarios.csv. "
            f"Available: {available}"
        )
    ssp            = sc_row["ssp"]
    wildfire_scale = float(sc_row["wildfire_scale"])

    # --- Shared asset parameters ---
    outage_prob_plant       = assumptions["outage_prob_wildfire"]   # P(damage|wf)
    outage_prob_tc          = assumptions["outage_prob_tc"]         # P(damage|TC)
    hours_per_year          = assumptions["hours_per_year"]

    # Allow UI slider to override outage durations for both hazards
    outage_dur_plant = (
        outage_hours_override.get("plant", assumptions["outage_duration_wildfire"])
        if outage_hours_override else assumptions["outage_duration_wildfire"]
    )
    outage_dur_transmission = (
        outage_hours_override.get("transmission", assumptions["outage_duration_tc"])
        if outage_hours_override else assumptions["outage_duration_tc"]
    )

    # --- Helper: extract anchor (years, values) for one category+parameter ---
    def _anchors(category: str, parameter: str):
        rows = [
            r for r in literature_rows
            if r.get("category") == category and r.get("parameter") == parameter
        ]
        rows_sorted = sorted(rows, key=lambda x: int(x["year"]))
        return (
            [int(r["year"]) for r in rows_sorted],
            [float(r["value"]) for r in rows_sorted],
        )

    # --- Helper: look up a single "all"-year EFFICIENCY or HEATWAVE parameter ---
    def _lit_param(category: str, param: str) -> float:
        row = next(
            (r for r in literature_rows
             if r.get("category") == category and r.get("parameter") == param),
            None,
        )
        if row is None:
            raise ValueError(f"{category}/{param} not found in literature_data.csv")
        return float(row["value"])

    # =========================================================================
    # WILDFIRE channel
    # =========================================================================
    wf_row = next(
        (r for r in hazard_rows if r["hazard"] == "wildfire"), None
    )
    if wf_row is None:
        raise ValueError("No 'wildfire' row found in climada_data.csv")

    wf_events    = float(wf_row["events_at_location"])    # 6
    wf_ref_years = float(wf_row["years_covered"])         # 20
    annual_freq_wf = wf_events / wf_ref_years             # 0.30 events/yr

    base_wf_plant = annual_freq_wf * outage_prob_plant * (outage_dur_plant / hours_per_year)
    base_wf_tx    = annual_freq_wf * outage_prob_tc    * (outage_dur_transmission / hours_per_year)

    anchor_yrs_wf, anchor_vals_wf = _anchors("WILDFIRE", "climate_factor")
    wf_factors = np.interp(years, anchor_yrs_wf, anchor_vals_wf)
    wf_scaled  = 1.0 + (wf_factors - 1.0) * wildfire_scale

    plant_outage_rates        = base_wf_plant * wf_scaled
    transmission_outage_rates = base_wf_tx    * wf_scaled

    # =========================================================================
    # TROPICAL CYCLONE channel
    # =========================================================================
    tc_row = next(
        (r for r in hazard_rows if r["hazard"] == "tropical_cyclone_damaging"), None
    )
    if tc_row is None:
        raise ValueError("No 'tropical_cyclone_damaging' row found in climada_data.csv")

    tc_events    = float(tc_row["events_at_location"])    # 5
    tc_ref_years = float(tc_row["years_covered"])         # 40
    annual_freq_tc = tc_events / tc_ref_years             # 0.125 events/yr

    # Both plant and transmission use outage_prob_tc / outage_duration_tc
    # (TC structural damage profile applies equally to generation equipment
    # and towers/lines; plant uses the same probability/duration as wildfire
    # here is intentional — a direct TC hit is less frequent but more severe
    # per event than a wildfire.)
    base_tc_plant = annual_freq_tc * outage_prob_tc * (outage_dur_plant        / hours_per_year)
    base_tc_tx    = annual_freq_tc * outage_prob_tc * (outage_dur_transmission / hours_per_year)

    anchor_yrs_tc, anchor_vals_tc = _anchors("TC", "climate_factor")
    tc_factors = np.interp(years, anchor_yrs_tc, anchor_vals_tc)
    tc_scaled  = 1.0 + (tc_factors - 1.0) * wildfire_scale

    tc_outage_rates            = base_tc_plant * tc_scaled
    tc_transmission_outage_rates = base_tc_tx  * tc_scaled

    # Combined (independent events: P(down) = 1 − P(wf_ok) × P(tc_ok))
    combined_outage_rates = (
        1.0 - (1.0 - plant_outage_rates) * (1.0 - tc_outage_rates)
    )
    combined_transmission_outage_rates = (
        1.0 - (1.0 - transmission_outage_rates) * (1.0 - tc_transmission_outage_rates)
    )

    # =========================================================================
    # DROUGHT channel — capacity derate
    # =========================================================================
    drought_base           = assumptions["drought_capacity_derate_base"]
    drought_severe_mult    = assumptions["drought_severe_multiplier"]
    # Severe drought scenario emphasises drought above SSP5-8.5 baseline.
    # Other scenarios: multiplier = 1.0 (no amplification beyond standard scale).
    drought_scenario_mult  = drought_severe_mult if physical_scenario == "severe_drought" else 1.0

    anchor_yrs_dr, anchor_vals_dr = _anchors("DROUGHT", "climate_factor")
    dr_factors = np.interp(years, anchor_yrs_dr, anchor_vals_dr)
    dr_scaled  = 1.0 + (dr_factors - 1.0) * wildfire_scale

    capacity_derates = drought_base * dr_scaled * drought_scenario_mult

    # =========================================================================
    # HEAT / SST channel — efficiency loss (two components)
    # =========================================================================

    # --- Component A: chronic ambient + SST warming ---
    ambient_derate_pct = _lit_param("EFFICIENCY", "ambient_derate_model")  # %/°C
    cooling_derate_pct = _lit_param("EFFICIENCY", "cooling_water_derate")  # %/°C
    sst_air_ratio      = _lit_param("EFFICIENCY", "sst_air_ratio")         # dimensionless

    eff_loss_per_C = (ambient_derate_pct + sst_air_ratio * cooling_derate_pct) / 100.0

    anchor_yrs_tmp, anchor_vals_tmp = _anchors("HEAT", "korea_temp_change_ssp585")
    delta_T_ssp585  = np.interp(years, anchor_yrs_tmp, anchor_vals_tmp)
    delta_T_scaled  = delta_T_ssp585 * wildfire_scale

    chronic_efficiency_losses = delta_T_scaled * eff_loss_per_C

    # --- Component B: acute heatwave events ---
    hw_days_base   = _lit_param("HEATWAVE", "days_baseline")    # 5.0 d/yr (2024)
    hw_days_future = _lit_param("HEATWAVE", "days_future")      # 17.4 d/yr (2100, SSP5-8.5)
    hw_eff_pct     = _lit_param("HEATWAVE", "efficiency_loss")  # 4.0 % per event day

    # Linear increase from 2024 baseline to 2100 SSP5-8.5, scaled by SSP intensity
    hw_t        = np.clip((years - 2024) / (2100 - 2024), 0.0, 1.0)
    heatwave_days = hw_days_base + (hw_days_future - hw_days_base) * hw_t * wildfire_scale
    heatwave_efficiency_losses = (heatwave_days / 365.0) * (hw_eff_pct / 100.0)

    # Total efficiency loss
    efficiency_losses = chronic_efficiency_losses + heatwave_efficiency_losses

    n = len(years)
    logger.info(
        "Built physical adjustments [%s / %s]: %d years, scale=%.2f | "
        "wf_plant_2050=%.5f, tc_plant_2050=%.5f, combined_outage_2050=%.5f | "
        "cap_derate_2050=%.4f, eff_loss_2050=%.4f (chronic=%.4f, hw=%.4f)",
        physical_scenario, ssp, n, wildfire_scale,
        float(np.interp(2050, years, plant_outage_rates)),
        float(np.interp(2050, years, tc_outage_rates)),
        float(np.interp(2050, years, combined_outage_rates)),
        float(np.interp(2050, years, capacity_derates)),
        float(np.interp(2050, years, efficiency_losses)),
        float(np.interp(2050, years, chronic_efficiency_losses)),
        float(np.interp(2050, years, heatwave_efficiency_losses)),
    )

    return YearlyPhysicalAdjustments(
        years=years,
        outage_rates=plant_outage_rates,
        capacity_derates=capacity_derates,
        efficiency_losses=efficiency_losses,
        water_constraints=np.ones(n),
        transmission_outage_rates=transmission_outage_rates,
        asset_capex_loss_rates=np.zeros(n),
        scenario_name=physical_scenario,
        tc_outage_rates=tc_outage_rates,
        tc_transmission_outage_rates=tc_transmission_outage_rates,
        combined_outage_rates=combined_outage_rates,
        combined_transmission_outage_rates=combined_transmission_outage_rates,
        chronic_efficiency_losses=chronic_efficiency_losses,
        heatwave_efficiency_losses=heatwave_efficiency_losses,
    )

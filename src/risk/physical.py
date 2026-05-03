"""Physical risk module — wildfire, drought and heat/SST channels.

Computes year-by-year physical risk adjustments for a coal power plant by
reading CSV inputs from ``data/physical/`` and linearly interpolating to
every operating year.

Active channels
---------------
- **Wildfire outage** (plant + transmission): wildfire damage to equipment/lines.
- **Drought capacity derate**: reduced CF from water/cooling constraints under drought.
- **Heat/SST efficiency loss**: raised heat-rate from warmer ambient and seawater.

Planned but not yet active: TC outage, flood outage, SLR, asset capex loss.

Data sources (all in ``data/physical/``)
-----------------------------------------
- ``climada_data.csv``       — CLIMADA event counts (NASA FIRMS, IBTrACS, ISIMIP)
- ``literature_data.csv``    — Verified climate factors (WWA 2025, IPCC AR6, Kim 2016)
- ``model_assumptions.csv``  — Outage probabilities, durations, base derate/loss rates
- ``scenarios.csv``          — Physical scenario definitions incl. ``wildfire_scale``

Physical scenario → SSP mapping and scenario scale
---------------------------------------------------
Defined in ``data/physical/scenarios.csv`` (no hardcoded values in code):
  baseline         → ssp126, wildfire_scale = 0.30
  moderate_physical → ssp245, wildfire_scale = 0.60
  high_physical    → ssp585, wildfire_scale = 1.00
  severe_drought   → ssp585, wildfire_scale = 1.00

The same ``wildfire_scale`` is reused as a universal SSP intensity scale for all
hazard channels (drought factors, temperature change), since all are driven by
the same greenhouse-gas trajectory.

Algorithm (wildfire, outage_rate channel)
-----------------------------------------
1.  annual_frequency = events_at_location / years_covered
        (from climada_data.csv, hazard == "wildfire")
2.  base_outage_rate = annual_frequency
                       × outage_prob_wildfire
                       × (outage_duration_wildfire / hours_per_year)
        (from model_assumptions.csv)
3.  wildfire_factor(year) = np.interp(year, anchor_years, factors)
        (category WILDFIRE, from literature_data.csv)
4.  projected_wildfire_outage(year)
        = base_outage_rate × [1 + (wildfire_factor(year) − 1) × wildfire_scale]

Transmission outage follows the same formula using outage_prob_tc and
outage_duration_tc as a conservative proxy.

Algorithm (drought, capacity_derate channel)
---------------------------------------------
1.  drought_factor(year) = np.interp(year, anchor_years, factors)
        (category DROUGHT, from literature_data.csv; SSP5-8.5 full scale)
2.  drought_factor_scaled = 1 + (drought_factor − 1) × wildfire_scale
3.  capacity_derate(year) = drought_base × drought_factor_scaled(year)
        (drought_base from model_assumptions.csv)

Samcheok Blue Power uses seawater cooling, so drought impact is lower than for
inland plants; the base derate (0.5 %) reflects auxiliary system constraints only.

Algorithm (heat/SST, efficiency_loss channel)
----------------------------------------------
1.  delta_T_ssp585(year) = np.interp(year, anchor_years, temp_changes)
        (category HEAT, parameter korea_temp_change_ssp585, from literature_data.csv)
2.  delta_T_scaled(year) = delta_T_ssp585(year) × wildfire_scale
3.  eff_loss_per_C = (ambient_derate_model + sst_air_ratio × cooling_water_derate) / 100
        (from EFFICIENCY rows in literature_data.csv)
4.  efficiency_loss(year) = delta_T_scaled(year) × eff_loss_per_C

Both the ambient air warming and the sea surface temperature (SST) rise reduce
condenser efficiency; SST rise ≈ sst_air_ratio × air temperature rise.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
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
# Data structures (mirrors archive/src/risk/physical.py interface)
# ---------------------------------------------------------------------------

@dataclass
class PhysicalAdjustments:
    """Physical risk adjustments for a single year.

    Attributes
    ----------
    outage_rate : float
        Fraction of annual hours the plant is unavailable due to wildfire
        (and later TC/flood) damage to plant equipment.
    capacity_derate : float
        Capacity factor reduction from drought / temperature (chronic).
        Zero until temperature channel is activated.
    efficiency_loss : float
        Fractional increase in fuel heat rate from wildfire smoke fouling
        (acute) and thermal stress (chronic, activated later).
    water_constrained_capacity : float
        Maximum effective CF from water availability constraint.  1.0 until
        water-risk channel is activated.
    transmission_outage_rate : float
        Fraction of hours the transmission path is unavailable due to wildfire
        damage to lines, towers, or substations.
    asset_capex_loss_rate : float
        Annual fraction of plant + transmission replacement value destroyed.
        Placeholder; populated when asset damage model is activated.
    notes : str
        Provenance label for debugging.
    """

    outage_rate: float
    capacity_derate: float
    efficiency_loss: float
    water_constrained_capacity: float = 1.0
    transmission_outage_rate: float = 0.0
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
        Plant unavailability fraction — wildfire (active) + other (future).
    capacity_derates : np.ndarray
        Chronic CF reduction — temperature / drought (placeholder zeros).
    efficiency_losses : np.ndarray
        Fractional fuel heat-rate increase from wildfire smoke fouling.
    water_constraints : np.ndarray
        Max CF from water availability (1.0 until water channel active).
    transmission_outage_rates : np.ndarray
        Transmission unavailability fraction — wildfire damage.
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

    def get_adjustment_for_year(self, year: int) -> PhysicalAdjustments:
        """Return a ``PhysicalAdjustments`` snapshot for *year*.

        Returns zero-risk adjustments for years outside the modelled range.
        """
        mask = self.years == year
        if not mask.any():
            return PhysicalAdjustments(0.0, 0.0, 0.0, 1.0, 0.0, 0.0, "out of range")
        idx = int(np.where(mask)[0][0])
        return PhysicalAdjustments(
            outage_rate=float(self.outage_rates[idx]),
            capacity_derate=float(self.capacity_derates[idx]),
            efficiency_loss=float(self.efficiency_losses[idx]),
            water_constrained_capacity=float(self.water_constraints[idx]),
            transmission_outage_rate=float(self.transmission_outage_rates[idx]),
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

    Algorithm
    ---------
    See module docstring.  Currently only the wildfire channel is populated;
    all other channels (capacity_derate, water_constraints, asset_capex) are
    set to their neutral values (0 or 1.0) until activated.

    Args:
        start_year: First calendar year of the modelled operating life.
        n_years: Number of years to model.
        physical_scenario: One of the scenarios in ``physical_scenarios.csv``
            (baseline / moderate_physical / high_physical / severe_drought).
        outage_hours_override: Optional ``{"plant": hours, "transmission": hours}``
            that overrides the CSV default restoration durations.  Used by the
            dashboard slider without changing any file on disk.

    Returns:
        ``YearlyPhysicalAdjustments`` with arrays of length *n_years*.
    """
    years = np.arange(start_year, start_year + n_years, dtype=float)

    # --- Load inputs from CSVs ---
    hazard_rows    = load_physical_hazard_data()
    literature_rows = load_physical_literature_data()
    assumptions    = load_physical_model_assumptions()

    # --- SSP & wildfire scale from data/physical/scenarios.csv (no hardcoded values) ---
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

    # --- CLIMADA: wildfire event counts ---
    wildfire_row = next(
        (r for r in hazard_rows if r["hazard"] == "wildfire"), None
    )
    if wildfire_row is None:
        raise ValueError("No 'wildfire' row found in climada_data.csv")

    events = float(wildfire_row["events_at_location"])
    ref_years = float(wildfire_row["years_covered"])
    annual_frequency = events / ref_years      # 6/20 = 0.30 events/yr

    # --- Model assumptions: outage probability and duration ---
    outage_prob_plant = assumptions["outage_prob_wildfire"]
    outage_dur_plant = (
        outage_hours_override.get("plant", assumptions["outage_duration_wildfire"])
        if outage_hours_override
        else assumptions["outage_duration_wildfire"]
    )
    outage_dur_transmission = (
        outage_hours_override.get("transmission", assumptions["outage_duration_tc"])
        if outage_hours_override
        else assumptions["outage_duration_tc"]
    )
    outage_prob_transmission = assumptions["outage_prob_tc"]
    hours_per_year = assumptions["hours_per_year"]

    # Base outage rates (before climate factor)
    base_plant_outage = annual_frequency * outage_prob_plant * (outage_dur_plant / hours_per_year)
    base_transmission_outage = (
        annual_frequency * outage_prob_transmission * (outage_dur_transmission / hours_per_year)
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

    # -------------------------------------------------------------------------
    # WILDFIRE channel — outage rates
    # -------------------------------------------------------------------------
    anchor_yrs_wf, anchor_vals_wf = _anchors("WILDFIRE", "climate_factor")
    wf_climate_factors = np.interp(years, anchor_yrs_wf, anchor_vals_wf)
    wf_scaled = 1.0 + (wf_climate_factors - 1.0) * wildfire_scale

    plant_outage_rates        = base_plant_outage        * wf_scaled
    transmission_outage_rates = base_transmission_outage * wf_scaled

    # -------------------------------------------------------------------------
    # DROUGHT channel — capacity derate
    # -------------------------------------------------------------------------
    drought_base = assumptions["drought_capacity_derate_base"]

    anchor_yrs_dr, anchor_vals_dr = _anchors("DROUGHT", "climate_factor")
    dr_climate_factors = np.interp(years, anchor_yrs_dr, anchor_vals_dr)
    dr_scaled = 1.0 + (dr_climate_factors - 1.0) * wildfire_scale

    capacity_derates = drought_base * dr_scaled

    # -------------------------------------------------------------------------
    # HEAT / SST channel — efficiency loss
    # -------------------------------------------------------------------------
    # Coefficients from EFFICIENCY rows (all-year entries, not year-anchored)
    def _eff_param(param: str) -> float:
        row = next(
            (r for r in literature_rows
             if r.get("category") == "EFFICIENCY" and r.get("parameter") == param),
            None,
        )
        if row is None:
            raise ValueError(f"EFFICIENCY/{param} not found in literature_data.csv")
        return float(row["value"])

    ambient_derate_pct  = _eff_param("ambient_derate_model")   # %/°C
    cooling_derate_pct  = _eff_param("cooling_water_derate")    # %/°C
    sst_air_ratio       = _eff_param("sst_air_ratio")           # dimensionless

    # Fraction efficiency loss per °C of warming
    eff_loss_per_C = (ambient_derate_pct + sst_air_ratio * cooling_derate_pct) / 100.0

    anchor_yrs_tmp, anchor_vals_tmp = _anchors("HEAT", "korea_temp_change_ssp585")
    delta_T_ssp585  = np.interp(years, anchor_yrs_tmp, anchor_vals_tmp)
    delta_T_scaled  = delta_T_ssp585 * wildfire_scale   # scale ΔT by SSP intensity

    efficiency_losses = delta_T_scaled * eff_loss_per_C

    n = len(years)
    logger.info(
        "Built physical adjustments [%s / %s]: %d years, scale=%.2f | "
        "plant_outage_2050=%.5f, tx_outage_2050=%.5f | "
        "capacity_derate_2050=%.4f, efficiency_loss_2050=%.4f",
        physical_scenario, ssp, n, wildfire_scale,
        float(np.interp(2050, years, plant_outage_rates)),
        float(np.interp(2050, years, transmission_outage_rates)),
        float(np.interp(2050, years, capacity_derates)),
        float(np.interp(2050, years, efficiency_losses)),
    )

    return YearlyPhysicalAdjustments(
        years=years,
        outage_rates=plant_outage_rates,
        capacity_derates=capacity_derates,
        efficiency_losses=efficiency_losses,
        water_constraints=np.ones(n),          # water risk: activated later
        transmission_outage_rates=transmission_outage_rates,
        asset_capex_loss_rates=np.zeros(n),    # asset damage model: activated later
        scenario_name=physical_scenario,
    )

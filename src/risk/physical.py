"""Wildfire physical risk module.

Computes year-by-year physical risk adjustments for a coal power plant by
reading the pre-computed anchor data in ``data/raw/physical_risk/`` and
linearly interpolating to every operating year.

Currently only the wildfire channel is active.  The data structure is designed
to hold all hazard channels (TC, flood, temperature, SLR) so they can be
activated later without changing the interface.

Data sources
------------
- ``climada_data.csv``         — CLIMADA event counts (NASA FIRMS, IBTrACS, ISIMIP)
- ``literature_data.csv``      — Verified climate factors and efficiency coefficients
- ``model_assumptions.csv``    — Outage probabilities and durations (industry assumptions)
- ``physical_risk_output.csv`` — Pre-computed anchor outputs at 2024/2030/2050/2100

Physical scenario → SSP mapping (from archive/src/pipeline/runner.py)
----------------------------------------------------------------------
  baseline         → ssp126   (low physical risk acceleration)
  moderate_physical → ssp245  (mid-range; currently uses RCP8.5 data as proxy)
  high_physical    → ssp585   (worst-case; RCP8.5 full data)
  severe_drought   → ssp585   (same climate pathway, drought emphasis)

The RCP8.5 output anchors are used for high_physical / severe_drought.
For baseline and moderate_physical the wildfire climate factor trajectory
is scaled down because lower SSP pathways produce smaller fire-weather
intensification.  Scaling factors follow WWA (2025) analysis:
  ssp126 scale = 0.30  (30 % of RCP8.5 intensification)
  ssp245 scale = 0.60

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
4.  projected_wildfire_outage(year) = base_outage_rate × wildfire_factor(year)
        × ssp_scale (scenario-dependent)

Transmission outage follows the same formula using outage_prob_tc and
outage_duration_tc as a conservative proxy until TC data is activated.

Efficiency loss tracks the wildfire outage trajectory scaled by the
ratio from the physical_risk_output.csv anchor data.
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
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SSP scale factors for wildfire intensity relative to RCP8.5
# Based on WWA (2025) analysis of South Korean wildfire likelihood
# ---------------------------------------------------------------------------
_SSP_WILDFIRE_SCALE: Dict[str, float] = {
    "ssp126": 0.30,
    "ssp245": 0.60,
    "ssp585": 1.00,
}


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

    # --- Load inputs from archive CSVs ---
    hazard_rows = load_physical_hazard_data()
    literature_rows = load_physical_literature_data()
    assumptions = load_physical_model_assumptions()

    # --- SSP-based wildfire scale (scenario dimension) ---
    _SSP_MAP = {
        "baseline": "ssp126",
        "moderate_physical": "ssp245",
        "high_physical": "ssp585",
        "severe_drought": "ssp585",
    }
    ssp = _SSP_MAP.get(physical_scenario, "ssp585")
    wildfire_scale = _SSP_WILDFIRE_SCALE.get(ssp, 1.0)

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

    # --- Literature: wildfire climate factors (WILDFIRE category) ---
    wf_factor_rows = [
        r for r in literature_rows
        if r.get("category") == "WILDFIRE" and r.get("parameter") == "climate_factor"
    ]
    anchor_years_wf = sorted(int(r["year"]) for r in wf_factor_rows)
    anchor_factors_wf = [
        float(r["value"])
        for r in sorted(wf_factor_rows, key=lambda x: int(x["year"]))
    ]

    # Interpolate climate factors to every operating year; hold constant beyond last anchor
    climate_factors = np.interp(years, anchor_years_wf, anchor_factors_wf)

    # Apply SSP scenario scaling
    climate_factors = 1.0 + (climate_factors - 1.0) * wildfire_scale

    # --- Projected outage rates ---
    plant_outage_rates = base_plant_outage * climate_factors
    transmission_outage_rates = base_transmission_outage * climate_factors

    # --- Efficiency loss ---
    # Wildfire causes plant unavailability (outage_rate) not thermal efficiency
    # loss; that channel belongs to the temperature hazard (activated later).
    # Set to zero for the current wildfire-only implementation.
    efficiency_losses = np.zeros(len(years))

    n = len(years)
    logger.info(
        "Built wildfire adjustments [%s / %s]: %d years, freq=%.3f/yr, "
        "scale=%.2f, plant_outage_2050=%.5f, tx_outage_2050=%.5f",
        physical_scenario, ssp, n, annual_frequency, wildfire_scale,
        float(np.interp(2050, years, plant_outage_rates)),
        float(np.interp(2050, years, transmission_outage_rates)),
    )

    return YearlyPhysicalAdjustments(
        years=years,
        outage_rates=plant_outage_rates,
        capacity_derates=np.zeros(n),         # temperature/drought: activated later
        efficiency_losses=efficiency_losses,
        water_constraints=np.ones(n),          # water risk: activated later
        transmission_outage_rates=transmission_outage_rates,
        asset_capex_loss_rates=np.zeros(n),    # asset damage model: activated later
        scenario_name=physical_scenario,
    )

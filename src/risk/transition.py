"""Transition risk adjustments.

Computes per-year capacity factors and carbon costs driven by policy scenarios.

Design:
- ``TransitionAdjustments``: static snapshot for a single year (used in cashflow).
- ``YearlyTransitionAdjustments``: full time-series for a scenario.
- ``build_yearly_transition_adjustments()``: factory that wires a
  ``TransitionScenario`` into a year-by-year trajectory.

Carbon price interpolation
--------------------------
The policy CSV has anchor prices at 2025, 2030, 2040, 2050.  We linearly
interpolate between anchors and hold constant beyond 2050.

Carbon cost per MWh = carbon_price (USD/tCO₂) × emissions (tCO₂/MWh)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from src.scenarios.base import TransitionScenario

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Static snapshot (single year)
# ---------------------------------------------------------------------------

@dataclass
class TransitionAdjustments:
    """Transition risk adjustments for a single year / scenario snapshot.

    Attributes:
        capacity_factor: Effective CF after dispatch penalty.
        operating_years: Effective plant life under this scenario.
        notes: Human-readable summary.
    """

    capacity_factor: float
    operating_years: int
    notes: str = ""


# ---------------------------------------------------------------------------
# Time-series container
# ---------------------------------------------------------------------------

@dataclass
class YearlyTransitionAdjustments:
    """Year-by-year transition risk adjustments.

    Attributes:
        years: Array of calendar years (e.g. 2025…2064).
        capacity_factors: CF for each year after dispatch penalty.
        carbon_costs_per_mwh: Carbon cost (USD/MWh) for each year,
            computed as ``carbon_price × emissions_intensity``.
        scenario_name: Scenario label for logging/output.
    """

    years: np.ndarray
    capacity_factors: np.ndarray
    carbon_costs_per_mwh: np.ndarray
    scenario_name: str = ""

    def get_cf_for_year(self, year: int) -> float:
        """Return capacity factor for *year*.  Returns base CF if out of range."""
        idx = np.where(self.years == year)[0]
        return float(self.capacity_factors[idx[0]]) if len(idx) else float(self.capacity_factors[0])

    def get_carbon_cost_per_mwh_for_year(self, year: int) -> float:
        """Return carbon cost (USD/MWh) for *year*.  Returns 0 if out of range."""
        idx = np.where(self.years == year)[0]
        return float(self.carbon_costs_per_mwh[idx[0]]) if len(idx) else 0.0


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def build_yearly_transition_adjustments(
    scenario: TransitionScenario,
    base_capacity_factor: float,
    emissions_tco2_per_mwh: float,
    start_year: int = 2025,
) -> YearlyTransitionAdjustments:
    """Build a full time-series of transition adjustments for *scenario*.

    Algorithm:
        CF(year) = base_CF × (1 − dispatch_penalty)

        carbon_price(year) = linear interpolation over anchor years
            {2025, 2030, 2040, 2050}; capped at 2050 value beyond 2050.

        carbon_cost_per_mwh(year) = carbon_price(year) × emissions_tco2_per_mwh

    Args:
        scenario: Policy scenario from ``TransitionScenario``.
        base_capacity_factor: Technical CF with no policy risk (from plant CSV).
        emissions_tco2_per_mwh: Plant emission intensity (tCO₂/MWh).
        start_year: First year of operations.

    Returns:
        ``YearlyTransitionAdjustments`` covering ``start_year`` to
        ``start_year + retirement_years - 1``.
    """
    n = scenario.retirement_years
    years = np.arange(start_year, start_year + n)

    # --- Capacity factor ---
    # Constant dispatch penalty applied uniformly across all years.
    # A more granular ramp could be added later if needed.
    cf = base_capacity_factor * (1.0 - scenario.dispatch_penalty)
    capacity_factors = np.full(n, max(0.0, cf))

    # --- Carbon prices: linear interpolation over anchor years ---
    anchor_prices = scenario.carbon_prices
    if anchor_prices:
        anchor_yrs = np.array(sorted(anchor_prices.keys()), dtype=float)
        anchor_vals = np.array([anchor_prices[int(y)] for y in anchor_yrs], dtype=float)
        # np.interp clips to edge values beyond the anchors
        raw_prices = np.interp(years.astype(float), anchor_yrs, anchor_vals)
    else:
        raw_prices = np.zeros(n)

    carbon_costs_per_mwh = raw_prices * emissions_tco2_per_mwh

    logger.debug(
        "Transition [%s]: CF=%.3f  carbon_2025=%.1f  carbon_2050=%.1f USD/tCO2",
        scenario.name,
        cf,
        float(raw_prices[0]) if len(raw_prices) else 0,
        float(np.interp(2050, years.astype(float), raw_prices)) if len(raw_prices) else 0,
    )

    return YearlyTransitionAdjustments(
        years=years,
        capacity_factors=capacity_factors,
        carbon_costs_per_mwh=carbon_costs_per_mwh,
        scenario_name=scenario.name,
    )


def apply_transition(
    scenario: TransitionScenario,
    base_capacity_factor: float,
) -> TransitionAdjustments:
    """Return a static ``TransitionAdjustments`` snapshot for *scenario*.

    Useful for quick single-year checks; the cashflow engine uses
    ``YearlyTransitionAdjustments`` for full time-series runs.
    """
    cf = base_capacity_factor * (1.0 - scenario.dispatch_penalty)
    return TransitionAdjustments(
        capacity_factor=max(0.0, cf),
        operating_years=scenario.retirement_years,
        notes=f"scenario={scenario.name} penalty={scenario.dispatch_penalty:.0%}",
    )

"""Scenario definitions for transition risk modelling.

Only transition risk scenarios are implemented here.  Physical risk scenarios
will be added in a future step once the transition pipeline is validated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class TransitionScenario:
    """A single climate-transition policy scenario.

    Attributes:
        name: Unique scenario identifier (must match ``policy.csv`` column).
        dispatch_penalty: Fraction by which the capacity factor is reduced
            due to dispatch merit-order effects from competing clean capacity
            (e.g. 0.10 → 10 % lower dispatch).
        retirement_years: Expected plant operating life under this scenario.
            May be shorter than the technical life if stranded-asset risk is
            factored in.
        carbon_prices: Map from calendar year to carbon price (USD/tCO₂).
            Intermediate years are linearly interpolated by
            ``YearlyTransitionAdjustments``.
        carbon_scenario: Label from policy.csv (informational).
        description: Human-readable description.
    """

    name: str
    dispatch_penalty: float  # fraction [0, 1)
    retirement_years: int    # years
    carbon_prices: Dict[int, float] = field(default_factory=dict)  # {year: USD/tCO2}
    carbon_scenario: str = ""
    description: str = ""

    @classmethod
    def from_policy_row(cls, row: Dict) -> "TransitionScenario":
        """Build a TransitionScenario from a policy.csv row dict.

        Expected keys: ``scenario``, ``dispatch_penalty``, ``retirement_years``,
        ``carbon_price_2025``, ``carbon_price_2030``, ``carbon_price_2040``,
        ``carbon_price_2050``, ``carbon_scenario``, ``description``.
        """
        return cls(
            name=row["scenario"],
            dispatch_penalty=float(row["dispatch_penalty"]),
            retirement_years=int(row["retirement_years"]),
            carbon_prices={
                2025: float(row["carbon_price_2025"]),
                2030: float(row["carbon_price_2030"]),
                2040: float(row["carbon_price_2040"]),
                2050: float(row["carbon_price_2050"]),
            },
            carbon_scenario=row.get("carbon_scenario", ""),
            description=row.get("description", ""),
        )

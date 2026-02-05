"""
Korea Basic Power Plan (전력수급기본계획) Data.

Data sources:
- Ministry of Trade, Industry and Energy (MOTIE)
- 10th Basic Plan for Power Supply (제10차 전력수급기본계획, Dec 2022)
- Korea Electric Power Corporation (KEPCO) statistics

See docs/sources/TRANSITION_ASSUMPTIONS.md for full citations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from pathlib import Path
import csv

from src.models.base import BaseScenario


@dataclass
class KoreaPowerPlan(BaseScenario):
    """
    Korea Basic Power Plan scenario.

    Defines year-by-year coal capacity factor trajectory based on
    national power supply planning (전력수급기본계획).

    Attributes:
        _name: Plan identifier
        _description: Human-readable description
        _source: Official source citation
        dispatch_trajectory: Dict mapping year -> capacity factor multiplier (0-1)
        retirement_year: Year of mandatory retirement (if any)
        coal_share_trajectory: Dict mapping year -> coal share in generation mix (%)
    """
    _name: str
    _description: str
    _source: str
    dispatch_trajectory: Dict[int, float] = field(default_factory=dict)
    retirement_year: Optional[int] = None
    coal_share_trajectory: Dict[int, float] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def source(self) -> str:
        return self._source

    def get_value(self, year: int) -> float:
        """Get dispatch factor (capacity factor multiplier) for a given year."""
        if self.retirement_year and year >= self.retirement_year:
            return 0.0

        if year in self.dispatch_trajectory:
            return self.dispatch_trajectory[year]

        # Interpolate between known years
        years = sorted(self.dispatch_trajectory.keys())
        if not years:
            return 1.0
        if year < years[0]:
            import logging
            logging.getLogger(__name__).warning(
                f"Year {year} is before trajectory start ({years[0]}), using first value"
            )
            return self.dispatch_trajectory[years[0]]
        if year > years[-1]:
            import logging
            logging.getLogger(__name__).warning(
                f"Year {year} is beyond trajectory end ({years[-1]}), using last value"
            )
            return self.dispatch_trajectory[years[-1]]

        # Linear interpolation
        for i, y in enumerate(years[:-1]):
            if years[i] <= year < years[i + 1]:
                y0, y1 = years[i], years[i + 1]
                f0, f1 = self.dispatch_trajectory[y0], self.dispatch_trajectory[y1]
                return f0 + (f1 - f0) * (year - y0) / (y1 - y0)

        return self.dispatch_trajectory[years[-1]]

    def get_capacity_factor(self, year: int, baseline_cf: float) -> float:
        """Get effective capacity factor after policy constraints."""
        return baseline_cf * self.get_value(year)

    def get_coal_share(self, year: int) -> float:
        """Get coal share in generation mix (%)."""
        if year in self.coal_share_trajectory:
            return self.coal_share_trajectory[year]

        years = sorted(self.coal_share_trajectory.keys())
        if not years:
            return 0.0
        if year < years[0]:
            return self.coal_share_trajectory[years[0]]
        if year > years[-1]:
            return self.coal_share_trajectory[years[-1]]

        for i, y in enumerate(years[:-1]):
            if years[i] <= year < years[i + 1]:
                y0, y1 = years[i], years[i + 1]
                s0, s1 = self.coal_share_trajectory[y0], self.coal_share_trajectory[y1]
                return s0 + (s1 - s0) * (year - y0) / (y1 - y0)

        return self.coal_share_trajectory[years[-1]]

    def get_remaining_lifetime(self, cod_year: int, baseline_life: int) -> int:
        """Get remaining lifetime considering retirement mandate."""
        natural_end = cod_year + baseline_life
        if self.retirement_year:
            return max(0, min(self.retirement_year, natural_end) - cod_year)
        return baseline_life

    def get_trajectory(self, start_year: int, end_year: int) -> Dict[int, float]:
        """Get full dispatch trajectory."""
        return {year: self.get_value(year) for year in range(start_year, end_year + 1)}


# =============================================================================
# PREDEFINED KOREA POWER PLANS
# =============================================================================

KOREA_POWER_PLANS: Dict[str, KoreaPowerPlan] = {
    "10th_basic_plan": KoreaPowerPlan(
        _name="10th_basic_plan",
        _description="제10차 전력수급기본계획 (10th Basic Plan, Dec 2022)",
        _source="Ministry of Trade, Industry and Energy (MOTIE), Dec 2022",
        dispatch_trajectory={
            2024: 1.00,  # Current baseline
            2025: 0.95,  # Beginning of phase-down
            2030: 0.70,  # Target: coal share ~30%
            2035: 0.50,  # Continued reduction
            2040: 0.30,  # Near phase-out
            2050: 0.00,  # Full phase-out target
        },
        retirement_year=2050,
        coal_share_trajectory={
            2024: 32.4,  # 2024 actual share
            2030: 21.2,  # 10th plan target
            2036: 14.4,  # 10th plan projection
        },
    ),

    "11th_basic_plan_draft": KoreaPowerPlan(
        _name="11th_basic_plan_draft",
        _description="제11차 전력수급기본계획 초안 (11th Basic Plan Draft, 2024)",
        _source="MOTIE draft proposals, subject to change",
        dispatch_trajectory={
            2024: 1.00,
            2025: 0.90,
            2030: 0.60,  # More aggressive than 10th plan
            2035: 0.35,
            2038: 0.20,  # New intermediate target
            2040: 0.10,
            2050: 0.00,
        },
        retirement_year=2050,
        coal_share_trajectory={
            2024: 32.4,
            2030: 18.0,  # Lower target
            2038: 10.0,
        },
    ),

    "carbon_neutrality_2050": KoreaPowerPlan(
        _name="carbon_neutrality_2050",
        _description="2050 탄소중립 시나리오 A (Carbon Neutrality Scenario A)",
        _source="2050 Carbon Neutrality Commission, 2021",
        dispatch_trajectory={
            2024: 1.00,
            2025: 0.85,
            2030: 0.50,  # Accelerated phase-down
            2035: 0.20,
            2040: 0.00,  # Full phase-out by 2040
        },
        retirement_year=2040,
        coal_share_trajectory={
            2024: 32.4,
            2030: 15.0,
            2040: 0.0,
        },
    ),

    "current_trajectory": KoreaPowerPlan(
        _name="current_trajectory",
        _description="현행 정책 유지 (Current Policy Continuation)",
        _source="Based on historical trends, no acceleration",
        dispatch_trajectory={
            2024: 1.00,
            2025: 1.00,
            2030: 0.90,
            2035: 0.85,
            2040: 0.75,
            2050: 0.50,
        },
        retirement_year=None,  # No mandatory retirement
        coal_share_trajectory={
            2024: 32.4,
            2030: 30.0,
            2040: 25.0,
            2050: 15.0,
        },
    ),

    "baseline_no_change": KoreaPowerPlan(
        _name="baseline_no_change",
        _description="기준 시나리오 (Baseline - No Policy Change)",
        _source="Hypothetical baseline for comparison",
        dispatch_trajectory={
            2024: 1.00,
            2030: 1.00,
            2040: 1.00,
            2050: 1.00,
        },
        retirement_year=None,
        coal_share_trajectory={
            2024: 32.4,
            2030: 32.4,
            2040: 32.4,
        },
    ),
}


def load_korea_power_plan_from_csv(csv_path: Path) -> Dict[str, KoreaPowerPlan]:
    """
    Load Korea Power Plan data from CSV file.

    Expected CSV format:
    plan_name,year,dispatch_factor,coal_share,retirement_year,source
    10th_basic_plan,2024,1.00,32.4,2050,"MOTIE 2022"
    10th_basic_plan,2030,0.70,21.2,2050,"MOTIE 2022"
    ...

    Args:
        csv_path: Path to CSV file

    Returns:
        Dict mapping plan name to KoreaPowerPlan
    """
    plans: Dict[str, Dict] = {}

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            plan_name = row['plan_name']
            if plan_name not in plans:
                plans[plan_name] = {
                    'dispatch': {},
                    'coal_share': {},
                    'retirement': None,
                    'source': row.get('source', ''),
                }

            year = int(row['year'])
            plans[plan_name]['dispatch'][year] = float(row['dispatch_factor'])

            if 'coal_share' in row and row['coal_share']:
                plans[plan_name]['coal_share'][year] = float(row['coal_share'])

            if 'retirement_year' in row and row['retirement_year']:
                plans[plan_name]['retirement'] = int(row['retirement_year'])

    result = {}
    for name, data in plans.items():
        result[name] = KoreaPowerPlan(
            _name=name,
            _description=f"Loaded from {csv_path.name}",
            _source=data['source'],
            dispatch_trajectory=data['dispatch'],
            retirement_year=data['retirement'],
            coal_share_trajectory=data['coal_share'],
        )

    return result

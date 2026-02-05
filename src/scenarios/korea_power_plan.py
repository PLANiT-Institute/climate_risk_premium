"""
Korea National Power Supply Plan (전력수급기본계획) scenarios.
Implements dispatch reduction trajectories from the 10th Basic Plan.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
import numpy as np


@dataclass
class KoreaPowerPlanScenario:
    """
    Korea power supply plan trajectory for coal generation.

    Attributes:
        name: Scenario identifier
        cf_trajectory: Dict mapping year -> capacity factor for Samcheok plant
        early_retirement_year: Year of forced closure (if any)
        policy_reference: Source document/policy
        description: Scenario description
    """
    name: str
    cf_trajectory: Dict[int, float]
    early_retirement_year: int | None
    policy_reference: str
    description: str = ""

    def get_capacity_factor(self, year: int, baseline_cf: float = 0.50) -> float:
        """
        Get capacity factor for a given year.

        Uses linear interpolation between available data points.
        Returns 0 if year >= early_retirement_year.

        Args:
            year: Target year
            baseline_cf: Maximum capacity factor (design limit)

        Returns:
            Capacity factor (0-1)
        """
        # Check early retirement
        if self.early_retirement_year and year >= self.early_retirement_year:
            return 0.0

        # If exact year exists, return it
        if year in self.cf_trajectory:
            return min(self.cf_trajectory[year], baseline_cf)

        # Find bounding years for interpolation
        years = sorted(self.cf_trajectory.keys())

        # If before first year, use first year value
        if year < years[0]:
            return min(self.cf_trajectory[years[0]], baseline_cf)

        # If after last year, use last year value (or retirement)
        if year > years[-1]:
            if self.early_retirement_year and year < self.early_retirement_year:
                # Extrapolate linear decline to retirement
                last_year = years[-1]
                last_cf = self.cf_trajectory[last_year]
                years_to_retirement = self.early_retirement_year - last_year
                annual_decline = last_cf / years_to_retirement
                cf = max(0.0, last_cf - (year - last_year) * annual_decline)
                return min(cf, baseline_cf)
            else:
                return min(self.cf_trajectory[years[-1]], baseline_cf)

        # Linear interpolation between bounding years
        for i in range(len(years) - 1):
            if years[i] <= year <= years[i + 1]:
                y0, y1 = years[i], years[i + 1]
                cf0, cf1 = self.cf_trajectory[y0], self.cf_trajectory[y1]

                # Linear interpolation
                weight = (year - y0) / (y1 - y0)
                cf = cf0 + weight * (cf1 - cf0)

                return min(cf, baseline_cf)

        # Fallback (should not reach here)
        return baseline_cf

    def get_operating_years(self, start_year: int = 2024, design_life: int = 40) -> int:
        """
        Calculate actual operating years considering early retirement.

        Args:
            start_year: Plant commissioning year
            design_life: Design operating lifetime (years)

        Returns:
            Actual operating years
        """
        if self.early_retirement_year:
            return max(1, self.early_retirement_year - start_year)
        else:
            return design_life


def load_korea_power_plan_scenarios(file_path: str) -> Dict[str, KoreaPowerPlanScenario]:
    """
    Load Korea power plan scenarios from CSV file.

    Expected CSV format:
        year, total_coal_twh, total_demand_twh, coal_share_pct,
        implied_cf_samcheok, scenario_type, policy_reference, notes

    Args:
        file_path: Path to korea_power_plan.csv

    Returns:
        Dict of scenario name -> KoreaPowerPlanScenario
    """
    import pandas as pd

    df = pd.read_csv(file_path)

    # Extract capacity factor trajectory from CSV
    cf_trajectory = dict(zip(df['year'], df['implied_cf_samcheok']))

    # Define scenarios based on different interpretations of power plan
    scenarios = {}

    # Scenario 1: Official 10th Power Plan (moderate)
    official_years = df[df['scenario_type'].isin(['projection', 'ndc_target', 'plan_target'])]['year'].tolist()
    official_cfs = df[df['scenario_type'].isin(['projection', 'ndc_target', 'plan_target'])]['implied_cf_samcheok'].tolist()

    scenarios['official_10th_plan'] = KoreaPowerPlanScenario(
        name='official_10th_plan',
        cf_trajectory=dict(zip(official_years, official_cfs)),
        early_retirement_year=None,  # No forced closure, but economically unviable after 2045
        policy_reference='10th Basic Plan for Electricity Supply and Demand (2023-2036)',
        description='Official government power plan trajectory with coal phase-down to 2036'
    )

    # Scenario 1.5: 11th Power Plan (Draft)
    plan_11_years = df[df['scenario_type'] == 'official_11th_plan']['year'].tolist()
    plan_11_cfs = df[df['scenario_type'] == 'official_11th_plan']['implied_cf_samcheok'].tolist()
    
    if plan_11_years:
        scenarios['official_11th_plan'] = KoreaPowerPlanScenario(
            name='official_11th_plan',
            cf_trajectory=dict(zip(plan_11_years, plan_11_cfs)),
            early_retirement_year=None,
            policy_reference='11th Basic Plan (Draft)',
            description='Draft 11th Basic Plan with accelerated coal phase-down'
        )
    else:
        # Fallback if CSV not updated yet (should not happen with correct data)
        official_11th_cfs = [cf * 0.80 for cf in official_cfs]
        scenarios['official_11th_plan'] = KoreaPowerPlanScenario(
            name='official_11th_plan',
            cf_trajectory=dict(zip(official_years, official_11th_cfs)),
            early_retirement_year=None,
            policy_reference='11th Basic Plan (Assumed)',
            description='Assumed 11th Basic Plan with 20% faster coal phase-down'
        )

    # Scenario 2: Accelerated phase-out (aggressive civil society)
    accel_df = df[df['year'] <= 2045].copy()
    # Steeper decline than official
    accel_df['implied_cf_samcheok'] = accel_df['implied_cf_samcheok'] * 0.85  # 15% more aggressive

    scenarios['accelerated_phaseout'] = KoreaPowerPlanScenario(
        name='accelerated_phaseout',
        cf_trajectory=dict(zip(accel_df['year'], accel_df['implied_cf_samcheok'])),
        early_retirement_year=2045,
        policy_reference='Solutions for Our Climate - Coal Phase-out Roadmap',
        description='Accelerated coal phase-out aligned with 1.5C pathways'
    )

    # Scenario 3: Delayed transition (baseline inertia)
    delay_df = df[df['year'] <= 2055].copy()
    # Slower decline than official
    delay_df['implied_cf_samcheok'] = delay_df['implied_cf_samcheok'] * 1.15  # 15% slower decline
    delay_df['implied_cf_samcheok'] = delay_df['implied_cf_samcheok'].clip(upper=0.65)  # Cap at 65%

    scenarios['delayed_transition'] = KoreaPowerPlanScenario(
        name='delayed_transition',
        cf_trajectory=dict(zip(delay_df['year'], delay_df['implied_cf_samcheok'])),
        early_retirement_year=None,
        policy_reference='Baseline scenario assuming policy implementation delays',
        description='Delayed implementation of power plan with political/economic resistance'
    )

    # Scenario 4: Net Zero 2050 aligned (full trajectory)
    netzero_years = df['year'].tolist()
    netzero_cfs = df['implied_cf_samcheok'].tolist()

    scenarios['netzero_2050'] = KoreaPowerPlanScenario(
        name='netzero_2050',
        cf_trajectory=dict(zip(netzero_years, netzero_cfs)),
        early_retirement_year=2050,
        policy_reference='Korea Carbon Neutrality 2050 Scenario',
        description='Full trajectory to net-zero with near-complete coal phase-out by 2050'
    )

    return scenarios


def calculate_revenue_impact(
    scenario: KoreaPowerPlanScenario,
    capacity_mw: float,
    power_price: float,
    start_year: int = 2024,
    end_year: int = 2050,
    baseline_cf: float = 0.50
) -> Dict[str, float]:
    """
    Calculate revenue impact from Korea power plan dispatch reductions.

    Args:
        scenario: Power plan scenario
        capacity_mw: Plant capacity (MW)
        power_price: Electricity price ($/MWh)
        start_year: Start year for analysis
        end_year: End year for analysis
        baseline_cf: Baseline capacity factor without power plan constraints

    Returns:
        Dict with cumulative_revenue_loss, avg_annual_loss, npv_loss (at 8% discount)
    """
    discount_rate = 0.08

    total_baseline_revenue = 0.0
    total_plan_revenue = 0.0
    annual_losses = []

    for year in range(start_year, end_year + 1):
        t = year - start_year

        # Baseline revenue (no power plan constraints)
        baseline_generation = capacity_mw * 8760 * baseline_cf
        baseline_revenue = baseline_generation * power_price
        baseline_pv = baseline_revenue / (1 + discount_rate) ** t
        total_baseline_revenue += baseline_pv

        # Power plan constrained revenue
        plan_cf = scenario.get_capacity_factor(year, baseline_cf)
        plan_generation = capacity_mw * 8760 * plan_cf
        plan_revenue = plan_generation * power_price
        plan_pv = plan_revenue / (1 + discount_rate) ** t
        total_plan_revenue += plan_pv

        annual_losses.append(baseline_revenue - plan_revenue)

    npv_loss = total_baseline_revenue - total_plan_revenue
    cumulative_loss = sum(annual_losses)
    avg_annual_loss = cumulative_loss / (end_year - start_year + 1)

    return {
        'cumulative_revenue_loss': cumulative_loss,
        'avg_annual_loss': avg_annual_loss,
        'npv_loss': npv_loss,
        'total_baseline_npv': total_baseline_revenue,
        'total_plan_npv': total_plan_revenue,
        'npv_loss_pct': (npv_loss / total_baseline_revenue * 100) if total_baseline_revenue > 0 else 0
    }

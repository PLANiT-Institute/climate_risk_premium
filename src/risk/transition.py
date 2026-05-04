"""
Transition risk adjustments (policy, dispatch, early retirement).

Updated to integrate Korea National Power Supply Plan (전력수급기본계획) dispatch trajectories
and enhanced 11th Basic Plan scenarios with comprehensive carbon pricing integration.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, TYPE_CHECKING

import numpy as np

from src.scenarios import TransitionScenario

logger = logging.getLogger(__name__)

# Conditional import for Korea Power Plan - allows backward compatibility
try:
    from src.scenarios.korea_power_plan import KoreaPowerPlanScenario
    KOREA_POWER_PLAN_AVAILABLE = True
except ImportError:
    KOREA_POWER_PLAN_AVAILABLE = False
    KoreaPowerPlanScenario = None

# Conditional import for enhanced scenarios
try:
    from src.scenarios.enhanced_korea_power_plan import EnhancedKoreaPowerPlanScenario
    ENHANCED_SCENARIOS_AVAILABLE = True
except ImportError:
    ENHANCED_SCENARIOS_AVAILABLE = False
    EnhancedKoreaPowerPlanScenario = None

if TYPE_CHECKING:
    from src.scenarios.korea_power_plan import KoreaPowerPlanScenario as KoreaPowerPlanScenarioType
    from src.scenarios.enhanced_korea_power_plan import EnhancedKoreaPowerPlanScenario as EnhancedKoreaPowerPlanScenarioType


@dataclass
class TransitionAdjustments:
    """
    Transition risk adjustments to plant operations.

    Attributes:
        capacity_factor: Adjusted capacity factor after policy constraints (0-1)
        operating_years: Adjusted operating lifetime (years)
        notes: Description of adjustments applied
    """
    capacity_factor: float
    operating_years: int
    notes: str = ""


def apply_transition(
    plant_params: Dict[str, Any],
    scenario: TransitionScenario,
    korea_plan_scenario: Optional['KoreaPowerPlanScenarioType'] = None,
    enhanced_korea_scenario: Optional['EnhancedKoreaPowerPlanScenarioType'] = None,
    current_year: Optional[int] = None,
    carbon_pricing_scenario: str = "ndc_aligned"
) -> TransitionAdjustments:
    """
    Apply transition assumptions to baseline plant parameters.

    Can use either generic TransitionScenario (simple dispatch penalty) or
    Korea Power Plan trajectory (year-by-year dispatch reductions from 전력수급계획).

    Args:
        plant_params: Plant design parameters
        scenario: Generic transition risk scenario
        korea_plan_scenario: Optional Korea Power Plan scenario (overrides if provided)
        current_year: Year for Korea Power Plan trajectory lookup

    Returns:
        TransitionAdjustments with capacity factor and operating years

    Priority order (if multiple provided):
        1. Enhanced Korea Power Plan (11th Basic Plan with carbon integration)
        2. Korea Power Plan trajectory (10th Basic Plan)
        3. TransitionScenario dispatch penalty (generic approach)

    Note:
        Carbon price integration is now available through enhanced scenarios.
        Legacy scenarios access carbon price via scenario.get_carbon_price(year)
        in cash flow calculations, not stored in TransitionAdjustments.
    """
    baseline_cf = float(plant_params.get("capacity_factor", 0.85))
    baseline_life = int(plant_params.get("operating_years", 40))
    
    # Initialize with default values
    adjusted_cf = baseline_cf
    adjusted_life = baseline_life
    notes = "No transition adjustments applied"

    # Use Enhanced Korea Power Plan (11th Basic Plan) if available
    if enhanced_korea_scenario is not None and ENHANCED_SCENARIOS_AVAILABLE:
        try:
            # Import enhanced transition functions locally
            from src.risk.enhanced_transition import apply_enhanced_transition, EnhancedTransitionAdjustments
            
            enhanced_adjustments = apply_enhanced_transition(
                plant_params=plant_params,
                scenario=scenario,
                enhanced_korea_scenario=enhanced_korea_scenario,
                current_year=current_year,
                carbon_pricing_scenario=carbon_pricing_scenario
            )
            
            # Convert enhanced adjustments to legacy format for backward compatibility
            return TransitionAdjustments(
                capacity_factor=enhanced_adjustments.capacity_factor,
                operating_years=enhanced_adjustments.operating_years,
                notes=enhanced_adjustments.notes
            )
        except Exception as e:
            logger.warning(
                "Enhanced transition failed, falling back to legacy approach: %s", e
            )
    
    # Use legacy Korea Power Plan trajectory if available
    elif korea_plan_scenario is not None and KOREA_POWER_PLAN_AVAILABLE:
        if current_year is not None:
            # Year-specific capacity factor from power plan
            adjusted_cf = korea_plan_scenario.get_capacity_factor(current_year, baseline_cf)
        else:
            # Use average over lifetime if no specific year provided
            start_year = plant_params.get("cod_year", 2024)
            end_year = start_year + baseline_life
            total_cf = sum(
                korea_plan_scenario.get_capacity_factor(year, baseline_cf)
                for year in range(start_year, end_year)
            )
            adjusted_cf = total_cf / baseline_life

        # Operating years from power plan early retirement
        adjusted_life = korea_plan_scenario.get_operating_years(
            plant_params.get("cod_year", 2024),
            baseline_life
        )

        notes = f"Korea Power Plan: {korea_plan_scenario.name} | {korea_plan_scenario.policy_reference}"

    else:
        # Traditional approach: simple dispatch penalty
        adjusted_cf = max(0.0, baseline_cf - scenario.dispatch_priority_penalty)
        adjusted_life = min(baseline_life, scenario.retirement_years)
        notes = f"Generic transition: {scenario.name} | penalty={scenario.dispatch_priority_penalty:.1%}"

    return TransitionAdjustments(
        capacity_factor=adjusted_cf,
        operating_years=adjusted_life,
        notes=notes
    )


def apply_korea_power_plan_trajectory(
    plant_params: Dict[str, Any],
    korea_plan_scenario: 'KoreaPowerPlanScenarioType',
    start_year: int = 2024,
    end_year: int = 2050
) -> Dict[int, float]:
    """
    Generate year-by-year capacity factor trajectory from Korea Power Plan.

    This function returns annual capacity factors for use in time-series
    cash flow modeling, directly from 전력수급기본계획 data.

    Args:
        plant_params: Plant design parameters
        korea_plan_scenario: Korea Power Plan scenario
        start_year: Analysis start year
        end_year: Analysis end year

    Returns:
        Dict mapping year -> capacity factor

    Example:
        >>> from src.scenarios.korea_power_plan import load_korea_power_plan_scenarios
        >>> scenarios = load_korea_power_plan_scenarios('data/raw/korea_power_plan.csv')
        >>> plan = scenarios['official_10th_plan']
        >>> cf_trajectory = apply_korea_power_plan_trajectory(plant_params, plan, 2024, 2050)
        >>> print(cf_trajectory[2030])  # Capacity factor in 2030
        0.45
    """
    baseline_cf = float(plant_params.get("capacity_factor", 0.85))

    trajectory = {}
    for year in range(start_year, end_year + 1):
        trajectory[year] = korea_plan_scenario.get_capacity_factor(year, baseline_cf)

    return trajectory


@dataclass
class YearlyTransitionAdjustments:
    """Year-by-year transition risk adjustments (dispatch + carbon costs)."""
    years: np.ndarray                    # [2025, 2026, ..., 2060]
    capacity_factors: np.ndarray         # per-year CF (dispatch trajectory)
    carbon_costs_per_mwh: np.ndarray     # per-year $/MWh carbon cost
    scenario_name: str = ""

    def get_cf_for_year(self, year: int) -> float:
        idx = np.searchsorted(self.years, year)
        if idx < len(self.years) and self.years[idx] == year:
            return float(self.capacity_factors[idx])
        # Out of range: clamp to nearest boundary
        return float(self.capacity_factors[min(idx, len(self.capacity_factors) - 1)])

    def get_carbon_cost_per_mwh_for_year(self, year: int) -> float:
        idx = np.searchsorted(self.years, year)
        if idx < len(self.years) and self.years[idx] == year:
            return float(self.carbon_costs_per_mwh[idx])
        return float(self.carbon_costs_per_mwh[min(idx, len(self.carbon_costs_per_mwh) - 1)])


def _carbon_cost_per_mwh(scenario, year: int, emission_factor: float) -> float:
    """Compute carbon cost per MWh: carbon_price_usd × emission_factor."""
    cp = scenario.get_carbon_price(year)
    if cp is None:
        return 0.0
    return cp.carbon_price_usd * emission_factor


def create_yearly_transition_adjustments(
    plant_params: Dict[str, Any],
    enhanced_korea_scenario,
    start_year: int,
    end_year: int,
    emission_factor: float = 0.82,  # tCO2/MWh (supercritical coal)
    dispatch_priority_penalty: float = 0.0,
) -> YearlyTransitionAdjustments:
    """
    Build year-by-year transition adjustments from an enhanced Korea Power Plan.

    Args:
        plant_params: Plant design parameters (needs capacity_factor)
        enhanced_korea_scenario: Enhanced 11th Basic Plan scenario object
        start_year: First operating year
        end_year: Last operating year (inclusive)
        emission_factor: tCO2/MWh for the plant (default 0.82 supercritical coal)
        dispatch_priority_penalty: Severity scaling factor from TransitionScenario
            (e.g. 0.10 for moderate → CFs multiplied by 0.90)

    Returns:
        YearlyTransitionAdjustments with per-year CF and carbon costs
    """
    baseline_cf = float(plant_params.get("capacity_factor", 0.85))
    years = np.arange(start_year, end_year + 1)

    capacity_factors = np.array([
        enhanced_korea_scenario.get_capacity_factor(int(y), baseline_cf) for y in years
    ])

    # Apply severity scaling consistent with apply_enhanced_transition()
    if dispatch_priority_penalty > 0:
        capacity_factors = capacity_factors * (1.0 - dispatch_priority_penalty)

    carbon_costs_per_mwh = np.array([
        _carbon_cost_per_mwh(enhanced_korea_scenario, int(y), emission_factor)
        for y in years
    ])

    return YearlyTransitionAdjustments(
        years=years,
        capacity_factors=capacity_factors,
        carbon_costs_per_mwh=carbon_costs_per_mwh,
        scenario_name=getattr(enhanced_korea_scenario, 'name', ''),
    )

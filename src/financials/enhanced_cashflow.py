"""
Enhanced cash flow model with 11th Basic Plan integration.

Implements comprehensive cash flow modeling with:
- Policy-adjusted revenue streams from 11th Basic Plan
- Carbon cost integration with K-ETS pricing
- Compound transition impact analysis
- Integration with enhanced transition module

Uses the standard compute_cashflows_timeseries() engine with enhanced
transition adjustments layered on top.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Any

import numpy as np

from src.financials.cashflow import CashFlowTimeSeries, compute_cashflows_timeseries
from src.risk import TransitionAdjustments, PhysicalAdjustments
from src.risk.enhanced_transition import (
    apply_enhanced_transition,
    EnhancedTransitionAdjustments,
)
from src.scenarios import TransitionScenario, MarketScenario
from src.scenarios.enhanced_korea_power_plan import (
    EnhancedKoreaPowerPlan,
)

logger = logging.getLogger(__name__)


@dataclass
class EnhancedCashFlowAnalysis:
    """Enhanced cash flow analysis with transition and carbon cost integration."""

    # Core results
    baseline_cashflows: Optional[CashFlowTimeSeries] = None
    policy_adjusted_cashflows: Optional[CashFlowTimeSeries] = None
    enhanced_adjustments: Optional[EnhancedTransitionAdjustments] = None

    # Aggregate impacts (computed in __post_init__)
    baseline_npv: float = 0.0
    adjusted_npv: float = 0.0
    total_carbon_costs: float = 0.0
    financing_impact_bps: float = 0.0
    transition_risk_premium_pct: float = 0.0

    def __post_init__(self):
        """Calculate aggregate metrics from cash flow results."""
        discount_rate = 0.08

        if self.baseline_cashflows is not None:
            self.baseline_npv = np.sum(
                self.baseline_cashflows.free_cash_flow
                / (1 + discount_rate) ** np.arange(len(self.baseline_cashflows.years))
            )

        if self.policy_adjusted_cashflows is not None:
            self.adjusted_npv = np.sum(
                self.policy_adjusted_cashflows.free_cash_flow
                / (1 + discount_rate) ** np.arange(len(self.policy_adjusted_cashflows.years))
            )

        if self.enhanced_adjustments is not None:
            self.total_carbon_costs = self.enhanced_adjustments.carbon_cost_burden
            self.transition_risk_premium_pct = self.enhanced_adjustments.transition_risk_premium

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "enhanced_adjustments": (
                self.enhanced_adjustments.to_dict() if self.enhanced_adjustments else {}
            ),
            "baseline_cashflows": (
                self.baseline_cashflows.to_dict() if self.baseline_cashflows is not None else {}
            ),
            "policy_adjusted_cashflows": (
                self.policy_adjusted_cashflows.to_dict()
                if self.policy_adjusted_cashflows is not None
                else {}
            ),
            "aggregate_impacts": {
                "baseline_npv": self.baseline_npv,
                "adjusted_npv": self.adjusted_npv,
                "total_carbon_costs": self.total_carbon_costs,
                "financing_impact_bps": self.financing_impact_bps,
                "transition_risk_premium_pct": self.transition_risk_premium_pct,
            },
        }


def create_enhanced_cashflow_analysis(
    plant_params: Dict[str, Any],
    enhanced_plan: EnhancedKoreaPowerPlan,
    transition_scenario: TransitionScenario,
    physical_adj: PhysicalAdjustments,
    market_scenario: Optional[MarketScenario] = None,
    start_year: int = 2024,
    carbon_pricing_scenario: str = "ndc_aligned",
    yearly_physical_adj=None,
) -> EnhancedCashFlowAnalysis:
    """
    Create comprehensive cash flow analysis with enhanced transition integration.

    This function runs two cash flow projections:
    1. Baseline — using the standard transition scenario (10th Plan or generic)
    2. Enhanced — using the 11th Basic Plan enhanced adjustments

    Both use the same compute_cashflows_timeseries() engine.

    Args:
        plant_params: Plant design parameters (must include all keys required
            by compute_cashflows_timeseries: capacity_mw, power_price_per_mwh,
            heat_rate_mmbtu_mwh, etc.)
        enhanced_plan: Enhanced Korea Power Plan (11th Basic Plan)
        transition_scenario: Baseline TransitionScenario for comparison
        physical_adj: Physical risk adjustments
        market_scenario: Optional market scenario
        start_year: First year of operation
        carbon_pricing_scenario: K-ETS pricing scenario for enhanced path
        yearly_physical_adj: Optional year-by-year physical adjustments

    Returns:
        EnhancedCashFlowAnalysis with baseline and enhanced results
    """
    baseline_cf = float(plant_params.get("capacity_factor", 0.5))
    baseline_life = int(plant_params.get("operating_years", 40))

    # --- 1. Baseline cash flows (without 11th Plan) ---
    baseline_transition_adj = TransitionAdjustments(
        capacity_factor=max(0.0, baseline_cf - transition_scenario.dispatch_priority_penalty),
        operating_years=min(baseline_life, transition_scenario.retirement_years),
        notes=f"Baseline: {transition_scenario.name}",
    )

    baseline_cashflows = compute_cashflows_timeseries(
        plant_params=plant_params,
        transition_scenario=transition_scenario,
        transition_adj=baseline_transition_adj,
        physical_adj=physical_adj,
        market_scenario=market_scenario,
        start_year=start_year,
        yearly_physical_adj=yearly_physical_adj,
    )

    # --- 2. Enhanced cash flows (with 11th Basic Plan) ---
    enhanced_adjustments = apply_enhanced_transition(
        plant_params=plant_params,
        scenario=transition_scenario,
        enhanced_korea_scenario=enhanced_plan,
        current_year=start_year,
        carbon_pricing_scenario=carbon_pricing_scenario,
    )

    enhanced_transition_adj = TransitionAdjustments(
        capacity_factor=enhanced_adjustments.capacity_factor,
        operating_years=enhanced_adjustments.operating_years,
        notes=enhanced_adjustments.notes,
    )

    enhanced_cashflows = compute_cashflows_timeseries(
        plant_params=plant_params,
        transition_scenario=transition_scenario,
        transition_adj=enhanced_transition_adj,
        physical_adj=physical_adj,
        market_scenario=market_scenario,
        start_year=start_year,
        yearly_physical_adj=yearly_physical_adj,
    )

    return EnhancedCashFlowAnalysis(
        baseline_cashflows=baseline_cashflows,
        policy_adjusted_cashflows=enhanced_cashflows,
        enhanced_adjustments=enhanced_adjustments,
    )


def create_transition_scenario_comparison(
    plant_params: Dict[str, Any],
    scenarios: Dict[str, EnhancedKoreaPowerPlan],
    transition_scenario: TransitionScenario,
    physical_adj: PhysicalAdjustments,
    market_scenario: Optional[MarketScenario] = None,
    start_year: int = 2024,
) -> Dict[str, EnhancedCashFlowAnalysis]:
    """
    Create comparison analysis between multiple transition scenarios.

    Args:
        plant_params: Plant parameters
        scenarios: Dictionary of scenario names to EnhancedKoreaPowerPlan objects
        transition_scenario: Baseline TransitionScenario
        physical_adj: Physical risk adjustments
        market_scenario: Optional market scenario
        start_year: Analysis start year

    Returns:
        Dictionary with EnhancedCashFlowAnalysis per scenario
    """
    results = {}

    for scenario_name, plan in scenarios.items():
        results[scenario_name] = create_enhanced_cashflow_analysis(
            plant_params=plant_params,
            enhanced_plan=plan,
            transition_scenario=transition_scenario,
            physical_adj=physical_adj,
            market_scenario=market_scenario,
            start_year=start_year,
        )

    return results


def analyze_policy_transition_timeline(
    plant_params: Dict[str, Any],
    enhanced_plan: EnhancedKoreaPowerPlan,
) -> Dict[str, Any]:
    """
    Analyze the policy transition timeline and its impacts.

    Args:
        plant_params: Plant parameters
        enhanced_plan: Enhanced Korea Power Plan

    Returns:
        Dictionary with timeline analysis
    """
    capacity_mw = float(plant_params.get("capacity_mw", 1000))
    baseline_cf = float(plant_params.get("capacity_factor", 0.50))
    power_price = float(plant_params.get("power_price_per_mwh", 50.0))
    heat_rate = float(plant_params.get("heat_rate", 0.33))

    policy_effective_year = enhanced_plan.effective_date
    cod_year = plant_params.get("cod_year", 2024)
    pre_transition_years = max(0, policy_effective_year - cod_year)
    post_transition_years = (
        enhanced_plan.coal_schedule.complete_phase_out_year - policy_effective_year
    )

    timeline_analysis: Dict[str, Any] = {}

    for year in [policy_effective_year, policy_effective_year + 5, policy_effective_year + 10]:
        policy_cf = enhanced_plan.get_capacity_factor(year, baseline_cf)

        baseline_generation = capacity_mw * 8760 * baseline_cf
        policy_generation = capacity_mw * 8760 * policy_cf

        carbon_price = enhanced_plan.get_carbon_price(year)
        carbon_cost = 0.0
        if carbon_price:
            carbon_cost = policy_generation * heat_rate * carbon_price.carbon_price_usd / 1_000_000

        baseline_revenue = baseline_generation * power_price
        policy_revenue = policy_generation * power_price
        revenue_loss = policy_revenue - baseline_revenue

        timeline_analysis[f"year_{year}"] = {
            "capacity_factor_baseline": baseline_cf,
            "capacity_factor_policy": policy_cf,
            "generation_difference_mwh": policy_generation - baseline_generation,
            "revenue_loss_usd": revenue_loss,
            "carbon_cost_usd": carbon_cost,
            "policy_transition_phase": (
                "pre-transition" if year < policy_effective_year else "post-transition"
            ),
        }

    timeline_analysis["policy_summary"] = {
        "effective_year": policy_effective_year,
        "pre_transition_years": pre_transition_years,
        "post_transition_years": post_transition_years,
        "coal_phase_out_complete": enhanced_plan.coal_schedule.complete_phase_out_year,
        "phase_out_acceleration_pct": 42.0,
    }

    return timeline_analysis

"""
Enhanced transition risk module with 11th Basic Power Plan integration.
Implements comprehensive policy transition mechanisms and carbon pricing integration.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

from src.scenarios import TransitionScenario
try:
    from src.scenarios.enhanced_korea_power_plan import (
        EnhancedKoreaPowerPlan, EnhancedKoreaPowerPlanScenario,
        get_transition_scenarios, create_enhanced_11th_plan
    )
    ENHANCED_PLAN_AVAILABLE = True
except ImportError:
    ENHANCED_PLAN_AVAILABLE = False
    EnhancedKoreaPowerPlan = None
    EnhancedKoreaPowerPlanScenario = None
    get_transition_scenarios = None
    create_enhanced_11th_plan = None

# Conditional import for Korea Power Plan - allows backward compatibility
try:
    from src.scenarios.korea_power_plan import KoreaPowerPlanScenario
    KOREA_POWER_PLAN_AVAILABLE = True
except ImportError:
    KOREA_POWER_PLAN_AVAILABLE = False
    KoreaPowerPlanScenario = None


@dataclass
class EnhancedTransitionAdjustments:
    """
    Enhanced transition risk adjustments with carbon cost integration.
    
    Attributes:
        capacity_factor: Adjusted capacity factor after policy constraints (0-1)
        operating_years: Adjusted operating lifetime (years)
        carbon_cost_burden: Annual carbon cost ($/year)
        revenue_loss_pct: Revenue loss percentage vs baseline
        transition_risk_premium: Additional risk premium for financing (%)
        policy_mechanism: Primary policy driver
        carbon_price_trajectory: Year -> carbon price mapping
        notes: Description of adjustments applied
    """
    capacity_factor: float
    operating_years: int
    carbon_cost_burden: float
    revenue_loss_pct: float
    transition_risk_premium: float
    policy_mechanism: str
    carbon_price_trajectory: Dict[int, float]
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'capacity_factor': self.capacity_factor,
            'operating_years': self.operating_years,
            'carbon_cost_burden': self.carbon_cost_burden,
            'revenue_loss_pct': self.revenue_loss_pct,
            'transition_risk_premium': self.transition_risk_premium,
            'policy_mechanism': self.policy_mechanism,
            'carbon_price_trajectory': dict(self.carbon_price_trajectory),
            'notes': self.notes,
        }


class PolicyTransitionMechanism:
    """Policy transition mechanism implementation."""
    
    @staticmethod
    def calculate_coal_phaseout_acceleration(
        baseline_cf: float,
        year: int,
        accelerated_rate: float = 1.42  # 42% faster than 10th Plan
    ) -> float:
        """Calculate capacity factor reduction from accelerated coal phase-out."""
        # 10th Plan baseline phase-out: linear from 65% in 2024 to 20% by 2036
        baseline_coal_cf = max(0.20, 0.65 - (year - 2024) * 0.0375)
        
        # 11th Plan acceleration
        accelerated_cf = max(0.05, baseline_coal_cf * (1 - accelerated_rate * 0.1))
        
        return accelerated_cf
    
    @staticmethod
    def calculate_renewable_integration_impact(
        solar_capacity_year: int,
        wind_capacity_year: int,
        target_solar_2038: float,
        target_wind_2038: float,
        baseline_solar: float = 1.0,
        baseline_wind: float = 1.5
    ) -> Tuple[float, float]:
        """Calculate renewable expansion impact on grid stability and coal dispatch."""
        years_to_2038 = max(2038 - solar_capacity_year, 1)
        
        # Required annual expansion rates
        solar_annual_rate = (target_solar_2038 - baseline_solar) / years_to_2038
        wind_annual_rate = (target_wind_2038 - baseline_wind) / years_to_2038
        
        # Grid integration impacts on thermal plants
        solar_integration_penalty = min(0.15, solar_annual_rate * 0.05)
        wind_integration_penalty = min(0.10, wind_annual_rate * 0.03)
        
        return solar_integration_penalty, wind_integration_penalty
    
    @staticmethod
    def calculate_nuclear_expansion_impact(
        nuclear_capacity_addition: float,
        grid_stability_factor: float = 1.0
    ) -> float:
        """Calculate nuclear expansion impact on coal plant dispatch priority."""
        # New nuclear capacity reduces need for coal baseload
        nuclear_displacement_factor = min(0.25, nuclear_capacity_addition / 100.0)
        
        return nuclear_displacement_factor * grid_stability_factor


class KETSCarbonPricing:
    """K-ETS carbon price trajectory integration."""
    
    @staticmethod
    def get_carbon_price_trajectory(
        scenario: str,
        start_year: int = 2024,
        end_year: int = 2050
    ) -> Dict[int, float]:
        """
        Generate K-ETS carbon price trajectory.
        
        Args:
            scenario: Policy scenario (current_policy, ndc_aligned, net_zero)
            start_year: Start year
            end_year: End year
            
        Returns:
            Dict mapping year -> carbon price (USD/ton)
        """
        trajectory = {}
        
        # Base trajectories calibrated to K-ETS phases
        # Source: KRX 배출권시장, 2024 avg ~9,465 KRW/ton ≈ $7-8/ton
        # These prices align with KETSCarbonPrice.create_price_trajectory() in
        # enhanced_korea_power_plan.py (KRW/1300 conversion).
        # When an EnhancedKoreaPowerPlan is available, its get_carbon_price()
        # is used directly instead of these fallback trajectories.
        if scenario == "current_policy":
            # Conservative: follows KRX market trends with modest escalation
            base_prices = {
                2024: 7, 2025: 8, 2026: 11, 2027: 14, 2028: 17,
                2030: 23, 2032: 28, 2035: 35, 2038: 45, 2040: 51,
                2045: 75, 2050: 115
            }
        elif scenario == "ndc_aligned":
            # NDC-aligned: moderate escalation consistent with NDC 2030 targets
            base_prices = {
                2024: 7, 2025: 8, 2026: 11, 2027: 14, 2028: 17,
                2030: 23, 2032: 28, 2035: 35, 2038: 45, 2040: 51,
                2045: 97, 2050: 150
            }
        elif scenario == "net_zero":
            # Net-zero aligned: aggressive trajectory for 2050 carbon neutrality
            base_prices = {
                2024: 7, 2025: 8, 2026: 15, 2027: 22, 2028: 30,
                2030: 40, 2032: 55, 2035: 80, 2038: 110, 2040: 140,
                2045: 220, 2050: 300
            }
        else:
            raise ValueError(f"Unknown carbon price scenario: {scenario}")
        
        # Interpolate for all years
        sorted_years = sorted(base_prices.keys())
        for year in range(start_year, end_year + 1):
            if year in base_prices:
                trajectory[year] = base_prices[year]
            else:
                # Linear interpolation
                if year < sorted_years[0]:
                    trajectory[year] = base_prices[sorted_years[0]]
                elif year > sorted_years[-1]:
                    trajectory[year] = base_prices[sorted_years[-1]]
                else:
                    for i in range(len(sorted_years) - 1):
                        y0, y1 = sorted_years[i], sorted_years[i + 1]
                        if y0 <= year <= y1:
                            p0, p1 = base_prices[y0], base_prices[y1]
                            weight = (year - y0) / (y1 - y0)
                            trajectory[year] = p0 + weight * (p1 - p0)
                            break
        
        return trajectory
    
    @staticmethod
    def calculate_carbon_cost_burden(
        capacity_mw: float,
        capacity_factor: float,
        heat_rate: float,  # MMBtu/MWh
        carbon_content: float,  # tons CO2/MMBtu
        carbon_price: float,
    ) -> float:
        """Calculate annual carbon cost burden for a coal plant."""
        # Annual generation (MWh)
        annual_generation = capacity_mw * 8760 * capacity_factor
        
        # Annual emissions (tons CO2)
        annual_emissions = annual_generation * heat_rate * carbon_content
        
        # Annual carbon cost ($)
        annual_carbon_cost = annual_emissions * carbon_price
        
        return annual_carbon_cost


def apply_enhanced_transition(
    plant_params: Dict[str, Any],
    scenario: TransitionScenario,
    enhanced_korea_scenario: Optional[EnhancedKoreaPowerPlanScenario] = None,
    korea_plan_scenario: Optional['KoreaPowerPlanScenario'] = None,
    current_year: Optional[int] = None,
    carbon_pricing_scenario: str = "ndc_aligned"
) -> EnhancedTransitionAdjustments:
    """
    Apply enhanced transition assumptions with 11th Basic Plan integration.
    
    Priority order (if multiple provided):
        1. Enhanced Korea Power Plan (11th Basic Plan)
        2. Legacy Korea Power Plan (10th Basic Plan)
        3. Traditional TransitionScenario approach
    
    Args:
        plant_params: Plant design parameters
        scenario: Generic transition risk scenario
        enhanced_korea_scenario: Enhanced Korea Power Plan scenario (11th Basic)
        korea_plan_scenario: Legacy Korea Power Plan scenario (10th Basic)
        current_year: Year for policy trajectory lookup
        carbon_pricing_scenario: K-ETS carbon pricing scenario
        
    Returns:
        EnhancedTransitionAdjustments with comprehensive adjustments
    """
    baseline_cf = float(plant_params.get("capacity_factor", 0.5))
    baseline_life = int(plant_params.get("operating_years", 40))
    capacity_mw = float(plant_params.get("capacity_mw", 1000))
    heat_rate = float(plant_params.get("heat_rate", 8.8))  # Typical for supercritical coal
    carbon_content = float(plant_params.get("carbon_content", 0.093))  # Tons CO2/MMBtu for coal
    
    # Initialize carbon price trajectory
    carbon_trajectory = KETSCarbonPricing.get_carbon_price_trajectory(
        carbon_pricing_scenario
    )
    
    # Use Enhanced Korea Power Plan (11th Basic Plan) if available
    if enhanced_korea_scenario is not None:
        if current_year is not None:
            # Year-specific capacity factor from enhanced power plan
            adjusted_cf = enhanced_korea_scenario.get_capacity_factor(current_year, baseline_cf)
            carbon_price_obj = enhanced_korea_scenario.get_carbon_price(current_year)
            carbon_price = carbon_price_obj.carbon_price_usd if carbon_price_obj else carbon_trajectory.get(current_year, 8)
        else:
            # Use average over lifetime
            start_year = plant_params.get("cod_year", 2024)
            end_year = start_year + baseline_life
            total_cf = sum(
                enhanced_korea_scenario.get_capacity_factor(year, baseline_cf)
                for year in range(start_year, end_year)
            )
            adjusted_cf = total_cf / baseline_life
            prices = []
            for year in range(start_year, end_year):
                cp = enhanced_korea_scenario.get_carbon_price(year)
                prices.append(cp.carbon_price_usd if cp else carbon_trajectory.get(year, 8))
            carbon_price = np.mean(prices)
        
        enhanced_life = enhanced_korea_scenario.get_operating_years(
            plant_params.get("cod_year", 2024),
            baseline_life
        )

        # Apply scenario severity: dispatch_priority_penalty scales the enhanced plan CF
        # moderate (0.10) → CF reduced by 10%, aggressive (0.25) → CF reduced by 25%
        if scenario.dispatch_priority_penalty > 0:
            adjusted_cf = adjusted_cf * (1.0 - scenario.dispatch_priority_penalty)

        # Cap operating years with scenario's retirement schedule
        adjusted_life = min(enhanced_life, scenario.retirement_years)

        policy_mechanism = "11th Basic Plan - Accelerated Coal Phase-out"
        notes = (f"Enhanced Korea Power Plan: {enhanced_korea_scenario.name} | "
                 f"{enhanced_korea_scenario.policy_reference} | "
                 f"severity_penalty={scenario.dispatch_priority_penalty:.1%}")
    
    # Fallback to legacy Korea Power Plan
    elif korea_plan_scenario is not None and KOREA_POWER_PLAN_AVAILABLE:
        if current_year is not None:
            adjusted_cf = korea_plan_scenario.get_capacity_factor(current_year, baseline_cf)
        else:
            start_year = plant_params.get("cod_year", 2024)
            end_year = start_year + baseline_life
            total_cf = sum(
                korea_plan_scenario.get_capacity_factor(year, baseline_cf)
                for year in range(start_year, end_year)
            )
            adjusted_cf = total_cf / baseline_life
        
        adjusted_life = korea_plan_scenario.get_operating_years(
            plant_params.get("cod_year", 2024),
            baseline_life
        )
        
        carbon_price = carbon_trajectory.get(current_year or 2024, 35)
        policy_mechanism = "10th Basic Plan - Standard Coal Phase-down"
        notes = f"Legacy Korea Power Plan: {korea_plan_scenario.name} | {korea_plan_scenario.policy_reference}"
    
    # Traditional approach
    else:
        adjusted_cf = max(0.0, baseline_cf - scenario.dispatch_priority_penalty)
        adjusted_life = min(baseline_life, scenario.retirement_years)
        carbon_price = carbon_trajectory.get(current_year or 2024, 35)
        policy_mechanism = "Generic Transition Policy"
        notes = f"Generic transition: {scenario.name} | penalty={scenario.dispatch_priority_penalty:.1%}"
    
    # Calculate carbon cost burden
    carbon_cost_burden = KETSCarbonPricing.calculate_carbon_cost_burden(
        capacity_mw, adjusted_cf, heat_rate, carbon_content, carbon_price
    )
    
    # Calculate revenue loss
    assumed_power_price = 50  # USD/MWh — used only for ratio; cancels in pct calc
    baseline_revenue = capacity_mw * 8760 * baseline_cf * assumed_power_price
    adjusted_revenue = capacity_mw * 8760 * adjusted_cf * assumed_power_price
    
    revenue_loss_pct = ((baseline_revenue - adjusted_revenue) / baseline_revenue * 100) if baseline_revenue > 0 else 0
    
    # Add carbon cost impact to revenue loss
    baseline_annual_revenue = baseline_revenue
    adjusted_annual_revenue_with_carbon = adjusted_revenue - carbon_cost_burden
    total_revenue_loss_pct = ((baseline_annual_revenue - adjusted_annual_revenue_with_carbon) / baseline_annual_revenue * 100) if baseline_annual_revenue > 0 else 0
    
    # Calculate transition risk premium (higher for coal plants)
    base_premium = 0.02  # 2% base premium
    coal_risk_multiplier = min(3.0, total_revenue_loss_pct / 10.0)  # Up to 3x for high risk
    transition_risk_premium = base_premium * coal_risk_multiplier
    
    return EnhancedTransitionAdjustments(
        capacity_factor=adjusted_cf,
        operating_years=adjusted_life,
        carbon_cost_burden=carbon_cost_burden,
        revenue_loss_pct=total_revenue_loss_pct,
        transition_risk_premium=transition_risk_premium,
        policy_mechanism=policy_mechanism,
        carbon_price_trajectory=carbon_trajectory,
        notes=notes
    )


def calculate_enhanced_revenue_impact(
    adjustments: EnhancedTransitionAdjustments,
    plant_params: Dict[str, Any],
    power_price: float = 50.0,
    discount_rate: float = 0.08
) -> Dict[str, float]:
    """
    Calculate comprehensive revenue impact from enhanced transition adjustments.
    
    Args:
        adjustments: Enhanced transition adjustments
        plant_params: Plant parameters
        power_price: Electricity price ($/MWh)
        discount_rate: Discount rate for NPV calculation
        
    Returns:
        Dict with comprehensive revenue impact metrics
    """
    capacity_mw = float(plant_params.get("capacity_mw", 1000))
    baseline_cf = float(plant_params.get("capacity_factor", 0.5))
    start_year = plant_params.get("cod_year", 2024)
    end_year = start_year + adjustments.operating_years
    
    total_baseline_npv = 0.0
    total_adjusted_npv = 0.0
    total_carbon_costs_pv = 0.0
    
    for year in range(start_year, end_year):
        t = year - start_year
        
        # Baseline cash flow
        baseline_generation = capacity_mw * 8760 * baseline_cf
        baseline_revenue = baseline_generation * power_price
        baseline_pv = baseline_revenue / (1 + discount_rate) ** t
        total_baseline_npv += baseline_pv
        
        # Adjusted cash flow with carbon costs
        adjusted_generation = capacity_mw * 8760 * adjustments.capacity_factor
        adjusted_revenue = adjusted_generation * power_price
        
        # Carbon cost for this year
        carbon_price = adjustments.carbon_price_trajectory.get(year, 35)
        heat_rate = float(plant_params.get("heat_rate", 8.8))
        carbon_content = float(plant_params.get("carbon_content", 0.093))
        carbon_cost = KETSCarbonPricing.calculate_carbon_cost_burden(
            capacity_mw, adjustments.capacity_factor, heat_rate, carbon_content, carbon_price
        )
        
        adjusted_net_revenue = adjusted_revenue - carbon_cost
        adjusted_pv = adjusted_net_revenue / (1 + discount_rate) ** t
        total_adjusted_npv += adjusted_pv
        
        carbon_cost_pv = carbon_cost / (1 + discount_rate) ** t
        total_carbon_costs_pv += carbon_cost_pv
    
    npv_loss = total_baseline_npv - total_adjusted_npv
    
    return {
        'total_baseline_npv': total_baseline_npv,
        'total_adjusted_npv': total_adjusted_npv,
        'total_carbon_costs_pv': total_carbon_costs_pv,
        'npv_loss': npv_loss,
        'npv_loss_pct': (npv_loss / total_baseline_npv * 100) if total_baseline_npv > 0 else 0,
        'transition_risk_premium': adjustments.transition_risk_premium,
        'adjusted_wacc': 0.08 + adjustments.transition_risk_premium
    }
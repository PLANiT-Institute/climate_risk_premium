"""
Transition Risk Model.

Calculates financial impact of transition risks on coal power plants:
- Policy-driven dispatch reductions (Korea Power Plan)
- Early retirement risk

Based on Korea Basic Power Plan (전력수급기본계획).
See docs/sources/TRANSITION_ASSUMPTIONS.md for methodology.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional, List

from src.models.base import BaseRiskModel, RiskType, RiskResult
from .korea_power_plan import KoreaPowerPlan, KOREA_POWER_PLANS


@dataclass
class TransitionRiskComponents:
    """Breakdown of transition risk components."""
    dispatch_factor: float           # Capacity factor multiplier (0-1)
    coal_share: float                # Coal share in generation mix (%)
    retirement_penalty: float        # NPV reduction from early retirement
    effective_cf: float              # Actual capacity factor
    revenue_loss_pct: float          # Revenue loss percentage


class TransitionRiskModel(BaseRiskModel):
    """
    Transition Risk Model for coal power plants.

    Uses Korea Basic Power Plan (전력수급기본계획) to calculate
    the financial impact of policy-driven dispatch reductions.

    Example:
        >>> model = TransitionRiskModel()
        >>> model.set_power_plan("10th_basic_plan")
        >>> result = model.calculate(year=2030, baseline_cf=0.85)
    """

    def __init__(self, name: str = "TransitionRiskModel"):
        super().__init__(name)
        self._power_plan: Optional[KoreaPowerPlan] = None

        # Register all predefined plans
        for plan in KOREA_POWER_PLANS.values():
            self.register_scenario(plan)

    @property
    def risk_type(self) -> RiskType:
        return RiskType.TRANSITION

    def set_power_plan(self, name: str) -> None:
        """Set the active Korea Power Plan."""
        if name not in KOREA_POWER_PLANS:
            raise ValueError(f"Unknown power plan: {name}. Available: {list(KOREA_POWER_PLANS.keys())}")
        self._power_plan = KOREA_POWER_PLANS[name]

    def list_power_plans(self) -> Dict[str, str]:
        """List available Korea Power Plans with descriptions."""
        return {name: p.description for name, p in KOREA_POWER_PLANS.items()}

    def get_current_plan(self) -> Optional[KoreaPowerPlan]:
        """Get currently selected power plan."""
        return self._power_plan

    def calculate_components(
        self,
        year: int,
        baseline_cf: float = 0.85,
        cod_year: int = 2024,
        baseline_life: int = 40,
    ) -> TransitionRiskComponents:
        """
        Calculate detailed transition risk components.

        Args:
            year: Target calculation year
            baseline_cf: Baseline capacity factor
            cod_year: Commercial operation date year
            baseline_life: Original plant lifetime (years)

        Returns:
            TransitionRiskComponents with breakdown
        """
        # Dispatch factor
        dispatch_factor = 1.0
        coal_share = 32.4  # Default 2024 baseline
        if self._power_plan:
            dispatch_factor = self._power_plan.get_value(year)
            coal_share = self._power_plan.get_coal_share(year)

        # Effective capacity factor
        effective_cf = baseline_cf * dispatch_factor

        # Revenue loss percentage
        revenue_loss_pct = (1 - dispatch_factor) * 100

        # Early retirement penalty
        retirement_penalty = 0.0
        if self._power_plan and self._power_plan.retirement_year:
            remaining = self._power_plan.get_remaining_lifetime(cod_year, baseline_life)
            lost_years = baseline_life - remaining
            if lost_years > 0:
                retirement_penalty = lost_years / baseline_life

        return TransitionRiskComponents(
            dispatch_factor=dispatch_factor,
            coal_share=coal_share,
            retirement_penalty=retirement_penalty,
            effective_cf=effective_cf,
            revenue_loss_pct=revenue_loss_pct,
        )

    def calculate(
        self,
        year: int,
        scenario_name: str = None,
        damage_function_name: Optional[str] = None,
        **kwargs
    ) -> RiskResult:
        """
        Calculate transition risk for a given year.

        Args:
            year: Target year
            scenario_name: Power plan name (or use set_power_plan)
            damage_function_name: Not used for transition risk
            **kwargs: Additional parameters (baseline_cf, cod_year, etc.)

        Returns:
            RiskResult with transition risk value
        """
        if scenario_name and scenario_name in KOREA_POWER_PLANS:
            self.set_power_plan(scenario_name)

        baseline_cf = kwargs.get("baseline_cf", 0.85)

        components = self.calculate_components(
            year=year,
            baseline_cf=baseline_cf,
            cod_year=kwargs.get("cod_year", 2024),
            baseline_life=kwargs.get("baseline_life", 40),
        )

        # Risk value = revenue loss percentage
        risk_value = components.revenue_loss_pct

        sources = []
        plan_name = "none"
        if self._power_plan:
            sources.append(self._power_plan.source)
            plan_name = self._power_plan.name

        return RiskResult(
            risk_type=RiskType.TRANSITION,
            value=risk_value,
            unit="percent",
            year=year,
            scenario=plan_name,
            components={
                "dispatch_factor": components.dispatch_factor,
                "coal_share": components.coal_share,
                "retirement_penalty": components.retirement_penalty,
                "effective_cf": components.effective_cf,
            },
            sources=sources,
            notes=f"Baseline CF: {baseline_cf}, Plan: {plan_name}",
        )

    def calculate_trajectory(
        self,
        start_year: int,
        end_year: int,
        scenario_name: str = None,
        **kwargs
    ) -> Dict[int, RiskResult]:
        """
        Calculate transition risk trajectory over time.

        Args:
            start_year: First year
            end_year: Last year
            scenario_name: Power plan name
            **kwargs: Additional parameters

        Returns:
            Dict mapping year to RiskResult
        """
        if scenario_name and scenario_name in KOREA_POWER_PLANS:
            self.set_power_plan(scenario_name)

        return {
            year: self.calculate(year=year, **kwargs)
            for year in range(start_year, end_year + 1)
        }

    def get_dispatch_trajectory(self, start_year: int, end_year: int) -> Dict[int, float]:
        """Get dispatch factor trajectory for current power plan."""
        if not self._power_plan:
            return {year: 1.0 for year in range(start_year, end_year + 1)}
        return self._power_plan.get_trajectory(start_year, end_year)

    def get_coal_share_trajectory(self, start_year: int, end_year: int) -> Dict[int, float]:
        """Get coal share trajectory for current power plan."""
        if not self._power_plan:
            return {year: 32.4 for year in range(start_year, end_year + 1)}
        return {
            year: self._power_plan.get_coal_share(year)
            for year in range(start_year, end_year + 1)
        }

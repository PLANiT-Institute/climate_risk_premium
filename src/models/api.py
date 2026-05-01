"""
Climate Risk Model API.

Unified interface for selecting scenarios, damage functions, and running models.

Example:
    >>> from src.models.api import ClimateRiskAPI
    >>> api = ClimateRiskAPI()
    >>> api.list_available()  # See all options
    >>> api.configure(
    ...     climate_scenario="RCP8.5",
    ...     power_plan="10th_basic_plan",
    ...     damage_functions={"wildfire": "korea_forest_service"}
    ... )
    >>> results = api.calculate(year=2050)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional, List

# Import models
from .transition import TransitionRiskModel, KOREA_POWER_PLANS
from .physical import TemperatureModel
from .base import RiskResult


@dataclass
class CombinedRiskResult:
    """
    Combined result from transition and physical risk calculations.

    Attributes:
        year: Target year
        transition_result: Result from transition model (Korea Power Plan)
        physical_result: Result from physical model (climate hazards)
        total_risk_premium: Combined risk premium (bps)
        summary: Human-readable summary
    """
    year: int
    transition_result: RiskResult
    physical_result: RiskResult
    total_risk_premium: float  # basis points
    summary: str


class ClimateRiskAPI:
    """
    Unified API for climate risk modeling.

    Provides a single interface for:
    - Listing available power plans, scenarios, and damage functions
    - Configuring model components
    - Running risk calculations
    - Getting formatted results
    """

    def __init__(self):
        # Initialize models
        self._transition_model = TransitionRiskModel()
        self._physical_model = PhysicalRiskModel()

        # Initialize damage function registry
        self._damage_registry = DamageFunctionRegistry()
        self._register_default_damage_functions()

    def _register_default_damage_functions(self) -> None:
        """Register all available damage functions."""
        # Wildfire
        self._damage_registry.register(FWILinearFunction())
        self._damage_registry.register(FWIExponentialFunction())
        self._damage_registry.register(KoreaForestServiceFunction())

        # Flood
        self._damage_registry.register(DepthDamageFunction())
        self._damage_registry.register(DurationDamageFunction())

        # Tropical Cyclone
        self._damage_registry.register(WindSpeedPowerFunction())
        self._damage_registry.register(HollandWindFunction())

    # =========================================================================
    # LIST AVAILABLE OPTIONS
    # =========================================================================

    def list_available(self) -> Dict[str, Any]:
        """List all available configuration options."""
        return {
            "power_plans": self.list_power_plans(),
            "climate_scenarios": self.list_climate_scenarios(),
            "damage_functions": self.list_damage_functions(),
            "hazard_types": self.list_hazard_types(),
        }

    def list_power_plans(self) -> Dict[str, str]:
        """List available Korea Power Plans."""
        return {name: p.description for name, p in KOREA_POWER_PLANS.items()}

    def list_climate_scenarios(self) -> Dict[str, str]:
        """List available climate scenarios (RCP + SSP)."""
        result = {}
        for name, scenario in RCP_SCENARIOS.items():
            result[name] = scenario.description
        for name, scenario in SSP_SCENARIOS.items():
            result[name] = scenario.description
        return result

    def list_damage_functions(self) -> Dict[str, List[str]]:
        """List available damage functions by hazard type."""
        return self._damage_registry.list_by_hazard()

    def list_hazard_types(self) -> List[str]:
        """List available hazard types."""
        return [h.value for h in HazardType]

    # =========================================================================
    # CONFIGURATION
    # =========================================================================

    def configure(
        self,
        climate_scenario: str = "RCP8.5",
        power_plan: str = "10th_basic_plan",
        damage_functions: Dict[str, str] = None,
    ) -> None:
        """
        Configure the risk models.

        Args:
            climate_scenario: Climate scenario name (RCP or SSP)
            power_plan: Korea Power Plan name
            damage_functions: Dict mapping hazard type to function name

        Raises:
            ValueError: If any name is invalid
        """
        # Set climate scenario for physical model
        if climate_scenario in RCP_SCENARIOS:
            self._physical_model.set_rcp(climate_scenario)
        elif climate_scenario in SSP_SCENARIOS:
            # Map SSP to RCP for physical model
            rcp_map = {
                "SSP1-1.9": "RCP2.6",
                "SSP1-2.6": "RCP2.6",
                "SSP2-4.5": "RCP4.5",
                "SSP3-7.0": "RCP8.5",
                "SSP5-8.5": "RCP8.5",
            }
            self._physical_model.set_rcp(rcp_map.get(climate_scenario, "RCP8.5"))
        else:
            raise ValueError(f"Unknown climate scenario: {climate_scenario}")

        # Set Korea Power Plan for transition model
        self._transition_model.set_power_plan(power_plan)

        # Set damage functions
        if damage_functions:
            for hazard_type, func_name in damage_functions.items():
                func = self._damage_registry.get(func_name)
                if func:
                    hazard = HazardType(hazard_type)
                    self._physical_model.set_damage_function(hazard, func)

    # =========================================================================
    # CALCULATIONS
    # =========================================================================

    def calculate(
        self,
        year: int,
        baseline_cf: float = 0.85,
        **kwargs
    ) -> CombinedRiskResult:
        """
        Calculate combined climate risk for a given year.

        Args:
            year: Target year
            baseline_cf: Baseline capacity factor
            **kwargs: Additional parameters

        Returns:
            CombinedRiskResult with transition and physical risk
        """
        # Transition risk (dispatch reduction from Korea Power Plan)
        transition_result = self._transition_model.calculate(
            year=year,
            baseline_cf=baseline_cf,
            **kwargs
        )

        # Physical risk (climate hazards)
        physical_result = self._physical_model.calculate(year=year, **kwargs)

        # Combined risk premium
        # Transition: dispatch reduction -> revenue loss
        transition_premium = transition_result.value * 10  # % -> bps

        # Physical risk as capacity factor reduction
        physical_cf_impact = physical_result.value
        physical_premium = physical_cf_impact * 10000  # fraction -> bps

        total_premium = transition_premium + physical_premium

        summary = (
            f"Year {year}: "
            f"Transition {transition_premium:.0f}bps + "
            f"Physical {physical_premium:.0f}bps = "
            f"Total {total_premium:.0f}bps"
        )

        return CombinedRiskResult(
            year=year,
            transition_result=transition_result,
            physical_result=physical_result,
            total_risk_premium=total_premium,
            summary=summary,
        )

    def calculate_trajectory(
        self,
        start_year: int = 2024,
        end_year: int = 2050,
        **kwargs
    ) -> Dict[int, CombinedRiskResult]:
        """
        Calculate risk trajectory over time.

        Args:
            start_year: First year
            end_year: Last year
            **kwargs: Additional parameters

        Returns:
            Dict mapping year to CombinedRiskResult
        """
        return {
            year: self.calculate(year=year, **kwargs)
            for year in range(start_year, end_year + 1)
        }

    # =========================================================================
    # EXPORTS
    # =========================================================================

    def get_summary_table(
        self,
        years: List[int] = None
    ) -> Dict[str, Dict[int, float]]:
        """
        Get summary table of key metrics by year.

        Args:
            years: List of years (default: [2024, 2030, 2050])

        Returns:
            Dict with metrics by year
        """
        if years is None:
            years = [2024, 2030, 2050]

        table = {
            "dispatch_factor": {},
            "coal_share": {},
            "physical_risk": {},
            "total_premium": {},
        }

        dispatch_traj = self._transition_model.get_dispatch_trajectory(
            min(years), max(years)
        )
        coal_traj = self._transition_model.get_coal_share_trajectory(
            min(years), max(years)
        )
        physical_table = self._physical_model.get_summary_table(years)

        for year in years:
            table["dispatch_factor"][year] = dispatch_traj.get(year, 1.0)
            table["coal_share"][year] = coal_traj.get(year, 32.4)
            table["physical_risk"][year] = physical_table[year]["total_risk"]

            result = self.calculate(year=year)
            table["total_premium"][year] = result.total_risk_premium

        return table

"""
Climate Stress Testing Framework.

Implements regulatory-grade climate stress testing following:
- NGFS Climate Scenarios (2023)
- ECB Climate Stress Test methodology (2022)
- BOK Climate Risk Assessment framework
- Basel Committee climate stress principles

All scenario data loaded from CSV files.

Scenarios:
1. Orderly - Early, smooth transition
2. Disorderly - Late, abrupt transition
3. Hot House - No transition, high physical risk
4. Current Policies - Existing policies continue

Sources:
- NGFS (2023) "NGFS Climate Scenarios"
- ECB (2022) "Climate risk stress test"
- FSB (2022) "Supervisory and Regulatory Approaches"
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

from src.data.loaders import (
    load_ngfs_scenarios,
    load_korean_coal_fleet,
    NGFSScenario as NGFSScenarioData,
    CoalPlantData,
)


class ScenarioType(Enum):
    """NGFS scenario types."""
    ORDERLY = "orderly"
    DISORDERLY = "disorderly"
    HOT_HOUSE = "hot_house"
    CURRENT_POLICIES = "current_policies"
    NDC = "ndc"  # Nationally Determined Contributions


@dataclass
class StressScenario:
    """
    Climate stress test scenario definition.

    Based on NGFS scenarios with physical and transition risk components.
    """
    name: str
    scenario_type: ScenarioType
    description: str

    # Temperature pathway
    temp_2030_c: float                   # Temperature anomaly by 2030
    temp_2050_c: float                   # Temperature anomaly by 2050
    temp_2100_c: float                   # Temperature anomaly by 2100

    # Physical risk multipliers
    physical_risk_multiplier: float      # Multiplier vs baseline physical risk
    acute_risk_multiplier: float         # Acute hazard multiplier
    chronic_risk_multiplier: float       # Chronic hazard multiplier

    # Transition risk multipliers
    transition_risk_multiplier: float    # Overall transition risk
    carbon_price_2030_usd: float         # Carbon price in 2030
    carbon_price_2050_usd: float         # Carbon price in 2050

    # GDP impact
    gdp_impact_2030_pct: float           # GDP impact by 2030
    gdp_impact_2050_pct: float           # GDP impact by 2050

    # Probability weight
    probability: float = 0.25            # Scenario probability

    def get_physical_risk_factor(self, year: int) -> float:
        """Get physical risk factor for a year."""
        if year <= 2030:
            return 1.0 + (self.physical_risk_multiplier - 1.0) * (year - 2024) / 6
        elif year <= 2050:
            return self.physical_risk_multiplier
        else:
            # Assume continues to increase for hot house
            if self.scenario_type == ScenarioType.HOT_HOUSE:
                return self.physical_risk_multiplier * (1 + 0.02 * (year - 2050))
            return self.physical_risk_multiplier


def _load_ngfs_scenarios() -> Dict[ScenarioType, StressScenario]:
    """Load NGFS scenarios from CSV."""
    csv_data = load_ngfs_scenarios()
    scenarios = {}

    for scenario_type_str, data in csv_data.items():
        try:
            scenario_type = ScenarioType(scenario_type_str)
            scenarios[scenario_type] = StressScenario(
                name=data.name,
                scenario_type=scenario_type,
                description=data.description,
                temp_2030_c=data.temp_2030_c,
                temp_2050_c=data.temp_2050_c,
                temp_2100_c=data.temp_2100_c,
                physical_risk_multiplier=data.physical_risk_multiplier,
                acute_risk_multiplier=data.acute_risk_multiplier,
                chronic_risk_multiplier=data.chronic_risk_multiplier,
                transition_risk_multiplier=data.transition_risk_multiplier,
                carbon_price_2030_usd=data.carbon_price_2030_usd,
                carbon_price_2050_usd=data.carbon_price_2050_usd,
                gdp_impact_2030_pct=data.gdp_impact_2030_pct,
                gdp_impact_2050_pct=data.gdp_impact_2050_pct,
                probability=data.probability,
            )
        except (ValueError, KeyError):
            continue

    return scenarios


# Lazy-loading NGFS scenarios
class _NGFSScenariosDict(dict):
    """Lazy-loading dict for NGFS scenarios."""
    _loaded = False

    def _ensure_loaded(self):
        if not self._loaded:
            self.update(_load_ngfs_scenarios())
            self._loaded = True

    def get(self, key, default=None):
        self._ensure_loaded()
        return super().get(key, default)

    def __getitem__(self, key):
        self._ensure_loaded()
        return super().__getitem__(key)

    def keys(self):
        self._ensure_loaded()
        return super().keys()

    def values(self):
        self._ensure_loaded()
        return super().values()

    def items(self):
        self._ensure_loaded()
        return super().items()

    def __iter__(self):
        self._ensure_loaded()
        return super().__iter__()


NGFS_SCENARIOS = _NGFSScenariosDict()


@dataclass
class StressTestResult:
    """
    Stress test result for an asset or portfolio.
    """
    asset_id: str
    scenario: StressScenario
    year: int

    # Physical risk
    baseline_physical_risk_pct: float
    stressed_physical_risk_pct: float
    physical_risk_increase_pct: float

    # Financial impacts
    baseline_value_usd: float
    value_at_risk_usd: float
    expected_loss_usd: float
    var_95_usd: float
    var_99_usd: float

    # Credit impacts
    baseline_spread_bps: int
    stressed_spread_bps: int
    rating_notches_change: int

    # Generation impacts (for power assets)
    generation_loss_twh: float = 0.0
    revenue_loss_usd: float = 0.0

    @property
    def total_impact_usd(self) -> float:
        """Total financial impact."""
        return self.expected_loss_usd + self.revenue_loss_usd

    @property
    def impact_pct(self) -> float:
        """Impact as % of baseline value."""
        if self.baseline_value_usd > 0:
            return self.total_impact_usd / self.baseline_value_usd * 100
        return 0.0


class ClimateStressTest:
    """
    Climate stress testing engine.

    Runs stress tests across NGFS scenarios.
    Uses PhysicalRiskModel for baseline physical risk instead of hardcoded values.
    """

    def __init__(
        self,
        scenarios: Dict[ScenarioType, StressScenario] = None,
    ):
        self.scenarios = scenarios or dict(NGFS_SCENARIOS)
        self._physical_risk_model = None

    def set_physical_risk_model(self, model) -> None:
        """Set the physical risk model for dynamic risk calculation."""
        self._physical_risk_model = model

    def get_baseline_physical_risk(
        self,
        asset_id: str,
        year: int,
        scenario: str = "RCP8.5",
    ) -> float:
        """
        Get baseline physical risk for an asset.

        If PhysicalRiskModel is set, uses it. Otherwise falls back to CSV data.
        """
        if self._physical_risk_model is not None:
            # Use the physical risk model
            result = self._physical_risk_model.calculate(year=year, scenario_name=scenario)
            return result.value * 100  # Convert to percentage

        # Fallback: calculate from hazard baselines
        from src.data.loaders import load_hazard_baselines, get_climate_factor

        baselines = load_hazard_baselines()
        total_risk = 0.0

        for hazard_type, baseline in baselines.items():
            climate_factor = get_climate_factor(hazard_type, year, scenario)
            hazard_risk = baseline.total_annual_impact * climate_factor
            total_risk += hazard_risk

        return total_risk * 100  # Convert to percentage

    def run_asset_stress_test(
        self,
        asset_id: str,
        baseline_value_usd: float,
        baseline_physical_risk_pct: float = None,
        baseline_spread_bps: int = 100,
        scenario_type: ScenarioType = ScenarioType.HOT_HOUSE,
        year: int = 2050,
        annual_revenue_usd: float = 0.0,
        rcp: str = "RCP8.5",
    ) -> StressTestResult:
        """
        Run stress test on a single asset.

        Args:
            asset_id: Asset identifier
            baseline_value_usd: Asset value
            baseline_physical_risk_pct: Baseline physical risk (if None, calculated dynamically)
            baseline_spread_bps: Baseline credit spread
            scenario_type: NGFS scenario
            year: Target year
            annual_revenue_usd: Annual revenue for revenue impact
            rcp: RCP scenario for physical risk calculation

        Returns:
            StressTestResult
        """
        scenario = self.scenarios[scenario_type]

        # Get baseline physical risk dynamically if not provided
        if baseline_physical_risk_pct is None:
            baseline_physical_risk_pct = self.get_baseline_physical_risk(asset_id, 2024, rcp)

        # Apply physical risk multiplier
        physical_factor = scenario.get_physical_risk_factor(year)
        stressed_risk = baseline_physical_risk_pct * physical_factor

        # Calculate VaR
        # Using simplified approach: VaR = stress factor × baseline value × risk
        expected_loss = baseline_value_usd * stressed_risk / 100
        var_95 = expected_loss * 1.65  # Normal approximation
        var_99 = expected_loss * 2.33

        # Credit impact
        # Rule: +10bps per 1% physical risk increase
        risk_increase = stressed_risk - baseline_physical_risk_pct
        spread_increase = int(risk_increase * 10)
        stressed_spread = baseline_spread_bps + spread_increase

        # Rating notches (rough: 50bps = 1 notch)
        notches = int(spread_increase / 50)

        # Revenue loss
        revenue_loss = annual_revenue_usd * stressed_risk / 100 if annual_revenue_usd > 0 else 0.0

        return StressTestResult(
            asset_id=asset_id,
            scenario=scenario,
            year=year,
            baseline_physical_risk_pct=baseline_physical_risk_pct,
            stressed_physical_risk_pct=stressed_risk,
            physical_risk_increase_pct=risk_increase,
            baseline_value_usd=baseline_value_usd,
            value_at_risk_usd=var_95,
            expected_loss_usd=expected_loss,
            var_95_usd=var_95,
            var_99_usd=var_99,
            baseline_spread_bps=baseline_spread_bps,
            stressed_spread_bps=stressed_spread,
            rating_notches_change=notches,
            revenue_loss_usd=revenue_loss,
        )

    def run_portfolio_stress_test(
        self,
        assets: List[Dict],
        scenario_type: ScenarioType = ScenarioType.HOT_HOUSE,
        year: int = 2050,
    ) -> Dict[str, StressTestResult]:
        """Run stress test on portfolio."""
        results = {}
        for asset in assets:
            result = self.run_asset_stress_test(
                asset_id=asset["asset_id"],
                baseline_value_usd=asset["value_usd"],
                baseline_physical_risk_pct=asset.get("physical_risk_pct"),
                baseline_spread_bps=asset.get("spread_bps", 100),
                scenario_type=scenario_type,
                year=year,
                annual_revenue_usd=asset.get("revenue_usd", 0),
            )
            results[asset["asset_id"]] = result
        return results

    def run_all_scenarios(
        self,
        asset_id: str,
        baseline_value_usd: float,
        baseline_physical_risk_pct: float = None,
        year: int = 2050,
    ) -> Dict[ScenarioType, StressTestResult]:
        """Run all NGFS scenarios for an asset."""
        results = {}
        for scenario_type in self.scenarios.keys():
            results[scenario_type] = self.run_asset_stress_test(
                asset_id=asset_id,
                baseline_value_usd=baseline_value_usd,
                baseline_physical_risk_pct=baseline_physical_risk_pct,
                scenario_type=scenario_type,
                year=year,
            )
        return results

    def get_probability_weighted_loss(
        self,
        all_scenario_results: Dict[ScenarioType, StressTestResult],
    ) -> float:
        """Calculate probability-weighted expected loss."""
        total = 0.0
        for scenario_type, result in all_scenario_results.items():
            scenario = self.scenarios[scenario_type]
            total += result.expected_loss_usd * scenario.probability
        return total


def run_korean_coal_stress_test(
    year: int = 2050,
    scenario_type: ScenarioType = ScenarioType.HOT_HOUSE,
    physical_risk_model=None,
) -> Dict[str, any]:
    """
    Run stress test on Korean coal fleet.

    Uses data from CSV files and optionally a PhysicalRiskModel for
    dynamic physical risk calculation.
    """
    coal_fleet = load_korean_coal_fleet()

    stress_test = ClimateStressTest()
    if physical_risk_model is not None:
        stress_test.set_physical_risk_model(physical_risk_model)

    results = {}
    total_value = 0
    total_expected_loss = 0
    total_var_95 = 0

    for plant_id, plant_data in coal_fleet.items():
        result = stress_test.run_asset_stress_test(
            asset_id=plant_id,
            baseline_value_usd=plant_data.replacement_cost_usd,
            baseline_physical_risk_pct=None,  # Calculate dynamically
            baseline_spread_bps=100,
            scenario_type=scenario_type,
            year=year,
            annual_revenue_usd=plant_data.annual_revenue_usd,
        )
        results[plant_id] = result
        total_value += plant_data.replacement_cost_usd
        total_expected_loss += result.expected_loss_usd
        total_var_95 += result.var_95_usd

    return {
        "scenario": scenario_type.value,
        "year": year,
        "num_assets": len(results),
        "total_portfolio_value_usd": total_value,
        "total_expected_loss_usd": total_expected_loss,
        "portfolio_var_95_usd": total_var_95,
        "portfolio_loss_pct": (total_expected_loss / total_value * 100) if total_value > 0 else 0,
        "by_asset": {k: v.impact_pct for k, v in results.items()},
    }

"""
Carbon pricing scenarios for Korea ETS and global benchmarks.

Implements realistic carbon price trajectories based on:
1. Korea ETS (K-ETS) historical and projected prices
2. IEA World Energy Outlook scenarios
3. NGFS climate scenarios for financial risk assessment

References:
- Korea Exchange (KRX) ETS market data
- IEA WEO 2023 carbon price assumptions
- NGFS Climate Scenarios (2023)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum
import numpy as np


class CarbonPriceScenario(Enum):
    """Standard carbon price scenario types."""
    CURRENT_POLICY = "current_policy"           # K-ETS as-is, modest growth
    NDC_ALIGNED = "ndc_aligned"                 # Korea 2030 NDC target
    NET_ZERO_2050 = "net_zero_2050"             # Carbon neutrality pathway
    DELAYED_ACTION = "delayed_action"           # Policy delays then rapid catch-up
    HIGH_AMBITION = "high_ambition"             # 1.5°C aligned (aggressive)
    NO_POLICY = "no_policy"                     # Hypothetical baseline (for comparison only)


@dataclass
class CarbonPricingScenario:
    """
    Carbon pricing trajectory with full flexibility.

    Attributes:
        name: Scenario identifier
        price_trajectory: Dict mapping year -> price in USD/tCO2
        description: Scenario description
        source: Data source reference
        includes_ets: Whether this includes ETS costs
        includes_carbon_tax: Whether this includes carbon tax
    """
    name: str
    price_trajectory: Dict[int, float]  # year -> USD/tCO2
    description: str = ""
    source: str = ""
    includes_ets: bool = True
    includes_carbon_tax: bool = False

    def get_carbon_price(self, year: int) -> float:
        """
        Get carbon price for given year with interpolation.

        Args:
            year: Target year

        Returns:
            Carbon price in USD/tCO2
        """
        if not self.price_trajectory:
            return 0.0

        years = sorted(self.price_trajectory.keys())

        # Before first year
        if year <= years[0]:
            return self.price_trajectory[years[0]]

        # After last year - extrapolate with last growth rate
        if year >= years[-1]:
            if len(years) >= 2:
                # Use growth rate from last two points
                y1, y2 = years[-2], years[-1]
                p1, p2 = self.price_trajectory[y1], self.price_trajectory[y2]
                if p1 > 0:
                    annual_growth = (p2 / p1) ** (1 / (y2 - y1)) - 1
                    years_beyond = year - years[-1]
                    return p2 * (1 + annual_growth) ** years_beyond
            return self.price_trajectory[years[-1]]

        # Interpolate between years
        for i in range(len(years) - 1):
            if years[i] <= year <= years[i + 1]:
                y0, y1 = years[i], years[i + 1]
                p0, p1 = self.price_trajectory[y0], self.price_trajectory[y1]
                weight = (year - y0) / (y1 - y0)
                return p0 + weight * (p1 - p0)

        return self.price_trajectory[years[-1]]

    def get_trajectory_array(self, start_year: int, end_year: int) -> np.ndarray:
        """Get carbon prices as numpy array for vectorized calculations."""
        return np.array([self.get_carbon_price(y) for y in range(start_year, end_year + 1)])

    def to_dict(self) -> Dict:
        """Export scenario to dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'source': self.source,
            'price_trajectory': self.price_trajectory,
            'includes_ets': self.includes_ets,
            'includes_carbon_tax': self.includes_carbon_tax,
        }


# =============================================================================
# KOREA ETS SCENARIOS
# =============================================================================

def create_korea_ets_current_policy() -> CarbonPricingScenario:
    """
    Korea ETS current policy trajectory (CONSERVATIVE baseline).

    Based on K-ETS historical prices with conservative growth assumptions:
    - Current prices ~₩10,000-12,000 ($8/tCO2)
    - Assumes policy inertia and market oversupply continues
    - Gradual increase but not aggressive tightening
    - Represents "business as usual" without major policy changes

    This is more conservative than government targets to serve as
    a realistic baseline for comparison.

    Sources:
    - KRX ETS market data (current)
    - Conservative extrapolation (not government targets)
    """
    # Conservative K-ETS trajectory (USD/tCO2)
    # Much lower than NDC-aligned scenarios
    trajectory = {
        2024: 8,      # Current ~₩10,000-12,000
        2025: 8,      # Stable - market oversupply continues
        2026: 10,     # Minor increase
        2027: 12,     #
        2028: 14,     #
        2029: 16,     #
        2030: 20,     # Modest increase (below NDC requirement)
        2032: 25,     #
        2035: 35,     # Gradual growth
        2040: 50,     # Conservative mid-century
        2045: 60,     #
        2050: 75,     # Well below net-zero requirements
    }

    return CarbonPricingScenario(
        name="korea_ets_current_policy",
        price_trajectory=trajectory,
        description="Korea ETS conservative baseline (policy inertia, no major changes)",
        source="KRX ETS data + conservative extrapolation",
        includes_ets=True,
        includes_carbon_tax=False,
    )


def create_korea_ets_ndc_aligned() -> CarbonPricingScenario:
    """
    Korea ETS trajectory aligned with enhanced 2030 NDC (40% reduction).

    Assumes stronger policy action to meet NDC:
    - Faster cap reductions
    - Reduced free allocation
    - Higher auction share
    - Potential carbon tax supplement
    """
    trajectory = {
        2024: 8,      # Current
        2025: 15,     # Policy signal effect
        2026: 25,     # Cap reduction accelerates
        2027: 35,     #
        2028: 48,     # Significant tightening
        2029: 62,     # Pre-NDC push
        2030: 80,     # NDC target year - high price signal needed
        2032: 100,    # Maintained high price
        2035: 130,    # Continued increase
        2040: 180,    # Strong trajectory to net-zero
        2045: 230,    #
        2050: 280,    # Carbon neutrality
    }

    return CarbonPricingScenario(
        name="korea_ets_ndc_aligned",
        price_trajectory=trajectory,
        description="Korea ETS with enhanced ambition to meet 40% NDC reduction by 2030",
        source="Based on IEA analysis of NDC-consistent carbon prices",
        includes_ets=True,
        includes_carbon_tax=False,
    )


def create_korea_net_zero_2050() -> CarbonPricingScenario:
    """
    Carbon price trajectory for Korea's 2050 Carbon Neutrality.

    Based on:
    - Korea's Carbon Neutrality Scenario (2021)
    - NGFS Net Zero 2050 scenario
    - IEA WEO 2023 NZE scenario adjusted for Korea
    """
    trajectory = {
        2024: 8,      # Current
        2025: 20,     # Strong early signal
        2026: 35,     # Rapid increase
        2027: 50,     #
        2028: 68,     #
        2029: 88,     #
        2030: 110,    # High price for NDC
        2032: 140,    # Continued acceleration
        2035: 190,    # IEA NZE benchmark ~$140-200
        2040: 260,    # High sustained price
        2045: 350,    # Near-zero emissions needed
        2050: 450,    # Full carbon neutrality
    }

    return CarbonPricingScenario(
        name="korea_net_zero_2050",
        price_trajectory=trajectory,
        description="Aggressive carbon pricing for Korea 2050 Carbon Neutrality (aligned with IEA NZE)",
        source="Korea Carbon Neutrality Scenario + IEA WEO 2023 NZE",
        includes_ets=True,
        includes_carbon_tax=True,  # Likely needs tax supplement
    )


def create_delayed_action_scenario() -> CarbonPricingScenario:
    """
    Delayed policy action followed by rapid catch-up.

    Represents scenario where:
    - Political/economic resistance delays action until late 2020s
    - Sudden policy shift requires aggressive catch-up
    - Higher long-term prices to compensate for lost time

    Based on NGFS "Delayed Transition" scenario.
    """
    trajectory = {
        2024: 8,      # Current
        2025: 8,      # No change - policy paralysis
        2026: 10,     # Minimal increase
        2027: 12,     #
        2028: 15,     # Still delayed
        2029: 25,     # Policy shift begins
        2030: 50,     # Catch-up acceleration
        2032: 90,     # Rapid increase
        2035: 160,    # Aggressive catch-up
        2040: 280,    # Higher than orderly scenario
        2045: 400,    #
        2050: 500,    # Very high to achieve net-zero despite late start
    }

    return CarbonPricingScenario(
        name="delayed_action",
        price_trajectory=trajectory,
        description="Delayed policy action until 2029 then aggressive catch-up to net-zero",
        source="Based on NGFS Delayed Transition scenario",
        includes_ets=True,
        includes_carbon_tax=True,
    )


def create_high_ambition_scenario() -> CarbonPricingScenario:
    """
    High ambition 1.5°C aligned scenario.

    Based on:
    - IPCC 1.5°C pathways
    - IEA WEO 2023 NZE scenario (high end)
    - Academic estimates for 1.5°C consistency
    """
    trajectory = {
        2024: 15,     # Immediate increase from current
        2025: 40,     # Strong early signal
        2026: 65,     # Rapid scaling
        2027: 90,     #
        2028: 120,    #
        2029: 150,    #
        2030: 185,    # Very high for 1.5°C
        2032: 230,    #
        2035: 320,    # Peak carbon price period
        2040: 420,    #
        2045: 520,    #
        2050: 600,    # Very high to ensure 1.5°C
    }

    return CarbonPricingScenario(
        name="high_ambition_1.5c",
        price_trajectory=trajectory,
        description="1.5°C aligned carbon pricing (IPCC high ambition pathway)",
        source="IPCC SR1.5 + IEA WEO 2023 NZE high estimate",
        includes_ets=True,
        includes_carbon_tax=True,
    )


def create_no_policy_baseline() -> CarbonPricingScenario:
    """
    Hypothetical no-policy baseline.

    WARNING: This is for comparison purposes only.
    Korea already has K-ETS, so this represents a counterfactual.
    """
    trajectory = {year: 0.0 for year in range(2024, 2061)}

    return CarbonPricingScenario(
        name="no_policy_baseline",
        price_trajectory=trajectory,
        description="Hypothetical no carbon pricing (COUNTERFACTUAL - for comparison only)",
        source="Hypothetical baseline",
        includes_ets=False,
        includes_carbon_tax=False,
    )


# =============================================================================
# GLOBAL BENCHMARK SCENARIOS (for comparison)
# =============================================================================

def create_iea_aps_scenario() -> CarbonPricingScenario:
    """
    IEA Announced Pledges Scenario (APS) for advanced economies.

    From IEA World Energy Outlook 2023.
    """
    trajectory = {
        2024: 25,     # Current average for advanced economies
        2025: 35,
        2030: 90,     # APS 2030
        2035: 125,
        2040: 160,    # APS 2040
        2045: 195,
        2050: 230,    # APS 2050
    }

    return CarbonPricingScenario(
        name="iea_aps_advanced",
        price_trajectory=trajectory,
        description="IEA Announced Pledges Scenario for advanced economies",
        source="IEA World Energy Outlook 2023",
    )


def create_eu_ets_benchmark() -> CarbonPricingScenario:
    """
    EU ETS trajectory for comparison.

    EU ETS is the world's largest carbon market and often used as benchmark.
    """
    trajectory = {
        2024: 70,     # Current EU ETS ~€65 ≈ $70
        2025: 80,
        2026: 90,
        2027: 100,
        2028: 110,
        2029: 120,
        2030: 140,    # EU Fit for 55 target
        2035: 180,
        2040: 220,
        2045: 280,
        2050: 350,    # EU carbon neutrality
    }

    return CarbonPricingScenario(
        name="eu_ets_benchmark",
        price_trajectory=trajectory,
        description="EU ETS trajectory for international comparison",
        source="EU ETS market data + EC projections",
    )


# =============================================================================
# SCENARIO LOADER
# =============================================================================

def get_all_carbon_scenarios() -> Dict[str, CarbonPricingScenario]:
    """Load all predefined carbon pricing scenarios."""
    return {
        # Korea scenarios
        "korea_ets_current": create_korea_ets_current_policy(),
        "korea_ets_ndc": create_korea_ets_ndc_aligned(),
        "korea_net_zero": create_korea_net_zero_2050(),
        "delayed_action": create_delayed_action_scenario(),
        "high_ambition": create_high_ambition_scenario(),
        "no_policy": create_no_policy_baseline(),
        # Global benchmarks
        "iea_aps": create_iea_aps_scenario(),
        "eu_ets": create_eu_ets_benchmark(),
    }


def get_carbon_scenario(name: str) -> CarbonPricingScenario:
    """Get a specific carbon pricing scenario by name."""
    scenarios = get_all_carbon_scenarios()
    if name not in scenarios:
        available = list(scenarios.keys())
        raise ValueError(f"Unknown carbon scenario '{name}'. Available: {available}")
    return scenarios[name]


def load_carbon_scenarios_from_csv(file_path: str) -> Dict[str, CarbonPricingScenario]:
    """
    Load carbon pricing scenarios from CSV file.

    Expected format:
        scenario,year,price_usd,description,source
        korea_ets_current,2024,8,Current K-ETS,KRX
        korea_ets_current,2025,10,...
    """
    import pandas as pd

    df = pd.read_csv(file_path)

    scenarios = {}
    for scenario_name in df['scenario'].unique():
        scenario_df = df[df['scenario'] == scenario_name]

        trajectory = dict(zip(
            scenario_df['year'].astype(int),
            scenario_df['price_usd'].astype(float)
        ))

        # Get metadata from first row
        first_row = scenario_df.iloc[0]

        scenarios[scenario_name] = CarbonPricingScenario(
            name=scenario_name,
            price_trajectory=trajectory,
            description=str(first_row.get('description', '')),
            source=str(first_row.get('source', '')),
        )

    return scenarios


# =============================================================================
# ANALYSIS UTILITIES
# =============================================================================

def compare_scenarios(
    scenarios: Dict[str, CarbonPricingScenario],
    years: list = None
) -> Dict[str, Dict[int, float]]:
    """
    Compare carbon prices across scenarios for given years.

    Returns dict of scenario name -> {year: price}
    """
    if years is None:
        years = [2024, 2025, 2030, 2035, 2040, 2045, 2050]

    comparison = {}
    for name, scenario in scenarios.items():
        comparison[name] = {year: scenario.get_carbon_price(year) for year in years}

    return comparison


def calculate_cumulative_carbon_cost(
    scenario: CarbonPricingScenario,
    annual_emissions_tco2: float,
    start_year: int = 2024,
    end_year: int = 2050,
    discount_rate: float = 0.08
) -> Dict[str, float]:
    """
    Calculate cumulative carbon costs under a scenario.

    Args:
        scenario: Carbon pricing scenario
        annual_emissions_tco2: Annual CO2 emissions (tonnes)
        start_year: Start year
        end_year: End year
        discount_rate: Discount rate for NPV

    Returns:
        Dict with undiscounted and discounted (NPV) costs
    """
    total_undiscounted = 0.0
    total_npv = 0.0

    for year in range(start_year, end_year + 1):
        t = year - start_year
        carbon_price = scenario.get_carbon_price(year)
        annual_cost = annual_emissions_tco2 * carbon_price

        total_undiscounted += annual_cost
        total_npv += annual_cost / (1 + discount_rate) ** t

    return {
        'cumulative_undiscounted': total_undiscounted,
        'cumulative_npv': total_npv,
        'avg_annual_cost': total_undiscounted / (end_year - start_year + 1),
    }

"""
Factory for loading enhanced Korea Power Plan scenarios with 11th Basic Plan integration.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from src.scenarios.enhanced_korea_power_plan import (
    EnhancedKoreaPowerPlan,
    EnhancedKoreaPowerPlanScenario,
    PowerMixTarget,
    NuclearExpansionPlan,
    RenewableExpansionTarget,
    KETSCarbonPrice,
    CoalPhaseoutSchedule
)


@dataclass
class GWPowerMixTarget:
    """
    Power mix target using absolute GW capacity values (from CSV).
    This is used by the loader to store raw CSV data before converting
    to the percentage-based PowerMixTarget used by EnhancedKoreaPowerPlan.
    """
    year: int
    coal_gw: float
    lng_gw: float
    nuclear_gw: float
    solar_gw: float
    wind_gw: float
    hydro_gw: float
    hydrogen_ammonia_gw: float
    pumped_storage_gw: float
    carbon_free_percentage: float

    @property
    def total_gw(self) -> float:
        return (self.coal_gw + self.lng_gw + self.nuclear_gw +
                self.solar_gw + self.wind_gw + self.hydro_gw +
                self.hydrogen_ammonia_gw + self.pumped_storage_gw)

    def to_power_mix_target(self) -> PowerMixTarget:
        """Convert GW capacity to generation-share-based PowerMixTarget.

        Applies typical capacity factors per source to approximate generation (GWh),
        then computes generation share percentages.  This aligns with the hardcoded
        generation-share targets in create_enhanced_11th_plan().
        """
        # Approximate generation using typical capacity factors
        coal_gen = self.coal_gw * 0.65
        lng_gen = self.lng_gw * 0.45
        nuclear_gen = self.nuclear_gw * 0.85
        solar_gen = self.solar_gw * 0.15
        wind_gen = self.wind_gw * 0.25
        hydro_gen = self.hydro_gw * 0.30
        h2_gen = self.hydrogen_ammonia_gw * 0.50
        ps_gen = self.pumped_storage_gw * 0.10

        total_gen = (coal_gen + lng_gen + nuclear_gen + solar_gen +
                     wind_gen + hydro_gen + h2_gen + ps_gen)
        if total_gen <= 0:
            total_gen = 1.0

        # Estimate total demand TWh
        total_demand_twh = total_gen * 8760 / 1000

        return PowerMixTarget(
            year=self.year,
            coal_share=(coal_gen / total_gen) * 100,
            nuclear_share=(nuclear_gen / total_gen) * 100,
            renewable_share=((solar_gen + wind_gen + hydro_gen) / total_gen) * 100,
            gas_share=(lng_gen / total_gen) * 100,
            hydrogen_share=((h2_gen + ps_gen) / total_gen) * 100,
            total_demand_twh=total_demand_twh,
        )


@dataclass
class LoadedScenario:
    """
    Wrapper that holds both GW-based data from CSV and the
    EnhancedKoreaPowerPlan object for the model pipeline.
    """
    name: str
    plan: EnhancedKoreaPowerPlan
    gw_targets: List[GWPowerMixTarget] = field(default_factory=list)

    # Delegate all methods to the plan
    @property
    def power_mix_targets(self):
        return self.plan.power_mix_targets

    @property
    def nuclear_expansion(self):
        return self.plan.nuclear_plan

    @property
    def renewable_targets(self):
        return self.plan.renewable_targets

    @property
    def coal_phaseout(self):
        return self.plan.coal_schedule

    @property
    def policy_reference(self):
        return self.plan.policy_reference

    def get_power_mix(self, year: int) -> Optional[GWPowerMixTarget]:
        """Get GW-based power mix target for a year (interpolated)."""
        # Exact match
        for t in self.gw_targets:
            if t.year == year:
                return t
        # Interpolate
        if len(self.gw_targets) < 2:
            return None
        years = [t.year for t in self.gw_targets]
        if year < min(years) or year > max(years):
            return None
        for i in range(len(years) - 1):
            if years[i] <= year <= years[i + 1]:
                t1, t2 = self.gw_targets[i], self.gw_targets[i + 1]
                w = (year - years[i]) / (years[i + 1] - years[i])
                return GWPowerMixTarget(
                    year=year,
                    coal_gw=t1.coal_gw + w * (t2.coal_gw - t1.coal_gw),
                    lng_gw=t1.lng_gw + w * (t2.lng_gw - t1.lng_gw),
                    nuclear_gw=t1.nuclear_gw + w * (t2.nuclear_gw - t1.nuclear_gw),
                    solar_gw=t1.solar_gw + w * (t2.solar_gw - t1.solar_gw),
                    wind_gw=t1.wind_gw + w * (t2.wind_gw - t1.wind_gw),
                    hydro_gw=t1.hydro_gw + w * (t2.hydro_gw - t1.hydro_gw),
                    hydrogen_ammonia_gw=t1.hydrogen_ammonia_gw + w * (t2.hydrogen_ammonia_gw - t1.hydrogen_ammonia_gw),
                    pumped_storage_gw=t1.pumped_storage_gw + w * (t2.pumped_storage_gw - t1.pumped_storage_gw),
                    carbon_free_percentage=t1.carbon_free_percentage + w * (t2.carbon_free_percentage - t1.carbon_free_percentage),
                )
        return None

    def get_capacity_factor(self, year: int, baseline_cf: float = 0.50) -> float:
        return self.plan.get_capacity_factor(year, baseline_cf)

    def get_carbon_price(self, year: int):
        return self.plan.get_carbon_price(year)

    def get_operating_years(self, cod_year: int, baseline_life: int) -> int:
        """Estimate operating years based on coal phase-out schedule."""
        phase_out_year = self.plan.coal_schedule.complete_phase_out_year
        remaining = phase_out_year - cod_year
        return min(baseline_life, max(1, remaining))

    def calculate_revenue_impact(self, capacity_mw: float, power_price: float,
                                  start_year: int, end_year: int,
                                  baseline_cf: float) -> Dict:
        """Calculate revenue impact over analysis period."""
        return self.plan.calculate_compound_transition_impact(
            plant_params={
                'capacity_mw': capacity_mw,
                'baseline_cf': baseline_cf,
                'emission_factor': 0.82,
                'capex_usd': capacity_mw * 2_333_333,  # ~$2.33M/MW for coal
            },
            electricity_price_trajectory={y: power_price for y in range(start_year, end_year + 1)},
            start_year=start_year,
            end_year=min(end_year, 2045),
        )


def load_enhanced_korea_power_plan_scenarios(
    file_path: str
) -> Dict[str, LoadedScenario]:
    """
    Load enhanced Korea power plan scenarios from CSV file.

    Expected CSV format:
        year,power_plan,total_coal_gw,total_lng_gw,nuclear_gw,solar_gw,wind_gw,
        hydro_gw,hydrogen_ammonia_gw,pumped_storage_gw,carbon_free_pct,
        policy_reference,scenario_type,notes

    Args:
        file_path: Path to enhanced_korea_power_plan.csv

    Returns:
        Dict of scenario name -> LoadedScenario
    """
    df = pd.read_csv(file_path)

    scenarios = {}

    # Main 11th Basic Plan scenario
    plan_11_df = df[df['scenario_type'].isin(['official_11th_plan', 'historical'])].copy()

    if not plan_11_df.empty:
        # Build GW-based targets from CSV
        gw_targets = []
        for _, row in plan_11_df.iterrows():
            target = GWPowerMixTarget(
                year=int(row['year']),
                coal_gw=float(row['total_coal_gw']),
                lng_gw=float(row['total_lng_gw']),
                nuclear_gw=float(row['nuclear_gw']),
                solar_gw=float(row['solar_gw']),
                wind_gw=float(row['wind_gw']),
                hydro_gw=float(row['hydro_gw']),
                hydrogen_ammonia_gw=float(row['hydrogen_ammonia_gw']),
                pumped_storage_gw=float(row['pumped_storage_gw']),
                carbon_free_percentage=float(row['carbon_free_pct'])
            )
            gw_targets.append(target)

        # Convert to percentage-based PowerMixTarget for the plan
        power_mix_targets = [t.to_power_mix_target() for t in gw_targets]

        # Renewable expansion targets (cumulative installed capacity, GW)
        # Source: 11차 전기본 공식 발표 (산업통상자원부 고시 제2025-169호)
        renewable_targets = [
            RenewableExpansionTarget(
                year=2024, solar_capacity_gw=25.0, wind_capacity_gw=1.7,
                total_renewable_gw=26.7, annual_addition_gw=3.0
            ),
            RenewableExpansionTarget(
                year=2030, solar_capacity_gw=39.0, wind_capacity_gw=10.0,
                total_renewable_gw=49.0, annual_addition_gw=5.5
            ),
            RenewableExpansionTarget(
                year=2038, solar_capacity_gw=77.2, wind_capacity_gw=40.7,
                total_renewable_gw=117.9, annual_addition_gw=8.5,
                grid_stability_requirement=21.5,
                storage_requirement_gw=35.0
            ),
        ]

        # Nuclear expansion plan (2 large units + 1 SMR)
        nuclear_plan = NuclearExpansionPlan(
            phase={
                2028: {'total_capacity': 25.7, 'addition': 1.0},
                2032: {'total_capacity': 28.1, 'addition': 2.4},
                2035: {'total_capacity': 30.1, 'addition': 2.0},
            }
        )

        # Coal phase-out schedule (42% faster than 10th Plan)
        coal_schedule = CoalPhaseoutSchedule()

        # Carbon price trajectory from K-ETS
        # Source: KRX 배출권시장 (ets.krx.co.kr), 2024 avg ~9,465 KRW/ton ≈ $7-8/ton
        carbon_prices = KETSCarbonPrice.create_price_trajectory()

        plan = EnhancedKoreaPowerPlan(
            name='official_11th_plan',
            version=11,
            effective_date=2025,
            policy_reference='제11차 전력수급기본계획 (2024-2038), 산업통상자원부 공고 제2025-169호',
            description='Official 11th Basic Plan with accelerated coal phase-out, renewable expansion, and nuclear optimization',
            power_mix_targets=power_mix_targets,
            renewable_targets=renewable_targets,
            nuclear_plan=nuclear_plan,
            coal_schedule=coal_schedule,
            carbon_prices=carbon_prices,
        )

        scenarios['official_11th_plan'] = LoadedScenario(
            name='official_11th_plan',
            plan=plan,
            gw_targets=gw_targets,
        )

    return scenarios


def get_enhanced_scenario_analysis(
    scenarios: Dict[str, LoadedScenario],
    plant_params: dict,
    analysis_years: List[int] = None
) -> Dict[str, Dict]:
    """
    Get comprehensive analysis across enhanced scenarios.

    Args:
        scenarios: Dictionary of enhanced scenarios
        plant_params: Plant parameters for analysis
        analysis_years: Years to analyze (default: 2024-2050)

    Returns:
        Dict with analysis results per scenario
    """
    if analysis_years is None:
        analysis_years = list(range(2024, 2051))

    results = {}

    for scenario_name, scenario in scenarios.items():
        scenario_results = {
            'capacity_factors': {},
            'carbon_prices': {},
            'revenue_impacts': {},
            'policy_mechanisms': {}
        }

        for year in analysis_years:
            # Capacity factor trajectory
            scenario_results['capacity_factors'][year] = scenario.get_capacity_factor(
                year, plant_params.get('capacity_factor', 0.5)
            )

            # Carbon price trajectory
            carbon_price = scenario.get_carbon_price(year)
            scenario_results['carbon_prices'][year] = carbon_price.carbon_price_usd if carbon_price else 0.0

            # Policy mechanism from GW data
            power_mix = scenario.get_power_mix(year)
            if power_mix:
                scenario_results['policy_mechanisms'][year] = {
                    'coal_capacity_gw': power_mix.coal_gw,
                    'carbon_free_pct': power_mix.carbon_free_percentage,
                    'nuclear_capacity_gw': power_mix.nuclear_gw,
                    'renewable_capacity_gw': power_mix.solar_gw + power_mix.wind_gw
                }

        # Revenue impact analysis
        scenario_results['revenue_impacts'] = scenario.calculate_revenue_impact(
            capacity_mw=plant_params.get('capacity_mw', 1000),
            power_price=50.0,
            start_year=plant_params.get('cod_year', 2024),
            end_year=2050,
            baseline_cf=plant_params.get('capacity_factor', 0.5)
        )

        results[scenario_name] = scenario_results

    return results

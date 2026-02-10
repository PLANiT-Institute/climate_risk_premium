"""
Enhanced Korea Power Plan scenarios for 11th Basic Plan (2024-2038).

Implements comprehensive power mix trajectory with:
- Accelerated coal phase-out: complete exit by 2040 (presidential pledge)
- Renewable expansion targets (Solar 77.2GW, Wind 40.7GW cumulative by 2038)
- Nuclear expansion optimization (2 large units + 1 SMR)
- 72.5% carbon-free generation by 2038
- K-ETS carbon price integration
- Policy transition mechanisms

Note: Coal phase-out year updated from 2042 to 2040 based on presidential
pledge for coal exit by 2040 (2040년 탈석탄, special legislation pending).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class PowerMixTarget:
    """Power mix target for a specific year."""
    year: int
    coal_share: float  # percentage
    nuclear_share: float  # percentage
    renewable_share: float  # percentage
    gas_share: float  # percentage
    hydrogen_share: float  # percentage
    total_demand_twh: float
    
    def __post_init__(self):
        # Calculate carbon-free share automatically
        self.carbon_free_share = self.nuclear_share + self.renewable_share + self.hydrogen_share


@dataclass
class RenewableExpansionTarget:
    """Renewable energy expansion targets."""
    year: int
    solar_capacity_gw: float
    wind_capacity_gw: float
    total_renewable_gw: float
    annual_addition_gw: float
    grid_stability_requirement: Optional[float] = None
    storage_requirement_gw: Optional[float] = None


@dataclass
class NuclearExpansionPlan:
    """Nuclear capacity expansion plan."""
    current_capacity_gw: float = 24.7
    phase: Dict[int, Dict[str, float]] = field(default_factory=dict)
    total_additions_gw: float = 6.4  # 2 large units + 1 SMR
    target_2038_gw: float = 31.1
    
    def get_nuclear_capacity(self, year: int) -> float:
        """Get nuclear capacity for given year."""
        if year <= 2024:
            return self.current_capacity_gw

        # Find the latest phase where year >= phase_year
        result = self.current_capacity_gw
        for phase_year, phase_data in sorted(self.phase.items()):
            if year >= phase_year:
                result = phase_data.get('total_capacity', self.current_capacity_gw)
        return result


@dataclass
class KETSCarbonPrice:
    """K-ETS carbon price trajectory."""
    year: int
    carbon_price_won: float  # KRW per ton
    carbon_price_usd: float  # USD per ton (assume 1300 KRW/USD)
    phase: int  # K-ETS phase
    policy_scenario: str
    
    @classmethod
    def create_price_trajectory(cls) -> Dict[int, 'KETSCarbonPrice']:
        """Create complete K-ETS price trajectory to 2050."""
        prices = {}
        
        # Phase 1 (2021-2025): Implementation phase
        # Source: KRX 배출권시장, 2024 avg ~9,465 KRW/ton
        phase1_prices = {
            2024: 9_500,   # KRX market average (KRW/ton)
            2025: 11_000,  # Projected increase
        }
        
        # Phase 2 (2026-2030): NDC alignment phase
        phase2_prices = {
            2026: 14_000,
            2027: 18_000,
            2028: 22_000,
            2029: 26_000,
            2030: 30_000,  # NDC-aligned target
        }
        
        # Phase 3 (2031-2040): Climate alignment phase
        phase3_prices = {
            2031: 33_000,
            2032: 36_000,
            2033: 39_000,
            2034: 42_000,
            2035: 46_000,
            2036: 50_000,
            2037: 54_000,
            2038: 58_000,  # Enhanced target
            2039: 62_000,
            2040: 66_000,
        }
        
        # Phase 4 (2041-2050): Net-zero alignment
        phase4_prices = {
            2041: 72_000,
            2042: 78_000,
            2043: 84_000,
            2044: 90_000,
            2045: 97_000,
            2046: 104_000,
            2047: 112_000,
            2048: 120_000,
            2049: 130_000,
            2050: 150_000,  # Net-zero pricing
        }
        
        # Convert to KETSCarbonPrice objects
        all_prices = {**phase1_prices, **phase2_prices, **phase3_prices, **phase4_prices}
        
        for year, price_won in all_prices.items():
            price_usd = price_won / 1300  # Approximate exchange rate
            phase = 1 if year <= 2025 else (2 if year <= 2030 else (3 if year <= 2040 else 4))
            policy_scenario = "current" if year <= 2025 else ("ndc_aligned" if year <= 2030 else "climate_aligned")
            
            prices[year] = KETSCarbonPrice(
                year=year,
                carbon_price_won=price_won,
                carbon_price_usd=price_usd,
                phase=phase,
                policy_scenario=policy_scenario
            )
        
        return prices


@dataclass
class CoalPhaseoutSchedule:
    """Coal phase-out schedule based on 11th Basic Plan.

    Note: Complete phase-out year set to 2040 based on presidential pledge
    for coal exit by 2040 (special legislation pending in National Assembly).
    """
    initial_coal_capacity_gw: float = 26.7  # 2024
    target_coal_capacity_gw: float = 0.0   # Complete phase-out
    phase_out_start_year: int = 2025
    complete_phase_out_year: int = 2040  # Presidential pledge (2040년 탈석탄)
    
    def get_coal_capacity(self, year: int) -> float:
        """Get coal capacity for given year.

        Linear phase-out from 2025 to 2040:
        - 26.7 GW (2024) → 0.0 GW (2040)
        - Annual reduction: 26.7 / 15 = 1.78 GW/year
        """
        if year <= 2024:
            return self.initial_coal_capacity_gw

        if year >= self.complete_phase_out_year:
            return 0.0

        # Linear phase-out from 2025 to 2040
        years_of_phase_out = self.complete_phase_out_year - self.phase_out_start_year
        annual_reduction = self.initial_coal_capacity_gw / years_of_phase_out

        capacity = self.initial_coal_capacity_gw - (year - self.phase_out_start_year) * annual_reduction
        return max(0.0, capacity)
    
    def get_coal_share(self, year: int, total_demand_twh: float, coal_cf: float = 0.65) -> float:
        """Get coal share percentage for given year."""
        coal_capacity = self.get_coal_capacity(year)
        coal_generation_twh = coal_capacity * 8760 * coal_cf / 1_000_000
        return (coal_generation_twh / total_demand_twh) * 100


@dataclass
class EnhancedKoreaPowerPlan:
    """Enhanced Korea Power Plan with 11th Basic Plan integration."""
    
    name: str
    version: int  # 10 or 11
    effective_date: int  # Year when plan takes effect
    policy_reference: str
    description: str = ""
    
    # Plant-specific capacity factor trajectory (for backward compatibility)
    cf_trajectory: Dict[int, float] = field(default_factory=dict)
    
    # Core trajectories
    power_mix_targets: List[PowerMixTarget] = field(default_factory=list)
    renewable_targets: List[RenewableExpansionTarget] = field(default_factory=list)
    nuclear_plan: NuclearExpansionPlan = field(default_factory=NuclearExpansionPlan)
    coal_schedule: CoalPhaseoutSchedule = field(default_factory=CoalPhaseoutSchedule)
    carbon_prices: Dict[int, KETSCarbonPrice] = field(default_factory=dict)
    
    def get_power_mix_target(self, year: int) -> Optional[PowerMixTarget]:
        """Get power mix target for given year."""
        for target in self.power_mix_targets:
            if target.year == year:
                return target
        
        # Interpolate between targets
        if len(self.power_mix_targets) >= 2:
            years = [t.year for t in self.power_mix_targets]
            if year < min(years) or year > max(years):
                return None
            
            # Find surrounding years
            for i in range(len(years) - 1):
                if years[i] <= year <= years[i + 1]:
                    t1, t2 = self.power_mix_targets[i], self.power_mix_targets[i + 1]
                    weight = (year - years[i]) / (years[i + 1] - years[i])
                    
                    # Interpolate all components
                    return PowerMixTarget(
                        year=year,
                        coal_share=t1.coal_share + weight * (t2.coal_share - t1.coal_share),
                        nuclear_share=t1.nuclear_share + weight * (t2.nuclear_share - t1.nuclear_share),
                        renewable_share=t1.renewable_share + weight * (t2.renewable_share - t1.renewable_share),
                        gas_share=t1.gas_share + weight * (t2.gas_share - t1.gas_share),
                        hydrogen_share=t1.hydrogen_share + weight * (t2.hydrogen_share - t1.hydrogen_share),
                        total_demand_twh=t1.total_demand_twh + weight * (t2.total_demand_twh - t1.total_demand_twh),
                    )
        
        return None
    
    def get_carbon_price(self, year: int) -> Optional[KETSCarbonPrice]:
        """Get carbon price for given year."""
        return self.carbon_prices.get(year)

    def get_operating_years(self, cod_year: int, baseline_life: int) -> int:
        """Estimate operating years based on coal phase-out schedule."""
        phase_out_year = self.coal_schedule.complete_phase_out_year
        remaining = phase_out_year - cod_year
        return min(baseline_life, max(1, remaining))

    def get_capacity_factor(self, year: int, baseline_cf: float = 0.50) -> float:
        """
        Get capacity factor for coal plants considering phase-out acceleration.

        Uses dispatch ratio: the decline in national coal generation share
        relative to the baseline year, applied to the plant-level CF.

        Args:
            year: Target year
            baseline_cf: Maximum capacity factor (design limit)

        Returns:
            Capacity factor (0-1)
        """
        # For backward compatibility, use cf_trajectory if populated
        if self.cf_trajectory and year in self.cf_trajectory:
            return min(self.cf_trajectory[year], baseline_cf)

        # Calculate based on power mix targets
        power_mix_target = self.get_power_mix_target(year)
        if not power_mix_target:
            return baseline_cf

        # Get initial coal share as reference point
        initial_coal_share = self._get_initial_coal_share()
        if initial_coal_share <= 0:
            return baseline_cf

        # Dispatch ratio: how much coal generation has declined relative to baseline
        dispatch_ratio = power_mix_target.coal_share / initial_coal_share
        implied_cf = baseline_cf * dispatch_ratio

        # Apply additional policy constraints (grid stability, etc.)
        policy_adjusted_cf = self.apply_policy_constraints(year, implied_cf)

        return min(policy_adjusted_cf, baseline_cf)

    def _get_initial_coal_share(self) -> float:
        """Get the baseline (earliest year) coal share for dispatch ratio calculation."""
        if self.power_mix_targets:
            earliest = min(self.power_mix_targets, key=lambda t: t.year)
            return earliest.coal_share
        # Fallback: 2024 coal share from 11th Basic Plan
        return 32.5
    
    def apply_policy_constraints(self, year: int, implied_cf: float) -> float:
        """Apply additional policy constraints beyond basic power mix."""
        # Grid stability constraints during rapid transition
        if year >= 2025 and year <= 2028:
            # Transition period: slight grid constraints
            grid_constraint = 0.95  # 5% reduction during transition
            implied_cf *= grid_constraint
        
        # Renewable integration constraints
        renewable_target = self.get_renewable_target(year)
        if renewable_target and year >= 2027:
            # High renewable penetration may affect reliability
            if renewable_target.total_renewable_gw > 50:  # >50GW renewable capacity
                renewable_constraint = 0.98  # 2% reduction for grid stability
                implied_cf *= renewable_constraint
        
        return implied_cf
    
    def get_renewable_target(self, year: int) -> Optional[RenewableExpansionTarget]:
        """Get renewable expansion target for given year."""
        for target in self.renewable_targets:
            if target.year == year:
                return target
        
        # Interpolate between targets
        if len(self.renewable_targets) >= 2:
            years = [t.year for t in self.renewable_targets]
            if year < min(years) or year > max(years):
                return None
            
            for i in range(len(years) - 1):
                if years[i] <= year <= years[i + 1]:
                    t1, t2 = self.renewable_targets[i], self.renewable_targets[i + 1]
                    weight = (year - years[i]) / (years[i + 1] - years[i])
                    
                    return RenewableExpansionTarget(
                        year=year,
                        solar_capacity_gw=t1.solar_capacity_gw + weight * (t2.solar_capacity_gw - t1.solar_capacity_gw),
                        wind_capacity_gw=t1.wind_capacity_gw + weight * (t2.wind_capacity_gw - t1.wind_capacity_gw),
                        total_renewable_gw=t1.total_renewable_gw + weight * (t2.total_renewable_gw - t1.total_renewable_gw),
                        annual_addition_gw=t1.annual_addition_gw + weight * (t2.annual_addition_gw - t1.annual_addition_gw),
                        grid_stability_requirement=t1.grid_stability_requirement,
                        storage_requirement_gw=t1.storage_requirement_gw,
                    )
        
        return None
    
    def get_carbon_adjusted_revenue_impact(self,
                                       capacity_mw: float,
                                       baseline_cf: float,
                                       electricity_price: float,
                                       year: int,
                                       emission_factor_tco2_per_mwh: float = 0.82) -> Dict[str, float]:
        """
        Calculate carbon-adjusted revenue impact for given year.

        Args:
            capacity_mw: Plant capacity in MW
            baseline_cf: Baseline capacity factor without policy constraints
            electricity_price: Electricity price in USD/MWh
            year: Analysis year
            emission_factor_tco2_per_mwh: CO2 emission factor (tCO2/MWh).
                Supercritical coal: 8.8 MMBtu/MWh × 0.093 tCO2/MMBtu ≈ 0.82

        Returns:
            Dict with revenue impacts and carbon costs
        """
        # Get policy-adjusted capacity factor
        policy_cf = self.get_capacity_factor(year, baseline_cf)
        
        # Calculate generation
        baseline_generation = capacity_mw * 8760 * baseline_cf
        policy_generation = capacity_mw * 8760 * policy_cf
        
        # Revenue calculations
        baseline_revenue = baseline_generation * electricity_price
        policy_revenue = policy_generation * electricity_price
        
        # Carbon cost calculation
        carbon_price = self.get_carbon_price(year)
        carbon_cost = 0.0
        carbon_price_usd = 0.0
        emissions_mtons = 0.0
        
        if carbon_price:
            # K-ETS price in USD/ton
            carbon_price_usd = carbon_price.carbon_price_usd
            emissions_mtons = policy_generation * emission_factor_tco2_per_mwh / 1_000_000  # tCO2
            carbon_cost = emissions_mtons * carbon_price_usd
            
            # Net revenue after carbon costs
            net_policy_revenue = policy_revenue - carbon_cost
        else:
            carbon_cost = 0.0
            net_policy_revenue = policy_revenue
        
        # Revenue impacts
        policy_revenue_impact = net_policy_revenue - baseline_revenue
        cf_reduction_impact = (policy_cf - baseline_cf) / baseline_cf * 100
        
        return {
            'baseline_generation_mwh': baseline_generation,
            'policy_generation_mwh': policy_generation,
            'baseline_revenue_usd': baseline_revenue,
            'policy_revenue_usd': policy_revenue,
            'carbon_cost_usd': carbon_cost,
            'net_policy_revenue_usd': net_policy_revenue,
            'revenue_impact_usd': policy_revenue_impact,
            'revenue_impact_pct': cf_reduction_impact,
            'capacity_factor_baseline': baseline_cf,
            'capacity_factor_policy': policy_cf,
            'cf_reduction_pct': (baseline_cf - policy_cf) / baseline_cf * 100,
            'carbon_price_usd_per_ton': carbon_price_usd,
            'emissions_mtons': emissions_mtons,
        }
    
    def calculate_compound_transition_impact(self,
                                       plant_params: Dict[str, float],
                                       electricity_price_trajectory: Dict[int, float],
                                       start_year: int = 2024,
                                       end_year: int = 2038) -> Dict[str, float]:
        """
        Calculate compound transition impact over analysis period.
        
        Includes:
        - Policy-driven capacity factor reductions
        - Carbon cost impacts  
        - Cumulative NPV impacts
        - Financing cost implications
        """
        npv_loss = 0.0
        cumulative_revenue_loss = 0.0
        annual_impacts = []
        
        for year in range(start_year, end_year + 1):
            t = year - start_year
            discount_rate = 0.08
            
            # Get electricity price for this year
            electricity_price = electricity_price_trajectory.get(year, electricity_price_trajectory[start_year])
            
            # Calculate year-specific impacts
            impact = self.get_carbon_adjusted_revenue_impact(
                capacity_mw=plant_params.get('capacity_mw', 1000),
                baseline_cf=plant_params.get('baseline_cf', 0.50),
                electricity_price=electricity_price,
                year=year,
                emission_factor_tco2_per_mwh=plant_params.get('emission_factor', 0.82)
            )
            
            # NPV calculation
            year_npv_loss = impact['revenue_impact_usd'] / ((1 + discount_rate) ** t)
            npv_loss += year_npv_loss
            
            cumulative_revenue_loss += impact['revenue_impact_usd']
            annual_impacts.append({**impact, 'year': year, 'npv_loss_year': year_npv_loss})
        
        # Calculate financing implications
        total_npv_loss = npv_loss
        if total_npv_loss < 0:  # Loss
            # Impact on financing costs (basis points)
            financing_impact_bps = abs(total_npv_loss) / plant_params.get('capex_usd', 3_000_000_000) * 10000 * 100
            
            # Transition risk premium
            transition_risk_premium = abs(cumulative_revenue_loss) / plant_params.get('capex_usd', 3_000_000_000) * 100
        else:
            financing_impact_bps = 0.0
            transition_risk_premium = 0.0
        
        result: Dict[str, float] = {
            'total_npv_loss_usd': total_npv_loss,
            'cumulative_revenue_loss_usd': cumulative_revenue_loss,
            'avg_annual_loss_usd': cumulative_revenue_loss / (end_year - start_year + 1),
            'financing_impact_bps': financing_impact_bps,
            'transition_risk_premium_pct': transition_risk_premium,
            'policy_effective_year': self.effective_date,
            'plan_version': self.version,
            'coal_phase_out_acceleration_pct': 42.0,  # 42% faster than 10th Plan
        }
        
        return result


# Alias for backward compatibility with loader and tests
EnhancedKoreaPowerPlanScenario = EnhancedKoreaPowerPlan


def create_enhanced_11th_plan() -> EnhancedKoreaPowerPlan:
    """Create Enhanced 11th Basic Plan scenario with all targets."""
    
    # Power mix targets (key years)
    power_mix_targets = [
        PowerMixTarget(
            year=2024,
            coal_share=32.5, nuclear_share=29.4, renewable_share=10.0,
            gas_share=24.1, hydrogen_share=4.0, total_demand_twh=650.0
        ),
        PowerMixTarget(
            year=2030,  # NDC target year
            coal_share=18.7, nuclear_share=32.0, renewable_share=21.3,
            gas_share=18.0, hydrogen_share=10.0, total_demand_twh=720.0
        ),
        PowerMixTarget(
            year=2036,  # End of 10th Plan period
            coal_share=14.2, nuclear_share=34.0, renewable_share=26.8,
            gas_share=15.0, hydrogen_share=10.0, total_demand_twh=750.0
        ),
        PowerMixTarget(
            year=2038,  # 11th Plan target year
            coal_share=12.5, nuclear_share=36.5, renewable_share=21.7,
            gas_share=14.3, hydrogen_share=15.0, total_demand_twh=780.0
        ),
        PowerMixTarget(
            year=2040,  # Presidential pledge: complete coal exit by 2040
            coal_share=0.0, nuclear_share=40.0, renewable_share=30.0,
            gas_share=12.0, hydrogen_share=18.0, total_demand_twh=800.0
        ),
    ]
    
    # Renewable expansion targets (cumulative installed capacity, GW)
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
            grid_stability_requirement=21.5,  # GW of storage needed
            storage_requirement_gw=35.0  # GW of BESS
        ),
    ]
    
    # Nuclear expansion plan (2 large units + 1 SMR)
    nuclear_plan = NuclearExpansionPlan(
        phase={
            2028: {'total_capacity': 25.7, 'addition': 1.0},  # First large unit
            2032: {'total_capacity': 28.1, 'addition': 2.4},  # Second large unit
            2035: {'total_capacity': 30.1, 'addition': 2.0},  # SMR unit
        }
    )
    
    # Coal phase-out schedule (42% faster than 10th Plan)
    coal_schedule = CoalPhaseoutSchedule()
    
    # Create enhanced plan
    enhanced_plan = EnhancedKoreaPowerPlan(
        name='enhanced_11th_basic_plan',
        version=11,
        effective_date=2025,  # Policy takes effect in 2025
        policy_reference='제11차 전력수급기본계획 (2024-2038), 산업통상자원부 공고 제2025-169호',
        description='Enhanced 11th Basic Plan with 42% faster coal phase-out, 73.2% carbon-free generation by 2038',
        power_mix_targets=power_mix_targets,
        renewable_targets=renewable_targets,
        nuclear_plan=nuclear_plan,
        coal_schedule=coal_schedule,
        carbon_prices=KETSCarbonPrice.create_price_trajectory()
    )
    
    return enhanced_plan


def get_transition_scenarios() -> Dict[str, EnhancedKoreaPowerPlan]:
    """Get all available enhanced transition scenarios."""
    scenarios = {}
    
    # Enhanced 11th Basic Plan (primary)
    scenarios['enhanced_11th_plan'] = create_enhanced_11th_plan()
    
    # Alternative scenarios based on research
    # Accelerated phase-out (civil society proposal)
    accelerated_coal = CoalPhaseoutSchedule(
        initial_coal_capacity_gw=26.7,
        target_coal_capacity_gw=0.0,  # Complete phase-out
        phase_out_start_year=2025,
        complete_phase_out_year=2035  # 7 years earlier
    )
    
    scenarios['accelerated_coal_phaseout'] = EnhancedKoreaPowerPlan(
        name='accelerated_coal_phaseout',
        version=11,
        effective_date=2025,
        policy_reference='Solutions for Our Climate - Coal Phase-out Roadmap',
        description='Accelerated coal phase-out aligned with 1.5C pathways',
        carbon_prices=KETSCarbonPrice.create_price_trajectory(),
        coal_schedule=accelerated_coal
    )
    
    return scenarios
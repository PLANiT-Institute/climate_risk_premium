"""
Integration tests for enhanced transition module with 11th Basic Plan scenarios.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from src.scenarios.enhanced_korea_power_plan_loader import load_enhanced_korea_power_plan_scenarios
from src.risk.enhanced_transition import apply_enhanced_transition, calculate_enhanced_revenue_impact, KETSCarbonPricing
from src.risk.transition import apply_transition, YearlyTransitionAdjustments, create_yearly_transition_adjustments


class TestEnhancedTransitionIntegration:
    """Test enhanced transition functionality."""

    @pytest.fixture
    def enhanced_scenarios(self):
        """Load enhanced scenarios for testing."""
        from pathlib import Path

        project_root = Path(__file__).parent.parent
        test_file = project_root / "data" / "raw" / "enhanced_korea_power_plan.csv"

        if not test_file.exists():
            pytest.skip(f"Enhanced Korea Power Plan data not available at {test_file}")

        return load_enhanced_korea_power_plan_scenarios(str(test_file))

    @pytest.fixture
    def sample_plant_params(self):
        """Sample coal plant parameters."""
        return {
            'capacity_mw': 1000,
            'capacity_factor': 0.65,
            'operating_years': 40,
            'cod_year': 2024,
            'heat_rate': 8.8,  # MMBtu/MWh
            'carbon_content': 0.093  # tons CO2/MMBtu
        }

    def test_enhanced_scenario_loading(self, enhanced_scenarios):
        """Test that enhanced scenarios load correctly."""
        assert 'official_11th_plan' in enhanced_scenarios

        scenario = enhanced_scenarios['official_11th_plan']
        assert scenario.name == 'official_11th_plan'
        assert len(scenario.power_mix_targets) > 0
        assert len(scenario.gw_targets) > 0
        assert scenario.coal_phaseout.complete_phase_out_year == 2040

    def test_carbon_free_generation_target(self, enhanced_scenarios):
        """Test 72.5% carbon-free generation target by 2038 (2040 exit aligned)."""
        scenario = enhanced_scenarios['official_11th_plan']

        power_mix_2038 = scenario.get_power_mix(2038)
        assert power_mix_2038 is not None
        # Updated to 72.5% with 2040 coal phase-out alignment
        assert abs(power_mix_2038.carbon_free_percentage - 72.5) < 0.1

    def test_coal_phaseout_acceleration(self, enhanced_scenarios, sample_plant_params):
        """Test 42% faster coal phase-out compared to 10th Plan.

        With dispatch-ratio CF formula:
        - 2024 CF ≈ baseline (dispatch_ratio ≈ 1.0)
        - 2030 CF ≈ 0.40 (coal share drops ~40%)
        - 2038 CF ≈ 0.10 (coal share drops ~85%)
        """
        scenario = enhanced_scenarios['official_11th_plan']
        baseline_cf = sample_plant_params['capacity_factor']

        cf_2030 = scenario.get_capacity_factor(2030, baseline_cf)
        # Dispatch ratio: coal share declines ~40% from baseline → CF ≈ 0.40
        assert 0.25 < cf_2030 < 0.50, f"Expected 2030 CF in (0.25, 0.50), got {cf_2030:.3f}"

        # By 2038, coal share drops ~85% from baseline → CF ≈ 0.10
        cf_2038 = scenario.get_capacity_factor(2038, baseline_cf)
        assert cf_2038 < 0.15, f"Expected 2038 CF < 0.15, got {cf_2038:.3f}"

    def test_renewable_expansion_targets(self, enhanced_scenarios):
        """Test renewable expansion: solar 77.2GW, wind 40.7GW by 2038."""
        scenario = enhanced_scenarios['official_11th_plan']

        power_mix_2038 = scenario.get_power_mix(2038)
        assert power_mix_2038 is not None

        # Solar capacity target (cumulative installed)
        assert abs(power_mix_2038.solar_gw - 77.2) < 0.1

        # Wind capacity target (cumulative installed)
        assert abs(power_mix_2038.wind_gw - 40.7) < 0.1

    def test_nuclear_expansion_changes(self, enhanced_scenarios):
        """Test nuclear expansion plan."""
        scenario = enhanced_scenarios['official_11th_plan']

        nuclear = scenario.nuclear_expansion
        # Check that nuclear phases are defined
        assert 2028 in nuclear.phase
        assert 2032 in nuclear.phase
        assert 2035 in nuclear.phase

    def test_carbon_price_trajectory(self, enhanced_scenarios):
        """Test K-ETS carbon price trajectory integration."""
        scenario = enhanced_scenarios['official_11th_plan']

        # Test key years - prices are KETSCarbonPrice objects
        price_2025 = scenario.get_carbon_price(2025)
        price_2030 = scenario.get_carbon_price(2030)
        price_2038 = scenario.get_carbon_price(2038)

        assert price_2025 is not None
        assert price_2030 is not None
        assert price_2038 is not None

        # K-ETS prices should be reasonable (based on actual market data)
        # 2024 avg ~$7-8/ton, growing over time
        assert price_2025.carbon_price_usd < 15  # ~11,000 KRW / 1300
        assert price_2030.carbon_price_usd > 15  # ~30,000 KRW / 1300
        assert price_2038.carbon_price_usd > 30  # ~58,000 KRW / 1300

        # Prices should increase over time
        assert price_2025.carbon_price_usd < price_2030.carbon_price_usd < price_2038.carbon_price_usd

    def test_enhanced_transition_adjustments(self, enhanced_scenarios, sample_plant_params):
        """Test enhanced transition adjustments application."""
        scenario = enhanced_scenarios['official_11th_plan']

        from src.scenarios import TransitionScenario
        generic_scenario = TransitionScenario(name="test", dispatch_priority_penalty=0.1, retirement_years=30)

        # Use the plan object for apply_enhanced_transition
        adjustments = apply_enhanced_transition(
            plant_params=sample_plant_params,
            scenario=generic_scenario,
            enhanced_korea_scenario=scenario.plan,
            current_year=2030,
            carbon_pricing_scenario="ndc_aligned"
        )

        assert adjustments.capacity_factor < sample_plant_params['capacity_factor']
        assert adjustments.operating_years < sample_plant_params['operating_years']
        assert adjustments.carbon_cost_burden > 0
        assert adjustments.revenue_loss_pct > 0
        assert adjustments.transition_risk_premium > 0
        assert "11th Basic Plan" in adjustments.policy_mechanism
        assert len(adjustments.carbon_price_trajectory) > 0

    def test_revenue_impact_calculation(self, enhanced_scenarios, sample_plant_params):
        """Test comprehensive revenue impact calculation."""
        scenario = enhanced_scenarios['official_11th_plan']

        from src.scenarios import TransitionScenario
        generic_scenario = TransitionScenario(name="test", dispatch_priority_penalty=0.1, retirement_years=30)

        adjustments = apply_enhanced_transition(
            plant_params=sample_plant_params,
            scenario=generic_scenario,
            enhanced_korea_scenario=scenario.plan,
            current_year=2030,
            carbon_pricing_scenario="ndc_aligned"
        )

        revenue_impact = calculate_enhanced_revenue_impact(
            adjustments=adjustments,
            plant_params=sample_plant_params,
            power_price=50.0
        )

        assert revenue_impact['total_baseline_npv'] > 0
        assert revenue_impact['total_adjusted_npv'] < revenue_impact['total_baseline_npv']
        assert revenue_impact['npv_loss'] > 0
        assert revenue_impact['npv_loss_pct'] > 0
        assert revenue_impact['total_carbon_costs_pv'] > 0
        assert revenue_impact['transition_risk_premium'] > 0
        assert revenue_impact['adjusted_wacc'] > 0.08

    def test_backward_compatibility(self, enhanced_scenarios, sample_plant_params):
        """Test backward compatibility with legacy transition function."""
        scenario = enhanced_scenarios['official_11th_plan']

        from src.scenarios import TransitionScenario
        generic_scenario = TransitionScenario(name="test", dispatch_priority_penalty=0.1, retirement_years=30)

        # Test that legacy function works with enhanced plan object
        legacy_adjustments = apply_transition(
            plant_params=sample_plant_params,
            scenario=generic_scenario,
            enhanced_korea_scenario=scenario.plan,
            current_year=2030
        )

        assert isinstance(legacy_adjustments.capacity_factor, float)
        assert isinstance(legacy_adjustments.operating_years, int)
        assert legacy_adjustments.capacity_factor < sample_plant_params['capacity_factor']
        assert "Enhanced Korea Power Plan" in legacy_adjustments.notes or "11th" in legacy_adjustments.notes

    def test_krets_carbon_pricing_scenarios(self):
        """Test K-ETS carbon pricing scenarios have realistic values."""
        for scenario_name in ["current_policy", "ndc_aligned", "net_zero"]:
            trajectory = KETSCarbonPricing.get_carbon_price_trajectory(scenario_name)

            # 2024 base should be ~$7 for all scenarios (KRX market: ~9,465 KRW/ton ≈ $7/ton)
            assert trajectory[2024] == 7, f"{scenario_name}: 2024 price should be $7, got {trajectory[2024]}"

            # Prices should increase monotonically
            prev_price = 0
            for year in sorted(trajectory.keys()):
                assert trajectory[year] >= prev_price, f"{scenario_name}: price decreased at year {year}"
                prev_price = trajectory[year]

        # Sanity check ranges (aligned with KETSCarbonPrice: 30,000 KRW/1,300 ≈ $23 for 2030)
        cp = KETSCarbonPricing.get_carbon_price_trajectory("current_policy")
        assert 20 <= cp[2030] <= 30  # current_policy 2030
        assert 100 <= cp[2050] <= 130  # current_policy 2050

        ndc = KETSCarbonPricing.get_carbon_price_trajectory("ndc_aligned")
        assert 20 <= ndc[2030] <= 30  # ndc_aligned 2030 (aligned with KETSCarbonPrice)
        assert 130 <= ndc[2050] <= 180  # ndc_aligned 2050

        nz = KETSCarbonPricing.get_carbon_price_trajectory("net_zero")
        assert 35 <= nz[2030] <= 50  # net_zero 2030
        assert 250 <= nz[2050] <= 350  # net_zero 2050

    def test_solar_wind_monotonic_increase(self, enhanced_scenarios):
        """Test that solar and wind capacity increase monotonically in CSV data."""
        scenario = enhanced_scenarios['official_11th_plan']

        prev_solar = 0
        prev_wind = 0
        for target in scenario.gw_targets:
            assert target.solar_gw >= prev_solar, f"Solar decreased at year {target.year}"
            assert target.wind_gw >= prev_wind, f"Wind decreased at year {target.year}"
            prev_solar = target.solar_gw
            prev_wind = target.wind_gw


    def test_yearly_transition_cf_trajectory(self, enhanced_scenarios, sample_plant_params):
        """Test CF decreases over time via YearlyTransitionAdjustments."""
        scenario = enhanced_scenarios['official_11th_plan']

        ytadj = create_yearly_transition_adjustments(
            plant_params=sample_plant_params,
            enhanced_korea_scenario=scenario.plan,
            start_year=2025,
            end_year=2038,
        )

        assert isinstance(ytadj, YearlyTransitionAdjustments)
        assert len(ytadj.years) == 14  # 2025..2038 inclusive

        cf_2025 = ytadj.get_cf_for_year(2025)
        cf_2030 = ytadj.get_cf_for_year(2030)
        cf_2038 = ytadj.get_cf_for_year(2038)

        # CF should decline over time as coal dispatch drops
        assert cf_2025 > cf_2030, f"2025 CF ({cf_2025:.3f}) should exceed 2030 ({cf_2030:.3f})"
        assert cf_2030 > cf_2038, f"2030 CF ({cf_2030:.3f}) should exceed 2038 ({cf_2038:.3f})"
        assert cf_2038 < 0.15, f"2038 CF should be < 0.15, got {cf_2038:.3f}"

    def test_carbon_costs_in_cashflow(self, enhanced_scenarios, sample_plant_params):
        """Test carbon costs appear in cashflow and reduce EBITDA."""
        scenario = enhanced_scenarios['official_11th_plan']

        # Build full plant params needed by cashflow engine
        full_params = {
            **sample_plant_params,
            'power_price_per_mwh': 80.0,
            'heat_rate_mmbtu_mwh': 9.5,
            'fuel_price_per_mmbtu': 3.2,
            'fixed_opex_per_kw_year': 35.0,
            'variable_opex_per_mwh': 4.5,
            'total_capex_million': 4900,
            'useful_life': 30,
            'tax_rate': 0.22,
            'debt_fraction': 0.70,
            'equity_fraction': 0.30,
            'debt_interest_rate': 0.061,
            'debt_tenor_years': 20,
        }

        from src.risk import TransitionAdjustments, PhysicalAdjustments
        from src.financials import compute_cashflows_timeseries
        from src.scenarios import TransitionScenario

        transition_adj = TransitionAdjustments(
            capacity_factor=0.65, operating_years=14, notes="test"
        )
        physical_adj = PhysicalAdjustments(outage_rate=0.0, efficiency_loss=0.0)
        transition_scenario = TransitionScenario(
            name="test", dispatch_priority_penalty=0.0, retirement_years=40,
        )

        ytadj = create_yearly_transition_adjustments(
            plant_params=full_params,
            enhanced_korea_scenario=scenario.plan,
            start_year=2025,
            end_year=2038,
        )

        cf_with = compute_cashflows_timeseries(
            full_params, transition_scenario, transition_adj, physical_adj,
            start_year=2025, yearly_transition_adj=ytadj,
        )

        cf_without = compute_cashflows_timeseries(
            full_params, transition_scenario, transition_adj, physical_adj,
            start_year=2025, yearly_transition_adj=None,
        )

        # Carbon costs should be > 0 when yearly_transition_adj is provided
        assert cf_with.carbon_costs.sum() > 0, "Carbon costs should be positive"

        # EBITDA should be lower with carbon costs
        assert cf_with.ebitda.sum() < cf_without.ebitda.sum(), (
            "EBITDA with carbon costs should be lower than without"
        )

    def test_backward_compat_no_yearly_transition(self, sample_plant_params):
        """Test that omitting yearly_transition_adj yields zero carbon costs."""
        full_params = {
            **sample_plant_params,
            'power_price_per_mwh': 80.0,
            'heat_rate_mmbtu_mwh': 9.5,
            'fuel_price_per_mmbtu': 3.2,
            'fixed_opex_per_kw_year': 35.0,
            'variable_opex_per_mwh': 4.5,
            'total_capex_million': 4900,
            'useful_life': 30,
            'tax_rate': 0.22,
            'debt_fraction': 0.70,
            'equity_fraction': 0.30,
            'debt_interest_rate': 0.061,
            'debt_tenor_years': 20,
        }

        from src.risk import TransitionAdjustments, PhysicalAdjustments
        from src.financials import compute_cashflows_timeseries
        from src.scenarios import TransitionScenario

        transition_adj = TransitionAdjustments(
            capacity_factor=0.65, operating_years=10, notes="test"
        )
        physical_adj = PhysicalAdjustments(outage_rate=0.0, efficiency_loss=0.0)
        transition_scenario = TransitionScenario(
            name="test", dispatch_priority_penalty=0.0, retirement_years=40,
        )

        cf = compute_cashflows_timeseries(
            full_params, transition_scenario, transition_adj, physical_adj,
            start_year=2025,
        )

        # carbon_costs should all be zero
        assert np.allclose(cf.carbon_costs, 0.0), (
            f"Carbon costs should be zero without yearly_transition_adj, got {cf.carbon_costs}"
        )


if __name__ == "__main__":
    pytest.main([__file__])

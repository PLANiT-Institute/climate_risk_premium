"""
Integration tests for the end-to-end CRP pipeline.

Tests the full flow:
1. Define plant parameters and scenarios
2. Apply transition adjustments
3. Apply physical adjustments
4. Compute cash flows
5. Calculate financial metrics
6. Assess credit rating
7. Calculate CRP via rating migration
8. Decompose CRP via Shapley attribution
"""
import pytest
import numpy as np
from src.financials.cashflow import compute_cashflows_timeseries
from src.financials.metrics import calculate_metrics
from src.risk import (
    TransitionAdjustments,
    PhysicalAdjustments,
    apply_transition,
    assess_credit_rating,
    calculate_rating_metrics_from_financials,
    rating_migration_analysis,
    decompose_risk_shapley,
)
from src.risk.credit_rating import calculate_crp_from_ratings, Rating
from src.risk.financing import calculate_expected_loss, map_expected_loss_to_spreads
from src.scenarios import TransitionScenario


@pytest.fixture
def samcheok_plant():
    """Samcheok-like coal plant parameters."""
    return {
        "capacity_mw": 2100,
        "capacity_factor": 0.85,
        "power_price_per_mwh": 80,
        "heat_rate_mmbtu_mwh": 9.5,
        "fuel_price_per_mmbtu": 3.2,
        "fixed_opex_per_kw_year": 35,
        "variable_opex_per_mwh": 4.5,
        "total_capex_million": 4900,
        "useful_life": 40,
        "tax_rate": 0.24,
        "debt_fraction": 0.70,
        "debt_interest_rate": 0.061,
        "debt_tenor_years": 20,
        "operating_years": 40,
        "discount_rate": 0.08,
    }


class TestEndToEndPipeline:
    """Test the full CRP calculation pipeline."""

    def test_baseline_cashflows_positive_ebitda(self, samcheok_plant):
        trans = TransitionScenario("Baseline", 0.0, 40)
        trans_adj = TransitionAdjustments(0.85, 40)
        phys_adj = PhysicalAdjustments(0.0, 0.0)

        cf = compute_cashflows_timeseries(samcheok_plant, trans, trans_adj, phys_adj)

        assert np.all(cf.ebitda > 0), "Baseline should have positive EBITDA"
        assert len(cf.years) == 40

    def test_risk_scenario_lower_npv_than_baseline(self, samcheok_plant):
        trans = TransitionScenario("Baseline", 0.0, 40)
        phys_no_risk = PhysicalAdjustments(0.0, 0.0)
        phys_risky = PhysicalAdjustments(0.03, 0.01)

        trans_adj_base = TransitionAdjustments(0.85, 40)
        trans_adj_risk = TransitionAdjustments(0.65, 30)

        cf_base = compute_cashflows_timeseries(samcheok_plant, trans, trans_adj_base, phys_no_risk)
        cf_risk = compute_cashflows_timeseries(samcheok_plant, trans, trans_adj_risk, phys_risky)

        m_base = calculate_metrics(cf_base, samcheok_plant)
        m_risk = calculate_metrics(cf_risk, samcheok_plant)

        assert m_risk.npv < m_base.npv

    def test_full_crp_calculation_pipeline(self, samcheok_plant):
        """Test the complete pipeline from scenarios to CRP."""
        trans = TransitionScenario("Test", 0.0, 40)

        # Baseline
        base_adj = TransitionAdjustments(0.85, 40)
        base_phys = PhysicalAdjustments(0.0, 0.0)
        cf_base = compute_cashflows_timeseries(samcheok_plant, trans, base_adj, base_phys)
        m_base = calculate_metrics(cf_base, samcheok_plant)

        # Risk scenario
        risk_adj = TransitionAdjustments(0.65, 30)
        risk_phys = PhysicalAdjustments(0.03, 0.01)
        cf_risk = compute_cashflows_timeseries(samcheok_plant, trans, risk_adj, risk_phys)
        m_risk = calculate_metrics(cf_risk, samcheok_plant)

        # Expected loss
        capex = 4900e6
        el_pct = calculate_expected_loss(m_base.npv, m_risk.npv, capex)
        assert el_pct > 0

        # Financing impact
        params = {
            "spread_slope_bps_per_pct": 50,
            "equity_slope_pct_per_pct": 0.8,
            "baseline_spread_bps": 150,
            "risk_free_rate": 0.035,
            "debt_fraction": 0.70,
            "equity_fraction": 0.30,
        }
        impact = map_expected_loss_to_spreads(el_pct, m_base.npv - m_risk.npv, params)
        assert impact.crp_bps > 0

    def test_credit_rating_based_crp(self, samcheok_plant):
        """Test CRP calculation via credit rating migration."""
        trans = TransitionScenario("Test", 0.0, 40)

        # Baseline (strong financials)
        base_adj = TransitionAdjustments(0.85, 40)
        base_phys = PhysicalAdjustments(0.0, 0.0)
        cf_base = compute_cashflows_timeseries(samcheok_plant, trans, base_adj, base_phys)

        # Build rating metrics from baseline
        avg_ebitda = np.mean(cf_base.ebitda)
        total_capex = 4900e6
        avg_interest = np.mean(cf_base.interest_expense[:20])

        base_metrics = calculate_rating_metrics_from_financials(
            capacity_mw=2100,
            ebitda=avg_ebitda,
            fixed_assets=total_capex,
            interest_expense=max(avg_interest, 1.0),
            total_debt=total_capex * 0.70,
            cash_and_equivalents=0,
            total_equity=total_capex * 0.30,
            total_assets=total_capex,
        )
        base_rating = assess_credit_rating(base_metrics)

        # Rating should be at least investment grade for baseline
        assert base_rating.overall_rating.is_investment_grade

    def test_shapley_decomposition_consistency(self, samcheok_plant):
        """Test that Shapley decomposition is consistent with total CRP."""
        baseline_crp = 0
        transition_crp = 120
        physical_crp = 80
        combined_crp = 230

        result = decompose_risk_shapley(
            baseline_crp, transition_crp, physical_crp, combined_crp
        )

        total_attribution = (
            result["transition_contribution_bps"]
            + result["physical_contribution_bps"]
        )
        expected_total = combined_crp - baseline_crp

        assert abs(total_attribution - expected_total) < 1e-9

    def test_transition_apply_with_generic_scenario(self, samcheok_plant):
        """Test applying transition risk via generic scenario."""
        scenario = TransitionScenario("aggressive", 0.20, 25)
        adj = apply_transition(samcheok_plant, scenario)

        assert adj.capacity_factor == 0.85 - 0.20
        assert adj.operating_years == 25


class TestMultiScenarioComparison:
    """Test comparing multiple scenarios."""

    def test_increasing_risk_decreases_npv(self, samcheok_plant):
        trans = TransitionScenario("Test", 0.0, 40)
        risk_levels = [
            (0.85, 40, PhysicalAdjustments(0.0, 0.0)),
            (0.70, 35, PhysicalAdjustments(0.01, 0.005)),
            (0.55, 25, PhysicalAdjustments(0.03, 0.01)),
        ]

        npvs = []
        for cf_val, years, phys in risk_levels:
            adj = TransitionAdjustments(cf_val, years)
            cf = compute_cashflows_timeseries(samcheok_plant, trans, adj, phys)
            m = calculate_metrics(cf, samcheok_plant)
            npvs.append(m.npv)

        # NPVs should be monotonically decreasing
        for i in range(1, len(npvs)):
            assert npvs[i] < npvs[i - 1]

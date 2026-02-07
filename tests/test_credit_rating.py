"""
Comprehensive tests for credit rating module (src/risk/credit_rating.py).

Tests cover:
- Rating enum properties (spread, investment grade, distressed)
- Individual component rating functions
- Overall credit rating assessment
- Rating metrics calculation from financials
- Rating migration analysis
- CRP calculation from rating migration
- Counterfactual rating assessment
- Edge cases (negative EBITDA, extreme values)
"""
import pytest
from src.risk.credit_rating import (
    Rating,
    RatingMetrics,
    RatingAssessment,
    assess_credit_rating,
    rate_capacity,
    rate_profitability,
    rate_coverage,
    rate_dscr,
    rate_net_debt_leverage,
    rate_equity_leverage,
    rate_asset_leverage,
    calculate_rating_metrics_from_financials,
    rating_migration_analysis,
    calculate_crp_from_ratings,
    get_counterfactual_baseline_rating,
    assess_rating_with_counterfactual,
)


class TestRatingEnum:
    """Test Rating enum properties."""

    def test_rating_ordering(self):
        assert Rating.AAA.value < Rating.D.value
        assert Rating.BBB.value < Rating.BB.value

    def test_investment_grade_boundary(self):
        assert Rating.AAA.is_investment_grade
        assert Rating.AA.is_investment_grade
        assert Rating.A.is_investment_grade
        assert Rating.BBB.is_investment_grade
        assert not Rating.BB.is_investment_grade
        assert not Rating.B.is_investment_grade

    def test_distressed_boundary(self):
        assert not Rating.B.is_distressed
        assert Rating.CCC.is_distressed
        assert Rating.CC.is_distressed
        assert Rating.C.is_distressed
        assert Rating.D.is_distressed

    def test_spread_monotonically_increases(self):
        ratings = [Rating.AAA, Rating.AA, Rating.A, Rating.BBB,
                   Rating.BB, Rating.B, Rating.CCC, Rating.CC, Rating.C, Rating.D]
        spreads = [r.to_spread_bps() for r in ratings]
        for i in range(1, len(spreads)):
            assert spreads[i] > spreads[i - 1]

    def test_specific_spreads(self):
        assert Rating.AAA.to_spread_bps() == 50
        assert Rating.BBB.to_spread_bps() == 250
        assert Rating.D.to_spread_bps() == 5000

    def test_numeric_score(self):
        assert Rating.AAA.numeric_score == 1
        assert Rating.D.numeric_score == 10

    def test_str_representation(self):
        assert str(Rating.AAA) == "AAA"
        assert str(Rating.CCC) == "CCC"


class TestComponentRatings:
    """Test individual rating component functions."""

    def test_rate_capacity_boundaries(self):
        assert rate_capacity(2000) == Rating.AAA
        assert rate_capacity(800) == Rating.AA
        assert rate_capacity(400) == Rating.A
        assert rate_capacity(100) == Rating.BBB
        assert rate_capacity(20) == Rating.BB
        assert rate_capacity(10) == Rating.B

    def test_rate_profitability_positive(self):
        assert rate_profitability(15) == Rating.AAA
        assert rate_profitability(11) == Rating.AA
        assert rate_profitability(8) == Rating.A
        assert rate_profitability(4) == Rating.BBB
        assert rate_profitability(1) == Rating.BB
        assert rate_profitability(0.5) == Rating.B

    def test_rate_profitability_negative(self):
        assert rate_profitability(-5) == Rating.B
        assert rate_profitability(-15) == Rating.CCC
        assert rate_profitability(-25, is_negative=True) == Rating.CC

    def test_rate_coverage_positive(self):
        assert rate_coverage(12) == Rating.AAA
        assert rate_coverage(6) == Rating.AA
        assert rate_coverage(4) == Rating.A
        assert rate_coverage(2) == Rating.BBB
        assert rate_coverage(1) == Rating.BB
        assert rate_coverage(0.7) == Rating.B

    def test_rate_coverage_negative(self):
        assert rate_coverage(-1) == Rating.CC
        assert rate_coverage(-3) == Rating.C
        assert rate_coverage(-6) == Rating.D

    def test_rate_coverage_very_low(self):
        assert rate_coverage(0.3) == Rating.CCC

    def test_rate_dscr_project_finance(self):
        assert rate_dscr(2.5) == Rating.AAA
        assert rate_dscr(2.0) == Rating.AA
        assert rate_dscr(1.6) == Rating.A
        assert rate_dscr(1.3) == Rating.BBB
        assert rate_dscr(1.1) == Rating.BB
        assert rate_dscr(1.0) == Rating.B

    def test_rate_dscr_distressed(self):
        assert rate_dscr(0.9) == Rating.CCC
        assert rate_dscr(0.7) == Rating.CC
        assert rate_dscr(0.3) == Rating.C
        assert rate_dscr(-0.5) == Rating.D

    def test_rate_net_debt_leverage(self):
        assert rate_net_debt_leverage(0.5) == Rating.AAA
        assert rate_net_debt_leverage(3) == Rating.AA
        assert rate_net_debt_leverage(5) == Rating.A
        assert rate_net_debt_leverage(8) == Rating.BBB
        assert rate_net_debt_leverage(11) == Rating.BB
        assert rate_net_debt_leverage(15) == Rating.B

    def test_rate_net_debt_leverage_negative_ebitda(self):
        assert rate_net_debt_leverage(5, is_ebitda_negative=True) == Rating.CC

    def test_rate_net_debt_leverage_net_cash(self):
        assert rate_net_debt_leverage(-2) == Rating.AAA

    def test_rate_equity_leverage(self):
        assert rate_equity_leverage(50) == Rating.AAA
        assert rate_equity_leverage(100) == Rating.AA
        assert rate_equity_leverage(200) == Rating.A
        assert rate_equity_leverage(280) == Rating.BBB
        assert rate_equity_leverage(350) == Rating.BB
        assert rate_equity_leverage(500) == Rating.B

    def test_rate_asset_leverage(self):
        assert rate_asset_leverage(10) == Rating.AAA
        assert rate_asset_leverage(30) == Rating.AA
        assert rate_asset_leverage(50) == Rating.A
        assert rate_asset_leverage(70) == Rating.BBB
        assert rate_asset_leverage(85) == Rating.BB
        assert rate_asset_leverage(95) == Rating.B


class TestAssessCreditRating:
    """Test overall credit rating assessment."""

    def test_strong_metrics_get_high_rating(self):
        metrics = RatingMetrics(
            capacity_mw=2000,
            ebitda_to_fixed_assets=15,
            ebitda_to_interest=12,
            net_debt_to_ebitda=1,
            debt_to_equity=80,
            debt_to_assets=20,
            dscr=2.5,
        )
        assessment = assess_credit_rating(metrics)
        assert assessment.overall_rating.is_investment_grade
        assert assessment.overall_rating.value <= 3

    def test_weak_metrics_get_low_rating(self):
        metrics = RatingMetrics(
            capacity_mw=50,
            ebitda_to_fixed_assets=1,
            ebitda_to_interest=1.5,
            net_debt_to_ebitda=10,
            debt_to_equity=400,
            debt_to_assets=90,
            dscr=1.0,
        )
        assessment = assess_credit_rating(metrics)
        assert not assessment.overall_rating.is_investment_grade

    def test_distressed_override(self):
        metrics = RatingMetrics(
            capacity_mw=2000,
            ebitda_to_fixed_assets=-25,
            ebitda_to_interest=-3,
            net_debt_to_ebitda=999,
            debt_to_equity=200,
            debt_to_assets=50,
            dscr=0.3,
            is_ebitda_negative=True,
        )
        assessment = assess_credit_rating(metrics)
        assert assessment.overall_rating.is_distressed

    def test_assessment_has_all_components(self):
        metrics = RatingMetrics(
            capacity_mw=1000,
            ebitda_to_fixed_assets=10,
            ebitda_to_interest=5,
            net_debt_to_ebitda=4,
            debt_to_equity=200,
            debt_to_assets=50,
            dscr=1.5,
        )
        assessment = assess_credit_rating(metrics)
        assert "capacity" in assessment.component_ratings
        assert "profitability" in assessment.component_ratings
        assert "coverage" in assessment.component_ratings
        assert "dscr" in assessment.component_ratings
        assert "net_debt_leverage" in assessment.component_ratings
        assert "equity_leverage" in assessment.component_ratings
        assert "asset_leverage" in assessment.component_ratings

    def test_assessment_to_dict(self):
        metrics = RatingMetrics(
            capacity_mw=1000,
            ebitda_to_fixed_assets=10,
            ebitda_to_interest=5,
            net_debt_to_ebitda=4,
            debt_to_equity=200,
            debt_to_assets=50,
            dscr=1.5,
        )
        assessment = assess_credit_rating(metrics)
        d = assessment.to_dict()
        assert "overall_rating" in d
        assert "spread_bps" in d
        assert "is_investment_grade" in d
        assert "is_distressed" in d
        assert "dscr" in d


class TestRatingMetricsFromFinancials:
    """Test RatingMetrics calculation from financial data."""

    def test_positive_ebitda_metrics(self):
        metrics = calculate_rating_metrics_from_financials(
            capacity_mw=2100,
            ebitda=500e6,
            fixed_assets=3000e6,
            interest_expense=50e6,
            total_debt=2000e6,
            cash_and_equivalents=100e6,
            total_equity=1500e6,
            total_assets=3500e6,
            dscr=2.0,
        )
        assert metrics.capacity_mw == 2100
        assert not metrics.is_ebitda_negative
        assert metrics.dscr == 2.0
        assert metrics.ebitda_to_interest == 10.0  # 500/50

    def test_negative_ebitda_metrics(self):
        metrics = calculate_rating_metrics_from_financials(
            capacity_mw=2100,
            ebitda=-200e6,
            fixed_assets=3000e6,
            interest_expense=50e6,
            total_debt=2000e6,
            cash_and_equivalents=100e6,
            total_equity=1500e6,
            total_assets=3500e6,
        )
        assert metrics.is_ebitda_negative
        assert metrics.ebitda_to_interest < 0

    def test_zero_interest_expense(self):
        metrics = calculate_rating_metrics_from_financials(
            capacity_mw=1000,
            ebitda=100e6,
            fixed_assets=500e6,
            interest_expense=0,
            total_debt=0,
            cash_and_equivalents=50e6,
            total_equity=500e6,
            total_assets=500e6,
        )
        assert metrics.ebitda_to_interest == 999


class TestRatingMigration:
    """Test rating migration analysis."""

    def test_downgrade_migration(self):
        metrics_good = RatingMetrics(2000, 15, 12, 1, 80, 20, dscr=2.5)
        metrics_bad = RatingMetrics(2000, 3, 1.5, 10, 400, 90, dscr=0.8)

        baseline = assess_credit_rating(metrics_good)
        risk = assess_credit_rating(metrics_bad)

        migration = rating_migration_analysis(baseline, risk)
        assert migration["notch_change"] > 0
        assert "Downgrade" in migration["migration"]
        assert migration["spread_increase_bps"] > 0

    def test_no_change_migration(self):
        metrics = RatingMetrics(1000, 10, 5, 4, 200, 50, dscr=1.5)
        assessment = assess_credit_rating(metrics)

        migration = rating_migration_analysis(assessment, assessment)
        assert migration["notch_change"] == 0
        assert "No Change" in migration["migration"]
        assert migration["spread_increase_bps"] == 0


class TestCRPFromRatings:
    """Test Climate Risk Premium calculation from rating migration."""

    def test_crp_positive_for_downgrade(self):
        crp = calculate_crp_from_ratings(Rating.A, Rating.BB)
        assert crp > 0

    def test_crp_zero_for_no_change(self):
        crp = calculate_crp_from_ratings(Rating.A, Rating.A)
        assert crp == 0

    def test_crp_negative_for_upgrade(self):
        crp = calculate_crp_from_ratings(Rating.BB, Rating.A)
        assert crp < 0

    def test_crp_increases_with_severity(self):
        crp_1notch = calculate_crp_from_ratings(Rating.A, Rating.BBB)
        crp_3notch = calculate_crp_from_ratings(Rating.A, Rating.B)
        assert crp_3notch > crp_1notch


class TestCounterfactualRating:
    """Test counterfactual-based rating assessment."""

    def test_counterfactual_baseline_is_A(self):
        assert get_counterfactual_baseline_rating() == Rating.A

    def test_assess_with_counterfactual(self):
        metrics = RatingMetrics(
            capacity_mw=2100,
            ebitda_to_fixed_assets=5,
            ebitda_to_interest=3,
            net_debt_to_ebitda=6,
            debt_to_equity=250,
            debt_to_assets=60,
            dscr=1.2,
        )
        result = assess_rating_with_counterfactual(metrics)

        assert "counterfactual_rating" in result
        assert "scenario_rating" in result
        assert "crp_bps" in result
        assert "notch_change" in result
        assert result["counterfactual_rating"] == "A"

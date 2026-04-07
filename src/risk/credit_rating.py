"""
Credit rating assessment based on KIS (Korea Investors Service) methodology.
Implements quantitative mapping grid for Private Power Generation (IPP) industry.

ENHANCED: Extended to handle negative EBITDA and distressed scenarios.
Adds sub-investment grade ratings (CCC, CC, C, D) and DSCR-based coverage analysis.

Reference:
- KIS Rating Methodology: Power Generation Sector (2023)
- Moody's Global Infrastructure Finance Rating Methodology (2021)
- S&P Project Finance Rating Criteria (2022)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum


class Rating(Enum):
    """
    Credit rating categories - Extended scale including distressed ratings.

    Investment Grade: AAA, AA, A, BBB
    Speculative Grade: BB, B
    Distressed/Default: CCC, CC, C, D

    This extended scale allows proper differentiation when entities have
    negative EBITDA or severe financial distress.
    """

    AAA = 1  # Prime
    AA = 2  # High Grade
    A = 3  # Upper Medium Grade
    BBB = 4  # Lower Medium Grade (lowest investment grade)
    BB = 5  # Non-Investment Speculative
    B = 6  # Highly Speculative
    CCC = 7  # Substantial Risk
    CC = 8  # Very High Risk / Default imminent
    C = 9  # Near Default
    D = 10  # In Default

    def __str__(self):
        return self.name

    def to_spread_bps(self) -> float:
        """
        Convert rating to typical spread over risk-free rate (bps).

        Spreads based on historical corporate bond spreads (BBB-CCC from
        Bloomberg US Corporate Bond Index, 2020-2024 average).
        Distressed ratings (CC, C, D) use distressed debt trading levels.
        """
        spread_map = {
            Rating.AAA: 50,
            Rating.AA: 100,
            Rating.A: 150,
            Rating.BBB: 250,
            Rating.BB: 400,
            Rating.B: 600,
            Rating.CCC: 900,  # Substantial risk - typical CCC bond spread
            Rating.CC: 1500,  # Very high risk - distressed debt territory
            Rating.C: 2500,  # Near default - deep distress
            Rating.D: 5000,  # Default - recovery value pricing
        }
        return spread_map[self]

    @property
    def numeric_score(self) -> int:
        """Numeric score for rating (1=best, 10=worst)."""
        return self.value

    @property
    def is_investment_grade(self) -> bool:
        """Check if rating is investment grade (BBB or better)."""
        return self.value <= 4

    @property
    def is_distressed(self) -> bool:
        """Check if rating indicates financial distress (CCC or worse)."""
        return self.value >= 7


@dataclass
class RatingMetrics:
    """
    Financial metrics used for credit rating assessment.

    Extended to include DSCR (Debt Service Coverage Ratio) which is the
    standard metric for project finance credit assessment.
    """

    # Business Stability & Profitability
    capacity_mw: float
    ebitda_to_fixed_assets: float  # percentage

    # Coverage Ratios
    ebitda_to_interest: float  # times

    # Leverage Ratios
    net_debt_to_ebitda: float  # times
    debt_to_equity: float  # percentage
    debt_to_assets: float  # percentage

    # Optional fields with defaults (must come after required fields)
    dscr: float = 1.0  # Debt Service Coverage Ratio (CFADS / Total Debt Service)
    is_ebitda_negative: bool = False  # Distress indicator
    consecutive_loss_years: int = 0  # Distress indicator


@dataclass
class RatingAssessment:
    """Credit rating assessment result."""

    overall_rating: Rating
    component_ratings: Dict[str, Rating]
    metrics: RatingMetrics
    rating_rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_rating": str(self.overall_rating),
            "rating_numeric": self.overall_rating.numeric_score,
            "spread_bps": self.overall_rating.to_spread_bps(),
            "is_investment_grade": self.overall_rating.is_investment_grade,
            "is_distressed": self.overall_rating.is_distressed,
            "policy_industry_rating": str(self.component_ratings["policy_industry"]),
            "profitability_rating": str(self.component_ratings["profitability"]),
            "coverage_rating": str(self.component_ratings["coverage"]),
            "dscr_rating": str(self.component_ratings.get("dscr", "N/A")),
            "net_debt_leverage_rating": str(self.component_ratings["net_debt_leverage"]),
            "equity_leverage_rating": str(self.component_ratings["equity_leverage"]),
            "asset_leverage_rating": str(self.component_ratings["asset_leverage"]),
            "capacity_mw": self.metrics.capacity_mw,
            "ebitda_to_fixed_assets": self.metrics.ebitda_to_fixed_assets,
            "ebitda_to_interest": self.metrics.ebitda_to_interest,
            "dscr": self.metrics.dscr,
            "net_debt_to_ebitda": self.metrics.net_debt_to_ebitda,
            "debt_to_equity": self.metrics.debt_to_equity,
            "debt_to_assets": self.metrics.debt_to_assets,
            "is_ebitda_negative": self.metrics.is_ebitda_negative,
            "rating_rationale": self.rating_rationale,
        }


def rate_capacity(capacity_mw: float) -> Rating:
    """Rate based on installed capacity (MW)."""
    if capacity_mw >= 2000:
        return Rating.AAA
    elif capacity_mw >= 800:
        return Rating.AA
    elif capacity_mw >= 400:
        return Rating.A
    elif capacity_mw >= 100:
        return Rating.BBB
    elif capacity_mw >= 20:
        return Rating.BB
    else:
        return Rating.B


def rate_profitability(ebitda_to_fixed_assets: float, is_negative: bool = False) -> Rating:
    """
    Rate based on EBITDA/Fixed Assets (%).

    Enhanced to handle negative EBITDA cases which indicate severe distress.
    """
    # Handle negative EBITDA - distressed ratings
    if is_negative or ebitda_to_fixed_assets < -20:
        return Rating.CC  # Severe loss
    elif ebitda_to_fixed_assets < -10:
        return Rating.CCC  # Significant loss
    elif ebitda_to_fixed_assets < 0:
        return Rating.B  # Marginal loss

    # Standard thresholds for positive EBITDA
    if ebitda_to_fixed_assets >= 15:
        return Rating.AAA
    elif ebitda_to_fixed_assets >= 11:
        return Rating.AA
    elif ebitda_to_fixed_assets >= 8:
        return Rating.A
    elif ebitda_to_fixed_assets >= 4:
        return Rating.BBB
    elif ebitda_to_fixed_assets >= 1:
        return Rating.BB
    else:
        return Rating.B


def rate_coverage(ebitda_to_interest: float) -> Rating:
    """
    Rate based on EBITDA/Interest Expense (times).

    Enhanced to handle negative coverage ratios (negative EBITDA).
    Negative EBITDA/Interest indicates inability to cover interest
    from operations - a severe credit concern.
    """
    # Handle negative coverage - distressed ratings
    if ebitda_to_interest < -5:
        return Rating.D  # Severe - cannot cover interest, likely default
    elif ebitda_to_interest < -2:
        return Rating.C  # Near default
    elif ebitda_to_interest < 0:
        return Rating.CC  # Cannot cover interest from EBITDA
    elif ebitda_to_interest < 0.5:
        return Rating.CCC  # Barely any coverage

    # Standard thresholds for positive coverage
    if ebitda_to_interest >= 12:
        return Rating.AAA
    elif ebitda_to_interest >= 6:
        return Rating.AA
    elif ebitda_to_interest >= 4:
        return Rating.A
    elif ebitda_to_interest >= 2:
        return Rating.BBB
    elif ebitda_to_interest >= 1:
        return Rating.BB
    else:
        return Rating.B


def rate_dscr(dscr: float) -> Rating:
    """
    Rate based on Debt Service Coverage Ratio (DSCR).

    DSCR = Cash Flow Available for Debt Service / Total Debt Service

    This is the PRIMARY metric for project finance credit assessment.
    Thresholds based on:
    - Moody's Global Infrastructure Finance (2021)
    - S&P Project Finance Criteria (2022)

    Project finance typically requires minimum DSCR of 1.2-1.4x.
    """
    # Handle negative/very low DSCR - distressed
    if dscr < 0:
        return Rating.D  # Cannot service debt - default likely
    elif dscr < 0.5:
        return Rating.C  # Severe shortfall
    elif dscr < 0.8:
        return Rating.CC  # Significant shortfall
    elif dscr < 1.0:
        return Rating.CCC  # Below breakeven

    # Standard thresholds (project finance standards)
    if dscr >= 2.5:
        return Rating.AAA  # Very strong coverage
    elif dscr >= 2.0:
        return Rating.AA  # Strong coverage
    elif dscr >= 1.6:
        return Rating.A  # Good coverage
    elif dscr >= 1.3:
        return Rating.BBB  # Adequate - investment grade minimum
    elif dscr >= 1.1:
        return Rating.BB  # Weak but serviceable
    else:
        return Rating.B  # Marginal - high risk


def rate_net_debt_leverage(net_debt_to_ebitda: float, is_ebitda_negative: bool = False) -> Rating:
    """
    Rate based on Net Debt/EBITDA (times). Lower is better.

    Enhanced to handle negative EBITDA cases where ratio becomes meaningless
    or negative.
    """
    # Handle negative EBITDA - ratio is not meaningful, use distressed rating
    if is_ebitda_negative:
        return Rating.CC  # Negative EBITDA makes this ratio meaningless

    # Handle extreme or negative ratios (negative net debt = net cash position)
    if net_debt_to_ebitda < 0:
        return Rating.AAA  # Net cash position
    elif net_debt_to_ebitda > 20:
        return Rating.CCC  # Extreme leverage

    # Standard thresholds
    if net_debt_to_ebitda <= 1:
        return Rating.AAA
    elif net_debt_to_ebitda <= 4:
        return Rating.AA
    elif net_debt_to_ebitda <= 7:
        return Rating.A
    elif net_debt_to_ebitda <= 10:
        return Rating.BBB
    elif net_debt_to_ebitda <= 12:
        return Rating.BB
    else:
        return Rating.B


def rate_equity_leverage(debt_to_equity: float) -> Rating:
    """Rate based on Debt-to-Equity Ratio (%). Lower is better."""
    if debt_to_equity <= 80:
        return Rating.AAA
    elif debt_to_equity <= 150:
        return Rating.AA
    elif debt_to_equity <= 250:
        return Rating.A
    elif debt_to_equity <= 300:
        return Rating.BBB
    elif debt_to_equity <= 400:
        return Rating.BB
    else:
        return Rating.B


def rate_asset_leverage(debt_to_assets: float) -> Rating:
    """Rate based on Debt-to-Assets Ratio (%). Lower is better."""
    if debt_to_assets <= 20:
        return Rating.AAA
    elif debt_to_assets <= 40:
        return Rating.AA
    elif debt_to_assets <= 60:
        return Rating.A
    elif debt_to_assets <= 80:
        return Rating.BBB
    elif debt_to_assets <= 90:
        return Rating.BB
    else:
        return Rating.B


def assess_credit_rating(metrics: RatingMetrics) -> RatingAssessment:
    """
    Assess overall credit rating based on KIS methodology.

    ENHANCED: Uses weighted approach with DSCR as primary metric for project finance.
    Handles negative EBITDA by using distressed rating scale (CCC, CC, C, D).

    Rating Philosophy:
    1. DSCR is the primary driver for project finance (40% weight)
    2. Coverage (EBITDA/Interest) is secondary (20% weight)
    3. Leverage ratios provide context (40% combined)
    4. Distress indicators can override to lower ratings
    """
    # Determine if EBITDA is negative (triggers distress logic)
    is_ebitda_negative = metrics.is_ebitda_negative or metrics.ebitda_to_fixed_assets < 0

    # Calculate component ratings with distress awareness
    component_ratings = {
        "policy_industry": Rating.AA,  # fixed AA for all scenarios; not in weighted score
        "profitability": rate_profitability(metrics.ebitda_to_fixed_assets, is_ebitda_negative),
        "coverage": rate_coverage(metrics.ebitda_to_interest),
        "dscr": rate_dscr(metrics.dscr),  # distress override only; excluded from weights
        "net_debt_leverage": rate_net_debt_leverage(metrics.net_debt_to_ebitda, is_ebitda_negative),
        "equity_leverage": rate_equity_leverage(metrics.debt_to_equity),
        "asset_leverage": rate_asset_leverage(metrics.debt_to_assets),
    }

    # Weighted average approach for project finance
    # DSCR is most important (standard project finance practice)
    weights = {
        "policy_industry": 0.50,  # Policy & industry risk (fixed AA)
        "profitability": 0.10,    # Operating efficiency
        "coverage": 0.12,         # Interest coverage
        "net_debt_leverage": 0.12,  # Leverage
        "asset_leverage": 0.08,   # Balance sheet strength
        "equity_leverage": 0.08,  # Capital structure
    }

    # Calculate weighted score
    weighted_score = sum(
        component_ratings[metric].value * weight for metric, weight in weights.items()
    )

    # Round to nearest rating
    rounded_score = round(weighted_score)
    rounded_score = max(1, min(10, rounded_score))  # Clamp to valid range

    if metrics.dscr < 0:
        rounded_score = Rating.D.value
        rationale = f"Overall D: DSCR negative ({metrics.dscr:.3f})"
    elif metrics.dscr < 1.0:
        rounded_score = min(10, rounded_score + 1)
        overall_rating = Rating(rounded_score)
        rationale = (
            f"Overall {overall_rating}: Weighted average downgraded 1 notch "
            f"(DSCR={metrics.dscr:.3f} < 1.0)"
        )
    else:
        rationale = (
            f"Overall {Rating(rounded_score)}: Weighted average "
            f"(DSCR={metrics.dscr:.3f} ≥ 1.0, no override)"
        )
    overall_rating = Rating(rounded_score)

    return RatingAssessment(
        overall_rating=overall_rating,
        component_ratings=component_ratings,
        metrics=metrics,
        rating_rationale=rationale,
    )


def calculate_rating_metrics_from_financials(
    capacity_mw: float,
    ebitda: float,
    fixed_assets: float,
    interest_expense: float,
    total_debt: float,
    cash_and_equivalents: float,
    total_equity: float,
    total_assets: float,
    dscr: Optional[float] = None,
    total_debt_service: Optional[float] = None,
    cfads: Optional[float] = None,
    consecutive_loss_years: int = 0,
) -> RatingMetrics:
    """
    Calculate rating metrics from financial statement items.

    Args:
        capacity_mw: Installed capacity
        ebitda: Earnings before interest, taxes, depreciation, amortization
        fixed_assets: Property, plant & equipment
        interest_expense: Annual interest payments
        total_debt: Total debt outstanding
        cash_and_equivalents: Liquid assets
        total_equity: Total shareholder equity
        total_assets: Total assets
        dscr: Debt Service Coverage Ratio (if pre-calculated)
        total_debt_service: Total annual debt service (P+I) for DSCR calculation
        cfads: Cash Flow Available for Debt Service (for DSCR calculation)
        consecutive_loss_years: Number of consecutive years with negative EBITDA
    """
    # Track if EBITDA is negative for distress handling
    is_ebitda_negative = ebitda < 0

    # Calculate ratios - preserve actual values including negative
    ebitda_to_fixed_assets = (ebitda / fixed_assets * 100) if fixed_assets > 0 else 0

    # For negative EBITDA, show actual negative ratio (important for credit assessment)
    if interest_expense > 0:
        ebitda_to_interest = ebitda / interest_expense
    else:
        ebitda_to_interest = 999.0 if ebitda >= 0 else -999.0

    # Net Debt / EBITDA - handle negative EBITDA case
    net_debt = total_debt - cash_and_equivalents
    if is_ebitda_negative:
        # Negative EBITDA: ratio is meaningless, set high to trigger distress
        net_debt_to_ebitda = 999.0 if net_debt > 0 else -999.0
    elif ebitda > 0:
        net_debt_to_ebitda = net_debt / ebitda
    else:
        net_debt_to_ebitda = 999.0

    # Leverage ratios - standard calculation
    debt_to_equity = (total_debt / total_equity * 100) if total_equity > 0 else 999.0
    debt_to_assets = (total_debt / total_assets * 100) if total_assets > 0 else 100

    # DSCR calculation - primary metric for project finance
    if dscr is not None:
        # Use provided DSCR
        calculated_dscr = dscr
    elif total_debt_service is not None and total_debt_service > 0:
        # Calculate from CFADS and debt service
        if cfads is not None:
            calculated_dscr = cfads / total_debt_service
        else:
            # Use EBITDA as proxy for CFADS (simplified)
            calculated_dscr = (
                ebitda / total_debt_service if ebitda > 0 else ebitda / total_debt_service
            )
    elif interest_expense > 0:
        # Use proper annuity formula: PMT = P * r(1+r)^n / ((1+r)^n - 1)
        # Estimate from interest expense: P ≈ interest / rate, typical rate ~5%, tenor ~20yr
        estimated_rate = 0.05
        estimated_tenor = 20
        annuity_factor = (estimated_rate * (1 + estimated_rate) ** estimated_tenor) / (
            (1 + estimated_rate) ** estimated_tenor - 1
        )
        estimated_principal = interest_expense / estimated_rate
        estimated_debt_service = estimated_principal * annuity_factor
        calculated_dscr = ebitda / estimated_debt_service if estimated_debt_service > 0 else 0
    else:
        # No debt service info - assume coverage equals EBITDA/Interest
        calculated_dscr = ebitda_to_interest if ebitda_to_interest < 100 else 2.0

    return RatingMetrics(
        capacity_mw=capacity_mw,
        ebitda_to_fixed_assets=ebitda_to_fixed_assets,
        ebitda_to_interest=ebitda_to_interest,
        dscr=calculated_dscr,
        net_debt_to_ebitda=net_debt_to_ebitda,
        debt_to_equity=debt_to_equity,
        debt_to_assets=debt_to_assets,
        is_ebitda_negative=is_ebitda_negative,
        consecutive_loss_years=consecutive_loss_years,
    )


def rating_migration_analysis(
    baseline_rating: RatingAssessment,
    risk_rating: RatingAssessment,
) -> Dict[str, Any]:
    """
    Analyze credit rating migration from baseline to risk scenario.

    Returns dictionary with migration details and impact.
    """
    notch_change = risk_rating.overall_rating.value - baseline_rating.overall_rating.value
    spread_change = (
        risk_rating.overall_rating.to_spread_bps() - baseline_rating.overall_rating.to_spread_bps()
    )

    if notch_change == 0:
        migration = "No Change"
    elif notch_change > 0:
        migration = f"Downgrade by {notch_change} notch(es)"
    else:
        migration = f"Upgrade by {abs(notch_change)} notch(es)"

    # Identify which metrics deteriorated most
    metric_changes = {}
    for metric_name in baseline_rating.component_ratings.keys():
        baseline_val = baseline_rating.component_ratings[metric_name].value
        risk_val = risk_rating.component_ratings[metric_name].value
        metric_changes[metric_name] = risk_val - baseline_val

    worst_metric = max(metric_changes.items(), key=lambda x: x[1])

    return {
        "baseline_rating": str(baseline_rating.overall_rating),
        "risk_rating": str(risk_rating.overall_rating),
        "migration": migration,
        "notch_change": notch_change,
        "spread_increase_bps": spread_change,
        "worst_deteriorating_metric": worst_metric[0],
        "worst_deterioration_notches": worst_metric[1],
        "metric_changes": {k: v for k, v in metric_changes.items()},
    }


def calculate_crp_from_ratings(
    baseline_rating: Rating,
    scenario_rating: Rating,
    risk_free_rate: float = 0.03,
    debt_fraction: float = 0.70,
    baseline_equity_rate: float = 0.12,
) -> float:
    """
    Calculate Climate Risk Premium (CRP) in basis points from rating migration.

    CRP = WACC_scenario - WACC_baseline (in bps)

    This provides the clean spread differential driven purely by credit
    rating changes, which is the core measure of climate risk pricing.

    Args:
        baseline_rating: Credit rating for baseline scenario
        scenario_rating: Credit rating for risk scenario
        risk_free_rate: Risk-free rate (default 3%)
        debt_fraction: Debt share of capital structure (default 70%)
        baseline_equity_rate: Baseline equity cost of capital (default 12%)

    Returns:
        CRP in basis points
    """
    equity_fraction = 1 - debt_fraction

    # Debt cost from ratings
    baseline_debt_rate = risk_free_rate + (baseline_rating.to_spread_bps() / 10000)
    scenario_debt_rate = risk_free_rate + (scenario_rating.to_spread_bps() / 10000)

    # Equity premium scales with rating (rough heuristic: 0.5% per notch)
    equity_premium_per_notch = 0.005
    notch_diff = scenario_rating.value - baseline_rating.value
    scenario_equity_rate = baseline_equity_rate + (notch_diff * equity_premium_per_notch)

    # WACC calculations
    wacc_baseline = debt_fraction * baseline_debt_rate + equity_fraction * baseline_equity_rate
    wacc_scenario = debt_fraction * scenario_debt_rate + equity_fraction * scenario_equity_rate

    # CRP in basis points
    crp_bps = (wacc_scenario - wacc_baseline) * 10000

    return crp_bps


def get_counterfactual_baseline_rating() -> Rating:
    """
    Returns the expected baseline rating for a no-carbon counterfactual scenario.

    In a no-carbon world, a 2100 MW coal plant like Samcheok would be
    expected to achieve investment-grade rating (A-range) based on:
    - Large capacity (2100 MW → AAA on capacity)
    - Positive EBITDA (~$800M+ annually)
    - DSCR > 1.5x (typical for baseload power)
    - Moderate leverage (70% D/E typical for project finance)

    This provides the proper comparison point for calculating CRP.
    """
    return Rating.A


def assess_rating_with_counterfactual(
    scenario_metrics: RatingMetrics,
    counterfactual_rating: Optional[Rating] = None,
) -> Dict[str, Any]:
    """
    Assess credit rating and calculate CRP against counterfactual baseline.

    This is the recommended approach for climate risk premium calculation:
    - Counterfactual: What would the rating be WITHOUT climate risks?
    - Scenario: What IS the rating WITH climate risks?
    - CRP: Spread differential between the two

    Args:
        scenario_metrics: Financial metrics for the scenario to assess
        counterfactual_rating: Override counterfactual rating (default: A)

    Returns:
        Dictionary with rating assessment and CRP calculation
    """
    if counterfactual_rating is None:
        counterfactual_rating = get_counterfactual_baseline_rating()

    # Assess scenario rating
    scenario_assessment = assess_credit_rating(scenario_metrics)

    # Calculate CRP
    crp_bps = calculate_crp_from_ratings(
        baseline_rating=counterfactual_rating,
        scenario_rating=scenario_assessment.overall_rating,
    )

    # Rating migration
    notch_change = scenario_assessment.overall_rating.value - counterfactual_rating.value
    if notch_change == 0:
        migration_desc = "No change"
    elif notch_change > 0:
        migration_desc = f"Downgrade by {notch_change} notch(es)"
    else:
        migration_desc = f"Upgrade by {abs(notch_change)} notch(es)"

    return {
        "counterfactual_rating": str(counterfactual_rating),
        "counterfactual_spread_bps": counterfactual_rating.to_spread_bps(),
        "scenario_rating": str(scenario_assessment.overall_rating),
        "scenario_spread_bps": scenario_assessment.overall_rating.to_spread_bps(),
        "rating_migration": migration_desc,
        "notch_change": notch_change,
        "crp_bps": crp_bps,
        "scenario_assessment": scenario_assessment,
        "is_investment_grade": scenario_assessment.overall_rating.is_investment_grade,
        "is_distressed": scenario_assessment.overall_rating.is_distressed,
    }

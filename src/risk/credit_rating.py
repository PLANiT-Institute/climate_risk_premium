"""
Credit rating assessment based on KIS (Korea Investors Service) methodology.
Implements quantitative mapping grid for Private Power Generation (IPP) industry.

ENHANCED: Extended to handle negative EBITDA and distressed scenarios.
Adds sub-investment grade ratings (CCC, CC, C, D) and DSCR-based coverage analysis.

Reference:
- KIS Rating Methodology: Power Generation Sector (2023)
- Moody's Global Infrastructure Finance Rating Methodology (2021)
- S&P Project Finance Rating Criteria (2022)

All threshold constants, component weights, and spread mappings are loaded from:
  data/raw/rating_thresholds.csv
  data/raw/rating_weights.csv
  data/raw/rating_spreads.csv
  data/raw/model_assumptions.csv
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from src.data.loaders import (
    load_model_assumptions,
    load_rating_spreads,
    load_rating_thresholds,
    load_rating_weights,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level config loaded once at import time
# ---------------------------------------------------------------------------

_THRESHOLDS: Dict[str, Dict[str, float]] = load_rating_thresholds()
_WEIGHTS: Dict[str, float] = load_rating_weights()
_SPREADS: Dict[str, float] = load_rating_spreads()
_ASSUMPTIONS: Dict[str, Any] = load_model_assumptions()

# Rating evaluation order — from best to worst
_RATING_ORDER = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "CC", "C", "D"]


# ---------------------------------------------------------------------------
# Rating enum
# ---------------------------------------------------------------------------

class Rating(Enum):
    """
    Credit rating categories — extended scale including distressed ratings.

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

    def __str__(self) -> str:
        return self.name

    def to_spread_bps(self) -> float:
        """Convert rating to typical spread over risk-free rate (bps).

        Values are loaded from ``data/raw/rating_spreads.csv``.
        """
        return _SPREADS[self.name]

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


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Generic table-driven rating helpers
# ---------------------------------------------------------------------------

def _rate_higher_is_better(value: float, metric: str) -> Rating:
    """Assign rating for a metric where higher value means better credit.

    Iterates from AAA (best) to D (worst); returns the first rating whose
    threshold (minimum value) is met.  Falls back to the last rating in the
    table if no threshold is satisfied.

    Thresholds are loaded from ``data/raw/rating_thresholds.csv``.
    """
    thresholds = _THRESHOLDS[metric]
    for rating_name in _RATING_ORDER:
        if rating_name in thresholds and value >= thresholds[rating_name]:
            return Rating[rating_name]
    # Ultimate fallback — should only trigger if table has no negative sentinel
    return Rating.D


def _rate_lower_is_better(value: float, metric: str) -> Rating:
    """Assign rating for a metric where lower value means better credit.

    Iterates from AAA (best) to D (worst); returns the first rating whose
    threshold (maximum value) is not exceeded.

    Thresholds are loaded from ``data/raw/rating_thresholds.csv``.
    """
    thresholds = _THRESHOLDS[metric]
    for rating_name in _RATING_ORDER:
        if rating_name in thresholds and value <= thresholds[rating_name]:
            return Rating[rating_name]
    return Rating.D


# ---------------------------------------------------------------------------
# Component rating functions
# ---------------------------------------------------------------------------

def rate_capacity(capacity_mw: float) -> Rating:
    """Rate based on installed capacity (MW)."""
    return _rate_higher_is_better(capacity_mw, "capacity_mw")


def rate_profitability(ebitda_to_fixed_assets: float, is_negative: bool = False) -> Rating:
    """Rate based on EBITDA/Fixed Assets (%).

    The ``is_negative`` flag (derived from actual EBITDA sign) overrides to
    Rating.CC regardless of the ratio value — it indicates declared distress
    that the ratio alone may not fully capture.

    Thresholds merge the positive and distressed zones into one monotone scale;
    see ``data/raw/rating_thresholds.csv`` for breakpoints.
    """
    if is_negative:
        # Hard override: explicitly negative EBITDA = severe credit distress
        return Rating.CC
    return _rate_higher_is_better(ebitda_to_fixed_assets, "profitability_pct")


def rate_coverage(ebitda_to_interest: float) -> Rating:
    """Rate based on EBITDA/Interest Expense (times).

    Handles negative coverage ratios (negative EBITDA / inability to cover
    interest) through the distressed thresholds in the table.
    """
    return _rate_higher_is_better(ebitda_to_interest, "coverage_times")


def rate_dscr(dscr: float) -> Rating:
    """Rate based on Debt Service Coverage Ratio (DSCR).

    DSCR = Cash Flow Available for Debt Service / Total Debt Service.

    This is the PRIMARY metric for project finance credit assessment.
    Thresholds based on Moody's Global Infrastructure Finance (2021) and
    S&P Project Finance Criteria (2022).
    """
    return _rate_higher_is_better(dscr, "dscr")


def rate_net_debt_leverage(
    net_debt_to_ebitda: float, is_ebitda_negative: bool = False
) -> Rating:
    """Rate based on Net Debt/EBITDA (times). Lower is better.

    When EBITDA is negative the ratio loses meaning; Rating.CC is returned
    directly to reflect that the leverage position cannot be assessed normally.
    A net cash position (ratio < 0) maps to AAA via the lower_is_better logic.
    """
    if is_ebitda_negative:
        return Rating.CC  # Negative EBITDA makes this ratio meaningless
    if net_debt_to_ebitda < 0:
        return Rating.AAA  # Net cash position
    return _rate_lower_is_better(net_debt_to_ebitda, "net_debt_ebitda")


def rate_equity_leverage(debt_to_equity: float) -> Rating:
    """Rate based on Debt-to-Equity Ratio (%). Lower is better."""
    return _rate_lower_is_better(debt_to_equity, "equity_leverage")


def rate_asset_leverage(debt_to_assets: float) -> Rating:
    """Rate based on Debt-to-Assets Ratio (%). Lower is better."""
    return _rate_lower_is_better(debt_to_assets, "asset_leverage")


# ---------------------------------------------------------------------------
# Overall rating assessment
# ---------------------------------------------------------------------------

def assess_credit_rating(metrics: RatingMetrics) -> RatingAssessment:
    """Assess overall credit rating based on KIS methodology.

    Uses a weighted average of component ratings.  DSCR provides an
    additional one-notch downgrade override when DSCR < 1.0, reflecting
    standard project finance covenants.  Negative DSCR forces Rating.D.

    Component weights and the fixed policy/industry rating are loaded from
    ``data/raw/rating_weights.csv`` and ``data/raw/model_assumptions.csv``.
    """
    is_ebitda_negative = metrics.is_ebitda_negative or metrics.ebitda_to_fixed_assets < 0

    # Fixed sector/policy rating loaded from model_assumptions
    policy_industry_name: str = str(_ASSUMPTIONS["policy_industry_rating"])
    policy_industry_rating = Rating[policy_industry_name]

    component_ratings: Dict[str, Rating] = {
        "policy_industry": policy_industry_rating,
        "profitability": rate_profitability(metrics.ebitda_to_fixed_assets, is_ebitda_negative),
        "coverage": rate_coverage(metrics.ebitda_to_interest),
        "dscr": rate_dscr(metrics.dscr),  # distress override only; excluded from weights
        "net_debt_leverage": rate_net_debt_leverage(
            metrics.net_debt_to_ebitda, is_ebitda_negative
        ),
        "equity_leverage": rate_equity_leverage(metrics.debt_to_equity),
        "asset_leverage": rate_asset_leverage(metrics.debt_to_assets),
    }

    # Weighted average — DSCR component intentionally excluded from the weight
    # sum (it acts as an override, not a weighted input)
    weighted_score = sum(
        component_ratings[component].value * weight
        for component, weight in _WEIGHTS.items()
    )

    rounded_score = round(weighted_score)
    rounded_score = max(1, min(10, rounded_score))

    if metrics.dscr < 0:
        rounded_score = Rating.D.value
        rationale = f"Overall D: DSCR negative ({metrics.dscr:.3f})"
    elif metrics.dscr < _THRESHOLDS["dscr"]["B"]:  # B threshold from rating_thresholds.csv
        rounded_score = min(10, rounded_score + 1)
        overall_rating = Rating(rounded_score)
        _dscr_b = _THRESHOLDS["dscr"]["B"]
        rationale = (
            f"Overall {overall_rating}: Weighted average downgraded 1 notch "
            f"(DSCR={metrics.dscr:.3f} < {_dscr_b})"
        )
    else:
        _dscr_b = _THRESHOLDS["dscr"]["B"]
        rationale = (
            f"Overall {Rating(rounded_score)}: Weighted average "
            f"(DSCR={metrics.dscr:.3f} ≥ {_dscr_b}, no override)"
        )
    overall_rating = Rating(rounded_score)

    return RatingAssessment(
        overall_rating=overall_rating,
        component_ratings=component_ratings,
        metrics=metrics,
        rating_rationale=rationale,
    )


# ---------------------------------------------------------------------------
# Financial metric → RatingMetrics conversion
# ---------------------------------------------------------------------------

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
    """Calculate rating metrics from financial statement items.

    When ``dscr`` is not pre-calculated and ``total_debt_service`` is also
    unavailable, the function estimates debt service using
    ``estimated_debt_rate`` and ``estimated_debt_tenor`` from
    ``data/raw/model_assumptions.csv`` rather than hardcoded fallbacks.

    Args:
        capacity_mw: Installed capacity in MW.
        ebitda: Earnings before interest, taxes, depreciation & amortization.
        fixed_assets: Property, plant & equipment (book value).
        interest_expense: Annual interest payments.
        total_debt: Total debt outstanding.
        cash_and_equivalents: Liquid assets.
        total_equity: Total shareholder equity.
        total_assets: Total assets.
        dscr: Pre-calculated DSCR; skips estimation when provided.
        total_debt_service: Annual P+I for DSCR calculation.
        cfads: Cash Flow Available for Debt Service.
        consecutive_loss_years: Consecutive years with negative EBITDA.
    """
    is_ebitda_negative = ebitda < 0

    ebitda_to_fixed_assets = (ebitda / fixed_assets * 100) if fixed_assets > 0 else 0.0

    if interest_expense > 0:
        ebitda_to_interest = ebitda / interest_expense
    else:
        ebitda_to_interest = 999.0 if ebitda >= 0 else -999.0

    net_debt = total_debt - cash_and_equivalents
    if is_ebitda_negative:
        net_debt_to_ebitda = 999.0 if net_debt > 0 else -999.0
    elif ebitda > 0:
        net_debt_to_ebitda = net_debt / ebitda
    else:
        net_debt_to_ebitda = 999.0

    debt_to_equity = (total_debt / total_equity * 100) if total_equity > 0 else 999.0
    debt_to_assets = (total_debt / total_assets * 100) if total_assets > 0 else 100.0

    # DSCR — use provided value, or estimate from config-loaded fallback parameters
    if dscr is not None:
        calculated_dscr = dscr
    elif total_debt_service is not None and total_debt_service > 0:
        if cfads is not None:
            calculated_dscr = cfads / total_debt_service
        else:
            calculated_dscr = ebitda / total_debt_service
    elif interest_expense > 0:
        # Estimate debt service via annuity formula using config-defined fallback params
        est_rate = float(_ASSUMPTIONS["estimated_debt_rate"])
        est_tenor = float(_ASSUMPTIONS["estimated_debt_tenor"])
        annuity_factor = (est_rate * (1 + est_rate) ** est_tenor) / (
            (1 + est_rate) ** est_tenor - 1
        )
        estimated_principal = interest_expense / est_rate
        estimated_debt_service = estimated_principal * annuity_factor
        calculated_dscr = ebitda / estimated_debt_service if estimated_debt_service > 0 else 0.0
    else:
        # Sentinel check: if coverage ratio is at the "infinity" sentinel,
        # use the configured fallback DSCR rather than the sentinel value itself
        _sentinel = float(_ASSUMPTIONS["coverage_infinity_sentinel"])
        _fallback = float(_ASSUMPTIONS["ebitda_coverage_fallback_dscr"])
        calculated_dscr = ebitda_to_interest if ebitda_to_interest < _sentinel else _fallback

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


# ---------------------------------------------------------------------------
# CRP and counterfactual helpers
# ---------------------------------------------------------------------------

def calculate_crp_from_ratings(
    baseline_rating: Rating,
    scenario_rating: Rating,
    risk_free_rate: float,
    debt_fraction: float,
) -> float:
    """Calculate Climate Risk Premium (CRP) in basis points from rating migration.

    Algorithm:
        CRP = (WACC_scenario − WACC_baseline) × 10⁴

    where WACC uses debt cost from rating spreads and equity cost scaled by
    notch difference.  ``baseline_equity_rate`` and ``equity_premium_per_notch``
    are loaded from ``data/raw/model_assumptions.csv``.

    Args:
        baseline_rating: Credit rating for the counterfactual (no-risk) scenario.
        scenario_rating: Credit rating for the climate-risk scenario.
        risk_free_rate: Risk-free rate (plant-specific, from plant_parameters.csv).
        debt_fraction: Debt share of capital structure.

    Returns:
        CRP in basis points.
    """
    equity_fraction = 1.0 - debt_fraction
    equity_premium_per_notch = float(_ASSUMPTIONS["equity_premium_per_notch"])
    baseline_equity_rate = float(_ASSUMPTIONS["baseline_equity_rate"])

    baseline_debt_rate = risk_free_rate + (baseline_rating.to_spread_bps() / 10000)
    scenario_debt_rate = risk_free_rate + (scenario_rating.to_spread_bps() / 10000)

    notch_diff = scenario_rating.value - baseline_rating.value
    scenario_equity_rate = baseline_equity_rate + (notch_diff * equity_premium_per_notch)

    wacc_baseline = debt_fraction * baseline_debt_rate + equity_fraction * baseline_equity_rate
    wacc_scenario = debt_fraction * scenario_debt_rate + equity_fraction * scenario_equity_rate

    return (wacc_scenario - wacc_baseline) * 10000


def get_counterfactual_baseline_rating() -> Rating:
    """Return the counterfactual credit rating (no climate transition risk).

    The rating is loaded from ``data/raw/model_assumptions.csv``
    (``counterfactual_rating`` key).  Default in the config file is ``A``,
    reflecting that a 2,100 MW baseload plant with no carbon exposure would
    be expected to achieve upper-medium-grade status based on capacity scale,
    positive EBITDA, and DSCR > 1.5x at standard project finance leverage.
    """
    rating_name: str = str(_ASSUMPTIONS["counterfactual_rating"])
    return Rating[rating_name]


def rating_migration_analysis(
    baseline_rating: RatingAssessment,
    risk_rating: RatingAssessment,
) -> Dict[str, Any]:
    """Analyse credit rating migration from baseline to risk scenario.

    Returns a dictionary with migration details and impact metrics.
    """
    notch_change = risk_rating.overall_rating.value - baseline_rating.overall_rating.value
    spread_change = (
        risk_rating.overall_rating.to_spread_bps()
        - baseline_rating.overall_rating.to_spread_bps()
    )

    if notch_change == 0:
        migration = "No Change"
    elif notch_change > 0:
        migration = f"Downgrade by {notch_change} notch(es)"
    else:
        migration = f"Upgrade by {abs(notch_change)} notch(es)"

    metric_changes = {
        metric: risk_rating.component_ratings[metric].value
        - baseline_rating.component_ratings[metric].value
        for metric in baseline_rating.component_ratings
    }
    worst_metric = max(metric_changes.items(), key=lambda x: x[1])

    return {
        "baseline_rating": str(baseline_rating.overall_rating),
        "risk_rating": str(risk_rating.overall_rating),
        "migration": migration,
        "notch_change": notch_change,
        "spread_increase_bps": spread_change,
        "worst_deteriorating_metric": worst_metric[0],
        "worst_deterioration_notches": worst_metric[1],
        "metric_changes": dict(metric_changes),
    }


def assess_rating_with_counterfactual(
    scenario_metrics: RatingMetrics,
    counterfactual_rating: Optional[Rating] = None,
) -> Dict[str, Any]:
    """Assess credit rating and calculate CRP against counterfactual baseline.

    This is the recommended approach for climate risk premium calculation:
    - Counterfactual: rating WITHOUT climate risks (loaded from config)
    - Scenario: rating WITH climate risks
    - CRP: spread differential between the two

    Args:
        scenario_metrics: Financial metrics for the scenario to assess.
        counterfactual_rating: Override counterfactual rating; defaults to
            ``get_counterfactual_baseline_rating()``.

    Returns:
        Dictionary with rating assessment and CRP calculation.
    """
    if counterfactual_rating is None:
        counterfactual_rating = get_counterfactual_baseline_rating()

    scenario_assessment = assess_credit_rating(scenario_metrics)

    # Note: risk_free_rate and debt_fraction are not available here;
    # callers who need CRP should use calculate_crp_from_ratings directly.
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
        "scenario_assessment": scenario_assessment,
        "is_investment_grade": scenario_assessment.overall_rating.is_investment_grade,
        "is_distressed": scenario_assessment.overall_rating.is_distressed,
    }

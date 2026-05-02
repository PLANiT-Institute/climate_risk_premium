"""
Translate expected losses into financing spreads and Climate Risk Premium (CRP).

ENHANCED: Updated to work with extended credit rating scale (AAA to D)
and counterfactual-based CRP calculation for proper climate risk pricing.

All model-level constants (baseline_equity_rate, equity_premium_per_notch,
equity_slope, spread_slope, baseline_spread_bps) are loaded from
``data/raw/model_assumptions.csv``.  Plant-specific parameters (risk_free_rate,
debt_fraction, equity_fraction) must be supplied by the caller via ``params``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from src.data.loaders import load_model_assumptions

# ---------------------------------------------------------------------------
# Module-level config loaded once at import time
# ---------------------------------------------------------------------------

_ASSUMPTIONS: Dict[str, Any] = load_model_assumptions()

_BASELINE_EQUITY_RATE: float = float(_ASSUMPTIONS["baseline_equity_rate"])
_EQUITY_PREMIUM_PER_NOTCH: float = float(_ASSUMPTIONS["equity_premium_per_notch"])
_EQUITY_SLOPE: float = float(_ASSUMPTIONS["equity_slope"])
_SPREAD_SLOPE: float = float(_ASSUMPTIONS["spread_slope"])
_BASELINE_SPREAD_BPS: float = float(_ASSUMPTIONS["baseline_spread_bps"])


# ---------------------------------------------------------------------------
# Output dataclass
# ---------------------------------------------------------------------------

@dataclass
class FinancingImpact:
    expected_loss_pct: float
    npv_loss_million: float
    debt_spread_bps: float
    equity_premium_pct: float
    crp_bps: float
    wacc_baseline_pct: float
    wacc_adjusted_pct: float

    @property
    def climate_risk_premium_bps(self) -> float:
        """Alias for crp_bps for clearer naming."""
        return self.crp_bps

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expected_loss_pct": self.expected_loss_pct,
            "npv_loss_million": self.npv_loss_million,
            "debt_spread_bps": self.debt_spread_bps,
            "equity_premium_pct": self.equity_premium_pct,
            "crp_bps": self.crp_bps,
            "climate_risk_premium_bps": self.crp_bps,
            "wacc_baseline_pct": self.wacc_baseline_pct,
            "wacc_adjusted_pct": self.wacc_adjusted_pct,
        }


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

def calculate_expected_loss(
    baseline_npv: float,
    risk_adjusted_npv: float,
    total_capex: float,
) -> float:
    """Calculate expected loss as percentage of capital at risk.

    Algorithm:
        EL% = (Baseline NPV − Risk-Adjusted NPV) / Total CAPEX × 100
    """
    npv_loss = baseline_npv - risk_adjusted_npv
    if total_capex <= 0:
        return 0.0
    return max(0.0, (npv_loss / total_capex) * 100)


def map_expected_loss_to_spreads(
    expected_loss_pct: float,
    npv_loss: float,
    params: Dict[str, Any],
    rating_spread_bps: float | None = None,
) -> FinancingImpact:
    """Map expected loss to financing cost impacts (reduced-form model).

    When ``rating_spread_bps`` is provided, it overrides the linear spread-slope
    model and the function acts as a structural (rating-based) model.

    ``baseline_equity_rate``, ``equity_slope``, ``spread_slope``, and
    ``baseline_spread_bps`` come from ``data/raw/model_assumptions.csv``.

    Args:
        expected_loss_pct: Expected loss as % of CAPEX.
        npv_loss: Absolute NPV loss in USD.
        params: Plant-specific financing parameters; must contain
            ``risk_free_rate``, ``debt_fraction``, ``equity_fraction``.
        rating_spread_bps: Optional explicit rating-based spread.  When
            supplied, overrides the linear spread-slope calculation.
    """
    risk_free_rate = float(params["risk_free_rate"])
    debt_fraction = float(params["debt_fraction"])
    equity_fraction = float(params["equity_fraction"])

    baseline_debt_rate = risk_free_rate + (_BASELINE_SPREAD_BPS / 10000)

    if rating_spread_bps is not None:
        debt_spread = rating_spread_bps
    else:
        debt_spread = _BASELINE_SPREAD_BPS + expected_loss_pct * _SPREAD_SLOPE

    adjusted_debt_rate = risk_free_rate + (debt_spread / 10000)

    equity_premium_pct = expected_loss_pct * _EQUITY_SLOPE
    adjusted_equity_rate = _BASELINE_EQUITY_RATE + (equity_premium_pct / 100)

    wacc_baseline = (
        debt_fraction * baseline_debt_rate + equity_fraction * _BASELINE_EQUITY_RATE
    )
    wacc_adjusted = debt_fraction * adjusted_debt_rate + equity_fraction * adjusted_equity_rate

    crp = (wacc_adjusted - wacc_baseline) * 10000

    return FinancingImpact(
        expected_loss_pct=expected_loss_pct,
        npv_loss_million=npv_loss / 1e6,
        debt_spread_bps=debt_spread,
        equity_premium_pct=equity_premium_pct,
        crp_bps=crp,
        wacc_baseline_pct=wacc_baseline * 100,
        wacc_adjusted_pct=wacc_adjusted * 100,
    )


def calculate_financing_from_rating(
    rating_spread_bps: float,
    baseline_spread_bps: float,
    npv_loss: float,
    total_capex: float,
    params: Dict[str, Any],
) -> FinancingImpact:
    """Calculate financing impact for a specific credit rating spread.

    ``baseline_equity_rate`` and ``equity_slope`` come from
    ``data/raw/model_assumptions.csv``.

    Args:
        rating_spread_bps: Spread for the scenario's credit rating (e.g. 250 for BBB).
        baseline_spread_bps: Spread for the baseline scenario.
        npv_loss: Absolute NPV loss (Baseline NPV − Scenario NPV) in USD.
        total_capex: Total CAPEX for expected loss % calculation.
        params: Must contain ``risk_free_rate``, ``debt_fraction``,
            ``equity_fraction``.
    """
    risk_free_rate = float(params["risk_free_rate"])
    debt_fraction = float(params["debt_fraction"])
    equity_fraction = float(params["equity_fraction"])

    expected_loss_pct = 0.0
    if total_capex > 0:
        expected_loss_pct = max(0.0, (npv_loss / total_capex) * 100)

    adjusted_debt_rate = risk_free_rate + (rating_spread_bps / 10000)
    baseline_debt_rate = risk_free_rate + (baseline_spread_bps / 10000)

    equity_premium_pct = expected_loss_pct * _EQUITY_SLOPE
    adjusted_equity_rate = _BASELINE_EQUITY_RATE + (equity_premium_pct / 100)

    wacc_baseline = (
        debt_fraction * baseline_debt_rate + equity_fraction * _BASELINE_EQUITY_RATE
    )
    wacc_adjusted = debt_fraction * adjusted_debt_rate + equity_fraction * adjusted_equity_rate

    crp = (wacc_adjusted - wacc_baseline) * 10000

    return FinancingImpact(
        expected_loss_pct=expected_loss_pct,
        npv_loss_million=npv_loss / 1e6,
        debt_spread_bps=rating_spread_bps,
        equity_premium_pct=equity_premium_pct,
        crp_bps=crp,
        wacc_baseline_pct=wacc_baseline * 100,
        wacc_adjusted_pct=wacc_adjusted * 100,
    )


def calculate_financing_with_counterfactual(
    scenario_spread_bps: float,
    counterfactual_spread_bps: float,
    npv_loss: float,
    total_capex: float,
    params: Dict[str, Any],
    scenario_notch: int = 6,
    counterfactual_notch: int = 3,
) -> FinancingImpact:
    """Calculate financing impact using counterfactual baseline comparison.

    This is the standard approach for Climate Risk Premium calculation:
    - Counterfactual: investment-grade rating (A) assuming no carbon pricing.
    - Scenario: actual rating with all climate risks priced in.

    Algorithm:
        CRP = (WACC_scenario − WACC_counterfactual) × 10⁴

    ``baseline_equity_rate`` and ``equity_premium_per_notch`` come from
    ``data/raw/model_assumptions.csv``.

    Args:
        scenario_spread_bps: Credit spread for the scenario (from Rating.to_spread_bps()).
        counterfactual_spread_bps: Credit spread for counterfactual baseline.
        npv_loss: Absolute NPV loss (Counterfactual NPV − Scenario NPV) in USD.
        total_capex: Total CAPEX for expected loss % calculation.
        params: Must contain ``risk_free_rate``, ``debt_fraction``,
            ``equity_fraction``.
        scenario_notch: Rating ordinal for scenario (1=AAA … 10=D).
        counterfactual_notch: Rating ordinal for counterfactual (default 3 = A).

    Returns:
        FinancingImpact with CRP calculated against counterfactual.
    """
    risk_free_rate = float(params["risk_free_rate"])
    debt_fraction = float(params["debt_fraction"])
    equity_fraction = float(params["equity_fraction"])

    expected_loss_pct = 0.0
    if total_capex > 0:
        expected_loss_pct = max(0.0, (npv_loss / total_capex) * 100)

    counterfactual_debt_rate = risk_free_rate + (counterfactual_spread_bps / 10000)
    scenario_debt_rate = risk_free_rate + (scenario_spread_bps / 10000)

    notch_diff = scenario_notch - counterfactual_notch
    equity_premium_pct = notch_diff * (_EQUITY_PREMIUM_PER_NOTCH * 100)
    scenario_equity_rate = _BASELINE_EQUITY_RATE + (equity_premium_pct / 100)

    wacc_counterfactual = (
        debt_fraction * counterfactual_debt_rate + equity_fraction * _BASELINE_EQUITY_RATE
    )
    wacc_scenario = debt_fraction * scenario_debt_rate + equity_fraction * scenario_equity_rate

    crp = (wacc_scenario - wacc_counterfactual) * 10000

    return FinancingImpact(
        expected_loss_pct=expected_loss_pct,
        npv_loss_million=npv_loss / 1e6,
        debt_spread_bps=scenario_spread_bps,
        equity_premium_pct=equity_premium_pct,
        crp_bps=crp,
        wacc_baseline_pct=wacc_counterfactual * 100,
        wacc_adjusted_pct=wacc_scenario * 100,
    )

"""
Translate expected losses into financing spreads and Climate Risk Premium (CRP).

ENHANCED: Updated to work with extended credit rating scale (AAA to D)
and counterfactual-based CRP calculation for proper climate risk pricing.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional


def _load_financing_defaults() -> dict:
    """Load default financing parameters from CSV."""
    csv_path = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "financing_parameters.csv"
    if not csv_path.exists():
        return {}
    defaults = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            defaults[row.get("param_name", row.get("parameter", ""))] = float(row["value"])
    return defaults


_FINANCING_DEFAULTS = _load_financing_defaults()


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
            "climate_risk_premium_bps": self.crp_bps,  # Include alias in export
            "wacc_baseline_pct": self.wacc_baseline_pct,
            "wacc_adjusted_pct": self.wacc_adjusted_pct,
        }


def calculate_expected_loss(
    baseline_npv: float,
    risk_adjusted_npv: float,
    total_capex: float,
) -> float:
    """
    Calculate expected loss as percentage of capital at risk.
    Expected Loss % = (Baseline NPV - Risk-Adjusted NPV) / Total CAPEX * 100
    """
    npv_loss = baseline_npv - risk_adjusted_npv
    if total_capex <= 0:
        return 0.0
    expected_loss_pct = (npv_loss / total_capex) * 100
    return max(0.0, expected_loss_pct)  # Floor at zero


def map_expected_loss_to_spreads(
    expected_loss_pct: float,
    npv_loss: float,
    params: Dict[str, Any],
    rating_spread_bps: Optional[float] = None,
) -> FinancingImpact:
    """
    Map expected loss to financing cost impacts (debt spreads, equity premiums).
    Calculate Climate Risk Premium (CRP) and adjusted WACC.

    Args:
        expected_loss_pct: Expected loss as % of CAPEX
        npv_loss: Absolute NPV loss
        params: Financing parameters
        rating_spread_bps: Optional explicit spread from credit rating model.
                           If provided, overrides the linear spread slope model.
    """
    # Extract parameters
    spread_slope = float(params.get("spread_slope_bps_per_pct", _FINANCING_DEFAULTS.get("spread_slope_bps_per_pct", 50)))
    equity_slope = float(params.get("equity_slope_pct_per_pct", _FINANCING_DEFAULTS.get("equity_slope_pct_per_pct", 0.8)))
    baseline_spread = float(params.get("baseline_spread_bps", _FINANCING_DEFAULTS.get("baseline_spread_bps", 150)))
    risk_free_rate = float(params.get("risk_free_rate", _FINANCING_DEFAULTS.get("risk_free_rate", 0.03)))
    debt_fraction = float(params.get("debt_fraction", _FINANCING_DEFAULTS.get("debt_fraction", 0.70)))
    equity_fraction = float(params.get("equity_fraction", _FINANCING_DEFAULTS.get("equity_fraction", 0.30)))

    # Baseline debt cost
    baseline_debt_rate = risk_free_rate + (baseline_spread / 10000)

    # Risk-adjusted debt spread
    if rating_spread_bps is not None:
        # Use the explicit rating-based spread (Structural Model)
        debt_spread = rating_spread_bps
    else:
        # Fallback to linear model (Reduced Form Model)
        debt_spread = baseline_spread + expected_loss_pct * spread_slope

    adjusted_debt_rate = risk_free_rate + (debt_spread / 10000)

    # Equity cost (baseline equity return ~12%, adjusted by risk premium)
    baseline_equity_rate = float(params.get("baseline_equity_rate", _FINANCING_DEFAULTS.get("baseline_equity_rate", 0.12)))
    equity_premium_pct = expected_loss_pct * equity_slope
    adjusted_equity_rate = baseline_equity_rate + (equity_premium_pct / 100)

    # WACC calculations
    # Tax shield ignored for simplicity
    wacc_baseline = debt_fraction * baseline_debt_rate + equity_fraction * baseline_equity_rate
    wacc_adjusted = debt_fraction * adjusted_debt_rate + equity_fraction * adjusted_equity_rate

    # Climate Risk Premium (increase in total cost of capital)
    crp = (wacc_adjusted - wacc_baseline) * 10000  # in bps

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
    """
    Calculate financing impact based on a specific credit rating spread.

    Args:
        rating_spread_bps: Spread for the scenario's credit rating
            (e.g., 250 for BBB)
        baseline_spread_bps: Spread for the baseline scenario
        npv_loss: Absolute NPV loss (Baseline NPV - Scenario NPV)
        total_capex: Total CAPEX for expected loss % calculation
        params: Financing parameters
    """
    # Extract parameters
    equity_slope = float(params.get("equity_slope_pct_per_pct", _FINANCING_DEFAULTS.get("equity_slope_pct_per_pct", 0.8)))
    risk_free_rate = float(params.get("risk_free_rate", _FINANCING_DEFAULTS.get("risk_free_rate", 0.03)))
    debt_fraction = float(params.get("debt_fraction", _FINANCING_DEFAULTS.get("debt_fraction", 0.70)))
    equity_fraction = float(params.get("equity_fraction", _FINANCING_DEFAULTS.get("equity_fraction", 0.30)))

    # Calculate Expected Loss % (for reporting purposes, even if not driving spread)
    expected_loss_pct = 0.0
    if total_capex > 0:
        expected_loss_pct = max(0.0, (npv_loss / total_capex) * 100)

    # 1. Debt Cost
    # Use the explicit rating spread
    debt_spread = rating_spread_bps
    adjusted_debt_rate = risk_free_rate + (debt_spread / 10000)

    # Baseline debt cost (for comparison)
    baseline_debt_rate = risk_free_rate + (baseline_spread_bps / 10000)

    # 2. Equity Cost
    # Linear model for equity premium (no credit rating equivalent for equity)
    # Could scale by spread increase ratio, but slope approach is safer.
    baseline_equity_rate = float(params.get("baseline_equity_rate", _FINANCING_DEFAULTS.get("baseline_equity_rate", 0.12)))
    equity_premium_pct = expected_loss_pct * equity_slope
    adjusted_equity_rate = baseline_equity_rate + (equity_premium_pct / 100)

    # 3. WACC
    wacc_baseline = debt_fraction * baseline_debt_rate + equity_fraction * baseline_equity_rate
    wacc_adjusted = debt_fraction * adjusted_debt_rate + equity_fraction * adjusted_equity_rate

    # 4. Climate Risk Premium (CRP)
    crp = (wacc_adjusted - wacc_baseline) * 10000  # in bps

    return FinancingImpact(
        expected_loss_pct=expected_loss_pct,
        npv_loss_million=npv_loss / 1e6,
        debt_spread_bps=debt_spread,
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
    """
    Calculate financing impact using counterfactual baseline comparison.

    This is the proper approach for Climate Risk Premium calculation:
    - Counterfactual: Investment-grade rating (A) assuming no carbon pricing
    - Scenario: Actual rating with all climate risks priced in

    CRP = WACC(scenario) - WACC(counterfactual)

    This ensures meaningful spread differential even when all current
    scenarios have negative EBITDA (due to carbon costs).

    Args:
        scenario_spread_bps: Credit spread for the scenario (from Rating.to_spread_bps())
        counterfactual_spread_bps: Credit spread for counterfactual (default A = 150 bps)
        npv_loss: Absolute NPV loss (Counterfactual NPV - Scenario NPV)
        total_capex: Total CAPEX for expected loss % calculation
        params: Financing parameters
        scenario_notch: Rating notch for scenario (1=AAA, 10=D)
        counterfactual_notch: Rating notch for counterfactual (default 3=A)

    Returns:
        FinancingImpact with CRP calculated against counterfactual
    """
    # Extract parameters
    risk_free_rate = float(params.get("risk_free_rate", _FINANCING_DEFAULTS.get("risk_free_rate", 0.03)))
    debt_fraction = float(params.get("debt_fraction", _FINANCING_DEFAULTS.get("debt_fraction", 0.70)))
    equity_fraction = float(params.get("equity_fraction", _FINANCING_DEFAULTS.get("equity_fraction", 0.30)))
    baseline_equity_rate = float(params.get("baseline_equity_rate", _FINANCING_DEFAULTS.get("baseline_equity_rate", 0.12)))

    # Calculate Expected Loss % (for reporting)
    expected_loss_pct = 0.0
    if total_capex > 0:
        expected_loss_pct = max(0.0, (npv_loss / total_capex) * 100)

    # Debt costs from rating spreads
    counterfactual_debt_rate = risk_free_rate + (counterfactual_spread_bps / 10000)
    scenario_debt_rate = risk_free_rate + (scenario_spread_bps / 10000)

    # Equity premium scales with rating (0.5% per notch deterioration)
    equity_premium_per_notch = 0.005
    notch_diff = scenario_notch - counterfactual_notch
    equity_premium_pct = notch_diff * (equity_premium_per_notch * 100)  # in percentage points
    scenario_equity_rate = baseline_equity_rate + (equity_premium_pct / 100)

    # WACC calculations
    wacc_counterfactual = (
        debt_fraction * counterfactual_debt_rate + equity_fraction * baseline_equity_rate
    )
    wacc_scenario = debt_fraction * scenario_debt_rate + equity_fraction * scenario_equity_rate

    # CRP = spread differential in basis points
    crp = (wacc_scenario - wacc_counterfactual) * 10000

    return FinancingImpact(
        expected_loss_pct=expected_loss_pct,
        npv_loss_million=npv_loss / 1e6,
        debt_spread_bps=scenario_spread_bps,
        equity_premium_pct=equity_premium_pct,
        crp_bps=crp,
        wacc_baseline_pct=wacc_counterfactual * 100,  # Counterfactual as baseline
        wacc_adjusted_pct=wacc_scenario * 100,
    )

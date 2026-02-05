"""
Financial metrics: NPV, IRR, DSCR, LLCR for project finance analysis.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any
import numpy as np
import numpy_financial as npf

from src.financials.cashflow import CashFlowTimeSeries


@dataclass
class FinancialMetrics:
    """Project finance metrics."""
    npv: float
    irr: float
    avg_dscr: float
    min_dscr: float
    llcr: float
    payback_years: float | None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "npv_million": self.npv / 1e6,
            "irr_pct": self.irr * 100,
            "avg_dscr": self.avg_dscr,
            "min_dscr": self.min_dscr,
            "llcr": self.llcr,
            "payback_years": self.payback_years,
        }


@dataclass
class DebtStructure:
    """Debt financing structure."""
    debt_amount: float
    interest_rate: float
    tenor_years: int
    annual_debt_service: float
    principal_schedule: np.ndarray
    interest_schedule: np.ndarray


def calculate_debt_service(
    total_capex: float,
    debt_fraction: float,
    interest_rate: float,
    tenor_years: int
) -> DebtStructure:
    """
    Calculate debt service schedule for project finance.
    Uses level debt service (annuity).
    """
    debt_amount = total_capex * debt_fraction

    # Annual debt service (level payment)
    annual_ds = -npf.pmt(interest_rate, tenor_years, debt_amount)

    # Build amortization schedule
    principal = np.zeros(tenor_years)
    interest = np.zeros(tenor_years)
    balance = debt_amount

    for i in range(tenor_years):
        interest[i] = balance * interest_rate
        principal[i] = annual_ds - interest[i]
        balance -= principal[i]

    return DebtStructure(
        debt_amount=debt_amount,
        interest_rate=interest_rate,
        tenor_years=tenor_years,
        annual_debt_service=annual_ds,
        principal_schedule=principal,
        interest_schedule=interest,
    )


def calculate_metrics(
    cashflows: CashFlowTimeSeries,
    plant_params: Dict[str, Any],
) -> FinancialMetrics:
    """
    Calculate NPV, IRR, DSCR, LLCR from cash flow time series.
    """
    # Extract parameters
    total_capex = float(plant_params.get("total_capex_million", 3200)) * 1e6
    discount_rate = float(plant_params.get("discount_rate", 0.08))
    debt_fraction = float(plant_params.get("debt_fraction", 0.70))
    equity_fraction = float(plant_params.get("equity_fraction", 0.30))
    debt_interest = float(plant_params.get("debt_interest_rate", 0.05))
    debt_tenor = int(plant_params.get("debt_tenor_years", 20))

    # Free cash flows from operations
    fcf = cashflows.free_cash_flow

    # NPV of free cash flows minus initial investment
    # npf.npv discounts from period 1, so we add FCFs discounted and subtract initial investment
    npv = npf.npv(discount_rate, fcf) - total_capex

    # IRR calculation requires initial investment (negative) at t=0
    # Create cash flow array: [-CAPEX, FCF_1, FCF_2, ..., FCF_n]
    fcf_with_investment = np.concatenate([[-total_capex], fcf])
    try:
        irr = npf.irr(fcf_with_investment)
    except Exception:
        irr = np.nan

    # Debt service calculations
    debt_struct = calculate_debt_service(total_capex, debt_fraction, debt_interest, debt_tenor)

    # DSCR (Debt Service Coverage Ratio) = EBITDA / Debt Service
    # Only calculate for years where debt is outstanding
    n_debt_years = min(debt_tenor, len(cashflows.ebitda))
    dscr = np.zeros(n_debt_years)
    
    # Use Tax-Adjusted Cash Flow Available for Debt Service (CFADS)
    # CFADS = EBITDA - Tax (paid) - Capex + Working Capital Changes
    # For simplicity, often DSCR uses EBITDA / Debt Service in early stage models,
    # but since we now have tax, we should be more precise:
    # CFADS = Net Income + Depreciation + Interest + Amortization - Capex - Tax
    # Wait, Net Income = EBIT - Interest - Tax.
    # So Net Income + Interest + Depreciation = EBITDA - Tax.
    # So CFADS = EBITDA - Tax.
    
    # Calculate Tax from cashflows if available, else 0
    tax_paid = getattr(cashflows, 'tax_expense', np.zeros(len(cashflows.ebitda)))
    cfads = cashflows.ebitda - tax_paid - cashflows.capex
    
    for i in range(n_debt_years):
        if debt_struct.annual_debt_service > 0:
            dscr[i] = cfads[i] / debt_struct.annual_debt_service
        else:
            dscr[i] = np.inf

    avg_dscr = np.mean(dscr) if len(dscr) > 0 else 0.0
    min_dscr = np.min(dscr) if len(dscr) > 0 else 0.0

    # LLCR (Loan Life Coverage Ratio) = NPV of cash flows during loan life / Debt outstanding
    # NPV of available cash flows for debt service over loan life
    # CFADS for LLCR
    cash_available = cfads[:n_debt_years]
    llcr_numerator = npf.npv(debt_interest, cash_available)
    llcr = llcr_numerator / debt_struct.debt_amount if debt_struct.debt_amount > 0 else 0.0

    # Payback period (using FCF including initial investment)
    cumulative_fcf = np.cumsum(fcf_with_investment)
    # Find where cumulative FCF becomes positive (recovers initial investment)
    payback_idx = np.where(cumulative_fcf >= 0)[0]
    # Year 0 is investment year, so payback years is the index directly
    payback_years = float(payback_idx[0]) if len(payback_idx) > 0 else None

    return FinancialMetrics(
        npv=npv,
        irr=irr if not np.isnan(irr) else 0.0,
        avg_dscr=avg_dscr,
        min_dscr=min_dscr,
        llcr=llcr,
        payback_years=payback_years,
    )

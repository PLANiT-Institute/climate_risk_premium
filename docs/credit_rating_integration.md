# Credit Rating Integration - KIS Methodology

## Overview

We've successfully integrated the **Korea Investors Service (KIS)** credit rating methodology for Private Power Generation (IPP) into our Climate Risk Premium framework.

## What Was Added

### 1. Credit Rating Module (`src/risk/credit_rating.py`)

**Key Features:**
- Implements KIS quantitative mapping grid (AAA to B ratings)
- 6 rating metrics across 3 categories:
  - **Business Stability**: Capacity (MW), EBITDA/Fixed Assets
  - **Coverage Ratios**: EBITDA/Interest Expense
  - **Leverage Ratios**: Net Debt/EBITDA, Debt/Equity, Debt/Assets
- Conservative rating methodology (worst component drives overall)
- Automatic spread mapping (AAA=50bps, AA=100bps, A=150bps, BBB=250bps, BB=400bps, B=600bps)

### 2. KIS Rating Criteria

| Metric | AAA | AA | A | BBB | BB | B |
|--------|-----|----|----|-----|----|----|
| **Capacity (MW)** | ≥2000 | ≥800 | ≥400 | ≥100 | ≥20 | <20 |
| **EBITDA/Fixed Assets (%)** | ≥15 | ≥11 | ≥8 | ≥4 | ≥1 | <1 |
| **EBITDA/Interest (x)** | ≥12 | ≥6 | ≥4 | ≥2 | ≥1 | <1 |
| **Net Debt/EBITDA (x)** | ≤1 | ≤4 | ≤7 | ≤10 | ≤12 | >12 |
| **Debt/Equity (%)** | ≤80 | ≤150 | ≤250 | ≤300 | ≤400 | >400 |
| **Debt/Assets (%)** | ≤20 | ≤40 | ≤60 | ≤80 | ≤90 | >90 |

## Samcheok Power Plant Results

### Baseline Scenario
```
Overall Rating: BBB (spread: 250 bps)
Component Ratings:
  - Capacity: AAA (2,000 MW ≥ 2,000)
  - Profitability: A (9.1% EBITDA/Fixed Assets)
  - Coverage: BBB (2.6x EBITDA/Interest)
  - Net Debt Leverage: BBB (7.6x Net Debt/EBITDA)
  - Equity Leverage: A (233% Debt/Equity)
  - Asset Leverage: BBB (70% Debt/Assets)

Metrics:
  - Capacity: 2,000 MW
  - EBITDA/Fixed Assets: 9.06%
  - EBITDA/Interest: 2.59x
  - Net Debt/EBITDA: 7.62x
  - Debt/Equity: 233%
  - Debt/Assets: 70%
```

### Aggressive Transition Scenario
```
Overall Rating: B (spread: 600 bps)
Rating Downgrade: BBB → B (2 notches, +350 bps)

Component Ratings:
  - Capacity: AAA (unchanged)
  - Profitability: B (-9.97% EBITDA/Fixed Assets - NEGATIVE!)
  - Coverage: B (-2.85x EBITDA/Interest - NEGATIVE!)
  - Net Debt Leverage: B (999x - unpayable)
  - Equity Leverage: A (unchanged structure)
  - Asset Leverage: BBB (unchanged structure)

Metrics:
  - EBITDA/Fixed Assets: -9.97% (project unprofitable)
  - EBITDA/Interest: -2.85x (cannot cover interest)
  - Net Debt/EBITDA: 999x (technical default territory)
```

### Key Insights

1. **Climate risks cause credit rating downgrades**
   - Baseline: **BBB** (investment grade)
   - Aggressive climate scenarios: **B** (junk/speculative grade)
   - **Loss of investment-grade status**

2. **Spread implications**
   - Baseline spread: 250 bps
   - Risk scenario spread: 600 bps
   - **Additional +350 bps from rating downgrade alone**

3. **Combined with CRP**
   - KIS rating spread: +350 bps (BBB→B downgrade)
   - Climate Risk Premium: +9,575 bps (from our model)
   - **Total spread increase: ~9,925 bps (99 percentage points!)**

4. **Most deteriorating metrics**
   - **Profitability**: 9.06% → -9.97% (becomes negative)
   - **Coverage**: 2.59x → -2.85x (cannot service debt)
   - **Leverage**: 7.6x → 999x (technically insolvent)

## How It Works

### Integration Flow

```
Raw Data (CSV)
    ↓
Cash Flow Model (with climate risks)
    ↓
Financial Metrics (EBITDA, NPV, IRR, DSCR, LLCR)
    ↓
├─→ Climate Risk Premium (CRP) Calculation
│   - Expected Loss from NPV differential
│   - Spread mapping (50 bps per 1% EL)
│   - WACC adjustment
│
└─→ Credit Rating Assessment (KIS)
    - 6 quantitative metrics
    - Component ratings (AAA-B)
    - Overall rating (conservative approach)
    - Spread mapping (rating → bps)
    ↓
Combined Risk Analysis
    - Rating migration (baseline → risk)
    - Spread increase decomposition
    - Investment grade loss
```

### Two Complementary Approaches

| Aspect | **CRP Model** | **KIS Rating Model** |
|--------|--------------|---------------------|
| **Origin** | Climate finance theory | Korean credit rating practice |
| **Method** | Expected loss → spread sensitivity | Financial ratios → rating grid |
| **Granularity** | Continuous (any EL% → bps) | Discrete (6 rating buckets) |
| **Focus** | Climate-specific risks | General creditworthiness |
| **Output** | Custom spread for climate risks | Standard market rating + spread |
| **Use Case** | Novel risk quantification | Market-comparable assessment |

**Together they provide:**
- ✅ **CRP**: Quantifies incremental cost of climate risks
- ✅ **Rating**: Maps to market-standard credit spreads
- ✅ **Combined**: Shows both new climate impacts AND rating migration

## Code Implementation

### Calculate Credit Rating
```python
from src.risk import assess_credit_rating, calculate_rating_metrics_from_financials

# Calculate metrics from balance sheet
rating_metrics = calculate_rating_metrics_from_financials(
    capacity_mw=2000,
    ebitda=290.5e6,
    fixed_assets=3200e6,
    interest_expense=112e6,
    total_debt=2240e6,
    cash_and_equivalents=29e6,
    total_equity=960e6,
    total_assets=3200e6,
)

# Assess rating
assessment = assess_credit_rating(rating_metrics)

print(f"Rating: {assessment.overall_rating}")
print(f"Spread: {assessment.overall_rating.to_spread_bps()} bps")
```

### Analyze Rating Migration
```python
from src.risk import rating_migration_analysis

migration = rating_migration_analysis(baseline_rating, risk_rating)

print(f"Migration: {migration['migration']}")
print(f"Spread Increase: {migration['spread_increase_bps']} bps")
print(f"Worst Metric: {migration['worst_deteriorating_metric']}")
```

## Policy Implications

### Investment Grade Loss
- **Baseline**: BBB (investment grade)
- **Climate scenarios**: B (speculative/junk)
- **Consequence**: Many institutional investors (pension funds, insurers) **cannot hold sub-investment grade debt** by mandate

### Financing Cost Explosion
```
Baseline:
  KIS Spread: 250 bps
  Total Cost: 5.5% (3% risk-free + 2.5%)

Aggressive Climate Risk:
  KIS Spread: 600 bps (+350 bps from downgrade)
  CRP Addition: +9,575 bps (climate risk premium)
  Total Cost: ~103% (3% + 6% + 95.75%)
```
**Project becomes unfinanceable**

### Stranded Asset Risk
Climate risks can:
1. Reduce profitability (negative EBITDA)
2. Impair debt service (EBITDA < Interest)
3. Trigger rating downgrades (BBB → B)
4. Increase spreads dramatically (+350 to +9,900 bps)
5. **Render project economically unviable**

## Next Steps

1. **Streamlit Dashboard Update** (pending)
   - Add "Credit Rating" tab
   - Show rating migration matrix
   - Display component ratings
   - Compare KIS spreads vs CRP

2. **Mathematical Framework Update** (pending)
   - Add Section 8: Credit Rating Theory
   - Formalize rating migration process
   - Link to financing spreads

3. **Sensitivity Analysis**
   - Rating sensitivity to each metric
   - Threshold analysis (investment grade boundary)
   - Rating migration probability

4. **Validation**
   - Compare to actual Korean power plant ratings
   - Calibrate component weights if needed
   - Validate spread-rating mapping

## Files Modified

- ✅ `src/risk/credit_rating.py` - New module (400+ lines)
- ✅ `src/risk/__init__.py` - Export rating functions
- ✅ `src/pipeline/runner.py` - Integrate rating calculation
- ✅ Data export - New `credit_ratings.csv` output
- ⏳ `src/app/streamlit_app.py` - Add rating tab (next)
- ⏳ `docs/mathematical_framework.tex` - Add rating theory (next)

## Summary

The KIS credit rating integration provides:
1. **Market-standard assessment** of creditworthiness
2. **Rating migration analysis** showing climate risk impacts
3. **Investment grade loss** demonstration
4. **Complementary evidence** alongside CRP calculations
5. **Policy-relevant insights** on asset stranding

**Combined with our CRP model, this creates the most comprehensive climate-finance risk framework for power infrastructure in Korea.**

---

**Status**: ✅ Module complete, tests passing, results generating
**Next**: Update Streamlit dashboard with credit rating tab

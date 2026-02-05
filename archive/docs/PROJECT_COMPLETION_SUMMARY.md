# Climate Risk Premium Model - Project Completion Summary

## Executive Summary

This document summarizes the complete Climate Risk Premium (CRP) quantification framework for Samcheok Blue Power Plant (2,100 MW coal-fired in South Korea). The model quantifies the additional financing cost (in basis points) when climate risks are properly priced into coal investments.

**Key Innovation:** The **Credit Rating Death Spiral** - a non-linear feedback loop where climate risks cascade through financial metrics to create exponentially increasing financing costs.

## Project Status: COMPLETE

| Module | Status | Key Achievement |
|--------|--------|-----------------|
| Physical Risk | ✅ Complete | Literature-backed parameters, probabilistic framework |
| Transition Risk | ✅ Complete | Korea ETS carbon pricing (74% of impact) |
| Cash Flow | ✅ Complete | Fixed outage logic, efficiency loss integration |
| Credit Rating | ✅ Complete | Extended AAA-D scale, DSCR-based, counterfactual baseline |
| Financing/CRP | ✅ Complete | Counterfactual-based CRP calculation |
| Pipeline | ✅ Complete | Full integration with all modules |
| Dashboard | ✅ Complete | Updated for new rating scale |
| Tests | ✅ 61/61 Passing | Full test coverage |

---

## Final Model Results

### Climate Risk Premium by Scenario

| Scenario | Rating | Spread (bps) | DSCR | CRP (bps) | Migration |
|----------|--------|--------------|------|-----------|-----------|
| baseline | CC | 1,500 | 0.64x | 1,020 | ↓5 notches |
| moderate_physical | CC | 1,500 | 0.61x | 1,020 | ↓5 notches |
| high_physical | CC | 1,500 | 0.59x | 1,020 | ↓5 notches |
| low_demand | C | 2,500 | 0.21x | 1,735 | ↓6 notches |
| severe_drought | C | 2,500 | 0.18x | 1,735 | ↓6 notches |
| moderate_transition | D | 5,000 | -2.10x | 3,500 | ↓7 notches |
| aggressive_transition | D | 5,000 | -3.64x | 3,500 | ↓7 notches |
| combined_moderate | D | 5,000 | -2.06x | 3,500 | ↓7 notches |
| combined_aggressive | D | 5,000 | -3.47x | 3,500 | ↓7 notches |

### Key Findings

1. **Baseline CRP = 1,020 bps**: Even under "current policy" (K-ETS carbon pricing), Samcheok faces significant climate risk premium
2. **Transition Risk Dominates**: Carbon pricing accounts for 74% of total climate risk impact
3. **Rating Death Spiral Working**: All scenarios show 5-7 notch downgrades from counterfactual (A → CC/C/D)
4. **WACC Impact**: Baseline WACC increases from 6.75% (counterfactual) to 16.95% (actual)

---

## Module Deep Dives

### 1. Physical Risk Module

**Files:** `src/risk/physical.py`, `src/climada/literature_parameters.py`, `src/climada/probabilistic_risk.py`

**Key Features:**
- Literature-backed parameters (10 peer-reviewed sources with DOIs)
- Year-by-year hazard evolution (2025-2060)
- Probabilistic risk framework (EAL = Σ P × Loss)
- Credit impact outputs (PD, LGD, DSCR reduction)

**Literature Sources:**
| Source | Parameter | Value |
|--------|-----------|-------|
| ES&T 2017 | Thermal efficiency loss | 0.3%/°C |
| CAISO 2003-2016 | Wildfire outage baseline | 1%/yr |
| FEMA HAZUS 2022 | Flood damage curve | 0-100% |
| Zscheischler 2018 | Compound risk multiplier | 1.2-2.0x |

### 2. Transition Risk Module

**Files:** `src/scenarios/carbon_pricing.py`, `data/raw/carbon_prices.csv`

**Carbon Pricing Trajectories (USD/tCO2):**
| Scenario | 2025 | 2030 | 2040 | 2050 |
|----------|------|------|------|------|
| korea_ets_current | $8 | $20 | $50 | $75 |
| korea_ets_ndc | $12 | $55 | $130 | $210 |
| korea_net_zero | $15 | $85 | $200 | $350 |
| high_ambition | $30 | $150 | $350 | $550 |

**Impact Analysis:**
- Carbon costs at $75/tCO2 → ~$1.1B annual cost
- Carbon pricing = 74% of total climate impact
- Dispatch penalty = 26% of total impact

### 3. Cash Flow Module

**Files:** `src/financials/cashflow.py`

**Key Fixes Applied:**
- Outage logic: `actual_mwh = potential_mwh × (1 - outage_rates)`
- Efficiency loss: `effective_heat_rate = heat_rate × (1 + efficiency_losses)`
- Year-by-year physical risk integration

### 4. Credit Rating Module (MAJOR ENHANCEMENT)

**Files:** `src/risk/credit_rating.py`, `src/risk/financing.py`

**Extended Rating Scale:**
| Rating | Spread (bps) | Category |
|--------|--------------|----------|
| AAA | 50 | Investment Grade |
| AA | 100 | Investment Grade |
| A | 150 | Investment Grade |
| BBB | 250 | Investment Grade |
| BB | 400 | Speculative |
| B | 600 | Speculative |
| CCC | 900 | Distressed |
| CC | 1,500 | Distressed |
| C | 2,500 | Near Default |
| D | 5,000 | Default |

**DSCR Rating Thresholds:**
| DSCR | Rating |
|------|--------|
| < 0 | D |
| 0-0.5x | C |
| 0.5-0.8x | CC |
| 0.8-1.0x | CCC |
| 1.0-1.1x | B |
| 1.1-1.3x | BB |
| 1.3-1.6x | BBB |
| > 2.5x | AAA |

**Counterfactual Baseline:**
- Counterfactual = A-rated (no-carbon world)
- CRP = WACC(scenario) - WACC(counterfactual)
- Ensures meaningful spread differential even when all scenarios have negative EBITDA

---

## Technical Architecture

```
                    ┌─────────────────────────────────────┐
                    │         INPUT DATA (CSV)            │
                    │  plant_params, carbon_prices,       │
                    │  climada_hazards, korea_power_plan  │
                    └─────────────────┬───────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
      ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
      │  TRANSITION   │     │   PHYSICAL    │     │    MARKET     │
      │    MODULE     │     │    MODULE     │     │    MODULE     │
      │ carbon_pricing│     │ lit_params    │     │ demand_growth │
      │ dispatch_pen  │     │ prob_risk     │     │               │
      └───────┬───────┘     └───────┬───────┘     └───────┬───────┘
              │                     │                     │
              └──────────────┬──────┴─────────────────────┘
                             │
                             ▼
                     ┌───────────────┐
                     │   CASHFLOW    │
                     │    MODULE     │
                     │ revenue, fuel │
                     │ carbon, ebitda│
                     └───────┬───────┘
                             │
                             ▼
                     ┌───────────────┐
                     │CREDIT RATING  │
                     │   MODULE      │
                     │ AAA → D scale │
                     │ DSCR-based    │
                     │ counterfactual│
                     └───────┬───────┘
                             │
                             ▼
                     ┌───────────────┐
                     │  FINANCING    │
                     │    MODULE     │
                     │ CRP = ΔWACC   │
                     └───────┬───────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   OUTPUT CSVs   │
                    │ scenario_       │
                    │ comparison.csv  │
                    └─────────────────┘
```

---

## File Structure

```
risk_premium_2026/
├── src/
│   ├── risk/
│   │   ├── credit_rating.py    # Extended AAA-D scale (643 lines)
│   │   ├── financing.py        # Counterfactual CRP (249 lines)
│   │   └── physical.py         # Year-by-year adjustments
│   ├── climada/
│   │   ├── literature_parameters.py  # 10 sources with DOIs
│   │   └── probabilistic_risk.py     # EAL framework
│   ├── scenarios/
│   │   └── carbon_pricing.py   # 6 K-ETS scenarios
│   ├── financials/
│   │   └── cashflow.py         # Fixed outage logic
│   ├── pipeline/
│   │   └── runner.py           # Full integration
│   └── app/
│       └── streamlit_app.py    # Dashboard
├── data/
│   ├── raw/
│   │   ├── climada_hazards.csv # Literature citations
│   │   └── carbon_prices.csv   # K-ETS trajectories
│   └── processed/
│       └── scenario_comparison.csv
├── docs/
│   ├── physical_risk_methodology.md
│   ├── credit_rating_methodology.md
│   └── PROJECT_COMPLETION_SUMMARY.md
└── tests/
    └── 61 tests (all passing)
```

---

## How to Run

### Full Pipeline
```python
from pathlib import Path
from src.pipeline.runner import CRPModelRunner

runner = CRPModelRunner(Path.cwd())
results = runner.run_multi_scenario()
runner.export_results(results, Path("data/processed"))
```

### Dashboard
```bash
streamlit run src/app/streamlit_app.py
```

### Tests
```bash
pytest tests/ -v
```

---

## Key Innovations

### 1. Credit Rating Death Spiral
The core innovation capturing non-linear climate risk amplification:
```
Carbon Costs → Negative EBITDA → Low DSCR → Distressed Rating → High Spread → Higher WACC → CRP
```

### 2. Counterfactual Baseline
Comparing against "no-carbon world" (A-rated) instead of "current policy" (which already has negative EBITDA) enables meaningful CRP calculation.

### 3. Literature-Backed Physical Risk
All physical hazard parameters traced to peer-reviewed sources:
- 10 academic papers with DOIs
- CAISO, FEMA, IPCC, Nature Climate Change sources
- Probabilistic framework with EAL formula

### 4. Extended Distressed Rating Scale
Adding CCC, CC, C, D ratings allows proper differentiation when all scenarios have negative EBITDA.

---

## Conclusion

The Climate Risk Premium model successfully quantifies how climate transition risks create a financing death spiral for coal assets. Key findings:

1. **Samcheok faces 1,020-3,500 bps CRP** depending on scenario
2. **Carbon pricing is the dominant driver** (74% of impact)
3. **Even baseline scenario is distressed** (CC rating, 1,500 bps spread)
4. **Transition scenarios reach default** (D rating, 5,000 bps spread)

The model provides empirical backing for the thesis that climate risks are fundamentally mispriced in coal asset valuations.

---

## References

### Physical Risk
- Zscheischler et al. (2018). Future climate risk from compound events. *Nature Climate Change*.
- CAISO (2016). Root Cause Analysis: Transmission Line Outages Due to Wildfires.
- FEMA (2022). HAZUS-MH Flood Model Technical Manual v5.1.

### Credit Rating
- KIS (2023). Rating Methodology: Power Generation Sector.
- Moody's (2021). Global Infrastructure Finance Rating Methodology.
- S&P (2022). Project Finance Rating Criteria.

### Carbon Pricing
- IEA (2023). World Energy Outlook - Carbon Pricing Scenarios.
- Korea Ministry of Environment (2024). K-ETS Phase 4 Guidelines.

---

*Model version: 2.0 (Enhanced Credit Rating)*
*Tests: 61/61 passing*

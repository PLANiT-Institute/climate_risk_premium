# Consultant Review: Climate Risk Premium Model
## Problem Statement & Independent Assessment

**Prepared for**: PLANiT Institute
**Prepared by**: Independent Technical Review
**Date**: January 2026
**Status**: First Encounter Assessment

---

## 1. Executive Summary

This report presents an independent assessment of the "Climate Risk Premium Model" repository, a sophisticated financial modeling framework designed to quantify stranded asset risk for Korean coal-fired power infrastructure. The review was conducted from the perspective of a consultant encountering the project for the first time.

### Key Assessment

| Dimension | Score | Notes |
|-----------|-------|-------|
| Problem Definition | A | Well-defined, policy-relevant |
| Methodology Rigor | A- | Multi-source integration, academically grounded |
| Code Architecture | B+ | Modular but complex; 67+ modules |
| Data Quality | A | Authoritative sources (CLIMADA, MOTIE, KIS) |
| Documentation | B | README excellent; internal docs fragmented |
| Reproducibility | B+ | Clear entry points; some hard-coded params |

---

## 2. Problem Statement

### 2.1 The Core Problem

**How should investors price the risk that government climate policies will strand coal power assets before their economic life ends?**

This is not merely a physical climate risk question. The model demonstrates that **policy risk dominates physical risk by 4-6x** in determining asset values. This finding challenges conventional climate finance approaches that focus primarily on physical hazards.

### 2.2 The Samcheok Paradox

South Korea presents a unique natural experiment:
- **Commitment**: Carbon neutrality by 2050 (legally binding)
- **Action**: Commissioned 2.1 GW Samcheok Blue Power in 2024
- **Result**: Likely the last coal plant ever built in Korea

This paradox creates a real-time case study: investors priced the asset at commissioning, but government policy has since announced accelerated phase-out schedules. The question becomes: **What is the true risk premium investors should have demanded?**

### 2.3 Quantified Problem Scope

| Metric | Baseline | With Climate/Transition Risk |
|--------|----------|------------------------------|
| NPV | +$2.9B | -$8.4B |
| DSCR | 1.81x | -4.32x (negative) |
| Credit Rating | BBB | B |
| Risk Premium | 250 bps | **5,854 bps** |

The model demonstrates that under combined aggressive scenarios, the asset becomes **unfinanceable**--debt service would exceed total revenue.

---

## 3. Methodology Assessment

### 3.1 Three-Pillar Data Integration

The model integrates three independent, authoritative data sources:

```
+-------------------+     +-------------------+     +-------------------+
|   CLIMADA (ETH)   |     |  Korea Power Plan |     |   KIS Rating      |
|   Physical Risk   |     |  Transition Risk  |     |   Credit Risk     |
+-------------------+     +-------------------+     +-------------------+
| Wildfire FWI      |     | Dispatch caps     |     | DSCR thresholds   |
| Flood probability |     | Carbon price      |     | Rating triggers   |
| Sea level rise    |     | Phase-out dates   |     | Spread curves     |
+-------------------+     +-------------------+     +-------------------+
         |                         |                         |
         +------------+------------+------------+------------+
                      |                         |
                      v                         v
              +---------------+        +------------------+
              | Physical Risk |        | Transition Risk  |
              | Module        |        | Module           |
              +---------------+        +------------------+
                      |                         |
                      +------------+------------+
                                   |
                                   v
                      +------------------------+
                      |   Financial Module     |
                      |   CDDM / Credit Risk   |
                      |   Stress Testing       |
                      +------------------------+
                                   |
                                   v
                      +------------------------+
                      |   Credit Rating        |
                      |   Death Spiral         |
                      +------------------------+
```

### 3.2 Physical Risk Framework

The physical risk module follows established frameworks:

| Component | Framework | Source |
|-----------|-----------|--------|
| Risk Formula | R = H x E x V | CLIMADA (Aznar-Siguan & Bresch, 2019) |
| Damage Functions | Sigmoid: f(i) = i^n/(1+i^n) | Emanuel (2011) |
| Asset-Level | 70% underestimation fix | Bressan et al. (2024) |
| Climate VaR | Monte Carlo + Gumbel/GPD | Industry standard |

**Key Physical Risk Results (RCP8.5, 2050)**:
- Tropical Cyclone: 1.42% annual loss
- Flood: 0.68% annual loss
- Wildfire: 0.25% annual loss
- Compound: 0.20% correlation uplift
- **Total: 2.55% annual expected loss**

### 3.3 Transition Risk Framework

The transition module uses official government data:

| Policy Source | Application |
|---------------|-------------|
| 10th Power Supply Plan (MOTIE) | Dispatch trajectory 2024-2050 |
| NDC Update (2023) | 40% reduction target |
| Carbon Neutrality Act | 2050 phase-out requirement |

**Key Transition Results**:
- 2024: 65% capacity factor (baseline)
- 2030: 45% capacity factor (NDC)
- 2050: 4% capacity factor (phase-out)

### 3.4 Financial Translation

The newly implemented financial module (`src/models/financial/`) provides:

1. **Asset-Level Exposure** (`asset_exposure.py`)
   - Korean coal fleet: 7 plants, 29.3 GW, $41B replacement cost
   - Ownership chains and insurance coverage modeling

2. **Climate VaR** (`climate_var.py`)
   - Monte Carlo engine with 10,000+ simulations
   - Supports Gumbel, Lognormal, and Pareto distributions

3. **Generation Loss** (`generation_loss.py`)
   - WRI-EBRD methodology
   - Coal: 1.7% by 2030 vs CCGT: 0.8%

4. **NGFS Stress Testing** (`stress_test.py`)
   - 4 scenarios: Orderly, Disorderly, Hot House, Current Policies
   - Probability-weighted loss aggregation

5. **Credit Risk Translation** (`credit_risk.py`)
   - Physical risk -> DSCR -> Rating -> Spread
   - Rule: +7 bps per 1% physical risk

6. **CDDM** (`cddm.py`)
   - Climate-adjusted equity valuation
   - 15 bps risk premium per 1% physical risk

### 3.5 The Death Spiral Mechanism

The model's core innovation is demonstrating non-linear feedback:

```
Climate Risks
     |
     v
Lower Revenue ---------> Lower EBITDA
     ^                        |
     |                        v
Higher Interest <----- Lower DSCR
     ^                        |
     |                        v
Wider Spread <-------- Rating Downgrade
```

This mechanism explains how a **linear** policy change (dispatch reduction) creates a **non-linear** financial outcome (rating collapse from BBB to B, spread widening from 250 to 5,854 bps).

---

## 4. Technical Architecture Assessment

### 4.1 Code Structure

```
src/
├── models/
│   ├── physical/           # 12 modules
│   │   ├── damage_functions/
│   │   │   ├── base.py         # Sigmoid functions (Emanuel 2011)
│   │   │   ├── tropical_cyclone.py
│   │   │   ├── flood.py
│   │   │   ├── wildfire.py
│   │   │   └── drought.py
│   │   ├── scenarios/
│   │   │   ├── rcp.py
│   │   │   └── ssp.py
│   │   ├── model.py
│   │   ├── exposure.py
│   │   ├── hazards.py
│   │   └── compound_risk.py
│   ├── transition/         # 3 modules
│   │   ├── model.py
│   │   └── korea_power_plan.py
│   └── financial/          # 9 modules (NEW)
│       ├── asset_exposure.py
│       ├── climate_var.py
│       ├── generation_loss.py
│       ├── transmission_channels.py
│       ├── calibration.py
│       ├── cddm.py
│       ├── credit_risk.py
│       └── stress_test.py
├── risk/                   # 4 modules
├── scenarios/              # 3 modules
├── climada/                # 5 modules
├── financials/             # 2 modules
├── pipeline/               # 2 modules
└── app/                    # 1 module
```

**Total**: ~67 Python modules across 6 core packages

### 4.2 Strengths

1. **Modular Design**: Clear separation of physical, transition, and financial concerns
2. **Type Safety**: Extensive use of dataclasses and type hints
3. **Documentation**: Inline citations to academic sources
4. **Calibration**: Korean historical event database (typhoons, floods, wildfires)

### 4.3 Areas for Improvement

1. **Hard-coded Parameters**: Some values embedded in code (e.g., `physical_risk_pct=2.55`)
2. **Test Coverage**: Test directory exists but coverage unclear
3. **Configuration Management**: No centralized config; parameters scattered
4. **Archive Accumulation**: Multiple `archive/` directories with deprecated code

---

## 5. Key Findings

### 5.1 Primary Finding: Policy Risk Dominates

| Risk Type | NPV Impact | Magnitude |
|-----------|------------|-----------|
| Physical Risk (High) | -$1.7B | -59% |
| Transition Risk (Aggressive) | -$10.9B | -375% |
| **Ratio** | **6.4x** | Policy > Physical |

**Implication**: Climate finance frameworks that focus primarily on physical hazards miss the dominant risk factor for fossil fuel assets.

### 5.2 Secondary Finding: Death Spiral is Real

The model demonstrates that credit risk is **non-linear**:

| Scenario | DSCR | Rating | Spread | Feedback |
|----------|------|--------|--------|----------|
| Baseline | 1.81x | BBB | 250 bps | None |
| Moderate Trans. | -1.39x | B | 3,880 bps | Active |
| Aggressive Trans. | -4.37x | B | 5,635 bps | Severe |
| Combined | -4.32x | B | 5,854 bps | Terminal |

**Implication**: Linear stress tests underestimate tail risk. Negative DSCR triggers default before "expected" lifetime.

### 5.3 Tertiary Finding: Asset-Level Granularity Matters

Following Bressan et al. (2024), the model correctly identifies that:
- Country-level physical risk: ~1.5% annual
- Asset-level physical risk (Samcheok): **2.55%** annual

**Underestimation Factor**: 70% (consistent with literature)

---

## 6. Critical Assessment

### 6.1 What the Model Does Well

1. **Integrates Multiple Risk Types**: Unlike single-factor models, captures interaction effects
2. **Uses Authoritative Data**: Government policy (MOTIE), climate science (CLIMADA), credit methodology (KIS)
3. **Demonstrates Non-linearity**: Death spiral mechanism is novel and policy-relevant
4. **Asset-Level Precision**: Avoids aggregation bias in physical risk

### 6.2 Limitations and Assumptions

1. **Scenario Dependency**: Results highly sensitive to Korea Power Plan trajectory
2. **Single Asset Focus**: Framework is generalizable but implementation is Samcheok-specific
3. **Static Adaptation**: No dynamic response modeling (e.g., fuel switching, retrofits)
4. **Correlation Assumptions**: Compound risk uses fixed correlation (0.3) without empirical validation

### 6.3 Model Risk

| Risk | Severity | Mitigation |
|------|----------|------------|
| Policy reversal | High | Scenario range included |
| Physical risk undercount | Medium | Conservative baselines |
| Correlation tail risk | Medium | Copula extension possible |
| Data vintage | Low | Recent sources (2023-2024) |

---

## 7. Recommendations

### 7.1 Immediate (Next 30 Days)

1. **Centralize Configuration**: Move hard-coded parameters to `config.yaml`
2. **Expand Test Suite**: Target 80% coverage on financial module
3. **Clean Archives**: Consolidate deprecated code

### 7.2 Short-term (Next Quarter)

1. **Multi-Asset Extension**: Apply framework to other Korean coal plants (Dangjin, Taean, Hadong)
2. **Dynamic Adaptation**: Add retrofit and fuel-switching decision logic
3. **Validation Study**: Compare model predictions to actual financing terms (if available)

### 7.3 Medium-term (Next Year)

1. **Regional Expansion**: Adapt to Southeast Asian coal assets (Indonesia, Vietnam, Philippines)
2. **Real-time Integration**: Connect to live policy tracking (e.g., Carbon Tracker)
3. **Regulatory Engagement**: Present to Korean FSS for potential regulatory adoption

---

## 8. Conclusion

### 8.1 Problem Statement (Formal)

> **How can institutional investors quantify the total risk premium--combining physical climate hazards, government transition policies, and credit feedback loops--for coal-fired power assets facing policy-driven obsolescence?**

### 8.2 Solution Provided

This project provides a rigorous, multi-factor framework that:
1. Integrates three independent authoritative data sources
2. Translates physical risk to financial impact via CLIMADA and damage functions
3. Models transition risk via official government dispatch projections
4. Captures credit feedback through a novel "death spiral" mechanism
5. Produces a single output metric: **Climate Risk Premium (bps)**

### 8.3 Key Metric

**Climate Risk Premium for Samcheok Blue Power: 5,854 basis points**

This represents the additional yield investors should demand to compensate for combined physical and transition risks under aggressive climate policy scenarios.

### 8.4 Policy Implications

1. **For Investors**: Current BBB ratings and ~250 bps spreads do not reflect forward-looking policy risk
2. **For Policymakers**: Disorderly transition costs $4-5B; structured early retirement could save $3.5B
3. **For Rating Agencies**: Climate risk disclosure must include policy scenario analysis, not just physical exposure
4. **For Regulators**: Forward-looking stress tests should include NGFS scenarios with non-linear feedback

---

## Appendix A: Module Inventory

| Package | Modules | Purpose |
|---------|---------|---------|
| `models/physical` | 12 | Hazard modeling, damage functions, scenarios |
| `models/transition` | 3 | Korea Power Plan, policy trajectories |
| `models/financial` | 9 | VaR, credit risk, stress testing, CDDM |
| `risk` | 4 | Credit rating, financing, physical integration |
| `scenarios` | 3 | Scenario definitions and management |
| `climada` | 5 | CLIMADA API integration |
| `financials` | 2 | Cash flow modeling |
| `pipeline` | 2 | Analysis orchestration |
| `app` | 1 | Streamlit dashboard |
| **Total** | **41** | Core modules |

## Appendix B: Data Sources

| Source | Provider | Vintage | Coverage |
|--------|----------|---------|----------|
| Korea Power Supply Plan | MOTIE | 2023 | 2024-2050 |
| CLIMADA Hazards | ETH Zurich | 2024 | Global, RCP 2.6/4.5/8.5 |
| KIS Rating Grid | Korea Investors Service | 2023 | IPP sector |
| Korean Disaster Events | NDMS, Korean Re, EM-DAT | 2002-2024 | Typhoons, floods, wildfires |

## Appendix C: Key Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Physical Risk (Baseline) | 2.55% annual | CLIMADA + compound |
| Generation Loss (2050) | 1.63% | WRI-EBRD model |
| Credit Spread Sensitivity | +7 bps / 1% risk | Calibrated |
| Climate Risk Premium | 15 bps / 1% risk | Literature |
| Discount Rate | 8% | Korean WACC |
| Tax Rate | 24% | Korean corporate |

---

*End of Report*

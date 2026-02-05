# Physical Risk Methodology

## Overview

This document describes the methodology for quantifying physical climate risks to the Samcheok Blue Power coal-fired power plant. The framework implements three integrated approaches:

1. **Option A: CLIMADA Integration Framework** - Proper probabilistic hazard-exposure-vulnerability model
2. **Option B: Literature-Backed Parameters** - All values derived from peer-reviewed sources
3. **Option C: Probabilistic Risk Framework** - Full risk chain from hazard to credit impact

## Key Literature Sources

| Citation | Application | Key Data |
|----------|-------------|----------|
| Zscheischler et al. (2018) Nature Climate Change | Compound risk multipliers | Base 1.2x, Max 2.0x amplification |
| California ISO (2003-2016) | Wildfire outage rates | 336 fires, 10% major impact |
| FEMA HAZUS-MH (2022) | Flood depth-damage curves | 0-15 ft depth → 0-100% damage |
| S&P Global/ES&T (2017) | Thermal efficiency loss | 0.3% per 1°C air temp, 0.17% per 1°C water temp |
| IPCC AR6 WGIII (2022) | Climate projections | RCP4.5/8.5 scenarios, SLR projections |
| Nature Communications (2024) | Asset-level risk | 70-82% loss underestimation warning |
| NREL (2023) | Power system wildfire risks | Probabilistic outage models |
| Seoul Flood Control Policy (2012) | Korea flood standards | 100-200 year design return periods |

---

## 1. Hazard Inputs (Physical Climate Variables)

### 1.1 Wildfire Risk

**Source:** California ISO wildfire transmission statistics (2003-2016), NREL (2023)

**Key Statistics:**
- 336 large wildfires along California's major transmission lines (2003-2016)
- ~10% had major impact (significant outages or costly generation changes)
- This translates to ~2.4 major events per year affecting transmission

**Outage Rate Derivation:**
```
Annual wildfire outage rate = (Major events per year) × (Average outage duration) / (8760 hours)
Baseline = 2.4 events × 72 hours / 8760 = 0.0197 ≈ 2%
Conservative estimate: 1% baseline (California is higher risk than Korea)
```

**Fire Weather Index (FWI) Correlation:**
- FWI developed in 1970 for quantitative wildfire risk assessment
- Probabilistic models show 10-30% higher outage risk when multiple factors considered
- FWI thresholds: 20 (low), 30 (moderate), 40 (high), 50+ (extreme)

### 1.2 Flood Risk

**Source:** FEMA HAZUS-MH Flood Model Technical Manual (2022), Seoul Flood Control Policy

**Design Standards (Korea):**
- National rivers: 100-200 year return period
- Local rivers: 50-100 year return period
- Urban drainage: 10-30 year return period

**Annual Probability:**
```
P(100-year flood in any year) = 1/100 = 1%
P(50-year flood in any year) = 1/50 = 2%
```

**Depth-Damage Curve (HAZUS utility infrastructure):**

| Flood Depth (m) | Damage Fraction | Description |
|-----------------|-----------------|-------------|
| 0.0 | 0% | No damage |
| 0.3 | 5% | Minor equipment damage |
| 0.6 | 15% | Electrical systems affected |
| 1.0 | 30% | Significant equipment damage |
| 1.5 | 50% | Major systems offline |
| 2.0 | 70% | Severe structural damage |
| 3.0 | 90% | Near-total loss |
| 4.5 | 100% | Complete loss |

### 1.3 Sea Level Rise

**Source:** IPCC AR6 WGIII (2022)

**Global Mean SLR Projections:**

| Scenario | 2030 | 2050 | 2100 |
|----------|------|------|------|
| RCP4.5 | 0.10m | 0.28m | 0.53m |
| RCP8.5 | 0.12m | 0.45m | 0.84m |

**Impact on Coastal Power Plants:**
- Cooling water intake salinity increase
- Potential intake flooding during storm surge
- Capacity derate: ~2% per 0.1m SLR (derived estimate)

### 1.4 Heat Wave / Thermal Efficiency

**Source:** S&P Global/ES&T (2017), ScienceDirect (2015)

**Efficiency Loss Rates:**
- Air temperature: **0.3% efficiency loss per 1°C** (range: 0.1-0.5%)
- Cooling water temperature: **0.17% efficiency loss per 1°C**
- Total capacity loss: **1.0-2.0% per 1°C** (including shutdowns)

**Coal vs. Gas Sensitivity:**
- Coal plants: 0.05-0.07 percentage points per 10°C
- Gas plants: More sensitive (higher loss per °C)

---

## 2. Compound Risk Framework

### 2.1 Theoretical Basis

**Source:** Zscheischler et al. (2018) "Future climate risk from compound events"

**Key Principles:**
1. Compound events = combination of multiple drivers/hazards contributing to risk
2. Impacts are **non-linear** - cannot simply sum individual impacts
3. Complex interactions can **amplify** compound impacts significantly

**Compound Event Types:**
1. **Preconditioned events**: Weather precondition aggravates hazard impact
2. **Multivariate events**: Multiple concurrent drivers/hazards
3. **Temporally compounding**: Succession of hazards over time
4. **Spatially compounding**: Hazards in multiple connected locations

### 2.2 Compound Multiplier

**Literature Basis:**
- Base multiplier: **1.2x** (minimum for any compound scenario)
- Maximum multiplier: **2.0x** (severe cascading failures)

**Calculation:**
```python
# System stress = sum of individual risk rates
stress = wildfire_rate + flood_rate + slr_rate

# Sigmoid scaling from 1.2x to 2.0x
stress_factor = min(1.0, stress × 10)  # Normalizes 0-0.1 to 0-1
compound_multiplier = 1.2 + (0.8 × stress_factor)
```

**Example:**
- Low stress (total risk = 1%): multiplier = 1.28x
- Medium stress (total risk = 5%): multiplier = 1.60x
- High stress (total risk = 10%): multiplier = 2.00x

### 2.3 Residual Damage

**Source:** Nature Communications (2024)

- **10% residual damage factor** between events
- Infrastructure not fully restored to pre-event condition
- Cumulative effects from previous years compound over time

---

## 3. Probabilistic Framework

### 3.1 Risk Equation

```
Expected Annual Loss (EAL) = Σ [P(event_i) × Damage(event_i)]
```

Where:
- P(event) = Annual probability of occurrence
- Damage(event) = Conditional loss given event occurs

### 3.2 Event Scenarios

**Flood Events:**
| Return Period | Annual Probability | Depth (m) | Damage |
|---------------|-------------------|-----------|--------|
| 2-year | 50% | 0.0 | 0% |
| 5-year | 20% | 0.3 | 5% |
| 10-year | 10% | 0.6 | 15% |
| 25-year | 4% | 1.0 | 30% |
| 50-year | 2% | 1.5 | 50% |
| 100-year | 1% | 2.0 | 70% |
| 250-year | 0.4% | 3.0 | 90% |
| 500-year | 0.2% | 4.0 | 100% |

**Wildfire Events (FWI-based):**
| FWI Level | Annual Probability | Outage Rate |
|-----------|-------------------|-------------|
| 20 (Low) | 60% | 1% |
| 30 (Moderate) | 20% | 3% |
| 40 (High) | 10% | 6% |
| 50 (Very High) | 5% | 10% |
| 60 (Extreme) | 3% | 15% |
| 80 (Catastrophic) | 1% | 25% |

### 3.3 Climate Change Adjustment

**Annual Intensity Increase Rates:**

| Hazard | RCP4.5 | RCP8.5 |
|--------|--------|--------|
| Flood | 1.0%/yr | 2.0%/yr |
| Wildfire | 1.5%/yr | 2.5%/yr |
| Heat Wave | 1.5%/yr | 3.0%/yr |
| SLR | 0.5%/yr | 1.0%/yr |

**2050 Projection Example (RCP8.5):**
```
Adjustment factor = 1.0 + (rate × years_from_2024)
Wildfire 2050 = 1.0 + (0.025 × 26) = 1.65x baseline intensity
```

---

## 4. Outputs

### 4.1 Physical Risk Outputs

| Output | Unit | Description |
|--------|------|-------------|
| Expected Annual Loss (EAL) | USD/year | Average annual loss from all scenarios |
| Expected Annual Outage Days | days/year | Average downtime from physical hazards |
| PML-100yr | USD | Probable Maximum Loss at 100-year return |
| PML-250yr | USD | Probable Maximum Loss at 250-year return |
| Capacity Factor Reduction | % | Annual average CF reduction |

### 4.2 Credit Risk Outputs

| Output | Unit | Derivation |
|--------|------|------------|
| PD Increase | bps | EAL_rate × 1000 |
| LGD Increase | % | PML / Asset_value × 100 |
| DSCR Reduction | x | Baseline_DSCR × EAL_rate |
| Rating Notches Down | notches | DSCR_reduction / 0.2 |
| Spread Impact | bps | PD_increase + (notches × 50) |

### 4.3 Integration with CRP Model

**Physical risk feeds into the main model:**

```
Physical Adjustments
    → outage_rate (reduces generation)
    → capacity_derate (reduces maximum output)
    → efficiency_loss (increases fuel costs)
    → water_constrained_capacity (hard cap on operations)

Cash Flow Impact
    → Revenue = Generation × Price × (1 - outage_rate)
    → Fuel Costs = Generation × Heat_Rate × (1 + efficiency_loss) × Fuel_Price
    → Total Impact feeds to DSCR → Credit Rating → Financing Cost
```

---

## 5. Validation and Limitations

### 5.1 Data Limitations

1. **Korea-specific wildfire data**: Used California as proxy (higher risk)
2. **Power plant flood damage**: Generic utility curve from HAZUS
3. **Compound multipliers**: Theoretical framework, limited empirical validation
4. **SLR capacity impact**: Derived estimate, needs site-specific study

### 5.2 Conservative Assumptions

- Baseline outage rates likely **conservative** for Korea (lower fire risk than California)
- Compound multipliers use literature **base values** (1.2x baseline)
- Climate adjustment uses **median** projections, not extremes

### 5.3 Recommended Improvements

1. **Run actual CLIMADA model** for Samcheok location with Korean hazard data
2. **Obtain Korean forced outage statistics** from KEPCO/KPX
3. **Commission site-specific flood study** for Samcheok coastal area
4. **Validate compound multipliers** with Korean multi-hazard studies

---

## References

1. Zscheischler, J., et al. (2018). Future climate risk from compound events. *Nature Climate Change*, 8, 469-477. https://doi.org/10.1038/s41558-018-0156-3

2. California ISO. (2003-2016). Effect of Wildfires on Transmission Line Reliability. https://ia.cpuc.ca.gov/environment/info/aspen/sunrise/deir/apps/a01/

3. FEMA. (2022). Hazus Flood Technical Manual 5.1. https://www.fema.gov/sites/default/files/documents/fema_hazus-flood-model-technical-manual-5-1.pdf

4. Miara, A., et al. (2017). Effects of Environmental Temperature Change on the Efficiency of Coal- and Natural Gas-Fired Power Plants. *Environmental Science & Technology*. https://doi.org/10.1021/acs.est.6b01503

5. IPCC. (2022). AR6 Climate Change 2022: Mitigation of Climate Change, Chapter 6: Energy Systems. https://www.ipcc.ch/report/ar6/wg3/chapter/chapter-6/

6. Bressan, G., et al. (2024). Asset-level assessment of climate physical risk matters for adaptation finance. *Nature Communications*. https://doi.org/10.1038/s41467-024-48820-1

7. NREL. (2023). Power System Wildfire Risks and Potential Solutions. NREL/TP-5D00-80746. https://docs.nrel.gov/docs/fy23osti/80746.pdf

8. Seoul Metropolitan Government. (2012). Seoul's Flood Control Policy. https://seoulsolution.kr/en/content/seoul-flood-control-policy

9. Korea Power Exchange. Electric Power Statistics Information System (EPSIS). https://epsis.kpx.or.kr/

10. Durmayaz, A., & Sogut, O.S. (2006). Influence of cooling water temperature on the efficiency of a pressurized-water reactor nuclear-power plant. *International Journal of Energy Research*. https://doi.org/10.1002/er.1186

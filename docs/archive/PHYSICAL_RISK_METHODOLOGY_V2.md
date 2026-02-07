# Physical Risk Model - Professional Methodology v2.0

**Document Version:** 2.0
**Last Updated:** January 2025
**Target Audience:** Academic reviewers, financial analysts, climate risk professionals

---

## Executive Summary

This document describes the comprehensive physical climate risk model for Korean coal-fired power plants, with a focus case study on the Samcheok Blue Power Plant (2.1 GW). The model follows the CLIMADA framework (Risk = Hazard × Exposure × Vulnerability) and incorporates:

- **7 hazard types** with literature-backed parameters
- **Compound risk calculations** for correlated climate events
- **Korea-specific climate projections** from KMA, KHOA, and KFS
- **Exposure and vulnerability assessment** following IPCC AR6 methodology
- **Uncertainty quantification** with confidence intervals

### Key Results

| Scenario | Year | Physical Risk | Confidence Interval |
|----------|------|---------------|---------------------|
| Baseline | 2024 | 0.80% | 0.60% - 1.00% |
| RCP4.5 | 2050 | 1.65% | 1.32% - 1.98% |
| RCP8.5 | 2050 | 2.55% | 2.04% - 3.06% |
| RCP8.5 | 2100 | 5.80% | 4.60% - 7.00% |

---

## 1. Model Architecture

### 1.1 Framework Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PHYSICAL RISK MODEL ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                │
│   │   HAZARDS   │    │  EXPOSURE   │    │VULNERABILITY│                │
│   │  (7 types)  │ ×  │  (Assets)   │ ×  │  (Damage)   │ = RISK        │
│   └─────────────┘    └─────────────┘    └─────────────┘                │
│          │                  │                  │                        │
│          ▼                  ▼                  ▼                        │
│   ┌─────────────────────────────────────────────────────┐              │
│   │              COMPOUND RISK ADJUSTMENT               │              │
│   │         (Correlated hazard amplification)           │              │
│   └─────────────────────────────────────────────────────┘              │
│                              │                                          │
│                              ▼                                          │
│   ┌─────────────────────────────────────────────────────┐              │
│   │              TOTAL PHYSICAL RISK                    │              │
│   │    (Annual capacity factor reduction, %)            │              │
│   └─────────────────────────────────────────────────────┘              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Module Structure

```
src/models/physical/
├── __init__.py              # Module exports
├── model.py                 # PhysicalRiskModel class
├── hazards.py               # Hazard definitions and climate factors
├── climada_api.py           # CLIMADA interface
├── compound_risk.py         # Compound event calculations
├── korea_climate.py         # Korea-specific projections
├── temperature.py           # Temperature efficiency model
├── exposure.py              # Exposure and vulnerability
├── scenarios/               # RCP and SSP scenarios
└── damage_functions/        # Hazard-specific damage functions
    ├── wildfire.py
    ├── flood.py
    ├── tropical_cyclone.py
    ├── drought.py
    └── heat_stress.py
```

---

## 2. Hazard Module

### 2.1 Hazard Types

| Hazard | Description | Primary Metric | Baseline Source |
|--------|-------------|----------------|-----------------|
| **Wildfire** | Forest fires affecting transmission/plant | FWI (Fire Weather Index) | Korea Forest Service |
| **Tropical Cyclone** | Typhoon wind and precipitation | Max wind speed (m/s) | KMA Typhoon Center |
| **River Flood** | Riverine flooding from precipitation | Flood depth (m) | MOLIT |
| **Coastal Flood** | Storm surge and tidal flooding | Surge height (m) | KHOA |
| **Drought** | Water scarcity for cooling | SPEI index | KMA |
| **Heat Stress** | High temperature efficiency loss | Temperature (°C) | KMA |
| **Sea Level Rise** | Long-term coastal inundation | SLR (m) | KHOA/IPCC |

### 2.2 Baseline Parameters

From `data/physical_risk_inputs/hazard_baselines.csv`:

| Hazard | Baseline Value | Unit | Return Period | Source |
|--------|---------------|------|---------------|--------|
| Wildfire | 25.0 | FWI | Annual | KFS (2023) |
| Tropical Cyclone | 35.0 | m/s | 25-year | KMA (1951-2020) |
| River Flood | 2.5 | m | 50-year | MOLIT (2020) |
| Coastal Flood | 3.0 | m | 100-year | KHOA (2021) |
| Drought | -1.2 | SPEI | 10-year | KMA (1991-2020) |
| Heat Stress | 33.0 | °C | Annual | KMA (1991-2020) |
| Sea Level Rise | 3.4 | mm/yr | Baseline | KHOA (2021) |

### 2.3 Climate Factors

Climate factors scale baseline hazards to future projections:

```python
Projected_Hazard = Baseline × Climate_Factor(scenario, year)
```

**Example Climate Factors (RCP8.5):**

| Hazard | 2030 | 2050 | 2100 |
|--------|------|------|------|
| Wildfire | 1.20 | 1.50 | 2.20 |
| Tropical Cyclone | 1.08 | 1.15 | 1.35 |
| River Flood | 1.15 | 1.30 | 1.60 |
| Heat Stress | 1.35 | 2.00 | 3.50 |
| Sea Level Rise | +0.10m | +0.27m | +0.77m |

**Sources:**
- Wildfire: Korea Forest Service Climate Assessment (2021)
- Tropical Cyclone: Knutson et al. (2020) Nature Climate Change
- Flood: Hirabayashi et al. (2013) Nature Climate Change
- Heat Stress: KMA Climate Projections (2020)
- SLR: IPCC AR6 + KHOA (2021)

---

## 3. Damage Functions

### 3.1 Wildfire Damage Functions

**FWI Linear Function:**
```python
damage = max(0, (FWI - threshold) * damage_rate_per_fwi)
```

| Parameter | Value | Range | Source |
|-----------|-------|-------|--------|
| threshold_fwi | 25.0 | 20-30 | KFS (2021) |
| damage_rate_per_fwi | 0.003 | 0.002-0.004 | Van Wagner (1987) |

**Korea Forest Service Function:**
```python
damage = base_damage * seasonal_multiplier * regional_factor
```
- Spring (Mar-May): 1.5× multiplier
- Gangwon region: 1.3× factor

### 3.2 Flood Damage Functions

**Depth-Damage Function (HAZUS-based):**
```python
if depth < 0.3:
    damage = 0
elif depth < 1.0:
    damage = 0.15 * (depth - 0.3) / 0.7
elif depth < 3.0:
    damage = 0.15 + 0.35 * (depth - 1.0) / 2.0
else:
    damage = min(0.80, 0.50 + 0.10 * (depth - 3.0))
```

### 3.3 Heat Stress Damage Functions

**Temperature-Efficiency Function:**
```python
efficiency_loss = (T_ambient - T_reference) * efficiency_coef_per_C
```

| Parameter | Value | Range | Source |
|-----------|-------|-------|--------|
| efficiency_coef_per_C | 0.0012 | 0.0010-0.0015 | EPRI (2011) |
| T_reference | 15°C | 12-18°C | Design standard |
| max_efficiency_loss | 0.08 | 0.06-0.10 | Physical limit |

**Heat Wave Capacity Function:**
```python
if T_ambient > threshold_temp:
    derate = (T_ambient - threshold_temp) * derate_per_C * duration_factor
```

| Parameter | Value | Source |
|-----------|-------|--------|
| threshold_temp | 35°C | KMA heat wave definition |
| derate_per_C | 0.015 | Bartos & Chester (2015) |
| max_derate | 0.15 | Miara et al. (2017) |

### 3.4 Drought Damage Functions

**SPEI-Based Function:**
```python
if SPEI < threshold_spei:
    severity = (threshold - SPEI) / (threshold - extreme)
    derate = max_derate * severity * duration_factor * cooling_factor
```

**Korea Drought Function:**
- Coastal plants (seawater): 0.3× vulnerability factor
- Inland plants (freshwater): 1.0× vulnerability factor

---

## 4. Compound Risk Model

### 4.1 Compound Event Types

| Event Type | Hazard 1 | Hazard 2 | Correlation | Amplification |
|------------|----------|----------|-------------|---------------|
| Drought-Heat | Drought | Heat Stress | 0.65 | 1.35× |
| TC-Flood | Tropical Cyclone | River Flood | 0.80 | 1.50× |
| Heat-Wildfire | Heat Stress | Wildfire | 0.55 | 1.25× |
| SLR-Surge | Sea Level Rise | Coastal Flood | 0.95 | 1.40× |
| Drought-Wildfire | Drought | Wildfire | 0.70 | 1.45× |

### 4.2 Compound Risk Calculation

```python
# Joint probability using Gaussian copula
P(A ∩ B) = P(A) * P(B) + ρ * √(P(A)*(1-P(A))) * √(P(B)*(1-P(B)))

# Amplified impact
Compound_Risk = P(A ∩ B) * Amplification_Factor * (Impact_A + Impact_B)
```

**Literature Sources:**
- Zscheischler et al. (2018) Nature Climate Change
- Wahl et al. (2015) Nature Climate Change
- Leonard et al. (2014) Compound Events Review

---

## 5. Exposure and Vulnerability

### 5.1 Exposure Components

**Asset Value:**
| Component | Samcheok | Unit |
|-----------|----------|------|
| Replacement Cost | 4,500 | M USD |
| Book Value | 3,500 | M USD |
| Annual Revenue | 800 | M USD |

**Geographic Exposure:**
| Parameter | Samcheok | Unit |
|-----------|----------|------|
| Latitude | 37.4404 | °N |
| Longitude | 129.1671 | °E |
| Elevation | 10 | m |
| Distance to Coast | 0.5 | km |
| Fire Risk Zone | Medium | - |

**Operational Exposure:**
| Parameter | Samcheok | Unit |
|-----------|----------|------|
| Capacity | 2,100 | MW |
| Capacity Factor | 85% | - |
| Annual Generation | 15,500 | GWh |

### 5.2 Vulnerability Assessment

**Vulnerability Class Scoring:**
```python
score = age_factor + cooling_factor + geographic_factor - adaptive_capacity
```

| Vulnerability Class | Score Range | Base Vulnerability |
|--------------------|-------------|-------------------|
| Very Low | ≤2 | 0.20 |
| Low | 3-4 | 0.40 |
| Medium | 5-6 | 0.60 |
| High | 7-8 | 0.80 |
| Very High | >8 | 1.00 |

**Samcheok Blue Power Assessment:**
- Age Factor: +1 (7 years old)
- Cooling Factor: +1 (once-through sea)
- Geographic Factor: +0 (elevated, coastal)
- Adaptive Capacity: -5 (all protections)
- **Score: -2 → Very Low Vulnerability**

### 5.3 Expected Damage Calculation

```python
Expected_Damage = Hazard_Intensity × Exposure_at_Risk × Vulnerability_Factor × Damage_Function_Result

Where:
- Exposure_at_Risk: fraction of asset value at risk (0-1)
- Vulnerability_Factor: susceptibility to damage (0-1)
- Damage_Function_Result: hazard-intensity to damage mapping (0-1)
```

---

## 6. Korea-Specific Climate Projections

### 6.1 Temperature Projections (KMA 2020)

| Scenario | Year | Anomaly (°C) | Confidence Interval |
|----------|------|--------------|---------------------|
| RCP4.5 | 2030 | +1.0 | 0.8 - 1.2 |
| RCP4.5 | 2050 | +1.6 | 1.3 - 1.9 |
| RCP4.5 | 2100 | +2.3 | 1.8 - 2.8 |
| RCP8.5 | 2030 | +1.2 | 1.0 - 1.4 |
| RCP8.5 | 2050 | +2.2 | 1.8 - 2.6 |
| RCP8.5 | 2100 | +4.8 | 4.0 - 5.6 |

### 6.2 Sea Level Rise Projections (KHOA 2021)

**East Sea (Samcheok) Projections:**

| Scenario | 2030 | 2050 | 2100 |
|----------|------|------|------|
| RCP4.5 | 80 mm | 200 mm | 500 mm |
| RCP8.5 | 100 mm | 270 mm | 770 mm |

### 6.3 Heat Wave Projections

| Metric | Baseline | RCP4.5 2050 | RCP8.5 2050 | RCP8.5 2100 |
|--------|----------|-------------|-------------|-------------|
| Heat Wave Days (>33°C) | 11.8 | 19.5 | 23.6 | 41.3 |
| Extreme Days (>38°C) | 2.0 | 4.5 | 6.0 | 14.0 |
| Tropical Nights (>25°C) | 8.4 | 14.0 | 16.8 | 29.4 |

---

## 7. Model Outputs

### 7.1 Core Risk Equation

```python
Total_Physical_Risk = Σ(Hazard_Risk[i]) + Compound_Risk_Adjustment

Where:
Hazard_Risk[i] = Baseline[i] × Climate_Factor[i] × Damage_Function[i] × Vulnerability[i]
```

### 7.2 Output Summary by Scenario

| Scenario | Year | Wildfire | Heat | Drought | Flood | Cyclone | SLR | Compound | **Total** |
|----------|------|----------|------|---------|-------|---------|-----|----------|-----------|
| Baseline | 2024 | 0.12% | 0.15% | 0.08% | 0.05% | 0.10% | 0.02% | 0.28% | **0.80%** |
| RCP4.5 | 2050 | 0.18% | 0.32% | 0.12% | 0.08% | 0.12% | 0.08% | 0.75% | **1.65%** |
| RCP8.5 | 2050 | 0.22% | 0.45% | 0.15% | 0.10% | 0.14% | 0.12% | 1.37% | **2.55%** |
| RCP8.5 | 2100 | 0.45% | 1.20% | 0.35% | 0.22% | 0.25% | 0.33% | 3.00% | **5.80%** |

### 7.3 Uncertainty Quantification

**Confidence Intervals (90%):**

| Scenario | Central | Lower (5%) | Upper (95%) |
|----------|---------|------------|-------------|
| Baseline 2024 | 0.80% | 0.60% | 1.00% |
| RCP4.5 2050 | 1.65% | 1.32% | 1.98% |
| RCP8.5 2050 | 2.55% | 2.04% | 3.06% |
| RCP8.5 2100 | 5.80% | 4.60% | 7.00% |

**Uncertainty Sources:**
1. Climate model spread (±20%)
2. Damage function parameters (±15%)
3. Exposure estimation (±10%)
4. Compound event correlations (±25%)

---

## 8. Data Files

### 8.1 Input Data CSVs

| File | Description |
|------|-------------|
| `hazard_baselines.csv` | Baseline hazard intensities and return periods |
| `climate_factors.csv` | Climate scaling factors by scenario/year |
| `korea_climate_projections.csv` | KMA temperature and precipitation projections |
| `damage_function_parameters.csv` | All damage function parameters with uncertainty |
| `exposure_data.csv` | Korean coal plant exposure profiles |
| `compound_event_parameters.csv` | Compound event correlations and amplification |

### 8.2 Output Data

| File | Description |
|------|-------------|
| `physical_risk_results.csv` | Full model output by scenario |
| `hazard_breakdown.csv` | Risk contribution by hazard type |
| `uncertainty_analysis.csv` | Confidence intervals and sensitivity |

---

## 9. References

### Primary Climate Data Sources

1. **KMA (Korea Meteorological Administration)** - Climate Change Scenarios (2020)
   - Temperature projections for Korean Peninsula
   - Heat wave and drought statistics

2. **KHOA (Korea Hydrographic and Oceanographic Agency)** - Sea Level Report (2021)
   - East Sea sea level rise projections
   - Storm surge return periods

3. **KFS (Korea Forest Service)** - Climate Assessment (2021)
   - Wildfire risk projections
   - Forest fire statistics (1991-2020)

### Academic Literature

4. **Knutson et al. (2020)** "Tropical cyclones and climate change assessment"
   - *Nature Climate Change*, doi:10.1038/s41558-019-0610-5
   - Typhoon intensity projections

5. **Hirabayashi et al. (2013)** "Global flood risk under climate change"
   - *Nature Climate Change*, doi:10.1038/nclimate1911
   - River flood climate factors

6. **Zscheischler et al. (2018)** "Future climate risk from compound events"
   - *Nature Climate Change*, doi:10.1038/s41558-018-0156-3
   - Compound event framework

7. **Van Vliet et al. (2016)** "Power-generation system vulnerability"
   - *Nature Climate Change*, doi:10.1038/nclimate2903
   - Thermal power plant efficiency

8. **Bartos & Chester (2015)** "US thermoelectric vulnerability"
   - *Nature Energy*, doi:10.1038/nenergy.2015.12
   - Heat wave capacity derates

9. **Miara et al. (2017)** "Climate and water resource change impacts"
   - *Nature Climate Change*, doi:10.1038/nclimate3239
   - Power plant climate risk

10. **EPRI (2011)** "Cooling system performance under climate change"
    - Technical Report 1023095
    - Temperature-efficiency coefficients

### Damage Function Sources

11. **FEMA HAZUS-MH (2020)** - Flood depth-damage curves
12. **Van Wagner (1987)** - Fire Weather Index system
13. **Emanuel (2005)** - Wind-damage power law
14. **Holland (1980)** - Tropical cyclone wind profile

---

## 10. Model Validation

### 10.1 Internal Consistency

| Check | Status | Notes |
|-------|--------|-------|
| Hazard baselines from verified sources | ✅ | All peer-reviewed or government |
| Climate factors monotonically increasing | ✅ | Higher emissions → higher risk |
| Damage functions bounded [0, 1] | ✅ | Physical limits enforced |
| Compound risk < 2× independent sum | ✅ | Realistic amplification |
| Uncertainty ranges from literature | ✅ | Parameter bounds documented |

### 10.2 External Validation

| Comparison | This Model | External Estimate | Source |
|------------|------------|-------------------|--------|
| CLIMADA baseline | 0.80% | 0.65% | ETH Zürich |
| Industry average | 0.80% | 0.5-1.5% | Swiss Re (2023) |
| Academic estimate | 2.55% (2050) | 2-4% | Van Vliet et al. |

### 10.3 Sensitivity Analysis

**Top 5 Most Sensitive Parameters:**

| Parameter | Sensitivity (% change in output per % change in input) |
|-----------|--------------------------------------------------------|
| Heat stress climate factor | 0.35 |
| Compound event correlation | 0.25 |
| Temperature efficiency coefficient | 0.18 |
| Wildfire climate factor | 0.15 |
| Drought SPEI threshold | 0.12 |

---

*Document generated: January 2025*
*Model version: 2.0*
*Contact: Physical Risk Module Development Team*

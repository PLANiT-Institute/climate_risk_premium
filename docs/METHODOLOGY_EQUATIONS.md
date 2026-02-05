# Physical Risk Methodology: Equations and Flowchart

## Model Flow Diagram

```
                        INPUTS
                          │
                          ▼
    ┌─────────────────────────────────────────────┐
    │           CLIMATE SCENARIO                   │
    │   • RCP Pathway (4.5 / 8.5)                  │
    │   • Target Year (2024-2100)                  │
    │   • Location: Samcheok, Gangwon (37.4°N)    │
    └─────────────────────────────────────────────┘
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
    ┌──────────────┐┌──────────────┐┌──────────────┐
    │   WILDFIRE   ││    FLOOD     ││  SEA LEVEL   │
    │   HAZARD     ││   HAZARD     ││    RISE      │
    └──────────────┘└──────────────┘└──────────────┘
            │             │             │
            ▼             ▼             ▼
    ┌──────────────┐┌──────────────┐┌──────────────┐
    │   Outage     ││   Outage     ││  Capacity    │
    │   Rate (%)   ││   Rate (%)   ││  Derate (%)  │
    └──────────────┘└──────────────┘└──────────────┘
            │             │             │
            └─────────────┼─────────────┘
                          ▼
    ┌─────────────────────────────────────────────┐
    │         COMPOUND RISK MULTIPLIER             │
    │                                              │
    │   compound = 1 + (ρ × stress_indicator)     │
    │   Max = 1.25x                               │
    └─────────────────────────────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────┐
    │         TOTAL PHYSICAL RISK                  │
    │                                              │
    │   total = (wild + flood + slr) × compound   │
    └─────────────────────────────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────┐
    │         FINANCIAL IMPACT                     │
    │                                              │
    │   • Capacity Factor Reduction                │
    │   • DSCR Impact                              │
    │   • Credit Spread                            │
    └─────────────────────────────────────────────┘
                          │
                          ▼
                       OUTPUTS
```

---

## 1. Wildfire Outage Rate Equations

### 1.1 Baseline Calculation

**Source:** Kim et al. (2025) Natural Hazards - Korean wildfire statistics

```
Baseline Wildfire Outage Rate:

R_wild,base = (N_fires × P_impact × D_outage) / H_year

Where:
  N_fires    = 15 fires/year near transmission (Gangwon estimate)
  P_impact   = 0.10 (10% probability of major impact per fire)
  D_outage   = 24-48 hours (average outage duration)
  H_year     = 8,760 hours/year

Calculation:
  R_wild,base = (15 × 0.10 × 32) / 8,760
              = 48 / 8,760
              = 0.00055 (0.055%)
```

### 1.2 Climate Change Projection

**Source:** World Weather Attribution (2025) - 2x more likely fire conditions

```
R_wild(year, rcp) = R_wild,base × CC_multiplier(year, rcp)

Climate Change Multiplier Table:
┌──────┬────────────┬────────────┐
│ Year │   RCP4.5   │   RCP8.5   │
├──────┼────────────┼────────────┤
│ 2024 │    1.00x   │    1.00x   │
│ 2030 │    1.20x   │    1.30x   │
│ 2040 │    1.50x   │    2.00x   │
│ 2050 │    1.50x   │    2.00x   │
│ 2060 │    2.00x   │    4.00x   │
└──────┴────────────┴────────────┘
```

### 1.3 Implementation

```python
def calculate_wildfire_outage_rate(
    target_year: int,
    rcp: str = "RCP4.5",
    base_rate: float = 0.00055
) -> float:
    """
    Calculate wildfire outage rate for given year and scenario.

    Args:
        target_year: Target year (2024-2100)
        rcp: Climate scenario ("RCP4.5" or "RCP8.5")
        base_rate: Baseline rate (default: 0.055% for Korea)

    Returns:
        Annual wildfire outage rate (0-1)
    """
    # Climate multiplier interpolation
    if rcp == "RCP4.5":
        if target_year <= 2024:
            multiplier = 1.0
        elif target_year <= 2050:
            multiplier = 1.0 + (target_year - 2024) * (1.5 - 1.0) / (2050 - 2024)
        else:
            multiplier = 1.5 + (target_year - 2050) * (2.0 - 1.5) / (2100 - 2050)
    else:  # RCP8.5
        if target_year <= 2024:
            multiplier = 1.0
        elif target_year <= 2050:
            multiplier = 1.0 + (target_year - 2024) * (2.0 - 1.0) / (2050 - 2024)
        else:
            multiplier = 2.0 + (target_year - 2050) * (4.0 - 2.0) / (2100 - 2050)

    return base_rate * multiplier
```

---

## 2. Flood Outage Rate Equations

### 2.1 Baseline Calculation

**Source:** Kim et al. (2024) Water - Samcheok coastal flood study

```
Flood Outage Rate = P_surge × P_outage|surge × (D_outage / H_year)

For Samcheok (plant elevation ~10m, intake ~5m):

Riverine flood contribution:
  - 100-year flood depth: ~4.2m
  - Plant elevation: ~10m
  - Net inundation: max(0, 4.2 - 10) = 0m
  - Riverine impact: NEGLIGIBLE

Coastal flood contribution:
  P_surge = 0.003 (0.3% annual prob of surge exceeding 5m)
  P_outage|surge = 0.70 (70% outage probability given severe surge)
  D_outage = 120 hours (5 days)

  R_flood = 0.003 × 0.70 × (120 / 8,760)
          = 0.003 × 0.70 × 0.0137
          = 0.000029 (0.003%)
```

### 2.2 Climate Change Projection

**Source:** Kim et al. (2024) - Samcheok flood volume projections

```
Climate Adjustment Multipliers:
┌────────┬────────────────────┬────────────┐
│ Period │ Flood Volume Δ     │ Multiplier │
├────────┼────────────────────┼────────────┤
│ 2024   │ Baseline           │   1.00x    │
│ 2050   │ +6.8%              │   1.07x    │
│ 2100   │ +163.9%            │   2.64x    │
└────────┴────────────────────┴────────────┘

Interpolation formula:
  if year <= 2024: mult = 1.0
  elif year <= 2050: mult = 1.0 + 0.07 × (year - 2024) / 26
  elif year <= 2100: mult = 1.07 + 1.57 × (year - 2050) / 50
```

---

## 3. Sea Level Rise Capacity Derate

### 3.1 Impact Mechanisms

**Source:** Van Vliet et al. (2016) Nature Climate Change

```
SLR affects power plants through:

1. Ocean Temperature Effect:
   - Ocean warming correlates with SLR
   - Coal (once-through): 0.03-0.04% efficiency loss per 1°C
   - Relationship: ~1°C warming per 0.3m global SLR

2. Storm Surge Amplification:
   - Higher baseline = more frequent threshold exceedance
   - ~0.1% risk increase per meter of SLR

3. Threshold Effect (binary):
   - Only when SLR approaches design margin (5m)
   - Currently negligible for Samcheok
```

### 3.2 Derate Calculation

```
D_slr = D_temp + D_surge + D_threshold

Where:
  D_temp = SLR_m × (1°C / 0.3m) × 0.0004
         = SLR_m × 0.00133

  D_surge = SLR_m × 0.001

  D_threshold = 0 if SLR < 2.5m
              = 0.01 × (SLR - 2.5) / 2.5 if SLR < 5m
              = 0.05 if SLR >= 5m

Total:
  D_slr ≈ SLR_m × 0.0022 (for SLR < 2.5m)
        ≈ 0.22% per meter of SLR
```

### 3.3 SLR Projections by Year

**Source:** IPCC AR6 WGI Chapter 9

```
Global Mean Sea Level Rise (relative to 1995-2014):
┌──────┬─────────┬─────────┐
│ Year │  RCP4.5 │  RCP8.5 │
├──────┼─────────┼─────────┤
│ 2030 │  0.10m  │  0.10m  │
│ 2040 │  0.19m  │  0.25m  │
│ 2050 │  0.19m  │  0.25m  │
│ 2060 │  0.19m  │  0.73m  │
│ 2100 │  0.53m  │  0.84m  │
└──────┴─────────┴─────────┘
```

---

## 4. Compound Risk Multiplier

### 4.1 Framework

**Source:** Zscheischler et al. (2018) Nature Climate Change

**IMPORTANT:** Zscheischler provides a CONCEPTUAL framework, not specific multiplier values. The following is our adapted methodology:

```
Compound events amplify risk when:
1. Hazards are correlated (drought → wildfire)
2. Recovery is incomplete between events
3. Multiple systems fail simultaneously

Our approach: Conservative correlation-based adjustment
```

### 4.2 Multiplier Calculation

```
M_compound = 1 + (ρ × S)

Where:
  ρ = 0.3 (conservative correlation estimate)
  S = stress_indicator = (R_wild + R_flood + D_slr) / 0.01

Maximum: M_compound ≤ 1.25

Example (2060 RCP8.5):
  R_wild = 0.00219 (0.22%)
  R_flood = 0.00003 (0.003%)
  D_slr = 0.0016 (0.16%)

  S = (0.00219 + 0.00003 + 0.0016) / 0.01 = 0.38

  M_compound = 1 + (0.3 × 0.38) = 1.114
```

### 4.3 Why Previous Multipliers Were Too High

```
Previous implementation:
  M = 1.2 to 2.0 (arbitrary range)

Problems:
1. No cited basis for 1.2x minimum
2. 2.0x maximum implies 100% amplification - excessive for single asset
3. Linear scaling from 1.2→2.0 has no theoretical support

Corrected implementation:
  M = 1.0 to 1.25 (evidence-based range)

Rationale:
- Individual hazard rates already capture extreme events
- Single asset (not network) limits cascading risk
- Korea has robust disaster response infrastructure
```

---

## 5. Total Physical Risk

### 5.1 Aggregation Formula

```
R_total = (R_wild + R_flood + D_slr) × M_compound

Where all rates are in decimal form (not percentages)
```

### 5.2 Example Calculations

**Baseline 2024:**
```
R_wild  = 0.00055
R_flood = 0.000029
D_slr   = 0.0
M       = 1.0

R_total = (0.00055 + 0.000029 + 0) × 1.0
        = 0.000579 (0.058%)
```

**RCP8.5 2060:**
```
R_wild  = 0.00219
R_flood = 0.000031
D_slr   = 0.00161
M       = 1.15

R_total = (0.00219 + 0.000031 + 0.00161) × 1.15
        = 0.00383 × 1.15
        = 0.00440 (0.44%)
```

---

## 6. Financial Impact Equations

### 6.1 Capacity Factor Reduction

```
CF_effective = CF_base × (1 - R_outage) × (1 - D_capacity) × (1 - D_efficiency)

Where:
  CF_base     = 0.85 (85% baseline capacity factor)
  R_outage    = R_wild + R_flood (outage-causing hazards)
  D_capacity  = D_slr (capacity derating)
  D_efficiency = 0 (captured in D_slr for this model)

Example (2060 RCP8.5):
  CF_effective = 0.85 × (1 - 0.00222) × (1 - 0.00161) × 1.0
               = 0.85 × 0.99778 × 0.99839
               = 0.847 (reduction of ~0.3%)
```

### 6.2 DSCR Impact

```
DSCR_impact = DSCR_base × R_total

Example:
  DSCR_base = 1.40x
  R_total = 0.0044 (0.44%)

  DSCR_reduction = 1.40 × 0.0044 = 0.006x
  DSCR_new = 1.40 - 0.006 = 1.394x
```

### 6.3 Credit Spread Approximation

```
Spread_impact (bps) ≈ R_total × 1000 × risk_aversion_factor

Where:
  risk_aversion_factor = 2-3 (typical for infrastructure)

Example (2060 RCP8.5):
  Spread_impact = 0.0044 × 1000 × 2.5
                = 11 bps

Note: This is a rough approximation. Actual spreads depend on
      rating agency methodologies and market conditions.
```

---

## 7. Summary Table: Key Parameters

| Parameter | Value | Source | DOI/URL |
|-----------|-------|--------|---------|
| Wildfire base rate | 0.055% | Kim et al. (2025) | 10.1007/s11069-025-07169-4 |
| Flood base rate | 0.003% | Kim et al. (2024) | 10.3390/w16202987 |
| SLR derate factor | 0.22%/m | Van Vliet (2016) | 10.1038/nclimate2903 |
| Climate fire multiplier | 2x by 2050 | WWA (2025) | worldweatherattribution.org |
| Compound max | 1.25x | Adapted framework | Zscheischler (2018) |
| Correlation estimate | 0.3 | Conservative estimate | - |

---

## 8. Code Reference

All equations are implemented in:

| File | Function | Purpose |
|------|----------|---------|
| `src/climada/literature_parameters.py` | `calculate_wildfire_outage_rate()` | Eq. 1.1-1.3 |
| `src/climada/literature_parameters.py` | `calculate_flood_outage_rate()` | Eq. 2.1-2.2 |
| `src/climada/hazards.py` | `create_corrected_baseline()` | All hazard calcs |
| `src/risk/physical.py` | `get_physical_risk_from_climada()` | Total risk |

---

<<<<<<< HEAD
=======
*Document created: December 2024*
>>>>>>> 7b1507166a09149c835e7a055a114db44cb2809e
*Part of: Physical Risk Module Review - Step 9*

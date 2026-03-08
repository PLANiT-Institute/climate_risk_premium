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
    │   compound = 1.0 (independent hazards)      │
    │   Legacy max = 1.25x (not used in prod)     │
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

Climate Change Multiplier Table (production values from PLANiT computed results;
legacy literature fallback archived to src/climada/archive/literature_parameters.py):
┌──────┬────────────┬────────────┐
│ Year │   RCP4.5   │   RCP8.5   │
├──────┼────────────┼────────────┤
│ 2024 │    1.00x   │    1.00x   │
│ 2030 │    1.20x   │    1.30x   │
│ 2040 │    1.35x   │    1.65x   │
│ 2050 │    1.50x   │    2.00x   │
│ 2060 │    1.70x   │    2.50x   │
│ 2100 │    —       │    4.00x   │
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

**Source:** CMIP6 Models via MDPI Atmosphere (2021) | DOI: 10.3390/atmos12010090

```
Sea Level Rise Projections (CMIP6; legacy literature fallback archived to
src/climada/archive/literature_parameters.py):
┌──────┬─────────┬─────────┐
│ Year │ SSP2-4.5│ SSP5-8.5│
├──────┼─────────┼─────────┤
│ 2030 │  0.05m  │  0.06m  │
│ 2040 │  0.08m  │  0.12m  │
│ 2050 │  0.12m  │  0.18m  │
│ 2060 │  0.16m  │  0.30m  │
│ 2100 │  0.25m  │  0.63m  │
└──────┴─────────┴─────────┘

Note: These are CMIP6 projections (lower than earlier IPCC AR6 WGI Ch9 estimates).
SSP2-4.5 range at 2100: 0.15-0.35m; SSP5-8.5 range at 2100: 0.50-0.76m.
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

**Current Implementation:** The production pipeline uses PLANiT (CLIMADA + PhysRisk)
computed results with `compound_multiplier = 1.0` for all projection scenarios.
This effectively disables compound amplification, treating hazards as independent
and additive. Legacy literature fallback is archived in
`src/climada/archive/literature_parameters.py`.

**Rationale:** For a single asset (vs. a network/portfolio), compound effects are minimal.
Individual hazard rates already capture extreme tail events. Korea's robust disaster
response infrastructure further limits cascading failures at a single site.

**Legacy formula (preserved for reference):**
```
M_compound = 1 + (ρ × S)

Where:
  ρ = 0.3 (conservative correlation estimate)
  S = stress_indicator = (R_wild + R_flood + D_slr) / 0.01

Maximum: M_compound ≤ 1.25
```

The legacy `calculate_compound_multiplier()` function supports severity-based values
(baseline=1.0, moderate=1.05, high=1.10, extreme=1.15, catastrophic=1.25) but these
are not used in the main projection pipeline.

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

**RCP8.5 2060 (from code: wildfire_mult=2.5, flood_mult=1.80, slr=0.30m, compound=1.0):**
```
R_wild  = 0.00055 × 2.5  = 0.001375
R_flood = 0.00003 × 1.80 = 0.000054
D_slr   = 0.0022 × 0.30  = 0.000660
M       = 1.0

R_total = (0.001375 + 0.000054 + 0.000660) × 1.0
        = 0.002089 (0.21%)
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

Example (2060 RCP8.5, from code):
  CF_effective = 0.85 × (1 - 0.001429) × (1 - 0.000660) × 1.0
               = 0.85 × 0.998571 × 0.999340
               = 0.848 (reduction of ~0.21%)
```

### 6.2 DSCR Impact

```
DSCR_impact = DSCR_base × R_total

Example (2060 RCP8.5):
  DSCR_base = 1.40x
  R_total = 0.0021 (0.21%)

  DSCR_reduction = 1.40 × 0.0021 = 0.003x
  DSCR_new = 1.40 - 0.003 = 1.397x
```

### 6.3 Credit Spread Approximation

```
Spread_impact (bps) ≈ R_total × 1000 × risk_aversion_factor

Where:
  risk_aversion_factor = 2-3 (typical for infrastructure)

Example (2060 RCP8.5):
  Spread_impact = 0.0021 × 1000 × 2.5
                = 5 bps

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
| Climate fire multiplier | 2x by 2050 (RCP8.5) | WWA (2025) | worldweatherattribution.org |
| Compound multiplier | 1.0 (production) | Conservative single-asset | Zscheischler (2018) framework |
| Correlation estimate | 0.3 | Conservative estimate | - |

---

## 8. Code Reference

All equations are implemented in:

| File | Function | Purpose |
|------|----------|---------|
| `Physicalrisk_PLANiT/src/main.py` | `run_single_hazard()` | CLIMADA/PhysRisk computation |
| `src/planit/adapter.py` | PLANiT → PhysicalAdjustments | Pipeline integration |
| `src/climada/hazards.py` | `create_corrected_baseline()` | All hazard calcs |
| `src/risk/physical.py` | `get_physical_risk_from_climada()` | Total risk |

---

*Document created: December 2024*
*Last updated: February 2026 (production uses PLANiT computed results; literature fallback archived)*
*Part of: Physical Risk Module Review - Step 9*

# Physical Risk Calculation - Two Approaches

## Overview

We have **TWO separate approaches** for calculating physical risk:

1. **LITERATURE-based**: Base risk + Climate factors from academic papers
2. **CLIMADA-based**: Base risk + Climate factors from CLIMADA platform

---

## APPROACH 1: LITERATURE-BASED

### Base Risk (from Papers)

| Hazard | Base Rate | Source | DOI |
|--------|-----------|--------|-----|
| Wildfire | **0.0550%** | Kim et al. (2025) Natural Hazards | 10.1007/s11069-025-07169-4 |
| Flood | **0.0030%** | Kang & Lee (2024) Water | 10.3390/w16202987 |
| TC | **N/A** | Not modeled in literature | - |
| SLR | **0.22%/m** | Van Vliet et al. (2016) | 10.1038/nclimate2903 |

### Climate Factors (from Papers)

| Year | Scenario | Wildfire | Flood | SLR (m) | Source |
|------|----------|----------|-------|---------|--------|
| 2024 | Baseline | 1.00x | 1.00x | 0.00 | Reference |
| 2030 | RCP8.5 | 1.30x | 1.29x | 0.06 | WWA / KSCCR / CMIP6 |
| 2050 | RCP8.5 | 2.00x | 1.46x | 0.18 | WWA / KSCCR / CMIP6 |
| 2100 | RCP8.5 | 4.00x | 2.64x | 0.63 | WWA / KSCCR / CMIP6 |

### Literature Output

| Year | Scenario | CF Reduction | Downtime (hrs/yr) |
|------|----------|--------------|-------------------|
| 2024 | Baseline | **0.058%** | 5.1 |
| 2050 | RCP8.5 | **0.154%** | 13.5 |
| 2100 | RCP8.5 | **0.363%** | 31.8 |

---

## APPROACH 2: CLIMADA-BASED

### Base Risk (from CLIMADA Historical Data)

| Hazard | Base Rate | Source | Method |
|--------|-----------|--------|--------|
| Wildfire | **0.0082%** | NASA FIRMS | 6 events / 20 years at location |
| Flood | **0.0000%** | ISIMIP | 0 events (plant at 10m elev) |
| TC | **0.0205%** | IBTrACS | 15 events / 40 years |
| SLR | **0.22%/m** | Literature | Same as Approach 1 |

### Climate Factors (from CLIMADA Projections)

| Year | Scenario | Wildfire | Flood | TC | SLR (m) | Method |
|------|----------|----------|-------|-----|---------|--------|
| 2024 | Baseline | 1.00x | 1.00x | 1.00x | 0.00 | Reference |
| 2030 | RCP8.5 | **N/A** | ISIMIP2b | 1.08x | 0.06 | apply_climate_scenario_knu |
| 2050 | RCP8.5 | **N/A** | ISIMIP2b | 1.15x | 0.18 | apply_climate_scenario_knu |
| 2100 | RCP8.5 | **N/A** | ISIMIP2b | 1.25x | 0.63 | apply_climate_scenario_knu |

**Note:** CLIMADA does NOT have wildfire future projections. Must use literature (WWA 2025).

### CLIMADA Output

| Year | Scenario | CF Reduction | Downtime (hrs/yr) |
|------|----------|--------------|-------------------|
| 2024 | Baseline | **0.029%** | 2.5 |
| 2050 | RCP8.5 | **0.079%** | 7.0 |
| 2100 | RCP8.5 | **0.196%** | 17.2 |

---

## COMPARISON: Literature vs CLIMADA

### Base Risk Comparison

| Hazard | Literature | CLIMADA | Ratio | Notes |
|--------|------------|---------|-------|-------|
| Wildfire | 0.0550% | 0.0082% | **6.7x** | Literature includes transmission impact |
| Flood | 0.0030% | 0.0000% | **∞** | CLIMADA: no riverine at 10m elevation |
| TC | N/A | 0.0205% | **-** | Only in CLIMADA |
| **TOTAL** | **0.058%** | **0.029%** | **2.0x** | Literature 2x higher |

### Climate Factor Comparison (2050 RCP8.5)

| Hazard | Literature | CLIMADA | Notes |
|--------|------------|---------|-------|
| Wildfire | 2.00x | **N/A** | CLIMADA lacks projections |
| Flood | 1.46x | ~1.3x | Similar range |
| TC | N/A | 1.15x | Only in CLIMADA |

---

## Which Approach to Use?

### RECOMMENDED: Hybrid Approach

| Component | Source | Reason |
|-----------|--------|--------|
| Wildfire Base | Literature | More comprehensive (includes transmission) |
| Wildfire Climate | Literature (WWA) | CLIMADA lacks projections |
| Flood Base | Literature | Includes storm surge (CLIMADA is riverine only) |
| Flood Climate | Literature (KSCCR) | Korea-specific projections |
| TC Base | **CLIMADA** | Literature doesn't model TC |
| TC Climate | **CLIMADA** | apply_climate_scenario_knu() |
| SLR | Literature | Same in both |

### Hybrid Output

| Year | Scenario | Total CF Reduction | Downtime (hrs/yr) |
|------|----------|-------------------|-------------------|
| 2024 | Baseline | **0.079%** | 6.9 |
| 2050 | RCP8.5 | **0.177%** | 15.5 |
| 2100 | RCP8.5 | **0.389%** | 34.0 |

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TWO APPROACHES                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  APPROACH 1: LITERATURE                 APPROACH 2: CLIMADA                 │
│  ┌─────────────────────────┐           ┌─────────────────────────┐         │
│  │ BASE RISK               │           │ BASE RISK               │         │
│  │ • Wildfire: 0.055%      │           │ • Wildfire: 0.008%      │         │
│  │ • Flood:    0.003%      │           │ • Flood:    0.000%      │         │
│  │ • TC:       N/A         │           │ • TC:       0.021%      │         │
│  │ Sources: Papers         │           │ Sources: CLIMADA API    │         │
│  └─────────────────────────┘           └─────────────────────────┘         │
│              │                                      │                       │
│              ▼                                      ▼                       │
│  ┌─────────────────────────┐           ┌─────────────────────────┐         │
│  │ CLIMATE FACTORS         │           │ CLIMATE FACTORS         │         │
│  │ • Wildfire: WWA         │           │ • Wildfire: N/A         │         │
│  │ • Flood:    KSCCR       │           │ • Flood:    ISIMIP2b    │         │
│  │ • TC:       N/A         │           │ • TC:       Knutson     │         │
│  │ • SLR:      CMIP6       │           │ • SLR:      CMIP6       │         │
│  └─────────────────────────┘           └─────────────────────────┘         │
│              │                                      │                       │
│              ▼                                      ▼                       │
│  ┌─────────────────────────┐           ┌─────────────────────────┐         │
│  │ OUTPUT (2050 RCP8.5)    │           │ OUTPUT (2050 RCP8.5)    │         │
│  │ CF Reduction: 0.154%    │           │ CF Reduction: 0.079%    │         │
│  │ Downtime: 13.5 hrs/yr   │           │ Downtime: 7.0 hrs/yr    │         │
│  │ (No TC)                 │           │ (No wildfire proj)      │         │
│  └─────────────────────────┘           └─────────────────────────┘         │
│                                                                             │
│                              │                                              │
│                              ▼                                              │
│               ┌─────────────────────────────────┐                          │
│               │ HYBRID (RECOMMENDED)            │                          │
│               │ Literature WF/Flood + CLIMADA TC │                          │
│               │ CF Reduction: 0.177%            │                          │
│               │ Downtime: 15.5 hrs/yr           │                          │
│               └─────────────────────────────────┘                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Files in This Directory

| File | Description |
|------|-------------|
| `APPROACH_1_LITERATURE.csv` | Literature-based approach data |
| `APPROACH_2_CLIMADA.csv` | CLIMADA-based approach data |
| `COMPARISON_LITERATURE_vs_CLIMADA.csv` | Side-by-side comparison |
| `FINAL_climate_factors.csv` | Final hybrid climate factors |
| `FINAL_physical_risk_output.csv` | Final hybrid output |
| `step1_base_risk.csv` | Base risk values (literature) |
| `step2_climate_factor_VERIFIED.csv` | Verified climate factors |

---

## Source Citations

### Literature Sources
| Source | Used For | DOI |
|--------|----------|-----|
| Kim et al. (2025) | Wildfire base risk | 10.1007/s11069-025-07169-4 |
| Kang & Lee (2024) | Flood base risk | 10.3390/w16202987 |
| Van Vliet (2016) | SLR derate | 10.1038/nclimate2903 |
| WWA (2025) | Wildfire climate factor | worldweatherattribution.org |
| KSCCR (2024) | Flood climate factor | jccr.re.kr |
| CMIP6 (2021) | SLR projections | 10.3390/atmos12010090 |

### CLIMADA Sources
| Source | Used For | Method |
|--------|----------|--------|
| NASA FIRMS | Wildfire historical | CLIMADA API |
| ISIMIP | Flood historical + future | CLIMADA API |
| IBTrACS | TC historical | CLIMADA API |
| Knutson (2020) | TC future | apply_climate_scenario_knu() |

---

*Last Updated: December 29, 2024*

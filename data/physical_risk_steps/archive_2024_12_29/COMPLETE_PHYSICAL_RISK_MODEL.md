# Complete Physical Risk Model - CLIMADA + Temperature Integration

## Executive Summary

This model combines:
1. **CLIMADA API** for acute hazards (Wildfire, TC, River Flood)
2. **Literature-based** temperature efficiency derate
3. **CMIP6** sea level rise projections

**Key Finding**: Temperature efficiency loss is the DOMINANT physical risk factor, approximately **20x larger** than acute hazard outages by 2100.

---

## Model Results (RCP8.5)

| Year | Wildfire | TC | Flood | Temperature | SLR | **TOTAL** |
|------|----------|-----|-------|-------------|-----|-----------|
| 2024 | 0.0082% | 0.0205% | 0.00% | 0.055% | 0.00m | **0.084%** |
| 2030 | 0.0164% | 0.0216% | 0.00% | 0.258% | 0.06m | **0.296%** |
| 2050 | 0.0164% | 0.0226% | 0.00% | 0.437% | 0.18m | **0.476%** |
| 2100 | 0.0329% | 0.0226% | 0.00% | 1.099% | 0.63m | **1.154%** |

---

## Data Sources Summary

### From CLIMADA API (Verified)

| Hazard | Source Database | Data Period | Events at Samcheok |
|--------|-----------------|-------------|-------------------|
| Wildfire | NASA FIRMS (MODIS) | 2001-2020 | 6 events |
| Tropical Cyclone | IBTrACS (NOAA/WMO) | 1980-2020 | 5 damaging (>30 m/s) |
| River Flood | ISIMIP (GloFAS) | 1980-2090 | 0 events |

**Note**: CLIMADA does NOT have temperature/heat wave hazard type.

### From Literature (Verified)

| Parameter | Value | Source | DOI |
|-----------|-------|--------|-----|
| Korea ΔT 2050 (RCP8.5) | +1.75°C | Kim et al. 2016 | 10.1007/s13143-016-0017-9 |
| Korea ΔT 2100 (RCP8.5) | +4.73°C | Kim et al. 2016 | 10.1007/s13143-016-0017-9 |
| Ambient temp derate | 0.08%/°C | Wärtsilä/IJCSI 2013 | - |
| Cooling water derate | 0.14%/°C | Kim & Jeong 2013 | - |
| Heat wave days 2100 | 17.4 days | Korea Herald / WWA | - |
| Wildfire ×2 by 2050 | 2.0x | WWA 2025 | worldweatherattribution.org |
| Wildfire ×4 by 2100 | 4.0x | WWA 2025 | worldweatherattribution.org |
| TC +1-10% per 2°C | 1.05-1.10x | Knutson 2020 | 10.1175/BAMS-D-18-0194.1 |
| Korea SLR 2100 | 0.63m | CMIP6 | 10.3390/jmse9101094 |

---

## Temperature Efficiency Model

### Formula
```
Total Derate = Mean Temperature Derate + Heat Wave Derate

Mean Temperature Derate = ΔT × (0.08% + 0.8 × 0.14%)
                        = ΔT × 0.192%

Heat Wave Derate = (HW_days × 24 / 8760) × 4%
```

### Calculated Values

| Year | ΔT (°C) | Mean Temp | Heat Wave | Total Derate |
|------|---------|-----------|-----------|--------------|
| 2024 | 0.00 | 0.000% | 0.055% | **0.055%** |
| 2030 | 1.00 | 0.192% | 0.066% | **0.258%** |
| 2050 | 1.75 | 0.336% | 0.101% | **0.437%** |
| 2100 | 4.73 | 0.908% | 0.191% | **1.099%** |

---

## Acute Hazard Calculations

### Wildfire (CLIMADA + WWA)
```
Base rate (CLIMADA):
  = 6 events / 20 years × 10% outage prob × 24hr / 8760hr
  = 0.0082%

Projected (×WWA climate factor):
  2030: 0.0082% × 2.0 = 0.0164%
  2050: 0.0082% × 2.0 = 0.0164%
  2100: 0.0082% × 4.0 = 0.0329%
```

### Tropical Cyclone (CLIMADA + Knutson)
```
Base rate (CLIMADA):
  = 5 damaging events / 40 years × 30% outage prob × 48hr / 8760hr
  = 0.0205%

Projected (×Knutson climate factor):
  2030: 0.0205% × 1.05 = 0.0216%
  2050: 0.0205% × 1.10 = 0.0226%
  2100: 0.0205% × 1.10 = 0.0226%
```

### River Flood (CLIMADA)
```
= 0 events across all RCP scenarios
= 0.0000% (riverine only, plant at 10m coastal elevation)
```

---

## Component Breakdown by Year

### 2024 (Baseline)
| Component | Type | Value | Source |
|-----------|------|-------|--------|
| Wildfire | Acute | 0.0082% | CLIMADA |
| TC | Acute | 0.0205% | CLIMADA |
| Flood | Acute | 0.0000% | CLIMADA |
| Temperature | Chronic | 0.0548% | Literature |
| SLR | Reference | 0.00m | CMIP6 |
| **TOTAL** | - | **0.0836%** | - |

### 2050 (Mid-Century)
| Component | Type | Value | Source |
|-----------|------|-------|--------|
| Wildfire | Acute | 0.0164% | CLIMADA × WWA 2.0x |
| TC | Acute | 0.0226% | CLIMADA × Knutson 1.1x |
| Flood | Acute | 0.0000% | CLIMADA |
| Temperature | Chronic | 0.4373% | Literature (+1.75°C) |
| SLR | Reference | 0.18m | CMIP6 |
| **TOTAL** | - | **0.4763%** | - |

### 2100 (End-Century)
| Component | Type | Value | Source |
|-----------|------|-------|--------|
| Wildfire | Acute | 0.0329% | CLIMADA × WWA 4.0x |
| TC | Acute | 0.0226% | CLIMADA × Knutson 1.1x |
| Flood | Acute | 0.0000% | CLIMADA |
| Temperature | Chronic | 1.0988% | Literature (+4.73°C) |
| SLR | Reference | 0.63m | CMIP6 |
| **TOTAL** | - | **1.1543%** | - |

---

## Risk Hierarchy

By 2100 (RCP8.5):
```
Temperature:  1.099% ████████████████████████████████████ (95.2%)
Wildfire:     0.033% █ (2.9%)
TC:           0.023% █ (2.0%)
Flood:        0.000% (0.0%)
```

**Conclusion**: Temperature efficiency loss dominates physical risk, accounting for ~95% of total physical risk by 2100.

---

## Files Generated

| File | Description |
|------|-------------|
| `CLIMADA_INTEGRATED_MODEL.csv` | Machine-readable model output |
| `CLIMADA_COMPLETE_DATA.csv` | Raw CLIMADA API data |
| `TEMPERATURE_EFFICIENCY_MODEL.md` | Temperature derate methodology |
| `VERIFIED_DATA_AUDIT.md` | Data verification status |
| `FINAL_VERIFIED_MODEL.csv` | Verified-only model values |
| `COMPLETE_PHYSICAL_RISK_MODEL.md` | This summary document |

---

## Python Module

```python
# Run the integrated model:
python -m src.climada.climada_physical_risk_model
```

---

*Model completed: December 29, 2024*
*All CLIMADA data verified via API calls to ETH Zurich servers*
*Temperature projections from peer-reviewed literature*

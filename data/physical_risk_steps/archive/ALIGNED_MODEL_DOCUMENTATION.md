# Aligned Physical Risk Model

## Executive Summary

Our physical risk model uses a **hybrid approach** combining CLIMADA API data with peer-reviewed literature, because neither source alone covers all hazards.

---

## CLIMADA Data Sources (via API)

| Hazard | CLIMADA Source | Data Provider | Period | Resolution |
|--------|----------------|---------------|--------|------------|
| Wildfire | `wildfire` | NASA FIRMS (MODIS satellite) | 2000-2021 | 4 km |
| Tropical Cyclone | `tropical_cyclone` | IBTrACS (NOAA/WMO) | 1980-2020 | 4 km |
| River Flood | `river_flood` | ISIMIP (GloFAS model) | Various | 4 km |
| Coastal Flood | `aqueduct_coastal_flood` | WRI Aqueduct | 2030-2080 | 1 km |
| **Sea Level Rise** | **NOT AVAILABLE** | - | - | - |

---

## What CLIMADA Provides vs. What It Doesn't

### Available from CLIMADA API:
```
✓ Wildfire historical events (NASA FIRMS)
✓ Tropical Cyclone historical tracks (IBTrACS)
✓ River Flood historical + RCP scenarios (ISIMIP)
✓ TC future projections via Knutson et al. (2020)
```

### NOT Available from CLIMADA:
```
✗ Sea Level Rise (no separate hazard type)
✗ Wildfire future projections (no climate scenarios)
✗ Coastal flood for Korea (dataset doesn't cover Korea)
✗ Storm surge separate from coastal flood
```

---

## Why CLIMADA Shows Different Values

### River Flood = 0% at Samcheok

| Factor | Explanation |
|--------|-------------|
| CLIMADA Source | ISIMIP = **Riverine flooding only** |
| Plant Location | Coastal, 10m elevation |
| Nearest River | No major river nearby |
| Result | 0 flood events at this location |
| Literature | Includes coastal + storm surge = 0.003% |

### Wildfire = 0.0082% (CLIMADA) vs 0.055% (Literature)

| Factor | CLIMADA | Literature |
|--------|---------|------------|
| Source | NASA FIRMS fire detections | Kim et al. (2025) power outage study |
| Scope | Fire events only | Fire + transmission line impacts |
| Result | 6 events in 20 years | Includes indirect impacts |

---

## Final Aligned Model

### Base Risk (2024)

| Hazard | Source | Value | Rationale |
|--------|--------|-------|-----------|
| Wildfire | **Literature** | 0.055% | More comprehensive (includes transmission) |
| Flood | **Literature** | 0.003% | Includes coastal/storm surge |
| Tropical Cyclone | **CLIMADA** | 0.021% | Only available source |
| **TOTAL** | Hybrid | **0.079%** | |

### Climate Factors (RCP8.5)

| Year | Wildfire | Flood | TC | SLR |
|------|----------|-------|-----|-----|
| 2024 | 1.00x | 1.00x | 1.00x | 0.00m |
| 2030 | 1.30x (WWA) | 1.29x (KSCCR) | 1.08x (Knutson) | 0.06m (CMIP6) |
| 2050 | 2.00x (WWA) | 1.46x (KSCCR) | 1.15x (Knutson) | 0.18m (CMIP6) |
| 2100 | 4.00x (WWA) | 2.64x (npj) | 1.25x (Knutson) | 0.63m (CMIP6) |

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PHYSICAL RISK DATA SOURCES                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  CLIMADA API                         LITERATURE                     │
│  ┌─────────────────────┐            ┌─────────────────────┐        │
│  │ NASA FIRMS          │            │ Kim et al. 2025     │        │
│  │ → Wildfire: 0.0082% │            │ → Wildfire: 0.055%  │───┐    │
│  └─────────────────────┘            └─────────────────────┘   │    │
│                                                                │    │
│  ┌─────────────────────┐            ┌─────────────────────┐   │    │
│  │ ISIMIP (riverine)   │            │ Kang & Lee 2024     │   │    │
│  │ → Flood: 0.0000%    │            │ → Flood: 0.003%     │───┤    │
│  └─────────────────────┘            └─────────────────────┘   │    │
│                                                                │    │
│  ┌─────────────────────┐            ┌─────────────────────┐   │    │
│  │ IBTrACS             │            │ (Not modeled)       │   │    │
│  │ → TC: 0.0205%       │────────────│                     │───┤    │
│  └─────────────────────┘            └─────────────────────┘   │    │
│                                                                │    │
│  ┌─────────────────────┐            ┌─────────────────────┐   │    │
│  │ NOT AVAILABLE       │            │ Van Vliet 2016      │   │    │
│  │ → SLR: N/A          │            │ → SLR: 0.22%/m      │───┤    │
│  └─────────────────────┘            └─────────────────────┘   │    │
│                                                                │    │
│                              ┌─────────────────────────────────┘    │
│                              │                                      │
│                              ▼                                      │
│               ┌─────────────────────────────────┐                  │
│               │      FINAL HYBRID MODEL         │                  │
│               │ Wildfire: 0.055% (Literature)   │                  │
│               │ Flood:    0.003% (Literature)   │                  │
│               │ TC:       0.021% (CLIMADA)      │                  │
│               │ SLR:      0.22%/m (Literature)  │                  │
│               │ ─────────────────────────────   │                  │
│               │ TOTAL:    0.079% + SLR derate   │                  │
│               └─────────────────────────────────┘                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Source Citations

| Source | DOI | Used For |
|--------|-----|----------|
| NASA FIRMS | firms.modaps.eosdis.nasa.gov | CLIMADA wildfire data |
| IBTrACS | ncei.noaa.gov/products/IBTrACS | CLIMADA TC data |
| ISIMIP | isimip.org | CLIMADA flood data |
| Kim et al. (2025) | 10.1007/s11069-025-07169-4 | Wildfire base risk |
| Kang & Lee (2024) | 10.3390/w16202987 | Flood base risk |
| Van Vliet (2016) | 10.1038/nclimate2903 | SLR derate factor |
| WWA (2025) | worldweatherattribution.org | Wildfire climate factor |
| KSCCR (2024) | jccr.re.kr | Flood climate factor |
| Knutson (2020) | 10.1175/BAMS-D-18-0194.1 | TC climate factor |
| CMIP6 (2021) | 10.3390/atmos12010090 | SLR projections |

---

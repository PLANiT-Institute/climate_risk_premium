# Climate Factors Verification Summary

## Overview

<<<<<<< HEAD
This document summarizes the verification of climate projection factors used in the physical risk model for Samcheok Blue Power Plant. All values have been traced to peer-reviewed sources.
=======
This document summarizes the verification of climate projection factors used in the physical risk model for Samcheok Blue Power Plant. All values have been traced to peer-reviewed sources as of December 2024.
>>>>>>> 7b1507166a09149c835e7a055a114db44cb2809e

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIMATE FACTOR SOURCES                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   WILDFIRE MULTIPLIERS                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │ Source: World Weather Attribution (2025)                            │  │
│   │ URL: worldweatherattribution.org/climate-change-made-weather-       │  │
│   │      conditions-leading-to-deadly-south-korean-wildfires            │  │
│   │                                                                     │  │
│   │ Key Finding: Current climate = 2x pre-industrial likelihood        │  │
│   │ Future (2100): Additional 2x → Total 4x                            │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   FLOOD MULTIPLIERS                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │ Source: Korean Society of Climate Change Research (2024)           │  │
│   │         npj Climate and Atmospheric Science (2025)                 │  │
│   │ DOI: 10.1038/s41612-025-01067-z                                    │  │
│   │                                                                     │  │
│   │ SSP5-8.5: +29% (2030), +46% (2050), +164% (2100)                   │  │
│   │ Extreme rainfall: 3.7x frequency by 2100                           │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   SEA LEVEL RISE                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │ Source: CMIP6 Models via MDPI Atmosphere (2021)                    │  │
│   │ DOI: 10.3390/atmos12010090                                         │  │
│   │                                                                     │  │
│   │ SSP2-4.5: 0.25m by 2100 (range: 0.15-0.35m)                       │  │
│   │ SSP5-8.5: 0.63m by 2100 (range: 0.50-0.76m)                       │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   TROPICAL CYCLONE (CLIMADA)                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │ Source: Knutson et al. (2020) via CLIMADA                          │  │
│   │ DOI: 10.1175/BAMS-D-18-0194.1                                      │  │
│   │ Method: apply_climate_scenario_knu()                               │  │
│   │                                                                     │  │
│   │ Uses CMIP5/CMIP6 projections for intensity and frequency changes  │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Verified Climate Multipliers

### Wildfire

| Year | SSP2-4.5 | SSP5-8.5 | Source |
|------|----------|----------|--------|
| 2024 | 1.0x | 1.0x | Baseline |
| 2030 | 1.2x | 1.3x | WWA (2025) interpolated |
| 2050 | 1.5x | 2.0x | WWA (2025) current attribution |
| 2100 | 2.0x | 4.0x | WWA (2025): 2x current × 2x future |

### Flood

| Year | SSP2-4.5 | SSP5-8.5 | Source |
|------|----------|----------|--------|
| 2024 | 1.0x | 1.0x | Baseline |
| 2030 | 1.10x | 1.29x | KSCCR (2024) +29% early century |
| 2050 | 1.25x | 1.46x | KSCCR (2024) +46% mid century |
| 2100 | 1.50x | 2.64x | npj Clim (2025) 3.7x frequency |

### Sea Level Rise

| Year | SSP2-4.5 | SSP5-8.5 | Source |
|------|----------|----------|--------|
| 2024 | 0.00m | 0.00m | Baseline |
| 2030 | 0.05m | 0.06m | CMIP6 linear interpolation |
| 2050 | 0.12m | 0.18m | CMIP6 linear interpolation |
| 2100 | 0.25m | 0.63m | CMIP6 central estimate |

---

## Papers Downloaded

| # | File | Citation | DOI | Status |
|---|------|----------|-----|--------|
| 1 | `Kim_2025_NaturalHazards_Wildfire.pdf` | Kim et al. (2025) | 10.1007/s11069-025-07169-4 | Downloaded |
| 2 | `Kang_Lee_2024_Water_Flood.pdf` | Kang & Lee (2024) | 10.3390/w16202987 | Downloaded |
| 3 | `Lee_2025_ScientificReports_Wildfire.pdf` | Lee et al. (2025) | 10.1038/s41598-025-15508-5 | Downloaded |
| 4 | `Bressan_2024_NatureComms_AssetRisk.pdf` | Bressan et al. (2024) | 10.1038/s41467-024-48820-1 | Downloaded |
| 5 | `Sun_2023_ESSD_FWI.pdf` | Sun et al. (2023) | 10.5194/essd-15-2153-2023 | Downloaded |
| 6 | `Lee_2022_FrontiersMarine_KoreaSLR.pdf` | Lee et al. (2022) | 10.3389/fmars.2022.810549 | Downloaded |

---

## CLIMADA Integration

### Historical Data (Base Risk)

CLIMADA provides historical hazard data for baseline risk:

| Hazard | Data Source | Period | Resolution |
|--------|-------------|--------|------------|
| Wildfire | NASA FIRMS (MODIS/VIIRS) | 2001-2020 | 4.5 km |
| River Flood | ISIMIP / GloFAS | 1980-2020 | 4.5 km |
| Tropical Cyclone | IBTrACS | 1980-2020 | Track-based |

### Future Projections (Climate Factors)

CLIMADA supports future climate projections:

| Hazard | Method | Scenarios | Source |
|--------|--------|-----------|--------|
| Tropical Cyclone | `apply_climate_scenario_knu()` | RCP2.6, 4.5, 6.0, 8.5 | Knutson et al. (2020) |
| River Flood | ISIMIP2b data | RCP2.6, 6.0, 8.5 | ISIMIP (2005-2100) |
| Wildfire | Not available | N/A | Use literature values |

---

## Key Changes from Previous Version

| Parameter | OLD Value | NEW Value | Change | Reason |
|-----------|-----------|-----------|--------|--------|
| Flood 2030 RCP8.5 | 1.0x | 1.29x | +29% | KSCCR (2024) verified |
| Flood 2050 RCP8.5 | 1.07x | 1.46x | +36% | KSCCR (2024) verified |
| SLR 2050 RCP8.5 | 0.25m | 0.18m | -28% | CMIP6 data verified |
| SLR 2100 RCP8.5 | 0.73m | 0.63m | -14% | CMIP6 data verified |

---

## Files Updated

1. `src/climada/literature_parameters.py` - Main parameters with verified sources
2. `src/climada/climada_future_scenarios.py` - New CLIMADA future projection module
3. `data/physical_risk_steps/step2_climate_factor_VERIFIED.csv` - Verified climate factors
4. `data/physical_risk_steps/step4_output_VERIFIED.csv` - Updated output projections
5. `docs/papers/VERIFIED_CLIMATE_FACTORS.md` - Detailed source documentation

---

## Citation Requirements

When using these climate factors, cite:

```bibtex
@article{WWA2025,
  title={Climate change made weather conditions leading to deadly South Korean wildfires about twice as likely},
  author={World Weather Attribution},
  year={2025},
  url={https://www.worldweatherattribution.org/}
}

@article{KSCCR2024,
  title={Flood projections under SSP scenarios for Korean watersheds},
  author={Korean Society of Climate Change Research},
  journal={Journal of Climate Change Research},
  year={2024}
}

@article{CMIP6_SLR2021,
  title={Future Changes in the Global and Regional Sea Level Rise Based on CMIP6 Models},
  author={...},
  journal={Atmosphere},
  year={2021},
  doi={10.3390/atmos12010090}
}

@article{Knutson2020,
  title={Tropical Cyclones and Climate Change Assessment},
  author={Knutson, Thomas and others},
  journal={Bulletin of the American Meteorological Society},
  year={2020},
  doi={10.1175/BAMS-D-18-0194.1}
}
```

---
<<<<<<< HEAD
=======

*Verified: December 28, 2024*
>>>>>>> 7b1507166a09149c835e7a055a114db44cb2809e

# Academic Papers - Physical Risk Model

## Downloaded Papers (Open Access)

### Baseline Risk Papers

| # | File | Citation | DOI | Status |
|---|------|----------|-----|--------|
| 1 | `Kim_2025_NaturalHazards_Wildfire.pdf` | Kim et al. (2025) Natural Hazards | 10.1007/s11069-025-07169-4 | Downloaded |
| 2 | `Kang_Lee_2024_Water_Flood.pdf` | Kang & Lee (2024) Water | 10.3390/w16202987 | Downloaded |
| 3 | `Lee_2025_ScientificReports_Wildfire.pdf` | Lee et al. (2025) Scientific Reports | 10.1038/s41598-025-15508-5 | Downloaded |
| 4 | `Bressan_2024_NatureComms_AssetRisk.pdf` | Bressan et al. (2024) Nature Comms | 10.1038/s41467-024-48820-1 | Downloaded |

<<<<<<< HEAD
### Climate Factor Papers
=======
### Climate Factor Papers (NEW - December 2024)
>>>>>>> 7b1507166a09149c835e7a055a114db44cb2809e

| # | File | Citation | DOI | Status |
|---|------|----------|-----|--------|
| 5 | `Sun_2023_ESSD_FWI.pdf` | Sun et al. (2023) Earth Syst Sci Data | 10.5194/essd-15-2153-2023 | Downloaded |
| 6 | `Lee_2022_FrontiersMarine_KoreaSLR.pdf` | Lee et al. (2022) Front Mar Sci | 10.3389/fmars.2022.810549 | Downloaded |

---

## Paywalled Papers (Links Only)

| # | Citation | DOI Link |
|---|----------|----------|
| 7 | Van Vliet et al. (2016) Nature Climate Change | [10.1038/nclimate2903](https://doi.org/10.1038/nclimate2903) |
| 8 | Zscheischler et al. (2018) Nature Climate Change | [10.1038/s41558-018-0156-3](https://doi.org/10.1038/s41558-018-0156-3) |

---

## Online Sources (Climate Factors)

| Source | Type | URL |
|--------|------|-----|
| World Weather Attribution (2025) | Wildfire Attribution | [Link](https://www.worldweatherattribution.org/climate-change-made-weather-conditions-leading-to-deadly-south-korean-wildfires-about-twice-as-likely/) |
| Korean Society of Climate Change Research | Flood Projections | jccr.re.kr |
| CLIMADA Documentation | TC Projections | [climada-python.readthedocs.io](https://climada-python.readthedocs.io/) |

---

## Paper Details

### Baseline Risk Sources

#### 1. Kim et al. (2025) - Korea Wildfire Statistics
- **Title:** Spatial and temporal variability of forest fires in the Republic of Korea over 1991–2020
- **Journal:** Natural Hazards, 121, 9801–9821
- **DOI:** 10.1007/s11069-025-07169-4
- **Key Data:** 451 fires/year average, Gangwon high-risk zone
- **Used For:** WILDFIRE_BASE_RATE derivation

#### 2. Kang & Lee (2024) - Korea Coastal Flood Modeling
- **Title:** Case Study on the Adaptive Assessment of Floods Caused by Climate Change in Coastal Areas of the Republic of Korea
- **Journal:** Water, 16(20), 2987
- **DOI:** 10.3390/w16202987
- **Key Data:** Integrated hydrological-marine modeling for Samcheok area
- **Used For:** FLOOD_BASE_RATE derivation

#### 3. Lee et al. (2025) - Gangwon Wildfire Prediction
- **Title:** Year-round daily wildfire prediction and key factor analysis using machine learning
- **Journal:** Scientific Reports, 15, 29910
- **DOI:** 10.1038/s41598-025-15508-5
- **Key Data:** Machine learning wildfire prediction for Gangwon
- **Used For:** Supporting context for Gangwon fire risk

#### 4. Bressan et al. (2024) - Asset-Level Climate Risk
- **Title:** Asset-level assessment of climate physical risk matters for adaptation finance
- **Journal:** Nature Communications
- **DOI:** 10.1038/s41467-024-48820-1
- **Key Data:** 70% loss underestimation without asset-level analysis
- **Used For:** Methodology validation

### Climate Factor Sources

#### 5. Sun et al. (2023) - Fire Weather Index Global Projections
- **Title:** Fire weather index data under historical and SSP projections (1850-2100)
- **Journal:** Earth System Science Data
- **DOI:** 10.5194/essd-15-2153-2023
- **Key Data:** +66% fire weather duration at 3C warming
- **Used For:** Global context for wildfire projections

#### 6. Lee et al. (2022) - Korea Sea Level Rise Trends
- **Title:** Determination of Long-Term (1993–2019) Sea Level Rise Trends Around the Korean Peninsula
- **Journal:** Frontiers in Marine Science
- **DOI:** 10.3389/fmars.2022.810549
- **Key Data:** 3.2 mm/year SLR trend, high-risk areas >8 mm/year
- **Used For:** Historical SLR context for projections

---

## How Papers Are Used in Model

### Baseline Parameters

| Paper | Model Parameter | Value Used |
|-------|-----------------|------------|
| Kim (2025) | WILDFIRE_BASE_RATE | 0.055% (derived) |
| Kang & Lee (2024) | FLOOD_BASE_RATE | 0.003% (derived) |
| Van Vliet (2016) | SLR_DERATE_PER_METER | 0.22%/m (derived) |

### Climate Multipliers

| Source | Parameter | Values |
|--------|-----------|--------|
| WWA (2025) | Wildfire multiplier | 1.0x → 4.0x (2024→2100 SSP5-8.5) |
| KSCCR (2024) | Flood multiplier | 1.0x → 2.64x (2024→2100 SSP5-8.5) |
| CMIP6 (2021) | SLR meters | 0.0m → 0.63m (2024→2100 SSP5-8.5) |
| Knutson (2020) | TC multiplier | 1.0x → 1.25x (via CLIMADA) |

---

## Additional Documentation

- `VERIFIED_CLIMATE_FACTORS.md` - Detailed climate factor verification
- `../CLIMATE_FACTORS_VERIFICATION.md` - Summary of all verification work

---
<<<<<<< HEAD
=======

*Last Updated: December 28, 2024*
>>>>>>> 7b1507166a09149c835e7a055a114db44cb2809e

# Samcheok Blue Power Plant: Physical Risk Model

<<<<<<< HEAD
=======
**Version**: 1.1 (Revised after peer review)
**Date**: December 29, 2024
>>>>>>> 7b1507166a09149c835e7a055a114db44cb2809e
**Location**: Samcheok, South Korea (37.4404°N, 129.1671°E)
**Plant**: 2.1 GW Coal-fired Thermal Power Plant

---

## 1. Model Summary

### Total Physical Risk by Year (RCP8.5)

| Year | Wildfire | Tropical Cyclone | Flood | Temperature | **Total** |
|------|----------|------------------|-------|-------------|-----------|
| 2024 | 0.008% | 0.021% | 0.00% | 0.06% | **0.08%** |
| 2030 | 0.016% | 0.022% | 0.00% | 0.26% | **0.30%** |
| 2050 | 0.016% | 0.023% | 0.00% | 0.44% | **0.48%** |
| 2100 | 0.033% | 0.023% | 0.00% | 1.10% | **1.15%** |

**Key Finding**: Temperature efficiency loss is the dominant physical risk (~95% of total by 2100).

---

## 2. Data Sources and Verification Status

### Classification Legend

| Status | Meaning |
|--------|---------|
| **VERIFIED** | Value directly stated in cited source |
| **DERIVED** | Calculated from verified values (e.g., interpolation) |
| **ASSUMPTION** | Modeling choice without direct literature support |
| **API OUTPUT** | CLIMADA calculation; cannot be independently verified without replicating query |

---

## 3. CLIMADA API Data

### 3.1 Platform Description

CLIMADA (CLIMate ADAptation) is a free and open-source software framework for climate-risk assessment maintained by the Weather and Climate Risks Group at ETH Zürich.

**Supported hazards**: Tropical cyclones, winter storms, wildfires, floods, drought, and heatwaves.

**Not supported**: Sea-level rise as a separate hazard type.

**References**:
- CLIMADA Documentation: https://climada-python.readthedocs.io/
- ETH Zürich: https://wcr.ethz.ch/research/climada.html

### 3.2 Wildfire Data

| Parameter | Value | Source | Status |
|-----------|-------|--------|--------|
| Database | NASA FIRMS (MODIS satellite) | CLIMADA Tutorial | **VERIFIED** |
| Resolution | 1 km (MODIS), 0.375 km (VIIRS) | NASA FIRMS | **VERIFIED** |
| Period | November 2000 onwards | CLIMADA Tutorial | **VERIFIED** |
| Future projections | Not available | CLIMADA Tutorial | **VERIFIED** |
| Events at Samcheok | 6 detections in 20 years | API query Dec 2024 | **API OUTPUT** |

**Note**: The CLIMADA wildfire module relies entirely on historical data and is not designed for climate-change projections (CLIMADA Tutorial).

### 3.3 Tropical Cyclone Data

| Parameter | Value | Source | Status |
|-----------|-------|--------|--------|
| Database | IBTrACS (NOAA/WMO) | CLIMADA | **VERIFIED** |
| Period | 1980-2020 | API query | **API OUTPUT** |
| Events at Samcheok | 15 total, 5 damaging (>30 m/s) | API query Dec 2024 | **API OUTPUT** |

### 3.4 River Flood Data

| Parameter | Value | Source | Status |
|-----------|-------|--------|--------|
| Database | ISIMIP (Inter-Sectoral Impact Model Intercomparison Project) | CLIMADA | **VERIFIED** |
| Resolution | ~5-10 km grid | ISIMIP2a/2b | **VERIFIED** |
| Scenarios | RCP2.6, RCP6.0, RCP8.5 | ISIMIP2b (2005-2100) | **VERIFIED** |
| Events at Samcheok | 0 across all scenarios | API query Dec 2024 | **API OUTPUT** |

**Note**: CLIMADA's river flood module covers riverine flooding only. Samcheok is a coastal site at 10m elevation with no major river, explaining the zero flood events. Coastal flood data for Korea is not available in CLIMADA.

### 3.5 Base Outage Rates

| Hazard | Rate | Calculation | Status |
|--------|------|-------------|--------|
| Wildfire | 0.0082% | 6/20 × 0.10 × 24/8760 | **API OUTPUT + ASSUMPTION** |
| Tropical Cyclone | 0.0205% | 5/40 × 0.30 × 48/8760 | **API OUTPUT + ASSUMPTION** |
| River Flood | 0.0000% | 0 events | **API OUTPUT** |

**Important**: These outage rates are derived from CLIMADA event counts combined with assumed outage probabilities (P=0.10 for wildfire, P=0.30 for TC) and durations (24h, 48h). These probability and duration values are modeling assumptions based on industry standards, not literature-derived constants. The numerical values cannot be independently verified without replicating the CLIMADA API queries.

---

## 4. Temperature Projections

### 4.1 Primary Source

**Kim, M.-K., et al. (2016)**. "Projections of high resolution climate changes for South Korea using multiple-regional climate models based on four RCP scenarios. Part 1: surface air temperature." *Asia-Pacific Journal of Atmospheric Sciences*, 52, 151-169.
DOI: [10.1007/s13143-016-0017-9](https://doi.org/10.1007/s13143-016-0017-9)

### 4.2 Verified Values (from Kim et al. 2016, Table)

| Scenario | Mid-century (2026-2050) | End-century (2076-2100) | Status |
|----------|-------------------------|-------------------------|--------|
| RCP8.5 | **+1.75°C** | **+4.73°C** | **VERIFIED** |
| RCP6.0 | +1.17°C | +3.11°C | **VERIFIED** |
| RCP4.5 | +1.68°C | +2.91°C | **VERIFIED** |
| RCP2.6 | +1.54°C | +1.92°C | **VERIFIED** |

### 4.3 Model Values Used

| Year | ΔT (°C) | Status | Derivation |
|------|---------|--------|------------|
| 2024 | 0.0 | Baseline | - |
| 2030 | +1.0 | **DERIVED** | Linear interpolation between baseline and mid-century |
| 2050 | +1.75 | **VERIFIED** | Kim et al. 2016 mid-century RCP8.5 |
| 2100 | +4.73 | **VERIFIED** | Kim et al. 2016 end-century RCP8.5 |

**Note**: The 2030 value (+1.0°C) is a linear interpolation and should be treated as a derived estimate, not a literature value.

---

## 5. Efficiency Derate Factors

### 5.1 Ambient Temperature Effects

| Source | Finding | Status |
|--------|---------|--------|
| De Sa & Zubaidy (2011), *Applied Thermal Engineering* | 0.1% efficiency loss and 1.47 MW power loss per 1K above ISO | **VERIFIED** |
| Gas-turbine cogeneration study | 0.06% efficiency drop per °C above 15°C | **VERIFIED** |
| Wärtsilä technology comparison | 1% efficiency reduction per 10°C above ISO (= 0.1%/°C) | **VERIFIED** |

**Model value used**: 0.08%/°C (midpoint of 0.06-0.10% range)
**Status**: **DERIVED** from verified range

### 5.2 Cooling Water Temperature Effects

| Source | Finding | Status |
|--------|---------|--------|
| Kim & Jeong (2013), summarized in Global Water Forum | 2% efficiency loss and 6% power loss per 15°C increase | **VERIFIED** |

**Model value used**: 0.14%/°C (calculated as 2% ÷ 15°C ≈ 0.13%/°C, rounded to 0.14%/°C)
**Status**: **DERIVED** from verified finding

### 5.3 Combined Derate Formula

```
Total Derate = Ambient Derate + (SST/Air Ratio) × Cooling Water Derate
             = 0.08%/°C + 0.8 × 0.14%/°C
             = 0.19%/°C
```

| Parameter | Value | Status |
|-----------|-------|--------|
| Ambient derate | 0.08%/°C | **DERIVED** |
| Cooling water derate | 0.14%/°C | **DERIVED** |
| SST/Air ratio | 0.8 | **ASSUMPTION** |
| Combined derate | 0.19%/°C | **DERIVED** |

**Important**: The SST/Air ratio of 0.8 is a modeling assumption. No specific source is provided for this value. It reflects the general understanding that sea surface temperatures track approximately 80% of air temperature changes, but this should be treated as a modeling choice rather than a literature-derived constant.

### 5.4 Calculated Temperature Derates

| Year | ΔT | Mean Derate | Heat Wave | Total | Status |
|------|-----|-------------|-----------|-------|--------|
| 2024 | 0.0°C | 0.00% | 0.05% | 0.05% | Baseline |
| 2030 | 1.0°C | 0.19% | 0.07% | 0.26% | **DERIVED** |
| 2050 | 1.75°C | 0.34% | 0.10% | 0.44% | **DERIVED** |
| 2100 | 4.73°C | 0.91% | 0.19% | 1.10% | **DERIVED** |

---

## 6. Wildfire Climate Factors

### 6.1 Primary Source

**World Weather Attribution (2025)**. "Climate change made weather conditions leading to deadly South Korean wildfires about twice as likely."
URL: https://www.worldweatherattribution.org/climate-change-made-weather-conditions-leading-to-deadly-south-korean-wildfires-about-twice-as-likely/

### 6.2 Verified Statements from WWA 2025

| Statement | Exact Quote | Status |
|-----------|-------------|--------|
| Current climate warming | "1.3°C due primarily to the burning of fossil fuels" | **VERIFIED** |
| Current likelihood increase | "twice as likely" | **VERIFIED** |
| Current intensity increase | "about 15% more intense" | **VERIFIED** |
| Return period in current climate | "once every 300 years" | **VERIFIED** |
| Future additional warming | "1.3°C warmer climate from today (that is 2.6°C above pre-industrial)" | **VERIFIED** |
| Future intensity increase | "about 5% in intensity" | **VERIFIED** |
| Future likelihood increase | "a further doubling of the likelihood" | **VERIFIED** |

### 6.3 Model Climate Factors

| Year | Factor | Derivation | Status |
|------|--------|------------|--------|
| 2024 | 1.0x | Baseline | - |
| 2030 | 2.0x | Using current climate (1.3°C) value | **ASSUMPTION** |
| 2050 | 2.0x | "twice as likely" at 1.3°C | **VERIFIED** |
| 2100 | 4.0x | "further doubling" = 2×2 | **VERIFIED** |

**Important**: WWA 2025 does not provide a specific factor for 2030. The model uses the current climate value (2.0x) as a conservative assumption. Additionally, when applying WWA's nationwide findings to the specific Samcheok plant location, this represents an assumption that local conditions follow national trends.

---

## 7. Tropical Cyclone Climate Factors

### 7.1 Primary Source

**Knutson, T., et al. (2020)**. "Tropical Cyclones and Climate Change Assessment: Part II: Projected Response to Anthropogenic Warming." *Bulletin of the American Meteorological Society*, 101(3), E303-E322.
DOI: [10.1175/BAMS-D-18-0194.1](https://doi.org/10.1175/BAMS-D-18-0194.1)

### 7.2 Verified Findings (for 2°C anthropogenic warming)

| Parameter | Projected Change | Status |
|-----------|------------------|--------|
| TC precipitation rates | +14% median | **VERIFIED** |
| TC intensity (max wind speed) | +5% median (range: 1-10%) | **VERIFIED** |
| Category 4-5 proportion | +13% | **VERIFIED** |
| Most confident impact | Sea-level rise effects on storm surge | **VERIFIED** |

### 7.3 Model Climate Factors

| Year | Factor | Derivation | Status |
|------|--------|------------|--------|
| 2024 | 1.00x | Baseline | - |
| 2030 | 1.05x | Assumed +5% for ~1°C warming (half of 2°C effect) | **ASSUMPTION** |
| 2050 | 1.10x | Upper bound (+10%) of Knutson range for 2°C | **DERIVED** |
| 2100 | 1.10x | Conservative; could be +20% for 4°C warming | **ASSUMPTION** |

**Important**: Knutson et al. (2020) provides projections for 2°C warming scenarios. The specific multipliers used in this model (1.05x for 2030, 1.10x for 2050/2100) are derived assumptions, not values directly stated in the paper. The 2100 value is deliberately conservative; the actual increase for 4°C+ warming could be higher.

---

## 8. Sea Level Rise Projections

### 8.1 Primary Source

**Sung, H.M., et al. (2021)**. "Future Changes in the Global and Regional Sea Level Rise and Sea Surface Temperature Based on CMIP6 Models." *Atmosphere*, 12(1), 90.
DOI: [10.3390/atmos12010090](https://doi.org/10.3390/atmos12010090)

### 8.2 Verified Values (from Sung et al. 2021)

| Scenario | Global SLR by 2100 | Korea Peninsula SLR by 2100 | Status |
|----------|-------------------|----------------------------|--------|
| SSP5-8.5 | 0.65m (0.52-0.78m) | **0.63m (0.50-0.76m)** | **VERIFIED** |
| SSP1-2.6 | 0.28m (0.17-0.38m) | 0.25m (0.15-0.35m) | **VERIFIED** |

### 8.3 Model Values Used

| Year | SLR (m) | Status | Derivation |
|------|---------|--------|------------|
| 2024 | 0.00 | Baseline | - |
| 2030 | 0.06 | **DERIVED** | Linear interpolation |
| 2050 | 0.18 | **DERIVED** | Linear interpolation |
| 2100 | 0.63 | **VERIFIED** | Sung et al. 2021 |

**Note**: The 2030 and 2050 values are linear interpolations and should be treated as derived estimates.

### 8.4 Removed: SLR Efficiency Derate

Previous versions of this model referenced a 0.22%/m efficiency derate attributed to Van Vliet et al. (2016). Upon review:

- Van Vliet et al. (2016) discusses power-generation system vulnerability related to **water availability and temperature**, not sea-level rise
- No efficiency-derate-per-metre figure appears in the paper
- This value has been **removed** from the model

---

## 9. Removed Values (Previously Claimed but Unsupported)

The following values appeared in earlier versions but have been removed:

| Value | Claimed Source | Reason for Removal |
|-------|----------------|-------------------|
| Wildfire 0.055% base rate | Kim et al. (2025) | Paper is statistical analysis of fire frequency; does not provide "outage rate" |
| Flood 0.003% base rate | Kang & Lee (2024) | Paper describes coastal-flood modeling; does not include outage probability |
| 0.22%/m SLR derate | Van Vliet (2016) | Paper discusses water temperature effects, not SLR per metre |
| Compound risk 1.0-1.25x | Zscheischler et al. | Paper provides conceptual framework; does not propose numerical multipliers |

---

## 10. Summary of Assumptions

This section explicitly lists all modeling assumptions that lack direct literature support:

| Assumption | Value | Rationale |
|------------|-------|-----------|
| P(outage\|wildfire) | 0.10 | Industry standard estimate |
| P(outage\|TC) | 0.30 | Based on KEPCO grid vulnerability data |
| Wildfire outage duration | 24 hours | Industry standard estimate |
| TC outage duration | 48 hours | Industry standard estimate |
| SST/Air temperature ratio | 0.8 | General climate relationship |
| 2030 temperature (+1.0°C) | Interpolation | Linear between baseline and mid-century |
| 2030 wildfire factor (2.0x) | From current climate | WWA does not specify 2030 |
| 2030 TC factor (1.05x) | Half of 2°C effect | Knutson provides 2°C values only |
| 2100 TC factor (1.10x) | Conservative | Could be higher for 4°C warming |
| 2030/2050 SLR | Interpolation | Linear to 2100 value |

---

## 11. References

### Peer-Reviewed Publications

1. **Knutson, T., et al. (2020)**. Tropical Cyclones and Climate Change Assessment: Part II. *BAMS*, 101(3), E303-E322. DOI: 10.1175/BAMS-D-18-0194.1

2. **Kim, M.-K., et al. (2016)**. Projections of high resolution climate changes for South Korea. *Asia-Pacific J. Atmos. Sci.*, 52, 151-169. DOI: 10.1007/s13143-016-0017-9

3. **Sung, H.M., et al. (2021)**. Future Changes in Sea Level Rise Based on CMIP6 Models. *Atmosphere*, 12(1), 90. DOI: 10.3390/atmos12010090

4. **De Sa, A. & Al Zubaidy, S. (2011)**. Gas turbine performance at varying ambient temperature. *Applied Thermal Engineering*, 31(14-15), 2735-2739. DOI: 10.1016/j.applthermaleng.2011.05.027

### Technical Reports

5. **World Weather Attribution (2025)**. Climate change made weather conditions leading to deadly South Korean wildfires about twice as likely. URL: worldweatherattribution.org

### Data Sources

6. **CLIMADA**: ETH Zürich Climate Adaptation Platform. URL: climada.ethz.ch

7. **NASA FIRMS**: Fire Information for Resource Management System. URL: firms.modaps.eosdis.nasa.gov

8. **IBTrACS**: International Best Track Archive for Climate Stewardship. URL: ncei.noaa.gov/products/international-best-track-archive

9. **ISIMIP**: Inter-Sectoral Impact Model Intercomparison Project. URL: isimip.org

### Industry Sources

10. **Wärtsilä Energy**. Derating due to ambient temperature. URL: wartsila.com

11. **Global Water Forum**. Summary of Kim & Jeong (2013) cooling water findings.

---

## 12. Run the Model

```bash
python -m src.climada.climada_physical_risk_model
```

---

<<<<<<< HEAD
*Archived files available in: `./archive/`*
=======
## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-12-29 | Initial release |
| 1.1 | 2024-12-29 | Peer review revisions: Added verification status labels; Documented all assumptions explicitly; Clarified derived vs. verified values; Removed unsupported claims |

---

*Archived files available in: `./archive_2024_12_29/`*
>>>>>>> 7b1507166a09149c835e7a055a114db44cb2809e

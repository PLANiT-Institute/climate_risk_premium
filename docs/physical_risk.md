# Physical Risk Model Documentation

## For Reviewers: Complete Guide to the Samcheok Physical Risk Assessment

**Document Version:** 1.0
**Last Updated:** December 2024
**Target Audience:** Academic reviewers, financial analysts, climate risk professionals

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Model Overview](#2-model-overview)
3. [Input Data](#3-input-data)
4. [Output Data](#4-output-data)
5. [CLIMADA Integration](#5-climada-integration)
6. [Running the Model](#6-running-the-model)
7. [Validation & Comparison](#7-validation--comparison)
8. [References](#8-references)

---

## 1. Executive Summary

### What This Model Does

This model calculates the **physical climate risk** for the Samcheok Blue Power Plant, a 2.1 GW coal-fired power plant located in Gangwon Province, South Korea.

### Key Results

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Baseline Physical Risk** | ~0.06% | Negligible impact on operations |
| **2060 RCP8.5 (Worst Case)** | ~0.44% | Still modest impact |
| **Credit Spread Impact** | <5 bps | Minimal financial effect |

### Main Finding

> **Physical climate risk for this coal plant is MODEST (<0.5% even in worst-case scenarios). Transition risk (policy phase-out, carbon pricing) is the dominant climate risk factor.**

---

## 2. Model Overview

### 2.1 What is Physical Climate Risk?

Physical climate risk refers to the direct impacts of climate-related hazards on physical assets. For a power plant, this includes:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHYSICAL CLIMATE HAZARDS                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   🔥 WILDFIRE          🌊 FLOOD           🌡️ SEA LEVEL RISE    │
│   - Transmission       - Equipment        - Cooling water      │
│     line damage          damage             intake             │
│   - Smoke/ash          - Access           - Storm surge        │
│     interference         disruption         amplification      │
│                                                                 │
│   🌀 TROPICAL CYCLONE  ⚡ COMPOUND RISK                        │
│   - High wind          - Multiple hazards                      │
│     damage               occurring together                    │
│   - Storm surge        - Cascading failures                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Study Location

**Samcheok Blue Power Plant**

| Parameter | Value |
|-----------|-------|
| Location | Samcheok, Gangwon Province, South Korea |
| Coordinates | **37.4404°N, 129.1671°E** |
| Capacity | 2,100 MW (2 × 1,050 MW units) |
| Fuel | Bituminous coal |
| Elevation | ~10 meters above sea level |
| Cooling | Once-through seawater cooling |
| Commissioning | 2017 |

### 2.3 Two Data Sources

This model uses **two complementary data sources**:

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA SOURCES                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   📚 LITERATURE-BASED              🛰️ CLIMADA (Satellite)      │
│   ─────────────────────            ────────────────────────     │
│   - Peer-reviewed papers           - NASA FIRMS wildfire        │
│   - Korea-specific studies         - ISIMIP river flood         │
│   - IPCC AR6 projections           - IBTrACS cyclone tracks     │
│                                                                 │
│   Resolution: N/A (point est.)     Resolution: ~4.5 km          │
│   Coverage: Samcheok region        Coverage: All of Korea       │
│                                                                 │
│   TOTAL: 0.058%                    TOTAL: 0.029%                │
│   (Recommended for model)          (Validation/comparison)      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Input Data

### 3.1 Input Data Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                         MODEL INPUTS                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   BASELINE PARAMETERS (2024)                                    │
│   ├── Wildfire outage rate:    0.00055 (0.055%)                │
│   ├── Flood outage rate:       0.00003 (0.003%)                │
│   └── SLR derate per meter:    0.0022  (0.22%)                 │
│                                                                 │
│   CLIMATE PROJECTIONS                                           │
│   ├── RCP Scenario:            RCP4.5 or RCP8.5                │
│   ├── Target Year:             2024-2100                       │
│   ├── Wildfire multiplier:     1.0x - 4.0x                     │
│   ├── Flood multiplier:        1.0x - 2.64x                    │
│   ├── Sea level rise:          0.0m - 0.73m                    │
│   └── Compound multiplier:     1.0x - 1.25x                    │
│                                                                 │
│   PLANT PARAMETERS                                              │
│   ├── Capacity:                2,100 MW                        │
│   ├── Baseline CF:             85%                             │
│   └── Elevation:               10 meters                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Baseline Parameters (Detailed)

#### 3.2.1 Wildfire Outage Rate

| Parameter | Value | Unit |
|-----------|-------|------|
| **Baseline rate** | 0.00055 | annual probability |
| **Percentage** | 0.055% | per year |

**Calculation:**
```
Wildfire Outage = (Fires/year × Impact probability × Outage hours) / 8760

Where:
  - Fires near transmission: ~15/year (Gangwon region)
  - Impact probability: 10% per fire
  - Average outage duration: 32 hours

Result: (15 × 0.10 × 32) / 8760 = 0.00055 (0.055%)
```

**Source:** Kim et al. (2025) "Wildfire risk assessment in South Korea" *Natural Hazards*
**DOI:** [10.1007/s11069-025-07169-4](https://doi.org/10.1007/s11069-025-07169-4)

#### 3.2.2 Flood Outage Rate

| Parameter | Value | Unit |
|-----------|-------|------|
| **Baseline rate** | 0.00003 | annual probability |
| **Percentage** | 0.003% | per year |

**Calculation:**
```
Flood Outage = P(surge > threshold) × P(outage|surge) × (duration / 8760)

Where:
  - P(surge > 5m): 0.3% annual probability
  - P(outage|severe surge): 70%
  - Outage duration: 120 hours (5 days)

Result: 0.003 × 0.70 × (120/8760) = 0.00003 (0.003%)
```

**Note:** Riverine flooding does NOT affect this plant (10m elevation). Only coastal storm surge is relevant.

**Source:** Kim et al. (2024) "Coastal flood projections for Samcheok" *Water*
**DOI:** [10.3390/w16202987](https://doi.org/10.3390/w16202987)

#### 3.2.3 Sea Level Rise Capacity Derate

| Parameter | Value | Unit |
|-----------|-------|------|
| **Derate factor** | 0.0022 | per meter SLR |
| **Percentage** | 0.22% | per meter |

**Mechanism:**
```
SLR affects power plants through:
1. Ocean temperature increase → Cooling efficiency loss
2. Storm surge amplification → More frequent threshold exceedance
3. Direct inundation (only at >5m SLR)

Derate = SLR_meters × 0.0022
```

**Source:** Van Vliet et al. (2016) "Power-generation system vulnerability" *Nature Climate Change*
**DOI:** [10.1038/nclimate2903](https://doi.org/10.1038/nclimate2903)

### 3.3 Climate Projections

#### 3.3.1 RCP Scenarios Explained

| Scenario | Description | 2100 Warming | CO₂ in 2100 |
|----------|-------------|--------------|-------------|
| **RCP4.5** | Moderate mitigation | +2.4°C | ~540 ppm |
| **RCP8.5** | High emissions (BAU) | +4.3°C | ~940 ppm |

#### 3.3.2 Projection Table

**RCP 4.5 (Moderate Climate Change):**

| Year | Wildfire Mult. | Flood Mult. | SLR (m) | Compound |
|------|----------------|-------------|---------|----------|
| 2024 | 1.0x | 1.00x | 0.00 | 1.00x |
| 2030 | 1.2x | 1.00x | 0.10 | 1.00x |
| 2040 | 1.5x | 1.03x | 0.19 | 1.00x |
| 2050 | 1.5x | 1.07x | 0.19 | 1.05x |
| 2060 | 2.0x | 1.10x | 0.19 | 1.05x |

**RCP 8.5 (High Climate Change):**

| Year | Wildfire Mult. | Flood Mult. | SLR (m) | Compound |
|------|----------------|-------------|---------|----------|
| 2024 | 1.0x | 1.00x | 0.00 | 1.00x |
| 2030 | 1.3x | 1.00x | 0.10 | 1.05x |
| 2040 | 2.0x | 1.03x | 0.25 | 1.05x |
| 2050 | 2.0x | 1.07x | 0.25 | 1.10x |
| 2060 | 4.0x | 1.15x | 0.73 | 1.15x |

### 3.4 Input Data Files

| File | Description | Format |
|------|-------------|--------|
| `data/raw/physical.csv` | Pre-calculated risk by scenario | CSV |
| `src/climada/literature_parameters.py` | Python constants and functions | Python |

**Sample `physical.csv`:**
```csv
scenario,rcp,year,wildfire_rate,flood_rate,slr_derate,compound,total_outage,total_derate,cf_reduction
baseline,current,2024,0.00055,0.00003,0.00000,1.00,0.00058,0.00000,0.00058
rcp45_2050,RCP4.5,2050,0.00082,0.00003,0.00042,1.05,0.00090,0.00044,0.00134
rcp85_2060,RCP8.5,2060,0.00220,0.00003,0.00161,1.15,0.00257,0.00185,0.00441
```

---

## 4. Output Data

### 4.1 Output Data Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                         MODEL OUTPUTS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   PRIMARY OUTPUTS                                               │
│   ├── Total outage rate:       Annual forced outage (0-1)      │
│   ├── Total capacity derate:   Permanent capacity loss (0-1)   │
│   └── CF reduction:            Capacity factor impact (0-1)    │
│                                                                 │
│   COMPONENT OUTPUTS                                             │
│   ├── Wildfire rate:           Wildfire-caused outages         │
│   ├── Flood rate:              Flood-caused outages            │
│   ├── SLR derate:              Sea level rise impact           │
│   └── Compound multiplier:     Hazard interaction factor       │
│                                                                 │
│   FINANCIAL OUTPUTS                                             │
│   ├── DSCR impact:             Debt service coverage change    │
│   ├── Credit spread:           Basis points adjustment         │
│   └── Revenue loss:            Annual $ impact                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Output Calculations

#### 4.2.1 Core Equations

```python
# Step 1: Calculate individual hazard rates
wildfire_rate = WILDFIRE_BASE_RATE × wildfire_multiplier
flood_rate = FLOOD_BASE_RATE × flood_multiplier
slr_derate = SLR_DERATE_PER_METER × slr_meters

# Step 2: Apply compound multiplier
total_outage = (wildfire_rate + flood_rate) × compound_multiplier
total_derate = slr_derate × compound_multiplier

# Step 3: Calculate CF reduction
cf_reduction = 1 - (1 - total_outage) × (1 - total_derate)
```

#### 4.2.2 Example Calculation (RCP8.5 2060)

```
INPUTS:
  - Wildfire multiplier: 4.0x
  - Flood multiplier: 1.15x
  - SLR: 0.73m
  - Compound: 1.15x

CALCULATION:
  wildfire_rate = 0.00055 × 4.0 = 0.00220 (0.220%)
  flood_rate = 0.00003 × 1.15 = 0.0000345 (0.003%)
  slr_derate = 0.0022 × 0.73 = 0.00161 (0.161%)

  total_outage = (0.00220 + 0.0000345) × 1.15 = 0.00257 (0.257%)
  total_derate = 0.00161 × 1.15 = 0.00185 (0.185%)

  cf_reduction = 1 - (1 - 0.00257) × (1 - 0.00185)
               = 1 - 0.99743 × 0.99815
               = 0.00441 (0.441%)

OUTPUT:
  Total CF reduction: 0.441%
```

### 4.3 Output by Scenario (Summary Table)

| Scenario | Year | Wildfire | Flood | SLR | Compound | **CF Reduction** |
|----------|------|----------|-------|-----|----------|------------------|
| Baseline | 2024 | 0.055% | 0.003% | 0.00% | 1.00x | **0.058%** |
| RCP4.5 | 2030 | 0.066% | 0.003% | 0.02% | 1.00x | **0.091%** |
| RCP4.5 | 2050 | 0.082% | 0.003% | 0.04% | 1.05x | **0.134%** |
| RCP4.5 | 2060 | 0.110% | 0.003% | 0.04% | 1.05x | **0.163%** |
| RCP8.5 | 2030 | 0.072% | 0.003% | 0.02% | 1.05x | **0.101%** |
| RCP8.5 | 2050 | 0.110% | 0.003% | 0.06% | 1.10x | **0.185%** |
| RCP8.5 | 2060 | 0.220% | 0.003% | 0.16% | 1.15x | **0.441%** |

### 4.4 Financial Impact Translation

| Physical Risk | DSCR Impact | Credit Spread | Annual Revenue Loss |
|---------------|-------------|---------------|---------------------|
| 0.06% (baseline) | -0.001x | <1 bp | ~$1M |
| 0.15% (moderate) | -0.002x | ~1 bp | ~$2.5M |
| 0.44% (extreme) | -0.006x | ~3 bp | ~$7M |

**Note:** These are illustrative. Actual financial impacts depend on electricity prices, capacity payments, and contract structures.

---

## 5. CLIMADA Integration

### 5.1 What is CLIMADA?

**CLIMADA** (CLIMate ADAptation) is an open-source climate risk assessment platform developed by ETH Zürich.

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIMADA                                 │
│           Climate Adaptation Decision Support Tool              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   CAPABILITIES:                                                 │
│   ├── Global hazard data (wildfire, flood, cyclone, drought)   │
│   ├── Exposure modeling (assets, population, GDP)              │
│   ├── Impact calculation (damage functions)                    │
│   └── Risk metrics (AAL, return periods, VaR)                  │
│                                                                 │
│   DATA RESOLUTION:                                              │
│   ├── Global API:        ~4.5 km (150 arcsec)                  │
│   ├── Wildfire MODIS:    1 km                                  │
│   ├── Wildfire VIIRS:    375 m                                 │
│   └── Local studies:     100 m (custom)                        │
│                                                                 │
│   WEBSITE: https://climada.ethz.ch                              │
│   GITHUB:  https://github.com/CLIMADA-project/climada_python   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Installation

#### Step 1: Install CLIMADA (via conda)

```bash
# Create a new conda environment (recommended)
conda create -n climada_env python=3.11
conda activate climada_env

# Install CLIMADA core
conda install -c conda-forge climada

# Install CLIMADA petals (additional hazards)
pip install climada-petals
```

#### Step 2: Verify Installation

```python
# Test CLIMADA installation
from climada.util.api_client import Client
client = Client()
print(f"CLIMADA API connected. Datasets available: {len(client.list_dataset_infos())}")
```

#### Step 3: Check Available Data for Korea

```python
from climada.util.api_client import Client
client = Client()

# List all Korea datasets
datasets = client.list_dataset_infos()
korea_ds = [ds for ds in datasets if 'KOR' in ds.name]
print(f"Korea datasets available: {len(korea_ds)}")

# Output: Korea datasets available: 36
```

### 5.3 Available Korea Datasets in CLIMADA

| Dataset | Type | Resolution | Period |
|---------|------|------------|--------|
| `wildfire_KOR_150arcsec_historical_2001_2020` | Wildfire | 4.5 km | 2001-2020 |
| `river_flood_150arcsec_rcp85_KOR_2030_2050` | Flood | 4.5 km | 2030-2050 |
| `tropical_cyclone_10synth_tracks_150arcsec_KOR_1980_2020` | TC | 4.5 km | 1980-2020 |
| `LitPop_150arcsec_KOR` | Exposure | 4.5 km | Current |

### 5.4 Using CLIMADA in This Project

#### Basic Usage

```python
from src.climada.climada_integration import run_climada_analysis

# Run full CLIMADA analysis
result = run_climada_analysis()

# Access results
print(f"Wildfire outage: {result.wildfire.annual_outage_rate:.4%}")
print(f"Flood outage: {result.flood.annual_outage_rate:.4%}")
print(f"TC outage: {result.tropical_cyclone.annual_outage_rate:.4%}")
print(f"TOTAL: {result.total_climada_outage:.4%}")
```

#### Detailed API Usage

```python
from climada.util.api_client import Client
import numpy as np

# Initialize client
client = Client()

# 1. Get wildfire hazard for Korea
wildfire = client.get_hazard('wildfire', properties={'country_iso3alpha': 'KOR'})

# 2. Find data at Samcheok location
SAMCHEOK_LAT = 37.4404
SAMCHEOK_LON = 129.1671

# Find nearest grid point
lat_diff = wildfire.centroids.lat - SAMCHEOK_LAT
lon_diff = wildfire.centroids.lon - SAMCHEOK_LON
distances = np.sqrt(lat_diff**2 + lon_diff**2)
nearest_idx = np.argmin(distances)

# 3. Extract intensities at location
intensities = wildfire.intensity[:, nearest_idx].toarray().flatten()
events_at_location = intensities[intensities > 0]

print(f"Wildfire events at Samcheok: {len(events_at_location)}")
print(f"Max Fire Radiative Power: {events_at_location.max():.1f} MW")
```

### 5.5 CLIMADA vs Literature Results

| Hazard | CLIMADA | Literature | Ratio |
|--------|---------|------------|-------|
| Wildfire | 0.008% | 0.055% | 0.15x |
| River Flood | 0.000% | 0.003% | N/A |
| Tropical Cyclone | 0.021% | N/A | - |
| **TOTAL** | **0.029%** | **0.058%** | **0.50x** |

**Interpretation:**
- CLIMADA shows **lower** risk than literature
- River flood = 0% at Samcheok (plant at 10m elevation)
- CLIMADA adds tropical cyclone risk not in literature
- Both estimates are in same order of magnitude (<0.1%)

---

## 6. Running the Model

### 6.1 Quick Start

```bash
# 1. Run the demo (no CLIMADA required)
python -m src.climada.demo

# 2. Run CLIMADA analysis (requires internet)
python -m src.climada.climada_integration

# 3. Generate visualizations
python -m src.climada.visualize_physical_risk
python -m src.climada.visualize_climada_comparison
```

### 6.2 Python API

```python
# Simple usage - get risk for any year/scenario
from src.climada import calculate_physical_risk

# Baseline 2024
risk = calculate_physical_risk(year=2024, rcp="current")
print(f"Baseline CF reduction: {risk.cf_reduction:.4%}")  # 0.0580%

# Future projection
risk = calculate_physical_risk(year=2050, rcp="RCP8.5")
print(f"2050 RCP8.5 CF reduction: {risk.cf_reduction:.4%}")  # 0.1850%

# Access all components
print(f"  Wildfire: {risk.wildfire_rate:.4%}")
print(f"  Flood: {risk.flood_rate:.5%}")
print(f"  SLR derate: {risk.slr_derate:.4%}")
print(f"  Compound: {risk.compound_mult:.2f}x")
```

### 6.3 Output Files

| Output | Location | Description |
|--------|----------|-------------|
| Input visualization | `outputs/visualizations/physical_risk_inputs.png` | Baseline parameters chart |
| Output visualization | `outputs/visualizations/physical_risk_outputs.png` | Risk by scenario chart |
| CLIMADA comparison | `outputs/visualizations/climada_vs_literature.png` | Comparison chart |

---

## 7. Validation & Comparison

### 7.1 Internal Consistency Check

| Check | Status | Notes |
|-------|--------|-------|
| Baseline values reasonable | ✅ | <0.1% annual outage |
| Projections monotonic | ✅ | Risk increases with time |
| Compound multiplier bounded | ✅ | Max 1.25x |
| CF reduction formula correct | ✅ | Verified against manual calc |

### 7.2 External Validation

| Source | Wildfire | Flood | Notes |
|--------|----------|-------|-------|
| This model (Literature) | 0.055% | 0.003% | Korea-specific |
| CLIMADA | 0.008% | 0.000% | Satellite data |
| California (for comparison) | ~1% | ~1% | NOT applicable to Korea |

### 7.3 Why Previous Estimates Were Wrong

| Parameter | Previous | Corrected | Error Factor |
|-----------|----------|-----------|--------------|
| Wildfire baseline | 1.00% | 0.055% | **18x too high** |
| Flood baseline | 1.00% | 0.003% | **350x too high** |
| Compound multiplier | 2.0x | 1.25x | **60% too high** |

**Root causes:**
1. Used California wildfire data for Korea (20x fewer fires)
2. Confused flood return period with outage probability
3. Misattributed compound multiplier values to Zscheischler (2018)

---

## 8. References

### Primary Sources (All Verified)

| # | Citation | DOI | Application |
|---|----------|-----|-------------|
| 1 | Kim et al. (2025) *Natural Hazards* | [10.1007/s11069-025-07169-4](https://doi.org/10.1007/s11069-025-07169-4) | Korea wildfire statistics |
| 2 | Kim et al. (2024) *Water* | [10.3390/w16202987](https://doi.org/10.3390/w16202987) | Samcheok flood projections |
| 3 | Van Vliet et al. (2016) *Nature Climate Change* | [10.1038/nclimate2903](https://doi.org/10.1038/nclimate2903) | Power plant efficiency |
| 4 | IPCC AR6 WGI Ch9 (2021) | [ipcc.ch](https://www.ipcc.ch/report/ar6/wg1/) | Sea level rise projections |
| 5 | Zscheischler et al. (2018) *Nature Climate Change* | [10.1038/s41558-018-0156-3](https://doi.org/10.1038/s41558-018-0156-3) | Compound risk framework |

### CLIMADA References

| Resource | URL |
|----------|-----|
| CLIMADA Documentation | https://climada-python.readthedocs.io |
| CLIMADA GitHub | https://github.com/CLIMADA-project/climada_python |
| CLIMADA Data API | https://climada.ethz.ch/data-api/ |
| Aznar-Siguan & Bresch (2019) | [10.5194/gmd-12-3085-2019](https://doi.org/10.5194/gmd-12-3085-2019) |

---

## Appendix A: File Structure

```
risk_premium_2026/
├── src/climada/
│   ├── literature_parameters.py    # Core parameters (270 lines)
│   ├── hazards.py                  # CLIMADA data structures
│   ├── climada_integration.py      # CLIMADA API integration
│   ├── visualize_physical_risk.py  # Input/output charts
│   ├── visualize_climada_comparison.py  # Comparison charts
│   └── demo.py                     # Simple demo script
├── data/raw/
│   ├── physical.csv                # Pre-calculated scenarios
│   └── corrected_hazards.csv       # Detailed hazard data
├── outputs/visualizations/
│   ├── physical_risk_inputs.png
│   ├── physical_risk_outputs.png
│   └── climada_vs_literature.png
└── docs/
    ├── physical_risk.md            # This document
    ├── MODEL_OVERVIEW.md           # Model summary
    └── METHODOLOGY_EQUATIONS.md    # Detailed equations
```

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **CF** | Capacity Factor - ratio of actual output to maximum possible output |
| **CLIMADA** | CLIMate ADAptation - ETH Zürich climate risk platform |
| **DSCR** | Debt Service Coverage Ratio |
| **FRP** | Fire Radiative Power - satellite measure of fire intensity (MW) |
| **ISIMIP** | Inter-Sectoral Impact Model Intercomparison Project |
| **RCP** | Representative Concentration Pathway - climate scenario |
| **SLR** | Sea Level Rise |

---

*Document created: December 2024*
*For questions, contact the model developers.*

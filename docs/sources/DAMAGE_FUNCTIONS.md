# Damage Function Data Sources

This document provides full citations for all damage functions.

## Wildfire Damage Functions

### 1. FWI Linear Function (`fwi_linear`)

**Description**: Linear relationship between Fire Weather Index and outage rate.

**Parameters**:
- `base_rate`: 0.00001 (0.001% baseline)
- `slope`: 0.000002 (0.0002% per FWI unit)

**Sources**:
1. **van Wagner, C.E. (1987)**
   - Title: Development and Structure of the Canadian Forest Fire Weather Index System
   - Publication: Forestry Technical Report 35, Canadian Forestry Service
   - URL: https://cfs.nrcan.gc.ca/publications?id=19927

2. **Korea Forest Service (2023)**
   - Title: 산림청 산불통계 (Forest Fire Statistics)
   - Data: 2001-2023 fire occurrence records
   - URL: https://www.forest.go.kr/

### 2. FWI Exponential Function (`fwi_exponential`)

**Description**: Exponential relationship for high FWI scenarios.

**Parameters**:
- `a`: 0.000001
- `b`: 0.1 (exponential rate)
- `threshold`: 15 FWI

**Sources**:
1. **Syphard, A.D. et al. (2017)**
   - Title: The Role of Defensible Space for Residential Structure Protection
   - Journal: International Journal of Wildland Fire
   - DOI: 10.1071/WF16084

### 3. Korea Forest Service Function (`korea_forest_service`)

**Description**: Statistical model based on Korean fire data.

**Parameters**:
- `fires_per_year_baseline`: 0.75 events/year
- `outage_prob_per_fire`: 0.5%
- `outage_duration_hours`: 12 hours

**Sources**:
1. **Korea Forest Service (2023)** - Fire statistics
2. **KEPCO (2023)** - Power grid outage correlations
3. **World Weather Attribution (2020)**
   - Title: Attribution of increased wildfire risk
   - URL: https://www.worldweatherattribution.org/

---

## Flood Damage Functions

### 1. Depth-Damage HAZUS (`depth_damage_hazus`)

**Description**: Standard depth-damage curve from FEMA HAZUS.

**Parameters**:
- `threshold_m`: 0.5m
- `max_damage`: 80%
- `saturation_depth`: 3.0m

**Sources**:
1. **FEMA HAZUS-MH (2023)**
   - Title: HAZUS Flood Model Technical Manual
   - URL: https://www.fema.gov/flood-maps/tools-resources/flood-map-products/hazus

2. **Huizinga, J. et al. (2017)**
   - Title: Global flood depth-damage functions
   - Journal: JRC Technical Reports
   - DOI: 10.2760/16510

### 2. Depth-Duration Combined (`depth_duration_combined`)

**Description**: Incorporates flood duration for infrastructure.

**Parameters**:
- `depth_weight`: 0.6
- `duration_weight`: 0.4
- `critical_depth`: 0.5m
- `critical_duration`: 24 hours

**Sources**:
1. **Merz, B. et al. (2010)**
   - Title: Assessment of economic flood damage
   - Journal: Natural Hazards and Earth System Sciences
   - DOI: 10.5194/nhess-10-1697-2010

---

## Tropical Cyclone Damage Functions

### 1. Wind Power Law (`wind_power_law`)

**Description**: Power-law relationship between wind speed and damage.

**Formula**: Damage ∝ (v - v_threshold)³

**Parameters**:
- `threshold_ms`: 20 m/s
- `exponent`: 3.0
- `normalization_ms`: 60 m/s

**Sources**:
1. **Emanuel, K. (2011)**
   - Title: Global Warming Effects on U.S. Hurricane Damage
   - Journal: Weather, Climate, and Society
   - DOI: 10.1175/WCAS-D-11-00007.1

### 2. Holland Profile (`holland_profile`)

**Description**: Uses Holland wind profile for spatial damage.

**Parameters**:
- `B`: 1.5 (Holland B parameter)
- `rmax_km`: 50 km
- `vmax_threshold`: 25 m/s

**Sources**:
1. **Holland, G.J. (1980)**
   - Title: An Analytic Model of the Wind and Pressure Profiles in Hurricanes
   - Journal: Monthly Weather Review
   - DOI: 10.1175/1520-0493(1980)108<1212:AAMOTW>2.0.CO;2

### 3. Korea Typhoon (`korea_typhoon`)

**Description**: Statistical model for Korean peninsula.

**Parameters**:
- `events_per_year_baseline`: 0.15
- `outage_prob_per_event`: 1%
- `outage_duration_hours`: 24 hours

**Sources**:
1. **IBTrACS (2023)**
   - Title: International Best Track Archive for Climate Stewardship
   - URL: https://www.ncei.noaa.gov/products/international-best-track-archive

2. **Knutson, T. et al. (2020)**
   - Title: Tropical Cyclones and Climate Change Assessment
   - Journal: Bulletin of the American Meteorological Society
   - DOI: 10.1175/BAMS-D-18-0194.1

---

## Temperature Efficiency Functions

### Model Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Ambient derate | 0.10%/°C | Maulbetsch & DiFilippo (2006) |
| Cooling water derate | 0.15%/°C | Maulbetsch & DiFilippo (2006) |
| SST-to-air ratio | 0.50 | Literature estimate |
| Heat wave efficiency loss | 5% | Industry data |

### Sources

1. **Maulbetsch, J.S. & DiFilippo, M.N. (2006)**
   - Title: Cost and Value of Water Use at Combined-Cycle Power Plants
   - Publication: CEC-500-2006-034
   - URL: https://www.energy.ca.gov/

2. **KMA (2020)**
   - Title: Korea Climate Change Assessment Report
   - Publisher: Korea Meteorological Administration

3. **IPCC AR6 (2021)**
   - Chapter: Energy sector vulnerabilities

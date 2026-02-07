# Physical Risk Module - Final Structure

**Date:** December 29, 2024

---

## HONEST ASSESSMENT: CLIMADA API Usage

### What ACTUALLY Uses CLIMADA API

| File | Function | CLIMADA API Call | Purpose |
|------|----------|------------------|---------|
| `climada_integration.py:107` | `analyze_wildfire()` | `client.get_hazard('wildfire', ...)` | Historical wildfire data |
| `climada_integration.py:132` | `analyze_flood()` | `client.get_hazard('river_flood', ...)` | Historical flood data |
| `climada_integration.py:165` | `analyze_tropical_cyclone()` | `client.get_hazard('tropical_cyclone', ...)` | Historical TC data |

### What Uses HARDCODED Literature Values (NOT CLIMADA API)

| File | Function | What It Claims | What It Actually Does |
|------|----------|----------------|----------------------|
| `climada_climate_projections.py:172` | `_get_knutson_multiplier()` | CLIMADA TC projections | Hardcoded Knutson (2020) lookup table |
| `climada_climate_projections.py:316` | `_get_ksccr_flood_multiplier()` | CLIMADA flood projections | Hardcoded KSCCR (2024) values |
| `climada_climate_projections.py:394` | `_get_wwa_wildfire_multiplier()` | Wildfire projections | Hardcoded WWA (2025) values |
| `climada_climate_projections.py:409` | `_get_cmip6_slr()` | SLR projections | Hardcoded CMIP6 values |

### Summary

```
CLIMADA API Usage:
├── HISTORICAL DATA (Base Risk): REAL CLIMADA API
│   ├── Wildfire: client.get_hazard('wildfire')
│   ├── Flood: client.get_hazard('river_flood')
│   └── TC: client.get_hazard('tropical_cyclone')
│
└── FUTURE PROJECTIONS (Climate Factors): HARDCODED LITERATURE VALUES
    ├── TC: Knutson et al. (2020) lookup table
    ├── Flood: KSCCR (2024) lookup table
    ├── Wildfire: WWA (2025) lookup table
    └── SLR: CMIP6 (2021) lookup table
```

---

## Python Functions List

### src/climada/climada_integration.py

```python
# ACTUAL CLIMADA API CALLS
from climada.util.api_client import Client
from climada.hazard import Hazard

client = Client()

# Function: analyze_wildfire(client, lat, lon)
client.get_hazard('wildfire', properties={'country_iso3alpha': 'KOR'})

# Function: analyze_flood(client, lat, lon, scenario)
client.get_hazard('river_flood', properties={
    'country_iso3alpha': 'KOR',
    'climate_scenario': scenario,
    'year_range': '2030_2050'
})

# Function: analyze_tropical_cyclone(client, lat, lon)
client.get_hazard('tropical_cyclone', properties={
    'country_iso3alpha': 'KOR',
    'event_type': 'observed'
})

# Function: get_hazard_at_location(hazard, lat, lon)
# - Extracts intensity at nearest centroid
# - Returns (n_events, max_intensity, mean_intensity, distance_km, total_events)

# Function: run_climada_analysis()
# - Main entry point
# - Returns CLIMADASummary dataclass
```

### src/climada/climada_climate_projections.py

```python
# IMPORTS (but not fully utilized for projections)
from climada.hazard import TropCyclone, Hazard
from climada.hazard.tc_tracks import TCTracks
from climada.util.api_client import Client

# Function: get_tc_climate_projection(target_year, scenario, baseline_year, percentile)
# - Returns CLIMADAProjectionResult
# - ACTUALLY USES: _get_knutson_multiplier() (hardcoded lookup table)

# Function: _get_knutson_multiplier(year, scenario, percentile)
# - HARDCODED lookup table from Knutson et al. (2020)
# - NOT using apply_climate_scenario_knu()

# Function: get_flood_climate_projection(target_year, scenario)
# - TRIES to use client.get_hazard() but falls back to KSCCR values
# - Returns CLIMADAProjectionResult

# Function: _get_ksccr_flood_multiplier(year, scenario)
# - HARDCODED lookup table from KSCCR (2024)

# Function: get_all_climate_projections(target_year, scenario)
# - Combines all projections
# - Returns CLIMADAClimateFactors

# Function: _get_wwa_wildfire_multiplier(year, scenario)
# - HARDCODED lookup table from WWA (2025)

# Function: _get_cmip6_slr(year, scenario)
# - HARDCODED lookup table from CMIP6 (2021)
```

### src/climada/literature_parameters.py

```python
# VERIFIED LITERATURE VALUES
WILDFIRE_BASE_RATE = 0.00055  # Kim et al. (2025) DOI: 10.1007/s11069-025-07169-4
FLOOD_BASE_RATE = 0.00003    # Kang & Lee (2024) DOI: 10.3390/w16202987
SLR_DERATE_RATE = 0.0022     # Van Vliet (2016) DOI: 10.1038/nclimate2903

# Function: calculate_wildfire_outage_rate(year, scenario)
# Function: calculate_flood_outage_rate(year, scenario)
# Function: get_corrected_baseline_values()
```

### src/climada/hazards.py

```python
# Data classes for hazard representation
@dataclass
class CLIMADAHazardData:
    wildfire_outage_rate: float
    flood_outage_rate: float
    slr_capacity_derate: float
    compound_multiplier: float
    # ... methods

# Function: interpolate_hazard_by_year(hazards, year, scenario_prefix)
# Function: create_corrected_baseline(target_year, rcp)
```

### src/risk/physical.py

```python
# Main physical risk module
# Function: apply_physical(plant_params, scenario, climada_hazard)
# Function: apply_climada_physical_risk(plant_params, climada_hazard)
# Function: create_yearly_physical_adjustments(climada_hazards, scenario_prefix, start_year, end_year)
# Function: get_physical_risk_scenario(level)
# Function: get_physical_risk_from_climada(target_year, rcp)
```

---

## Final Directory Structure

```
risk_premium_2026/
├── src/
│   ├── climada/                              # Physical risk module
│   │   ├── __init__.py
│   │   ├── climada_integration.py            # REAL CLIMADA API (historical)
│   │   ├── climada_climate_projections.py    # Hardcoded projections
│   │   ├── literature_parameters.py          # Verified base rates
│   │   ├── hazards.py                        # Data structures
│   │   ├── visualize_climada_comparison.py   # Visualization
│   │   └── visualize_physical_risk.py        # Visualization
│   │
│   └── risk/
│       └── physical.py                       # Main physical risk logic
│
├── data/
│   ├── raw/
│   │   └── physical.csv                      # Input: verified physical risk scenarios
│   │
│   └── physical_risk_steps/                  # Documentation
│       ├── APPROACH_1_LITERATURE.csv         # Literature-only approach
│       ├── APPROACH_2_CLIMADA.csv            # CLIMADA-only approach
│       ├── COMPARISON_LITERATURE_vs_CLIMADA.csv
│       ├── FINAL_climate_factors.csv         # Final hybrid factors
│       ├── FINAL_physical_risk_output.csv    # Final output
│       ├── README.md                         # Comprehensive docs
│       └── SOURCE_VERIFICATION_FINAL.md      # Citation verification
│
└── archive/
    └── deprecated_physical_risk_2024/        # 15 archived files
        ├── README.md
        ├── step1_base_risk.csv
        ├── step2_climate_factor.csv
        ├── step2_climate_factor_VERIFIED.csv
        ├── step3_calculation.csv
        ├── step4_output.csv
        ├── step4_output_VERIFIED.csv
        ├── step5_climada_comparison.csv
        ├── climada_api_hazards.csv
        ├── corrected_hazards.csv
        ├── physical_risk_improved.csv
        ├── physical_risk_literature_backed.csv
        └── physical_risk_sensitivity.csv
```

---

## Verified Sources Summary

| Source | DOI | Used For |
|--------|-----|----------|
| Kim et al. (2025) | 10.1007/s11069-025-07169-4 | Wildfire base rate |
| Kang & Lee (2024) | 10.3390/w16202987 | Flood base rate |
| Van Vliet (2016) | 10.1038/nclimate2903 | SLR derate |
| WWA (2025) | worldweatherattribution.org | Wildfire climate factor |
| KSCCR (2024) | jccr.re.kr | Flood climate factor |
| CMIP6/Sung (2021) | 10.3390/atmos12010090 | SLR projections |
| Knutson et al. (2020) | 10.1175/BAMS-D-18-0194.1 | TC climate factor |

---

*Document created: December 29, 2024*

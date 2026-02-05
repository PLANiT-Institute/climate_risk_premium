# Climate Scenario Data Sources

This document provides full citations and methodology for climate scenario data.

## RCP Scenarios (CMIP5)

Representative Concentration Pathways from IPCC AR5.

### Data Sources

| Scenario | Description | Source |
|----------|-------------|--------|
| RCP2.6 | Strong mitigation (<2°C) | IPCC AR5 WG1 (2013) |
| RCP4.5 | Intermediate | IPCC AR5 WG1 (2013) |
| RCP6.0 | Higher emissions | IPCC AR5 WG1 (2013) |
| RCP8.5 | No mitigation | IPCC AR5 WG1 (2013) |

### Primary References

1. **IPCC AR5 WG1 (2013)**
   - Title: Climate Change 2013: The Physical Science Basis
   - URL: https://www.ipcc.ch/report/ar5/wg1/
   - Chapter 12: Long-term Climate Change: Projections, Commitments and Irreversibility

2. **CMIP5 Multi-Model Ensemble**
   - Data: https://esgf-node.llnl.gov/search/cmip5/
   - Models: 40+ GCMs from global modeling centers

3. **KMA Korea Downscaling**
   - Source: Korea Meteorological Administration
   - Report: 한반도 기후변화 전망보고서 (2020)
   - Resolution: 1km × 1km for Korean peninsula

### Temperature Projections

| Scenario | 2030 | 2050 | 2100 | Source |
|----------|------|------|------|--------|
| RCP2.6 (Global) | +1.3°C | +1.5°C | +1.6°C | IPCC AR5 |
| RCP4.5 (Global) | +1.4°C | +1.8°C | +2.4°C | IPCC AR5 |
| RCP8.5 (Global) | +1.5°C | +2.3°C | +4.3°C | IPCC AR5 |
| RCP8.5 (Korea) | +1.9°C | +3.0°C | +5.7°C | KMA 2020 |

### Sea Level Rise Projections

| Scenario | 2050 | 2100 | Source |
|----------|------|------|--------|
| RCP2.6 | 0.24m | 0.44m | IPCC AR5 WG1 |
| RCP4.5 | 0.28m | 0.53m | IPCC AR5 WG1 |
| RCP8.5 | 0.34m | 0.82m | IPCC AR5 WG1 |

---

## SSP Scenarios (CMIP6)

Shared Socioeconomic Pathways from IPCC AR6.

### Data Sources

| Scenario | Description | Radiative Forcing | Source |
|----------|-------------|-------------------|--------|
| SSP1-1.9 | Sustainability (1.5°C) | 1.9 W/m² | IPCC AR6 WG1 |
| SSP1-2.6 | Sustainability (2°C) | 2.6 W/m² | IPCC AR6 WG1 |
| SSP2-4.5 | Middle of Road | 4.5 W/m² | IPCC AR6 WG1 |
| SSP3-7.0 | Regional Rivalry | 7.0 W/m² | IPCC AR6 WG1 |
| SSP5-8.5 | Fossil Development | 8.5 W/m² | IPCC AR6 WG1 |

### Primary References

1. **IPCC AR6 WG1 (2021)**
   - Title: Climate Change 2021: The Physical Science Basis
   - URL: https://www.ipcc.ch/report/ar6/wg1/
   - Chapter 4: Future Global Climate: Scenario-based Projections

2. **CMIP6 Multi-Model Ensemble**
   - Data: https://esgf-node.llnl.gov/search/cmip6/
   - Models: 50+ GCMs from global modeling centers

3. **O'Neill et al. (2016)**
   - Title: The Scenario Model Intercomparison Project (ScenarioMIP)
   - Journal: Geoscientific Model Development
   - DOI: 10.5194/gmd-9-3461-2016

---

## CLIMADA Integration

### Hazard Data Sources

| Hazard | CLIMADA Module | Data Source |
|--------|----------------|-------------|
| Wildfire | climada.hazard.Wildfire | MODIS fire data |
| Tropical Cyclone | climada.hazard.TropCyclone | IBTrACS |
| River Flood | climada.hazard.RiverFlood | ISIMIP |
| Coastal Flood | climada.hazard.CoastalFlood | DIVA |

### API Query Parameters (Samcheok)

```python
LOCATION = {
    "lat": 37.4404,
    "lon": 129.1671,
    "name": "Samcheok Blue Power Plant"
}

QUERY_PARAMS = {
    "wildfire": {"years": "1980-2023", "radius_km": 50},
    "tropical_cyclone": {"years": "1980-2023", "basin": "WP"},
    "river_flood": {"scenario": "rcp85", "years": "2020-2100"},
}
```

### CLIMADA References

1. **Aznar-Siguan & Bresch (2019)**
   - Title: CLIMADA v1: a global weather and climate risk assessment platform
   - Journal: Geoscientific Model Development
   - DOI: 10.5194/gmd-12-3085-2019

2. **CLIMADA Documentation**
   - URL: https://climada-python.readthedocs.io/

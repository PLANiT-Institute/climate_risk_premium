# Physical Risk Model - Samcheok Blue Power Plant

## Overview

This model calculates **physical climate risk** for the Samcheok Blue Power Plant (2.1 GW coal-fired plant in Gangwon Province, South Korea).

**Key Finding:** Physical risk is modest (~0.06-0.44%). Transition risk (policy phase-out) is far more significant for coal plants.

---

## Quick Start

```python
from src.climada import calculate_physical_risk

# Calculate risk for any year/scenario
risk = calculate_physical_risk(year=2050, rcp="RCP8.5")
print(f"Total CF reduction: {risk.cf_reduction:.4%}")  # ~0.19%

# Access individual components
print(f"Wildfire: {risk.wildfire_rate:.4%}")
print(f"Flood: {risk.flood_rate:.5%}")
print(f"SLR derate: {risk.slr_derate:.4%}")
```

### Run Demo

```bash
python -m src.climada.demo
```

### Generate Visualizations

```bash
python -m src.climada.visualize_physical_risk
# Outputs saved to: outputs/visualizations/
```

---

## Baseline Parameters (2024)

| Hazard | Rate | Source |
|--------|------|--------|
| Wildfire | 0.055% | Kim et al. (2025) Natural Hazards |
| Flood | 0.003% | Kim et al. (2024) Water |
| SLR Derate | 0.22%/meter | Van Vliet et al. (2016) Nature Climate Change |

---

## Physical Risk by Scenario

| Scenario | Wildfire | Flood | SLR | Total CF Reduction |
|----------|----------|-------|-----|-------------------|
| Baseline 2024 | 0.055% | 0.003% | 0.00% | **0.058%** |
| RCP4.5 2050 | 0.082% | 0.003% | 0.04% | **0.134%** |
| RCP4.5 2060 | 0.110% | 0.003% | 0.04% | **0.163%** |
| RCP8.5 2050 | 0.110% | 0.003% | 0.06% | **0.185%** |
| RCP8.5 2060 | 0.220% | 0.003% | 0.16% | **0.441%** |

---

## Model Architecture

```
src/climada/
├── literature_parameters.py   # Core parameters and calculate_physical_risk()
├── hazards.py                 # CLIMADAHazardData structures
├── visualize_physical_risk.py # Visualization tools
├── demo.py                    # Simple demo script
└── __init__.py                # Module exports
```

### Key Functions

| Function | Description |
|----------|-------------|
| `calculate_physical_risk(year, rcp)` | Main entry point - returns PhysicalRiskResult |
| `create_corrected_baseline(year, rcp)` | Returns CLIMADAHazardData |
| `create_combined_visualization()` | Generates input/output charts |

---

## Data Files

| File | Description |
|------|-------------|
| `data/raw/physical.csv` | Clean physical risk data by scenario |
| `data/raw/corrected_hazards.csv` | Detailed hazard data with citations |

---

## Key Equations

### Wildfire Outage Rate
```
wildfire_rate = 0.00055 × climate_multiplier
```

### Total Physical Risk
```
total_outage = (wildfire + flood) × compound_multiplier
total_derate = slr_derate × compound_multiplier
cf_reduction = 1 - (1 - total_outage) × (1 - total_derate)
```

See `docs/METHODOLOGY_EQUATIONS.md` for complete equations.

---

## Verified Sources

| # | Source | DOI |
|---|--------|-----|
| 1 | Kim et al. (2025) Natural Hazards | 10.1007/s11069-025-07169-4 |
| 2 | Kim et al. (2024) Water | 10.3390/w16202987 |
| 3 | Van Vliet et al. (2016) Nature Climate Change | 10.1038/nclimate2903 |
| 4 | IPCC AR6 (2021) WGI Ch9 | ipcc.ch |
| 5 | World Weather Attribution (2025) | worldweatherattribution.org |

---

## Simplified in December 2024

Previous version had 763 lines of complex code. Simplified to ~270 lines.

**Changes:**
- Removed unused LiteratureSource/LiteratureParameter classes
- Consolidated projections into simple PROJECTIONS dict
- Single entry point: `calculate_physical_risk(year, rcp)`
- Added visualization tools

**Archived files:** `archive/deprecated_2024_correction/`

---

*Last updated: December 2024*

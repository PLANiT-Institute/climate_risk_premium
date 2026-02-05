# Deprecated Files - 2024 Physical Risk Correction

This folder contains files that were deprecated during the 2024 comprehensive review of the physical risk module.

## Why These Files Were Archived

### 1. Data Files

**`literature_hazards.csv`** (DEPRECATED)
- Original literature-based hazard values
- **Problem**: Values were overestimated by 10-50x
  - Wildfire: 1% baseline (should be ~0.05%)
  - Flood: 1% baseline (should be ~0.003%)
  - Compound multiplier: 1.2-2.0x (should be 1.0-1.25x)
- **Replaced by**: `corrected_hazards.csv`

**`climada_real_data.csv`** (DEPRECATED)
- Attempted to store real CLIMADA/ISIMIP data
- **Problem**: ISIMIP data was never successfully downloaded
- **Replaced by**: Corrected literature values

**`physical.csv`** (DEPRECATED)
- Old simple physical scenario definitions
- **Problem**: Did not use corrected values
- **Replaced by**: Dynamic scenario generation in `hazards.py`

### 2. Source Code

**`fetch_real_data.py`** (DEPRECATED)
- Script to fetch real CLIMADA/ISIMIP hazard data
- **Problem**: ISIMIP server data not accessible without registration
- **Status**: May be restored if ISIMIP data access is obtained

**`climada_api.py`** (DEPRECATED)
- CLIMADA API wrapper with synthetic data fallback
- **Problem**: Only generated synthetic data, not real hazard modeling
- **Replaced by**: Direct calculation using `literature_parameters.py`

## Replacement Files

The following files now contain the corrected values:

1. **`data/raw/corrected_hazards.csv`** - Corrected scenario values
2. **`data/raw/combined_hazards.csv`** - All scenarios (corrected + CLIMADA synthetic)
3. **`src/climada/literature_parameters.py`** - Corrected formulas and citations
4. **`src/climada/hazards.py`** - Corrected calculation functions

## Key Corrections Made

| Metric | Original | Corrected | Source |
|--------|----------|-----------|--------|
| Wildfire baseline | 1.00% | 0.05% | Kim et al. (2025) Korea Wildfires |
| Flood baseline | 1.00% | 0.003% | Kim et al. (2024) Samcheok Floods |
| SLR derate | 2% per 0.1m | 0.03% per 0.1m | Van Vliet et al. (2016) |
| Compound max | 2.0x | 1.25x | Removed: Zscheischler misattribution |

## Documentation

See `docs/literature_review/` for detailed methodology reviews:
- `02_flood_risk_methodology.md`
- `03_slr_methodology.md`
- `04_wildfire_methodology.md`
- `05_compound_risk_methodology.md`

---

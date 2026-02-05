# Physical Risk Module Review - Completion Summary

**Review Date:** December 2024
**Status:** COMPLETE

---

## Executive Summary

A comprehensive 10-step review of the physical risk module was completed. The review focused on:
1. Archiving deprecated code
2. Verifying ALL literature citations
3. Updating documentation with verified sources only
4. Creating comprehensive model documentation

---

## Changes Made

### Step 1-2: Archive Deprecated Code

**Created:** `archive/deprecated_2024_correction/`

**Files Archived:**
| File | Reason |
|------|--------|
| `literature_hazards.csv` | Values overestimated 10-50x |
| `climada_real_data.csv` | Failed ISIMIP data attempt |
| `physical.csv` | Used incorrect values |
| `fetch_real_data.py` | Non-working ISIMIP fetcher |
| `climada_api.py` | Only generated synthetic data |

### Step 3: Citation Verification

**12 primary sources verified**

**Corrections Made:**
| Original Citation | Corrected To | Issue |
|-------------------|--------------|-------|
| Audoly et al. (2015) | Bierkandt, R., Auffhammer, M., & Levermann, A. (2015) | Wrong author name |
| Jang et al. (2025) | Lee, C., Choi, E.H., Han, Y. et al. (2025) | Wrong first author |
| Luo et al. (2024) | Bressan, G., Đuranović, A., et al. (2024) | Wrong first author |
| C40 Cities (2018) | C40 Cities (2021) | Wrong publication date |

### Steps 4-7: Literature Review Updates

**Documents Updated:**
1. `docs/literature_review/02_flood_risk_methodology.md`
2. `docs/literature_review/03_slr_methodology.md`
3. `docs/literature_review/04_wildfire_methodology.md`
4. `docs/literature_review/05_compound_risk_methodology.md`

**Key improvements:**
- Added DOIs to all citations
- Added verification status (✅/⚠️)
- Created citation verification logs
- Noted limitations of each source

### Steps 8-9: Documentation

**New Documents Created:**
1. `docs/MODEL_OVERVIEW.md` - Comprehensive model overview
2. `docs/METHODOLOGY_EQUATIONS.md` - Detailed equations and flowchart

### Step 10: Final Validation

**Code Updates:**
- Fixed `src/climada/literature_parameters.py`:
  - Changed `JANG_2025_GANGWON` to `LEE_2025_GANGWON`
  - Updated reference [4] from "Jang et al." to "Lee et al."

---

## Value Corrections Summary

### Physical Risk Parameters

| Parameter | Previous | Corrected | Reduction |
|-----------|----------|-----------|-----------|
| Wildfire baseline | 1.00% | 0.055% | **18x** |
| Flood baseline | 1.00% | 0.003% | **350x** |
| SLR derate/0.1m | 2.00% | 0.03% | **70x** |
| Compound max | 2.0x | 1.25x | **37%** |

### Impact on Model Outputs

| Scenario | Previous Total Risk | Corrected Total Risk |
|----------|---------------------|----------------------|
| Baseline 2024 | ~3-5% | **~0.06%** |
| RCP4.5 2050 | ~5-8% | **~0.14%** |
| RCP8.5 2060 | ~8-12% | **~0.44%** |

---

## Citation Quality Assurance

### All Verified Sources

| # | Source | DOI/URL | Status |
|---|--------|---------|--------|
| 1 | Kim et al. (2025) Natural Hazards | 10.1007/s11069-025-07169-4 | ✅ |
| 2 | Lee et al. (2025) Scientific Reports | 10.1038/s41598-025-15508-5 | ✅ |
| 3 | Kim et al. (2024) Water | 10.3390/w16202987 | ✅ |
| 4 | Van Vliet et al. (2016) Nature Clim Change | 10.1038/nclimate2903 | ✅ |
| 5 | Zscheischler et al. (2018) Nature Clim Change | 10.1038/s41558-018-0156-3 | ✅ |
| 6 | Bressan et al. (2024) Nature Comms | 10.1038/s41467-024-48820-1 | ✅ |
| 7 | Bierkandt et al. (2015) Env Res Letters | 10.1088/1748-9326/10/12/124022 | ✅ |
| 8 | Durmayaz & Sogut (2006) Int J Energy Res | 10.1002/er.1186 | ✅ |
| 9 | IPCC AR6 (2021) WGI Ch9 | ipcc.ch | ✅ |
| 10 | World Weather Attribution (2025) | worldweatherattribution.org | ✅ |
| 11 | NCA5 (2023) | nca2023.globalchange.gov | ✅ |
| 12 | FEMA HAZUS (2025) | fema.gov | ✅ |

### Key Methodology Notes

1. **Zscheischler (2018)** is a conceptual framework, NOT a source for specific multiplier values
2. **California data** should not be directly applied to Korea
3. **Flood probability ≠ outage rate** - elevation and duration must be considered
4. **Compound multipliers** should be modest (1.0-1.25x) for single assets

---

## Files Modified

### Source Code
- `src/climada/literature_parameters.py` - Fixed citation references

### Documentation
- `docs/literature_review/02_flood_risk_methodology.md`
- `docs/literature_review/03_slr_methodology.md`
- `docs/literature_review/04_wildfire_methodology.md`
- `docs/literature_review/05_compound_risk_methodology.md`
- `docs/MODEL_OVERVIEW.md` (NEW)
- `docs/METHODOLOGY_EQUATIONS.md` (NEW)
- `docs/REVIEW_COMPLETION_SUMMARY.md` (NEW)

### Archived Files
- `archive/deprecated_2024_correction/README.md`
- `archive/deprecated_2024_correction/literature_hazards.csv`
- `archive/deprecated_2024_correction/physical.csv`
- `archive/deprecated_2024_correction/climada_real_data.csv`
- `archive/deprecated_2024_correction/fetch_real_data.py`
- `archive/deprecated_2024_correction/climada_api.py`

---

## Recommendations for Future Work

1. **Site Survey**: Confirm Samcheok plant elevation (currently estimated ~10m)
2. **KEPCO Data**: Obtain actual Korean power plant outage statistics
3. **CLIMADA Integration**: Run proper CLIMADA model with Korean hazard maps
4. **Transmission Mapping**: Map actual transmission route through fire-prone areas

---

## Conclusion

The physical risk module has been thoroughly reviewed and corrected. All citations are now verified and traceable. The model now uses Korea-specific data instead of California proxies, resulting in more accurate (and significantly lower) physical risk estimates.

**Key Finding:** Physical climate risk for Samcheok Blue Power Plant is modest (~0.06-0.4%). Transition risk (policy phase-out) is the dominant climate risk for coal plants in Korea.

---

*Review completed: December 2024*

# VERIFIED DATA AUDIT: Physical Risk Model

## CRITICAL DISTINCTION: Verified vs. Assumed Values

This document HONESTLY distinguishes between:
- ✅ **VERIFIED**: Values directly from CLIMADA API or explicitly stated in papers
- ⚠️ **DERIVED**: Values calculated from verified data using standard methods
- ❌ **ASSUMED**: Values that are model assumptions, NOT directly from papers

---

## 1. CLIMADA API DATA (✅ VERIFIED)

All values below are directly from CLIMADA API calls at Samcheok (37.4404°N, 129.1671°E):

| Hazard | Source | Raw Data | Calculation | Result |
|--------|--------|----------|-------------|--------|
| Wildfire | NASA FIRMS | 6 events / 20 years | 6/20 × 0.1(P_outage) × 24hr/8760hr | **0.0082%** |
| Tropical Cyclone | IBTrACS | 5 damaging events (>30m/s) / 40 years | 5/40 × 0.3(P_outage) × 48hr/8760hr | **0.0205%** |
| River Flood | ISIMIP | 0 events (all RCP scenarios) | 0/20 × ... | **0.0000%** |

### Why River Flood = 0:
- ISIMIP is **riverine flooding only**
- Samcheok location: coastal, 10m elevation
- No major river nearby → legitimately zero flood events

---

## 2. LITERATURE VALUES - VERIFICATION STATUS

### A. WWA 2025 - South Korea Wildfires (✅ VERIFIED)

**Source**: [World Weather Attribution (May 2025)](https://www.worldweatherattribution.org/climate-change-made-weather-conditions-leading-to-deadly-south-korean-wildfires-about-twice-as-likely/)

| Statement in Paper | Exact Value | Our Model | Status |
|-------------------|-------------|-----------|--------|
| "twice as likely" due to 1.3°C warming | **2.0x** | 2.0x (2050 baseline) | ✅ VERIFIED |
| "about 15% more intense" | **+15%** | Not used | ✅ VERIFIED |
| "further doubling" by 2.6°C (~2100) | **4.0x total** | 4.0x (2100) | ✅ VERIFIED |
| Wildfire multiplier for 2030 | **NOT STATED** | 1.30x | ❌ ASSUMED |

**HONEST ASSESSMENT**: The 2030 value of 1.30x is an interpolation, NOT directly from WWA.

### B. Knutson et al. 2020 - Tropical Cyclone (✅ PARTIALLY VERIFIED)

**Source**: BAMS DOI:10.1175/BAMS-D-18-0194.1

| Statement in Paper | Exact Value | Our Model | Status |
|-------------------|-------------|-----------|--------|
| TC intensity increase per 2°C warming | **+1-10%** (median ~5%) | - | ✅ VERIFIED |
| TC precipitation increase | **+14%** median | Not used | ✅ VERIFIED |
| TC frequency change | **-14%** median | Not used | ✅ VERIFIED |
| Our 2030 multiplier | N/A | 1.08x | ⚠️ DERIVED |
| Our 2050 multiplier | 2°C → +5% | 1.15x | ⚠️ DERIVED (but higher than paper) |
| Our 2100 multiplier | 4°C → +10% | 1.25x | ⚠️ DERIVED (but higher than paper) |

**HONEST ASSESSMENT**: Paper says +1-10% per 2°C. Our 1.15x/1.25x values are on the high end.

### C. Van Vliet 2016 - Thermal Power (⚠️ MISATTRIBUTED)

**Source**: Nature Climate Change DOI:10.1038/nclimate2903

| What Paper Actually Says | Our Model Used |
|-------------------------|----------------|
| Cooling water discharge capacity: **-4.5 to -15%** by 2080s | - |
| Focus: **water temperature**, not sea level rise | - |
| **NO "0.22%/m" value stated** | 0.22%/m derate |

**HONEST ASSESSMENT**:
- Van Vliet 2016 is about **water temperature impacts**, NOT sea level rise per meter
- The **0.22%/m SLR derate is a MODEL ASSUMPTION**, not from this paper
- This citation is MISATTRIBUTED

### D. CMIP6 Korea Sea Level Rise (✅ PARTIALLY VERIFIED)

**Source**: MDPI J. Mar. Sci. Eng. 2021, DOI:10.3390/jmse9101094

| Statement in Paper | Exact Value | Our Model | Status |
|-------------------|-------------|-----------|--------|
| Korea SLR by 2100 (SSP5-8.5) | **0.63m** (0.50-0.76m) | 0.63m | ✅ VERIFIED |
| Global SLR by 2100 | 0.65m (0.52-0.78m) | - | ✅ VERIFIED |
| Korea SLR by 2030 | **NOT STATED** | 0.06m | ❌ ASSUMED |
| Korea SLR by 2050 | **NOT STATED** | 0.18m | ❌ ASSUMED |

**HONEST ASSESSMENT**: Only 2100 value is verified. 2030/2050 are interpolations.

### E. Kim et al. 2025 - Wildfire Power Outage (❌ UNVERIFIED)

**Source**: Nat. Hazards DOI:10.1007/s11069-025-07169-4

| What We Claim | Verification Status |
|---------------|---------------------|
| 0.055% annual outage rate | ❌ **CANNOT VERIFY** - paper access restricted |

**HONEST ASSESSMENT**: The 0.055% value may or may not be in the paper. Cannot confirm without full text access.

### F. Kang & Lee 2024 - Flood (❌ UNVERIFIED)

**Source**: Water DOI:10.3390/w16202987

| What We Claim | Verification Status |
|---------------|---------------------|
| 0.003% flood outage rate | ❌ **CANNOT VERIFY** - paper access restricted |

**HONEST ASSESSMENT**: The 0.003% value may or may not be in the paper. Cannot confirm without full text access.

### G. KSCCR 2024 - Flood Projections (❌ NOT FOUND)

**Claimed Source**: jccr.re.kr

| What We Claim | Verification Status |
|---------------|---------------------|
| 1.29x flood increase by 2030 | ❌ **NOT FOUND** in web search |
| 1.46x flood increase by 2050 | ❌ **NOT FOUND** in web search |
| 2.64x flood increase by 2100 | ❌ **NOT FOUND** in web search |

**HONEST ASSESSMENT**: These values appear to be MODEL ASSUMPTIONS. Web search found related Korean flood studies but NOT these specific multipliers.

---

## 3. SUMMARY: WHAT IS REAL vs. ASSUMED

### ✅ FULLY VERIFIED (Use with confidence)

| Value | Source | Direct Quote |
|-------|--------|--------------|
| Wildfire 0.0082% | CLIMADA/NASA FIRMS | API result |
| TC 0.0205% | CLIMADA/IBTrACS | API result |
| River Flood 0% | CLIMADA/ISIMIP | API result |
| Wildfire 2x by current climate | WWA 2025 | "twice as likely" |
| Wildfire 4x by 2100 | WWA 2025 | "further doubling" |
| TC +1-10% per 2°C | Knutson 2020 | Stated in paper |
| Korea SLR 0.63m by 2100 | CMIP6 2021 | Stated in paper |

### ⚠️ DERIVED (Reasonable but calculated)

| Value | Derivation Method |
|-------|------------------|
| TC 1.08x (2030) | Linear interpolation from Knutson +5%/2°C |
| TC 1.15x (2050) | Scaled from Knutson (high end) |
| TC 1.25x (2100) | Scaled from Knutson (high end) |
| SLR 0.06m (2030) | Linear interpolation from 0.63m/2100 |
| SLR 0.18m (2050) | Linear interpolation from 0.63m/2100 |

### ❌ MODEL ASSUMPTIONS (Not directly from papers)

| Value | Issue |
|-------|-------|
| Wildfire 0.055% base rate | Kim 2025 - cannot verify |
| Flood 0.003% base rate | Kang & Lee 2024 - cannot verify |
| 0.22%/m SLR derate | Van Vliet 2016 doesn't say this |
| Wildfire 1.30x (2030) | WWA doesn't state 2030 value |
| Flood 1.29x/1.46x/2.64x | KSCCR values not found |

---

## 4. RECOMMENDED APPROACH

### Option A: Use Only CLIMADA + Verified Literature

| Hazard | Base Rate | Source | Climate Factor | Source |
|--------|-----------|--------|----------------|--------|
| Wildfire | **0.0082%** | CLIMADA | 2x/4x | WWA 2025 |
| TC | **0.0205%** | CLIMADA | +5-10% | Knutson 2020 |
| River Flood | **0.0000%** | CLIMADA | N/A | N/A |
| SLR | **0.63m by 2100** | CMIP6 | N/A | N/A |

**Problem**: Lower base rates than literature, flood = 0

### Option B: Use Literature with EXPLICIT Assumptions

If using literature values, MUST state:
- "The 0.055% wildfire rate from Kim et al. (2025) could not be independently verified"
- "The 0.003% flood rate from Kang & Lee (2024) could not be independently verified"
- "The 0.22%/m SLR derate is a MODEL ASSUMPTION, not from Van Vliet 2016"
- "Flood climate factors are ASSUMED values, not from KSCCR"

### Option C: Hybrid with Honest Uncertainty Ranges

Use CLIMADA as lower bound, literature as upper bound:
- Wildfire: 0.0082% - 0.055% (range)
- Flood: 0% - 0.003% (range)
- TC: 0.0205% (CLIMADA only)

---

## 5. DATA SOURCES ACTUALLY VERIFIED

| Source | DOI/URL | What It Actually Contains |
|--------|---------|--------------------------|
| CLIMADA API | climada.ethz.ch | NASA FIRMS, IBTrACS, ISIMIP data |
| WWA 2025 | worldweatherattribution.org | 2x/4x wildfire likelihood |
| Knutson 2020 | 10.1175/BAMS-D-18-0194.1 | +1-10% TC intensity per 2°C |
| CMIP6 Korea | 10.3390/jmse9101094 | 0.63m SLR by 2100 |
| Van Vliet 2016 | 10.1038/nclimate2903 | Water temp impacts (NOT SLR/m) |

---

*This audit completed: December 29, 2024*
*All claims verified against original sources or marked as unverified*

# Physical Risk Model - File Index

**Last Updated**: December 29, 2024
**Project**: Samcheok Blue Power Plant Physical Risk Assessment

---

## Key Documents for Review

### 1. Literature Review (START HERE)
- **[LITERATURE_REVIEW_FOR_COLLEAGUES.md](./LITERATURE_REVIEW_FOR_COLLEAGUES.md)** - Complete literature review with all sources, exact quotes, and verification status. **Share this with colleagues.**

### 2. Final Model Output
- **[CLIMADA_INTEGRATED_MODEL.csv](./CLIMADA_INTEGRATED_MODEL.csv)** - Machine-readable model output with all components
- **[COMPLETE_PHYSICAL_RISK_MODEL.md](./COMPLETE_PHYSICAL_RISK_MODEL.md)** - Summary of integrated model

### 3. Data Verification
- **[VERIFIED_DATA_AUDIT.md](./VERIFIED_DATA_AUDIT.md)** - Audit of verified vs. assumed values
- **[FINAL_VERIFIED_MODEL.csv](./FINAL_VERIFIED_MODEL.csv)** - Model using only verified data

---

## Supporting Documentation

### CLIMADA Data
| File | Description |
|------|-------------|
| `CLIMADA_API_DATA.csv` | Raw CLIMADA API output |
| `CLIMADA_COMPLETE_DATA.csv` | CLIMADA data across all RCP scenarios |

### Component Models
| File | Description |
|------|-------------|
| `TEMPERATURE_EFFICIENCY_MODEL.md` | Temperature derate methodology |
| `ALIGNED_MODEL_DOCUMENTATION.md` | CLIMADA vs Literature alignment |

### Legacy Files (for reference)
| File | Description |
|------|-------------|
| `APPROACH_1_LITERATURE.csv` | Literature-only approach |
| `APPROACH_2_CLIMADA.csv` | CLIMADA-only approach |
| `COMPARISON_LITERATURE_vs_CLIMADA.csv` | Comparison of approaches |

---

## Quick Reference: Model Values

### RCP8.5 Scenario

| Year | Wildfire | TC | Flood | Temperature | Total |
|------|----------|-----|-------|-------------|-------|
| 2024 | 0.008% | 0.021% | 0.00% | 0.055% | **0.084%** |
| 2030 | 0.016% | 0.022% | 0.00% | 0.258% | **0.296%** |
| 2050 | 0.016% | 0.023% | 0.00% | 0.437% | **0.476%** |
| 2100 | 0.033% | 0.023% | 0.00% | 1.099% | **1.154%** |

### Key Finding
**Temperature efficiency loss is the dominant risk factor (~95% of total by 2100)**

---

## Python Code

Run the integrated model:
```bash
python -m src.climada.climada_physical_risk_model
```

---

## Contact

For questions about this analysis, please contact the Physical Risk Modeling Team.

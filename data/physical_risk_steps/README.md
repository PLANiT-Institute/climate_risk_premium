<<<<<<< HEAD
# Physical Risk Model
=======
# Physical Risk Model v2.0
>>>>>>> 7b1507166a09149c835e7a055a114db44cb2809e

## Overview

CSV-based physical risk model for Samcheok Blue Power Plant.

**All inputs are stored in CSV files for full traceability.**

---

## Directory Structure

```
physical_risk_steps/
├── README.md                    # This file
├── PHYSICAL_RISK_MODEL.md       # Full documentation with sources
│
├── input/                       # ALL MODEL INPUTS
│   ├── climada_data.csv         # CLIMADA API outputs
│   ├── literature_data.csv      # Verified literature values
│   └── model_assumptions.csv    # Modeling assumptions
│
├── output/                      # MODEL OUTPUTS
│   └── physical_risk_output.csv # Calculated results
│
<<<<<<< HEAD
└── archive/                     # Previous versions
=======
└── archive_2024_12_29/          # Previous versions
>>>>>>> 7b1507166a09149c835e7a055a114db44cb2809e
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         INPUT FILES                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  climada_data.csv              literature_data.csv               │
│  ┌─────────────────┐          ┌─────────────────────┐           │
│  │ Wildfire: 6 ev  │          │ Temp +1.75°C (2050) │           │
│  │ TC: 5 damaging  │          │ Temp +4.73°C (2100) │           │
│  │ Flood: 0 events │          │ Wildfire 2x/4x WWA  │           │
│  └────────┬────────┘          │ TC +5-10% Knutson   │           │
│           │                   │ SLR 0.63m CMIP6     │           │
│           │                   │ Derate 0.08%/°C     │           │
│           │                   └──────────┬──────────┘           │
│           │                              │                       │
│           │    model_assumptions.csv     │                       │
│           │    ┌─────────────────────┐   │                       │
│           │    │ P(outage|fire)=0.10 │   │                       │
│           │    │ P(outage|TC)=0.30   │   │                       │
│           │    │ Duration: 24h, 48h  │   │                       │
│           │    └──────────┬──────────┘   │                       │
│           │               │              │                       │
└───────────┴───────────────┴──────────────┴───────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CALCULATION                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Base Rate = (CLIMADA events / years) × P(outage) × (dur/8760)  │
│                                                                  │
│  Projected = Base Rate × Climate Factor (from literature)        │
│                                                                  │
│  Temp Derate = ΔT × (ambient + SST_ratio × cooling) derate      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         OUTPUT                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  output/physical_risk_output.csv                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Year  Wildfire    TC      Flood    Temp     SLR    TOTAL   │ │
│  │ 2024  0.0082%  0.0205%  0.0000%  0.0548%  0.00m  0.0836%  │ │
│  │ 2030  0.0164%  0.0216%  0.0000%  0.2519%  0.06m  0.2899%  │ │
│  │ 2050  0.0164%  0.0226%  0.0000%  0.4275%  0.18m  0.4665%  │ │
│  │ 2100  0.0329%  0.0226%  0.0000%  1.0724%  0.63m  1.1278%  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Input Files

### 1. climada_data.csv

<<<<<<< HEAD
CLIMADA API outputs.
=======
CLIMADA API outputs from December 29, 2024 query.
>>>>>>> 7b1507166a09149c835e7a055a114db44cb2809e

| Column | Description |
|--------|-------------|
| hazard | Hazard type |
| database | Data source |
| events_at_location | Events within 2km of plant |
| years_covered | Data period length |
| status | API_OUTPUT |

### 2. literature_data.csv

Verified values from peer-reviewed sources.

| Column | Description |
|--------|-------------|
| category | TEMPERATURE, EFFICIENCY, WILDFIRE, TC, SLR, HEATWAVE |
| parameter | Specific parameter name |
| value | Numerical value |
| source | Citation |
| doi | DOI if available |
| status | VERIFIED, DERIVED, or ASSUMPTION |
| exact_quote | Quote from paper if available |

### 3. model_assumptions.csv

Values without direct literature support.

| Column | Description |
|--------|-------------|
| parameter | Parameter name |
| value | Assumed value |
| rationale | Justification |
| status | Always ASSUMPTION |

---

## Run the Model

```bash
python -m src.climada.climada_physical_risk_model
```

---

## Key Results (RCP8.5)

| Year | Total Physical Risk | Acute Hazards | Temperature Derate |
|------|---------------------|---------------|-------------------|
| 2024 | 0.08% | 0.03% | 0.05% |
| 2030 | 0.29% | 0.04% | 0.25% |
| 2050 | 0.47% | 0.04% | 0.43% |
| 2100 | 1.13% | 0.06% | 1.07% |

**Key Finding**: Temperature efficiency loss dominates (~95% of total by 2100).

---

## Documentation

Full methodology and sources: [PHYSICAL_RISK_MODEL.md](./PHYSICAL_RISK_MODEL.md)
<<<<<<< HEAD
=======

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-12-29 | Initial release |
| 1.1 | 2024-12-29 | Peer review revisions |
| 2.0 | 2024-12-29 | CSV-based pipeline |
>>>>>>> 7b1507166a09149c835e7a055a114db44cb2809e

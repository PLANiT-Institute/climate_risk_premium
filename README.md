# Climate Risk Premium Model: Quantifying Stranded Asset Risk for Samcheok Blue Power

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Executive Summary

This repository contains a comprehensive financial modeling framework for quantifying the **Climate Risk Premium (CRP)** of coal-fired power infrastructure. The model integrates three independent data sources:

1. **Korea Power Supply Plan** (MOTIE) - Official government coal dispatch trajectories
2. **CLIMADA Physical Hazards** (ETH Zurich) - Spatially-explicit wildfire, flood, and sea level rise data
3. **KIS Credit Rating Methodology** - Korean credit rating agency quantitative grid

**Key Finding**: Government policy — not physical climate change — is the primary driver of coal asset stranding in Korea. Under the enhanced 11th Basic Plan (2040 coal phase-out), the Samcheok plant's NPV drops from +$3,098M to -$2,999M and its credit rating collapses from AA to CC, generating a Climate Risk Premium of 1,020 basis points. Physical risks alone have negligible impact (~$3-5M NPV reduction), confirming that transition risk is the dominant stranding channel.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Key Results](#key-results)
- [Model Architecture](#model-architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Data Sources](#data-sources)
- [Methodology](#methodology)
- [Project Structure](#project-structure)
- [Academic Paper](#academic-paper)
- [License](#license)

---

## Project Overview

### The Samcheok Paradox

South Korea faces a critical dilemma: while committing to carbon neutrality by 2050, the country recently commissioned the 2.1 GW Samcheok Blue Power plant in 2024—likely the last coal-fired power plant in its history. This contradiction presents a unique case study for analyzing "stranded asset" risk in real-time.

### Research Questions

1. How do government energy policies translate into plant-level financial impacts?
2. How do physical climate hazards (wildfire, flood, sea level rise) affect project economics?
3. How do climate risks trigger credit rating downgrades and financing cost increases?
4. What is the total "Climate Risk Premium" investors should demand?

### Core Innovation: The Credit Rating Death Spiral

The model demonstrates a non-linear feedback loop:
1. Climate risks reduce revenue and cash flows
2. Lower cash flows reduce Debt Service Coverage Ratio (DSCR)
3. Lower DSCR triggers credit rating downgrades
4. Lower ratings increase cost of debt (spread widens)
5. Higher interest expense further reduces cash flows
6. **Loop repeats until technical default**

---

## Key Results

### Scenario Analysis Summary

| Scenario | NPV ($M) | IRR | Min DSCR | Rating | CRP (bps) |
|----------|----------|------|----------|--------|-----------|
| Baseline | 3,098 | 11.99% | 1.86× | AA | -50 |
| Moderate Transition | 2,034 | 10.55% | 1.65× | A | 0 |
| Aggressive Transition | -75 | 7.04% | 1.33× | A | 0 |
| Moderate Physical | 3,095 | 11.99% | 1.85× | AA | -50 |
| High Physical | 3,093 | 11.99% | 1.85× | AA | -50 |
| Combined Moderate | 2,031 | 10.55% | 1.65× | A | 0 |
| Combined Aggressive | -78 | 7.03% | 1.33× | A | 0 |
| Low Demand | 494 | 8.21% | 1.17× | BBB | 85 |
| Severe Drought | 3,099 | 11.99% | 1.86× | AA | -50 |
| Enhanced 11th Plan | -2,999 | -8.09% | 0.07× | CC | 1,020 |
| Enhanced Combined | -3,000 | -8.09% | 0.07× | CC | 1,020 |

### Key Insights

1. **Policy Dominates**: The Enhanced 11th Plan (2040 coal phase-out) destroys $6.1B in value (NPV swing from +$3,098M to -$2,999M), while physical risks have negligible financial impact (~$3-5M NPV reduction)
2. **Credit Rating Collapse**: Baseline AA rating drops to CC under the 2040 phase-out scenario, with DSCR collapsing from 1.86x to 0.07x
3. **Climate Risk Premium**: 1,020 bps under the most severe policy scenario, reflecting a 10.2% additional cost of capital
4. **Physical Risk Is Minimal for Korea**: Korea-specific wildfire (0.055%) and flood (0.003%) risks are orders of magnitude smaller than transition risk, consistent with Korea's temperate geography

---

## Model Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL RISK INPUTS                         │
├─────────────────────────────┬───────────────────────────────────┤
│   Physical Hazards          │   Transition Policy               │
│   (CLIMADA)                 │   (Korea Power Plan)              │
│   • Wildfire FWI            │   • Dispatch caps                 │
│   • Flood probability       │   • Carbon price                  │
│   • Sea level rise          │   • Phase-out schedule            │
└─────────────┬───────────────┴───────────────┬───────────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OPERATIONAL IMPACT                           │
│   • Generation volume (MWh) reduction                          │
│   • Carbon costs ($)                                           │
│   • Forced outages (%)                                         │
│   • Capacity derating (%)                                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FINANCIAL MODEL                              │
│   Revenue → EBITDA → CFADS → DSCR                              │
│   Tax (24%), Depreciation, Debt Service                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
│  CREDIT RATING  │ │  COST OF    │ │      NPV        │
│  (KIS Method)   │◄┤    DEBT     │ │   (Project      │
│  AAA → B        │ │   (Spread)  │ │    Value)       │
└────────┬────────┘ └──────┬──────┘ └─────────────────┘
         │                 │
         │    DEATH        │
         └────SPIRAL───────┘
              LOOP
```

---

## Installation

### Prerequisites

- Python 3.10+
- pip or conda

### Quick Start

```bash
# Clone the repository
git clone https://github.com/jinsu-park/climate_risk_premium.git
cd climate_risk_premium

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the analysis (regenerates all scenario results)
python scripts/regenerate_dashboard_data.py

# Launch the Next.js dashboard
cd crp-dashboard && npm run dev
```

### Dependencies

Core dependencies include:
- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.24.0` - Numerical computing
- `streamlit>=1.28.0` - Interactive dashboard
- `matplotlib>=3.7.0` - Visualization
- `seaborn>=0.12.0` - Statistical graphics

---

## Usage

### Running the Full Analysis

```bash
python scripts/regenerate_dashboard_data.py
```

This will:
1. Load plant parameters from `data/raw/plant.csv`
2. Load climate scenarios from `data/raw/physical.csv` and `data/raw/literature_hazards.csv`
3. Run financial model for 11 scenario combinations (including enhanced 11th Plan)
4. Calculate credit ratings using KIS methodology
5. Output results to `data/processed/` (CSV) and `crp-dashboard/src/data/` (JSON)

### Interactive Dashboard

```bash
cd crp-dashboard && npm run dev
```

The Next.js dashboard provides:
- **Overview**: Key metrics and model summary
- **Scenario Analysis**: NPV comparison across scenarios
- **Credit Rating**: Rating migration visualization
- **Cash Flow**: Detailed waterfall analysis

### Generating Publication Figures

```bash
python -m src.analysis.generate_paper_figures
```

Produces publication-ready figures in `data/processed/figures/`:
- `fig_npv_waterfall.png` - NPV comparison
- `fig_cashflow_comparison.png` - Cash flow decomposition
- `fig_rating_migration.png` - Credit rating paths
- `fig_sensitivity_heatmap.png` - Sensitivity analysis

### Authoritative Results

The `results/` directory contains the authoritative model output. Files in `data/processed/`
are regenerated by the pipeline and may reflect interim runs.

---

## Data Sources

### 1. Korea Power Supply Plan (MOTIE)

**Source**: Ministry of Trade, Industry and Energy, 10th Basic Plan (2023-2036)

| Year | Coal TWh | Total TWh | Coal Share | Implied CF |
|------|----------|-----------|------------|------------|
| 2024 | 195 | 600 | 32.5% | 65% |
| 2030 | 130 | 675 | 19.3% | 45% (NDC) |
| 2036 | 95 | 735 | 12.9% | 32% |
| 2050 | 15 | 860 | 1.7% | 4% (Net-Zero) |

### 2. CLIMADA Physical Hazards

**Source**: ETH Zurich CLIMADA platform

| Hazard | Baseline | RCP 4.5 (2050) | RCP 8.5 (2050) |
|--------|----------|----------------|----------------|
| Wildfire (FWI) | 20 | 30 | 42 |
| Flood (outage rate) | 0.2% | 0.3% | 0.35% |
| Sea Level Rise | 0m | +0.28m | +0.45m |

### 3. KIS Credit Rating Methodology

**Source**: Korea Investors Service, IPP Sector Rating Grid

| Metric | AAA | AA | A | BBB | BB | B |
|--------|-----|----|----|-----|----|----|
| Capacity (MW) | ≥2,000 | ≥800 | ≥400 | ≥100 | ≥20 | <20 |
| EBITDA/Interest | ≥12× | ≥6× | ≥4× | ≥2× | ≥1× | <1× |
| Net Debt/EBITDA | ≤1× | ≤4× | ≤7× | ≤10× | ≤12× | >12× |
| **Spread (bps)** | 50 | 100 | 150 | 250 | 400 | 600 |

---

## Methodology

### NPV Calculation

```
NPV = Σ(t=1 to T) [CF_t / (1 + WACC)^t] - I_0

where:
  CF_t = (EBIT × (1 - τ)) + Depreciation - Capex - ΔWC
  τ = 24% (Korean corporate tax rate)
  WACC = (E/V × r_e) + (D/V × r_d × (1 - τ))
```

### Climate Risk Premium

```
CRP = Spread(R_risk) - Spread(R_baseline) + Expected_Loss_Spread

where:
  R = f(DSCR, EBITDA/Interest, Net Debt/EBITDA, ...)
  Expected_Loss = P(default) × LGD
```

### Credit Rating Death Spiral

```
Climate Risks → ↓Revenue → ↓EBITDA → ↓DSCR → ↓Rating
                                              ↓
                        ←←←← ↑Spread ←←←←←←←←
```

---

## Project Structure

```
climate_risk_premium/
├── src/
│   ├── app/                    # Streamlit dashboard (legacy)
│   │   └── streamlit_app.py
│   ├── analysis/              # Figure generation & sensitivity
│   │   ├── generate_paper_figures.py
│   │   └── physical_risk_sensitivity.py
│   ├── climada/               # Physical risk module
│   │   ├── hazards.py         # CLIMADA hazard data loader
│   │   └── literature_parameters.py  # Verified risk parameters
│   ├── financials/            # Cash flow model
│   │   ├── cashflow.py        # Time-series cash flow engine
│   │   └── metrics.py         # NPV, IRR, DSCR calculations
│   ├── models/                # Class-based risk models (new API)
│   │   ├── physical/          # Physical hazard models
│   │   ├── transition/        # Transition risk models
│   │   └── financial/         # Financial impact models
│   ├── pipeline/              # Analysis orchestrator
│   │   └── runner.py          # CRPModelRunner
│   ├── planit/                # PLANiT integration module
│   ├── reporting/             # Visualization helpers
│   │   └── plots.py
│   ├── risk/                  # Risk assessment modules
│   │   ├── credit_rating.py   # KIS credit rating methodology
│   │   ├── transition.py      # Policy/transition risk
│   │   ├── physical.py        # Physical risk integration
│   │   ├── attribution.py     # Shapley-value decomposition
│   │   └── financing.py       # Financing impact calculations
│   └── scenarios/             # Scenario definitions
│       ├── base.py            # Scenario dataclasses
│       └── korea_power_plan.py  # Korea Power Plan loader
├── data/
│   ├── raw/                   # Input data (CSV)
│   │   ├── plant.csv          # Plant parameters (2.1 GW Samcheok)
│   │   ├── physical.csv       # Literature-verified physical scenarios
│   │   ├── literature_hazards.csv  # CLIMADA hazard data
│   │   ├── policy.csv         # Transition policy scenarios
│   │   ├── financing.csv      # Financial terms
│   │   └── korea_power_plan.csv  # Power Supply Plan dispatch
│   └── processed/             # Generated output
│       ├── scenario_comparison.csv
│       ├── credit_ratings.csv
│       ├── cashflow_*.csv     # Per-scenario cash flows
│       └── figures/           # Generated figures
├── results/                   # Authoritative model output
│   ├── scenario_comparison.csv
│   ├── credit_ratings.csv
│   ├── model_results.csv
│   └── figures/
├── crp-dashboard/             # Next.js interactive dashboard
├── scripts/                   # Utility scripts
│   ├── regenerate_dashboard_data.py
│   └── reproduce_results.py   # Canonical result reproduction
├── docs/                      # Documentation
│   ├── METHODOLOGY_EQUATIONS.md  # Physical risk equations
│   ├── VERIFIED_LITERATURE.md    # Verified citations & derivations
│   ├── ARCHITECTURE.md           # System architecture
│   └── MODEL_OVERVIEW.md         # Quick-start guide
├── tests/                     # Test suite
├── notebooks/                 # Jupyter notebooks
└── requirements.txt           # Python dependencies
```

---

## Academic Paper

Key sections of the accompanying research paper:

1. **Introduction**: The Samcheok Paradox and research gap
2. **Theoretical Framework**: Integrated cash flow model and credit rating death spiral
3. **Methodology & Data**: Korea Power Plan, CLIMADA, and KIS methodology
4. **Results**: Scenario analysis and financial impacts
5. **Discussion**: Policy implications and just transition finance
6. **Appendices**: Detailed parameters and data tables

### Citation

If you use this model in your research, please cite:

```bibtex
@article{park2026climate,
  title={Quantifying the Climate Risk Premium: A Case Study of the Samcheok Blue Power Plant in South Korea},
  author={Park, Jinsu},
  journal={Energy Policy},
  year={2026},
  institution={PLANiT Institute},
  publisher={Elsevier}
}
```

---

## Key Findings for Policymakers

1. **Stranded Asset Risk is Real**: The Enhanced 11th Basic Plan (2040 coal phase-out) creates a $6.1 billion NPV swing for the Samcheok plant, from +$3,098M to -$2,999M.

2. **Early Retirement is Optimal**: Under the 2040 phase-out, DSCR collapses to 0.07x by mid-life. Negotiated early retirement dominates market-driven collapse.

3. **Just Transition Finance Needed**: The 1,020 bps Climate Risk Premium under the most severe scenario renders new coal unfinanceable. Structured transition mechanisms (early retirement contracts, transition bonds) are essential.

4. **Rating Agencies Must Adapt**: The model's baseline AA rating does not yet reflect forward-looking policy risk. Under the Enhanced 11th Plan, the rating collapses to CC — a 10-notch downgrade that current static methodologies fail to capture.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **PLANiT Institute** for research support
- **Solutions for Our Climate (SFOC)** for Korean coal policy data
- **ETH Zurich CLIMADA Team** for open-source hazard modeling tools
- **Korea Investors Service (KIS)** for credit rating methodology

---

## Contact

For questions or collaboration inquiries:
- **Author**: Jinsu Park
- **Institution**: PLANiT Institute, Seoul, South Korea
- **Email**: jinsu@planit.institute

---

*Last Updated: February 2026*

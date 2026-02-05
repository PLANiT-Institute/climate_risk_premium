# Climate Risk Premium Model: Quantifying Stranded Asset Risk for Samcheok Blue Power

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Executive Summary

This repository contains a comprehensive financial modeling framework for quantifying the **Climate Risk Premium (CRP)** of coal-fired power infrastructure. The model integrates three independent data sources:

1. **Korea Power Supply Plan** (MOTIE) - Official government coal dispatch trajectories
2. **CLIMADA Physical Hazards** (ETH Zurich) - Spatially-explicit wildfire, flood, and sea level rise data
3. **KIS Credit Rating Methodology** - Korean credit rating agency quantitative grid

**Key Finding**: Government policy—not physical climate change—is the primary driver of coal asset stranding in Korea. Transition scenarios reduce NPV by 251-375%, while physical risks reduce NPV by 33-59%. Combined risks trigger a "credit rating death spiral" with Climate Risk Premiums reaching 5,854 basis points.

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

| Scenario | NPV ($M) | Δ NPV | Min DSCR | Rating | CRP (bps) |
|----------|----------|-------|----------|--------|-----------|
| Baseline | 2,898 | — | 1.81× | BBB | — |
| Moderate Transition | -4,381 | -251% | -1.39× | B | 3,880 |
| Aggressive Transition | -7,964 | -375% | -4.37× | B | 5,635 |
| Moderate Physical | 1,928 | -33% | 1.58× | BBB | 475 |
| High Physical | 1,189 | -59% | 1.42× | BBB | 837 |
| Combined Aggressive | -8,411 | -390% | -4.32× | B | 5,854 |

### Key Insights

1. **Policy Dominates**: Transition risk is 4-6× larger than physical risk
2. **Investment Grade Lost**: All transition scenarios trigger BBB → B downgrade
3. **Death Spiral Activated**: DSCR falls from 1.81× to negative values
4. **Unfinanceable**: At 5,854 bps CRP, debt service exceeds total revenue

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
git clone https://github.com/your-username/risk_premium_2026.git
cd risk_premium_2026

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the analysis
python run_full_analysis.py

# Launch the dashboard
python run_app.py
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
python run_full_analysis.py
```

This will:
1. Load plant parameters from `data/raw/plant.csv`
2. Load climate scenarios from `data/raw/physical.csv` and `data/raw/policy.csv`
3. Run financial model for all scenario combinations
4. Calculate credit ratings using KIS methodology
5. Output results to `data/processed/`

### Interactive Dashboard

```bash
python run_app.py
```

The Streamlit dashboard provides:
- **Overview**: Key metrics and model summary
- **Scenario Analysis**: NPV comparison across scenarios
- **Credit Rating**: Rating migration visualization
- **Physical Risks**: CLIMADA hazard explorer
- **Cash Flow**: Detailed waterfall analysis

### Generating Figures

```bash
python generate_figures.py
```

Produces publication-ready figures:
- `fig1_npv_comparison.png` - NPV by scenario
- `fig2_waterfall.png` - Cash flow decomposition
- `fig3_rating_migration.png` - Credit rating paths
- `fig4_model_architecture.png` - Model architecture diagram
- `fig5_death_spiral.png` - Feedback loop illustration
- `fig6_data_integration.png` - Data source integration

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
risk_premium_2026/
├── src/
│   ├── app/                    # Streamlit dashboard
│   │   └── streamlit_app.py
│   ├── climada/               # Physical risk module
│   │   ├── hazards.py
│   │   └── integration.py
│   ├── risk/                  # Financial risk module
│   │   ├── credit_rating.py   # KIS methodology
│   │   ├── transition.py      # Policy risk
│   │   └── physical.py        # CLIMADA integration
│   ├── scenarios/             # Scenario definitions
│   │   └── definitions.py
│   ├── financial/             # Cash flow model
│   │   └── model.py
│   └── pipeline/              # Analysis runner
│       └── runner.py
├── data/
│   ├── raw/                   # Input data
│   │   ├── plant.csv          # Plant parameters
│   │   ├── physical.csv       # CLIMADA scenarios
│   │   ├── policy.csv         # Transition scenarios
│   │   └── financing.csv      # Financial terms
│   └── processed/             # Output data
│       ├── results.csv        # Scenario results
│       ├── credit_ratings.csv # Rating assessments
│       └── figures/           # Generated figures
├── docs/                      # Documentation
│   ├── korea_power_plan_methodology.md
│   ├── climada_integration_methodology.md
│   └── credit_rating_integration.md
├── tests/                     # Test suite
├── notebooks/                 # Jupyter notebooks
├── paper.tex                  # Academic paper (LaTeX)
├── paper.pdf                  # Compiled paper
├── run_app.py                 # Dashboard launcher
├── run_full_analysis.py       # Analysis runner
├── generate_figures.py        # Figure generator
└── requirements.txt           # Dependencies
```

---

## Academic Paper

The full academic paper is available in `paper.pdf`. Key sections:

1. **Introduction**: The Samcheok Paradox and research gap
2. **Theoretical Framework**: Integrated cash flow model and credit rating death spiral
3. **Methodology & Data**: Korea Power Plan, CLIMADA, and KIS methodology
4. **Results**: Scenario analysis and financial impacts
5. **Discussion**: Policy implications and just transition finance
6. **Appendices**: Detailed parameters and data tables

### Citation

If you use this model in your research, please cite:

```bibtex
@article{park2025climate,
  title={Quantifying the Climate Risk Premium: A Case Study of the Samcheok Blue Power Plant in South Korea},
  author={Park, Jinsu},
  journal={Energy Policy},
  year={2025},
  institution={PLANiT Institute},
  publisher={Elsevier}
}
```

---

## Key Findings for Policymakers

1. **Stranded Asset Risk is Real**: The 10th Power Supply Plan creates material financial risk for coal assets. Samcheok faces -251% to -390% NPV swing.

2. **Early Retirement is Optimal**: Waiting for "natural" economic obsolescence subjects owners to accelerating losses. Negotiated early retirement dominates market-driven collapse.

3. **Just Transition Finance Needed**: Total societal cost of disorderly exit: $4-5 billion. Structured transition (early retirement contracts, transition bonds) could save $3.5 billion vs. chaotic default.

4. **Rating Agencies Must Adapt**: Current ratings (BBB, 6-7% yields) don't reflect Power Supply Plan constraints. Forward-looking ratings should downgrade based on scheduled dispatch reductions.

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

*Last Updated: November 2025*

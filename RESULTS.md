# RESULTS.md

## Project Result Deep Explanation

This document explains what the model produced, why those results occur, and how to interpret them for decision-making.

## 1) Scope of This Result Set

- Asset: Samcheok Blue Power (2,100 MW coal)
- Output source: `results/scenario_comparison.csv`, `results/credit_ratings.csv`
- Run family: canonical frozen run currently tracked in this repository

The model combines:

- Transition channel: dispatch/pathway constraints and enhanced policy stress
- Physical channel: PLANiT-based wildfire, drought, water risk adjustments
- Financial channel: cashflow → DSCR/LLCR/NPV → rating → spread/WACC → CRP

## 2) Headline Outcomes (Current Canonical Files)

- Baseline NPV: **$4,628.9M**
- Worst-case NPV (enhanced_combined): **-$1,895.9M**
- Total value swing (best-to-worst): **$6,524.8M**
- Baseline rating: **AA**
- Severe policy rating: **CC**
- Enhanced-policy counterfactual CRP: **1,020 bps**

Interpretation:

- The dominant loss mechanism is transition policy stress, not physical hazard stress.
- Physical-only scenarios reduce value modestly in this calibration.

## 3) Scenario-by-Scenario Reading

### Baseline

- NPV: 4,628.9M
- IRR: 16.51%
- Avg DSCR: 2.99x
- Rating: AA

Meaning: healthy project-finance profile under base assumptions.

### Transition stress

- `moderate_transition`: NPV **-1,095.1M** vs baseline
- `aggressive_transition`: NPV **-3,260.2M** vs baseline

Meaning: dispatch and policy pressure reduce earnings power directly, then propagate to lower coverage and weaker valuation.

### Physical stress (PLANiT path)

- `moderate_physical`: NPV **-29.9M** vs baseline
- `high_physical`: NPV **-63.3M** vs baseline
- `severe_drought`: NPV **-19.8M** vs baseline

Meaning: in the current parameterization, physical risk is present but second-order compared to transition policy effects.

### Combined stress

- `combined_moderate`: NPV 3,512.8M
- `combined_aggressive`: NPV 1,329.7M

Meaning: combined outcomes are close to transition-dominant behavior; physical deltas are relatively small around transition trajectories.

### Enhanced 11th plan stress

- `enhanced_11th_plan`: NPV **-1,890.7M**, rating **CC**, CRP **1,020 bps**
- `enhanced_combined`: NPV **-1,895.9M**, rating **CC**, CRP **1,020 bps**

Meaning: when policy stress is severe enough, credit quality shifts to distress regime and cost of capital reprices sharply.

## 4) Why the Results Look Like This

### 4.1 Mechanical chain in the model

1. Risk assumptions lower effective generation or raise costs.
2. EBITDA declines.
3. DSCR/coverage weaken.
4. Rating deteriorates.
5. Spread and WACC rise.
6. NPV and financing conditions worsen further.

This is the practical "credit feedback" loop captured in the pipeline.

### 4.2 Why transition dominates in this run

- Transition scenarios directly compress utilization over many years.
- Enhanced plan stress can push coverage near/below debt-service comfort thresholds.
- Physical-risk conversion terms (wildfire outage, drought derate, water cap) are non-zero but currently small relative to transition-induced cashflow compression.

## 5) What CRP Means Here

This repository reports counterfactual CRP using an A-rated no-climate-risk reference.

- Counterfactual baseline spread: 150 bps (A)
- Scenario spread comes from rating mapping
- Financing layer computes WACC differential; CRP is expressed in bps

So a large CRP (e.g., 1,020 bps) should be read as a financing repricing signal under stressed climate-policy conditions.

## 6) Key Decision Insights

- For near-term risk management, policy/transition monitoring is the primary lever.
- Physical-risk live integration still matters for site-specific updates, but in current calibration it is not the first-order value driver.
- Credit outcomes are nonlinear: rating can remain stable for mild stress, then fall quickly under stronger policy constraints.

## 7) Limits and Cautions

- Results are model- and calibration-dependent, not universal constants.
- Physical module quality depends on PLANiT input coverage, scenario-year anchors, and asset matching.
- Some values in dashboard views are presentation-focused; regulatory claims should rely on files under `results/` and frozen manifests under `paper_dev/`.

## 8) Reproducibility Pointers

- Run model output refresh: `python scripts/regenerate_dashboard_data.py`
- Authoritative tables: `results/scenario_comparison.csv`, `results/credit_ratings.csv`
- Full process doc: `docs/MODEL_PROCESS_FULL.md`

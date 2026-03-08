# Climate Risk Premium Model - Canonical Results Summary

**Run Date**: February 26, 2026 (UTC)
**Subject**: Samcheok Blue Power Plant (2.1 GW)
**Source of Truth**:

- `results/scenario_comparison.csv`
- `results/credit_ratings.csv`
- Frozen snapshot + manifest under `paper_dev/02_results_freeze`

## Executive Summary

In the canonical run, transition-dominant severe policy scenarios generate the largest value destruction and credit deterioration.

- Baseline NPV: **$4,629M**
- Enhanced 11th Plan NPV: **-$1,891M**
- Baseline to Enhanced NPV swing: **$6,520M**
- Baseline rating: **AA**
- Enhanced 11th Plan rating: **CC**
- Enhanced 11th Plan counterfactual CRP: **1,020 bps**

## Scenario Results (Canonical)

| Scenario | NPV ($M) | IRR | Min DSCR | Rating | Counterfactual CRP (bps) |
|----------|----------|-----|----------|--------|--------------------------|
| Baseline | 4,629 | 16.51% | 2.56x | AA | -50 |
| Moderate Transition | 3,534 | 14.63% | 2.27x | AA | -50 |
| Aggressive Transition | 1,369 | 10.86% | 1.82x | A | 0 |
| Moderate Physical | 4,599 | 16.47% | 2.56x | AA | -50 |
| High Physical | 4,566 | 16.39% | 2.55x | AA | -50 |
| Combined Moderate | 3,513 | 14.59% | 2.26x | AA | -50 |
| Combined Aggressive | 1,330 | 10.76% | 1.80x | A | 0 |
| Low Demand | 1,994 | 12.70% | 1.66x | A | 0 |
| Severe Drought | 4,609 | 16.49% | 2.56x | AA | -50 |
| Enhanced 11th Plan | -1,891 | -8.18% | -0.34x | CC | 1,020 |
| Enhanced Combined | -1,896 | -8.23% | -0.34x | CC | 1,020 |

## Notes

1. This summary is intentionally synchronized to the canonical run used for paper freeze.
2. Dashboard-oriented derived files may differ if regenerated separately.
3. For manuscript claims, use the claim registry:
   - `paper_dev/04_sources/claim_registry.csv`

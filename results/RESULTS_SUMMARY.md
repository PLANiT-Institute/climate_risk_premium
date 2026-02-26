# Climate Risk Premium Model - Canonical Results Summary

**Run Date**: February 17, 2026 (UTC)
**Subject**: Samcheok Blue Power Plant (2.1 GW)
**Source of Truth**:

- `/Users/jinsu/Documents/GitHub/climate_risk_premium/results/scenario_comparison.csv`
- `/Users/jinsu/Documents/GitHub/climate_risk_premium/results/credit_ratings.csv`
- Frozen snapshot + manifest under `/Users/jinsu/Documents/GitHub/climate_risk_premium/paper_dev/02_results_freeze`

## Executive Summary

In the canonical run, transition-dominant severe policy scenarios generate the largest value destruction and credit deterioration.

- Baseline NPV: **$3,103M**
- Enhanced 11th Plan NPV: **-$3,293M**
- Baseline to Enhanced NPV swing: **$6,396M**
- Baseline rating: **AA**
- Enhanced 11th Plan rating: **C**
- Enhanced 11th Plan counterfactual CRP: **1,735 bps**

## Scenario Results (Canonical)

| Scenario | NPV ($M) | IRR | Min DSCR | Rating | Counterfactual CRP (bps) |
|----------|----------|-----|----------|--------|--------------------------|
| Baseline | 3,103 | 12.00% | 1.86x | AA | -50 |
| Moderate Transition | 2,038 | 10.56% | 1.65x | A | 0 |
| Aggressive Transition | -72 | 7.05% | 1.33x | A | 0 |
| Moderate Physical | 3,074 | 11.96% | 1.85x | AA | -50 |
| High Physical | 3,042 | 11.91% | 1.84x | AA | -50 |
| Combined Moderate | 2,018 | 10.53% | 1.64x | A | 0 |
| Combined Aggressive | -109 | 6.97% | 1.32x | A | 0 |
| Low Demand | 497 | 8.22% | 1.17x | BBB | 85 |
| Severe Drought | 3,084 | 11.98% | 1.85x | AA | -50 |
| Enhanced 11th Plan | -3,293 | -13.02% | -0.24x | C | 1,735 |
| Enhanced Combined | -3,297 | -13.07% | -0.24x | C | 1,735 |

## Notes

1. This summary is intentionally synchronized to the canonical run used for paper freeze.
2. Dashboard-oriented derived files may differ if regenerated separately.
3. For manuscript claims, use the claim registry:
   - `/Users/jinsu/Documents/GitHub/climate_risk_premium/paper_dev/04_sources/claim_registry.csv`

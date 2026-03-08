# Scenario Definition Contract (Climate Risk Management Paper)

This document defines the only scenario set admissible for manuscript tables, figures, and claims.

## Scenario Set ID

`default_11_scenarios_v1`

## Producer

- Script: `/Users/jinsu/Documents/GitHub/climate_risk_premium/scripts/reproduce_results.py`
- Runner: `CRPModelRunner.run_multi_scenario()` default scenario list

## Admissible Scenarios

1. `baseline`
2. `moderate_transition`
3. `aggressive_transition`
4. `moderate_physical`
5. `high_physical`
6. `combined_moderate`
7. `combined_aggressive`
8. `low_demand`
9. `severe_drought`
10. `enhanced_11th_plan`
11. `enhanced_combined`

## Canonical Output Files

- `scenario_comparison.csv`
- `credit_ratings.csv`
- `cashflow_*.csv`

All manuscript numbers must be traceable to a frozen snapshot in:

- `/Users/jinsu/Documents/GitHub/climate_risk_premium/paper_dev/02_results_freeze`

## Policy for Non-Model Claims

- Only primary sources are allowed for policy/process claims.
- If a claim cannot be tied to a primary source or frozen output hash, remove or rewrite as a hypothesis.

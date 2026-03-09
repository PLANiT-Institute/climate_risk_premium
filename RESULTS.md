# RESULTS.md

## 1. What this file explains

This document explains:

1. What the current model run produced
2. How physical risk inputs are converted into financial impacts
3. Why transition scenarios dominate value loss in the current calibration

Primary source table: `results/scenario_comparison.csv`.

## 2. Scenario outcomes (current canonical outputs)

| Scenario | NPV (USD mn) | Delta vs Baseline (USD mn) | IRR | Min DSCR | Rating | Counterfactual CRP (bps) |
|---|---:|---:|---:|---:|---|---:|
| baseline | 4,628.9 | 0.0 | 16.51% | 2.56 | AA | -50 |
| moderate_transition | 3,533.8 | -1,095.1 | 14.63% | 2.27 | AA | -50 |
| aggressive_transition | 1,368.7 | -3,260.2 | 10.86% | 1.82 | A | 0 |
| moderate_physical | 4,597.1 | -31.9 | 16.46% | 2.56 | AA | -50 |
| high_physical | 4,563.3 | -65.7 | 16.39% | 2.55 | AA | -50 |
| combined_moderate | 3,511.1 | -1,117.8 | 14.59% | 2.26 | AA | -50 |
| combined_aggressive | 1,328.3 | -3,300.7 | 10.76% | 1.80 | A | 0 |
| low_demand | 1,993.8 | -2,635.1 | 12.70% | 1.66 | A | 0 |
| severe_drought | 4,606.8 | -22.2 | 16.49% | 2.56 | AA | -50 |
| enhanced_11th_plan | -1,890.7 | -6,519.7 | -8.18% | -0.34 | CC | 1,020 |
| enhanced_combined | -1,896.4 | -6,525.3 | -8.23% | -0.34 | CC | 1,020 |

Summary:
- Baseline to enhanced_combined swing is about **6,525.3 USD mn**.
- Physical-only deltas are small relative to transition-policy deltas in this run.

## 3. Physical risk conversion logic used in this repository

The CRP model uses PLANiT as the physical-risk gateway.

- Wildfire data source: CLIMADA (through PLANiT)
- Drought and water-risk data source: PhysRisk/OS-Climate (through PLANiT)

### 3.1 Wildfire -> outage rate

Primary conversion in `src/planit/adapter.py`:

```text
outage_rate = annual_event_frequency_per_year
              x wildfire_outage_probability
              x (wildfire_outage_duration_hours / hours_per_year)
```

Default parameters (`src/planit/config.py`):
- `wildfire_outage_probability = 0.10`
- `wildfire_outage_duration_hours = 24`
- `hours_per_year = 8760`

Example:
- if annual frequency = 1.0 event/year,
- outage_rate = 1.0 x 0.10 x (24/8760) = 0.000274 (0.0274%).

When frequency metadata is missing, wildfire outage is treated as 0.0
(or explicit baseline fallback if provided in the calling context).

### 3.2 Drought -> capacity derate

When distribution is provided, model uses expected value from bins:

```text
expected_impact = sum( midpoint(bin_i) x probability_i )
capacity_derate = expected_impact x drought_severity_scale
```

If distribution is not available, it uses `impact_mean`.

### 3.3 Water risk -> constrained capacity

```text
expected_impact = sum( midpoint(bin_i) x probability_i )
water_constrained_capacity = max(0, 1 - expected_impact)
```

If distribution is not available, it uses `impact_mean`.

### 3.4 Time handling

PLANiT hazard anchors are interpolated linearly across years (default 2030/2040/2050/2060),
with a baseline blend from year 2024 before first anchor.

## 4. Why financial results move

End-to-end chain:

1. Physical and transition factors modify generation/cost assumptions.
2. EBITDA and CFADS change.
3. DSCR/LLCR move.
4. Credit rating and spread move.
5. WACC and valuation (NPV/IRR) move.

In this calibration, transition scenarios directly reduce dispatch/utilization over many years,
so transition loss dominates physical-only loss.

## 5. Live location behavior (validated)

With:
- `CRP_PLANIT_MODE=live`
- `CRP_PLANIT_LAT/LON` provided

the runner generates a dynamic site GeoJSON and executes PLANiT runtime calls for the input location.
For dynamic location mode, pipeline uses live rows directly (no CSV backfill).

## 6. Practical interpretation

- This model is not forcing wildfire risk through monetary-loss normalization.
- Wildfire is treated as event-probability-driven outage when event frequency exists.
- Drought/water-risk are treated as expected operational stress from PhysRisk distributions/means.
- Financial impact is produced through the same cashflow/rating engine used for transition risk.

## 7. Validation status in this update

- PLANiT integration tests: pass (`tests/test_planit_integration.py`)
- CLIMADA integration tests: pass (`tests/test_climada_integration.py`)
- Live smoke checks performed for wildfire, drought, water_risk with dynamic location inputs

# Climate Risk Premium Model for Samcheok Blue Power

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This repository quantifies plant-level climate risk premium (CRP) by connecting:

1. Korea power-policy/dispatch pathways (transition risk)
2. PLANiT physical risk engine (CLIMADA wildfire + PhysRisk drought/water risk)
3. Project-finance cashflow model + KIS-style credit-rating/spread logic

The target asset is Samcheok Blue Power (2.1 GW).

## Current Headline Results (canonical run)

Source: `results/scenario_comparison.csv` (refreshed March 2026)

| Scenario | NPV (USD mn) | IRR | Min DSCR | Rating | Counterfactual CRP (bps) |
|---|---:|---:|---:|---|---:|
| baseline | 4,628.9 | 16.51% | 2.56x | AA | -50 |
| moderate_transition | 3,533.8 | 14.63% | 2.27x | AA | -50 |
| aggressive_transition | 1,368.7 | 10.86% | 1.82x | A | 0 |
| moderate_physical | 4,597.1 | 16.46% | 2.56x | AA | -50 |
| high_physical | 4,563.3 | 16.39% | 2.55x | AA | -50 |
| combined_moderate | 3,511.1 | 14.59% | 2.26x | AA | -50 |
| combined_aggressive | 1,328.3 | 10.76% | 1.80x | A | 0 |
| low_demand | 1,993.8 | 12.70% | 1.66x | A | 0 |
| severe_drought | 4,606.8 | 16.49% | 2.56x | AA | -50 |
| enhanced_11th_plan | -1,890.7 | -8.18% | -0.34x | CC | 1,020 |
| enhanced_combined | -1,896.4 | -8.23% | -0.34x | CC | 1,020 |

Key read:
- Baseline to enhanced_combined NPV swing: about **6,525.3 USD mn**.
- In this calibration, transition-policy stress dominates physical-only stress.

## Physical Risk Logic (PLANiT integration)

Active hazards in CRP pipeline:
- `wildfire` (CLIMADA output via PLANiT)
- `drought` (PhysRisk output via PLANiT)
- `water_risk` (PhysRisk output via PLANiT)

The ambient-temperature heat-derate channel is explicitly disabled by
`PLANiTIntegrationConfig.efficiency_channel.enabled = false`. The repository
does not currently include site-level daily ERA5 temperature histories or
downscaled SSP temperature series for Samcheok, so total physical risk is
underestimated and reported physical risk premium values should be read as
conservative with respect to thermal-efficiency losses.

### Wildfire conversion

Primary method (`event_probability`):

```text
outage_rate = annual_event_frequency_per_year
              x wildfire_outage_probability
              x (wildfire_outage_duration_hours / hours_per_year)
```

Default parameters in `src/planit/config.py`:
- `wildfire_outage_probability = 0.10`
- `wildfire_outage_duration_hours = 24`
- `hours_per_year = 8760`

Sourcing caveat: `0.10` is a central modeling assumption, not a directly
observed KEPCO/KPX fire-to-outage statistic. It is benchmarked against Dale et
al. (2018, CCCA4-CEC-2018-002), which reports that most wildfires near
California transmission paths have little/no grid impact. Reviewer-facing
results should include `wildfire_outage_probability` sensitivity `[0.05, 0.20]`.
The `24h` duration is benchmarked against PG&E's 2025 CAISO transmission
availability report, where mean forced-outage durations for higher-voltage
classes are around one day; use duration sensitivity `[12h, 72h]`.

If event-frequency metadata is unavailable, wildfire outage defaults to 0.0
(or explicit CSV baseline when provided).

Appendix sensitivity table:

```bash
python scripts/wildfire_outage_sensitivity.py
```

### Drought and water risk conversion

When distribution data exists, the adapter uses distribution expected impact instead of raw mean.

```text
expected_impact = sum( midpoint(bin_i) x probability_i )
```

Then:

```text
capacity_derate (drought) = expected_impact x drought_severity_scale
water_constrained_capacity = max(0, 1 - expected_impact)
```

If distribution is absent, raw `impact_mean` is used.

### Time interpolation

PLANiT anchor years are interpolated linearly (default anchors: 2030, 2040, 2050, 2060),
with 2024 baseline blending for pre-anchor years.

## Live location call flow

Default mode is CSV snapshot mode. Set live mode to call PLANiT runtime directly.

### Live run example (dynamic location)

```bash
CRP_PLANIT_MODE=live \
CRP_PLANIT_LAT=37.4404 \
CRP_PLANIT_LON=129.1671 \
CRP_PLANIT_ASSET_NAME="samcheok_live" \
python scripts/reproduce_results.py
```

Optional runtime controls:
- `CRP_PLANIT_SCENARIOS=ssp126,ssp245,ssp585`
- `CRP_PLANIT_YEARS=2030,2040,2050,2060`
- `CRP_PLANIT_WILDFIRE_MAX_IT`, `CRP_PLANIT_WILDFIRE_BLURR_STEPS`, `CRP_PLANIT_WILDFIRE_MAX_PROB_SEASONS`
- `CRP_PLANIT_INCLUDE_GRID=1` (default) to include plant + substation + transmission line in dynamic GeoJSON
- `CRP_PLANIT_TARGET_ASSET_MODE=all|plant` (`all` default when grid included)

Wildfire outage assumption overrides:
- `CRP_WILDFIRE_OUTAGE_PROBABILITY` (default `0.10`)
- `CRP_WILDFIRE_OUTAGE_DURATION_HOURS` (default `24`)
- `CRP_WILDFIRE_OUTAGE_METHOD=event_probability`

Notes:
- With dynamic location (`CRP_PLANIT_LAT/LON`), pipeline uses live results without CSV backfill.
- Dynamic location mode now supports grid-aware assets (power plant, substation, transmission line).
- Runner includes Python 3.14 compatibility shims for PLANiT/CLIMADA dependency edges.

## End-to-end process

1. Load plant/financing/scenario inputs.
2. Build yearly transition adjustments.
3. Build yearly physical adjustments from PLANiT adapter.
4. Convert adjustments to generation, costs, EBITDA, CFADS, DSCR, NPV/IRR.
5. Map financial metrics to rating and spread.
6. Compute CRP and scenario comparison outputs.

## Data interfaces (core)

`PLANiTHazardResult` (`src/planit/runner.py`) fields used by the adapter:
- Required: `hazard_type`, `scenario`, `year`, `asset`, `value`, `unit`, `source`
- Wildfire metadata: `event_frequency_per_year`, `event_count`, `reference_years`
- PhysRisk distribution: `impact_bin_edges`, `impact_probabilities`, `impact_exceedance_values`, `impact_exceedance_probabilities`

## Installation

```bash
git clone https://github.com/jinsu-park/climate_risk_premium.git
cd climate_risk_premium
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run and test

```bash
python scripts/reproduce_results.py
python scripts/regenerate_dashboard_data.py
pytest -q tests/test_planit_integration.py tests/test_climada_integration.py
```

## Dashboard / Vercel

The web app lives in `crp-dashboard/`.
For Vercel deployment, set **Root Directory** to `crp-dashboard`.

Local dev:

```bash
cd crp-dashboard
npm install
npm run dev
```

## Key outputs

- Authoritative outputs: `results/`
- Dashboard JSON outputs: `crp-dashboard/src/data/`
- Processed CSVs: `data/processed/`

## Documentation

- Full process guide: `docs/MODEL_PROCESS_FULL.md`
- Result interpretation: `RESULTS.md`
- Architecture: `docs/ARCHITECTURE.md`

## License

MIT License (`LICENSE`).

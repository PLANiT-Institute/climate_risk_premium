# Gate 5 — Final-Output Level Ablation

## Pipeline Trace: CLIMADA → Final CRP

```
CLIMADA WildFire.set_proba_fire_seasons()
  → hazard.frequency array (sums to ~1.0 for ALL SSPs)
  → PLANiTHazardResult.event_frequency_per_year ≈ 1.0
  → PLANiTAdapter._extract_wildfire_frequency()     [adapter.py:286-306]
  → PLANiTAdapter._compute_wildfire_outage_rate()   [adapter.py:308-345]
    outage_rate = freq × outage_prob × (hours/8760)
    outage_rate *= get_climate_factor("wildfire", year, scenario)  ← [adapter.py:336-337]
  → PhysicalAdjustments.outage_rate
  → compute_cashflows_timeseries()
  → credit_rating → CRP spread bps
```

**Key finding**: `get_climate_factor()` is called at `src/planit/adapter.py:336`
AFTER the CLIMADA frequency is converted to outage_rate. It reads from
`data/physical/climate_factors.csv` via `src/data/loaders.py:272`.

## CLIMADA Frequency Per SSP (n=100, seed=42)

| SSP | frequency_sum | n_events | |AAI| |
|-----|--------------|----------|------|
| historical | 1.000000 | 110 | 28016519 |
| ssp126 | 1.000000 | 110 | 81455346 |
| ssp245 | 1.000000 | 110 | 244026235 |
| ssp585 | 1.000000 | 110 | 428101546 |

**All SSPs have frequency_sum ≈ 1.0** because CLIMADA normalizes event
frequencies to represent annual rates (frequency = 1/equivalent_years).

## Climate Factors Applied (wildfire, year=2040)

| SSP | CRP Label | Climate Factor |
|-----|-----------|---------------|
| historical | baseline | 1.0000 |
| ssp126 | SSP1-2.6 | 1.1400 |
| ssp245 | RCP4.5 | 1.2000 |
| ssp585 | RCP8.5 | 1.5750 |

Source: `data/physical/climate_factors.csv` (IPCC AR6 + KMA projections)

## Final Outage Rate Ablation

Parameters: outage_prob=0.1, duration=24.0h, hours/yr=8760.0

| SSP | freq | CF | outage (with CF) | outage (no CF) | CSV contribution |
|-----|------|-----|-----------------|----------------|------------------|
| historical | 1.0000 | 1.0000 | 0.00027397 | 0.00027397 | 0.0% |
| ssp126 | 1.0000 | 1.1400 | 0.00031233 | 0.00027397 | 12.3% |
| ssp245 | 1.0000 | 1.2000 | 0.00032877 | 0.00027397 | 16.7% |
| ssp585 | 1.0000 | 1.5750 | 0.00043151 | 0.00027397 | 36.5% |

## Interpretation

### SSP Differentiation Sources at Each Level

| Level | CLIMADA-driven | CSV-driven |
|-------|---------------|------------|
| CLIMADA AAI | 100% (intensity varies: 81455346 → 428101546) | 0% |
| Adapter outage_rate | ~0% (freq≈1.0 for all) | ~100% (CF: 1.14 → 1.57) |
| Final CRP spread | Mixed (both paths contribute) | Mixed |

### Why This Matters

The adapter's outage_rate pathway discards CLIMADA's intensity signal
(AAI) and uses only the frequency (≈1.0 for all SSPs). The SSP
differentiation in the final CRP comes **entirely from `climate_factors.csv`**
at this point in the pipeline.

CLIMADA's role is to provide a physically-grounded **baseline frequency**
(~1 event/year for Samcheok), not to differentiate between SSPs. The SSP
differentiation is legitimately provided by the IPCC AR6/KMA multipliers
in the CSV — these are peer-reviewed climate projections, not arbitrary
assumptions.

### Paper Framing Recommendation

The paper MUST acknowledge both sources:

> "Wildfire physical risk is computed in two stages: (1) CLIMADA provides
> a site-specific baseline event frequency from MODIS/FIRMS fire detection
> data and Monte Carlo probabilistic fire propagation (n=100 seasons,
> seed=42); (2) scenario-dependent climate change multipliers from IPCC AR6
> projections (Table 4.5/4.8) scale the baseline frequency to reflect
> SSP-specific warming trajectories."

Do NOT claim that CLIMADA directly produces SSP-differentiated risk.
CLIMADA provides the **site-specific baseline**; CSV provides the
**scenario scaling**.

## Line Number Reference

| Step | File | Lines | Description |
|------|------|-------|-------------|
| 1 | `src/planit/adapter.py` | 286-306 | Extract frequency from PLANiT result |
| 2 | `src/planit/adapter.py` | 321-330 | Compute base outage_rate from frequency |
| 3 | `src/planit/adapter.py` | 333-341 | Apply `get_climate_factor()` multiplier |
| 4 | `src/data/loaders.py` | 272-329 | `get_climate_factor()` with interpolation |
| 5 | `data/physical/climate_factors.csv` | all | Wildfire multiplier table by scenario/year |
| 6 | `src/pipeline/runner.py` | 326-333 | Adapter called per year in yearly loop |
| 7 | `src/pipeline/runner.py` | 408-414 | CSV fallback also uses `get_climate_factor()` |

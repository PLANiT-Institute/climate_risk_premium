# PLANiT Module — Archived

Archived: 2026-04-09  
Branch: feat/wri-thermal-integration

## Why archived

The PLANiT module bridged CLIMADA/PhysRisk external APIs to the CRP pipeline. It was
replaced by three self-contained parametric models in `src/models/physical/`:

| Old channel         | Old source               | New source                          |
|---------------------|--------------------------|-------------------------------------|
| outage_rate         | PLANiT wildfire cache    | `WildfireModel` (KFS/CLIMADA params)|
| efficiency_loss     | hardcoded 0.0 in adapter | `TemperatureModel` (KMA/EPRI)       |
| water_temp_disruption | WRI CSV via adapter    | `WaterTemperatureModel` (WRI curves)|
| capacity_derate     | drought model            | **removed** (channel deleted)       |
| water_constrained_capacity | water-stress model | **removed** (channel deleted)    |

## What went wrong

1. The CSV snapshot directory (`data/planit_snapshots/`) never existed in this repo —
   it lived on the original developer's machine in a separate repository.
2. The wildfire CLIMADA cache was missing the `event_frequency_per_year` field,
   causing a KeyError that silently fell back to zero.
3. `efficiency_loss` was hardcoded to `0.0` in `PLANiTAdapter.get_physical_adjustments()`.

All three physical risk channels therefore produced zero values in production.

## Files archived here

- `runner.py` — 796-line PLANiT orchestrator
- `adapter.py` — 414-line CLIMADA/PhysRisk → CRP adapter
- `cache.py` — hazard event cache utilities
- `config.py` — PLANiT configuration dataclasses
- `vulnerability.py` — damage function / vulnerability curves
- `__init__.py` — module exports

`archive/risk/physical_legacy.py` — the old monolithic `src/risk/physical.py`
(predates the `src/risk/physical/` package refactor).

`archive/tests/test_planit_integration.py` — integration tests for PLANiT adapter.
The TemperatureModel tests were migrated to `tests/test_temperature_model.py`.

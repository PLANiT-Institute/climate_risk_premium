# Climate Risk Premium Model - Architecture

## New Class-Based Structure

```
src/models/
├── __init__.py                 # Exports all models
├── base.py                     # Base classes (BaseRiskModel, BaseScenario, BaseDamageFunction)
├── transition/                 # Transition risk module
│   ├── __init__.py
│   ├── model.py               # TransitionRiskModel class
│   ├── carbon_pricing.py      # Carbon pricing scenarios
│   └── policy.py              # Policy phase-out logic
├── physical/                   # Physical risk module
│   ├── __init__.py
│   ├── model.py               # PhysicalRiskModel class
│   ├── hazards.py             # Hazard calculations
│   └── temperature.py         # Temperature efficiency model
├── scenarios/                  # Climate scenarios (CLIMADA-based)
│   ├── __init__.py
│   ├── climate_scenario.py    # ClimateScenario class
│   ├── rcp.py                 # RCP pathway data
│   └── ssp.py                 # SSP pathway data
└── damage_functions/          # Selectable damage functions
    ├── __init__.py
    ├── base.py                # BaseDamageFunction
    ├── wildfire.py            # Wildfire damage functions
    ├── flood.py               # Flood damage functions
    ├── tropical_cyclone.py    # TC damage functions
    └── registry.py            # DamageFunction registry
```

## Class Hierarchy

```
BaseRiskModel (ABC)
├── TransitionRiskModel        # Carbon pricing, policy, dispatch
└── PhysicalRiskModel          # Hazards, temperature, SLR

BaseScenario (ABC)
├── ClimateScenario            # RCP/SSP climate pathways
├── TransitionScenario         # Policy scenarios
└── MarketScenario             # Price scenarios

BaseDamageFunction (ABC)
├── WildfireDamageFunction     # FWI → outage rate
├── FloodDamageFunction        # Depth → damage
├── TCDamageFunction           # Wind speed → damage
└── TemperatureDamageFunction  # ΔT → efficiency loss
```

## User Selection Interface

Users can select:
1. **Climate Scenario**: RCP2.6, RCP4.5, RCP8.5 (from CLIMADA)
2. **Target Year**: 2030, 2050, 2100
3. **Damage Functions**: Multiple options per hazard type

## Data Sources

All data sources are documented in `docs/sources/`:
- `CLIMATE_SCENARIOS.md` - CLIMADA RCP/SSP data sources
- `DAMAGE_FUNCTIONS.md` - Literature sources for each function
- `TRANSITION_ASSUMPTIONS.md` - Carbon pricing, policy sources

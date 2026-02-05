# Physical Risk Model - Technical Documentation

## Executive Summary

The Physical Risk Model quantifies climate-related physical hazard impacts on thermal power plants, specifically Korean coal-fired generation assets. It translates hazard data from CLIMADA and literature sources into annual financial impact estimates, supporting climate stress testing and equity valuation adjustments.

**Key Outputs:**
- Total Physical Risk: 0.96% (2024 baseline) → 2.55% (2050 RCP8.5)
- Breakdown by hazard type (acute vs. chronic)
- Confidence intervals (10th/90th percentile)
- Integration with financial modules (CDDM, Stress Test)

---

## 1. Model Architecture

### 1.1 Module Structure

```
src/models/physical/
├── model.py              # PhysicalRiskModel - main entry point
├── hazards.py            # Hazard definitions, baselines, climate factors
├── compound_risk.py      # Multi-hazard interaction model
├── temperature.py        # Temperature efficiency impact model
├── exposure.py           # Asset exposure and vulnerability
├── climada_api.py        # CLIMADA data interface
├── scenarios/            # RCP/SSP climate scenarios
│   ├── climate_scenario.py
│   ├── rcp.py
│   └── ssp.py
└── damage_functions/     # Hazard-specific damage functions
    ├── base.py           # Sigmoid damage function base
    ├── wildfire.py
    ├── flood.py
    ├── tropical_cyclone.py
    ├── drought.py
    └── heat_stress.py
```

### 1.2 Data Flow

```
CSV Data Files                    Code Modules                    Outputs
──────────────                    ────────────                    ───────
data/physical/
├── hazard_baselines.csv    →    hazards.py                  →   HazardResult
├── climate_factors.csv     →    get_climate_factor()        →   ClimateFactorSet
└── compound_events.csv     →    compound_risk.py            →   CompoundRiskResult
                                       ↓
                                 model.py                     →   RiskResult
                                 PhysicalRiskModel                 ↓
                                       ↓                      Financial Modules
                                 temperature.py               ←───────────────
                                 TemperatureModel
```

### 1.3 Core Formula

```
Total Physical Risk = Σ(Hazard_i × Climate_Factor_i) + Compound_Adjustment

Where:
  Hazard_i = Outage_Rate + Capacity_Derate + Efficiency_Loss
  Climate_Factor_i = f(year, scenario) from IPCC projections
  Compound_Adjustment = (Total_Base × Compound_Factor) for correlated events
```

---

## 2. Hazard Types and Baselines

### 2.1 Seven Hazard Categories

| Hazard Type | Baseline Impact | Unit | Data Source |
|-------------|-----------------|------|-------------|
| **Wildfire** | 0.0034% | Outage rate | CLIMADA WildFire + Korea Forest Service |
| **Tropical Cyclone** | 0.0055% | Outage rate | CLIMADA TropCyclone + IBTrACS |
| **River Flood** | 0.0% | - | Plant at 10m elevation (negligible) |
| **Coastal Flood** | 0.0% | - | Plant at 10m elevation (negligible) |
| **Drought** | 0.7% | Capacity derate | KMA drought + SPEI data |
| **Heat Stress** | 0.1% | Efficiency loss | KMA heat wave data |
| **Sea Level Rise** | Indirect | Via coastal flood | NASA/IPCC AR6 projections |

### 2.2 Baseline Data Sources

All baselines loaded from `data/physical/hazard_baselines.csv`:

```csv
hazard_type,base_frequency,base_intensity,intensity_unit,outage_rate,capacity_derate,efficiency_loss
wildfire,0.75,25.0,FWI,0.000034,0.0,0.0
tropical_cyclone,0.15,35.0,m/s,0.000055,0.0,0.0
drought,0.15,-1.2,SPI,0.0,0.005,0.002
heat_stress,7.0,36.5,C,0.0,0.0,0.001
```

### 2.3 Impact Categories

1. **Outage Rate**: Forced shutdowns from acute events (hours lost / 8760)
2. **Capacity Derate**: Reduced maximum output (e.g., cooling water constraints)
3. **Efficiency Loss**: Reduced thermal efficiency (e.g., higher condenser temperatures)

---

## 3. Climate Change Factors

### 3.1 Projection Methodology

Climate factors represent multipliers on baseline hazard impacts:
- Factor = 1.0 at 2024 baseline
- Factors increase non-linearly with warming

### 3.2 Scenario Support

| Scenario | Type | Temperature Target |
|----------|------|-------------------|
| RCP4.5 | Representative Concentration Pathway | ~2.4°C by 2100 |
| RCP8.5 | Representative Concentration Pathway | ~4.3°C by 2100 |
| SSP1-2.6 | Shared Socioeconomic Pathway | ~1.8°C by 2100 |
| SSP2-4.5 | Shared Socioeconomic Pathway | ~2.7°C by 2100 |
| SSP5-8.5 | Shared Socioeconomic Pathway | ~4.4°C by 2100 |

### 3.3 Climate Factor Projections (RCP8.5)

| Year | Wildfire | Tropical Cyclone | Drought | Heat Stress | SLR (m) |
|------|----------|-----------------|---------|-------------|---------|
| 2024 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 |
| 2030 | 1.15 | 1.03 | 1.12 | 1.20 | 0.07 |
| 2050 | 2.00 | 1.10 | 1.40 | 2.50 | 0.25 |
| 2100 | 4.00 | 1.20 | 1.80 | 5.00 | 0.80 |

**Sources:**
- IPCC AR6 WG1 Tables 4.5, 4.8
- Korea Meteorological Administration (KMA) regional projections
- World Weather Attribution (WWA)

### 3.4 Interpolation

For years between defined points, linear interpolation is applied:

```python
def get_climate_factor(hazard_type, year, scenario):
    factors = load_climate_factors()[scenario]
    years = sorted(factors.keys())

    if year in factors:
        return factors[year].get_factor(hazard_type)

    # Linear interpolation between bracketing years
    for i, y in enumerate(years[:-1]):
        if years[i] <= year < years[i + 1]:
            y0, y1 = years[i], years[i + 1]
            f0, f1 = factors[y0].get_factor(hazard_type), factors[y1].get_factor(hazard_type)
            return f0 + (f1 - f0) * (year - y0) / (y1 - y0)
```

---

## 4. Damage Functions

### 4.1 Sigmoid Damage Function (CLIMADA Standard)

Following Emanuel (2011) and Lüthi et al. (2021):

```
f(i) = i^n / (1 + i^n)

Where:
  i = (intensity - threshold) / i_half
  i_half = intensity at 50% damage
  n = power exponent (typically 3)
```

### 4.2 Available Functions by Hazard

| Hazard | Function | Parameters | Source |
|--------|----------|------------|--------|
| Wildfire | FWILinearFunction | threshold=15, slope=0.02 | Korea Forest Service |
| Wildfire | FWIExponentialFunction | threshold=20, i_half=45 | Lüthi et al. (2021) |
| Tropical Cyclone | EmanuelWindDamage | threshold=25.7 m/s, i_half=74.7 m/s | Emanuel (2011) |
| Flood | DepthDamageFunction | threshold=0.1m, i_half=1.5m | HAZUS-MH |
| Drought | SPEIDamageFunction | threshold=-1.0, i_half=-2.0 | KMA + literature |
| Heat Stress | TemperatureEfficiencyFunction | 0.1%/°C air, 0.15%/°C water | Maulbetsch & DiFilippo (2006) |

### 4.3 Damage Function Registry

```python
registry = DamageFunctionRegistry()
registry.register(FWILinearFunction())
registry.register(EmanuelWindDamage())

# Use in model
model = PhysicalRiskModel()
model.set_damage_function(HazardType.WILDFIRE, registry.get("fwi_linear"))
```

---

## 5. Compound Risk Model

### 5.1 Compound Event Types

Multi-hazard interactions where co-occurrence amplifies impacts:

| Event Type | Hazard 1 | Hazard 2 | Correlation | Amplification |
|------------|----------|----------|-------------|---------------|
| drought_heat | Drought | Heat Stress | 0.65 | 1.5x |
| tc_flood | Tropical Cyclone | River Flood | 0.45 | 1.3x |
| heat_wildfire | Heat Stress | Wildfire | 0.55 | 1.4x |
| slr_surge | Sea Level Rise | Coastal Flood | 1.00 | 2.0x |
| drought_wildfire | Drought | Wildfire | 0.60 | 1.6x |

### 5.2 Joint Probability Calculation

Using Gaussian copula approximation:

```python
def calculate_joint_probability(p1, p2, correlation):
    if correlation == 0:
        return p1 * p2

    independent = p1 * p2
    correlated = independent * (1 + correlation * min(p1, p2) / max(p1, p2))
    return min(correlated, min(p1, p2))
```

### 5.3 Compound Impact Formula

```python
def calculate_compound_impact(impact1, impact2, amplification, correlation):
    base_impact = impact1 + impact2
    effective_amp = 1.0 + (amplification - 1.0) * abs(correlation)
    return min(base_impact * effective_amp, 1.0)
```

**Literature:**
- Zscheischler et al. (2018) "Future climate risk from compound events" Nature Climate Change
- Raymond et al. (2020) "Understanding and managing connected extreme events" Nature Climate Change
- IPCC AR6 WG1 Chapter 11

---

## 6. Temperature Efficiency Model

### 6.1 Efficiency Loss Components

| Component | Coefficient | Source |
|-----------|-------------|--------|
| Air temperature on turbine | 0.10%/°C | EPRI (2011) |
| Condenser vacuum loss | 0.05%/°C | Maulbetsch & DiFilippo (2006) |
| Cooling water temperature | 0.15%/°C | Zhou et al. (2018) |
| Heat wave derate | 5% during events | van Vliet et al. (2012) |
| Extreme heat derate | 8% during >40°C | Korea power plant data |

### 6.2 Temperature Projections (Korea)

**RCP8.5 Scenario:**

| Year | ΔT Air (°C) | ΔT SST (°C) | Heat Wave Days | Tropical Nights |
|------|-------------|-------------|----------------|-----------------|
| 2024 | 0.0 | 0.0 | 7 | 8.4 |
| 2030 | 0.8 | 0.5 | 12 | 14.2 |
| 2050 | 2.0 | 1.4 | 25 | 37.2 |
| 2100 | 4.7 | 3.5 | 50 | 85.2 |

**Sources:**
- KMA (Korea Meteorological Administration) projections
- KHOA (Korea Hydrographic and Oceanographic Agency) SST data
- IPCC AR6 WG1 Chapter 4

### 6.3 Samcheok Blue Power Sea Surface Temperature

```python
SAMCHEOK_SST = {
    "annual_mean": 14.5,       # °C
    "summer_mean": 22.0,       # July-August
    "summer_max": 26.5,        # Peak temperature
    "warming_rate": 0.04,      # °C/year since 1990
    "source": "KHOA East Sea SST data (1990-2023)",
}
```

---

## 7. Exposure and Vulnerability

### 7.1 CLIMADA Framework

```
Risk = Hazard × Exposure × Vulnerability
```

### 7.2 Exposure Components

| Component | Description | Data Source |
|-----------|-------------|-------------|
| Asset Value | Replacement cost, book value | KEPCO, KOSPO reports |
| Geographic | Location, elevation, coastal proximity | Plant specifications |
| Operational | Capacity, generation, capacity factor | EPSIS data |

### 7.3 Vulnerability Factors

| Factor | Description | Impact |
|--------|-------------|--------|
| Plant Age | Older plants more vulnerable | +1 to +4 score |
| Cooling System | Once-through sea is most resilient | ±1 to ±3 score |
| Elevation | <5m increases flood risk | +2 score |
| Adaptive Capacity | Backup systems reduce vulnerability | -1 to -5 score |

### 7.4 Samcheok Blue Power Profile

```python
SAMCHEOK_BLUE_POWER = PowerPlantExposure(
    name="Samcheok Blue Power",
    capacity_mw=2100.0,
    plant_type=PlantType.COAL_USC,
    cooling_system=CoolingSystem.ONCE_THROUGH_SEA,
    construction_year=2017,
    replacement_cost_musd=4500.0,
    elevation_m=10.0,
    distance_coast_km=0.5,
)
```

---

## 8. CLIMADA Integration

### 8.1 Data Sources

| Source | Hazard Types | Coverage |
|--------|--------------|----------|
| IBTrACS | Tropical Cyclones | 1842-present |
| ERA5 | Wildfire, Temperature | 1979-present |
| ISIMIP | River Floods | 1971-2010 |
| GTSR | Coastal Floods, SLR | 1979-present |
| SPEI | Drought | 1958-present |

### 8.2 API Interface

```python
api = CLIMADAInterface()

# Get hazard data for a location
data = api.get_hazard_data(
    hazard=HazardType.TROPICAL_CYCLONE,
    location=LocationQuery(37.4404, 129.1671, name="Samcheok"),
    start_year=1980,
    end_year=2023,
)

# Calculate projected risk
result = api.calculate_projected_risk(
    hazard=HazardType.TROPICAL_CYCLONE,
    location=KOREA_LOCATIONS["samcheok"],
    year=2050,
    rcp="RCP8.5",
)
```

### 8.3 Fallback Strategy

1. **Cache**: Check local cache (30-day expiry)
2. **CLIMADA API**: Fetch from CLIMADA if installed
3. **Literature**: Use baseline values from CSV if CLIMADA unavailable

---

## 9. Financial Module Integration

### 9.1 Integration Points

The Physical Risk Model connects to financial modules via:

```python
# In stress_test.py
class ClimateStressTest:
    def set_physical_risk_model(self, model: PhysicalRiskModel):
        self._physical_risk_model = model

    def get_baseline_physical_risk(self, asset_id, year, scenario):
        if self._physical_risk_model:
            result = self._physical_risk_model.calculate(year=year, scenario_name=scenario)
            return result.value * 100  # Convert to percentage

# In cddm.py
class ClimateDiscountModel:
    def set_physical_risk_model(self, model: PhysicalRiskModel):
        self._physical_risk_model = model

    def get_physical_risk(self, year, scenario):
        if self._physical_risk_model:
            result = self._physical_risk_model.calculate(year=year, scenario_name=scenario)
            return result.value * 100
```

### 9.2 Data Flow to Financial Modules

```
PhysicalRiskModel.calculate()
         ↓
    RiskResult
    ├── value: 0.0255 (2.55%)
    ├── components: {wildfire, tc, flood, drought, heat_stress...}
    └── scenario: "RCP8.5"
         ↓
┌────────────────┴────────────────┐
│                                 │
ClimateStressTest            ClimateDiscountModel
├── stressed_risk              ├── climate_risk_premium
├── VaR calculations           ├── cash_flow_projections
└── rating_impact              └── equity_value_impact
```

---

## 10. Model Outputs

### 10.1 RiskResult Structure

```python
@dataclass
class RiskResult:
    risk_type: RiskType.PHYSICAL
    value: float                    # Total physical risk (0.0255 = 2.55%)
    unit: str                       # "fraction"
    year: int                       # 2050
    scenario: str                   # "RCP8.5"
    components: {
        # Acute hazards
        "wildfire_outage": 0.000068,
        "tc_outage": 0.0000605,
        "river_flood_outage": 0.0,
        "coastal_flood_outage": 0.0,
        "drought_derate": 0.007,
        "acute_total": 0.0071285,
        # Chronic hazards
        "temp_efficiency_loss": 0.0055,
        "heat_stress_loss": 0.0025,
        "slr_derate": 0.0,
        "chronic_total": 0.008,
        # Compound adjustment
        "compound_adjustment": 0.0025,
        # Confidence intervals
        "confidence_low": 0.018,
        "confidence_high": 0.035,
    }
    sources: ["CLIMADA...", "KMA...", "IPCC AR6..."]
    notes: "Location: Samcheok, RCP: RCP8.5"
```

### 10.2 Summary Table Example

| Year | Wildfire | TC | Drought | Heat | Total Acute | Temp Loss | Total Chronic | Total Risk |
|------|----------|----|---------| ---- |-------------|-----------|---------------|------------|
| 2024 | 0.003% | 0.006% | 0.50% | 0.10% | 0.61% | 0.10% | 0.25% | 0.96% |
| 2030 | 0.004% | 0.006% | 0.56% | 0.12% | 0.74% | 0.18% | 0.35% | 1.27% |
| 2050 | 0.007% | 0.007% | 0.70% | 0.25% | 0.96% | 0.55% | 0.80% | 2.55% |
| 2100 | 0.014% | 0.007% | 0.90% | 0.50% | 1.42% | 1.80% | 2.30% | 5.52% |

---

## 11. Known Limitations and Gaps

### 11.1 Data Limitations

| Issue | Description | Mitigation |
|-------|-------------|------------|
| **River/Coastal Flood = 0** | Plant at 10m elevation makes flood risk negligible | Verified against elevation data; residual risk only |
| **Limited Historical Events** | Only 15 calibration events in CSV | Supplemented with literature damage ratios |
| **Korea-specific Calibration** | Some functions use US/global parameters | Applied Korea Forest Service and KMA data where available |

### 11.2 Methodology Limitations

1. **Linear Climate Factor Interpolation**: Real climate change is non-linear; model uses linear interpolation between anchor years
2. **Gaussian Copula for Compound Events**: Simplified dependency structure; tail dependencies may be underestimated
3. **Static Vulnerability**: Assumes no adaptation over time; real plants may upgrade

### 11.3 Data Not Yet in CSV

The following data is still hardcoded and should be moved to CSV:

| File | Data | Priority |
|------|------|----------|
| `temperature.py` | Temperature projections (RCP4.5, RCP8.5) | Medium |
| `exposure.py` | Korean coal plant profiles | Medium |
| `damage_functions/*.py` | Function parameters | Low (per-function CSV) |

---

## 12. Usage Examples

### 12.1 Basic Physical Risk Calculation

```python
from src.models.physical import PhysicalRiskModel

# Initialize model
model = PhysicalRiskModel()
model.set_rcp("RCP8.5")
model.set_location_by_name("samcheok")

# Calculate for 2050
result = model.calculate(year=2050)

print(f"Total Physical Risk: {result.value * 100:.2f}%")
print(f"Acute Total: {result.components['acute_total'] * 100:.2f}%")
print(f"Chronic Total: {result.components['chronic_total'] * 100:.2f}%")
```

### 12.2 Hazard-Specific Analysis

```python
from src.models.physical import PhysicalRiskModel, HazardType

model = PhysicalRiskModel()
model.set_rcp("RCP8.5")

# Get detailed hazard information
detail = model.get_hazard_detail(HazardType.TROPICAL_CYCLONE, year=2050)

print(f"Hazard: {detail['hazard_type']}")
print(f"Climate Factor: {detail['projected']['climate_factor']:.2f}x")
print(f"Projected Outage Rate: {detail['projected']['outage_rate'] * 100:.4f}%")
```

### 12.3 Trajectory Analysis

```python
# Get risk trajectory from 2024 to 2100
trajectory = model.calculate_trajectory(
    start_year=2024,
    end_year=2100,
    scenario_name="RCP8.5",
)

for year, result in trajectory.items():
    if year % 10 == 0:  # Print every 10 years
        print(f"{year}: {result.value * 100:.2f}%")
```

### 12.4 Compound Risk Analysis

```python
from src.models.physical import CompoundRiskModel, CompoundEventType

model = CompoundRiskModel()

# Calculate specific compound event
result = model.calculate_compound_risk(
    event_type=CompoundEventType.DROUGHT_HEAT,
    year=2050,
    rcp="RCP8.5",
)

print(f"Event: {result.event_type.value}")
print(f"Base Impact: {result.base_impact * 100:.2f}%")
print(f"Compound Impact: {result.compound_impact * 100:.2f}%")
print(f"Amplification: {result.amplification_factor:.2f}x")
```

### 12.5 Integration with Financial Modules

```python
from src.models.physical import PhysicalRiskModel
from src.models.financial import ClimateStressTest, ScenarioType

# Create physical risk model
phys_model = PhysicalRiskModel()
phys_model.set_rcp("RCP8.5")
phys_model.set_location_by_name("samcheok")

# Wire to stress test
stress_test = ClimateStressTest()
stress_test.set_physical_risk_model(phys_model)

# Run stress test with dynamic physical risk
result = stress_test.run_asset_stress_test(
    asset_id="samcheok",
    baseline_value_usd=4.5e9,
    baseline_physical_risk_pct=None,  # Calculate dynamically
    scenario_type=ScenarioType.HOT_HOUSE,
    year=2050,
)

print(f"Stressed Physical Risk: {result.stressed_physical_risk_pct:.2f}%")
print(f"Expected Loss: ${result.expected_loss_usd / 1e6:.1f}M")
```

---

## 13. References

### 13.1 Primary Sources

1. **CLIMADA**: ETH Zurich Climate Adaptation Framework
   - https://climada-python.readthedocs.io/

2. **IPCC AR6**: Climate Change 2021 - Physical Science Basis
   - Chapter 4: Future Global Climate
   - Chapter 11: Weather and Climate Extreme Events

3. **KMA**: Korea Meteorological Administration
   - Climate Change Scenarios for Korea (2020)

### 13.2 Hazard-Specific Literature

| Hazard | Key Reference | Citation |
|--------|---------------|----------|
| Wildfire | Lüthi et al. (2021) | GMD 14:3337-3356 |
| Tropical Cyclone | Emanuel (2011) | Weather, Climate, and Society 3(4):261-268 |
| Flood | HAZUS-MH | FEMA Technical Manual |
| Drought | SPEI Global Drought Monitor | Vicente-Serrano et al. (2010) |
| Heat Stress | Maulbetsch & DiFilippo (2006) | California Energy Commission |
| Compound Events | Zscheischler et al. (2018) | Nature Climate Change 8:469-477 |

### 13.3 Korea-Specific Sources

1. Korea Forest Service - Wildfire statistics (2001-2023)
2. KHOA - Korea Hydrographic and Oceanographic Agency SST data
3. KEPCO - Korea Electric Power Corporation statistics
4. EPSIS - Electric Power Statistics Information System

---

## Appendix A: CSV File Schemas

### hazard_baselines.csv

```
hazard_type,base_frequency,base_intensity,intensity_unit,outage_rate,
capacity_derate,efficiency_loss,damage_ratio,confidence_low,confidence_high,
source,methodology,climada_events,climada_years
```

### climate_factors.csv

```
scenario,year,wildfire,tropical_cyclone,river_flood,coastal_flood,
drought,heat_stress,slr_meters,source
```

### compound_events.csv

```
event_type,hazard1,hazard2,correlation,amplification,joint_probability,source
```

---

## Appendix B: Validation Checklist

- [ ] Hazard baselines sum to reasonable total (~1% baseline)
- [ ] Climate factors increase monotonically with year
- [ ] RCP8.5 factors > RCP4.5 factors for all hazards
- [ ] Compound amplification factors > 1.0
- [ ] Temperature efficiency loss matches literature range
- [ ] Integration test: PhysicalRiskModel → Financial modules

---

*Document Version: 1.0*
*Last Updated: January 2026*
*Author: Climate Risk Model Team*

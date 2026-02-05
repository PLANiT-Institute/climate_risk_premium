# Risk Modeling Module Refactoring

## Overview

The risk modeling modules have been comprehensively refactored to improve maintainability, add comprehensive testing, and enhance documentation. The refactoring follows scientific computing best practices and creates modular, reusable components.

## New Architecture

### Core Infrastructure (`src/risk/core/`)

#### Types (`src/risk/core/types.py`)
- **Standardized data structures**: `RiskMetrics`, `PlantCharacteristics`, `ScenarioParameters`
- **Protocols**: `RiskModel` interface for consistent implementation patterns
- **Type aliases**: Clear, semantic typing for financial and risk metrics
- **Validation**: Structured approach to input validation

#### Utilities (`src/risk/core/utils.py`)
- **Financial calculations**: Probability of default, recovery rates, Credit VaR
- **Mathematical functions**: Interpolation, stress testing, confidence intervals
- **Validation utilities**: Input validation with detailed error reporting
- **Monte Carlo methods**: Rating migration simulation
- **Formatting utilities**: Consistent financial value formatting

### Enhanced Credit Rating (`src/risk/credit/`)

#### Rating Engine (`src/risk/credit/engine.py`)
- **Extended rating scale**: AAA to D with distressed ratings (CCC, CC, C, D)
- **Death spiral detection**: Early warning system for credit deterioration
- **Component-based assessment**: Modular rating factors with clear weighting
- **Climate risk integration**: Direct climate impact on credit ratings
- **Monte Carlo analysis**: Stochastic rating migration modeling

#### Key Features
1. **Death Spiral Detection**
   - Trend analysis across multiple metrics
   - Accelerating deterioration identification
   - Rating trajectory projection
   - Multiple deteriorating trend detection

2. **Climate Risk Integration**
   - Climate cost ratio assessment
   - Physical and transition risk scoring
   - Counterfactual baseline comparison
   - Climate-driven rating deterioration

3. **Enhanced Assessment**
   - Component-based rating with clear rationale
   - Critical metric override logic
   - Historical trend analysis
   - Confidence interval calculations

### Enhanced Physical Risk (`src/risk/physical/`)

#### Enhanced Engine (`src/risk/physical/enhanced_engine.py`)
- **Hazard modeling**: Comprehensive climate hazard intensity calculation
- **Exposure analysis**: Detailed asset exposure characteristics
- **Vulnerability assessment**: Sophisticated damage function modeling
- **Impact aggregation**: Multi-hazard impact combination
- **Mitigation effects**: Protection measure impact quantification

#### Hazard Types
- **Wildfire**: Fire risk based on location and climate conditions
- **Flood**: Flooding risk with elevation and proximity factors
- **Drought**: Water scarcity impact on power generation
- **Heat**: Temperature stress on equipment and efficiency
- **Water Scarcity**: Cooling water availability constraints

#### Damage Functions
- **Linear**: Proportional damage increase
- **Exponential**: Accelerating damage patterns
- **Logistic**: Gradual then rapid damage curves
- **Hazard-specific**: Tailored damage patterns per hazard type

## Testing Strategy

### Comprehensive Test Coverage

#### Credit Rating Tests (`tests/test_credit_rating_engine.py`)
- **15 test cases** covering all major functionality
- **Death spiral detection**: Multiple deterioration scenarios
- **Component rating**: Individual factor testing
- **Climate integration**: Climate impact validation
- **Edge cases**: Zero values, extreme scenarios

#### Physical Risk Tests (`tests/test_enhanced_physical_risk.py`)
- **21 test cases** covering hazard, exposure, and vulnerability
- **Hazard intensity**: All hazard type calculations
- **Damage functions**: Linear, exponential, logistic curves
- **Vulnerability assessment**: Impact calculation and aggregation
- **Time series**: Multi-year assessment validation

### Test Categories

#### Unit Tests
- Individual component functionality
- Mathematical calculations
- Data structure behavior
- Edge case handling

#### Integration Tests
- Component interaction validation
- End-to-end workflow testing
- Data flow verification
- System behavior validation

#### Property Tests
- Type safety validation
- Boundary condition testing
- Invariant property checking
- Consistency validation

## Key Improvements

### 1. Modular Architecture
- **Separation of concerns**: Clear boundaries between hazard, exposure, and vulnerability
- **Reusable components**: Modular design enables component reuse
- **Interface consistency**: Protocol-based design ensures consistency
- **Dependency injection**: Flexible component composition

### 2. Enhanced Documentation
- **Comprehensive docstrings**: All functions and classes documented
- **Type annotations**: Full type hint coverage for better IDE support
- **Usage examples**: Clear examples in documentation
- **Architecture documentation**: System design clearly explained

### 3. Scientific Computing Best Practices
- **Numerical stability**: Proper handling of edge cases and numerical precision
- **Validation**: Comprehensive input validation with detailed error messages
- **Testing**: High test coverage with both unit and integration tests
- **Versioning**: Model versioning for reproducibility

### 4. Climate Risk Integration
- **Death spiral modeling**: Early warning system for climate-induced credit deterioration
- **Physical risk quantification**: Detailed hazard modeling for power generation assets
- **Counterfactual analysis**: Proper baseline comparison for climate risk pricing
- **Time series analysis**: Multi-year impact projection

## Usage Examples

### Credit Rating Assessment
```python
from src.risk.credit.engine import assess_credit_rating, RatingMetrics
from src.risk.core import ScenarioParameters, RiskType

# Create rating metrics
metrics = RatingMetrics(
    capacity_mw=1000,
    ebitda_to_fixed_assets=8.0,
    ebitda_to_interest=4.0,
    net_debt_to_ebitda=5.0,
    debt_to_equity=180.0,
    debt_to_assets=65.0,
    dscr=1.4,
    climate_cost_ratio=0.3,
    physical_risk_score=0.7,
    transition_risk_score=0.6,
)

# Create climate scenario
scenario = ScenarioParameters(
    name="Moderate Climate Risk",
    risk_type=RiskType.COMPOUND,
    description="Combined physical and transition risks",
    severity_score=0.6,
)

# Assess credit rating with climate impact
assessment = assess_credit_rating(metrics, scenario=scenario)
print(f"Rating: {assessment.overall_rating}")
print(f"Climate Impact: {assessment.climate_notch_deterioration} notches")
```

### Physical Risk Assessment
```python
from src.risk.physical.enhanced_engine import get_enhanced_physical_risk_engine
from src.risk.physical.enhanced_engine import AssetExposure
from src.risk.core import PlantCharacteristics, ScenarioParameters

# Create plant characteristics
plant = PlantCharacteristics(
    capacity_mw=2100,
    plant_type="Coal",
    location="Samcheok",
    construction_cost_million=3200,
    base_capacity_factor=0.85,
    operating_years=40,
    efficiency_rate=0.40,
)

# Create asset exposure
exposure = AssetExposure(
    plant=plant,
    latitude=37.45,
    longitude=129.17,
    elevation_m=30,
    distance_to_coast_km=2,
    foundation_type="piled",
    cooling_system_type="once_through",
    protection_measures=["flood_wall"],
    water_requirements_m3_per_hour=15000,
)

# Create climate scenario
scenario = ScenarioParameters(
    name="Extreme Physical Risk",
    risk_type=RiskType.PHYSICAL,
    description="Extreme physical climate risks",
    severity_score=1.0,
    temperature_change_celsius=4.0,
)

# Assess physical risk
engine = get_enhanced_physical_risk_engine()
impact = engine.assess_physical_risk(plant, exposure, scenario, 2050)

print(f"Outage Probability: {impact.outage_probability:.1%}")
print(f"Capacity Derate: {impact.capacity_derate_fraction:.1%}")
print(f"Water Constraint: {impact.water_constraint_factor:.1%}")
```

### Time Series Analysis
```python
# Create time series assessment
time_series = engine.create_time_series_assessment(
    plant, exposure, scenario, 2024, 2060
)

for year, impact in time_series.items():
    if year % 10 == 0:  # Print every 10 years
        print(f"{year}: Outage {impact.outage_probability:.1%}, "
              f"Derate {impact.capacity_derate_fraction:.1%}")
```

## Performance Considerations

### Computational Efficiency
- **Vectorized operations**: Use NumPy for numerical calculations
- **Caching**: Expensive calculations cached where appropriate
- **Lazy evaluation**: Computation only when needed
- **Memory management**: Efficient data structures

### Scaling
- **Large portfolios**: Batch processing capabilities
- **Parallel processing**: Multi-hazard assessment parallelization
- **Database integration**: Efficient data loading and caching
- **API design**: RESTful interfaces for integration

## Validation and Quality Assurance

### Input Validation
- **Type checking**: Comprehensive type annotation and validation
- **Range validation**: Proper bounds checking for all inputs
- **Consistency validation**: Cross-parameter consistency checks
- **Error messages**: Clear, actionable error reporting

### Model Validation
- **Backtesting**: Historical validation against known outcomes
- **Sensitivity analysis**: Parameter impact assessment
- **Stress testing**: Extreme scenario validation
- **Cross-validation**: Model performance verification

## Future Enhancements

### Planned Improvements
1. **Enhanced hazard models**: Higher resolution climate data integration
2. **Machine learning**: Advanced pattern recognition for early warning
3. **Geographic information systems**: Spatial hazard modeling
4. **Real-time data**: Live hazard monitoring integration

### Extensions
1. **Multi-asset portfolio**: Portfolio-level risk assessment
2. **Supply chain modeling**: Vendor and supplier risk integration
3. **Regulatory compliance**: Automated regulatory reporting
4. **Climate scenario integration**: IPCC scenario pathway modeling

## Conclusion

The refactored risk modeling modules provide a robust, maintainable, and extensible foundation for climate risk assessment. The modular architecture enables easy extension and modification, while comprehensive testing ensures reliability. The enhanced documentation and type annotations improve developer experience and reduce maintenance costs.

The new architecture follows scientific computing best practices and provides clear separation of concerns, making the system more maintainable and extensible for future enhancements.
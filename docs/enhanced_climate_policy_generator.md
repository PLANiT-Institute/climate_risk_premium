# Enhanced Climate Policy Scenario Generator

This comprehensive system provides real-time Korean energy policy monitoring and dynamic climate scenario generation with automatic financial model integration.

## Overview

The Enhanced Climate Policy Scenario Generator integrates the latest Korean energy policy announcements with financial risk models to provide:

- **Real-time Policy Monitoring**: Automated monitoring of Korean government sources (MOTIE, Climate Ministry)
- **Dynamic Scenario Generation**: Scenario creation based on latest policy announcements
- **Financial Impact Assessment**: Automatic integration with transition risk models
- **Scenario Validation**: Comprehensive validation of scenario consistency and feasibility
- **Interactive Dashboard**: Streamlit-based interface for analysis and visualization

## Latest Korean Policy Integration (2025-2026)

### Key Policy Announcements

1. **COP30 Powering Past Coal Alliance (Nov 17, 2025)**
   - Korea joins PPCA, committing to phase out 40 coal plants by 2040
   - No new unabated coal plants
   - High impact transformational policy

2. **100 GW Renewable Target (Dec 17, 2025)**
   - Accelerated renewable deployment to 100 GW by 2030
   - Part of comprehensive green transformation (K-GX)
   - Transformational impact on energy mix

3. **Industrial Green Transition (K-GX)**
   - Comprehensive industrial decarbonization strategy
   - Links to manufacturing and industrial policy
   - Medium to high impact level

## Components

### 1. Enhanced Climate Policy Generator
**File**: `src/scenarios/enhanced_climate_policy_generator.py`

Main orchestrator that:
- Integrates policy announcements into scenarios
- Provides scenario validation and financial impact assessment
- Maintains scenario cache and updates
- Offers comprehensive scenario comparison tools

**Key Classes**:
- `PolicyAnnouncement`: Structured policy data
- `ScenarioValidation`: Validation results and scoring
- `FinancialImpact`: Comprehensive financial impact assessment
- `EnhancedScenarioGenerator`: Main scenario generation engine

### 2. Korean Policy Monitor
**File**: `src/scenarios/korean_policy_monitor.py`

Automated monitoring system that:
- Continuously monitors Korean government sources
- Parses and classifies policy announcements
- Extracts quantitative metrics from policy text
- Provides real-time policy feed

**Key Classes**:
- `PolicyParser`: Text analysis and classification
- `AutomatedPolicyMonitor`: Source monitoring and announcement extraction
- `PolicySource`: Configuration for monitoring sources

### 3. Interactive Dashboard
**File**: `src/scenarios/policy_dashboard.py`

Streamlit-based interface providing:
- Real-time policy feed visualization
- Interactive scenario builder
- Financial impact analysis
- Scenario comparison tools
- Export capabilities

## Usage

### Quick Start

```python
from src.scenarios.enhanced_climate_policy_generator import EnhancedScenarioGenerator

# Initialize generator
generator = EnhancedScenarioGenerator()

# Generate scenario from latest policies
latest_policies = generator.get_latest_policies()
combined_scenario = generator.generate_scenario(
    name="latest_policy_combined_2026",
    policy_combination=latest_policies[:2],
    description="Combined scenario from latest COP30 and renewable announcements"
)

# Assess financial impact
impact = generator.assess_financial_impact(combined_scenario.name)
print(f"NPV impact: {impact.npv_change_pct:.1f}%")
```

### Running the Dashboard

```bash
streamlit run src/scenarios/policy_dashboard.py
```

The dashboard provides five main sections:

1. **📰 Policy Feed**: Real-time policy announcements
2. **🔧 Scenario Builder**: Create custom scenarios from policy combinations
3. **💰 Financial Impact**: Analyze financial consequences
4. **📈 Comparison**: Compare multiple scenarios
5. **📤 Export**: Export results and scenarios

### Advanced Usage

#### Custom Policy Monitoring

```python
from src.scenarios.korean_policy_monitor import AutomatedPolicyMonitor, PolicyType

# Initialize monitor
monitor = AutomatedPolicyMonitor()

# Subscribe to policy updates
def handle_new_policy(policy):
    print(f"New policy: {policy.title}")
    # Trigger scenario updates, alerts, etc.

monitor.subscribe(handle_new_policy)

# Start monitoring (in production)
# monitor.start_monitoring()

# Manual check
new_policies = monitor.manual_check()
```

#### Scenario Validation

```python
# Validate scenario consistency and feasibility
validation = generator.validate_scenario(scenario)

print(f"Overall score: {validation.overall_score:.2f}")
print(f"Is valid: {validation.is_valid}")
print(f"Issues: {validation.issues}")
print(f"Recommendations: {validation.recommendations}")
```

## Configuration

### Policy Sources

Edit `config/automated_monitor.json` to configure monitoring sources:

```json
{
  "sources": [
    {
      "name": "MOTIE",
      "url": "https://www.motie.go.kr/motie/ne/nes2/nes2131/nes213101.jsp",
      "source_type": "government",
      "update_frequency_hours": 12,
      "selectors": ["press", "policy", "announcement"]
    }
  ],
  "monitoring": {
    "enabled": true,
    "check_interval_minutes": 60,
    "max_retries": 3,
    "timeout_seconds": 30
  }
}
```

### Financial Parameters

Default financial parameters can be adjusted in the dashboard or by passing parameters to `assess_financial_impact()`:

```python
impact = generator.assess_financial_impact(
    scenario_name="my_scenario",
    capacity_mw=1000,        # Plant capacity in MW
    baseline_cf=0.85,        # Baseline capacity factor
    discount_rate=0.08,      # Discount rate
    power_price=100,         # Power price in $/MWh
    analysis_years=30        # Analysis period in years
)
```

## Data Sources

### Korean Government Sources
- **MOTIE** (Ministry of Trade, Industry and Energy)
- **Climate Ministry** (Ministry of Climate, Energy and Environment)
- **Korea Power Exchange** (KPX)
- **Official government announcements**

### International Commitments
- **Powering Past Coal Alliance** (PPCA)
- **COP30 commitments**
- **UNFCCC reporting**

### News Sources
- **Korea Herald**
- **Korea Times**
- **Asia Economy Daily**

## Policy Classification System

### Policy Types
- **COAL_PHASE_OUT**: Coal plant retirement and phase-out policies
- **RENEWABLE_TARGET**: Renewable energy deployment targets
- **EMISSIONS_REDUCTION**: Emissions reduction commitments
- **NUCLEAR_EXPANSION**: Nuclear power expansion policies
- **CARBON_PRICING**: Carbon pricing and ETS policies
- **INDUSTRIAL_TRANSITION**: Industrial decarbonization policies
- **TECHNOLOGY_SPECIFIC**: Technology-specific policies (hydrogen, CCUS)

### Impact Levels
- **LOW**: Reviews, studies, considerations
- **MEDIUM**: Plans, targets, strategies
- **HIGH**: Commitments, pledges, agreements
- **TRANSFORMATIONAL**: Phase-outs, bans, mandatory requirements

## Integration with Existing Models

The enhanced generator seamlessly integrates with existing transition risk models:

```python
from src.models.transition.model import TransitionRiskModel

# Standard transition risk model still works
transition_model = TransitionRiskModel()
transition_model.set_power_plan("10th_basic_plan")
result = transition_model.calculate(year=2030, baseline_cf=0.85)

# Enhanced scenarios available
for scenario_name in generator.enhanced_scenarios:
    transition_model.set_power_plan(scenario_name)
    enhanced_result = transition_model.calculate(year=2030, baseline_cf=0.85)
```

## Financial Impact Metrics

The system provides comprehensive financial impact assessment:

### Key Metrics
- **NPV Change**: Net present value impact as percentage
- **Revenue Loss**: Cumulative revenue loss percentage
- **Cashflow Impact**: Year-by-year cashflow changes
- **Risk-Adjusted Return**: Risk-adjusted financial return
- **Break-even Year**: Year when cumulative losses equal initial investment
- **Sensitivity Bounds**: Range of possible outcomes

### Sensitivity Analysis

The system automatically calculates sensitivity bounds for key metrics based on:
- Policy implementation timing variations
- Confidence levels in policy announcements
- Economic parameter uncertainties

## Output and Export

### Scenario Export
Scenarios can be exported in JSON format including:
- Scenario parameters and trajectories
- Validation results
- Financial impact assessment
- Source policy information

```python
generator.export_scenario(
    scenario_name="my_scenario",
    output_path=Path("output/my_scenario.json"),
    include_validation=True,
    include_financial=True
)
```

### Comparison Export
Scenario comparisons can be exported as CSV for further analysis.

### Policy Feed Export
Policy announcements can be exported with full metadata and metrics.

## Technical Architecture

### Dependencies
- `pandas` for data manipulation
- `numpy` for numerical calculations
- `plotly` for visualizations
- `streamlit` for dashboard
- `requests` for web scraping
- `beautifulsoup4` for HTML parsing
- `feedparser` for RSS feeds

### Data Flow
1. **Policy Monitoring**: Automated source monitoring → Policy parsing → Structured announcements
2. **Scenario Generation**: Policy combination → Trajectory calculation → Scenario creation
3. **Validation**: Consistency checks → Feasibility analysis → Confidence scoring
4. **Financial Analysis**: Cashflow modeling → NPV calculation → Sensitivity analysis
5. **Visualization**: Dashboard updates → Charts → Export

### Caching
- Scenario validation results cached for performance
- Financial impact calculations cached
- Policy announcements stored locally

## Error Handling and Logging

The system includes comprehensive error handling:
- Graceful degradation when sources are unavailable
- Validation of policy parsing results
- Fallback scenarios for missing data
- Detailed logging for debugging

## Security Considerations

- API keys stored securely in configuration
- Rate limiting implemented for source requests
- Input validation for all user inputs
- Error messages sanitized for security

## Future Enhancements

Planned improvements include:
- Machine learning for policy impact prediction
- Integration with international policy databases
- Advanced sensitivity analysis techniques
- Real-time alert system for critical policy changes
- API endpoints for external integration

## Troubleshooting

### Common Issues

1. **No policy announcements found**
   - Check network connectivity
   - Verify source URLs are accessible
   - Review source configuration

2. **Scenario validation fails**
   - Check policy data completeness
   - Verify trajectory calculations
   - Review confidence levels

3. **Financial impact calculation errors**
   - Validate financial parameters
   - Check scenario dispatch trajectories
   - Review discount rate and time periods

### Debug Mode

Enable debug logging by setting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

To contribute new features:

1. Add new policy sources to configuration
2. Extend policy parser for new policy types
3. Enhance validation rules as needed
4. Update dashboard components
5. Add comprehensive tests

## License

This system is part of the risk premium analysis project and follows the same licensing terms.
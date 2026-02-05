# Physical → Financial Risk Translation: 10-Step Implementation Plan

> **Based on**: Literature Review (2025-01-05)
> **Goal**: Professional-grade physical-to-financial risk translation for Korean coal plants

---

## Executive Summary

Your literature review identifies the critical insight:

```
Financial Loss = Hazard × Exposure × Vulnerability
```

**Current State**: Model calculates physical risk (CF reduction: 2.55% for RCP8.5 2050)
**Gap**: Missing formal financial risk translation with calibrated damage functions

---

## 10-Step Implementation Plan

### Step 1: Implement CLIMADA-Style Sigmoid Damage Functions

**Rationale**: Lüthi et al. (2021) demonstrates that sigmoid functions better capture non-linear damage relationships.

**Current**: Linear damage functions
**Target**: Emanuel (2011) sigmoid function

```python
# From your review - CLIMADA wildfire damage function
def sigmoid_damage(intensity, i_half, threshold=295):
    """
    f(i) = i³ / (1 + i³)

    Where:
        i = (intensity - threshold) / i_half
        i_half = intensity at 50% damage (calibration parameter)
    """
    if intensity < threshold:
        return 0.0
    i = (intensity - threshold) / i_half
    return (i ** 3) / (1 + i ** 3)
```

**Implementation**:
- Add `SigmoidDamageFunction` base class
- Implement for wildfire, flood, cyclone
- Calibrate i_half parameters using Korean historical data

**Files to modify**:
- `src/models/physical/damage_functions/base.py`
- `src/models/physical/damage_functions/wildfire.py`

---

### Step 2: Add Asset-Level Financial Exposure Module

**Rationale**: Bressan et al. (2024) shows 70% underestimation without asset-level data.

**Current**: Single plant exposure (SAMCHEOK_BLUE_POWER)
**Target**: Full Korean coal fleet with detailed financials

```python
@dataclass
class AssetLevelExposure:
    """Following Bressan et al. (2024) 5-step methodology."""

    # Step 1: Asset database
    plant_id: str
    asset_value_usd: float           # Replacement cost
    book_value_usd: float            # Accounting value
    insured_value_usd: float         # Insurance coverage
    revenue_per_mwh: float           # $/MWh

    # Ownership chain
    parent_company: str
    ultimate_owner: str
    listed_exchange: str             # KRX, etc.

    # Financial exposure
    debt_outstanding_usd: float
    debt_maturity_years: float
    interest_rate: float
    credit_rating: str               # Moody's/S&P

    # Insurance
    property_coverage_usd: float
    business_interruption_days: int
    deductible_usd: float
```

**Files to create**:
- `src/models/financial/asset_exposure.py`
- `data/physical_risk_inputs/korean_coal_financials.csv`

---

### Step 3: Implement Climate VaR Calculation

**Rationale**: Bressan et al. shows 82% underestimation of tail risk without proper VaR.

**Target**: Climate Value-at-Risk following industry standards

```python
@dataclass
class ClimateVaR:
    """Climate Value-at-Risk calculation."""

    # VaR metrics
    expected_annual_loss: float      # AAL
    var_95: float                    # 1-in-20 year loss
    var_99: float                    # 1-in-100 year loss
    tail_var_99: float               # Expected shortfall

    # Time horizons
    horizon_years: int
    discount_rate: float
    npv_expected_loss: float

    def calculate(
        self,
        exposure: AssetLevelExposure,
        hazard_distribution: Distribution,
        damage_function: DamageFunction,
    ) -> "ClimateVaR":
        """
        Monte Carlo simulation of climate losses.

        1. Sample N hazard events from distribution
        2. Apply damage function to each
        3. Calculate loss distribution
        4. Extract VaR percentiles
        """
        pass
```

**Files to create**:
- `src/models/financial/climate_var.py`

---

### Step 4: Add Power Generation Loss Model (WRI-EBRD Style)

**Rationale**: WRI-EBRD methodology shows coal plants lose 1.7% generation vs 0.8% for CCGT.

**Current**: Efficiency loss only
**Target**: Full generation loss cascade

```python
@dataclass
class GenerationLossModel:
    """
    WRI-EBRD Power Generation Loss Model.

    Loss drivers:
    1. Water stress → Cooling water shortage
    2. Water temperature → Cooling efficiency
    3. Air temperature → Thermal efficiency
    4. Drought → Forced outage
    """

    # From WRI-EBRD Table
    LOSS_FACTORS = {
        "coal": {
            "water_stress_2030": 0.017,    # 1.7%
            "water_stress_2040": 0.024,    # 2.4%
            "temperature_per_c": 0.003,    # 0.3%/°C
        },
        "ccgt": {
            "water_stress_2030": 0.008,    # 0.8%
            "water_stress_2040": 0.011,    # 1.1%
            "temperature_per_c": 0.002,    # 0.2%/°C
        },
    }

    def calculate_generation_loss(
        self,
        plant_type: str,
        year: int,
        scenario: str,
        water_stress_index: float,
        temp_anomaly_c: float,
    ) -> float:
        """Calculate TWh generation loss."""
        pass
```

**Key insight from WRI**: Coal plants are 2× more vulnerable than CCGT to climate.

---

### Step 5: Implement Transmission Channel Framework (NGFS/Basel)

**Rationale**: Your review identifies NGFS transmission channels as the standard framework.

```python
class TransmissionChannel(Enum):
    """NGFS/Basel physical risk transmission channels."""

    # Direct channels
    ASSET_DAMAGE = "asset_damage"           # Physical destruction
    BUSINESS_INTERRUPTION = "business_interruption"
    SUPPLY_CHAIN = "supply_chain_disruption"

    # Indirect channels
    MARKET_PRICE = "market_price_change"    # Electricity price
    DEMAND_SHIFT = "demand_pattern_shift"
    REGULATORY = "regulatory_response"

    # Systemic channels
    CREDIT_CONTAGION = "credit_contagion"
    INSURANCE_REPRICING = "insurance_repricing"
    STRANDED_ASSETS = "stranded_assets"


@dataclass
class ChannelImpact:
    """Impact through a specific transmission channel."""
    channel: TransmissionChannel
    probability: float
    severity_usd: float
    time_to_materialize_years: float
    reversibility: str  # "permanent", "temporary", "partial"
```

---

### Step 6: Add Calibration Module with Korean Historical Data

**Rationale**: CLIMADA achieves 63% of events within one order of magnitude through calibration.

**Target**: Calibrate damage functions using Korean disaster data

```python
class DamageFunctionCalibrator:
    """
    Calibrate damage functions using historical data.

    Data sources (Korean):
    - NDMS (National Disaster Management System)
    - Korean Re insurance claims
    - KEPCO outage records
    - KMA extreme weather database
    """

    def __init__(self):
        self.historical_events = []
        self.observed_losses = []

    def load_korean_data(self):
        """Load Korean disaster/loss data."""
        # Typhoons: MABIS, RUSA, MAEMI, HINNAMNOR
        # Floods: 2020 Central region floods
        # Fires: 2019 Gangwon wildfires
        pass

    def calibrate(
        self,
        damage_function: DamageFunction,
        metric: str = "RMSF",  # Root Mean Square Fraction
    ) -> Dict[str, float]:
        """
        Optimize damage function parameters.

        Returns calibrated parameters.
        """
        pass

    def validate(
        self,
        damage_function: DamageFunction,
        holdout_events: List,
    ) -> Dict[str, float]:
        """
        Validate on held-out events.

        Returns:
            - RMSF: Root Mean Square Fraction
            - MAE: Mean Absolute Error
            - Within-1-order: % of events within 1 order of magnitude
        """
        pass
```

**Data files to create**:
- `data/calibration/korean_typhoons.csv`
- `data/calibration/korean_floods.csv`
- `data/calibration/korean_wildfires.csv`
- `data/calibration/kepco_outages.csv`

---

### Step 7: Implement Financial Impact Cascade (CDDM)

**Rationale**: Bressan et al. uses Climate Dividend Discount Model for equity valuation.

```python
class ClimateDiscountModel:
    """
    Climate Dividend Discount Model (CDDM).

    Connects physical risk → corporate performance → security value.

    From Bressan et al. (2024):
    - Physical damage → Reduced EBITDA
    - Generation loss → Revenue reduction
    - Repair costs → CapEx increase
    - Insurance → Premium/deductible changes
    """

    def calculate_equity_impact(
        self,
        physical_risk_result: PhysicalRiskComponents,
        company_financials: CompanyFinancials,
        discount_rate: float = 0.08,
        horizon_years: int = 30,
    ) -> EquityImpact:
        """
        Calculate equity value adjustment from climate risk.

        Returns:
            - baseline_equity_value
            - climate_adjusted_equity_value
            - climate_risk_discount (%)
            - var_95_equity_loss
        """

        # 1. Project physical impacts over horizon
        annual_generation_loss = []
        annual_repair_costs = []
        annual_insurance_costs = []

        # 2. Calculate annual cash flow impacts
        annual_ebitda_impact = []

        # 3. Discount to present value
        npv_climate_loss = sum(
            impact / (1 + discount_rate) ** year
            for year, impact in enumerate(annual_ebitda_impact)
        )

        # 4. Calculate equity value reduction
        climate_risk_discount = npv_climate_loss / company_financials.market_cap

        return EquityImpact(...)
```

---

### Step 8: Add Credit Risk Translation Module

**Rationale**: Your review highlights credit risk as key transmission channel.

```python
class ClimateCredit RiskModel:
    """
    Translate physical risk to credit metrics.

    Key relationships:
    - Physical damage → DSCR reduction → Default probability
    - Generation loss → Revenue → Interest coverage
    - Asset impairment → Collateral value → LGD
    """

    # Physical risk → DSCR impact
    DSCR_SENSITIVITY = {
        "coal_plant": {
            "per_1pct_cf_reduction": -0.015,  # -1.5% DSCR per 1% CF loss
            "per_1pct_asset_damage": -0.020,  # -2% DSCR per 1% asset loss
        },
    }

    # DSCR → Credit spread (from rating agencies)
    DSCR_SPREAD_CURVE = {
        2.0: 50,    # bps
        1.5: 100,
        1.2: 200,
        1.0: 400,
        0.8: 800,
    }

    def calculate_credit_impact(
        self,
        physical_risk: PhysicalRiskComponents,
        baseline_dscr: float,
        baseline_spread_bps: float,
    ) -> CreditImpact:
        """
        Calculate credit spread adjustment from physical risk.

        Returns:
            - adjusted_dscr
            - adjusted_spread_bps
            - implied_pd_change
            - rating_notches_impact
        """
        pass
```

---

### Step 9: Build Scenario Stress Testing Framework

**Rationale**: WRI notes only 25% of banks do physical risk scenario analysis.

```python
class ClimateStressTest:
    """
    Regulatory-grade climate stress testing.

    Aligns with:
    - BOK climate stress test guidelines
    - ECB climate stress test methodology
    - NGFS scenario framework
    """

    SCENARIOS = {
        "orderly": {
            "description": "Early, smooth transition",
            "physical_risk_multiplier": 1.0,
            "transition_risk_multiplier": 1.0,
        },
        "disorderly": {
            "description": "Late, disruptive transition",
            "physical_risk_multiplier": 1.2,
            "transition_risk_multiplier": 1.5,
        },
        "hot_house": {
            "description": "No transition, high physical risk",
            "physical_risk_multiplier": 2.0,
            "transition_risk_multiplier": 0.3,
        },
        "current_policies": {
            "description": "Current policies continue",
            "physical_risk_multiplier": 1.5,
            "transition_risk_multiplier": 0.8,
        },
    }

    def run_stress_test(
        self,
        portfolio: List[AssetLevelExposure],
        scenario: str,
        horizon_years: int = 30,
    ) -> StressTestResult:
        """
        Run full stress test on portfolio.

        Returns:
            - portfolio_var_95
            - portfolio_expected_loss
            - concentration_risk (by hazard, geography)
            - systemic_risk_contribution
        """
        pass
```

---

### Step 10: Create Integrated Financial Risk Dashboard

**Rationale**: Provide actionable outputs for financial decision-making.

```python
class PhysicalRiskFinancialDashboard:
    """
    Integrated dashboard connecting physical → financial risk.

    Outputs:
    1. Asset-level risk scores
    2. Portfolio-level VaR
    3. Credit spread adjustments
    4. Insurance premium impacts
    5. Regulatory capital implications
    """

    def generate_report(
        self,
        portfolio: List[AssetLevelExposure],
        scenario: str,
        year: int,
    ) -> FinancialRiskReport:
        """
        Generate comprehensive financial risk report.

        Sections:
        1. Executive Summary
        2. Physical Risk Assessment
        3. Financial Impact Analysis
        4. Credit Risk Implications
        5. Stress Test Results
        6. Recommendations
        """

        # Run all models
        physical_results = self.physical_model.calculate_portfolio(portfolio, year, scenario)
        var_results = self.var_model.calculate(portfolio, physical_results)
        credit_results = self.credit_model.calculate(portfolio, physical_results)
        stress_results = self.stress_test.run(portfolio, scenario)

        return FinancialRiskReport(
            # Summary metrics
            portfolio_var_95=var_results.var_95,
            expected_annual_loss=var_results.expected_annual_loss,
            credit_spread_impact_bps=credit_results.spread_adjustment,

            # Detailed breakdowns
            by_asset=...,
            by_hazard=...,
            by_transmission_channel=...,

            # Recommendations
            hedging_strategies=...,
            adaptation_investments=...,
            portfolio_rebalancing=...,
        )
```

---

## Implementation Priority

| Step | Priority | Complexity | Value |
|------|----------|------------|-------|
| 1. Sigmoid damage functions | HIGH | Medium | Foundation for accurate loss estimation |
| 2. Asset-level exposure | HIGH | Low | 70% accuracy improvement |
| 3. Climate VaR | HIGH | High | Industry-standard risk metric |
| 4. Generation loss model | MEDIUM | Medium | Power sector specific |
| 5. Transmission channels | MEDIUM | Low | Conceptual framework |
| 6. Calibration module | HIGH | High | Validation and credibility |
| 7. CDDM equity model | MEDIUM | High | Investor-focused output |
| 8. Credit risk translation | HIGH | Medium | Lender-focused output |
| 9. Stress testing | MEDIUM | Medium | Regulatory alignment |
| 10. Dashboard | LOW | Medium | User interface |

---

## Key Data Requirements

### Korean-Specific Data Needed

| Data Type | Source | Purpose |
|-----------|--------|---------|
| Historical typhoon damages | NDMS, Korean Re | Calibration |
| Flood event losses | MOLIT | Calibration |
| Wildfire damages | KFS | Calibration |
| KEPCO outage records | KEPCO | Power-specific calibration |
| Plant financial data | DART, annual reports | Asset exposure |
| Insurance premiums | Korean Re | Insurance module |
| Credit ratings history | KIS, NICE | Credit model |

### Literature Parameters to Implement

From your review:
- **WRI-EBRD**: Coal 1.7% loss, CCGT 0.8% loss
- **CLIMADA**: Sigmoid i_half calibration
- **Bressan**: 70% asset-level impact, 82% tail risk
- **WRI Yunnan**: $136-255M annual agricultural loss from wildfire
- **Aqueduct**: $535B urban flood damage by 2030

---

## Expected Outcomes

After implementing all 10 steps:

| Metric | Current | Target |
|--------|---------|--------|
| Physical risk output | CF reduction (%) | + VaR, credit spread, equity impact |
| Asset granularity | 1 plant | Full Korean coal fleet (8+ plants) |
| Damage function accuracy | Linear | Calibrated sigmoid (63% within 1 order) |
| Financial metrics | None | VaR, DSCR impact, spread adjustment |
| Validation | None | Historical calibration |
| Stress testing | None | NGFS-aligned scenarios |

---

## References (from your review)

1. Lüthi et al. (2021) - CLIMADA wildfire, GMD
2. Bressan et al. (2024) - Asset-level assessment, Nature Communications
3. WRI-EBRD (2021) - Power portfolio assessment
4. NGFS (2023) - Climate scenarios
5. Emanuel (2011) - Sigmoid damage function

---

*Plan created: 2025-01-05*
*Based on: Literature review of physical→financial risk methodologies*

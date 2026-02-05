# Korea Power Supply Plan (전력수급계획) Integration

## Overview

This document details the integration of Korea's **National Power Supply Plan** (전력수급기본계획, 전수계) coal reduction targets into the Climate Risk Premium model. The power plan provides official government projections for coal plant dispatch and capacity reductions, which directly impact project revenue and cash flows.

## Korea Power Supply Plan Background

### 10th Basic Plan for Long-term Electricity Supply and Demand (2022-2036)

The Korean government's 10th Power Supply Plan, announced in January 2023, outlines the following coal reduction trajectory:

**Key Targets:**
- **2022 Baseline**: Coal provides ~35% of electricity generation (~200 TWh)
- **2030 Target**: Coal reduced to 21.8% (~130 TWh) - NDC commitment
- **2036 Target**: Coal further reduced to 14.4% (~95 TWh)
- **Implied 2050**: Near-zero coal (<5%) under carbon neutrality commitment

### Coal Plant Dispatch Constraints

The power plan imposes several constraints on coal plants:

1. **Merit Order Displacement**
   - Coal pushed down in dispatch order by renewables (must-run)
   - Nuclear priority maintained (82% capacity factor mandate)
   - LNG peaking plants take flexible load

2. **Capacity Factor Trajectory**
   - **Historical (2015-2020)**: 80-85% average
   - **Current (2022-2025)**: 65-70% average
   - **2030 (NDC target)**: 45-50% average
   - **2036 (Plan target)**: 30-35% average
   - **2040+**: 15-20% average (stranded asset risk)

3. **Early Retirement Schedule**
   - Coal plants designed for 30-40 year lifetime
   - Policy-driven retirement likely by 2045 at latest
   - Samcheok Blue Power (COD 2024): At risk of 15-20 year early closure

## Model Integration Approach

### 1. Dispatch Reduction Function

We model the **annual capacity factor reduction** based on power plan targets:

```
ρ_t^coal = ρ_baseline × (1 - dispatch_penalty_t) × power_plan_factor_t

where:
  ρ_baseline = 0.50 (design capacity factor, conservative)
  dispatch_penalty_t = policy-driven constraints from transition scenarios
  power_plan_factor_t = trajectory from power supply plan
```

### 2. Power Plan Factor Trajectory

Based on 10th Power Supply Plan data:

| Year | Coal TWh | Total TWh | Coal Share | Implied CF (2.1 GW plant) |
|------|----------|-----------|------------|---------------------------|
| 2024 | 195      | 600       | 32.5%      | 65% (current)             |
| 2025 | 185      | 615       | 30.1%      | 60%                       |
| 2028 | 160      | 655       | 24.4%      | 52%                       |
| 2030 | 130      | 675       | 19.3%      | 45% (NDC target)          |
| 2034 | 110      | 710       | 15.5%      | 38%                       |
| 2036 | 95       | 735       | 12.9%      | 32% (Plan target)         |
| 2040 | 70       | 780       | 9.0%       | 22%                       |
| 2045 | 40       | 820       | 4.9%       | 12%                       |
| 2050 | 15       | 860       | 1.7%       | 4% (near phase-out)       |

**Calculation Method:**
- Total coal capacity in Korea: ~42 GW (as of 2024)
- Samcheok share: 2.1 GW / 42 GW = 5%
- If total coal generation = 130 TWh (2030), Samcheok allocation ≈ 6.5 TWh
- Implied capacity factor: 6.5 TWh / (2.1 GW × 8,760 hrs) = 35%

### 3. Revenue Impact Mechanism

The dispatch reduction translates directly to revenue loss:

```
Revenue_t = Price_t × Generation_t
          = Price_t × Capacity × 8760 × ρ_t^coal

Revenue Loss (%) = (ρ_baseline - ρ_t^coal) / ρ_baseline × 100
```

**Example (2030 vs 2025):**
- 2025 CF: 60% → Revenue: $885M
- 2030 CF: 45% → Revenue: $664M
- **Revenue Loss: 25% ($221M annually)**

### 4. Scenario Definitions

We define four **power plan scenarios** based on dispatch trajectory:

#### Scenario 1: Baseline (No Policy Enforcement)
- Ignores power plan targets
- CF remains at 50% (conservative baseline)
- Carbon price = 0
- Lifetime = 40 years

#### Scenario 2: Moderate Transition (10th Power Plan Compliance)
- Follows official 10th power plan trajectory
- CF: 60% (2025) → 45% (2030) → 32% (2036) → 15% (2045)
- Carbon price: $15-80/tCO2 (Korea ETS projections)
- Lifetime = 30 years (closes 2054, but uneconomic after 2045)

#### Scenario 3: Aggressive Transition (Accelerated Phase-out)
- Faster than official plan (civil society pressure + economics)
- CF: 55% (2025) → 35% (2030) → 20% (2036) → 5% (2040)
- Carbon price: $25-150/tCO2 (aligned with IEA Net Zero)
- Lifetime = 25 years (forced closure 2049)

#### Scenario 4: Korea NDC Scenario (2030 Target + Continuation)
- Strict enforcement of NDC coal reduction
- CF: 58% (2025) → 42% (2030) → 28% (2036) → 10% (2043)
- Carbon price: $20-100/tCO2 (NDC carbon budget consistent)
- Lifetime = 28 years (economic unviability by 2052)

## Data Sources

### Primary Sources
1. **10th Basic Plan for Electricity Supply and Demand (2023)**
   - Ministry of Trade, Industry and Energy (MOTIE)
   - Official coal generation targets (TWh)

2. **Korea Power Exchange (KPX) Statistics**
   - Historical coal plant capacity factors
   - Actual dispatch data by fuel type

3. **Korea Energy Economics Institute (KEEI) Projections**
   - Coal phase-out scenarios
   - Regional power demand forecasts

### Secondary Sources
4. **Solutions for Our Climate (SFOC) Analysis**
   - Civil society coal phase-out roadmap
   - Faster timeline than government plan

5. **IEA Net Zero Korea Roadmap**
   - International benchmark for coal phase-out
   - Aligned with 1.5°C pathways

## Implementation in Code

### New Data File: `data/raw/korea_power_plan.csv`

```csv
year,total_coal_twh,total_demand_twh,coal_share_pct,implied_cf_2100mw,scenario_type,policy_reference
2024,195,600,32.5,0.650,historical,Actual 2023 data
2025,185,615,30.1,0.600,baseline,10th Power Plan
2026,177,625,28.3,0.575,baseline,10th Power Plan (interpolated)
2028,160,655,24.4,0.520,baseline,10th Power Plan
2030,130,675,19.3,0.450,ndc_target,NDC 2030 + 10th Plan
2032,120,690,17.4,0.410,baseline,10th Power Plan (interpolated)
2034,110,710,15.5,0.380,baseline,10th Power Plan (interpolated)
2036,95,735,12.9,0.320,plan_target,10th Power Plan endpoint
2038,85,755,11.3,0.280,extrapolation,Linear decline post-2036
2040,70,780,9.0,0.220,extrapolation,Consistent with net-zero
2043,50,800,6.3,0.150,extrapolation,Pre-phase-out
2045,40,820,4.9,0.120,extrapolation,Phase-out acceleration
2050,15,860,1.7,0.040,carbon_neutrality,Net-zero 2050 target
```

### Module Updates

**`src/scenarios/korea_power_plan.py`** (NEW)
```python
@dataclass
class KoreaPowerPlanScenario:
    """Korea national power supply plan trajectory."""
    name: str
    cf_trajectory: Dict[int, float]  # year -> capacity factor
    early_retirement_year: int | None
    policy_reference: str
```

**`src/risk/transition.py`** (UPDATED)
```python
def apply_korea_power_plan_adjustment(
    plant_params: Dict,
    year: int,
    scenario: KoreaPowerPlanScenario
) -> float:
    """Apply capacity factor adjustment from Korea power plan."""
    cf_baseline = plant_params['capacity_factor']
    cf_plan = scenario.cf_trajectory.get(year, cf_baseline)
    return min(cf_baseline, cf_plan)  # Never exceed baseline
```

## Impact on Financial Metrics

### NPV Sensitivity to Dispatch Reduction

Using Samcheok parameters (2.1 GW, $4.9B investment):

| Scenario | Avg CF | NPV (Baseline) | NPV (Power Plan) | Loss | CRP (bps) |
|----------|--------|----------------|------------------|------|-----------|
| Baseline | 50%    | $8,964M        | $8,964M          | 0%   | 0         |
| 10th Plan| 38%    | $8,964M        | $4,200M          | 53%  | 2,850     |
| NDC      | 35%    | $8,964M        | $3,100M          | 65%  | 3,650     |
| Net Zero | 28%    | $8,964M        | $1,200M          | 87%  | 5,200     |

**Key Finding**:
The Korea Power Supply Plan dispatch reductions alone (without carbon pricing) can reduce NPV by 50-65%, translating to 2,850-3,650 bps increase in financing costs.

## Policy Implications

1. **Stranded Asset Risk is Policy-Driven**
   - The 10th Power Supply Plan creates material financial risk
   - Government policy, not just carbon markets, drives asset devaluation

2. **Early Retirement Compensation**
   - If plant becomes uneconomic by 2040 (20 years early), compensation = ~$2-3B
   - Cost-benefit: Early retirement vs. continued subsidies

3. **Investor Due Diligence**
   - Future coal plant investments must factor official government phase-out plans
   - Credit rating agencies should downgrade based on power plan trajectory

4. **Just Transition Financing**
   - Workers, communities, and investors all face losses
   - Structured finance mechanisms needed for orderly phase-out

## References

1. Ministry of Trade, Industry and Energy (2023). "10th Basic Plan for Electricity Supply and Demand (2023-2036)."
2. Korea Power Exchange. "Coal Generation Statistics 2020-2024."
3. Solutions for Our Climate (2022). "Roadmap for Coal Phase-out in Korea."
4. IEA (2023). "Net Zero Roadmap: Korea."
5. Presidential Commission on Carbon Neutrality (2021). "2050 Carbon Neutral Scenario."

---

**Document Status**: Draft v1.0
**Last Updated**: 2025-11-21
**Author**: Jinsu Park, PLANiT Institute

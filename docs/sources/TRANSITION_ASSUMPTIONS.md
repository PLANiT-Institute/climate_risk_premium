# Transition Risk Data Sources

This document provides full citations for carbon pricing and policy data.

## Carbon Pricing Scenarios

### 1. Korea ETS Current (`korea_ets_current` / `current_policy`)

**Description**: Korea ETS business-as-usual trajectory based on actual K-ETS market data.

| Year | Price (USD/tCO2) | Source |
|------|------------------|--------|
| 2024 | 8 | KRX market data (avg ~9,465 KRW/ton) |
| 2025 | 9 | Projection |
| 2030 | 25 | Government target |
| 2040 | 90 | Projection |
| 2050 | 120 | Projection |

**Sources**:
1. **Korea Exchange (KRX)**
   - Title: Korea ETS Market Data (배출권시장)
   - URL: https://ets.krx.co.kr/
   - Note: 2024 average KAU price ~9,465 KRW/ton

2. **Ministry of Environment (Korea)**
   - Title: Korea ETS Allocation Plan Phase 3 (2021-2025)

### 2. Korea ETS NDC-Aligned (`ndc_aligned`)

**Description**: NDC-aligned trajectory with stronger carbon pricing policy.

| Year | Price (USD/tCO2) | Source |
|------|------------------|--------|
| 2024 | 8 | KRX market data |
| 2030 | 50 | NDC target alignment |
| 2040 | 180 | Projection |
| 2050 | 250 | Target for carbon neutrality |

### 3. Korea ETS Net-Zero (`net_zero`)

**Description**: Aggressive pricing aligned with net-zero by 2050.

| Year | Price (USD/tCO2) | Source |
|------|------------------|--------|
| 2024 | 8 | KRX market data |
| 2030 | 80 | Accelerated target |
| 2040 | 330 | Projection |
| 2050 | 400 | Net-zero pricing |

### 4. IEA Net Zero 2050 (`iea_nze_2050`)

**Description**: IEA Net Zero Scenario for advanced economies.

| Year | Price (USD/tCO2) | Source |
|------|------------------|--------|
| 2030 | 130 | IEA NZE |
| 2050 | 250 | IEA NZE |

**Sources**:
1. **IEA (2023)**
   - Title: World Energy Outlook 2023
   - URL: https://www.iea.org/reports/world-energy-outlook-2023
   - Section: Net Zero Emissions Scenario

### 5. NGFS Scenarios

**Description**: Central bank climate scenarios.

| Scenario | 2030 | 2050 | Source |
|----------|------|------|--------|
| Orderly | 100 | 250 | NGFS 2023 |
| Disorderly | 30 | 350 | NGFS 2023 |
| Hot House | 10 | 20 | NGFS 2023 |

**Sources**:
1. **NGFS (2023)**
   - Title: NGFS Climate Scenarios
   - URL: https://www.ngfs.net/ngfs-scenarios-portal/

---

## Policy Scenarios

### 1. Korea 11th Basic Plan (`enhanced_11th_plan`)

**Description**: Official 11th Basic Plan for Electricity Supply and Demand (2024-2038).

| Year | Coal (GW) | Solar (GW) | Wind (GW) | Carbon-Free % |
|------|-----------|------------|-----------|----------------|
| 2024 | 26.7 | 25.0 | 1.7 | 38.2% |
| 2030 | 18.0 | 39.0 | 10.0 | 52.0% |
| 2038 | 3.6 | 77.2 | 40.7 | 72.5% |
| 2040 | 0.0 | 86.8 | 48.3 | 83.0% |

**Key Features**:
- 42% faster coal phase-out compared to 10th Plan
- Complete coal phase-out by 2040 (대통령 공약, special legislation pending)
- 72.5% carbon-free generation by 2038
- Nuclear expansion: 2 large units + 1 SMR (+6.4 GW total)

**Sources**:
1. **Ministry of Trade, Industry and Energy (2025)**
   - Title: 제11차 전력수급기본계획 (2024-2038)
   - English: 11th Basic Plan for Power Supply and Demand
   - Official Gazette: 산업통상자원부 공고 제2025-169호 (2025.2.21 확정)

### 2. Korea 10th Basic Plan (`korea_10th_plan`)

**Description**: Official Korea power supply plan (2022).

| Year | Dispatch Factor | Coal Share Target |
|------|-----------------|-------------------|
| 2024 | 1.00 | Current |
| 2030 | 0.70 | ~30% |
| 2050 | 0.00 | Phase-out |

**Sources**:
1. **Ministry of Trade, Industry and Energy (2022)**
   - Title: 제10차 전력수급기본계획
   - English: 10th Basic Plan for Power Supply
   - Year: December 2022

2. **Korea Electric Power Corporation (KEPCO)**
   - Title: Power Statistics
   - URL: https://home.kepco.co.kr/

### 3. Korea Accelerated (`korea_accelerated`)

**Description**: Accelerated phase-out (2040 target).

| Year | Dispatch Factor |
|------|-----------------|
| 2030 | 0.50 |
| 2040 | 0.00 |

**Sources**:
1. **2050 Carbon Neutrality Commission**
   - Scenario A: Accelerated transition

### 4. EU Taxonomy Aligned (`eu_taxonomy_aligned`)

**Description**: No financing for coal under EU rules.

**Sources**:
1. **EU Commission (2021)**
   - Title: EU Taxonomy Climate Delegated Act
   - URL: https://ec.europa.eu/sustainable-finance-taxonomy/

---

## Coal Phase-Out Timeline Sources

### Global Context

| Region | Phase-out Year | Source |
|--------|----------------|--------|
| EU | 2030 (most) | EU Green Deal |
| UK | 2024 | Net Zero Strategy |
| Korea | 2040 | Presidential Pledge (2040년 탈석탄) |
| Japan | 2030s | GX Strategy |
| China | 2060 | Net Zero Pledge |

### References

1. **Global Energy Monitor (2024)**
   - Title: Global Coal Plant Tracker
   - URL: https://globalenergymonitor.org/

2. **Climate Analytics (2023)**
   - Title: 1.5°C Coal Phase-out Dates
   - URL: https://climateanalytics.org/

3. **IEA (2023)**
   - Title: Coal 2023 Analysis and Forecast
   - URL: https://www.iea.org/reports/coal-2023

---

## K-ETS Carbon Price (enhanced_korea_power_plan.py)

K-ETS prices in the Enhanced module use KRW values converted at ~1,300 KRW/USD:

| Year | KRW/ton | USD/ton | Phase |
|------|---------|---------|-------|
| 2024 | 9,500 | ~7.3 | Phase 1 |
| 2025 | 11,000 | ~8.5 | Phase 1 |
| 2030 | 30,000 | ~23.1 | Phase 2 |
| 2038 | 58,000 | ~44.6 | Phase 3 |
| 2050 | 150,000 | ~115.4 | Phase 4 |

**Data Verification Note**: The 2024 base price of ~9,500 KRW/ton is validated against
KRX 배출권시장 (ets.krx.co.kr) 2024 annual average trading data for KAU (Korean Allowance Unit).
Previous model versions used $25-50/ton for 2024, which was 3-15x higher than actual market data.

---

## Methodology Notes

### Carbon Cost Calculation

```
Carbon Cost (USD/MWh) = Carbon Price (USD/tCO2) × Emissions Rate (tCO2/MWh)

For Samcheok: 0.85 tCO2/MWh (supercritical coal)
```

### Dispatch Factor Interpretation

- 1.0 = Full dispatch (baseline capacity factor)
- 0.7 = 70% of baseline (merit order effect)
- 0.0 = No dispatch (phase-out)

### Retirement Year Calculation

```python
remaining_life = min(natural_end, policy_retirement) - current_year
```

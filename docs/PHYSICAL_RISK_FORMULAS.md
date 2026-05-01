# Physical Risk — 산식 정리

## 데이터 소스 → 변환 → 캐시플로우 → CRP 전체 흐름

```
┌─────────────────────────────────────────────────────────────┐
│ 1단계: 데이터 소스 (실시간)                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [CLIMADA v6 — 산불]                                        │
│  NASA FIRMS 위성 → WildFire 객체 → Impact.calc()            │
│  출력: n_events, event_frequency, aai_agg(KRW)              │
│                                                             │
│  [OS-Climate PhysRisk — 가뭄]                               │
│  Container().get("get_asset_impact")                        │
│  출력: impact_mean, impact_std, impact_distribution          │
│                                                             │
│  [OS-Climate PhysRisk — 수자원]                              │
│  Container().get("get_asset_impact")                        │
│  출력: impact_mean, impact_std, impact_distribution          │
│                                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2단계: PLANiT Adapter 변환                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  산불 → outage_rate:                                        │
│  ┌─────────────────────────────────────────────────┐       │
│  │ outage_rate = freq × P_outage × (T_outage / T_year) │   │
│  │            = 1.0  × 0.10    × (24 / 8760)      │       │
│  │            = 0.000274 (0.027%)                   │       │
│  └─────────────────────────────────────────────────┘       │
│    freq = n_events / reference_years                        │
│    P_outage = 0.10 (산불 1건당 정전 확률)                     │
│    T_outage = 24h (정전 지속시간)                             │
│    T_year = 8,760h                                          │
│                                                             │
│  가뭄 → capacity_derate:                                    │
│  ┌─────────────────────────────────────────────────┐       │
│  │ capacity_derate = impact_mean × severity_scale  │        │
│  │                 = 0.008125  × 1.0               │        │
│  │                 = 0.81%                          │        │
│  └─────────────────────────────────────────────────┘       │
│                                                             │
│  수자원 → water_constrained_capacity:                       │
│  ┌─────────────────────────────────────────────────┐       │
│  │ water_cap = max(0, 1 - impact_mean)             │        │
│  │          = 1 - 0.00702                          │        │
│  │          = 0.993 (99.3%)                        │        │
│  └─────────────────────────────────────────────────┘       │
│                                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 3단계: 캐시플로우 적용 (매년 반복)                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ① CF 감소 (가뭄):                                          │
│     cf = base_cf × (1 - capacity_derate)                    │
│        = 0.85 × (1 - 0.0081) = 0.843                       │
│                                                             │
│  ② 수자원 상한 (hard cap):                                   │
│     cf = min(cf, water_cap)                                 │
│        = min(0.843, 0.993) = 0.843                          │
│                                                             │
│  ③ 잠재 발전량:                                              │
│     potential_MWh = MW × 8,760 × cf                         │
│                   = 2,100 × 8,760 × 0.843                   │
│                   = 15,510,948 MWh                           │
│                                                             │
│  ④ 실제 발전량 (산불 정전 차감):                               │
│     actual_MWh = potential_MWh × (1 - outage_rate)           │
│                = 15,510,948 × (1 - 0.000274)                 │
│                = 15,506,698 MWh                              │
│                                                             │
│  ⑤ 매출:                                                    │
│     revenue = actual_MWh × power_price                      │
│                                                             │
│  ⑥ 연료비 (효율 저하 반영):                                   │
│     eff_heat_rate = heat_rate × (1 + efficiency_loss)        │
│     fuel_cost = actual_MWh × eff_heat_rate × fuel_price      │
│                                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 4단계: 재무 → 신용등급 → CRP                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  EBITDA = revenue - fuel - opex - carbon_cost               │
│  NPV = Σ(FCF_t / (1+r)^t)                                  │
│  DSCR = EBITDA / debt_service                               │
│                                                             │
│  신용등급 = f(DSCR, profitability, leverage, ...)            │
│  CRP = scenario_spread - counterfactual_spread (bps)        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 시나리오별 SSP 매핑

| CRP 시나리오 | SSP | 의미 |
|-------------|-----|------|
| baseline | SSP1-2.6 | 저배출 (현재 수준) |
| moderate_physical | SSP2-4.5 | 중간 배출 |
| high_physical | SSP5-8.5 | 고배출 |
| severe_drought | SSP5-8.5 (2050) | 고배출 + 후기 |

## 현재 사용하는 값 vs 버리는 값

### CLIMADA (산불)
| 항목 | 사용 여부 | 현재 값 |
|------|---------|--------|
| n_events | ✅ 사용 → freq 계산 | 10 |
| aai_agg (피해액) | ❌ 미사용 | 1.36억원/년 |
| at_event (이벤트별 분포) | ❌ 미사용 | [0, 13.6억, 0, ...] |
| frequency (이벤트별 빈도) | ❌ 미사용 | [0.1, 0.1, ...] |

### PhysRisk (가뭄/수자원)
| 항목 | 사용 여부 | 예시 (가뭄 ssp585/2050) |
|------|---------|----------------------|
| impact_mean | ✅ 사용 | 0.001007 |
| impact_std | ❌ 미사용 | 0.0092 |
| impact_distribution | ❌ 미사용 | {bin_edges, probabilities} |
| impact_exceedance | ❌ 미사용 | {values, exceed_probabilities} |

### PhysRisk 미사용 위험 유형
| 위험 유형 | impact_mean | 미사용 이유 |
|----------|------------|-----------|
| Fire | 0.00007 | CLIMADA 산불과 중복 |
| Wind | 0.001 | 미반영 |
| WaterTemperature | 0.001 | 미반영 |
| AirTemperature | 0.0 | 삼척은 극단 폭염 없음 |
| CoastalInundation | 0.0 | 침수 위험 없음 |
| RiverineInundation | 0.0 | 하천범람 없음 |
| Hail | 0.0 | 우박 위험 없음 |

## 활성 코드 파일 목록

| 파일 | 역할 |
|------|------|
| `src/pipeline/runner.py` | 파이프라인 오케스트레이터 |
| `src/planit/runner.py` | CLIMADA/PhysRisk subprocess 실행 |
| `src/planit/adapter.py` | 원시값 → outage/derate/water 변환 |
| `src/planit/config.py` | 설정 (정전확률, 시간 등) |
| `src/planit/cache.py` | 결과 캐시 |
| `src/risk/physical/__init__.py` | PhysicalAdjustments 데이터 구조 |
| `src/models/physical/temperature.py` | 온도 효율 저하 계산 |
| `src/financials/cashflow.py` | 캐시플로우에 물리적 조정 적용 |
| `Physicalrisk_PLANiT/src/core/hazard.py` | CLIMADA WildFire 실행 |
| `Physicalrisk_PLANiT/src/core/exposure.py` | GeoJSON → CLIMADA Exposure |
| `Physicalrisk_PLANiT/src/core/vulnerability.py` | ImpfWildfire + Impact 계산 |

# CRP 모델 전체 프로세스 설명서 (실동작 기준)

기준일: 2026-03-07  
기준 코드: `src/pipeline/runner.py`, `src/planit/*`, `src/financials/*`, `src/risk/*`

## 1) 한 줄 요약

이 모델은 `전환 리스크 + 물리 리스크`를 운영지표(발전량, 이용률, 비용)로 바꾸고, 이를 현금흐름/신용등급/자본비용으로 전파해 **Climate Risk Premium (CRP)** 를 계산합니다.

## 2) 현재 실제 동작 흐름

1. 입력 데이터 로드 (`data/raw/*.csv`, PLANiT 결과 CSV 또는 PLANiT live 실행)
2. 전환 리스크 계산 (`capacity_factor`, `operating_years`)
3. 물리 리스크 계산 (`outage_rate`, `capacity_derate`, `water_constrained_capacity`)
4. 연도별 발전량/매출/비용 계산
5. FCF, NPV, IRR, DSCR, LLCR 계산
6. 신용등급(AAA~D) 산정
7. 카운터팩추얼(무기후리스크 가정 A등급) 대비 CRP(bps) 계산
8. 시나리오별 결과 CSV/JSON 출력

핵심 오케스트레이터: `src/pipeline/runner.py`

## 3) 모델별 데이터 형태 (입력/출력 스키마)

### 3.1 PLANiT 원천 결과 스키마

`Physicalrisk_PLANiT/data/results/` 예시:

- `wildfire_results_*.csv`
  - `hazard_type, scenario, annual_frequency_per_year, n_events, years_covered`
- `drought_results_*.csv`, `water_risk_results_*.csv`
  - `hazard_type, scenario, year, asset, impact_mean, impact_std`

파이프라인 내부 표준 객체 (`PLANiTHazardResult`):

- `hazard_type: str`
- `scenario: str` (예: `ssp126`, `ssp585`)
- `year: int`
- `asset: str`
- `value: float`
- `std: float`
- `unit: str` (`krw` 또는 `fraction`)
- `source: str` (`climada` 또는 `physrisk`)

### 3.2 물리 리스크 변환 후 스키마

`PhysicalAdjustments`:

- `outage_rate`
- `capacity_derate`
- `efficiency_loss`
- `water_constrained_capacity`
- `notes`

### 3.3 전환 리스크 스키마

`TransitionAdjustments`:

- `capacity_factor`
- `operating_years`
- `notes`

### 3.4 현금흐름/재무/신용 출력 스키마

`CashFlowTimeSeries`:

- `years, revenue, fuel_costs, variable_opex, fixed_opex, lost_revenue_from_outages, total_costs, ebitda, ebit, tax_expense, free_cash_flow ...`

`FinancialMetrics`:

- `npv, irr, avg_dscr, min_dscr, llcr, payback_years`

`RatingAssessment`:

- `overall_rating(AAA~D)`, 구성지표 등급, 지표값

`results/yearly_ratings.csv` (연간 신용등급 시계열):

- `scenario, display_name, year, dscr, rating, spread_bps, cost_of_debt, ebitda, debt_service`
- 11개 시나리오 × 운영 연수 (총 352행)

`FinancingImpact`:

- `expected_loss_pct, debt_spread_bps, equity_premium_pct, crp_bps, wacc_baseline_pct, wacc_adjusted_pct`

## 4) wildfire / drought / water_risk 의미

### wildfire (CLIMADA)

- 의미: 산불 이벤트의 연간 발생 빈도(및 이벤트 수)
- 변환:
  - `outage_rate = annual_event_frequency_per_year × outage_probability × (outage_duration_hours / 8760)`
- 코드: `src/planit/adapter.py`

### drought (PhysRisk)

- 의미: 가뭄으로 인한 영향 강도 (`impact_mean`, 0~1 근사)
- 변환:
  - `capacity_derate = impact_mean * drought_severity_scale` (기본 1.0)
- 코드: `src/planit/adapter.py`

### water_risk (PhysRisk)

- 의미: 수자원 제약 위험 (`impact_mean`)
- 변환:
  - `water_constrained_capacity = max(0, 1 - impact_mean)`
- 코드: `src/planit/adapter.py`

## 5) 오픈소스 사용 방식 (실제)

### 5.1 CLIMADA 사용처

- 산불 hazard 생성: `climada_petals.hazard.WildFire`
- 취약도 함수: `climada_petals.entity.impact_funcs.wildfire.ImpfWildfire`
- 영향 계산: `climada.engine.Impact` (실패 시 fallback 계산 경로 있음)
- 구현: `Physicalrisk_PLANiT/src/core/hazard.py`, `Physicalrisk_PLANiT/src/core/vulnerability.py`

### 5.2 PhysRisk 사용처

- API 호출: `physrisk.container.Container().requester().get("get_asset_impact", ...)`
- hazard: `drought`, `water_risk` 등
- 구현: `Physicalrisk_PLANiT/src/core/hazard.py`

### 5.3 메인 CRP 파이프라인과의 연결

- 연결 모듈: `src/planit/runner.py` + `src/planit/adapter.py`
- 기본값: **CSV 모드** (`CRP_PLANIT_MODE=csv`)
- 옵션: **live 모드** (`CRP_PLANIT_MODE=live`) 시 런타임 호출

## 6) 위치 입력 시 동작 (live 통합)

환경변수:

- `CRP_PLANIT_LAT`, `CRP_PLANIT_LON`
- (옵션) `CRP_PLANIT_ASSET_NAME`, `CRP_PLANIT_CAPACITY_MW`, `CRP_PLANIT_SITE_HALF_SIZE_DEG`

동작:

1. `src/planit/runner.py`가 임시 `dynamic_site.geojson` 생성
2. PLANiT config의 `project.geojson_source`를 동적으로 교체
3. live PLANiT 실행
4. 동적 위치일 때는 CSV 백필 없이 live 결과만 사용

즉, 위치 입력 기반 live 호출은 코드상 통합되어 있습니다.

### 6.1 왜 처음에 고정 GeoJSON 기반이었나

초기에는 재현성 때문에 고정 GeoJSON(`Physicalrisk_PLANiT/data/samcheok_power_grid_all.geojson`)을 기본으로 썼습니다.

- 같은 자산 경계/가치로 반복 실행 가능
- CLIMADA/PhysRisk 결과를 frozen CSV와 비교하기 쉬움
- 논문/리포트 숫자 고정에 유리

지금은 이 기본값을 유지하면서도, 환경변수로 동적 위치를 덮어쓸 수 있게 확장된 상태입니다.

## 7) 재무적 가치로 바뀌는 이유와 계산 근거

### 7.1 운영 전파

- 발전량:
  - `potential_mwh = capacity_mw * 8760 * cf_series`
  - `actual_mwh = potential_mwh * (1 - outage_rate)`
- 전환/물리 반영:
  - `cf_series = base_cf_series * (1 - capacity_derate)`
  - `cf_series = min(cf_series, water_constrained_capacity)`
- 코드: `src/financials/cashflow.py`

### 7.2 손익/현금흐름

- `revenue = actual_mwh * power_price`
- `fuel_costs = actual_mwh * heat_rate * (1 + efficiency_loss) * fuel_price`
- `EBITDA = revenue - total_costs`
- `FCF = NOPAT + depreciation - capex`
- 코드: `src/financials/cashflow.py`

### 7.3 가치평가/커버리지

- `NPV = npf.npv(discount_rate, fcf) - initial_capex`
- `IRR`, `DSCR`, `LLCR` 계산
- 코드: `src/financials/metrics.py`

### 7.4 신용등급/자본비용/CRP

- 신용등급: DSCR/coverage/leverage 가중평균 + distress override
- 등급별 스프레드 매핑: AAA 50bps ... D 5000bps
- 카운터팩추얼 기준(`A`) 대비 WACC 차이를 CRP로 계산
- 코드: `src/risk/credit_rating.py`, `src/risk/financing.py`

## 8) 통합 상태 점검 (현재 기준)

### 8.1 통합된 부분

- PLANiT ↔ CRP 파이프라인 연결
- CSV 모드 + live 모드
- 위치 입력 기반 dynamic GeoJSON 생성
- wildfire/drought/water_risk를 재무 모델 입력으로 변환

### 8.2 아직 남은 기술적 이슈/주의점

1. 문서 불일치:
   - `docs/VULNERABILITY_FUNCTIONS.md`에는 한때 wildfire-only라고 되어 있으나,
   - 현재 `src/planit/config.py` 기본은 `["wildfire", "drought", "water_risk"]` 입니다.
2. wildfire 연도 처리:
   - CLIMADA wildfire는 본질적으로 연도축이 약해 anchor year(2030/2040/2050/2060)로 복제 사용합니다.
3. baseline 물리리스크:
   - target year 2024는 baseline값(기본 0)으로 처리되므로 사실상 no-physical baseline에 가깝습니다.
4. 위치 입력 단순화:
   - 사용자 위치는 기본적으로 정사각형 폴리곤으로 근사합니다.
5. 자산명 매칭:
   - 한글 자산명 부분일치 로직에 의존하므로, 명칭 표준화가 중요합니다.
6. Python 3.14 호환:
   - `src/planit/runner.py`는 런타임에 CLIMADA 호환 패치(distutils alias, pandas/contextily 호환, `impact.py` dataclass 기본값 수정)를 적용합니다.
   - 즉, "아예 불가"는 아니지만, 패치 의존 운영이라 환경 고정(권장: venv + 버전 잠금)이 필요합니다.

## 9) 실행 가이드 (현재 권장)

### 9.1 기본(재현성 우선, CSV)

```bash
python scripts/regenerate_dashboard_data.py
```

### 9.2 live 호출(고정 자산)

```bash
CRP_PLANIT_MODE=live python scripts/regenerate_dashboard_data.py
```

### 9.3 live 호출(위치 입력)

```bash
CRP_PLANIT_MODE=live \
CRP_PLANIT_LAT=37.365 \
CRP_PLANIT_LON=129.224 \
CRP_PLANIT_ASSET_NAME=samcheok_input \
python scripts/regenerate_dashboard_data.py
```

## 10) frozen 결과 메타데이터 (참고)

`Physicalrisk_PLANiT/data/results/manifest.json` 기준:

- wildfire 실행일: 2026-01-16
- drought 실행일: 2026-01-17
- water_risk 실행일: 2026-01-17

이 값들은 CSV 모드에서 기본적으로 참조되는 스냅샷입니다.

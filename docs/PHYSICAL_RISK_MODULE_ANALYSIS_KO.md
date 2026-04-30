# 물리적 리스크 모듈 구조 및 입출력 분석

## 1. 목적과 결론

이 문서는 현재 저장소에서 물리적 리스크 관련 모듈들이 어떻게 연결되어 있는지, 어떤 입력을 받아 어떤 출력을 만들고, 그 출력이 실제로 `Cash flow`까지 연결되는지를 코드 기준으로 정리한 것이다.

핵심 결론은 다음과 같다.

1. 현재 기본 실행 경로에서 물리적 리스크가 현금흐름에 반영되는 실제 값은 주로 `data/physical_risk_steps/output/physical_risk_output.csv`의 `total_acute_pct`와 `temp_total_pct`이다.
2. `PLANiTAdapter.convert()`가 계산한 `drought`, `water_risk`, `wildfire` 개별 값은 현재 `CRPModelRunner.run_scenario()`의 기본 경로에서 최종 현금흐름에 직접 반영되지 않을 수 있으며, 실제로는 연도별 CSV 보간값이 이를 덮어쓴다.
3. 기본/정적 CSV 기반 경로에서 exposure는 사실상 `발전소 단일 자산` 중심이다.
4. 다만 `live` 동적 위치 모드에서 `CRP_PLANIT_INCLUDE_GRID=1`이면 발전소뿐 아니라 `변전소 + 송전선`까지 포함한 grid-aware exposure를 구성할 수 있다.
5. 코드베이스에는 `src/risk/physical.py`와 `src/risk/physical/` 패키지가 동시에 존재하며, 실제 import는 패키지 쪽 `src/risk/physical/__init__.py`를 사용한다. 따라서 물리 리스크 로직은 하나가 아니라 여러 세대 구현이 공존한다.

---

## 2. 실제 실행 경로

현재 표준 시나리오 실행의 중심은 [runner.py](/C:/dev/climate_risk_premium/src/pipeline/runner.py)이다.

실행 흐름은 아래와 같다.

1. `CRPModelRunner.run_scenario()`
2. `self._load_physical_scenario(physical_scenario_name)`
3. `PLANiTAdapter.convert(...)`로 정적 `PhysicalAdjustments` 생성
4. 동시에 `load_yearly_from_output_csv(...)`로 연도별 `YearlyPhysicalAdjustments` 생성
5. `compute_cashflows_timeseries(...)` 호출
6. 이 함수는 `yearly_physical_adj`가 있으면 정적 `physical_adj`보다 연도별 값을 우선 사용
7. 결과가 `EBITDA -> CFADS -> DSCR -> Rating -> Spread -> NPV/IRR/CRP`로 연결

즉, 물리 리스크가 현금흐름으로 이어지는 공식 경로는 아래와 같다.

```text
PLANiT/기타 물리 리스크 데이터
-> 물리 리스크 조정치 생성
-> 연간 발전량/효율/가동률 제약
-> Revenue / Fuel Costs / EBITDA
-> CFADS / DSCR
-> Credit Rating / Spread
-> WACC / NPV / IRR / CRP
```

다만 현재 기본 경로에서는 위 "물리 리스크 조정치 생성"의 실제 소스가 `PLANiTAdapter.convert()`라기보다 `physical_risk_output.csv`의 연도별 보간값으로 수렴한다.

---

## 3. exposure 좌표의 의미

### 3.1 기본 경로: 발전소 중심

기본 정적 실행 경로는 `PLANiTRunner.load_results_from_csv(...)`를 통해 PLANiT 결과 CSV를 읽는다. 여기서 `target_asset`은 삼척 발전소 이름으로 고정되어 있으며, PhysRisk의 `drought`, `water_risk` 행도 이 자산명으로 필터링된다.

관련 코드:

- [runner.py](/C:/dev/climate_risk_premium/src/planit/runner.py)
- [config.py](/C:/dev/climate_risk_premium/src/planit/config.py)

캐시된 실제 자산명 예시는 아래와 같다.

- `data/cache/planit/drought_ssp585_2050.json`
- `data/cache/planit/water_risk_ssp585_2050.json`

여기 기록된 asset은 `삼척화력발전소`이다.

따라서 기본 경로에서 exposure 좌표/자산은 실질적으로 `발전소 단일 자산`으로 보는 것이 맞다.

### 3.2 동적 위치 모드: 발전소 + 변전소 + 송전선 포함 가능

`PLANiTRunner._apply_dynamic_location_override()`는 환경변수 기반으로 동적 GeoJSON을 생성한다.

이때:

- `CRP_PLANIT_LAT`
- `CRP_PLANIT_LON`
- `CRP_PLANIT_INCLUDE_GRID=1`

이면 아래 3개 feature가 생성된다.

1. 발전소 Polygon
2. 변전소 Point
3. 송전선 LineString

실제 생성된 예시는 [dynamic_site.geojson](/C:/dev/climate_risk_premium/data/cache/planit/dynamic_site.geojson)에서 확인된다.

즉, 동적 live 모드에서는 exposure가 `발전소만`이 아니라 `변전소와 송전선까지 포함`할 수 있다.

### 3.3 target asset mode에 따른 차이

동적 모드에서는 `CRP_PLANIT_TARGET_ASSET_MODE`가 중요하다.

- `all` 또는 `grid`: 발전소 + 변전소 + 송전선 전체를 대상으로 결과 집계
- `plant`: 발전소만 대상으로 사용

코드상 기본값은 `include_grid=True`일 때 사실상 `all`이다.

### 3.4 정리

현재 저장소의 exposure 좌표 의미를 한 줄로 요약하면 아래와 같다.

- 기본 canonical 경로: `발전소 중심`
- live 동적 위치 경로: `발전소 + 변전소 + 송전선 포함 가능`

즉, "exposure 좌표가 발전소만인가?"라는 질문에 대한 정확한 답은 `기본 경로는 거의 그렇지만, live grid-aware 모드에서는 아니다`이다.

---

## 4. 현재 현금흐름까지 실제로 연결되는 물리 리스크 값

### 4.1 직접 연결되는 함수

[cashflow.py](/C:/dev/climate_risk_premium/src/financials/cashflow.py)의 `compute_cashflows_timeseries()`가 물리 리스크를 실제 재무 변수로 변환한다.

이 함수에서 물리 리스크가 쓰이는 방식은 다음과 같다.

1. `outage_rates`
   - 실제 발전량을 줄인다.
   - `actual_mwh = potential_mwh * (1 - outage_rates)`
   - 결과적으로 `revenue` 감소

2. `capacity_derates`
   - capacity factor를 줄인다.
   - `cf_series = base_cf_series * (1 - capacity_derates)`

3. `water_constraints`
   - capacity factor 상한을 강제로 제한한다.
   - `cf_series = min(cf_series, water_constraints)`

4. `efficiency_losses`
   - 열효율 악화로 연료비를 증가시킨다.
   - `effective_heat_rates = heat_rate * (1 + efficiency_losses)`

이 네 값만 현금흐름에 직접 연결된다.

### 4.2 그런데 현재 기본 경로에서 실제 쓰이는 값

문제는 [runner.py](/C:/dev/climate_risk_premium/src/pipeline/runner.py)에서 `yearly_physical_adj = load_yearly_from_output_csv(...)`를 항상 만들고, 이를 `compute_cashflows_timeseries(...)`로 넘긴다는 점이다.

그러면 [cashflow.py](/C:/dev/climate_risk_premium/src/financials/cashflow.py)는 정적 `physical_adj` 대신 `yearly_physical_adj`를 우선 사용한다.

그리고 [src/risk/physical/__init__.py](/C:/dev/climate_risk_premium/src/risk/physical/__init__.py)의 `load_yearly_from_output_csv()`는 아래처럼 동작한다.

1. `physical_risk_output.csv`를 읽는다.
2. `total_acute_pct`를 `outage_rates`로 사용한다.
3. `temp_total_pct`를 `efficiency_losses`로 사용한다.
4. `capacity_derates`는 항상 `0`
5. `water_constraints`는 항상 `1`

즉, 현재 기본 경로에서 물리 리스크가 현금흐름에 반영되는 실제 값은 사실상 아래 둘뿐이다.

1. `total_acute_pct -> outage_rates`
2. `temp_total_pct -> efficiency_losses`

반대로 아래 값들은 현재 기본 경로에서 현금흐름에 실질 반영되지 않는다.

1. `PLANiTAdapter.convert()`가 계산한 `capacity_derate`
2. `PLANiTAdapter.convert()`가 계산한 `water_constrained_capacity`
3. `PLANiTAdapter.convert()`가 계산한 정적 `outage_rate`
4. `PLANiTAdapter.convert()`가 계산한 정적 `efficiency_loss`

이유는 연도별 CSV 경로가 이들을 덮어쓰기 때문이다.

---

## 5. 어떤 모듈이 Cash flow로 이어지고, 어떤 모듈이 이어지지 않는가

### 5.1 Cash flow로 이어지는 모듈

#### A. `src/pipeline/runner.py`

역할:

- 전체 시나리오 실행 orchestration
- 물리 리스크 입력을 재무 모듈로 전달

입력:

- plant params
- transition scenario
- physical scenario name
- market scenario

출력:

- `ScenarioResult`
- 내부적으로 `CashFlowTimeSeries`, `FinancialMetrics`, `RatingAssessment`

Cash flow 연결 여부:

- `직접 연결됨`

#### B. `src/risk/physical/__init__.py`의 `load_yearly_from_output_csv()`

역할:

- 연도별 물리 리스크 조정치 생성

입력:

- `data/physical_risk_steps/output/physical_risk_output.csv`

출력:

- `YearlyPhysicalAdjustments`

Cash flow 연결 여부:

- `직접 연결됨`

현재 실제 영향:

- `total_acute_pct`, `temp_total_pct`만 사용

#### C. `src/financials/cashflow.py`

역할:

- 물리 리스크와 전환 리스크를 실제 현금흐름으로 변환

입력:

- `TransitionAdjustments`
- `PhysicalAdjustments` 또는 `YearlyPhysicalAdjustments`

출력:

- `CashFlowTimeSeries`

Cash flow 연결 여부:

- `핵심 연결 모듈`

#### D. `src/financials/metrics.py`, `src/risk/credit_rating.py`, `src/risk/financing.py`

역할:

- 현금흐름 결과를 DSCR, rating, spread, CRP로 변환

입력:

- `CashFlowTimeSeries`

출력:

- `FinancialMetrics`
- `RatingAssessment`
- `FinancingImpact`

Cash flow 연결 여부:

- `직접 연결됨`

### 5.2 정의는 있으나 현재 기본 경로에서 직접 이어지지 않는 모듈/값

#### A. `src/planit/adapter.py`

역할:

- PLANiT 결과를 `PhysicalAdjustments`로 변환

입력:

- wildfire / drought / water_risk 결과

출력:

- `outage_rate`
- `capacity_derate`
- `efficiency_loss`
- `water_constrained_capacity`

현 상태:

- [runner.py](/C:/dev/climate_risk_premium/src/pipeline/runner.py)에서 `_load_physical_scenario()`를 통해 호출되긴 한다.
- 그러나 이후 `load_yearly_from_output_csv()`가 다시 연도별 조정치를 넣으므로, 기본 경로에서는 이 값들이 최종 cash flow에 그대로 반영되지 않는다.

판정:

- `부분적으로만 연결됨`
- `현재 기본 run에서는 사실상 우회될 수 있음`

#### B. `src/risk/physical.py`

역할:

- 또 다른 세대의 물리 리스크 유틸리티 구현

현 상태:

- 파일은 존재하지만 실제 import는 패키지 `src/risk/physical/__init__.py`로 해석된다.
- `python -c` 확인 결과 `src.risk.physical.__file__`는 패키지 쪽 파일이다.

판정:

- `현재 주 실행 경로에서는 비핵심`

#### C. `src/risk/physical/enhanced_engine.py`

역할:

- hazard / exposure / vulnerability를 더 정교하게 계산하는 확장 엔진

현 상태:

- 구조적으로 잘 분리되어 있으나, `CRPModelRunner.run_scenario()`의 표준 경로에서 직접 호출되지 않는다.

판정:

- `현재 canonical cashflow 경로에는 미연결`

#### D. `src/models/physical/*`

포함:

- `model.py`
- `exposure.py`
- `hazards.py`
- `temperature.py`
- `compound_risk.py`
- `damage_functions/*`

현 상태:

- 물리 리스크를 풍부하게 모델링하는 별도 계층이다.
- 하지만 현재 메인 pipeline은 이 계층을 전면적으로 사용하지 않는다.
- 일부 개념은 반영되었으나, 현재 최종 재무 경로는 여기보다 `runner.py -> risk/physical/__init__.py -> cashflow.py` 축에 더 의존한다.

판정:

- `연구/확장용 비중이 크고, 현재 메인 cashflow 경로와는 느슨하게 연결`

---

## 6. scenario별 물리 리스크가 실제로 구분되는가

현재 기본 실행에서는 물리 시나리오 이름이 충분히 구분되어 현금흐름으로 반영되지 않을 가능성이 매우 크다.

이유는 아래와 같다.

1. `physical_scenario_name`은 `_load_physical_scenario()`에서 정적 `physical_adj`를 만들 때만 차이를 만든다.
2. 그러나 실제 계산 직전에 `load_yearly_from_output_csv()`가 공통 연도별 물리 조정치를 다시 만든다.
3. 이 연도별 조정치는 scenario name을 받지 않고, 동일한 `physical_risk_output.csv`를 읽는다.
4. 따라서 `moderate_physical`, `high_physical`, `severe_drought`가 동일한 연도별 물리 경로를 탈 수 있다.

실제 결과 파일 [scenario_comparison.csv](/C:/dev/climate_risk_premium/results/scenario_comparison.csv)에서도 아래 현상이 보인다.

1. `baseline`
2. `moderate_physical`
3. `high_physical`
4. `severe_drought`

이들의 NPV/IRR/DSCR이 동일하거나 사실상 동일하다.

또한 [cashflow_baseline.csv](/C:/dev/climate_risk_premium/results/cashflow_baseline.csv)와 [cashflow_moderate_physical.csv](/C:/dev/climate_risk_premium/results/cashflow_moderate_physical.csv)의 앞부분도 동일하다.

이는 현재 canonical path에서 물리 시나리오의 차별화가 cash flow까지 충분히 전달되지 않는다는 강한 증거다.

---

## 7. 모듈별 입출력 구조 요약

### `src/planit/runner.py`

입력:

- PLANiT 결과 CSV 또는 live PLANiT runtime
- 환경변수 (`CRP_PLANIT_LAT`, `CRP_PLANIT_LON`, `CRP_PLANIT_INCLUDE_GRID` 등)

출력:

- `PLANiTHazardResult[]`

비고:

- live 모드에서는 발전소/변전소/송전선을 포함한 동적 GeoJSON 생성 가능

### `src/planit/adapter.py`

입력:

- `PLANiTHazardResult[]`
- target year
- scenario label

출력:

- `dict(outage_rate, capacity_derate, efficiency_loss, water_constrained_capacity, notes)`

비고:

- wildfire는 event frequency 기반 outage로 변환
- drought/water는 expected impact 기반 변환

### `src/risk/physical/__init__.py::load_yearly_from_output_csv`

입력:

- `physical_risk_output.csv`

출력:

- `YearlyPhysicalAdjustments`

비고:

- 현재 메인 pipeline에서 실질적으로 가장 중요한 물리 리스크 입력 모듈

### `src/financials/cashflow.py`

입력:

- plant parameters
- transition adjustments
- physical adjustments

출력:

- revenue
- costs
- EBITDA
- FCF
- DSCR

### `src/risk/credit_rating.py` / `src/risk/financing.py`

입력:

- cash flow metrics

출력:

- rating
- spread
- CRP

---

## 8. 질문별 직접 답변

### 질문 1. exposure 좌표가 무엇인지, 발전소만인지 변전소와 송배전을 포함하는지

답:

- 기본 정적 CSV 기반 경로에서는 사실상 `발전소 중심`이다.
- live 동적 위치 모드에서는 `발전소 + 변전소 + 송전선`을 함께 포함할 수 있다.
- 따라서 저장소 전체 관점에서는 "발전소만"이라고 단정하면 틀리고, "기본 경로는 발전소 중심, live grid-aware 경로는 변전소/송전선 포함 가능"이 정확하다.

### 질문 2. 어떤 모듈이 결과, 특히 Cash flow로 이어지고 어떤 값이 사용되지 않는지

Cash flow로 이어지는 핵심 모듈:

1. `src/pipeline/runner.py`
2. `src/risk/physical/__init__.py::load_yearly_from_output_csv`
3. `src/financials/cashflow.py`
4. `src/financials/metrics.py`
5. `src/risk/credit_rating.py`
6. `src/risk/financing.py`

현재 기본 경로에서 사용되지 않거나 직접 연결되지 않는 값:

1. `PLANiTAdapter.convert()`가 만든 정적 `capacity_derate`
2. `PLANiTAdapter.convert()`가 만든 정적 `water_constrained_capacity`
3. `PLANiTAdapter.convert()`가 만든 정적 `outage_rate`
4. `PLANiTAdapter.convert()`가 만든 정적 `efficiency_loss`
5. `src/models/physical/*`의 풍부한 세부 hazard/exposure/vulnerability 결과 대부분
6. `src/risk/physical/enhanced_engine.py`의 확장 계산 결과 대부분

현재 기본 경로에서 실제로 cash flow에 반영되는 물리 값:

1. `physical_risk_output.csv`의 `total_acute_pct`
2. `physical_risk_output.csv`의 `temp_total_pct`

---

## 9. 해석상 주의점

이 저장소는 물리 리스크 관련 구현이 여러 세대로 중첩되어 있다.

1. PLANiT 연동 경로
2. `physical_risk_output.csv` 기반 경로
3. `src/models/physical/*` 기반 고도화 경로
4. `src/risk/physical/enhanced_engine.py` 경로

하지만 현재 canonical run은 이들을 모두 동등하게 쓰지 않는다. 따라서 "코드에 존재한다"와 "현재 결과 생성에 실제 사용된다"를 반드시 구분해야 한다.

현재 결과 재현 관점에서 가장 중요한 사실은 아래 한 줄이다.

> 물리적 리스크의 최종 cash flow 반영은 현재 주로 `physical_risk_output.csv`의 연도별 보간 경로를 통해 이루어지며, PLANiT의 세부 hazard 결과는 기본 실행 경로에서 직접 재무값으로 끝까지 전달되지 않을 수 있다.


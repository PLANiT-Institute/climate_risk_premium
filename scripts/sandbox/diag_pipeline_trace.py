"""
전체 파이프라인 추적: Stage 1 → 4
2050년 RCP8.5 기준으로 각 단계 값 변화 추적.

Stage 1: PLANiTHazardResult (원본 hazard 수치)
Stage 2: PhysicalAdjustments (PLANiTAdapter 변환 후 - Path A)
         YearlyPhysicalAdjustments (physical_risk_output.csv - Path B)
Stage 3: cashflow 함수 진입 직전 실제 적용 값 (B 우선)
Stage 4: cashflow 계산 결과 (revenue/fuel_cost 영향)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np

SCENARIO = "RCP8.5"
TARGET_YEAR = 2050
START_YEAR = 2025
END_YEAR = 2055


def print_section(title):
    print(f"\n{'=' * 68}")
    print(f"  {title}")
    print(f"{'=' * 68}")


def pct(v):
    return f"{v*100:.5f}%" if v is not None else "N/A"


def main():
    print(f"파이프라인 추적: {SCENARIO} / TARGET={TARGET_YEAR} / 운영기간 {START_YEAR}~{END_YEAR}")

    # ------------------------------------------------------------------
    # Stage 1: PLANiTHazardResult 원본
    # ------------------------------------------------------------------
    print_section("Stage 1: PLANiTHazardResult (원본 hazard 수치)")
    from src.planit.config import PLANiTIntegrationConfig
    from src.planit.runner import PLANiTRunner

    config = PLANiTIntegrationConfig()
    results_dir = str(config.get_results_dir(str(ROOT)))
    planit_results = PLANiTRunner.load_results_from_csv(results_dir)

    if not planit_results:
        print("  [주의] PLANiT CSV 결과 없음 — Physicalrisk_PLANiT/data/results/ 디렉터리 확인 필요")
        print(f"  탐색 경로: {results_dir}")
    else:
        col = "  {:<12} {:<10} {:<6} {:>14}  {}"
        print(col.format("hazard", "scenario", "year", "value", "unit"))
        print("  " + "-" * 58)
        seen = {}
        for r in planit_results:
            k = (r.hazard_type, r.scenario, r.year)
            if k not in seen:
                seen[k] = r
        for (hz, sc, yr), r in sorted(seen.items()):
            print(col.format(hz, sc, str(yr), f"{r.value:.8f}", r.unit))
        print(f"\n  wildfire 주요 메타데이터 (첫 번째 ssp585 행):")
        for r in planit_results:
            if r.hazard_type == "wildfire" and "ssp585" in str(r.scenario):
                print(f"    event_frequency_per_year : {r.event_frequency_per_year}")
                print(f"    event_count              : {r.event_count}")
                print(f"    reference_years          : {r.reference_years}")
                print(f"    value (legacy_impact)    : {r.value:.8f}")
                break

    # ------------------------------------------------------------------
    # Stage 2A: PhysicalAdjustments (Path A)
    # ------------------------------------------------------------------
    print_section("Stage 2A: PhysicalAdjustments @ 2050/RCP8.5  (Path A — PLANiTAdapter)")
    from src.planit.adapter import PLANiTAdapter

    adapter = PLANiTAdapter(config)
    adj_a = adapter.convert(planit_results, TARGET_YEAR, SCENARIO)

    print(f"  outage_rate           : {pct(adj_a['outage_rate'])}")
    print(f"  capacity_derate       : {pct(adj_a['capacity_derate'])}")
    print(f"  efficiency_loss       : {pct(adj_a['efficiency_loss'])}")
    print(f"  water_constrained_cap : {adj_a['water_constrained_capacity']:.6f}")
    print(f"  notes  : {adj_a['notes']}")

    # ------------------------------------------------------------------
    # Stage 2B: YearlyPhysicalAdjustments (Path B)
    # ------------------------------------------------------------------
    print_section("Stage 2B: YearlyPhysicalAdjustments  (Path B — physical_risk_output.csv)")
    from src.risk.physical import load_yearly_from_output_csv

    yearly_b = load_yearly_from_output_csv(start_year=START_YEAR, end_year=END_YEAR)
    adj_b_2050 = yearly_b.get_adjustment_for_year(TARGET_YEAR)

    print(f"  scenario_name: {yearly_b.scenario_name}")
    col2 = "  {:<6} {:>12} {:>12} {:>12} {:>14}"
    print(col2.format("year", "outage%", "derate%", "eff_loss%", "water_cap"))
    print("  " + "-" * 58)
    for yr in [2025, 2030, 2040, 2050, 2055]:
        if yr in yearly_b.years:
            i = np.where(yearly_b.years == yr)[0][0]
            print(col2.format(
                yr,
                f"{yearly_b.outage_rates[i]*100:.5f}",
                f"{yearly_b.capacity_derates[i]*100:.5f}",
                f"{yearly_b.efficiency_losses[i]*100:.5f}",
                f"{yearly_b.water_constraints[i]:.6f}",
            ))

    # ------------------------------------------------------------------
    # Stage 3: cashflow 진입 직전 실제 적용 값 (B 우선)
    # ------------------------------------------------------------------
    print_section("Stage 3: cashflow 진입 직전 실제 적용 값  (yearly_physical_adj 우선)")

    years_op = np.arange(START_YEAR, END_YEAR + 1)
    # cashflow.py 137~161 로직 재현
    outage_rates    = np.array([yearly_b.get_adjustment_for_year(int(y)).outage_rate for y in years_op])
    capacity_derates= np.array([yearly_b.get_adjustment_for_year(int(y)).capacity_derate for y in years_op])
    efficiency_losses=np.array([yearly_b.get_adjustment_for_year(int(y)).efficiency_loss for y in years_op])
    water_constraints=np.array([yearly_b.get_adjustment_for_year(int(y)).water_constrained_capacity for y in years_op])

    idx_2050 = np.where(years_op == TARGET_YEAR)[0][0]
    print(f"  2050년 실제 적용값:")
    print(f"    outage_rate           : {pct(outage_rates[idx_2050])}")
    print(f"    capacity_derate       : {pct(capacity_derates[idx_2050])}  ← Path A={pct(adj_a['capacity_derate'])} 이었으나 0으로 덮어씌워짐")
    print(f"    efficiency_loss       : {pct(efficiency_losses[idx_2050])}")
    print(f"    water_constrained_cap : {water_constraints[idx_2050]:.6f}  ← Path A={adj_a['water_constrained_capacity']:.6f} 이었으나 1.0으로 덮어씌워짐")

    print(f"\n  A vs B 차이 요약 @ {TARGET_YEAR}:")
    col3 = "  {:<25} {:>12} {:>12}  {}"
    print(col3.format("field", "Path A", "Path B (적용)", "손실 여부"))
    print("  " + "-" * 62)
    diff_derate = adj_a['capacity_derate'] - capacity_derates[idx_2050]
    diff_water  = adj_a['water_constrained_capacity'] - water_constraints[idx_2050]
    print(col3.format("outage_rate", pct(adj_a['outage_rate']), pct(outage_rates[idx_2050]),
                      "덮어씌워짐" if abs(adj_a['outage_rate'] - outage_rates[idx_2050]) > 1e-9 else "동일"))
    print(col3.format("capacity_derate", pct(adj_a['capacity_derate']), pct(capacity_derates[idx_2050]),
                      f"PLANiT 값 {pct(diff_derate)} 손실" if diff_derate > 1e-9 else "동일 (둘 다 0)"))
    print(col3.format("efficiency_loss", pct(adj_a['efficiency_loss']), pct(efficiency_losses[idx_2050]),
                      "덮어씌워짐"))
    print(col3.format("water_cap", f"{adj_a['water_constrained_capacity']:.6f}", f"{water_constraints[idx_2050]:.6f}",
                      f"PLANiT 값 {diff_water:+.6f} 손실" if abs(diff_water) > 1e-9 else "동일 (둘 다 1.0)"))

    # ------------------------------------------------------------------
    # Stage 4: cashflow 계산 결과 (2050년 단면)
    # ------------------------------------------------------------------
    print_section("Stage 4: cashflow 영향 추정 (2050년 단면, 기본 파라미터 기준)")

    capacity_mw = 2100.0
    base_cf = 0.85
    price_krw_per_mwh = 120_000
    heat_rate_mmbtu_per_mwh = 8.5
    fuel_price_krw_per_mmbtu = 15_000

    out_r   = outage_rates[idx_2050]
    eff_l   = efficiency_losses[idx_2050]
    cap_d   = capacity_derates[idx_2050]
    wat_c   = water_constraints[idx_2050]

    # cashflow.py 178~206 로직 재현
    cf = base_cf * (1 - cap_d)
    cf = min(cf, wat_c)
    potential_mwh = capacity_mw * 8760 * cf
    actual_mwh    = potential_mwh * (1 - out_r)
    revenue       = actual_mwh * price_krw_per_mwh
    eff_heat_rate = heat_rate_mmbtu_per_mwh * (1 + eff_l)
    fuel_cost     = actual_mwh * eff_heat_rate * fuel_price_krw_per_mmbtu

    # 리스크 없는 기준값
    potential_mwh_base = capacity_mw * 8760 * base_cf
    actual_mwh_base    = potential_mwh_base
    revenue_base       = actual_mwh_base * price_krw_per_mwh
    fuel_cost_base     = actual_mwh_base * heat_rate_mmbtu_per_mwh * fuel_price_krw_per_mmbtu

    print(f"  기준 파라미터: capacity={capacity_mw:.0f}MW, base_CF={base_cf:.0%},")
    print(f"                 price={price_krw_per_mwh:,}원/MWh, heat_rate={heat_rate_mmbtu_per_mwh} MMBtu/MWh")
    print(f"                 fuel_price={fuel_price_krw_per_mmbtu:,}원/MMBtu")

    print(f"\n  {'':30} {'기준(리스크없음)':>20}  {'2050/RCP8.5 적용후':>20}  {'차이':>15}")
    print("  " + "-" * 90)

    def row(label, base_val, adj_val, unit="억원"):
        diff = adj_val - base_val
        b = f"{base_val/1e8:,.1f}{unit}"
        a = f"{adj_val/1e8:,.1f}{unit}"
        d = f"{diff/1e8:+,.1f}{unit}"
        print(f"  {label:<30} {b:>20}  {a:>20}  {d:>15}")

    def row_mwh(label, base_val, adj_val):
        diff = adj_val - base_val
        b = f"{base_val:,.0f} MWh"
        a = f"{adj_val:,.0f} MWh"
        d = f"{diff:+,.0f} MWh"
        print(f"  {label:<30} {b:>20}  {a:>20}  {d:>15}")

    row_mwh("actual_mwh", actual_mwh_base, actual_mwh)
    row("revenue", revenue_base, revenue)
    row("fuel_cost", fuel_cost_base, fuel_cost)
    row("gross_profit (rev-fuel)", revenue_base - fuel_cost_base, revenue - fuel_cost)

    rev_loss_pct = (revenue_base - revenue) / revenue_base * 100
    fuel_inc_pct = (fuel_cost - fuel_cost_base) / fuel_cost_base * 100
    print(f"\n  revenue 감소율  : {rev_loss_pct:.4f}%  (outage_rate={pct(out_r)} 주도)")
    print(f"  fuel_cost 증가율: {fuel_inc_pct:.4f}%  (efficiency_loss={pct(eff_l)} 주도)")

    print(f"\n{'=' * 68}")
    print("Done.")


if __name__ == "__main__":
    main()

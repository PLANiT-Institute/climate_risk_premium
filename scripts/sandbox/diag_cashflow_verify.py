"""
cashflow 역산 검증: YearlyPhysicalAdjustments 입력값이 cashflow 계산에 그대로 들어가는지 확인.

역산 공식 (cashflow.py 기준):
  outage_rate    = lost_revenue_from_outages / (revenue + lost_revenue_from_outages)
  efficiency_loss = fuel_costs / (actual_mwh * heat_rate * fuel_price) - 1
    where actual_mwh  = revenue / price
          potential_mwh = capacity_mw * 8760 * cf_applied
  capacity_derate → final_cf 에서 역산: base_cf * (1 - derate) = cf_series
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np

CHECK_YEARS = [2025, 2030, 2040, 2050, 2055]


def main():
    from src.pipeline.runner import CRPModelRunner
    from src.risk.physical import load_yearly_from_output_csv
    from src.risk import apply_transition
    from src.financials.cashflow import compute_cashflows_timeseries

    runner = CRPModelRunner(ROOT)
    plant_params = runner._get_plant_params()

    transition_scenario = runner._load_transition_scenario("baseline")
    physical_adj        = runner._load_physical_scenario("baseline")
    market_scenario     = runner._load_market_scenario("baseline")
    transition_adj      = apply_transition(plant_params, transition_scenario)

    start_year = int(plant_params.get("cod_year", 2025))
    end_year   = start_year + transition_adj.operating_years - 1

    yearly_physical_adj = load_yearly_from_output_csv(start_year=start_year, end_year=end_year)

    cf_result = compute_cashflows_timeseries(
        plant_params, transition_scenario, transition_adj,
        physical_adj, market_scenario,
        yearly_physical_adj=yearly_physical_adj,
    )

    # 파라미터
    capacity_mw = float(plant_params.get("capacity_mw", 2100))
    heat_rate   = float(plant_params["heat_rate_mmbtu_mwh"])
    fuel_price  = float(plant_params["fuel_price_per_mmbtu"])
    base_cf     = transition_adj.capacity_factor

    years_op = np.arange(start_year, end_year + 1)

    # cashflow 배열
    revenue_arr      = cf_result.revenue
    fuel_cost_arr    = cf_result.fuel_costs
    lost_rev_arr     = cf_result.lost_revenue_from_outages
    final_cf_arr     = cf_result.final_cf   # cf_series * (1 - outage_rates)

    print(f"파라미터: capacity={capacity_mw:.0f}MW, base_CF={base_cf:.4f}, "
          f"heat_rate={heat_rate}, fuel_price={fuel_price}")
    print()

    # ── outage_rate 검증 ──────────────────────────────────────────────
    # lost_revenue = potential_mwh * outage_rate * price
    # revenue      = potential_mwh * (1-outage_rate) * price
    # => outage_rate = lost_revenue / (revenue + lost_revenue)
    print("[ outage_rate 검증 ]")
    print(f"  {'year':<6} {'input%':>10} {'backCalc%':>12}  {'diff':>10}  {'match':>6}")
    print("  " + "-" * 50)
    outage_ok = True
    for yr in CHECK_YEARS:
        if yr not in years_op:
            continue
        i = np.where(years_op == yr)[0][0]
        inp = yearly_physical_adj.get_adjustment_for_year(yr).outage_rate
        denom = revenue_arr[i] + lost_rev_arr[i]
        back = lost_rev_arr[i] / denom if denom > 0 else None
        diff = abs(back - inp) if back is not None else None
        ok = diff is not None and diff < 1e-9
        if not ok:
            outage_ok = False
        print(f"  {yr:<6} {inp*100:>10.6f} {(back*100 if back is not None else float('nan')):>12.6f}"
              f"  {(diff if diff is not None else float('nan')):>10.2e}  {'OK' if ok else 'MISMATCH':>6}")
    print(f"  => {'전체 OK' if outage_ok else 'MISMATCH 있음'}")

    # ── efficiency_loss 검증 ──────────────────────────────────────────
    # fuel_costs = actual_mwh * heat_rate * (1 + eff_loss) * fuel_price
    # actual_mwh = revenue / price  (price는 revenue/actual_mwh 로 역산)
    # 대신: eff_loss = fuel_costs/(actual_mwh*heat_rate*fuel_price) - 1
    # actual_mwh 를 final_cf 에서 구함: final_cf = cf*(1-outage) → actual_mwh = capacity*8760*final_cf
    print()
    print("[ efficiency_loss 검증 ]")
    print(f"  {'year':<6} {'input%':>10} {'backCalc%':>12}  {'diff':>10}  {'match':>6}")
    print("  " + "-" * 50)
    eff_ok = True
    for yr in CHECK_YEARS:
        if yr not in years_op:
            continue
        i = np.where(years_op == yr)[0][0]
        inp = yearly_physical_adj.get_adjustment_for_year(yr).efficiency_loss
        actual_mwh = capacity_mw * 8760 * final_cf_arr[i]
        base_fuel  = actual_mwh * heat_rate * fuel_price
        back = (fuel_cost_arr[i] / base_fuel - 1.0) if base_fuel > 0 else None
        diff = abs(back - inp) if back is not None else None
        ok = diff is not None and diff < 1e-9
        if not ok:
            eff_ok = False
        print(f"  {yr:<6} {inp*100:>10.6f} {(back*100 if back is not None else float('nan')):>12.6f}"
              f"  {(diff if diff is not None else float('nan')):>10.2e}  {'OK' if ok else 'MISMATCH':>6}")
    print(f"  => {'전체 OK' if eff_ok else 'MISMATCH 있음'}")

    # ── capacity_derate / water_constraint 검증 ───────────────────────
    # final_cf = cf_series * (1 - outage_rate)
    # cf_series = base_cf * (1-derate), capped by water_constraint
    # capacity_derate=0, water=1.0 이므로 cf_series = base_cf 여야 함
    print()
    print("[ capacity_derate / water_constraint 검증 (둘 다 0/1.0 이어야 함) ]")
    print(f"  {'year':<6} {'inp_derate%':>12} {'inp_water':>10} {'implied_cf_series':>18}  {'expected_cf_series':>18}  {'match':>6}")
    print("  " + "-" * 80)
    derate_ok = True
    for yr in CHECK_YEARS:
        if yr not in years_op:
            continue
        i = np.where(years_op == yr)[0][0]
        inp = yearly_physical_adj.get_adjustment_for_year(yr)
        outage_i = inp.outage_rate
        # final_cf = cf_series * (1 - outage)  =>  cf_series = final_cf / (1 - outage)
        implied_cf = final_cf_arr[i] / (1 - outage_i) if (1 - outage_i) > 0 else None
        expected_cf = base_cf * (1 - inp.capacity_derate)
        expected_cf = min(expected_cf, inp.water_constrained_capacity)
        diff = abs(implied_cf - expected_cf) if implied_cf is not None else None
        ok = diff is not None and diff < 1e-9
        if not ok:
            derate_ok = False
        print(f"  {yr:<6} {inp.capacity_derate*100:>12.6f} {inp.water_constrained_capacity:>10.6f}"
              f" {(implied_cf if implied_cf is not None else float('nan')):>18.6f}"
              f"  {expected_cf:>18.6f}"
              f"  {'OK' if ok else 'MISMATCH':>6}")
    print(f"  => {'전체 OK' if derate_ok else 'MISMATCH 있음'}")

    print()
    if outage_ok and eff_ok and derate_ok:
        print("최종 결론: YearlyPhysicalAdjustments 값이 변형 없이 cashflow에 그대로 적용됨.")
    else:
        print("최종 결론: 일부 MISMATCH — 중간 변형 경로 존재.")


if __name__ == "__main__":
    main()

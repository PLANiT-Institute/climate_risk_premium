"""
A vs B 비교: Path A (PLANiT) vs Path B (physical_risk_output.csv)

각 hazard별 수치를 나란히 출력하여 어느 쪽이 더 크고,
실제 캐시플로우에 어느 값이 적용되는지를 확인.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np

TARGET_YEAR = 2050
SCENARIO = "RCP8.5"
START_YEAR = 2025
END_YEAR = 2055


def load_path_a():
    """Path A: PLANiT CSV → PLANiTHazardResult → PLANiTAdapter → PhysicalAdjustments"""
    from src.planit.config import PLANiTIntegrationConfig
    from src.planit.runner import PLANiTRunner
    from src.planit.adapter import PLANiTAdapter

    config = PLANiTIntegrationConfig()
    results_dir = str(config.get_results_dir(str(ROOT)))
    results = PLANiTRunner.load_results_from_csv(results_dir)

    adapter = PLANiTAdapter(config)
    adj = adapter.convert(results, TARGET_YEAR, SCENARIO)

    yearly = adapter.convert_yearly(results, START_YEAR, END_YEAR, SCENARIO)

    return results, adj, yearly


def load_path_b():
    """Path B: physical_risk_output.csv → YearlyPhysicalAdjustments"""
    from src.risk.physical import load_yearly_from_output_csv
    yearly = load_yearly_from_output_csv(start_year=START_YEAR, end_year=END_YEAR)
    return yearly


def print_section(title):
    print(f"\n{'=' * 65}")
    print(f"  {title}")
    print(f"{'=' * 65}")


def main():
    print(f"Target: {SCENARIO} / year={TARGET_YEAR}  (yearly: {START_YEAR}~{END_YEAR})")

    # ---- Path A ----
    print_section("PATH A: PLANiT CSV → PLANiTAdapter")
    try:
        results, adj_a, yearly_a = load_path_a()
        print(f"\n[PLANiTHazardResult 목록]  총 {len(results)}개 항목")
        hz_seen = {}
        for r in results:
            key = (r.hazard_type, r.scenario, r.year)
            if key not in hz_seen:
                hz_seen[key] = r
        col = "  {:<12} {:<10} {:<6} {:>12}  unit={}"
        print(col.format("hazard", "scenario", "year", "value", ""))
        print("  " + "-" * 55)
        for (hz, sc, yr), r in sorted(hz_seen.items()):
            print(col.format(hz, sc, str(yr), f"{r.value:.8f}", r.unit))

        print(f"\n[PhysicalAdjustments @ {TARGET_YEAR}/{SCENARIO}]")
        print(f"  outage_rate              : {adj_a['outage_rate']:.8f}  ({adj_a['outage_rate']*100:.5f}%)")
        print(f"  capacity_derate          : {adj_a['capacity_derate']:.8f}  ({adj_a['capacity_derate']*100:.5f}%)")
        print(f"  efficiency_loss          : {adj_a['efficiency_loss']:.8f}  ({adj_a['efficiency_loss']*100:.5f}%)")
        print(f"  water_constrained_cap    : {adj_a['water_constrained_capacity']:.8f}")
        print(f"  notes                    : {adj_a['notes']}")

        print(f"\n[yearly_a 연도별 샘플 (Path A convert_yearly)]")
        years_a = yearly_a["years"]
        col2 = "  {:<6} {:>12} {:>12} {:>12} {:>12}"
        print(col2.format("year", "outage%", "derate%", "eff_loss%", "water_cap"))
        print("  " + "-" * 57)
        sample_years = [2025, 2030, 2040, 2050, 2055]
        for yr in sample_years:
            if yr in years_a:
                i = np.where(years_a == yr)[0][0]
                print(col2.format(
                    yr,
                    f"{yearly_a['outage_rates'][i]*100:.5f}",
                    f"{yearly_a['capacity_derates'][i]*100:.5f}",
                    f"{yearly_a['efficiency_losses'][i]*100:.5f}",
                    f"{yearly_a['water_constraints'][i]:.6f}",
                ))
    except Exception as e:
        print(f"  Path A 로드 실패: {type(e).__name__}: {e}")
        adj_a = None
        yearly_a = None

    # ---- Path B ----
    print_section("PATH B: physical_risk_output.csv → YearlyPhysicalAdjustments")
    try:
        yearly_b = load_path_b()
        years_b = yearly_b.years
        col2 = "  {:<6} {:>12} {:>12} {:>12} {:>12}"
        print(col2.format("year", "outage%", "derate%", "eff_loss%", "water_cap"))
        print("  " + "-" * 57)
        sample_years = [2025, 2030, 2040, 2050, 2055]
        for yr in sample_years:
            if yr in years_b:
                i = np.where(years_b == yr)[0][0]
                print(col2.format(
                    yr,
                    f"{yearly_b.outage_rates[i]*100:.5f}",
                    f"{yearly_b.capacity_derates[i]*100:.5f}",
                    f"{yearly_b.efficiency_losses[i]*100:.5f}",
                    f"{yearly_b.water_constraints[i]:.6f}",
                ))
    except Exception as e:
        print(f"  Path B 로드 실패: {type(e).__name__}: {e}")
        yearly_b = None

    # ---- A vs B 비교 ----
    print_section(f"A vs B 비교 @ year={TARGET_YEAR}")
    fields = ["outage_rate", "capacity_derate", "efficiency_loss", "water_constrained_capacity"]

    def get_b_val(field, year):
        if yearly_b is None:
            return None
        adj = yearly_b.get_adjustment_for_year(year)
        return getattr(adj, field)

    def get_a_val(field):
        if adj_a is None:
            return None
        return adj_a.get(field)

    col3 = "  {:<30} {:>14} {:>14}  {}"
    print(col3.format("field", "Path A (PLANiT)", "Path B (CSV)", "실제 적용"))
    print("  " + "-" * 68)
    for f in fields:
        a_val = get_a_val(f)
        b_val = get_b_val(f, TARGET_YEAR)
        applied = "Path B (yearly_physical_adj 우선)"
        if b_val is None:
            applied = "Path A (B 없음)"
        a_str = f"{a_val*100:.5f}%" if a_val is not None else "N/A"
        b_str = f"{b_val*100:.5f}%" if b_val is not None and f != "water_constrained_capacity" else (f"{b_val:.6f}" if b_val is not None else "N/A")
        if f == "water_constrained_capacity":
            a_str = f"{a_val:.6f}" if a_val is not None else "N/A"
        print(col3.format(f, a_str, b_str, applied))

    print("\n  * Path B가 있으면 outage/derate/eff_loss/water 모두 Path B 값으로 덮어씀")
    print("  * Path B의 capacity_derate=0, water_constraints=1.0 은 하드코딩 (PLANiT drought/water 무력화)")


if __name__ == "__main__":
    main()

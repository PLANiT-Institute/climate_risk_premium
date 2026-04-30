"""
Deeper inspection of physrisk hello-world results — Phase 1 analysis.

Reads scripts/sandbox/physrisk_probe_results/hello_raw.json and unpacks
calc_details for each hazard × scenario × year combination. Focuses on:
  - RiverineInundation ssp585/2050: why 1.48% AAL for a riverbank plant
  - WaterTemperature ssp585/2050: which indicator, freshwater vs seawater
"""

import json
from pathlib import Path

INPUT_FILE = Path(__file__).parent / "physrisk_probe_results" / "hello_raw.json"

EDGE_N = 3  # how many values to show from each end of a long list

HIGHLIGHTS = {
    ("RiverineInundation", "ssp585", "2050"),
    ("WaterTemperature", "ssp585", "2050"),
}


def _abbrev(lst: list, n: int = EDGE_N) -> str:
    if lst is None:
        return "(none)"
    if len(lst) <= 2 * n:
        return str([round(v, 6) if isinstance(v, float) else v for v in lst])
    head = [round(v, 6) if isinstance(v, float) else v for v in lst[:n]]
    tail = [round(v, 6) if isinstance(v, float) else v for v in lst[-n:]]
    return f"{head} ... {tail}  (len={len(lst)})"


def _print_dist(label: str, dist: dict | None) -> None:
    if not dist:
        return
    edges = dist.get("bin_edges") or dist.get("values") or dist.get("intensity_bin_edges")
    probs = dist.get("probabilities") or dist.get("exceed_probabilities") or dist.get("prob_matrix")
    print(f"    {label}:")
    print(f"      edges  : {_abbrev(edges)}")
    if isinstance(probs, list) and probs and isinstance(probs[0], list):
        # prob_matrix — just show dimensions
        rows, cols = len(probs), len(probs[0])
        print(f"      probs  : [{rows}x{cols} matrix - identity-like]")
    else:
        print(f"      probs  : {_abbrev(probs)}")


def _print_impact(impact: dict, is_highlight: bool) -> None:
    key = impact.get("key", {})
    hazard = key.get("hazard_type", "?")
    scenario = key.get("scenario_id", "?")
    year = key.get("year", "?")
    indicator = impact.get("hazard_indicator_id", "?")
    mean = impact.get("impact_mean")
    std = impact.get("impact_std_deviation")
    itype = impact.get("impact_type", "?")

    flag = "  *** HIGHLIGHT ***" if is_highlight else ""
    print(f"\n{'=' * 70}")
    print(f"  {hazard}  |  {scenario}  |  year={year}{flag}")
    print(f"{'=' * 70}")
    print(f"  indicator  : {indicator}")
    print(f"  type       : {itype}")
    mean_str = f"{mean:.6f}  ({mean * 100:.4f}%)" if isinstance(mean, float) else str(mean)
    std_str = f"{std:.6f}" if isinstance(std, float) else str(std)
    print(f"  mean       : {mean_str}")
    print(f"  std_dev    : {std_str}")

    # impact distribution (output side)
    _print_dist("impact_dist  bin_edges/probs", impact.get("impact_distribution"))

    calc = impact.get("calc_details", {})
    if not calc:
        print("  calc_details: (none)")
        return

    # hazard paths — always show all (usually short)
    paths = calc.get("hazard_path", [])
    if paths:
        print("  hazard_path(s):")
        for p in paths:
            print(f"    {p}")

    # for inundation types: show actual hazard intensity distribution
    haz_dist = calc.get("hazard_distribution")
    if haz_dist:
        _print_dist("hazard_dist  (intensity, m)", haz_dist)

    haz_exc = calc.get("hazard_exceedance")
    if haz_exc:
        _print_dist("hazard_exceedance", haz_exc)

    # vulnerability curve if present
    vuln = calc.get("vulnerability_distribution")
    if vuln:
        _print_dist("vuln_dist  intensity_bins", {"intensity_bin_edges": vuln.get("intensity_bin_edges")})
        _print_dist("vuln_dist  impact_bins   ", {"intensity_bin_edges": vuln.get("impact_bin_edges")})
        prob_matrix = vuln.get("prob_matrix")
        if prob_matrix:
            rows = len(prob_matrix)
            cols = len(prob_matrix[0]) if prob_matrix else 0
            print(f"    vuln_dist  prob_matrix  : [{rows}x{cols} matrix]")


def main() -> None:
    if not INPUT_FILE.exists():
        print(f"File not found: {INPUT_FILE}")
        print("Run physrisk_hello.py first to generate the raw results.")
        raise SystemExit(1)

    raw = json.loads(INPUT_FILE.read_text(encoding="utf-8"))

    asset_list = raw.get("asset_impacts", [])
    if not asset_list:
        print("No asset_impacts in file.")
        raise SystemExit(1)

    impacts = asset_list[0].get("impacts", [])
    print(f"Loaded {INPUT_FILE}")
    print(f"Total impact records: {len(impacts)}")

    # collect unique hazard types for a quick tally first
    seen = {}
    for imp in impacts:
        k = imp.get("key", {})
        hz = k.get("hazard_type", "?")
        sc = k.get("scenario_id", "?")
        yr = k.get("year", "?")
        mean = imp.get("impact_mean")
        seen.setdefault(hz, []).append((sc, yr, mean))

    print("\nQuick tally (hazard → scenario/year/mean):")
    for hz, rows in sorted(seen.items()):
        for sc, yr, mean in rows:
            mean_str = f"{mean * 100:.4f}%" if isinstance(mean, float) else str(mean)
            print(f"  {hz:<25} {sc:<12} {yr:<6} {mean_str}")

    print("\n\nDetailed breakdown:")
    for imp in impacts:
        key = imp.get("key", {})
        hz = key.get("hazard_type", "?")
        sc = key.get("scenario_id", "?")
        yr = key.get("year", "?")
        is_hl = (hz, sc, str(yr)) in HIGHLIGHTS
        _print_impact(imp, is_hl)

    print(f"\n{'=' * 70}")
    print("Done.")


if __name__ == "__main__":
    main()

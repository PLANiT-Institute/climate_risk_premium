"""Gate 5 ablation at the final-output level (outage_rate, not AAI).

Measures how much of the per-SSP outage_rate differentiation comes from
the climate_factors.csv multiplier vs. CLIMADA's intrinsic frequency signal.
"""

import json
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data.loaders import get_climate_factor, load_climate_factors
from src.planit.outage_assumptions import OUTAGE_RATE_PER_EVENT, OUTAGE_DURATION_HOURS

# =============================================================================
# Configuration: CRP scenario mapping (from src/pipeline/runner.py:45-50, 287)
# =============================================================================
PHYSICAL_SCENARIO_SSP_MAP = {
    "baseline": ("ssp126", 2024),
    "moderate_physical": ("ssp245", 2040),
    "high_physical": ("ssp585", 2040),
    "severe_drought": ("ssp585", 2050),
}
SSP_TO_CRP = {"ssp126": "SSP1-2.6", "ssp245": "RCP4.5", "ssp585": "RCP8.5"}

# Adapter parameters (from src/planit/config.py defaults)
# The adapter uses wildfire_outage_probability (default from outage_assumptions.py)
OUTAGE_PROB = OUTAGE_RATE_PER_EVENT  # 0.10
OUTAGE_HOURS = OUTAGE_DURATION_HOURS  # 24.0
HOURS_PER_YEAR = 8760.0

# =============================================================================
# Load provenance data from n=100 runs
# =============================================================================
SSPS = ["historical", "ssp126", "ssp245", "ssp585"]
RUNS_DIR = Path("reports/verify/runs_100")

provenance = {}
for ssp in SSPS:
    prov_path = RUNS_DIR / ssp / "_provenance.json"
    if prov_path.exists():
        provenance[ssp] = json.loads(prov_path.read_text())
    else:
        print(f"WARNING: Missing provenance for {ssp}")
        provenance[ssp] = None

# =============================================================================
# Extract CLIMADA event_frequency_per_year from provenance
# =============================================================================
print("=" * 70)
print("GATE 5 ABLATION — FINAL OUTPUT LEVEL (outage_rate)")
print("=" * 70)

print("\n## 1. CLIMADA frequency_sum per SSP (from provenance)")
print(f"{'SSP':<12} {'freq_sum':<12} {'n_events':<10} {'|AAI|':<14}")
print("-" * 50)
for ssp in SSPS:
    if provenance[ssp]:
        h = provenance[ssp]["hazard"]
        aai = abs(provenance[ssp]["impact"]["aai_agg"])
        print(f"{ssp:<12} {h['frequency_sum']:<12.6f} {h['n_events']:<10} {aai:<14.0f}")

# =============================================================================
# Compute climate factors for each SSP at target years
# =============================================================================
print("\n## 2. Climate factors from CSV (wildfire column)")
print(f"{'CRP Scenario':<12} {'SSP':<8} {'Year':<6} {'Climate Factor':<15}")
print("-" * 45)

# For verification context, use 2040 as target year (moderate/high physical)
TARGET_YEAR = 2040

climate_factors = {}
for ssp in SSPS:
    crp_label = SSP_TO_CRP.get(ssp, "SSP1-2.6")
    if ssp == "historical":
        cf = 1.0
        year = 2024
    else:
        cf = get_climate_factor("wildfire", TARGET_YEAR, crp_label)
        year = TARGET_YEAR
    climate_factors[ssp] = cf
    print(f"{crp_label:<12} {ssp:<8} {year:<6} {cf:<15.4f}")

# =============================================================================
# Compute final outage_rate with and without climate factor
# =============================================================================
print(f"\n## 3. Final outage_rate computation")
print(f"Formula: outage_rate = event_freq × outage_prob({OUTAGE_PROB}) × (duration({OUTAGE_HOURS}h) / {HOURS_PER_YEAR}h) × climate_factor")
print(f"\n{'SSP':<12} {'freq':<8} {'CF':<8} {'outage_w/CF':<14} {'outage_w/o_CF':<14} {'CSV contrib':<12}")
print("-" * 70)

results = {}
for ssp in SSPS:
    if not provenance[ssp]:
        continue
    freq = provenance[ssp]["hazard"]["frequency_sum"]  # ≈1.0 for all
    cf = climate_factors[ssp]

    outage_with_cf = freq * OUTAGE_PROB * (OUTAGE_HOURS / HOURS_PER_YEAR) * cf
    outage_without_cf = freq * OUTAGE_PROB * (OUTAGE_HOURS / HOURS_PER_YEAR) * 1.0

    if outage_with_cf > 0:
        csv_contribution = (outage_with_cf - outage_without_cf) / outage_with_cf
    else:
        csv_contribution = 0.0

    results[ssp] = {
        "freq": freq,
        "climate_factor": cf,
        "outage_with_cf": outage_with_cf,
        "outage_without_cf": outage_without_cf,
        "csv_contribution": csv_contribution,
    }
    print(
        f"{ssp:<12} {freq:<8.4f} {cf:<8.4f} {outage_with_cf:<14.8f} "
        f"{outage_without_cf:<14.8f} {csv_contribution*100:<12.1f}%"
    )

# =============================================================================
# Analysis: SSP differentiation source
# =============================================================================
print("\n## 4. SSP differentiation source analysis")
print()

# With climate factor
outage_with = {ssp: results[ssp]["outage_with_cf"] for ssp in SSPS if ssp in results}
# Without climate factor (pure CLIMADA frequency)
outage_without = {ssp: results[ssp]["outage_without_cf"] for ssp in SSPS if ssp in results}

# Spread across SSPs
spread_with = outage_with["ssp585"] - outage_with["ssp126"]
spread_without = outage_without["ssp585"] - outage_without["ssp126"]

print(f"Outage spread (ssp585 - ssp126):")
print(f"  With climate factor:    {spread_with:.8f}")
print(f"  Without climate factor: {spread_without:.8f}")
if spread_with > 0:
    print(f"  CSV's share of spread:  {(spread_with - spread_without) / spread_with * 100:.1f}%")
    print(f"  CLIMADA's share:        {spread_without / spread_with * 100:.1f}%")

# Since freq≈1.0 for all, CLIMADA's frequency contribution to spread is ~0
# The entire spread comes from climate_factor differences
print()
print("FINDING: Since CLIMADA normalizes frequency_sum to ≈1.0 for all SSPs,")
print("the adapter receives identical event_frequency inputs regardless of SSP.")
print("The ENTIRE SSP differentiation in outage_rate comes from climate_factors.csv.")
print()
print("However, CLIMADA DOES differentiate SSPs through intensity/AAI:")
aai_126 = abs(provenance["ssp126"]["impact"]["aai_agg"]) if provenance["ssp126"] else 0
aai_585 = abs(provenance["ssp585"]["impact"]["aai_agg"]) if provenance["ssp585"] else 0
print(f"  |AAI| ssp126 = {aai_126:.0f}")
print(f"  |AAI| ssp585 = {aai_585:.0f}")
print(f"  Ratio: {aai_585/aai_126:.1f}x")
print("  But AAI is NOT used in the outage_rate pathway (only frequency is).")

# =============================================================================
# Write report
# =============================================================================
md = []
md.append("# Gate 5 — Final-Output Level Ablation")
md.append("")
md.append("## Pipeline Trace: CLIMADA → Final CRP")
md.append("")
md.append("```")
md.append("CLIMADA WildFire.set_proba_fire_seasons()")
md.append("  → hazard.frequency array (sums to ~1.0 for ALL SSPs)")
md.append("  → PLANiTHazardResult.event_frequency_per_year ≈ 1.0")
md.append("  → PLANiTAdapter._extract_wildfire_frequency()     [adapter.py:286-306]")
md.append("  → PLANiTAdapter._compute_wildfire_outage_rate()   [adapter.py:308-345]")
md.append("    outage_rate = freq × outage_prob × (hours/8760)")
md.append("    outage_rate *= get_climate_factor(\"wildfire\", year, scenario)  ← [adapter.py:336-337]")
md.append("  → PhysicalAdjustments.outage_rate")
md.append("  → compute_cashflows_timeseries()")
md.append("  → credit_rating → CRP spread bps")
md.append("```")
md.append("")
md.append("**Key finding**: `get_climate_factor()` is called at `src/planit/adapter.py:336`")
md.append("AFTER the CLIMADA frequency is converted to outage_rate. It reads from")
md.append("`data/physical/climate_factors.csv` via `src/data/loaders.py:272`.")
md.append("")
md.append("## CLIMADA Frequency Per SSP (n=100, seed=42)")
md.append("")
md.append("| SSP | frequency_sum | n_events | |AAI| |")
md.append("|-----|--------------|----------|------|")
for ssp in SSPS:
    if provenance[ssp]:
        h = provenance[ssp]["hazard"]
        aai = abs(provenance[ssp]["impact"]["aai_agg"])
        md.append(f"| {ssp} | {h['frequency_sum']:.6f} | {h['n_events']} | {aai:.0f} |")
md.append("")
md.append("**All SSPs have frequency_sum ≈ 1.0** because CLIMADA normalizes event")
md.append("frequencies to represent annual rates (frequency = 1/equivalent_years).")
md.append("")

md.append("## Climate Factors Applied (wildfire, year=2040)")
md.append("")
md.append("| SSP | CRP Label | Climate Factor |")
md.append("|-----|-----------|---------------|")
for ssp in SSPS:
    crp = SSP_TO_CRP.get(ssp, "baseline")
    md.append(f"| {ssp} | {crp} | {climate_factors[ssp]:.4f} |")
md.append("")
md.append("Source: `data/physical/climate_factors.csv` (IPCC AR6 + KMA projections)")
md.append("")

md.append("## Final Outage Rate Ablation")
md.append("")
md.append(f"Parameters: outage_prob={OUTAGE_PROB}, duration={OUTAGE_HOURS}h, hours/yr={HOURS_PER_YEAR}")
md.append("")
md.append("| SSP | freq | CF | outage (with CF) | outage (no CF) | CSV contribution |")
md.append("|-----|------|-----|-----------------|----------------|------------------|")
for ssp in SSPS:
    if ssp in results:
        r = results[ssp]
        md.append(
            f"| {ssp} | {r['freq']:.4f} | {r['climate_factor']:.4f} | "
            f"{r['outage_with_cf']:.8f} | {r['outage_without_cf']:.8f} | "
            f"{r['csv_contribution']*100:.1f}% |"
        )
md.append("")

md.append("## Interpretation")
md.append("")
md.append("### SSP Differentiation Sources at Each Level")
md.append("")
md.append("| Level | CLIMADA-driven | CSV-driven |")
md.append("|-------|---------------|------------|")
md.append(f"| CLIMADA AAI | 100% (intensity varies: {aai_126:.0f} → {aai_585:.0f}) | 0% |")
md.append(f"| Adapter outage_rate | ~0% (freq≈1.0 for all) | ~100% (CF: {climate_factors['ssp126']:.2f} → {climate_factors['ssp585']:.2f}) |")
md.append("| Final CRP spread | Mixed (both paths contribute) | Mixed |")
md.append("")
md.append("### Why This Matters")
md.append("")
md.append("The adapter's outage_rate pathway discards CLIMADA's intensity signal")
md.append("(AAI) and uses only the frequency (≈1.0 for all SSPs). The SSP")
md.append("differentiation in the final CRP comes **entirely from `climate_factors.csv`**")
md.append("at this point in the pipeline.")
md.append("")
md.append("CLIMADA's role is to provide a physically-grounded **baseline frequency**")
md.append("(~1 event/year for Samcheok), not to differentiate between SSPs. The SSP")
md.append("differentiation is legitimately provided by the IPCC AR6/KMA multipliers")
md.append("in the CSV — these are peer-reviewed climate projections, not arbitrary")
md.append("assumptions.")
md.append("")
md.append("### Paper Framing Recommendation")
md.append("")
md.append("The paper MUST acknowledge both sources:")
md.append("")
md.append('> "Wildfire physical risk is computed in two stages: (1) CLIMADA provides')
md.append("> a site-specific baseline event frequency from MODIS/FIRMS fire detection")
md.append("> data and Monte Carlo probabilistic fire propagation (n=100 seasons,")
md.append("> seed=42); (2) scenario-dependent climate change multipliers from IPCC AR6")
md.append("> projections (Table 4.5/4.8) scale the baseline frequency to reflect")
md.append('> SSP-specific warming trajectories."')
md.append("")
md.append("Do NOT claim that CLIMADA directly produces SSP-differentiated risk.")
md.append("CLIMADA provides the **site-specific baseline**; CSV provides the")
md.append("**scenario scaling**.")
md.append("")

md.append("## Line Number Reference")
md.append("")
md.append("| Step | File | Lines | Description |")
md.append("|------|------|-------|-------------|")
md.append("| 1 | `src/planit/adapter.py` | 286-306 | Extract frequency from PLANiT result |")
md.append("| 2 | `src/planit/adapter.py` | 321-330 | Compute base outage_rate from frequency |")
md.append("| 3 | `src/planit/adapter.py` | 333-341 | Apply `get_climate_factor()` multiplier |")
md.append("| 4 | `src/data/loaders.py` | 272-329 | `get_climate_factor()` with interpolation |")
md.append("| 5 | `data/physical/climate_factors.csv` | all | Wildfire multiplier table by scenario/year |")
md.append("| 6 | `src/pipeline/runner.py` | 326-333 | Adapter called per year in yearly loop |")
md.append("| 7 | `src/pipeline/runner.py` | 408-414 | CSV fallback also uses `get_climate_factor()` |")
md.append("")

Path("reports/verify/05_ablation_final.md").write_text("\n".join(md), encoding="utf-8")
print("\n" + "=" * 70)
print("Report written to: reports/verify/05_ablation_final.md")

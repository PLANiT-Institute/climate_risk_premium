#!/usr/bin/env python3
"""
Physical Risk Model - Simple Demo.

This script demonstrates the simplified physical risk model
for the Samcheok Blue Power Plant.

Run: python -m src.climada.demo
"""
from .literature_parameters import (
    WILDFIRE_BASE_RATE,
    FLOOD_BASE_RATE,
    SLR_DERATE_PER_METER,
    calculate_physical_risk,
    PROJECTIONS,
)


def main():
    """Run the physical risk model demo."""
    print("=" * 70)
    print("PHYSICAL RISK MODEL - SAMCHEOK BLUE POWER PLANT (2.1 GW Coal)")
    print("=" * 70)

    # =========================================================================
    # Section 1: Baseline Parameters
    # =========================================================================
    print("\n1. BASELINE PARAMETERS (2024)")
    print("-" * 50)
    print(f"   Wildfire outage rate:  {WILDFIRE_BASE_RATE:.5f}  ({WILDFIRE_BASE_RATE*100:.4f}%)")
    print(f"   Flood outage rate:     {FLOOD_BASE_RATE:.6f}  ({FLOOD_BASE_RATE*100:.5f}%)")
    print(f"   SLR derate per meter:  {SLR_DERATE_PER_METER:.4f}  ({SLR_DERATE_PER_METER*100:.3f}%)")

    print("\n   Sources:")
    print("   - Wildfire: Kim et al. (2025) Natural Hazards")
    print("   - Flood:    Kim et al. (2024) Water")
    print("   - SLR:      Van Vliet et al. (2016) Nature Climate Change")

    # =========================================================================
    # Section 2: Climate Projections
    # =========================================================================
    print("\n2. CLIMATE PROJECTIONS")
    print("-" * 50)

    print("\n   RCP 4.5 (Moderate Climate Change):")
    for key in ["rcp45_2030", "rcp45_2040", "rcp45_2050", "rcp45_2060"]:
        proj = PROJECTIONS[key]
        print(f"     {proj.year}: Wildfire {proj.wildfire_multiplier:.1f}x, "
              f"SLR {proj.slr_meters:.2f}m, Compound {proj.compound_multiplier:.2f}x")

    print("\n   RCP 8.5 (High Climate Change):")
    for key in ["rcp85_2030", "rcp85_2040", "rcp85_2050", "rcp85_2060"]:
        proj = PROJECTIONS[key]
        print(f"     {proj.year}: Wildfire {proj.wildfire_multiplier:.1f}x, "
              f"SLR {proj.slr_meters:.2f}m, Compound {proj.compound_multiplier:.2f}x")

    # =========================================================================
    # Section 3: Calculated Physical Risk
    # =========================================================================
    print("\n3. CALCULATED PHYSICAL RISK")
    print("-" * 50)

    scenarios = [
        (2024, "current", "Baseline"),
        (2030, "RCP4.5", "RCP4.5 2030"),
        (2050, "RCP4.5", "RCP4.5 2050"),
        (2060, "RCP4.5", "RCP4.5 2060"),
        (2030, "RCP8.5", "RCP8.5 2030"),
        (2050, "RCP8.5", "RCP8.5 2050"),
        (2060, "RCP8.5", "RCP8.5 2060"),
    ]

    print(f"\n   {'Scenario':<15} {'Wildfire':>10} {'Flood':>10} {'SLR':>10} {'Total CF':>12}")
    print("   " + "-" * 57)

    for year, rcp, name in scenarios:
        r = calculate_physical_risk(year, rcp)
        print(f"   {name:<15} {r.wildfire_rate*100:>9.4f}% {r.flood_rate*100:>9.5f}% "
              f"{r.slr_derate*100:>9.4f}% {r.cf_reduction*100:>11.4f}%")

    # =========================================================================
    # Section 4: Key Insights
    # =========================================================================
    print("\n4. KEY INSIGHTS")
    print("-" * 50)
    print("""
   PHYSICAL RISK IS MODEST:
   - Baseline 2024:     ~0.06% capacity factor reduction
   - RCP4.5 2060:       ~0.16% (moderate climate)
   - RCP8.5 2060:       ~0.44% (high climate, worst-case)

   CONTEXT:
   - These values are Korea-specific (not California)
   - Wildfire is the dominant risk driver
   - Flood risk is minimal (plant elevation ~10m)
   - Transition risk >> Physical risk for coal plants

   FINANCIAL IMPACT:
   - DSCR impact: <0.01x (negligible)
   - Credit spread impact: <5 bps even worst-case
   - Policy phase-out risk is far more significant
    """)

    print("=" * 70)
    print("For visualizations, run: python -m src.climada.visualize_physical_risk")
    print("=" * 70)


if __name__ == "__main__":
    main()

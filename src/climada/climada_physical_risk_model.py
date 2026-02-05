"""
CLIMADA Physical Risk Model for Samcheok Blue Power Plant.

This model reads ALL inputs from CSV files:
- input/climada_data.csv: CLIMADA API outputs
- input/literature_data.csv: Verified literature values
- input/model_assumptions.csv: Modeling assumptions

Run: python -m src.climada.climada_physical_risk_model

Version: 2.0 (CSV-based pipeline)
<<<<<<< HEAD
=======
Date: December 29, 2024
>>>>>>> 7b1507166a09149c835e7a055a114db44cb2809e
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd


# =============================================================================
# PATHS
# =============================================================================

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "physical_risk_steps"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class HazardResult:
    """Result from hazard analysis."""
    hazard_type: str
    base_outage_rate: float
    climate_factor: float
    projected_outage_rate: float
    source: str
    status: str


@dataclass
class TemperatureResult:
    """Temperature efficiency impact."""
    year: int
    delta_t: float
    mean_temp_derate: float
    heat_wave_derate: float
    total_temp_derate: float


@dataclass
class PhysicalRiskSummary:
    """Complete physical risk summary."""
    year: int
    scenario: str
    wildfire: HazardResult
    tropical_cyclone: HazardResult
    river_flood: HazardResult
    temperature: TemperatureResult
    sea_level_rise_m: float
    total_acute_outage: float
    total_chronic_derate: float
    total_physical_risk: float


# =============================================================================
# DATA LOADING FUNCTIONS
# =============================================================================

def load_climada_data() -> pd.DataFrame:
    """Load CLIMADA API data from CSV."""
    path = INPUT_DIR / "climada_data.csv"
    print(f"Loading CLIMADA data from: {path}")
    return pd.read_csv(path)


def load_literature_data() -> pd.DataFrame:
    """Load literature values from CSV."""
    path = INPUT_DIR / "literature_data.csv"
    print(f"Loading literature data from: {path}")
    return pd.read_csv(path)


def load_assumptions() -> pd.DataFrame:
    """Load model assumptions from CSV."""
    path = INPUT_DIR / "model_assumptions.csv"
    print(f"Loading assumptions from: {path}")
    return pd.read_csv(path)


def get_literature_value(df: pd.DataFrame, category: str, parameter: str,
                         year: Optional[int] = None) -> float:
    """Extract a specific value from literature data."""
    mask = (df['category'] == category) & (df['parameter'] == parameter)
    if year is not None:
        # Try exact year match first
        year_mask = mask & (df['year'].astype(str) == str(year))
        if year_mask.any():
            return df.loc[year_mask, 'value'].iloc[0]
        # Fall back to 'all' if no year-specific value
        year_mask = mask & (df['year'].astype(str) == 'all')
        if year_mask.any():
            return df.loc[year_mask, 'value'].iloc[0]
    return df.loc[mask, 'value'].iloc[0]


def get_assumption(df: pd.DataFrame, parameter: str) -> float:
    """Extract a specific assumption value."""
    mask = df['parameter'] == parameter
    return df.loc[mask, 'value'].iloc[0]


# =============================================================================
# CALCULATION FUNCTIONS
# =============================================================================

def calculate_base_outage_rates(climada_df: pd.DataFrame,
                                 assumptions_df: pd.DataFrame) -> Dict[str, HazardResult]:
    """Calculate base outage rates from CLIMADA data."""
    results = {}
    hours_per_year = get_assumption(assumptions_df, 'hours_per_year')

    # Wildfire
    wf_row = climada_df[climada_df['hazard'] == 'wildfire'].iloc[0]
    wf_events = wf_row['events_at_location']
    wf_years = wf_row['years_covered']
    wf_prob = get_assumption(assumptions_df, 'outage_prob_wildfire')
    wf_duration = get_assumption(assumptions_df, 'outage_duration_wildfire')

    wf_annual_freq = wf_events / wf_years
    wf_base_rate = wf_annual_freq * wf_prob * (wf_duration / hours_per_year)

    results['wildfire'] = HazardResult(
        hazard_type="Wildfire",
        base_outage_rate=wf_base_rate,
        climate_factor=1.0,
        projected_outage_rate=wf_base_rate,
        source=f"CLIMADA: {wf_events} events / {wf_years} years",
        status="API_OUTPUT + ASSUMPTION"
    )

    # Tropical Cyclone (damaging events only)
    tc_row = climada_df[climada_df['hazard'] == 'tropical_cyclone_damaging'].iloc[0]
    tc_events = tc_row['events_at_location']
    tc_years = tc_row['years_covered']
    tc_prob = get_assumption(assumptions_df, 'outage_prob_tc')
    tc_duration = get_assumption(assumptions_df, 'outage_duration_tc')

    tc_annual_freq = tc_events / tc_years
    tc_base_rate = tc_annual_freq * tc_prob * (tc_duration / hours_per_year)

    results['tropical_cyclone'] = HazardResult(
        hazard_type="Tropical Cyclone",
        base_outage_rate=tc_base_rate,
        climate_factor=1.0,
        projected_outage_rate=tc_base_rate,
        source=f"CLIMADA: {tc_events} damaging events / {tc_years} years",
        status="API_OUTPUT + ASSUMPTION"
    )

    # River Flood
    fl_row = climada_df[climada_df['hazard'] == 'river_flood_rcp85'].iloc[0]
    fl_events = fl_row['events_at_location']

    results['river_flood'] = HazardResult(
        hazard_type="River Flood",
        base_outage_rate=0.0,
        climate_factor=1.0,
        projected_outage_rate=0.0,
        source=f"CLIMADA: {fl_events} events (riverine only, 10m elevation)",
        status="API_OUTPUT"
    )

    return results


def calculate_temperature_impact(year: int, lit_df: pd.DataFrame,
                                  assumptions_df: pd.DataFrame) -> TemperatureResult:
    """Calculate temperature efficiency derate for given year."""
    hours_per_year = get_assumption(assumptions_df, 'hours_per_year')

    # Get temperature change
    if year == 2024:
        delta_t = 0.0
    elif year == 2030:
        delta_t = get_literature_value(lit_df, 'TEMPERATURE', 'korea_temp_change', 2030)
    elif year <= 2050:
        delta_t = get_literature_value(lit_df, 'TEMPERATURE', 'korea_temp_change', '2026-2050')
    else:
        delta_t = get_literature_value(lit_df, 'TEMPERATURE', 'korea_temp_change', '2076-2100')

    # Get derate factors
    ambient_derate = get_literature_value(lit_df, 'EFFICIENCY', 'ambient_derate_model')
    cooling_derate = get_literature_value(lit_df, 'EFFICIENCY', 'cooling_water_derate')
    sst_ratio = get_literature_value(lit_df, 'EFFICIENCY', 'sst_air_ratio')

    # Combined derate (convert from %/C to fraction)
    combined_derate_per_c = (ambient_derate + sst_ratio * cooling_derate) / 100
    mean_temp_derate = delta_t * combined_derate_per_c

    # Heat wave derate
    hw_days_base = get_literature_value(lit_df, 'HEATWAVE', 'days_baseline', 2024)
    hw_days_2100 = get_literature_value(lit_df, 'HEATWAVE', 'days_future', 2100)
    hw_efficiency_loss = get_literature_value(lit_df, 'HEATWAVE', 'efficiency_loss') / 100

    # Interpolate heat wave days
    if year <= 2024:
        hw_days = hw_days_base
    elif year >= 2100:
        hw_days = hw_days_2100
    else:
        hw_days = hw_days_base + (hw_days_2100 - hw_days_base) * (year - 2024) / (2100 - 2024)

    hw_hours = hw_days * 24
    heat_wave_derate = (hw_hours / hours_per_year) * hw_efficiency_loss

    total = mean_temp_derate + heat_wave_derate

    return TemperatureResult(
        year=year,
        delta_t=delta_t,
        mean_temp_derate=mean_temp_derate,
        heat_wave_derate=heat_wave_derate,
        total_temp_derate=total
    )


def get_climate_factor(lit_df: pd.DataFrame, category: str, year: int) -> float:
    """Get climate factor for a hazard at given year."""
    return get_literature_value(lit_df, category, 'climate_factor', year)


def get_slr(lit_df: pd.DataFrame, year: int) -> float:
    """Get sea level rise projection for given year."""
    return get_literature_value(lit_df, 'SLR', 'korea_projection', year)


def calculate_physical_risk(year: int, scenario: str = "RCP8.5") -> PhysicalRiskSummary:
    """Calculate complete physical risk for given year."""

    # Load all data from CSV files
    climada_df = load_climada_data()
    lit_df = load_literature_data()
    assumptions_df = load_assumptions()

    # Calculate base rates from CLIMADA
    base_rates = calculate_base_outage_rates(climada_df, assumptions_df)

    # Apply climate factors from literature
    wf_factor = get_climate_factor(lit_df, 'WILDFIRE', year)
    tc_factor = get_climate_factor(lit_df, 'TC', year)

    wildfire = HazardResult(
        hazard_type="Wildfire",
        base_outage_rate=base_rates['wildfire'].base_outage_rate,
        climate_factor=wf_factor,
        projected_outage_rate=base_rates['wildfire'].base_outage_rate * wf_factor,
        source=base_rates['wildfire'].source + f" × WWA factor {wf_factor}x",
        status="VERIFIED" if year in [2050, 2100] else "ASSUMPTION"
    )

    tropical_cyclone = HazardResult(
        hazard_type="Tropical Cyclone",
        base_outage_rate=base_rates['tropical_cyclone'].base_outage_rate,
        climate_factor=tc_factor,
        projected_outage_rate=base_rates['tropical_cyclone'].base_outage_rate * tc_factor,
        source=base_rates['tropical_cyclone'].source + f" × Knutson factor {tc_factor}x",
        status="DERIVED" if year == 2050 else "ASSUMPTION"
    )

    river_flood = base_rates['river_flood']

    # Temperature impact
    temperature = calculate_temperature_impact(year, lit_df, assumptions_df)

    # Sea level rise
    slr = get_slr(lit_df, year)

    # Totals
    total_acute = wildfire.projected_outage_rate + tropical_cyclone.projected_outage_rate + river_flood.projected_outage_rate
    total_chronic = temperature.total_temp_derate
    total_risk = total_acute + total_chronic

    return PhysicalRiskSummary(
        year=year,
        scenario=scenario,
        wildfire=wildfire,
        tropical_cyclone=tropical_cyclone,
        river_flood=river_flood,
        temperature=temperature,
        sea_level_rise_m=slr,
        total_acute_outage=total_acute,
        total_chronic_derate=total_chronic,
        total_physical_risk=total_risk
    )


def save_output(results: List[PhysicalRiskSummary]):
    """Save results to CSV."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "physical_risk_output.csv"

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'year', 'scenario',
            'wildfire_base_pct', 'wildfire_factor', 'wildfire_projected_pct', 'wildfire_status',
            'tc_base_pct', 'tc_factor', 'tc_projected_pct', 'tc_status',
            'flood_pct',
            'temp_delta_c', 'temp_mean_derate_pct', 'temp_heatwave_pct', 'temp_total_pct',
            'slr_m',
            'total_acute_pct', 'total_chronic_pct', 'total_risk_pct'
        ])

        for r in results:
            writer.writerow([
                r.year, r.scenario,
                f"{r.wildfire.base_outage_rate:.6f}",
                f"{r.wildfire.climate_factor:.2f}",
                f"{r.wildfire.projected_outage_rate:.6f}",
                r.wildfire.status,
                f"{r.tropical_cyclone.base_outage_rate:.6f}",
                f"{r.tropical_cyclone.climate_factor:.2f}",
                f"{r.tropical_cyclone.projected_outage_rate:.6f}",
                r.tropical_cyclone.status,
                f"{r.river_flood.projected_outage_rate:.6f}",
                f"{r.temperature.delta_t:.2f}",
                f"{r.temperature.mean_temp_derate:.6f}",
                f"{r.temperature.heat_wave_derate:.6f}",
                f"{r.temperature.total_temp_derate:.6f}",
                f"{r.sea_level_rise_m:.2f}",
                f"{r.total_acute_outage:.6f}",
                f"{r.total_chronic_derate:.6f}",
                f"{r.total_physical_risk:.6f}"
            ])

    print(f"\nOutput saved to: {output_file}")


def run_full_analysis():
    """Run complete physical risk analysis."""
    print("=" * 70)
    print("CLIMADA PHYSICAL RISK MODEL v2.0")
    print("CSV-Based Data Pipeline")
    print("=" * 70)
    print("\nSamcheok Blue Power Plant (37.4404°N, 129.1671°E)")
    print("Scenario: RCP8.5 / SSP5-8.5")
    print()

    # Load data
    print("--- LOADING DATA FROM CSV FILES ---")
    climada_df = load_climada_data()
    lit_df = load_literature_data()
    assumptions_df = load_assumptions()

    print(f"  CLIMADA data: {len(climada_df)} records")
    print(f"  Literature data: {len(lit_df)} records")
    print(f"  Assumptions: {len(assumptions_df)} records")

    # Run for each year
    years = [2024, 2030, 2050, 2100]
    results = []

    for year in years:
        print(f"\n{'='*70}")
        print(f"YEAR: {year}")
        print('='*70)

        result = calculate_physical_risk(year)
        results.append(result)

        print(f"\n--- ACUTE HAZARDS ---")
        print(f"  Wildfire:     {result.wildfire.base_outage_rate:.4%} × {result.wildfire.climate_factor:.1f}x = {result.wildfire.projected_outage_rate:.4%} [{result.wildfire.status}]")
        print(f"  TC:           {result.tropical_cyclone.base_outage_rate:.4%} × {result.tropical_cyclone.climate_factor:.2f}x = {result.tropical_cyclone.projected_outage_rate:.4%} [{result.tropical_cyclone.status}]")
        print(f"  River Flood:  {result.river_flood.projected_outage_rate:.4%} [{result.river_flood.status}]")

        print(f"\n--- CHRONIC IMPACTS ---")
        print(f"  Temperature:  +{result.temperature.delta_t:.2f}°C → {result.temperature.total_temp_derate:.4%} derate")
        print(f"    - Mean temp:   {result.temperature.mean_temp_derate:.4%}")
        print(f"    - Heat waves:  {result.temperature.heat_wave_derate:.4%}")
        print(f"  Sea Level:    {result.sea_level_rise_m:.2f}m")

        print(f"\n--- TOTALS ---")
        print(f"  Acute:   {result.total_acute_outage:.4%}")
        print(f"  Chronic: {result.total_chronic_derate:.4%}")
        print(f"  TOTAL:   {result.total_physical_risk:.4%}")

    # Summary table
    print("\n" + "=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)
    print(f"\n{'Year':<8} {'Wildfire':>10} {'TC':>10} {'Flood':>10} {'Temp':>10} {'SLR':>8} {'TOTAL':>10}")
    print("-" * 70)

    for r in results:
        print(f"{r.year:<8} {r.wildfire.projected_outage_rate:>9.4%} {r.tropical_cyclone.projected_outage_rate:>9.4%} "
              f"{r.river_flood.projected_outage_rate:>9.4%} {r.temperature.total_temp_derate:>9.4%} "
              f"{r.sea_level_rise_m:>7.2f}m {r.total_physical_risk:>9.4%}")

    # Save output
    save_output(results)

    # Data flow summary
    print("\n" + "=" * 70)
    print("DATA FLOW")
    print("=" * 70)
    print("""
    INPUT FILES:
    ├── input/climada_data.csv      → CLIMADA API outputs
    ├── input/literature_data.csv   → Verified literature values
    └── input/model_assumptions.csv → Modeling assumptions

    PROCESSING:
    ├── Base rates = CLIMADA events × assumptions
    ├── Climate factors = Literature values
    └── Temperature = Literature + assumptions

    OUTPUT:
    └── output/physical_risk_output.csv
    """)

    return results


# =============================================================================
# EXPORTS
# =============================================================================

# Location constants (for external use)
SAMCHEOK_LAT = 37.4404
SAMCHEOK_LON = 129.1671

# Climate factors (loaded from CSV when needed)
def get_climate_factors():
    """Load climate factors from literature CSV."""
    lit_df = load_literature_data()
    factors = {}
    for year in [2024, 2030, 2050, 2100]:
        factors[year] = {
            'wildfire': get_climate_factor(lit_df, 'WILDFIRE', year),
            'tc': get_climate_factor(lit_df, 'TC', year)
        }
    return factors

WILDFIRE_CLIMATE_FACTORS = None  # Load lazily
TC_CLIMATE_FACTORS = None
KOREA_TEMP_PROJECTIONS_RCP85 = None
SLR_PROJECTIONS_M = None


if __name__ == "__main__":
    run_full_analysis()

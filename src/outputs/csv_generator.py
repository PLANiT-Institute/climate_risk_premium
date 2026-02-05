"""
Output CSV Generators for each module.

Generates long-format CSV files with year-by-year results:
- transition_results.csv: Transition risk impacts (capacity factor, carbon prices)
- physical_results.csv: Physical risk impacts (outage, derate)
- cashflow_results.csv: Cash flow calculations (revenue, costs, EBITDA)
- credit_results.csv: Credit rating assessments (DSCR, rating, spread)
- model_results.csv: Combined final results
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
import numpy as np

try:
    import numpy_financial as npf
except ImportError:
    npf = None

from src.data_loader import DataLoader, PhysicalScenario


# =============================================================================
# TRANSITION RESULTS GENERATOR
# =============================================================================

def generate_transition_results(
    loader: DataLoader,
    scenario_name: str = "baseline",
    power_plan_scenario: str = None,
    start_year: int = 2024,
    end_year: int = 2064,
) -> pd.DataFrame:
    """Generate year-by-year transition risk impacts."""
    plant = loader.load_plant_parameters()
    transitions = loader.load_transition_scenarios()
    power_plan = loader.load_korea_power_plan()
    market = loader.load_market_scenarios()
    
    transition = transitions.get(scenario_name, transitions['baseline'])
    
    # Get market scenario for carbon prices
    market_baseline = market.get('baseline', [])
    carbon_prices_by_year = {m.year: m.carbon_price_usd_ton for m in market_baseline}
    
    # Get power plan dispatch trajectory if specified
    cf_trajectory = {}
    if power_plan_scenario:
        plan_data = power_plan[power_plan['scenario_type'].str.contains(
            power_plan_scenario.replace('official_', ''), case=False, na=False
        )]
        if plan_data.empty:
            plan_data = power_plan[power_plan['policy_reference'].str.contains(
                power_plan_scenario.replace('official_', '').replace('_', ' '), case=False, na=False
            )]
        if not plan_data.empty:
            cf_trajectory = dict(zip(plan_data['year'].astype(int), plan_data['implied_cf_samcheok']))
    
    rows = []
    base_cf = plant.capacity_factor
    retirement_year = start_year + transition.retirement_years
    
    for year in range(start_year, end_year + 1):
        # Determine capacity factor
        if year in cf_trajectory:
            cf = cf_trajectory[year]
        else:
            years_elapsed = year - start_year
            penalty_factor = min(1.0, years_elapsed / 10) * transition.dispatch_penalty
            cf = max(0, base_cf - penalty_factor)
        
        operating = 1 if year < retirement_year and cf > 0.01 else 0
        
        # Get carbon price
        carbon_price = carbon_prices_by_year.get(year, 0)
        if not carbon_price and carbon_prices_by_year:
            known_years = sorted(carbon_prices_by_year.keys())
            if year < known_years[0]:
                carbon_price = carbon_prices_by_year[known_years[0]]
            elif year > known_years[-1]:
                carbon_price = carbon_prices_by_year[known_years[-1]]
        
        rows.append({
            'scenario': scenario_name,
            'power_plan': power_plan_scenario or 'none',
            'year': year,
            'capacity_factor': cf if operating else 0,
            'dispatch_penalty': transition.dispatch_penalty,
            'carbon_price_usd_ton': carbon_price,
            'operating_flag': operating,
            'policy_reference': transition.description,
        })
    
    return pd.DataFrame(rows)


# =============================================================================
# PHYSICAL RESULTS GENERATOR
# =============================================================================

def generate_physical_results(
    loader: DataLoader,
    scenario_name: str = "baseline",
    start_year: int = 2024,
    end_year: int = 2064,
) -> pd.DataFrame:
    """Generate year-by-year physical risk impacts."""
    physicals = loader.load_physical_scenarios()
    
    # Get base scenario
    base_scenario = physicals.get(scenario_name, physicals.get('baseline'))
    
    rows = []
    for year in range(start_year, end_year + 1):
        phys = base_scenario
        
        rows.append({
            'scenario': scenario_name,
            'year': year,
            'wildfire_outage_rate': phys.wildfire_outage_rate,
            'flood_outage_rate': phys.flood_outage_rate,
            'slr_capacity_derate': phys.slr_capacity_derate,
            'compound_multiplier': phys.compound_multiplier,
            'total_outage_rate': phys.total_outage_rate,
            'total_capacity_derate': phys.total_capacity_derate,
            'fwi_index': phys.fwi_index,
            'slr_meters': phys.slr_meters,
            'data_source': phys.data_source,
        })
    
    return pd.DataFrame(rows)


# =============================================================================
# CASHFLOW RESULTS GENERATOR
# =============================================================================

def generate_cashflow_results(
    loader: DataLoader,
    transition_df: pd.DataFrame,
    physical_df: pd.DataFrame,
    start_year: int = 2024,
) -> pd.DataFrame:
    """Generate year-by-year cashflow results."""
    plant = loader.load_plant_parameters()
    market_scenarios = loader.load_market_scenarios()
    
    market_data = market_scenarios.get('baseline', [])
    market_by_year = {m.year: m for m in market_data}
    
    capacity_mw = plant.capacity_mw
    total_capex = plant.total_capex_million * 1e6
    debt_fraction = plant.debt_fraction
    debt_rate = plant.debt_interest_rate
    debt_tenor = plant.debt_tenor_years
    tax_rate = plant.tax_rate
    fixed_opex = plant.fixed_opex_per_kw * capacity_mw * 1000
    variable_opex_rate = plant.variable_opex_per_mwh
    heat_rate = plant.heat_rate_mmbtu_mwh
    emissions_rate = plant.emissions_tCO2_per_mwh
    
    debt_amount = total_capex * debt_fraction
    if npf:
        annual_ds = -npf.pmt(debt_rate, debt_tenor, debt_amount)
    else:
        annual_ds = debt_amount * (debt_rate * (1 + debt_rate)**debt_tenor) / ((1 + debt_rate)**debt_tenor - 1)
    depreciation_annual = total_capex / plant.operating_years
    
    rows = []
    
    for _, t_row in transition_df.iterrows():
        year = t_row['year']
        scenario = t_row['scenario']
        cf_transition = t_row['capacity_factor']
        operating = t_row['operating_flag']
        carbon_price = t_row['carbon_price_usd_ton']
        
        p_row = physical_df[physical_df['year'] == year]
        if len(p_row) > 0:
            outage_rate = p_row.iloc[0]['total_outage_rate']
            capacity_derate = p_row.iloc[0]['total_capacity_derate']
        else:
            outage_rate, capacity_derate = 0, 0
        
        cf_effective = cf_transition * (1 - outage_rate) * (1 - capacity_derate)
        hours_per_year = 8760
        generation_mwh = capacity_mw * cf_effective * hours_per_year * operating
        
        if year in market_by_year:
            power_price = market_by_year[year].smp_usd_mwh
            coal_price_ton = market_by_year[year].coal_price_usd_ton
        else:
            power_price = plant.power_price_per_mwh
            coal_price_ton = 120
        
        coal_price_mmbtu = coal_price_ton / 25
        fuel_cost = heat_rate * generation_mwh * coal_price_mmbtu
        revenue = generation_mwh * power_price
        carbon_cost = generation_mwh * emissions_rate * carbon_price
        opex = fixed_opex + variable_opex_rate * generation_mwh
        ebitda = revenue - fuel_cost - carbon_cost - opex
        
        years_since_start = year - start_year
        if 0 <= years_since_start < debt_tenor:
            interest_expense = debt_amount * debt_rate * (1 - years_since_start / debt_tenor)
            debt_service = annual_ds
        else:
            interest_expense, debt_service = 0, 0
        
        ebt = ebitda - depreciation_annual - interest_expense
        taxes = max(0, ebt * tax_rate)
        fcf = ebitda - interest_expense - taxes
        
        rows.append({
            'scenario': scenario,
            'year': year,
            'operating_flag': operating,
            'capacity_factor_effective': cf_effective,
            'generation_mwh': generation_mwh,
            'power_price_usd_mwh': power_price,
            'revenue_usd': revenue,
            'fuel_cost_usd': fuel_cost,
            'carbon_cost_usd': carbon_cost,
            'opex_usd': opex,
            'ebitda_usd': ebitda,
            'depreciation_usd': depreciation_annual,
            'interest_usd': interest_expense,
            'debt_service_usd': debt_service,
            'ebt_usd': ebt,
            'taxes_usd': taxes,
            'fcf_usd': fcf,
        })
    
    return pd.DataFrame(rows)


# =============================================================================
# CREDIT RESULTS GENERATOR
# =============================================================================

def generate_credit_results(
    loader: DataLoader,
    cashflow_df: pd.DataFrame,
) -> pd.DataFrame:
    """Generate year-by-year credit rating assessments."""
    plant = loader.load_plant_parameters()
    credit_grid = loader.load_credit_rating_grid()
    
    rating_order = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B']
    
    def dscr_to_rating(dscr: float) -> str:
        thresholds = credit_grid.thresholds.get('ebitda_to_interest', {})
        for rating in rating_order:
            if dscr >= thresholds.get(rating, 0):
                return rating
        return 'B'
    
    rows = []
    
    for _, cf_row in cashflow_df.iterrows():
        year = cf_row['year']
        scenario = cf_row['scenario']
        ebitda = cf_row['ebitda_usd']
        interest = cf_row['interest_usd']
        debt_service = cf_row['debt_service_usd']
        
        dscr = ebitda / debt_service if debt_service > 0 else (999 if ebitda > 0 else 0)
        ebitda_to_interest = ebitda / interest if interest > 0 else (999 if ebitda > 0 else 0)
        
        rating = dscr_to_rating(ebitda_to_interest)
        spread_bps = credit_grid.spreads.get(rating, 600)
        cost_of_debt = plant.risk_free_rate + spread_bps / 10000
        
        rows.append({
            'scenario': scenario,
            'year': year,
            'ebitda_usd': ebitda,
            'interest_usd': interest,
            'debt_service_usd': debt_service,
            'dscr': min(dscr, 999),
            'ebitda_to_interest': min(ebitda_to_interest, 999),
            'credit_rating': rating,
            'spread_bps': spread_bps,
            'cost_of_debt': cost_of_debt,
        })
    
    return pd.DataFrame(rows)


# =============================================================================
# COMBINED FINAL RESULTS
# =============================================================================

def generate_model_results(
    transition_df: pd.DataFrame,
    physical_df: pd.DataFrame,
    cashflow_df: pd.DataFrame,
    credit_df: pd.DataFrame,
) -> pd.DataFrame:
    """Combine all module results into final comprehensive output."""
    result = transition_df.merge(
        physical_df, on=['year'], how='left', suffixes=('', '_physical')
    )
    result = result.merge(
        cashflow_df, on=['scenario', 'year'], how='left', suffixes=('', '_cashflow')
    )
    result = result.merge(
        credit_df, on=['scenario', 'year'], how='left', suffixes=('', '_credit')
    )
    
    cols_to_keep = [
        'scenario', 'power_plan', 'year',
        'capacity_factor', 'dispatch_penalty', 'carbon_price_usd_ton', 'operating_flag',
        'wildfire_outage_rate', 'flood_outage_rate', 'slr_capacity_derate',
        'total_outage_rate', 'total_capacity_derate',
        'capacity_factor_effective', 'generation_mwh', 'revenue_usd', 
        'fuel_cost_usd', 'carbon_cost_usd', 'opex_usd', 'ebitda_usd',
        'interest_usd', 'debt_service_usd', 'taxes_usd', 'fcf_usd',
        'dscr', 'credit_rating', 'spread_bps', 'cost_of_debt',
    ]
    
    available_cols = [c for c in cols_to_keep if c in result.columns]
    return result[available_cols]


# =============================================================================
# MAIN RUNNER
# =============================================================================

def run_full_pipeline(
    base_dir: Path = None,
    transition_scenario: str = "baseline",
    power_plan_scenario: str = "official_10th_plan",
    physical_scenario: str = "baseline",
    start_year: int = 2024,
    end_year: int = 2064,
    save_outputs: bool = True,
) -> Dict[str, pd.DataFrame]:
    """Run full model pipeline and generate all CSV outputs."""
    if base_dir is None:
        base_dir = Path(".")
    
    loader = DataLoader(base_dir)
    output_dir = base_dir / "results" / "modules"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating transition results for {transition_scenario} / {power_plan_scenario}...")
    transition_df = generate_transition_results(
        loader, transition_scenario, power_plan_scenario, start_year, end_year
    )
    
    print(f"Generating physical results for {physical_scenario}...")
    physical_df = generate_physical_results(
        loader, physical_scenario, start_year, end_year
    )
    
    print("Generating cashflow results...")
    cashflow_df = generate_cashflow_results(
        loader, transition_df, physical_df, start_year
    )
    
    print("Generating credit results...")
    credit_df = generate_credit_results(loader, cashflow_df)
    
    print("Combining all results...")
    combined_df = generate_model_results(
        transition_df, physical_df, cashflow_df, credit_df
    )
    
    if save_outputs:
        transition_df.to_csv(output_dir / "transition_results.csv", index=False)
        physical_df.to_csv(output_dir / "physical_results.csv", index=False)
        cashflow_df.to_csv(output_dir / "cashflow_results.csv", index=False)
        credit_df.to_csv(output_dir / "credit_results.csv", index=False)
        combined_df.to_csv(base_dir / "results" / "model_results.csv", index=False)
        print(f"Saved outputs to {output_dir}")
    
    return {
        'transition': transition_df,
        'physical': physical_df,
        'cashflow': cashflow_df,
        'credit': credit_df,
        'combined': combined_df,
    }


if __name__ == "__main__":
    results = run_full_pipeline()
    print("\n=== Pipeline Complete ===")
    for name, df in results.items():
        print(f"{name}: {len(df)} rows, {len(df.columns)} columns")

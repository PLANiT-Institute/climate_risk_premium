"""
Physical Risk Sensitivity Analysis: Literature vs CLIMADA Comparison.

Compares two data sources for physical risk parameters:
1. Literature-based (conservative, from peer-reviewed sources)
2. CLIMADA-synthetic (climate-adjusted calculations)

This enables sensitivity analysis showing the range of possible outcomes.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class PhysicalRiskComparison:
    """Comparison of physical risk from different data sources."""
    scenario: str
    rcp: str
    year: int

    # Literature-based values
    lit_wildfire_rate: float
    lit_flood_rate: float
    lit_slr_derate: float
    lit_compound_mult: float
    lit_total_outage: float

    # CLIMADA/Synthetic values
    clim_wildfire_rate: float
    clim_flood_rate: float
    clim_slr_derate: float
    clim_compound_mult: float
    clim_total_outage: float

    # Derived metrics
    @property
    def flood_ratio(self) -> float:
        """Literature / CLIMADA ratio for flood risk."""
        if self.clim_flood_rate > 0:
            return self.lit_flood_rate / self.clim_flood_rate
        return float('inf')

    @property
    def total_outage_ratio(self) -> float:
        """Literature / CLIMADA ratio for total outage."""
        if self.clim_total_outage > 0:
            return self.lit_total_outage / self.clim_total_outage
        return 1.0

    @property
    def lit_cf_impact(self) -> float:
        """Capacity factor reduction from literature values."""
        return (1 - self.lit_slr_derate) * (1 - self.lit_total_outage)

    @property
    def clim_cf_impact(self) -> float:
        """Capacity factor reduction from CLIMADA values."""
        return (1 - self.clim_slr_derate) * (1 - self.clim_total_outage)


def load_literature_hazards(base_dir: Path) -> pd.DataFrame:
    """Load literature-based hazard data."""
    path = base_dir / "data" / "raw" / "literature_hazards.csv"
    if not path.exists():
        # Try old name
        path = base_dir / "data" / "raw" / "climada_hazards.csv"
    return pd.read_csv(path)


def load_climada_hazards(base_dir: Path) -> pd.DataFrame:
    """Load CLIMADA API-generated hazard data."""
    path = base_dir / "data" / "raw" / "climada_api_hazards.csv"
    if not path.exists():
        logger.warning("CLIMADA API hazards not found. Run climada_api.py first.")
        return pd.DataFrame()
    return pd.read_csv(path)


def match_scenarios(
    lit_df: pd.DataFrame,
    clim_df: pd.DataFrame
) -> List[PhysicalRiskComparison]:
    """Match scenarios between literature and CLIMADA data."""
    comparisons = []

    # Map RCP and year combinations
    for _, lit_row in lit_df.iterrows():
        lit_rcp = str(lit_row.get('rcp_scenario', 'current')).lower().replace('.', '')
        lit_year = int(lit_row.get('target_year', 2024))

        # Find matching CLIMADA row
        clim_match = None
        for _, clim_row in clim_df.iterrows():
            clim_rcp = str(clim_row.get('rcp_scenario', 'current')).lower().replace('.', '')
            clim_year = int(clim_row.get('target_year', 2024))

            if clim_rcp == lit_rcp and clim_year == lit_year:
                clim_match = clim_row
                break

        if clim_match is None:
            # Use baseline CLIMADA values if no match
            clim_match = clim_df[clim_df['scenario'] == 'baseline'].iloc[0] if len(clim_df) > 0 else None

        if clim_match is not None:
            # Calculate total outage rates
            lit_total = (
                (lit_row['wildfire_outage_rate'] + lit_row['flood_outage_rate'])
                * lit_row.get('compound_multiplier', 1.0)
            )
            clim_total = (
                (clim_match['wildfire_outage_rate'] + clim_match['flood_outage_rate'])
                * clim_match.get('compound_multiplier', 1.0)
            )

            comparisons.append(PhysicalRiskComparison(
                scenario=lit_row['scenario'],
                rcp=lit_rcp,
                year=lit_year,
                lit_wildfire_rate=float(lit_row['wildfire_outage_rate']),
                lit_flood_rate=float(lit_row['flood_outage_rate']),
                lit_slr_derate=float(lit_row['slr_capacity_derate']),
                lit_compound_mult=float(lit_row.get('compound_multiplier', 1.0)),
                lit_total_outage=lit_total,
                clim_wildfire_rate=float(clim_match['wildfire_outage_rate']),
                clim_flood_rate=float(clim_match['flood_outage_rate']),
                clim_slr_derate=float(clim_match['slr_capacity_derate']),
                clim_compound_mult=float(clim_match.get('compound_multiplier', 1.0)),
                clim_total_outage=clim_total,
            ))

    return comparisons


def calculate_financial_impact(
    comparison: PhysicalRiskComparison,
    capacity_mw: float = 2100,
    capacity_factor: float = 0.85,
    power_price: float = 80.0,  # $/MWh
) -> Dict[str, float]:
    """Calculate financial impact of physical risk differences."""
    annual_hours = 8760
    base_generation = capacity_mw * annual_hours * capacity_factor  # MWh
    base_revenue = base_generation * power_price  # $

    # Literature-based impact
    lit_cf_eff = comparison.lit_cf_impact
    lit_generation = base_generation * lit_cf_eff
    lit_revenue = lit_generation * power_price
    lit_revenue_loss = base_revenue - lit_revenue

    # CLIMADA-based impact
    clim_cf_eff = comparison.clim_cf_impact
    clim_generation = base_generation * clim_cf_eff
    clim_revenue = clim_generation * power_price
    clim_revenue_loss = base_revenue - clim_revenue

    return {
        'base_revenue_million': base_revenue / 1e6,
        'lit_revenue_million': lit_revenue / 1e6,
        'lit_revenue_loss_million': lit_revenue_loss / 1e6,
        'clim_revenue_million': clim_revenue / 1e6,
        'clim_revenue_loss_million': clim_revenue_loss / 1e6,
        'revenue_loss_range_million': abs(lit_revenue_loss - clim_revenue_loss) / 1e6,
        'lit_cf_effective': lit_cf_eff,
        'clim_cf_effective': clim_cf_eff,
    }


def generate_sensitivity_report(base_dir: Path) -> pd.DataFrame:
    """Generate comprehensive sensitivity analysis report."""
    lit_df = load_literature_hazards(base_dir)
    clim_df = load_climada_hazards(base_dir)

    if clim_df.empty:
        logger.error("Cannot generate sensitivity report without CLIMADA data")
        return pd.DataFrame()

    comparisons = match_scenarios(lit_df, clim_df)

    rows = []
    for comp in comparisons:
        fin_impact = calculate_financial_impact(comp)

        rows.append({
            'scenario': comp.scenario,
            'rcp': comp.rcp.upper(),
            'year': comp.year,

            # Literature values
            'lit_wildfire_rate': f"{comp.lit_wildfire_rate:.2%}",
            'lit_flood_rate': f"{comp.lit_flood_rate:.2%}",
            'lit_slr_derate': f"{comp.lit_slr_derate:.2%}",
            'lit_compound': f"{comp.lit_compound_mult:.2f}x",
            'lit_total_outage': f"{comp.lit_total_outage:.2%}",

            # CLIMADA values
            'clim_wildfire_rate': f"{comp.clim_wildfire_rate:.2%}",
            'clim_flood_rate': f"{comp.clim_flood_rate:.2%}",
            'clim_slr_derate': f"{comp.clim_slr_derate:.2%}",
            'clim_compound': f"{comp.clim_compound_mult:.2f}x",
            'clim_total_outage': f"{comp.clim_total_outage:.2%}",

            # Comparison ratios
            'flood_ratio': f"{comp.flood_ratio:.1f}x",
            'outage_ratio': f"{comp.total_outage_ratio:.1f}x",

            # Financial impact
            'lit_cf_impact': f"{comp.lit_cf_impact:.2%}",
            'clim_cf_impact': f"{comp.clim_cf_impact:.2%}",
            'lit_revenue_loss_M': f"${fin_impact['lit_revenue_loss_million']:.1f}M",
            'clim_revenue_loss_M': f"${fin_impact['clim_revenue_loss_million']:.1f}M",
            'uncertainty_range_M': f"${fin_impact['revenue_loss_range_million']:.1f}M",
        })

    return pd.DataFrame(rows)


def generate_sensitivity_csv(base_dir: Path, output_path: Optional[Path] = None) -> Path:
    """Generate and save sensitivity analysis CSV."""
    df = generate_sensitivity_report(base_dir)

    if output_path is None:
        output_path = base_dir / "data" / "processed" / "physical_risk_sensitivity.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    logger.info(f"Saved sensitivity analysis to {output_path}")
    return output_path


def print_sensitivity_summary(base_dir: Path):
    """Print formatted sensitivity analysis summary."""
    lit_df = load_literature_hazards(base_dir)
    clim_df = load_climada_hazards(base_dir)

    if clim_df.empty:
        print("ERROR: CLIMADA API hazards not found. Run climada_api.py first.")
        return

    comparisons = match_scenarios(lit_df, clim_df)

    print("=" * 80)
    print("PHYSICAL RISK SENSITIVITY ANALYSIS")
    print("Literature (Conservative) vs CLIMADA (Calculated)")
    print("=" * 80)

    print("\n### KEY FINDINGS ###\n")

    # Find key scenarios for comparison
    key_scenarios = [c for c in comparisons if 'rcp85' in c.rcp and c.year in [2050, 2060]]

    for comp in key_scenarios:
        fin = calculate_financial_impact(comp)

        print(f"\n{comp.rcp.upper()} {comp.year}:")
        print("-" * 50)
        print(f"  {'Metric':<25} {'Literature':>12} {'CLIMADA':>12} {'Ratio':>10}")
        print(f"  {'-'*25} {'-'*12} {'-'*12} {'-'*10}")
        print(f"  {'Wildfire Outage Rate':<25} {comp.lit_wildfire_rate:>11.2%} {comp.clim_wildfire_rate:>11.2%} {comp.lit_wildfire_rate/max(0.0001,comp.clim_wildfire_rate):>9.1f}x")
        print(f"  {'Flood Outage Rate':<25} {comp.lit_flood_rate:>11.2%} {comp.clim_flood_rate:>11.2%} {comp.flood_ratio:>9.1f}x")
        print(f"  {'SLR Capacity Derate':<25} {comp.lit_slr_derate:>11.2%} {comp.clim_slr_derate:>11.2%} {comp.lit_slr_derate/max(0.0001,comp.clim_slr_derate):>9.1f}x")
        print(f"  {'Compound Multiplier':<25} {comp.lit_compound_mult:>11.2f}x {comp.clim_compound_mult:>11.2f}x")
        print(f"  {'Total Outage Rate':<25} {comp.lit_total_outage:>11.2%} {comp.clim_total_outage:>11.2%} {comp.total_outage_ratio:>9.1f}x")
        print(f"  {'Effective CF':<25} {comp.lit_cf_impact:>11.2%} {comp.clim_cf_impact:>11.2%}")
        print(f"  {'Annual Revenue Loss':<25} ${fin['lit_revenue_loss_million']:>10.1f}M ${fin['clim_revenue_loss_million']:>10.1f}M")

    print("\n" + "=" * 80)
    print("INTERPRETATION:")
    print("-" * 80)
    print("""
  Literature values are MORE CONSERVATIVE (higher risk estimates):
    - Flood risk: Literature assumes ALL 100-year floods affect plant
    - CLIMADA calculates: actual flood depth vs plant elevation

  Key difference sources:
    - Literature: Seoul Flood Policy (generic 100-year standard)
    - CLIMADA: Site-specific depth calculation (4.2m flood vs 10m elevation)

  Recommendation:
    - Use Literature for conservative/worst-case analysis (papers, regulatory)
    - Use CLIMADA for expected-case analysis (internal planning)
    - Report BOTH as uncertainty range in publications
""")
    print("=" * 80)


def create_combined_hazards_csv(base_dir: Path) -> Path:
    """
    Create combined hazards CSV with both Literature and CLIMADA values.

    This allows the model to run sensitivity analysis using both sources.
    """
    lit_df = load_literature_hazards(base_dir)
    clim_df = load_climada_hazards(base_dir)

    # Add source column to each
    lit_df = lit_df.copy()
    lit_df['data_source_type'] = 'literature'
    lit_df['scenario'] = lit_df['scenario'].apply(lambda x: f"lit_{x}")

    if not clim_df.empty:
        clim_df = clim_df.copy()
        clim_df['data_source_type'] = 'climada_synthetic'
        clim_df['scenario'] = clim_df['scenario'].apply(lambda x: f"clim_{x}")

        # Combine
        combined = pd.concat([lit_df, clim_df], ignore_index=True)
    else:
        combined = lit_df

    output_path = base_dir / "data" / "raw" / "combined_hazards.csv"
    combined.to_csv(output_path, index=False)

    logger.info(f"Created combined hazards CSV: {output_path}")
    print(f"Created: {output_path}")
    print(f"  Literature scenarios: {len(lit_df)}")
    print(f"  CLIMADA scenarios: {len(clim_df) if not clim_df.empty else 0}")
    print(f"  Total scenarios: {len(combined)}")

    return output_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    base_dir = Path(__file__).parent.parent.parent

    # Print summary
    print_sensitivity_summary(base_dir)

    # Generate CSV outputs
    print("\n\nGenerating CSV outputs...")
    sensitivity_path = generate_sensitivity_csv(base_dir)
    combined_path = create_combined_hazards_csv(base_dir)

    print(f"\nOutputs:")
    print(f"  1. Sensitivity analysis: {sensitivity_path}")
    print(f"  2. Combined hazards: {combined_path}")

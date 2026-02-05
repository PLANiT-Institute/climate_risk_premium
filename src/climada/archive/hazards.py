"""
CLIMADA hazard data structures and loaders.
Integrates wildfire, flood, and sea level rise impacts.

CORRECTED (2024 Review):
- Compound multiplier now uses 1.0-1.25 range (was 1.2-2.0)
- Uses corrected formulas from literature_parameters.py
- Updated thresholds for description based on realistic values
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
import pandas as pd

from .literature_parameters import (
    calculate_compound_multiplier as lit_compound_mult,
    calculate_wildfire_outage_rate as lit_wildfire_rate,
    calculate_flood_outage_rate as lit_flood_rate,
    calculate_slr_capacity_derate as lit_slr_derate,
    WILDFIRE_OUTAGE_PARAMS,
    FLOOD_OUTAGE_PARAMS,
    SLR_PARAMS,
    COMPOUND_RISK_PARAMS,
    CLIMATE_MULTIPLIERS,
)


@dataclass
class CLIMADAHazardData:
    """
    CLIMADA-derived physical hazard impacts.

    All rates and factors are annual values.

    Attributes:
        wildfire_outage_rate: Annual forced outage rate from wildfires (0-1)
        flood_outage_rate: Annual forced outage rate from floods (0-1)
        slr_capacity_derate: Capacity derating from sea level rise (0-1)
        compound_multiplier: Amplification factor for concurrent hazards (1.0-1.25)
        fwi_index: Fire Weather Index (CLIMADA metric)
        flood_return_period: Return period of design flood (years)
        slr_meters: Sea level rise above baseline (meters)
        data_source: Source of hazard data
        notes: Additional metadata
    """
    wildfire_outage_rate: float
    flood_outage_rate: float
    slr_capacity_derate: float
    compound_multiplier: float = 1.0
    fwi_index: float = 0.0
    flood_return_period: float = 100.0
    slr_meters: float = 0.0
    data_source: str = ""
    notes: str = ""

    @property
    def total_outage_rate(self) -> float:
        """
        Combined annual outage rate from all hazards.

        Outages are additive (wildfire OR flood causes shutdown).
        Compound multiplier accounts for hazard interactions.
        """
        base_outage = self.wildfire_outage_rate + self.flood_outage_rate
        return min(1.0, base_outage * self.compound_multiplier)

    @property
    def total_capacity_derate(self) -> float:
        """
        Total capacity derating from long-term hazards (primarily SLR).

        Derating is multiplicative (reduces effective capacity).
        """
        return min(1.0, self.slr_capacity_derate * self.compound_multiplier)

    @property
    def effective_capacity_factor_multiplier(self) -> float:
        """
        Combined effect on capacity factor.

        CF_effective = CF_baseline × (1 - derate) × (1 - outage_rate)
        """
        return (1 - self.total_capacity_derate) * (1 - self.total_outage_rate)

    def to_dict(self) -> Dict[str, float]:
        """Export as dictionary for CSV/analysis."""
        return {
            'wildfire_outage_rate': self.wildfire_outage_rate,
            'flood_outage_rate': self.flood_outage_rate,
            'slr_capacity_derate': self.slr_capacity_derate,
            'compound_multiplier': self.compound_multiplier,
            'total_outage_rate': self.total_outage_rate,
            'total_capacity_derate': self.total_capacity_derate,
            'effective_cf_multiplier': self.effective_capacity_factor_multiplier,
            'fwi_index': self.fwi_index,
            'flood_return_period': self.flood_return_period,
            'slr_meters': self.slr_meters,
        }


def load_climada_hazards(file_path: str, scenario_name: str = None) -> Dict[str, CLIMADAHazardData]:
    """
    Load CLIMADA hazard data from CSV file.

    Args:
        file_path: Path to climada_hazards.csv or literature_hazards.csv
        scenario_name: Optional filter for specific scenario

    Returns:
        Dict of scenario name -> CLIMADAHazardData
    """
    df = pd.read_csv(file_path)

    if scenario_name:
        df = df[df['scenario'] == scenario_name]

    hazards = {}

    for _, row in df.iterrows():
        scenario = row['scenario']
        hazards[scenario] = CLIMADAHazardData(
            wildfire_outage_rate=float(row['wildfire_outage_rate']),
            flood_outage_rate=float(row['flood_outage_rate']),
            slr_capacity_derate=float(row['slr_capacity_derate']),
            compound_multiplier=float(row['compound_multiplier']),
            fwi_index=float(row.get('fwi_index', 0)),
            flood_return_period=float(row.get('flood_return_period_yr', 100)),
            slr_meters=float(row.get('slr_meters', 0)),
            data_source=str(row.get('data_source', '')),
            notes=str(row.get('notes', ''))
        )

    return hazards


def calculate_compound_risk(
    wildfire_outage: float,
    flood_outage: float,
    slr_derate: float,
    scenario_severity: str = "baseline"
) -> CLIMADAHazardData:
    """
    Calculate compound hazard risk with corrected multipliers.

    CORRECTED: Uses 1.0-1.25 range (was 1.2-2.0).

    NOTE: Zscheischler (2018) is a CONCEPTUAL FRAMEWORK, not a source for
    specific multiplier values. These multipliers are based on conservative
    estimates from hazard correlation analysis.

    For a single asset like Samcheok:
    - Baseline: 1.0x (no amplification)
    - Moderate: 1.05x (mild correlation)
    - High: 1.10x (moderate correlation)
    - Extreme: 1.15x (high correlation)
    - Maximum: 1.25x (concurrent hazards)

    Args:
        wildfire_outage: Base wildfire outage rate
        flood_outage: Base flood outage rate
        slr_derate: Base SLR capacity derating
        scenario_severity: "baseline", "moderate", "high", "extreme", "catastrophic"

    Returns:
        CLIMADAHazardData with compound effects
    """
    # Use the corrected compound multiplier function
    final_multiplier = lit_compound_mult(
        wildfire_rate=wildfire_outage,
        flood_rate=flood_outage,
        slr_derate=slr_derate,
        scenario_severity=scenario_severity
    )

    total_base_risk = wildfire_outage + flood_outage + slr_derate

    return CLIMADAHazardData(
        wildfire_outage_rate=wildfire_outage,
        flood_outage_rate=flood_outage,
        slr_capacity_derate=slr_derate,
        compound_multiplier=final_multiplier,
        notes=f"Compound risk with {final_multiplier:.2f}x amplification "
              f"(System Stress: {total_base_risk:.4%}, Severity: {scenario_severity})"
    )


def calculate_compound_risk_legacy(
    wildfire_outage: float,
    flood_outage: float,
    slr_derate: float,
    base_amplification: float = 1.2
) -> CLIMADAHazardData:
    """
    DEPRECATED: Original compound risk calculation with flawed 1.2-2.0 range.

    This function is kept for backwards compatibility but should not be used.
    Use calculate_compound_risk() instead.

    The original formula:
    - risk_factor = min(1.0, total_base_risk * 10)
    - final_multiplier = 1.2 + (0.8 * risk_factor)  # Range: 1.2 to 2.0

    This was WRONG because:
    1. Zscheischler (2018) does NOT provide these values
    2. 2.0x multiplier is only appropriate for systemic/cascading failures
    3. For a single asset, 1.25x is maximum reasonable compound effect
    """
    # Sum of individual risks (proxy for total system stress)
    total_base_risk = wildfire_outage + flood_outage + slr_derate

    # DEPRECATED formula (kept for reference)
    risk_factor = min(1.0, total_base_risk * 10)
    final_multiplier = base_amplification + (0.8 * risk_factor)

    return CLIMADAHazardData(
        wildfire_outage_rate=wildfire_outage,
        flood_outage_rate=flood_outage,
        slr_capacity_derate=slr_derate,
        compound_multiplier=final_multiplier,
        notes=f"DEPRECATED: {final_multiplier:.2f}x amplification (use calculate_compound_risk instead)"
    )


def get_hazard_description(hazard: CLIMADAHazardData) -> str:
    """
    Generate a human-readable description of the hazard profile.

    CORRECTED: Thresholds updated for realistic values.
    - Old: >1% = "High", >0.5% = "Severe"
    - New: >0.1% = "Elevated", >0.05% = "Moderate"
    """
    parts = []

    # Wildfire thresholds (corrected for Korea)
    if hazard.wildfire_outage_rate > 0.001:  # >0.1%
        parts.append(f"Elevated Wildfire Risk ({hazard.wildfire_outage_rate:.4%})")
    elif hazard.wildfire_outage_rate > 0.0005:  # >0.05%
        parts.append(f"Moderate Wildfire Risk ({hazard.wildfire_outage_rate:.4%})")
    elif hazard.wildfire_outage_rate > 0:
        parts.append(f"Low Wildfire Risk ({hazard.wildfire_outage_rate:.4%})")

    # Flood thresholds (corrected for Samcheok elevation)
    if hazard.flood_outage_rate > 0.0005:  # >0.05%
        parts.append(f"Elevated Flood Risk ({hazard.flood_outage_rate:.4%})")
    elif hazard.flood_outage_rate > 0.0001:  # >0.01%
        parts.append(f"Moderate Flood Risk ({hazard.flood_outage_rate:.4%})")
    elif hazard.flood_outage_rate > 0:
        parts.append(f"Low Flood Risk ({hazard.flood_outage_rate:.4%})")

    # SLR thresholds (corrected for realistic values)
    if hazard.slr_capacity_derate > 0.002:  # >0.2%
        parts.append(f"Noticeable SLR Impact ({hazard.slr_capacity_derate:.4%})")
    elif hazard.slr_capacity_derate > 0.0005:  # >0.05%
        parts.append(f"Minor SLR Impact ({hazard.slr_capacity_derate:.4%})")
    elif hazard.slr_capacity_derate > 0:
        parts.append(f"Negligible SLR Impact ({hazard.slr_capacity_derate:.4%})")

    # Compound multiplier (corrected range)
    if hazard.compound_multiplier > 1.15:
        parts.append(f"Significant Compound Amplification ({hazard.compound_multiplier:.2f}x)")
    elif hazard.compound_multiplier > 1.05:
        parts.append(f"Mild Compound Amplification ({hazard.compound_multiplier:.2f}x)")
    elif hazard.compound_multiplier > 1.0:
        parts.append(f"Minimal Compound Effect ({hazard.compound_multiplier:.2f}x)")

    return ", ".join(parts) if parts else "Low Physical Risk"


def create_corrected_baseline(target_year: int = 2024, rcp: str = "current") -> CLIMADAHazardData:
    """
    Create hazard data using corrected literature parameters.

    Uses the corrected formulas from literature_parameters.py.

    Args:
        target_year: Target year for projections
        rcp: RCP scenario ("current", "RCP4.5", "RCP8.5")

    Returns:
        CLIMADAHazardData with corrected values
    """
    # Get climate multipliers based on scenario
    if rcp == "current" or target_year <= 2024:
        wildfire_mult = 1.0
        flood_mult = 1.0
    elif rcp == "RCP4.5":
        if target_year <= 2030:
            wildfire_mult = CLIMATE_MULTIPLIERS["wildfire_rcp45_2030"]
        elif target_year <= 2050:
            wildfire_mult = CLIMATE_MULTIPLIERS["wildfire_rcp45_2050"]
        else:
            wildfire_mult = CLIMATE_MULTIPLIERS["wildfire_rcp45_2100"]
        flood_mult = CLIMATE_MULTIPLIERS["flood_2050_multiplier"] if target_year >= 2050 else 1.0
    else:  # RCP8.5
        if target_year <= 2030:
            wildfire_mult = CLIMATE_MULTIPLIERS["wildfire_rcp85_2030"]
        elif target_year <= 2050:
            wildfire_mult = CLIMATE_MULTIPLIERS["wildfire_rcp85_2050"]
        else:
            wildfire_mult = CLIMATE_MULTIPLIERS["wildfire_rcp85_2100"]
        flood_mult = CLIMATE_MULTIPLIERS["flood_2100_multiplier"] if target_year >= 2100 else \
                     CLIMATE_MULTIPLIERS["flood_2050_multiplier"] if target_year >= 2050 else 1.0

    # Calculate using corrected formulas
    wildfire_rate = lit_wildfire_rate(climate_multiplier=wildfire_mult)

    # Flood rate with climate adjustment
    base_flood = lit_flood_rate()
    flood_rate = base_flood * flood_mult

    # SLR derate based on scenario projections
    if rcp == "current" or target_year <= 2024:
        slr_m = 0.0
    elif rcp == "RCP4.5":
        if target_year <= 2030:
            slr_m = SLR_PARAMS["rcp45_slr_2030_m"].value
        else:
            slr_m = SLR_PARAMS["rcp45_slr_2050_m"].value
    else:
        if target_year <= 2030:
            slr_m = SLR_PARAMS["rcp85_slr_2030_m"].value
        elif target_year <= 2050:
            slr_m = SLR_PARAMS["rcp85_slr_2050_m"].value
        else:
            slr_m = SLR_PARAMS["rcp85_slr_2100_m"].value

    slr_derate = lit_slr_derate(slr_m)

    # Determine severity for compound multiplier
    if rcp == "current":
        severity = "baseline"
    elif rcp == "RCP4.5":
        severity = "moderate" if target_year >= 2050 else "baseline"
    else:
        if target_year >= 2060:
            severity = "extreme"
        elif target_year >= 2050:
            severity = "high"
        elif target_year >= 2030:
            severity = "moderate"
        else:
            severity = "baseline"

    compound_mult = lit_compound_mult(wildfire_rate, flood_rate, slr_derate, severity)

    return CLIMADAHazardData(
        wildfire_outage_rate=wildfire_rate,
        flood_outage_rate=flood_rate,
        slr_capacity_derate=slr_derate,
        compound_multiplier=compound_mult,
        slr_meters=slr_m,
        data_source=f"Corrected literature parameters ({rcp} {target_year})",
        notes="Based on Korea-specific data, not California"
    )


def interpolate_hazard_by_year(
    hazards: Dict[str, CLIMADAHazardData],
    target_year: int,
    scenario_prefix: str = "high_physical"
) -> CLIMADAHazardData:
    """
    Interpolate CLIMADA hazard data for a specific year.

    Useful when hazard data is available for discrete years (2030, 2040, 2050)
    but analysis requires annual projections.

    Args:
        hazards: Dict of scenario -> hazard data (must include year in key)
        target_year: Year to interpolate for
        scenario_prefix: Scenario type (e.g., "high_physical", "moderate_physical")

    Returns:
        Interpolated CLIMADAHazardData

    Example:
        >>> hazards = load_climada_hazards('data/climada_hazards.csv')
        >>> hazard_2035 = interpolate_hazard_by_year(hazards, 2035, "high_physical")
    """
    # Extract scenarios with matching prefix and parse years
    relevant_scenarios = {
        key: value for key, value in hazards.items()
        if key.startswith(scenario_prefix)
    }

    if not relevant_scenarios:
        raise ValueError(f"No scenarios found with prefix '{scenario_prefix}'")

    # Parse years from scenario names (e.g., "high_physical_2040" -> 2040)
    years_data = []
    for key, hazard in relevant_scenarios.items():
        try:
            year = int(key.split('_')[-1])
            years_data.append((year, hazard))
        except ValueError:
            continue  # Skip scenarios without year suffix

    if not years_data:
        # Return first available if no year parsing possible
        return list(relevant_scenarios.values())[0]

    years_data.sort(key=lambda x: x[0])
    years = [y for y, _ in years_data]
    hazards_list = [h for _, h in years_data]

    # If target year is outside range, return nearest endpoint
    if target_year <= years[0]:
        return hazards_list[0]
    if target_year >= years[-1]:
        return hazards_list[-1]

    # Find bounding years for interpolation
    for i in range(len(years) - 1):
        if years[i] <= target_year <= years[i + 1]:
            y0, y1 = years[i], years[i + 1]
            h0, h1 = hazards_list[i], hazards_list[i + 1]

            # Linear interpolation weight
            weight = (target_year - y0) / (y1 - y0)

            # Interpolate each component
            return CLIMADAHazardData(
                wildfire_outage_rate=h0.wildfire_outage_rate + weight * (h1.wildfire_outage_rate - h0.wildfire_outage_rate),
                flood_outage_rate=h0.flood_outage_rate + weight * (h1.flood_outage_rate - h0.flood_outage_rate),
                slr_capacity_derate=h0.slr_capacity_derate + weight * (h1.slr_capacity_derate - h0.slr_capacity_derate),
                compound_multiplier=h0.compound_multiplier + weight * (h1.compound_multiplier - h0.compound_multiplier),
                fwi_index=h0.fwi_index + weight * (h1.fwi_index - h0.fwi_index),
                flood_return_period=h0.flood_return_period + weight * (h1.flood_return_period - h0.flood_return_period),
                slr_meters=h0.slr_meters + weight * (h1.slr_meters - h0.slr_meters),
                data_source=f"Interpolated between {y0} and {y1}",
                notes=f"Linear interpolation for year {target_year}"
            )

    # Fallback (should not reach)
    return hazards_list[0]


def calculate_economic_impact(
    hazard: CLIMADAHazardData,
    capacity_mw: float,
    power_price: float,
    annual_fixed_costs: float = 0.0
) -> Dict[str, float]:
    """
    Calculate economic impact of CLIMADA hazards.

    Args:
        hazard: CLIMADA hazard data
        capacity_mw: Plant capacity (MW)
        power_price: Electricity price ($/MWh)
        annual_fixed_costs: Fixed O&M costs ($/year)

    Returns:
        Dict with revenue_loss, generation_loss, cost_per_mwh_increase
    """
    # Annual generation loss from outages
    outage_generation_loss = capacity_mw * 8760 * hazard.total_outage_rate
    outage_revenue_loss = outage_generation_loss * power_price

    # Annual generation loss from capacity derating
    derate_generation_loss = capacity_mw * 8760 * hazard.total_capacity_derate
    derate_revenue_loss = derate_generation_loss * power_price

    # Total impact
    total_generation_loss = outage_generation_loss + derate_generation_loss
    total_revenue_loss = outage_revenue_loss + derate_revenue_loss

    # Effective generation after hazards
    effective_generation = capacity_mw * 8760 * hazard.effective_capacity_factor_multiplier

    # Cost increase per MWh (fixed costs spread over less generation)
    cost_per_mwh_increase = 0.0
    if effective_generation > 0 and annual_fixed_costs > 0:
        baseline_generation = capacity_mw * 8760
        baseline_cost_per_mwh = annual_fixed_costs / baseline_generation
        hazard_cost_per_mwh = annual_fixed_costs / effective_generation
        cost_per_mwh_increase = hazard_cost_per_mwh - baseline_cost_per_mwh

    return {
        'annual_generation_loss_mwh': total_generation_loss,
        'annual_revenue_loss': total_revenue_loss,
        'outage_generation_loss_mwh': outage_generation_loss,
        'derate_generation_loss_mwh': derate_generation_loss,
        'effective_generation_mwh': effective_generation,
        'cost_per_mwh_increase': cost_per_mwh_increase,
        'capacity_factor_reduction_pct': (1 - hazard.effective_capacity_factor_multiplier) * 100
    }

"""
Unified Data Loaders.

Loads all model data from CSV files. No hardcoded data in the codebase.
All data should be maintained in CSV files under data/ directory.

Directory structure:
    data/
    ├── physical/
    │   ├── hazard_baselines.csv
    │   ├── climate_factors.csv
    │   ├── compound_events.csv
    │   └── damage_function_params.csv
    ├── financial/
    │   ├── korean_coal_fleet.csv
    │   ├── ngfs_scenarios.csv
    │   ├── generation_loss_factors.csv
    │   └── credit_spreads.csv
    └── calibration/
        └── historical_events.csv
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from functools import lru_cache


# =============================================================================
# PATH CONFIGURATION
# =============================================================================

def get_data_root() -> Path:
    """Get the root data directory."""
    # Try relative to this file first
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    data_dir = project_root / "data"

    if data_dir.exists():
        return data_dir

    # Fallback: try current working directory
    cwd_data = Path.cwd() / "data"
    if cwd_data.exists():
        return cwd_data

    raise FileNotFoundError(f"Data directory not found. Tried: {data_dir}, {cwd_data}")


# =============================================================================
# PHYSICAL RISK DATA LOADERS
# =============================================================================

@dataclass
class HazardBaseline:
    """Hazard baseline data from CSV."""
    hazard_type: str
    base_frequency: float
    base_intensity: float
    intensity_unit: str
    outage_rate: float
    capacity_derate: float
    efficiency_loss: float
    damage_ratio: float
    confidence_low: float
    confidence_high: float
    source: str
    methodology: str
    climada_events: int
    climada_years: int

    @property
    def total_annual_impact(self) -> float:
        """Combined annual impact."""
        return self.outage_rate + self.capacity_derate + self.efficiency_loss


@dataclass
class ClimateFactor:
    """Climate change factor row from ``data/physical/climate_factors.csv``.

    Columns:
        scenario/year identify the projection path and interpolation anchor.
        wildfire, tropical_cyclone, river_flood, coastal_flood, drought, and
        heat_stress are multiplicative factors applied to baseline hazard
        frequencies or impacts (1.0 = current-climate baseline).
        slr_meters is an absolute sea-level-rise assumption kept in the CSV for
        documentation; ``get_factor("sea_level_rise")`` intentionally returns
        1.0 because SLR is not a multiplicative hazard factor in this loader.
        source is the high-level evidence label from the CSV.

    These are scenario multipliers, not observed event counts. Current rows cite
    IPCC AR6/KMA/WWA summary assumptions and should be sensitivity-tested before
    being presented as calibrated Korea site-level projections.
    """
    scenario: str
    year: int
    wildfire: float
    tropical_cyclone: float
    river_flood: float
    coastal_flood: float
    drought: float
    heat_stress: float
    slr_meters: float
    source: str

    def get_factor(self, hazard_type: str) -> float:
        """Get factor for a specific hazard type."""
        mapping = {
            "wildfire": self.wildfire,
            "tropical_cyclone": self.tropical_cyclone,
            "river_flood": self.river_flood,
            "coastal_flood": self.coastal_flood,
            "drought": self.drought,
            "heat_stress": self.heat_stress,
            "sea_level_rise": 1.0,
        }
        return mapping.get(hazard_type, 1.0)


@dataclass
class CompoundEvent:
    """Compound event configuration from CSV."""
    event_type: str
    hazard1: str
    hazard2: str
    correlation: float
    amplification: float
    joint_probability: float
    source: str


@dataclass
class DamageFunctionParams:
    """Damage function parameters from CSV."""
    hazard_type: str
    function_type: str
    threshold: float
    i_half: float
    exponent: float
    max_damage: float
    source: str
    notes: str


@lru_cache(maxsize=1)
def load_hazard_baselines() -> Dict[str, HazardBaseline]:
    """Load hazard baseline data from CSV."""
    data_root = get_data_root()
    csv_path = data_root / "physical" / "hazard_baselines.csv"

    baselines = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            hazard_type = row['hazard_type']
            baselines[hazard_type] = HazardBaseline(
                hazard_type=hazard_type,
                base_frequency=float(row['base_frequency']),
                base_intensity=float(row['base_intensity']),
                intensity_unit=row['intensity_unit'],
                outage_rate=float(row['outage_rate']),
                capacity_derate=float(row['capacity_derate']),
                efficiency_loss=float(row['efficiency_loss']),
                damage_ratio=float(row['damage_ratio']),
                confidence_low=float(row['confidence_low']),
                confidence_high=float(row['confidence_high']),
                source=row['source'],
                methodology=row['methodology'],
                climada_events=int(row['climada_events']),
                climada_years=int(row['climada_years']),
            )
    return baselines


@lru_cache(maxsize=1)
def load_climate_factors() -> Dict[str, Dict[int, ClimateFactor]]:
    """Load climate factors from CSV, organized by scenario and year."""
    data_root = get_data_root()
    csv_path = data_root / "physical" / "climate_factors.csv"

    factors: Dict[str, Dict[int, ClimateFactor]] = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            scenario = row['scenario']
            year = int(row['year'])

            if scenario not in factors:
                factors[scenario] = {}

            factors[scenario][year] = ClimateFactor(
                scenario=scenario,
                year=year,
                wildfire=float(row['wildfire']),
                tropical_cyclone=float(row['tropical_cyclone']),
                river_flood=float(row['river_flood']),
                coastal_flood=float(row['coastal_flood']),
                drought=float(row['drought']),
                heat_stress=float(row['heat_stress']),
                slr_meters=float(row['slr_meters']),
                source=row['source'],
            )
    return factors


@lru_cache(maxsize=1)
def load_compound_events() -> Dict[str, CompoundEvent]:
    """Load compound event configurations from CSV."""
    data_root = get_data_root()
    csv_path = data_root / "physical" / "compound_events.csv"

    events = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            event_type = row['event_type']
            events[event_type] = CompoundEvent(
                event_type=event_type,
                hazard1=row['hazard1'],
                hazard2=row['hazard2'],
                correlation=float(row['correlation']),
                amplification=float(row['amplification']),
                joint_probability=float(row['joint_probability']),
                source=row['source'],
            )
    return events


@lru_cache(maxsize=1)
def load_damage_function_params() -> Dict[str, DamageFunctionParams]:
    """Load damage function parameters from CSV."""
    data_root = get_data_root()
    csv_path = data_root / "physical" / "damage_function_params.csv"

    params = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            hazard_type = row['hazard_type']
            params[hazard_type] = DamageFunctionParams(
                hazard_type=hazard_type,
                function_type=row['function_type'],
                threshold=float(row['threshold']),
                i_half=float(row['i_half']),
                exponent=float(row['exponent']),
                max_damage=float(row['max_damage']),
                source=row['source'],
                notes=row['notes'],
            )
    return params


def get_wildfire_i_half(default: float = 45.0) -> float:
    """Return wildfire i_half from damage_function_params.csv, or *default*."""
    try:
        params = load_damage_function_params()
        wf = params.get("wildfire")
        if wf is not None:
            return wf.i_half
    except Exception:
        pass
    return default


def get_climate_factor(hazard_type: str, year: int, scenario: str = "RCP8.5") -> float:
    """
    Get an interpolated climate multiplier for a hazard at a given year.

    Data source and assumptions:
        Reads ``data/physical/climate_factors.csv`` through
        ``load_climate_factors()``. The CSV columns are:
        ``scenario``, ``year``, ``wildfire``, ``tropical_cyclone``,
        ``river_flood``, ``coastal_flood``, ``drought``, ``heat_stress``,
        ``slr_meters``, and ``source``.

        Hazard columns are dimensionless multipliers applied to baseline
        frequencies or impact fractions. ``slr_meters`` is an absolute sea-level
        rise assumption and is not returned by this multiplier function.
        The ``source`` column is a summary label (currently IPCC AR6/KMA/WWA or
        baseline); values are scenario assumptions, not directly observed
        Samcheok plant measurements.

    Args:
        hazard_type: Type of hazard (e.g., "wildfire", "tropical_cyclone")
        year: Target year
        scenario: Climate scenario (e.g., "RCP4.5", "RCP8.5", "SSP5-8.5")

    Returns:
        Climate change multiplier (1.0 = no change from baseline)
    """
    # Kill-switch: disable all climate factors (returns 1.0 = baseline for all)
    if os.environ.get("CRP_DISABLE_CLIMATE_FACTOR") == "1":
        return 1.0

    all_factors = load_climate_factors()

    if scenario not in all_factors:
        # Fallback to RCP8.5 if scenario not found
        scenario = "RCP8.5"

    factors = all_factors[scenario]
    years = sorted(factors.keys())

    # Exact year match
    if year in factors:
        return factors[year].get_factor(hazard_type)

    # Before first year
    if year <= years[0]:
        return factors[years[0]].get_factor(hazard_type)

    # After last year
    if year >= years[-1]:
        return factors[years[-1]].get_factor(hazard_type)

    # Linear interpolation
    for i, y in enumerate(years[:-1]):
        if years[i] <= year < years[i + 1]:
            y0, y1 = years[i], years[i + 1]
            f0 = factors[y0].get_factor(hazard_type)
            f1 = factors[y1].get_factor(hazard_type)
            return f0 + (f1 - f0) * (year - y0) / (y1 - y0)

    return 1.0


# =============================================================================
# FINANCIAL DATA LOADERS
# =============================================================================

@dataclass
class CoalPlantData:
    """Coal plant data from CSV."""
    asset_id: str
    asset_name: str
    asset_type: str
    latitude: float
    longitude: float
    capacity_mw: float
    country: str
    region: str
    commissioning_year: int
    expected_lifetime_years: int
    replacement_cost_usd: float
    annual_revenue_usd: float
    annual_ebitda_usd: float
    cooling_type: str
    owner_name: str
    owner_type: str
    owner_country: str
    ownership_pct: float
    insurance_provider: str
    insurance_coverage_usd: float
    insurance_deductible_usd: float
    total_debt_usd: float
    senior_debt_usd: float
    subordinated_debt_usd: float
    debt_maturity_year: int
    interest_rate: float


@dataclass
class NGFSScenario:
    """NGFS scenario data from CSV."""
    scenario_type: str
    name: str
    description: str
    temp_2030_c: float
    temp_2050_c: float
    temp_2100_c: float
    physical_risk_multiplier: float
    acute_risk_multiplier: float
    chronic_risk_multiplier: float
    transition_risk_multiplier: float
    carbon_price_2030_usd: float
    carbon_price_2050_usd: float
    gdp_impact_2030_pct: float
    gdp_impact_2050_pct: float
    probability: float

    def get_physical_risk_factor(self, year: int) -> float:
        """Get physical risk factor for a year."""
        if year <= 2030:
            return 1.0 + (self.physical_risk_multiplier - 1.0) * (year - 2024) / 6
        elif year <= 2050:
            return self.physical_risk_multiplier
        else:
            if self.scenario_type == "hot_house":
                return self.physical_risk_multiplier * (1 + 0.02 * (year - 2050))
            return self.physical_risk_multiplier


@dataclass
class GenerationLossFactor:
    """Generation loss factor from CSV."""
    plant_technology: str
    year: int
    water_stress_loss_pct: float
    temperature_loss_pct: float
    combined_loss_pct: float
    total_loss_pct: float
    source: str


@dataclass
class CreditSpread:
    """Credit spread data from CSV."""
    rating: str
    spread_bps: int
    pd_1y: float
    pd_10y: float
    lgd: float
    recovery_rate: float
    source: str


@lru_cache(maxsize=1)
def load_korean_coal_fleet() -> Dict[str, CoalPlantData]:
    """Load Korean coal fleet data from CSV."""
    data_root = get_data_root()
    csv_path = data_root / "financial" / "korean_coal_fleet.csv"

    fleet = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            asset_id = row['asset_id']
            fleet[asset_id] = CoalPlantData(
                asset_id=asset_id,
                asset_name=row['asset_name'],
                asset_type=row['asset_type'],
                latitude=float(row['latitude']),
                longitude=float(row['longitude']),
                capacity_mw=float(row['capacity_mw']),
                country=row['country'],
                region=row['region'],
                commissioning_year=int(row['commissioning_year']),
                expected_lifetime_years=int(row['expected_lifetime_years']),
                replacement_cost_usd=float(row['replacement_cost_usd']),
                annual_revenue_usd=float(row['annual_revenue_usd']),
                annual_ebitda_usd=float(row['annual_ebitda_usd']),
                cooling_type=row['cooling_type'],
                owner_name=row['owner_name'],
                owner_type=row['owner_type'],
                owner_country=row['owner_country'],
                ownership_pct=float(row['ownership_pct']),
                insurance_provider=row['insurance_provider'],
                insurance_coverage_usd=float(row['insurance_coverage_usd']),
                insurance_deductible_usd=float(row['insurance_deductible_usd']),
                total_debt_usd=float(row['total_debt_usd']),
                senior_debt_usd=float(row['senior_debt_usd']),
                subordinated_debt_usd=float(row['subordinated_debt_usd']),
                debt_maturity_year=int(row['debt_maturity_year']),
                interest_rate=float(row['interest_rate']),
            )
    return fleet


@lru_cache(maxsize=1)
def load_ngfs_scenarios() -> Dict[str, NGFSScenario]:
    """Load NGFS scenarios from CSV."""
    data_root = get_data_root()
    csv_path = data_root / "financial" / "ngfs_scenarios.csv"

    scenarios = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            scenario_type = row['scenario_type']
            scenarios[scenario_type] = NGFSScenario(
                scenario_type=scenario_type,
                name=row['name'],
                description=row['description'],
                temp_2030_c=float(row['temp_2030_c']),
                temp_2050_c=float(row['temp_2050_c']),
                temp_2100_c=float(row['temp_2100_c']),
                physical_risk_multiplier=float(row['physical_risk_multiplier']),
                acute_risk_multiplier=float(row['acute_risk_multiplier']),
                chronic_risk_multiplier=float(row['chronic_risk_multiplier']),
                transition_risk_multiplier=float(row['transition_risk_multiplier']),
                carbon_price_2030_usd=float(row['carbon_price_2030_usd']),
                carbon_price_2050_usd=float(row['carbon_price_2050_usd']),
                gdp_impact_2030_pct=float(row['gdp_impact_2030_pct']),
                gdp_impact_2050_pct=float(row['gdp_impact_2050_pct']),
                probability=float(row['probability']),
            )
    return scenarios


@lru_cache(maxsize=1)
def load_generation_loss_factors() -> Dict[Tuple[str, int], GenerationLossFactor]:
    """Load generation loss factors from CSV."""
    data_root = get_data_root()
    csv_path = data_root / "financial" / "generation_loss_factors.csv"

    factors = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row['plant_technology'], int(row['year']))
            factors[key] = GenerationLossFactor(
                plant_technology=row['plant_technology'],
                year=int(row['year']),
                water_stress_loss_pct=float(row['water_stress_loss_pct']),
                temperature_loss_pct=float(row['temperature_loss_pct']),
                combined_loss_pct=float(row['combined_loss_pct']),
                total_loss_pct=float(row['total_loss_pct']),
                source=row['source'],
            )
    return factors


@lru_cache(maxsize=1)
def load_credit_spreads() -> Dict[str, CreditSpread]:
    """Load credit spread data from CSV."""
    data_root = get_data_root()
    csv_path = data_root / "financial" / "credit_spreads.csv"

    spreads = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rating = row['rating']
            spreads[rating] = CreditSpread(
                rating=rating,
                spread_bps=int(row['spread_bps']),
                pd_1y=float(row['pd_1y']),
                pd_10y=float(row['pd_10y']),
                lgd=float(row['lgd']),
                recovery_rate=float(row['recovery_rate']),
                source=row['source'],
            )
    return spreads


def get_generation_loss(technology: str, year: int, scenario: str = "RCP8.5") -> float:
    """
    Get interpolated generation loss for a technology and year.

    Args:
        technology: Plant technology (e.g., "coal_supercritical", "ccgt")
        year: Target year
        scenario: Climate scenario (affects interpolation factor)

    Returns:
        Total generation loss as percentage
    """
    factors = load_generation_loss_factors()

    # Get available years for this technology
    tech_years = sorted([y for (t, y) in factors.keys() if t == technology])

    if not tech_years:
        return 0.0

    # Before first year
    if year <= tech_years[0]:
        return factors[(technology, tech_years[0])].total_loss_pct

    # After last year
    if year >= tech_years[-1]:
        return factors[(technology, tech_years[-1])].total_loss_pct

    # Linear interpolation
    for i, y in enumerate(tech_years[:-1]):
        if tech_years[i] <= year < tech_years[i + 1]:
            y0, y1 = tech_years[i], tech_years[i + 1]
            f0 = factors[(technology, y0)].total_loss_pct
            f1 = factors[(technology, y1)].total_loss_pct
            return f0 + (f1 - f0) * (year - y0) / (y1 - y0)

    return 0.0


# =============================================================================
# CALIBRATION DATA LOADERS
# =============================================================================

@dataclass
class HistoricalEvent:
    """Historical disaster event from CSV."""
    event_id: str
    event_name: str
    hazard_type: str
    date: str
    location: str
    intensity: float
    intensity_unit: str
    observed_damage_usd: float
    exposed_value_usd: float
    damage_ratio: float
    source: str
    data_quality: float


@lru_cache(maxsize=1)
def load_historical_events() -> Dict[str, List[HistoricalEvent]]:
    """Load historical events from CSV, organized by hazard type."""
    data_root = get_data_root()
    csv_path = data_root / "calibration" / "historical_events.csv"

    events: Dict[str, List[HistoricalEvent]] = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            hazard_type = row['hazard_type']
            event = HistoricalEvent(
                event_id=row['event_id'],
                event_name=row['event_name'],
                hazard_type=hazard_type,
                date=row['date'],
                location=row['location'],
                intensity=float(row['intensity']),
                intensity_unit=row['intensity_unit'],
                observed_damage_usd=float(row['observed_damage_usd']),
                exposed_value_usd=float(row['exposed_value_usd']),
                damage_ratio=float(row['damage_ratio']),
                source=row['source'],
                data_quality=float(row['data_quality']),
            )

            if hazard_type not in events:
                events[hazard_type] = []
            events[hazard_type].append(event)

    return events


# =============================================================================
# TEMPERATURE PROJECTIONS
# =============================================================================

@dataclass
class TemperatureProjection:
    """Temperature projection data from CSV."""
    scenario: str
    year: int
    delta_t_air: float
    delta_t_sst: float
    heat_wave_days: float
    tropical_nights: float
    max_temp_increase: float
    confidence_low: float
    confidence_high: float
    source: str


@lru_cache(maxsize=1)
def load_temperature_projections() -> Dict[str, Dict[int, TemperatureProjection]]:
    """Load temperature projections from CSV, organized by scenario and year."""
    data_root = get_data_root()
    csv_path = data_root / "physical" / "temperature_projections.csv"

    projections: Dict[str, Dict[int, TemperatureProjection]] = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            scenario = row['scenario']
            year = int(row['year'])

            if scenario not in projections:
                projections[scenario] = {}

            projections[scenario][year] = TemperatureProjection(
                scenario=scenario,
                year=year,
                delta_t_air=float(row['delta_t_air']),
                delta_t_sst=float(row['delta_t_sst']),
                heat_wave_days=float(row['heat_wave_days']),
                tropical_nights=float(row['tropical_nights']),
                max_temp_increase=float(row['max_temp_increase']),
                confidence_low=float(row['confidence_low']),
                confidence_high=float(row['confidence_high']),
                source=row['source'],
            )
    return projections


# =============================================================================
# PLANT EXPOSURE DATA
# =============================================================================

@dataclass
class PlantExposure:
    """Plant exposure data from CSV."""
    plant_id: str
    plant_name: str
    owner: str
    plant_type: str
    cooling_system: str
    capacity_mw: float
    latitude: float
    longitude: float
    elevation_m: float
    distance_coast_km: float
    distance_river_km: float
    construction_year: int
    design_life_years: int
    remaining_life_years: int
    replacement_cost_musd: float
    book_value_musd: float
    annual_revenue_musd: float
    design_temperature_c: float
    design_wind_speed_ms: float
    design_flood_depth_m: float
    flood_zone: str
    seismic_zone: str
    fire_risk_zone: str
    backup_cooling: bool
    emergency_power: bool
    flood_protection: bool
    fire_suppression: bool
    weather_monitoring: bool
    remote_operation: bool
    insurance_coverage: str
    data_source: str
    last_updated: str


@lru_cache(maxsize=1)
def load_plant_exposures() -> Dict[str, PlantExposure]:
    """Load plant exposure data from CSV."""
    data_root = get_data_root()
    csv_path = data_root / "physical" / "plant_exposure.csv"

    plants = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            plant_id = row['plant_id']
            plants[plant_id] = PlantExposure(
                plant_id=plant_id,
                plant_name=row['plant_name'],
                owner=row['owner'],
                plant_type=row['plant_type'],
                cooling_system=row['cooling_system'],
                capacity_mw=float(row['capacity_mw']),
                latitude=float(row['latitude']),
                longitude=float(row['longitude']),
                elevation_m=float(row['elevation_m']),
                distance_coast_km=float(row['distance_coast_km']),
                distance_river_km=float(row['distance_river_km']),
                construction_year=int(row['construction_year']),
                design_life_years=int(row['design_life_years']),
                remaining_life_years=int(row['remaining_life_years']),
                replacement_cost_musd=float(row['replacement_cost_musd']),
                book_value_musd=float(row['book_value_musd']),
                annual_revenue_musd=float(row['annual_revenue_musd']),
                design_temperature_c=float(row['design_temperature_c']),
                design_wind_speed_ms=float(row['design_wind_speed_ms']),
                design_flood_depth_m=float(row['design_flood_depth_m']),
                flood_zone=row['flood_zone'],
                seismic_zone=row['seismic_zone'],
                fire_risk_zone=row['fire_risk_zone'],
                backup_cooling=row['backup_cooling'].lower() == 'true',
                emergency_power=row['emergency_power'].lower() == 'true',
                flood_protection=row['flood_protection'].lower() == 'true',
                fire_suppression=row['fire_suppression'].lower() == 'true',
                weather_monitoring=row['weather_monitoring'].lower() == 'true',
                remote_operation=row['remote_operation'].lower() == 'true',
                insurance_coverage=row['insurance_coverage'],
                data_source=row['data_source'],
                last_updated=row['last_updated'],
            )
    return plants


# =============================================================================
# DATA SOURCES AND FLOOD RISK NOTES
# =============================================================================

@dataclass
class DataSourceInfo:
    """Data source metadata from CSV."""
    hazard_type: str
    primary_source: str
    fallback_source: str
    data_status: str
    coverage_years: str
    spatial_resolution: str
    notes: str


@lru_cache(maxsize=1)
def load_data_sources() -> Dict[str, DataSourceInfo]:
    """Load data source metadata from CSV."""
    data_root = get_data_root()
    csv_path = data_root / "physical" / "data_sources.csv"

    sources = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            hazard_type = row['hazard_type']
            sources[hazard_type] = DataSourceInfo(
                hazard_type=hazard_type,
                primary_source=row['primary_source'],
                fallback_source=row['fallback_source'],
                data_status=row['data_status'],
                coverage_years=row['coverage_years'],
                spatial_resolution=row['spatial_resolution'],
                notes=row['notes'],
            )
    return sources


@dataclass
class FloodRiskNote:
    """Flood risk documentation from CSV."""
    plant_id: str
    plant_name: str
    elevation_m: float
    flood_zone: str
    river_flood_risk: float
    coastal_flood_risk: float
    justification: str
    verification_source: str
    verification_date: str


@lru_cache(maxsize=1)
def load_flood_risk_notes() -> Dict[str, FloodRiskNote]:
    """Load flood risk documentation from CSV."""
    data_root = get_data_root()
    csv_path = data_root / "physical" / "flood_risk_notes.csv"

    notes = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            plant_id = row['plant_id']
            notes[plant_id] = FloodRiskNote(
                plant_id=plant_id,
                plant_name=row['plant_name'],
                elevation_m=float(row['elevation_m']),
                flood_zone=row['flood_zone'],
                river_flood_risk=float(row['river_flood_risk']),
                coastal_flood_risk=float(row['coastal_flood_risk']),
                justification=row['justification'],
                verification_source=row['verification_source'],
                verification_date=row['verification_date'],
            )
    return notes


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def clear_all_caches():
    """Clear all cached data. Use when CSV files are updated."""
    load_hazard_baselines.cache_clear()
    load_climate_factors.cache_clear()
    load_compound_events.cache_clear()
    load_damage_function_params.cache_clear()
    load_korean_coal_fleet.cache_clear()
    load_ngfs_scenarios.cache_clear()
    load_generation_loss_factors.cache_clear()
    load_credit_spreads.cache_clear()
    load_historical_events.cache_clear()
    load_temperature_projections.cache_clear()
    load_plant_exposures.cache_clear()
    load_data_sources.cache_clear()
    load_flood_risk_notes.cache_clear()


def validate_data_files() -> Dict[str, bool]:
    """Check that all required CSV files exist."""
    data_root = get_data_root()

    required_files = [
        "physical/hazard_baselines.csv",
        "physical/climate_factors.csv",
        "physical/compound_events.csv",
        "physical/damage_function_params.csv",
        "physical/temperature_projections.csv",
        "physical/plant_exposure.csv",
        "physical/data_sources.csv",
        "physical/flood_risk_notes.csv",
        "financial/korean_coal_fleet.csv",
        "financial/ngfs_scenarios.csv",
        "financial/generation_loss_factors.csv",
        "financial/credit_spreads.csv",
        "calibration/historical_events.csv",
    ]

    results = {}
    for file_path in required_files:
        full_path = data_root / file_path
        results[file_path] = full_path.exists()

    return results


def get_data_summary() -> Dict[str, Any]:
    """Get summary of all loaded data."""
    return {
        "hazard_baselines": len(load_hazard_baselines()),
        "climate_scenarios": len(load_climate_factors()),
        "compound_events": len(load_compound_events()),
        "damage_functions": len(load_damage_function_params()),
        "temperature_projections": sum(len(v) for v in load_temperature_projections().values()),
        "plant_exposures": len(load_plant_exposures()),
        "data_sources": len(load_data_sources()),
        "flood_risk_notes": len(load_flood_risk_notes()),
        "coal_plants": len(load_korean_coal_fleet()),
        "ngfs_scenarios": len(load_ngfs_scenarios()),
        "generation_loss_entries": len(load_generation_loss_factors()),
        "credit_ratings": len(load_credit_spreads()),
        "historical_events": sum(len(v) for v in load_historical_events().values()),
    }

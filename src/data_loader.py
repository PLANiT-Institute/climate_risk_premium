"""
Unified Data Loader for Climate Risk Premium Model

Loads all input CSV files from data/input/ directory and provides
clean interfaces for each module to access the data they need.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class PlantParameters:
    """Samcheok Blue Power Plant technical specifications."""
    capacity_mw: float
    capacity_factor: float
    efficiency: float
    total_capex_million: float
    operating_years: int
    debt_fraction: float
    debt_interest_rate: float
    debt_tenor_years: int
    power_price_per_mwh: float
    fuel_price_per_mmbtu: float
    heat_rate_mmbtu_mwh: float
    emissions_tCO2_per_mwh: float
    fixed_opex_per_kw: float
    variable_opex_per_mwh: float
    tax_rate: float
    discount_rate: float
    risk_free_rate: float
    
    @classmethod
    def from_csv(cls, df: pd.DataFrame) -> 'PlantParameters':
        """Create from CSV loaded as param_name -> value DataFrame."""
        params = df.set_index('param_name')['value'].to_dict()
        return cls(
            capacity_mw=float(params.get('capacity_mw', 2100)),
            capacity_factor=float(params.get('capacity_factor', 0.85)),
            efficiency=float(params.get('efficiency', 0.42)),
            total_capex_million=float(params.get('total_capex_million', 4900)),
            operating_years=int(float(params.get('operating_years', 40))),
            debt_fraction=float(params.get('debt_fraction', 0.70)),
            debt_interest_rate=float(params.get('debt_interest_rate', 0.061)),
            debt_tenor_years=int(float(params.get('debt_tenor_years', 20))),
            power_price_per_mwh=float(params.get('power_price_per_mwh', 80.0)),
            fuel_price_per_mmbtu=float(params.get('fuel_price_per_mmbtu', 3.2)),
            heat_rate_mmbtu_mwh=float(params.get('heat_rate_mmbtu_mwh', 9.5)),
            emissions_tCO2_per_mwh=float(params.get('emissions_tCO2_per_mwh', 0.95)),
            fixed_opex_per_kw=float(params.get('fixed_opex_per_kw', 35.0)),
            variable_opex_per_mwh=float(params.get('variable_opex_per_mwh', 4.5)),
            tax_rate=float(params.get('tax_rate', params.get('corporate_tax_rate', 0.24))),
            discount_rate=float(params.get('discount_rate', 0.08)),
            risk_free_rate=float(params.get('risk_free_rate', 0.035)),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'capacity_mw': self.capacity_mw,
            'capacity_factor': self.capacity_factor,
            'efficiency': self.efficiency,
            'total_capex_million': self.total_capex_million,
            'operating_years': self.operating_years,
            'debt_fraction': self.debt_fraction,
            'debt_interest_rate': self.debt_interest_rate,
            'debt_tenor_years': self.debt_tenor_years,
            'power_price_per_mwh': self.power_price_per_mwh,
            'fuel_price_per_mmbtu': self.fuel_price_per_mmbtu,
            'heat_rate_mmbtu_mwh': self.heat_rate_mmbtu_mwh,
            'emissions_tCO2_per_mwh': self.emissions_tCO2_per_mwh,
            'fixed_opex_per_kw': self.fixed_opex_per_kw,
            'variable_opex_per_mwh': self.variable_opex_per_mwh,
            'tax_rate': self.tax_rate,
            'discount_rate': self.discount_rate,
            'risk_free_rate': self.risk_free_rate,
        }


@dataclass
class TransitionScenario:
    """Transition risk scenario."""
    name: str
    dispatch_penalty: float
    retirement_years: int
    carbon_prices: Dict[int, float] = field(default_factory=dict)
    description: str = ""


@dataclass
class PhysicalScenario:
    """Physical risk scenario from CLIMADA data."""
    name: str
    rcp_scenario: str
    target_year: int
    wildfire_outage_rate: float
    flood_outage_rate: float
    slr_capacity_derate: float
    compound_multiplier: float
    fwi_index: float
    slr_meters: float
    data_source: str
    
    @property
    def total_outage_rate(self) -> float:
        return (self.wildfire_outage_rate + self.flood_outage_rate) * self.compound_multiplier
    
    @property
    def total_capacity_derate(self) -> float:
        return self.slr_capacity_derate


@dataclass 
class MarketScenario:
    """Year-by-year market price data."""
    year: int
    scenario: str
    smp_usd_mwh: float
    coal_price_usd_ton: float
    carbon_price_usd_ton: float
    cpi_index: float


@dataclass
class CreditRatingGrid:
    """KIS credit rating threshold grid."""
    thresholds: Dict[str, Dict[str, float]]
    spreads: Dict[str, int]


# =============================================================================
# DATA LOADER
# =============================================================================

class DataLoader:
    """Unified data loader for all input CSV files."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.input_dir = self.base_dir / "data" / "input"
        
        if not self.input_dir.exists():
            self.input_dir = self.base_dir / "data" / "raw"
            if not self.input_dir.exists():
                self.input_dir = self.base_dir / "archive" / "legacy_data_raw"
    
    def load_plant_parameters(self) -> PlantParameters:
        path = self.input_dir / "plant_parameters.csv"
        df = pd.read_csv(path)
        return PlantParameters.from_csv(df)
    
    def load_transition_scenarios(self) -> Dict[str, TransitionScenario]:
        path = self.input_dir / "transition_scenarios.csv"
        if not path.exists():
            path = self.input_dir / "policy.csv"
        
        df = pd.read_csv(path)
        scenarios = {}
        
        for _, row in df.iterrows():
            name = row['scenario']
            carbon_prices = {}
            for col in df.columns:
                if col.startswith('carbon_price_'):
                    year = int(col.replace('carbon_price_', ''))
                    carbon_prices[year] = float(row[col])
            
            scenarios[name] = TransitionScenario(
                name=name,
                dispatch_penalty=float(row['dispatch_penalty']),
                retirement_years=int(row['retirement_years']),
                carbon_prices=carbon_prices,
                description=str(row.get('description', '')),
            )
        
        return scenarios
    
    def load_korea_power_plan(self) -> pd.DataFrame:
        path = self.input_dir / "korea_power_plan.csv"
        return pd.read_csv(path)
    
    def load_physical_scenarios(self) -> Dict[str, PhysicalScenario]:
        # Prefer literature_hazards.csv (has correct schema: scenario, wildfire_outage_rate, etc.)
        # physical_scenarios.csv has different schema (scenario_name, hazard_type, parameter, value)
        path = self.input_dir / "literature_hazards.csv"
        if not path.exists():
            # Legacy fallback
            path = self.input_dir / "climada_hazards.csv"
        
        df = pd.read_csv(path)
        scenarios = {}
        
        for _, row in df.iterrows():
            name = row['scenario']
            scenarios[name] = PhysicalScenario(
                name=name,
                rcp_scenario=row.get('rcp_scenario', 'current'),
                target_year=int(row.get('target_year', 2024)),
                wildfire_outage_rate=float(row['wildfire_outage_rate']),
                flood_outage_rate=float(row['flood_outage_rate']),
                slr_capacity_derate=float(row['slr_capacity_derate']),
                compound_multiplier=float(row.get('compound_multiplier', 1.0)),
                fwi_index=float(row.get('fwi_index', 0)),
                slr_meters=float(row.get('slr_meters', 0)),
                data_source=row.get('data_source', 'CLIMADA'),
            )
        
        return scenarios
    
    def load_market_scenarios(self) -> Dict[str, List[MarketScenario]]:
        path = self.input_dir / "market_scenarios.csv"
        df = pd.read_csv(path)
        
        scenarios: Dict[str, List[MarketScenario]] = {}
        
        for _, row in df.iterrows():
            scenario_name = row['scenario']
            if scenario_name not in scenarios:
                scenarios[scenario_name] = []
            
            scenarios[scenario_name].append(MarketScenario(
                year=int(row['year']),
                scenario=scenario_name,
                smp_usd_mwh=float(row['smp_usd_mwh']),
                coal_price_usd_ton=float(row['coal_price_usd_ton']),
                carbon_price_usd_ton=float(row['carbon_price_usd_ton']),
                cpi_index=float(row['cpi_index']),
            ))
        
        for name in scenarios:
            scenarios[name].sort(key=lambda x: x.year)
        
        return scenarios
    
    def load_financing_parameters(self) -> Dict[str, float]:
        path = self.input_dir / "financing_parameters.csv"
        if not path.exists():
            path = self.input_dir / "financing_params.csv"
        
        df = pd.read_csv(path)
        return df.set_index('param_name')['value'].to_dict()
    
    def load_credit_rating_grid(self) -> CreditRatingGrid:
        path = self.input_dir / "credit_rating_grid.csv"
        df = pd.read_csv(path)
        
        thresholds = {}
        spreads = {}
        ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B']
        
        for _, row in df.iterrows():
            metric = row['metric']
            if metric == 'spread_bps':
                for rating in ratings:
                    spreads[rating] = int(row[rating])
            else:
                thresholds[metric] = {rating: float(row[rating]) for rating in ratings}
        
        return CreditRatingGrid(thresholds=thresholds, spreads=spreads)
    
    def load_debt_schedule(self) -> pd.DataFrame:
        path = self.input_dir / "debt_schedule.csv"
        if not path.exists():
            path = self.input_dir / "debt_repayment_schedule.csv"
        return pd.read_csv(path)
    
    def load_all(self) -> Dict[str, Any]:
        return {
            'plant': self.load_plant_parameters(),
            'transition': self.load_transition_scenarios(),
            'power_plan': self.load_korea_power_plan(),
            'physical': self.load_physical_scenarios(),
            'market': self.load_market_scenarios(),
            'financing': self.load_financing_parameters(),
            'credit_grid': self.load_credit_rating_grid(),
            'debt_schedule': self.load_debt_schedule(),
        }


def load_data(base_dir: Path = None) -> Dict[str, Any]:
    """Quick function to load all data."""
    if base_dir is None:
        base_dir = Path(".")
    loader = DataLoader(base_dir)
    return loader.load_all()


if __name__ == "__main__":
    loader = DataLoader(Path("."))
    data = loader.load_all()
    
    print("=== Data Loader Test ===")
    print(f"Plant capacity: {data['plant'].capacity_mw} MW")
    print(f"Transition scenarios: {list(data['transition'].keys())}")
    print(f"Physical scenarios: {list(data['physical'].keys())}")
    print(f"Market scenarios: {list(data['market'].keys())}")

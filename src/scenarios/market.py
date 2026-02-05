"""
Market scenarios (Power Demand, Price).
"""
from dataclasses import dataclass


@dataclass
class MarketScenario:
    """
    Market conditions affecting the plant's economics.
    
    Attributes:
        name: Scenario name
        demand_growth_pct: Annual growth (or decline) in power demand (%)
        price_sensitivity: % change in price per 1% change in demand
        base_power_price: Starting power price ($/MWh)
    """
    name: str
    demand_growth_pct: float = 1.0  # 1% annual growth
    price_sensitivity: float = 0.5  # 0.5% price change per 1% demand change
    base_power_price: float = 80.0

    def get_demand_factor(self, year: int, base_year: int = 2025) -> float:
        """Calculate demand multiplier relative to base year."""
        years_elapsed = year - base_year
        return (1 + self.demand_growth_pct / 100) ** years_elapsed

    def get_power_price(self, year: int, base_year: int = 2025) -> float:
        """Calculate power price based on demand growth."""
        demand_factor = self.get_demand_factor(year, base_year)
        demand_change_pct = (demand_factor - 1) * 100
        
        # Price changes based on sensitivity to demand
        price_change_pct = demand_change_pct * self.price_sensitivity
        price_factor = 1 + (price_change_pct / 100)
        
        return self.base_power_price * price_factor

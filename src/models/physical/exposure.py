"""
Exposure and Vulnerability Module.

Quantifies asset exposure and vulnerability to climate hazards.
Based on CLIMADA framework: Risk = Hazard × Exposure × Vulnerability

Exposure Components:
1. Asset value (replacement cost, revenue capacity)
2. Geographic exposure (location, elevation, coastal proximity)
3. Operational exposure (capacity, generation, utilization)

Vulnerability Components:
1. Physical vulnerability (design standards, age, condition)
2. Operational vulnerability (cooling type, fuel type)
3. Adaptive capacity (backup systems, redundancy)

Sources:
- CLIMADA Exposure module
- KEPCO power plant statistics
- Korea Electric Power Statistics
- IEA World Energy Investment
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import date
import math


class PlantType(Enum):
    """Power plant technology types."""
    COAL_SUBCRITICAL = "coal_subcritical"
    COAL_SUPERCRITICAL = "coal_supercritical"
    COAL_USC = "coal_usc"          # Ultra-supercritical
    GAS_CCGT = "gas_ccgt"          # Combined cycle gas turbine
    GAS_OCGT = "gas_ocgt"          # Open cycle gas turbine
    NUCLEAR = "nuclear"
    HYDRO = "hydro"
    SOLAR_PV = "solar_pv"
    WIND_ONSHORE = "wind_onshore"
    WIND_OFFSHORE = "wind_offshore"


class CoolingSystem(Enum):
    """Cooling system types."""
    ONCE_THROUGH_SEA = "once_through_sea"
    ONCE_THROUGH_RIVER = "once_through_river"
    COOLING_TOWER_WET = "cooling_tower_wet"
    COOLING_TOWER_DRY = "cooling_tower_dry"
    COOLING_TOWER_HYBRID = "cooling_tower_hybrid"
    AIR_COOLED = "air_cooled"


class VulnerabilityClass(Enum):
    """Vulnerability classification levels."""
    VERY_LOW = "very_low"      # Modern design, excellent maintenance
    LOW = "low"                # Recent construction, good maintenance
    MEDIUM = "medium"          # Standard design, normal maintenance
    HIGH = "high"              # Older plant, some deficiencies
    VERY_HIGH = "very_high"    # Aging infrastructure, poor condition


@dataclass
class AssetValue:
    """
    Asset value components.

    Attributes:
        replacement_cost_musd: Full replacement cost (million USD)
        book_value_musd: Current book value
        annual_revenue_musd: Annual revenue
        npv_remaining_musd: NPV of remaining cash flows
        currency: Currency code
        valuation_date: Date of valuation
    """
    replacement_cost_musd: float
    book_value_musd: float = 0.0
    annual_revenue_musd: float = 0.0
    npv_remaining_musd: float = 0.0
    currency: str = "USD"
    valuation_date: str = "2024-01-01"


@dataclass
class GeographicExposure:
    """
    Geographic exposure characteristics.

    Attributes:
        latitude: Decimal degrees north
        longitude: Decimal degrees east
        elevation_m: Elevation above sea level (m)
        distance_coast_km: Distance to coastline (km)
        distance_river_km: Distance to nearest river (km)
        flood_zone: FEMA-equivalent flood zone
        seismic_zone: Seismic hazard zone
        fire_risk_zone: Wildfire risk zone
    """
    latitude: float
    longitude: float
    elevation_m: float = 0.0
    distance_coast_km: float = 0.0
    distance_river_km: float = 0.0
    flood_zone: str = "X"           # X = minimal flood risk
    seismic_zone: str = "low"
    fire_risk_zone: str = "low"


@dataclass
class OperationalExposure:
    """
    Operational exposure characteristics.

    Attributes:
        capacity_mw: Installed capacity (MW)
        annual_generation_gwh: Annual generation (GWh)
        capacity_factor: Average capacity factor (0-1)
        planned_outage_rate: Planned outage rate (0-1)
        forced_outage_rate: Historical forced outage rate (0-1)
        operating_hours_year: Annual operating hours
        start_stop_cycles: Annual start/stop cycles
    """
    capacity_mw: float
    annual_generation_gwh: float = 0.0
    capacity_factor: float = 0.85
    planned_outage_rate: float = 0.05
    forced_outage_rate: float = 0.03
    operating_hours_year: float = 7446.0  # 85% CF
    start_stop_cycles: int = 50


@dataclass
class PhysicalVulnerability:
    """
    Physical vulnerability characteristics.

    Attributes:
        plant_type: Technology type
        cooling_system: Cooling system type
        design_temperature_c: Design ambient temperature
        design_wind_speed_ms: Design wind speed
        design_flood_depth_m: Design flood depth
        construction_year: Year of construction
        design_life_years: Original design life
        remaining_life_years: Estimated remaining life
        design_code: Design code/standard
    """
    plant_type: PlantType
    cooling_system: CoolingSystem
    design_temperature_c: float = 35.0
    design_wind_speed_ms: float = 40.0
    design_flood_depth_m: float = 0.5
    construction_year: int = 2017
    design_life_years: int = 40
    remaining_life_years: int = 33
    design_code: str = "KEPCO Standard"


@dataclass
class AdaptiveCapacity:
    """
    Adaptive capacity and resilience measures.

    Attributes:
        backup_cooling: Has backup cooling system
        emergency_power: Has emergency power
        flood_protection: Has flood protection measures
        fire_suppression: Has wildfire protection
        weather_monitoring: Has advanced weather monitoring
        remote_operation: Can operate remotely
        insurance_coverage: Level of insurance coverage
    """
    backup_cooling: bool = False
    emergency_power: bool = True
    flood_protection: bool = True
    fire_suppression: bool = True
    weather_monitoring: bool = True
    remote_operation: bool = True
    insurance_coverage: str = "full"


@dataclass
class PowerPlantExposure:
    """
    Complete power plant exposure profile.

    Combines asset value, geographic, operational, and vulnerability
    characteristics into a comprehensive exposure profile.
    """
    name: str
    plant_id: str
    owner: str

    # Value
    asset_value: AssetValue

    # Geographic
    geographic: GeographicExposure

    # Operational
    operational: OperationalExposure

    # Vulnerability
    physical: PhysicalVulnerability
    adaptive: AdaptiveCapacity

    # Metadata
    data_source: str = ""
    last_updated: str = ""

    def get_vulnerability_class(self) -> VulnerabilityClass:
        """Calculate overall vulnerability class."""
        score = 0

        # Age factor
        age = 2024 - self.physical.construction_year
        if age < 10:
            score += 1
        elif age < 20:
            score += 2
        elif age < 30:
            score += 3
        else:
            score += 4

        # Cooling system factor
        if self.physical.cooling_system == CoolingSystem.ONCE_THROUGH_SEA:
            score += 1  # Reliable water source
        elif self.physical.cooling_system == CoolingSystem.COOLING_TOWER_WET:
            score += 2
        elif self.physical.cooling_system == CoolingSystem.ONCE_THROUGH_RIVER:
            score += 3  # Drought vulnerable
        else:
            score += 2

        # Geographic factors
        if self.geographic.elevation_m < 5:
            score += 2  # Flood risk
        if self.geographic.fire_risk_zone == "high":
            score += 2

        # Adaptive capacity
        adaptive_score = sum([
            self.adaptive.backup_cooling,
            self.adaptive.emergency_power,
            self.adaptive.flood_protection,
            self.adaptive.fire_suppression,
            self.adaptive.weather_monitoring,
        ])
        score -= adaptive_score  # Reduce vulnerability

        # Map to class
        if score <= 2:
            return VulnerabilityClass.VERY_LOW
        elif score <= 4:
            return VulnerabilityClass.LOW
        elif score <= 6:
            return VulnerabilityClass.MEDIUM
        elif score <= 8:
            return VulnerabilityClass.HIGH
        else:
            return VulnerabilityClass.VERY_HIGH

    def get_exposure_at_risk(self, hazard_type: str) -> float:
        """
        Calculate exposure at risk for a specific hazard.

        Returns fraction of asset value at risk.
        """
        base_exposure = 1.0

        if hazard_type == "wildfire":
            if self.geographic.fire_risk_zone == "low":
                return base_exposure * 0.1
            elif self.geographic.fire_risk_zone == "medium":
                return base_exposure * 0.3
            else:
                return base_exposure * 0.6

        elif hazard_type == "flood":
            if self.geographic.elevation_m > 10:
                return base_exposure * 0.05
            elif self.geographic.elevation_m > 5:
                return base_exposure * 0.2
            else:
                return base_exposure * 0.5

        elif hazard_type == "tropical_cyclone":
            if self.geographic.distance_coast_km > 50:
                return base_exposure * 0.3
            elif self.geographic.distance_coast_km > 20:
                return base_exposure * 0.5
            else:
                return base_exposure * 0.8

        elif hazard_type == "drought":
            if self.physical.cooling_system in [
                CoolingSystem.ONCE_THROUGH_SEA,
                CoolingSystem.COOLING_TOWER_DRY,
            ]:
                return base_exposure * 0.1
            else:
                return base_exposure * 0.5

        elif hazard_type == "heat_stress":
            # All thermal plants affected
            return base_exposure * 0.8

        else:
            return base_exposure * 0.5


# =============================================================================
# VULNERABILITY FUNCTIONS
# =============================================================================

def calculate_vulnerability_factor(
    exposure: PowerPlantExposure,
    hazard_type: str,
) -> float:
    """
    Calculate vulnerability factor for a hazard.

    Returns factor between 0 (no vulnerability) and 1 (maximum vulnerability).
    """
    vuln_class = exposure.get_vulnerability_class()

    # Base vulnerability by class
    base_vuln = {
        VulnerabilityClass.VERY_LOW: 0.2,
        VulnerabilityClass.LOW: 0.4,
        VulnerabilityClass.MEDIUM: 0.6,
        VulnerabilityClass.HIGH: 0.8,
        VulnerabilityClass.VERY_HIGH: 1.0,
    }[vuln_class]

    # Hazard-specific adjustments
    if hazard_type == "heat_stress":
        # Cooling system matters most
        if exposure.physical.cooling_system == CoolingSystem.ONCE_THROUGH_SEA:
            return base_vuln * 0.7
        elif exposure.physical.cooling_system == CoolingSystem.COOLING_TOWER_DRY:
            return base_vuln * 1.3
        else:
            return base_vuln

    elif hazard_type == "drought":
        if exposure.physical.cooling_system == CoolingSystem.ONCE_THROUGH_SEA:
            return base_vuln * 0.2  # Seawater not affected
        elif exposure.physical.cooling_system == CoolingSystem.ONCE_THROUGH_RIVER:
            return base_vuln * 1.5  # Very vulnerable
        else:
            return base_vuln

    elif hazard_type == "flood":
        if exposure.adaptive.flood_protection:
            return base_vuln * 0.5
        return base_vuln

    elif hazard_type == "wildfire":
        if exposure.adaptive.fire_suppression:
            return base_vuln * 0.6
        return base_vuln

    else:
        return base_vuln


def calculate_expected_damage(
    exposure: PowerPlantExposure,
    hazard_type: str,
    hazard_intensity: float,
    damage_function_result: float,
) -> Dict[str, float]:
    """
    Calculate expected damage in monetary terms.

    Args:
        exposure: Plant exposure profile
        hazard_type: Type of hazard
        hazard_intensity: Hazard intensity
        damage_function_result: Result from damage function

    Returns:
        Dict with damage values
    """
    # Exposure at risk
    exposure_factor = exposure.get_exposure_at_risk(hazard_type)

    # Vulnerability factor
    vuln_factor = calculate_vulnerability_factor(exposure, hazard_type)

    # Total damage ratio
    damage_ratio = damage_function_result * exposure_factor * vuln_factor

    # Monetary damage
    asset_damage = damage_ratio * exposure.asset_value.replacement_cost_musd
    revenue_loss = damage_ratio * exposure.asset_value.annual_revenue_musd

    return {
        "damage_ratio": damage_ratio,
        "exposure_factor": exposure_factor,
        "vulnerability_factor": vuln_factor,
        "asset_damage_musd": asset_damage,
        "revenue_loss_musd": revenue_loss,
        "total_loss_musd": asset_damage + revenue_loss,
    }


# =============================================================================
# PREDEFINED EXPOSURES
# =============================================================================

SAMCHEOK_BLUE_POWER = PowerPlantExposure(
    name="Samcheok Blue Power",
    plant_id="KR-CBP-001",
    owner="Korea Southern Power Co. (KOSPO)",

    asset_value=AssetValue(
        replacement_cost_musd=4500.0,    # ~$4.5B for 2.1GW USC plant
        book_value_musd=3500.0,
        annual_revenue_musd=800.0,       # Estimated annual revenue
        npv_remaining_musd=6000.0,
        currency="USD",
        valuation_date="2024-01-01",
    ),

    geographic=GeographicExposure(
        latitude=37.4404,
        longitude=129.1671,
        elevation_m=10.0,
        distance_coast_km=0.5,          # Coastal plant
        distance_river_km=5.0,
        flood_zone="X",                  # Minimal flood risk (elevated)
        seismic_zone="low",
        fire_risk_zone="medium",         # Gangwon forest area
    ),

    operational=OperationalExposure(
        capacity_mw=2100.0,             # 2.1 GW
        annual_generation_gwh=15500.0,   # ~85% CF
        capacity_factor=0.85,
        planned_outage_rate=0.05,
        forced_outage_rate=0.02,
        operating_hours_year=7446,
        start_stop_cycles=30,
    ),

    physical=PhysicalVulnerability(
        plant_type=PlantType.COAL_USC,
        cooling_system=CoolingSystem.ONCE_THROUGH_SEA,
        design_temperature_c=35.0,
        design_wind_speed_ms=45.0,
        design_flood_depth_m=0.5,
        construction_year=2017,
        design_life_years=40,
        remaining_life_years=33,
        design_code="KEPCO USC Standard 2015",
    ),

    adaptive=AdaptiveCapacity(
        backup_cooling=True,
        emergency_power=True,
        flood_protection=True,
        fire_suppression=True,
        weather_monitoring=True,
        remote_operation=True,
        insurance_coverage="comprehensive",
    ),

    data_source="KEPCO, KOSPO Annual Report 2023",
    last_updated="2024-01-01",
)


# Other Korean coal plants (simplified)
KOREA_COAL_PLANTS: Dict[str, Dict[str, Any]] = {
    "dangjin": {
        "name": "Dangjin Thermal Power",
        "capacity_mw": 6040,
        "plant_type": "coal_supercritical",
        "cooling": "once_through_sea",
        "lat": 36.9310,
        "lon": 126.6325,
        "owner": "Korea East-West Power (EWP)",
    },
    "taean": {
        "name": "Taean Thermal Power",
        "capacity_mw": 6100,
        "plant_type": "coal_supercritical",
        "cooling": "once_through_sea",
        "lat": 36.7536,
        "lon": 126.2642,
        "owner": "Korea Western Power (WP)",
    },
    "boryeong": {
        "name": "Boryeong Thermal Power",
        "capacity_mw": 4000,
        "plant_type": "coal_subcritical",
        "cooling": "once_through_sea",
        "lat": 36.3588,
        "lon": 126.4921,
        "owner": "Korea Midland Power (KOMIPO)",
    },
    "hadong": {
        "name": "Hadong Thermal Power",
        "capacity_mw": 4000,
        "plant_type": "coal_supercritical",
        "cooling": "once_through_sea",
        "lat": 34.9344,
        "lon": 127.8819,
        "owner": "Korea Southern Power (KOSPO)",
    },
}


def get_korea_total_coal_exposure() -> Dict[str, float]:
    """Get total Korean coal power exposure."""
    total_capacity = sum(p["capacity_mw"] for p in KOREA_COAL_PLANTS.values())
    total_capacity += 2100  # Samcheok

    # Estimated values
    avg_capex_per_mw = 2.0  # $2M/MW average
    total_value = total_capacity * avg_capex_per_mw

    return {
        "total_capacity_mw": total_capacity,
        "num_plants": len(KOREA_COAL_PLANTS) + 1,
        "total_replacement_value_musd": total_value,
        "avg_plant_age_years": 15,
    }

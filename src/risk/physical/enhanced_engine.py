"""
Enhanced physical risk engine with modular architecture.

This module provides a sophisticated physical risk assessment system
with improved hazard modeling, exposure analysis, and vulnerability
assessment specifically designed for power generation assets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Protocol, Union
from enum import Enum
import numpy as np
import pandas as pd
import logging

from ..core import (
    RiskMetrics,
    PlantCharacteristics,
    ScenarioParameters,
    RiskType,
    ValidationResult,
    interpolate_linear,
    validate_scenario_consistency,
)

logger = logging.getLogger(__name__)


class HazardType(Enum):
    """Types of physical climate hazards."""
    WILDFIRE = "wildfire"
    FLOOD = "flood"
    DROUGHT = "drought"
    HEAT = "heat"
    STORM = "storm"
    SEA_LEVEL_RISE = "sea_level_rise"
    WATER_SCARCITY = "water_scarcity"


@dataclass
class HazardIntensity:
    """Physical hazard intensity metrics."""
    hazard_type: HazardType
    intensity_value: float
    intensity_unit: str
    frequency: float  # Annual probability
    duration_days: float = 0.0
    spatial_extent_km2: float = 0.0
    
    def get_severity_score(self) -> float:
        """Convert intensity to normalized severity score (0-1)."""
        severity_mappings = {
            HazardType.WILDFIRE: min(1.0, self.intensity_value / 10.0),  # Fire intensity scale 0-10
            HazardType.FLOOD: min(1.0, self.intensity_value / 5.0),     # Flood depth meters
            HazardType.DROUGHT: min(1.0, self.intensity_value / 100.0),  # Drought index
            HazardType.HEAT: min(1.0, max(0.0, (self.intensity_value - 20) / 30)),  # Temp above 20°C
            HazardType.STORM: min(1.0, self.intensity_value / 200),        # Wind speed km/h
            HazardType.WATER_SCARCITY: 1.0 - self.intensity_value,        # Availability fraction
        }
        return severity_mappings.get(self.hazard_type, 0.5)


@dataclass
class AssetExposure:
    """Enhanced asset exposure characteristics."""
    plant: PlantCharacteristics
    
    # Geographic exposure
    latitude: float
    longitude: float
    elevation_m: float
    distance_to_coast_km: float
    distance_to_water_body_km: float
    
    # Physical exposure characteristics
    foundation_type: str  # "shallow", "deep", "piled"
    cooling_system_type: str  # "once_through", "recirculating", "dry_cooled"
    construction_material: str  # "concrete", "steel", "mixed"
    protection_measures: List[str] = field(default_factory=list)  # Flood walls, firebreaks, etc.
    
    # Operational exposure
    water_requirements_m3_per_hour: float = 0.0
    temperature_sensitivity_celsius: float = 0.0  # Efficiency loss per °C above design
    flood_criticality: str = "medium"  # "low", "medium", "high", "critical"
    
    def get_hazard_sensitivity(self, hazard_type: HazardType) -> float:
        """Get asset sensitivity to specific hazard type (0-1)."""
        sensitivity_matrix = {
            HazardType.WILDFIRE: {
                "once_through": 0.3,
                "recirculating": 0.4,
                "dry_cooled": 0.6,  # Higher sensitivity due to outdoor equipment
            }.get(self.cooling_system_type, 0.4),
            HazardType.FLOOD: {
                "shallow": 0.8,
                "deep": 0.5,
                "piled": 0.3,
            }.get(self.foundation_type, 0.5),
            HazardType.DROUGHT: {
                "once_through": 0.9,  # High water dependency
                "recirculating": 0.6,
                "dry_cooled": 0.1,  # Low water dependency
            }.get(self.cooling_system_type, 0.5),
            HazardType.HEAT: {
                "once_through": 0.7,
                "recirculating": 0.8,
                "dry_cooled": 0.9,  # Most sensitive to heat
            }.get(self.cooling_system_type, 0.8),
            HazardType.WATER_SCARCITY: {
                "once_through": 0.9,
                "recirculating": 0.6,
                "dry_cooled": 0.2,
            }.get(self.cooling_system_type, 0.5),
        }
        
        base_sensitivity = sensitivity_matrix.get(hazard_type, 0.5)
        
        # Adjust for protection measures
        protection_reduction = 0.0
        if hazard_type == HazardType.WILDFIRE and "firebreak" in self.protection_measures:
            protection_reduction += 0.2
        if hazard_type == HazardType.FLOOD and "flood_wall" in self.protection_measures:
            protection_reduction += 0.3
        
        return max(0.0, base_sensitivity - protection_reduction)


@dataclass
class DamageFunction:
    """Damage function for specific hazard-asset combination."""
    hazard_type: HazardType
    asset_type: str
    intensity_threshold: float  # Minimum intensity for damage
    damage_curve_params: Dict[str, Union[str, float]]  # Parameters for damage curve
    
    def calculate_damage_ratio(self, intensity: HazardIntensity) -> float:
        """Calculate damage ratio (0-1) given hazard intensity."""
        if intensity.intensity_value < self.intensity_threshold:
            return 0.0
        
        # Use different damage curve types based on parameters
        curve_type = self.damage_curve_params.get("curve_type", "linear")
        
        if curve_type == "linear":
            # Linear damage: ratio = slope * (intensity - threshold)
            slope = float(self.damage_curve_params.get("slope", 0.1))
            excess_intensity = intensity.intensity_value - self.intensity_threshold
            return min(1.0, slope * excess_intensity)
        
        elif curve_type == "exponential":
            # Exponential damage: ratio = 1 - exp(-k * excess_intensity)
            k = float(self.damage_curve_params.get("k", 0.1))
            excess_intensity = intensity.intensity_value - self.intensity_threshold
            return 1 - np.exp(-k * excess_intensity)
        
        elif curve_type == "logistic":
            # Logistic damage function for gradual then rapid damage
            L = float(self.damage_curve_params.get("max_damage", 1.0))  # Maximum damage
            k = float(self.damage_curve_params.get("steepness", 0.5))
            x0 = float(self.damage_curve_params.get("inflection_point", self.intensity_threshold))
            
            x = intensity.intensity_value
            return L / (1 + np.exp(-k * (x - x0)))
        
        else:
            # Default to simple proportional damage
            return min(1.0, (intensity.intensity_value - self.intensity_threshold) / 10.0)


@dataclass
class PhysicalImpact:
    """Comprehensive physical impact assessment."""
    outage_probability: float  # Probability of complete outage
    outage_duration_hours: float
    capacity_derate_fraction: float  # Permanent capacity reduction
    efficiency_loss_fraction: float  # Temporary efficiency loss
    repair_cost_ratio: float  # Repair cost as % of asset value
    water_constraint_factor: float  # Water availability constraint (0-1)
    cumulative_annual_impact_days: float
    
    # Component breakdown
    component_damages: Dict[str, float] = field(default_factory=dict)
    restoration_time_days: float = 0.0
    operational_restrictions: List[str] = field(default_factory=list)
    
    def get_financial_impact(
        self,
        annual_revenue: float,
        fixed_costs: float,
        replacement_cost: float,
    ) -> Dict[str, float]:
        """Calculate financial impact in monetary terms."""
        # Revenue loss from outages
        outage_revenue_loss = (
            annual_revenue * 
            (self.outage_duration_hours / 8760) * 
            self.outage_probability
        )
        
        # Revenue loss from capacity derating
        derate_revenue_loss = annual_revenue * self.capacity_derate_fraction * 0.8  # 80% of year
        
        # Efficiency loss impact
        efficiency_revenue_loss = annual_revenue * self.efficiency_loss_fraction * 0.3  # 30% of year
        
        # Repair costs
        repair_costs = replacement_cost * self.repair_cost_ratio
        
        # Water constraint costs (alternative cooling, water purchase)
        water_costs = fixed_costs * (1 - self.water_constraint_factor) * 0.5
        
        total_impact = (
            outage_revenue_loss + 
            derate_revenue_loss + 
            efficiency_revenue_loss + 
            repair_costs + 
            water_costs
        )
        
        return {
            "outage_revenue_loss": outage_revenue_loss,
            "capacity_derate_loss": derate_revenue_loss,
            "efficiency_loss": efficiency_revenue_loss,
            "repair_costs": repair_costs,
            "water_constraint_costs": water_costs,
            "total_annual_impact": total_impact,
        }


class HazardModel:
    """Physical hazard modeling and intensity calculation."""
    
    def __init__(self):
        self.damage_functions = self._load_damage_functions()
    
    def calculate_hazard_intensity(
        self,
        exposure: AssetExposure,
        scenario: ScenarioParameters,
        year: int,
    ) -> List[HazardIntensity]:
        """
        Calculate hazard intensities for all relevant hazard types.
        
        Args:
            exposure: Asset exposure characteristics
            scenario: Climate risk scenario
            year: Assessment year
            
        Returns:
            List of hazard intensities for the asset
        """
        intensities = []
        
        # Wildfire risk based on location and temperature
        wildfire_intensity = self._calculate_wildfire_intensity(exposure, scenario, year)
        if wildfire_intensity:
            intensities.append(wildfire_intensity)
        
        # Flood risk based on location and elevation
        flood_intensity = self._calculate_flood_intensity(exposure, scenario, year)
        if flood_intensity:
            intensities.append(flood_intensity)
        
        # Drought/water scarcity risk
        drought_intensity = self._calculate_drought_intensity(exposure, scenario, year)
        if drought_intensity:
            intensities.append(drought_intensity)
        
        # Heat stress risk
        heat_intensity = self._calculate_heat_intensity(exposure, scenario, year)
        if heat_intensity:
            intensities.append(heat_intensity)
        
        # Water scarcity specific to power plants
        water_intensity = self._calculate_water_scarcity_intensity(exposure, scenario, year)
        if water_intensity:
            intensities.append(water_intensity)
        
        return intensities
    
    def _calculate_wildfire_intensity(
        self, exposure: AssetExposure, scenario: ScenarioParameters, year: int
    ) -> Optional[HazardIntensity]:
        """Calculate wildfire hazard intensity."""
        # Base fire risk increases with temperature and decreases with precipitation
        base_intensity = 0.1
        
        # Scenario severity adjustment
        severity_multiplier = 1 + (scenario.severity_score * 3)
        
        # Location-based adjustment (simplified)
        if exposure.distance_to_coast_km < 50:
            base_intensity *= 0.3  # Lower coastal fire risk
        
        # Time progression (fire risk increases over time in warming scenarios)
        time_factor = 1 + ((year - 2024) * 0.02)
        
        intensity_value = base_intensity * severity_multiplier * time_factor
        
        if intensity_value > 0.05:  # Threshold for consideration
            return HazardIntensity(
                hazard_type=HazardType.WILDFIRE,
                intensity_value=intensity_value,
                intensity_unit="fire_risk_index",
                frequency=min(0.1, intensity_value * 0.1),  # Annual probability
                duration_days=7.0,
                spatial_extent_km2=100.0,
            )
        
        return None
    
    def _calculate_flood_intensity(
        self, exposure: AssetExposure, scenario: ScenarioParameters, year: int
    ) -> Optional[HazardIntensity]:
        """Calculate flood hazard intensity."""
        base_intensity = 0.05
        
        # Elevation-based adjustment
        if exposure.elevation_m < 10:
            base_intensity *= 3.0  # High flood risk
        elif exposure.elevation_m < 50:
            base_intensity *= 1.5
        
        # Distance to water bodies
        if exposure.distance_to_water_body_km < 1:
            base_intensity *= 2.0
        elif exposure.distance_to_water_body_km < 5:
            base_intensity *= 1.2
        
        # Sea level rise consideration for coastal plants
        if exposure.distance_to_coast_km < 10:
            sea_level_rise = scenario.sea_level_rise_meters or 0.0
            base_intensity += sea_level_rise * 0.1
        
        # Scenario severity
        severity_multiplier = 1 + (scenario.severity_score * 2)
        intensity_value = base_intensity * severity_multiplier
        
        if intensity_value > 0.05:
            return HazardIntensity(
                hazard_type=HazardType.FLOOD,
                intensity_value=intensity_value,
                intensity_unit="depth_meters",
                frequency=min(0.05, intensity_value * 0.05),
                duration_days=3.0,
                spatial_extent_km2=50.0,
            )
        
        return None
    
    def _calculate_drought_intensity(
        self, exposure: AssetExposure, scenario: ScenarioParameters, year: int
    ) -> Optional[HazardIntensity]:
        """Calculate drought hazard intensity."""
        # Base drought intensity based on scenario
        base_intensity = scenario.severity_score * 0.5
        
        # Cooling system dependency
        if exposure.cooling_system_type == "once_through":
            base_intensity *= 1.5
        elif exposure.cooling_system_type == "dry_cooled":
            base_intensity *= 0.3
        
        # Water requirements
        if exposure.water_requirements_m3_per_hour > 10000:
            base_intensity *= 1.2
        
        intensity_value = min(1.0, base_intensity)
        
        if intensity_value > 0.1:
            return HazardIntensity(
                hazard_type=HazardType.DROUGHT,
                intensity_value=intensity_value,
                intensity_unit="drought_index",
                frequency=0.3,  # Droughts are seasonal
                duration_days=90.0,
            )
        
        return None
    
    def _calculate_heat_intensity(
        self, exposure: AssetExposure, scenario: ScenarioParameters, year: int
    ) -> Optional[HazardIntensity]:
        """Calculate heat stress hazard intensity."""
        # Base temperature increase from scenario
        base_temp_increase = scenario.temperature_change_celsius or 0.0
        
        # Add scenario severity effect
        severity_temp_bonus = scenario.severity_score * 2.0
        
        # Location-based adjustment
        if exposure.elevation_m < 100:
            base_temp_increase += 1.0  # Low elevation = hotter
        
        # Cooling system sensitivity
        if exposure.cooling_system_type == "dry_cooled":
            severity_temp_bonus += 1.0  # Dry cooling less effective in heat
        
        # Time progression
        time_factor = 1 + ((year - 2024) * 0.01)
        
        intensity_value = (base_temp_increase + severity_temp_bonus) * time_factor
        
        if intensity_value > 2.0:  # Threshold for consideration
            return HazardIntensity(
                hazard_type=HazardType.HEAT,
                intensity_value=20 + intensity_value,  # Absolute temperature
                intensity_unit="degrees_celsius",
                frequency=0.2,  # Heat waves seasonal
                duration_days=14.0,
            )
        
        return None
    
    def _calculate_water_scarcity_intensity(
        self, exposure: AssetExposure, scenario: ScenarioParameters, year: int
    ) -> Optional[HazardIntensity]:
        """Calculate water scarcity specific to power generation."""
        # Base water availability reduction
        base_reduction = scenario.severity_score * 0.3
        
        # Cooling system dependency
        if exposure.cooling_system_type == "once_through":
            base_reduction *= 1.5
        elif exposure.cooling_system_type == "dry_cooled":
            base_reduction *= 0.2
        
        # Water requirements impact
        if exposure.water_requirements_m3_per_hour > 15000:
            base_reduction *= 1.1
        
        # Cumulative effect over time
        time_factor = 1 + ((year - 2024) * 0.015)
        availability = max(0.2, 1.0 - (base_reduction * time_factor))
        
        if availability < 0.9:
            return HazardIntensity(
                hazard_type=HazardType.WATER_SCARCITY,
                intensity_value=availability,
                intensity_unit="availability_fraction",
                frequency=0.4,  # Water issues can be persistent
                duration_days=180.0,
            )
        
        return None
    
    def _load_damage_functions(self) -> Dict[Tuple[HazardType, str], DamageFunction]:
        """Load damage functions for different hazard-asset combinations."""
        functions = {}
        
        # Wildfire damage functions
        functions[(HazardType.WILDFIRE, "Coal")] = DamageFunction(
            hazard_type=HazardType.WILDFIRE,
            asset_type="Coal",
            intensity_threshold=0.2,
            damage_curve_params={
                "curve_type": "exponential",
                "k": 0.8,
            },
        )
        
        # Flood damage functions
        functions[(HazardType.FLOOD, "Coal")] = DamageFunction(
            hazard_type=HazardType.FLOOD,
            asset_type="Coal",
            intensity_threshold=0.1,  # 10cm water depth
            damage_curve_params={
                "curve_type": "logistic",
                "max_damage": 0.8,
                "steepness": 2.0,
                "inflection_point": 0.5,
            },
        )
        
        # Heat damage functions (mainly efficiency, not structural)
        functions[(HazardType.HEAT, "Coal")] = DamageFunction(
            hazard_type=HazardType.HEAT,
            asset_type="Coal",
            intensity_threshold=35.0,  # 35°C
            damage_curve_params={
                "curve_type": "linear",
                "slope": 0.02,  # 2% efficiency loss per °C above threshold
            },
        )
        
        # Drought damage functions (operational constraints)
        functions[(HazardType.DROUGHT, "Coal")] = DamageFunction(
            hazard_type=HazardType.DROUGHT,
            asset_type="Coal",
            intensity_threshold=0.3,
            damage_curve_params={
                "curve_type": "exponential",
                "k": 1.5,
            },
        )
        
        return functions


class VulnerabilityModel:
    """Asset vulnerability and damage assessment."""
    
    def __init__(self, hazard_model: HazardModel):
        self.hazard_model = hazard_model
        self.damage_functions = hazard_model.damage_functions
    
    def assess_vulnerability(
        self,
        exposure: AssetExposure,
        scenario: ScenarioParameters,
        year: int = 2024,
    ) -> PhysicalImpact:
        """
        Assess physical vulnerability and calculate impacts.
        
        Args:
            exposure: Asset exposure characteristics
            scenario: Climate risk scenario
            year: Assessment year
            
        Returns:
            Comprehensive physical impact assessment
        """
        # Calculate hazard intensities
        intensities = self.hazard_model.calculate_hazard_intensity(
            exposure, scenario, year
        )
        
        # Calculate damage for each hazard
        total_impact = PhysicalImpact(
            outage_probability=0.0,
            outage_duration_hours=0.0,
            capacity_derate_fraction=0.0,
            efficiency_loss_fraction=0.0,
            repair_cost_ratio=0.0,
            water_constraint_factor=1.0,
            cumulative_annual_impact_days=0.0,
        )
        
        for intensity in intensities:
            impact = self._calculate_hazard_impact(exposure, intensity)
            self._aggregate_impacts(total_impact, impact)
        
        # Apply mitigation effects
        total_impact = self._apply_mitigation_effects(exposure, total_impact)
        
        return total_impact
    
    def _calculate_hazard_impact(
        self, exposure: AssetExposure, intensity: HazardIntensity
    ) -> PhysicalImpact:
        """Calculate impact from a single hazard intensity."""
        # Get damage function
        damage_func = self.damage_functions.get(
            (intensity.hazard_type, exposure.plant.plant_type)
        )
        
        if not damage_func:
            # Default damage function if specific one not found
            damage_func = DamageFunction(
                hazard_type=intensity.hazard_type,
                asset_type=exposure.plant.plant_type,
                intensity_threshold=0.1,
                damage_curve_params={"curve_type": "linear", "slope": 0.1},
            )
        
        # Calculate damage ratio
        damage_ratio = damage_func.calculate_damage_ratio(intensity)
        
        # Get asset sensitivity
        sensitivity = exposure.get_hazard_sensitivity(intensity.hazard_type)
        
        # Adjust damage by sensitivity
        adjusted_damage = damage_ratio * sensitivity
        
        # Convert damage ratio to specific impacts based on hazard type
        if intensity.hazard_type == HazardType.WILDFIRE:
            return PhysicalImpact(
                outage_probability=adjusted_damage * 0.3,  # 30% chance of outage
                outage_duration_hours=adjusted_damage * 168,  # Up to 1 week
                capacity_derate_fraction=adjusted_damage * 0.1,  # 10% capacity loss
                efficiency_loss_fraction=0.0,
                repair_cost_ratio=adjusted_damage * 0.2,  # 20% of asset value
                water_constraint_factor=1.0,
                cumulative_annual_impact_days=adjusted_damage * 30,  # 30 days impact
                component_damages={"electrical_equipment": adjusted_damage * 0.5},
            )
        
        elif intensity.hazard_type == HazardType.FLOOD:
            return PhysicalImpact(
                outage_probability=adjusted_damage * 0.5,
                outage_duration_hours=adjusted_damage * 336,  # Up to 2 weeks
                capacity_derate_fraction=adjusted_damage * 0.2,
                efficiency_loss_fraction=0.0,
                repair_cost_ratio=adjusted_damage * 0.3,  # Flood damage expensive
                water_constraint_factor=1.0,
                cumulative_annual_impact_days=adjusted_damage * 60,
                component_damages={"turbine": adjusted_damage * 0.3, "electrical": adjusted_damage * 0.4},
            )
        
        elif intensity.hazard_type == HazardType.HEAT:
            return PhysicalImpact(
                outage_probability=adjusted_damage * 0.1,  # Less likely to cause outage
                outage_duration_hours=adjusted_damage * 24,  # Short outages
                capacity_derate_fraction=0.0,
                efficiency_loss_fraction=adjusted_damage * 0.5,  # Main impact is efficiency
                repair_cost_ratio=adjusted_damage * 0.05,  # Low repair costs
                water_constraint_factor=1.0,
                cumulative_annual_impact_days=adjusted_damage * 90,  # Long seasonal impact
                component_damages={"cooling_system": adjusted_damage * 0.6},
            )
        
        elif intensity.hazard_type == HazardType.DROUGHT:
            return PhysicalImpact(
                outage_probability=adjusted_damage * 0.2,
                outage_duration_hours=adjusted_damage * 72,  # Few days
                capacity_derate_fraction=adjusted_damage * 0.3,  # Capacity reduction
                efficiency_loss_fraction=adjusted_damage * 0.1,
                repair_cost_ratio=0.0,  # No physical damage
                water_constraint_factor=1 - adjusted_damage,  # Water constraint
                cumulative_annual_impact_days=adjusted_damage * 120,
                operational_restrictions=["water_use_limits"],
            )
        
        elif intensity.hazard_type == HazardType.WATER_SCARCITY:
            availability = intensity.intensity_value  # Water availability fraction
            return PhysicalImpact(
                outage_probability=0.0,
                outage_duration_hours=0.0,
                capacity_derate_fraction=1 - availability,  # Capacity limited by water
                efficiency_loss_fraction=0.0,
                repair_cost_ratio=0.0,
                water_constraint_factor=availability,
                cumulative_annual_impact_days=365 * (1 - availability),  # Year-round constraint
                operational_restrictions=["continuous_water_constraints"],
            )
        
        else:
            # Default impact
            return PhysicalImpact(
                outage_probability=adjusted_damage * 0.1,
                outage_duration_hours=adjusted_damage * 48,
                capacity_derate_fraction=adjusted_damage * 0.05,
                efficiency_loss_fraction=0.0,
                repair_cost_ratio=adjusted_damage * 0.1,
                water_constraint_factor=1.0,
                cumulative_annual_impact_days=adjusted_damage * 30,
            )
    
    def _aggregate_impacts(self, total: PhysicalImpact, additional: PhysicalImpact):
        """Aggregate multiple hazard impacts using appropriate methods."""
        # For probabilities, use union bound approximation
        total.outage_probability = min(
            1.0,
            total.outage_probability + additional.outage_probability
        )
        
        # For durations, use maximum
        total.outage_duration_hours = max(
            total.outage_duration_hours,
            additional.outage_duration_hours
        )
        
        # For capacity derating, use additive approach
        total.capacity_derate_fraction = min(
            1.0,
            total.capacity_derate_fraction + additional.capacity_derate_fraction
        )
        
        # For efficiency loss, use additive approach
        total.efficiency_loss_fraction = min(
            1.0,
            total.efficiency_loss_fraction + additional.efficiency_loss_fraction
        )
        
        # For repair costs, use additive approach
        total.repair_cost_ratio = min(
            1.0,
            total.repair_cost_ratio + additional.repair_cost_ratio
        )
        
        # For water constraints, use minimum (most restrictive)
        total.water_constraint_factor = min(
            total.water_constraint_factor,
            additional.water_constraint_factor
        )
        
        # For impact days, use additive approach
        total.cumulative_annual_impact_days += additional.cumulative_annual_impact_days
        
        # Merge component damages
        for component, damage in additional.component_damages.items():
            if component in total.component_damages:
                total.component_damages[component] = min(
                    1.0,
                    total.component_damages[component] + damage
                )
            else:
                total.component_damages[component] = damage
        
        # Merge operational restrictions
        total.operational_restrictions.extend(
            r for r in additional.operational_restrictions 
            if r not in total.operational_restrictions
        )
    
    def _apply_mitigation_effects(
        self, exposure: AssetExposure, impact: PhysicalImpact
    ) -> PhysicalImpact:
        """Apply mitigation measure effects to reduce impacts."""
        # Create a copy to modify
        mitigated_impact = PhysicalImpact(
            outage_probability=impact.outage_probability,
            outage_duration_hours=impact.outage_duration_hours,
            capacity_derate_fraction=impact.capacity_derate_fraction,
            efficiency_loss_fraction=impact.efficiency_loss_fraction,
            repair_cost_ratio=impact.repair_cost_ratio,
            water_constraint_factor=impact.water_constraint_factor,
            cumulative_annual_impact_days=impact.cumulative_annual_impact_days,
            component_damages=impact.component_damages.copy(),
            operational_restrictions=impact.operational_restrictions.copy(),
        )
        
        # Apply protection measure effects
        for protection in exposure.protection_measures:
            if protection == "flood_wall":
                mitigated_impact.repair_cost_ratio *= 0.5
                mitigated_impact.outage_probability *= 0.7
            elif protection == "firebreak":
                mitigated_impact.repair_cost_ratio *= 0.6
                mitigated_impact.outage_probability *= 0.8
            elif protection == "backup_cooling":
                mitigated_impact.capacity_derate_fraction *= 0.5
                mitigated_impact.water_constraint_factor = max(
                    mitigated_impact.water_constraint_factor,
                    0.8  # Minimum 80% availability with backup
                )
            elif protection == "heat_resistant_design":
                mitigated_impact.efficiency_loss_fraction *= 0.6
        
        return mitigated_impact


class EnhancedPhysicalRiskEngine:
    """
    Enhanced physical risk engine with modular architecture.
    
    Integrates hazard modeling, exposure analysis, and vulnerability assessment
    for comprehensive physical climate risk assessment of power generation assets.
    """
    
    def __init__(self):
        self.hazard_model = HazardModel()
        self.vulnerability_model = VulnerabilityModel(self.hazard_model)
    
    def assess_physical_risk(
        self,
        plant: PlantCharacteristics,
        exposure: AssetExposure,
        scenario: ScenarioParameters,
        year: int = 2024,
    ) -> PhysicalImpact:
        """
        Assess physical climate risk for a power generation asset.
        
        Args:
            plant: Plant characteristics
            exposure: Asset exposure characteristics
            scenario: Climate risk scenario
            year: Assessment year
            
        Returns:
            Comprehensive physical impact assessment
        """
        logger.info(
            f"Assessing physical risk for {plant.plant_type} plant at {plant.location} "
            f"under scenario '{scenario.name}' for year {year}"
        )
        
        # Validate inputs
        self._validate_assessment_inputs(plant, exposure, scenario)
        
        # Assess vulnerability
        impact = self.vulnerability_model.assess_vulnerability(exposure, scenario, year)
        
        logger.info(
            f"Physical risk assessment completed: "
            f"Outage prob: {impact.outage_probability:.1%}, "
            f"Capacity derate: {impact.capacity_derate_fraction:.1%}, "
            f"Impact days: {impact.cumulative_annual_impact_days:.0f}"
        )
        
        return impact
    
    def create_time_series_assessment(
        self,
        plant: PlantCharacteristics,
        exposure: AssetExposure,
        scenario: ScenarioParameters,
        start_year: int = 2024,
        end_year: int = 2060,
    ) -> Dict[int, PhysicalImpact]:
        """
        Create time series of physical risk assessments.
        
        Args:
            plant: Plant characteristics
            exposure: Asset exposure characteristics
            scenario: Climate risk scenario
            start_year: Start year for assessment
            end_year: End year for assessment
            
        Returns:
            Dictionary mapping year to physical impact assessment
        """
        time_series = {}
        
        for year in range(start_year, end_year + 1):
            impact = self.assess_physical_risk(plant, exposure, scenario, year)
            time_series[year] = impact
        
        return time_series
    
    def _validate_assessment_inputs(
        self,
        plant: PlantCharacteristics,
        exposure: AssetExposure,
        scenario: ScenarioParameters,
    ) -> None:
        """Validate inputs for physical risk assessment."""
        if plant.capacity_mw <= 0:
            raise ValueError("Plant capacity must be positive")
        
        if not -90 <= exposure.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90 degrees")
        
        if not -180 <= exposure.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180 degrees")
        
        if scenario.severity_score < 0 or scenario.severity_score > 1:
            raise ValueError("Scenario severity score must be between 0 and 1")


# Global engine instance
_enhanced_engine = EnhancedPhysicalRiskEngine()


def get_enhanced_physical_risk_engine() -> EnhancedPhysicalRiskEngine:
    """Get the global enhanced physical risk engine instance."""
    return _enhanced_engine
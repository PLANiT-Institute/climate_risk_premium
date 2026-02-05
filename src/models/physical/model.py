"""
Physical Risk Model.

Calculates financial impact of physical climate risks:
- Acute hazards: wildfire, tropical cyclone, flood, drought
- Chronic impacts: temperature efficiency loss, sea level rise, heat stress

All data from CLIMADA + literature sources.
See docs/sources/CLIMATE_SCENARIOS.md for methodology.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional, List

from src.models.base import BaseRiskModel, BaseDamageFunction, RiskType, RiskResult
from .hazards import (
    HazardType,
    HazardResult,
    HAZARD_BASELINES,
    get_climate_factor,
    get_climate_factor_set,
    calculate_projected_hazard,
)
from .climada_api import CLIMADAInterface, LocationQuery, KOREA_LOCATIONS
from .compound_risk import CompoundRiskModel, CompoundEventType
from .temperature import TemperatureModel


@dataclass
class PhysicalRiskComponents:
    """Breakdown of physical risk components."""
    # Acute hazards (event-driven)
    wildfire_outage: float          # Annual outage rate from wildfire
    tc_outage: float                # Annual outage rate from tropical cyclones
    river_flood_outage: float       # Annual outage rate from river flooding
    coastal_flood_outage: float     # Annual outage rate from coastal flooding
    drought_derate: float           # Capacity derate from drought
    acute_total: float              # Total acute impact
    # Chronic hazards (continuous)
    temp_efficiency_loss: float     # Efficiency loss from temperature
    heat_stress_loss: float         # Efficiency loss from heat stress
    slr_derate: float               # Capacity derate from SLR
    chronic_total: float            # Total chronic impact
    # Combined
    total_risk: float               # Combined physical risk (incl. compound)
    # Optional fields with defaults
    compound_adjustment: float = 0.0  # Additional risk from compound events
    confidence_low: float = 0.0       # 10th percentile
    confidence_high: float = 0.0      # 90th percentile


class PhysicalRiskModel(BaseRiskModel):
    """
    Physical Risk Model for power plants.

    Combines CLIMADA hazard data with literature-based damage functions
    to calculate physical climate risk impacts.

    Example:
        >>> model = PhysicalRiskModel()
        >>> model.set_rcp("RCP8.5")
        >>> model.set_location_by_name("samcheok")
        >>> result = model.calculate(year=2050)
    """

    def __init__(self, name: str = "PhysicalRiskModel"):
        super().__init__(name)
        self._rcp: str = "RCP8.5"
        self._location: LocationQuery = KOREA_LOCATIONS["samcheok"]
        self._temperature_model = TemperatureModel()
        self._active_damage_functions: Dict[HazardType, BaseDamageFunction] = {}
        self._climada_api = CLIMADAInterface()
        self._compound_model = CompoundRiskModel()
        self._include_compound: bool = True  # Include compound risk by default

    @property
    def risk_type(self) -> RiskType:
        return RiskType.PHYSICAL

    def set_rcp(self, rcp: str) -> None:
        """Set RCP scenario ("RCP4.5" or "RCP8.5")."""
        if rcp not in ["RCP4.5", "RCP8.5"]:
            raise ValueError(f"Unknown RCP: {rcp}. Use 'RCP4.5' or 'RCP8.5'")
        self._rcp = rcp
        self._temperature_model = TemperatureModel(rcp)

    def set_location(self, lat: float, lon: float, radius_km: float = 50.0, name: str = "") -> None:
        """Set location for hazard calculations."""
        self._location = LocationQuery(lat, lon, radius_km, name)

    def set_location_by_name(self, name: str) -> None:
        """
        Set location using a predefined Korean power plant name.

        Available: samcheok, dangjin, boryeong, hadong, taean
        """
        name_lower = name.lower()
        if name_lower not in KOREA_LOCATIONS:
            available = list(KOREA_LOCATIONS.keys())
            raise ValueError(f"Unknown location: {name}. Available: {available}")
        self._location = KOREA_LOCATIONS[name_lower]

    def get_location(self) -> LocationQuery:
        """Get current location."""
        return self._location

    def get_climada_summary(self) -> Dict[str, Any]:
        """Get summary of CLIMADA data for current location."""
        return self._climada_api.get_summary(self._location)

    def set_compound_risk(self, include: bool) -> None:
        """Enable or disable compound risk adjustments."""
        self._include_compound = include

    def get_compound_risks(self, year: int) -> Dict[str, Any]:
        """
        Get detailed compound risk information.

        Args:
            year: Target year

        Returns:
            Dict with compound event details
        """
        all_compounds = self._compound_model.calculate_all_compound_risks(year, self._rcp)
        adjustment = self._compound_model.get_total_compound_adjustment(year, self._rcp)

        return {
            "events": {
                event_type.value: {
                    "compound_impact": result.compound_impact,
                    "amplification": result.amplification_factor,
                    "base_impact": result.base_impact,
                }
                for event_type, result in all_compounds.items()
            },
            "total_adjustment": adjustment["compound_adjustment_factor"],
            "total_compound_impact": adjustment["total_compound_impact"],
        }

    def list_hazard_types(self) -> List[str]:
        """List available hazard types."""
        return [h.value for h in HazardType]

    def list_rcp_scenarios(self) -> List[str]:
        """List available RCP scenarios."""
        return ["RCP4.5", "RCP8.5"]

    def set_damage_function(self, hazard: HazardType, func: BaseDamageFunction) -> None:
        """Set damage function for a specific hazard type."""
        self._active_damage_functions[hazard] = func
        self.register_damage_function(func)

    def get_hazard_baseline(self, hazard: HazardType) -> HazardResult:
        """Get CLIMADA baseline data for a hazard type."""
        return HAZARD_BASELINES.get(hazard)

    def calculate_hazard_risk(
        self,
        hazard: HazardType,
        year: int,
    ) -> Dict[str, Any]:
        """
        Calculate risk for a single hazard type.

        Uses CLIMADA API for baseline data and applies climate change factors.

        Args:
            hazard: Type of hazard
            year: Target year

        Returns:
            Dict with projected values and confidence intervals
        """
        baseline = HAZARD_BASELINES.get(hazard)
        if not baseline:
            return {
                "base_rate": 0.0,
                "climate_factor": 1.0,
                "projected_rate": 0.0,
                "projected_derate": 0.0,
                "projected_efficiency_loss": 0.0,
                "confidence_low": 0.0,
                "confidence_high": 0.0,
                "source": "No data",
            }

        # Get climate factor for this hazard and year
        climate_factor = get_climate_factor(hazard, year, self._rcp)

        # Apply climate factor to all impact types
        projected_rate = baseline.outage_rate * climate_factor
        projected_derate = baseline.capacity_derate * climate_factor
        projected_efficiency_loss = baseline.efficiency_loss * climate_factor

        # Apply custom damage function if registered
        if hazard in self._active_damage_functions:
            func = self._active_damage_functions[hazard]
            projected_rate = func.calculate(
                intensity=baseline.base_intensity,
                year=year,
                climate_factor=climate_factor
            )

        # Scale confidence intervals with climate factor
        conf_low = baseline.confidence_low * climate_factor
        conf_high = baseline.confidence_high * climate_factor

        return {
            "base_rate": baseline.outage_rate,
            "base_derate": baseline.capacity_derate,
            "base_efficiency_loss": baseline.efficiency_loss,
            "climate_factor": climate_factor,
            "projected_rate": projected_rate,
            "projected_derate": projected_derate,
            "projected_efficiency_loss": projected_efficiency_loss,
            "confidence_low": conf_low,
            "confidence_high": conf_high,
            "source": baseline.source,
            "methodology": baseline.methodology,
        }

    def calculate_components(self, year: int) -> PhysicalRiskComponents:
        """
        Calculate detailed physical risk components.

        Includes all 7 hazard types with CLIMADA-based projections.

        Args:
            year: Target year

        Returns:
            PhysicalRiskComponents with full breakdown
        """
        # Get climate factors for this year
        climate_factors = get_climate_factor_set(year, self._rcp)

        # Acute hazards (event-driven)
        wildfire = self.calculate_hazard_risk(HazardType.WILDFIRE, year)
        tc = self.calculate_hazard_risk(HazardType.TROPICAL_CYCLONE, year)
        river_flood = self.calculate_hazard_risk(HazardType.RIVER_FLOOD, year)
        coastal_flood = self.calculate_hazard_risk(HazardType.COASTAL_FLOOD, year)
        drought = self.calculate_hazard_risk(HazardType.DROUGHT, year)

        # Sum acute impacts (outage rates + capacity derates)
        acute_total = (
            wildfire["projected_rate"] +
            tc["projected_rate"] +
            river_flood["projected_rate"] +
            coastal_flood["projected_rate"] +
            drought.get("projected_derate", 0.0)
        )

        # Chronic impacts (continuous)
        # Temperature efficiency loss from temperature model
        temp_result = self._temperature_model.calculate_efficiency_loss(year)
        temp_efficiency_loss = temp_result.total_derate

        # Heat stress additional impact
        heat_stress = self.calculate_hazard_risk(HazardType.HEAT_STRESS, year)
        heat_stress_loss = heat_stress.get("projected_efficiency_loss", 0.0)

        # SLR impact - affects coastal flood probability
        slr_baseline = HAZARD_BASELINES.get(HazardType.SEA_LEVEL_RISE)
        slr_derate = slr_baseline.capacity_derate if slr_baseline else 0.0

        chronic_total = temp_efficiency_loss + heat_stress_loss + slr_derate

        # Calculate compound risk adjustment
        compound_adjustment = 0.0
        if self._include_compound:
            try:
                compound_data = self._compound_model.get_total_compound_adjustment(year, self._rcp)
                # Compound adjustment is the additional risk from correlated events
                compound_adjustment = compound_data["compound_adjustment_factor"] * (acute_total + chronic_total)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    f"Compound risk calculation failed for year={year}, rcp={self._rcp}: {e}. "
                    f"Using compound_adjustment=0.0"
                )
                compound_adjustment = 0.0

        total_risk = acute_total + chronic_total + compound_adjustment

        # Calculate confidence intervals (sum of individual CI)
        conf_low = sum([
            wildfire.get("confidence_low", 0.0),
            tc.get("confidence_low", 0.0),
            river_flood.get("confidence_low", 0.0),
            coastal_flood.get("confidence_low", 0.0),
            drought.get("confidence_low", 0.0),
            heat_stress.get("confidence_low", 0.0),
        ])

        conf_high = sum([
            wildfire.get("confidence_high", 0.0),
            tc.get("confidence_high", 0.0),
            river_flood.get("confidence_high", 0.0),
            coastal_flood.get("confidence_high", 0.0),
            drought.get("confidence_high", 0.0),
            heat_stress.get("confidence_high", 0.0),
        ])

        return PhysicalRiskComponents(
            wildfire_outage=wildfire["projected_rate"],
            tc_outage=tc["projected_rate"],
            river_flood_outage=river_flood["projected_rate"],
            coastal_flood_outage=coastal_flood["projected_rate"],
            drought_derate=drought.get("projected_derate", 0.0),
            acute_total=acute_total,
            temp_efficiency_loss=temp_efficiency_loss,
            heat_stress_loss=heat_stress_loss,
            slr_derate=slr_derate,
            chronic_total=chronic_total,
            compound_adjustment=compound_adjustment,
            total_risk=total_risk,
            confidence_low=conf_low,
            confidence_high=conf_high,
        )

    def calculate(
        self,
        year: int,
        scenario_name: str = None,
        damage_function_name: Optional[str] = None,
        **kwargs
    ) -> RiskResult:
        """
        Calculate physical risk for a given year.

        Args:
            year: Target year
            scenario_name: RCP scenario (or use set_rcp)
            damage_function_name: Not directly used (set via set_damage_function)
            **kwargs: Additional parameters

        Returns:
            RiskResult with physical risk value
        """
        if scenario_name and scenario_name.upper() in ["RCP4.5", "RCP8.5"]:
            self.set_rcp(scenario_name.upper())

        components = self.calculate_components(year)

        # Collect all relevant sources
        sources = []
        for hazard in [HazardType.WILDFIRE, HazardType.TROPICAL_CYCLONE,
                       HazardType.RIVER_FLOOD, HazardType.DROUGHT]:
            baseline = HAZARD_BASELINES.get(hazard)
            if baseline:
                sources.append(baseline.source)
        sources.append(self._temperature_model.projections[2024].source)

        location_name = self._location.name if self._location.name else f"{self._location.latitude:.4f}, {self._location.longitude:.4f}"

        return RiskResult(
            risk_type=RiskType.PHYSICAL,
            value=components.total_risk,
            unit="fraction",
            year=year,
            scenario=self._rcp,
            components={
                # Acute hazards
                "wildfire_outage": components.wildfire_outage,
                "tc_outage": components.tc_outage,
                "river_flood_outage": components.river_flood_outage,
                "coastal_flood_outage": components.coastal_flood_outage,
                "drought_derate": components.drought_derate,
                "acute_total": components.acute_total,
                # Chronic hazards
                "temp_efficiency_loss": components.temp_efficiency_loss,
                "heat_stress_loss": components.heat_stress_loss,
                "slr_derate": components.slr_derate,
                "chronic_total": components.chronic_total,
                # Compound risk
                "compound_adjustment": components.compound_adjustment,
                # Confidence intervals
                "confidence_low": components.confidence_low,
                "confidence_high": components.confidence_high,
            },
            sources=sources,
            notes=f"Location: {location_name}, RCP: {self._rcp}",
        )

    def calculate_trajectory(
        self,
        start_year: int,
        end_year: int,
        scenario_name: str = None,
        **kwargs
    ) -> Dict[int, RiskResult]:
        """
        Calculate physical risk trajectory over time.

        Args:
            start_year: First year
            end_year: Last year
            scenario_name: RCP scenario
            **kwargs: Additional parameters

        Returns:
            Dict mapping year to RiskResult
        """
        if scenario_name:
            self.set_rcp(scenario_name.upper())

        return {
            year: self.calculate(year=year, **kwargs)
            for year in range(start_year, end_year + 1)
        }

    def get_summary_table(self, years: List[int] = None) -> Dict[int, Dict[str, float]]:
        """
        Get summary table of physical risks by year.

        Args:
            years: List of years (default: [2024, 2030, 2050, 2100])

        Returns:
            Dict mapping year to component values
        """
        if years is None:
            years = [2024, 2030, 2050, 2100]

        table = {}
        for year in years:
            components = self.calculate_components(year)
            table[year] = {
                # Acute hazards
                "wildfire": components.wildfire_outage,
                "tropical_cyclone": components.tc_outage,
                "river_flood": components.river_flood_outage,
                "coastal_flood": components.coastal_flood_outage,
                "drought": components.drought_derate,
                # Chronic hazards
                "temperature": components.temp_efficiency_loss,
                "heat_stress": components.heat_stress_loss,
                "slr": components.slr_derate,
                # Totals
                "total_acute": components.acute_total,
                "total_chronic": components.chronic_total,
                "total_risk": components.total_risk,
                # Confidence intervals
                "confidence_low": components.confidence_low,
                "confidence_high": components.confidence_high,
            }

        return table

    def get_hazard_detail(self, hazard: HazardType, year: int) -> Dict[str, Any]:
        """
        Get detailed information for a specific hazard.

        Args:
            hazard: Type of hazard
            year: Target year

        Returns:
            Dict with full hazard details
        """
        risk = self.calculate_hazard_risk(hazard, year)
        baseline = HAZARD_BASELINES.get(hazard)

        return {
            "hazard_type": hazard.value,
            "year": year,
            "rcp": self._rcp,
            "location": {
                "name": self._location.name,
                "latitude": self._location.latitude,
                "longitude": self._location.longitude,
            },
            "baseline": {
                "frequency": baseline.base_frequency if baseline else 0.0,
                "intensity": baseline.base_intensity if baseline else 0.0,
                "intensity_unit": baseline.intensity_unit if baseline else "",
            },
            "projected": {
                "climate_factor": risk["climate_factor"],
                "outage_rate": risk["projected_rate"],
                "capacity_derate": risk["projected_derate"],
                "efficiency_loss": risk["projected_efficiency_loss"],
            },
            "confidence": {
                "low": risk["confidence_low"],
                "high": risk["confidence_high"],
            },
            "source": risk["source"],
            "methodology": risk.get("methodology", ""),
        }

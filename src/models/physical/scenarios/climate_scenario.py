"""
Climate Scenario Base Classes.

Defines the interface for climate scenarios (RCP, SSP).
Data sources:
- CLIMADA climate scenarios
- IPCC AR6 pathways
- CMIP6 model outputs

See docs/sources/CLIMATE_SCENARIOS.md for full documentation.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import Enum

from src.models.base import BaseScenario


class ScenarioFamily(Enum):
    """Climate scenario family."""
    RCP = "RCP"    # Representative Concentration Pathways (CMIP5)
    SSP = "SSP"    # Shared Socioeconomic Pathways (CMIP6)


@dataclass
class ClimateProjection:
    """
    Climate projection data for a single year.

    Attributes:
        year: Target year
        global_temp_anomaly: Global mean temperature change (°C)
        regional_temp_anomaly: Regional (Korea) temperature change (°C)
        sea_level_rise: Global mean SLR (m)
        co2_concentration: Atmospheric CO2 (ppm)
    """
    year: int
    global_temp_anomaly: float
    regional_temp_anomaly: float
    sea_level_rise: float
    co2_concentration: float


class ClimateScenario(BaseScenario, ABC):
    """
    Abstract base class for climate scenarios.

    Climate scenarios define future climate pathways including
    temperature, sea level rise, and atmospheric conditions.
    """

    @property
    @abstractmethod
    def family(self) -> ScenarioFamily:
        """Scenario family (RCP or SSP)."""
        pass

    @property
    @abstractmethod
    def radiative_forcing(self) -> float:
        """Radiative forcing in 2100 (W/m²)."""
        pass

    @abstractmethod
    def get_projection(self, year: int) -> ClimateProjection:
        """Get full climate projection for a year."""
        pass

    def get_temperature(self, year: int) -> float:
        """Get regional temperature anomaly for a year."""
        return self.get_projection(year).regional_temp_anomaly

    def get_slr(self, year: int) -> float:
        """Get sea level rise for a year."""
        return self.get_projection(year).sea_level_rise


@dataclass
class RCPScenario(ClimateScenario):
    """
    Representative Concentration Pathway scenario.

    RCP scenarios from IPCC AR5/CMIP5.
    """
    _name: str
    _description: str
    _source: str
    _radiative_forcing: float
    projections: Dict[int, ClimateProjection] = field(default_factory=dict)

    @property
    def family(self) -> ScenarioFamily:
        return ScenarioFamily.RCP

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def source(self) -> str:
        return self._source

    @property
    def radiative_forcing(self) -> float:
        return self._radiative_forcing

    def get_value(self, year: int) -> float:
        """Get global temperature anomaly."""
        return self.get_projection(year).global_temp_anomaly

    def get_projection(self, year: int) -> ClimateProjection:
        """Get full climate projection for a year."""
        if year in self.projections:
            return self.projections[year]

        # Interpolate between known years
        years = sorted(self.projections.keys())
        if year <= years[0]:
            return self.projections[years[0]]
        if year >= years[-1]:
            return self.projections[years[-1]]

        # Linear interpolation
        for i, y in enumerate(years[:-1]):
            if years[i] <= year < years[i + 1]:
                y0, y1 = years[i], years[i + 1]
                p0, p1 = self.projections[y0], self.projections[y1]
                weight = (year - y0) / (y1 - y0)

                return ClimateProjection(
                    year=year,
                    global_temp_anomaly=p0.global_temp_anomaly + weight * (p1.global_temp_anomaly - p0.global_temp_anomaly),
                    regional_temp_anomaly=p0.regional_temp_anomaly + weight * (p1.regional_temp_anomaly - p0.regional_temp_anomaly),
                    sea_level_rise=p0.sea_level_rise + weight * (p1.sea_level_rise - p0.sea_level_rise),
                    co2_concentration=p0.co2_concentration + weight * (p1.co2_concentration - p0.co2_concentration),
                )

        return self.projections[years[-1]]


@dataclass
class SSPScenario(ClimateScenario):
    """
    Shared Socioeconomic Pathway scenario.

    SSP scenarios from IPCC AR6/CMIP6.
    """
    _name: str
    _description: str
    _source: str
    _radiative_forcing: float
    _ssp_number: int
    projections: Dict[int, ClimateProjection] = field(default_factory=dict)

    @property
    def family(self) -> ScenarioFamily:
        return ScenarioFamily.SSP

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def source(self) -> str:
        return self._source

    @property
    def radiative_forcing(self) -> float:
        return self._radiative_forcing

    @property
    def ssp_number(self) -> int:
        return self._ssp_number

    def get_value(self, year: int) -> float:
        """Get global temperature anomaly."""
        return self.get_projection(year).global_temp_anomaly

    def get_projection(self, year: int) -> ClimateProjection:
        """Get full climate projection for a year."""
        if year in self.projections:
            return self.projections[year]

        # Interpolate (same as RCPScenario)
        years = sorted(self.projections.keys())
        if year <= years[0]:
            return self.projections[years[0]]
        if year >= years[-1]:
            return self.projections[years[-1]]

        for i, y in enumerate(years[:-1]):
            if years[i] <= year < years[i + 1]:
                y0, y1 = years[i], years[i + 1]
                p0, p1 = self.projections[y0], self.projections[y1]
                weight = (year - y0) / (y1 - y0)

                return ClimateProjection(
                    year=year,
                    global_temp_anomaly=p0.global_temp_anomaly + weight * (p1.global_temp_anomaly - p0.global_temp_anomaly),
                    regional_temp_anomaly=p0.regional_temp_anomaly + weight * (p1.regional_temp_anomaly - p0.regional_temp_anomaly),
                    sea_level_rise=p0.sea_level_rise + weight * (p1.sea_level_rise - p0.sea_level_rise),
                    co2_concentration=p0.co2_concentration + weight * (p1.co2_concentration - p0.co2_concentration),
                )

        return self.projections[years[-1]]

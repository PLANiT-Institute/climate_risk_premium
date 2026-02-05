"""
Compound Risk Model.

Calculates multi-hazard interactions and compound event risks.
All configuration data loaded from CSV files.

Compound risks occur when:
1. Multiple hazards coincide temporally (e.g., drought + heat wave)
2. Sequential hazards amplify impacts (e.g., wildfire after drought)
3. Common drivers create correlated hazards (e.g., El Nino effects)

Literature References:
- Zscheischler et al. (2018) "Future climate risk from compound events"
- Raymond et al. (2020) "Understanding and managing connected extreme events"
- Seneviratne et al. (2021) IPCC AR6 Chapter 11 "Weather and Climate Extreme Events"
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import math

from src.data.loaders import (
    load_compound_events,
    load_hazard_baselines,
    get_climate_factor,
    CompoundEvent as CompoundEventData,
    HazardBaseline,
)
from .hazards import HazardType, HazardResult, HAZARD_BASELINES


class CompoundEventType(Enum):
    """Types of compound climate events."""
    # Temporal compounds (co-occurrence)
    DROUGHT_HEAT = "drought_heat"              # Drought + heat wave
    TC_FLOOD = "tc_flood"                      # Tropical cyclone + flooding
    HEAT_WILDFIRE = "heat_wildfire"            # Heat wave + wildfire
    SLR_SURGE = "slr_surge"                    # Sea level rise + storm surge

    # Sequential compounds
    DROUGHT_WILDFIRE = "drought_wildfire"      # Drought followed by wildfire
    FLOOD_LANDSLIDE = "flood_landslide"        # Heavy rain + landslide

    # Spatially compound
    MULTI_BASIN_FLOOD = "multi_basin_flood"    # Multiple river basins flooding


@dataclass
class CompoundEventConfig:
    """
    Configuration for compound event analysis.

    Attributes:
        event_type: Type of compound event
        hazard1: First hazard type
        hazard2: Second hazard type
        correlation: Correlation coefficient (-1 to 1)
        amplification: Impact amplification factor (>1 = amplified)
        joint_probability: P(H1 AND H2) / (P(H1) * P(H2))
        literature_source: Source citation
    """
    event_type: CompoundEventType
    hazard1: HazardType
    hazard2: HazardType
    correlation: float = 0.0
    amplification: float = 1.0
    joint_probability: float = 1.0
    literature_source: str = ""


def _load_compound_configs() -> Dict[CompoundEventType, CompoundEventConfig]:
    """Load compound event configurations from CSV."""
    csv_data = load_compound_events()
    configs = {}

    for event_type_str, data in csv_data.items():
        try:
            event_type = CompoundEventType(event_type_str)
            hazard1 = HazardType(data.hazard1)
            hazard2 = HazardType(data.hazard2)

            configs[event_type] = CompoundEventConfig(
                event_type=event_type,
                hazard1=hazard1,
                hazard2=hazard2,
                correlation=data.correlation,
                amplification=data.amplification,
                joint_probability=data.joint_probability,
                literature_source=data.source,
            )
        except (ValueError, KeyError):
            # Skip invalid entries
            continue

    return configs


# Lazy-loading compound events from CSV
class _CompoundEventsDict(dict):
    """Lazy-loading dict for compound events."""
    _loaded = False

    def _ensure_loaded(self):
        if not self._loaded:
            self.update(_load_compound_configs())
            self._loaded = True

    def get(self, key, default=None):
        self._ensure_loaded()
        return super().get(key, default)

    def __getitem__(self, key):
        self._ensure_loaded()
        return super().__getitem__(key)

    def keys(self):
        self._ensure_loaded()
        return super().keys()

    def values(self):
        self._ensure_loaded()
        return super().values()

    def items(self):
        self._ensure_loaded()
        return super().items()

    def __iter__(self):
        self._ensure_loaded()
        return super().__iter__()


COMPOUND_EVENTS = _CompoundEventsDict()


@dataclass
class CompoundRiskResult:
    """
    Result from compound risk analysis.

    Attributes:
        event_type: Type of compound event
        base_probability: Independent joint probability
        compound_probability: Actual joint probability (with correlation)
        base_impact: Sum of independent impacts
        compound_impact: Actual impact (with amplification)
        amplification_factor: Ratio of compound to base impact
        climate_factor: Climate change scaling
        confidence_low: 10th percentile
        confidence_high: 90th percentile
        sources: List of data sources
    """
    event_type: CompoundEventType
    base_probability: float
    compound_probability: float
    base_impact: float
    compound_impact: float
    amplification_factor: float
    climate_factor: float = 1.0
    confidence_low: float = 0.0
    confidence_high: float = 0.0
    sources: List[str] = field(default_factory=list)


class CompoundRiskModel:
    """
    Model for compound climate risk assessment.

    Calculates joint probabilities and amplified impacts
    from multi-hazard events.

    Example:
        >>> model = CompoundRiskModel()
        >>> result = model.calculate_compound_risk(
        ...     CompoundEventType.DROUGHT_HEAT,
        ...     year=2050,
        ...     rcp="RCP8.5"
        ... )
    """

    def __init__(self):
        # Force loading of compound configs
        self._compound_configs = dict(COMPOUND_EVENTS)

    def list_compound_events(self) -> List[str]:
        """List available compound event types."""
        return [e.value for e in CompoundEventType]

    def get_compound_config(self, event_type: CompoundEventType) -> CompoundEventConfig:
        """Get configuration for a compound event type."""
        return COMPOUND_EVENTS.get(event_type)

    def calculate_joint_probability(
        self,
        p1: float,
        p2: float,
        correlation: float,
    ) -> float:
        """
        Calculate joint probability with correlation.

        Uses Gaussian copula approximation for dependent events.

        Args:
            p1: Probability of hazard 1
            p2: Probability of hazard 2
            correlation: Correlation coefficient

        Returns:
            Joint probability P(H1 AND H2)
        """
        if correlation == 0:
            return p1 * p2

        # Gaussian copula approximation
        # For high correlation, joint probability increases
        independent = p1 * p2
        correlated = independent * (1 + correlation * min(p1, p2) / max(p1, p2, 1e-10))

        return min(correlated, min(p1, p2))  # Can't exceed individual probabilities

    def calculate_compound_impact(
        self,
        impact1: float,
        impact2: float,
        amplification: float,
        correlation: float,
    ) -> float:
        """
        Calculate compound impact with amplification.

        When hazards co-occur, impacts may be amplified beyond simple sum.

        Args:
            impact1: Impact of hazard 1 (fraction)
            impact2: Impact of hazard 2 (fraction)
            amplification: Amplification factor
            correlation: Correlation coefficient

        Returns:
            Compound impact (fraction)
        """
        # Base impact (independent sum)
        base_impact = impact1 + impact2

        # Correlated amplification
        # Higher correlation = higher amplification effect
        effective_amp = 1.0 + (amplification - 1.0) * abs(correlation)

        compound_impact = base_impact * effective_amp

        # Cap at 1.0 (100% impact)
        return min(compound_impact, 1.0)

    def calculate_compound_risk(
        self,
        event_type: CompoundEventType,
        year: int,
        rcp: str = "RCP8.5",
    ) -> CompoundRiskResult:
        """
        Calculate compound risk for a specific event type.

        Args:
            event_type: Type of compound event
            year: Target year
            rcp: RCP scenario

        Returns:
            CompoundRiskResult with probabilities and impacts
        """
        config = COMPOUND_EVENTS.get(event_type)
        if not config:
            raise ValueError(f"Unknown compound event: {event_type}")

        # Get baseline hazard data
        h1 = HAZARD_BASELINES.get(config.hazard1)
        h2 = HAZARD_BASELINES.get(config.hazard2)

        if not h1 or not h2:
            raise ValueError(f"Missing baseline data for {config.hazard1} or {config.hazard2}")

        # Get climate factors
        cf1 = get_climate_factor(config.hazard1.value, year, rcp)
        cf2 = get_climate_factor(config.hazard2.value, year, rcp)
        avg_climate_factor = (cf1 + cf2) / 2

        # Calculate probabilities
        p1 = h1.base_frequency * cf1  # Annual probability of hazard 1
        p2 = h2.base_frequency * cf2  # Annual probability of hazard 2

        base_prob = p1 * p2
        compound_prob = self.calculate_joint_probability(p1, p2, config.correlation)

        # Calculate impacts
        impact1 = h1.total_annual_impact * cf1
        impact2 = h2.total_annual_impact * cf2

        base_impact = impact1 + impact2
        compound_impact = self.calculate_compound_impact(
            impact1, impact2, config.amplification, config.correlation
        )

        amplification = compound_impact / base_impact if base_impact > 0 else 1.0

        # Confidence intervals (wider for compounds due to uncertainty)
        uncertainty_factor = 1.5  # Compound events have higher uncertainty
        conf_low = compound_impact * (1 - 0.3 * uncertainty_factor)
        conf_high = compound_impact * (1 + 0.5 * uncertainty_factor)

        return CompoundRiskResult(
            event_type=event_type,
            base_probability=base_prob,
            compound_probability=compound_prob,
            base_impact=base_impact,
            compound_impact=compound_impact,
            amplification_factor=amplification,
            climate_factor=avg_climate_factor,
            confidence_low=max(0, conf_low),
            confidence_high=min(1, conf_high),
            sources=[h1.source, h2.source, config.literature_source],
        )

    def calculate_all_compound_risks(
        self,
        year: int,
        rcp: str = "RCP8.5",
    ) -> Dict[CompoundEventType, CompoundRiskResult]:
        """
        Calculate all compound risks for a given year.

        Args:
            year: Target year
            rcp: RCP scenario

        Returns:
            Dict mapping event type to result
        """
        results = {}
        for event_type in CompoundEventType:
            try:
                results[event_type] = self.calculate_compound_risk(event_type, year, rcp)
            except ValueError:
                continue  # Skip if data unavailable

        return results

    def get_total_compound_adjustment(
        self,
        year: int,
        rcp: str = "RCP8.5",
    ) -> Dict[str, float]:
        """
        Calculate total adjustment factor from all compound events.

        Returns adjustment to apply to simple hazard sum.

        Args:
            year: Target year
            rcp: RCP scenario

        Returns:
            Dict with adjustment factor and components
        """
        all_results = self.calculate_all_compound_risks(year, rcp)

        total_base = 0.0
        total_compound = 0.0

        for result in all_results.values():
            total_base += result.base_impact
            total_compound += result.compound_impact

        # Adjustment factor: how much compound effects add
        if total_base > 0:
            adjustment = (total_compound - total_base) / total_base
        else:
            adjustment = 0.0

        return {
            "compound_adjustment_factor": adjustment,
            "total_base_impact": total_base,
            "total_compound_impact": total_compound,
            "num_compound_events": len(all_results),
        }

    def get_summary_table(self, years: List[int] = None, rcp: str = "RCP8.5") -> Dict[int, Dict]:
        """
        Get summary table of compound risks by year.

        Args:
            years: List of years
            rcp: RCP scenario

        Returns:
            Dict mapping year to compound risk summary
        """
        if years is None:
            years = [2024, 2030, 2050, 2100]

        table = {}
        for year in years:
            results = self.calculate_all_compound_risks(year, rcp)
            adjustment = self.get_total_compound_adjustment(year, rcp)

            table[year] = {
                "compound_events": {
                    event_type.value: {
                        "compound_impact": result.compound_impact,
                        "amplification": result.amplification_factor,
                    }
                    for event_type, result in results.items()
                },
                "adjustment_factor": adjustment["compound_adjustment_factor"],
                "total_compound_impact": adjustment["total_compound_impact"],
            }

        return table


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def calculate_portfolio_compound_risk(
    hazard_exposures: Dict[HazardType, float],
    year: int,
    rcp: str = "RCP8.5",
) -> Dict[str, Any]:
    """
    Calculate compound risk for a portfolio of hazard exposures.

    Args:
        hazard_exposures: Dict mapping hazard type to exposure fraction
        year: Target year
        rcp: RCP scenario

    Returns:
        Dict with portfolio compound risk metrics
    """
    model = CompoundRiskModel()

    # Find relevant compound events
    relevant_compounds = []
    for event_type, config in COMPOUND_EVENTS.items():
        if config.hazard1 in hazard_exposures and config.hazard2 in hazard_exposures:
            relevant_compounds.append(event_type)

    # Calculate compound risks
    total_compound_impact = 0.0
    compound_details = []

    for event_type in relevant_compounds:
        try:
            result = model.calculate_compound_risk(event_type, year, rcp)
            config = COMPOUND_EVENTS[event_type]

            # Weight by exposures
            weight1 = hazard_exposures.get(config.hazard1, 0.0)
            weight2 = hazard_exposures.get(config.hazard2, 0.0)
            weighted_impact = result.compound_impact * weight1 * weight2

            total_compound_impact += weighted_impact

            compound_details.append({
                "event_type": event_type.value,
                "weighted_impact": weighted_impact,
                "amplification": result.amplification_factor,
            })
        except ValueError:
            continue

    return {
        "total_compound_impact": total_compound_impact,
        "compound_events": compound_details,
        "num_events": len(compound_details),
        "year": year,
        "rcp": rcp,
    }

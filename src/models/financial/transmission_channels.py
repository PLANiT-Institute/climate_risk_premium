"""
NGFS/Basel Transmission Channel Framework.

Implements the transmission channels through which physical climate
risks translate to financial risks, following:
- NGFS (2020) "Overview of Environmental Risk Analysis"
- Basel Committee (2021) "Climate-related financial risks"
- FSB (2020) "The Implications of Climate Change for Financial Stability"

Transmission channels:
1. Direct physical damage to assets
2. Business interruption
3. Supply chain disruption
4. Market/price changes
5. Regulatory response
6. Litigation
7. Insurance repricing
8. Credit contagion
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class TransmissionChannel(Enum):
    """
    NGFS/Basel physical risk transmission channels.

    Categories:
    - DIRECT: Immediate physical impacts
    - INDIRECT: Secondary economic effects
    - SYSTEMIC: Financial system effects
    """
    # Direct channels
    ASSET_DAMAGE = "asset_damage"
    BUSINESS_INTERRUPTION = "business_interruption"
    SUPPLY_CHAIN = "supply_chain_disruption"
    INFRASTRUCTURE = "infrastructure_damage"

    # Indirect channels
    MARKET_PRICE = "market_price_change"
    DEMAND_SHIFT = "demand_pattern_shift"
    PRODUCTIVITY = "productivity_loss"
    REGULATORY = "regulatory_response"
    LITIGATION = "litigation_risk"

    # Systemic channels
    CREDIT_CONTAGION = "credit_contagion"
    INSURANCE_REPRICING = "insurance_repricing"
    STRANDED_ASSETS = "stranded_assets"
    MARKET_LIQUIDITY = "market_liquidity"


class ImpactType(Enum):
    """Type of financial impact."""
    REVENUE = "revenue"
    COST = "cost"
    ASSET_VALUE = "asset_value"
    CREDIT = "credit"
    LIQUIDITY = "liquidity"
    OPERATIONAL = "operational"


class Reversibility(Enum):
    """Reversibility of impact."""
    PERMANENT = "permanent"        # Stranded assets, destroyed infrastructure
    LONG_TERM = "long_term"        # Multi-year recovery
    MEDIUM_TERM = "medium_term"    # 1-3 year recovery
    SHORT_TERM = "short_term"      # < 1 year recovery
    TEMPORARY = "temporary"        # Days to weeks


@dataclass
class ChannelImpact:
    """
    Impact through a specific transmission channel.

    Quantifies how physical risk translates to financial impact
    through each channel.
    """
    channel: TransmissionChannel
    impact_type: ImpactType
    probability: float               # Probability of impact (0-1)
    severity_usd: float              # Monetary impact if occurs
    severity_pct: float              # As % of relevant base
    time_to_materialize_years: float # When impact hits
    duration_years: float            # How long impact lasts
    reversibility: Reversibility
    confidence: float = 0.7          # Confidence in estimate

    @property
    def expected_impact(self) -> float:
        """Expected value of impact."""
        return self.probability * self.severity_usd

    @property
    def annualized_impact(self) -> float:
        """Annualized expected impact."""
        if self.duration_years > 0:
            return self.expected_impact / self.duration_years
        return self.expected_impact


@dataclass
class TransmissionResult:
    """
    Complete transmission analysis result.
    """
    asset_id: str
    scenario: str
    year: int

    # Channel impacts
    channel_impacts: Dict[TransmissionChannel, ChannelImpact]

    # Aggregates by type
    total_revenue_impact: float = 0.0
    total_cost_impact: float = 0.0
    total_asset_impact: float = 0.0
    total_credit_impact: float = 0.0

    # Grand total
    total_impact_usd: float = 0.0
    total_impact_pct: float = 0.0

    def __post_init__(self):
        """Calculate aggregates."""
        for impact in self.channel_impacts.values():
            if impact.impact_type == ImpactType.REVENUE:
                self.total_revenue_impact += impact.expected_impact
            elif impact.impact_type == ImpactType.COST:
                self.total_cost_impact += impact.expected_impact
            elif impact.impact_type == ImpactType.ASSET_VALUE:
                self.total_asset_impact += impact.expected_impact
            elif impact.impact_type == ImpactType.CREDIT:
                self.total_credit_impact += impact.expected_impact

        self.total_impact_usd = (
            self.total_revenue_impact +
            self.total_cost_impact +
            self.total_asset_impact +
            self.total_credit_impact
        )


class TransmissionModel:
    """
    NGFS/Basel transmission channel model.

    Maps physical risk to financial impacts through transmission channels.
    """

    # Channel weights by sector (power generation)
    CHANNEL_WEIGHTS = {
        TransmissionChannel.ASSET_DAMAGE: 0.25,
        TransmissionChannel.BUSINESS_INTERRUPTION: 0.20,
        TransmissionChannel.SUPPLY_CHAIN: 0.10,
        TransmissionChannel.MARKET_PRICE: 0.15,
        TransmissionChannel.REGULATORY: 0.10,
        TransmissionChannel.INSURANCE_REPRICING: 0.10,
        TransmissionChannel.STRANDED_ASSETS: 0.10,
    }

    # Impact parameters by channel
    CHANNEL_PARAMETERS = {
        TransmissionChannel.ASSET_DAMAGE: {
            "impact_type": ImpactType.ASSET_VALUE,
            "reversibility": Reversibility.LONG_TERM,
            "base_probability": 0.05,
            "damage_ratio": 0.15,
            "time_to_materialize": 0.0,
            "duration": 10.0,
        },
        TransmissionChannel.BUSINESS_INTERRUPTION: {
            "impact_type": ImpactType.REVENUE,
            "reversibility": Reversibility.SHORT_TERM,
            "base_probability": 0.10,
            "damage_ratio": 0.05,
            "time_to_materialize": 0.0,
            "duration": 0.5,
        },
        TransmissionChannel.SUPPLY_CHAIN: {
            "impact_type": ImpactType.COST,
            "reversibility": Reversibility.MEDIUM_TERM,
            "base_probability": 0.08,
            "damage_ratio": 0.03,
            "time_to_materialize": 0.25,
            "duration": 1.0,
        },
        TransmissionChannel.MARKET_PRICE: {
            "impact_type": ImpactType.REVENUE,
            "reversibility": Reversibility.MEDIUM_TERM,
            "base_probability": 0.30,
            "damage_ratio": 0.02,
            "time_to_materialize": 0.5,
            "duration": 3.0,
        },
        TransmissionChannel.REGULATORY: {
            "impact_type": ImpactType.COST,
            "reversibility": Reversibility.LONG_TERM,
            "base_probability": 0.20,
            "damage_ratio": 0.05,
            "time_to_materialize": 2.0,
            "duration": 10.0,
        },
        TransmissionChannel.INSURANCE_REPRICING: {
            "impact_type": ImpactType.COST,
            "reversibility": Reversibility.MEDIUM_TERM,
            "base_probability": 0.40,
            "damage_ratio": 0.01,
            "time_to_materialize": 1.0,
            "duration": 5.0,
        },
        TransmissionChannel.STRANDED_ASSETS: {
            "impact_type": ImpactType.ASSET_VALUE,
            "reversibility": Reversibility.PERMANENT,
            "base_probability": 0.15,
            "damage_ratio": 0.30,
            "time_to_materialize": 5.0,
            "duration": 20.0,
        },
    }

    def __init__(self, scenario: str = "RCP8.5"):
        self.scenario = scenario

    def analyze(
        self,
        asset_id: str,
        replacement_cost_usd: float,
        annual_revenue_usd: float,
        annual_opex_usd: float,
        physical_risk_pct: float,
        year: int,
    ) -> TransmissionResult:
        """
        Analyze transmission of physical risk to financial impacts.

        Args:
            asset_id: Asset identifier
            replacement_cost_usd: Asset replacement cost
            annual_revenue_usd: Annual revenue
            annual_opex_usd: Annual operating expenses
            physical_risk_pct: Physical risk (% CF reduction)
            year: Target year

        Returns:
            TransmissionResult with channel breakdown
        """
        channel_impacts = {}

        for channel, params in self.CHANNEL_PARAMETERS.items():
            impact_type = params["impact_type"]

            # Determine base value for impact calculation
            if impact_type == ImpactType.ASSET_VALUE:
                base_value = replacement_cost_usd
            elif impact_type == ImpactType.REVENUE:
                base_value = annual_revenue_usd
            elif impact_type == ImpactType.COST:
                base_value = annual_opex_usd
            else:
                base_value = replacement_cost_usd

            # Scale probability and severity with physical risk
            probability = params["base_probability"] * (1 + physical_risk_pct / 100)
            probability = min(0.95, probability)

            damage_ratio = params["damage_ratio"] * (1 + physical_risk_pct / 100)
            severity_usd = base_value * damage_ratio

            channel_impacts[channel] = ChannelImpact(
                channel=channel,
                impact_type=impact_type,
                probability=probability,
                severity_usd=severity_usd,
                severity_pct=damage_ratio * 100,
                time_to_materialize_years=params["time_to_materialize"],
                duration_years=params["duration"],
                reversibility=params["reversibility"],
            )

        return TransmissionResult(
            asset_id=asset_id,
            scenario=self.scenario,
            year=year,
            channel_impacts=channel_impacts,
        )

    def get_channel_summary(self, result: TransmissionResult) -> Dict[str, Dict]:
        """Get summary by transmission channel."""
        summary = {}
        for channel, impact in result.channel_impacts.items():
            summary[channel.value] = {
                "expected_impact_usd": impact.expected_impact,
                "probability": impact.probability,
                "severity_usd": impact.severity_usd,
                "reversibility": impact.reversibility.value,
            }
        return summary

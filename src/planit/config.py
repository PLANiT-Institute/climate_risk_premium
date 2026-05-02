"""PLANiT integration configuration."""
from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import List, Optional


@dataclass
class EfficiencyChannelConfig:
    """Configuration for ambient-temperature thermal-efficiency derating."""

    enabled: bool = False


@dataclass
class PLANiTIntegrationConfig:
    """Configuration for PLANiT → CRP pipeline integration.

    Attributes:
        planit_config_path: Path to PLANiT's unified_config.yaml
        planit_results_dir: Path to pre-computed PLANiT result CSVs
        target_asset: Korean name of the target asset in PLANiT results
        cache_dir: Directory for cached PLANiT results
        cache_ttl_hours: Cache time-to-live in hours
        enabled: Whether PLANiT integration is active
        planit_hazards: Hazard types sourced from PLANiT (wildfire, drought, water_risk)
        efficiency_channel: Explicit switch for ambient-temperature derating.
            Disabled until site-level daily temperature series and SSP
            projections are available.
        csv_fallback_hazards: Hazard types that always fall back to CSV
        anchor_years: PLANiT projection years used as interpolation anchors
        drought_severity_scale: Scaling factor for drought impact_mean → capacity_derate
        heat_efficiency_scale: Scaling factor for heatwave impact_mean → efficiency_loss
        flood_outage_scale: Scaling factor for flood impact_mean → outage_rate
        wildfire_outage_method: Wildfire outage conversion method
            ("event_probability")
        wildfire_outage_probability: Conditional probability that a wildfire
            event causes generation outage (0-1)
        wildfire_outage_duration_hours: Expected outage duration (hours) when
            outage occurs
        hours_per_year: Hours used to convert expected outage hours to outage rate
        wildfire_frequency_reference_years: Reference years for inferring
            annual event frequency from event_count when frequency is missing
        drought_use_distribution: Use PhysRisk impact distribution (if available)
            instead of raw impact_mean
        water_risk_use_distribution: Use PhysRisk impact distribution (if available)
            instead of raw impact_mean
    """
    planit_config_path: str = "Physicalrisk_PLANiT/config/unified_config.yaml"
    planit_results_dir: str = "Physicalrisk_PLANiT/data/results"
    target_asset: str = "삼척화력발전소"
    cache_dir: str = "data/cache/planit"
    cache_ttl_hours: float = 24.0
    enabled: bool = True
    planit_hazards: List[str] = field(
        default_factory=lambda: ["wildfire", "drought", "water_risk"]
    )
    efficiency_channel: EfficiencyChannelConfig = field(
        default_factory=EfficiencyChannelConfig
    )
    csv_fallback_hazards: List[str] = field(
        default_factory=lambda: []
    )
    anchor_years: List[int] = field(
        default_factory=lambda: [2030, 2040, 2050, 2060]
    )
    # Conversion scaling factors
    drought_severity_scale: float = 1.0
    heat_efficiency_scale: float = 1.0
    flood_outage_scale: float = 1.0
    # Wildfire conversion settings
    wildfire_outage_method: str = "event_probability"
    wildfire_outage_probability: float = 0.10
    wildfire_outage_duration_hours: float = 24.0
    hours_per_year: float = 8760.0
    wildfire_frequency_reference_years: float = 20.0
    drought_use_distribution: bool = True
    water_risk_use_distribution: bool = True

    def __post_init__(self) -> None:
        """Apply optional environment variable overrides."""
        raw = os.getenv("CRP_WILDFIRE_OUTAGE_METHOD", "").strip().lower()
        if raw in {"event_probability"}:
            self.wildfire_outage_method = raw

        raw = os.getenv("CRP_WILDFIRE_OUTAGE_PROBABILITY", "").strip()
        if raw:
            self.wildfire_outage_probability = min(1.0, max(0.0, float(raw)))

        raw = os.getenv("CRP_WILDFIRE_OUTAGE_DURATION_HOURS", "").strip()
        if raw:
            self.wildfire_outage_duration_hours = max(0.0, float(raw))

        raw = os.getenv("CRP_WILDFIRE_HOURS_PER_YEAR", "").strip()
        if raw:
            self.hours_per_year = max(1.0, float(raw))

    def get_planit_config_path(self, base_dir: Optional[str] = None) -> Path:
        """Resolve absolute path to PLANiT config."""
        p = Path(self.planit_config_path)
        if p.is_absolute():
            return p
        if base_dir:
            return Path(base_dir) / p
        return p

    def get_results_dir(self, base_dir: Optional[str] = None) -> Path:
        """Resolve absolute path to PLANiT results directory."""
        p = Path(self.planit_results_dir)
        if p.is_absolute():
            return p
        if base_dir:
            return Path(base_dir) / p
        return p

    def get_cache_dir(self, base_dir: Optional[str] = None) -> Path:
        """Resolve absolute path to cache directory."""
        p = Path(self.cache_dir)
        if p.is_absolute():
            return p
        if base_dir:
            return Path(base_dir) / p
        return p

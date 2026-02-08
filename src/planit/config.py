"""PLANiT integration configuration."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class PLANiTIntegrationConfig:
    """Configuration for PLANiT → CRP pipeline integration.

    Attributes:
        planit_config_path: Path to PLANiT's unified_config.yaml
        planit_results_dir: Path to pre-computed PLANiT result CSVs
        target_asset: Korean name of the target asset in PLANiT results
        total_asset_value_krw: Total asset value in KRW (for AAI → rate conversion)
        cache_dir: Directory for cached PLANiT results
        cache_ttl_hours: Cache time-to-live in hours
        enabled: Whether PLANiT integration is active
        planit_hazards: Hazard types sourced from PLANiT (wildfire, drought, water_risk)
        csv_fallback_hazards: Hazard types that always fall back to CSV
        anchor_years: PLANiT projection years used as interpolation anchors
        drought_severity_scale: Scaling factor for drought impact_mean → capacity_derate
        heat_efficiency_scale: Scaling factor for heatwave impact_mean → efficiency_loss
        flood_outage_scale: Scaling factor for flood impact_mean → outage_rate
    """
    planit_config_path: str = "Physicalrisk_PLANiT/config/unified_config.yaml"
    planit_results_dir: str = "Physicalrisk_PLANiT/data/results"
    target_asset: str = "삼척화력발전소"
    total_asset_value_krw: float = 4.879e12
    cache_dir: str = "data/cache/planit"
    cache_ttl_hours: float = 24.0
    enabled: bool = True
    planit_hazards: List[str] = field(
        default_factory=lambda: ["wildfire", "drought", "water_risk"]
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

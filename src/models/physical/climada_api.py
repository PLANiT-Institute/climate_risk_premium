"""
CLIMADA API Integration Layer.

Provides interface to CLIMADA hazard data for physical risk modeling.
Supports both API calls (when CLIMADA is installed) and cached data.

CLIMADA (CLIMate ADAptation) is developed by ETH Zurich.
Documentation: https://climada-python.readthedocs.io/

Data Sources:
- IBTrACS: International Best Track Archive for Climate Stewardship (TC)
- ERA5: ECMWF Reanalysis v5 (wildfire, temperature)
- ISIMIP: Inter-Sectoral Impact Model Intercomparison Project (flood)
- KMA: Korea Meteorological Administration (local calibration)
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import logging

from .hazards import (
    HazardType,
    HazardResult,
    HazardParameters,
    HAZARD_BASELINES,
    HAZARD_PARAMETERS,
    get_climate_factor,
)

logger = logging.getLogger(__name__)


class CLIMADASource(Enum):
    """CLIMADA data sources for different hazard types."""
    IBTRACS = "IBTrACS"           # Tropical cyclones
    ERA5 = "ERA5"                 # Wildfire, temperature
    ISIMIP = "ISIMIP"             # River floods
    GTSR = "GTSR"                 # Coastal floods (Global Tide and Surge Reanalysis)
    SPEI = "SPEI"                 # Drought index
    NASADEM = "NASADEM"           # Elevation for exposure


@dataclass
class LocationQuery:
    """
    Geographic query for hazard data.

    Attributes:
        latitude: Decimal degrees north
        longitude: Decimal degrees east
        radius_km: Search radius in kilometers
        name: Location name (for labeling)
    """
    latitude: float
    longitude: float
    radius_km: float = 50.0
    name: str = ""

    def to_bounds(self) -> Tuple[float, float, float, float]:
        """Convert to bounding box (min_lon, min_lat, max_lon, max_lat)."""
        # Approximate degrees per km at this latitude
        lat_deg_per_km = 1 / 111.0
        lon_deg_per_km = 1 / (111.0 * math.cos(math.radians(self.latitude)))

        dlat = self.radius_km * lat_deg_per_km
        dlon = self.radius_km * lon_deg_per_km

        return (
            self.longitude - dlon,
            self.latitude - dlat,
            self.longitude + dlon,
            self.latitude + dlat,
        )


@dataclass
class HazardDataset:
    """
    CLIMADA hazard dataset for a specific location and hazard type.

    Attributes:
        hazard_type: Type of hazard
        location: Geographic query
        start_year: First year of data
        end_year: Last year of data
        events: List of historical events
        frequency: Annual event frequency
        intensity_mean: Mean intensity of events
        intensity_p90: 90th percentile intensity
        intensity_unit: Unit of intensity
        source: Data source citation
        last_updated: Last data update timestamp
    """
    hazard_type: HazardType
    location: LocationQuery
    start_year: int
    end_year: int
    events: List[Dict[str, Any]] = field(default_factory=list)
    frequency: float = 0.0
    intensity_mean: float = 0.0
    intensity_p90: float = 0.0
    intensity_unit: str = ""
    source: str = ""
    last_updated: str = ""

    @property
    def num_years(self) -> int:
        return self.end_year - self.start_year + 1

    @property
    def num_events(self) -> int:
        return len(self.events)

    def calculate_frequency(self) -> float:
        """Calculate annual frequency from events."""
        if self.num_years > 0:
            return self.num_events / self.num_years
        return 0.0


@dataclass
class CLIMADAConfig:
    """
    Configuration for CLIMADA API.

    Attributes:
        cache_dir: Directory for cached data
        use_cache: Whether to use cached data
        cache_expiry_days: Days before cache expires
        api_timeout: Timeout for API calls (seconds)
        default_radius_km: Default search radius
    """
    cache_dir: Path = field(default_factory=lambda: Path("data/climada_cache"))
    use_cache: bool = True
    cache_expiry_days: int = 30
    api_timeout: int = 60
    default_radius_km: float = 50.0


class CLIMADAInterface:
    """
    Interface to CLIMADA hazard data.

    Provides a unified API for fetching hazard data from CLIMADA
    with local caching and fallback to literature-based values.

    Example:
        >>> api = CLIMADAInterface()
        >>> data = api.get_hazard_data(
        ...     HazardType.TROPICAL_CYCLONE,
        ...     LocationQuery(37.4404, 129.1671, name="Samcheok")
        ... )
        >>> print(f"TC frequency: {data.frequency:.2f}/year")
    """

    # CLIMADA availability flag
    _climada_available: Optional[bool] = None

    # Hazard type to CLIMADA class mapping
    HAZARD_CLASS_MAP = {
        HazardType.WILDFIRE: "WildFire",
        HazardType.TROPICAL_CYCLONE: "TropCyclone",
        HazardType.RIVER_FLOOD: "RiverFlood",
        HazardType.COASTAL_FLOOD: "CoastalFlood",
        HazardType.DROUGHT: "Drought",
        HazardType.HEAT_STRESS: "HeatWave",
        HazardType.SEA_LEVEL_RISE: "RelativeSLR",
    }

    # Source mapping for hazard types
    SOURCE_MAP = {
        HazardType.WILDFIRE: CLIMADASource.ERA5,
        HazardType.TROPICAL_CYCLONE: CLIMADASource.IBTRACS,
        HazardType.RIVER_FLOOD: CLIMADASource.ISIMIP,
        HazardType.COASTAL_FLOOD: CLIMADASource.GTSR,
        HazardType.DROUGHT: CLIMADASource.SPEI,
        HazardType.HEAT_STRESS: CLIMADASource.ERA5,
        HazardType.SEA_LEVEL_RISE: CLIMADASource.GTSR,
    }

    def __init__(self, config: CLIMADAConfig = None):
        """Initialize CLIMADA interface with optional config."""
        self.config = config or CLIMADAConfig()
        self._ensure_cache_dir()
        self._datasets: Dict[str, HazardDataset] = {}

    def _ensure_cache_dir(self) -> None:
        """Ensure cache directory exists."""
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def is_climada_available(cls) -> bool:
        """Check if CLIMADA library is installed and available."""
        if cls._climada_available is not None:
            return cls._climada_available

        try:
            import climada
            cls._climada_available = True
            version = getattr(climada, '__version__', 'unknown')
            logger.info(f"CLIMADA {version} available")
        except ImportError:
            cls._climada_available = False
            logger.info("CLIMADA not installed - using cached/literature data")

        return cls._climada_available

    def _get_cache_key(self, hazard: HazardType, location: LocationQuery) -> str:
        """Generate cache key for a hazard/location combination."""
        return f"{hazard.value}_{location.latitude:.4f}_{location.longitude:.4f}_{location.radius_km:.0f}"

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get path to cache file."""
        return self.config.cache_dir / f"{cache_key}.json"

    def _load_from_cache(self, cache_key: str) -> Optional[HazardDataset]:
        """Load hazard data from cache if valid."""
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)

            # Check cache expiry
            if data.get('last_updated'):
                updated = datetime.fromisoformat(data['last_updated'])
                age_days = (datetime.now() - updated).days
                if age_days > self.config.cache_expiry_days:
                    logger.debug(f"Cache expired for {cache_key}")
                    return None

            # Reconstruct dataset
            location = LocationQuery(**data['location'])
            return HazardDataset(
                hazard_type=HazardType(data['hazard_type']),
                location=location,
                start_year=data['start_year'],
                end_year=data['end_year'],
                events=data.get('events', []),
                frequency=data['frequency'],
                intensity_mean=data['intensity_mean'],
                intensity_p90=data.get('intensity_p90', 0.0),
                intensity_unit=data['intensity_unit'],
                source=data['source'],
                last_updated=data['last_updated'],
            )

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Invalid cache file {cache_path}: {e}")
            return None

    def _save_to_cache(self, cache_key: str, dataset: HazardDataset) -> None:
        """Save hazard data to cache."""
        cache_path = self._get_cache_path(cache_key)

        data = {
            'hazard_type': dataset.hazard_type.value,
            'location': asdict(dataset.location),
            'start_year': dataset.start_year,
            'end_year': dataset.end_year,
            'events': dataset.events,
            'frequency': dataset.frequency,
            'intensity_mean': dataset.intensity_mean,
            'intensity_p90': dataset.intensity_p90,
            'intensity_unit': dataset.intensity_unit,
            'source': dataset.source,
            'last_updated': dataset.last_updated or datetime.now().isoformat(),
        }

        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _fetch_from_climada(
        self,
        hazard: HazardType,
        location: LocationQuery,
        start_year: int,
        end_year: int,
    ) -> Optional[HazardDataset]:
        """
        Fetch hazard data from CLIMADA API.

        Returns None if CLIMADA is not available.
        """
        if not self.is_climada_available():
            return None

        try:
            # Import CLIMADA modules
            from climada.hazard import Hazard
            from climada.util.coordinates import get_coastlines

            bounds = location.to_bounds()
            hazard_class = self.HAZARD_CLASS_MAP.get(hazard)

            if hazard == HazardType.TROPICAL_CYCLONE:
                return self._fetch_tropical_cyclone(location, start_year, end_year)
            elif hazard == HazardType.WILDFIRE:
                return self._fetch_wildfire(location, start_year, end_year)
            elif hazard == HazardType.RIVER_FLOOD:
                return self._fetch_river_flood(location, start_year, end_year)
            else:
                logger.warning(f"CLIMADA fetch not implemented for {hazard}")
                return None

        except Exception as e:
            logger.error(f"CLIMADA fetch error: {e}")
            return None

    def _fetch_tropical_cyclone(
        self,
        location: LocationQuery,
        start_year: int,
        end_year: int,
    ) -> Optional[HazardDataset]:
        """Fetch tropical cyclone data from IBTrACS via CLIMADA."""
        try:
            from climada.hazard import TropCyclone

            bounds = location.to_bounds()

            # Fetch historical TC tracks from IBTrACS
            tc = TropCyclone.from_tracks_cartopy(
                track_set_id="ibtracs",
                start_year=start_year,
                end_year=end_year,
                basin="WP",  # Western Pacific
                centroids_bounds=bounds,
            )

            # Extract events within radius
            events = []
            for event in tc.event_id:
                intensity = tc.intensity[event].max()
                if intensity > 17:  # Tropical storm threshold
                    events.append({
                        'event_id': str(event),
                        'intensity': float(intensity),
                        'date': tc.date[event] if hasattr(tc, 'date') else None,
                    })

            num_years = end_year - start_year + 1

            return HazardDataset(
                hazard_type=HazardType.TROPICAL_CYCLONE,
                location=location,
                start_year=start_year,
                end_year=end_year,
                events=events,
                frequency=len(events) / num_years,
                intensity_mean=sum(e['intensity'] for e in events) / len(events) if events else 0,
                intensity_p90=sorted([e['intensity'] for e in events])[int(0.9*len(events))] if events else 0,
                intensity_unit="m/s",
                source=f"IBTrACS via CLIMADA ({start_year}-{end_year})",
                last_updated=datetime.now().isoformat(),
            )

        except Exception as e:
            logger.error(f"TC fetch error: {e}")
            return None

    def _fetch_wildfire(
        self,
        location: LocationQuery,
        start_year: int,
        end_year: int,
    ) -> Optional[HazardDataset]:
        """Fetch wildfire data from ERA5/FIRMS via CLIMADA."""
        try:
            from climada.hazard import WildFire

            bounds = location.to_bounds()

            # This would use CLIMADA's wildfire module
            # Simplified implementation
            wf = WildFire()
            # wf.from_nasa_firms(...) or wf.from_era5(...)

            # Return placeholder - actual implementation would process CLIMADA data
            logger.info("Wildfire CLIMADA fetch - using cached data")
            return None

        except Exception as e:
            logger.error(f"Wildfire fetch error: {e}")
            return None

    def _fetch_river_flood(
        self,
        location: LocationQuery,
        start_year: int,
        end_year: int,
    ) -> Optional[HazardDataset]:
        """Fetch river flood data from ISIMIP via CLIMADA."""
        try:
            from climada.hazard import RiverFlood

            bounds = location.to_bounds()

            # ISIMIP flood data
            rf = RiverFlood.from_isimip(
                dph_path=None,  # Would specify data path
                frc_path=None,
                bbox=bounds,
            )

            logger.info("River flood CLIMADA fetch - using cached data")
            return None

        except Exception as e:
            logger.error(f"River flood fetch error: {e}")
            return None

    def _get_literature_fallback(
        self,
        hazard: HazardType,
        location: LocationQuery,
    ) -> HazardDataset:
        """
        Get literature-based fallback data for a hazard.

        Uses HAZARD_BASELINES from hazards.py as source.
        """
        baseline = HAZARD_BASELINES.get(hazard)
        params = HAZARD_PARAMETERS.get(hazard)

        if not baseline:
            logger.warning(f"No baseline data for {hazard}")
            return HazardDataset(
                hazard_type=hazard,
                location=location,
                start_year=1980,
                end_year=2023,
                frequency=0.0,
                intensity_mean=0.0,
                intensity_unit="unknown",
                source="No data available",
                last_updated=datetime.now().isoformat(),
            )

        return HazardDataset(
            hazard_type=hazard,
            location=location,
            start_year=1980,
            end_year=2023,
            events=[],  # No event-level data from literature
            frequency=baseline.base_frequency,
            intensity_mean=baseline.base_intensity,
            intensity_p90=baseline.base_intensity * 1.5,  # Estimate
            intensity_unit=params.intensity_unit if params else baseline.intensity_unit,
            source=baseline.source,
            last_updated=datetime.now().isoformat(),
        )

    def get_hazard_data(
        self,
        hazard: HazardType,
        location: LocationQuery,
        start_year: int = 1980,
        end_year: int = 2023,
        force_refresh: bool = False,
    ) -> HazardDataset:
        """
        Get hazard data for a location.

        Attempts in order:
        1. Local cache (if use_cache=True and not expired)
        2. CLIMADA API (if installed)
        3. Literature fallback

        Args:
            hazard: Type of hazard
            location: Geographic query
            start_year: Start of historical period
            end_year: End of historical period
            force_refresh: Skip cache and fetch fresh data

        Returns:
            HazardDataset with historical data
        """
        cache_key = self._get_cache_key(hazard, location)

        # Try cache first
        if self.config.use_cache and not force_refresh:
            cached = self._load_from_cache(cache_key)
            if cached:
                logger.debug(f"Using cached data for {cache_key}")
                return cached

        # Try CLIMADA API
        dataset = self._fetch_from_climada(hazard, location, start_year, end_year)

        if dataset:
            # Save to cache
            if self.config.use_cache:
                self._save_to_cache(cache_key, dataset)
            return dataset

        # Fall back to literature
        logger.info(f"Using literature fallback for {hazard.value}")
        dataset = self._get_literature_fallback(hazard, location)

        # Cache literature data too
        if self.config.use_cache:
            self._save_to_cache(cache_key, dataset)

        return dataset

    def get_all_hazards(
        self,
        location: LocationQuery,
        hazards: List[HazardType] = None,
    ) -> Dict[HazardType, HazardDataset]:
        """
        Get data for all hazard types at a location.

        Args:
            location: Geographic query
            hazards: List of hazards (default: all types)

        Returns:
            Dict mapping hazard type to dataset
        """
        if hazards is None:
            hazards = list(HazardType)

        return {
            hazard: self.get_hazard_data(hazard, location)
            for hazard in hazards
        }

    def calculate_projected_risk(
        self,
        hazard: HazardType,
        location: LocationQuery,
        year: int,
        rcp: str = "RCP8.5",
    ) -> HazardResult:
        """
        Calculate projected hazard risk for a future year.

        Combines CLIMADA baseline with climate change factors.

        Args:
            hazard: Type of hazard
            location: Geographic query
            year: Target year
            rcp: RCP scenario

        Returns:
            HazardResult with projected values
        """
        # Get baseline data
        dataset = self.get_hazard_data(hazard, location)
        baseline = HAZARD_BASELINES.get(hazard)

        if not baseline:
            raise ValueError(f"No baseline data for hazard: {hazard}")

        # Get climate factor
        climate_factor = get_climate_factor(hazard, year, rcp)

        # Project values
        projected_outage = baseline.outage_rate * climate_factor
        projected_derate = baseline.capacity_derate * climate_factor
        projected_efficiency = baseline.efficiency_loss * climate_factor

        return HazardResult(
            hazard_type=hazard,
            base_frequency=dataset.frequency * math.sqrt(climate_factor),
            base_intensity=dataset.intensity_mean,
            intensity_unit=dataset.intensity_unit,
            outage_rate=projected_outage,
            capacity_derate=projected_derate,
            efficiency_loss=projected_efficiency,
            damage_ratio=baseline.damage_ratio * climate_factor,
            confidence_low=baseline.confidence_low * climate_factor,
            confidence_high=baseline.confidence_high * climate_factor,
            source=f"{dataset.source} + {rcp} {year}",
            methodology=baseline.methodology,
            climada_events=dataset.num_events,
            climada_years=dataset.num_years,
        )

    def get_summary(self, location: LocationQuery) -> Dict[str, Any]:
        """
        Get summary of all hazard data for a location.

        Args:
            location: Geographic query

        Returns:
            Dict with summary statistics
        """
        all_data = self.get_all_hazards(location)

        return {
            'location': {
                'name': location.name,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'radius_km': location.radius_km,
            },
            'hazards': {
                hazard.value: {
                    'frequency': data.frequency,
                    'intensity_mean': data.intensity_mean,
                    'intensity_unit': data.intensity_unit,
                    'num_events': data.num_events,
                    'data_years': data.num_years,
                    'source': data.source,
                }
                for hazard, data in all_data.items()
            },
            'data_sources': list(set(d.source for d in all_data.values())),
            'climada_available': self.is_climada_available(),
        }


# =============================================================================
# PREDEFINED LOCATIONS
# =============================================================================

KOREA_LOCATIONS: Dict[str, LocationQuery] = {
    "samcheok": LocationQuery(
        latitude=37.4404,
        longitude=129.1671,
        radius_km=50.0,
        name="Samcheok Blue Power",
    ),
    "dangjin": LocationQuery(
        latitude=36.9310,
        longitude=126.6325,
        radius_km=50.0,
        name="Dangjin Coal Power",
    ),
    "boryeong": LocationQuery(
        latitude=36.3588,
        longitude=126.4921,
        radius_km=50.0,
        name="Boryeong Coal Power",
    ),
    "hadong": LocationQuery(
        latitude=34.9344,
        longitude=127.8819,
        radius_km=50.0,
        name="Hadong Coal Power",
    ),
    "taean": LocationQuery(
        latitude=36.7536,
        longitude=126.2642,
        radius_km=50.0,
        name="Taean Coal Power",
    ),
}


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_climada_data(
    hazard: HazardType,
    lat: float,
    lon: float,
    radius_km: float = 50.0,
) -> HazardDataset:
    """
    Convenience function to get CLIMADA data.

    Args:
        hazard: Type of hazard
        lat: Latitude
        lon: Longitude
        radius_km: Search radius

    Returns:
        HazardDataset
    """
    api = CLIMADAInterface()
    location = LocationQuery(lat, lon, radius_km)
    return api.get_hazard_data(hazard, location)


def get_korea_power_plant_hazards(
    plant_name: str,
    hazards: List[HazardType] = None,
) -> Dict[HazardType, HazardDataset]:
    """
    Get hazard data for a Korean power plant.

    Args:
        plant_name: Name from KOREA_LOCATIONS
        hazards: List of hazards (default: all)

    Returns:
        Dict of HazardDataset by type
    """
    if plant_name.lower() not in KOREA_LOCATIONS:
        available = list(KOREA_LOCATIONS.keys())
        raise ValueError(f"Unknown plant: {plant_name}. Available: {available}")

    location = KOREA_LOCATIONS[plant_name.lower()]
    api = CLIMADAInterface()
    return api.get_all_hazards(location, hazards)


def check_climada_installation() -> Dict[str, Any]:
    """
    Check CLIMADA installation status and version.

    Returns:
        Dict with installation status and details
    """
    result = {
        'installed': False,
        'version': None,
        'modules': [],
        'error': None,
    }

    try:
        import climada
        result['installed'] = True
        result['version'] = climada.__version__

        # Check available modules
        available_modules = []

        try:
            from climada.hazard import TropCyclone
            available_modules.append('TropCyclone')
        except ImportError:
            pass

        try:
            from climada.hazard import WildFire
            available_modules.append('WildFire')
        except ImportError:
            pass

        try:
            from climada.hazard import RiverFlood
            available_modules.append('RiverFlood')
        except ImportError:
            pass

        result['modules'] = available_modules

    except ImportError as e:
        result['error'] = str(e)

    return result

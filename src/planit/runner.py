"""PLANiT runner — wraps PLANiT's programmatic API (CLIMADA + PhysRisk)."""
from __future__ import annotations

import csv
import importlib
import inspect
import json
import logging
import math
import os
import pkgutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import PLANiTIntegrationConfig
from .cache import PLANiTResultCache

logger = logging.getLogger(__name__)


@dataclass
class PLANiTHazardResult:
    """Single hazard result from PLANiT."""
    hazard_type: str       # e.g. "wildfire", "drought"
    scenario: str          # e.g. "ssp245", "ssp585"
    year: int              # e.g. 2050
    asset: str             # Asset name from PLANiT
    value: float           # Primary impact value
    std: float             # Standard deviation (0 if unavailable)
    unit: str              # e.g. "krw" for legacy monetary impact, "fraction" for impact_mean
    source: str            # "climada" or "physrisk"
    # Optional metadata used for probability-based outage conversion.
    event_frequency_per_year: Optional[float] = None
    event_count: Optional[float] = None
    reference_years: Optional[float] = None
    impact_bin_edges: Optional[List[float]] = None
    impact_probabilities: Optional[List[float]] = None
    impact_exceedance_values: Optional[List[float]] = None
    impact_exceedance_probabilities: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hazard_type": self.hazard_type,
            "scenario": self.scenario,
            "year": self.year,
            "asset": self.asset,
            "value": self.value,
            "std": self.std,
            "unit": self.unit,
            "source": self.source,
            "event_frequency_per_year": self.event_frequency_per_year,
            "event_count": self.event_count,
            "reference_years": self.reference_years,
            "impact_bin_edges": self.impact_bin_edges,
            "impact_probabilities": self.impact_probabilities,
            "impact_exceedance_values": self.impact_exceedance_values,
            "impact_exceedance_probabilities": self.impact_exceedance_probabilities,
        }


class PLANiTRunner:
    """Wraps PLANiT's ``run_single_hazard()`` for programmatic use.

    Adds ``Physicalrisk_PLANiT/src`` to ``sys.path`` so the PLANiT
    ``main`` module can be imported without installing it as a package.
    """

    # CLIMADA wildfire rows include event-frequency metadata; PhysRisk rows return impact_mean (fraction)
    CLIMADA_HAZARDS = {"wildfire", "fire"}
    PHYSRISK_HAZARDS = {"drought", "flood", "heatwave", "coastal_inundation", "water_risk"}

    def __init__(self, config: PLANiTIntegrationConfig, base_dir: Optional[str] = None):
        self._config = config
        self._base_dir = base_dir or str(Path.cwd())
        self._cache = PLANiTResultCache(
            cache_dir=str(config.get_cache_dir(self._base_dir)),
            ttl_hours=config.cache_ttl_hours,
        )
        self._planit_main = None  # Lazy import

    def _ensure_planit_imported(self):
        """Lazily add PLANiT src to sys.path and import main module."""
        if self._planit_main is not None:
            return
        self._ensure_local_venv_site_packages()
        self._ensure_distutils_compat()
        self._ensure_pandas_deprecate_kwarg_compat()
        self._ensure_contextily_stamen_compat()
        self._ensure_climada_impact_py314_compat()
        planit_src = str(Path(self._base_dir) / "Physicalrisk_PLANiT" / "src")
        if planit_src not in sys.path:
            sys.path.insert(0, planit_src)
            logger.info(f"Added PLANiT src to sys.path: {planit_src}")
        # Import PLANiT main module (contains run_single_hazard, load_config)
        from main import load_config as planit_load_config  # type: ignore
        from main import run_single_hazard as planit_run  # type: ignore
        self._planit_load_config = planit_load_config
        self._planit_run = planit_run
        self._planit_main = True

    def _ensure_local_venv_site_packages(self) -> None:
        """Add local .venv site-packages to sys.path for live PLANiT imports."""
        venv = Path(self._base_dir) / ".venv"
        pyver = f"python{sys.version_info.major}.{sys.version_info.minor}"
        candidates = [
            venv / "lib" / pyver / "site-packages",
            venv / "Lib" / "site-packages",
        ]
        for path in candidates:
            if path.exists() and str(path) not in sys.path:
                sys.path.insert(0, str(path))

    @staticmethod
    def _ensure_distutils_compat():
        """Provide distutils compatibility for Python 3.12+ via setuptools.

        Some CLIMADA/PLANiT dependency paths still import ``distutils``.
        Python 3.12+ removed stdlib distutils, so we alias to
        ``setuptools._distutils`` when needed.
        """
        try:
            import distutils  # noqa: F401
            return
        except ModuleNotFoundError:
            pass

        try:
            import setuptools._distutils as su_distutils
        except Exception:
            return

        sys.modules["distutils"] = su_distutils
        for mod in pkgutil.iter_modules(su_distutils.__path__):
            sub = mod.name
            alias = f"distutils.{sub}"
            target = f"setuptools._distutils.{sub}"
            if alias in sys.modules:
                continue
            try:
                sys.modules[alias] = importlib.import_module(target)
            except Exception:
                continue

    @staticmethod
    def _ensure_pandas_deprecate_kwarg_compat():
        """Patch pandas 3 deprecate_kwarg signature for older pandas_datareader.

        pandas 3 changed ``deprecate_kwarg`` to require the warning class as
        first argument; some transitive dependencies still call the older
        signature. Provide a small backward-compatible wrapper when needed.
        """
        try:
            from pandas.util import _decorators as pd_decorators
        except Exception:
            return

        fn = getattr(pd_decorators, "deprecate_kwarg", None)
        if fn is None:
            return

        try:
            params = list(inspect.signature(fn).parameters.keys())
        except Exception:
            return

        # pandas<3 uses old_arg_name as first parameter already.
        if not params or params[0] != "klass":
            return

        # Avoid double-wrapping.
        if getattr(fn, "_crp_compat_wrapped", False):
            return

        orig = fn

        def compat_deprecate_kwarg(*args, **kwargs):
            # New-style call (klass, old_arg_name, ...)
            if args and isinstance(args[0], type) and issubclass(args[0], Warning):
                return orig(*args, **kwargs)

            klass = kwargs.pop("klass", FutureWarning)

            if "old_arg_name" in kwargs:
                old = kwargs.pop("old_arg_name")
                new = kwargs.pop("new_arg_name", None)
                mapping = kwargs.pop("mapping", None)
                stacklevel = kwargs.pop("stacklevel", 2)
                return orig(klass, old, new, mapping=mapping, stacklevel=stacklevel)

            old = args[0] if len(args) >= 1 else kwargs.pop("old_arg_name")
            new = args[1] if len(args) >= 2 else kwargs.pop("new_arg_name", None)
            mapping = args[2] if len(args) >= 3 else kwargs.pop("mapping", None)
            stacklevel = args[3] if len(args) >= 4 else kwargs.pop("stacklevel", 2)
            return orig(klass, old, new, mapping=mapping, stacklevel=stacklevel)

        setattr(compat_deprecate_kwarg, "_crp_compat_wrapped", True)
        pd_decorators.deprecate_kwarg = compat_deprecate_kwarg

    @staticmethod
    def _ensure_contextily_stamen_compat():
        """Restore legacy ctx.providers.Stamen alias when missing."""
        try:
            import contextily as ctx
            from xyzservices.lib import Bunch
        except Exception:
            return

        if hasattr(ctx.providers, "Stamen") or not hasattr(ctx.providers, "Stadia"):
            return

        try:
            ctx.providers["Stamen"] = Bunch(
                Terrain=ctx.providers.Stadia.StamenTerrain,
                Toner=ctx.providers.Stadia.StamenToner,
                Watercolor=ctx.providers.Stadia.StamenWatercolor,
            )
        except Exception:
            return

    @staticmethod
    def _ensure_climada_impact_py314_compat():
        """Patch CLIMADA impact module defaults for Python 3.14 dataclass rules."""
        try:
            import climada
        except Exception:
            return

        impact_path = Path(climada.__file__).resolve().parent / "engine" / "impact.py"
        if not impact_path.exists():
            return

        try:
            text = impact_path.read_text(encoding="utf-8")
        except Exception:
            return

        patched = text
        if "from dataclasses import dataclass" in patched and "from dataclasses import dataclass, field" not in patched:
            patched = patched.replace("from dataclasses import dataclass", "from dataclasses import dataclass, field")

        patched = patched.replace(
            "return_per : np.array = np.array([])",
            "return_per : np.array = field(default_factory=lambda: np.array([]))",
        )
        patched = patched.replace(
            "impact : np.array = np.array([])",
            "impact : np.array = field(default_factory=lambda: np.array([]))",
        )

        if patched == text:
            return

        try:
            impact_path.write_text(patched, encoding="utf-8")
            logger.info("Patched CLIMADA impact.py for Python 3.14 compatibility")
        except Exception:
            return

    def _load_planit_config(self) -> Dict[str, Any]:
        """Load PLANiT's YAML config."""
        self._ensure_planit_imported()
        config_path = str(self._config.get_planit_config_path(self._base_dir))
        cfg = self._planit_load_config(config_path)
        self._normalize_planit_paths(cfg)
        self._apply_runtime_overrides(cfg)
        self._apply_dynamic_location_override(cfg)
        return cfg

    def _normalize_planit_paths(self, cfg: Dict[str, Any]) -> None:
        """Normalize key PLANiT file paths to absolute paths.

        PLANiT internals resolve some paths relative to current working
        directory, not config base path. Make key inputs absolute so live
        runs are robust regardless of caller cwd.
        """
        planit_root = Path(self._base_dir) / "Physicalrisk_PLANiT"

        project = cfg.get("project", {})
        geojson_source = project.get("geojson_source")
        if isinstance(geojson_source, str) and geojson_source:
            p = Path(geojson_source)
            if not p.is_absolute():
                project["geojson_source"] = str(planit_root / p)

        climada = cfg.get("climada", {})
        hazard = climada.get("hazard", {})
        firms_data_path = hazard.get("firms_data_path")
        if isinstance(firms_data_path, str) and firms_data_path:
            p = Path(firms_data_path)
            if not p.is_absolute():
                hazard["firms_data_path"] = str(planit_root / p)

    @staticmethod
    def _apply_runtime_overrides(cfg: Dict[str, Any]) -> None:
        """Apply runtime safety defaults for live wildfire calculation.

        Environment variables (optional):
        - CRP_PLANIT_WILDFIRE_MAX_IT
        - CRP_PLANIT_WILDFIRE_BLURR_STEPS
        - CRP_PLANIT_WILDFIRE_MAX_PROB_SEASONS
        """
        climada = cfg.setdefault("climada", {})
        hazard = climada.setdefault("hazard", {})

        raw = os.getenv("CRP_PLANIT_WILDFIRE_MAX_IT")
        if raw:
            hazard["wildfire_max_it_propa"] = int(raw)
        raw = os.getenv("CRP_PLANIT_WILDFIRE_BLURR_STEPS")
        if raw:
            hazard["wildfire_blurr_steps"] = int(raw)
        raw = os.getenv("CRP_PLANIT_WILDFIRE_MAX_PROB_SEASONS")
        if raw:
            hazard["wildfire_max_probabilistic_seasons"] = int(raw)

    def _apply_dynamic_location_override(self, cfg: Dict[str, Any]) -> None:
        """Override PLANiT asset GeoJSON from env-provided location."""
        lat_raw = os.getenv("CRP_PLANIT_LAT", "").strip()
        lon_raw = os.getenv("CRP_PLANIT_LON", "").strip()
        if not lat_raw or not lon_raw:
            return

        try:
            lat = float(lat_raw)
            lon = float(lon_raw)
        except ValueError:
            logger.warning("Invalid CRP_PLANIT_LAT/LON; skipping dynamic location override.")
            return

        asset_name = os.getenv("CRP_PLANIT_ASSET_NAME", "user_input_site").strip() or "user_input_site"
        capacity_mw = float(os.getenv("CRP_PLANIT_CAPACITY_MW", "2100"))
        half_size_deg = float(os.getenv("CRP_PLANIT_SITE_HALF_SIZE_DEG", "0.01"))
        include_grid = self._env_bool("CRP_PLANIT_INCLUDE_GRID", True)

        polygon = [
            [lon - half_size_deg, lat - half_size_deg],
            [lon + half_size_deg, lat - half_size_deg],
            [lon + half_size_deg, lat + half_size_deg],
            [lon - half_size_deg, lat + half_size_deg],
            [lon - half_size_deg, lat - half_size_deg],
        ]
        features: List[Dict[str, Any]] = [
            {
                "type": "Feature",
                "properties": {
                    "name": asset_name,
                    "capacity_mw": capacity_mw,
                    "type": "Coal/Steam/Recirculating",
                    "source": "user_input",
                },
                "geometry": {"type": "Polygon", "coordinates": [polygon]},
            }
        ]

        if include_grid:
            substation_name = (
                os.getenv("CRP_PLANIT_SUBSTATION_NAME", f"{asset_name}_substation").strip()
                or f"{asset_name}_substation"
            )
            substation_voltage_kv = float(os.getenv("CRP_PLANIT_SUBSTATION_VOLTAGE_KV", "345"))
            line_name = (
                os.getenv("CRP_PLANIT_LINE_NAME", f"{asset_name} transmission corridor").strip()
                or f"{asset_name} transmission corridor"
            )

            sub_lat_raw = os.getenv("CRP_PLANIT_SUBSTATION_LAT", "").strip()
            sub_lon_raw = os.getenv("CRP_PLANIT_SUBSTATION_LON", "").strip()
            if sub_lat_raw and sub_lon_raw:
                try:
                    sub_lat = float(sub_lat_raw)
                    sub_lon = float(sub_lon_raw)
                except ValueError:
                    logger.warning(
                        "Invalid CRP_PLANIT_SUBSTATION_LAT/LON; falling back to distance/bearing offset."
                    )
                    sub_lat_raw, sub_lon_raw = "", ""
            if not sub_lat_raw or not sub_lon_raw:
                distance_km = float(os.getenv("CRP_PLANIT_SUBSTATION_DISTANCE_KM", "30"))
                bearing_deg = float(os.getenv("CRP_PLANIT_SUBSTATION_BEARING_DEG", "235"))
                sub_lat, sub_lon = self._offset_lat_lon_km(lat, lon, distance_km, bearing_deg)

            features.extend(
                [
                    {
                        "type": "Feature",
                        "properties": {
                            "name": substation_name,
                            "type": "substation",
                            "source": "user_input",
                            "voltage_kv": substation_voltage_kv,
                        },
                        "geometry": {"type": "Point", "coordinates": [sub_lon, sub_lat]},
                    },
                    {
                        "type": "Feature",
                        "properties": {
                            "name": line_name,
                            "type": "transmission_line",
                            "source": "user_input",
                        },
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[lon, lat, 0.0], [sub_lon, sub_lat, 0.0]],
                        },
                    },
                ]
            )

        geojson = {
            "type": "FeatureCollection",
            "features": features,
        }

        dynamic_geojson_path = self._config.get_cache_dir(self._base_dir) / "dynamic_site.geojson"
        dynamic_geojson_path.parent.mkdir(parents=True, exist_ok=True)
        dynamic_geojson_path.write_text(json.dumps(geojson, ensure_ascii=False), encoding="utf-8")

        project = cfg.setdefault("project", {})
        project["geojson_source"] = str(dynamic_geojson_path)
        target_mode = os.getenv(
            "CRP_PLANIT_TARGET_ASSET_MODE",
            "all" if include_grid else "plant",
        ).strip().lower()
        if target_mode in {"all", "aggregate", "grid"}:
            self._config.target_asset = ""
        else:
            self._config.target_asset = asset_name
        logger.info(
            "Applied dynamic location override for PLANiT (asset=%s, lat=%.6f, lon=%.6f, include_grid=%s, target_mode=%s)",
            asset_name, lat, lon, include_grid, target_mode,
        )

    @staticmethod
    def _env_bool(name: str, default: bool) -> bool:
        """Parse common true/false env var forms."""
        raw = os.getenv(name, "").strip().lower()
        if not raw:
            return default
        if raw in {"1", "true", "yes", "y", "on"}:
            return True
        if raw in {"0", "false", "no", "n", "off"}:
            return False
        return default

    @staticmethod
    def _offset_lat_lon_km(lat: float, lon: float, distance_km: float, bearing_deg: float) -> tuple[float, float]:
        """Approximate destination point using local km→degree conversion."""
        theta = math.radians(bearing_deg)
        d_lat = (distance_km / 111.0) * math.cos(theta)
        cos_lat = max(1e-6, abs(math.cos(math.radians(lat))))
        d_lon = (distance_km / (111.0 * cos_lat)) * math.sin(theta)
        return lat + d_lat, lon + d_lon

    def run_hazard(
        self,
        hazard: str,
        scenarios: Optional[List[str]] = None,
        years: Optional[List[int]] = None,
    ) -> List[PLANiTHazardResult]:
        """Run PLANiT for a single hazard type across scenarios and years.

        Args:
            hazard: Hazard type (e.g. "wildfire", "drought")
            scenarios: SSP scenarios (default from config)
            years: Projection years (default from config anchor_years)

        Returns:
            List of PLANiTHazardResult
        """
        planit_cfg = self._load_planit_config()

        if scenarios is None:
            scenarios = [s for s in planit_cfg.get("scenarios", ["ssp585"]) if s != "historical"]
        if years is None:
            years = planit_cfg.get("years", self._config.anchor_years)

        # Override config with requested scenarios/years
        planit_cfg["scenarios"] = ["historical"] + list(scenarios)
        planit_cfg["years"] = list(years)

        results: List[PLANiTHazardResult] = []
        use_cache = self._should_use_cache(hazard)

        # Check cache first for all (scenario, year) combos
        uncached_scenarios = set()
        for scenario in scenarios:
            if not use_cache:
                uncached_scenarios.add(scenario)
                continue
            for year in years:
                cached = self._cache.get(hazard, scenario, year)
                if cached:
                    results.append(PLANiTHazardResult(**cached))
                else:
                    uncached_scenarios.add(scenario)

        if not uncached_scenarios:
            logger.info(f"All {hazard} results served from cache")
            return results

        # Run PLANiT for uncached data
        logger.info(f"Running PLANiT for {hazard} (scenarios: {uncached_scenarios})")
        try:
            raw = self._planit_run(planit_cfg, hazard, plot=False)
        except Exception as e:
            logger.error(f"PLANiT run failed for {hazard}: {e}")
            return results  # Return whatever was cached

        # Parse results
        new_results = self._parse_results(raw, hazard)
        requested_scenarios = set(scenarios)
        for r in new_results:
            if r.scenario not in requested_scenarios:
                continue
            if use_cache and r.scenario in uncached_scenarios:
                self._cache.put(hazard, r.scenario, r.year, r.to_dict())
            results.append(r)

        return results

    @staticmethod
    def _should_use_cache(hazard: str) -> bool:
        """Decide whether disk cache should be used for a hazard."""
        if os.getenv("CRP_PLANIT_LAT", "").strip() and os.getenv("CRP_PLANIT_LON", "").strip():
            # Dynamic location requests should not reuse cached results from
            # other assets/locations.
            return False

        ht = hazard.lower()
        if ht in PLANiTRunner.CLIMADA_HAZARDS:
            # Wildfire runtime parameters changed frequently; stale cache can
            # silently mix incompatible outputs. Allow opt-in cache usage.
            return os.getenv("CRP_PLANIT_WILDFIRE_CACHE", "0").strip() == "1"
        return True

    def run_all_hazards(
        self,
        scenarios: Optional[List[str]] = None,
        years: Optional[List[int]] = None,
    ) -> Dict[str, List[PLANiTHazardResult]]:
        """Run all configured PLANiT hazards.

        Returns:
            Dict mapping hazard_type to list of results
        """
        all_results = {}
        for hazard in self._config.planit_hazards:
            try:
                all_results[hazard] = self.run_hazard(hazard, scenarios, years)
            except Exception as e:
                logger.error(f"Failed to run {hazard}: {e}")
                all_results[hazard] = []
        return all_results

    # ------------------------------------------------------------------
    # Static CSV loader — reads pre-computed PLANiT result CSVs
    # ------------------------------------------------------------------

    @staticmethod
    def load_results_from_csv(
        results_dir: str,
        target_asset: str = "삼척화력발전소",
        anchor_years: Optional[List[int]] = None,
    ) -> List[PLANiTHazardResult]:
        """Load PLANiT results from pre-computed CSV files.

        This allows using PLANiT outputs without CLIMADA/PhysRisk installed.
        Reads wildfire (CLIMADA event-frequency metadata), drought, and water_risk (PhysRisk
        impact_mean) CSVs from ``results_dir``.

        Args:
            results_dir: Path to ``Physicalrisk_PLANiT/data/results/``.
            target_asset: Korean asset name to filter PhysRisk rows.
            anchor_years: Years to replicate wildfire metadata rows across
                (default: [2030, 2040, 2050, 2060]).

        Returns:
            List of PLANiTHazardResult covering all available hazards.
        """
        if anchor_years is None:
            anchor_years = [2030, 2040, 2050, 2060]

        rdir = Path(results_dir)
        results: List[PLANiTHazardResult] = []

        def _parse_optional_float(row: Dict[str, Any], key: str) -> Optional[float]:
            raw = row.get(key, None)
            if raw in (None, ""):
                return None
            try:
                return float(raw)
            except (ValueError, TypeError):
                return None

        def _parse_optional_float_list(row: Dict[str, Any], key: str) -> Optional[List[float]]:
            raw = row.get(key, None)
            if raw in (None, ""):
                return None
            values: Any = raw
            if isinstance(values, str):
                text = values.strip()
                if not text:
                    return None
                try:
                    values = json.loads(text)
                except Exception:
                    return None
            if not isinstance(values, list):
                return None
            out: List[float] = []
            for v in values:
                try:
                    out.append(float(v))
                except (ValueError, TypeError):
                    return None
            return out

        # --- Wildfire (CLIMADA): hazard_type, scenario, annual_frequency_per_year, n_events ---
        for p in sorted(rdir.glob("wildfire_results_*.csv")):
            with open(p, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    scenario_raw = row.get("scenario", "").strip()
                    legacy_impact = float(row.get("legacy_impact_krw", 0) or 0)
                    scenario = scenario_raw  # already "historical" / "ssp126"
                    annual_freq = _parse_optional_float(row, "annual_frequency_per_year")
                    event_count = _parse_optional_float(row, "n_events")
                    reference_years = _parse_optional_float(row, "years_covered")
                    # Replicate across anchor years (CLIMADA has no year dim)
                    for year in anchor_years:
                        results.append(PLANiTHazardResult(
                            hazard_type="wildfire",
                            scenario=scenario,
                            year=year,
                            asset=target_asset,
                            value=legacy_impact,
                            std=0.0,
                            unit="krw",
                            source="climada",
                            event_frequency_per_year=annual_freq,
                            event_count=event_count,
                            reference_years=reference_years,
                        ))
            break  # use newest file only

        # --- PhysRisk CSVs (drought, water_risk): scenario, year, asset, impact_mean ---
        for hazard_name in ("drought", "water_risk"):
            for p in sorted(rdir.glob(f"{hazard_name}_results_*.csv")):
                with open(p, encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        asset = row.get("asset", "").strip()
                        if target_asset not in asset and asset not in target_asset:
                            continue
                        scenario_raw = row.get("scenario", "").strip()
                        # Normalize: "ssp126_2030" → scenario="ssp126", year=2030
                        # "historical_None" → scenario="historical", year=0
                        parts = scenario_raw.split("_", 1)
                        scenario = parts[0]
                        raw_year = parts[1] if len(parts) > 1 else row.get("year", "")
                        try:
                            year = int(raw_year)
                        except (ValueError, TypeError):
                            year = 0

                        impact_mean = float(row.get("impact_mean", 0))
                        impact_std = float(row.get("impact_std", 0))
                        impact_bin_edges = _parse_optional_float_list(row, "impact_bin_edges")
                        impact_probabilities = _parse_optional_float_list(row, "impact_probabilities")
                        impact_exceedance_values = _parse_optional_float_list(row, "impact_exceedance_values")
                        impact_exceedance_probabilities = _parse_optional_float_list(row, "impact_exceedance_probabilities")

                        results.append(PLANiTHazardResult(
                            hazard_type=hazard_name,
                            scenario=scenario,
                            year=year,
                            asset=asset,
                            value=impact_mean,
                            std=impact_std,
                            unit="fraction",
                            source="physrisk",
                            impact_bin_edges=impact_bin_edges,
                            impact_probabilities=impact_probabilities,
                            impact_exceedance_values=impact_exceedance_values,
                            impact_exceedance_probabilities=impact_exceedance_probabilities,
                        ))
                break  # use newest file only

        logger.info(
            "Loaded %d PLANiT results from CSV (%s)",
            len(results), results_dir,
        )
        return results

    def _parse_results(
        self, raw: Dict[str, Any], hazard: str
    ) -> List[PLANiTHazardResult]:
        """Parse raw PLANiT output into PLANiTHazardResult list."""
        results = []
        target_asset = self._config.target_asset
        ht = hazard.lower()

        if ht in self.CLIMADA_HAZARDS:
            results.extend(self._parse_climada_results(raw, hazard, target_asset))
        else:
            results.extend(self._parse_physrisk_results(raw, hazard, target_asset))

        return results

    def _parse_climada_results(
        self, raw: Dict[str, Any], hazard: str, target_asset: str
    ) -> List[PLANiTHazardResult]:
        """Parse CLIMADA wildfire results (event-frequency metadata)."""
        results = []
        def _to_optional_float(v: Any) -> Optional[float]:
            if v in (None, ""):
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                return None

        for scenario_key, scenario_data in raw.get("scenarios", {}).items():
            if "error" in scenario_data:
                continue
            legacy_impact = scenario_data.get("legacy_impact_krw", 0.0)
            annual_freq = _to_optional_float(scenario_data.get("annual_frequency_per_year"))
            event_count = _to_optional_float(scenario_data.get("n_events"))
            reference_years = _to_optional_float(scenario_data.get("years_covered"))
            # CLIMADA wildfire has no year dimension — apply to all anchor years
            for year in self._config.anchor_years:
                results.append(PLANiTHazardResult(
                    hazard_type=hazard,
                    scenario=scenario_key,
                    year=year,
                    asset=target_asset,
                    value=float(legacy_impact),
                    std=0.0,
                    unit="krw",
                    source="climada",
                    event_frequency_per_year=annual_freq,
                    event_count=event_count,
                    reference_years=reference_years,
                ))
        return results

    def _parse_physrisk_results(
        self, raw: Dict[str, Any], hazard: str, target_asset: str
    ) -> List[PLANiTHazardResult]:
        """Parse PhysRisk results (impact_mean per scenario/year/asset)."""
        results = []
        def _to_optional_float_list(values: Any) -> Optional[List[float]]:
            if values is None:
                return None
            if not isinstance(values, list):
                return None
            out: List[float] = []
            for v in values:
                try:
                    out.append(float(v))
                except (ValueError, TypeError):
                    return None
            return out

        for entry in raw.get("asset_impacts", []):
            asset_name = entry.get("asset", "")
            # Match target asset (partial match on Korean name)
            if target_asset and target_asset not in asset_name and asset_name not in target_asset:
                # If no target match, still include (will use first asset)
                if results:
                    continue

            scenario = entry.get("scenario", "")
            year = entry.get("year", 0)
            impact_mean = entry.get("impact_mean", 0.0)
            impact_std = entry.get("impact_std", 0.0)
            impact_bin_edges = _to_optional_float_list(entry.get("impact_bin_edges"))
            impact_probabilities = _to_optional_float_list(entry.get("impact_probabilities"))
            impact_exceedance_values = _to_optional_float_list(entry.get("impact_exceedance_values"))
            impact_exceedance_probabilities = _to_optional_float_list(entry.get("impact_exceedance_probabilities"))

            results.append(PLANiTHazardResult(
                hazard_type=hazard,
                scenario=scenario,
                year=int(year) if year and str(year) != 'None' else 0,
                asset=asset_name,
                value=float(impact_mean),
                std=float(impact_std),
                unit="fraction",
                source="physrisk",
                impact_bin_edges=impact_bin_edges,
                impact_probabilities=impact_probabilities,
                impact_exceedance_values=impact_exceedance_values,
                impact_exceedance_probabilities=impact_exceedance_probabilities,
            ))

        return results

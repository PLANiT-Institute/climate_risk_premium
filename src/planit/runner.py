"""PLANiT runner — wraps PLANiT's programmatic API (CLIMADA + PhysRisk)."""
from __future__ import annotations

import csv
import logging
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
    unit: str              # e.g. "krw" for AAI, "fraction" for impact_mean
    source: str            # "climada" or "physrisk"

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
        }


class PLANiTRunner:
    """Wraps PLANiT's ``run_single_hazard()`` for programmatic use.

    Adds ``Physicalrisk_PLANiT/src`` to ``sys.path`` so the PLANiT
    ``main`` module can be imported without installing it as a package.
    """

    # CLIMADA hazards return AAI in KRW; PhysRisk hazards return impact_mean (fraction)
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

    def _load_planit_config(self) -> Dict[str, Any]:
        """Load PLANiT's YAML config."""
        self._ensure_planit_imported()
        config_path = str(self._config.get_planit_config_path(self._base_dir))
        return self._planit_load_config(config_path)

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

        # Check cache first for all (scenario, year) combos
        uncached_scenarios = set()
        for scenario in scenarios:
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
        for r in new_results:
            if r.scenario in uncached_scenarios:
                self._cache.put(hazard, r.scenario, r.year, r.to_dict())
                results.append(r)

        return results

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
        Reads wildfire (CLIMADA AAI), drought, and water_risk (PhysRisk
        impact_mean) CSVs from ``results_dir``.

        Args:
            results_dir: Path to ``Physicalrisk_PLANiT/data/results/``.
            target_asset: Korean asset name to filter PhysRisk rows.
            anchor_years: Years to replicate wildfire AAI across
                (default: [2030, 2040, 2050, 2060]).

        Returns:
            List of PLANiTHazardResult covering all available hazards.
        """
        if anchor_years is None:
            anchor_years = [2030, 2040, 2050, 2060]

        rdir = Path(results_dir)
        results: List[PLANiTHazardResult] = []

        # --- Wildfire (CLIMADA): hazard_type, scenario, aai_krw ---
        for p in sorted(rdir.glob("wildfire_results_*.csv")):
            with open(p, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    scenario_raw = row.get("scenario", "").strip()
                    aai = float(row.get("aai_krw", 0))
                    scenario = scenario_raw  # already "historical" / "ssp126"
                    # Replicate across anchor years (CLIMADA has no year dim)
                    for year in anchor_years:
                        results.append(PLANiTHazardResult(
                            hazard_type="wildfire",
                            scenario=scenario,
                            year=year,
                            asset=target_asset,
                            value=aai,
                            std=0.0,
                            unit="krw",
                            source="climada",
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

                        results.append(PLANiTHazardResult(
                            hazard_type=hazard_name,
                            scenario=scenario,
                            year=year,
                            asset=asset,
                            value=impact_mean,
                            std=impact_std,
                            unit="fraction",
                            source="physrisk",
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
        """Parse CLIMADA wildfire results (AAI per scenario)."""
        results = []
        for scenario_key, scenario_data in raw.get("scenarios", {}).items():
            if "error" in scenario_data:
                continue
            aai = scenario_data.get("aai", 0.0)
            # CLIMADA wildfire has no year dimension — apply to all anchor years
            for year in self._config.anchor_years:
                results.append(PLANiTHazardResult(
                    hazard_type=hazard,
                    scenario=scenario_key,
                    year=year,
                    asset=target_asset,
                    value=float(aai),
                    std=0.0,
                    unit="krw",
                    source="climada",
                ))
        return results

    def _parse_physrisk_results(
        self, raw: Dict[str, Any], hazard: str, target_asset: str
    ) -> List[PLANiTHazardResult]:
        """Parse PhysRisk results (impact_mean per scenario/year/asset)."""
        results = []
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

            results.append(PLANiTHazardResult(
                hazard_type=hazard,
                scenario=scenario,
                year=int(year) if year and str(year) != 'None' else 0,
                asset=asset_name,
                value=float(impact_mean),
                std=float(impact_std),
                unit="fraction",
                source="physrisk",
            ))

        return results

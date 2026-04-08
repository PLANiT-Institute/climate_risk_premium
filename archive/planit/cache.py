"""Disk-backed JSON cache for PLANiT results."""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class PLANiTResultCache:
    """TTL-based disk cache under data/cache/planit/.

    Key format: {hazard}_{scenario}_{year}.json
    Each file stores: {"timestamp": epoch, "data": <result_dict>}
    """

    def __init__(self, cache_dir: str = "data/cache/planit", ttl_hours: float = 24.0):
        self._cache_dir = Path(cache_dir)
        self._ttl_seconds = ttl_hours * 3600
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _key_path(self, hazard: str, scenario: str, year: int) -> Path:
        return self._cache_dir / f"{hazard}_{scenario}_{year}.json"

    def get(self, hazard: str, scenario: str, year: int) -> Optional[Dict[str, Any]]:
        """Get cached result if fresh, else None."""
        path = self._key_path(hazard, scenario, year)
        if not path.exists():
            return None
        try:
            with open(path, "r") as f:
                entry = json.load(f)
            age = time.time() - entry.get("timestamp", 0)
            if age > self._ttl_seconds:
                logger.debug(f"Cache stale for {path.name} (age={age:.0f}s)")
                return None
            logger.debug(f"Cache hit for {path.name}")
            return entry["data"]
        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.warning(f"Cache read error for {path.name}: {e}")
            return None

    def put(self, hazard: str, scenario: str, year: int, data: Dict[str, Any]) -> None:
        """Write result to cache."""
        path = self._key_path(hazard, scenario, year)
        try:
            with open(path, "w") as f:
                json.dump({"timestamp": time.time(), "data": data}, f, indent=2)
            logger.debug(f"Cached {path.name}")
        except OSError as e:
            logger.warning(f"Cache write error for {path.name}: {e}")

    def invalidate(self, hazard: str = None, scenario: str = None, year: int = None) -> int:
        """Invalidate cache entries matching the given filters. Returns count removed."""
        count = 0
        for path in self._cache_dir.glob("*.json"):
            parts = path.stem.split("_")
            if len(parts) < 3:
                continue
            h, s, y = parts[0], "_".join(parts[1:-1]), parts[-1]
            if hazard and h != hazard:
                continue
            if scenario and s != scenario:
                continue
            if year is not None and y != str(year):
                continue
            path.unlink(missing_ok=True)
            count += 1
        if count:
            logger.info(f"Invalidated {count} cache entries")
        return count

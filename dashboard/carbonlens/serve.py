#!/usr/bin/env python3
"""Minimal HTTP server for local CarbonLens development.

Serves the SPA as static files and exposes a single JSON endpoint:

    GET /api/data   →  all CSV data in the exact shape model.jsx expects

Usage:
    python3 serve.py [port]   (default: 8888)
"""
import csv
import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent.parent / "data"


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def _rows(rel_path: str) -> list[dict]:
    """Read a CSV under _DATA_DIR and return list[dict]."""
    with open(_DATA_DIR / rel_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _num(v: str) -> float | int | str:
    """Try to cast a string to int, then float, else keep as str."""
    try:
        i = int(v)
        return i
    except (ValueError, TypeError):
        pass
    try:
        return float(v)
    except (ValueError, TypeError):
        return v


# ---------------------------------------------------------------------------
# Payload builder
# ---------------------------------------------------------------------------

def build_api_payload() -> dict:
    """Read every CSV and return a single JSON-serialisable dict."""

    # ── Plant parameters ────────────────────────────────────────────────────
    plant_raw = {r["param_name"]: r["value"] for r in _rows("plant/plant_parameters.csv")}
    # Key aliases: CSV name → JS property name
    _PLANT_ALIASES = {
        "plant_name":           "name",
        "emissions_tCO2_per_mwh": "emissions_tco2_per_mwh",
        "heat_rate_mmbtu_mwh":  "heat_rate_mmbtu_per_mwh",
        "corporate_tax_rate":   "tax_rate",
    }
    plant: dict = {}
    for k, v in plant_raw.items():
        key = _PLANT_ALIASES.get(k, k)
        plant[key] = v if key == "name" else _num(v)

    # ── Model assumptions ───────────────────────────────────────────────────
    ma_raw = {r["param_name"]: r["value"] for r in _rows("assumptions/model_assumptions.csv")}
    model_assumptions: dict = {}
    _ARRAY_PARAMS = {"carbon_price_years", "physical_anchor_years"}
    for k, v in ma_raw.items():
        if k in _ARRAY_PARAMS:
            model_assumptions[k] = [int(x) for x in v.split("-")]
        else:
            model_assumptions[k] = _num(v)

    # Inject shared model params into plant so JS DEFAULT_PLANT has them
    plant["hours_per_year"] = model_assumptions.get("hours_per_year", 8760)
    plant["start_year"]     = model_assumptions.get("start_year", 2025)

    # ── Physical model assumptions ──────────────────────────────────────────
    # Note: physical/model_assumptions.csv uses "parameter" (not "param_name")
    physical_assumptions = {
        r["parameter"]: _num(r["value"])
        for r in _rows("physical/model_assumptions.csv")
    }

    # ── CLIMADA hazard data ─────────────────────────────────────────────────
    climada_rows = {r["hazard"]: r for r in _rows("physical/climada_data.csv")}
    wf  = climada_rows.get("wildfire", {})
    tc  = climada_rows.get("tropical_cyclone_damaging", {})
    climada = {
        "wildfire_events":      _num(wf.get("events_at_location", 0)),
        "wildfire_years":       _num(wf.get("years_covered", 1)),
        "tc_damaging_events":   _num(tc.get("events_at_location", 0)),
        "tc_damaging_years":    _num(tc.get("years_covered", 1)),
    }

    # ── Literature data — build all climate factor arrays + params ──────────
    lit = _rows("physical/literature_data.csv")

    def _factors(category: str, parameter: str) -> list[list]:
        rows = [r for r in lit if r["category"] == category and r["parameter"] == parameter]
        rows.sort(key=lambda r: int(r["year"]))
        return [[int(r["year"]), float(r["value"])] for r in rows]

    def _lit_param(category: str, parameter: str) -> float:
        row = next((r for r in lit if r["category"] == category and r["parameter"] == parameter), None)
        return float(row["value"]) if row else 0.0

    def _lit_year(category: str, parameter: str) -> int:
        row = next((r for r in lit if r["category"] == category and r["parameter"] == parameter), None)
        return int(row["year"]) if row else 0

    wf_climate_factors  = _factors("WILDFIRE", "climate_factor")
    tc_climate_factors  = _factors("TC",       "climate_factor")
    dr_climate_factors  = _factors("DROUGHT",  "climate_factor")
    temp_change_ssp585  = _factors("HEAT",     "korea_temp_change_ssp585")

    efficiency_params = {
        "ambient_derate_model": _lit_param("EFFICIENCY", "ambient_derate_model"),
        "cooling_water_derate": _lit_param("EFFICIENCY", "cooling_water_derate"),
        "sst_air_ratio":        _lit_param("EFFICIENCY", "sst_air_ratio"),
    }

    heatwave_params = {
        "days_baseline":   _lit_param("HEATWAVE", "days_baseline"),
        "days_future":     _lit_param("HEATWAVE", "days_future"),
        "efficiency_loss": _lit_param("HEATWAVE", "efficiency_loss"),
        "year_baseline":   _lit_year("HEATWAVE", "days_baseline"),
        "year_future":     _lit_year("HEATWAVE", "days_future"),
    }

    # ── Rating spreads ──────────────────────────────────────────────────────
    rating_spreads = {
        r["rating"]: int(float(r["spread_bps"]))
        for r in _rows("credit/rating_spreads.csv")
    }

    # ── Rating score model ──────────────────────────────────────────────────
    rsm_rows = _rows("credit/rating_score_model.csv")

    def _rsm_tiers(component: str) -> list[dict]:
        rows = [r for r in rsm_rows if r["component"] == component]
        result = []
        for r in rows:
            thr = r.get("threshold", "").strip()
            dlt = r.get("score_delta", "").strip()
            result.append({
                "threshold": float(thr) if thr else None,   # None = catch-all
                "delta":     int(dlt)   if dlt else 0,
            })
        # Replace Python None with JS -Infinity sentinel string; handled in JS
        # Actually keep None — JS will get null, and we guard with ?? in JS
        return result

    base_score_row = next((r for r in rsm_rows if r["component"] == "base_score"), None)
    consec_row     = next((r for r in rsm_rows if r["component"] == "consecutive_loss_d"), None)
    scale_row      = next((r for r in rsm_rows if r["component"] == "scale_bonus"), None)
    cutoff_rows    = [r for r in rsm_rows if r["component"] == "cutoff"]

    rating_score_model = {
        "base_score":         int(base_score_row["score_delta"]) if base_score_row else 60,
        "consecutive_loss_d": int(consec_row["score_delta"])     if consec_row else 8,
        "scale_threshold_mw": float(scale_row["threshold"])      if scale_row else 2000,
        "scale_bonus":        int(scale_row["score_delta"])       if scale_row else 4,
        "dscr":             _rsm_tiers("dscr"),
        "coverage":         _rsm_tiers("coverage"),
        "equity_leverage":  _rsm_tiers("equity_leverage"),
        "cutoffs": [
            {"score": int(r["score_delta"]), "rating": r["rating"]}
            for r in cutoff_rows
        ],
    }

    # ── Transition scenarios ────────────────────────────────────────────────
    transitions = []
    for r in _rows("transition/scenarios.csv"):
        transitions.append({
            "id":       r["scenario"],
            "name":     r["scenario"].replace("_", " ").title(),
            "dispatch": float(r["dispatch_penalty"]),
            "retire":   int(r["retirement_years"]),
            "cp": [
                float(r["carbon_price_2025"]),
                float(r["carbon_price_2030"]),
                float(r["carbon_price_2040"]),
                float(r["carbon_price_2050"]),
            ],
            "desc": r.get("description", ""),
        })

    # ── Physical scenarios ──────────────────────────────────────────────────
    _PHYS_NAMES = {
        "baseline":          "Baseline (SSP1-2.6)",
        "moderate_physical": "Moderate (SSP2-4.5)",
        "high_physical":     "High (SSP5-8.5)",
        "severe_drought":    "Severe Drought (SSP5-8.5)",
    }
    physical_scenarios = []
    for r in _rows("physical/scenarios.csv"):
        sid = r["scenario"]
        physical_scenarios.append({
            "id":       sid,
            "name":     _PHYS_NAMES.get(sid, sid),
            "wildfire": float(r["wildfire_scale"]),
            "color":    r.get("color", "#94a3b8"),
        })

    return {
        "plant":               plant,
        "model_assumptions":   model_assumptions,
        "physical_assumptions": physical_assumptions,
        "climada":             climada,
        "wf_climate_factors":  wf_climate_factors,
        "tc_climate_factors":  tc_climate_factors,
        "dr_climate_factors":  dr_climate_factors,
        "temp_change_ssp585":  temp_change_ssp585,
        "efficiency_params":   efficiency_params,
        "heatwave_params":     heatwave_params,
        "rating_spreads":      rating_spreads,
        "rating_score_model":  rating_score_model,
        "transitions":         transitions,
        "physical_scenarios":  physical_scenarios,
    }


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class NoCacheHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/data":
            self._serve_api_data()
        else:
            super().do_GET()

    def _serve_api_data(self):
        try:
            payload = build_api_payload()
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            msg = json.dumps({"error": str(exc)}).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, fmt, *args):
        code = args[1] if len(args) > 1 else ""
        if code not in ("304",):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with HTTPServer(("127.0.0.1", port), NoCacheHandler) as httpd:
        print(f"Serving CarbonLens on http://127.0.0.1:{port}/CarbonLens.html", flush=True)
        print(f"  API endpoint: http://127.0.0.1:{port}/api/data", flush=True)
        httpd.serve_forever()

#!/usr/bin/env bash
# CLIMADA Verification — Integrated Pass
# Runs 9 CLIMADA invocations: 4 normal + 4 no_csv + 1 replay
set -e

cd "$(dirname "$0")/../.."
PROJECT_ROOT="$(pwd)"
PLANIT_ROOT="$PROJECT_ROOT/Physicalrisk_PLANiT"
VENV_PYTHON="$PROJECT_ROOT/.venv-climada/bin/python3"
REPORT_DIR="$PROJECT_ROOT/reports/verify"

mkdir -p "$REPORT_DIR/runs/normal" "$REPORT_DIR/runs/no_csv" "$REPORT_DIR/runs/replay"

# ===========================================================================
# STEP 1 — Code diff (grep checks)
# ===========================================================================
echo "============================================"
echo "STEP 1 — Code Diff (Prompt verification)"
echo "============================================"

{
  echo "## Prompt 1 — subprocess SSP collapse / seed / n_seasons"
  grep -rn "MAX_PROB_SEASONS\|wildfire_max_probabilistic_seasons" src/ Physicalrisk_PLANiT/ 2>/dev/null || echo "  none"
  echo
  grep -rn "np.random.seed\|numpy.random.seed" src/planit/ Physicalrisk_PLANiT/src/ 2>/dev/null
  echo
  grep -rn "CRP_WILDFIRE_SEED" src/ Physicalrisk_PLANiT/ 2>/dev/null
  echo

  echo "## Prompt 2 — heat-efficiency"
  grep -rn "efficiency_loss" src/planit/ src/pipeline/ 2>/dev/null | head -15
  echo
  grep -rn "compute_efficiency_loss\|Heat-derate channel" src/ 2>/dev/null || echo "  none"
  echo

  echo "## Prompt 3 — magic 0.10"
  grep -rn "OUTAGE_RATE_PER_EVENT\|OUTAGE_DURATION_HOURS" src/ 2>/dev/null
  echo
  grep -rnE "0\.10[^0-9]" src/planit/adapter.py src/data/loaders.py 2>/dev/null || echo "  none"
  echo

  echo "## Prompt 4 — spatial resolution"
  grep -rn "polygon_buffer_km\|line_buffer_km" Physicalrisk_PLANiT/src/core/ 2>/dev/null || echo "  none"
  grep -rn "i_half" Physicalrisk_PLANiT/src/core/vulnerability.py 2>/dev/null || echo "  none"
  echo

  echo "## Prompt 5 — PhysRisk mode"
  grep -rn "data_mode\|snapshot_date\|PHYSRISK_HAZARD_INVENTORY_PATH" src/ 2>/dev/null || echo "  none"
  echo

  echo "## Prompt 6 — n_probabilistic_seasons"
  grep -rn "n_probabilistic_seasons" Physicalrisk_PLANiT/config/ 2>/dev/null
  echo
} > "$REPORT_DIR/code_diff.txt"

cat "$REPORT_DIR/code_diff.txt"

# --- Gate check: Prompts 1, 2, 6 must be present ---
MISSING=""
if ! grep -q "CRP_WILDFIRE_SEED" "$REPORT_DIR/code_diff.txt"; then
  MISSING="$MISSING 1(seed)"
fi
if ! grep -q "np.random.seed" "$REPORT_DIR/code_diff.txt"; then
  MISSING="$MISSING 1(seed_call)"
fi
if ! grep -q "efficiency_loss" "$REPORT_DIR/code_diff.txt"; then
  MISSING="$MISSING 2(efficiency)"
fi
if ! grep -q "n_probabilistic_seasons.*100" "$REPORT_DIR/code_diff.txt"; then
  MISSING="$MISSING 6(n_seasons=100)"
fi

if [ -n "$MISSING" ]; then
  echo ""
  echo "*** ABORT: Critical prompts appear MISSING: $MISSING ***"
  echo "Fix before running CLIMADA invocations."
  exit 1
fi

echo ""
echo "Code diff OK — all critical prompts detected."
echo ""

# ===========================================================================
# STEP 2 — Check .venv-climada availability
# ===========================================================================
if [ ! -x "$VENV_PYTHON" ]; then
  echo "*** ABORT: $VENV_PYTHON not found or not executable ***"
  echo "CLIMADA verification requires .venv-climada with CLIMADA installed."
  exit 1
fi

echo "Using Python: $VENV_PYTHON"
echo ""

# ===========================================================================
# STEP 3 — Run 9 CLIMADA invocations
# ===========================================================================
export CRP_WILDFIRE_SEED=42
# Override for faster verification (production uses 100 from config)
export CRP_PLANIT_WILDFIRE_MAX_PROB_SEASONS=10
export CRP_PLANIT_WILDFIRE_MAX_IT=10000

# --- Helper: inline CLIMADA runner that bypasses visualization imports ---
RUNNER_SCRIPT='
import sys, os, json, logging, warnings
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
sys.path.insert(0, "src")

import yaml
import numpy as np

with open("config/unified_config.yaml") as f:
    cfg = yaml.safe_load(f)
cfg["_base_path"] = os.getcwd()

# Override scenarios from env
scenarios = json.loads(os.environ.get("CRP_SCENARIOS", "[]"))
if scenarios:
    cfg["scenarios"] = scenarios

# Apply runtime overrides for verification speed
max_prob = os.environ.get("CRP_PLANIT_WILDFIRE_MAX_PROB_SEASONS")
if max_prob:
    cfg.setdefault("climada", {}).setdefault("hazard", {})["wildfire_max_probabilistic_seasons"] = int(max_prob)
max_it = os.environ.get("CRP_PLANIT_WILDFIRE_MAX_IT")
if max_it:
    cfg.setdefault("climada", {}).setdefault("hazard", {})["wildfire_max_it_propa"] = int(max_it)

from core.hazard import get_hazard
from core.exposure import load_assets_from_geojson, get_exposure
from core.vulnerability import calculate_impact
from core.provenance import stamp

prov_dir = os.environ.get("CRP_PROVENANCE_DIR", "")

hazards = get_hazard(cfg, "wildfire")
exposure = get_exposure(cfg, "wildfire")

for scenario, haz in hazards.items():
    imp = calculate_impact(cfg, "wildfire", haz, exposure)
    freq = getattr(haz, "frequency", None)
    annual_freq = float(np.sum(freq)) if freq is not None else None

    _sp = cfg.get("climada", {}).get("hazard", {}).get("scenario_params", {}).get(scenario, {})
    n_proba = _sp.get("n_probabilistic_seasons", 100)

    print(f"  {scenario}: aai={imp.aai_agg:.0f}, events={len(imp.at_event)}, freq={annual_freq}")

    if prov_dir:
        stamp(haz, exposure, imp, scenario,
              output_dir=os.path.join(prov_dir, scenario),
              execution_path="in_process",
              n_proba_seasons=n_proba)

print("Done.")
'

# --- Normal runs (4 scenarios, climate factors active) ---
echo "============================================"
echo "STEP 3a — Normal runs (seed=42, climate factors ON)"
echo "============================================"
unset CRP_DISABLE_CLIMATE_FACTOR
export CRP_PROVENANCE_DIR="$REPORT_DIR/runs/normal"
export CRP_SCENARIOS='["historical","ssp126","ssp245","ssp585"]'

cd "$PLANIT_ROOT"
"$VENV_PYTHON" -c "$RUNNER_SCRIPT" 2>&1 | tail -30
cd "$PROJECT_ROOT"

echo ""

# --- No-CSV runs (4 scenarios, climate factors disabled) ---
echo "============================================"
echo "STEP 3b — No-CSV runs (seed=42, climate factors OFF)"
echo "============================================"
export CRP_DISABLE_CLIMATE_FACTOR=1
export CRP_PROVENANCE_DIR="$REPORT_DIR/runs/no_csv"

cd "$PLANIT_ROOT"
"$VENV_PYTHON" -c "$RUNNER_SCRIPT" 2>&1 | tail -30
cd "$PROJECT_ROOT"

unset CRP_DISABLE_CLIMATE_FACTOR
echo ""

# --- Replay run (ssp245 only, seed=1337) ---
echo "============================================"
echo "STEP 3c — Replay run (seed=1337, ssp245 only)"
echo "============================================"
export CRP_WILDFIRE_SEED=1337
export CRP_PROVENANCE_DIR="$REPORT_DIR/runs/replay"
export CRP_SCENARIOS='["ssp245"]'

cd "$PLANIT_ROOT"
"$VENV_PYTHON" -c "$RUNNER_SCRIPT" 2>&1 | tail -30
cd "$PROJECT_ROOT"

echo ""
echo "============================================"
echo "All 9 invocations complete."
echo "============================================"

# ===========================================================================
# STEP 4 — Run analysis
# ===========================================================================
echo ""
echo "Running analysis..."
python3 scripts/verify/analyze.py

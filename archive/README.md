# Archive

This directory contains deprecated files that are no longer used in the latest version of the Climate Risk Premium model. These files are preserved for historical reference and backward compatibility purposes.

## Archived: November 2024

### deprecated_data/
Old data files replaced by more comprehensive versions:

| File | Replaced By | Reason |
|------|-------------|--------|
| `plant.csv` | `plant_parameters.csv` | More detailed plant specifications with additional parameters |
| `policy.csv` | `src/scenarios/korea_power_plan.py` | Replaced by dedicated Korea Power Plan module with official 10th/11th Plan trajectories |
| `physical.csv` | `climada_hazards.csv` | Generic physical risk data superseded by CLIMADA spatially-explicit hazard data |
| `financing.csv` | `financing_params.csv` | Expanded financing parameters with KIS methodology integration |

### deprecated_docs/
Documentation files that have been merged or superseded:

| File | Status | Notes |
|------|--------|-------|
| `mathematical_framework_backup.tex` | Merged into `paper.tex` | Original mathematical framework before integration into main paper |
| `risk.tex` | Merged into `paper.tex` | Standalone risk equations document, now part of Section 2 of paper |

### deprecated_scripts/
Entry point scripts replaced by improved versions:

| File | Replaced By | Reason |
|------|-------------|--------|
| `run_analysis.py` | `run_full_analysis.py` | Original runner replaced by comprehensive multi-scenario analysis script |
| `debug_imports.py` | N/A | Troubleshooting script no longer needed after import issues resolved |

## Current Active Files

For the latest version of the model, use:
- **Data**: Files in `data/raw/` (excluding archived files)
- **Entry Points**: `run_app.py` (Streamlit) or `run_full_analysis.py` (batch)
- **Documentation**: `paper.tex` and `docs/*.md`

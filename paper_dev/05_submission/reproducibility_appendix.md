# Reproducibility Appendix

## Canonical Command Sequence

1. Run full model scenarios:

```bash
python3 /Users/jinsu/Documents/GitHub/climate_risk_premium/scripts/reproduce_results.py
```

2. Freeze outputs and hashes:

```bash
python3 /Users/jinsu/Documents/GitHub/climate_risk_premium/scripts/freeze_paper_results.py \
  --source-dir /Users/jinsu/Documents/GitHub/climate_risk_premium/results \
  --dest-dir /Users/jinsu/Documents/GitHub/climate_risk_premium/paper_dev/02_results_freeze/results_snapshot \
  --manifest-path /Users/jinsu/Documents/GitHub/climate_risk_premium/paper_dev/02_results_freeze/manifest.json \
  --strict
```

3. Generate frozen tables and figures:

```bash
python3 /Users/jinsu/Documents/GitHub/climate_risk_premium/scripts/generate_frozen_paper_figures.py \
  --scenario-csv /Users/jinsu/Documents/GitHub/climate_risk_premium/paper_dev/02_results_freeze/results_snapshot/scenario_comparison.csv \
  --output-dir /Users/jinsu/Documents/GitHub/climate_risk_premium/paper_dev/03_figures
```

4. Generate robustness outputs and manuscript numeric macros:

```bash
python3 /Users/jinsu/Documents/GitHub/climate_risk_premium/scripts/run_paper_robustness.py \
  --manifest-path /Users/jinsu/Documents/GitHub/climate_risk_premium/paper_dev/02_results_freeze/manifest.json \
  --scenario-csv /Users/jinsu/Documents/GitHub/climate_risk_premium/paper_dev/02_results_freeze/results_snapshot/scenario_comparison.csv \
  --output-dir /Users/jinsu/Documents/GitHub/climate_risk_premium/paper_dev/02_results_freeze/robustness \
  --strict
```

5. Validate manuscript numeric consistency:

```bash
python3 /Users/jinsu/Documents/GitHub/climate_risk_premium/scripts/validate_manuscript_numbers.py \
  --manuscript-path /Users/jinsu/Documents/GitHub/climate_risk_premium/paper_dev/01_manuscript/paper_energy_policy.tex \
  --manifest-path /Users/jinsu/Documents/GitHub/climate_risk_premium/paper_dev/02_results_freeze/manifest.json \
  --scenario-csv /Users/jinsu/Documents/GitHub/climate_risk_premium/paper_dev/02_results_freeze/results_snapshot/scenario_comparison.csv \
  --robustness-csv /Users/jinsu/Documents/GitHub/climate_risk_premium/paper_dev/02_results_freeze/robustness/robustness_summary.csv \
  --fail-on-mismatch
```

6. Build submission package archive:

```bash
python3 /Users/jinsu/Documents/GitHub/climate_risk_premium/scripts/build_paper_package.py --fail-on-missing
```

## Mandatory Artifacts

- Frozen scenario outputs and cash-flow files
- Manifest JSON including run metadata and SHA-256 hashes
- Frozen figures/tables generated from snapshot only
- Robustness summary CSV and tornado figure
- Claim registry and reference registry
- Validator report with zero mismatches
- Submission package zip from `build_paper_package.py`

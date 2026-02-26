# Energy Policy Submission Checklist

## Manuscript Integrity

- [x] Canonical manuscript path fixed (`paper_dev/01_manuscript/paper_energy_policy.tex`)
- [x] Abstract length <= 250 words
- [x] Keywords count <= 6
- [x] Numeric claims inserted via `\input{}` generated files
- [x] No conflicting quantitative claims across manuscript and frozen outputs

## Reproducibility Governance

- [x] Scenario contract fixed to `default_11_scenarios_v1`
- [x] Canonical run reproduced (`scripts/reproduce_results.py`)
- [x] Frozen outputs and manifest regenerated (`scripts/freeze_paper_results.py`)
- [x] Robustness package generated (`scripts/run_paper_robustness.py`)
- [x] Manuscript validation passes with zero mismatch

## Evidence Governance

- [x] `claim_registry.csv` statuses limited to `verified|needs_revision|remove`
- [x] `claim_registry.csv` unresolved statuses (`needs_revision|remove`) = 0
- [x] `reference_registry.csv` schema matches required contract
- [x] `reference_registry.csv` non-verified entries = 0

## Submission Metadata

- [x] Highlights provided (3-5 items, each <= 85 chars)
- [x] Cover letter prepared
- [x] Data availability statement prepared
- [x] Code availability statement prepared
- [x] Reproducibility appendix prepared
- [x] CRediT authorship statement included in manuscript
- [x] Competing interest statement included in manuscript
- [x] Funding statement included in manuscript

## Delivery

- [x] Submission package folder generated
- [x] Submission package zip generated

# Energy Policy Submission Strategy (Updated 2026)

## Target and Positioning

- Primary target: **Energy Policy**
- Fallback target after first decision: **Energy Economics**
- Paper type: single-case Samcheok study with reproducibility-first package

## Current Baseline (Canonical Frozen Run)

- Baseline NPV: **$3,103M**
- Enhanced 11th Plan NPV: **-$3,293M**
- NPV swing: **$6,396M**
- Baseline rating: **AA**
- Enhanced rating: **C**
- Counterfactual CRP (enhanced): **1,735 bps**

## Working Timeline (2026)

| Stage | Energy Policy | Notes |
|------|---------------|-------|
| Freeze canonical package | Complete | Frozen outputs + manifest in `paper_dev/02_results_freeze` |
| Manuscript consistency pass | Week of Feb 17, 2026 | Remove conflicting legacy claims |
| Internal review + final edits | Week of Feb 24, 2026 | Claim registry and reproducibility checks |
| Submission window | Early March 2026 | Submit once checklist is fully complete |

## Required Submission Materials

- Manuscript (`paper_dev/01_manuscript/paper_energy_policy.tex`)
- Highlights (`paper_dev/05_submission/highlights.md`)
- Cover letter (`paper_dev/05_submission/cover_letter.md`)
- Data availability statement (`paper_dev/05_submission/data_availability.md`)
- Code availability statement (`paper_dev/05_submission/code_availability.md`)
- Reproducibility appendix (`paper_dev/05_submission/reproducibility_appendix.md`)
- Claim registry (`paper_dev/04_sources/claim_registry.csv`)

## Quality Gates Before Submission

1. Canonical producer rerun succeeds.
2. Freeze manifest hashes match snapshot files.
3. Manuscript number validator returns no mismatches.
4. `pytest` passes without `PYTHONPATH` workaround.
5. README summary and results summary match frozen numbers.

## Fallback Rule

If Energy Policy declines, activate fallback checklist:

- `paper_dev/00_admin/fallback_energy_economics.md`

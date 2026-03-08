# Code Availability Statement

The complete analysis code is available in this repository. The canonical paper workflow is executed with:

- `scripts/reproduce_results.py`
- `scripts/freeze_paper_results.py`
- `scripts/generate_frozen_paper_figures.py`
- `scripts/run_paper_robustness.py`
- `scripts/validate_manuscript_numbers.py`
- `scripts/build_paper_package.py`

`build_paper_package.py` assembles a submission archive and enforces manuscript/package integrity checks when `--fail-on-missing` is enabled.

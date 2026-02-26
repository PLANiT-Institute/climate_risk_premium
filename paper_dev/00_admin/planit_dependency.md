# PLANiT Dependency Note

The CRP pipeline can ingest pre-computed PLANiT outputs when available.

Configured path (default):

- `/Users/jinsu/Documents/GitHub/climate_risk_premium/Physicalrisk_PLANiT/data/results`

Operational behavior:

1. If PLANiT CSV outputs are present, they are loaded and converted through `src/planit/adapter.py`.
2. If they are absent, the loader returns an empty result set and the pipeline can still run, but physical-risk detail may be reduced.

For paper reproducibility, always rely on frozen outputs and manifest under:

- `/Users/jinsu/Documents/GitHub/climate_risk_premium/paper_dev/02_results_freeze`

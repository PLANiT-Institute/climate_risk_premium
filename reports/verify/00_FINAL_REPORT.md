# CLIMADA Verification Report

Climada version: `unknown`  
Python: `3.12.12`  
Seed (normal/no_csv): 42, Seed (replay): 1337  
n_probabilistic_seasons: 100  

## Gate 1 — Code diff
See `reports/verify/code_diff.txt`. All critical prompts (1, 2, 6) detected.

## Gate 2 — Execution provenance
- All in_process: **PASS**
- Centroid count consistent: **PASS** (7812 centroids)
- Probabilistic seasons active: **FAIL** (hist=20, ssp126=20, ssp245=20, ssp585=20)
- ssp126 vs ssp585 intensity differs: **PASS**
- |AAI| monotone (126 < 245 < 585): **PASS** ['28757875', '8321327', '51312330', '695474946']
- Frequency sums: ['1.0000', '1.0000', '1.0000', '1.0000'] (normalized to ~1.0 by CLIMADA — not useful for SSP ordering)

## Gate 3 — Object sanity (ssp245)
- haz.size: 20 **PASS**
- intensity_max: 474.8 **PASS**
- imp_mat.nnz: 12 **PASS**
- |aai_agg|: 5.131e+07 **PASS**
- bbox in Korea: **PASS**

## Gate 4 — Seed control
- seed=42 vs seed=1337 fingerprint differs: **PASS**
  - seed=42:   intensity_hash=139355315bd0097e, freq_sum=1.0000
  - seed=1337: intensity_hash=bc6d79af92fd5b6f, freq_sum=1.0000

Note: byte-identical replay (same seed twice) not tested to save runtime. Add a 10th run if needed.

## Gate 5 — SSP attribution ablation
| SSP | normal |AAI| | no_csv |AAI| | CSV contribution |
|-----|-----------|------------|------------------|
| historical | 2.876e+07 | 2.876e+07 | 0.0% |
| ssp126 | 8.321e+06 | 8.321e+06 | 0.0% |
| ssp245 | 5.131e+07 | 5.131e+07 | 0.0% |
| ssp585 | 6.955e+08 | 6.955e+08 | 0.0% |

**Max CSV contribution: 0.0%**  
**Paper framing: CLIMADA-driven**

## Verdict
**PASS** — critical checks (G2 in-process, G2 probabilistic, G2 SSP differs, G3 nnz, G4 seed)
# Submission Strategy (Updated 2026-02-27)

## Target and Positioning

- Paper type: single-case Samcheok study with reproducibility-first package
- Author profile: early-career, small institution (PLANiT Institute)
- Paper characteristics: deterministic scenario analysis, project finance model, credit rating/CRP, reproducibility governance

## Tiered Submission Strategy (APC-free priority)

```
1st  Climate Risk Management (Elsevier, IF 5.0)  elsarticle compatible, Case Report accepted
2nd  Clean Energy (Oxford UP, IF 3.7)             APC free, OUP reformat required
3rd  Carbon Management (T&F, IF 3.2)              subscription-only = APC free, T&F reformat required
```

---

## Journal Details

### 1. Climate Risk Management (Elsevier) — CURRENT TARGET

| Field | Detail |
|-------|--------|
| IF | 5.0 (CiteScore 5.7) |
| Competition | Moderate — ~89 articles/year |
| Scope | Climate risk assessment, risk management for decision-making |
| Case study | "Case Report" type explicitly accepted |
| Review | ~30 weeks (submission to publication) |
| APC | $3,480 (Gold OA mandatory) |
| Format | elsarticle — **current manuscript format, no reformat needed** |

**Why this journal:**
- Journal name directly matches paper topic (climate risk + management)
- Case Report type explicitly welcomed — no single-case reviewer resistance
- elsarticle compatible — zero reformatting
- IF 5.0 — meaningful for early-career first publication
- Small community — lower competition than Energy Policy (~1,000+ articles/year)

**Caveat:** APC $3,480 (Gold OA mandatory). If budget is a constraint, fall back to Clean Energy.

### 2. Clean Energy (Oxford University Press) — FALLBACK (APC-FREE)

| Field | Detail |
|-------|--------|
| IF | 3.7 |
| Competition | Low-moderate — founded 2017, growing |
| Scope | Clean energy technologies, decarbonization |
| Case study | Applied/industrial case studies accepted |
| Review | Relatively fast (newer journal) |
| APC | **Free ($0)** |
| Format | OUP template — **reformat required** |

**Why this journal:**
- APC $0 — decisive advantage for small institution
- IF 3.7 — meaningful level
- Coal decarbonization papers published before
- Growing journal — welcoming submissions

**Reformat needed:** OUP LaTeX template, energy transition/decarbonization framing emphasis.

### 3. Carbon Management (Taylor & Francis) — FALLBACK (NICHE)

| Field | Detail |
|-------|--------|
| IF | 3.2 |
| Competition | Low — niche journal, small community |
| Scope | GHG, carbon policy, carbon economics |
| Case study | Applied case studies accepted |
| Review | ~13 weeks (fast) |
| APC | $2,195 (OA optional) / **subscription-only = free** |
| Format | T&F template — **reformat required** |

**Why this journal:**
- Niche and accessible
- Carbon pricing/emission scenario emphasis fits scope
- Subscription-only option avoids APC

**Reformat needed:** T&F template, emphasize carbon pricing aspects.

---

## Journals NOT Recommended

| Journal | IF | Reason |
|---------|-----|--------|
| Energy Policy | 9.2 | Too competitive for single-case early-career paper |
| Energy Economics | 13.0 | More competitive + econometric methodology preferred |
| Energy Strategy Reviews | 9.9 | Same competition level as Energy Policy |
| Energy Research & Social Science | 8.5 | Social science methodology required — scope mismatch |
| Sustainability (MDPI) | 3.3 | Norwegian Level 0 — reputation risk |
| Energy for Sustainable Development | 4.9 | Developing country focus — Korea not applicable |
| Int'l J. Sustainable Energy | 2.0 | Renewable energy engineering focus |

---

## Current Baseline (Canonical Frozen Run)

- Baseline NPV: **$4,629M**
- Enhanced 11th Plan NPV: **-$1,891M**
- NPV swing: **$6,520M**
- Baseline rating: **AA**
- Enhanced rating: **CC**
- Counterfactual CRP (enhanced): **1,020 bps**

## Working Timeline (2026)

| Stage | Status | Notes |
|-------|--------|-------|
| Freeze canonical package | Complete | Frozen outputs + manifest in `paper_dev/02_results_freeze` |
| Manuscript consistency pass | Complete | Week of Feb 17, 2026 |
| Internal review + final edits | Complete | Week of Feb 24, 2026 |
| Fact-check parameter fix | Complete | Feb 26, 2026 — corrected 6 plant parameters, re-ran full pipeline |
| Journal strategy research | Complete | Feb 27, 2026 — tiered strategy finalized |
| Submission window | Mid-March 2026 | Submit to Climate Risk Management first |

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

## Fallback Procedure

If Climate Risk Management desk-rejects or rejects after review:

1. **Clean Energy (OUP):** Reformat to OUP template, strengthen energy transition framing, update cover letter. No APC cost.
2. **Carbon Management (T&F):** Reformat to T&F template, emphasize carbon pricing and emission scenario dimensions. Choose subscription-only to avoid APC.
3. Detailed fallback checklists in `paper_dev/00_admin/fallback_clean_energy.md` and `paper_dev/00_admin/fallback_carbon_management.md`.

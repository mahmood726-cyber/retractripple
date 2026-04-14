# RetractRipple Design

Status: draft
Date: 2026-04-14
Author: Mahmood Ahmad

## Purpose

Map the downstream blast radius of primary-study retractions:

1. Which live Cochrane CDSR meta-analyses still pool at least one retracted primary (for data/results-concerns reasons)?
2. When the retracted primary is removed and the MA is recomputed under its original pooling method, does the pooled effect flip direction or significance?
3. Which current ESC / ACC / AHA / NICE cardiology guideline recommendations rest on those flipped MAs?

Outputs a BMJ Analysis manuscript, an E156 micro-paper, a static GitHub Pages dashboard, and a reusable recomputed-effects CSV consumable by MetaAudit, MetaRepair, and NICE Cardiology.

## Non-goals

- Not a replacement for Retraction Watch or RW's own downstream-impact work.
- Not a causal claim that any retraction caused a guideline change. Descriptive dependency mapping only.
- Not covering non-Cochrane SRs (Phase 2 with Epistemonikos).
- Not covering non-cardiology guidelines (Phase 2).
- Not correcting NMAs (pairwise MA only; NMA correction belongs to SheafNMA / ConformalMA extensions).

## Cohort

- **Retractions:** Retraction Watch DB, filtered to "data/results concerns" via a pinned keyword list stored in `retractions/concerns_keywords.yml` and validated against a hand-audit subsample. Version pinned in `retractions/rw_export_version.txt`.
- **MA corpus:** all currently-live Cochrane CDSR reviews, from the same dated CDSR metadata export pinned for Proto-Pub-Drift.
- **Guideline corpus:** current-edition ESC, ACC/AHA, and NICE cardiology guidelines (OA PDFs).

Temporal scope: all-time snapshot, frozen at pinned export dates. Not a living dashboard.

## Module layout

```
C:\Models\RetractRipple\
  retractions/           # Retraction Watch ingest + data/results-concerns filter
  cdsr_pool/             # CDSR metadata parsing; per-review primary list + IV weights
  match_engine/          # retracted-primary -> affected-MA bipartite graph
  recompute/             # per-MA removal + repool under MA's original method
  flip_rules/            # three flip definitions (A primary, B and C sensitivity)
  guidelines/            # ESC/ACC/AHA/NICE cardiology PDF citation extraction
  analysis/              # blast-radius counts, flip rates, guideline chain
  dashboard/             # static GitHub Pages: graph, league, per-MA cards
  paper/                 # BMJ Analysis manuscript
  e156-submission/       # E156 body + workbook entry
  sap/                   # pre-registered analysis plan
  tests/                 # pooling method unit tests + R/metafor validation + schema checks
  data/                  # pinned RW + CDSR exports; recomputed_effects.csv (reusable)
  docs/                  # this spec + downstream plan
  LICENSE, README.md, E156-PROTOCOL.md, index.html, PROGRESS.md (gitignored)
```

## Recomputation policy

For every Cochrane MA pooling at least one retracted primary, re-pool with the retracted study removed, using the MA's original pooling method as declared in CDSR metadata (DL, REML, HKSJ, Peto, or Mantel-Haenszel).

Advanced-stats rules that must be honoured:

- DL is used only if k_after_removal >= 10; otherwise switch to REML or PM and record the method change in the CSV.
- HKSJ uses the t-distribution with df = k - 1 (`qt(alpha/2, k-1)`), not normal quantiles.
- HKSJ variance floor: `max(1, Q/(k-1))` (prevents CI narrowing below DL when Q < k - 1).
- All ratio effects (OR, RR, HR) pooled on the log scale; back-transform after.
- Zero-cell continuity correction applied only if at least one cell is zero.
- Fisher z variance uses `1/(n-3)` where relevant; clamp at r = +/-0.9999.
- k_after_removal = 1 -> no recomputation; flag in CSV as `single_study_remaining`.
- k_after_removal = 2 with HKSJ -> fail-closed with explicit message; do not emit a degenerate CI.

## Flip rules

All three rules are computed for every affected MA. The headline paper figure uses Rule A. Rules B and C are sensitivity analyses.

| Rule | Definition |
|------|------------|
| A (primary) | Flip = significance change OR direction change |
| B | Flip = direction change OR crossing a pre-specified clinical threshold (HR 1.0 or MCID per outcome) |
| C | Flip considered only if retracted study's inverse-variance weight >= 10% of pooled total; flip = significance OR direction change |

The blast-radius count in the headline is inclusive: the number of live Cochrane MAs pooling at least one retracted primary, regardless of flip status. Flip rates are broken out by rule.

## Guideline citation extraction

Per current-edition ESC / ACC/AHA / NICE cardiology guideline:

1. Parse PDF text (pdfplumber or pdfminer.six).
2. Locate reference list; extract CDSR review identifiers (Cochrane DOI, review ID, or first-author+year match to CDSR metadata).
3. For each cited review, extract the strongest recommendation class and evidence level associated with that citation in the guideline body.
4. Hand-audit 50-citation stratified subsample; extractor accuracy gate: >= 0.85. Below 0.85 blocks headline "guideline dependency" figure.

## Recomputed-effects CSV schema

`data/recomputed_effects.csv`:

```
cdsr_review_id, retracted_pmid, k_original, k_after_removal, method_original,
method_used_after_removal, effect_original, ci_lower_original, ci_upper_original,
effect_removed, ci_lower_removed, ci_upper_removed, weight_retracted,
flip_rule_A, flip_rule_B, flip_rule_C, clinical_threshold_used,
weight_source_flag (iv_from_cdsr | recomputed_from_ci_altman_bland)
```

## Data sources

All OA:

- Retraction Watch DB export (CSV via Crossref Event Data partnership).
- Cochrane CDSR metadata export, shared with Proto-Pub-Drift, version pinned.
- ESC guideline PDFs (escardio.org), AHA/ACC (jacc.org), NICE (nice.org.uk).
- Crossref Event Data for citation-graph cross-validation only.

No paywalled content; no PubMed full-text paywall dependency.

## Testing

- Unit tests per pooling method on synthetic fixtures: DL, REML, HKSJ, Peto, M-H.
- R / metafor validation on a 20-MA subset with tolerance 1e-6. Rscript from `C:\Program Files\R\R-4.5.2\bin\Rscript.exe`.
- Edge cases:
  - k = 2 after removal with HKSJ (fail-closed, no fake CI).
  - k = 1 after removal (skip recomputation, flag row).
  - Zero-cell 2x2 after removal (continuity correction only if a true zero exists).
  - Log-scale pooling validated for OR, RR, HR (regression guard against natural-scale Simpson's paradox).
  - `0.5 * (a + b)` vs `(a + b) / 2` for Windows/Python rounding drift in mean calculations.
- Schema check on Retraction Watch CSV (fail-closed on column drift).
- Hand-audit 50-citation guideline subsample; accuracy >= 0.85 per guideline society.
- Numerical baselines pinned for all recomputed-effects CSV columns against hand-verified 20-MA fixture set.

## Failure-mode guards

- Retraction Watch reason field is free-text; the "data/results concerns" filter is the largest classification-error surface and is explicitly declared in the limitations section. Pinned keyword list versioned in repo.
- CDSR inverse-variance weights missing from export -> recompute SE from published 95% CI using Altman-Bland; flag via `weight_source_flag`.
- Heterogeneous guideline citation formats -> hand-audit gate >= 0.85 per society; below-bar societies blocked from headline.
- Retraction-of-retraction cases -> filter by `retraction_status_as_of` equal to pinned export date.
- TruthCert on all pooled claims (blast-radius counts, flip rates, guideline-dependency counts). HMAC key sourced from `TRUTHCERT_HMAC_KEY` env var only; never from the bundle; `hmac.compare_digest` for MAC comparison; no placeholder signatures.
- Memory != evidence: all export versions pinned as version-controlled artifacts.
- No hardcoded local paths in the dashboard, HTML, or E156 PDFs; Windows candidate-root pattern for AACT / PDF directories.

## Shipping artifacts

- BMJ Analysis manuscript (`paper/bmj-analysis.md`).
- E156 micro-paper body + `e156-submission/` + rewrite-workbook entry (CURRENT BODY only; YOUR REWRITE empty; SUBMITTED `[ ]`).
- Static GitHub Pages dashboard (`index.html`): retraction -> MA -> guideline graph, sponsor/society league table, per-MA recomputation cards. Offline-first, no CDN.
- TruthCert bundle covering blast-radius counts, flip rates per rule, and guideline-dependency counts.
- Reusable artifact: `data/recomputed_effects.csv`, consumed read-only by MetaAudit, MetaRepair, NICE Cardiology.
- `INDEX.md` entry and `rewrite-workbook.txt` entry (count incremented).

## Timeline

~5-6 weeks.

## Dependencies / prereqs (Task 0 fail-closed gate)

Before the implementation plan runs a single test:

- `python C:\ProjectIndex\reconcile_counts.py` exits 0 (registry sane).
- Retraction Watch export path resolves on disk.
- Cochrane CDSR metadata export path resolves (same pinned version as Proto-Pub-Drift).
- ESC / ACC/AHA / NICE cardiology guideline PDF directory resolves and contains at least current-edition files.
- `C:\Program Files\R\R-4.5.2\bin\Rscript.exe` resolves and `library(metafor)` loads.
- `TRUTHCERT_HMAC_KEY` env var set.

Any missing prereq fails closed with a specific user-action list.

## Out of scope for this spec

- Non-Cochrane SR corpora (Phase 2 via Epistemonikos).
- Non-cardiology guidelines (Phase 2).
- Causal attribution of guideline change to retraction (descriptive only).
- NMA recomputation (belongs to SheafNMA / ConformalMA extension).
- Retractions for plagiarism / duplicate publication / authorship disputes where the numerical evidence is not in question.

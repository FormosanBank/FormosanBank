# Audit: Formosan-Safolu-Amis-Dictionary (formerly Formosan-Amis-Moedict) — Safolu kept, Poinsot split out

**Date:** 2026-06-12 (updated 2026-06-14)
**Auditor:** Claude (audit-dev-repo skill), with maintainer (Joshua Hartshorne) sign-off at each step.
**Dev repo audited:** `Formosan-Amis-Moedict`, since renamed to **`Formosan-Safolu-Amis-Dictionary`** (Amis; g0v Amis Moedict `docs/s`).
**Outcome:** audit → remediation. Safolu fixed in place; Poinsot split into a new
dedicated repo `/workspace/Formosan-Poinsot-Amis-Dictionary`.

## What the repo did (as audited)

A clean, well-documented converter (`make formosanbank`): `fetch_sources.py` pins
three upstream repos by SHA → `build_formosanbank_xml.py` extracts examples →
a bespoke `validate_formosanbank_xml.py` + `audit_source_coverage.py`. Two
sentence-level outputs (no W/M), built from two of the three g0v moedict
dictionaries (Virginia Fey `docs/p` excluded as already processed):

- **Poinsot/Pourrias** (`docs/m` / `miaoski/amis-francais`): 23 Amis–French examples.
- **Safolu / Tsai 蔡中涵** (`docs/s`): 48,914 Amis–Chinese examples, 505 rejected.

Data-touching transformations reviewed: `clean_text` (collapse whitespace, strip
XML-invalid chars), `clean_moedict_link_markup` (delete `` ` ``/`~` markup,
de-space before punctuation), `recover_form_from_translation` (split empty-FORM
rows), `clean_poinsot_form` (strip surrounding quotes). The `original` tier uses
ASCII apostrophe for the glottal stop — no curly-quote loss (concern a clear).

## Findings by concern

### (d) Source-extraction completeness — the headline issues

**Poinsot was capped at 23 by inheriting an upstream bug.** Upstream
`amis-francais/moedict.py` hardcodes `for i in range(1, 3)` — it only ever read
`txt/001-002`. The repo faithfully replicated that. But the dictionary is **353
crowd-proofread pages**; the SOURCE_AUDIT claim that the rest is "OCR or partially
edited text" is only half true:
- **Pages 001–004** are clean line-per-entry text. Parsing all of them yields
  **36** example pairs (+13: e.g. `Fagcalay 'Adigo` → "Esprit Saint") and **144**
  headword→definition lexicon entries.
- **Pages 005–353** are reflowed OCR: entries run together on one line with inline
  `-`/`=`/`.` delimiters and **2,315 Chinese proofreader placeholders**
  (`[這是空白]`, `[圖片不清楚]`). Not cleanly parseable — an OCR-correction project.
- The original "coverage audit proves nothing is unaccounted" guarantee was scoped
  to the artificial 2-page window — false confidence about completeness.

**Original scans exist** for OCR correction: `miaoski/amis-francais` ships
`pic/001–353` (page scans), `hocr/001–353` (Tesseract hOCR), and the crowd-proofread
`txt/` — all aligned per page.

**Safolu rejected 505 rows, ~487 of which were recoverable.** The converter
imposed a "must have FORM and TRANSL" rule **stricter than FormosanBank's schema**
(`S_Type` is `xs:choice minOccurs="0"` — TRANSL is optional):
- **447** rows had a clean Amis FORM but no translation → valid FORM-only sentences,
  wrongly rejected (410 multiword).
- **56** `empty_form` rows had the Amis embedded in a Chinese note via `` `…~ ``
  markup; the old recovery bailed whenever the field started with CJK.
- **17→14** of the 187 *already-recovered* rows were **mis-split** to a stray `(`
  because recovery stripped `〔…〕` but not `(…)`/`（…）` loanword annotations.

### (b) Suppressed punctuation / markup
`clean_moedict_link_markup` deletes all `` ` ``/`~` (Moedict link markup — correct)
but doing so *before* recovery is what hid the embedded Amis in the 56 `empty_form`
rows; the fix runs recovery on the raw field. De-spacing before punctuation is
acceptable normalization on the example fields.

### (c) Convention breaks
- **Missing `TEXT/@dialect`** (HARD V036). Hunter's own validator never checked it.
- **No `standard` tier** — expected at dev stage (QC `standardize.py --copy`).
- **Reproducibility break**: build wrote `Final_XML/<Source>/` but committed files
  were hand-moved to `Final_XML/Amis/<Source>/`, and `make validate` pointed at the
  non-`Amis/` path — so `make` did not reproduce the committed tree.

### (a) Orthography
No dropped orthography characters found. Pre-existing source noise (smart quotes,
zero-width chars: validate_text V127/V131, 50 HARD) is **not** introduced by the
build and is left for the QC `clean_xml.py` step. Confirmed 0 of these are in
recovered/added rows.

## Remediation performed (with maintainer sign-off)

### Safolu (`Formosan-Safolu-Amis-Dictionary`, fixed in place)
- Generalized annotation stripping → fixes the **14** mis-split rows.
- Added high-precision embedded-note recovery → **+32** clean rows.
- Stopped rejecting FORM-only rows → **+447** valid Amis sentences.
- Result: **48,914 → 49,393** sentences; rejected **505 → 26**. Coverage conserved
  (49,393 + 26 = 49,419). `validate_xml`/coverage green; only expected SOFT findings.
- Added `dialect="unknown"`; aligned all paths to `Final_XML/Amis/<Source>/`
  (build + audit + Makefile) so `make` reproduces the committed layout; relaxed the
  repo's own validator to allow FORM-only `S`.

### Poinsot (split into new repo `Formosan-Poinsot-Amis-Dictionary`)
- Extended parsing to all 353 pages → **36** examples; added a separate
  **`amis_poinsot_lexicon.xml`** (144 headword→French entries) with quality guards
  that route reflowed-page debris to a rejected audit instead of the XML.
- Moved into its own dev repo (own `build_poinsot_xml.py`, `fetch_sources.py`
  fetching the full amis-francais incl. scans/hOCR, coverage audit, Makefile,
  README, git history) so the **349 reflowed pages remain an OCR-correction
  worklist without blocking Safolu publication**. Builds + validates green.

## Remaining before porting either corpus into `Corpora/`
1. Set the real `TEXT/@dialect` (currently `unknown`) for both corpora via the
   FormosanBank dialect detector.
2. Run the standard QC pipeline (`clean_xml.py` for the pre-existing smart-quote/
   zero-width noise, `standardize.py --copy` to create the standard tier, then the
   validators).
3. Poinsot only: decide whether to invest in OCR-correcting pages 005–353 against
   the scans before publishing, or publish the clean 4-page subset first.

## Status of changes
- `Formosan-Safolu-Amis-Dictionary` (renamed from `Formosan-Amis-Moedict`):
  remediation committed and pushed; the GitHub repo was renamed accordingly.
- `Formosan-Poinsot-Amis-Dictionary`: created, committed, and pushed to FormosanBank/Formosan-Poinsot-Amis-Dictionary.

## Update — 2026-06-14 (post-audit work)
- **CJK-in-FORM cleanup** (the source packed `Amis 中文` content into the form
  slot): single-glued pairs and `；`-separated lists are split into one `S` per
  pair; unsplittable/pure-Chinese fields rejected; a straddling `（…）` annotation
  and orphaned leading `)` repaired. New totals: **49,400 sentences / 44 rejected**
  (all 49,419 source fields accounted at the source-field level).
- **Stable source-ordinal IDs** for Safolu (and page+line IDs for Poinsot) so
  regenerations diff cleanly instead of renumbering every row.
- **QC pipeline run** on Safolu (Ortho113): `clean_xml → standardize --copy →
  clean_xml → add_phonology`, wired as `make qc` + documented in the README. Adds
  the standard tier + IPA `PHON`. `validate_xml` clean; `validate_text` 0 HARD.
- **Perf fix (FormosanBank tool):** `QC/utilities/add_phonology.py` was O(n²)
  (re-scanned the whole tree per FORM); replaced with a one-time parent map
  (~33 min → ~1 s on 49k sentences).
- `Tsai, Chung-Han (Safolu Kacaw Lalanges)` corrected to a single author in the
  citation/BibTeX.

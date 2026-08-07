# Song Limei (2018), *Introduction to Kanakanavu Grammar*

The Kanakanavu (`xnb`) corpus drawn from Song
Limei's 2018 *Kanakanafu yu yufa gailun* [Introduction to Kanakanavu Grammar]
(Taiwan nandao yuyan congshu 16; Council of Indigenous Peoples), scraped from the
official Alilin e-reader. It produces two files in the
[FormosanBank XML format](https://ai4commsci.gitbook.io/formosanbank/the-bank-architecture/formosanbank-xml-format):
the grammar's interlinear examples and the Appendix 2A dictionary.

## Rights and permissions

The author (Li-May Sung) granted permission to publish this corpus under
**CC BY-NC 4.0** (Creative Commons Attribution–NonCommercial); the permission
evidence is on Basecamp card
[`10081339846`](https://app.basecamp.com/3340659/buckets/31258415/card_tables/cards/10081339846).
Each `<TEXT>` element's `copyright` attribute records this license. Attribution
and non-commercial use are required; see the FormosanBank
[LICENSE](../../LICENSE.md) and [AI-USE-ADDENDUM](../../AI-USE-ADDENDUM.md).

## What's in the corpus

| | Grammar | Dictionary (Appendix 2A) |
|---|---|---|
| File (under `XML/Kanakanavu/`) | `Song_2018_Kanakanavu_Grammar.xml` | `Song_2018_Kanakanavu_Grammar_Dictionary.xml` |
| `S` elements | 699 sentences | 870 entries |
| Interlinear analyses | 650 (with `W`/`M`) | — |
| Words / morphemes | 3,477 `W` / 5,034 `M` | — |

Language `xnb` (Kanakanavu); dialect `Kanakanavu`; orthography Ortho113.

## Project structure

- **`XML/Kanakanavu/`** — the published data: `Song_2018_Kanakanavu_Grammar.xml` and `Song_2018_Kanakanavu_Grammar_Dictionary.xml`.
- **`CodeAndDocs/`** — everything needed to reproduce `XML/` from the source:
  - `scripts/` — acquisition and the reproduction pipeline (see [Processing](#processing)).
  - `raw_data/` — the acquired source, retained so the corpus rebuilds without re-scraping: `source.pdf` (the 268 official Alilin page images compiled in order) and `official_text.jsonl` (the official positioned-text layer, one record per page). Both SHA-256-pinned in `scripts/build_xml.py`.
  - `intermediate/` — the reviewed ledgers the build consumes (all hash-pinned in `build_xml.py`): `page_inventory.csv` + `candidate_ledger.csv` (the closed page/candidate review — 268 pages, 443 machine candidates, all with terminal statuses); `source_ledger.csv` (699 included, 14 excluded, with reasons); `dictionary_ledger.csv` (767 headwords; 11 marked bound-excluded); `interlinear_ledger.jsonl` (the recovered `W`/`M` analyses); and `standard_surface_decisions.tsv` (128 exact, source-reviewed standard-tier decisions).
  - `docs/` — `extraction_plan.md`, `extraction_review.md` (the page-by-page review log), `source_manifest.md`, `standard_surface_review.md`, `clean_clone_reproduction.md`.
  - `tests/` — interlinear-extraction regression tests.
  - `requirements.txt`.

## Reproduction

The reviewed ledgers and raw source are retained under `CodeAndDocs/`, so a
rebuild does **not** re-scrape. Point `FORMOSANBANK_PATH` at a clean FormosanBank
checkout at the commit pinned as `EXPECTED_FORMOSANBANK_COMMIT` in
`CodeAndDocs/scripts/rebuild_final_xml.sh` (a *separate* checkout, since the
script asserts that tree is clean), then, from `CodeAndDocs/`:

```bash
cd CodeAndDocs
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
FORMOSANBANK_PATH=/path/to/clean/FormosanBank scripts/rebuild_final_xml.sh
```

The rebuild writes the regenerated corpus to `CodeAndDocs/Final_XML/`; compare it
against the published `XML/` to confirm reproduction.

`rebuild_final_xml.sh` asserts the FormosanBank checkout is clean and at the
pinned commit (before and after), and `build_xml.py` asserts the
source-PDF/positioned-text hashes, the closed page/candidate inventory, the
reviewed-artifact hashes, the ledger counts, and continuous sentence IDs — so any
drift in the source or the ledgers fails the build loudly.

## Processing

### Upstream (one-time; the outputs are committed, so you do not re-run these)

**A. Acquire the source** — `scripts/acquire_source.py` downloads every numbered
Alilin page image and its `iPhone/text/<page>.xml` positioned-text record,
verifies the page count, compiles the images into `raw_data/source.pdf`, and
writes `raw_data/official_text.jsonl`. The **page images are authoritative**; the
positioned text is a reading aid only.

**B. Build machine candidates** — `scripts/build_candidates.py` scans the
positioned text for labeled examples and writes `page_inventory.csv` +
`candidate_ledger.csv` (all `UNREVIEWED`).

**C. Human review** (the heart of the corpus) — every one of the 268 pages was
reconciled by hand against the page image: expanding/repairing machine
candidates, recovering examples that had no candidate, restoring word boundaries
and punctuation the text layer had dropped, and excluding non-sentences. The
result is `source_ledger.csv` (699 included, 14 excluded). The full page-by-page
log is `docs/extraction_review.md`.

### Rebuild pipeline (`CodeAndDocs/scripts/rebuild_final_xml.sh`)

1. **Extract the dictionary** — `extract_dictionary.py` reconstructs Appendix 2A
   from the positioned text, cross-checking barred vowels against the duplicate
   Chinese-sorted Appendix 2B and applying documented OCR corrections →
   `dictionary_ledger.csv`.

2. **Verify barred-vowel reconciliation** — `reconcile_barred_vowels.py --check`
   confirms the `u`/`ʉ` corrections between the sentence ledger and the dictionary
   are consistent (fails if they have drifted).

3. **Recover interlinear analyses** — `extract_interlinear.py` aligns each
   reviewed sentence's printed word and gloss lines into `W`/`M` analyses (650
   analyses; 3,477 `W`; 5,034 `M`), using position-based alignment plus
   source-checked overrides for cells the text layer merged →
   `interlinear_ledger.jsonl`. W forms keep the source's `-`, `=`, and `<…>`
   notation; M forms drop affix/infix apparatus but keep the aligned clitic `=`.

4. **Build the XML** — `build_xml.py` writes both files (after asserting all
   hashes/counts):
   - **Grammar:** 699 `S`; the 650 with a printed analysis get `W`/`M`. Two
     sentences (5-2 and footnote 27) have a translation but no printed word gloss,
     so they carry no analysis.
   - **Dictionary:** the 767 headwords become **870 single-form `S` entries**.
     Slash (`/`), semicolon (`;`), and optional `(…)` variants are split into
     separate entries *before the standard tier is copied* — 114 headwords split,
     adding 140 entries; multi-variant headwords get `a`/`b`/`c`-suffixed IDs
     (e.g. `dictionary-0006a`), share the TRANSL, and note the printed apparatus
     on the original tier. 26 split variants whose (form, translation) duplicate
     another record are dropped (the source prints those forms as their own
     records). The 11 bound citation forms (trailing `-`, e.g. `ara-`, `'ap(a)-`)
     are excluded — no free-standing surface exists. There is **no `alternate`
     tier**, and every (form, translation) pair is unique.

5. **Re-apply manual edits** — `apply_manual_edits.py` (FormosanBank) re-applies
   any recorded hand edits first; a no-op here (no `CodeAndDocs/manual_edits.xml`).

6. **Clean** — `clean_xml.py` (FormosanBank) does canonical Unicode / HTML-entity
   / punctuation normalization.

7. **Create the standard tier** — `standardize.py --copy` (FormosanBank). The
   source is already Ortho113, so standardization is an identity copy of the
   original tier.

8. **Apply reviewed surface decisions** — `normalize_standard_forms.py` applies
   the 128 exact decisions in `standard_surface_decisions.tsv` to the standard
   tier (no marker is removed by a blanket rule): the dictionary's per-variant
   standard forms, the two break-punctuation sentences (S0469/S0472, rendered as a
   dash), the song's lyric segmentation resolved with independently attested word
   boundaries, the bound-form standard omissions, and the `takananga` standard
   correction (see Notes). Ordinary prose parentheses are left unchanged.

9. **Fold stress accents** — `fold_standard_stress.py` folds acute-accented vowels
   (`á é í ó ú`, and the decomposed `ʉ́`) to their base vowel **in the standard
   tier only**; the original tier keeps the printed stress. Stress is
   suprasegmental annotation in this source, not Ortho113 orthography.

10. **Add phonology** — `add_shared_phonology.py` delegates both tiers to
    FormosanBank's shared `add_phonology.py` (Ortho113). For the original-tier PHON
    it feeds a *temporary* stress-folded copy, so the PHON is clean IPA while the
    original FORM is restored byte-for-byte. There is no corpus-specific phonology
    mapping.

## Notes / user beware

- **Orthography is Ortho113.** Detector and reviewer evidence agree: the source
  uses `ʉ` and `r`, has no `l` (its own discussion notes `r` covers the former
  `l`/`r` contrast), and maps `r` → `r~ɾ`. Against the Kanakanavu reference,
  character-frequency cosine is 1.00 and bigram cosine 0.99.
- **Stress accents** (`á í ú …`) are kept in the original tier and folded in the
  standard tier (step 9); PHON is accent-free on both tiers.
- **Dictionary variants:** slash/semicolon alternatives and optional `(…)`
  material are materialized into separate single-form entries; bound prefixes
  (trailing `-`) are excluded; cross-record duplicate variants are dropped.
  Nothing is deleted by a blanket rule — every exclusion is a recorded decision
  (`dictionary_ledger.csv` exclusions and `standard_surface_decisions.tsv`).
- **`takananga` (p.69):** the printed analysis line's OCR reads `takanaga` (a bare
  `g`, which is not an Ortho113 letter) where the sentence surface has
  `takananga`. The printed `takanaga` is kept in the original `W`/`M` tier and
  corrected to `takananga` only in the standard tier.
- **Excluded sentences (14):** 6 noun-phrase fragments, 5 source-starred
  ungrammatical forms, and 3 examples with no printed Chinese translation. See
  `source_ledger.csv`.
- **Rights:** published under CC BY-NC 4.0 by permission of the author (Li-May Sung); recorded in each `<TEXT>` `copyright` attribute.

## QC

Adjudication of the reviewed surface decisions is in
`CodeAndDocs/docs/standard_surface_review.md`. QC evidence is regenerated on
demand by running FormosanBank's validators (`validate_xml`, `validate_text`,
`validate_glosses`) against `XML/`. All canonical hard gates pass; the remaining
findings are expected SOFT diagnostics — ordinary prose parentheses, the
deliberate break-punctuation dash, and the `W`-count-vs-word-count gloss noise
(a clitic counts as one `W`).

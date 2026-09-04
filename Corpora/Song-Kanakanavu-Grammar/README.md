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
| Words / morphemes | 3,477 `W` / 5,048 `M` | — |

Language `xnb` (Kanakanavu); dialect `Kanakanavu`; orthography Ortho113.

## Project structure

- **`XML/Kanakanavu/`** — the published data: `Song_2018_Kanakanavu_Grammar.xml` and `Song_2018_Kanakanavu_Grammar_Dictionary.xml`.
- **`CodeAndDocs/`** — everything needed to reproduce `XML/` from the source:
  - `scripts/` — acquisition and the reproduction pipeline (see [Processing](#processing)).
  - `raw_data/` — the acquired source, retained so the corpus rebuilds without re-scraping: `source.pdf` (the 268 official Alilin page images compiled in order) and `official_text.jsonl` (the official positioned-text layer, one record per page). Both SHA-256-pinned in `scripts/build_xml.py`.
  - `intermediate/` — the reviewed ledgers the build consumes (all hash-pinned in `build_xml.py`): `page_inventory.csv` + `candidate_ledger.csv` (the closed page/candidate review — 268 pages, 443 machine candidates, all with terminal statuses); `source_ledger.csv` (699 included, 14 excluded, with reasons); `dictionary_ledger.csv` (767 headwords; 11 marked bound-excluded); `interlinear_ledger.jsonl` (the recovered `W`/`M` analyses); and `standard_surface_decisions.tsv` (128 exact, source-reviewed standard-tier decisions).
  - `docs/` — `extraction_plan.md`, `extraction_review.md` (the page-by-page review log), `source_manifest.md`, `standard_surface_review.md`, `mt_quality_review.md`, and `clean_clone_reproduction.md`.
  - `tests/` — interlinear-extraction regression tests.
  - `requirements.txt`.

## Reproduction

The reviewed ledgers and raw source are retained under `CodeAndDocs/`, so a
rebuild does **not** re-scrape. One command rebuilds the published `XML/` from
them:

```bash
CodeAndDocs/scripts/make_xml.sh
```

That is the corpus's only entry point; it runs every step below in order and
writes the two files in `XML/Kanakanavu/` in place, so `git diff` shows exactly
what a rebuild changes. It uses the FormosanBank checkout that contains this
corpus for the shared QC utilities (pass a path, or set `FORMOSANBANK_PATH`, to
use another one) and `python3` unless `PYTHON` names an interpreter. The
dependencies are in `CodeAndDocs/requirements.txt`:

```bash
python3 -m venv CodeAndDocs/.venv
CodeAndDocs/.venv/bin/pip install -r CodeAndDocs/requirements.txt
```

`build_xml.py` asserts the source-PDF/positioned-text hashes, the closed
page/candidate inventory, the reviewed-artifact hashes, the ledger counts, and
continuous sentence IDs — so any drift in the source or the ledgers fails the
build loudly. `make_xml.sh` records the FormosanBank commit the published XML
was last built against and notes it when the checkout differs. The rebuild is
deterministic: running it twice reproduces the same bytes.

`CodeAndDocs/tests/` holds the extraction regression tests, which also check the
published XML; run them with `pytest` from `CodeAndDocs/`.

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

### Rebuild pipeline (`CodeAndDocs/scripts/make_xml.sh`)

1. **Extract the dictionary** — `extract_dictionary.py` reconstructs Appendix 2A
   from the positioned text, cross-checking barred vowels against the duplicate
   Chinese-sorted Appendix 2B and applying documented OCR corrections →
   `dictionary_ledger.csv`.

2. **Verify barred-vowel reconciliation** — `reconcile_barred_vowels.py --check`
   confirms the `u`/`ʉ` corrections between the sentence ledger and the dictionary
   are consistent (fails if they have drifted).

3. **Recover interlinear analyses** — `extract_interlinear.py` aligns each
   reviewed sentence's printed word and gloss lines into `W`/`M` analyses (650
   analyses; 3,477 `W`; 5,048 `M`), using position-based alignment plus
   source-checked overrides for cells the text layer merged →
   `interlinear_ledger.jsonl`. W forms keep the source's `-`, `=`, and `<…>`
   notation. Under POL-014, an infixed root keeps a gap hyphen and the infix is
   written `-X-`; under POL-015, each clitic M keeps a leading `=`. Two override
   tables in that script carry every analysis the positional aligner cannot
   derive, each keyed by record id and each citing its reader page:
   `ANALYSIS_OVERRIDES` (gloss/segment pairings the text layer merged) and
   `MORPHEME_OVERRIDES` (five page images whose printed form and gloss lines do
   not align one-to-one, preserving partial source glossing without inventing
   missing M glosses). Both are applied to the **original** tier at extraction,
   before any standard tier exists — see "Recorded per-record corrections" under
   Notes for the full list.

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
   the recorded hand edits in `CodeAndDocs/manual_edits.xml` before any cleaning
   or derivation, so every downstream tier is built from the repaired original.
   One record: the p.69 `takananga` typesetting slip (see Notes). The script
   warns loudly if a record has become a no-op.

6. **Clean** — `clean_xml.py` (FormosanBank) does canonical Unicode / HTML-entity
   / punctuation normalization.

7. **Create the standard tier** — `standardize.py --remove_accents`
   (FormosanBank). The source is already Ortho113, so no conversion table is
   needed; `--remove_accents` copies the original tier and folds the source's
   acute stress vowels (`á é í ó ú`, and the decomposed `ʉ́`) out of the
   standard tier only. Stress is suprasegmental annotation in this source, not
   Ortho113 orthography, so the original tier keeps the printed accents.

8. **Apply reviewed surface decisions** — `normalize_standard_forms.py` applies
   the 128 exact decisions in `standard_surface_decisions.tsv` to the standard
   tier (no marker is removed by a blanket rule): the dictionary's per-variant
   standard forms, the two break-punctuation sentences (S0469/S0472, rendered as a
   dash), the song's lyric segmentation resolved with independently attested word
   boundaries, the bound-form standard omissions, and the `takananga` standard
   correction (see Notes). Ordinary prose parentheses are left unchanged.

9. **Add phonology** — `add_phonology.py --orthography Ortho113`
   (FormosanBank), both tiers. PHON is a segmental tier, so the shared utility
   folds stress accents itself before mapping; the original FORM keeps its
   accents and the PHON is clean IPA. There is no corpus-specific phonology
   mapping and no corpus-specific wrapper.

## Notes / user beware

- **Orthography is Ortho113.** Detector and reviewer evidence agree: the source
  uses `ʉ` and `r`, has no `l` (its own discussion notes `r` covers the former
  `l`/`r` contrast), and maps `r` to the IPA variants `r` and `ɾ`. The current
  detector selects Ortho113 for both XML files.
- **Stress accents** (`á í ú …`) are kept in the original tier and folded in the
  standard tier (step 7); PHON is accent-free on both tiers.
- **Dictionary variants:** slash/semicolon alternatives and optional `(…)`
  material are materialized into separate single-form entries; bound prefixes
  (trailing `-`) are excluded; cross-record duplicate variants are dropped.
  Nothing is deleted by a blanket rule — every exclusion is a recorded decision
  (`dictionary_ledger.csv` exclusions and `standard_surface_decisions.tsv`).
- **`takananga` (p.69) — a typesetting slip in the book, repaired in the
  original tier.** Reader p.69 example 4-9 prints `takananga` in its sentence
  line and `takanaga` one line below in its own aligned analysis. Confirmed
  against the page image, so this is what the book prints, not a scraping
  artifact. The reading is not in doubt: `takananga` occurs 22× across the
  corpus — including in that same example's sentence line — while `takanaga`
  occurs exactly twice, both inside that one analysis. The bare `g` is also not
  an Ortho113 letter, so before the repair it had no phonological mapping and
  surfaced as `*` in the original PHON. The repair is a recorded manual edit
  (`CodeAndDocs/manual_edits.xml`, applied by the shared
  `apply_manual_edits.py` at build step 5) to the **original** tier; the
  standard tier and both PHON tiers regenerate from it. The extraction ledgers
  still record exactly what the page prints.

### Recorded per-record corrections

Everything below is applied by name to a specific record, never by a blanket
rule, and each entry names the reader page it was checked against. Nothing else
in the corpus is hand-corrected.

**Applied to the `original` tier at extraction** (`extract_interlinear.py`,
step 3 — before any standard tier exists):

| Record | Reader page | What the source prints | What is recorded |
| --- | --- | --- | --- |
| `S0318` W3 | 156 (ex. 13-2a) | `t<in>i-taini`, gloss `重疊<完成貌>丟` | M `t-i` 重疊 · `-in-` `<完成貌>` · `taini` 丟 |
| `S0422` W2 | 182 (ex. 15-8a) | `m-ukʉrʉ`, one whole-word gloss `拿著` | M `m` · `ukʉrʉ`, **both without an M gloss** |
| `S0609` W15 | 243 (narrative 26) | `ka-cangcangarʉ-a`, gloss `處在-重疊-快樂-關係詞` | M `ka` 處在- · `cangcangarʉ` 重疊-快樂- · `a` 關係詞 (no boundary is printed inside `cangcangarʉ`, so its two gloss units stay grouped) |
| `S0636` W5 | 248 (narrative 53) | `pa-arivivini-ʉn`, gloss `使動-跟隨在後` | M `pa` 使動- · `arivivini` 跟隨在後 · `ʉn` **without an M gloss** |
| `S0678` W6 | 258 (narrative 38) | `t<um>a-túturu`, gloss `<主事焦點>-告知` | M `t-a` **without an M gloss** · `-um-` `<主事焦點>-` · `túturu` 告知 |

`ANALYSIS_OVERRIDES` in the same script covers gloss/segment pairings the
e-reader's text layer merged; it is likewise keyed by record id with the page
cited in place.

**Applied to the `original` tier as a recorded manual edit**
(`CodeAndDocs/manual_edits.xml`, step 5) — the shared mechanism for repairing
an error in the original, from which every derived tier regenerates:

| Record | Reader page | Printed | Recorded |
| --- | --- | --- | --- |
| `S0012` W4 + its host M | 69 | `takanaga=kasu` / `takanaga` | `takananga=kasu` / `takananga` |

**Applied to the `standard` tier only** (`normalize_standard_forms.py`, step 8).
Just one, and only because the original must stay faithful to the printed page
(POL-001) while the standard tier carries running words:

| Record | Reader page | `original` keeps | `standard` gets |
| --- | --- | --- | --- |
| `S0477` | 190 | the lyric-division hyphens exactly as printed | `mati'ara'aravang 'aa 'aravang vatu 'aravang vatu! tisa'ʉ ku 'apasʉ.` |

Reader p.190's punctuation table (Appendix 1, row 10, 連結號) defines that
hyphen as a *song* mark — it breaks lyrics to fit the musical score, not
morphemes. Deleting the hyphens is not enough to recover words: the printed
`ti-sa-'ʉku-'a-pa-sʉ` would collapse to a single `tisa'ʉku'apasʉ`, where the
attested reading is three words. The boundaries come from an independent
attestation of the same song, pinned by commit and SHA-256 in
`docs/standard_surface_review.md`.

The other two grammar decisions (`S0469`, `S0472`) change no text at all. Row 8
of the same p.190 table defines `--` as the halfwidth spelling of 破折號, the
em dash whose fullwidth Chinese equivalent is `―`; `build_xml.py` renders it as
a single `-` in the **original** tier, so the standard tier inherits it
unchanged and the decision rows only attach a `notes` string. (This is why
`validate_text` reports two V133 `-`-in-standard findings: the mark is
punctuation, but it is spelled like a segmentation hyphen.)

The dictionary's 125 remaining decisions in `standard_surface_decisions.tsv`
change nothing at this step: `build_xml.py` has already emitted one clean
surface per entry, and step 8 only *verifies* that state.
- **Partial morpheme glossing:** reader pages 182, 248, and 258 print segmented
  forms without a separately aligned gloss for every unit. Their W glosses are
  preserved exactly, while four M elements intentionally omit `TRANSL` rather
  than receiving inferred labels.
- **Excluded sentences (14):** 6 noun-phrase fragments, 5 source-starred
  ungrammatical forms, and 3 examples with no printed Chinese translation. See
  `source_ledger.csv`.
- **Repeated surface forms (63 groups, 130 `S`):** 34 dictionary groups are
  homographs with different translations, one preserves two original stress
  variants that fold to the same standard form, and 28 grammar groups repeat at
  distinct source locators. There is no exact or same-locator duplicate.
- **Words without a morpheme analysis (2 of 3,477 `W`):** pages 68 and 128 print
  one whole-word gloss for `m-u'iara` and `ma-marang`. The words carry no `M`
  children rather than an invented segmentation.
- **Rights:** published under CC BY-NC 4.0 by permission of the author (Li-May Sung); recorded in each `<TEXT>` `copyright` attribute.

## QC

Adjudication is recorded in `CodeAndDocs/docs/standard_surface_review.md`,
`CodeAndDocs/docs/mt_quality_review.md`, and
`CodeAndDocs/docs/clean_clone_reproduction.md`. The current update-view XML
validator has no finding, the gloss validator has no HARD finding, all 63
duplicate groups are source-supported, and port readiness reports 0 HARD and 0
WARN. The remaining text and gloss SOFT rows are documented source properties.

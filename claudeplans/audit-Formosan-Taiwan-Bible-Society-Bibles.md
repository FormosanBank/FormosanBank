# Dev-repo audit — Formosan-Taiwan-Bible-Society-Bibles

**Date:** 2026-06-12
**Auditor:** Claude (audit-dev-repo skill), with maintainer sign-off at each checkpoint
**Repo:** `../Formosan-Taiwan-Bible-Society-Bibles/` (dev repo; not yet ported)
**Source:** FHL / Taiwan Bible Society Bible Tools (https://cb.fhl.net/, https://bible.fhl.net/json/)
**Scope:** 9 languages, 509 XML files, 219,043 `<S>` (verses).
Amis (ami), Atayal (tay), Bunun (bnn), Puyuma (pyu), Rukai (dru), Seediq+Truku (trv),
Tsou (tsu), Yami (tao).

> **Permission note:** the README states the extracted Bible text/XML must not be
> published without further authorization from the project owner and rights holders.
> This audit reads the data locally only.

---

## 1. What Hunter built (preprocessing summary)

A fully scripted FHL→FormosanBank pipeline (`scripts/`, run in this order):

1. `discover_versions.py` / `fetch_books.py` / `fetch_verses.py` — download version
   metadata and per-chapter JSON from the FHL API. Pure I/O, no transformation.
2. `parse_api.py` (+ `parse_html_fallback.py`) — extract verse records. **Every**
   verse (Formosan, Mandarin, English alike) passes through one cleaning function,
   `common.normalize_source_text()` — the only character/content-altering step.
3. `build_parallel.py` — join Formosan/zh/en by `(book, chapter, verse)`. No text mutation.
4. `build_formosanbank_xml.py` — emit XML: one `<S>` per verse, `FORM kindOf="original"`
   = cleaned Formosan text, plus at most one Mandarin (`tcv2019`) and one English (`kjv`)
   `<TRANSL>`; withholds risky translations (keeps the Formosan verse).
5. `validate_formosanbank_xml.py` / `generate_reports.py` — his own (weaker) validator
   and reports.

### `normalize_source_text()` — the cleaning core (`common.py:445`)

Applied to the Formosan **original** tier as well as the translations. In order:

- Remove HTML section headings `<h1-6>…</h1-6>` (+ a `STRAY_TRAILING_HEADING` rule that
  deletes a trailing heading tag **plus up to 160 following chars**, and an
  empty-heading-followed-by-label rule).
- Remove cross-references `（#…|）`, FHL footnotes `<RF>…<Rf>` / `<FO>…<Fo>`, Strong's/KJV
  markup (`FI/CM/WH#/WG#`), `<br>`→space, strip `<b>/<u>/<font>`.
- **Delete "numbered source notes"** (`NUMBERED_SOURCE_NOTE_RE`): a parenthetical span of
  **up to ~1000 chars**, gated by a lookahead listing hardcoded Formosan words
  (`Hibur, Patas, qtai, pnaah, smdalih, Wadulru…`).
- **Delete Rukai bracket notes** (`RUKAI_BRACKET_SOURCE_NOTE_RE`, a `.*?` span) and **any
  isolated `(chap:verse)` reference** (`ISOLATED_SOURCE_REF_RE`).
- Delete Chinese translator notes (zho only).
- `html.unescape` → NFC normalize → strip XML-forbidden control chars → collapse
  newlines/`\xa0`/runs of spaces → strip.

Verses whose cleaned text is the FHL placeholder `無經文` (no scripture), `併於上節`
(merged into previous verse), or a single stray letter are **excluded** from the XML
(`marker_info` / `is_actual_text`).

---

## 2. Pipeline mapping (his step → ours)

| His step | Our equivalent | Verdict |
|---|---|---|
| html.unescape / NFC / control-char / whitespace collapse | `clean_xml.py` | We do this; harmless to redo |
| Strip FHL markup, `<h>`, footnotes | none (source-specific) | Legitimately his job |
| `STRAY_TRAILING_HEADING` (+160 chars) | none | Risk — verified, does not fire in practice |
| `NUMBERED_SOURCE_NOTE` (≤1000 chars) | none | Deletion on faithful tier; spot-checks correct |
| `RUKAI_BRACKET` / `ISOLATED_SOURCE_REF` | none | Deletion on faithful tier; verified correct (Rukai) |
| Chinese translator-note strip | none | zho-only, no-op for Formosan |
| Exclude `無經文`/`併於上節`/single-letter | (we'd keep all S) | Sound — excludes placeholder verses |
| `FORM kindOf="original"` only | two-tier; `standardize.py --copy` | Expected; `standard` tier added later |
| Dialect from hardcoded map (Chinese strings) | `dialects.csv` canonical | **Conflict** — see (c) |
| TRANSL `kindOf` hand-edited post-build | TRANSL `kindOf` optional | **Reproducibility gap** — see (c) |
| Withhold translations by length/markup heuristics | none | Conservative; keeps Formosan |
| Align zho/eng by shared verse key | — | Correct here (single source) — see (e) |

---

## 3. Findings by concern

Validator artifacts (run against `Final_XML/`):
`validate_xml` → 509/509 files with issues; `validate_text` → 487/509.
CSVs: `/tmp/bibles-qc/validate_xml.csv`, `/tmp/bibles-qc/validate_text.csv`,
orthography extract `/tmp/bibles-qc/extract/`.

### (a) Eliminated orthography characters — **NOT FOUND**
- No letter-level substitution exists anywhere in his code.
- Orthography validator could meaningfully run on **Tsou** and **Yami**:
  character-frequency **cosine 0.99** vs reference; the flagged set-disjunction
  (Jaccard 0.70/0.67) is driven by *extra* punctuation (`<>` quotes, smart quotes,
  fullwidth `！`, `…`, diacritics `í á ó é`), **not missing letters**. Tsou barred-`ʉ`
  and the glottal `'` are all present.
- Truku/Seediq/Rukai could **not** be compared: the extract's dialect folders are
  Chinese-named (`太魯閣語`, `德固達雅賽德克語`) and don't match `reference/<Language>/`.
  This is a downstream symptom of the dialect bug (c), not an orthography loss.

### (b) Suppressed punctuation — **mostly faithful; two items**
- The editorial strips (HTML, FHL footnotes, `(#…|)` cross-refs, source/translator
  notes) work correctly on every sample checked. Verified live: Truku Mark 1:1 raw
  `<h2>Gmarang Kari ka Yuhani Ptgaya Sminaw</h2>(#Maruku 3:1-12; …|)<br/> Malu kari laqi
  Utux Baraw ( 1 Duma patas qniri smudal…` → clean `Malu kari laqi Utux Baraw Yisu
  Kiristu o saw nii ka pnrjingan na.` (a complete verse; note correctly removed).
- **High-risk regexes verified (targeted, live re-fetch):**
  - `STRAY_TRAILING_HEADING_RE` (+160 chars): **fired on 0 of ~60 sampled chapters.**
    Headings come closed (`<h2>…</h2>`); the unclosed-trailing case is essentially
    theoretical. No over-deletion realized.
  - `RUKAI_BRACKET_SOURCE_NOTE_RE` (`.*?`): correct in 6/6 sampled firings — removes
    textual-variant footnotes (e.g. `([1.1] …{<<ka Lalake ki Twaumase>>}…)`) and leaves
    the clean verse. The lazy span terminates correctly.
- **Over-deletion search (length-anomaly detector, `scripts/check_short_formosan.py`):**
  the silent failure modes are (i) the lazy terminator anchoring past the note's true end,
  and (ii) a false trigger from `NUMBERED_SOURCE_NOTE_RE`'s common-word gate (`kari`,
  `elug`, `madu` are ordinary vocabulary) — both leave a well-formed but truncated verse.
  Symptom = Formosan FORM short relative to its translation. The detector ranks the worst
  cases (translation/Formosan char-ratio outliers per version + the 215 translations Hunter
  withheld as "too long"); the **top 45 were re-fetched from FHL and re-cleaned — 44 had
  `removed=0`, and the one delta (`ams Ezra 8:2`, −10) was only `<br/>`/newline collapse,
  not content.** No realized over-deletion. (The false-trigger mechanism itself is real —
  reproduced on constructed input — but does not surface in the actual corpus.)
- **Open item — quote punctuation collides with our conventions:**
  - `<…>` / `<<…>>` used as **quotation marks** in source (Tsou, Amis, Rukai):
    **V134 ×106,539 (SOFT)** — collides with our reserved infix-segmentation `<…>`.
  - Smart quotes incl. U+2019: **V127 ×28,534 (HARD)** (4,180 `'` / 4,128 `'` /
    21,644 `"` / 20,092 `"`). These are faithful source quotation marks (confirmed:
    Truku Mark 1:2 nested speech `'…'`), not glottal stops (those use ASCII `'`).
  - **Maintainer decision: normalize `<…>` and smart quotes to proper/straight quotes
    in cleaning before porting.**

### (c) Convention breaks — **CONFIRMED, must-fix**
- **Dialect — every file fails `V036` (HARD ×509).** Two failure modes:
  - 7 of 9 languages (Amis, Bunun, Atayal, Tsou, Yami, Puyuma, generic Rukai) emit **no
    `dialect` attribute**.
  - The 2 that do use **Chinese strings**: `太魯閣語`, `德固達雅賽德克語`,
    `萬山/茂林/多納魯凱語`. `dialects.csv` expects canonical romanized values
    (`Truku`, `Tegudaya`, `Wanshan`, `Maolin`, `Dona`); single-dialect languages take
    the language name (`Tsou`, `Yami`). V036 message for Truku:
    `dialect='太魯閣語' is not valid for xml:lang='trv'; expected one of
    ['DeluValley','Duda','Tegudaya','Truku','unknown']`.
  - **Knock-on:** the `trv`+`Truku`→Truku counting rule (`corpus_counts.py`) will
    misclassify all 66 Truku Bibles as **Seediq**; and it blocks orthography comparison
    for trv/dru.
- **No `standard` tier** — `V014 ×219,043 (SOFT)`. Expected; `standardize.py --copy`
  fills it before orthography QC.
- **Reproducibility gap:** committed `Final_XML` has `<TRANSL>` with **no `kindOf`**
  (432,419 TRANSL, 0 with kindOf), but `build_formosanbank_xml.py:384/397` writes
  `kindOf="original"` on every TRANSL. The last commit ("fix kindOf elements")
  hand-edited the output; re-running the documented pipeline would re-add the attribute
  and not reproduce the committed tree. (FORM text **is** reproducible — verified
  byte-for-byte on Truku Mark 1:1.)

### (d) Source-extraction artifacts — **CONFIRMED, low-volume**
- **Footnote-digit leaks** — `V137 ×2,086 (SOFT)`: inline markers like `i1`, `a1`, and
  stray digits mid-verse (e.g. Truku John 3:16 FORM: "sbgay ka **1** laqi na").
  Untagged superscripts that slipped past the `<RF>/<FO>` strippers. Concentrated in the
  Amis-1997 (`ams`) text.
- **Asterisks** — `V129 ×102 (HARD)`: embedded disputed-passage/footnote markers
  (e.g. Mark 16:20). Not sentence-initial ungrammaticality markers (Bible text).
- **Discarded Formosan-language section headings** — 7/45 verses in Truku Mark 1 alone
  carried an editorial Formosan heading (`Gmarang Kari ka Yuhani Ptgaya Sminaw`, etc.)
  that is deleted. **Maintainer decision: keep deleting (editorial apparatus, not
  scripture).**

### (e) Versification / cross-translation alignment — **NO PROBLEM (tested)**
The Mandarin (`tcv2019`) and English (`kjv`) translations are aligned to the Formosan
purely by shared `(book, chapter, verse)` key. This is **correct here** because all
three versions come from one source (FHL) on **one master verse grid**. Evidence:
- **Acts 8:37** (a KJV-only verse): simply **absent** in the Formosan; its neighbors
  carry the correct KJV **8:36** and **8:38** English — no off-by-one shift.
- **Psalm superscriptions** (the systematic offset case): folded into v1 uniformly
  across all three. Ps 3:1 Formosan/zho = "how many enemies" = KJV 3:1; Ps 51:1 =
  "have mercy" = KJV 51:1.
- FHL's `無經文` / `併於上節` placeholders are exactly the master-grid bookkeeping that
  makes this safe.

This is fundamentally different from `Formosan-Siraya_Gospels`, where the Gravius
Dutch-era text, CUV, and KJV came from **different** sources and required explicit
per-chapter `verse_remap` dicts (`add_english_trans.py`, `check_cuv_versification.py`).
That hazard does not arise here.
*Minor:* English superscription text rides along inside Psalm v1 cells (benign asymmetry).

---

## 4. Recommended remediation (before porting)

**Must-fix (blockers):**
1. **Dialect attributes.** Map `FORMOSAN_LANGUAGE_MAP` dialect values to `dialects.csv`
   canonical names: `太魯閣語`→`Truku`, `德固達雅賽德克語`→`Tegudaya`,
   `萬山魯凱語`→`Wanshan`, `茂林魯凱語`→`Maolin`, `多納魯凱語`→`Dona`. Set single-dialect
   languages to the language name (`Tsou`, `Yami`); for genuinely-unknown multi-dialect
   files (Amis/Atayal/Bunun/Puyuma/generic-Rukai) emit `dialect="unknown"`. Clears V036
   and fixes the Truku→Seediq miscount. *(Maintainer is investigating the mapping.)*
2. **Reproducibility.** The committed XML differs from the build only in that `<TRANSL>`
   has no `kindOf` (the "fix kindOf elements" hand-edit removed `kindOf="original"`; FORM
   untouched — verified on the df1eec0 diff). Added **`scripts/postprocess_strip_transl_kindof.py`**
   to replay that edit deterministically as a final pipeline step after
   `build_formosanbank_xml.py` (regex-strips `kindOf` from TRANSL tags only; idempotent;
   dry-run by default). Alternatively, change `build_formosanbank_xml.py` to not emit
   `kindOf` on TRANSL and relax its `validate_tree` check (lines 277-279, 384, 397).

**Should-fix (quality, per maintainer decisions):**
3. **Normalize quote punctuation.** Smart quotes (V127) are **already handled by
   `QC/cleaning/clean_xml.py`** (`swap_punctuation` maps U+2018/2019/201C/201D → ASCII),
   so they clear when the QC pipeline runs — no new code needed. The `<…>`/`<<…>>`
   angle-bracket quotes (V134) are NOT touched by `clean_xml` and must NOT be added to its
   global `swap_punctuation` (that would destroy real `<…>` infix markers in W/M-segmented
   corpora). Added **`scripts/normalize_angle_quotes.py`** — a corpus-specific step that
   converts `<<`/`>>`/`<`/`>` → `"` in S-level FORM only (safe here: verse-level, no W/M).
   Dry-run shows it would normalize 33,966 FORM elements across 260 files.
4. **Footnote-digit leaks (V137) and asterisks (V129)** — extend footnote handling to
   catch untagged inline superscripts (esp. Amis-1997) and strip stray markers.

**Accepted / no action:**
5. Section-heading deletion — keep (editorial).
6. Heuristic span-deletions (`NUMBERED_SOURCE_NOTE` / `RUKAI_BRACKET` /
   `STRAY_TRAILING_HEADING`) — accepted; targeted verification found no over-deletion.
7. Cross-translation alignment — correct as-is (single-source grid).

**Standard QC still owed at port time:** `standardize.py --copy` to create the
`standard` tier; then re-run `orthography_extract.py --kindOf original` +
`validate_orthography.py` (now that dialects resolve to reference folders) for
Truku/Seediq/Rukai.

---

## 5. Evidence index
- Scripts: `scripts/common.py:445` (`normalize_source_text`), `scripts/parse_api.py:67`,
  `scripts/build_formosanbank_xml.py:369-399`.
- Validator CSVs: `/tmp/bibles-qc/validate_xml.csv`, `/tmp/bibles-qc/validate_text.csv`.
- Orthography extract: `/tmp/bibles-qc/extract/{Tsou,Yami,...}/`.
- Live source-diff harness: imported his `common.normalize_source_text` and re-fetched
  Truku Mark, Rukai Mark, Truku Psalms from `bible.fhl.net/json/qb.php` to verify
  before/after (Acts 8:37 gap, Ps 3/51 superscriptions, Rukai bracket-note deletions).

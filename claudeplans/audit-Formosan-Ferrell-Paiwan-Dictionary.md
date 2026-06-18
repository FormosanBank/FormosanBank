# Dev-repo audit — Formosan-Ferrell-Paiwan-Dictionary

**Date:** 2026-06-12 · **Status:** complete (pre-port). **Verdict: BLOCKING — do
not port as-is.** Recommend returning to Hunter (or a hand-OCR pass) for source
re-extraction; see "Hypotheses for automatic correction" for what a human could
verify to let tooling assist the cleanup.
**Source:** Ferrell, Raleigh. 1982. *Paiwan dictionary*. Pacific Linguistics
Series C, No. 73. Canberra: ANU. DOI 10.15144/PL-C73. `xml:lang="pwn"`,
glottocode `paiw1248`. One `TEXT` = the Paiwan→English dictionary (printed pages
53–364 + addenda p. 503). Permission: `full_rights_obtained`.
**Audit driver:** `audit-dev-repo` skill + `claudeplans/2026-06-09-dev-repo-audit-briefing.md`.

## Overall assessment

This is **not** a sentence corpus — it is an **image-scanned PDF run through its
embedded OCR text layer and parsed into lexical `<S>` units by heuristics**. That
makes it categorically riskier than the thesis-style corpora the audit workflow
was built around, and the risk has materialized: **OCR mis-recognition has
corrupted the published data at scale, and the FORM/TRANSL boundary is *guessed*
rather than read from the source.**

All logic lives in one 2,884-line
[`scripts/pipeline.py`](../../Formosan-Ferrell-Paiwan-Dictionary/scripts/pipeline.py);
the 14 scripts the README tells you to run are 5-line wrappers around it. The
package is well-instrumented (per-step logs, sidecar CSVs, page images, an
internal validator that reports `PASS`) and the *intent* is conservative (no fresh
OCR, `�`-records excluded, NFC only, no ASCII-folding). But the instrumentation
measures the wrong thing: the internal validator only guards against literal `�`
(U+FFFD) and its own hand-built English wordlists — **it never checks the FORM
tier against FormosanBank's reference Paiwan orthography**, so it certifies
`PASS` while 10% of entries carry Devanagari, Armenian, Greek, and Cyrillic
characters.

Churn profile (Hunter): 5 commits, including "Remove segmentation artifacts from
Paiwan XML surface forms" immediately followed by "**Restore** original Paiwan
segmentation in XML" — i.e. a change made and then reverted. The parser's English
wordlists (`BROKEN_DEFINITION_STRINGS = {"corne on": "come on", ...}`,
`BROKEN_ENGLISH_PAIRS`, ~400 hand-listed words) are point-patches to individual
parse failures, the signature of churn-prone heuristic tuning.

### Headline numbers (from the XML + the repo's own reports)

| Metric | Value |
|---|---|
| Dictionary entries parsed | 12,158 |
| Entries admitted to XML (`<S>`) | 6,922 (57%) |
| Entries **rejected** by quality filter | 5,236 (43%) |
| `�`/U+FFFD records excluded | 1,547 |
| **`<S>` with out-of-orthography chars in FORM** | **720 / 6,922 = 10.4%** |
| W tokens | 8,569 · M elements | 0 (disabled in config) |
| Internal validator result | `PASS`, 0 failures |

## What Hunter built (Steps 1–2: preprocessing, in pipeline order)

1. **inspect_pdf** — hashes/metadata; confirms unencrypted, no fresh OCR.
2. **extract_pdf_text** — `pdftotext -layout` + PyMuPDF per page; strips
   running headers/footers (Ferrell citation, ©1982 line); counts `�`.
3. **render_pdf_pages** — every page → PNG in `data/raw/page_images/` (514 present).
4. **extract_layout_blocks** — PyMuPDF `dict` blocks; classify lines by printed
   page range + indent.
5. **parse_abbreviations** — hardcoded abbreviation + dialect (W/OD/Q/T) tables.
6. **parse_dictionary_entries** — the core. Re-groups OCR words into visual lines
   by y-coordinate (`page_word_layout_lines`), then per line:
   - `split_form_definition` — **guesses where the Paiwan form ends and the
     English definition begins**, via `form_score`/`definition_score` over the
     `COMMON_ENGLISH`/`BAD_ENGLISH_IN_FORM` wordlists.
   - `repair_split_leakage` — **moves tokens across the FORM/TRANSL boundary**
     ("english_tail_moved_from_form", "paiwan_prefix_moved_from_translation",
     "paiwan_final_i_moved_from_translation").
   - continuation-line joining; colon-subentry extraction.
7. **normalize_text** — `clean_form` (collapse whitespace around `-` and `/`,
   strip trailing `(n)` sense numbers, NFC, strip control chars) and
   `clean_definition` (heavy English OCR repair); flags `�`.
8. **map_language** — `pwn` / `paiw1248`; no `dialect` attribute (entries mix
   source labels W/OD/Q/T, preserved only in sidecars).
9. **quality_filter** — rejects ~43% on heuristics (see breakdown below).
10. **dedupe_entries** / **dedupe_against_formosanbank** — exact-pair dedupe +
    sibling-repo overlap flag (133 flagged).
11. **build_formosanbank_xml** — `FORM[original]=clean_form(...)`,
    `FORM[standard]=surface form` (segmentation stripped), `TRANSL[eng]`, `<W>`
    tokens. **No `<M>`** (`include_m_morphemes: false`).
12. **validate_formosanbank_xml** — internal validator (see caveat above).

**Quality-filter rejection breakdown** (5,236 rows): low_confidence 1,389 ·
prose_only 1,251 · **source_target_contamination 969** · no_english_definition
865 · proper_name_only 237 · cross_reference_only 211 · morpheme_only 61 ·
duplicate 48. The 969 "source_target_contamination" rejections are the parser
*detecting its own split failures* — corroborating that the FORM/TRANSL boundary
is unreliable.

## Findings by concern

### (a) Eliminated / corrupted orthography characters — **CRITICAL, systemic**

The pipeline excludes literal `�`, but the OCR **also mapped scanned glyphs to
thousands of plausible-but-wrong real Unicode codepoints that passed straight
into Final_XML.** Measured on the published FORM tier:

- **720 / 6,922 entries (10.4%)** contain a character outside the Paiwan letter
  set (`a–z`, space, apostrophe, segmentation markers).
- Across **263 distinct codepoints** spanning entire foreign scripts:
  Devanagari (72 entries), Armenian (55), Bengali (8), Greek (13), Cyrillic (3),
  plus 113 exotic-Latin-diacritic, 271 ASCII-uppercase, 184 ASCII-digit entries.
- The corruption lands **on the phonemically-important glyphs** — Ferrell's
  special phonetic symbols (glottal stop, schwa, special consonants):
  - `ॽaken` → "I" — `ॽ` is *DEVANAGARI LETTER GLOTTAL STOP*; the source has a
    glottal-stop-initial word.
  - `əm/elu`, `ɘ/alud` — schwa OCR'd as IPA `ə`/`ɘ` instead of orthographic `e`.
  - `Ǉ/adal` ("climb ladder") — `Ǉ` is *LATIN CAPITAL LETTER LJ*: the Paiwan
    `lj` digraph, OCR'd as the lj-ligature.
  - `Qung-alis-an`, `beUq`, `m-aEu` — `q`/`u`/schwa rendered as `Q`/`U`/`E`.

This is **worse than dropping the characters**: it is silent substitution into
valid-but-wrong Unicode, which our orthography validator will flag but a casual
reader will not. The repo's `normalization_report.md` claim that "Paiwan
orthography … is preserved" and "replacement characters are never silently
replaced" is **true only for U+FFFD**, not for this far larger class.

### (b) Suppressed punctuation / segmentation — low/medium

- `clean_form` collapses whitespace around `-` and `/` and strips trailing `(n)`
  sense numbers, so the `original` tier is **normalized, not raw** — acceptable
  under our "minor punctuation normalization" allowance, but worth noting it is
  not a faithful source string.
- Segmentation markers survive in `original`/`W` and are stripped from `standard`
  (`surface_sentence_form`), which matches the C012 convention (Paiwan does not
  list `-` as a letter). **No segmentation-suppression bug found.**
- **Open linguistic question:** `/` occurs **3,413×** mid-word (`kim/an`,
  `Ȋ/m/ut`, `p/n/eÃiq`, `9/m/aingal`). It looks like Ferrell's infix/boundary
  notation (`/m/`, `/n/` = actor/instrument-focus infixes). The pipeline treats
  it as a generic segmentation marker. **Needs your call**: should `/m/` map to
  the FormosanBank infix convention `<m>` rather than be stripped?

### (c) Other convention breaks — low

- Schema/`kindOf`/ids/`ver` all conform; `<M>` correctly disabled, so no V064
  ("every M needs a TRANSL") risk. No `dialect` attribute — defensible for a
  mixed-dialect lexical source, but means these entries won't carry dialect
  identity (W/OD/Q/T live only in sidecars, not the XML).
- **Lexical dictionary entries as `<S>` units** is a project-level decision; the
  repo's own import report flags it ("ready … if project owners accept lexical
  dictionary entries as S units"). Precedent exists (Glosbe, ILRDF_Dicts).

### (d) Source-extraction artifacts — **HIGH**

- **English leaking into FORM**, missed by the quality filter:
  `Qaisang outstanding` (form = `qaisang`, "outstanding" is the definition's
  first word), `ma-aEu chewable`, `ȃa-dalar-an flowered`,
  `kim/an ॼalak` ("the child who is eating" — two-word example phrase whose
  split is uncertain).
- **Broken spacing leaking into TRANSL**: `"to fil l something"`,
  `"food which' has been cooked"` (stray apostrophe), `"to hail, s leet"`.
- Stray digits as word characters (`9ail-i`, `1aqa`, `17`) — OCR misreads, not
  source content.
- The 43% rejection rate (and 969 self-detected contamination rejections) means
  the admitted 57% is the parser's best-guess subset, not a clean source slice.

## Pipeline mapping (his step → our pipeline)

| Hunter step | Our equivalent | Verdict |
|---|---|---|
| `clean_form` whitespace/`-`/`/` normalization | `clean_xml.py` char-level + C012 | Overlaps; his is gentler but pre-applied to `original` |
| `surface_sentence_form` strips seg. from standard | C012 hyphen rule in `clean_xml.py` | **Matches convention** (Paiwan strips `-`) |
| `split_form_definition` / `repair_split_leakage` | *(no equivalent — we never guess FORM/TRANSL)* | **Conflict/risk**: invents the source/target boundary |
| English wordlist quality filter | *(no equivalent)* | Risk: may drop valid Paiwan; opaque |
| internal `validate_formosanbank_xml` | `validate_xml` + `validate_text` + `validate_orthography` | His skips the orthography check → false `PASS` |
| `�`-only exclusion | `add_phonology` `*`-replacement is unrelated | His misses non-`�` OCR corruption |

> Our `validate_orthography.py` (run on `orthography_extract.py --kindOf
> original` vs `QC/validation/reference/Paiwan/`) is the tool that surfaces
> concern (a); the 263-codepoint inventory above is the same signal it produces.
> It was not run inside the dev repo.

## Hypotheses for automatic correction — *verify against page images first*

**Encouraging structural fact:** **628 of the 720 corrupted entries (87%) have
exactly ONE corrupt glyph**; 308 are word-initial, 464 word-medial, 55
word-final. So most entries are a single-glyph fix, and every entry is tied to a
printed page in `data/processed/xml_index.csv` with the page image already
rendered in `data/raw/page_images/`. A targeted, page-anchored correction pass is
very feasible.

These are **hypotheses, not assertions** — each needs a human to confirm against
the rendered page before any tooling applies it. Tiered by confidence:

**Tier 1 — high-confidence systematic substitutions (spot-check ~5 each, then
likely safe to auto-apply).** All map onto real Paiwan letters and the OCR error
is explainable:

| Garbage | → likely | Count | Evidence / verify on printed page |
|---|---|---|---|
| `Ǉ` (LATIN CAPITAL LJ) | `lj` | 8 | `Ǉ/adal` p.274, `Ǉ/alau` p.276 — the lj-ligature for the `lj` digraph |
| `ə`,`ɘ`,`ǝ`,`ɘ` (schwa family) | `e` | ~12 | `əm/elu` p.116, `ɘ/alud` p.254 — Paiwan `e` = /ə/, OCR kept the IPA glyph |
| `Q` (capital) | `q` | 62 | `Qung-alis-an` p.55, `QaliQal` — headwords are lowercase; `q` is valid |
| `ś` | `s` | 6 | `ślekel` p.139, `ślavay` p.155 — word-initial s with spurious acute |
| `ü` | `u` | 9 | `ükuris` p.128, `ülavar` p.136 — word-initial u with spurious diaeresis |

**Tier 2 — known small candidate set, needs human disambiguation per glyph
(cannot auto-apply blind, but the choice is binary/small):**

| Garbage | candidates | Count | Notes |
|---|---|---|---|
| `I` (capital i) | `l` or `i` | 118 | `djalI`→`djali`? vs `I/m/agay`→`l/m/agay`? — depends on glyph |
| `Ã` | `ng`? `e`? | 24 | always `eÃ` between vowels (`peÃuq` p.198) — one consistent target likely |
| `±` (word-final) | `q`? glottal? | 24 | consistently word-final (`daru±`, `9apu±` p.83) — a final consonant |
| `H` | vowel? deletion? | 27 | `lHavay`, `gH` — inspect; may be a special symbol |
| `ǆ` (dz-caron) | `dr`? `z`? | 5 | always pre-`r` initial (`ǆramil`, `ǆrumed`) |
| `Ɣ` (gamma) | `g`? | 4 | `gaƔay`, `kaƔagi` |
| `Ő` | `q`? `ng`? | 8 | medial (`kaluŐali`, `tuŐing`) |
| digits `9 4 1 7` as letters | `g`?/`l`?/… | ~185 | `9ail`→`gail`? `1aqa`→`laqa`? — per-digit hypothesis, verify |

**Tier 3 — NOT automatable; hand-correct against the page image.** The long tail
of ~200 single-occurrence Armenian / Bengali / Devanagari / curl/hook Latin
codepoints are unique OCR misfires on individual special glyphs — no systematic
mapping exists. These are exactly what a hand-OCR pass is for.

**Two meta-approaches that would let tooling help materially:**

1. **Generate a page-anchored correction worklist** (I can build this now): one
   row per affected entry — `unit_id`, printed page, the FORM with the corrupt
   glyph marked, the TRANSL, the Tier-1/2 candidate replacement — sorted by page.
   A human then verifies down the list against `page_images/`, and Tier-1
   confirmations can be batch-applied. Turns a 720-entry problem into a
   structured review, not a hunt.
2. **Independent second OCR/vision pass for cross-check** (they explicitly ran
   *no* fresh OCR): re-OCR each affected line image — constrained Tesseract with
   a Paiwan charset, or a vision-LLM on the cropped line — and surface only the
   characters where the two passes disagree. Disagreements localize precisely the
   corrupt glyphs and propose a reading, which a human confirms. This is the most
   scalable path and directly addresses the root cause.

> Caveat for whoever automates: confirm there is **no legitimate uppercase or
> non-`a–z` character** in Ferrell's Paiwan orthography before folding capitals
> (headwords are lowercase throughout, so capitals are almost certainly OCR
> errors — but verify on a page). And settle the `/`-as-infix question (concern
> b) before deciding whether `/m/` should be rewritten to `<m>`.

## Recommended remediation (before any port)

1. **Blocking — fix concern (a).** Re-extract the corrupted glyphs by hand-OCR or
   the second-pass cross-check above, against the page images. Re-extraction must
   guard against *any* non-orthography Unicode, not just `�`. Target: the FORM
   tier passes `validate_orthography.py` against `reference/Paiwan/`.
2. **Blocking — fix concern (d) FORM/TRANSL leaks.** The 720 corrupted entries
   and the English-in-FORM cases overlap heavily with the parser's lowest-
   confidence splits; re-validate splits on affected pages during the hand pass.
3. **Add our orthography check to his loop** so a future rebuild can't report
   `PASS` while carrying foreign-script characters
   (`orthography_extract.py --kindOf original` → `validate_orthography.py`).
4. **Resolve the `/` infix question** (concern b) and the dialect-attribute
   decision (concern c) with the maintainer; both are conventions, not bugs.
5. **Re-examine the 43% rejection** at least on a sample — confirm the English
   wordlist filter isn't discarding valid Paiwan forms.

## Appendix — how this was measured

- Char inventory: parsed `Final_XML/Paiwan/Ferrell_Paiwan_Dictionary_PL_C73.xml`,
  counted FORM `original`/`standard` characters outside
  `{a–z, space, ' - / = < >}`; grouped by Unicode block.
- Position/concentration: per-token index of each suspect char; 628/720 entries
  single-glyph.
- Page references: joined `sentence_id` → `printed_page_number` via
  `data/processed/xml_index.csv`.
- Rejection breakdown: `data/processed/rejected_records.csv`.
- Reference orthography: `QC/validation/reference/Paiwan/`,
  `Orthographies/Ortho113/Paiwan.tsv` (letters: a b c d dj dr e g h i k l lj m n
  ng o p q r s t tj u v w y z and `'`; `e`=/ə/).
- Not yet run (recommended next): `validate_xml.py`, `validate_text.py`,
  `orthography_extract.py --kindOf original` + `validate_orthography.py` on his
  `Final_XML` — predicted to flag the 263-codepoint inventory above.

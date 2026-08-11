# Dev-repo preprocessing audit — briefing

**Date:** 2026-06-09
**Audience:** a Claude instance about to audit one of an assistant's corpus dev repos
(`../Formosan-<Name>/`) before it is QC'd and ported into `FormosanBank/Corpora/`.
**Read this first**, then `FormosanBank/CLAUDE.md` (auto-loaded) and `QC/README.md`.
This is the single up-to-date entry point; it points down into the deeper
`claudeplans/` design docs only where you need them.

## Why this audit exists

An assistant built preprocessing for several new corpora in separate dev repos. It is a
**strong programmer that does not read the Formosan languages** and whose XML work
has shown churn (mass rewrites across languages). Before we trust its output, we
audit how its preprocessing maps onto our current pipeline.

**The general goal is to check anything that touches the data** — every
transformation should make sense and look correct. Below are four worries the
maintainer especially flagged; treat them as **highlighted priorities, not an
exhaustive checklist**. Anything else a step does to the data is equally fair game:

- **(a) Eliminated orthography characters** — did it drop characters that are real
  letters in the language's orthography (glottal-stop apostrophe, `ŋ`, `ə`, `ɬ`,
  barred/strokes, etc.)? The benchmark is the **actual source text**, not the raw
  scrape: an OCR/scrape *correction* toward the real spelling (e.g. `u`→`ʉ` where a
  barred vowel was misread) is expected and good — the bug is dropping a letter the
  source really has, or changing spelling away from what the source prints.
- **(b) Suppressed punctuation** — did it strip punctuation/segmentation in ways
  that disrupt the data? Note: **punctuation normalization on the original tier is
  fine** as long as it doesn't change spelling; the concern is punctuation the
  *source has* silently vanishing, or segmentation markers being lost.
- **(c) Other convention breaks** — schema, `kindOf`, `ver`, dialects, segmentation
  markers, id rules.
- **(d) Source-extraction artifacts** — leftovers like sentences marked
  ungrammatical, footnote leaks, out-of-language examples.

## What "correct" looks like (our conventions)

- **Two tiers.** `FORM[@kindOf="original"]` matches the **actual original source
  text** — the printed page / true source, *not* necessarily the raw scrape. OCR and
  scraping errors **should** be corrected (by hand-edit or script) so the tier matches
  what the source prints; punctuation may be normalized too. What must be preserved is
  the source's **spelling**. `FORM[@kindOf="standard"]` is the single common
  orthography. **The original tier is the faithfulness anchor** — but "faithful" means
  *faithful to the real source*, so the audit question is "does the original tier
  match the actual printed source (spelling included)?", **not** "does it differ from
  the scrape?" A correction that makes it match the source better is good; a change
  that alters spelling or drops a real letter/punctuation is the bug.
- **Segmentation markers** (`-`, `=`, `<…>`) belong in the **W** tier (both tiers)
  and in the S-level **original** FORM where the source had them. They are stripped
  from the S-level **standard** FORM only, gated on the sentence being
  morpheme-segmented (has `<M>`), keeping digit-flanked `-` (dates, verse ranges)
  and only for languages whose orthography does NOT list `-` as a letter
  (Bunun/Thao keep it). This is the C012 rule, which lives in **`standardize.py`**
  (moved out of `clean_xml.py` 2026-08; `standardize.py` owns all standard-tier
  cleaning — POL-002). The assistant stripping `-` from W FORMs or from S-original
  is a bug.
- **Ungrammatical sentences.** A source `*` at the start of a sentence means the
  whole sentence is ungrammatical and should be **excluded**, not ingested. A `*`
  mid-token / interacting with `/` may mark one alternative ungrammatical. (Lowking
  thesis card.) **Parenthesized stars are directional (POL-017):** `*(X)` = X
  obligatory → keep X; `(*X)` = X forbidden → drop X. Treating them identically
  is the NTU-Rukai bug class. `?` at sentence start marks marginality — V142
  flags it left inline. POL-016 (ruled 2026-08-10): both `*` and `?`
  examples are **excluded** at intake, not ingested with or without the
  marker.
- **Schema:** `QC/validation/xml_template.xsd`. `kindOf` ∈ {original, standard};
  `TRANSL/@ver="alt"` for redundant same-language translations; `TEXT/@dialect`
  required and valid per `dialects.csv` (single-dialect languages use the language
  name, e.g. `dialect="Yami"`).

## The current pipeline (what we would do)

Order (see `QC/README.md`): `apply_manual_edits` → `clean_xml` → (orthography
detection, human) → `standardize` → `add_phonology` → validators.

- **`apply_manual_edits.py`** — re-applies recorded hand edits
  (`CodeAndDocs/manual_edits.xml`) first; no-op if absent.
- **`clean_xml.py`** — character-level cruft + language-aware punctuation on the
  **original tier only** (all standard FORMs are standardize's property):
  normalizes caret variants, Chinese punctuation, typographic
  apostrophes/quotes → ASCII (POL-010), all dash/hyphen look-alikes → `-`
  (POL-011), null glyphs `ø`/`Ø` → `∅` in morpheme position (POL-012). Does
  NOT transliterate and no longer owns C012 (both are standardize's).
- **`standardize.py`** — regenerates the standard tier from the original on
  every run (`--copy`, or transliterate via a TSV; hand edits to standard FORMs
  are clobbered by design — POL-002), applies C012 (above), removes null units
  from S-standard in TSV mode, derives capital-letter rule variants from the
  table's source profile, and writes `standardize_warnings.csv` (per-run
  report, POL-033). Column resolution is single-vs-multi-dialect aware
  (`_dialect_inventory`).
- **`add_phonology.py`** — generates `<PHON>` IPA from FORM via the language's
  designated standard orthography per `standards.csv` (currently Ortho113 for
  all 16; a blank cell = standard PHON deliberately skipped). Null morphemes
  are silent; a whole-null FORM gets PHON `∅`; unmapped punctuation is dropped
  (POL-003/012). **Hazard relevant to (a):** it replaces
  any character that is not an orthography IPA letter, ASCII punctuation, or
  whitespace with `*` — and it drops typographic curly quotes/apostrophes (`'`
  U+2019) that may be a phonemic glottal stop. Don't mistake this PHON behavior for
  an assistant bug, but DO check whether the FORMs use curly apostrophes.
- **Validators** (new output 2026-06-09: compact per-rule **summary** with mnemonic
  names on the terminal + **one findings CSV** per validator, path printed; rule
  mnemonics come from `_rule_titles`):
  - `validate_xml.py` — schema, ids, `kindOf`, `ver` (V084/V085), dialects (V036).
  - `validate_text.py` — punctuation (V110–V116), `*` in FORM (V129), footnote
    leaks (V137–V139), segmentation in S-standard (V133/V134), `=` (V126),
    null-propagation family (V120 SOFT, V123–V125/V140 HARD — vacuous while
    null glyphs are non-canonical `ø`/`Ø`), informally marked
    ungrammatical/marginal examples (V142: leading `? ` in FORM, or
    "ungrammatical"/"marginal" only in @source/@notes free text — positive
    "is grammatical" notes never fire), and per-file
    TRANSL language/script swaps (V143, rate-based).
  - `validate_glosses.py` — W/M counts (V060/V061), segmentation preserved at W
    (V063), and **reconstruction**: M FORMs spell the W (V068) and W FORMs spell
    the S (V141) — these catch "the morphemes/words don't match the sentence."
  - `validate_orthography.py` / `validate_vocabulary.py` + `orthography_extract.py`
    — compare the corpus's character/word inventory to
    `QC/validation/reference/<Language>/`. **Primary tool for concern (a).**

## Concern → tool/check map

| Concern | Run / check |
|---|---|
| (a) dropped orthography chars | `orthography_extract.py --kindOf original` then `validate_orthography.py` vs `reference/<Language>/`; diff the original-tier char inventory against the **source** and the reference; watch curly-apostrophe loss |
| (b) suppressed punctuation | `validate_text.py` (V110–V116, V126, V133/V134); confirm the **original** tier still has source punctuation/segmentation; confirm W tier kept `-`/`=`/`<>` |
| (c) convention breaks | `validate_xml.py` (schema/kindOf/ver/dialects) + `validate_glosses.py` (V063 segmentation, V068/V141 reconstruction) |
| (d) extraction artifacts | `validate_text.py` V129 (`*`), V137–V139 (footnotes); grep the source + XML for sentence-initial `*` (should have been excluded), stray digits, out-of-language runs |

## How to audit one repo (the procedure)

1. **Read the preprocessing.** The repo's `README` + its scripts (scrape/parse/
   build). Summarize, in plain terms, what transformations it applies and in what
   order — especially anything that deletes or substitutes characters.
2. **Map to our pipeline.** For each transformation, decide: does our pipeline do
   this (and better), is it a no-op for us, or does it conflict with a convention?
3. **Run our validators** on the XML output (the `run-qc-pipeline` skill does the
   sequence; or run the four validators by_path). Read the summary + CSVs.
4. **Diff against source** for (a)/(b)/(d): take a sample of sentences, compare the
   `original` tier to the raw source — did characters or punctuation disappear?
5. **Flag and decide.** Group findings by concern (a–d) with evidence (file, id,
   sample). Pause for the maintainer's judgment on each class before concluding.
6. **Record** a per-repo report at `claudeplans/audit-<Repo>.md`.

## Reading list (on demand, not all up front)

- Conventions: `FormosanBank/CLAUDE.md`, `QC/README.md`.
- "What clean_xml should/shouldn't touch": `claudeplans/2026-05-29-clean-xml-extension-tests-design.md`.
- Orthography references: `QC/validation/reference/<Language>/`, `Orthographies/Ortho113/<Language>.tsv`, `dialects.csv`.
- Validator output model: `claudeplans/2026-06-09-validator-output-summary-design.md`.
- Assistant backlog context: roadmap `claudeplans/2026-05-27-roadmap.md` §C.2.

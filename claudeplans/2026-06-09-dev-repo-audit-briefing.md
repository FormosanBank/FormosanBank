# Dev-repo preprocessing audit — briefing

**Date:** 2026-06-09
**Audience:** a Claude instance about to audit one of Hunter S's corpus dev repos
(`../Formosan-<Name>/`) before it is QC'd and ported into `FormosanBank/Corpora/`.
**Read this first**, then `FormosanBank/CLAUDE.md` (auto-loaded) and `QC/README.md`.
This is the single up-to-date entry point; it points down into the deeper
`claudeplans/` design docs only where you need them.

## Why this audit exists

Hunter built preprocessing for several new corpora in separate dev repos. He is a
**strong programmer who does not read the Formosan languages** and whose XML work
has shown churn (mass rewrites across languages). Before we trust his output, we
audit how his preprocessing maps onto our current pipeline.

**The general goal is to check anything that touches the data** — every
transformation should make sense and look correct. Below are four worries the
maintainer especially flagged; treat them as **highlighted priorities, not an
exhaustive checklist**. Anything else a step does to the data is equally fair game:

- **(a) Eliminated orthography characters** — did he drop characters that are real
  letters in the language's orthography (glottal-stop apostrophe, `ŋ`, `ə`, `ɬ`,
  barred/strokes, etc.)?
- **(b) Suppressed punctuation** — did he strip punctuation/segmentation in ways
  that disrupt the data, especially from the tier that must stay faithful?
- **(c) Other convention breaks** — schema, `kindOf`, `ver`, dialects, segmentation
  markers, id rules.
- **(d) Source-extraction artifacts** — leftovers like sentences marked
  ungrammatical, footnote leaks, out-of-language examples.

## What "correct" looks like (our conventions)

- **Two tiers.** `FORM[@kindOf="original"]` stays as close to the source as
  possible (only minor punctuation/HTML-escape normalization). `FORM[@kindOf=
  "standard"]` is the single common orthography. **The original tier is the
  faithfulness anchor** — most of concerns (a)/(b)/(d) are "did the original tier
  lose something the source had?"
- **Segmentation markers** (`-`, `=`, `<…>`) belong in the **W** tier (both tiers)
  and in the S-level **original** FORM where the source had them. They are stripped
  from the S-level **standard** FORM only, and only for languages whose orthography
  does NOT list `-` as a letter (Bunun/Thao keep it). This is the C012 rule in
  `clean_xml.py`. Hunter stripping `-` from W FORMs or from S-original is a bug.
- **Ungrammatical sentences.** A source `*` at the start of a sentence means the
  whole sentence is ungrammatical and should be **excluded**, not ingested. A `*`
  mid-token / interacting with `/` may mark one alternative ungrammatical. (Lowking
  thesis card.)
- **Schema:** `QC/validation/xml_template.xsd`. `kindOf` ∈ {original, standard};
  `TRANSL/@ver="alt"` for redundant same-language translations; `TEXT/@dialect`
  required and valid per `dialects.csv` (single-dialect languages use the language
  name, e.g. `dialect="Yami"`).

## The current pipeline (what we would do)

Order (see `QC/README.md`): `clean_xml` → (orthography detection, human) →
`standardize` → `add_phonology` → validators.

- **`clean_xml.py`** — character-level cruft + language-aware punctuation; C012
  hyphen rule (above); normalizes caret variants, Chinese punctuation, etc. Does
  NOT transliterate (that's standardize).
- **`standardize.py`** — builds the standard tier (`--copy`, or transliterate via a
  TSV). Column resolution is single-vs-multi-dialect aware (`_dialect_inventory`).
- **`add_phonology.py`** — generates `<PHON>` IPA from FORM via
  `Orthographies/Ortho113/<Language>.tsv`. **Hazard relevant to (a):** it replaces
  any character that is not an orthography IPA letter, ASCII punctuation, or
  whitespace with `*` — and it drops typographic curly quotes/apostrophes (`'`
  U+2019) that may be a phonemic glottal stop. Don't mistake this PHON behavior for
  a Hunter bug, but DO check whether his FORMs use curly apostrophes.
- **Validators** (new output 2026-06-09: compact per-rule **summary** with mnemonic
  names on the terminal + **one findings CSV** per validator, path printed; rule
  mnemonics come from `_rule_titles`):
  - `validate_xml.py` — schema, ids, `kindOf`, `ver` (V084/V085), dialects (V036).
  - `validate_text.py` — punctuation (V110–V116), `*` in FORM (V129), footnote
    leaks (V137–V139), segmentation in S-standard (V133/V134), `=` (V126).
  - `validate_glosses.py` — W/M counts (V060/V061), segmentation preserved at W
    (V063), and **reconstruction**: M FORMs spell the W (V068) and W FORMs spell
    the S (V141) — these catch "the morphemes/words don't match the sentence."
  - `validate_orthography.py` / `validate_vocabulary.py` + `orthography_extract.py`
    — compare the corpus's character/word inventory to
    `QC/validation/reference/<Language>/`. **Primary tool for concern (a).**

## Concern → tool/check map

| Concern | Run / check |
|---|---|
| (a) dropped orthography chars | `orthography_extract.py --kindOf original` then `validate_orthography.py` vs `reference/<Language>/`; diff his original-tier char inventory against the **source** and the reference; watch curly-apostrophe loss |
| (b) suppressed punctuation | `validate_text.py` (V110–V116, V126, V133/V134); confirm his **original** tier still has source punctuation/segmentation; confirm W tier kept `-`/`=`/`<>` |
| (c) convention breaks | `validate_xml.py` (schema/kindOf/ver/dialects) + `validate_glosses.py` (V063 segmentation, V068/V141 reconstruction) |
| (d) extraction artifacts | `validate_text.py` V129 (`*`), V137–V139 (footnotes); grep his source + XML for sentence-initial `*` (should have been excluded), stray digits, out-of-language runs |

## How to audit one repo (the procedure)

1. **Read his preprocessing.** The repo's `README` + its scripts (scrape/parse/
   build). Summarize, in plain terms, what transformations he applies and in what
   order — especially anything that deletes or substitutes characters.
2. **Map to our pipeline.** For each transformation, decide: does our pipeline do
   this (and better), is it a no-op for us, or does it conflict with a convention?
3. **Run our validators** on his XML output (the `run-qc-pipeline` skill does the
   sequence; or run the four validators by_path). Read the summary + CSVs.
4. **Diff against source** for (a)/(b)/(d): take a sample of sentences, compare his
   `original` tier to the raw source — did characters or punctuation disappear?
5. **Flag and decide.** Group findings by concern (a–d) with evidence (file, id,
   sample). Pause for the maintainer's judgment on each class before concluding.
6. **Record** a per-repo report at `claudeplans/audit-<Repo>.md`.

## Reading list (on demand, not all up front)

- Conventions: `FormosanBank/CLAUDE.md`, `QC/README.md`.
- "What clean_xml should/shouldn't touch": `claudeplans/2026-05-29-clean-xml-extension-tests-design.md`.
- Orthography references: `QC/validation/reference/<Language>/`, `Orthographies/Ortho113/<Language>.tsv`, `dialects.csv`.
- Validator output model: `claudeplans/2026-06-09-validator-output-summary-design.md`.
- Hunter backlog context: roadmap `claudeplans/2026-05-27-roadmap.md` §C.2.

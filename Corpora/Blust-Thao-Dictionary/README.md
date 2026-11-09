# Blust (2003) Thao Dictionary

Robert Blust's *Thao Dictionary* (2003), the standard reference work for Thao,
as structured data: the dictionary's entries and definitions, its example
sentences, and the five interlinear texts printed in the book.

## Languages and dialects

- **Primary language:** Thao, ISO 639-3 `ssf`
- **Dialect:** Thao

All 21 XML files under `XML/Thao/` declare the same values on `<TEXT>`:
`xml:lang="ssf"`, `dialect="Thao"` and `glottocode="thao1240"`.

## Source

- **Source:** Robert Blust's 2003 *Thao Dictionary*, official Academia Sinica open-access PDF
- **Basecamp card:** [7012450955](https://app.basecamp.com/3340659/buckets/31258415/card_tables/cards/7012450955)
- **Published:** 2026-09-11. Developed in a private dev repo and ported here
  once it passed QC; see "Canonical XML regeneration" for how to rebuild it.

#### Overview

Robert Blust's *Thao Dictionary* (2003) is the standard reference work for Thao, a Formosan language of central Taiwan spoken around Sun-Moon Lake. Published by the Institute of Linguistics (Preparatory Office), Academia Sinica, it runs to over a thousand pages and records the language in far more depth than any other source: headwords and the forms derived from them, grammatical labels, definitions, etymologies reaching back to Proto-Austronesian, and thousands of example sentences collected from speakers.

This corpus is the whole of that linguistic material. It contains the dictionary itself — 7,248 entries and derived forms, each with its English definition — alongside 8,591 example sentences, and the five interlinear texts printed on pages 244–274, which are narrative rather than lexical and carry word-by-word glosses. Every sentence records the printed page it came from, the entry it belongs to, and its sense number, so anything here can be traced back to the book.

Thao is severely endangered, with very few remaining first-language speakers. Blust's dictionary is the most substantial record of it that exists, and this is the first time it has been available as structured, searchable data.

#### Corpus scope

The authorization from the Institute of Linguistics covers **the linguistic
material in the book**, not a named list of sections (maintainer's ruling,
2026-09-11). That is the five interlinear texts on printed pages 244-274 and
the Thao-English dictionary on printed pages 280-1068 -- its headwords, derived
forms, grammatical labels, definitions, etymologies, notes and
cross-references, as well as its example sentences. Front matter, the
expository chapters and the English-Thao index are not corpus source material
and are excluded.

The published XML is 21 files: 8 `blust_2003_thao_entries_*.xml` (7,248
sentences, one per published sense), 8 `blust_2003_thao_examples_*.xml` (8,591
sentences, one per example reading), and 5 `blust_2003_thao_text_*.xml` (167
sentences), each dictionary file covering a range of about 100 printed pages.

#### Audio

There is no audio. The XML carries no `AUDIO` element.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Blust-Thao-Dictionary_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

Blust, R. (2003). *Thao dictionary*. Institute of Linguistics (Preparatory Office), Academia Sinica.

## License

**License:** CC BY-NC 4.0
**Rights source:** Institute of Linguistics, Academia Sinica, 2024-01-30; evidence: ask maintainer

CC BY-NC 4.0.

The Institute of Linguistics (Preparatory Office), Academia Sinica — the publisher and economic rights holder of the *Thao Dictionary* — authorized FormosanBank to reprint, reproduce and adapt the linguistic material in the book under this licence.

The Institute of Linguistics (Preparatory Office), Academia Sinica — the
publisher and economic rights holder of Blust's 2003 *Thao Dictionary* —
authorized FormosanBank to reprint, reproduce and adapt **the linguistic
material in the book** under CC BY-NC. That wording is the grant's own, and is
what puts the dictionary's headwords and definitions in scope alongside the
interlinear texts and example sentences (maintainer's ruling, 2026-09-11). The operative terms and the
checksum of the authorization document are recorded in
`CodeAndDocs/rights-evidence.json`; the document itself stays in ignored
`Private/` storage. Per POL-042 the XML's `@copyright` carries the licence
value alone — the permission behind it is documented here and nowhere else.

## Notes and caveats

**Morpheme boundaries are part of the text.** Blust prints morpheme boundaries in the dictionary examples but not in the interlinear texts, and those hyphens are carried through into the standardized tier. This corpus therefore tokenizes differently from the other Thao material in FormosanBank, and word counts are not directly comparable. The sentences are also segmented into word and morpheme tiers.

## Reproduction and processing

### How to reproduce

From the FormosanBank repository root:

```bash
bash Corpora/Blust-Thao-Dictionary/CodeAndDocs/generate_xml.sh
```

The build needs Python with the packages in `requirements.txt` (PyMuPDF and
lxml) and a FormosanBank checkout around the corpus, whose `QC/` tools and
`Orthographies/` tables it uses. It does not read the source PDF and needs no
network: it starts from the JSON intermediates committed in `CodeAndDocs/`
(see "What each step does"). It replaces `XML/Thao/`. There is no
`validate.sh` for this corpus; the checks are the `unittest` commands below.

#### Reproducible source acquisition

```bash
python3 CodeAndDocs/download_source.py
python3 CodeAndDocs/download_source.py --check
python3 -m unittest CodeAndDocs/test_source_lock.py -v
python3 CodeAndDocs/extract_source.py --check
python3 -m unittest CodeAndDocs/test_extraction.py -v
python3 CodeAndDocs/expand_source.py --check
python3 -m unittest CodeAndDocs/test_expansion.py -v
```

The exact 1,117-page PDF is locked by byte count and SHA-256 in
`CodeAndDocs/source-lock.json`. The PDF and authorization document remain in
ignored `Private/` storage. Their hashes and operative provenance are recorded
without committing private evidence.

`download_source.py` fetches the PDF from the official Academia Sinica URL
recorded in `source-lock.json` into `Private/` when it is not already there,
and verifies its size and SHA-256; with `--check` it only verifies. The
`--check` modes of `extract_source.py` and `expand_source.py` re-derive their
JSON from the PDF and compare it with the committed file.

#### Canonical XML regeneration

One entry point (POL-047), run with whatever FormosanBank tools are in the
checkout — never a pinned one (POL-048):

Run from this directory. The surrounding FormosanBank checkout is found
automatically, so there is nothing to point at:

```bash
python3 -m pip install -r requirements.txt
./CodeAndDocs/generate_xml.sh
./CodeAndDocs/generate_xml.sh --check
python3 -m unittest CodeAndDocs/test_xml.py -v
```

The build emits the raw source tiers, applies the canonical cleaner once,
creates standard FORM with the reviewed Blust-to-Ortho113 table, and creates
original and standard PHON with the recorded orthography profiles. `--check`
rebuilds in a temporary directory and requires byte-identical XML. The
canonical output is 21 files under `XML/Thao`; no `Final_XML/` tree is used.

The FormosanBank commit the published XML was built against is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052). It is
provenance, not a gate: a mismatch is noted on stderr and the build proceeds.

**No POL-047 deviation.** Every step is the shared tool, unwrapped. The two
orthography tables this corpus needs are registered in FormosanBank's own
`Orthographies/` and read from there like any other corpus's:

| file | what it is |
|---|---|
| [Orthographies/Blust2003/Thao.tsv](../../Orthographies/Blust2003/Thao.tsv) | the source orthography profile, for `add_phonology.py --orthography Blust2003` |
| [Orthographies/ConversionTables/Thao_Blust2003_113.tsv](../../Orthographies/ConversionTables/Thao_Blust2003_113.tsv) | Blust's spelling to Ortho113, for `standardize.py` |

Keeping them there rather than under `CodeAndDocs/` is deliberate: a
corpus-local conversion table escapes the repo-wide symbol sweep, which is
what POL-056 exists to prevent.

### What each step does

#### Before the build: extraction and parsing (committed intermediates)

These scripts read the locked PDF in `Private/`. `generate_xml.sh` does not run
them; it reads their committed output.

- `CodeAndDocs/extract_source.py` (with `CodeAndDocs/pdf_text.py`) streams the
  pages and writes `CodeAndDocs/extracted-records.json`: the five texts and the
  dictionary's example sentences.
- `CodeAndDocs/expand_source.py` reads `extracted-records.json`,
  `slash-alternatives.json` and `slash-translations.json` and writes
  `CodeAndDocs/expanded-records.json`, with optional material and slash
  alternatives expanded.
- `CodeAndDocs/parse_entries.py` parses the dictionary against a declared
  schema and writes `CodeAndDocs/entry-records.json`.

The deterministic extraction contains five texts with 166 sentences and 2,531
raw aligned word positions, plus 8,368 dictionary examples. Explicitly optional
material and slash alternatives are expanded mechanically into complete
records, producing 167 text sentences with 2,542 aligned word positions and
8,630 dictionary sentences. Custom PDF glyphs, line-break hyphenation,
dictionary column order, and inline italic terms are handled explicitly in
`CodeAndDocs/pdf_text.py` and `CodeAndDocs/extract_source.py`. The recorded
visual review is in `CodeAndDocs/source-fidelity-review.json`.

The entry apparatus is parsed separately by `CodeAndDocs/parse_entries.py` into
`entry-records.json` -- 6,505 entries and 12,062 senses -- and built into XML by
`CodeAndDocs/build_entry_xml.py`. The two are kept in separate files because
they are different kinds of text, not for any rights reason: one S per sense in
`blust_2003_thao_entries_*.xml`, one S per example in
`blust_2003_thao_examples_*.xml`.

#### The build, step by step

`CodeAndDocs/generate_xml.sh` passes its arguments to
`CodeAndDocs/regenerate.py` (`--check`; `--formosanbank <path>` or
`$FORMOSANBANK_PATH`, used only when no surrounding checkout is found;
`--python`). `regenerate.py` finds the FormosanBank checkout (the first parent
folder containing `QC/utilities/standardize.py`), prints whether its HEAD
matches the commit in `provenance.json`, and builds everything in a temporary
folder, in this order:

1. **`build_xml.py --output-dir <tmp>/XML/Thao --texts-only`** (corpus-local).
   Reads `expanded-records.json` and stops unless it holds the reviewed total
   of 8,797 sentences. Writes only the five `blust_2003_thao_text_NN.xml` files
   (167 S, ids `blust-text-tNN-sNNN`): an original FORM per sentence (Blust's
   quotation glyphs normalized), English TRANSLs with editorial parentheticals
   moved to `TRANSL/@notes` by `QC/utilities/parentheticals.py`, and a W tier
   whose words carry their printed glosses (a printed footnote becomes
   `Source footnote:` in the gloss's `@notes`). Every `<TEXT>` gets the
   citation, BibTeX citation, `copyright="CC BY-NC 4.0"`, `xml:lang="ssf"`,
   `glottocode="thao1240"` and `dialect="Thao"`. It replaces its output folder
   wholesale, which is why it runs first.
2. **`build_entry_xml.py --output-dir <tmp>/XML/Thao`** (corpus-local, adds
   files). Reads `entry-records.json`, `curated-readings.json` and
   `slash-translations.json`, and writes 8 entries files and 8 examples files,
   one pair per printed-page range (280-379, 380-479, ... 980-1068).
   - Entries (ids `blust-entry-pPPPP-sNNN`): one S per sense; FORM is the
     headword or derived form, TRANSL the English definition. The etymology
     (first sense only), grammatical label, homograph number and an inferred
     sense number go in `FORM/@notes`; cross-references are not published.
     Skipped: a bound root's own definition-less header line; senses glossed
     `GLOSS?`; a bar-marked root when its entry also carries derived forms;
     senses whose gloss starts `(don't)`; forms with no letter or digit. For a
     capitalised name whose gloss describes what kind of name it is, the
     English becomes the name itself and the description moves to `@notes`.
   - Examples (ids `blust-ex-pPPPP-eNNN`): one S per example reading; a
     source note goes in `FORM/@notes`; a Thao question quoted inside an
     "answer to" parenthetical becomes its own S (`...-qNN`).
   - Readings, in this order: a curated reading from `curated-readings.json`;
     a phonemic shape between slashes (`/.../`) taken as one form; a bracket
     inside a word, kept as one S with a `ver="alt"` FORM; a slash, expanded
     with `QC/utilities/slash_alternatives.py` (with `slash-translations.json`
     for the English); an optional `(x)` token, expanded into two S, the
     English splitting in step only when it pairs.
   - A W tier (and an M tier where a word carries `-` boundaries) is added only
     when the FORM contains none of `( ) / ~ [ ]`. A W or M here carries no
     TRANSL.
3. **`QC/cleaning/apply_manual_edits.py --corpora_path <tmp>/XML --manual_file
   <tmp>/no-manual-edits.xml`.** That file does not exist, so nothing is
   applied: this corpus records no hand edits.
4. **`QC/cleaning/clean_xml.py --corpora_path <tmp>/XML --reference_dir
   QC/validation/reference`.** The shared cleaner, run once over all 21 files.
5. **`QC/utilities/standardize.py --tsv_path
   Orthographies/ConversionTables/Thao_Blust2003_113.tsv --corpora_path
   <tmp>/XML --ortho-path Orthographies/Ortho113`.** Writes the standard FORM
   in Ortho113. Ortho113 lists `-` as a Thao letter, so the hyphens are kept
   in the standard tier (with a warning for each).
6. **`QC/utilities/add_phonology.py --corpora_path <tmp>/XML --orthography
   Blust2003`.** Writes original PHON from `Orthographies/Blust2003/Thao.tsv`
   and standard PHON from Ortho113.
7. **`prefer_the_etymology.py --path <tmp>/XML/Thao`** (corpus-local). Groups S
   by FORM (standard, else original) plus their TRANSLs; where a group has a
   member whose `FORM/@notes` carries `Etymology:`, deletes the members that do
   not, so the next step cannot keep the copy without the etymology.
8. **`QC/cleaning/remove_duplicate_sentences.py by_path --path <tmp>/XML/Thao
   --scope corpus --apply`.** POL-022: removes S that repeat another S's
   standard FORM and TRANSLs anywhere in the corpus, keeping the first by
   (file, S id) and moving any TRANSL the survivor lacks onto it as
   `ver="alt"`. This takes out Blust's second listing of each derived form.
9. **`apply_same_form_rulings.py --path <tmp>/XML/Thao`** (corpus-local).
   Applies `same-form-rulings.json`: 88 verdicts on groups with the same FORM
   and different glosses (26 `merge-alt`, 18 `keep-both`, 18 `keep-either`,
   14 `keep-second`, 11 `keep-first`, 1 `merge-notes`). A verdict whose
   recorded glosses no longer match the build is refused and printed, not
   applied. It also warns if any of the 4 groups listed as settled by a rule
   has come back.
10. **Finish.** Deletes `cleaner_warnings.csv` and `standardize_warnings.csv`
    from the temporary tree. With `--check`, compares every XML file byte for
    byte with `XML/Thao/` and exits 1 on any difference; otherwise copies the
    tree to `XML/.Thao-canonical-build` and swaps it in as `XML/Thao/`.

#### Maintainer rulings, and what happens when the code catches up

Most of what this corpus does is a rule that applies everywhere and is tested.
Where a rule cannot reach, the maintainer's ruling is recorded as data and the
build consults it. Three files, in the order the build reads them:

| file | what it holds |
|---|---|
| `CodeAndDocs/curated-readings.json` | readings the rules cannot derive, keyed by the **printed Thao** exactly as it appears. `readings()` checks this first, so a curated record bypasses every rule. |
| `CodeAndDocs/settled-readings.json` | rulings that **used** to be curated and no longer need to be, because a later rule derives them. Nothing reads this at build time. |
| `CodeAndDocs/entry-rulings.json` | findings the maintainer has ruled are facts about the printed book, so `validate_entries.py` stops reporting them. |

#### Why `settled-readings.json` exists

A curated reading is a decision somebody made about a page. When a new rule
starts deriving that same reading from the page itself, the curation becomes
dead weight — it makes the list longer for anyone trying to follow what the
build does, without changing anything. So it comes out of
`curated-readings.json`.

But the decision does not stop being true when the code that honours it changes.
It moves to `settled-readings.json`, where it goes on being **checked** instead
of applied. Two tests in `CodeAndDocs/test_entry_xml.py` keep the two files
honest:

- **`test_no_curated_reading_is_superfluous`** runs each curated entry with and
  without its curation. If the outcome is the same, the rules have caught up and
  the entry belongs in `settled-readings.json`. The test names it.
- **`test_settled_readings_still_hold`** asks the build to produce each retired
  ruling *without* consulting the file. If one no longer matches, the rule that
  replaced the curation has regressed.

#### What to do when a test fires

**`test_no_curated_reading_is_superfluous` names an entry.** A rule now covers
it. Cut the entry out of `curated-readings.json` and paste it into
`settled-readings.json` with two extra fields — `retired` (the date and which
rule made it unnecessary) and `maintainer` (the words the ruling was given in,
so the reason survives). Re-run the tests.

**`test_settled_readings_still_hold` names an entry.** Something in this round's
changes stopped reproducing a ruling that used to hold. This is the point of the
file: decide which it is.

- *The new behaviour is wrong.* Fix the rule. The ruling was right and the test
  has just earned its keep.
- *The new behaviour is right and the old ruling is superseded.* Say so
  explicitly — POL-050 — and update the `readings` in `settled-readings.json`
  with a note saying what superseded it and when.
- *The rule can no longer reach it at all.* Move the entry back to
  `curated-readings.json`. That is not a defeat; it is the file doing its job.

Never delete an entry from `settled-readings.json` to make a test pass. The
whole value of the file is that a ruling given once is never silently dropped.

# Sung Li-May (2018), *Introduction to Kanakanavu Grammar*

This corpus is the Kanakanavu (`xnb`) material from Sung Li-May's 2018 *Kanakanafu yu yufa gailun* [Introduction to Kanakanavu Grammar] (Council of Indigenous Peoples), scraped from the official Alilin e-reader and reconciled page-by-page against the source page images. It comprises 699 grammar sentences — 650 of them with word- and morpheme-level interlinear glossing (3,477 words, 5,048 morphemes) — together with the book's Appendix 2A dictionary as a separate 870-entry lexicon. Text is in the Ortho113 orthography with Mandarin (`zho`) translations and glosses.

## Languages and dialects

Language `xnb` (Kanakanavu); dialect `Kanakanavu`; orthography Ortho113.

Both files, `XML/Kanakanavu/Song_2018_Kanakanavu_Grammar.xml` and
`XML/Kanakanavu/Song_2018_Kanakanavu_Grammar_Dictionary.xml`, carry
`xml:lang="xnb"` and `dialect="Kanakanavu"` on their `<TEXT>` element. All
translations and glosses are Mandarin (`xml:lang="zho"`).

## Source

The Kanakanavu (`xnb`) corpus drawn from Sung
Li-May's 2018 *Kanakanafu yu yufa gailun* [Introduction to Kanakanavu Grammar]
(Taiwan nandao yuyan congshu 16; Council of Indigenous Peoples), scraped from the
[official Alilin e-reader](https://alilin.cip.gov.tw/ebook/5949734115b6abe6caf971/HTML5/pc.html#/page/1).
It produces two files in the
[FormosanBank XML format](https://formosanbank.github.io/FormosanBank/the-bank-architecture/formosanbank-xml-format/):
the grammar's interlinear examples and the Appendix 2A dictionary.

The e-reader serves the book as 268 page images, each with a positioned-text
layer. The page images are the authority; the positioned text was used only as
a reading aid. The dictionary is the language-sorted Appendix 2A (reader
pp. 193-206), cross-checked against the duplicate Chinese-sorted Appendix 2B
(pp. 207-220), which is not published separately.

#### What's in the corpus

| | Grammar | Dictionary (Appendix 2A) |
|---|---|---|
| File (under `XML/Kanakanavu/`) | `Song_2018_Kanakanavu_Grammar.xml` | `Song_2018_Kanakanavu_Grammar_Dictionary.xml` |
| `S` elements | 699 sentences | 870 entries |
| Interlinear analyses | 650 (with `W`/`M`) | — |
| Words / morphemes | 3,477 `W` / 5,048 `M` | — |

There is no audio.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Song-Kanakanavu-Grammar_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

Sung, Li-May. (2018). *Kanakanafu yu yufa gailun* [Introduction to Kanakanavu Grammar]. *Taiwan nandao yuyan congshu*, 16. Council of Indigenous Peoples.

## License

**License:** CC BY-NC 4.0
**Rights source:** Li-May Sung (the author), date not recorded in this repository; evidence: ask maintainer

CC BY-NC 4.0 (Creative Commons Attribution–NonCommercial), by permission of the author (Li-May Sung).

The author (Li-May Sung) granted permission to publish this corpus under
**CC BY-NC 4.0** (Creative Commons Attribution–NonCommercial); the permission
evidence is on Basecamp card
[`10081339846`](https://app.basecamp.com/3340659/buckets/31258415/card_tables/cards/10081339846).
Each `<TEXT>` element's `copyright` attribute records this license as the
bare value `CC BY-NC 4.0`. (Until 2026-10-16 it held the prose "Song, Limei
(2018), Introduction to Kanakanavu Grammar (Council of Indigenous Peoples).
Licensed to FormosanBank under CC BY-NC 4.0 by permission of the author
(Li-May Sung)."; POL-042 allows only a vocabulary value there, so the
permission statement now lives in this section.) Attribution
and non-commercial use are required; see the FormosanBank
[LICENSE](../../LICENSE.md) and [AI-USE-ADDENDUM](../../AI-USE-ADDENDUM.md).

- **Rights:** published under CC BY-NC 4.0 by permission of the author (Li-May Sung); recorded in each `<TEXT>` `copyright` attribute.

## Notes and caveats

#### Translations and glosses

- **Everything is Mandarin; there is no English.** All 10,090 `TRANSL` elements
  are `xml:lang="zho"`. Morpheme glosses are the book's own Chinese category
  labels — `主事焦點` (actor focus), `受事焦點` (patient focus), `完成貌`
  (perfective), `非實現` (irrealis), `重疊` (reduplication), `主格` (nominative),
  `狀態改變` (change of state) — not Leipzig abbreviations.
- **Everything is in Mandarin; there is no English.** All 10,090 translations and glosses are `xml:lang="zho"`. Morpheme glosses use the book's own Chinese category labels — `主事焦點` (actor focus), `受事焦點` (patient focus), `完成貌` (perfective), `非實現` (irrealis), `重疊` (reduplication) — rather than Leipzig abbreviations.
- **Latin script inside a translation or gloss is not only proper names.**
  389 `TRANSL` elements contain Latin letters (135 sentence translations, 123
  `W` glosses, 131 `M` glosses). Most are proper names the book prints in the
  Latin script (`Pani`, `Paicʉ`, `Pori`, `’atai`, `Kini`), but the book also
  writes some labels in Latin: `Ca` in `Ca重疊` (126 occurrences), affix labels
  in capitals (`TA`, `PA`, `KA`, `MATA`, `TAKI`, `I-`/`IN`, `TO`), `Q` for the
  question clitic `=kara`, and Kanakanavu words cited inside glosses (`=cu`) or
  inside explanatory parentheses in sentence translations (`kani`, `misee`,
  `ara-`).

#### What is included and excluded

- **Source-language labels on dictionary headwords are not published.** Appendix 2A marks some headwords `（日語）` (Japanese) or `（借詞）` (loanword), e.g. `kasa（日語）`; the 14 labels are stripped and appear nowhere in the XML.

## Reproduction and processing

### How to reproduce

```bash
bash Corpora/Song-Kanakanavu-Grammar/CodeAndDocs/generate_xml.sh
```

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

The reviewed ledgers and raw source are retained under `CodeAndDocs/`, so a
rebuild does **not** re-scrape. One command rebuilds the published `XML/` from
them:

```bash
CodeAndDocs/generate_xml.sh
```

That is the corpus's only entry point; it runs every step below in order and
writes the two files in `XML/Kanakanavu/` in place, so `git diff` shows exactly
what a rebuild changes. It uses the FormosanBank checkout that contains this
corpus for the shared QC utilities (pass a path, or set `FORMOSANBANK_PATH`, to
use another one). For the interpreter it uses `PYTHON` if that is set, otherwise
`CodeAndDocs/.venv/bin/python3` if that exists, otherwise `python3`. The
dependencies are in `CodeAndDocs/requirements.txt`:

```bash
python3 -m venv CodeAndDocs/.venv
CodeAndDocs/.venv/bin/pip install -r CodeAndDocs/requirements.txt
```

Steps 1 and 3 also rewrite `intermediate/dictionary_ledger.csv` and
`intermediate/interlinear_ledger.jsonl`; step 4 then checks both against their
pinned hashes, so a rebuild that changes either ledger stops there.

`build_xml.py` asserts the source-PDF/positioned-text hashes, the closed
page/candidate inventory, the reviewed-artifact hashes, the ledger counts, and
continuous sentence IDs — so any drift in the source or the ledgers fails the
build loudly. `CodeAndDocs/provenance.json` records the FormosanBank commit the published
XML was last built against (POL-052), and `generate_xml.sh` notes it when the
checkout differs — a note, never a gate: rebuilds run with the current tools. The rebuild is
deterministic: running it twice reproduces the same bytes.

`CodeAndDocs/tests/` holds the extraction regression tests, which also check the
published XML; run them with `pytest` from `CodeAndDocs/`.

#### Project structure

- **`XML/Kanakanavu/`** — the published data: `Song_2018_Kanakanavu_Grammar.xml` and `Song_2018_Kanakanavu_Grammar_Dictionary.xml`.
- **`CodeAndDocs/`** — everything needed to reproduce `XML/` from the source:
  - `scripts/` — acquisition and the reproduction pipeline (see [Processing](#what-each-step-does)).
  - `raw_data/` — the acquired source, retained so the corpus rebuilds without re-scraping: `source.pdf` (the 268 official Alilin page images compiled in order) and `official_text.jsonl` (the official positioned-text layer, one record per page). Both SHA-256-pinned in `scripts/build_xml.py`.
  - `intermediate/` — the reviewed ledgers the build consumes (all hash-pinned in `build_xml.py`): `page_inventory.csv` + `candidate_ledger.csv` (the closed page/candidate review — 268 pages, 443 machine candidates, all with terminal statuses); `source_ledger.csv` (699 included, 14 excluded, with reasons); `dictionary_ledger.csv` (767 headwords; 11 marked bound-excluded); `interlinear_ledger.jsonl` (the recovered `W`/`M` analyses); and `standard_surface_decisions.tsv` (128 exact, source-reviewed standard-tier decisions).
  - `docs/` — `extraction_plan.md`, `extraction_review.md` (the page-by-page review log), `source_manifest.md`, `standard_surface_review.md`, `mt_quality_review.md`, and `clean_clone_reproduction.md`.
  - `tests/` — interlinear-extraction regression tests.
  - `requirements.txt`.

#### QC

Adjudication is recorded in `CodeAndDocs/docs/standard_surface_review.md`,
`CodeAndDocs/docs/mt_quality_review.md`, and
`CodeAndDocs/docs/clean_clone_reproduction.md`.

**No HARD finding from any validator, and `validate_port_readiness` reports
0 HARD / 0 WARN.** Every remaining SOFT row is a documented source property,
explained above:

| Validator | SOFT | What they are |
| --- | --- | --- |
| `validate_xml` | 49 × V148 | the 49 `S` the book prints without a word gloss |
| `validate_text` | 4 × V122, 2 × V133 | one genuine prose parenthetical (S0456, mirrored in its Chinese translation) and the two p.190 em dashes |
| `validate_glosses` | 377 × V060, 3 × V061, 4 × V064 | V060: a host+clitic is one `W` but two whitespace-free words, so W-count and word-count differ by design; V061: three words the book segments without printing a boundary for every unit; V064: the four deliberately unglossed `M` |
| `validate_duplicate_sentences` | 63 groups | 34 dictionary homographs with different translations, 1 stress-variant pair that folds to one standard form, 28 grammar repeats at distinct source locators. No exact same-locator duplicate; nothing is deduplicated |

Reproduce any of them with, e.g.:

```bash
python QC/validation/validate_text.py by_path --path Corpora/Song-Kanakanavu-Grammar/XML
```

### What each step does

#### Upstream (one-time; the outputs are committed, so you do not re-run these)

**A. Acquire the source** — `scripts/acquire_source.py` downloads every numbered
Alilin page image and its `iPhone/text/<page>.xml` positioned-text record,
verifies the page count, compiles the images into `raw_data/source.pdf`, and
writes `raw_data/official_text.jsonl`. The **page images are authoritative**; the
positioned text is a reading aid only. (The two output paths are passed as
`--pdf` and `--text-jsonl`; the script checks that the reader's manifest
declares 268 pages.)

**B. Build machine candidates** — `scripts/build_candidates.py` scans the
positioned text for labeled examples and writes `page_inventory.csv` +
`candidate_ledger.csv` (all `UNREVIEWED`).

**C. Human review** (the heart of the corpus) — every one of the 268 pages was
reconciled by hand against the page image: expanding/repairing machine
candidates, recovering examples that had no candidate, restoring word boundaries
and punctuation the text layer had dropped, and excluding non-sentences. The
result is `source_ledger.csv` (699 included, 14 excluded). The full page-by-page
log is `docs/extraction_review.md`.

#### Rebuild pipeline (`CodeAndDocs/generate_xml.sh`)

Before step 1 the script checks that the FormosanBank checkout has
`QC/cleaning/clean_xml.py`, and prints a note on stderr if that checkout's
commit differs from the one in `provenance.json`.

1. **Extract the dictionary** — `extract_dictionary.py` reconstructs Appendix 2A
   from the positioned text, cross-checking barred vowels against the duplicate
   Chinese-sorted Appendix 2B and applying documented OCR corrections →
   `dictionary_ledger.csv`.
   In detail: it reads reader pp. 193-206 (2A, two columns per page) and
   pp. 207-220 (2B). Where a 2A headword and a 2B headword have the same letters
   (ignoring the `u`/`ʉ` difference) and overlapping translations, every `u`
   that 2B prints as `ʉ` becomes `ʉ`. It then applies the 22 record-keyed
   `FORM_CORRECTIONS`, strips the `（日語）`/`（借詞）` source-language labels, and
   marks the 11 headwords that end in `-` as `included = no`, with the reason
   "Source prints a bound citation form with a trailing hyphen and supplies no
   unattached surface". It writes all 767 headwords, with IDs
   `song-2018-kanakanavu-dictionary-0001` to `-0767`.

2. **Verify barred-vowel reconciliation** — `reconcile_barred_vowels.py --check`
   confirms the `u`/`ʉ` corrections between the sentence ledger and the dictionary
   are consistent (fails if they have drifted).
   Concretely: for each word of each sentence in `source_ledger.csv` it looks up
   the dictionary forms with the same letters (ignoring `u`/`ʉ`, apostrophe style
   and accents); if every such form has `ʉ` where the sentence has `u`, the row
   still needs a correction. With `--check` it prints those rows and exits 1 if
   there are any; it writes nothing.

3. **Recover interlinear analyses** — `extract_interlinear.py` aligns each
   reviewed sentence's printed word and gloss lines into `W`/`M` analyses (650
   analyses; 3,477 `W`; 5,048 `M`), using position-based alignment plus
   source-checked overrides for cells the text layer merged →
   `interlinear_ledger.jsonl`. W forms keep the source's `-`, `=`, and `<…>`
   notation. Under POL-014, an infixed root keeps a gap hyphen and the infix is
   written `-X-`; under POL-015, each clitic M keeps a leading `=`. Four override
   tables in that script carry what the positional aligner cannot derive, each
   keyed by record id: `GLOSS_OVERRIDES` (28 sentences where the text layer
   merged two adjacent printed gloss cells), `TOKEN_JOIN_OVERRIDES` (one form the
   text layer split), `ANALYSIS_OVERRIDES` (three sentences whose layout cannot
   be recovered without inventing a word boundary) and
   `MORPHEME_OVERRIDES` (five page images whose printed form and gloss lines do
   not align one-to-one, preserving partial source glossing without inventing
   missing M glosses). Only the `MORPHEME_OVERRIDES` entries cite their reader
   page in the code. All are applied to the **original** tier at extraction,
   before any standard tier exists — see "Recorded per-record corrections" under
   Notes for the full list.
   Other things this step does, all in the same script: it skips reader
   pp. 187-220 (the punctuation appendix and the dictionary) and the two
   unglossed body examples `S0046` and `S0172`; it builds a lookup of known
   glosses from the dictionary ledger and from cleanly aligned examples on
   pp. 47-184 and 221-262, and uses it to choose between possible alignments;
   it restores `ʉ` in analysis forms from the dictionary the same way step 2
   checks sentences; it moves a gloss fragment that the text layer attached to
   the wrong cell (`格`, `主`/`事焦點`, `屬格`) back to its neighbour; where a
   printed form offers `a/b` alternatives it keeps the one that occurs in the
   sentence; and for ledger labels marked `-no-sua`/`-without-sua`, `-no-na` or
   `-no-miura` it leaves out the word that the sentence omits. A sentence for
   which no alignment passes the gloss checks gets no analysis.

4. **Build the XML** — `build_xml.py` writes both files (after asserting all
   hashes/counts):
   - **Grammar:** 699 `S`; the 650 with a printed analysis get `W`/`M`. The
     other **49 carry a translation but no `W`/`M`**, because the book prints
     none: 47 are the punctuation examples of Appendix 1 (pp. 187-191, which is
     a punctuation table, not a glossed text), and 2 are body examples the book
     leaves unglossed (5-2 on p.80, footnote 27 on p.118). No analysis is
     invented for them, so they are the corpus's V148 `W_less_S` findings.
     Each `S` gets a `source` attribute naming the reader page, the ledger label
     and the review note. The `--` in `S0469` and `S0472` becomes a single `-`
     in the original FORM, with a `notes` attribute saying so (the build stops
     if any other sentence contains `--`). For `S0143` and `S0149` the printed
     parenthetical paraphrase is moved out of the translation into the
     `TRANSL`'s `notes` attribute (see the table under Notes). In `W` forms any
     parenthesised material is deleted (`’arup(a)-ara` → `’arup-ara`).
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
     The split outputs come from the `dictionary` rows of
     `standard_surface_decisions.tsv`; the 26 dropped variant IDs are a fixed
     list in `normalize_standard_forms.py` (`DUPLICATE_VARIANT_ENTRY_IDS`), and
     the build stops if the computed duplicates differ from it.
   - Both `<TEXT>` elements get `xml:lang="xnb"`, `dialect="Kanakanavu"`,
     `copyright="CC BY-NC 4.0"`, the citation and BibTeX citation, and a
     `source` attribute naming the reader URL and the source PDF's SHA-256.

5. **Re-apply manual edits** — `apply_manual_edits.py` (FormosanBank) re-applies
   the recorded hand edits in `CodeAndDocs/manual_edits.xml` before any cleaning
   or derivation, so every downstream tier is built from the repaired original.
   One record: the p.69 `takananga` typesetting slip (see Notes). The script
   warns loudly if a record has become a no-op.
   Flags: `--corpora_path XML/`.

6. **Clean** — `clean_xml.py` (FormosanBank) does canonical Unicode / HTML-entity
   / punctuation normalization.
   Flags: `--corpora_path XML/`. Its per-run report, `XML/cleaner_warnings.csv`,
   is deleted at the end of the build (it is reviewed during QC and is not
   corpus data).

7. **Create the standard tier** — `standardize.py --remove_accents`
   (FormosanBank). The source is already Ortho113, so no conversion table is
   needed; `--remove_accents` copies the original tier and folds the source's
   acute stress vowels (`á é í ó ú`, and the decomposed `ʉ́`) out of the
   standard tier only. Stress is suprasegmental annotation in this source, not
   Ortho113 orthography, so the original tier keeps the printed accents.

8. **Apply reviewed surface decisions** — `normalize_standard_forms.py` walks
   the 128 exact decisions in `standard_surface_decisions.tsv`. No marker is
   removed by a blanket rule, and in practice this step **rewrites exactly one
   sentence**: the song on p.190, whose lyric hyphens resolve to independently
   attested word boundaries. The other 127 decisions are *verified*, not
   applied — `build_xml.py` has already emitted one clean surface per dictionary
   entry, and the two break-punctuation sentences are unchanged text carrying a
   `notes` attribute. The step also asserts that no analysis marker survives in
   any sentence-level standard form. Ordinary prose parentheses are left
   unchanged.
   It stops if the manifest no longer has exactly 128 decisions (125 dictionary,
   3 grammar, 11 bound exclusions, 140 extra entries), if the hyphen-bearing
   grammar sentences are not exactly the three with decisions, if a decision's
   expected source text or page no longer matches the XML, or if the dictionary
   no longer has 870 entries.

9. **Add phonology** — `add_phonology.py --orthography Ortho113`
   (FormosanBank), both tiers. PHON is a segmental tier, so the shared utility
   folds stress accents itself before mapping; the original FORM keeps its
   accents and the PHON is clean IPA. There is no corpus-specific phonology
   mapping and no corpus-specific wrapper.

Last, the script deletes `XML/cleaner_warnings.csv` and prints
`Rebuilt …/XML/Kanakanavu/`.

**Standard gloss tier** (final step): `QC/glossing/apply_gloss_standard.py` adds `TRANSL kindOf="standard"` glosses beside every original gloss (POL-036 — the original tier is never changed), converting each gloss code according to this corpus's standardization list, [Glossing/ConversionTables/Song-Kanakanavu-Grammar.tsv](https://github.com/FormosanBank/FormosanBank/blob/main/Glossing/ConversionTables/Song-Kanakanavu-Grammar.tsv) (segmentation conventions in [Song-Kanakanavu-Grammar.rules.tsv](https://github.com/FormosanBank/FormosanBank/blob/main/Glossing/ConversionTables/Song-Kanakanavu-Grammar.rules.tsv)). Codes without a ruled mapping are copied verbatim, so the standard tier is always complete; the project-wide approach, vocabulary and per-language gloss dictionaries are documented in [Glossing/README.md](https://github.com/FormosanBank/FormosanBank/blob/main/Glossing/README.md).

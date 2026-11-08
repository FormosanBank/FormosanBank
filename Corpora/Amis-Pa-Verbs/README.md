# Wu (2006) Amis pa-verbs

This corpus contains 29 Coastal Amis sentence variants from Joy Wu's 2006 paper, [The Analysis of Pa-Verbs in Amis](https://sil-philippines-languages.org/ical/papers/wu_joy-pa%20verbs.pdf). The paper identifies Haian/Coastal Amis from Changpin, Taitung. The XML has 154 W and 265 M, 33 sentence translations, and no audio. `TEXT/@source` carries the paper's URL and the SHA-256 of the transcribed PDF.

## Languages and dialects

Language is Amis (`ami`), dialect `Coastal`. The corpus is one file, `XML/Amis/pa-verbs.xml`, whose `<TEXT>` declares `xml:lang="ami"` and `dialect="Coastal"`.

Page 1 identifies Haian/Coastal Amis from Changpin, Taitung.

## Source

Wu (2006), The Analysis of Pa-Verbs in Amis, is a 13-page conference paper. Coastal Amis (`ami`) sentence examples from Joy Wu's [The Analysis of Pa-Verbs in Amis](https://sil-philippines-languages.org/ical/papers/wu_joy-pa%20verbs.pdf), presented at the Tenth International Conference on Austronesian Linguistics, 17–20 January 2006.

The inventory covers sentence examples on pages 6–10 of the 13-page paper. It retains 29 grammatical sentence variants, including both person/car readings of 20c and both case forms of 36a. The 15 exclusion entries identify two repeated earlier examples, seven ungrammatical examples, three forbidden alternatives, one starred translation and two questionable examples. Lexical tables, theory prose and references are accounted for separately in the page ledger, not claimed as sentence records.

All 13 source pages were reviewed. The corpus covers the sentence examples on pages 6–10; lexical tables and theory discussion are outside this sentence-example scope. The recorded exclusions cover repeated earlier examples, ungrammatical and questionable examples, forbidden alternatives and one starred translation. Person/car readings in 20c and both case forms of 36a remain separate, fully aligned variants.

Final XML has 29 S, 154 W, 265 M, 448 original and 448 standard FORM/PHON parents, and no audio. `TEXT/@source` carries the paper's URL and the SHA-256 of the PDF it was transcribed from. The source transcriptions, exclusions and page coverage are under `CodeAndDocs/`.

The source paper supplies no audio.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Amis-Pa-Verbs_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

Wu, Joy. 2006. The analysis of pa- verbs in Amis. Paper presented at the Tenth International Conference on Austronesian Linguistics, 17–20 January 2006, Puerto Princesa City, Palawan, Philippines.

## License

**License:** CC BY-NC-SA 4.0

**Rights source:** SIL International, 2025-01-25; evidence: ask maintainer

The date records the maintainer's verification of SIL's published archive terms, including the retained January 24 screenshot. Those terms apply unless an item states otherwise; this paper contains no conflicting grant. The optional PDF verification copy is not a required build input.

**CC BY-NC-SA 4.0.** SIL International's published archive terms apply unless an item states otherwise; this paper has no conflicting terms. The maintainer verified the grant in January 2025. Credit Joy Wu and SIL International, retain the noncommercial/share-alike conditions, and identify the transcription and normalization changes. Rights evidence is available from the maintainer.

The corpus is also subject to the central FormosanBank [Terms of Use](https://formosanbank.github.io/FormosanBank/additional-resources/terms-of-use/) and [AI Use and Commercial Licensing](https://formosanbank.github.io/FormosanBank/additional-resources/ai-use-and-commercial-licensing/).

## Notes and caveats

The paper segments `Pa-fli` but gives only the whole-word gloss `give`. Its two morphemes therefore have no individual glosses. (The source segments `Pa-fli` but gives only the whole-word gloss `give`; its two morphemes therefore have no individual glosses.) Other source form/gloss mismatches and analytic nulls are preserved; the source notes explain the reviewed cases. Source form/gloss mismatches and analytic nulls are preserved. Source `payau`, `ni/GEN-NCM`, `ku/NOM-NCM` and source `CaU` with additive standard `CAU` remain.

Original and standard PHON use different inventories, including the source's narrower vowel and lateral values. The conversion report records these differences; the tiers do not imply strict phonemic equivalence. In particular the `standard` tier merges Wu's `u`/`o` distinction, because Ortho113 Coastal writes one `o` for /o~u/; the `original` tier keeps the distinction. Original and standard PHON use different vowel and lateral inventories, so the tiers do not imply strict phonemic equivalence — in particular the standard tier merges Wu's `u`/`o` distinction, because Ortho113 Coastal writes one `o` for /o~u/.

Wu prints example 36a in two case forms. They are two `S` blocks, `s36a` and `s36a-opt`, because the alternation is a competing lexeme with a different gloss (`t-u`/DAT-NCM against `i`/PREP) rather than a spelling variant (POL-027/POL-028). They are two sentences, `s36a` and `s36a-opt`, because the alternation is a competing lexeme with a different gloss (`t-u`/DAT-NCM against `i`/PREP) rather than a spelling variant.

Seven analytic nulls are retained as `∅` in original S/W/M tiers; shared standardization removes them from S standard. Nulls are silent in PHON, except a whole-null FORM receives PHON `∅`.

The apostrophe is **not** converted. An earlier pass read Wu's `'` as the glottal stop /ʔ/ and mapped it to Ortho113's `^`; that was reverted in review. Ortho94 and Ortho113 agree that `'` is /ʡ/ and `^` is /ʔ/, so the claim departed from both standards rather than from one of them; the corpus carries the apostrophe in two tokens of a single word type and no `q` or `^` at all, so there is no contrast in it to record; and the bank spells this very lexeme with an apostrophe — `(ma)na'ay` 'not want' appears 81 times in standard tiers across the Amis corpora with `'` and never with `^`. [Source and conversion notes](CodeAndDocs/README.md) document these limitations and the exact source-inherent findings protected by tests.

## Reproduction and processing

### How to reproduce

With FormosanBank's documented Python dependencies installed:

```bash
bash Corpora/Amis-Pa-Verbs/CodeAndDocs/generate_xml.sh
```

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

XML and reproducible build inputs are in the Amis-Pa-Verbs directory (`XML/` and `CodeAndDocs/`).

In the development repository, set `FORMOSANBANK_ROOT` to the selected current FormosanBank checkout and run `bash CodeAndDocs/generate_xml.sh`. `PYTHON` selects the interpreter. The build reads committed tables, cleans, standardizes `u` to `o` (the source apostrophe is not converted; see "Notes and caveats"), and generates PHON using shared tools. It needs no PDF, network, Git metadata or historical tool checkout. Record the actual tools used for committed output in [provenance.json](CodeAndDocs/provenance.json); this record does not select or gate tools — the build always runs the tools in the checkout it is invoked from (POL-052).

Run `CodeAndDocs/generate_xml.sh` from the corpus package. It builds from committed inputs, applies corrections, cleans, standardizes and generates PHON with current shared tools, without a private PDF, network fetch or historical Git checkout. [provenance.json](CodeAndDocs/provenance.json) records the tools used for the committed output and does not pin future builds. Validation and source refresh are separate.

#### Validation

For read-only validation, run `QC_REPORT_DIR=/outside/corpus/reports bash CodeAndDocs/validate.sh` with the same environment. The conversion comparison reports a reviewed phoneme-level mismatch and therefore returns a nonzero command status. Review every report; script success alone cannot establish readiness. Source refresh and human source review remain separate from generation.

`validate.sh` refuses a `QC_REPORT_DIR` inside the corpus, runs each check below, writes each check's log and its exit code (`exit_codes.csv`) to that directory, and exits nonzero if any check did: `audit_source_alignment.py` (`source-alignment`); the corpus's own tests (`source-tests`); the shared `validate_xml.py`, `validate_text.py` and `validate_glosses.py` (`--no-exit-on-hard`); `audit_gloss_scrape.py --no-source`; `validate_duplicate_sentences.py`, `orthography_extract.py` and `validate_orthography.py` on the original and the standard tier; `validate_vocabulary.py` on the standard tier; `validate_conversion_table.py` for Ortho94 → Ortho113 Coastal through `Amis_94_113.tsv`; `validate_dialect.py`; `validate_registries.py`; and `validate_port_readiness.py`.

This corpus has its own build test suite at [`CodeAndDocs/tests/`](CodeAndDocs/tests/), which pins the reviewed source decisions — exact sentence and morpheme ids, counts, the unglossed `Pa-fli` boundary, and the retained exclusions — so a change to the shared tools or to the transcription cannot silently move them. Run it with `python -m pytest Corpora/Amis-Pa-Verbs/CodeAndDocs/tests`; `CodeAndDocs/validate.sh` also runs it as its `source-tests` check. **It is not collected by the repository's own `pytest` run**, whose `testpaths` is `tests/`, so it does not gate CI. The corpus carries its own build test suite under `CodeAndDocs/tests/`, which pins the reviewed source decisions — exact sentence and morpheme IDs, counts, the unglossed `Pa-fli` boundary and the retained exclusions — so neither a shared-tool change nor a transcription edit can move them silently. It runs as the `source-tests` check of `CodeAndDocs/validate.sh`, and is not part of the repository-wide test run.

### What each step does

`generate_xml.sh` resolves the FormosanBank checkout (`FORMOSANBANK_ROOT`, default three folders above `CodeAndDocs/`) and the interpreter (`PYTHON`, default `python3`), stops unless `QC/cleaning/clean_xml.py` exists there, and then runs five steps in this order, stopping at the first failure.

#### 1. `CodeAndDocs/build_xml.py`

Reads `source_examples.tsv` (it must have exactly the expected columns and 29 rows with unique ids), `source_manifest.tsv` (exactly one source with a URL and a 64-character SHA-256), `gloss_standardization.tsv` and `morpheme_ids.tsv`, and writes `XML/Amis/pa-verbs.xml`.

- `<TEXT>`: `xml:lang="ami"`, `dialect="Coastal"`, `copyright="CC BY-NC-SA 4.0"`, the citation and BibTeX written in the script, and `source` built from the manifest as "<url>; source PDF sha256 <hash>".
- Each row becomes one `S`. Its original `FORM` is the row's segmented words with `-`, `<`, `>` and `=` removed (a word beginning `∅-` is kept as written), plus the row's sentence ending (empty, `.` or `!`). Its English `TRANSL` is `translation_1` (with its note, if any); `translation_2`, when present, is a second `TRANSL` with `ver="alt"`.
- Each word becomes a `W` with the original `FORM` and its gloss. If `gloss_standardization.tsv` changes the gloss (its one row: `CaU` → `CAU`), the source gloss is written as `TRANSL kindOf="original"` and the normalized one as `TRANSL kindOf="standard"`.
- A word containing `-` is split into one `M` per part. If the number of form parts and gloss parts differ, the parts are kept with no gloss (this is `Pa-fli`/`give`); otherwise each part gets its gloss. A word without `-` is one `M`. M ids come from `morpheme_ids.tsv` where listed (`s32aw0m_a`, `s32aw0m_b` replace the retired `s32aw0m0`), otherwise `<word id>m<index>`.

The committed transcription tables preserve source spelling, W glosses, translations, exclusions and stable source IDs. The current source review restores obligatory `i/PREP` in example 32c (`*(i)`), 22 printed sentence endings and the two printed parts of `Pa-fli`. The latter retains W gloss `give`; its M parts have no individually supplied gloss and remain unglossed. No sentence or free translation is removed. Excluded examples are listed with their reasons in `CodeAndDocs/rejected_source_examples.tsv`; `source_coverage.tsv` accounts for every page and `direct_source_checks.tsv` keeps the raw notation of the difficult cases.

#### 2. `QC/cleaning/apply_manual_edits.py --corpora_path XML`

Re-applies the hand edits recorded in `CodeAndDocs/manual_edits.xml`. That file is an empty `MANUAL_EDITS`, so this step changes nothing. The six earlier reviewed correction records have been pruned: the transcription tables encode the same decisions, so each was re-applied as a no-op on every build. The decisions and their source locators remain in the corpus package (`CodeAndDocs/review_decisions.md`).

#### 3. `QC/cleaning/clean_xml.py --corpora_path XML --warnings_dir CodeAndDocs/reports`

The shared cleaner. `--warnings_dir` writes its per-run report to `CodeAndDocs/reports` instead of into the published `XML/` (POL-033).

#### 4. `QC/utilities/standardize.py --corpora_path XML --tsv_path Orthographies/ConversionTables/Amis_94_113.tsv --target_column Coastal`

Writes the `standard` FORM tier from the original using the bank's shared Ortho94 → Ortho113 table, `Coastal` column. `Amis_94_113.tsv` is a per-dialect table with no `standard` column, so the target column is the dialect; passing `standard` matches nothing and silently skips the conversion. In this corpus the conversion's visible effect is `u` → `o`; the table has no apostrophe row, so `'` is unchanged. Standardization also removes analytic nulls from the S standard FORM only.

#### 5. `QC/utilities/add_phonology.py --corpora_path XML --language Amis --orthography Orthographies/Ortho94`

Writes PHON for the original and standard tiers. Original PHON uses [`Orthographies/Ortho94/Amis.tsv`](../../Orthographies/Ortho94/Amis.tsv) — Wu's letter inventory is Coastal Ortho94 — and converts through the existing [`Orthographies/ConversionTables/Amis_94_113.tsv`](../../Orthographies/ConversionTables/Amis_94_113.tsv); standard PHON uses the registered Ortho113 Coastal profile. No corpus-specific orthography or conversion table is registered. Their phoneme inventories differ. [Source and conversion notes](CodeAndDocs/README.md) explain the reported differences without claiming strict phonemic equivalence or changing originals to satisfy a validator.

Original PHON uses [`Orthographies/Ortho94/Amis.tsv`](../../Orthographies/Ortho94/Amis.tsv), the bank's existing Coastal Ortho94 profile, and converts through the existing [`Amis_94_113.tsv`](../../Orthographies/ConversionTables/Amis_94_113.tsv); standard PHON uses Ortho113. Wu's letter inventory is Coastal Ortho94, so no corpus-specific orthography or conversion table is registered. The `u→o` spelling conversion merges Wu's `u`/`o` into Ortho113 Coastal's single `o`, which is the one reviewed phoneme-level difference.

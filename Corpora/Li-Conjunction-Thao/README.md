# Li (2014), *Conjunction in Thao*

This corpus comprises all 28 Thao example sentences from Paul Jen-Kuei Li's paper *Conjunction in Thao* (2014), a study of coordination and subordination in Thao — a Formosan language spoken at Sun-Moon Lake in central Taiwan. The 24 numbered examples carry word- and morpheme-level interlinear glossing aligned to the paper's analysis; the example quoted inline in footnote 5 and the three in footnote 7 are included as sentence-only (the source glosses none of them). Each sentence provides Li's source transcription (the `original` tier) alongside a rendering in FormosanBank's common Thao orthography (the `standard` tier), with English translations.

## Languages and dialects

Thao (ISO 639-3 `ssf`, glottocode `thao1240`), dialect `Thao`. The corpus has one file, `XML/Thao/li_2014_conjunction_in_thao.xml`, whose `TEXT` element carries `xml:lang="ssf"` and `dialect="Thao"`.

## Source

Paul Jen-Kuei Li's article in *Papers from 12-ICAL, Volume 2*, pp. 401–409, supplies this Thao (`ssf`, dialect `Thao`) corpus. The [official ANU volume](https://openresearch-repository.anu.edu.au/items/8bfb8bf0-2f58-4eae-947c-bf9af50faf9f) uses Li's scholarly transcription and aligned English glosses. The article occupies PDF pages 394–402 of the volume; the exact PDF used (file name, size, SHA-256, download URL, access date) is recorded in [source_manifest.json](CodeAndDocs/source_manifest.json).

`XML/Thao/li_2014_conjunction_in_thao.xml` contains 28 sentences: examples 1–24, the inline example in footnote 5, and the three examples in footnote 7. There are 211 W and 169 M elements, with 408 original and 408 standard FORMs and the same numbers of original and standard PHONs. The four unglossed footnote examples remain sentence-only.

Source W/M glosses remain lone, untiered TRANSL elements under POL-036.

Audio: None supplied by the source.

#### Source corrections

[Reviewed records](CodeAndDocs/reviewed_examples.tsv) preserve the printed readings; [source corrections](CodeAndDocs/source_corrections.tsv) record the exact before/after fields applied before W/M generation. They retain Joshua's reviewed `S → ʃ` and `D → ð` repairs from [the original port](https://github.com/FormosanBank/FormosanBank/commit/541fa53e8), plus the published English corrections (`firewood on`, `person`, `wild animals`) and sentence punctuation. Corrections never apply to gloss codes or metadata. Infix roots retain the gap hyphen, with the infix represented separately (POL-014).

The `S → ʃ` and `D → ð` repairs are the two source-transcription typos checked against Blust's *Thao Dictionary*; they are applied to the original FORM of four sentences (`li2014_thao_S021`, `S025`, `S026`, `S027`; the last three are the footnote-7 examples, which Li quotes from Blust 2003).

#### Coverage

[The coverage ledger](CodeAndDocs/source_ledger.csv) accounts for 28 included units and four pages without utterances across all nine article pages (PDF 394–402). The footnote-5 addition was recovered by `CodeAndDocs/scripts/recover_footnote5.py` from the volume identified in [source_manifest.json](CodeAndDocs/source_manifest.json). Its existing source text and translation are retained without new glosses or segmentation. Existing TEXT/S/W/M IDs and source associations remain unchanged; the addition uses `li2014_thao_fn5_1`.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Li-Conjunction-Thao_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

Li, P. J.-K. (2014). Conjunction in Thao. In I Wayan Arka & N. L. K. Mas Indrawati (Eds.), *Papers from 12-ICAL, Volume 2: Argument realisations and related constructions in Austronesian languages* (pp. 401–409). Asia-Pacific Linguistics.

See the FormosanBank [Terms of Use](https://formosanbank.github.io/FormosanBank/additional-resources/terms-of-use/).

## License

**License:** CC BY 4.0

**Rights source:** the article's own licence statement (Li 2014, published CC BY 4.0); evidence: ask maintainer

Creative Commons Attribution 4.0 International (CC BY 4.0).

The source article is published under Creative Commons Attribution 4.0 International. Until 2026-10-17 `TEXT/@copyright` carried that name in prose; POL-042 requires the exact vocabulary value `CC BY 4.0`.

## Notes and caveats

Morphology remains partial: 140 of 211 W elements have no M child, and the four unglossed footnote examples have no W tier. These produce SOFT V144 and V148 findings. The [merged corpus decision](https://github.com/FormosanBank/FormosanBank/commit/64654b68a) requires a linguistic ruling before adding the missing M analyses. [Issue #102](https://github.com/FormosanBank/FormosanBank/issues/102) was closed as not planned on September 9, 2026, without a replacement ruling. The published partial analysis is preserved.

A note on segmentation notation: Li's interlinear markers (`-` and `=` for morpheme/clitic boundaries, `<...>` for infixes) are preserved in the `original` tier and in the word/morpheme tiers, where they carry the morphological analysis. The **sentence-level** `standard` tier is flattened running text with no markers — in this source the hyphen is always a morpheme boundary, never a letter (Li writes the Thao glottal stop as `ʔ`).

The original tier is not a byte-for-byte copy of the print: the source corrections listed under "Source corrections" above (the `S → ʃ` / `D → ð` repairs and the English and punctuation fixes) are applied before any tier is built. The printed readings are kept in `CodeAndDocs/reviewed_examples.tsv`.

## Reproduction and processing

### How to reproduce

```bash
bash Corpora/Li-Conjunction-Thao/CodeAndDocs/generate_xml.sh
```

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

Use Python 3.11 or newer and the current FormosanBank Python dependencies. All required corpus inputs are committed under `CodeAndDocs/`; neither the PDF, a private repository, nor historical Git objects are required for generation.

From the corpus folder, the FormosanBank checkout and the Python interpreter can be named explicitly (by default `generate_xml.sh` uses the checkout three levels above `CodeAndDocs/` and `python3`):

```bash
FORMOSANBANK_ROOT=/path/to/FormosanBank PYTHON=python3 ./CodeAndDocs/generate_xml.sh
```

The corpus is fully regenerable from the committed reviewed source records: `CodeAndDocs/generate_xml.sh` rebuilds the XML (fresh original tiers from the reviewed records and recorded corrections → shared cleaning → standardization to the Ortho113 standard tier → phonology) with the current FormosanBank tools; `CodeAndDocs/provenance.json` records the FormosanBank commit of the published build. See the corpus README for details, including the two source-transcription typos corrected in code against Blust's *Thao Dictionary* (see "Source corrections" under Source, above).

The entry point builds fresh original tiers from the reviewed records and exact corrections, runs shared cleaning, standardizes through `Orthographies/ConversionTables/Thao_Li_113.tsv` with `--hard-remove-segmentation`, finalizes S-standard infix brackets, then runs `add_phonology.py --orthography Li`. Ortho113 is the standard tier; Li is the original PHON profile. Current shared phonology strips nonsegmental stress accents, fixing 20 published original-PHON placeholder values while preserving the accented original FORMs (POL-003).

**POL-047 deviation:** No `apply_manual_edits.py` step is needed: the documented corrections are applied to fresh source records in the builder. The merged Li-specific S-standard bracket finalizer remains between standardization and phonology; shared `--hard-remove-segmentation` now owns hyphens and clitics. Original and W/M analysis notation stays intact. This preserves the scope of the existing corpus ruling while shared standardization lacks the S-infix option.

[provenance.json](CodeAndDocs/provenance.json) records the tools used for the committed build. The entry point updates it from the supplied FormosanBank Git checkout; a Git-free export retains that record. It never selects or requires an older checkout. Source recovery is separate: `python3 CodeAndDocs/scripts/recover_footnote5.py /path/to/official-volume.pdf` verifies the manifest before reproducing the one-time footnote recovery.

#### Review and validation

```bash
FORMOSANBANK_ROOT=/path/to/FormosanBank PYTHON=python3 \
OUTPUT_DIR=/path/to/new-external-report-directory \
SOURCE_PDF=/path/to/official-volume.pdf ./CodeAndDocs/validate.sh
```

`SOURCE_PDF` is optional for validation. Without it, the script explicitly skips PDF verification and Group C source alignment (the comparison of the XML against the source text that `QC/validation/audit_gloss_scrape.py` calls "Group C"); it still checks the committed records and output. With it, Poppler verifies the PDF and extracts only the article pages. Validation is separate from generation and reports remain outside the corpus. Review every CSV and warning; a successful command is not a source-fidelity verdict.

Focused tests protect the reviewed corrections, infix shape, footnote coverage, stable IDs, partial M decision, and derived-tier boundaries. The source audit checks all output anchors against the records and corrections. It supplements direct page review and does not establish new linguistic analysis.

### What each step does

`generate_xml.sh` stops at the first failing step (`set -euo pipefail`). It first checks that `QC/cleaning/clean_xml.py` exists in the FormosanBank checkout, then runs, in order:

1. **`CodeAndDocs/scripts/build_xml.py`** (corpus-specific builder).
   - Reads `CodeAndDocs/reviewed_examples.tsv` (one row per sentence: ID, source locator, PDF and printed page, example label, printed original, gloss line, English translation, notes). It exits unless there are exactly 28 rows, all marked `included = yes`.
   - Applies `CodeAndDocs/source_corrections.tsv`: for each correction whose `id` matches a record, the named field must equal `before` exactly (otherwise the build stops with "Correction source changed") and is replaced by `after`. The printed readings in `reviewed_examples.tsv` are never rewritten.
   - Checks every record's PDF/printed page pair and locator against a fixed table (examples 1–5 on PDF p. 395, 6–8 and footnote 5 on p. 396, 9–14 on p. 397, 15–20 on p. 398, 21–24 and footnote 7 on p. 399), and, for glossed records, that the number of words equals the number of gloss words and that each word's morphemes line up with its gloss.
   - Writes `XML/Thao/li_2014_conjunction_in_thao.xml` from scratch: a `TEXT` with `citation`, `BibTeX_citation`, `copyright="CC BY 4.0"`, `xml:lang="ssf"`, `dialect="Thao"`, `glottocode="thao1240"` and `source`; one `S` per record (with its `id` and `source` locator), holding the original `FORM` and the English `TRANSL`.
   - For glossed records only, one `W` per whitespace-separated word (edge punctuation `.,!?;:…` stripped), holding the word's original `FORM` and its gloss as an English `TRANSL`. Each word is split into `M` elements at `-` and `=`; a clitic keeps a leading `=` on both form and gloss. An infix `<x>` becomes its own `M` written `-x-` with gloss `<X>`, and the root keeps a hyphen where the infix was removed (e.g. `ʃ<uŋ>kaʃ` → root `ʃ-kaʃ` plus infix `-uŋ-`). A word that is a single morpheme gets no `M` child: this preserves the published partial analysis (see Notes and caveats).
   - Rewrites `CodeAndDocs/source_ledger.csv`: the 28 included records plus four "page coverage" rows for PDF pages without utterances (394: title, introduction, rights notice; 400: summary prose only; 401: frequency table of counts; 402: references only).
2. **`QC/cleaning/clean_xml.py --corpora_path XML`** — the shared cleaner, run on the corpus's `XML/` folder. No `--warnings_dir` is passed, so if the cleaner has warnings its `cleaner_warnings.csv` is written into `XML/` (and removed by a run that finds nothing).
3. **`QC/utilities/standardize.py --tsv_path Orthographies/ConversionTables/Thao_Li_113.tsv --target_column standard --hard-remove-segmentation`** — adds a `standard` `FORM` beside every `original` `FORM` (sentence, word and morpheme), converting Li's transcription to Ortho113 with the Li→Ortho113 conversion table. On the sentence-level standard `FORM`, `--hard-remove-segmentation` strips the `-` and `=` segmentation markers even though `-` is a letter in Thao Ortho113 (without the flag the tool would keep them and warn).
4. **`CodeAndDocs/scripts/flatten_standard_segmentation.py XML`** — deletes `<` and `>` from the sentence-level standard `FORM` only; word and morpheme tiers and the original tier keep their infix brackets.
5. **`QC/utilities/add_phonology.py --orthography Li`** — writes `PHON` elements: original `PHON` from the Li orthography tables, standard `PHON` from Ortho113.
6. **Provenance (inline Python in `generate_xml.sh`)** — if the FormosanBank checkout is a Git checkout, writes its current `HEAD` commit to `CodeAndDocs/provenance.json`; otherwise it requires that file to exist already and stops if it does not.

`validate.sh` is separate and writes nothing into the corpus. It requires `OUTPUT_DIR` to be a new absolute directory outside the corpus, links every other published corpus into `OUTPUT_DIR/published-view` (for cross-corpus checks), and logs each step to `OUTPUT_DIR/<step>.log`. Steps, in order: `audit_source_fidelity.py --stage final` (with `--source` when `SOURCE_PDF` is set: size, SHA-256 and page count of the PDF, plus known source snippets; always: the manifest, the 32-row ledger, the 28 records against the XML at S/W/M level, 408 FORMs and PHONs per tier, no `-`, `=`, `<`, `>` in sentence standard FORMs); when `SOURCE_PDF` is set, `pdftotext` of PDF pages 394–402 and `audit_gloss_scrape.py` against that text; `audit_gloss_scrape.py --no-source`; the unit tests in `CodeAndDocs/tests/`; `validate_xml.py`, `validate_text.py` and `validate_glosses.py` (all with `--no-exit-on-hard`); `validate_conversion_table.py` on the Li, Ortho113 and conversion tables; for each of the original and standard tiers, `validate_duplicate_sentences.py`, `orthography_extract.py` and `validate_orthography.py`; `validate_vocabulary.py` on the standard tier; `validate_dialect.py`; `validate_registries.py`; and `validate_port_readiness.py`. It exits 1 if any step failed.

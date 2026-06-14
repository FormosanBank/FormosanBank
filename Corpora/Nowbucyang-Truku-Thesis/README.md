# Formosan-Lowking-Truku-WordFormation

This package extracts XML-eligible Truku linguistic examples from Lowking Wei-Cheng Hsu / 許韋晟, 2008, 太魯閣語構詞法研究 [Word Formation in Truku].

The workflow uses qpdf decryption and PDF text-layer extraction (`pdftotext -layout`, PyMuPDF, pdfplumber). OCR was not used.

Final validated XML is under `Final_XML/Truku/`, with `xml:lang="trv"`. Raw PDFs, extracted text, page images, parser sidecars, gloss records, morphology-table records, reports, and scripts are outside `Final_XML/`.

The XML includes sentence-level Truku/Chinese pairs and W/M gloss annotation for source examples whose Truku word tokens align reliably with the source gloss line. Alignment skips are documented in `data/processed/gloss_alignment_audit.csv`.

The thesis/source review notes Ortho94 orthography. Because FormosanBank XML only permits `original`, `standard`, and `alternate` as `FORM@kindOf` values, Ortho94 is recorded in `TEXT@source` and `data/processed/orthography_report.md`.

Manual QC lists for slash-option translations and parenthesized examples are in `data/processed/manual_qc_slash_options.txt` and `data/processed/manual_qc_parentheses.txt`.

## Processing pipeline

The corpus is produced in two phases.

### Phase 1 — build `Final_XML/` from the source PDF (this repo)

Run each stage with `python3 scripts/pipeline.py --step <name> --config scripts/config.yaml`, in order:

| # | step | purpose |
|---|------|---------|
| 1 | `inspect_pdf` | report PDF structure / metadata |
| 2 | `decrypt_pdf` | qpdf decryption |
| 3 | `extract_pdf_text` | `pdftotext -layout` (+ PyMuPDF / pdfplumber); **no OCR** |
| 4 | `render_pdf_pages` | page images for visual spot-checks |
| 5 | `extract_layout_blocks` | layout-aware text blocks |
| 6 | `parse_examples` | parse numbered example sentences |
| 7 | `parse_glosses` | parse the interlinear gloss lines |
| 8 | `extract_tables` | morphology tables |
| 9 | `normalize_text` | Unicode/whitespace normalization, footnote handling |
| 10 | `map_language` | assign `xml:lang` / dialect |
| 11 | `quality_filter` | drop rows not eligible for XML |
| 12 | `dedupe_examples` | within-thesis deduplication |
| 13 | `dedupe_against_formosanbank` | dedup against existing FormosanBank corpora |
| 14 | `build_formosanbank_xml` | emit `Final_XML/Truku/*.xml` (FORM/PHON/TRANSL/W/M; F1–F3 variant + translation handling; W-level word glosses; appends `data/manual/manual_sentences.xml`) |
| 15 | `validate_formosanbank_xml` | internal structural validation |
| 16 | `generate_reports` | summary reports |

Hand-curated examples and corrections live in `data/manual/manual_sentences.xml`. Each
`<S>` is appended verbatim by `build_formosanbank_xml` and **overrides** the automated S
of the same id, so manual edits (and additions the parser can't derive) survive rebuilds.

### Phase 2 — FormosanBank QC (run from the `FormosanBank` repo)

Using FormosanBank's `.venv`, run its QC tools against this repo's `Final_XML/`. The order
matters: `clean_xml` runs **both before and after** `standardize` (standardize re-copies the
original into the standard tier), and `add_phonology` runs last.

```bash
DEV=../Formosan-Nowbucyang-Truku-Thesis/Final_XML   # path to this repo's Final_XML

# 1. de-segment the standard tier (strip Ø, hyphens, '=' at the S level)
python QC/cleaning/clean_xml.py --corpora_path "$DEV"
# 2. Ortho94 -> Ortho113 standardization (selects the Truku dialect column)
python QC/utilities/standardize.py --corpora_path "$DEV" \
    --tsv_path Orthographies/ConversionTables/Seediq_94_113.tsv
# 3. de-segment again (standardize recreates the standard tier from the original)
python QC/cleaning/clean_xml.py --corpora_path "$DEV"
# 4. add IPA PHON (original tier = Ortho94 IPA, standard tier = Ortho113 IPA)
python QC/utilities/add_phonology.py --corpora_path "$DEV" --orthography Ortho94
```

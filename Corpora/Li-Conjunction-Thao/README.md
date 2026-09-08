# Li (2014), *Conjunction in Thao*

Paul Jen-Kuei Li's article in *Papers from 12-ICAL, Volume 2*, pp. 401–409, supplies this Thao (`ssf`, dialect `Thao`) corpus. The [official ANU volume](https://openresearch-repository.anu.edu.au/items/8bfb8bf0-2f58-4eae-947c-bf9af50faf9f) uses Li's scholarly transcription and aligned English glosses.

`XML/Thao/li_2014_conjunction_in_thao.xml` contains 28 sentences: examples 1–24, the inline example in footnote 5, and the three examples in footnote 7. There are 211 W and 169 M elements, with 408 original and 408 standard FORMs and the same numbers of original and standard PHONs. The four unglossed footnote examples remain sentence-only. There is no audio.

## Source and corrections

[Reviewed records](CodeAndDocs/reviewed_examples.tsv) preserve the printed readings; [source corrections](CodeAndDocs/source_corrections.tsv) record the exact before/after fields applied before W/M generation. They retain Joshua's reviewed `S → ʃ` and `D → ð` repairs from [the original port](https://github.com/FormosanBank/FormosanBank/commit/541fa53e8), plus the published English corrections (`firewood on`, `person`, `wild animals`) and sentence punctuation. Corrections never apply to gloss codes or metadata. Infix roots retain the gap hyphen, with the infix represented separately (POL-014).

[The coverage ledger](CodeAndDocs/source_ledger.csv) accounts for 28 included units and four pages without utterances across all nine article pages (PDF 394–402). The footnote-5 addition was recovered by `CodeAndDocs/scripts/recover_footnote5.py` from the volume identified in [source_manifest.json](CodeAndDocs/source_manifest.json). Its existing source text and translation are retained without new glosses or segmentation. Existing TEXT/S/W/M IDs and source associations remain unchanged; the addition uses `li2014_thao_fn5_1`.

**M coverage remains partial:** 140 of 211 W elements have no M child. The [merged corpus decision](https://github.com/FormosanBank/FormosanBank/commit/64654b68a) requires a linguistic ruling before adding those analyses. This rebuild preserves the published partial structure and does not resolve [issue #102](https://github.com/FormosanBank/FormosanBank/issues/102). Its V144 findings remain visible. Source W/M glosses remain lone, untiered TRANSL elements under POL-036.

## Rights

**License:** CC BY 4.0

**Rights source:** Paul Jen-Kuei Li, confirmed by Joshua Hartshorne, 2025-06-04; evidence: ask maintainer

The article's first page explicitly releases the work under CC BY 4.0. The source records and generated text derive from that licensed article. XML uses the exact rights-vocabulary value, preserving the published licence claim. The spelling change from the previous prose value still requires the normal maintainer rights review at merge (POL-042–044).

## Rebuild

Use Python 3.11 or newer and the current FormosanBank Python dependencies. All required corpus inputs are committed under `CodeAndDocs/`; neither the PDF, a private repository, nor historical Git objects are required for generation.

```bash
FORMOSANBANK_ROOT=/path/to/FormosanBank PYTHON=python3 ./CodeAndDocs/generate_xml.sh
```

The entry point builds fresh original tiers from the reviewed records and exact corrections, runs shared cleaning, standardizes through `Orthographies/ConversionTables/Thao_Li_113.tsv` with `--hard-remove-segmentation`, finalizes S-standard infix brackets, then runs `add_phonology.py --orthography Li`. Ortho113 is the standard tier; Li is the original PHON profile. Current shared phonology strips nonsegmental stress accents, fixing 20 published original-PHON placeholder values while preserving the accented original FORMs (POL-003).

**POL-047 deviation:** No `apply_manual_edits.py` step is needed: the documented corrections are applied to fresh source records in the builder. The merged Li-specific S-standard bracket finalizer remains between standardization and phonology; shared `--hard-remove-segmentation` now owns hyphens and clitics. Original and W/M analysis notation stays intact. This preserves the scope of the existing corpus ruling while shared standardization lacks the S-infix option.

[provenance.json](CodeAndDocs/provenance.json) records the tools used for the committed build. Update it to the actual FormosanBank commit after a rebuild with newer tools; it never selects or requires an older checkout. Source recovery is separate: `python3 CodeAndDocs/scripts/recover_footnote5.py /path/to/official-volume.pdf` verifies the manifest before reproducing the one-time footnote recovery.

## Review and validation

```bash
FORMOSANBANK_ROOT=/path/to/FormosanBank PYTHON=python3 \
OUTPUT_DIR=/path/to/new-external-report-directory \
SOURCE_PDF=/path/to/official-volume.pdf ./CodeAndDocs/validate.sh
```

`SOURCE_PDF` is optional for validation. Without it, the script explicitly skips PDF verification and Group C source alignment; it still checks the committed records and output. With it, Poppler verifies the PDF and extracts only the article pages. Validation is separate from generation and reports remain outside the corpus. Review every CSV and warning; a successful command is not a source-fidelity verdict.

Focused tests protect the reviewed corrections, infix shape, footnote coverage, stable IDs, partial M decision, and derived-tier boundaries. The source audit checks all output anchors against the records and corrections. It supplements direct page review, not independent evidence for linguistic analysis. No morphology-completion or issue-closure claim is made while the ruling remains outstanding.

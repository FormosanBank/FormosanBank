# Tsukida Seediq correlative clauses

Truku Seediq (`trv`, dialect `Truku`) examples from Naomi Tsukida's 2014 chapter, “Correlative clauses in Seediq,” printed pages 69–79 in [Papers from 12-ICAL, Volume 2](https://openresearch-repository.anu.edu.au/items/8bfb8bf0-2f58-4eae-947c-bf9af50faf9f).

The reviewed inventory accounts for all 39 numbered source units: 26 included, seven comparison-language examples, five starred examples and the explicitly repeated example 28a excluded. Optional constituents in examples 6 and 9 each produce two aligned variants. Final XML has 28 S, 201 W and 254 M, with 483 original and 483 standard FORM/PHON parents, 29 free translations and no audio.

All source words, glosses, clause brackets and translations from the expert-reviewed version are retained. The starred interpretation of grammatical example 13 remains excluded. Fourteen later-added mirror M elements from examples 3 and 6 are omitted under POL-023; their W forms and glosses remain. Reviewed infix roots, stacked infixes and clitics are preserved. XML lives under `XML/Truku/`; IDs use immutable source/example keys with `-opt` for the two expanded readings (POL-028).

## Audio

None supplied by the source.

## Notes and Issues

The reviewed source apostrophe preserves 130 glottal stops across 111 original PHON values. Current standard PHON omits them. Ortho113 uses doubled `ee` in some spellings, but supplies no general conversion for this source's apostrophes; see the [conversion decision](CodeAndDocs/README.md). Technical port readiness is pending that decision. Eleven source form/gloss pairs use flat infix notation; their reviewed analyses and both source and standardized glosses are preserved despite audit warnings.

## Rights

**License:** CC BY 4.0

**Rights source:** Naomi Tsukida / Asia-Pacific Linguistics, 2025-06-04; evidence: ask maintainer

The chapter's first page explicitly grants CC BY 4.0. The date above records the maintainer's verification of that published grant, not a new grant date. Source transcriptions and article extracts used by the build retain this attribution.

## Reproduce

From a FormosanBank checkout with its documented Python dependencies:

```bash
bash Corpora/Naomi-Tsukida-Correlative-Clauses-Seediq/CodeAndDocs/generate_xml.sh
```

In the development repository, set `FORMOSANBANK_ROOT` to a current FormosanBank checkout and run `bash CodeAndDocs/generate_xml.sh`. `PYTHON` selects the installed Python interpreter. No Git metadata, network request, private file or historical tooling checkout is required. The build updates its [provenance record](CodeAndDocs/provenance.json) from the supplied FormosanBank Git checkout; a Git-free export retains that record. Provenance never gates a rebuild.

**POL-047 deviation:** Seven source bracket values are restored after cleaning and before standardization, preserving the clause spans and translations in the source-reviewed version. Source refresh and validation are separate commands.

Generation starts from the committed transcription tables in `CodeAndDocs/raw_data/`, applies recorded corrections, cleans, standardizes `ŋ` to `ng`, and generates both PHON tiers with shared tools. Original PHON uses the [source profile](CodeAndDocs/source_orthography/Seediq.tsv), supported by [Tsukida's Teruku phoneme description](https://lingdy.aa-ken.jp/wp-content/uploads/2012/01/120217_naomi_tsukida_h.pdf), page 2 footnote 1; standard PHON uses the registered standard. This corrects the old build's use of Ortho94 instead of the profile it validated.

Validate existing output with `QC_REPORT_DIR=/outside/corpus/reports bash CodeAndDocs/validate.sh`, using the same environment. Review the CSVs and logs: command success alone is not a source or port-readiness verdict. [Source and review notes](CodeAndDocs/README.md) explain the exact scoped findings and reproduction inputs.

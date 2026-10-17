# QC Summary: {{CORPUS_NAME}}

**Dev repo:** {{DEV_REPO_PATH}}
**Run timestamp:** {{TIMESTAMP_UTC}}
**XML location:** {{XML_PATH}}

## Orthography

- Original (determined in Phase 2): **{{ORIGINAL_ORTHOGRAPHY}}**
- Detector output that informed the decision: see `<output_dir>/orthography_detector.log`
- Standardize args used: `{{STANDARDIZE_ARGS}}`

## Counts

| Metric | Value |
|---|---|
| Texts | {{N_TEXTS}} |
| Sentences | {{N_SENTENCES}} |
| Words (W-tier) | {{N_WORDS_OR_NA}} |
| Morphemes (M-tier) | {{N_MORPHEMES_OR_NA}} |
| Languages | {{LANGUAGES_LIST}} |
| Dialects | {{DIALECTS_LIST}} |

## Hard-gate findings

| Check | Result | Notes |
|---|---|---|
| `validate_xml.py` (XSD) | {{XML_RESULT}} | {{XML_NOTES}} |
| `validate_text.py` (punct + character set) | {{TEXT_RESULT}} | {{TEXT_NOTES}} |
| `validate_duplicate_sentences.py` (same-file dupes) | {{DUPES_RESULT}} | {{DUPES_NOTES}} |
| `validate_glosses.py` | {{GLOSSES_RESULT_OR_NA}} | {{GLOSSES_NOTES}} |
| `validate_audio.py` | {{AUDIO_RESULT_OR_NA}} | {{AUDIO_NOTES}} <!-- "skipped — audio not local" if applicable --> |

## Soft checks (info-only)

| Check | Number | Note |
|---|---|---|
| Orthography similarity vs reference | {{ORTHO_SIM}} | Thresholds uncalibrated (B Phase B4 work) |
| Vocabulary overlap vs reference | {{VOCAB_OVERLAP}} | Cross-genre comparisons may be noisy |
| Cross-file duplicate sentences (within corpus) | {{DUPES_SOFT_COUNT}} | May be legitimate (repeated proverbs etc.) |

## Dialect distribution

<!-- Paste the (xml:lang, dialect) -> count table from 05f_validate_dialect.log.
     Flag anything odd (missing dialects, leakage across languages) under
     "Unusual things surfaced". -->

## Unusual things surfaced

<!-- Anything the validators flagged that doesn't fit a category above, or that needs human judgment. -->

## Known limitations of this summary

- `<PHON>` is valid under `QC/validation/xml_template.xsd`, so a `validate_xml.py` failure after Phase 4 is a corpus error, never schema drift.
- `validate_orthography.py` and `validate_vocabulary.py` always exit 0; their numbers above are only meaningful if read against the thresholds and against the other published corpora of the language.

## Ready to port?

<!-- One-line verdict + reasoning. NOT a guarantee — the operator decides. -->

# XML Quality Review

## Reference Comparison

- Requested reference path `/Users/hunterschep/FormosanBankRepos/Formosan-Rik-Bunun` was not present locally.
- Installed Rik De Busser reference inspected: `/Users/hunterschep/FormosanBankRepos/Formosan-Bunun-Debusser-Dissertation/Final_XML/Bunun/Bunun.xml`.
- Matching conventions adopted: `TEXT` root, direct `S` children only, `S/W/M` IDs only, one `FORM kindOf="original"` at each S/W/M tier with optional `FORM kindOf="standard"`, and `TRANSL` with only `xml:lang`.
- No `class`, `sclass`, `NOTE`, or `AUDIO` elements are emitted in this corpus XML.
- The thesis source identifies the orthography as Ortho94. FormosanBank XSD only allows `original`, `standard`, and `alternate` in `FORM@kindOf`, so Ortho94 is recorded in sidecar metadata and the `TEXT@source` attribute rather than as a `kindOf` value.

## Current XML Counts

- S: 253
- W: 1120
- M: 1407
- FORM: 3033
- TRANSL: 1437
- Sentences with W/M: 253
- Sentences with morpheme-level source glosses: 221
- Sentences with word-level gloss translations: 0
- Sentences with W/M but no reliable source gloss alignment: 32

## Gloss Policy

- Sentence-level `TRANSL xml:lang="zho"` contains only source-published Chinese free translations.
- Morpheme-level `TRANSL xml:lang="zho"` contains source gloss parts only when the source gloss morpheme sequence aligns to the XML form morphemes.
- Word-level `TRANSL` is not emitted for source glosses; when morpheme-level alignment is not reliable, W/M forms are left unglossed rather than placing Leipzig glosses at W.
- If source glosses still do not align after safe normalization, W/M forms are emitted without invented gloss translations; the reason is recorded in `gloss_alignment_audit.csv`.
- Sentence-level `FORM kindOf="original"` and W-level `FORM` values preserve source segmentation (`-`, `=`, `<...>`, `Ø`) where present. Sentence-level `FORM kindOf="standard"` removes segmentation/null/parenthetical markers conservatively.
- Slash options are preserved in XML original forms when the alternatives are grammatical; starred alternatives are omitted. The source free translation is kept unchanged and flagged in `manual_qc_slash_options.txt` for hand QC.
- Parentheses are not used as a blanket rejection criterion. Parenthesized examples are included when otherwise XML-eligible and flagged in `manual_qc_parentheses.txt`.

## Validation

- `scripts/validate_formosanbank_xml.py` passed with zero failures.
- `/Users/hunterschep/FormosanBankRepos/FormosanBank/QC/validation/validate_xml.py by_path --path Final_XML` passed with zero issues.
- `/Users/hunterschep/FormosanBankRepos/FormosanBank/QC/validation/validate_glosses.py Final_XML --check_morpho` found no W-count mismatches. Its M-count heuristic reports expected infix reanalysis cases where one source W form is intentionally represented as a discontinuous base M plus an infix M; the current QC run reports 21 such cases in `logs/formosan_qc/glosses/validation_m_mismatches.csv`.
- `/Users/hunterschep/FormosanBankRepos/FormosanBank/QC/validation/validate_punct.py by_path --path Final_XML` exited 0 and reported PASS.

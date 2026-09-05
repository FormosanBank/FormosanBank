# QC summary

Date: 2026-08-22

Verdict: ready to port as a replacement of `Corpora/Presidential_Apologies`.

## Authority and build

- Canonical corpus output: `XML/`
- FormosanBank tooling commit: `3a3c47c220520113f747e6a2d441494000e13c4b`
- Tool and orthography versions: the live FormosanBank checkout (not pinned; see `data/provenance.json` for what the published output was built against)
- Reproduction modes: `--write` and independent `--check`, both successful
- XML inventory digest: `a6fe12ea3562bd2b2ed13f19c8c5d539b7b5d2069473a43b674b9c07168567fc`

The digest is the SHA-256 of the sorted per-file SHA-256 output for the 16 canonical XML files.

## Corpus inventory

| Element | Count |
| --- | ---: |
| TEXT | 16 |
| S | 524 |
| FORM | 1,048 |
| PHON | 1,048 |
| TRANSL | 1,048 |
| W | 0 |
| M | 0 |
| AUDIO | 0 |

All 16 TEXT IDs and all 524 sentence IDs match the published baseline. Every sentence has original and standard FORM, original and standard PHON, and untiered `zho` and `eng` translations.

## Source evidence

- Source artifacts: 36 of 36 manifest entries verified.
- Native PDF alignment: 524 of 524 sections passed.
- Mandarin PDF alignment: 524 of 524 sections passed.
- Total PDF alignment: 1,048 of 1,048 rows at `100.000`.
- Source-content corrections: Saaroa `S=0` and Truku `S=25`.
- Published word-boundary reconciliation: Kavalan `S=6`.

The paired-page audit confirms that the repeated Saaroa native paragraph in `S=22` and `S=23` occurs on both physical PDF pages 22 and 23 beside distinct Mandarin sections. It is a source-authored duplicate and remains in the corpus.

## QC results and adjudication

| Check | Result | Disposition |
| --- | --- | --- |
| Cleaner | 1,053 `c030` warnings | Source-aligned apostrophes and glottal marks are ambiguous to the generic quote heuristic. No `c031` or `c032` rewrite was produced. Retained. |
| XML validator | 0 findings | Passed. |
| Text validator | 466 SOFT findings | Reviewed below. No HARD findings. |
| Gloss validator | 524 SOFT `V060` findings | This is a sentence-level corpus with no source W/M analysis. W-count comparison is not applicable. |
| Duplicate validator | 1 SOFT group, 2 rows | Saaroa `S=22` and `S=23`, verified as repeated in the official PDF. Retained. |
| Port readiness | 0 HARD, 0 WARN | Passed. |
| Corpus tests | 11 passed | Passed. |

The 466 text findings are fixed by `data/qc_expectations.json` and are all source-faithful:

- `V116` 99: 92 Puyuma `ē` characters, four Bunun angle quotes, one Truku fullwidth apostrophe, and two Yami quotation marks.
- `V122` 252: 126 source parentheses pairs in FORM or translation text. CJK-only annotations are already removed from the standard tier; numbers, Latin alternatives, and translation parentheticals remain.
- `V133` 115: source hyphens in names and orthographic word forms, not preprocessing segmentation artifacts.

Any change to these reviewed counts fails the reproduction test and requires a new adjudication.

## Published-baseline comparison

The rebuilt XML is semantically identical to the published baseline except for the two verified source-content corrections:

- Saaroa `S=0`: both FORM tiers and both regenerated PHON tiers change with `mualiuhlʉ` to `mualiuhlu`.
- Truku `S=25`: both FORM tiers change from a semicolon to the source apostrophe. PHON is unchanged because the character is punctuation.

No metadata, translation, ID, sentence count, dialect, or other FORM/PHON content changes.

## Remaining gates

None. The source is recorded as public domain, contains no private material or audio, reproduces from approved public artifacts, and passes the current replacement-mode port gate.

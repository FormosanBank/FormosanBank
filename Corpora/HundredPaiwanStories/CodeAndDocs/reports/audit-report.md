# One Hundred Paiwan Texts audit report

Date: 2026-08-22

Verdict: ready to port under the recorded rights conditions.

## Authority and scope

- Public authority: FormosanBank commit `3a3c47c220520113f747e6a2d441494000e13c4b`
- Public corpus replaced: `Corpora/HundredPaiwanStories`
- Source: two checksum-pinned Word documents in the private development repository
- Visual source review: all 268 rendered DOCX pages reviewed
- XML scope: all 100 stories and every source sentence, word analysis, morpheme analysis, gloss, free translation, and TEXT metadata field

## Baseline findings

The legacy development XML was not publication-ready. Its hard findings included missing `xml:lang`, invalid translation language codes, empty FORM or PHON values, four missing dialect attributes, and collisions with the already published TEXT IDs. Both the legacy development and public versions also had 32 hard W/M FORM annotation findings.

The public corpus omitted one complete story 091 sentence, five complete interpretations of parenthetical tokens, nine source-final words, and four source metadata values. Its analysis also packed source units together and misrepresented many infix and reduplication boundaries.

## Remediation

- Reparsed all 100 stories from the source document using paragraph styles and the source text, analysis, gloss cycle.
- Preserved direct source text separately from W and M analysis tiers.
- Preserved every existing public ID and added deterministic IDs only for restored or expanded source material.
- Reconstructed equality-linked infixes from the printed surface, reusing 1,146 public gap positions and recording 243 source-inferred positions.
- Represented linear reduplication with the canonical `~` boundary.
- Restored the omitted story 091 sentence and nine truncated final words.
- Expanded five parenthetical source tokens into complete included and omitted S variants.
- Applied 166 exact source-reviewed sentence FORM decisions.
- Moved three labeled editorial notes from free-translation prose into `notes` attributes.
- Closed one unmatched source parenthesis without changing its wording.
- Preserved the unglossed final `-i` in 078S4 and marked the missing gloss explicitly as editorial unknown.
- Corrected four TEXT source metadata values and replaced the false public-domain or CC claim with the actual permission conditions.
- Removed the redundant explicit `Ḍ → dr` conversion row so the shared standardizer derives the case-preserving `Ḍ → Dr` mapping. The corrected table passes the standalone conversion-table audit.

## Final validation

The pinned clean-room reproduction produced:

- 100 TEXT, 2,921 S, 24,556 W, and 36,938 M elements
- 64,515 globally unique IDs
- all 64,198 previously published IDs preserved
- zero hard XML findings, including replacement-aware cross-corpus TEXT ID validation
- zero hard text findings
- zero hard gloss findings
- zero hard gloss-scrape findings
- 15 passing corpus and QC tests

All remaining soft findings are exhaustively classified in `reports/qc/qc-summary.md`. They are canonical reduplication notation, canonical infix-root gaps, exact source hyphens, and preserved source FORM or translation notation. None is a publication gate.

## Publication conditions

The corpus is published under CC BY-NC: attributed non-commercial use and
redistribution are allowed, and commercial use requires prior written
permission. No merge is authorized by this report.

Superseded 2026-09-03: this report originally required the public port to
exclude the author-provided Word files. Under the reproducibility ruling
that a published corpus must rebuild from a FormosanBank checkout alone,
both Word files are now distributed under `CodeAndDocs/`. The private
permission evidence remains excluded.

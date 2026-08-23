# Current QC status

- Run date: 2026-08-23
- FormosanBank authority: `3a3c47c220520113f747e6a2d441494000e13c4b`
- Verdict: `ready to port` as an update to `YeddaPalemeqBlog`
- Publication boundary: the public update remains subject to review and merge

## Canonical output

- 1 canonical XML file under `../XML/`
- 671 S
- 5,643 W
- 7,657 M
- 27,942 FORM
- 27,942 PHON
- 5,585 TRANSL
- 665 AUDIO
- XML SHA256: `b452f10f520053370d090ae95b2e7013006249f7e3b5931d366f0cfce304fb7a`

## Current gates

- Structural and update-mode XML: 0 findings
- Text: 0 HARD; 2,419 source-backed SOFT findings
- Gloss: 0 HARD; 8,680 source-limitation SOFT findings
- Duplicate sentences: two source-authentic groups in each tier
- Issue #1: 9/9 source-backed dispositions; 0 unresolved
- Exact adjudication: 11,107 accepted finding occurrences; 0 unresolved
- Published port readiness: 0 HARD, 0 WARN
- Regression tests: 9 passed

The text SOFT inventory is 30 V116 code-switching or source diacritics and
2,389 V122 source punctuation or analytic notes. The gloss SOFT inventory is
18 V060 word-count signals, 274 V062 prose-infix-gloss signals, 7,657 V064
missing morpheme translations, and 731 V065 missing word translations. The
blog does not provide a complete interlinear morpheme analysis, so these tiers
are retained without invented glosses.

## Live-source reconciliation

The 2026-08-23 audit fetched all 846 posts exposed by the live Blogger feed and
matched all 668 frozen source URLs. It repaired 24 sentence-level scrape
problems and 41 exact word-gloss misses across 31 pages. The sentence repairs
restore nine wholly omitted translations plus 15 incomplete or malformed
translation blocks. Phrase-level definitions were not forced onto individual
words, and genuinely absent word and morpheme glosses remain absent.

An exhaustive comparison of the rebuilt corpus with the live translation
blocks left two reviewed cases, `S483_1` and `S538_1`. The first is the
source-defined alternative expansion. The second combines the lexical gloss
`qau: bamboo` with another source sentence; the repair keeps the lexical gloss
on its word and the free translations on the sentence. Neither is unresolved.

The specialized pre-QC gloss audit reported 1,124 G001 HARD, 1,432 SOFT, and
one G010 warning under its generic interlinear assumptions. G001 and G002 are
inapplicable because Yedda's W translations are prose word definitions rather
than segmented Leipzig-style morpheme glosses. G003 reflects source-backed
discontinuous infix roots. G010 is the one reviewed original-tier segmentation
retained at `S652653654_2`; the standard tier removes it. G012 consists of
source-authentic parenthesized alternate, literal, or meaning translations.
All 108 square brackets are W-level analytic prose, not sentence free
translations. These findings introduce no unresolved source-fidelity defect.

## Reproducibility

The canonical file is rebuilt from the frozen 668-record scrape snapshot with
no network dependency. The snapshot hash, complete source coverage, three
alternative expansions, nine issue decisions, 24 sentence repairs, 41 word
repairs, generated XML, audit files, and current authority commit are all
fail-closed inputs to the handoff checks.

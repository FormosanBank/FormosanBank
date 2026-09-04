# Current QC status

- Run date: 2026-09-04 (final)
- FormosanBank authority: `7c2e0b692abed413bd9234d866cf9f0435c9651e`
- Verdict: `ready to port` as an update to `YeddaPalemeqBlog`
- Publication boundary: the public update remains subject to review and merge

## Canonical output

- 1 canonical XML file under `../XML/`
- 671 S
- 5,643 W
- 6,492 M
- 25,612 FORM
- 25,612 PHON
- 5,585 TRANSL
- 665 AUDIO
- XML SHA256: `5144410793dc3292a75a81feade52d699443bffd2497837c702d31afbb786752`

## Current gates

- Structural and update-mode XML: 0 HARD; 1 source-backed SOFT finding
- Text: 0 HARD; 2,407 source-backed SOFT findings
- Gloss: 0 HARD; 7,499 source-limitation SOFT findings
- Duplicate sentences: two source-authentic groups in each tier
- Issue #1: 9/9 source-backed dispositions; 0 unresolved
- Exact adjudication: 9,915 accepted finding occurrences; 0 unresolved
- Published port readiness: 0 HARD, 0 WARN
- Regression tests: 11 passed

The structural SOFT finding is one file-level V148: 16 of the 671 sentences
carry no W tier, because the blog gives them as bare phrase entries with no
word breakdown (`S268_1`, `S269_1`, `S378_1`-`S381_1`, `S393_1`, `S533_1`,
`S545_1`-`S545_8`). They are source-backed, unchanged from the predecessor, and
there is nothing to segment.

The text SOFT inventory is 18 V116 code-switching or source diacritics and
2,389 V122 source punctuation or analytic notes. The gloss SOFT inventory is
2 V060 word-count signals, 274 V062 prose-infix-gloss signals, 6,492 V064
missing morpheme translations, and 731 V065 missing word translations. V060 and
V148 both reflect authority `7c2e0b692`, which added V148 and scoped V060 to
files that have a W tier; under the earlier `3a3c47c22` pin V060 counted 18. The
blog does not provide a complete interlinear morpheme analysis, so the tiers
that remain are retained without invented glosses.

## Morpheme tier and standard-tier accents

Two decisions were added on 2026-09-03 on top of the source reconciliation.

`fix_m_tier.py` applies POL-023 per sentence: the 161 sentences the blog never
analysed lose their mirror M tier (1,165 morphemes), and every W in an analysed
sentence keeps at least one M. That accounts for the whole M 7,657 -> 6,492 and
V064 7,657 -> 6,492 movement; no gloss was invented or discarded. Because
`standardize.py` gates its C012 hyphen step on a surviving M tier, a stripped
sentence keeps any segmentation hyphen in its standard FORM.

`standardize.py --remove_accents` replaces the previous `--copy`, so the
standard tier is the original minus the combining acute, breve and macron. It
changes exactly two words, both quoted Mandarin kin terms in `S303_1`: `yípó`
-> `yipo` and `āyí` -> `ayi`, which accounts for the whole V116 30 -> 18
movement. Stripping is filtered through the keep set of letters the language
attests (`QC/validation/reference/<Language>/`); Paiwan attests no accented
letter, so nothing is protected here and both words flatten completely.
C012 now also produces the `S652653654_2` standard surface, which the retired
`apply_standard_surface.py` used to write by hand after standardize. That step
is gone: nothing in the build touches a standard FORM after `standardize.py`
runs (POL-002). The reason the two tiers differ is recorded as a `notes`
attribute on the sentence's *original* FORM, written by `build_xml.py` before
any derived tier exists, and the pipeline test asserts both that the note is
there and that no standard FORM carries one.

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
retained at `S652653654_2`; C012 removes it from the standard tier. G012 consists of
source-authentic parenthesized alternate, literal, or meaning translations.
All 108 square brackets are W-level analytic prose, not sentence free
translations. These findings introduce no unresolved source-fidelity defect.

## Reproducibility

The canonical file is rebuilt from the frozen 668-record scrape snapshot with
no network dependency. The snapshot hash, complete source coverage, three
alternative expansions, nine issue decisions, 24 sentence repairs, 41 word
repairs, generated XML, audit files, and current authority commit are all
fail-closed inputs to the handoff checks.

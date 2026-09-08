# Huteson processing notes

`generate_xml.sh` is the build entry point. `build_xml.py` reconstructs the
original tiers from its source-keyed Appendix B transcription and the natural
lines in `manual_source_review.tsv`. Shared tools own cleaning, standard FORM
and both PHON tiers. `validate.sh` validates separately. The audit and
source tests compare with the reviewed transcription; automatic PDF extraction
cannot replace the visual review because of legacy font encoding.

The source profile represents the printed IPA-based system. It maps `ɖ`, `ŋ`,
Dona `ʔ` and Dona `ə` to Ortho113 `dr`, `ng`, `'` and `e`. Maolin `e` and `ɨ`
retain their distinct values. Both registered dialect columns are checked by
the shared conversion-table validator.

## Preserved review decisions

Madeline Boese's [correction PR #1](https://github.com/FormosanBank/Formosan-Huteson-Rukai-Survey/pull/1),
merged as `eb1884f922a79cd70e3e3276ce5574e8293753a5`, established the retroflex
`ɖ`, joined `saokwamamitə` and Tona 15 literal translation. All survive.
`ACT/REAL` is a single source gloss, not alternative sentences. The source's
Takanaw/Takanao spelling distinction between FORM and English is preserved.

## Changes from the former proposal

The comparison is with private `b53bcd65ff749191a13608f88c4763cbae46cbe3`,
not a published corpus. All 29 S and 102 W identities remain. Fifteen sentences
carry source parsing; fourteen do not. The 51 all-single-M mirrors in the
latter are omitted under POL-023. Every word and source gloss survives at W.

Tona 9 restores analyzed W `a-kakə`. Former `S_tona_009_W_001_M_01` represented
all of `akakə`; it now identifies source segment `a`, and new
`S_tona_009_W_001_M_02` identifies `kakə`. This is the only split association.
The original W gloss `1S.TOP` remains there; neither M receives a guessed
meaning. Eight unsupported W `?` glosses and the corresponding M placeholders
are removed. The only new glosses are two separate standard `very.fat` tiers,
with the two original `very fat` values retained.

S follows the separately printed natural lines. Eighteen analyzed hyphens
remain in the source transcription and W/M analysis, while natural S lines
contain none. Tona 4 retains the explicit expert join. No letters, source
sentences, W, free translations or audio are removed.

The old audit report and compact Basecamp files are historical snapshots.
Their assertions requiring placeholder glosses, full mirror-M coverage,
original-S segmentation and seven comments are superseded by the source
review and current policy; no build or validation depends on those snapshots.

## Scoped source finding

Gloss-scrape G001 reports exactly `S_tona_009_W_001`: source `a-kakə` with
source gloss `1S.TOP`. That exact pair is present in the expert-reviewed XML
merged in PR #1, following Madeline's August 7 approval. The later pipeline
removed its boundary; this repair restores the approved pair (POL-050).
Keep the original dot and hyphen. The two source segments have no separately
assigned glosses, so the related G002 and V064 findings are retained for
review. Tests pin this ID, pair and segmentation; the exception is not a
general waiver for mismatched glosses.

# Huteson processing notes

`generate_xml.sh` is the build entry point (POL-047). `build_xml.py` reconstructs
the original tiers from its source-keyed Appendix B transcription and the natural
lines in `manual_source_review.tsv`; it is the only corpus-local processing code,
which is the standing POL-046 exception for initial parsing. Shared tools own
cleaning, the standard FORM and both PHON tiers, called directly with flags and
not wrapped. `validate.sh` validates separately, because validators do not run
inside the build.

## The orthography scheme

The source's writing system is registered as a scheme like any other (POL-039):

* `Orthographies/Huteson/Rukai.tsv` — letter to IPA, per dialect. Consumed by
  `add_phonology.py --orthography Huteson` for the **original** PHON tier.
* `Orthographies/ConversionTables/Rukai_Huteson_113.tsv` — Huteson to Ortho113.
  Consumed by `standardize.py --tsv_path` for the **standard** tier, whose PHON
  then comes from `Orthographies/Ortho113/Rukai.tsv` in the ordinary way.

It is a mixed system rather than plain IPA: `c` is [ʦ] and `y` is [j], which are
practical-orthography values, while `ŋ ɖ ʔ ə ɨ` are IPA symbols used directly.
The conversion table therefore needs rules only where the composition of those
two is not already the identity — `ɖ`→`dr`, `ŋ`→`ng`, `ʔ`→`'` (Dona), `ə`→`e`,
`e`→`é` (Maolin). `c` and `y` need none because Ortho113 uses the same
conventions.

**The `e` row order matters.** `standardize.py` applies conversion rules in file
order with literal replacement, so the `e`→`é` row must precede `ə`→`e`;
otherwise the schwa rule's output is rewritten by the `e` rule. The `e` row's
Dona value is `NA` because Ortho113 gives Dona no `é`.

Both registered dialect columns are checked by the shared conversion-table
validator, which reports `PASS` for each. Its remaining "information loss" lines
(`h`, `z`, `ð`, `ɭ`, `θ`) are phonemes Ortho113 gives these dialects that the
profile has no row for, because none occurs anywhere in the 29 sentences. At the
bank's own rates a corpus this size is expected to contain fewer than two of any
of them, so their absence says nothing about the language, and nothing in the
source reveals which symbols Huteson would use for them.

## Preserved review decisions

Madeline Boese's [correction PR #1](https://github.com/FormosanBank/Formosan-Huteson-Rukai-Survey/pull/1),
merged as `eb1884f922a79cd70e3e3276ce5574e8293753a5`, established the retroflex
`ɖ` and Tona 15's literal translation. Both survive. `ACT/REAL` is a single
source gloss, not alternative sentences. The source's Takanaw/Takanao spelling
distinction between FORM and English is preserved.

That review's other change — joining Tona 4's `saokwa mamitə` into
`saokwamamitə` — has been **reversed** (POL-050 supersedes it). Page 42's gloss
line prints two columns, `very` and `fat`, and the gloss decides word division.
Consequences: W ids for that sentence are contiguous `001/002/003` rather than
skipping `002`; the standardized `very.fat` gloss the join required is gone, so
the corpus carries no `TRANSL[@kindOf="standard"]`; and both restored words are
independently attested in the bank's Dona data.

## Published-identifier change (POL-037)

This corpus was published in PR #149 before the Tona 4 join was reversed, so the
split is a change to already-published identifiers and is announced here rather
than treated as a cleanup.

* **No id is removed, reused or renumbered.**
* **Two ids are added:** `S_tona_004_W_002` and `S_tona_004_W_002_M_01`, the
  second word of that sentence.
* **Three ids keep their number but denote a shorter word:** `S_tona_004`,
  `S_tona_004_W_001` and `S_tona_004_W_001_M_01` were `saokwamamitə` and are now
  `saokwa`. An external citation of `S_tona_004_W_001` made against the first
  published version resolves to the first half of what it used to name.
* Twenty-three ids change only their derived `standard` FORM, from the `e`/`é`
  correction; their `original` FORMs are untouched.

Removed published content (POL-051): **four `TRANSL`** — the `very fat` source
gloss and the standardized `very.fat` beside it, at both `S_tona_004_W_001` and
its morpheme. Both belonged to a word the source does not print. Five are added
in their place: `very` and `fat` at word and morpheme level, and Tona 14's
inferred `NOM`. Net translations +1; word count for Dona 54 -> 55.

## Source-derived findings retained for review

`S_tona_009_W_001` is source `a-kakə` with source gloss `1S.TOP`: the printed
form shows a morpheme boundary and the printed gloss is a single fused label.
The pair is kept exactly as printed, and neither morpheme is given a guessed
meaning. Three checks report this and all three are expected:
`audit_gloss_scrape` G001 (HARD, marker-skeleton parity), G002 (SOFT, morpheme
count vs gloss units), and `validate_glosses` V153 (SOFT, gloss pieces vs
morphemes). `tests/test_corpus.py` pins the id, the pair and the segmentation;
the exception is not a general waiver for mismatched glosses.

The eight blank word-gloss cells and the five blank morpheme glosses that
`validate_glosses` reports as V065 and V064 are likewise the source's own blanks,
listed in `audit_source_alignment.BLANKS`. The one exception is Tona 14's `ki`,
whose gloss is inferred from the corpus's own consistent usage and marked with
`@notes`; `INFERRED_GLOSSES` in `build_xml.py` records the reasoning, and the
audit script rejects an unmarked gloss on any blank column.

## Data that lives outside code

Per POL-039 the transcription is a TSV, not Python literals for anything a reader
needs: `manual_source_review.tsv` holds the natural line, the analyzed form, the
source gloss, the translations and the page locators for all 29 examples, and
`audit_source_alignment.py` checks the built XML against it field by field. The
source PDF's SHA-256 lives only in `source_manifest.md`; the audit script reads
it from there rather than carrying a second copy.

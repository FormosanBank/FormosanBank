# Source and preserved decisions

The reconstruction baseline is Joshua Hartshorne's published August 12 work
in FormosanBank commit `c52665d0ef8c94d130f597819bec4a4cbe777b76`.
Its evidence is `claudeplans/phase-b-reports/Nowbucyang-Truku-Thesis.md` and
the corpus README in that revision. The private predecessor is not a newer
source authority: its removal of unglossed M and reviewed repetitions is
not carried forward.

- Keep `data/manual/manual_sentences.xml` and its source-specific overrides.
- Keep the nine recorded W/M-free, marker-free readings in `manual_edits.xml`.
- Replay only the five reviewed merges in `reviewed_merges.csv`. Keep all six
  translation readings gained in that review. The tenth manual record retains
  `C01_E026B_0080_01`'s second reading, which differs only in final punctuation;
  the shared merger's newer normalized key would otherwise omit it.
- Keep the three distinct-provenance pairs: `C01_E011D` / `C01_E008Bb`,
  `C03_E012B` / `C04_E002C`, and `C01_E026A_0079_01` / `C03_E034b`.
- Run the shared cleaner once. Standardize owns standard FORM; add_phonology
  owns derived PHON. No Truku attestation dictionary is available, so the
  quote-glottal correction is disarmed.

Basecamp card 9896017215 preserves Joshua's May 18/20 source decisions:
Ortho94, source nulls retained, clitic M retains `=`, grammatical slash
readings expanded, and Chapter 2 compounds parsed using the post-arrow
translation. Infix analysis is local to the corresponding source word and
gloss, not a sentence-wide count adjustment (comments 9913568011/9913580811).
The author's occasional angle-bracket use does not itself prove an infix.

PDF identity: the original SHA-256 is recorded in `data/processed/source_metadata.csv`.
The published decrypted PDF hash there differs from the later private
qpdf output; the original PDF is identical. The PDFs themselves are retained
privately and are not required for reproduction.

## Source-column and infix repair

PDF pages 74, 75, 76 and 98 print `q-m-pah-an` with `工作<AF>-LF`.
Represent its W as `q<m>pah-an`, its root as `q-pah`, infix as `-m-`,
and suffix as `an` (POL-014). Match each source word and attached clitic
to its corresponding gloss before assigning M glosses. A sentence-wide
count match cannot justify moving a gloss across word boundaries.

The affected source units are C03_E003B, C03_E005B, C03_E006C and C03_E038B.
In the latter three's W3/W4 as applicable, and C03_E003B's W4, old M3 `pah`
joins M1 in the root; M2 remains the infix and **M4 remains the suffix ID**.
In C03_E005BW1 and C03_E006CW1, restore the three source segments
`G-m-bhngil` / `K-m-elug`, retaining M1/M2 and adding M3 for `bhngil` / `elug`.
No S or W ID changes. No translation, spelling, segmentation or gloss is
invented to fill a source absence.

Canonical angle notation is generated from the other already-reviewed infix
M tiers without changing their letters or M IDs. Source W glosses retain the
author's angle notation, including the non-infix prefix examples on PDF pages
34, 76, 82 and 86–90; their M boundaries follow Joshua's May 20 ruling.
The manual `T-m-kacing` example on page 88 follows the same rule. The manual
word-gloss reconstruction puts an infix gloss next to its root, before a
following suffix, matching `工作<AF>-LF` on page 40. An explicit prior W gloss
is never overwritten, and a source line cannot fill a manual W gloss unless
it agrees with every existing M gloss.

## Recovered page-95 example

PDF page 95 (printed page 79) has an unlabelled second example beneath (36a):
`Tama Lowking ka emp-txiluy nii.` Its gloss and Chinese translation are printed
on the next two lines, and the following paragraph calls it (36b). The raw
source block already preserves all three lines. `data/manual/source_additions.csv`
selects them by source record and line, with a SHA-256 guard against changed
source input. The build appends this reviewed source unit before XML parsing.

Its new ID is `C03_E036B_P095`. The existing published `C03_E036B` belongs
to a different source example on page 116 and remains untouched. Appending
the new input avoids shifting the legacy ordinal-based collision IDs.

## Recovered numbered examples

The old filters excluded six numbered interlinear examples on PDF pages 37,
38, 79 and 127. Keep their source FORM and word glosses (POL-001/POL-036):

| New ID suffix | Source | Free translation |
| --- | --- | --- |
| C01_E019A_P037 | (19a), `imah` | Absent in source |
| C01_E019B_P037 | (19b), `mah-un` | 飲料; literal reading 喝的東西 |
| C01_E020A_P038 | (20a), `patas` | Absent in source |
| C01_E020B_P038 | (20b), `ptas-un` | 作業; literal reading 要寫的東西 |
| C03_E011B_P079 | (11b), `Malu uq-un ka n-hapuy nii.` | Absent in source |
| C04_E005B_P127 | (5b), `btunux qurug` | 圓的石頭。 |

The two literal translations are separate `ver="alt"` readings (POL-024).
Do not invent the three missing free translations or reuse their word glosses
as sentence translations. Source locators and hashes use the same additions
ledger as page 95. These additions preserve all previous sentence subtrees
and IDs. The existing scope excludes lexical/derivation tables, retained in
`data/processed/morphology_tables.csv` for source review.

PDF page 140, example (18b), gives `pahung` the two readings `生氣/膽大`.
Keep both at W and M as separate TRANSL siblings, with `膽大` marked
`ver="alt"` (POL-025). The sentence already has both free translations;
its forms, segmentation and IDs remain unchanged.

## Partial source gloss alignment

Keep a reliably aligned W gloss even when it does not divide into the same
number of pieces as that word's written segments (POL-036). Assign M glosses
within that word only when its own source pieces align. A mismatch in one
word must not erase another word's gloss or shift a gloss across word boundaries.
The affected examples are on PDF pages 38, 40, 41, 55, 58, 74, 79, 126 and 138.
For example, page 138 gives `Tung-Xuwa` one gloss, `東華`; preserve it at W
without guessing separate glosses for `Tung` and `Xuwa`.

Pages 100 (39c) and 116 (37a) gloss `niya na` jointly as `尚未`. Two recorded
edits preserve that fact in the original FORM's notes and add only the three
separately aligned word/morpheme glosses: `不`, `我`, and `讀書` or `書寫`.
Neither part of `niya na` receives an invented individual gloss. All source
forms, segmentation, sentence translations and IDs remain unchanged.

Joshua's June 14 commit `b88df78f3d3a636fa8f033509f7c594131175091` explicitly
introduces the header-only Ortho94-to-Ortho113 table for this corpus. It
preserves letters. The profiles differ phonetically for `g` and `l`; the
conversion report's absent IPA routes do not authorize new letter substitutions.
Keep original PHON based on the source's page-23 values and standard PHON
based on the current Ortho113 profile.

## Gloss readings in repeated examples

The six older exact FORM/free-translation duplicates remain accounted for in
`data/processed/duplicates.csv`. Four also have identical glosses. Page 83's
(17b) and (18b) instead gloss `s-huda` and `S-bgihur` as `s-雪` and `s-風`,
where the retained earlier examples use `IF-雪` and `IF-風`. Recorded edits
keep these later W/M readings as `ver="alt"` with source locators (POL-025),
without replacing the earlier readings or adding duplicate sentences.

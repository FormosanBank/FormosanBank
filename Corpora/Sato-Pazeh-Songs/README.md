# Sato Pazeh ritual songs

Three Pazeh ritual songs in B. Sato's "Native Songs
from Taisha-sho, Pazeh Tribe, Formosa" (大社庄の蕃歌), published in *Nanpo
Dozoku* 3(1), April 1931, pp. 116–126.

Published under **CC BY-NC 4.0**. The public-domain status of the source
could not be established; see **Rights** below for what is known and why the
project is publishing anyway.

## Corpus

- Canonical output: `XML/Pazeh/`
- XML files: 3
- Sentences: 83, split 21, 39, and 23
- Japanese translations: 82
- Language: Pazeh, ISO 639-3 `pzh`, Glottocode `paze1234`, dialect `unknown`
- Tiers present: sentence-level `FORM[@kindOf="original"]` and `TRANSL[@xml:lang="jpn"]`
- Tiers absent: no `standard` FORM, no `PHON`, no `W`, `M` or gloss tiers, no audio

The final refrain has no printed Japanese translation and therefore has no
`TRANSL` tier.

## Rights

**License:** CC BY-NC 4.0
**Rights source:** Project determination.

If the author had passed by 1968, this text is public domain. Evidence is
unclear: We have possible evidence of life in 1967 (based on a book
publication in 1968, possibly by the same author). In balancing community need
against the unlikely commercial interests of the unknown heirs of the author
-- and given the plausible argument that extraction and curation of the data
here constitute a transformative use -- we are erring on the side of making
the derived data available under CC BY-NC 4.0. If you believe you own the
copyright of this text, please contact the project director directly.

## Notes and Issues

- **The article's Japanese notes are not extracted.** Each of the three
  sections is followed by 試註, a substantial block of Sato's philological
  notes on individual lines — notes 1–21 for section I, through note 41 for
  section II, through note 24 for section III. These are inventoried as
  excluded blocks in `CodeAndDocs/intermediate/source_blocks.csv` and were
  used to resolve line-wraps and readings, but none of their content is in
  the XML. They are the richest unextracted material in the source and
  could and should be captured — most plausibly as sentence-level
  `TRANSL[@kindOf]` or as notes attached to the lines they gloss.
- **There appears to be a second translation, also not extracted.** Each
  section also closes with 大意, a free Japanese rendering of the whole song.
  It is not aligned line-by-line with the `FORM` rows, which is why it was
  excluded, but it is in substance a second translation of the same text and
  a reader would want it. Extracting it means deciding how to represent a
  whole-text translation that does not map onto sentences.
- **No standard tier, by design.** Pazeh has no designated standard
  orthography — its `standards.csv` cell is deliberately blank — so there is
  nothing to transliterate into. `validate_xml.py` reports SOFT
  `V014 count_missing_standard_form` × 83; that is expected, not a defect.
  The corpus is consequently excluded from cross-corpus comparisons, which
  default to `--kindOf standard`.
- **No phonology tier.** We do not know the phonology of Sato's romanization.
  `Orthographies/Tsuchida/Pazeh.tsv` describes a different orthography — it
  has no `c`, `j` or `o`, all of which Sato uses — and generating PHON from it
  produces both unmapped-letter `*` marks and silent errors (every `h` becomes
  pharyngeal `ħ`, `rubuh` becomes `ɾoboħ`). `add_phonology.py` is deliberately
  not run.
- **Hyphens are syllable dividers, not morpheme boundaries.** 137 of 356
  tokens contain `-` (`Tap-ba-nan`, `Sap-bung-nga-kai-sih`). Everywhere else
  in FormosanBank a hyphen in a FORM marks morpheme segmentation. Anything
  that strips or interprets hyphens will be wrong here.
- **Doubled consonants are probably not geminates.** `bb kk nn rr dd hh mm tt
  ss pp` occur 24 times; they most likely mark syllable closure in Sato's
  romanization rather than length.
- **`dialect="unknown"`.** The source does not identify a Pazeh variety, and
  `dialects.csv` has no Pazeh row.
- **The 1934 date recorded by an earlier pass was wrong.** The issue is April
  1931; see `CodeAndDocs/docs/source_manifest.md` for the correction and for
  two points that remain unresolved.

## Source

The private 14-page attachment contains the article, colophon, contents, and
cover. It is not committed, and **the build does not read it** — the original
tier is transcribed into `CodeAndDocs/intermediate/reviewed_sentences.csv`,
which is. Supply the scan only if you want to re-verify it, at:

`Private/source/nanpo_dozoku_v3n1_taisha_songs_1931.pdf`

or set `SOURCE_PDF` to an equivalent local copy, then run
`CodeAndDocs/check_source.py`.

- Size: 16,508,391 bytes
- SHA-256: `094658186d845c0fd1fae2da6a8c41870734742a08e86fcfa97815710e1f485e`
- [NTU Library article record](https://dl.lib.ntu.edu.tw/s/tj/item/812667)
- [NLPI bound-issue catalog record](https://das.nlpi.edu.tw/handle/a678g)
- [Private Basecamp source card](https://app.basecamp.com/3340659/buckets/31258415/card_tables/cards/8538287698)

The article begins on printed p. 116; pp. 114–115 belong to the preceding
article. See `CodeAndDocs/docs/source_manifest.md` for the full evidence and
rights notes.

## Reproduce

```bash
CodeAndDocs/generate_xml.sh /path/to/FormosanBank
```

Offline and self-contained (POL-048): the build reads only `CodeAndDocs/` and
the FormosanBank checkout you point it at. No second clone, no pinned commit,
no `Private/` directory. Re-running over a clean checkout leaves `git status`
empty.

The FormosanBank commit the committed XML was built against is recorded in
[`CodeAndDocs/provenance.json`](CodeAndDocs/provenance.json).

> **Build history.** Step 3 runs the shared cleaner. Until commit `f614e0d7b`,
> `clean_xml.py` ASCII-ified Japanese punctuation in `TRANSL` tiers — `、` to
> `,` and `（）` to `()` — which rewrote 20 of the 82 translations. That is
> fixed; building against an older checkout would reintroduce it.

QC is separate, as POL-047 requires:

```bash
CodeAndDocs/validate.sh /path/to/FormosanBank [output-dir]
```

**POL-047 deviation:** steps 4 and 5 of the canonical order —
`standardize.py` and `add_phonology.py` — are omitted. Pazeh has no designated
standard orthography to transliterate into and no established phonology for
Sato's romanization, so both steps would fabricate tiers rather than derive
them. See **Notes and Issues** above.

## Readiness boundary

All 14 attachment pages were reviewed. The source ledger records 83 included
sentences and 16 excluded non-target blocks. Current validators, deterministic
regeneration, and clean-clone reproduction all pass.

The corpus is technically complete and, with the licence above, expressible
under POL-042. It is ready to port. No source file or QC log belongs in the
Git tree.

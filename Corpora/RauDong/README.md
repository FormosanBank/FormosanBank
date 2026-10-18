# RauDong — Yami texts (Rau & Dong 2006)

The 20 glossed Yami (Tao, `tao`) narrative texts published in

> Rau, D. V., & Dong, M. N. (2006). *Yami texts with reference grammar and
> dictionary.* Institute of Linguistics, Academia Sinica.

794 sentences, 13,295 words and 16,731 morphemes, each with Chinese and
English translations at the sentence, word **and** morpheme tier (except a few
glosses and one sentence translation the source leaves unknown; see Notes and
Issues). One file per text, named for the text. Every text carries
`dialect="Yami"`. There is no audio.

## License and AI Use

This corpus is subject to its source license and the central FormosanBank
terms in [LICENSE.md](../../LICENSE.md) and
[AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is
prohibited without prior written permission. The copyright holder made this
corpus available CC BY-NC.

## Tiers

Each `S`, `W` and `M` carries an `original` and a `standard` FORM, and a PHON
for each.

- **`original`** is Rau & Dong's own spelling, unmodified.
- **`standard`** is the same text with the lexical accent removed (see below)
  and, at sentence level only, with the morpheme-segmentation hyphens taken
  out so the sentence reads as running text. Word- and morpheme-level standard
  FORMs keep their hyphens.
- **PHON `original`** is derived from the `Orthographies/Ortho94` Yami
  profile, **PHON `standard`** from `Orthographies/Ortho113`.

### Orthography

Rau & Dong write Yami in the letters of the ROC-94 official orthography — `ng
p b t d k g ' v c j s z h m n r l w y i e a o`, with no `f`, `q` or `u` — plus
an acute accent on vowels (`á é í ó`). The accent marks **lexical stress**,
not a distinct vowel. It is part of the source's spelling, so the `original`
tier keeps it; FormosanBank's common orthography does not write stress, so the
`standard` tier does not have it.

Two consequences a data user should know:

- `add_phonology` folds the stress accent before mapping (it marks stress, not
  a different segment), so accented vowels come out as the plain vowel in
  **original** PHON: `ma-níring` → `maniriŋ`. Before that shared change
  (2026-09-05) they came out as `*` (1,098 PHON values); the rebuild recorded in
  `CodeAndDocs/provenance.json` replaced all of them.
- 29 PHON values per tier (58 in all, original and standard) still contain
  `*`. In 20 of each 29 the form quotes Chinese (`國小二三年級`, `mi開開玩笑`,
  `nim要理i`); those characters have no Yami phonological value. The other 9
  of each 29 are the `UNK` morphemes described below: Ortho94 and Ortho113
  have no Yami `u`, so `UNK` comes out as `*nk`.

### Notation inside the FORM tiers

- **`-`** marks morpheme boundaries in the `original` tier at all three
  levels, and in the `standard` tier at word and morpheme level.
- **`:`** marks the point of infixation inside an infixed root at morpheme
  level. `k-om-an` 'eat (AF)' is two morphemes: `om` (AF) and `k:an` (eat).
- **`'`** is the glottal-stop **letter**, not an apostrophe or a quote mark
  (132 occurrences per tier, original and standard alike: 44 each at sentence,
  word and morpheme level). Quotations are written with `"`.
- **`UNK`** appears as a morpheme FORM and gloss in 9 places where the source
  gives no morpheme analysis for the word.
- A handful of sentences contain Chinese words code-switched into the Yami
  text; they are transcribed as printed.

## Provenance and reproducibility

The machine-readable text of these 20 texts was supplied to FormosanBank
already digitized. **There is no scrape, OCR or parse stage in this repository
to re-run, and none can be reconstructed from what we hold.** The source of
record is therefore a snapshot of the XML in

    CodeAndDocs/pre_correction_snapshot/XML/

**The snapshot is not the XML as delivered.** It is the XML as published in
this repository at commit `2bed0e22f` (2026-10), after the original delivery
(commit `0d0df4710`, 2025-07-08) had been hand-corrected over several commits
between 2025-11 and 2026-06. Compared with the delivery, the snapshot has:

- a different sentence-level `original` FORM in 447 of the 793 delivered
  sentences — in 401 of them the only change is typographic double quotes
  (`“ ”`) becoming `"`;
- one sentence split in two: text 10, sentence 18 became sentences 18 and 18b
  (794 sentences in all);
- different sentence translations in 534 sentences (957 translation strings),
  mostly the same quote normalization plus `’` → `'`;
- structural changes, among them W and M ids, missing `kindOf` values,
  `TEXT` capitalization, `dialect="Yami"`, `zh`/`en` → `zho`/`eng`, and the
  files moved under `Yami/` and renamed;
- `standard` FORM and both PHON tiers, which the delivery did not have. The
  build regenerates all three (steps 2 and 3 below), so their snapshot values
  do not reach `XML/`.

No script in this repository replays those earlier edits; they exist only as
their result in the snapshot and in the git history. The delivered XML can be
recovered with `git show 0d0df4710:"Corpora/RauDong/XML/<file>"`.

The snapshot has had one edit since it was taken: its `TEXT/@copyright` was
changed from `CC NC-BY` to `CC BY-NC 4.0`, the same one-line change made to the
published XML on 2026-10-17 (POL-042).

Everything under `XML/` is rebuilt from that snapshot by
`CodeAndDocs/generate_xml.sh` (POL-047); nothing in `XML/` is hand-edited. If a
correction is ever needed, it is made by a script that runs as a pipeline step,
so it survives the next rebuild.

The `.png` files and `orthographic_info` in `CodeAndDocs/` are a character-
and word-frequency profile of the corpus produced during its original QC. They
document the corpus; they are not inputs to the build.

## Reproducing `XML/`

The FormosanBank commit the published `XML/` was last built against is recorded in
[`CodeAndDocs/provenance.json`](CodeAndDocs/provenance.json) (POL-052).

One command rebuilds the whole corpus:

```bash
./CodeAndDocs/generate_xml.sh
```

It takes an optional path to the FormosanBank checkout whose QC scripts should
be used (default: the checkout this corpus lives in); `FORMOSANBANK_ROOT` and
`PYTHON` do the same as environment variables. The script is idempotent — it
always starts from the snapshot, and a second run reproduces the first byte
for byte.

The steps it runs, in order:

```bash
# 0. restore XML/ from the snapshot
rm -rf XML && cp -r CodeAndDocs/pre_correction_snapshot/XML XML

# 1. canonicalize typography in the original tier
python <bank>/QC/cleaning/clean_xml.py --corpora_path XML

# 2. build the standard tier: copy of the original, minus the lexical acute
#    accent, minus sentence-level segmentation hyphens
python <bank>/QC/utilities/standardize.py --remove_accents --corpora_path XML

# 3. generate both PHON tiers
python <bank>/QC/utilities/add_phonology.py --orthography Ortho94 --corpora_path XML

# 4. unknown glosses -> <UNCLEAR/>, unknown sentence translation omitted
python CodeAndDocs/apply_unclear_glosses.py --corpora_path XML
```

Step 3's `--orthography Ortho94` supplies the **original** PHON; the
**standard** PHON comes from Ortho113, the scheme designated for Yami in the
repository's `standards.csv`.

Step 1 currently changes nothing. It reports two typographic single quotes in
the Chinese translation of sentence 41 of text 1 and leaves them alone, which
is correct — they are Chinese quotation marks.

Steps 1 and 2 write `cleaner_warnings.csv` / `standardize_warnings.csv` into
`XML/` when they have anything to report. Those are per-run reports: read them
after a run, then delete them. They are never committed.

Step 4 is this corpus's own script. It applies the rows of
`CodeAndDocs/unclear_glosses.tsv` (see "Unknown glosses" under Notes and
Issues) and fails without writing anything if a row no longer matches the
snapshot, or if any wholly unknown gloss is left that the table does not list.
It runs last because the shared `standardize.py` and `add_phonology.py` do not
handle `<UNCLEAR/>` inside a translation.

There is no `apply_manual_edits.py` step because there are no recorded hand
edits (no `CodeAndDocs/manual_edits.xml`).

## Notes and Issues

- **Infixes are written with hyphens, not angle brackets.** The word tier
  writes `k-om-an`, `s-in-avat`, `ni-t-om-agtag`; the morpheme tier splits
  them into the infix and the root with `:` at the infixation point. This
  differs from the FormosanBank convention (`k<om>an` at word level, `-` at
  the infixation point) and is the reason 60 words report a mismatch between
  their hyphen count and their morpheme count. Converting the notation is a
  linguistic task that has not been done.
- **9 words have a single `UNK` morpheme child** instead of an analysis, so
  their morpheme tier does not reconstruct the word: `ngomon-an`, `ngomon`,
  `mapa-sila-siláp-i`, `veza-no-dehdeh`, `vozovóza`,
  `nimakalkalima-so-nakem` (×2), `pángap`, `kong-koan`.
- **Unknown glosses are `<UNCLEAR/>`** (POL-021 and POL-061 as amended
  2026-10-17; the amendments are in PR #297). The source glosses
  six morphemes `?` in both Chinese and English and leaves the five words
  above them unglossed: text 5 `kominazazang` and `minipinizozongan`, text 9
  `naway`, text 12 `s:yak` (a morpheme of a glossed word), text 14 `viknaz`,
  text 18 `nipapo`. Those 22 glosses (12 morpheme, 10 word) are
  `<TRANSL xml:lang="..."><UNCLEAR/></TRANSL>`. Text 9 sentence 23 has no
  sentence translation: the source gives only `句意不詳` / `(Sentence meaning
  not clear`, and a wholly unknown sentence translation is not emitted. The
  source's doubt about a gloss it does give is kept as written (text 2,
  `sombing` glossed `糞(日語?)`). The changes are listed row by row in
  `CodeAndDocs/unclear_glosses.tsv`.
- **One sentence appears twice** in text 16, at sentence 22 and sentence 50
  (`i-ké-yngen na no oo na ni ina na a ka no ama na am,`). The two occurrences
  sit in unrelated passages and the source gives each its own Chinese and
  English translation, so this is repetition in the narrative, not a
  duplicated extraction. Both are kept.
- **Parentheses and slashes.** `validate_text.py` reports 204 V122 findings,
  one per `(`, `)` or `/` character: 196 in translations, which are part of
  the published translations, not conversion artifacts, and 8 in the
  sentence FORMs (both tiers) of text 11 sentence 12 and text 13 sentence 13,
  whose parentheses are in the delivered text. (205 before text 9 sentence
  23's English translation was omitted; see above.)

## References

Rau, D. V., & Dong, M. N. (2006). *Yami texts with reference grammar and
dictionary.* Institute of Linguistics, Academia Sinica.

## Rights

**License:** CC BY-NC 4.0

**Rights source:** the copyright holder (see References), date not recorded in this repository; evidence: ask maintainer

The copyright holder made this corpus available CC BY-NC. The licence was recorded as `CC NC-BY` until 2026-10-17; POL-042 normalises an unversioned grant to 4.0 (maintainer approval of the normalisation sweep, 2026-10-17).

# RauDong — Yami texts (Rau & Dong 2006)

The 20 glossed Yami (Tao, `tao`) narrative texts published in

> Rau, D. V., & Dong, M. N. (2006). *Yami texts with reference grammar and
> dictionary.* Institute of Linguistics, Academia Sinica.

794 sentences, 13,295 words and 16,731 morphemes, each with Chinese and
English translations at the sentence, word **and** morpheme tier. One file per
text, named for the text. Every text carries `dialect="Yami"`. There is no
audio.

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
  (2026-09-04) they came out as `*` (1,127 PHON values); the rebuild recorded in
  `CodeAndDocs/provenance.json` replaced all of them.
- A further 29 PHON values contain `*` because the sentence quotes Chinese
  (`國小二三年級`, `mi開開玩笑`, `nim要理i`). Those characters have no Yami
  phonological value.

### Notation inside the FORM tiers

- **`-`** marks morpheme boundaries in the `original` tier at all three
  levels, and in the `standard` tier at word and morpheme level.
- **`:`** marks the point of infixation inside an infixed root at morpheme
  level. `k-om-an` 'eat (AF)' is two morphemes: `om` (AF) and `k:an` (eat).
- **`'`** is the glottal-stop **letter**, not an apostrophe or a quote mark
  (264 occurrences). Quotations are written with `"`.
- **`UNK`** appears as a morpheme FORM and gloss in 9 places where the source
  gives no morpheme analysis for the word.
- A handful of sentences contain Chinese words code-switched into the Yami
  text; they are transcribed as printed.

## Provenance and reproducibility

The machine-readable text of these 20 texts was supplied to FormosanBank
already digitized. **There is no scrape, OCR or parse stage in this repository
to re-run, and none can be reconstructed from what we hold.** The delivered
XML is therefore the source of record, and it is preserved verbatim in

    CodeAndDocs/pre_correction_snapshot/XML/

Everything under `XML/` is rebuilt from that snapshot by
`CodeAndDocs/generate_xml.sh` (POL-047). The snapshot is never edited; nothing in `XML/` is
hand-edited. If a correction is ever needed, it is made by a script that runs
as a pipeline step, so it survives the next rebuild.

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

There is no `apply_manual_edits.py` step because there are no recorded hand
edits (no `CodeAndDocs/manual_edits.xml`).

## Known caveats

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
- **One sentence appears twice** in text 16, at sentence 22 and sentence 50
  (`i-ké-yngen na no oo na ni ina na a ka no ama na am,`). The two occurrences
  sit in unrelated passages and the source gives each its own Chinese and
  English translation, so this is repetition in the narrative, not a
  duplicated extraction. Both are kept.
- **Parentheses in translations.** 205 translation strings contain `(` or `)`.
  They are part of the published translations, not conversion artifacts.

## References

Rau, D. V., & Dong, M. N. (2006). *Yami texts with reference grammar and
dictionary.* Institute of Linguistics, Academia Sinica.

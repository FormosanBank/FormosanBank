# Sato (1931), Pazeh Ritual Songs

Sato Pazeh ritual songs: three Pazeh ritual songs recorded by B. Sato at
Taisha-shō (大社庄), the historic Pazeh village in what is now Taichung, and
published in the ethnographic journal *Nanpo Dozoku* in 1931: a song of
origins, a song of the great flood, and a song of the dispersion of the people
after the flood. There are 83 sentences, each an aligned line of the printed
text, and 82 Japanese translations. This is FormosanBank's first Pazeh
material.

## Languages and dialects

- Language: Pazeh, ISO 639-3 `pzh`, Glottocode `paze1234`, dialect `unknown`

All three XML files under `XML/Pazeh/` carry `xml:lang="pzh"`,
`glottocode="paze1234"` and `dialect="unknown"` on `<TEXT>`:

| File | Song | Sentences |
| --- | --- | --- |
| `Nanpo_Dozoku_1931_Kaiki_no_Uta.xml` | I 開基之歌 (Song of Origins) | 21 |
| `Nanpo_Dozoku_1931_Daisui_Hanran_no_Uta.xml` | II 大水氾濫之歌 (Song of the Great Flood) | 39 |
| `Nanpo_Dozoku_1931_Hanran_go_Jinmin_Bunkyo_no_Uta.xml` | III 氾濫後人民分居之歌 (Song of Post-Flood Dispersion) | 23 |

The source does not record the dialect. Pazeh has two dialects, Pazeh (巴宰)
and Kaxabu (噶哈巫); see **The dialect is unrecorded** under Notes and caveats.

The Japanese translations are tagged `TRANSL[@xml:lang="jpn"]`.

## Source

Three Pazeh ritual songs in B. Sato's "Native Songs
from Taisha-sho, Pazeh Tribe, Formosa" (大社庄の蕃歌), published in *Nanpo
Dozoku* 3(1), April 1931, pp. 116–126.

The songs belong to the Pazeh *ai-yan* genre, named for the refrain that opens
and closes them. The text is a Japanese-era romanization, preserved exactly as
printed; there is no standard tier and no phonology, for reasons given under
Notes and Issues (now **Notes and caveats**). No audio is included.

#### What the XML contains

- Canonical output: `XML/Pazeh/`
- XML files: 3
- Sentences: 83, split 21, 39, and 23
- Japanese translations: 82
- Tiers present: sentence-level `FORM[@kindOf="original"]` and `TRANSL[@xml:lang="jpn"]`
- Tiers absent: no `standard` FORM, no `PHON`, no `W`, `M` or gloss tiers, no audio

The final refrain has no printed Japanese translation and therefore has no
`TRANSL` tier.

#### The scan

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

The article is catalogued by
[NTU Library](https://dl.lib.ntu.edu.tw/s/tj/item/812667) and the bound issue
by [NLPI](https://das.nlpi.edu.tw/handle/a678g). The scan itself is not
public and is not required to rebuild the corpus.

The article begins on printed p. 116; pp. 114–115 belong to the preceding
article. See `CodeAndDocs/docs/source_manifest.md` for the full evidence and
rights notes.

#### The date of the issue

The article's date was corrected during review. An earlier pass had recorded it
as 1934; the issue cover reads "Vol. III, No. I, April. 1931" and lists this
article in its contents, so the citation follows the item itself. The XML
filenames and sentence identifiers use 1931 throughout.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Sato-Pazeh-Songs_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

Sato, B. 1931. "Native Songs from Taisha-sho, Pazeh Tribe, Formosa" (大社庄の
蕃歌). *Nanpo Dozoku* 3(1): 116–126.

## License

**License:** CC BY-NC 4.0
**Rights source:** Project determination.

Published under **CC BY-NC 4.0**. The public-domain status of the source
could not be established; see **Rights** below for what is known and why the
project is publishing anyway.

#### Rights

If the author had passed by 1968, this text is public domain. Evidence is
unclear: We have possible evidence of life in 1967 (based on a book
publication in 1968, possibly by the same author). In balancing community need
against the unlikely commercial interests of the unknown heirs of the author
-- and given the plausible argument that extraction and curation of the data
here constitute a transformative use -- we are erring on the side of making
the derived data available under CC BY-NC 4.0. If you believe you own the
copyright of this text, please contact the project director directly.

The corpus is also subject to FormosanBank's
[Terms of Use](https://formosanbank.github.io/FormosanBank/additional-resources/terms-of-use/) and
[AI Use and Commercial Licensing](https://formosanbank.github.io/FormosanBank/additional-resources/ai-use-and-commercial-licensing/).

## Notes and caveats

Seven things a user should know before comparing this corpus with FormosanBank's
other material. All are properties of the 1931 source or of the state of Pazeh
documentation, not defects in the port.

**Sato's philological notes are not extracted.** Each of the three sections is
followed by a block of line-by-line notes (試註) — notes 1–21 for section I,
through note 41 for section II, through note 24 for section III, roughly 86
notes across six printed pages (pp. 117–118, 120–121 and 124–125). They are
inventoried in the corpus's source ledger and were used during transcription
to resolve line-wraps and readings, but none of their content is in the XML.
They are the richest unextracted material in the source.

- **The article's Japanese notes are not extracted.** Each of the three
  sections is followed by 試註, a substantial block of Sato's philological
  notes on individual lines — notes 1–21 for section I, through note 41 for
  section II, through note 24 for section III. These are inventoried as
  excluded blocks in `CodeAndDocs/intermediate/source_blocks.csv` and were
  used to resolve line-wraps and readings, but none of their content is in
  the XML. They are the richest unextracted material in the source and
  could and should be captured — most plausibly as sentence-level
  `TRANSL[@kindOf]` or as notes attached to the lines they gloss.

**There is a second translation, also not extracted.** Each section closes with
a free Japanese rendering of the whole song (大意), occupying most of three
further printed pages. It was excluded because it does not align line-by-line
with the sentence tier, but it is in substance a second translation of the same
text.

- **There appears to be a second translation, also not extracted.** Each
  section also closes with 大意, a free Japanese rendering of the whole song.
  It is not aligned line-by-line with the `FORM` rows, which is why it was
  excluded, but it is in substance a second translation of the same text and
  a reader would want it. Extracting it means deciding how to represent a
  whole-text translation that does not map onto sentences.

**Hyphens are syllable dividers, not morpheme boundaries.** 137 of 356 tokens
contain a hyphen — `Tap-ba-nan`, `Sap-bung-nga-kai-sih`, `ki-kit-ta-ai`.
Everywhere else in FormosanBank a hyphen inside a FORM marks morpheme
segmentation. Anything that strips or interprets hyphens will be wrong on this
corpus.

- **Hyphens are syllable dividers, not morpheme boundaries.** 137 of 356
  tokens contain `-` (`Tap-ba-nan`, `Sap-bung-nga-kai-sih`). Everywhere else
  in FormosanBank a hyphen in a FORM marks morpheme segmentation. Anything
  that strips or interprets hyphens will be wrong here.

**Doubled consonants are probably not geminates.** The sequences `bb kk nn rr
dd hh mm tt ss pp` occur 24 times. They most likely mark syllable closure in
Sato's romanization rather than consonant length, but this is not settled.

- **Doubled consonants are probably not geminates.** `bb kk nn rr dd hh mm tt
  ss pp` occur 24 times; they most likely mark syllable closure in Sato's
  romanization rather than length.

**There is no standard tier and no phonology tier.** Pazeh has no designated
standard orthography in FormosanBank — its `standards.csv` cell is deliberately
blank, as Siraya's and Babuza-Favorlang's are — so there is nothing to
transliterate the text into, and the corpus is excluded from cross-corpus
comparisons, which read the standard tier. Nor is the phonology of Sato's
romanization known. A Pazeh scheme does exist in the bank
(`Orthographies/Tsuchida/Pazeh.tsv`), but it describes a different orthography:
it has no `c`, `j` or `o`, all of which Sato uses, and applying it produces
both unmapped letters and silent errors. Generating a phonology from it would
assert readings the source does not support, so neither tier is generated.

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

**The orthography is not validated against a reference.** FormosanBank has no
`QC/validation/reference/Pazeh/`, so the orthography and vocabulary checks that
other corpora pass cannot run for this language at all. The character
inventory is 21 ASCII letters with no diacritics, checked by hand; nothing more
than that has been verified against external Pazeh sources.

**The dialect is unrecorded.** Pazeh has two dialects, Pazeh (巴宰) and Kaxabu
(噶哈巫). The source does not say which this is, so every text carries
`dialect="unknown"`. Taisha-shō is Pazeh territory, but the corpus does not
assert what the source does not state.

- **`dialect="unknown"`.** The source does not identify a Pazeh variety.
  `dialects.csv` lists both Pazeh dialects (Pazeh and Kaxabu), but the corpus
  does not assign either.

Separately from the seven points above: **the 1934 date recorded by an earlier
pass was wrong.** The issue is April 1931; see
`CodeAndDocs/docs/source_manifest.md` for the correction and for two points
that remain unresolved.

## Reproduction and processing

### How to reproduce

```bash
bash Corpora/Sato-Pazeh-Songs/CodeAndDocs/generate_xml.sh
```

or, from any directory:

```bash
CodeAndDocs/generate_xml.sh /path/to/FormosanBank
```

The FormosanBank argument is optional: without it the script uses
`FORMOSANBANK_ROOT` if set, otherwise the checkout three levels above
`CodeAndDocs/` (the FormosanBank repository the corpus sits in). Set `PYTHON`
to choose the interpreter (default `python3`).

The XML and reproduction files are maintained in the
[FormosanBank repository](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Sato-Pazeh-Songs).

Offline and self-contained (POL-048): the build reads only `CodeAndDocs/` and
the FormosanBank checkout you point it at. No second clone, no pinned commit,
no `Private/` directory. Re-running over a clean checkout leaves `git status`
empty.

The corpus's `CodeAndDocs/generate_xml.sh` rebuilds from those committed inputs
and the current shared cleaner. It reads nothing else — no private repository,
no pinned checkout, no source download — and re-running it over a clean
checkout leaves the tree unchanged.

The FormosanBank commit the committed XML was built against is recorded in
[`CodeAndDocs/provenance.json`](CodeAndDocs/provenance.json) (POL-052;
provenance only, a rebuild always runs the current tools).
[Tool provenance](CodeAndDocs/provenance.json)
records the build without pinning later runs.

> **Build history.** Step 3 runs the shared cleaner. Until commit `f614e0d7b`,
> `clean_xml.py` ASCII-ified Japanese punctuation in `TRANSL` tiers — `、` to
> `,` and `（）` to `()` — which rewrote 20 of the 82 translations. That is
> fixed; building against an older checkout would reintroduce it.

QC is separate, as POL-047 requires:

```bash
CodeAndDocs/validate.sh /path/to/FormosanBank [output-dir]
```

Without `output-dir`, the logs go to `logs/<UTC timestamp>/` in the corpus
folder, which is gitignored.

**POL-047 deviation:** steps 4 and 5 of the canonical order —
`standardize.py` and `add_phonology.py` — are omitted. Pazeh has no designated
standard orthography to transliterate into and no established phonology for
Sato's romanization, so both steps would fabricate tiers rather than derive
them. See **Notes and Issues** above (now **Notes and caveats**).

The canonical standardization and phonology steps are deliberately absent; the
reason is in Notes and Issues above, and is declared in the corpus README as a
POL-047 deviation ("Notes and Issues" is now **Notes and caveats**).

[Reproduction and validation instructions](#how-to-reproduce)
cover both scripts and the full list of caveats.

### What each step does

The original tier was transcribed by hand from the scan, with OCR used only as
a diagnostic, and every one of the article's printed pages was reviewed. The
transcription is committed as a reviewed sentence table, and the corpus's
source ledger records all 83 included sentences alongside 16 excluded
non-target blocks — the philological notes, the free summaries, the running
headings, the colophon and the covers — each with a reason. The ledger's
identifier set is checked against the XML on every validation run
(`validate.sh`, through `audit_output.py`), so a sentence cannot be dropped
silently.

Punctuation is the source's own. The Japanese translations keep the
ideographic comma 、 and the full-width parentheses （） as printed rather than
being normalized to ASCII, and the iteration mark 々 is preserved.

`generate_xml.sh` runs three steps, in this order. It first reads
`formosanbank_commit` from `CodeAndDocs/provenance.json` and, if the
FormosanBank checkout's `HEAD` differs, prints a note to stderr; the build
proceeds either way.

**1. `build_ledger.py`** (no flags). Reads
`CodeAndDocs/intermediate/source_blocks.csv` (16 excluded blocks: article
headings, the 試註 notes, the 大意 summaries and the colophon/contents/cover
pages, each with an `exclusion_reason`) and
`CodeAndDocs/intermediate/reviewed_sentences.csv` (83 reviewed rows). It maps
printed pages 116–126 to attachment PDF pages 1–11 (PDF page = printed page −
115) and writes one ledger row per block or sentence, ordered by PDF page 1–14,
to `CodeAndDocs/intermediate/source_ledger.csv`. Included rows record the
target text, the Japanese translation, the final XML path and the final `S`
id; excluded rows record the reason. It prints the included and excluded
counts.

**2. `generate_xml.py`** (no flags). Reads `reviewed_sentences.csv` and stops
with an error if any row's `review_status` is not `reviewed`, if a row names an
unknown song, if a song's sequence numbers are not 1, 2, 3, … without gaps, or
if a song's row count differs from the expected 21 / 39 / 23 (set in
`CodeAndDocs/corpus_config.py`). It also refuses to run if `XML/Pazeh/` holds
any XML file other than the three expected ones. For each song it writes one
`TEXT` with the `citation`, `BibTeX_citation`, `copyright="CC BY-NC 4.0"`,
`xml:lang="pzh"`, `source`, `glottocode="paze1234"` and `dialect="unknown"`
attributes from `corpus_config.py`, and for each row one `S` whose `source`
attribute is the locator `attachment PDF p. N; printed p. P, <source line>`,
containing `FORM kindOf="original"` (the `form_original` column, unchanged)
and, when the `translation_jpn` column is non-empty, `TRANSL xml:lang="jpn"`.
`S` ids are `nanpo1931_<song>_sNNN` with one exception: in the dispersion song,
rows 22 and 23 get `nanpo1931_dispersion_s021b` and
`nanpo1931_dispersion_s022`. Each file is written to a temporary file and
then moved into place, overwriting `XML/Pazeh/` wholesale.

**3. Shared cleaner: `QC/cleaning/clean_xml.py --corpora_path XML`.** On every
`FORM` (except `kindOf="standard"`, of which there is none) it replaces
non-breaking spaces, applies Unicode NFC, decodes HTML entities, strips
zero-width characters, normalizes caret variants to `^`, converts full-width
and typographic punctuation to ASCII, normalizes null-morpheme signs, collapses
whitespace and trims repeated punctuation. On the Japanese `TRANSL` tiers it
leaves punctuation untouched and only strips zero-width characters, decodes
entities, normalizes carets, collapses whitespace and trims repeated
punctuation. The cleaner's apostrophe/glottal-stop correction needs
`QC/validation/reference/Pazeh/attestation.txt`, which does not exist, so it
does nothing here. No `--warnings_dir` is passed: if the cleaner ever raised a
warning it would write `XML/cleaner_warnings.csv` into the published folder;
none is committed.

**Steps 4 and 5 (`standardize.py`, `add_phonology.py`) are not run**; see the
POL-047 deviation above.

#### Validation (`validate.sh`)

`validate.sh` never stops at the first failure: it runs every check, writes
each one's output to `<output-dir>/<name>.log`, prints its exit code, and exits
non-zero if any failed. In order:

1. `audit_output.py`: checks the reviewed table, the XML and the ledger
   against one another: 83 reviewed rows, 83 `S`, 82 `TRANSL`, every `FORM`
   and `TRANSL` equal to its reviewed row, each `S` id and `source` locator as
   expected, `pzh` / `paze1234` / `unknown` / `CC BY-NC 4.0` / a 1931 citation
   on every `TEXT`, no `standard` FORM, `PHON`, `W`, `M` or `AUDIO`, ten
   spot-checked rows against fixed source readings, ledger `S` ids equal to
   the XML's, all 14 PDF pages covered, and 16 excluded blocks each with a
   reason.
2. `python -m unittest discover -s CodeAndDocs/tests`: the corpus's own unit
   tests (`CodeAndDocs/tests/test_corpus.py`).
3. `QC/validation/validate_xml.py`, `validate_text.py` and
   `validate_glosses.py`, each `by_path` on `XML/` with a findings CSV in the
   output folder.
4. `QC/validation/validate_dialect.py --path XML`.
5. `QC/validation/audit_gloss_scrape.py --xml XML --no-source`.
6. `QC/validation/validate_duplicate_sentences.py by_path --tier original
   --verbose`.
7. `QC/validation/validate_port_readiness.py --corpus_path <corpus>
   --repo-root <FormosanBank>`.

`CodeAndDocs/check_source.py` is not called by either script. Run it by hand
when you have the scan: it checks the file's size, SHA-256 and (if `pdfinfo` is
installed) its 14-page count.

#### Readiness boundary

All 14 attachment pages were reviewed. The source ledger records 83 included
sentences and 16 excluded non-target blocks. Current validators, deterministic
regeneration, and clean-clone reproduction all pass.

The corpus is technically complete and, with the licence above, expressible
under POL-042. It is ready to port. No source file or QC log belongs in the
Git tree.

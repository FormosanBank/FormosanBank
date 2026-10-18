# Song Limei (2018), *Introduction to Kanakanavu Grammar*

This corpus is the Kanakanavu (`xnb`) material from Song Limei's 2018 *Kanakanafu yu yufa gailun* [Introduction to Kanakanavu Grammar] (Council of Indigenous Peoples), scraped from the official Alilin e-reader and reconciled page-by-page against the source page images. It comprises 699 grammar sentences — 650 of them with word- and morpheme-level interlinear glossing (3,477 words, 5,048 morphemes) — together with the book's Appendix 2A dictionary as a separate 870-entry lexicon. Text is in the Ortho113 orthography with Mandarin (`zho`) translations and glosses.

## Languages and dialects

Language `xnb` (Kanakanavu); dialect `Kanakanavu`; orthography Ortho113.

Both files, `XML/Kanakanavu/Song_2018_Kanakanavu_Grammar.xml` and
`XML/Kanakanavu/Song_2018_Kanakanavu_Grammar_Dictionary.xml`, carry
`xml:lang="xnb"` and `dialect="Kanakanavu"` on their `<TEXT>` element. All
translations and glosses are Mandarin (`xml:lang="zho"`).

## Source

The Kanakanavu (`xnb`) corpus drawn from Song
Limei's 2018 *Kanakanafu yu yufa gailun* [Introduction to Kanakanavu Grammar]
(Taiwan nandao yuyan congshu 16; Council of Indigenous Peoples), scraped from the
[official Alilin e-reader](https://alilin.cip.gov.tw/ebook/5949734115b6abe6caf971/HTML5/pc.html#/page/1).
It produces two files in the
[FormosanBank XML format](https://formosanbank.github.io/FormosanBank/the-bank-architecture/formosanbank-xml-format/):
the grammar's interlinear examples and the Appendix 2A dictionary.

The e-reader serves the book as 268 page images, each with a positioned-text
layer. The page images are the authority; the positioned text was used only as
a reading aid. The dictionary is the language-sorted Appendix 2A (reader
pp. 193-206), cross-checked against the duplicate Chinese-sorted Appendix 2B
(pp. 207-220), which is not published separately.

#### What's in the corpus

| | Grammar | Dictionary (Appendix 2A) |
|---|---|---|
| File (under `XML/Kanakanavu/`) | `Song_2018_Kanakanavu_Grammar.xml` | `Song_2018_Kanakanavu_Grammar_Dictionary.xml` |
| `S` elements | 699 sentences | 870 entries |
| Interlinear analyses | 650 (with `W`/`M`) | — |
| Words / morphemes | 3,477 `W` / 5,048 `M` | — |

There is no audio (see Notes and caveats).

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Song-Kanakanavu-Grammar_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

Song, Limei. (2018). *Kanakanafu yu yufa gailun* [Introduction to Kanakanavu Grammar]. *Taiwan nandao yuyan congshu*, 16. Council of Indigenous Peoples.

## License

**License:** CC BY-NC 4.0
**Rights source:** Li-May Sung (the author), date not recorded in this repository; evidence: ask maintainer

CC BY-NC 4.0 (Creative Commons Attribution–NonCommercial), by permission of the author (Li-May Sung).

The author (Li-May Sung) granted permission to publish this corpus under
**CC BY-NC 4.0** (Creative Commons Attribution–NonCommercial); the permission
evidence is on Basecamp card
[`10081339846`](https://app.basecamp.com/3340659/buckets/31258415/card_tables/cards/10081339846).
Each `<TEXT>` element's `copyright` attribute records this license as the
bare value `CC BY-NC 4.0`. (Until 2026-10-16 it held the prose "Song, Limei
(2018), Introduction to Kanakanavu Grammar (Council of Indigenous Peoples).
Licensed to FormosanBank under CC BY-NC 4.0 by permission of the author
(Li-May Sung)."; POL-042 allows only a vocabulary value there, so the
permission statement now lives in this section.) Attribution
and non-commercial use are required; see the FormosanBank
[LICENSE](../../LICENSE.md) and [AI-USE-ADDENDUM](../../AI-USE-ADDENDUM.md).

- **Rights:** published under CC BY-NC 4.0 by permission of the author (Li-May Sung); recorded in each `<TEXT>` `copyright` attribute.

## Notes and caveats

The text was scraped from the official Alilin e-reader and reconciled page by page against the source page images. The book's own orthography discussion (reader pp. 31–44) describes the Ortho113 inventory — `ʉ` and `r`, no `l` — so no orthographic conversion is applied: the standard tier differs from the original tier only where the source's own apparatus does not belong in a standard surface.

Every departure from the printed text is recorded against a named record and a reader page, with two exceptions that the code applies by rule: the source-language labels `（日語）`/`（借詞）` are stripped from dictionary headwords, and parenthesised material is deleted from word (`W`) forms (one word in the current data). Both are described below. The full list is in the corpus [README](#recorded-per-record-corrections), and the reasoning behind the standard-tier decisions is in [`standard_surface_review.md`](CodeAndDocs/docs/standard_surface_review.md).

#### Orthography, tiers and phonology

- **Orthography is Ortho113.** Detector and reviewer evidence agree: the source
  uses `ʉ` and `r`, has no `l` (its own discussion notes `r` covers the former
  `l`/`r` contrast), and maps `r` to the IPA variants `r` and `ɾ`. The current
  detector selects Ortho113 for both XML files.
- **Stress accents** (`á í ú …`) are kept in the original tier and folded in the
  standard tier (step 7); PHON is accent-free on both tiers.
- **Stress accents** (`á é í ó ú`) mark stress in the book, not distinct letters. They are kept in the original tier and folded out of the standard tier; PHON is accent-free on both tiers.
- **The standard tier is nearly the original tier.** Kanakanavu's source
  orthography already *is* Ortho113, so no transliteration happens: across the
  whole corpus the standard tier differs from the original only by the folded
  stress accents and by the one song sentence below. Do not read "standard" here
  as evidence of a spelling change.
- **The standard tier is nearly the original tier.** The book's orthography already *is* Ortho113, so nothing is transliterated: across the whole corpus the standard tier differs from the original only by the folded stress accents and by the one song example below. Do not read "standard" here as evidence of a spelling change.
- **PHON uses pipe notation for phonemic variants** (POL-013): Ortho113 maps
  Kanakanavu `r` to `[r|ɾ]`, so `[r|ɾ]` in a PHON tier means "either of these",
  not a literal bracket. It appears in 4,922 PHON elements of the grammar file
  and 678 of the dictionary file (5,600 in all). PHON is otherwise
  marker-free: no `-`, `=` or infix brackets, and no stress accents.
- **Phonetic tiers use pipe notation for phonemic variants.** Ortho113 maps Kanakanavu `r` to `[r|ɾ]`, so a bracketed pipe in PHON means "either of these", not a literal bracket. PHON is otherwise marker-free and accent-free.

#### Translations and glosses

- **Everything is Mandarin; there is no English.** All 10,090 `TRANSL` elements
  are `xml:lang="zho"`. Morpheme glosses are the book's own Chinese category
  labels — `主事焦點` (actor focus), `受事焦點` (patient focus), `完成貌`
  (perfective), `非實現` (irrealis), `重疊` (reduplication), `主格` (nominative),
  `狀態改變` (change of state) — not Leipzig abbreviations.
- **Everything is in Mandarin; there is no English.** All 10,090 translations and glosses are `xml:lang="zho"`. Morpheme glosses use the book's own Chinese category labels — `主事焦點` (actor focus), `受事焦點` (patient focus), `完成貌` (perfective), `非實現` (irrealis), `重疊` (reduplication) — rather than Leipzig abbreviations.
- **Latin script inside a translation or gloss is not only proper names.**
  389 `TRANSL` elements contain Latin letters (135 sentence translations, 123
  `W` glosses, 131 `M` glosses). Most are proper names the book prints in the
  Latin script (`Pani`, `Paicʉ`, `Pori`, `’atai`, `Kini`), but the book also
  writes some labels in Latin: `Ca` in `Ca重疊` (126 occurrences), affix labels
  in capitals (`TA`, `PA`, `KA`, `MATA`, `TAKI`, `I-`/`IN`, `TO`), `Q` for the
  question clitic `=kara`, and Kanakanavu words cited inside glosses (`=cu`) or
  inside explanatory parentheses in sentence translations (`kani`, `misee`,
  `ara-`).

#### Segmentation and interlinear conventions

- **Segmentation lives on `W`/`M`, never on `S`.** Sentence-level FORMs are
  running text: no `-`, no `=`, no `<…>` on either tier (the two hyphens that do
  appear are em dashes — see below). `W` and `M` FORMs keep the source's
  notation in **both** tiers: 733 `W` with `-`, 484 with `=`, 117 with `<…>`.
- **Segmentation lives on the word and morpheme tiers, never on the sentence tier.** Sentence forms are running text on both tiers. Word and morpheme forms keep the source's `-`, `=` and `<…>` on both tiers.
- **Interlinear conventions.** W forms keep the source's `-`, `=` and `<…>` notation. An infixed root keeps a gap hyphen and the infix is written `-X-` (`t<um>a-túturu` → `t-a`, `-um-`, `túturu`); each clitic morpheme keeps a leading `=` (`te=musu` → `te`, `=musu`).
- **Infixes follow POL-014.** A `W` keeps the source's angle brackets
  (`t<um>a-túturu`); at `M` level the infixed root is one morpheme written with a
  gap hyphen at the infixation point and the infix is written between hyphens —
  `t-a` · `-um-` · `túturu`. So an `M` FORM containing an internal `-` is a root
  with an infix gap, not an unsplit word.
- **Clitics follow POL-015.** The `=` marks the clitic, not its host:
  `te=musu` is analysed `te` + `=musu`. Every clitic in this corpus is an
  enclitic (21 distinct forms — `=cu`, `=ku`, `=maku`, `=in`, `=kasu`, `=musu`,
  `=kee`, `=kara`, `=pa`, `=kani` and others), so every clitic `M` carries a
  **leading** `=` and no `M` carries a trailing one. The matching gloss carries
  the marker too (`=他.屬格`).
- **Parenthesised optional material is removed from `W` forms.** `build_xml.py`
  deletes any `(…)` in a printed word form (step 4). In the current data this
  affects one word: `’arup(a)-ara` in `S0410` (reader p. 179) is published as
  `’arup-ara`.
- **Partial glossing is preserved, not invented.** On five page images the printed form and gloss lines do not align one-to-one. Those words are still segmented, but a morpheme the book does not gloss separately carries no gloss of its own; the word-level gloss is always present.
- **Partial morpheme glossing (4 `M`):** reader pages 182, 248, and 258 print
  segmented forms without a separately aligned gloss for every unit. Their `W`
  glosses are preserved exactly, while four `M` elements intentionally omit
  `TRANSL` rather than receiving inferred labels. Their parent `W` always keeps
  its word-level gloss, so no gloss content is lost. These are the corpus's V064
  findings.
- **Words without a morpheme analysis (2 of 3,477 `W`):** pages 68 and 128 print
  one whole-word gloss for `m-u'iara` and `ma-marang`. The words carry no `M`
  children rather than an invented segmentation.

#### What is included and excluded

- **No audio.** The source is a printed book; there are no `AUDIO` elements and
  no recordings exist for this corpus.
- **No audio.** The source is a printed book; no recordings exist for this corpus.
- **No `alternate` FORMs.** Source variants are materialized as separate `S`
  entries (dictionary) rather than as an alternate tier.
- **Dictionary variants:** slash/semicolon alternatives and optional `(…)`
  material are materialized into separate single-form entries; bound prefixes
  (trailing `-`) are excluded; cross-record duplicate variants are dropped.
  Apart from the source-language labels in the next bullet but one, nothing is
  deleted by a blanket rule — every exclusion is a recorded decision
  (`dictionary_ledger.csv` exclusions and `standard_surface_decisions.tsv`).
- **Dictionary variants are split, not concatenated.** Slash and semicolon alternatives and optional `(…)` material in Appendix 2A become separate single-form entries. Bound citation forms (a trailing hyphen, with no free-standing surface in the book) are excluded, and split variants that duplicate another record are dropped. Every exclusion is a recorded decision.
- **Source-language labels on dictionary headwords are not published.**
  Appendix 2A marks some headwords `（日語）` (Japanese) or `（借詞）` (loanword),
  e.g. `kasa（日語）`, `kunga’a（借詞）`. `extract_dictionary.py` strips these
  labels from the form (step 1), and they appear nowhere in the ledger or the
  XML. The positioned text shows 14 such labels on reader pp. 195-206.
- **Sentences without an interlinear analysis (49 of 699):** 47 are the
  punctuation examples of Appendix 1 (pp. 187-191) and 2 are body examples the
  book leaves unglossed. The book prints no word gloss for any of them and none
  was invented. These are the corpus's V148 findings.
- **49 of the 699 sentences have no interlinear analysis.** 47 are the punctuation examples of Appendix 1 (pp. 187–191, a punctuation table rather than a glossed text) and 2 are body examples the book leaves unglossed. The book prints no word gloss for any of them, and none was invented.
- **Excluded sentences (14):** 6 noun-phrase fragments, 5 source-starred
  ungrammatical forms, and 3 examples with no printed Chinese translation. See
  `source_ledger.csv`.
- **14 source examples were excluded**: 6 noun-phrase fragments, 5 forms the book marks ungrammatical, and 3 examples printed without a Chinese translation. Each exclusion is recorded with its reason in the corpus's source ledger.
- **Repeated surface forms (63 groups, 130 `S`):** 34 dictionary groups are
  homographs with different translations, one preserves two original stress
  variants that fold to the same standard form, and 28 grammar groups repeat at
  distinct source locators. There is no exact or same-locator duplicate.
- **Repeated forms are deliberate, and are distinct attestations.** 63 groups recur: 28 are grammar examples the book reuses to illustrate different points, 34 are dictionary homographs with different translations, and one is a pair of stress variants that fold to the same standard form. Each `S` carries its own `source` attribute naming the page and label it came from. There is no exact same-locator duplicate, and nothing is deduplicated.

#### The typesetting slip and the punctuation table

- **`takananga` (p.69) — a typesetting slip in the book, repaired in the
  original tier.** Reader p.69 example 4-9 prints `takananga` in its sentence
  line and `takanaga` one line below in its own aligned analysis. Confirmed
  against the page image, so this is what the book prints, not a scraping
  artifact. The reading is not in doubt: `takananga` occurs 22× across the
  corpus — including in that same example's sentence line — while `takanaga`
  occurs exactly twice, both inside that one analysis. The bare `g` is also not
  an Ortho113 letter, so before the repair it had no phonological mapping and
  surfaced as `*` in the original PHON. The repair is a recorded manual edit
  (`CodeAndDocs/manual_edits.xml`, applied by the shared
  `apply_manual_edits.py` at build step 5) to the **original** tier; the
  standard tier and both PHON tiers regenerate from it. The extraction ledgers
  still record exactly what the page prints.
- **One repaired typesetting slip.** On reader p. 69 the aligned analysis line prints `takanaga` where the sentence line of the same example prints `takananga` (`takananga` occurs 22× in the corpus, `takanaga` twice — both inside that one analysis). It is repaired in the original tier as a recorded manual edit, so the standard tier and the phonetic tiers regenerate from the corrected form; the extraction ledgers still record exactly what the page prints.
- **Three examples come from the book's punctuation table (Appendix 1, p. 190), and its marks are not what they look like.**
  - *The song.* Row 10 of that table defines a hyphen used **in songs, to break lyrics to fit the musical score** — not morpheme boundaries. The one song example keeps those hyphens exactly as printed in the original tier. Its standard tier gives the running words, whose boundaries were recovered from an independent attestation of the same song: deleting the hyphens is not enough, since the last line would run together into a single word. This is the only place in the corpus where the standard tier is set from a source-checked decision rather than derived.
  - *The dash.* Row 8 defines `--`, written with two hyphens, as the Kanakanavu spelling of the **em dash** (破折號), whose Chinese equivalent is `―`. It is punctuation introducing an explanation or a list, not segmentation. The build renders it as a single `-` in the original tier, which the standard tier then inherits unchanged — so the two examples using it show a `-` that is a dash, not a morpheme boundary. They are the corpus's only two occurrences of a hyphen in a sentence-level standard form.

- **Everything above is checkable.** No validator reports a HARD finding. The remaining warnings are the documented source properties on this page — the unglossed sentences, the two em dashes, the four unglossed morphemes, the host+clitic word count, and the repeated forms — and the corpus README lists them one by one with counts.

#### Recorded per-record corrections

Everything below is applied by name to a specific record, never by a blanket
rule. The tables in this section name the reader page each entry was checked
against; the code tables summarised in the next paragraph are keyed by record
id only, and each record's `source` attribute in the XML names its reader page.

Besides the tables below, the build applies these record-keyed tables, which
correct what the e-reader's text layer got wrong so that the analysis matches
the printed page: `GLOSS_OVERRIDES` in `extract_interlinear.py` (corrected
glosses for 59 words in 28 sentences, where the text layer merged two adjacent
printed gloss cells), `TOKEN_JOIN_OVERRIDES` in the same script (one form split
by the text layer, rejoined as `katʉrʉpʉ=cu`), and `FORM_CORRECTIONS` in
`extract_dictionary.py` (22 dictionary headwords with OCR-style doubled or split
letters, e.g. `aaka` → `aka`, `sas patʉ` → `sasápatʉ`).

**Applied to the `original` tier at extraction** (`extract_interlinear.py`,
step 3 — before any standard tier exists):

| Record | Reader page | What the source prints | What is recorded |
| --- | --- | --- | --- |
| `S0318` W3 | 156 (ex. 13-2a) | `t<in>i-taini`, gloss `重疊<完成貌>丟` | M `t-i` 重疊 · `-in-` `<完成貌>` · `taini` 丟 |
| `S0422` W2 | 182 (ex. 15-8a) | `m-ukʉrʉ`, one whole-word gloss `拿著` | M `m` · `ukʉrʉ`, **both without an M gloss** |
| `S0609` W15 | 243 (narrative 26) | `ka-cangcangarʉ-a`, gloss `處在-重疊-快樂-關係詞` | M `ka` 處在- · `cangcangarʉ` 重疊-快樂- · `a` 關係詞 (no boundary is printed inside `cangcangarʉ`, so its two gloss units stay grouped) |
| `S0636` W5 | 248 (narrative 53) | `pa-arivivini-ʉn`, gloss `使動-跟隨在後` | M `pa` 使動- · `arivivini` 跟隨在後 · `ʉn` **without an M gloss** |
| `S0678` W6 | 258 (narrative 38) | `t<um>a-túturu`, gloss `<主事焦點>-告知` | M `t-a` **without an M gloss** · `-um-` `<主事焦點>-` · `túturu` 告知 |

`ANALYSIS_OVERRIDES` in the same script gives the whole word/gloss list for
three sentences (`S0141`, p. 106; `S0221`, p. 131; `S0544`, p. 232) whose layout
cannot be recovered from the positioned text without inventing a word boundary;
the code comment says each was checked against the page image. It is keyed by
record id; the code does not cite the page in place.

**Applied to the `original` tier as a recorded manual edit**
(`CodeAndDocs/manual_edits.xml`, step 5) — the shared mechanism for repairing
an error in the original, from which every derived tier regenerates:

| Record | Reader page | Printed | Recorded |
| --- | --- | --- | --- |
| `S0012` W4 + its host M | 69 | `takanaga=kasu` / `takanaga` | `takananga=kasu` / `takananga` |

**Applied to the sentence translation** (`build_xml.py`, step 4). The book adds
an analytic paraphrase in parentheses to two translations; the primary
`TRANSL` keeps the translation, and the full printed text is kept in that
`TRANSL`'s `notes` attribute:

| Record | Reader page | Printed translation (kept in `notes`) | Primary `TRANSL` |
| --- | --- | --- | --- |
| `S0143` | 108 (ex. 7-1b) | `我有錢。（=我的錢存在）` | `我有錢。` |
| `S0149` | 109 (ex. 7-3b) | `我沒有錢。（=我的錢沒有）` | `我沒有錢。` |

**Applied to the `standard` tier only** (`normalize_standard_forms.py`, step 8).
Just one, and only because the original must stay faithful to the printed page
(POL-001) while the standard tier carries running words:

| Record | Reader page | `original` keeps | `standard` gets |
| --- | --- | --- | --- |
| `S0477` | 190 | the lyric-division hyphens exactly as printed | `mati'ara'aravang 'aa 'aravang vatu 'aravang vatu! tisa'ʉ ku 'apasʉ.` |

Reader p.190's punctuation table (Appendix 1, row 10, 連結號) defines that
hyphen as a *song* mark — it breaks lyrics to fit the musical score, not
morphemes. Deleting the hyphens is not enough to recover words: the printed
`ti-sa-'ʉku-'a-pa-sʉ` would collapse to a single `tisa'ʉku'apasʉ`, where the
attested reading is three words. The boundaries come from an independent
attestation of the same song, pinned by commit and SHA-256 in
`docs/standard_surface_review.md`.

The other two grammar decisions (`S0469`, `S0472`) change no text at all. Row 8
of the same p.190 table defines `--` as the halfwidth spelling of 破折號, the
em dash whose fullwidth Chinese equivalent is `―`; `build_xml.py` renders it as
a single `-` in the **original** tier, so the standard tier inherits it
unchanged and the decision rows only attach a `notes` string. (This is why
`validate_text` reports two V133 `-`-in-standard findings: the mark is
punctuation, but it is spelled like a segmentation hyphen.)

The dictionary's 125 remaining decisions in `standard_surface_decisions.tsv`
change nothing at this step: `build_xml.py` has already emitted one clean
surface per entry, and step 8 only *verifies* that state.

## Reproduction and processing

### How to reproduce

```bash
bash Corpora/Song-Kanakanavu-Grammar/CodeAndDocs/generate_xml.sh
```

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

The reviewed ledgers and raw source are retained under `CodeAndDocs/`, so a
rebuild does **not** re-scrape. One command rebuilds the published `XML/` from
them:

```bash
CodeAndDocs/generate_xml.sh
```

That is the corpus's only entry point; it runs every step below in order and
writes the two files in `XML/Kanakanavu/` in place, so `git diff` shows exactly
what a rebuild changes. It uses the FormosanBank checkout that contains this
corpus for the shared QC utilities (pass a path, or set `FORMOSANBANK_PATH`, to
use another one). For the interpreter it uses `PYTHON` if that is set, otherwise
`CodeAndDocs/.venv/bin/python3` if that exists, otherwise `python3`. The
dependencies are in `CodeAndDocs/requirements.txt`:

```bash
python3 -m venv CodeAndDocs/.venv
CodeAndDocs/.venv/bin/pip install -r CodeAndDocs/requirements.txt
```

Steps 1 and 3 also rewrite `intermediate/dictionary_ledger.csv` and
`intermediate/interlinear_ledger.jsonl`; step 4 then checks both against their
pinned hashes, so a rebuild that changes either ledger stops there.

`build_xml.py` asserts the source-PDF/positioned-text hashes, the closed
page/candidate inventory, the reviewed-artifact hashes, the ledger counts, and
continuous sentence IDs — so any drift in the source or the ledgers fails the
build loudly. `CodeAndDocs/provenance.json` records the FormosanBank commit the published
XML was last built against (POL-052), and `generate_xml.sh` notes it when the
checkout differs — a note, never a gate: rebuilds run with the current tools. The rebuild is
deterministic: running it twice reproduces the same bytes.

`CodeAndDocs/tests/` holds the extraction regression tests, which also check the
published XML; run them with `pytest` from `CodeAndDocs/`.

#### Project structure

- **`XML/Kanakanavu/`** — the published data: `Song_2018_Kanakanavu_Grammar.xml` and `Song_2018_Kanakanavu_Grammar_Dictionary.xml`.
- **`CodeAndDocs/`** — everything needed to reproduce `XML/` from the source:
  - `scripts/` — acquisition and the reproduction pipeline (see [Processing](#what-each-step-does)).
  - `raw_data/` — the acquired source, retained so the corpus rebuilds without re-scraping: `source.pdf` (the 268 official Alilin page images compiled in order) and `official_text.jsonl` (the official positioned-text layer, one record per page). Both SHA-256-pinned in `scripts/build_xml.py`.
  - `intermediate/` — the reviewed ledgers the build consumes (all hash-pinned in `build_xml.py`): `page_inventory.csv` + `candidate_ledger.csv` (the closed page/candidate review — 268 pages, 443 machine candidates, all with terminal statuses); `source_ledger.csv` (699 included, 14 excluded, with reasons); `dictionary_ledger.csv` (767 headwords; 11 marked bound-excluded); `interlinear_ledger.jsonl` (the recovered `W`/`M` analyses); and `standard_surface_decisions.tsv` (128 exact, source-reviewed standard-tier decisions).
  - `docs/` — `extraction_plan.md`, `extraction_review.md` (the page-by-page review log), `source_manifest.md`, `standard_surface_review.md`, `mt_quality_review.md`, and `clean_clone_reproduction.md`.
  - `tests/` — interlinear-extraction regression tests.
  - `requirements.txt`.

#### QC

Adjudication is recorded in `CodeAndDocs/docs/standard_surface_review.md`,
`CodeAndDocs/docs/mt_quality_review.md`, and
`CodeAndDocs/docs/clean_clone_reproduction.md`.

**No HARD finding from any validator, and `validate_port_readiness` reports
0 HARD / 0 WARN.** Every remaining SOFT row is a documented source property,
explained above:

| Validator | SOFT | What they are |
| --- | --- | --- |
| `validate_xml` | 49 × V148 | the 49 `S` the book prints without a word gloss |
| `validate_text` | 4 × V122, 2 × V133 | one genuine prose parenthetical (S0456, mirrored in its Chinese translation) and the two p.190 em dashes |
| `validate_glosses` | 377 × V060, 3 × V061, 4 × V064 | V060: a host+clitic is one `W` but two whitespace-free words, so W-count and word-count differ by design; V061: three words the book segments without printing a boundary for every unit; V064: the four deliberately unglossed `M` |
| `validate_duplicate_sentences` | 63 groups | 34 dictionary homographs with different translations, 1 stress-variant pair that folds to one standard form, 28 grammar repeats at distinct source locators. No exact same-locator duplicate; nothing is deduplicated |

Reproduce any of them with, e.g.:

```bash
python QC/validation/validate_text.py by_path --path Corpora/Song-Kanakanavu-Grammar/XML
```

### What each step does

#### Upstream (one-time; the outputs are committed, so you do not re-run these)

**A. Acquire the source** — `scripts/acquire_source.py` downloads every numbered
Alilin page image and its `iPhone/text/<page>.xml` positioned-text record,
verifies the page count, compiles the images into `raw_data/source.pdf`, and
writes `raw_data/official_text.jsonl`. The **page images are authoritative**; the
positioned text is a reading aid only. (The two output paths are passed as
`--pdf` and `--text-jsonl`; the script checks that the reader's manifest
declares 268 pages.)

**B. Build machine candidates** — `scripts/build_candidates.py` scans the
positioned text for labeled examples and writes `page_inventory.csv` +
`candidate_ledger.csv` (all `UNREVIEWED`).

**C. Human review** (the heart of the corpus) — every one of the 268 pages was
reconciled by hand against the page image: expanding/repairing machine
candidates, recovering examples that had no candidate, restoring word boundaries
and punctuation the text layer had dropped, and excluding non-sentences. The
result is `source_ledger.csv` (699 included, 14 excluded). The full page-by-page
log is `docs/extraction_review.md`.

#### Rebuild pipeline (`CodeAndDocs/generate_xml.sh`)

Before step 1 the script checks that the FormosanBank checkout has
`QC/cleaning/clean_xml.py`, and prints a note on stderr if that checkout's
commit differs from the one in `provenance.json`.

1. **Extract the dictionary** — `extract_dictionary.py` reconstructs Appendix 2A
   from the positioned text, cross-checking barred vowels against the duplicate
   Chinese-sorted Appendix 2B and applying documented OCR corrections →
   `dictionary_ledger.csv`.
   In detail: it reads reader pp. 193-206 (2A, two columns per page) and
   pp. 207-220 (2B). Where a 2A headword and a 2B headword have the same letters
   (ignoring the `u`/`ʉ` difference) and overlapping translations, every `u`
   that 2B prints as `ʉ` becomes `ʉ`. It then applies the 22 record-keyed
   `FORM_CORRECTIONS`, strips the `（日語）`/`（借詞）` source-language labels, and
   marks the 11 headwords that end in `-` as `included = no`, with the reason
   "Source prints a bound citation form with a trailing hyphen and supplies no
   unattached surface". It writes all 767 headwords, with IDs
   `song-2018-kanakanavu-dictionary-0001` to `-0767`.

2. **Verify barred-vowel reconciliation** — `reconcile_barred_vowels.py --check`
   confirms the `u`/`ʉ` corrections between the sentence ledger and the dictionary
   are consistent (fails if they have drifted).
   Concretely: for each word of each sentence in `source_ledger.csv` it looks up
   the dictionary forms with the same letters (ignoring `u`/`ʉ`, apostrophe style
   and accents); if every such form has `ʉ` where the sentence has `u`, the row
   still needs a correction. With `--check` it prints those rows and exits 1 if
   there are any; it writes nothing.

3. **Recover interlinear analyses** — `extract_interlinear.py` aligns each
   reviewed sentence's printed word and gloss lines into `W`/`M` analyses (650
   analyses; 3,477 `W`; 5,048 `M`), using position-based alignment plus
   source-checked overrides for cells the text layer merged →
   `interlinear_ledger.jsonl`. W forms keep the source's `-`, `=`, and `<…>`
   notation. Under POL-014, an infixed root keeps a gap hyphen and the infix is
   written `-X-`; under POL-015, each clitic M keeps a leading `=`. Four override
   tables in that script carry what the positional aligner cannot derive, each
   keyed by record id: `GLOSS_OVERRIDES` (28 sentences where the text layer
   merged two adjacent printed gloss cells), `TOKEN_JOIN_OVERRIDES` (one form the
   text layer split), `ANALYSIS_OVERRIDES` (three sentences whose layout cannot
   be recovered without inventing a word boundary) and
   `MORPHEME_OVERRIDES` (five page images whose printed form and gloss lines do
   not align one-to-one, preserving partial source glossing without inventing
   missing M glosses). Only the `MORPHEME_OVERRIDES` entries cite their reader
   page in the code. All are applied to the **original** tier at extraction,
   before any standard tier exists — see "Recorded per-record corrections" under
   Notes for the full list.
   Other things this step does, all in the same script: it skips reader
   pp. 187-220 (the punctuation appendix and the dictionary) and the two
   unglossed body examples `S0046` and `S0172`; it builds a lookup of known
   glosses from the dictionary ledger and from cleanly aligned examples on
   pp. 47-184 and 221-262, and uses it to choose between possible alignments;
   it restores `ʉ` in analysis forms from the dictionary the same way step 2
   checks sentences; it moves a gloss fragment that the text layer attached to
   the wrong cell (`格`, `主`/`事焦點`, `屬格`) back to its neighbour; where a
   printed form offers `a/b` alternatives it keeps the one that occurs in the
   sentence; and for ledger labels marked `-no-sua`/`-without-sua`, `-no-na` or
   `-no-miura` it leaves out the word that the sentence omits. A sentence for
   which no alignment passes the gloss checks gets no analysis.

4. **Build the XML** — `build_xml.py` writes both files (after asserting all
   hashes/counts):
   - **Grammar:** 699 `S`; the 650 with a printed analysis get `W`/`M`. The
     other **49 carry a translation but no `W`/`M`**, because the book prints
     none: 47 are the punctuation examples of Appendix 1 (pp. 187-191, which is
     a punctuation table, not a glossed text), and 2 are body examples the book
     leaves unglossed (5-2 on p.80, footnote 27 on p.118). No analysis is
     invented for them, so they are the corpus's V148 `W_less_S` findings.
     Each `S` gets a `source` attribute naming the reader page, the ledger label
     and the review note. The `--` in `S0469` and `S0472` becomes a single `-`
     in the original FORM, with a `notes` attribute saying so (the build stops
     if any other sentence contains `--`). For `S0143` and `S0149` the printed
     parenthetical paraphrase is moved out of the translation into the
     `TRANSL`'s `notes` attribute (see the table under Notes). In `W` forms any
     parenthesised material is deleted (`’arup(a)-ara` → `’arup-ara`).
   - **Dictionary:** the 767 headwords become **870 single-form `S` entries**.
     Slash (`/`), semicolon (`;`), and optional `(…)` variants are split into
     separate entries *before the standard tier is copied* — 114 headwords split,
     adding 140 entries; multi-variant headwords get `a`/`b`/`c`-suffixed IDs
     (e.g. `dictionary-0006a`), share the TRANSL, and note the printed apparatus
     on the original tier. 26 split variants whose (form, translation) duplicate
     another record are dropped (the source prints those forms as their own
     records). The 11 bound citation forms (trailing `-`, e.g. `ara-`, `'ap(a)-`)
     are excluded — no free-standing surface exists. There is **no `alternate`
     tier**, and every (form, translation) pair is unique.
     The split outputs come from the `dictionary` rows of
     `standard_surface_decisions.tsv`; the 26 dropped variant IDs are a fixed
     list in `normalize_standard_forms.py` (`DUPLICATE_VARIANT_ENTRY_IDS`), and
     the build stops if the computed duplicates differ from it.
   - Both `<TEXT>` elements get `xml:lang="xnb"`, `dialect="Kanakanavu"`,
     `copyright="CC BY-NC 4.0"`, the citation and BibTeX citation, and a
     `source` attribute naming the reader URL and the source PDF's SHA-256.

5. **Re-apply manual edits** — `apply_manual_edits.py` (FormosanBank) re-applies
   the recorded hand edits in `CodeAndDocs/manual_edits.xml` before any cleaning
   or derivation, so every downstream tier is built from the repaired original.
   One record: the p.69 `takananga` typesetting slip (see Notes). The script
   warns loudly if a record has become a no-op.
   Flags: `--corpora_path XML/`.

6. **Clean** — `clean_xml.py` (FormosanBank) does canonical Unicode / HTML-entity
   / punctuation normalization.
   Flags: `--corpora_path XML/`. Its per-run report, `XML/cleaner_warnings.csv`,
   is deleted at the end of the build (it is reviewed during QC and is not
   corpus data).

7. **Create the standard tier** — `standardize.py --remove_accents`
   (FormosanBank). The source is already Ortho113, so no conversion table is
   needed; `--remove_accents` copies the original tier and folds the source's
   acute stress vowels (`á é í ó ú`, and the decomposed `ʉ́`) out of the
   standard tier only. Stress is suprasegmental annotation in this source, not
   Ortho113 orthography, so the original tier keeps the printed accents.

8. **Apply reviewed surface decisions** — `normalize_standard_forms.py` walks
   the 128 exact decisions in `standard_surface_decisions.tsv`. No marker is
   removed by a blanket rule, and in practice this step **rewrites exactly one
   sentence**: the song on p.190, whose lyric hyphens resolve to independently
   attested word boundaries. The other 127 decisions are *verified*, not
   applied — `build_xml.py` has already emitted one clean surface per dictionary
   entry, and the two break-punctuation sentences are unchanged text carrying a
   `notes` attribute. The step also asserts that no analysis marker survives in
   any sentence-level standard form. Ordinary prose parentheses are left
   unchanged. See "Recorded per-record corrections" above (under Notes and caveats).
   It stops if the manifest no longer has exactly 128 decisions (125 dictionary,
   3 grammar, 11 bound exclusions, 140 extra entries), if the hyphen-bearing
   grammar sentences are not exactly the three with decisions, if a decision's
   expected source text or page no longer matches the XML, or if the dictionary
   no longer has 870 entries.

9. **Add phonology** — `add_phonology.py --orthography Ortho113`
   (FormosanBank), both tiers. PHON is a segmental tier, so the shared utility
   folds stress accents itself before mapping; the original FORM keeps its
   accents and the PHON is clean IPA. There is no corpus-specific phonology
   mapping and no corpus-specific wrapper.

Last, the script deletes `XML/cleaner_warnings.csv` and prints
`Rebuilt …/XML/Kanakanavu/`.

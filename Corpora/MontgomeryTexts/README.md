# Montgomery Amis texts (1962)

This corpus contains three Amis texts with word-level segmentation, English word glosses and English sentence translations, digitized from [this publication](CodeAndDocs/Original.pdf) (cited in full under "How to cite" below). The `standard` tier is a real transliteration of the original through Akiw's letter correspondences below, not a copy of it: 185 of the 391 sentence- and word-level forms differ, including every sentence-level form.

## Languages and dialects

Amis (ISO 639-3 `ami`), in all three files: `XML/Amis/Day_I_Now.xml`, `XML/Amis/Fire_and_Water.xml` and `XML/Amis/Silo.xml`. Every `<TEXT>` carries `xml:lang="ami"` and `dialect="unknown"`. The source does not record the dialect.

The `dialect` attribute is left as `unknown`: the article does not say, and nothing in the orthography narrows it. (Southern Amis in particular is ruled out rather than suggested — Ortho113 marks `f` and `o` as unused in Southern, and these texts are full of both.)

## Source

Three Amis (`xml:lang="ami"`, `dialect="unknown"`) narrative texts published in the 1962 SIL Work Papers article reproduced at [`CodeAndDocs/Original.pdf`](CodeAndDocs/Original.pdf). Each sentence carries an English free translation, and each word an English gloss. The texts are **segmented into words but not into morphemes**: hyphens in the FORMs mark morpheme boundaries, but the article gives no morpheme-by-morpheme gloss line, so no `M` tier is invented. There is no audio.

| File | Text in the article | Sentences | Words |
|---|---|---|---|
| `XML/Amis/Day_I_Now.xml` | *O-LEMAK AKO ANINI* ("Day I Now") | 18 | 168 |
| `XML/Amis/Fire_and_Water.xml` | *NAMAR ATO NANOM* ("Fire and Water") | 11 | 100 |
| `XML/Amis/Silo.xml` | *SIRO* ("Silo") | 11 | 86 |

The article uses a 1962 SIL field transcription that it never names; it was identified afterwards (see Notes and caveats). Each file's first sentence is the text's **printed title**, which the article sets over its own word-aligned English gloss line, so the titles are published as sentences like any other.

Each file's `S1` is the text's **printed title**. The article sets each title over its own word-aligned English gloss line, in the same two-line format it uses for every numbered example, so the titles are translated text and are published as sentences like any other. `S2` onward are the article's numbered examples 1..n.

Two of the three titles are single-phrase headings with no word gloss beneath them, so `Fire_and_Water/S1` and `Silo/S1` carry no `W` elements. That is why `validate_xml` reports two SOFT `V148 W_less_S_in_segmented_file` findings; they are expected.

In the words of the old corpus page: the texts are segmented into words but **not into morphemes**: the hyphens in the forms mark morpheme boundaries, but the article gives no morpheme-by-morpheme gloss line, so no morpheme tier is invented.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/MontgomeryTexts_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

> Tamih and Montgomery, Robert L. (1962) Amis text. Work Papers of the Summer Institute of Linguistics, University of North Dakota Session: Vol. 6, Article 6. 10.31356/silwp.vol06.06

## License

**License:** CC BY-NC-ND 4.0
**Rights source:** Summer Institute of Linguistics / University of North Dakota (publisher), 2026-08-23; evidence: ask maintainer

The individual authors cannot be located. The publisher — the Summer Institute of Linguistics / University of North Dakota — released the article as **CC-BY-ND**, and FormosanBank has **interpreted that licence liberally** in order to publish the texts with their glosses and translations; publication rights were confirmed by the maintainer on 2026-08-23. The value recorded in `TEXT/@copyright` is `CC BY-NC-ND 4.0`, the `rights_vocabulary.csv` spelling (POL-042; an unversioned licence is 4.0). If you are a copyright owner, please reach out to us.

This corpus is also subject to the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

## Notes and caveats

#### The PHON tier was regenerated in September 2026

> **The `PHON` (IPA) tier was regenerated in September 2026, and 568 of its
> 788 values changed.** If you took a copy before then, refresh it. Three
> things moved: the retired bare-tilde variant notation (`o~u`) became the
> current `[o|u]` form; segmentation hyphens were stripped, as a PHON should
> not carry them; and a wrong cell in the orthography profile was corrected —
> it had given the letter `l` the sound /d/, where Akiw's own example
> (`tamlaw` → `tamdaw` "people", /tamɬaw/) shows it writes /ɬ~ɮ/. Before the
> fix, the same word was transcribed /dafak/ from the original tier and
> /ɬafak/ from the standard. They now agree on every element, and no value
> carries an uncertainty marker.

#### Orthography

The article uses a 1962 SIL field transcription and never names it. It was identified afterwards, by **Hsu Cheng-Wen "Akiw"**, whose letter correspondences are recorded as [`Orthographies/ConversionTables/Amis_Montgomery_113.tsv`](../../Orthographies/ConversionTables/Amis_Montgomery_113.tsv) and are what the `standard` tier is built with:

| Original (Montgomery) | Ortho113 | |
|---|---|---|
| `ts` | `c` | |
| `?` | `'` | glottal stop |
| `ř` | `r` | |
| `r` | `l` | |
| `l` | `d` | e.g. `tamlaw` → `tamdaw` "people" |

Two consequences worth knowing before using the original tier:

- **`?` is a letter, not punctuation.** It writes the glottal stop, word-internally and word-finally — `roma?` "home", `farotso?` "heart", `?aromanay` "many". Do not strip it, and do not read a sentence containing it as a question. It is also why `validate_text` reports two SOFT `V135 trailing_punct_mismatch` findings: an original FORM ending in `?` becomes a standard FORM ending in `'`, which V135 reads as a punctuation change.
- **`ř` is a letter of the transcription**, distinct from `r`, in `tahiřa`, `iřa`, `tayřa`, `hřek`, `řakot`, `mařanam` and others. It maps to Ortho113 `r`, while plain `r` maps to `l`; collapsing the two would merge two phonemes.

The table audits cleanly through IPA: `QC/validation/validate_conversion_table.py` confirms all five rows, with no information loss and no integrity errors. (It reports one mismatch under the **Southern** column, where Ortho113 `d` is /d/ rather than /ɬ~ɮ/. Southern is not a candidate for this text in any case: Ortho113 marks `f` and `o` `NA` for Southern, and Montgomery's text is full of both — `farotso?`, `foti?`, `toki`, `roma?`.) `dialect` stays `unknown`: the article does not say, and nothing in the orthography narrows it.

The correspondence table audits cleanly through IPA — all five rows confirmed, no information loss.

Akiw also notes two features that the correspondence table cannot express and that are **not** corrected in the data: the central vowel `e` is often simply absent (`tstsay` for *cecay* "one", `mahřek` for *maherek* "finish"), and glides are written inconsistently (`soar` for *sowal* "words"). The standard tier is a letter-for-letter transliteration, not a normalization; it does not repair either.

#### The uncertain letter

One word, `Day_I_Now/S15`'s `ma-sasi?af̆a?ařaw`, contains an **`f` carrying a diacritic** — the only occurrence in the corpus, and the source of the two SOFT `V116 non_ascii_in_form` findings. Akiw's notes record its status as uncertain, and it remains so. The XML writes it `f` + U+0306 COMBINING BREVE.

A 1200 dpi reading of `Original.pdf` p.19, example 14 shows the diacritic as a **caron**, the same mark the typescript puts on every `ř`, which would make the letter `f` + U+030C. That is an observation, not a change: one glyph on a 1962 mimeograph is not enough evidence to move a published letter for the third time (it was U+0302 before June 2026), and the maintainer has ruled that it stands until there is more. Recorded here so the next reader starts from the evidence rather than repeating the reading.

The status of the diacritic on `f` (which is rare — one word, `ma-sasi?af̆a?ařaw`) is uncertain, and remains so. The published XML writes it as `f` with a combining breve. A high-resolution reading of the scan suggests the mark is a caron, matching the `ř` elsewhere on the same line, but a single glyph on a 1962 mimeograph is not enough evidence to change a published letter, so it stands. The reasoning is recorded in the corpus's [`CodeAndDocs/source_discrepancies.md`](CodeAndDocs/source_discrepancies.md).

#### The PHON tier

`PHON` is regenerated by `add_phonology.py`: the `original` tier through [`Orthographies/Montgomery/Amis.tsv`](../../Orthographies/Montgomery/Amis.tsv), the `standard` tier through Ortho113 (POL-003). It comes out clean — **788 elements, zero `*` uncertainty markers**, and the original and standard PHON of every element now agree, which is what a sound-preserving transliteration should produce.

That last point is new. Until this rebuild, `Orthographies/Montgomery/Amis.tsv` gave the letter `l` the IPA value **`d`** — the letter it maps to in Ortho113, not that letter's sound. Ortho113's `d` is /ɬ~ɮ/, so the same word came out /dafak/ from the original tier and /ɬafak/ from the standard: one word, two pronunciations, differing in 50 of 394 elements. Akiw's own example gives the answer — `tamlaw` → `tamdaw` "people", which is pronounced /tamɬaw/, so Montgomery's `l` writes /ɬ~ɮ/. The profile now says `[ɬ|ɮ]`, the two tiers agree, and `validate_conversion_table.py` resolves all five rows.

The published PHON also predated POL-013: all 482 of its variant notations were the retired bare `~` form (`o~u`), which is the whole of GitHub issue #103's PHON complaint. They are now `[o|u]`, and segmentation hyphens are stripped as POL-003 requires. Of 788 elements, 568 change and none is deleted.

#### Hyphens

The import of hyphens, which are used sporadically, has not been ascertained. In the published data they are treated as morpheme boundaries: kept on the word tier, and removed from sentence-level `standard` forms so that tier reads as running text.

#### Source notation preserved in the original tier

- **`( )` marks the article's own commentary** in a gloss or translation — `is (existing)`, `you (pl)`, `eleven (?) o'clock`. These are the article's, they read naturally, and they are kept inline (POL-024). They are the ten SOFT `V122 parens_slashes_anywhere` findings.
- **`/` separated two English equivalents of one word** in the article's gloss line — `good/holy`, `noon/lunch`, `trip/walk`, `whole/all`, `and/with`. The Amis word does not vary, only its English rendering, so these are **not** POL-027 alternations and do not become separate sentences. Each is published as a primary `TRANSL` plus a `TRANSL[@ver="alt"]` on the same `W` — POL-025's mechanism one tier down (maintainer ruling, 2026-09-07). The five are listed with their page and example number in [`CodeAndDocs/gloss_alternations.json`](CodeAndDocs/gloss_alternations.json). **No published TRANSL keeps a slash.**
- **Hyphens mark morpheme boundaries** and are kept exactly as the article prints them on the word tier. Sentence-level `standard` FORMs have them removed, so that tier reads as running text (C012); the sentence-level `original` FORMs keep them.

#### Corrections against the source

Recorded in [`CodeAndDocs/source_discrepancies.md`](CodeAndDocs/source_discrepancies.md). There is one: the article prints `mi-salrama` in Silo example 4, and the sentence-level FORM had been hand-corrected to `mi-salama` in 2026 while the word-level FORM kept `mi-salrama`. The printed spelling is restored at both levels (POL-001).

#### Akiw's notes

Many thanks are owed to Hsu Cheng-Wen "Akiw", who helped identify the orthography. Her notes follow.

1. Letter Correspondences

These are some identified differences between the original orthography and the current standard. They are the table under "Orthography" above; Akiw headed its columns Original | Ortho113. Her note on the diacritic on `f` is under "The uncertain letter" above.

2. Omission of the central vowel “e”

It appears that the central vowel is missing in many places:

- mahřek -> maherek ("finish")
- tstsay -> cecay ("one")
- pafri -> pafeli ("give")

3. Glides are used inconsistently.

- soar → sowal (“words”)
- tsiwro → ciwlo(“elders” / 長老— loanword )

A fourth item that the old corpus page listed among these notes records a FormosanBank import decision rather than Akiw's observations:

4. Two English equivalents for one word

The article's gloss line sometimes gives two English readings separated by a slash — `good/holy`, `noon/lunch`, `trip/walk`, `whole/all`, `and/with`. The Amis word does not vary, only its English rendering, so these are not published as separate sentences. Each is a primary translation plus a second one marked `ver="alt"` on the same word. No published translation keeps a slash.

## Reproduction and processing

### How to reproduce

```bash
bash Corpora/MontgomeryTexts/CodeAndDocs/generate_xml.sh
```

From inside the corpus folder the same script runs as `./CodeAndDocs/generate_xml.sh`. It takes one optional argument, a FormosanBank root (or set `FORMOSANBANK_ROOT`), whose QC scripts and conversion table it uses; by default that is the checkout this corpus lives in. It runs `PYTHON` if set, otherwise that root's `.venv/bin/python`, falling back to `python3`. It stops with an error if the snapshot folder or `Orthographies/ConversionTables/Amis_Montgomery_113.tsv` is missing. It writes only `XML/` (plus any warning reports, see below). There is no `validate.sh`.

This corpus does not yet have a `CodeAndDocs/provenance.json` (POL-052; it is listed in `provenance_pending.txt`), so the FormosanBank commit the published XML was last built with is not recorded.

The run is idempotent: `XML/` is rebuilt from the snapshot every time, so a re-run over a clean checkout leaves `git status` empty. Nothing outside this checkout is required (POL-048).

All four shared pipeline steps run, so there is no step-order deviation to declare. Two smaller ones:

- **`apply_manual_edits.py` is not run** — the corpus has no `manual_edits.xml`. Hand corrections belong in the snapshot, which is the source of record, and are recorded in `source_discrepancies.md`.
- **`standardize.py` is passed `--segmented-without-m-tier`.** This corpus prints morpheme hyphens but publishes no `M` tier, and C012's hyphen handling is otherwise gated on the presence of one. The flag is opt-in and off by default: an S-level hyphen is not always segmentation, so whether a corpus's hyphens are is a per-corpus judgement.

Validators are not run by the build (POL-047, "build only"). Against this XML they report **0 HARD** findings; the SOFT findings are the ones explained above.

### What each step does

The four content pages of `Original.pdf` are image-only scans with no text layer, so there is no OCR or scrape stage to re-run. The texts were typed into XML by hand, and [`CodeAndDocs/pre_correction_snapshot/XML/`](CodeAndDocs/pre_correction_snapshot/XML/) — the **original tier only** — is this corpus's source of record (POL-035). `generate_xml.sh` rebuilds `XML/` from it in four steps:

1. `CodeAndDocs/generate_xml.py` — snapshot → `XML/`, splitting the five slashed word glosses per `gloss_alternations.json`.
2. `QC/cleaning/clean_xml.py` — shared original-tier canonicalization.
3. `QC/utilities/standardize.py --tsv_path Orthographies/ConversionTables/Amis_Montgomery_113.tsv --segmented-without-m-tier` — rebuilds the `standard` tier from the original (POL-002).
4. `QC/utilities/add_phonology.py --orthography Montgomery` — rebuilds both `PHON` tiers (POL-003).

In more detail:

1. **`generate_xml.py --snapshot CodeAndDocs/pre_correction_snapshot/XML --alternations CodeAndDocs/gloss_alternations.json --xml-dir XML`.** Refuses to run unless the target folder is named `XML`, then deletes `XML/` and rebuilds it. It reads every `.xml` file under the snapshot (three files; original-tier `FORM`s, `TRANSL`s and `W`s only, no `standard` FORM and no `PHON`). For each of the five entries in `gloss_alternations.json` it finds the named `W` (e.g. `Amis/Day_I_Now.xml` `S4W8`), requires exactly one `TRANSL` whose text is the printed slashed gloss (`good/holy`), rewrites it to the primary reading (`good`) and inserts a `TRANSL xml:lang="eng" ver="alt"` with the second reading (`holy`) right after it. A listed gloss that no longer matches the snapshot, a listed file that does not exist, or a count other than five applied is a hard error. It writes each file to the same relative path under `XML/` (pretty-printed) and prints `Built 3 files from the snapshot; split 5 slashed glosses`.
2. **`clean_xml.py --corpora_path XML`.** The shared cleaner, run in place. The comment in `generate_xml.sh` describes it as original-tier canonicalization of typographic quotes, dashes and tildes, null glyphs and entities. No `--warnings_dir` is passed, so its per-run report `cleaner_warnings.csv` is written into `XML/` when there are findings (and a stale one is removed when there are none); review it, then delete it, never commit it (POL-033).
3. **`standardize.py --tsv_path Orthographies/ConversionTables/Amis_Montgomery_113.tsv --corpora_path XML --segmented-without-m-tier`.** Builds each sentence- and word-level `standard` FORM from the `original` FORM through Akiw's five letter correspondences (`ts`→`c`, `?`→`'`, `l`→`d`, `r`→`l`, `ř`→`r`). With `--segmented-without-m-tier`, C012's hyphen handling also applies to S-level `standard` FORMs although the corpus has no `M` tier, so segmentation hyphens are removed there; `W`-level FORMs keep them. Its per-run report, `standardize_warnings.csv`, is written into `XML/` the same way; review it, then delete it.
4. **`add_phonology.py --orthography Montgomery --corpora_path XML`.** Writes the `original` PHON from the profile in `Orthographies/Montgomery/Amis.tsv` and the `standard` PHON from Ortho113.

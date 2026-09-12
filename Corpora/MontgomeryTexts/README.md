# Montgomery Amis texts (1962)

## Rights

**License:** CC BY-NC-ND 4.0
**Rights source:** Summer Institute of Linguistics / University of North Dakota (publisher), 2026-08-23; evidence: ask maintainer

> Tamih and Montgomery, Robert L. (1962) Amis text. Work Papers of the Summer Institute of Linguistics, University of North Dakota Session: Vol. 6, Article 6. 10.31356/silwp.vol06.06

The individual authors cannot be located. The publisher released the article as **CC-BY-ND**, and FormosanBank has **interpreted that licence liberally** in order to publish the texts with their glosses and translations; publication rights were confirmed by the maintainer on 2026-08-23. The value recorded in `TEXT/@copyright` is `CC BY-NC-ND 4.0`, the `rights_vocabulary.csv` spelling (POL-042; an unversioned licence is 4.0). If you are a copyright owner, please reach out to us.

This corpus is also subject to the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

## Contents

Three Amis (`xml:lang="ami"`, `dialect="unknown"`) narrative texts published in the 1962 SIL Work Papers article reproduced at [`CodeAndDocs/Original.pdf`](CodeAndDocs/Original.pdf). Each sentence carries an English free translation, and each word an English gloss. The texts are **segmented into words but not into morphemes**: hyphens in the FORMs mark morpheme boundaries, but the article gives no morpheme-by-morpheme gloss line, so no `M` tier is invented. There is no audio.

| File | Text in the article | Sentences | Words |
|---|---|---|---|
| `XML/Amis/Day_I_Now.xml` | *O-LEMAK AKO ANINI* ("Day I Now") | 18 | 168 |
| `XML/Amis/Fire_and_Water.xml` | *NAMAR ATO NANOM* ("Fire and Water") | 11 | 100 |
| `XML/Amis/Silo.xml` | *SIRO* ("Silo") | 11 | 86 |

Each file's `S1` is the text's **printed title**. The article sets each title over its own word-aligned English gloss line, in the same two-line format it uses for every numbered example, so the titles are translated text and are published as sentences like any other. `S2` onward are the article's numbered examples 1..n.

Two of the three titles are single-phrase headings with no word gloss beneath them, so `Fire_and_Water/S1` and `Silo/S1` carry no `W` elements. That is why `validate_xml` reports two SOFT `V148 W_less_S_in_segmented_file` findings; they are expected.

## Orthography

The article uses a 1962 SIL field transcription and never names it. It was identified afterwards, by **Hsu Cheng-Wen "Akiw"**, whose letter correspondences are recorded as [`Orthographies/ConversionTables/Amis_Montgomery_113.tsv`](../../Orthographies/ConversionTables/Amis_Montgomery_113.tsv) and are what the `standard` tier is built with:

| Montgomery | Ortho113 | |
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

Akiw also notes two features that the correspondence table cannot express and that are **not** corrected in the data: the central vowel `e` is often simply absent (`tstsay` for *cecay* "one", `mahřek` for *maherek* "finish"), and glides are written inconsistently (`soar` for *sowal* "words"). The standard tier is a letter-for-letter transliteration, not a normalization; it does not repair either.

### The uncertain letter

One word, `Day_I_Now/S15`'s `ma-sasi?af̆a?ařaw`, contains an **`f` carrying a diacritic** — the only occurrence in the corpus, and the source of the two SOFT `V116 non_ascii_in_form` findings. Akiw's notes record its status as uncertain, and it remains so. The XML writes it `f` + U+0306 COMBINING BREVE.

A 1200 dpi reading of `Original.pdf` p.19, example 14 shows the diacritic as a **caron**, the same mark the typescript puts on every `ř`, which would make the letter `f` + U+030C. That is an observation, not a change: one glyph on a 1962 mimeograph is not enough evidence to move a published letter for the third time (it was U+0302 before June 2026), and the maintainer has ruled that it stands until there is more. Recorded here so the next reader starts from the evidence rather than repeating the reading.

### The PHON tier

`PHON` is regenerated by `add_phonology.py`: the `original` tier through [`Orthographies/Montgomery/Amis.tsv`](../../Orthographies/Montgomery/Amis.tsv), the `standard` tier through Ortho113 (POL-003). It comes out clean — **788 elements, zero `*` uncertainty markers**, and the original and standard PHON of every element now agree, which is what a sound-preserving transliteration should produce.

That last point is new. Until this rebuild, `Orthographies/Montgomery/Amis.tsv` gave the letter `l` the IPA value **`d`** — the letter it maps to in Ortho113, not that letter's sound. Ortho113's `d` is /ɬ~ɮ/, so the same word came out /dafak/ from the original tier and /ɬafak/ from the standard: one word, two pronunciations, differing in 50 of 394 elements. Akiw's own example gives the answer — `tamlaw` → `tamdaw` "people", which is pronounced /tamɬaw/, so Montgomery's `l` writes /ɬ~ɮ/. The profile now says `[ɬ|ɮ]`, the two tiers agree, and `validate_conversion_table.py` resolves all five rows.

The published PHON also predated POL-013: all 482 of its variant notations were the retired bare `~` form (`o~u`), which is the whole of GitHub issue #103's PHON complaint. They are now `[o|u]`, and segmentation hyphens are stripped as POL-003 requires. Of 788 elements, 568 change and none is deleted.

## Source notation preserved in the original tier

- **`( )` marks the article's own commentary** in a gloss or translation — `is (existing)`, `you (pl)`, `eleven (?) o'clock`. These are the article's, they read naturally, and they are kept inline (POL-024). They are the ten SOFT `V122 parens_slashes_anywhere` findings.
- **`/` separated two English equivalents of one word** in the article's gloss line — `good/holy`, `noon/lunch`, `trip/walk`, `whole/all`, `and/with`. The Amis word does not vary, only its English rendering, so these are **not** POL-027 alternations and do not become separate sentences. Each is published as a primary `TRANSL` plus a `TRANSL[@ver="alt"]` on the same `W` — POL-025's mechanism one tier down (maintainer ruling, 2026-09-07). The five are listed with their page and example number in [`CodeAndDocs/gloss_alternations.json`](CodeAndDocs/gloss_alternations.json). **No published TRANSL keeps a slash.**
- **Hyphens mark morpheme boundaries** and are kept exactly as the article prints them on the word tier. Sentence-level `standard` FORMs have them removed, so that tier reads as running text (C012); the sentence-level `original` FORMs keep them.

## Corrections against the source

Recorded in [`CodeAndDocs/source_discrepancies.md`](CodeAndDocs/source_discrepancies.md). There is one: the article prints `mi-salrama` in Silo example 4, and the sentence-level FORM had been hand-corrected to `mi-salama` in 2026 while the word-level FORM kept `mi-salrama`. The printed spelling is restored at both levels (POL-001).

## Reproducing the XML

```bash
./CodeAndDocs/generate_xml.sh
```

The four content pages of `Original.pdf` are image-only scans with no text layer, so there is no OCR or scrape stage to re-run. The texts were typed into XML by hand, and [`CodeAndDocs/pre_correction_snapshot/XML/`](CodeAndDocs/pre_correction_snapshot/XML/) — the **original tier only** — is this corpus's source of record (POL-035). `generate_xml.sh` rebuilds `XML/` from it in three steps:

1. `CodeAndDocs/generate_xml.py` — snapshot → `XML/`, splitting the five slashed word glosses per `gloss_alternations.json`.
2. `QC/cleaning/clean_xml.py` — shared original-tier canonicalization.
3. `QC/utilities/standardize.py --tsv_path Orthographies/ConversionTables/Amis_Montgomery_113.tsv --segmented-without-m-tier` — rebuilds the `standard` tier from the original (POL-002).
4. `QC/utilities/add_phonology.py --orthography Montgomery` — rebuilds both `PHON` tiers (POL-003).

The run is idempotent: `XML/` is rebuilt from the snapshot every time, so a re-run over a clean checkout leaves `git status` empty. Nothing outside this checkout is required (POL-048).

All four shared pipeline steps run, so there is no step-order deviation to declare. Two smaller ones:

- **`apply_manual_edits.py` is not run** — the corpus has no `manual_edits.xml`. Hand corrections belong in the snapshot, which is the source of record, and are recorded in `source_discrepancies.md`.
- **`standardize.py` is passed `--segmented-without-m-tier`.** This corpus prints morpheme hyphens but publishes no `M` tier, and C012's hyphen handling is otherwise gated on the presence of one. The flag is opt-in and off by default: an S-level hyphen is not always segmentation, so whether a corpus's hyphens are is a per-corpus judgement.

Validators are not run by the build (POL-047, "build only"). Against this XML they report **0 HARD** findings; the SOFT findings are the ones explained above.

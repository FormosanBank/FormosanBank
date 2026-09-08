# Wakelin Yami texts (1958)

## Rights

**License:** CC BY-NC-ND 4.0
**Rights source:** Summer Institute of Linguistics / University of North Dakota (publisher), 2026-08-23; evidence: ask maintainer

> Indosan, S., Wakelin, G., Dararyaw, S., and Kalaku, S. (1958). Yami texts. Work Papers of the Summer Institute of Linguistics, University of North Dakota Session: Vol. 2, Article 7. 10.31356/silwp.vol02.07

The individual authors cannot be located. The publisher released the article as **CC-BY-ND**, and FormosanBank has **interpreted that licence liberally** in order to publish the texts with their glosses and translations; publication rights were confirmed by the maintainer on 2026-08-23. The value recorded in `TEXT/@copyright` is `CC BY-NC-ND 4.0`, the `rights_vocabulary.csv` spelling (POL-042; an unversioned licence is 4.0). If you are a copyright owner, please reach out to us.

This corpus is also subject to the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

## Contents

Six Yami (`xml:lang="tao"`, `dialect="Yami"`) narrative texts, collected on Orchid Island between 1955 and 1957 and published in the 1958 SIL Work Papers article reproduced at [`CodeAndDocs/Original.pdf`](CodeAndDocs/Original.pdf). Each sentence carries an English free translation; the texts are fully segmented into words and morphemes, with English glosses on both tiers. There is no audio.

> **This corpus now has a `standard` tier and a `PHON` tier, and both are new.**
> Until September 2026 it published the `original` tier alone, because the 1958
> article's writing system had never been identified. It has since been worked
> out — see [Orthography](#orthography) — and the corpus now carries the
> article's text, that text transliterated into Ortho113, and IPA for both.
> Two things to know before relying on the derived tiers: the letter `ř` is a
> phoneme we cannot resolve, so it is carried through unconverted and stars
> in 56 `PHON` values (41 original, 15 standard); and Ortho113 does not write a word-final glottal
> stop, so the `standard` tier drops a distinction the `original` tier keeps.
> The `original` tier remains the authoritative record of what the article
> prints.

| File | Text in the article | Informant | Sentences | Words | Morphemes |
|---|---|---|---|---|---|
| `XML/Yami/Kangkang.xml` | A. *Ji Kangkang* (The Rooster) | Samen Indosan, April 1955 | 44 | 219 | 249 |
| `XML/Yami/Kwaway.xml` | B. *Kwaway* (The Spirit) | Sinan Dararyaw, May 1957 | 64 | 278 | 348 |
| `XML/Yami/Kalaku1.xml` | C. | Saman Kalaku, 6 September 1956 | 22 | 97 | 131 |
| `XML/Yami/Kalaku2.xml` | D. | Samen Kalaku, 6 September 1956 | 14 | 76 | 114 |
| `XML/Yami/Kalaku3.xml` | E. | Saman Kalaku, 13 September 1956 | 11 | 56 | 92 |
| `XML/Yami/Sunagu.xml` | F. | Saman Sunagu, January 1957 | 24 | 161 | 189 |

Sentence counts exceed the article's printed sentence numbers because seven printed alternations are published as separate sentences — see [Alternations](#alternations-the-sources-slash-notation) below.

Text F was given by Saman Sunagu, not by Saman Kalaku. It was published as `Sunagu` until 2026-09-07, when the file and its `TEXT/@id` were **renamed to `Sunagu`** to name the right speaker. POL-037 makes published identifiers stable, so this is a breaking change announced rather than a cleanup: an external citation of `WakelinTexts/Sunagu` will not resolve. The sentence, word and morpheme ids inside the file are unchanged.

## Orthography

**The article states no writing system, but it has been worked out and is now profiled.** The transcription matched no existing profile: it uses `u` where modern Yami spelling uses `o`, `e` for a vowel the article describes only as fluctuating with `a`, and it has no `'`, `j`, or `z`. The reconstruction is recorded in **[`Orthographies/Wakelin/README.md`](../../Orthographies/Wakelin/README.md)**, with the phoneme table in `Orthographies/Wakelin/Yami.tsv` and the conversion to Ortho113 in `Orthographies/ConversionTables/Yami_Wakelin_113.tsv`.

In short: `u` is the phoneme Ortho113 writes `o` (worth 28 points of attestation on its own, and the article's own errata correct `o`→`u` twice); `ch` is the digraph for /ʨ/; `ǥ` is a barred g and equals modern `h` [ɰ]; `?` is a glottal stop; `r` is [ɻ] and covers both modern `r` and `z`; and a consonant followed by `w` or `y` corresponds to modern `Co`/`Ci`. Under those rules **78.7% of the corpus's morph tokens** reach a form attested in FormosanBank's other Yami data, against a 45.9% baseline. The one letter left unresolved is `ř` — see below.

It does have three symbols worth knowing about before using the data:

- **`?` is a letter, not punctuation.** There are **47 occurrences**, and they sit *inside* single words, word-internally and word-finally, on the word and morpheme tiers as well as the sentence tier — `tau?` 'person', `uvi?` 'potato', `lavi?` 'cry', `kayu?` 'tree', `ina?` 'mother'. They appear in plainly declarative sentences: `amyan su tau? nu-kakwa i-m-angay mang-aep su uvi?` = "A long time ago, there was a person who went to get some potatoes." **It is a glottal stop**, and two independent sources say so. The Ortho113 specification (pp. 21–23, §九 雅美) *removed* [ʔ] from the Yami consonant table and moved it to the notes, which state that the letter `’` marks the glottal stop, "a consonant that causes a pause or breaks a syllable", and that the community decided to **keep** it while leaving it out of the tables — so modern Yami has the phoneme and a letter for it. And the article's own errata delete `?` **exactly twice** (A42, A43), both times word-finally before the vowel-initial word `u`, which is the hiatus where a glottal transition is automatic and need not be written; everywhere else they leave it. Of the 21 surviving occurrences, 8 are sentence-final and 10 precede a consonant, so it is not merely a hiatus marker. Do not strip it as punctuation, and do not read a sentence containing it as a question.

  ⚠️ Note for anyone converting this corpus: modern Yami writes `’` medially and initially but **essentially never word-finally** — 8 occurrences in 135,435 tokens of the bank's other Yami data, all apparent typos. Wakelin's `?` is word-final in every word that has it, so a conversion to the common orthography would have to drop it, losing a distinction the original tier records.

- **`ř` is a letter of the transcription**, in twelve words: `kařwan` 'other', `vařit` 'bamboo strips', `pasavuřen-ku`, `pasamuřna`, `mi-kařakařa`, `k-ařima-raw` 'in five days', `a-pneřek-em`, `vařangyam` 'boat', `y-ařwa` 'two', `sipřutan`, `řerchip` 'cave', and `tiřarawa-kamu`. It is one of the corpus's two non-ASCII letters (the other is `ǥ` below), and part of the reason `validate_text` reports SOFT `V116 non_ascii_in_form` findings. The hand-typed XML originally lost the caron and spelled all of these with a plain `r`; the article prints `ř` and the transcription has been corrected to match. (The PDF's text layer renders the letter as `f'`, `fl`, `i'`, `:l'` or `~` depending on the word, which is how the loss went unnoticed.)

- **`ǥ` is a distinct letter from `g`.** The 1958 typescript writes two g's: a plain `g`, and a **g overstruck with a horizontal bar** (backspace-and-hyphen on the mimeograph master). The published XML writes the second as `ǥ` (U+01E5), in **41 FORM elements** across five words — `vaǥay` 'house' (11 tokens), `kalaǥen` 'to hunt for', `anyaǥay`, `laǥet` 'bad', `aǥapen` 'take'. It is a phonemic symbol, not scan noise: the bar falls only on `g`, never on a neighbouring letter; plain-g words (`kangkang`, `m-angay`, `kagling`, `ragaw`) are never barred; and every token of a barred lexeme is barred. The article's own Errata Addenda reproduces the bar in its "for …" fields, so its typists treated it as a character of the text.

  Post-errata it corresponds exactly to modern Yami `h` [ɰ]: `vaǥay` ~ *vahay* 'house', `aǥapen` ~ *ahapen* 'take', `laǥet` ~ *rahet* 'bad'. Barred g for a voiced velar fricative is standard 1950s SIL practice. The hand-typed XML had flattened it to plain `g`, merging the two phonemes; that has been corrected. Verified at 400 dpi against `CodeAndDocs/Original.pdf`, word by word.

  Ten further attestations were **printed barred but removed by the article's own errata**, so they do not appear in the XML and must not be reintroduced: `maǥay-rana` (A37 → `m-angay-rana`), `chitaǥen`/`ditaǥen` in six places (B4, B12, B16, B18, B19, C6, C15 → `chita-en`), `tunanal-aǥep-an` (B4 → `tunanal-aep-an`), `ya-na-ni-aǥep` (D14 → `ha-na-ni-aep`), and `akak-aǥep-an` / `(mangday su aǥep)` (E8 → `aep`). One morpheme sits at the join of the two rules: `Kwaway/S4W2M2` is barred in print, but errata B4 removes the consonant altogether, so it is published as `aep` — **the errata win over the bar**.

  That the errata delete the segment in some words and rewrite it `ng` in others, while leaving `vaǥay` and `laǥet` standing, is what one expects of a weak velar approximant the team was unsure how to treat. Modern orthography writes `h` throughout.

### `ř`, and what the derived tiers do not claim

`ř` is a third liquid, distinct from `r` and `l`, and it is **not one modern
phoneme**. Of the eleven words containing it, five reach an attested modern form
and they do so three different ways — `ařwa` → `adoa` 'two' and `kařwan` →
`kadoan` 'other' via `d`, `ařima` → `alima` 'five' via `l`, `vařit` → `vazit`
and `sipřutan` → `sipzotan` via `z` — and the other six reach nothing. A
letter-to-letter conversion row would assert a correspondence that does not
exist, so there is none.

Instead those five words are standardized **one word at a time**, by
`CodeAndDocs/r_caron_words.tsv` and the pipeline step that applies it.
Everywhere else `ř` is carried into the standard tier unchanged and maps to `*`
in PHON. That is deliberate: `*` is `add_phonology`'s marker for a letter the
profile cannot map, and it is the honest signal. **15 PHON values contain a
`*`** for this reason, 6 of them in the standard tier.

Two further limits worth stating plainly:

- **The standard tier cannot represent the word-final glottal stop.** `?` is a
  glottal stop (see below), but modern Yami writes `’` medially and initially
  and essentially never word-finally — 8 occurrences in 135,435 tokens of the
  bank's other Yami data, all apparent typos. The conversion therefore deletes
  it, and a distinction the article records is lost in transliteration. This is
  a property of the target orthography, not a judgement about the source.
- **`e` is mapped to /ə/ following Ortho113, and that is the least settled
  letter.** The article says /e/ and /a/ "fluctuate freely", `pengsu`
  corresponds to modern `pongso`, and the `-em` suffix corresponds to modern
  `am` — so some `e` is not a schwa. No conditioning rule tested better than
  leaving it alone.

## Source notation preserved in the original tier

Two notations from the printed article survive in the text and are faithful to it — they are not conversion artifacts:

- **`( )` marks a probable discrepancy** in the data, per the article's own key: `(n)aku`, `ku(a)`, `puken-(en)`. In `Sunagu.xml` sentence S2 the parentheses span several words in the article, so individual word FORMs there carry an unmatched `(` or `)`.
- **`/` separated alternative readings** in the article: `am/namen`, `varit/yaked`, `pipangn-epen/pipangungn-epen/pipangengne-eben`. **No published FORM keeps a slash** — every one is resolved, either into `alternate` siblings or into separate sentences. See [Alternations](#alternations-the-sources-slash-notation) below.

Hyphens mark morpheme boundaries, and are kept exactly as the article prints them, at every level. (In corpora that have a standard tier, sentence-level standard FORMs normally have these hyphens removed so that tier reads as running text. There is no standard tier here, so nothing is de-hyphenated: a sentence FORM reads `mang-anak-u-em`, as the article does.)

## KEY to symbols and abbreviations (from the article)

```
CM     construction marker      pl     plural
NM     name marker              incl   inclusive
unan   unanalyzed               VR     verbalizer
unctn  uncertain                rdpl   reduplication
imp    imperative               intrg  interrogative
EA     added from data of Erin Asai
( )    in data, probable discrepancy
```

The article also notes that the 'narration' suffix `-em`/`-m` occurs throughout without a translation given, and that phonemes /e/ and /a/ fluctuate freely.

## Project structure

- **`XML/`** — the published FormosanBank XML.
- **`CodeAndDocs/`**
  - `Original.pdf` — the 1958 article, the source of every sentence here.
  - `pre_correction_snapshot/Yami/` — the hand-typed XML: this corpus's source of record (see below).
  - `generate_xml.sh` — the one entry point; regenerates `XML/` (POL-047).
  - `generate_xml.py` — step 1, the corpus-local parser.
  - `alternative_decisions.json` — how each printed alternation is published.
  - `source_discrepancies.md` — snapshot-vs-article findings that are still open.
  - `r_caron_words.tsv` — the `ř` words whose modern equivalent is known.
  - `apply_r_caron_words.py` — pipeline step 4; applies that list to the standard tier.
  - `gloss_alignment_review.tsv` — the 52 words whose `M` tier was dropped, for review.
  - [`provenance.json`](CodeAndDocs/provenance.json) — the FormosanBank commit `XML/` was built against (POL-052).

## Provenance and the pre-correction snapshot

**The article's own errata are applied.** The 1958 publication ends with an "Errata Addenda" (`Original.pdf` p. 22) listing about fifty corrections in `for X read Y` form. The published text is the **corrected** reading throughout — `amyan` not `amian`, `mang-aep` not `mengep`, `puken` not `buken`, `tusya` not `tausya` — because the errata are part of the same publication and represent its authors' final word. Where an erratum and another source signal conflict, the erratum wins: `Kwaway/S4W2M2` is printed with a barred g, but B4 removes the consonant, so it is published `aep`. Deviations from the article are confined to two deliberate corrections, listed under "A correction to the source" below.

These texts were transferred from the printed article to XML **by hand**. There is no scraper and no OCR stage, so the hand-typed XML *is* this corpus's source data: `CodeAndDocs/pre_correction_snapshot/` is its **source of record** (POL-035), and the published `XML/` is derived from it on every run.

Because it is the source and not a build artefact, the snapshot is where a *source* correction belongs — a misread letter, a missed erratum, a mis-segmented word. Such corrections are made in the snapshot, and each one is evidenced against `Original.pdf` in [`CodeAndDocs/source_discrepancies.md`](CodeAndDocs/source_discrepancies.md). Everything *downstream* of the snapshot — the alternation handling below — is done by committed code, never by hand (POL-038). The published `XML/` is never edited directly.

The snapshot carries the `original` tier only. It once also held a `standard` tier written by the `Yami_Wakelin_113.tsv` "conversion table"; that tier was the original text minus its hyphens and asserted nothing, and both it and the table are gone.

The FormosanBank commit the published XML was built against is recorded in [`CodeAndDocs/provenance.json`](CodeAndDocs/provenance.json) (POL-052).

## Alternations: the source's slash notation

The article prints 18 alternations with a slash, plus one with parentheses, — `nipi/niripi`, `varit/yaked`, `akak-aep-an/(mangday su aep)`. These record **the transcriber's uncertainty about what was said**, not alternatives the speaker offered. That distinction matters: POL-027 turns a speaker's alternatives into one sentence per option, and applying it here would manufacture sentences the narrator never produced.

Each alternation is therefore classified by hand in `CodeAndDocs/alternative_decisions.json`, which records the printed string, the decision and the reason for all 19 (POL-039 — the table is data, not code). Two rules:

- **A clear spelling variant** — mostly overlapping letters, and the same gloss — is published as a `FORM[@kindOf="alternate"]` sibling **on the node that varies and on its word**, never on the sentence. A sentence-level alternate for a one-morpheme spelling difference is noise, and where one sentence carries two independent alternations (`Kalaku1/S17`) it is worse than noise: it can only show one of them, which reads as a claim that the other did not vary. The sentence FORM therefore carries the primary reading and the variation sits on the W and M that vary. 11 alternations: `nipi/niripi`, the `nem ~ namen` pronoun (six times), `mi-kalakala/mi-karakara`, the purely hyphenational `mikabak-abay-u/mikabakabayu`, and `pipangn-epen/pipangungn-epen/pipangengne-eben`, which is three-way.
- **Everything else** — different lexemes, different glosses, or a word against a phrase — becomes **separate sentences**. 8 alternations. A reading that replaces a whole word rather than one morpheme inside it inherits no morphemes: `Kalaku1/S6b`'s `namen-em` gets none, because the source's `ngaran` and `amn` are not in it. The first branch keeps the printed sentence number and the rest take `b`, `c`, …: `Kwaway/S48` and `Kwaway/S48b`. POL-037 forbids renumbering an already-published bare id, so there is no `S48a`.

Every call in the table has been reviewed. The two that were once borderline are settled: `Kalaku1/S6` becomes two sentences, `ngaran-amn` and `namen-em`, both glossed `name-we`; and `Kwaway/S2`'s single-vowel `a`/`u` stays a spelling variant, because the alternation is one vowel and not one word.

One alternation is written with parentheses rather than a slash. `Kangkang/S18` prints `kan(u)`, and that optional `u` is an alternation like any other: the sentence FORM keeps the printed `kan(u)` notation and the word carries `kan` with the alternate `kan-u`. It is the one place the article's optional-material parentheses are resolved instead of left as notation.

## A correction to the source

**`Kalaku1/S11`'s last two glosses are printed in the wrong order, and the corpus corrects them.** This is a deliberate departure from the article, not a transcription of it.

The article prints `dy-aru-pa-sira` above `unan-many-still/again-them` and `a-ni-padi/machyura-rana` above `unan-past(unctn)-accompany-completely`. Swapped, the slash divides the *word* rather than one morpheme inside it — and it divides the gloss at the same point, so both halves come out even:

| published sentence | word | gloss | morphemes : gloss units |
| --- | --- | --- | ---: |
| `S11` | `a-ni-padi` | `unan-many-still` | 3 : 3 |
| `S11b` | `machyura-rana` | `again-them` | 2 : 2 |

`dy-aru-pa-sira` is glossed `unan-past(unctn)-accompany-completely` in both.

A second, smaller correction: **`Kwaway/S9`'s gloss `bamboo-strips` is written `bamboo.strips`**.

A third, applied across the corpus: **a gloss for a single morpheme is written with dots, not hyphens.** Under the Leipzig conventions a hyphen marks a morpheme boundary and a period joins the parts of one gloss, so the article's `(one-after-another)` and `long-time-ago` both read as several morphemes where they are one.

This was done in two passes and the second is what makes the morpheme tier usable, so both are listed in full below. **No word's alignment is changed by notation alone** — the build's unit counting was already parenthesis-aware — but where a hyphenated gloss sat on a *single* morpheme the count genuinely disagreed, and the word lost its morpheme tier for a reason that was an artifact of English. Repairing those took the count of words publishing no morphemes from **21 to 6**.

**Pass 1 — inside parentheses (54 glosses).** Every parenthesised multi-word gloss: `(one.after.another)`, `(long.time.ago)`, `(sit.with.legs.straight.out)`, `(1st.person.imp)`, `(next.morning)`, `(dear.little.one)`, `(spend.the.night)`, `(betel.nut.basket)`, and the rest. The 162 parenthesised abbreviation markers that contain no hyphen are untouched (`(unctn)`, `(pl)`, `(dual)`, `(sg)`, `(come)`), as are hyphens outside parentheses, which are real morpheme boundaries: `house-their(dual)` is unchanged and `unan-(one.after.another)-us-completely` keeps its three outer hyphens.

**Pass 2 — outside parentheses, where the gloss belongs to one morpheme.** Every one:

| where | word | was | now |
|---|---|---|---|
| `Sunagu/S1W3` | `kakwa` | `long-time-ago` | `long.time.ago` |
| `Sunagu/S2W3` | `madegdeg` | `early-morning` | `early.morning` |
| `Sunagu/S4W6` | `utwen` | `cold-food` | `cold.food` |
| `Sunagu/S7W4` | `nikumagat` | `ship-wreck` | `ship.wreck` |
| `Sunagu/S15W3` | `kari` | `get-out` | `get.out` |
| `Sunagu/S19W2` | `kari` | `get-out` | `get.out` |
| `Sunagu/S16W4` | `chyaa?` | `it-doesn't-matter` | `it.doesn't.matter` |
| `Kangkang/S41W4` | `dinalulut` | `stick-weapons` | `stick.weapons` |
| `Kangkang/S42W4` | `apwapwasena` | `pick-up-stones` | `pick.up.stones` |
| `Kwaway/S33W8` | `vaunda` | `take-up(unctn)` | `take.up(unctn)` |

Each of those ten is a one-morpheme word, so the word gloss and its morpheme gloss both change. Four more are morpheme glosses whose word gloss was already correct:

| where | morpheme | was | now |
|---|---|---|---|
| `Kangkang/S33W1M1` | `simuskem` | `kill-with-boiling-water` | `kill.with.boiling.water` |
| `Kangkang/S33W1M4` | `muskem` | `killed-with-boiling-water` | `killed.with.boiling.water` |
| `Kangkang/S40W1M2` | `atey` | `stone-wall` | `stone.wall` |
| `Kangkang/S40W4M2` | `manginanawa` | `be-careful` | `be.careful` |

Two words needed the gloss put back together as well as dotted, because the transcription had split a single-morpheme gloss across the root and the `-em` narration suffix:

| where | word | was | now |
|---|---|---|---|
| `Kalaku1/S1W4` | `ilaud-em` | word `foreign-country`; `ilaud` 'foreign', `em` 'country' | word `foreign.country`; `ilaud` 'foreign.country', `em` unglossed (then `PAR`) |
| `Kangkang/S35W5` | `chinwat-em` | word `boiling-water`; `chinwat` 'boiling', `em` 'water' | word `boiling.water`; `chinwat` 'boiling.water', `em` unglossed (then `PAR`) |

And two word glosses live in `CodeAndDocs/alternative_decisions.json` rather than the snapshot, because they belong to a split sentence's branch. They are now **derived from the branch's own morphemes** instead of being written out by hand, so they cannot drift again:

| where | was | now |
|---|---|---|
| `Kangkang/S33` | `kill-with-boiling-water` | `kill.with.boiling.water` |
| `Kangkang/S33b` | `if(unctn)-not-killed-with-boiling-water` | `if(unctn)-not-killed.with.boiling.water` |

**Six words still publish no morpheme tier**, and all six are correct: `Kangkang/S34`'s three words, where the article gives three gloss units for two printed words so nothing can be aligned; `Kangkang/S39W5` and `S40W5` `ta-ka-mu`, three morphemes against the two-unit gloss `we-incl(EA)` because the source glosses only two of them; and `Sunagu/S2bW5` `d-imurud` glossed `from`, where the gloss has lost 'Imurud'.

Two of the 54 in pass 1 were also genuinely broken, with the parenthesised unit split across two morphemes; those are recorded in [`CodeAndDocs/source_discrepancies.md`](CodeAndDocs/source_discrepancies.md) §E: `Kalaku1/S4W1` (`(next` + `morning)`) and `Kwaway/S43W2` (`imp)unan` stranded on the morpheme `a`).

Both are recorded in [`CodeAndDocs/source_discrepancies.md`](CodeAndDocs/source_discrepancies.md), which also lists the corrections made *to* the hand-typed snapshot where it had departed from the article.

## Glosses: `unan`, and words whose morphemes do not line up

Two rules are applied corpus-wide when the XML is built (maintainer, 2026-09-06):

- **`unan` is not a gloss.** It is the article's "unanalyzed" marker — it records that the transcriber supplied *nothing*. A `TRANSL` whose entire text is `unan` is therefore **not published**, at any level, rather than shipped as though it meant something. Composite glosses that merely contain it (`unan-past(unctn)-accompany-completely`) are untouched: there the `unan` marks one morpheme inside an analysis that does exist.
- **The `-em`/`-m` narration suffix is glossed `PAR`.** The article's own NOTE says this suffix "occurs throughout without a translation given", and the hand transcription duplicated whatever gloss stood on the preceding morpheme onto it (`vanuad`/'wharf' followed by `em`/'wharf'). The build replaces that with `PAR` and appends `-PAR` to the word's gloss. This is the article's note applied to the tier rather than a correction to it, and it is **not** in the snapshot — it happens during processing, so the snapshot stays a record of what was typed. The gloss is not invented: Rau & Dong gloss the modern cognate `am` as 助 'particle' (423×) and 呢 (369×), the rest of FormosanBank's Yami data glosses `am` as `PAR` across 4,679 tokens, and `-em` ~ `am` is exactly the `e` ~ `a` correspondence the article's own "/e/ and /a/ fluctuate freely" note predicts. It applies only to a **word-final** suffix — `m` is a prefix elsewhere (`a-m-angay`) and is left alone. **37 words** are glossed this way, and because the suffix was the reason they carried one morpheme more than their gloss had units, **33 of them keep a morpheme tier they would otherwise have lost.**
- **A word whose morphemes do not line up with its gloss gets no morphemes.** If the number of `M` children disagrees with the number of units in the word's gloss, the word keeps its word-level gloss and its `M` tier is dropped, rather than publishing a mis-aligned analysis. `Kangkang/S33` is the clear case: `simuskem` is one morpheme glossed `kill-with-boiling-water`, and splitting that gloss across morphemes would invent an analysis the article never gave. A word left with no gloss at all by the first rule likewise keeps no `M`.

Gloss units are counted on hyphens *outside* parentheses, so `unan-(one-after-another)-us-completely` is four units and not six; and a gloss that carries the source's own slash alternation across the whole word (`unan-not-I-you(pl)/unan-curse-I-you(pl)`, `Kwaway/S25`) counts as aligned if either side matches. A word is also treated as unreliably segmented when a **morpheme gloss carries half a parenthesis** — the transcription split a parenthesised multi-word unit across two morphemes, writing `(next-morning)` as `(next` + `morning)` — since half a gloss is not a gloss.

**5 words lose their `M` tier this way** — down from 54 before the narration suffix was glossed, and from 21 before the dot convention reached unparenthesised glosses — and every one is listed in [`CodeAndDocs/gloss_alignment_review.tsv`](CodeAndDocs/gloss_alignment_review.tsv), regenerated on every build. What remains is listed word by word under "A correction to the source" above; all five are genuine, not artifacts.

Both rules make `validate_glosses` louder, on purpose: `V064 every_M_has_TRANSL` and `V065 every_W_has_TRANSL` now fire as SOFT findings wherever the article gave no gloss. That is the honest state of the data — the alternative is to publish `unan` as though it were a translation.

## Processing pipeline

The whole pipeline is one script (POL-047):

```bash
./CodeAndDocs/generate_xml.sh [FORMOSANBANK_ROOT]
```

It rebuilds `XML/` from the snapshot using the QC scripts of the FormosanBank checkout the corpus lives in (pass a path, or set `FORMOSANBANK_ROOT`, to use another checkout; set `PYTHON` to override the interpreter). Nothing outside this checkout is required (POL-048). It is idempotent: a re-run over a clean checkout leaves `git status` empty.

1. **Generate the original tier** — `CodeAndDocs/generate_xml.py`. Reads the snapshot, applies `alternative_decisions.json` and the gloss rules, writes `XML/`. This is the corpus-local parsing step POL-046 exempts from "shared tools first".
2. **Clean** — `QC/cleaning/clean_xml.py`. Unicode NFC, entity decoding, typographic look-alikes. The hand-typed text is near-ASCII (only `ř` and `ǥ`), so this currently changes nothing; it is the guarantee that it stays that way.
3. **Standardize** — `QC/utilities/standardize.py --tsv_path Orthographies/ConversionTables/Yami_Wakelin_113.tsv --segmented-without-m-tier`. Builds the `standard` tier. The `--segmented-without-m-tier` opt-in is needed because C012 uses the presence of an `M` tier as its proxy for "this sentence is segmented", and some sentences here print segmentation hyphens while publishing no morphemes — `Kangkang/S34` by ruling, and words whose gloss does not align. Without it those sentences keep a segmentation hyphen in the S-level standard FORM.
4. **Apply the `ř` word list** — `CodeAndDocs/apply_r_caron_words.py`. Standardizes the five `ř` words whose modern equivalent is known, one word at a time.

   ⚠️ **This step edits the `standard` tier outside `standardize.py`**, which POL-002 otherwise reserves to that tool. It does so on a maintainer ruling of 2026-09-07, taken with the cost understood, because `ř` is not a single correspondence and cannot be a conversion-table row. The cost is concrete and worth stating: **a standalone `standardize.py` run over this corpus silently reverts these five words**, since it regenerates the standard tier from the original. Anyone re-standardizing WakelinTexts must re-run this step — which is why it lives inside `generate_xml.sh` rather than being something a person is expected to remember. The step is strict: every row must match, and a row that matches nothing fails the build.
5. **Add phonology** — `QC/utilities/add_phonology.py --orthography Wakelin`. Generates PHON for both tiers: the `Orthographies/Wakelin/Yami.tsv` profile supplies the **original** tier's IPA, and `Orthographies/Ortho113/Yami.tsv` — selected from `standards.csv`, which maps Yami to Ortho113 — supplies the **standard** tier's.

Validators do not run inside the build (POL-047, "build only"); run them from `QC/` separately. Any `*_warnings.csv` a run leaves behind is a per-run report (POL-033): read it, then delete it. This corpus currently produces none.

## Known caveats

- **Three source discrepancies are still open**, listed with evidence in [`CodeAndDocs/source_discrepancies.md`](CodeAndDocs/source_discrepancies.md). Each is an erratum applied to some tiers of a sentence but not others: `Kangkang/S39` reads `ana-na-m` where errata A39 prints `ama-na-m`; `Kalaku2/S8W1` still reads `ap-en-mu-rana` under a sentence that reads `aep-en-mu-rana`; `Kwaway/S4W2M2` still reads `agep` inside a word that reads `tunanal-aep-an`. The other findings from that audit have been ruled on and are fixed.
- **`Kangkang/S34` publishes no word or morpheme glosses.** The article gives three gloss units for two printed words, so nothing can be aligned; only the sentence-level free translation is published.
- **28 `V121` findings are HARD and are accepted, not defects** — 14 on the original tier and, since September 2026, the same 14 again on the standard tier, which inherits the notation. They are parentheses inside word and morpheme FORMs, in eight words: `(n)aku-yakuyab-yab`, `puken-(en)`, `manuyung-(e)`, `(n)u-kipung`, `(u)m-lavi`, `chi-ka-(y)bubu`, `puken-ku(a)` and `sira(unctn)`. `V121` assumes a parenthesis marks **optional material**, which POL-026 would expand into two sentences. Here it does not: the article's own key defines `( )` as *"in data, probable discrepancy"* — an **uncertainty marker on the transcription**, not an optional word. Expanding it would manufacture readings the transcriber never proposed, so the notation stands and the findings are left standing with it. (`V121` was 28 on the original tier before the 2026-09 rebuild halved it. `Kangkang/S18`'s `kan(u)` is the one parenthesis in the corpus that really is an alternation, and it has been resolved as one.)
- Many words carry no morpheme tier. That is the article's own selective analysis plus the two gloss rules above, not a conversion loss: 52 words had a mis-aligned `M` tier removed (listed in [`CodeAndDocs/gloss_alignment_review.tsv`](CodeAndDocs/gloss_alignment_review.tsv)), and every gloss reading only `unan` was dropped because the article uses it to mean "unanalyzed".
- `Kwaway.xml` S36 and S40 are the same sentence. This is a narrative, and the repetition is in the article; both are retained under POL-022.

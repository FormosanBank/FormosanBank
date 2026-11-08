# Wakelin Yami texts (1958)

The Wakelin Texts are six glossed Yami narratives from a 1958 SIL Work Papers
article, typed into XML by hand and published here with the article's own text
(the `original` tier), that text transliterated into Ortho113 (the `standard`
tier), and IPA for both (`PHON`).

## Languages and dialects

Yami only. All six files, under `XML/Yami/`, declare `xml:lang="tao"` and
`dialect="Yami"` on their `<TEXT>` element.

## Source

This corpus contains the 6 glossed Yami texts [found here](CodeAndDocs/Original.pdf) in the article cited under [How to cite](#how-to-cite).

They were collected on Orchid Island between 1955 and 1957. Every sentence has an English free translation, and the texts are segmented into words and morphemes with English glosses on both tiers. There is no audio.

#### Contents

Six Yami (`xml:lang="tao"`, `dialect="Yami"`) narrative texts, collected on Orchid Island between 1955 and 1957 and published in the 1958 SIL Work Papers article reproduced at [`CodeAndDocs/Original.pdf`](CodeAndDocs/Original.pdf). Each sentence carries an English free translation; the texts are fully segmented into words and morphemes, with English glosses on both tiers. There is no audio.

| File | Text in the article | Informant | Sentences | Words | Morphemes |
|---|---|---|---|---|---|
| `XML/Yami/Kangkang.xml` | A. *Ji Kangkang* (The Rooster) | Samen Indosan, April 1955 | 44 | 219 | 249 |
| `XML/Yami/Kwaway.xml` | B. *Kwaway* (The Spirit) | Sinan Dararyaw, May 1957 | 64 | 278 | 348 |
| `XML/Yami/Kalaku1.xml` | C. | Saman Kalaku, 6 September 1956 | 22 | 97 | 131 |
| `XML/Yami/Kalaku2.xml` | D. | Samen Kalaku, 6 September 1956 | 14 | 76 | 114 |
| `XML/Yami/Kalaku3.xml` | E. | Saman Kalaku, 13 September 1956 | 11 | 56 | 92 |
| `XML/Yami/Sunagu.xml` | F. | Saman Sunagu, January 1957 | 24 | 161 | 189 |

Sentence counts exceed the article's printed sentence numbers because seven printed alternations are published as separate sentences — see [Alternations](#alternations-the-sources-slash-notation) below.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/WakelinTexts_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

> Indosan, S., Wakelin, G., Dararyaw, S., and Kalaku, S. (1958). Yami texts. Work Papers of the Summer Institute of Linguistics, University of North Dakota Session: Vol. 2, Article 7. 10.31356/silwp.vol02.07

## License

**License:** CC BY-NC-ND 4.0
**Rights source:** Summer Institute of Linguistics / University of North Dakota (publisher), 2026-08-23; evidence: ask maintainer

The individual authors cannot be located. The publisher released the article as **CC-BY-ND**, and FormosanBank has **interpreted that licence liberally** in order to publish the texts with their glosses and translations; publication rights were confirmed by the maintainer on 2026-08-23. The value recorded in `TEXT/@copyright` is `CC BY-NC-ND 4.0`, the `rights_vocabulary.csv` spelling (POL-042; an unversioned licence is 4.0). If you are a copyright owner, please reach out to us.

In short: the individual authors could not be located, and publication rights were confirmed by the FormosanBank maintainer on 23 August 2026.

This corpus is also subject to the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

## Notes and caveats

> **This corpus now has a `standard` tier and a `PHON` tier, and both are new.**
> Until September 2026 it published the `original` tier alone, because the 1958
> article's writing system had never been identified. It has since been worked
> out — see [Orthography](#orthography) — and the corpus now carries the
> article's text, that text transliterated into Ortho113, and IPA for both.
> Two things to know before relying on the derived tiers: the letter `ř` is a
> phoneme we cannot resolve, so it is carried through unconverted and stars
> in 51 `PHON` values (36 original, 15 standard); and Ortho113 does not write a word-final glottal
> stop, so the `standard` tier drops a distinction the `original` tier keeps.
> The `original` tier remains the authoritative record of what the article
> prints.

#### In brief

**This corpus now has a `standard` tier and a `PHON` tier, and both are new.** Until September 2026 it published the `original` tier alone, because the 1958 article's writing system had never been identified. It has since been reconstructed — from the text itself, from the article's own key and errata, and by testing candidate readings against FormosanBank's other Yami data — and the corpus now carries the article's text, that text transliterated into Ortho113, and IPA for both. The reasoning is written up in full at [`Orthographies/Wakelin/README.md`](../../Orthographies/Wakelin/README.md).

Under the resulting tables, **78.7% of the corpus's morph tokens** reach a form attested in the bank's other Yami data, against a 45.9% baseline. Two limits are worth knowing before relying on the derived tiers. The letter **`ř`** is a third liquid that is not a single modern phoneme — five of the eleven words containing it resolve, and to three different letters — so it is carried through unconverted except in those five words, and shows as `*` in 51 `PHON` values (36 on the original tier, 15 on the standard). (Three further original-tier `PHON` values carry a `*` for a different reason: the `h` of `ha-na-ni-aep`, `Kalaku2/S14`, its word `S14W3` and its morpheme `S14W3M1`.) And Ortho113 does not write a **word-final glottal stop**, which the article does, so the standard tier loses that distinction. The `original` tier remains the authoritative record of what the article prints.

* **`?` is a letter, not punctuation — it is a glottal stop.** It occurs 49 times, word-internally and word-finally, on all three tiers — `tau?` 'person', `uvi?` 'potato', `kayu?` 'tree' — and in plainly declarative sentences. Two sources confirm the identification. The official orthography specification *removed* [ʔ] from the Yami consonant table and moved it to the notes, where it states that the letter `’` marks the glottal stop, "a consonant that causes a pause or breaks a syllable", kept by community decision but left out of the tables. And the article's own errata delete `?` exactly twice, both times before a vowel-initial word — the hiatus where a glottal is automatic — and leave it everywhere else. Do not strip it as punctuation, and do not read a sentence containing it as a question. Note that modern Yami writes the glottal letter medially and initially but essentially never word-finally, which is where all of Wakelin's occurrences are.
* **Sentences keep the article's parentheses; words, morphemes and the standard tier do not.** The article's key defines `( )` as "in data, probable discrepancy": the transcriber was unsure of the bracketed letters, as in `(n)aku`, `puken-(en)`, `(u)m-lavi`. Since nothing else records these words, each sentence in the original tier shows exactly what the article prints, and its words, its morphemes and the standard tier read the fuller form with the brackets removed (`puken-en`). They are not treated as optional material: no reading is chosen, no variant is made, and no sentence is split. Eight sentences carry them.
* **Hyphens mark morpheme boundaries** and are kept exactly as printed, at every level of the original tier.
* **`ǥ` is a distinct letter from `g`.** The typescript writes two g's — a plain one, and a g overstruck with a horizontal bar — and the published XML writes the second as `ǥ` (U+01E5), in five words: `vaǥay` 'house', `kalaǥen`, `anyaǥay`, `laǥet` 'bad', `aǥapen` 'take'. It is phonemic, not scan noise: the bar falls only on `g`, plain-g words like `kangkang` and `ragaw` are never barred, and every token of a barred word is barred. Post-errata it corresponds exactly to modern Yami `h` [ɰ] — `vaǥay` ~ *vahay*, `aǥapen` ~ *ahapen*, `laǥet` ~ *rahet*. The hand-typed XML had flattened it to plain `g`, merging two phonemes; that has been corrected, verified word by word at 400 dpi.
* **`ř` is also a letter of the transcription**, in twelve words (`kařwan`, `vařit`, `k-ařima-raw`, `vařangyam`, `řerchip`, …). It too had been flattened, to plain `r`.
* **The article's own errata are applied.** The publication ends with an "Errata Addenda" of about fifty `for X read Y` corrections, and the published text is the corrected reading throughout. Where an erratum conflicts with another signal from the page, the erratum wins.
* An earlier release shipped a `standard` tier produced by `Yami_Wakelin_113.tsv`, a "conversion table" whose only rule deleted hyphens and which mapped no letters at all. That tier asserted nothing; both it and the table have been removed.

#### Known caveats

- **The three source discrepancies once listed as open are fixed in the published XML**, although [`CodeAndDocs/source_discrepancies.md`](CodeAndDocs/source_discrepancies.md) still lists them as open. Each was an erratum applied to some tiers of a sentence but not others, and each now reads the errata's text on every tier: `Kangkang/S39` reads `ama-na-m` (errata A39), `Kalaku2/S8W1` reads `aep-en-mu-rana` like its sentence, and `Kwaway/S4W2M2` reads `aep` inside a word that reads `tunanal-aep-an`. The other findings from that audit have been ruled on and are fixed.
- **`Kangkang/S34` publishes no word or morpheme glosses.** The article gives three gloss units for two printed words, so nothing can be aligned; only the sentence-level free translation is published.
- **The original tier's sentence FORMs keep the article's parentheses; nothing else does.** The key defines `( )` as "in data, probable discrepancy": the transcriber was unsure of the bracketed letters, and nothing else records the word, so each sentence shows exactly what the article prints, while its words, its morphemes and the standard tier read the fuller form (maintainer, 2026-10-15). Eight sentences: `Kalaku3/S7` `(n)aku-yakuyab-yab`, `Kalaku3/S10` `puken-(en)`, `Kangkang/S18` `(u)kanen-da`, `Kangkang/S34` `puken-ku(a)`, `Kwaway/S21` `manuyung-(e)`, `Kwaway/S45` `(n)u-kipung`, `Kwaway/S52` `(u)m-lavi`, `Kwaway/S53` `chi-ka-(y)bubu`. They are not variants and are not split. The validator reports them as `V122` (SOFT).
- Many words carry no morpheme tier. That is the article's own selective analysis plus the two gloss rules above, not a conversion loss: 5 words had a mis-aligned `M` tier removed (listed in [`CodeAndDocs/gloss_alignment_review.tsv`](CodeAndDocs/gloss_alignment_review.tsv)), and every gloss reading only `unan` was dropped because the article uses it to mean "unanalyzed".
- `Kwaway.xml` S36 and S40 are the same sentence. This is a narrative, and the repetition is in the article; both are retained under POL-022.

#### A renamed file

Text F was given by Saman Sunagu, not by Saman Kalaku. It was published as `Kalaku4` until 2026-09-07, when the file and its `TEXT/@id` were **renamed to `Sunagu`** to name the right speaker. POL-037 makes published identifiers stable, so this is a breaking change announced rather than a cleanup: an external citation of `WakelinTexts/Kalaku4` will not resolve. The sentence, word and morpheme ids inside the file are unchanged.

**Text F's file and `TEXT/@id` were renamed `Kalaku4` → `Sunagu` on 7 September 2026.** The text was given by Saman Sunagu, not by Saman Kalaku, and the old name said otherwise. Published identifiers are normally stable, so this is a breaking change announced rather than a quiet cleanup: a citation of `WakelinTexts/Kalaku4` will no longer resolve, and should be read as `WakelinTexts/Sunagu`. The sentence, word and morpheme identifiers inside the file are unchanged.

#### Orthography

**The article states no writing system, but it has been worked out and is now profiled.** The transcription matched no existing profile: it uses `u` where modern Yami spelling uses `o`, `e` for a vowel the article describes only as fluctuating with `a`, and it has no `'`, `j`, or `z`. The reconstruction is recorded in **[`Orthographies/Wakelin/README.md`](../../Orthographies/Wakelin/README.md)**, with the phoneme table in `Orthographies/Wakelin/Yami.tsv` and the conversion to Ortho113 in `Orthographies/ConversionTables/Yami_Wakelin_113.tsv`.

The writing system is now profiled. `Orthographies/Wakelin/Yami.tsv` gives the phoneme values for the article's own orthography and drives PHON on the original tier; `Orthographies/ConversionTables/Yami_Wakelin_113.tsv` converts it to Ortho113 to build the standard tier, whose PHON then comes from the Ortho113 Yami profile in the ordinary way. In short: `u` is the phoneme Ortho113 writes `o`, `ch` is /ʨ/, `ǥ` is a barred g equal to modern `h` [ɰ], `?` is a glottal stop, `r` is [ɻ], and a consonant plus `w` or `y` corresponds to modern `Co`/`Ci`. The five `ř` words whose modern equivalent is known are standardized individually by a committed word list; the rest keep `ř` and star in PHON.

**Where those tables come from.** They were not inherited from anywhere — the 1958 article names no writing system, and no previous profile for it existed. They were derived in September 2026 from three kinds of evidence: the article's own key and its Errata Addenda; the internal distribution of the letters (`c` occurs only in `ch`; `o` occurs in four word types against 510 tokens of `u`); and **attestation testing against every other Yami corpus in FormosanBank** — 12,831 word types over 135,435 tokens from RauDong, ePark, ILRDF_Dicts and Presidential_Apologies — preferring candidate readings whose glosses agree on both sides. Each rule's evidence is set out individually in the orthography README, along with what the tables do *not* fix. An earlier note in this file that `Yami_Wakelin_113.tsv` "should not be taken seriously" referred to a **different, long-deleted** table of the same name, whose single rule deleted hyphens and mapped no letters; nothing of it survives here.

The tables were not inherited from anywhere. They were derived in September 2026 from the article's own key and errata, from the internal distribution of its letters, and by testing candidate readings against every other Yami corpus in FormosanBank — 12,831 word types over 135,435 tokens — preferring readings whose glosses agree on both sides. Every rule's evidence, and what the tables do not fix, is set out in the orthography README.

In short: `u` is the phoneme Ortho113 writes `o` (worth 28 points of attestation on its own, and the article's own errata correct `o`→`u` twice); `ch` is the digraph for /ʨ/; `ǥ` is a barred g and equals modern `h` [ɰ]; `?` is a glottal stop; `r` is [ɻ] and covers both modern `r` and `z`; and a consonant followed by `w` or `y` corresponds to modern `Co`/`Ci`. Under those rules **78.7% of the corpus's morph tokens** reach a form attested in FormosanBank's other Yami data, against a 45.9% baseline. The one letter left unresolved is `ř` — see below.

It does have three symbols worth knowing about before using the data:

- **`?` is a letter, not punctuation.** There are **49 occurrences**, and they sit *inside* single words, word-internally and word-finally, on the word and morpheme tiers as well as the sentence tier — `tau?` 'person', `uvi?` 'potato', `lavi?` 'cry', `kayu?` 'tree', `ina?` 'mother'. They appear in plainly declarative sentences: `amyan su tau? nu-kakwa i-m-angay mang-aep su uvi?` = "A long time ago, there was a person who went to get some potatoes." **It is a glottal stop**, and two independent sources say so. The Ortho113 specification (pp. 21–23, §九 雅美) *removed* [ʔ] from the Yami consonant table and moved it to the notes, which state that the letter `’` marks the glottal stop, "a consonant that causes a pause or breaks a syllable", and that the community decided to **keep** it while leaving it out of the tables — so modern Yami has the phoneme and a letter for it. And the article's own errata delete `?` **exactly twice** (A42, A43), both times word-finally before the vowel-initial word `u`, which is the hiatus where a glottal transition is automatic and need not be written; everywhere else they leave it. Of the 21 surviving occurrences, 8 are sentence-final and 10 precede a consonant, so it is not merely a hiatus marker. Do not strip it as punctuation, and do not read a sentence containing it as a question.

  ⚠️ Note for anyone converting this corpus: modern Yami writes `’` medially and initially but **essentially never word-finally** — 8 occurrences in 135,435 tokens of the bank's other Yami data, all apparent typos. Wakelin's `?` is word-final in every word that has it, so a conversion to the common orthography would have to drop it, losing a distinction the original tier records.

- **`ř` is a letter of the transcription**, in twelve words: `kařwan` 'other', `vařit` 'bamboo strips', `pasavuřen-ku`, `pasamuřna`, `mi-kařakařa`, `k-ařima-raw` 'in five days', `a-pneřek-em`, `vařangyam` 'boat', `y-ařwa` 'two', `sipřutan`, `řerchip` 'cave', and `tiřarawa-kamu`. It is one of the corpus's two non-ASCII letters (the other is `ǥ` below), and part of the reason `validate_text` reports SOFT `V116 non_ascii_in_form` findings. The hand-typed XML originally lost the caron and spelled all of these with a plain `r`; the article prints `ř` and the transcription has been corrected to match. (The PDF's text layer renders the letter as `f'`, `fl`, `i'`, `:l'` or `~` depending on the word, which is how the loss went unnoticed.)

- **`ǥ` is a distinct letter from `g`.** The 1958 typescript writes two g's: a plain `g`, and a **g overstruck with a horizontal bar** (backspace-and-hyphen on the mimeograph master). The published XML writes the second as `ǥ` (U+01E5), in **41 FORM elements** across five words — `vaǥay` 'house' (11 tokens), `kalaǥen` 'to hunt for', `anyaǥay`, `laǥet` 'bad', `aǥapen` 'take'. It is a phonemic symbol, not scan noise: the bar falls only on `g`, never on a neighbouring letter; plain-g words (`kangkang`, `m-angay`, `kagling`, `ragaw`) are never barred; and every token of a barred lexeme is barred. The article's own Errata Addenda reproduces the bar in its "for …" fields, so its typists treated it as a character of the text.

  Post-errata it corresponds exactly to modern Yami `h` [ɰ]: `vaǥay` ~ *vahay* 'house', `aǥapen` ~ *ahapen* 'take', `laǥet` ~ *rahet* 'bad'. Barred g for a voiced velar fricative is standard 1950s SIL practice. The hand-typed XML had flattened it to plain `g`, merging the two phonemes; that has been corrected. Verified at 400 dpi against `CodeAndDocs/Original.pdf`, word by word.

  Ten further attestations were **printed barred but removed by the article's own errata**, so they do not appear in the XML and must not be reintroduced: `maǥay-rana` (A37 → `m-angay-rana`), `chitaǥen`/`ditaǥen` in six places (B4, B12, B16, B18, B19, C6, C15 → `chita-en`), `tunanal-aǥep-an` (B4 → `tunanal-aep-an`), `ya-na-ni-aǥep` (D14 → `ha-na-ni-aep`), and `akak-aǥep-an` / `(mangday su aǥep)` (E8 → `aep`). One morpheme sits at the join of the two rules: `Kwaway/S4W2M2` is barred in print, but errata B4 removes the consonant altogether, so it is published as `aep` — **the errata win over the bar**.

  That the errata delete the segment in some words and rewrite it `ng` in others, while leaving `vaǥay` and `laǥet` standing, is what one expects of a weak velar approximant the team was unsure how to treat. Modern orthography writes `h` throughout.

#### `ř`, and what the derived tiers do not claim

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
profile cannot map, and it is the honest signal. **51 PHON values contain a
`*`** for this reason, 15 of them in the standard tier.

Two further limits worth stating plainly:

- **The standard tier cannot represent the word-final glottal stop.** `?` is a glottal stop (see below), but modern Yami writes `’` medially and initially and essentially never word-finally — 8 occurrences in 135,435 tokens of the bank's other Yami data, all apparent typos. The conversion therefore deletes it, and a distinction the article records is lost in transliteration. This is a property of the target orthography, not a judgement about the source.
- **`e` is mapped to /ə/ following Ortho113, and that is the least settled letter.** The article says /e/ and /a/ "fluctuate freely", `pengsu` corresponds to modern `pongso`, and the `-em` suffix corresponds to modern `am` — so some `e` is not a schwa. No conditioning rule tested better than leaving it alone.

#### Source notation preserved in the original tier

Two notations from the printed article survive in the text and are faithful to it — they are not conversion artifacts:

- **`( )` marks a probable discrepancy** in the data, per the article's own key: `(n)aku`, `ku(a)`, `puken-(en)`. **The sentence FORM of the original tier keeps these parentheses; words, morphemes and the standard tier do not**, and keep the bracketed letters (`puken-en`). They are not optional material and not variants: the transcriber was unsure, and there is nothing else to go on (maintainer, 2026-10-15). In `Sunagu.xml` sentence S2 the parentheses instead wrap each side of a slash alternation, `(imurud nu tau)/(tau d-imurud)`; that sentence is split into two (see Alternations below), which carry no parentheses.
- **`/` separated alternative readings** in the article: `am/namen`, `varit/yaked`, `pipangn-epen/pipangungn-epen/pipangengne-eben`. **No published FORM keeps a slash** — every one is resolved, either into `alternate` siblings or into separate sentences. See [Alternations](#alternations-the-sources-slash-notation) below.

Hyphens mark morpheme boundaries, and are kept exactly as the article prints them, at every level of the original tier. (In corpora that have a standard tier, sentence-level standard FORMs normally have these hyphens removed so that tier reads as running text. This corpus's standard tier is treated the same way: the original tier's sentence FORM reads `mang-anak-u-em`, as the article does, and the standard tier's reads `manganakoem` (`Kalaku3/S1`); word and morpheme FORMs keep their hyphens on both tiers.)

#### KEY to symbols and abbreviations (from the article)

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

#### Alternations: the source's slash notation

The article prints 18 alternations with a slash — `nipi/niripi`, `varit/yaked`, `akak-aep-an/(mangday su aep)`. These record **the transcriber's uncertainty about what was said**, not alternatives the speaker offered. That distinction matters: POL-027 turns a speaker's alternatives into one sentence per option, and applying it here would manufacture sentences the narrator never produced.

Each alternation is therefore classified by hand in `CodeAndDocs/alternative_decisions.json`, which records the printed string, the decision and the reason for all 18 (POL-039 — the table is data, not code). Two rules:

- **A clear spelling variant** — mostly overlapping letters, and the same gloss — is published as a `FORM` with `ver="alt"` sibling **on the node that varies and on its word**, never on the sentence. A sentence-level alternate for a one-morpheme spelling difference is noise, and where one sentence carries two independent alternations (`Kalaku1/S17`) it is worse than noise: it can only show one of them, which reads as a claim that the other did not vary. The sentence FORM therefore carries the primary reading and the variation sits on the W and M that vary. 9 alternations: `nipi/niripi`, the `nem ~ namen` pronoun (six times), `mi-kalakala/mi-karakara`, and `pipangn-epen/pipangungn-epen/pipangengne-eben`, which is three-way.
- **One is published in its segmented reading only.** `Kwaway/S51` prints `mikabak-abay-u/mikabakabayu`, and the article glosses the two differently: `unan-waste-unan(unctn)` and `wails`. Ruled 2026-10-15: *"Remove the unglossed version entirely, put in a note with an explanation"*, the unsegmented one. The word publishes `mikabak-abay-u`, and its FORM's `notes` records the other reading.
- **Everything else** — different lexemes, different glosses, or a word against a phrase — becomes **separate sentences**. 8 alternations. A reading that replaces a whole word rather than one morpheme inside it inherits no morphemes: `Kalaku1/S6b`'s `namen-em` gets none, because the source's `ngaran` and `amn` are not in it. The first branch keeps the printed sentence number and the rest take `b`, `c`, …: `Kwaway/S48` and `Kwaway/S48b`. POL-037 forbids renumbering an already-published bare id, so there is no `S48a`.

Every call in the table has been reviewed. The two that were once borderline are settled: `Kalaku1/S6` becomes two sentences, `ngaran-amn` and `namen-em`, both glossed `name-we`; and `Kwaway/S2`'s single-vowel `a`/`u` stays a spelling variant, because the alternation is one vowel and not one word.

The article prints 18 alternations with a slash — `nipi/niripi`, `varit/yaked`, `akak-aep-an/(mangday su aep)`. These record **the transcriber's uncertainty**, not alternatives the speaker offered, so they are not automatically split into one sentence per option. Each is classified by hand in `CodeAndDocs/alternative_decisions.json`: a clear spelling variant (overlapping letters, same gloss) becomes a `ver="alt"` variant FORM sibling **on the node that varies and on its word**, never on the sentence; anything else — different lexemes, different glosses, a word against a phrase — becomes separate sentences, the first keeping the printed sentence number and the rest taking `b`, `c`, …. A reading that replaces a whole word rather than one morpheme inside it inherits no morphemes. **No published FORM keeps a slash.**

`Kangkang/S18` prints `kan(u)kanen-da`, with the `(u)` set against the `k` of `kanen-da`. The snapshot typed it as `kan(u) kanen-da` and the build used to publish `kan` with an alternate `kan-u`. Ruled 2026-10-15: *"These are not alternations, and the u appears to be attached to kanen anyway."* So `print_corrections.json` moves the `(u)` onto the next word, and it is handled like the article's other parentheses: the sentence reads `kan (u)kanen-da`, the word `ukanen-da`, and the standard tier `kan okanenda` (word `okanen-da`).

It is handled like the article's other brackets and attached to that word: the sentence reads `kan (u)kanen-da`, the word `ukanen-da`, and the standard tier `kan okanenda` (word `okanen-da`). It was formerly published as `kan` with an alternate `kan-u`. `Kwaway/S51` prints `mikabak-abay-u/mikabakabayu`, glossing the two readings differently; only the segmented one is published, with a note recording the other.

#### A correction to the source

**`Kalaku1/S11`'s last two glosses are printed in the wrong order, and the corpus corrects them.** This is a deliberate departure from the article, not a transcription of it.

**`Kalaku1/S11`'s last two glosses are printed in the wrong order, and the corpus corrects them.** This is a deliberate departure from the article rather than a transcription of it, recorded here so it is not mistaken for an error.

The article prints `dy-aru-pa-sira` above `unan-many-still/again-them` and `a-ni-padi/machyura-rana` above `unan-past(unctn)-accompany-completely`. Swapped, the slash divides the *word* rather than one morpheme inside it — and it divides the gloss at the same point, so both halves come out even:

| published sentence | word | gloss | morphemes : gloss units |
| --- | --- | --- | ---: |
| `S11` | `a-ni-padi` | `unan-many-still` | 3 : 3 |
| `S11b` | `machyura-rana` | `again-them` | 2 : 2 |

`dy-aru-pa-sira` is glossed `unan-past(unctn)-accompany-completely` in both. That is: sentence `S11` has `a-ni-padi` glossed `unan-many-still` (3 morphemes, 3 units) and `S11b` has `machyura-rana` glossed `again-them` (2 and 2), with `dy-aru-pa-sira` glossed `unan-past(unctn)-accompany-completely` in both.

A second, smaller correction: **`Kwaway/S9`'s gloss `bamboo-strips` is written `bamboo.strips`**.

A third, applied across the corpus: **a gloss for a single morpheme is written with dots, not hyphens.** Under the Leipzig conventions a hyphen marks a morpheme boundary and a period joins the parts of one gloss, so the article's `(one-after-another)` and `long-time-ago` both read as several morphemes where they are one.

A second, smaller correction: **`Kwaway/S9`'s gloss is written `bamboo.strips`, not `bamboo-strips`.** A third, across the corpus: **a gloss for a single morpheme is written with dots, not hyphens** — `(one.after.another)`, `long.time.ago`, `kill.with.boiling.water`. Under the Leipzig conventions a hyphen marks a morpheme boundary and a period joins the parts of one gloss, so the article's hyphens read as morpheme boundaries that are not there.

This was done in two passes and the second is what makes the morpheme tier usable, so both are listed in full below. **No word's alignment is changed by notation alone** — the build's unit counting was already parenthesis-aware — but where a hyphenated gloss sat on a *single* morpheme the count genuinely disagreed, and the word lost its morpheme tier for a reason that was an artifact of English. Repairing those took the count of words publishing no morphemes from **21 to 6**.

It was done in two passes. The first covered the 54 glosses written inside parentheses; the second covered those outside them, where the gloss belongs to a single morpheme — and that second pass is what makes the morpheme tier usable, because a hyphenated gloss on a one-morpheme word made the counts disagree and cost the word its morphemes. Repairing them took the number of words publishing no morpheme tier from **21 to 5**. The full list of every repaired gloss is in the corpus README, here.

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

Untouched throughout: the 162 parenthesised abbreviation markers with no hyphen (`(unctn)`, `(pl)`, `(dual)`), hyphens outside parentheses that are real morpheme boundaries, and sentence-level free translations, which are not glosses.

**Five words still publish no morpheme tier**, and all five are correct: `Kangkang/S34`'s three words, where the article gives three gloss units for two printed words so nothing can be aligned; and `Kangkang/S39W5` and `S40W5` `ta-ka-mu`, three morphemes against the two-unit gloss `we-incl(EA)` because the source glosses only two of them. (`Sunagu/S2bW5` `d-imurud`, once a sixth, is now glossed `from-Imurud` and keeps its two morphemes.)

The five words that still publish no morpheme tier are all genuine: `Kangkang/S34`'s three words, where the article gives three gloss units for two printed words, and `Kangkang/S39W5` and `S40W5`, where the article glosses two of three morphemes.

A further class of repair sits behind that number. The article's key defines `unan` as "unanalyzed", and wherever its printed gloss line was shorter than a word's segmentation the transcription padded the morpheme tier with `unan` — 31 words. In 28 the padded morpheme is the `-em`/`-m` suffix the article says is untranslated, so it records a real fact. Three were inventions with no basis in the print and are corrected, including `Sunagu/S2W8`, which the article glosses `from Imurud` where the transcription had `from` plus an invented `unan`.

Two of the 54 in pass 1 were also genuinely broken, with the parenthesised unit split across two morphemes; those are recorded in [`CodeAndDocs/source_discrepancies.md`](CodeAndDocs/source_discrepancies.md) §E: `Kalaku1/S4W1` (`(next` + `morning)`) and `Kwaway/S43W2` (`imp)unan` stranded on the morpheme `a`).

Both are recorded in [`CodeAndDocs/source_discrepancies.md`](CodeAndDocs/source_discrepancies.md), which also lists the corrections made *to* the hand-typed snapshot where it had departed from the article.

Both corrections, and the corrections made to the hand-typed snapshot where it had departed from the article, are listed in [`CodeAndDocs/source_discrepancies.md`](CodeAndDocs/source_discrepancies.md).

A checked comparison of the snapshot against the article and its errata is published at [`CodeAndDocs/source_discrepancies.md`](CodeAndDocs/source_discrepancies.md); it still lists three findings as open, but all three are now fixed in the published XML (see Known caveats above). The FormosanBank commit this corpus was built against is recorded in [`CodeAndDocs/provenance.json`](CodeAndDocs/provenance.json).

#### Glosses: `unan`, and words whose morphemes do not line up

Two rules are applied corpus-wide when the XML is built (maintainer, 2026-09-06):

- **`unan` is not a gloss.** It is the article's "unanalyzed" marker — it records that the transcriber supplied *nothing*. A `TRANSL` whose entire text is `unan` is therefore **not published**, at any level, rather than shipped as though it meant something. Composite glosses that merely contain it (`unan-past(unctn)-accompany-completely`) are untouched: there the `unan` marks one morpheme inside an analysis that does exist.
- **The `-em`/`-m` narration suffix is glossed `PAR`.** The article's own NOTE says this suffix "occurs throughout without a translation given", and the hand transcription duplicated whatever gloss stood on the preceding morpheme onto it (`vanuad`/'wharf' followed by `em`/'wharf'). The build replaces that with `PAR` and appends `-PAR` to the word's gloss. This is the article's note applied to the tier rather than a correction to it, and it is **not** in the snapshot — it happens during processing, so the snapshot stays a record of what was typed. The gloss is not invented: Rau & Dong gloss the modern cognate `am` as 助 'particle' (423×) and 呢 (369×), the rest of FormosanBank's Yami data glosses `am` as `PAR` across 4,679 tokens, and `-em` ~ `am` is exactly the `e` ~ `a` correspondence the article's own "/e/ and /a/ fluctuate freely" note predicts. It applies only to a **word-final** suffix — `m` is a prefix elsewhere (`a-m-angay`) and is left alone. **37 words** are glossed this way, and because the suffix was the reason they carried one morpheme more than their gloss had units, **all 37 of them keep a morpheme tier they would otherwise have lost.**
- **A word whose morphemes do not line up with its gloss gets no morphemes.** If the number of `M` children disagrees with the number of units in the word's gloss, the word keeps its word-level gloss and its `M` tier is dropped, rather than publishing a mis-aligned analysis. `Kangkang/S33` is the clear case: `simuskem` is one morpheme glossed `kill-with-boiling-water`, and splitting that gloss across morphemes would invent an analysis the article never gave. A word left with no gloss at all by the first rule likewise keeps no `M`.

Two rules govern the glosses:

* **`unan` is the article's "unanalyzed" marker, not a gloss.** A translation whose entire text is `unan` is not published, at any level — it recorded that the transcriber supplied nothing. Composite glosses that merely contain it, like `unan-past(unctn)-accompany-completely`, keep their `unan`; the `(unctn)` within them moves to the translation's `notes` attribute along with every other occurrence of the marker.
* **The `-em`/`-m` "narration suffix" is glossed `PAR`.** The article's own note says it "occurs throughout without a translation given", and the hand transcription duplicated the preceding morpheme's gloss onto it. The build replaces that with `PAR` — the gloss Rau & Dong and the rest of FormosanBank's Yami data give the modern cognate `am`. It is applied during processing, not written into the source snapshot, and only to a word-final suffix. 37 words are affected, and all 37 of them keep a morpheme tier they would otherwise have lost.
* **A word whose morphemes do not line up with its gloss carries no morphemes.** It keeps its word-level gloss and its `M` tier is dropped, rather than publishing an analysis the article never gave — `simuskem` is one morpheme glossed `kill-with-boiling-water`. 5 words are affected, listed in [`CodeAndDocs/gloss_alignment_review.tsv`](CodeAndDocs/gloss_alignment_review.tsv). The commonest case was once the `-em`/`-m` "narration" suffix, which the article itself says occurs throughout without a translation; since that suffix is glossed `PAR`, none of the five is.

Gloss units are counted on hyphens *outside* parentheses, so `unan-(one-after-another)-us-completely` is four units and not six; and a gloss that carries the source's own slash alternation across the whole word (`unan-not-I-you(pl)/unan-curse-I-you(pl)`, `Kwaway/S25`) counts as aligned if either side matches. A word is also treated as unreliably segmented when a **morpheme gloss carries half a parenthesis** — the transcription split a parenthesised multi-word unit across two morphemes, writing `(next-morning)` as `(next` + `morning)` — since half a gloss is not a gloss.

**5 words lose their `M` tier this way** — down from 54 before the narration suffix was glossed, and from 21 before the dot convention reached unparenthesised glosses — and every one is listed in [`CodeAndDocs/gloss_alignment_review.tsv`](CodeAndDocs/gloss_alignment_review.tsv), regenerated on every build. What remains is listed word by word under "A correction to the source" above; all five are genuine, not artifacts.

Both rules make `validate_glosses` louder, on purpose: `V064 every_M_has_TRANSL` and `V065 every_W_has_TRANSL` now fire as SOFT findings wherever the article gave no gloss. That is the honest state of the data — the alternative is to publish `unan` as though it were a translation.

Both rules mean many words and morphemes carry no gloss at all. That is the honest state of the data: the alternative is to publish `unan` as though it were a translation. `Kangkang/S34` goes furthest: the article gives three gloss units for two printed words, so that sentence publishes no word or morpheme glosses at all and only its free translation stands.

## Reproduction and processing

### How to reproduce

#### Processing pipeline

The whole pipeline is one script (POL-047):

```bash
./CodeAndDocs/generate_xml.sh [FORMOSANBANK_ROOT]
```

From the repository root, the same command is `bash Corpora/WakelinTexts/CodeAndDocs/generate_xml.sh`.

It rebuilds `XML/` from the snapshot using the QC scripts of the FormosanBank checkout the corpus lives in (pass a path, or set `FORMOSANBANK_ROOT`, to use another checkout; set `PYTHON` to override the interpreter). Nothing outside this checkout is required (POL-048). It is idempotent: a re-run over a clean checkout leaves `git status` empty.

The interpreter defaults to the checkout's `.venv/bin/python`, falling back to `python3` on the `PATH`. The script stops at once if `CodeAndDocs/pre_correction_snapshot/` is missing. It deletes `XML/` and writes it afresh, and it rewrites `CodeAndDocs/gloss_alignment_review.tsv`. There is no separate `validate.sh` for this corpus.

Validators do not run inside the build (POL-047, "build only"); run them from `QC/` separately. Any `*_warnings.csv` a run leaves behind is a per-run report (POL-033): read it, then delete it. This corpus currently produces none.

The FormosanBank commit the published XML was built against is recorded in [`CodeAndDocs/provenance.json`](CodeAndDocs/provenance.json) (POL-052; provenance only, a rebuild always runs the current tools).

**POL-047 deviation:** the build interleaves two corpus-local steps with the shared ones, and one of them sits where POL-047 does not contemplate. The numbering below is this script's own; POL-047's canonical sequence is 1 `generate_xml.py`, 2 `apply_manual_edits.py`, 3 `clean_xml.py`, 4 `standardize.py`, 5 `add_phonology.py`, so POL-047 step 3 is local step 2, POL-047 step 4 is local step 4 (coincidence), and POL-047 step 5 is local step 6.

- **Step 3, `resolve_parentheses.py --tier original`**, runs between clean and standardize, so the uncertainty marker reaches neither tier. **Step 5a, `resolve_parentheses.py --tier standard`**, runs after standardize and removes the article's `( )` from the standard tier. Detail in steps 3 and 5a below.
- **Step 5b, `apply_r_caron_words.py`**, runs *between* POL-047 steps 4 and 5 — before `add_phonology.py`, where POL-047 says a corpus-local corrections script "belongs after step 5". It must run before, because PHON is generated from the standard tier and has to reflect the corrected words. It also edits the standard tier outside `standardize.py`, which POL-002 otherwise reserves to that tool, on the maintainer ruling of 2026-09-07. Detail and accepted cost in step 5b below.
- **POL-047 step 2, `apply_manual_edits.py`, is absent**: the corpus has no `manual_edits.xml`. Hand corrections belong in the snapshot, which is the source of record.

*Superseded 2026-09-10 (POL-050).* `generate_xml.sh`'s header previously declared a different deviation — that POL-047 steps 4 and 5 (`standardize.py`, `add_phonology.py`) were absent because the 1958 orthography had never been identified, so the corpus published only the original tier. True until `282c49e31` (2026-09-08) profiled the orthography and added both tiers; the corpus now publishes 2189 standard FORMs and 4378 PHONs, and that deviation no longer exists.

#### Project structure

- **`XML/`** — the published FormosanBank XML.
- **`CodeAndDocs/`**
  - `Original.pdf` — the 1958 article, the source of every sentence here.
  - `pre_correction_snapshot/Yami/` — the hand-typed XML: this corpus's source of record (see below).
  - `generate_xml.sh` — the one entry point; regenerates `XML/` (POL-047).
  - `generate_xml.py` — step 1, the corpus-local parser.
  - `alternative_decisions.json` — how each printed alternation is published.
  - `source_discrepancies.md` — snapshot-vs-article findings, with evidence (its three "open" items are now fixed in the XML; see Known caveats).
  - `r_caron_words.tsv` — the `ř` words whose modern equivalent is known.
  - `apply_r_caron_words.py` — pipeline step 5b; applies that list to the standard tier.
  - `resolve_parentheses.py` — pipeline steps 3 and 5a; moves the uncertainty marker `(unctn)` to `@notes` (step 3) and removes the article's `( )` from the standard tier (step 5a).
  - `print_corrections.json` — corrections to the hand-typed snapshot where it does not match the printed article (one, `Kangkang/S18`), applied by `generate_xml.py`.
  - `gloss_alignment_review.tsv` — the 5 words whose `M` tier was dropped, for review.
  - [`provenance.json`](CodeAndDocs/provenance.json) — the FormosanBank commit `XML/` was built against (POL-052).

#### Provenance and the pre-correction snapshot

**The article's own errata are applied.** The 1958 publication ends with an "Errata Addenda" (`Original.pdf` p. 22) listing about fifty corrections in `for X read Y` form. The published text is the **corrected** reading throughout — `amyan` not `amian`, `mang-aep` not `mengep`, `puken` not `buken`, `tusya` not `tausya` — because the errata are part of the same publication and represent its authors' final word. Where an erratum and another source signal conflict, the erratum wins: `Kwaway/S4W2M2` is printed with a barred g, but B4 removes the consonant, so it is published `aep`. Deviations from the article are confined to two deliberate corrections, listed under "A correction to the source" below.

These texts were transferred from the printed article to XML **by hand**. There is no scraper and no OCR stage, so the hand-typed XML *is* this corpus's source data: `CodeAndDocs/pre_correction_snapshot/` is its **source of record** (POL-035), and the published `XML/` is derived from it on every run.

Because it is the source and not a build artefact, the snapshot is where a *source* correction belongs — a misread letter, a missed erratum, a mis-segmented word. Such corrections are made in the snapshot, and each one is evidenced against `Original.pdf` in [`CodeAndDocs/source_discrepancies.md`](CodeAndDocs/source_discrepancies.md). Everything *downstream* of the snapshot — the alternation handling below — is done by committed code, never by hand (POL-038). The published `XML/` is never edited directly.

The snapshot carries the `original` tier only. It once also held a `standard` tier written by the `Yami_Wakelin_113.tsv` "conversion table"; that tier was the original text minus its hyphens and asserted nothing, and both it and the table are gone.

The texts were transferred from the printed article to XML **by hand**, so the hand-typed XML is the corpus's source of record and is preserved in `CodeAndDocs/pre_correction_snapshot/`.

### What each step does

The published XML is rebuilt from the snapshot by `CodeAndDocs/generate_xml.sh`, in seven steps: the corpus-local parser, the shared cleaner, parenthesis resolution in the original tier, standardization against `Yami_Wakelin_113.tsv`, parenthesis removal in the standard tier, the `ř` word list, and phonology for both tiers.

Two of those are corpus-local additions to the canonical POL-047 order, and the second sits where POL-047 does not contemplate: the `ř` word list runs **between** POL-047's standardization and phonology steps, because `PHON` is generated from the standard tier and has to reflect the corrected words. Both are declared on the corpus README's `**POL-047 deviation:**` line. (The first, `resolve_parentheses.py`, runs twice: step 3 and step 5a.)

1. **Generate the original tier** — `CodeAndDocs/generate_xml.py`. Reads the snapshot, applies `alternative_decisions.json` and the gloss rules, writes `XML/`. This is the corpus-local parsing step POL-046 exempts from "shared tools first". In the order the code runs, for each snapshot file: it refuses a snapshot that already carries a `standard` FORM or a `PHON`; applies `print_corrections.json` (each node's expected snapshot text is checked first, and a mismatch stops the build); applies each of the 18 `alternative_decisions.json` entries (9 `variant`, 8 `split`, 1 `keep_primary`; see [Alternations](#alternations-the-sources-slash-notation)); glosses the word-final `-em`/`-m` suffix `PAR`; applies the two gloss rules (drop `TRANSL` reading only `unan`; drop the `M` tier of a word whose morpheme count does not match its gloss units, or whose morpheme gloss carries half a parenthesis); rewrites the snapshot's old `kindOf="alternate"` spelling as `kindOf="original" ver="alt"`; and writes the file. It then fails the build if any FORM still contains a slash, or if a morpheme's text does not occur in its own word, and writes the dropped-`M` list to `CodeAndDocs/gloss_alignment_review.tsv`.
2. **Clean** — `QC/cleaning/clean_xml.py`. Unicode NFC, entity decoding, typographic look-alikes. The hand-typed text is near-ASCII (only `ř` and `ǥ`), so this currently changes nothing; it is the guarantee that it stays that way. It is run with `--corpora_path XML/` only.
3. **The article's uncertainty marks, original tier** — `CodeAndDocs/resolve_parentheses.py --tier original`, run before `standardize.py`.

   **The article's `( )`** — `puken-(en)`, `(u)m-lavi`, `ku(a)` — the key defines as "in data, probable discrepancy". **The original tier's sentence FORM keeps them as printed; word and morpheme FORMs drop them here, keeping the letters (`puken-en`, M `en`); the standard tier loses them in step 5a** (maintainer, 2026-10-15: *"Not variants. The parentheses should be retained in the original tier, removed in the standard tier. ... The reason is that while the author was uncertain, we do not have anything else to go on."* and *"sentence FORM only, not the Ws or Ms."*). No reading is chosen and no variant is made. **8 sentences.**

   **The uncertainty marker `(unctn)`** (also `(onctn)`, `(unan)`) is not text — it is the article's note that a reading is doubtful. Deleting it would lose a judgement the article deliberately recorded, so it moves to `@notes`: on the **word** it qualifies (**1**), and on each **TRANSL** that carries it (**101**). Where the same marker also appeared on the enclosing sentence FORM it is deleted there (**1**) — the annotation belongs to the word, and repeating it up the tree says nothing extra. One gloss whose entire text is the marker (`Kalaku1.xml S2`) is left alone and reported: emptying a TRANSL is invalid, and choosing a replacement gloss is a human's call.

   **POL-050 note.** This supersedes two earlier handlings: until 2026-09-09 the `( )` were resolved in the standard tier only (commit `694bbc903`), and from 2026-09-09 to 2026-10-15 each was resolved in the original tier into a base FORM with the letters plus a `ver="alt"` FORM without them (POL-028 as revised 2026-09-09). POL-028 as amended 2026-10-15 records the exception.

   The article's `( )` notation stays in the sentence FORMs of the original tier and is removed everywhere else, keeping the bracketed letters (maintainer, 2026-10-15).

   Until 15 October 2026 each bracketed word was instead resolved into two readings on the same word, a fuller base FORM and a `ver="alt"` variant without the bracketed letters. That treated the brackets as optional material, which the article's key does not say they are.

   Where `( )` is the **uncertainty marker** `(unctn)` it is annotation rather than text, so it does not belong in a form or a gloss — but deleting it would lose a judgement the article deliberately recorded. It moves to a `notes` attribute instead: on the word it qualifies, and on each of the 101 translations carrying it. Where the same marker was merely repeated on the enclosing sentence it is dropped there, since the annotation belongs to the word. One gloss whose entire text is the marker is left as it stands and flagged for review, because emptying a translation is not valid and choosing a replacement is an editorial decision.

   Before September 2026 the brackets were resolved in the standard tier only, and from September to 15 October 2026 in both tiers, as described above.

   The note text the script writes is `source annotation: (unctn)` (or the marker as found). The script fails the build if a parenthesis survives in any word or morpheme FORM.
4. **Standardize** — `QC/utilities/standardize.py --tsv_path Orthographies/ConversionTables/Yami_Wakelin_113.tsv --segmented-without-m-tier`. Builds the `standard` tier. The `--segmented-without-m-tier` opt-in is needed because C012 uses the presence of an `M` tier as its proxy for "this sentence is segmented", and some sentences here print segmentation hyphens while publishing no morphemes — `Kangkang/S34` by ruling, and words whose gloss does not align. Without it those sentences keep a segmentation hyphen in the S-level standard FORM.
5a. **Remove the article's `( )` from the standard tier** — `CodeAndDocs/resolve_parentheses.py --tier standard`. Keeps the bracketed letters (`puken-(en)` → `puken-en`), so the standard tier reads the fuller form. Strict: the build fails if a parenthesis survives in a standard FORM.
5b. **Apply the `ř` word list** — `CodeAndDocs/apply_r_caron_words.py`. Standardizes the five `ř` words whose modern equivalent is known, one word at a time.

   ⚠️ **This step edits the `standard` tier outside `standardize.py`**, which POL-002 otherwise reserves to that tool. It does so on a maintainer ruling of 2026-09-07, taken with the cost understood, because `ř` is not a single correspondence and cannot be a conversion-table row. The cost is concrete and worth stating: **a standalone `standardize.py` run over this corpus silently reverts these five words**, since it regenerates the standard tier from the original. Anyone re-standardizing WakelinTexts must re-run this step — which is why it lives inside `generate_xml.sh` rather than being something a person is expected to remember. The step is strict: every row must match, and a row that matches nothing fails the build.

   How it finds the words: for each row of `r_caron_words.tsv` (`ařwa` → `adoa`, `kařwan` → `kadoan`, `ařima` → `alima`, `vařit` → `vazit`, `sipřutan` → `sipzotan`) it first computes what `Yami_Wakelin_113.tsv` turns the Wakelin spelling into, then replaces that string, longest first, in every `standard` FORM. A row whose conversion already gives the target spelling also fails the build, as a no-op.
6. **Add phonology** — `QC/utilities/add_phonology.py --orthography Wakelin`. Generates PHON for both tiers: the `Orthographies/Wakelin/Yami.tsv` profile supplies the **original** tier's IPA, and `Orthographies/Ortho113/Yami.tsv` — selected from `standards.csv`, which maps Yami to Ortho113 — supplies the **standard** tier's.

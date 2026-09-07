# Wakelin Yami texts (1958)

## Rights

**License:** CC BY-NC-ND 4.0
**Rights source:** Summer Institute of Linguistics / University of North Dakota (publisher), 2026-08-23; evidence: ask maintainer

> Indosan, S., Wakelin, G., Dararyaw, S., and Kalaku, S. (1958). Yami texts. Work Papers of the Summer Institute of Linguistics, University of North Dakota Session: Vol. 2, Article 7. 10.31356/silwp.vol02.07

The individual authors cannot be located. The publisher released the article as **CC-BY-ND**, and FormosanBank has **interpreted that licence liberally** in order to publish the texts with their glosses and translations; publication rights were confirmed by the maintainer on 2026-08-23. The value recorded in `TEXT/@copyright` is `CC BY-NC-ND 4.0`, the `rights_vocabulary.csv` spelling (POL-042; an unversioned licence is 4.0). If you are a copyright owner, please reach out to us.

This corpus is also subject to the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

## Contents

Six Yami (`xml:lang="tao"`, `dialect="Yami"`) narrative texts, collected on Orchid Island between 1955 and 1957 and published in the 1958 SIL Work Papers article reproduced at [`CodeAndDocs/Original.pdf`](CodeAndDocs/Original.pdf). Each sentence carries an English free translation; the texts are fully segmented into words and morphemes, with English glosses on both tiers. There is no audio.

> **Before you use this corpus: it has an `original` tier and nothing else.**
> Every `<FORM>` in it is `kindOf="original"` — the text as the 1958 article
> prints it. There is **no `standard` tier** and **no `PHON` (IPA) tier**,
> at the sentence, word or morpheme level. That is deliberate: the article's
> orthography has never been identified and we have no trustworthy way to
> convert it (see [Orthography](#orthography) below). Tooling and analyses
> that expect a standard tier will find none here; read the original tier
> instead, and treat its spelling as the article's own, not as
> FormosanBank's common orthography.

| File | Text in the article | Informant | Sentences | Words | Morphemes |
|---|---|---|---|---|---|
| `XML/Yami/Kangkang.xml` | A. *Ji Kangkang* (The Rooster) | Samen Indosan, April 1955 | 44 | 219 | 204 |
| `XML/Yami/Kwaway.xml` | B. *Kwaway* (The Spirit) | Sinan Dararyaw, May 1957 | 64 | 278 | 341 |
| `XML/Yami/Kalaku1.xml` | C. | Saman Kalaku, 6 September 1956 | 22 | 97 | 111 |
| `XML/Yami/Kalaku2.xml` | D. | Samen Kalaku, 6 September 1956 | 14 | 76 | 103 |
| `XML/Yami/Kalaku3.xml` | E. | Saman Kalaku, 13 September 1956 | 11 | 56 | 68 |
| `XML/Yami/Sunagu.xml` | F. | Saman Sunagu, January 1957 | 24 | 161 | 176 |

Sentence counts exceed the article's printed sentence numbers because seven printed alternations are published as separate sentences — see [Alternations](#alternations-the-sources-slash-notation) below.

Text F was given by Saman Sunagu, not by Saman Kalaku. It was published as `Sunagu` until 2026-09-07, when the file and its `TEXT/@id` were **renamed to `Sunagu`** to name the right speaker. POL-037 makes published identifiers stable, so this is a breaking change announced rather than a cleanup: an external citation of `WakelinTexts/Sunagu` will not resolve. The sentence, word and morpheme ids inside the file are unchanged.

## Orthography

**The orthography of these texts has not been identified, and no orthographic conversion is applied to them.** The article gives no statement of its writing system, and the transcription does not match any orthography currently profiled in [`Orthographies/`](../../Orthographies/): it uses `u` where modern Yami spelling uses `o`, `e` for a vowel the article describes only as fluctuating with `a`, and it has no `'`, `j`, or `z`.

It does have three symbols worth knowing about before using the data:

- **`?` is a letter, not punctuation.** There are **47 occurrences**, and they sit *inside* single words, word-internally and word-finally, on the word and morpheme tiers as well as the sentence tier — `tau?` 'person', `uvi?` 'potato', `lavi?` 'cry', `kayu?` 'tree', `ina?` 'mother'. They appear in plainly declarative sentences: `amyan su tau? nu-kakwa i-m-angay mang-aep su uvi?` = "A long time ago, there was a person who went to get some potatoes." On the evidence it writes a consonant that modern Yami spelling leaves unwritten, most plausibly a glottal stop — but **that identification is not confirmed**, and it is the single largest reason the writing system as a whole cannot be pinned down. Do not strip it as punctuation, and do not read a sentence containing it as a question.

- **`ř` is a letter of the transcription**, in twelve words: `kařwan` 'other', `vařit` 'bamboo strips', `pasavuřen-ku`, `pasamuřna`, `mi-kařakařa`, `k-ařima-raw` 'in five days', `a-pneřek-em`, `vařangyam` 'boat', `y-ařwa` 'two', `sipřutan`, `řerchip` 'cave', and `tiřarawa-kamu`. It is one of the corpus's two non-ASCII letters (the other is `ǥ` below), and part of the reason `validate_text` reports SOFT `V116 non_ascii_in_form` findings. The hand-typed XML originally lost the caron and spelled all of these with a plain `r`; the article prints `ř` and the transcription has been corrected to match. (The PDF's text layer renders the letter as `f'`, `fl`, `i'`, `:l'` or `~` depending on the word, which is how the loss went unnoticed.)

- **`ǥ` is a distinct letter from `g`.** The 1958 typescript writes two g's: a plain `g`, and a **g overstruck with a horizontal bar** (backspace-and-hyphen on the mimeograph master). The published XML writes the second as `ǥ` (U+01E5), in **41 FORM elements** across five words — `vaǥay` 'house' (11 tokens), `kalaǥen` 'to hunt for', `anyaǥay`, `laǥet` 'bad', `aǥapen` 'take'. It is a phonemic symbol, not scan noise: the bar falls only on `g`, never on a neighbouring letter; plain-g words (`kangkang`, `m-angay`, `kagling`, `ragaw`) are never barred; and every token of a barred lexeme is barred. The article's own Errata Addenda reproduces the bar in its "for …" fields, so its typists treated it as a character of the text.

  Post-errata it corresponds exactly to modern Yami `h` [ɰ]: `vaǥay` ~ *vahay* 'house', `aǥapen` ~ *ahapen* 'take', `laǥet` ~ *rahet* 'bad'. Barred g for a voiced velar fricative is standard 1950s SIL practice. The hand-typed XML had flattened it to plain `g`, merging the two phonemes; that has been corrected. Verified at 400 dpi against `CodeAndDocs/Original.pdf`, word by word.

  Ten further attestations were **printed barred but removed by the article's own errata**, so they do not appear in the XML and must not be reintroduced: `maǥay-rana` (A37 → `m-angay-rana`), `chitaǥen`/`ditaǥen` in six places (B4, B12, B16, B18, B19, C6, C15 → `chita-en`), `tunanal-aǥep-an` (B4 → `tunanal-aep-an`), `ya-na-ni-aǥep` (D14 → `ha-na-ni-aep`), and `akak-aǥep-an` / `(mangday su aǥep)` (E8 → `aep`). One morpheme sits at the join of the two rules: `Kwaway/S4W2M2` is barred in print, but errata B4 removes the consonant altogether, so it is published as `aep` — **the errata win over the bar**.

  That the errata delete the segment in some words and rewrite it `ng` in others, while leaving `vaǥay` and `laǥet` standing, is what one expects of a weak velar approximant the team was unsure how to treat. Modern orthography writes `h` throughout.

### Why there is no standard tier and no IPA

A `standard` FORM is a claim that a passage has been transliterated into FormosanBank's single common orthography, and a `PHON` is a claim about how it was pronounced. Making either claim requires knowing which letters the source is using and what they stand for. Here we do not, so the corpus makes neither claim: **the published XML carries only the `original` tier.**

The `ǥ` finding narrows the gap without closing it. Two of the transcription's puzzles now have good answers — `ǥ` is modern `h` [ɰ], and `?` is most plausibly a glottal stop — but the second is still unconfirmed, no conversion table exists, and nobody has checked the remaining letters against a profile. A partial mapping is not an orthography, so the tiers stay absent until someone does that work.

Concretely:

- **No orthographic conversion exists for this text.** The only table that ever purported to convert it, `Yami_Wakelin_113.tsv`, had a single rule — delete `-` — and mapped no letters at all; its source profile `Orthographies/Wakelin/Yami.tsv` was never written, so the table could not even be validated. It has been deleted from the repo. Earlier releases of this corpus did ship a standard tier produced by that table; it was the original text with its hyphens removed, and it asserted nothing. It is gone.
- **No phonology can be generated.** This was tested, not assumed. Running `add_phonology` with `Ortho113` — the profile Yami is assigned in [`standards.csv`](../../standards.csv) — yields 4240 IPA values and **zero** `*` uncertainty markers, i.e. it fails silently rather than loudly. It deletes every one of the 47 `?` letters (`tau?` → `tau`), and it invents sound values the article never claimed: `su` → `ʂu` (retroflex), `s-ina-na` → `ɕinana` (alveolo-palatal), `-em` → `-əm` (schwa, for the very vowel the article calls unstable). That is a fabricated pronunciation, so no phonology step is run.

If the orthography is later identified — starting with a confirmation of what `?` writes — a standard tier and a PHON tier can be generated by adding steps to the pipeline below. Until then their absence is the honest state of the data.

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
  - `pre_correction_snapshot/XML/` — the hand-typed XML: this corpus's source of record (see below).
  - `generate_xml.sh` — the one entry point; regenerates `XML/` (POL-047).
  - `generate_xml.py` — step 1, the corpus-local parser.
  - `alternative_decisions.json` — how each printed alternation is published.
  - `source_discrepancies.md` — snapshot-vs-article findings that are still open.
  - `gloss_alignment_review.tsv` — the 52 words whose `M` tier was dropped, for review.
  - [`provenance.json`](CodeAndDocs/provenance.json) — the FormosanBank commit `XML/` was built against (POL-052).

## Provenance and the pre-correction snapshot

**The article's own errata are applied.** The 1958 publication ends with an "Errata Addenda" (`Original.pdf` p. 22) listing about fifty corrections in `for X read Y` form. The published text is the **corrected** reading throughout — `amyan` not `amian`, `mang-aep` not `mengep`, `puken` not `buken`, `tusya` not `tausya` — because the errata are part of the same publication and represent its authors' final word. Where an erratum and another source signal conflict, the erratum wins: `Kwaway/S4W2M2` is printed with a barred g, but B4 removes the consonant, so it is published `aep`. Deviations from the article are confined to two deliberate corrections, listed under "A correction to the source" below.

These texts were transferred from the printed article to XML **by hand**. There is no scraper and no OCR stage, so the hand-typed XML *is* this corpus's source data: `CodeAndDocs/pre_correction_snapshot/XML/` is its **source of record** (POL-035), and the published `XML/` is derived from it on every run.

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

A second, smaller correction: **`Kwaway/S9`'s gloss `bamboo-strips` is written `bamboo.strips`**. Neither `varit` nor its alternate `yaked` is segmented in the text, so the gloss is one two-word unit; a hyphen would read as two morphemes. Leipzig dot notation says what is meant.

Both are recorded in [`CodeAndDocs/source_discrepancies.md`](CodeAndDocs/source_discrepancies.md), which also lists the corrections made *to* the hand-typed snapshot where it had departed from the article.

## Glosses: `unan`, and words whose morphemes do not line up

Two rules are applied corpus-wide when the XML is built (maintainer, 2026-09-06):

- **`unan` is not a gloss.** It is the article's "unanalyzed" marker — it records that the transcriber supplied *nothing*. A `TRANSL` whose entire text is `unan` is therefore **not published**, at any level, rather than shipped as though it meant something. Composite glosses that merely contain it (`unan-past(unctn)-accompany-completely`) are untouched: there the `unan` marks one morpheme inside an analysis that does exist.
- **A word whose morphemes do not line up with its gloss gets no morphemes.** If the number of `M` children disagrees with the number of units in the word's gloss, the word keeps its word-level gloss and its `M` tier is dropped, rather than publishing a mis-aligned analysis. `Kangkang/S33` is the clear case: `simuskem` is one morpheme glossed `kill-with-boiling-water`, and splitting that gloss across morphemes would invent an analysis the article never gave. A word left with no gloss at all by the first rule likewise keeps no `M`.

Gloss units are counted on hyphens *outside* parentheses, so `unan-(one-after-another)-us-completely` is four units and not six; and a gloss that carries the source's own slash alternation across the whole word (`unan-not-I-you(pl)/unan-curse-I-you(pl)`, `Kwaway/S25`) counts as aligned if either side matches.

**54 words lose their `M` tier this way**, and every one is listed in [`CodeAndDocs/gloss_alignment_review.tsv`](CodeAndDocs/gloss_alignment_review.tsv), regenerated on every build. Two patterns dominate: the article's `-em`/`-m` "narration" suffix, which it says outright occurs "throughout without a translation given", and single morphemes whose English gloss is a hyphenated phrase (`kakwa` 'long-time-ago', `utwen` 'cold-food').

Both rules make `validate_glosses` louder, on purpose: `V064 every_M_has_TRANSL` and `V065 every_W_has_TRANSL` now fire as SOFT findings wherever the article gave no gloss. That is the honest state of the data — the alternative is to publish `unan` as though it were a translation.

## Processing pipeline

The whole pipeline is one script (POL-047):

```bash
./CodeAndDocs/generate_xml.sh [FORMOSANBANK_ROOT]
```

It rebuilds `XML/` from the snapshot using the QC scripts of the FormosanBank checkout the corpus lives in (pass a path, or set `FORMOSANBANK_ROOT`, to use another checkout; set `PYTHON` to override the interpreter, which defaults to that checkout's `.venv`). Nothing outside this checkout is required (POL-048). It is idempotent: a re-run over a clean checkout leaves `git status` empty.

1. **Generate the original tier**

   ```bash
   python Corpora/WakelinTexts/CodeAndDocs/generate_xml.py
   ```

   Reads the snapshot, applies `alternative_decisions.json` and the two gloss rules above, and writes `XML/` plus `CodeAndDocs/gloss_alignment_review.tsv`. This is the corpus-local parsing step POL-046 exempts from "shared tools first": turning *this* hand-typed source into the original tier is inherently source-specific. It fails loudly if the snapshot ever acquires a derived tier, and if any published FORM still contains a slash.

2. **Clean the XML**

   ```bash
   python QC/cleaning/clean_xml.py --corpora_path Corpora/WakelinTexts/XML
   ```

   Removes empty elements, normalizes Unicode to NFC, decodes HTML escapes, and canonicalizes typographic look-alikes (curly quotes, dashes, tildes) and null-morpheme glyphs. The hand-typed text is near-ASCII — the only non-ASCII letters are `ř` and `ǥ`, both NFC-stable and untouched by the look-alike table — so this step currently changes nothing; it is the guarantee that it stays that way.

**Steps 4 and 5 of the POL-047 shape — `standardize.py` and `add_phonology.py` — are deliberately absent**, and this is the deviation POL-047 requires a corpus to state. See "Why there is no standard tier and no IPA" above. There is also no `apply_manual_edits.py` step: this corpus has no `manual_edits.xml`, because hand corrections belong in the snapshot, which is its source.

Validators do not run inside the build (POL-047, "build only"); run them from `QC/` separately.

Any `cleaner_warnings.csv` file a run leaves behind is a per-run report: read it, then delete it. Never commit it. This corpus currently produces none.

## Known caveats

- **Three source discrepancies are still open**, listed with evidence in [`CodeAndDocs/source_discrepancies.md`](CodeAndDocs/source_discrepancies.md). Each is an erratum applied to some tiers of a sentence but not others: `Kangkang/S39` reads `ana-na-m` where errata A39 prints `ama-na-m`; `Kalaku2/S8W1` still reads `ap-en-mu-rana` under a sentence that reads `aep-en-mu-rana`; `Kwaway/S4W2M2` still reads `agep` inside a word that reads `tunanal-aep-an`. The other findings from that audit have been ruled on and are fixed.
- **`Kangkang/S34` publishes no word or morpheme glosses.** The article gives three gloss units for two printed words, so nothing can be aligned; only the sentence-level free translation is published.
- **14 `V121` findings are HARD and are accepted, not defects.** They are parentheses inside word and morpheme FORMs, in eight words: `(n)aku-yakuyab-yab`, `puken-(en)`, `manuyung-(e)`, `(n)u-kipung`, `(u)m-lavi`, `chi-ka-(y)bubu`, `puken-ku(a)` and `sira(unctn)`. `V121` assumes a parenthesis marks **optional material**, which POL-026 would expand into two sentences. Here it does not: the article's own key defines `( )` as *"in data, probable discrepancy"* — an **uncertainty marker on the transcription**, not an optional word. Expanding it would manufacture readings the transcriber never proposed, so the notation stands and the findings are left standing with it. (`V121` was 28 before this rebuild. `Kangkang/S18`'s `kan(u)` is the one parenthesis in the corpus that really is an alternation, and it has been resolved as one.)
- Many words carry no morpheme tier. That is the article's own selective analysis plus the two gloss rules above, not a conversion loss: 52 words had a mis-aligned `M` tier removed (listed in [`CodeAndDocs/gloss_alignment_review.tsv`](CodeAndDocs/gloss_alignment_review.tsv)), and every gloss reading only `unan` was dropped because the article uses it to mean "unanalyzed".
- `Kwaway.xml` S36 and S40 are the same sentence. This is a narrative, and the repetition is in the article; both are retained under POL-022.

# The Wakelin Texts

This corpus contains the 6 glossed Yami texts [found here](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/WakelinTexts/CodeAndDocs/Original.pdf) in

> Indosan, S., Wakelin, G., Dararyaw, S., and Kalaku, S. (1958). Yami texts. Work Papers of the Summer Institute of Linguistics, University of North Dakota Session: Vol. 2, Article 7. 10.31356/silwp.vol02.07

They were collected on Orchid Island between 1955 and 1957. Every sentence has an English free translation, and the texts are segmented into words and morphemes with English glosses on both tiers. There is no audio.

**This corpus now has a `standard` tier and a `PHON` tier, and both are new.** Until September 2026 it published the `original` tier alone, because the 1958 article's writing system had never been identified. It has since been reconstructed — from the text itself, from the article's own key and errata, and by testing candidate readings against FormosanBank's other Yami data — and the corpus now carries the article's text, that text transliterated into Ortho113, and IPA for both. The reasoning is written up in full at [`Orthographies/Wakelin/README.md`](https://github.com/FormosanBank/FormosanBank/blob/main/Orthographies/Wakelin/README.md).

Under the resulting tables, **78.7% of the corpus's morph tokens** reach a form attested in the bank's other Yami data, against a 45.9% baseline. Two limits are worth knowing before relying on the derived tiers. The letter **`ř`** is a third liquid that is not a single modern phoneme — five of the eleven words containing it resolve, and to three different letters — so it is carried through unconverted except in those five words, and shows as `*` in 56 `PHON` values (41 on the original tier, 15 on the standard). And Ortho113 does not write a **word-final glottal stop**, which the article does, so the standard tier loses that distinction. The `original` tier remains the authoritative record of what the article prints.

***

<!-- CORPUS STATS START -->
### Corpus Statistics

| | Yami |
| --- | --- |
| Word count | 886 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 886 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 0 |
| Morphologically segmented | 872 |
| Glossed words | 871 |

***

<!-- CORPUS STATS END -->


### Notes

* **`?` is a letter, not punctuation — it is a glottal stop.** It occurs 47 times, word-internally and word-finally, on all three tiers — `tau?` 'person', `uvi?` 'potato', `kayu?` 'tree' — and in plainly declarative sentences. Two sources confirm the identification. The official orthography specification *removed* [ʔ] from the Yami consonant table and moved it to the notes, where it states that the letter `’` marks the glottal stop, "a consonant that causes a pause or breaks a syllable", kept by community decision but left out of the tables. And the article's own errata delete `?` exactly twice, both times before a vowel-initial word — the hiatus where a glottal is automatic — and leave it everywhere else. Do not strip it as punctuation, and do not read a sentence containing it as a question. Note that modern Yami writes the glottal letter medially and initially but essentially never word-finally, which is where all of Wakelin's occurrences are.
* **`( )` marks a probable discrepancy** in the data, per the article's own key: `(n)aku`, `puken-(en)`, `(u)m-lavi`. The article uses it to flag **uncertainty about the transcription itself**, not the optional material a parenthesis usually marks in FormosanBank — so the bracketed letters are never simply dropped, and the word is never expanded into two sentences, which would manufacture readings the transcriber never proposed. Instead the word keeps both readings on the same node: the fuller one, closest to the printed letter sequence, and a variant `ver="alt"` FORM without the bracketed material. Seven words are handled this way, in both tiers. **No published FORM keeps a parenthesis.**
* **Hyphens mark morpheme boundaries** and are kept exactly as printed, at every level.
* **`ǥ` is a distinct letter from `g`.** The typescript writes two g's — a plain one, and a g overstruck with a horizontal bar — and the published XML writes the second as `ǥ` (U+01E5), in five words: `vaǥay` 'house', `kalaǥen`, `anyaǥay`, `laǥet` 'bad', `aǥapen` 'take'. It is phonemic, not scan noise: the bar falls only on `g`, plain-g words like `kangkang` and `ragaw` are never barred, and every token of a barred word is barred. Post-errata it corresponds exactly to modern Yami `h` [ɰ] — `vaǥay` ~ *vahay*, `aǥapen` ~ *ahapen*, `laǥet` ~ *rahet*. The hand-typed XML had flattened it to plain `g`, merging two phonemes; that has been corrected, verified word by word at 400 dpi.
* **`ř` is also a letter of the transcription**, in twelve words (`kařwan`, `vařit`, `k-ařima-raw`, `vařangyam`, `řerchip`, …). It too had been flattened, to plain `r`.
* **The article's own errata are applied.** The publication ends with an "Errata Addenda" of about fifty `for X read Y` corrections, and the published text is the corrected reading throughout. Where an erratum conflicts with another signal from the page, the erratum wins.
* An earlier release shipped a `standard` tier produced by `Yami_Wakelin_113.tsv`, a "conversion table" whose only rule deleted hyphens and which mapped no letters at all. That tier asserted nothing; both it and the table have been removed.

### A renamed file

**Text F's file and `TEXT/@id` were renamed `Kalaku4` → `Sunagu` on 7 September 2026.** The text was given by Saman Sunagu, not by Saman Kalaku, and the old name said otherwise. Published identifiers are normally stable, so this is a breaking change announced rather than a quiet cleanup: a citation of `WakelinTexts/Kalaku4` will no longer resolve, and should be read as `WakelinTexts/Sunagu`. The sentence, word and morpheme identifiers inside the file are unchanged.

### Corpus Processing

The writing system is now profiled. `Orthographies/Wakelin/Yami.tsv` gives the phoneme values for the article's own orthography and drives PHON on the original tier; `Orthographies/ConversionTables/Yami_Wakelin_113.tsv` converts it to Ortho113 to build the standard tier, whose PHON then comes from the Ortho113 Yami profile in the ordinary way. In short: `u` is the phoneme Ortho113 writes `o`, `ch` is /ʨ/, `ǥ` is a barred g equal to modern `h` [ɰ], `?` is a glottal stop, `r` is [ɻ], and a consonant plus `w` or `y` corresponds to modern `Co`/`Ci`. The five `ř` words whose modern equivalent is known are standardized individually by a committed word list; the rest keep `ř` and star in PHON.

The tables were not inherited from anywhere. They were derived in September 2026 from the article's own key and errata, from the internal distribution of its letters, and by testing candidate readings against every other Yami corpus in FormosanBank — 12,831 word types over 135,435 tokens — preferring readings whose glosses agree on both sides. Every rule's evidence, and what the tables do not fix, is set out in the orthography README.

The article's `( )` notation reaches **no** published FORM, in either tier — no orthography has a parenthesis, and POL-028 requires that neither of the notation's two jobs leaves one behind. The resolution happens on the original tier, before standardization, so every derived tier is built from text that already carries none.

Where `( )` marks **optional material** the word is genuinely ambiguous, so it keeps both readings: the base FORM takes the fuller one, closest to the printed letter sequence, and a `ver="alt"` variant FORM of the same tier takes the reading without. `standardize.py` then derives the matching pair in the standard tier, so the word reads both ways in both orthographies — the same mechanism the corpus uses for the source's slash alternations.

Where `( )` is the **uncertainty marker** `(unctn)` it is annotation rather than text, so it does not belong in a form or a gloss — but deleting it would lose a judgement the article deliberately recorded. It moves to a `notes` attribute instead: on the word it qualifies, and on each of the 101 translations carrying it. Where the same marker was merely repeated on the enclosing sentence it is dropped there, since the annotation belongs to the word. One gloss whose entire text is the marker is left as it stands and flagged for review, because emptying a translation is not valid and choosing a replacement is an editorial decision.

Until September 2026 this step ran after standardization and touched the standard tier only, leaving the parentheses in the original tier. That was reversed when POL-028 settled that no published FORM keeps them.

The texts were transferred from the printed article to XML **by hand**, so the hand-typed XML is the corpus's source of record and is preserved in `CodeAndDocs/pre_correction_snapshot/`. The published XML is rebuilt from it by `CodeAndDocs/generate_xml.sh`, which runs a corpus-local parser and then the shared cleaner. There is deliberately no standardization and no phonology step.

The article prints 18 alternations with a slash — `nipi/niripi`, `varit/yaked`, `akak-aep-an/(mangday su aep)`. These record **the transcriber's uncertainty**, not alternatives the speaker offered, so they are not automatically split into one sentence per option. Each is classified by hand in `CodeAndDocs/alternative_decisions.json`: a clear spelling variant (overlapping letters, same gloss) becomes a `ver="alt"` variant FORM sibling **on the node that varies and on its word**, never on the sentence; anything else — different lexemes, different glosses, a word against a phrase — becomes separate sentences, the first keeping the printed sentence number and the rest taking `b`, `c`, …. A reading that replaces a whole word rather than one morpheme inside it inherits no morphemes. **No published FORM keeps a slash.**

Two rules govern the glosses:

* **`unan` is the article's "unanalyzed" marker, not a gloss.** A translation whose entire text is `unan` is not published, at any level — it recorded that the transcriber supplied nothing. Composite glosses that merely contain it, like `unan-past(unctn)-accompany-completely`, keep their `unan`; the `(unctn)` within them moves to the translation's `notes` attribute along with every other occurrence of the marker.
* **The `-em`/`-m` "narration suffix" is glossed `PAR`.** The article's own note says it "occurs throughout without a translation given", and the hand transcription duplicated the preceding morpheme's gloss onto it. The build replaces that with `PAR` — the gloss Rau & Dong and the rest of FormosanBank's Yami data give the modern cognate `am`. It is applied during processing, not written into the source snapshot, and only to a word-final suffix. 37 words are affected, and 33 of them keep a morpheme tier they would otherwise have lost.
* **A word whose morphemes do not line up with its gloss carries no morphemes.** It keeps its word-level gloss and its `M` tier is dropped, rather than publishing an analysis the article never gave — `simuskem` is one morpheme glossed `kill-with-boiling-water`. 5 words are affected, listed in [`CodeAndDocs/gloss_alignment_review.tsv`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/WakelinTexts/CodeAndDocs/gloss_alignment_review.tsv). The commonest case is the `-em`/`-m` "narration" suffix, which the article itself says occurs throughout without a translation.

Both rules mean many words and morphemes carry no gloss at all. That is the honest state of the data: the alternative is to publish `unan` as though it were a translation. `Kangkang/S34` goes furthest: the article gives three gloss units for two printed words, so that sentence publishes no word or morpheme glosses at all and only its free translation stands.

### A correction to the source

**`Kalaku1/S11`'s last two glosses are printed in the wrong order, and the corpus corrects them.** This is a deliberate departure from the article rather than a transcription of it, recorded here so it is not mistaken for an error.

The article prints `dy-aru-pa-sira` above `unan-many-still/again-them` and `a-ni-padi/machyura-rana` above `unan-past(unctn)-accompany-completely`. Swapped, the slash divides the *word* rather than one morpheme inside it — and it divides the gloss at the same point, so both halves come out even: sentence `S11` has `a-ni-padi` glossed `unan-many-still` (3 morphemes, 3 units) and `S11b` has `machyura-rana` glossed `again-them` (2 and 2), with `dy-aru-pa-sira` glossed `unan-past(unctn)-accompany-completely` in both.

A second, smaller correction: **`Kwaway/S9`'s gloss is written `bamboo.strips`, not `bamboo-strips`.** A third, across the corpus: **a gloss for a single morpheme is written with dots, not hyphens** — `(one.after.another)`, `long.time.ago`, `kill.with.boiling.water`. Under the Leipzig conventions a hyphen marks a morpheme boundary and a period joins the parts of one gloss, so the article's hyphens read as morpheme boundaries that are not there.

It was done in two passes. The first covered the 54 glosses written inside parentheses; the second covered those outside them, where the gloss belongs to a single morpheme — and that second pass is what makes the morpheme tier usable, because a hyphenated gloss on a one-morpheme word made the counts disagree and cost the word its morphemes. Repairing them took the number of words publishing no morpheme tier from **21 to 5**. The full list of every repaired gloss is in the corpus [README](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/WakelinTexts/README.md).

Untouched throughout: the 162 parenthesised abbreviation markers with no hyphen (`(unctn)`, `(pl)`, `(dual)`), hyphens outside parentheses that are real morpheme boundaries, and sentence-level free translations, which are not glosses.

The five words that still publish no morpheme tier are all genuine: `Kangkang/S34`'s three words, where the article gives three gloss units for two printed words, and `Kangkang/S39W5` and `S40W5`, where the article glosses two of three morphemes.

A further class of repair sits behind that number. The article's key defines `unan` as "unanalyzed", and wherever its printed gloss line was shorter than a word's segmentation the transcription padded the morpheme tier with `unan` — 31 words. In 28 the padded morpheme is the `-em`/`-m` suffix the article says is untranslated, so it records a real fact. Three were inventions with no basis in the print and are corrected, including `Sunagu/S2W8`, which the article glosses `from Imurud` where the transcription had `from` plus an invented `unan`.

One alternation is written with parentheses rather than a slash: `Kangkang/S18` prints `kan(u)`, and that optional `u` is treated as an alternation like any other — the sentence keeps the printed `kan(u)` notation and the word carries `kan` with the alternate `kan-u`.

Both corrections, and the corrections made to the hand-typed snapshot where it had departed from the article, are listed in [`CodeAndDocs/source_discrepancies.md`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/WakelinTexts/CodeAndDocs/source_discrepancies.md).

A checked comparison of the snapshot against the article and its errata is published at [`CodeAndDocs/source_discrepancies.md`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/WakelinTexts/CodeAndDocs/source_discrepancies.md); six findings there are still open. The FormosanBank commit this corpus was built against is recorded in [`CodeAndDocs/provenance.json`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/WakelinTexts/CodeAndDocs/provenance.json).

***

# Copyright

**License:** CC BY-NC-ND 4.0

The individual authors could not be located. The publisher released the article as **CC-BY-ND**, and FormosanBank has **interpreted that licence liberally** in order to publish the texts with their glosses and translations; publication rights were confirmed by the FormosanBank maintainer on 23 August 2026. If you are a copyright owner, please reach out to us.

***

### Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Indosan, S., Wakelin, G., Dararyaw, S., and Kalaku, S. (1958). Yami texts. Work Papers of the Summer Institute of Linguistics, University of North Dakota Session: Vol. 2, Article 7. 10.31356/silwp.vol02.07

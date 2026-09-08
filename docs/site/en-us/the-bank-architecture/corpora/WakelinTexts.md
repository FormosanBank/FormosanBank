# The Wakelin Texts

This corpus contains the 6 glossed Yami texts [found here](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/WakelinTexts/CodeAndDocs/Original.pdf) in

> Indosan, S., Wakelin, G., Dararyaw, S., and Kalaku, S. (1958). Yami texts. Work Papers of the Summer Institute of Linguistics, University of North Dakota Session: Vol. 2, Article 7. 10.31356/silwp.vol02.07

They were collected on Orchid Island between 1955 and 1957. Every sentence has an English free translation, and the texts are segmented into words and morphemes with English glosses on both tiers. There is no audio.

**Before you use this corpus: it has an `original` tier and nothing else.** Every `FORM` is `kindOf="original"` — the text as the 1958 article prints it. There is **no `standard` tier and no `PHON` (IPA) tier** at any level. The article states no writing system and its transcription matches no orthography profiled in FormosanBank, so the corpus asserts neither a transliteration nor a pronunciation. Tooling that expects a standard tier will find none; read the original tier, and treat its spelling as the article's own.

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
* **`( )` marks a probable discrepancy** in the data, per the article's own key: `(n)aku`, `puken-(en)`, `(u)m-lavi`. This notation is preserved, in eight words. It is worth being explicit about why, because the obvious reading is the wrong one: a parenthesis in FormosanBank usually marks **optional material**, which policy expands into two sentences. Here it does not — the article uses it to flag **uncertainty about the transcription itself**. Expanding it would manufacture readings the transcriber never proposed, so it stands, and the validator findings it produces are accepted rather than fixed. The one genuine exception is `Kangkang/S18`'s `kan(u)`, which really is an alternation and is published as one.
* **Hyphens mark morpheme boundaries** and are kept exactly as printed, at every level.
* **`ǥ` is a distinct letter from `g`.** The typescript writes two g's — a plain one, and a g overstruck with a horizontal bar — and the published XML writes the second as `ǥ` (U+01E5), in five words: `vaǥay` 'house', `kalaǥen`, `anyaǥay`, `laǥet` 'bad', `aǥapen` 'take'. It is phonemic, not scan noise: the bar falls only on `g`, plain-g words like `kangkang` and `ragaw` are never barred, and every token of a barred word is barred. Post-errata it corresponds exactly to modern Yami `h` [ɰ] — `vaǥay` ~ *vahay*, `aǥapen` ~ *ahapen*, `laǥet` ~ *rahet*. The hand-typed XML had flattened it to plain `g`, merging two phonemes; that has been corrected, verified word by word at 400 dpi.
* **`ř` is also a letter of the transcription**, in twelve words (`kařwan`, `vařit`, `k-ařima-raw`, `vařangyam`, `řerchip`, …). It too had been flattened, to plain `r`.
* **The article's own errata are applied.** The publication ends with an "Errata Addenda" of about fifty `for X read Y` corrections, and the published text is the corrected reading throughout. Where an erratum conflicts with another signal from the page, the erratum wins.
* An earlier release shipped a `standard` tier produced by `Yami_Wakelin_113.tsv`, a "conversion table" whose only rule deleted hyphens and which mapped no letters at all. That tier asserted nothing; both it and the table have been removed.

### A renamed file

**Text F's file and `TEXT/@id` were renamed `Kalaku4` → `Sunagu` on 7 September 2026.** The text was given by Saman Sunagu, not by Saman Kalaku, and the old name said otherwise. Published identifiers are normally stable, so this is a breaking change announced rather than a quiet cleanup: a citation of `WakelinTexts/Kalaku4` will no longer resolve, and should be read as `WakelinTexts/Sunagu`. The sentence, word and morpheme identifiers inside the file are unchanged.

### Corpus Processing

The texts were transferred from the printed article to XML **by hand**, so the hand-typed XML is the corpus's source of record and is preserved in `CodeAndDocs/pre_correction_snapshot/`. The published XML is rebuilt from it by `CodeAndDocs/generate_xml.sh`, which runs a corpus-local parser and then the shared cleaner. There is deliberately no standardization and no phonology step.

The article prints 18 alternations with a slash — `nipi/niripi`, `varit/yaked`, `akak-aep-an/(mangday su aep)`. These record **the transcriber's uncertainty**, not alternatives the speaker offered, so they are not automatically split into one sentence per option. Each is classified by hand in `CodeAndDocs/alternative_decisions.json`: a clear spelling variant (overlapping letters, same gloss) becomes an `alternate` FORM sibling **on the node that varies and on its word**, never on the sentence; anything else — different lexemes, different glosses, a word against a phrase — becomes separate sentences, the first keeping the printed sentence number and the rest taking `b`, `c`, …. A reading that replaces a whole word rather than one morpheme inside it inherits no morphemes. **No published FORM keeps a slash.**

Two rules govern the glosses:

* **`unan` is the article's "unanalyzed" marker, not a gloss.** A translation whose entire text is `unan` is not published, at any level — it recorded that the transcriber supplied nothing. Composite glosses that merely contain it, like `unan-past(unctn)-accompany-completely`, are untouched.
* **The `-em`/`-m` "narration suffix" is glossed `PAR`.** The article's own note says it "occurs throughout without a translation given", and the hand transcription duplicated the preceding morpheme's gloss onto it. The build replaces that with `PAR` — the gloss Rau & Dong and the rest of FormosanBank's Yami data give the modern cognate `am`. It is applied during processing, not written into the source snapshot, and only to a word-final suffix. 37 words are affected, and 33 of them keep a morpheme tier they would otherwise have lost.
* **A word whose morphemes do not line up with its gloss carries no morphemes.** It keeps its word-level gloss and its `M` tier is dropped, rather than publishing an analysis the article never gave — `simuskem` is one morpheme glossed `kill-with-boiling-water`. 21 words are affected, listed in [`CodeAndDocs/gloss_alignment_review.tsv`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/WakelinTexts/CodeAndDocs/gloss_alignment_review.tsv). The commonest case is the `-em`/`-m` "narration" suffix, which the article itself says occurs throughout without a translation.

Both rules mean many words and morphemes carry no gloss at all. That is the honest state of the data: the alternative is to publish `unan` as though it were a translation. `Kangkang/S34` goes furthest: the article gives three gloss units for two printed words, so that sentence publishes no word or morpheme glosses at all and only its free translation stands.

### A correction to the source

**`Kalaku1/S11`'s last two glosses are printed in the wrong order, and the corpus corrects them.** This is a deliberate departure from the article rather than a transcription of it, recorded here so it is not mistaken for an error.

The article prints `dy-aru-pa-sira` above `unan-many-still/again-them` and `a-ni-padi/machyura-rana` above `unan-past(unctn)-accompany-completely`. Swapped, the slash divides the *word* rather than one morpheme inside it — and it divides the gloss at the same point, so both halves come out even: sentence `S11` has `a-ni-padi` glossed `unan-many-still` (3 morphemes, 3 units) and `S11b` has `machyura-rana` glossed `again-them` (2 and 2), with `dy-aru-pa-sira` glossed `unan-past(unctn)-accompany-completely` in both.

A second, smaller correction: **`Kwaway/S9`'s gloss is written `bamboo.strips`, not `bamboo-strips`.** A third, across the corpus: **a multi-word gloss for a single morpheme is written with dots, not hyphens** — `(one.after.another)`, `(long.time.ago)`, `(next.morning)`. Under the Leipzig conventions a hyphen marks a morpheme boundary and a period joins the parts of one gloss, so the article's hyphens read as morpheme boundaries that are not there. 54 glosses are affected; the 162 parenthesised abbreviation markers that contain no hyphen (`(unctn)`, `(pl)`, `(dual)`) are untouched, as are hyphens outside parentheses. It is notation rather than analysis: no word's alignment changes. Neither `varit` nor its alternate `yaked` is segmented in the text, so the gloss is one two-word unit; a hyphen would read as two morphemes. Leipzig dot notation says what is meant.

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

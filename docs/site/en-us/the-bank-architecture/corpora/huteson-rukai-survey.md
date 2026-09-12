# Huteson (2003), Rukai Survey

This corpus contains the 29 Appendix B imitation-test sentences in Greg
Huteson's 2003 survey: 14 Maga (`Maolin`) and 15 Tona (`Dona`) examples.
Each has a natural source FORM, analyzed W forms, English translations,
Ortho113 forms and generated phonology. Fifteen sentences have source
morpheme analysis; fourteen have word glosses without an invented M tier.
There are 103 W and 70 M. Eight word-gloss cells are blank in the source: seven
stay unglossed and one carries a gloss inferred from the corpus's own usage,
marked as inferred in the data. No audio is included.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Rukai<br>Dona | Rukai<br>Maolin |
| --- | --- | --- |
| Word count | 55 | 48 |
| Total audio | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 | 0 |
| Translated words |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 55 | 48 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 0 | 0 |
| Morphologically segmented | 29 | 23 |
| Glossed words | 29 | 23 |

***

<!-- CORPUS STATS END -->


## **Notes and Issues**

Four things a user should know before comparing this corpus with FormosanBank's
other Rukai data. All are properties of the 2003 source, not defects in the
port.

**Maga (Maolin) does not distinguish schwa.** Ortho113 gives Maolin a
seven-vowel system, writing [e] as `é` and [ə] as `e`. Huteson's Maga
transcription uses six vowel symbols and never writes `ə` at all, though he
writes it 60 times in the Tona chapter. His `e` is therefore read as [e]
throughout and standardizes to `é`. Where the modern orthography has [ə] in
these words — `isierkɨ` 'sleep', spelled `sierkɨ` in ePark, is the clear case —
the distinction is simply not recorded in this source, and the standard tier
follows the author rather than reconciling him.

**Word-final vowels are written double.** All eleven doubled vowels in the Maga
data are word-final (`ikee`, `knee`, `mamaa`, `broo` …); the Tona data has none
in that position. The doubling is preserved as the author's, so the standard
tier writes `ikéé` where the bank's other Maolin corpus writes `iké`. Of 41
Maolin word types, 23 match the bank's spelling directly and a further 7 match
once word-final doubling is collapsed. Whether the doubling is phonemic length
or predictable final lengthening is unresolved.

**The particle `na` is never glossed.** All seven occurrences are blank in the
source's aligned display and no meaning has been coined for them: the word, and
its morpheme where the sentence is parsed, carry a form and no translation.
Seven further word-gloss cells are blank for the same reason, and Tona 9's
`a-kakə` carries one fused source gloss `1S.TOP` for two morphemes without
either being given an invented meaning. **One gloss is inferred, not from the
source:** page 43 leaves the `ki` column of Tona 14 blank, and since every other
`ki` in the corpus is glossed `NOM` and none is glossed anything else, `NOM` is
supplied there and marked as inferred.

**Case marking differs from the bank's other Rukai sources.** Huteson glosses
`ki` as `NOM`; ePark and the NTU Formosan Corpus gloss it `OBL` or `GEN`, never
`NOM`. The source's own analysis is preserved.

***

## **Access Details**

The XML and reproduction files are maintained in the
[FormosanBank repository](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Huteson-Rukai-Survey).
[The source archive](https://www.sil.org/resources/archives/9008) identifies
Huteson's report. This corpus covers its Appendix B, with all 46 PDF pages
accounted for in the source inventory.

## **Corpus Processing**

The reviewed transcription preserves natural and analyzed lines separately,
with stable example/page identities. The PDF's legacy embedded fonts require
visual source review. The sentence tier uses the natural test-list line and the
word tier the analyzed one, so the interlinear's hyphens appear at word and
morpheme level but not at the sentence. Expert corrections to `ɖ` and the
literal alternate translation in Tona 15 remain. Tona 9 retains printed
`a-kakə` and the combined word gloss `1S.TOP`; no meanings are invented for its
two individual morphemes. Four translation shorthands become same-sentence
alternatives, and every gloss is the source's apart from the single inferred one
noted above.

The source's writing system is registered as a scheme like any other:
`Orthographies/Huteson/Rukai.tsv` maps its letters to IPA for the original
phonology, and `Orthographies/ConversionTables/Rukai_Huteson_113.tsv` converts
it to Ortho113 for the standard tier. It is a mixed system rather than plain
IPA — `c` is [ʦ] and `y` is [j] — so the conversion table carries rules only
where those two systems disagree.

The corpus's `CodeAndDocs/generate_xml.sh` rebuilds from committed
transcription inputs and current shared cleaning, standardization and
phonology tools. No private repository, source download or historical Git
objects are needed. [Tool provenance](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Huteson-Rukai-Survey/CodeAndDocs/provenance.json)
records the actual build, without pinning later runs.
[Reproduction and validation instructions](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Huteson-Rukai-Survey/README.md)
include the source-specific gloss findings and correction history.

## **Copyright**

**License:** CC BY-NC-SA 4.0

SIL's terms of use state: "Unless stated otherwise in the file or item
description, all items are available under the Creative Commons
Attribution-Noncommercial-Share Alike 4.0 Unported License." Attribution to
Greg Huteson and SIL International, noncommercial use and ShareAlike
distribution are therefore required.
The corpus is also subject to FormosanBank's
[Terms of Use](../../additional-resources/terms-of-use.md) and
[AI Use and Commercial Licensing](../../additional-resources/ai-use-and-commercial-licensing.md).

## Citation

Under the [Terms of Use](../../additional-resources/terms-of-use.md), cite
FormosanBank and:

Huteson, Greg. 2003. *Sociolinguistic Survey Report for the Tona and Maga
Dialects of the Rukai Language*. SIL International.

# Sato (1931), Pazeh Ritual Songs

Three Pazeh ritual songs recorded by B. Sato at Taisha-shō (大社庄), the
historic Pazeh village in what is now Taichung, and published in the
ethnographic journal *Nanpo Dozoku* in 1931: a song of origins, a song of the
great flood, and a song of the dispersion of the people after the flood. There
are 83 sentences, each an aligned line of the printed text, and 82 Japanese
translations. This is FormosanBank's first Pazeh material.

The songs belong to the Pazeh *ai-yan* genre, named for the refrain that opens
and closes them. The text is a Japanese-era romanization, preserved exactly as
printed; there is no standard tier and no phonology, for reasons given under
Notes and Issues. No audio is included.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Pazeh<br>unknown |
| --- | --- |
| Word count | 356 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 351 |
| Morphologically segmented | 0 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->


## **Notes and Issues**

Six things a user should know before comparing this corpus with FormosanBank's
other material. All are properties of the 1931 source or of the state of Pazeh
documentation, not defects in the port.

**Sato's philological notes are not extracted.** Each of the three sections is
followed by a block of line-by-line notes (試註) — notes 1–21 for section I,
through note 41 for section II, through note 24 for section III, roughly 86
notes across five printed pages. They are inventoried in the corpus's source
ledger and were used during transcription to resolve line-wraps and readings,
but none of their content is in the XML. They are the richest unextracted
material in the source.

**There is a second translation, also not extracted.** Each section closes with
a free Japanese rendering of the whole song (大意), occupying most of three
further printed pages. It was excluded because it does not align line-by-line
with the sentence tier, but it is in substance a second translation of the same
text.

**Hyphens are syllable dividers, not morpheme boundaries.** 137 of 356 tokens
contain a hyphen — `Tap-ba-nan`, `Sap-bung-nga-kai-sih`, `ki-kit-ta-ai`.
Everywhere else in FormosanBank a hyphen inside a FORM marks morpheme
segmentation. Anything that strips or interprets hyphens will be wrong on this
corpus.

**Doubled consonants are probably not geminates.** The sequences `bb kk nn rr
dd hh mm tt ss pp` occur 24 times. They most likely mark syllable closure in
Sato's romanization rather than consonant length, but this is not settled.

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

**The orthography is not validated against a reference.** FormosanBank has no
`QC/validation/reference/Pazeh/`, so the orthography and vocabulary checks that
other corpora pass cannot run for this language at all. The character
inventory is 21 ASCII letters with no diacritics, checked by hand; nothing more
than that has been verified against external Pazeh sources.

**The dialect is unrecorded.** Pazeh has two dialects, Pazeh (巴宰) and Kaxabu
(噶哈巫). The source does not say which this is, so every text carries
`dialect="unknown"`. Taisha-shō is Pazeh territory, but the corpus does not
assert what the source does not state.

***

## **Access Details**

The XML and reproduction files are maintained in the
[FormosanBank repository](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Sato-Pazeh-Songs).
The article is catalogued by
[NTU Library](https://dl.lib.ntu.edu.tw/s/tj/item/812667) and the bound issue
by [NLPI](https://das.nlpi.edu.tw/handle/a678g). The scan itself is not
public and is not required to rebuild the corpus.

## **Corpus Processing**

The original tier was transcribed by hand from the scan, with OCR used only as
a diagnostic, and every one of the article's printed pages was reviewed. The
transcription is committed as a reviewed sentence table, and the corpus's
source ledger records all 83 included sentences alongside 16 excluded
non-target blocks — the philological notes, the free summaries, the running
headings, the colophon and the covers — each with a reason. The ledger's
identifier set is checked against the XML on every build, so a sentence cannot
be dropped silently.

Punctuation is the source's own. The Japanese translations keep the
ideographic comma 、 and the full-width parentheses （） as printed rather than
being normalized to ASCII, and the iteration mark 々 is preserved.

The corpus's `CodeAndDocs/generate_xml.sh` rebuilds from those committed inputs
and the current shared cleaner. It reads nothing else — no private repository,
no pinned checkout, no source download — and re-running it over a clean
checkout leaves the tree unchanged. The canonical standardization and phonology
steps are deliberately absent; the reason is in Notes and Issues above, and is
declared in the corpus README as a POL-047 deviation.
[Tool provenance](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Sato-Pazeh-Songs/CodeAndDocs/provenance.json)
records the build without pinning later runs.
[Reproduction and validation instructions](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Sato-Pazeh-Songs/README.md)
cover both scripts and the full list of caveats.

The article's date was corrected during review. An earlier pass had recorded it
as 1934; the issue cover reads "Vol. III, No. I, April. 1931" and lists this
article in its contents, so the citation follows the item itself. The XML
filenames and sentence identifiers use 1931 throughout.

## **Copyright**

**License:** CC BY-NC 4.0

If the author had passed by 1968, this text is public domain. Evidence is
unclear: we have possible evidence of life in 1967, based on a book publication
in 1968 possibly by the same author. In balancing community need against the
unlikely commercial interests of the unknown heirs of the author — and given
the plausible argument that extraction and curation of the data here constitute
a transformative use — we are erring on the side of making the derived data
available under CC BY-NC 4.0. If you believe you own the copyright of this
text, please contact the project director directly.

The corpus is also subject to FormosanBank's
[Terms of Use](../../additional-resources/terms-of-use.md) and
[AI Use and Commercial Licensing](../../additional-resources/ai-use-and-commercial-licensing.md).

## Citation

Under the [Terms of Use](../../additional-resources/terms-of-use.md), cite
FormosanBank and:

Sato, B. 1931. "Native Songs from Taisha-sho, Pazeh Tribe, Formosa" (大社庄の
蕃歌). *Nanpo Dozoku* 3(1): 116–126.

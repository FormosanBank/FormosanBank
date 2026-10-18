# Siraya Gospels of Gravius

Gravius's 1661 Matthew and John were printed in Siraya alongside Dutch. This corpus retains the hand-corrected Siraya transcription and its Dutch readings, with King James English and Chinese Union Version reference translations.

There are 49 chapters and 1,951 printed verse records: 1,071 in Matthew and 880 in John. All published chapter and verse IDs remain. The two source scans and the retained reference editions are identified in the corpus's [source manifest](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Siraya_Gospels/CodeAndDocs/source_manifest.json).

***

<!-- CORPUS STATS START -->
### Corpus Statistics

| | Siraya |
| --- | --- |
| Word count | 41,952 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 41,952 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 41,851 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 41,723 |
| Morphologically segmented | 0 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->

## Notes and Issues

- The Dutch transcription remains incomplete and error-prone, particularly in Matthew. It is retained under the existing decision but should not be used without further correction; b/v confusion is common. Nine Dutch readings are missing.
- John 1 divides modern verse 38 into printed verses 38 and 39. English and Chinese are split at that boundary, with later references offset through the end of the chapter.
- Four verses absent from this CUV edition's main text have no Chinese translation: Matthew 18:11 and 23:14, John 5:4 and 7:53. Available source footnote readings are retained as notes.
- Siraya has no designated modern standard, so orthography comparison is **not checked** under POL-058. The copied standard tier retains the approved fixed line-break corrections; PHON is absent.
- Historical spelling and rare combining-diaeresis letters remain, including the restored John 5:11 glyph. John 12:28 and 12:33 retain punctuation imbalances visible in the scan.

## Access Details

XML and reproduction inputs are in [Corpora/Siraya_Gospels](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Siraya_Gospels).

## Corpus Processing

The build starts from the preserved published transcription, imports the retained KJV/CUV editions, applies recorded corrections, then runs shared cleaning and standardization followed by the fixed Siraya hyphen mappings. It requires no private scan or old OCR environment. [Reproduction instructions](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Siraya_Gospels/README.md#reproduction) link the actual [tool provenance](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Siraya_Gospels/CodeAndDocs/provenance.json).

[Recorded repairs](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Siraya_Gospels/CodeAndDocs/corrections.md) restore the June 8 Dutch corrections and repair scan-confirmed OCR errors. Twenty-five following-chapter headings are removed from verse FORM without removing verses. The CUV parser retains poetry and paragraph continuations, with footnotes and section references in translation notes. The [earlier lexical correction history](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Siraya_Gospels/CodeAndDocs/transcription_history.md) and fixed standard-tier mappings remain preserved.

## Copyright

**License:** public domain

The existing public-domain designation covers the historical Gospels and retained KJV/CUV reference editions. See the corpus README for rights provenance and the central [Terms of Use](../../additional-resources/terms-of-use.md).

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or a product derived from it in a publication, cite FormosanBank and:

- Gravius, Daniël. 1661. *Het Heylige Evangelium Matthei en Johannis ofte Hagnau Ka D'llig Matiktik*. Amsterdam: Michiel Hartogh.
- The King James Bible.
- The Chinese Union Version of the Bible.

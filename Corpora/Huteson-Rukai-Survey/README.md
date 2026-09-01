# Huteson Rukai Survey

Rukai (`dru`) imitation-test examples from Greg Huteson's 2003
*Sociolinguistic Survey Report for the Tona and Maga Dialects of the Rukai
Language*. The source is [SIL archive item 9008](https://www.sil.org/resources/archives/9008).
The source record assigns CC BY-NC-SA 4.0.

The corpus contains 14 Maga examples labeled `Maolin` in FormosanBank and 15
Tona examples labeled `Dona`. Together they contain 29 sentences, 102 word
elements, 119 morpheme elements, 34 English translations, and 250 original
plus 250 standard PHON elements.

The published files were refreshed from private development commit
`b53bcd65ff749191a13608f88c4763cbae46cbe3` and revalidated on 2026-08-22
against FormosanBank tooling commit
`3a3c47c220520113f747e6a2d441494000e13c4b`. Status: ready to port. Private
source files are not included.
Rebuild the XML from the committed reviewed transcription with:

```bash
CodeAndDocs/make_xml.sh
```

Pass a FormosanBank root as the first argument, or set `FORMOSANBANK_PATH`, to
use a different checkout's current orthography and QC tools.

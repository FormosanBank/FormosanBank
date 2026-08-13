# Huteson Rukai Survey

Rukai (`dru`) imitation-test examples from Greg Huteson's 2003
*Sociolinguistic Survey Report for the Tona and Maga Dialects of the Rukai
Language*. The source is [SIL archive item 9008](https://www.sil.org/resources/archives/9008).
The source record assigns CC BY-NC-SA 4.0.

The corpus contains 14 Maga examples labeled `Maolin` in FormosanBank and 15
Tona examples labeled `Dona`. Together they contain 29 sentences, 102 word
elements, 119 morpheme elements, 34 English translations, and 250 original
plus 250 standard PHON elements.

The published files were prepared from the private development repository's
reviewed main branch on 2026-08-13. Private source files are not included.
Rebuild the XML from the committed reviewed transcription with:

```bash
CodeAndDocs/make_xml.sh
```

Pass a FormosanBank root as the first argument, or set `FORMOSANBANK_PATH`, to
use a different checkout's current orthography and QC tools.

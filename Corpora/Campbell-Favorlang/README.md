# Campbell-Favorlang

Favorlang material from Campbell's 1896 edition of *The Articles of Christian
Instruction in Favorlang-Formosan*. The source is public domain. The corpus
contains 1,049 Favorlang (`bzg`) sentences, including 684 sermon sentences, and
365 English translations.

Madeline Boese's completed sermon review is preserved in
`CodeAndDocs/sermon_review.tsv`. The reviewed decisions account for all 687
pre-review sermon units: two pairs are merged, the printed author signature is
excluded, and 684 reviewed forms are emitted. FormosanBank currently designates
no standard orthography for Babuza-Favorlang, so this corpus has no standard
or PHON tier.

The published files were refreshed from private development commit
`c07eb523f180dc1fd76887f9ad7221f1be8b2d57` and revalidated on 2026-08-22
against FormosanBank tooling commit
`3a3c47c220520113f747e6a2d441494000e13c4b`, then retagged from `fos`/Siraya to
`bzg`/Favorlang on port to match `languages.csv` and `Corpora/Latham-1862`.
Private source files are not included here. The tracked reviewed-record ledger is
sufficient for a source-free rebuild:

```bash
CodeAndDocs/make_xml.sh
```

Pass a FormosanBank root as the first argument, or set `FORMOSANBANK_PATH`, to
use a different checkout's shared cleaning tools.

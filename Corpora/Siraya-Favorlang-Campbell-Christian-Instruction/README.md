# Campbell Favorlang Christian Instruction

Favorlang material from Campbell's 1896 edition of *The Articles of Christian
Instruction in Favorlang-Formosan*. The source is public domain. The corpus
contains 1,049 Siraya (`fos`) sentences, including 684 sermon sentences, and
365 English translations.

Madeline Boese's completed sermon review is preserved in
`CodeAndDocs/sermon_review.tsv`. The reviewed decisions account for all 687
pre-review sermon units: two pairs are merged, the printed author signature is
excluded, and 684 reviewed forms are emitted. FormosanBank currently designates
no standard orthography for Siraya, so this corpus has no standard or PHON
tier.

The published files were prepared from the private development repository's
reviewed main branch on 2026-08-13. Private source files are not included here.
The tracked reviewed-record ledger is sufficient for a
source-free rebuild:

```bash
CodeAndDocs/make_xml.sh
```

Pass a FormosanBank root as the first argument, or set `FORMOSANBANK_PATH`, to
use a different checkout's shared cleaning tools.

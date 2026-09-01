# Wu Amis Pa-Verbs

Coastal Amis (`ami`) examples from Joy Wu's 2006 paper, “The Analysis of
Pa-Verbs in Amis,” presented at the Tenth International Conference on
Austronesian Linguistics. The Basecamp source record assigns CC BY-NC-SA 4.0;
the source PDF itself does not display a license statement.

The corpus contains 29 reviewed sentence variants, 153 word elements, 263
morpheme elements, and 445 original plus 445 standard PHON elements. The
committed tables record included examples, rejected readings, source coverage,
direct checks, and conversion decisions. The retained manual-edit file is
historical evidence; its accepted decisions are already integrated into the
reviewed source table used by the builder.

The published files were refreshed from private development commit
`3164d52165b413fd7803b20f109314774e1591bc` and revalidated on 2026-08-22
against FormosanBank tooling commit
`3a3c47c220520113f747e6a2d441494000e13c4b`. Status: ready to port. Private
source files are not included.
Rebuild the XML from the committed reviewed tables with:

```bash
CodeAndDocs/make_xml.sh
```

Pass a FormosanBank root as the first argument, or set `FORMOSANBANK_PATH`, to
use a different checkout's current orthography and QC tools.

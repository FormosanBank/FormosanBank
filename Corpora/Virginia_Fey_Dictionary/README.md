# Virginia Fey Amis Dictionary

Example sentences and phrases from Virginia Fey's (1986) *Amis Dictionary*
(阿美語字典), with English and Chinese translations. The current development
output contains 2,042 S records from 2,012 source examples, in
`XML/Amis/Amis.xml`. The language is Amis (`ami`), dialect Xiuguluan.
Source review remains incomplete; this output is not ready to port.

## Source and processing

The [source repository](https://github.com/miaoski/amis-data) and its maintained
spreadsheet provide the digital edition. Source versions, checksums, exact
corrections and dialect evidence are in
[source_decisions.json](CodeAndDocs/source_decisions.json). The dictionary's
introduction (printed page 13) identifies the main text as Central Amis;
the FormosanBank registry calls this dialect Xiuguluan.

Calista extensively corrected the original XML by hand. Joshua confirmed on
Basecamp card [7112943798](https://app.basecamp.com/3340659/buckets/31258415/card_tables/cards/7112943798)
that the lost converter need not be recreated. The immutable
`CodeAndDocs/pre_correction_snapshot/` is the POL-035 baseline. The build
preserves those translation readings and applies recorded source repairs,
rather than replacing the baseline with a new scrape.

[source_field_repairs.tsv](CodeAndDocs/source_field_repairs.tsv) records missing
source text with its exact witness and locator. It covers 503 unsplit examples;
16 affected slash rows and one corrected-Word reading are in the decision file.
An additional repeated translation was matched using the full source sentence.
The old upstream
stemmer dropped prefixes and entire short words. Replaying it reproduces 512
of the 519 sheet losses; the other seven have direct source evidence. Its
[2016 fix](https://github.com/miaoski/amis-data/commit/23b6efd42fe3e73c0d3cd249c14587ca6349af9f)
preserves those pieces. Source translations that were split or cleaned remain
recoverable in TRANSL notes. Later readings use `ver="alt"`. A FORM `notes`
attribute keeps the source cell only where it carries content beyond the
corrected text: the full cell of a split slash cell, and S1193's stray English
`Literally`. The sheet's converter-damaged text is not repeated in notes; it
remains in the frozen sheet copy (maintainer ruling 2026-10-17).

Sentences whose original FORM is identical are one sentence (POL-025,
maintainer ruling 2026-10-17): the later record merges into the earliest and
its translations become `ver="alt"`. Eight such pairs exist; the merged-away
ids S2843, S3026, S5023, S5280, S5703, S6241 and S6916 are retired (main had
already retired them), and S5991-opt is never created. One published sentence is removed: S6908 `ceco.`, the third option of the slash cell `sasoken a kowa' / cacoscosen a kowa' / ceco.` (Pith Paper Plant), because it is not clear how it should be read (maintainer ruling 2026-10-17); its id is retired, and the full cell remains in the FORM notes of S2761 and S6907. Records that the source
repair made different (S1899/S1900, S5141/S5142) stay separate. Historical
published IDs stay stable. New S readings use `-opt`.

## Reproduction

Use the current FormosanBank tools and their Python dependencies:

```bash
./CodeAndDocs/generate_xml.sh /path/to/FormosanBank
python3 CodeAndDocs/audit_source_alignment.py --path XML/Amis/Amis.xml
python3 -m pytest CodeAndDocs/tests
```

An embedded `Corpora/Virginia_Fey_Dictionary` checkout is detected automatically.
`FORMOSANBANK_ROOT` selects another tools checkout and `PYTHON` selects its
interpreter. The build uses committed inputs and performs no source download.

The entry point restores the snapshot, checks historical duplicate IDs,
reconciles source fields, runs shared cleaning, then standardizes and generates
PHON with the shared tables (`Orthographies/ConversionTables/Amis_Church_113.tsv`,
Xiuguluan column, and the Ortho113 profile) before shared deduplication. Validation runs separately.
The source audit checks the
recorded inventory and corrections; passing it does not resolve the remaining
source questions. Run the full FormosanBank audit and QC workflow separately.

**POL-047 deviation:** The historical ID guard and recorded source repairs
precede cleaning; reference-resource deduplication follows derived tiers.

The actual tools commit is recorded in
[provenance.json](CodeAndDocs/provenance.json), never used to select or pin a
future tools checkout. A Git-free export retains that record and requires
independent verification of its tools revision. Rebuild twice to verify all
declared outputs. Per-run cleaner and standardization warnings are disposable;
any `CodeAndDocs/quote_corrections.csv` is durable correction evidence.

## Rights

**License:** CC BY-NC 3.0

**Rights source:** Taiwan Bible Society, grant date not recorded; evidence: ask maintainer.

The pinned upstream README and licence state CC BY-NC 3.0. The publisher links
[Taiwan Bible Society correspondence dated 2008-10-07](https://drive.google.com/file/d/1s2_xzc_ZFbInk9wGXfVeUmvktJDZI5cb/view)
welcoming digitization, but that message does not specify a Creative Commons
licence or its grant date. Published XML said `CC BY-SA` until
2026-10-16, which matched neither the version nor the NonCommercial term of the
grant. The licence is kept as granted, CC BY-NC 3.0, by maintainer ruling
2026-10-16 (*"CC BY-NC 3.0 (as granted; add to vocabulary)"*) rather than mapped
to 4.0 (POL-042).

The corpus is also subject to the central FormosanBank
[licence](https://github.com/FormosanBank/FormosanBank/blob/main/LICENSE.md) and
[AI use terms](https://github.com/FormosanBank/FormosanBank/blob/main/AI-USE-ADDENDUM.md).
Commercial AI use requires prior written permission.

## Audio

No audio is supplied.

## Notes and Issues

- The digital source was checked against raw text, corrected Word files and
  conversion history. This is not a complete review of the printed dictionary.
- The digital edition writes the ng sound as `g` (printed guide, page 20), and its
  converter changed only lowercase `g`. A sentence-initial capital `G` is ng too,
  so S3846 reads `Nga'ayto` and S4934 `Nga'ayho` in both tiers (maintainer ruling
  2026-10-17).
  This narrow mapping does not recover phonemic contrasts absent from the source.
- [Printed page 345](https://drive.google.com/file/d/1eNMbHjQfC-ZR77ha17S_441hx9ZcsDhm/view)
  confirms `O kalatolo / kalitolo konini.` The page does not classify the pair
  as competing words or pronunciation variants; that decision remains open.
- Li, Joby and Zeitoun (2024) note that Fey misses some phonemic contrasts,
  including glottal versus pharyngealized stops. Wu Ming-yi modernized the
  digital spelling, but this does not establish that the distinction was
  recovered. Generated PHON must not be treated as source transcription.
- A sentence may have several English or Chinese translations. No W/M analysis
  is supplied.

## References

Fey, V. (1986). *Amis dictionary*. Taipei: The Bible Society.

Li, P. J. K., Joby, C., & Zeitoun, E. (2024). Word Lists and Dictionaries of
Formosan Languages. In *Handbook on Formosan Languages*. Brill.

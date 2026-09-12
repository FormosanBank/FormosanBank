# Virginia Fey Amis Dictionary

Example sentences and phrases from Virginia Fey's (1986) *Amis Dictionary*
(阿美語字典), with English and Chinese translations. The current development
output contains 2,051 S records from 2,012 source examples, in
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
recoverable in TRANSL notes. Later readings use `ver="alt"`.

The current shared duplicate remover compares both FORM and translations.
Previously merged records with distinct meanings are retained separately;
published translations are accounted for at their original source records.
Historical published IDs stay stable. New S readings use `-opt`.

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
reconciles source fields, runs shared cleaning, standardizes with
`--remove_accents`, generates PHON with `--orthography Ortho113`, and runs
shared deduplication. Validation runs separately. The source audit checks the
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

The pinned upstream README and licence state this licence and acknowledge the
Taiwan Bible Society's permission to digitize the dictionary. The exact grant
date still needs confirmation. Published XML previously said CC BY-SA, so the
change requires explicit maintainer rights review before publication.

The corpus is also subject to the central FormosanBank
[licence](https://github.com/FormosanBank/FormosanBank/blob/main/LICENSE.md) and
[AI use terms](https://github.com/FormosanBank/FormosanBank/blob/main/AI-USE-ADDENDUM.md).
Commercial AI use requires prior written permission.

## Audio

No audio is supplied.

## Notes and Issues

- The digital source was checked against raw text, corrected Word files and
  conversion history. This is not a complete review of the printed dictionary.
- S3846 retains the published source spelling `Ga'ayto`. The printed guide
  identifies g as the ng sound, but G is absent from the selected profile and
  its generated PHON contains `*`. Source-profile treatment remains unresolved;
  do not change the original spelling merely to clear that result.
- The proposed `kalatolo` / `kalitolo` reading still needs classification as
  competing words or pronunciation variants.
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

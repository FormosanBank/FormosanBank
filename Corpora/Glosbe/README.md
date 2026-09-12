# Glosbe Formosan Corpus

This corpus contains Glosbe dictionary and translation-memory examples for Amis,
Atayal, Saisiyat and Truku. It has eight XML files, 7,610 S, 7,789 TRANSL,
15,220 FORM and 15,220 PHON. There is no W/M analysis or Formosan audio.
Glosbe is crowdsourced; preserving a source pair does not establish that its
translation or language label is correct. Religious/JW material predominates.

## Source and coverage

The frozen crawl was captured on 2026-05-14. Its 4,245 translation-memory pairs
and 1,319 dictionary candidates were checked against 1,618 cached HTML pages by
immutable Glosbe translation ID and page SHA-256. The Chinese output instead uses
Joseph Lin's reviewed Traditional Chinese witness from
[development PR #1](https://github.com/FormosanBank/Formosan-Glosbe/pull/1),
retained at `CodeAndDocs/work/reference_glosbe/amis_glosbe_traditional.xml`.
All 25 Chinese pairs in the newer crawl have reviewed counterparts. The build
performs no new Chinese conversion and never replaces the reviewed translations
with the newer Simplified Chinese scrape.

`CodeAndDocs/source_records.jsonl` freezes the source fields, source keys,
locators, hashes and assigned S IDs. The full 5,860-row Chinese witness and
historical inputs remain available for tracing repeated and typographic variants.
`CodeAndDocs/source_labels.csv` records the 753 reviewed English pairs whose
matching page, paragraph or outline labels are editorial locators. Those labels
remain in the frozen source. Dates, years, unpaired numerals and Chinese source
labels are preserved. Parenthetical elaborations, dates written with slashes and
navigation symbols remain intact. `CodeAndDocs/source_notes.csv` moves sixteen
matching journal-citation suffixes into FORM/TRANSL notes, preserving their wording
without passing the references to PHON. Other source text is unchanged.
`CodeAndDocs/source_markers.csv` records the reviewed footnote and highlight roles
used during source capture; it does not authorize stripping unreviewed markers.

There are 1,307 lexical translations in 1,158 S, including 149 alternate readings.
Twelve candidates are excluded: one numeric-only entry, nine explicit invalid
entry/cross-reference notes, and two source-language spelling references without
an English definition. The source definitions `see (the road)` and `usb` are kept.
Absence from ILRDF or disagreement with an ILRDF gloss is never an exclusion rule.
Historical ILRDF comparison reports are reference evidence, not current QC verdicts.
They concern dictionary candidates only; `trv` means Truku in that comparison.

## Corrections and identifiers

Published TEXT/S identities are retained, except for one identical Chinese S:
`GLOSBE_ami_zho_TMEM_U000046` is represented by `..._U000012`. Their published
FORM, PHON and translation are identical. `CodeAndDocs/source_aliases.csv` also
accounts for 49 redundant English records in the old proposal. These are repeated
reference examples, not repeated occurrences in a continuous story (POL-022).
Distinct translations remain in one S with `ver="alt"` after the first (POL-025).
The two new lexical S use immutable Glosbe translation IDs. Text corrections do
not renumber records or generate new identities from their spelling.

The parser preserves word spaces around apostrophes, including the 26 dictionary
entries damaged by the old cleanup. Amis source spaces are also preserved in
Joseph's witness. Shared cleaning owns Unicode typography and quotation handling.
Only explicitly reviewed footnote stars and three keyword-highlighting pairs are
removed; a previously unreviewed star stops source capture. Literal grammaticality
judgments must not be admitted by stripping their markers (POL-016).

Joshua's accepted quotation corrections are retained in
`CodeAndDocs/quote_corrections.csv`. The original pre-correction XML remains
unchanged in `CodeAndDocs/pre_correction_snapshot/` (POL-035).
`CodeAndDocs/manual_edits.xml` replays 190 reviewed S blocks before cleaning so
fresh source builds preserve corrections without appending the same classifier
events on every run. It preserves three repairs that the restored context otherwise
defeats, separates the two quotations in Chinese S U001443,
and protects the glottal-stop letters in `ilaloma'` and `mipaino'` from two
classifier errors. The complete 119-record source-typography review identifies
57 English quotation repairs; parallel-witness and Chinese source review add
28 Chinese repairs, including
quotation/glottal boundaries missed by the classifier. It also excludes the redundant U003118 heading whose only
remaining difference is dash spacing. The source witnesses and translations
support these decisions (POL-018/025/030/050). Quote classification can still miss
quotations; neither its output nor a passing validator establishes source quality.

## Standardization and phonology

Joshua's merged source-profile decisions in `c2ce265ba` and `8fe8575e3` apply:

| Language | Original profile | Conversion table / column | XML dialect |
| --- | --- | --- | --- |
| Amis | Ortho94 | `Amis_94_113.tsv` / Coastal | unknown |
| Atayal | Church | `Atayal_Church_113.tsv` / standard | unknown |
| Truku | Ortho94 | `Seediq_94_113.tsv` / Truku | Truku |
| Saisiyat | Ortho94 | `Saisiyat_94_113.tsv` / standard | Saisiyat |

Amis is f/o-dominant. The approved non-Southern columns are identical; Coastal is
an explicit conversion route, not a claim that every speaker is Coastal. Its u→o
standardization is intentional. Unknown-dialect Amis and Atayal pronunciation uses
the supported profile defaults. Standard PHON follows Ortho113, and original PHON
uses the source profile. Accents remain in originals and follow current shared
vowel-folding rules in derived tiers. Saisiyat S and s remain distinct.

## Audio

No Formosan audio is included.

## Notes and Issues

Glosbe is crowdsourced and contains incorrect or incomplete translations and
language labels; religious/JW examples dominate. Amis and Atayal dialects are
unknown, and the approved Amis conversion does not resolve every o/u pronunciation.
Recorded quotation repairs preserve reviewed readings, but automatic quotation
classification can still miss errors. Parallel English/Chinese witnesses and
distinct source spellings remain separate even when their standard forms coincide.

## Reproduction

Use the current FormosanBank Python environment and shared checkout:

```bash
PYTHON=/path/to/FormosanBank/.venv/bin/python3 \
FORMOSANBANK_ROOT=/path/to/FormosanBank \
  CodeAndDocs/generate_xml.sh
```

The entry point starts from committed source records, applies recorded edits,
cleans, replays reviewed source aliases, deduplicates within each file, standardizes
with the tables above, and generates both PHON tiers. It uses no network, private sibling or
historical tools checkout. Run validation separately using the current QC tools.
Run `python -m pytest tests` from `CodeAndDocs/` with the same
`FORMOSANBANK_ROOT`; root-level tests exercise the historical acquisition code.
Cleaner and standardizer warning CSVs are disposable per-run reports; the quote
ledger is durable. Set `QC_OUTPUT_DIR` to put cleaner warnings outside the repository.
Review the full generated diff after changing any input or tool.

Final XML uses the shared registry's Amis, Atayal, Truku and Saisiyat directories
(POL-059). Frozen source locators and the pristine baseline retain their historical
ISO paths. Unexpected XML outside the declared output paths stops a rebuild.

**POL-047 deviation:** After cleaning, the shared removal helper applies the exact
associations in `source_aliases.csv`, preserving distinct translations as alternate
readings (POL-025). Ordinary shared deduplication then compares original FORM and
translations within each file, before standardization; standard spelling collisions
do not authorize deletion of distinct source spellings.

The reviewed output has no within-file original duplicates. Its 1,225
English/Chinese parallel groups preserve Joseph's separate witness and translations
(merged PR #72; POL-022/025). The current checker treats differing translations as
SOFT. Standard-tier checks also flag three Atayal spelling collisions, two with the
same translation, although this pipeline deduplicates original forms only. Source
language is not part of the checker's key, so Saisiyat and Truku `yako` also match.
Fixtures protect these distinct originals; findings remain visible for review.

[Build provenance](CodeAndDocs/provenance.json) records the actual shared checkout
commit without selecting or requiring that version. A Git-free export can supply
its verified revision through `FORMOSANBANK_COMMIT`; absent revision information
leaves the last reviewed provenance unchanged and prints a notice.

Source refresh is separate. `CodeAndDocs/capture_source.py --dev <dev-repo>` reads
the preserved crawl and reviewed index; it never fetches. `--refresh-labels` also
replaces the editorial-label candidates and requires their source review before
use. Historical acquisition scripts and reports are retained as evidence. They
are not alternate instructions for rebuilding the current XML.

## Rights

**License:** CC BY-NC-SA 4.0

**Rights source:** Glosbe Terms and Conditions, 2024-04-17; evidence: ask maintainer

Joshua's 2024-04-17 decision identifies the contributor licence in clause 4.4 of
the archived terms and requires share-alike distribution. Permission to scrape is
separate from this licence. Glosbe aggregates material from third-party sources;
retain the source attribution and follow the central FormosanBank terms in
[LICENSE.md](https://github.com/FormosanBank/FormosanBank/blob/main/LICENSE.md) and
[AI-USE-ADDENDUM.md](https://github.com/FormosanBank/FormosanBank/blob/main/AI-USE-ADDENDUM.md).
The proposed rights-attribute normalization requires normal maintainer merge review.

Joseph Lin prepared the reviewed Traditional Chinese conversion. Glosbe and its
contributors supplied the dictionary and translation-memory material.

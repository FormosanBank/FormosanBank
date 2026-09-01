# QC Summary

## Reviewed Inputs

- Basecamp card:
  `https://app.basecamp.com/3340659/buckets/31258415/card_tables/cards/9999151808`
- Local ignored PDF: `Private/source/latham_1862_comparative_philology.pdf`
- PDF SHA256:
  `e7b34a4063c5f552b288f2e97568d13387ffad471713e3191c644a2ec40ead7b`
- PDF size and extent: 1,195,720 bytes; 6 pages; printed pp. 314–319
- Authoritative transcription: `CodeAndDocs/source_ledger.tsv`
- Independent exact checks: `CodeAndDocs/source_checks.tsv`
- Reviewer regression ledger: `CodeAndDocs/reviewer_feedback.tsv`

The 64-cell target grid covers printed pp. 315–318. Sixty-two cells contain
lexical data. Sida Forehead and Sida Beard are printed as dashes and are
explicitly omitted. Printed pp. 314 and 319 contain no in-scope Formosan cells.

## Reviewer Feedback

All 12 July 25 attachment rows and the July 27 follow-up have explicit
regression coverage:

- Eight comma-separated source variants are separate original/alternate
  `FORM` tiers.
- Sida Mouth `motaus` is restored.
- Favorlang Ear is `chárrina`.
- Favorlang Belly is `cháan`.
- The Favorlang Neck line wrap `arribórri-` / `bon` is represented as the
  continuous alternate `arribórribon`.
- Vander Vlis Sideia `so` has no parentheses; `soa` remains an alternate.

## Reproducible Outputs

- `XML/Siraya/latham_1862_sideia_sida.xml`: 38 records.
- `XML/Babuza-Favorlang/latham_1862_favorlang.xml`: 24 records.
- `CodeAndDocs/extraction_report.csv`: exact row-level mapping.
- `CodeAndDocs/extraction_summary.md`: generated counts.
- `CodeAndDocs/source_coverage_audit.csv`: all 64 reviewed decisions.
- `CodeAndDocs/source_coverage_audit.md`: readable coverage summary.

The builder reads the source ledger directly. The source auditor independently
checks every report and XML field against that ledger and rejects missing,
extra, or ambiguous records.

## Current Authority QC

`scripts/run_final_qc.sh` requires a clean validator checkout at commit
`3a3c47c220520113f747e6a2d441494000e13c4b` and writes to a new absolute
directory outside this repository. It does not mutate corpus XML.

August 22 result:

| Check | Result |
| --- | --- |
| Source coverage | 62/62 pass; 2 dashes omitted; 0 unresolved |
| Unit tests | 8 pass |
| XML validator | 0 findings |
| Text validator | 9 SOFT |
| Gloss validator | 62 SOFT |
| Duplicate validator, original | 2 SOFT source-authentic groups |
| Duplicate validator, standard | 2 SOFT source-authentic groups |
| Dialect inventory | `bzg/Favorlang`: 1; `fos/Siraya`: 1 |
| Port readiness | 0 HARD; 0 WARN |
| Exact adjudication | 75 accepted occurrences/groups; 0 unresolved |

The XML check runs in update mode against the current public corpora while
excluding the existing `Latham-1862` target. It reports zero findings, so the
development XML has no structural, identifier, or new cross-corpus collision
blocker under the pinned authority.

### Text findings

The 9 V116 findings are exact historical diacritics in reviewed source forms:
`â`, `á`, `ó`, `é`, and `à`. `scripts/adjudicate_qc.py` requires the exact
record, rule, character, multiplicity, XML path, source-ledger value, and XML
value.

### Gloss findings

Every V060 finding is expected. The source is a lexical comparison table, not
an interlinear text, and supplies no token-aligned morphology. The adjudicator
requires exactly one V060 result for each of the 62 records and confirms that
no `W` tier was inferred.

### Duplicate findings

- `rahpal`: two distinct source cells for Foot, Klaproth Formosan Sideia on
  printed p. 315 and Sida on printed p. 318.
- `rima`: two distinct source cells for Hand, Favorlang and Sida on printed
  p. 317.

`CodeAndDocs/duplicate_group_review.csv` records the exact IDs, source
locators, severities, and rationale. Both original and standard outputs must
match it exactly.

### Orthography and vocabulary

The pinned extractor produces profiles for `Babuza-Favorlang/Favorlang` and
`Siraya/Siraya`. The public validator checkout has no reference profile for
either, so the comparison tools report a missing reference and skip the
comparison. The orthography detector's best matches are unrelated modern
profiles and are not used to alter the historical spellings.

## Reproduction

`scripts/reproduce.sh` verifies the PDF checksum, byte count, type, and page
count; rebuilds twice in a fresh work directory; reruns source checks and
pinned QC; and byte-compares the XML plus all generated reports with the
checked-in outputs.

`Private/` is ignored and absent from the tracked tree. The repository records
the public scan URL, exact local filename, size, page count, and SHA256 needed
to restore and verify the source without risking publication of local source
material.

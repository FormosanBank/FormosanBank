# Wu (2006) Amis Pa-Verbs

This corpus contains the Coastal Amis examples from Joy Wu's 2006 paper,
“The Analysis of Pa-Verbs in Amis.”

## Source and rights

Wu, Joy. 2006. “The Analysis of Pa-Verbs in Amis.” Paper presented at the
Tenth International Conference on Austronesian Linguistics, 17–20 January
2006, Puerto Princesa City, Palawan, Philippines.

The source is available through the
[SIL archive](https://www.sil.org/resources/archives/25653). The Basecamp
corpus card records CC BY-NC-SA 4.0, although the PDF does not display a
license statement. The corpus is also subject to FormosanBank's central
[license](../../LICENSE.md) and [AI-use addendum](../../AI-USE-ADDENDUM.md).

The source PDF is held privately during development and is not copied into
FormosanBank. Full page-review evidence is maintained in the
[development repository](https://github.com/FormosanBank/Formosan-Amis-Pa-Verbs).

## Contents

- `XML/Amis/pa-verbs.xml`: 29 S, 153 W, and 263 M elements.
- `CodeAndDocs/source_examples.tsv`: 29 included, source-aligned variants.
- `CodeAndDocs/rejected_source_examples.tsv`: 16 excluded items or readings.
- `CodeAndDocs/direct_source_checks.tsv`: 30 reviewed checks from PDF pages 6–10.
- `CodeAndDocs/source_coverage.tsv`: disposition for all 13 PDF pages.
- `CodeAndDocs/build_xml.py`: deterministic source-table generator.
- `CodeAndDocs/audit_source_alignment.py`: structured tier and coverage audit.
- `CodeAndDocs/adjudicate_findings.py`: exact expected-finding gate.
- `CodeAndDocs/reproduce.sh`: current generation and QC workflow.

The current port was generated and checked with FormosanBank tooling from
`ef1ebb62126337c3603e8b4f71359986b80d9494`.

## Corpus decisions

- S original FORM reconstructs the unsegmented source line. W/M original FORM
  preserves the paper's analysis markers.
- Seven printed nulls use canonical `∅` at S original and W/M. S standard
  omits the analytic null unit.
- Every W has at least one M under POL-023. Source `Pa-fli` / `give` remains
  one whole-word M because separate morpheme glosses are not printed.
- Source gloss `CaU` is retained as original, with additive standard `CAU`.
- Complete person, car, case, and translation variants follow POL-025.
  Starred, ungrammatical, and source-questionable readings remain excluded in
  the evidence ledger.
- Ortho94 is the explicit source profile. Standard FORM and PHON use the
  current shared remove-accents and Ortho113 behavior.

## Reproduce

From this corpus directory, run:

```bash
./CodeAndDocs/reproduce.sh
```

The script rebuilds XML from the reviewed tables, cleans once, standardizes,
generates original and standard phonology, verifies source alignment, and
runs the current XML, text, gloss, dialect, duplicate, orthography,
vocabulary, registry, and port-readiness checks. It then byte-compares the
rebuild with the committed XML and stores per-run reports outside the corpus.

Expected results are zero XML, validator HARD, duplicate, and port-readiness
findings. The exact reviewed SOFT and generic gloss-audit findings are locked
by `adjudicate_findings.py`. The corpus has no audio.

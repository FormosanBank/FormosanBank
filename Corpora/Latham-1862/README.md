# Latham 1862 comparative wordlist

The Formosan lexical tables in Robert Gordon Latham's *Elements of comparative
philology* (London: Walton and Maberly, 1862), printed pp. 315-318.

| Language | Source varieties | Records | XML |
| --- | --- | ---: | --- |
| Siraya (`fos`) | Klaproth Sideia, Vander Vlis Sideia, Sida | 38 | `XML/Siraya/latham_1862_sideia_sida.xml` |
| Babuza-Favorlang (`bzg`, dialect `Favorlang`) | Favorlang | 24 | `XML/Babuza-Favorlang/latham_1862_favorlang.xml` |

The 64 source cells contain 62 lexical records and two dashes (Sida Forehead
and Beard). Eight alternate readings bring the source FORM count to 70.
English headings supply the translations. Neighboring comparison languages
are outside this corpus.

## Rights

**License:** public domain

**Rights source:** Internet Archive / Mark Graves (status confirmation), 2008-07-23; evidence: ask maintainer

This is the existing public-domain work, not a new permission grant. The
[public scan record](https://archive.org/details/elementsofcompar00lathrich)
records the 1862 publication and its public-domain status. The normalized XML
value `public domain` preserves the prior `Public domain.` claim; the exact
spelling change remains subject to maintainer merge review.

## Source and preserved corrections

[The source ledger](CodeAndDocs/source_ledger.tsv) is the reviewed manual
transcription and build input. It preserves historical spelling, including
`â á ó é à`, source-variety and page locators, and distinct repeated
attestations of `rahpal` and `rima`. Comma-separated readings occupy original
and alternate FORM elements in the same record.

[The review record](CodeAndDocs/reviewer_feedback.tsv) preserves Madeline
Boese's July 25 and 27 corrections: the omitted Sida `motaus`, corrected
accents, the wrapped word `arribórribon`, and `(so)` corrected to `so` with
alternate `soa`. [Independent fixtures](CodeAndDocs/source_checks.tsv) and
[tests](CodeAndDocs/tests/test_source_ledger.py) protect these readings.
The published [pre-correction snapshot](CodeAndDocs/pre_correction_snapshot/)
is retained unchanged as historical evidence; current generation reads the
ledger, not the final XML.

The six-page review excerpt covers printed pp. 314-319. SHA-256:
`e7b34a4063c5f552b288f2e97568d13387ffad471713e3191c644a2ec40ead7b`
(1,195,720 bytes). It can be reviewed against the public scan; it is not a build
dependency. The book's Addenda and Corrigenda, pp. 753-757, contain no correction
to these Formosan tables.

## Reproduction

Use the Python environment installed for the current FormosanBank checkout:

```bash
./CodeAndDocs/generate_xml.sh
```

For a standalone development clone, set `FORMOSANBANK_ROOT` to the current
FormosanBank checkout and, if needed, `PYTHON` to its Python executable. In the
public corpus layout the surrounding checkout is used automatically. No
network fetch, private source, or historical tool checkout is required.

The build regenerates XML from the ledger and runs shared `clean_xml.py`.
[Build provenance](CodeAndDocs/provenance.json) records the tools used for the
reviewed output; it does not select or constrain future tools. Repeating a
build with unchanged inputs must leave the XML and extraction summaries
unchanged.

**POL-047 deviation:** No manual-edits file exists. Standard FORM and PHON are
omitted under the [August 12 corpus ruling](https://github.com/FormosanBank/FormosanBank/commit/be579c6b0fb4818ae90bedbbf7c0dc4d58145ac6): neither historical variety has an
approved standardization or pronunciation profile. No W/M analysis is
inferred. Query original FORM; token counting falls back to that tier.

## Validation

After building, write checks to a new directory outside the corpus:

```bash
OUTPUT_DIR=/path/to/new/review ./CodeAndDocs/validate.sh
```

The source audit is read-only by default. After an authorized ledger change,
`python CodeAndDocs/audit_source_coverage.py --write-reports` refreshes its
committed summaries. The validator runs every applicable check and rejects
unreviewed findings; [QC notes](CodeAndDocs/qc_summary.md) explain accepted
findings and unavailable comparisons.

The existing extraction wrapper calls the shared orthography API because its
CLI omits registered Babuza-Favorlang. Neither historical variety has a
reference inventory for automatic comparison. No shared code is changed here.

## Publication packaging

The complete public file set is `README.md`, `CodeAndDocs/` and `XML/` from one
verified private commit. Export those paths with `git archive` and install them
at `Corpora/Latham-1862/`; paths inside the corpus and all file bytes remain
unchanged. Replace superseded build files rather than overlaying competing
entry points. Both XML files are included; there are no private-only XML
exclusions. The preserved snapshot is a build-history input, not published XML.

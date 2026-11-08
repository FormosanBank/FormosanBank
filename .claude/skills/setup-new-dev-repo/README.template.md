# Formosan-{{CORPUS_NAME}}

**Primary language:** {{LANGUAGE}}
**Status:** Pre-QC, in development
**Created:** {{CREATED_DATE}}

## Source

<!-- Describe the source data: where it came from, who collected it, what format the original is in, any licensing/access constraints.

If the source includes private/unshareable material, large binaries, or scratch
intermediate artifacts, conventional dirs to use (already in .gitignore):
  data/        raw_data/        Original/        img-by-page/        text-by-page/
-->

TBD.

## Attribution

<!-- Citations for the original source(s). Include APA-style and BibTeX. -->

TBD.

## Rights

**License:** TBD
**Rights source:** TBD, YYYY-MM-DD; evidence: ask maintainer

<!-- POL-044. The License value is an exact value from FormosanBank's
     rights_vocabulary.csv and becomes TEXT/@copyright. The date is when
     permission was granted or last confirmed. Then, in prose, where the right
     came from. Fill this in before the first port; the port README keeps it. -->

## Scripts (in CodeAndDocs/)

<!-- Inventory of scripts that produce the contents of XML/ from the original source data. List each with one-line purpose. -->

TBD.

## How to reproduce

```bash
bash CodeAndDocs/generate_xml.sh      # the one entry point (POL-047)
```

<!-- Then, in some detail: what the source is and how it is read, what
     generate_xml.py does, every exclusion with its reason (CodeAndDocs/rejected.tsv),
     every decision table the build applies, and every shared QC step in the
     order generate_xml.sh runs them with its flags. The FormosanBank commit of
     the last build is in CodeAndDocs/provenance.json (POL-052), written by the
     build; link it, never copy the SHA into prose. -->

TBD.

## Notes and Issues

<!-- Known limitations, source defects, unresolved data problems and caveats a
     user needs before using this corpus (POL-055). "None known." if none. The
     port README keeps this section under exactly this name. -->

None known.

## QC notes

<!-- Anything specific about this corpus that affects QC: unusual orthography,
mixed dialects, code-switching, audio quality, etc. Populated by run-qc-pipeline
summaries over time. -->

TBD.

## Port-in checklist

When this corpus is ready to port into FormosanBank/Corpora/:
- [ ] Last `run-qc-pipeline` run passed and the summary is acceptable
- [ ] README is no longer all TBDs; Rights and Notes and Issues are filled in
- [ ] `CodeAndDocs/generate_xml.sh` is the only entry point, runs from a FormosanBank checkout alone, and writes `provenance.json`
- [ ] `CodeAndDocs/tests/test_source_accounting.py` is filled in and passes
- [ ] No private source data remains in the dev repo (or is gitignored)
- [ ] Run `port-corpus-in` from this directory

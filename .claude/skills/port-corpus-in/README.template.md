# {{CORPUS_NAME}}

<!-- This README is the corpus's only documentation: the FormosanBank site
     (https://formosanbank.github.io/FormosanBank/) renders it as the corpus
     page. Headings are fixed (tests/corpora/test_readme_sections.py; POL-044,
     POL-052 and POL-055 as amended 2026-10-18): keep every one, in this order.
     Optionally, a one-paragraph plain-language summary may sit here, above the
     first section. -->

## Languages and dialects

<!-- Each language (ISO 639-3 code) and dialect the XML declares, and which
     files carry which. If the source does not say which dialect it records,
     say so in those words ("The source does not record the dialect."). -->

{{LANGUAGES_AND_DIALECTS}}

## Source

<!-- Brief description of the source: what it is, who made it, when, what it
     contains, how much of it is published here, and whether there is audio. -->

{{SOURCE_DESCRIPTION}}

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/{{CORPUS_DIR}}_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

<!-- APA-style citation(s). Multiple citations separated by | per FormosanBank
     XML format conventions. -->

{{CITATION}}

## License

**License:** {{LICENSE}}
**Rights source:** {{GRANTOR}}, {{GRANT_DATE}}; evidence: ask maintainer

<!-- POL-044. The License value must equal the XML's TEXT/@copyright exactly
     (a value from rights_vocabulary.csv). The date is when permission was
     granted or last confirmed. Below, in prose: where the right came from, or
     where to find the evidence: the publisher's terms, a letter, a licence on
     the source page. -->

{{RIGHTS_PROSE}}

## Notes and caveats

<!-- POL-055. What a user needs to know before using this corpus: known
     limitations, source defects, unresolved data problems, OCR artifacts left
     in place, missing audio, hand-made edits, orthography assumptions, and
     import decisions not everyone would agree with. Not process history.
     Write "None known." if there are none. -->

{{NOTES_AND_CAVEATS}}

## Reproduction and processing

### How to reproduce

```bash
bash Corpora/{{CORPUS_DIR}}/CodeAndDocs/generate_xml.sh
```

<!-- Usually two scripts: generate_xml.sh (build) and validate.sh (checks).
     Say what each needs (inputs, environment, network) and where output goes.
     The FormosanBank commit the published XML was last built with is recorded
     in CodeAndDocs/provenance.json (POL-052): link it, never copy the SHA. -->

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

{{HOW_TO_REPRODUCE}}

### What each step does

<!-- Blow by blow, in the order generate_xml.sh runs them: every script and
     shared QC step with its flags, what it reads, what it decides, what it
     writes. Every exclusion with its reason (the rejected list lives in
     CodeAndDocs/), every decision table the build applies. A reader should be
     able to predict the XML from this section. -->

{{PROCESSING_STEPS}}

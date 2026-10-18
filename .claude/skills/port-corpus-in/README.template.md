# {{CORPUS_NAME}}

**Languages:** {{LANGUAGES}}
**Dialects:** {{DIALECTS}}
**Source:** {{SOURCE_DESCRIPTION}}

## Citation

<!-- APA-style citation(s). Multiple citations separated by | per FormosanBank XML format conventions. -->

{{CITATION}}

## Rights

**License:** {{LICENSE}}
**Rights source:** {{GRANTOR}}, {{GRANT_DATE}}; evidence: ask maintainer

<!-- POL-044. The License value must equal the XML's TEXT/@copyright exactly
     (a value from rights_vocabulary.csv). The date is when permission was
     granted or last confirmed. Below, in prose: where the right came from —
     the publisher's terms, a letter, a licence on the source page. -->

{{RIGHTS_PROSE}}

## Reproducibility

See `CodeAndDocs/` for the scripts that produce the contents of `XML/` from the
original source data. The FormosanBank commit the published XML was last built
with is recorded in [CodeAndDocs/provenance.json](CodeAndDocs/provenance.json)
(POL-052; provenance only — a rebuild always runs the current tools).

To rebuild from source:

```bash
bash Corpora/{{CORPUS_NAME}}/CodeAndDocs/generate_xml.sh
```

<!-- Then, in some detail, exactly how the data were processed: what the
     source is and how it is read (page range, columns, fields), what the
     corpus-local parser does, every exclusion with its reason (the rejected
     list lives in CodeAndDocs/), every decision table the build applies
     (overrides, corrections, review decisions — content-gated by the input
     text they expect), and every shared QC step in the order generate_xml.sh
     runs them with its flags. A reader should be able to predict the XML from
     this section. -->

<!-- Step-by-step instructions. Fill from the dev repo's README. Name every
     shared QC step the build runs, with its flags, in the order generate_xml.sh
     runs them — e.g. apply_manual_edits.py, clean_xml.py,
     suppress_transl_annotations.py (POL-024, if annotator notes were stripped
     from translations), standardize.py --tsv_path …, add_phonology.py
     --orthography …, clean_audio.py (if broken AUDIO entries were removed). -->

{{REPRODUCIBILITY_STEPS}}

## QC status

- Last QC run: {{LAST_QC_DATE}}
- Status: {{QC_VERDICT}}
- See dev repo: {{DEV_REPO_LINK_OR_NOTE}}

## Audio

{{AUDIO_STATUS}}

## Notes and Issues

<!-- Known limitations, source defects, unresolved data problems, and caveats a user
     should know before using this corpus (e.g. OCR artifacts left in place, missing
     audio for some entries, hand-made edits, orthography assumptions). Write
     "None known." if there are none. -->

{{NOTES_AND_ISSUES}}

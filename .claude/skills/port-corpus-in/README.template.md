# {{CORPUS_NAME}}

**Languages:** {{LANGUAGES}}
**Dialects:** {{DIALECTS}}
**Source:** {{SOURCE_DESCRIPTION}}
**License:** {{LICENSE}}

## Citation

<!-- APA-style citation(s). Multiple citations separated by | per FormosanBank XML format conventions. -->

{{CITATION}}

## Reproducibility

See `CodeAndDocs/` for the scripts that produce the contents of `XML/` from the original source data.

To rebuild from source:

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

# Siraya Gospels of Gravius

Gravius's 1661 Matthew and John, transcribed from the Siraya and Dutch columns, with King James English and Chinese Union Version translations. The corpus has 49 chapters and 1,951 verse records. Chapter and verse IDs retain the published `Siraya_Dutch_*` and `verse*` identities.

[Source card](https://3.basecamp.com/3340659/buckets/31258415/card_tables/cards/7289698742). This is the original development repository; the later Gravius project duplicated this corpus.

## Rights

**License:** public domain

**Rights source:** Joshua Hartshorne, 2026-03-21; evidence: ask maintainer

This preserves the rights recorded when the corpus was published. The John scan's Royal Danish Library cover marks the work public domain; the retained [CUV copyright page](CodeAndDocs/reference_translations/cmn-cu89t_usfm/copr.htm) declares the same for that edition. The KJV extract is retained with its source identity. Source scans stay private and are not build inputs. See the central [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md) for FormosanBank's existing use terms.

## Reproduction

From a FormosanBank checkout, using its Python environment:

```bash
bash Corpora/Siraya_Gospels/CodeAndDocs/generate_xml.sh
```

From this private repository, set `FORMOSANBANK_ROOT` to the current shared checkout and `PYTHON` to its Python executable, then run:

```bash
bash CodeAndDocs/generate_xml.sh
```

The build restores the committed [published transcription baseline](CodeAndDocs/baseline), imports the retained reference translations, applies [recorded corrections](CodeAndDocs/manual_edits.xml), cleans with the shared tools, copies original to standard, and applies the fixed Siraya line-break corrections. It needs no source download, ignored PDF, private second clone or historical tools checkout. All final XML is under `XML/Siraya/`. `QC_OUTPUT_DIR` can direct temporary warnings outside the repository.

[Source manifest](CodeAndDocs/source_manifest.json) records the baseline commit, scan identities and all 49 chapter page ranges. The original transcription is non-regenerable under POL-035: hand-corrected XML is the baseline, not a fresh OCR pass. [Provenance](CodeAndDocs/provenance.json) records the actual shared-tool commit used to build the output; it does not select or restrict the tools.

**POL-047 deviation:** Siraya has no defined standard or supported source phonology profile, so PHON is omitted. After shared `standardize.py --copy`, the corpus-specific `regenerate_standard_tier.py` applies the fixed `hyphen_removals.csv` decisions merged by Joshua on 2026-08-03. This retains the documented 158 line-break mappings without removing other hyphens. The copied standard tier does not assert a modern standardized spelling system. Reproduction starts from fresh input each time; validation is separate.

## Source alignment

Each XML file is one chapter and each S is one printed verse, following the recorded chapter/verse decision. Matthew has 1,071 verses; John has 880. Modern John 1:38 spans printed verses 38 and 39: the split comes before “What seek ye?” / “你們要甚麼？”. Subsequent John 1 references are one verse behind the printed IDs.

Chapter headings mistakenly appended to 25 final Matthew verses are separated from verse content; the preserved baseline and correction records retain the old text.

The CUV parser keeps poetry and paragraph continuation lines, source punctuation, verse footnotes in translation notes, and section cross-references on the section's first verse. It does not append section headings or cross-references to spoken text. Four verses absent from this CUV edition's main text remain without a Chinese TRANSL: Matthew 18:11 and 23:14, John 5:4 and 7:53. Source footnote readings remain notes rather than invented main-edition verses.

[Correction history](CodeAndDocs/transcription_history.md) preserves prior lexical decisions. [Current corrections](CodeAndDocs/corrections.md) identifies restored maintainer edits and the narrow source repairs. Retired notebooks are historical evidence only; their OCR substitutions must not be rerun over the corrected corpus.

## Audio

None.

## Notes and Issues

- Dutch OCR remains incomplete and error-prone, especially Matthew. The published instruction to retain it for now but not use it remains in effect. Nine verse readings are absent: John 11:6; Matthew 5:19, 9:26, 10:10, 10:41, 11:7, 11:29, 11:30 and 16:11. Character confusions such as b/v and f/long-s remain; this update repairs known alignment regressions and does not claim a complete Dutch transcription review.
- Siraya orthography is **not checked** under POL-058 because its standard is blank. Historical accents, meaningful hyphens, authorial parentheses and the combining `æ̈` glyph are retained. John 12:28 and 12:33 preserve unbalanced punctuation visible in the scan. PHON and W/M gloss tiers are unavailable.
- The 2026-08 re-transcription is superseded by the preserved published corrections plus the scoped repairs documented here. Its old whole-output hashes are not a source-fidelity verdict for this build.

## Citation

Gravius, Daniël. 1661. *Het Heylige Evangelium Matthei en Johannis ofte Hagnau Ka D'llig Matiktik. Ka na sasoulat ti Mattheus, ti Johannes appa.* Amsterdam: Michiel Hartogh.

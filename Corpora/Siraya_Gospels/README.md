# Siraya Gospels of Gravius

Gravius's 1661 Matthew and John, transcribed from the Siraya and Dutch columns, with King James English and Chinese Union Version translations. Gravius's 1661 Matthew and John were printed in Siraya alongside Dutch. This corpus retains the hand-corrected Siraya transcription and its Dutch readings, with King James English and Chinese Union Version reference translations.

## Languages and dialects

All 49 XML files (under `XML/Siraya/John/` and `XML/Siraya/Matthew/`) declare `xml:lang="fos"` (Siraya) and `dialect="Siraya"` on `<TEXT>`. The Siraya text is the sentence-level `FORM`; the Dutch column of the print is carried as `TRANSL xml:lang="nld"`, alongside English (`eng`, King James Version) and Chinese (`zho`, Chinese Union Version) translations.

## Source

Daniël Gravius's *Het Heylige Evangelium Matthei en Johannis* (Amsterdam, 1661), which prints the Gospels of Matthew and John in Siraya alongside Dutch.

The corpus has 49 chapters and 1,951 verse records. There are 49 chapters and 1,951 printed verse records: 1,071 in Matthew and 880 in John. Chapter and verse IDs retain the published `Siraya_Dutch_*` and `verse*` identities. All published chapter and verse IDs remain.

The two source scans are identified in the corpus's [source manifest](CodeAndDocs/source_manifest.json), and the retained King James and Chinese Union Version editions in its [reference-translation manifest](CodeAndDocs/reference_translations/manifest.json).

[Source card](https://3.basecamp.com/3340659/buckets/31258415/card_tables/cards/7289698742). This is the original development repository; the later Gravius project duplicated this corpus.

Audio: None.

#### Source alignment

Each XML file is one chapter and each S is one printed verse, following the recorded chapter/verse decision. Matthew has 1,071 verses; John has 880. Modern John 1:38 spans printed verses 38 and 39: the split comes before “What seek ye?” / “你們要甚麼？”. Subsequent John 1 references are one verse behind the printed IDs.

Chapter headings mistakenly appended to 25 final Matthew verses are separated from verse content; the preserved baseline and correction records retain the old text.

The CUV parser keeps poetry and paragraph continuation lines, source punctuation, verse footnotes in translation notes, and section cross-references on the section's first verse. It does not append section headings or cross-references to spoken text. Four verses absent from this CUV edition's main text remain without a Chinese TRANSL: Matthew 18:11 and 23:14, John 5:4 and 7:53. Source footnote readings remain notes rather than invented main-edition verses.

[Correction history](CodeAndDocs/transcription_history.md) preserves prior lexical decisions. [Current corrections](CodeAndDocs/corrections.md) identifies restored maintainer edits and the narrow source repairs. Retired notebooks are historical evidence only; their OCR substitutions must not be rerun over the corrected corpus.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Siraya_Gospels_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

- Gravius, Daniël. 1661. *Het Heylige Evangelium Matthei en Johannis ofte Hagnau Ka D'llig Matiktik. Ka na sasoulat ti Mattheus, ti Johannes appa.* Amsterdam: Michiel Hartogh.
- The King James Bible.
- The Chinese Union Version of the Bible.

## License

**License:** public domain
**Rights source:** Joshua Hartshorne, 2026-03-21; evidence: ask maintainer

This preserves the rights recorded when the corpus was published. The John scan's Royal Danish Library cover marks the work public domain; the retained [CUV copyright page](CodeAndDocs/reference_translations/cmn-cu89t_usfm/copr.htm) declares the same for that edition. The KJV extract is retained with its source identity. Source scans stay private and are not build inputs. See the central [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md) for FormosanBank's existing use terms.

The existing public-domain designation covers the historical Gospels and retained KJV/CUV reference editions. See the corpus README for rights provenance and the central [Terms of Use](https://formosanbank.github.io/FormosanBank/additional-resources/terms-of-use/).

## Notes and caveats

- Dutch OCR remains incomplete and error-prone, especially Matthew. The published instruction to retain it for now but not use it remains in effect. Nine verse readings are absent: John 11:6; Matthew 5:19, 9:26, 10:10, 10:41, 11:7, 11:29, 11:30 and 16:11. Character confusions such as b/v and f/long-s remain; this update repairs known alignment regressions and does not claim a complete Dutch transcription review. The Dutch transcription remains incomplete and error-prone, particularly in Matthew. It is retained under the existing decision but should not be used without further correction; b/v confusion is common. Nine Dutch readings are missing.
- John 1 divides modern verse 38 into printed verses 38 and 39. English and Chinese are split at that boundary, with later references offset through the end of the chapter.
- Four verses absent from this CUV edition's main text have no Chinese translation: Matthew 18:11 and 23:14, John 5:4 and 7:53. Available source footnote readings are retained as notes.
- Siraya orthography is **not checked** under POL-058 because its standard is blank. Historical accents, meaningful hyphens, authorial parentheses and the combining `æ̈` glyph are retained. John 12:28 and 12:33 preserve unbalanced punctuation visible in the scan. PHON and W/M gloss tiers are unavailable. Siraya has no designated modern standard, so orthography comparison is **not checked** under POL-058. The copied standard tier retains the approved fixed line-break corrections; PHON is absent.
- Historical spelling and rare combining-diaeresis letters remain, including the restored John 5:11 glyph. John 12:28 and 12:33 retain punctuation imbalances visible in the scan.
- The 2026-08 re-transcription is superseded by the preserved published corrections plus the scoped repairs documented here. Its old whole-output hashes are not a source-fidelity verdict for this build.

## Reproduction and processing

### How to reproduce

From a FormosanBank checkout, using its Python environment:

```bash
bash Corpora/Siraya_Gospels/CodeAndDocs/generate_xml.sh
```

From this private repository, set `FORMOSANBANK_ROOT` to the current shared checkout and `PYTHON` to its Python executable, then run:

```bash
bash CodeAndDocs/generate_xml.sh
```

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

The build restores the committed [published transcription baseline](CodeAndDocs/baseline), imports the retained reference translations, applies [recorded corrections](CodeAndDocs/manual_edits.xml), cleans with the shared tools, copies original to standard, and applies the fixed Siraya line-break corrections. It needs no source download, ignored PDF, private second clone or historical tools checkout. It requires no private scan or old OCR environment. All final XML is under `XML/Siraya/`. XML and reproduction inputs are in `Corpora/Siraya_Gospels`. `QC_OUTPUT_DIR` can direct temporary warnings outside the repository.

The build starts from the preserved published transcription, imports the retained KJV/CUV editions, applies recorded corrections, then runs shared cleaning and standardization followed by the fixed Siraya hyphen mappings. [Reproduction instructions](#how-to-reproduce) link the actual [tool provenance](CodeAndDocs/provenance.json).

[Source manifest](CodeAndDocs/source_manifest.json) records the baseline commit, scan identities and all 49 chapter page ranges. The original transcription is non-regenerable under POL-035: hand-corrected XML is the baseline, not a fresh OCR pass. [Provenance](CodeAndDocs/provenance.json) records the actual shared-tool commit used to build the output; it does not select or restrict the tools.

**POL-047 deviation:** Siraya has no defined standard or supported source phonology profile, so PHON is omitted. After shared `standardize.py --copy`, the corpus-specific `regenerate_standard_tier.py` applies the fixed `hyphen_removals.csv` decisions merged by Joshua on 2026-08-03. This retains the documented 158 line-break mappings without removing other hyphens. The copied standard tier does not assert a modern standardized spelling system. Reproduction starts from fresh input each time; validation is separate.

[Recorded repairs](CodeAndDocs/corrections.md) restore the June 8 Dutch corrections and repair scan-confirmed OCR errors. Twenty-five following-chapter headings are removed from verse FORM without removing verses. The CUV parser retains poetry and paragraph continuations, with footnotes and section references in translation notes. The [earlier lexical correction history](CodeAndDocs/transcription_history.md) and fixed standard-tier mappings remain preserved.

### What each step does

`CodeAndDocs/generate_xml.sh` runs with `set -euo pipefail`, so any failing step stops the build. It works in a fresh staging folder `CodeAndDocs/.build.XXXXXX/` (deleted on exit). `FORMOSANBANK_ROOT` (default: the checkout three levels above `CodeAndDocs/`) chooses the shared tools, `PYTHON` (default `python3`) the interpreter, and `QC_OUTPUT_DIR` (default: a new temporary folder) where cleaning warnings go. Python needs `lxml` (corpus `requirements.txt`) plus FormosanBank's own requirements. The steps, in order:

1. **`CodeAndDocs/generate_xml.py --output-dir <stage>/XML`** reads the 49 baseline files under `CodeAndDocs/baseline/Siraya/{John,Matthew}/chapter*.xml`, the reference-translation `manifest.json`, the KJV extract `eng-kjv-nltk-gutenberg.tsv` and the two CUV USFM books (`70-MATcmn-cu89t.usfm`, `73-JHNcmn-cu89t.usfm`). For each file it:
   - deletes every `FORM kindOf="standard"` and every `PHON` (both are rebuilt or omitted later);
   - for each `S`, reads the verse number from its `verse<N>` id; in John 1, verses 39 and later are looked up as verse N−1 (the printed split of modern 1:38);
   - fills each existing `TRANSL xml:lang="eng"` with the KJV verse text and each existing `TRANSL xml:lang="zho"` with the CUV verse text, setting a `notes` attribute when the CUV verse has footnotes or section cross-references (joined with ` / `). It only fills `TRANSL` elements the baseline already has; it creates none. The Dutch `TRANSL xml:lang="nld"` and the original `FORM` are left as the baseline has them;
   - stops with an error if one of the four CUV-omitted verses (listed in the manifest) has a Chinese `TRANSL`;
   - for John 1:38 and 1:39, splits the English and Chinese verse at the manifest's marker (`What seek ye?` / `「你們要甚麼？」`): verse 38 gets the text before it, verse 39 the marker and what follows, and the build stops if the marker is not found exactly once;
   - writes the file to the stage, indented with four spaces.

   The CUV reader (`CodeAndDocs/reference_translations.py`) joins a verse's continuation lines (`\q1`, `\m`, `\p`); drops `\s1` section headings; turns each `\r` line into a note `Parallel passages: …` on the first verse of the section; moves `\f … \f*` footnotes into notes; strips inline `\pn`, `\add`, `\fv`, `\ft` markers; and stops on any other USFM marker or duplicate verse. The KJV reader stops on a duplicate verse.

2. **`QC/cleaning/apply_manual_edits.py --corpora_path <stage>/XML --manual_file CodeAndDocs/manual_edits.xml`** replaces the recorded sentences with their corrected versions: 77 complete `S` records across 34 files (described in [corrections.md](CodeAndDocs/corrections.md)). It regenerates the human-readable changelog `CodeAndDocs/manual_edits.md`.

3. **`QC/cleaning/clean_xml.py --corpora_path <stage>/XML --warnings_dir <QC_OUTPUT_DIR>`** normalizes Unicode and HTML entities in place and writes `cleaner_warnings.csv` to the warnings folder, outside the published XML. Its apostrophe-as-quotation correction runs only for languages with a `QC/validation/reference/<Language>/attestation.txt`; there is no Siraya folder there, so it does not apply to this corpus (read from the folder listing; not run). Its quote-correction log path resolves inside the staging folder, which is deleted.

4. **`QC/utilities/standardize.py --corpora_path <stage>/XML --copy`** creates a `FORM kindOf="standard"` in every `S` as an exact copy of the original `FORM` (pure duplication, no spelling change).

5. **`CodeAndDocs/regenerate_standard_tier.py --xml-dir <stage>/XML/Siraya`** rewrites every standard `FORM` as its original `FORM` with the line-break hyphens listed in `CodeAndDocs/hyphen_removals.csv` removed (199 rows, 158 distinct hyphenated forms). Words are matched case-insensitively as runs of Latin letters, apostrophes and hyphens; a match is left alone when its hyphen touches an editorial bracket (`word-(`, `)-word`, `]-word`); an initial capital is kept. All other hyphens stay. It prints how many standard FORMs it rewrote.

6. **`rsync -a --delete <stage>/XML/ Corpora/Siraya_Gospels/XML/`** replaces the published XML with the staged build; files the build did not produce are deleted.

7. **Provenance.** If the FormosanBank checkout has a `.git`, its `HEAD` commit is written to [CodeAndDocs/provenance.json](CodeAndDocs/provenance.json); otherwise the existing file must already be there or the build stops.

8. The script prints the warnings folder path.

Not run by `generate_xml.sh`: `CodeAndDocs/test_source_alignment.py` (a separate check) and the retired notebooks in `CodeAndDocs/legacy_notebooks/`.

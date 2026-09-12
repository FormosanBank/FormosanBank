# Akiw (2012): Sakizaya affixes

Akiw, Chung-Wen Hsu. 2012. *The Study of Affixes in Sakizaya*. Master's thesis,
National Dong Hwa University. The corpus contains Sakizaya forms, Chinese
translations and source analyses from the numbered examples and affix tables.

## Review status

**Technical QC: ready to port. Publication licence unresolved.** Source and
output review preserves the expert transcription, restores missed footnote/prose
examples and translation readings, and verifies repeatable standalone builds.
Example 17d keeps its source null prefix; 23c has two aligned optional readings.

Madeline Boese's August 14 review supplies the corrected Chinese, alternative
meanings, notes, morpheme analyses and exclusions. Regeneration preserves that
complete transcription; a new OCR pass does not replace it. Examples 69a/82a
retain their different source analyses even though their standard forms agree.

## Corpus

Two TEXT files under `XML/Sakizaya/` contain 677 S: 239 numbered-example readings,
six footnote/prose examples and 432 affix entries, with 1,763 W, 2,552 M,
9,984 FORM, 4,992 standard PHON and 5,134 TRANSL.
There are 731 S translations and 4,403 untiered W/M source glosses. No audio
or source-supplied phonetic transcription is included.

The committed inventories account for 814 units: 261 numbered occurrences,
434 main-table rows, 113 late summary rows and six footnote/prose examples.
Fourteen exact repeats, nine source-starred examples, two additional expert
exclusions and every summary
row are excluded. The collection covers sentence examples and the main affix
inventory; phonology demonstrations, paradigms, lexical discussion and quoted
analyses of other languages remain source context. This is not a transcription
of every linguistic item in the thesis.
The 238 included numbered occurrences produce 239 S because 23c permits both
`ha-min han mu-kan` and `ha-min han mu-kan kiya hemay` (scan p. 55, POL-026).

## Reproduce

From a FormosanBank checkout, with its Python dependencies installed:

```bash
source .venv/bin/activate
./Corpora/Sakizaya-Affixes/CodeAndDocs/generate_xml.sh
python -m unittest discover -s Corpora/Sakizaya-Affixes/CodeAndDocs -p test_source.py
```

The build uses the committed source inventories and TEXT metadata for fresh
pre-manual S records, applies all 670 expert correction records through the
shared manual-edit tool, expands 23c and adds the source supplement, then cleans,
standardizes and generates standard PHON. The supplement recovers footnotes
9, 10, 14 and 15, a prose example spanning PDF pages 130-131, and four source
translation alternatives alongside the retained primary readings.
The inventories plus complete manual transcription are the documented source
baseline (POL-035); no private scan, OCR cache, download or historical Git object
is needed. All manual records are retained, including no-ops (POL-030).

**POL-047 deviation:** Original PHON is omitted under Madeline's August 13–14
decision because the source supplies no phonetic transcription. The reviewed
TSV removes circumfix ellipses only from derived standard forms, preserving
original M such as `ma-...-ay` and producing standard `ma--ay`.
The source-specific 23c expansion follows manual transcription and precedes
cleaning; it preserves the longer reading's IDs and gives the shorter reading
stable `-opt` IDs, with only its own W/M and Chinese translation. The same
pre-cleaning step adds the scan-located supplement to the expert transcription.
The shared `--segmented-without-m-tier` option removes the explicit morphology
hyphen from the standard sentence in footnote 10 without inventing M analysis.
The source uses Lin (2011)'s dictionary spelling (scan pp. 29–31); its retained
letters align with Ortho113. Standard PHON represents that designated standard,
not the source's narrower phonetic descriptions.

[Build provenance](CodeAndDocs/provenance.json) records the actual tools after a
successful build. It never selects or pins tools. A Gitless export retains its
record and reports that its tools revision needs separate verification.
Source acquisition and validation run separately from generation.

## Rights

**License:** Unresolved; author permission has not yet been mapped to an
evidenced value in FormosanBank's rights vocabulary.

**Rights source:** Akiw, Chung-Wen Hsu, 2026-04-01; evidence: ask maintainer

The author permits thesis data in FormosanBank but the available grant names
no Creative Commons licence. The existing permission statement is preserved
in XML pending a maintainer decision. It is not a compliant POL-042 licence,
and publication remains blocked. The source PDF is not distributed here.

## Audio

None in the source.

## Notes and Issues

The source uses whole-word Chinese meanings beside separate affix/root analyses
in the inventory, and sometimes glosses an unsegmented word as a complex form.
Some analyzed sentences have incomplete M coverage; four footnote examples
have no word glosses. No missing analysis or gloss has been invented.
Source circumfix ellipses and the distinct analyses of repeated examples are
preserved. Only standard PHON is supplied, following the expert review.
The excluded late-summary dataset is not part of the corpus. The author grant
does not yet establish a publication licence.

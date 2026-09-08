# Akiw (2012): Sakizaya affixes

Akiw, Chung-Wen Hsu. 2012. *The Study of Affixes in Sakizaya*. Master's thesis,
National Dong Hwa University. The corpus contains Sakizaya forms, Chinese
translations and source analyses from the numbered examples and affix tables.

## Review status

**Not ready to port.** The licence decision and final source-coverage/gloss
review remain open. The former ready-to-merge claims predate the current review.
The repair restores example 17d's source null prefix on original S/W and its
two M units, and expands example 23c's optional object into two aligned S.
Standard S omits the silent prefix; the null M is unglossed.

Madeline Boese's August 14 review supplies the corrected Chinese, alternative
meanings, notes, morpheme analyses and exclusions. Regeneration preserves that
complete transcription; a new OCR pass does not replace it. Examples 69a/82a
retain their different source analyses even though their standard forms agree.

## Corpus

Two TEXT files contain 671 S: 239 numbered-example variants and 432 affix entries,
with 1,752 W, 2,544 M, 9,934 FORM, 4,967 standard PHON and 5,105 TRANSL.
There are 721 S translations and 4,384 untiered W/M source glosses. No audio
or source-supplied phonetic transcription is included.

The committed inventories account for 808 units: 261 numbered occurrences,
434 main-table rows and 113 late summary rows. Fourteen exact repeats, nine
source-starred examples, two additional expert exclusions and every summary
row are excluded. This inventory count is not a claim that every linguistic
item in the 174-page thesis has been included; unnumbered/background material
and footnotes still need final coverage accounting.
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
shared manual-edit tool, expands 23c, then cleans, standardizes and generates
standard PHON.
The inventories plus complete manual transcription are the documented source
baseline (POL-035); no private scan, OCR cache, download or historical Git object
is needed. All manual records are retained, including no-ops (POL-030).

**POL-047 deviation:** Original PHON is omitted under Madeline's August 13–14
decision because the source supplies no phonetic transcription. The reviewed
TSV removes circumfix ellipses only from derived standard forms, preserving
original M such as `ma-...-ay` and producing standard `ma--ay`.
The source-specific 23c expansion follows manual transcription and precedes
cleaning; it preserves the longer reading's IDs and gives the shorter reading
stable `_SHORT` IDs, with only its own W/M and Chinese translation.

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

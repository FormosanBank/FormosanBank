# Huteson (2003) Rukai Survey

This corpus contains the 29 Rukai imitation-test sentences in Appendix B of
Greg Huteson's 2003 sociolinguistic survey: 14 from Maga and 15 from Tona.
FormosanBank uses the canonical dialect labels Maolin for Maga and Dona for
Tona.

Each sentence has source-faithful and Ortho113 forms, standard phonology, an
English translation, and printed-page provenance. Word and morpheme tiers are
included only where the published alignment supports them. Eight words with
blank source gloss cells remain unglossed, and Tona 9 keeps its fused source
gloss without invented morpheme analysis. No audio is included.

## Source and rights

Huteson, Greg. 2003. *Sociolinguistic Survey Report for the Tona and Maga
Dialects of the Rukai Language*. SIL International.

The report was distributed through the
[SIL archive](https://www.sil.org/resources/archives/9008). SIL's accompanying
terms identify the source as Creative Commons
Attribution-NonCommercial-ShareAlike 4.0 unless otherwise stated. Attribution
to the contributor, SIL International, and named rights holders is required.

The source files and full review evidence remain in the
[development repository](https://github.com/FormosanBank/Formosan-Huteson-Rukai-Survey).
They are not copied into FormosanBank.

## Contents

- `XML/Rukai/`: the two published Maga/Maolin and Tona/Dona XML files.
- `CodeAndDocs/build_xml.py`: deterministic Appendix B XML builder.
- `CodeAndDocs/extraction_report.tsv`: the 29 reviewed source records.
- `CodeAndDocs/huteson_source_to_ortho113.tsv`: source-to-Ortho113 mapping.
- `CodeAndDocs/preserve_rukai_segmentation.py`: preserves reviewed Rukai
  segmentation after shared cleaning.
- `CodeAndDocs/reproduce.sh`: rebuilds and validates the published XML.

## Reproduce

From this corpus directory:

```bash
./CodeAndDocs/reproduce.sh
```

Set `FORMOSANBANK_PATH` or `PYTHON` to override the containing FormosanBank
checkout or its Python environment.

The development audit checked all 46 source pages and visually reviewed
Appendix B pages 38-44. The final corrections use printed `ɖ`, the detailed
aligned form for Tona 4, and an alternate literal translation for Tona 15.
All hard validators pass. Remaining soft findings preserve source punctuation,
reviewed Rukai hyphens, blank printed gloss cells, and Tona 9's fused gloss.

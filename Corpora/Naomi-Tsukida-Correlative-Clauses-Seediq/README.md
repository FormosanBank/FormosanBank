# Naomi-Tsukida-Correlative-Clauses-Seediq

**Language:** Seediq (`trv`), Truku dialect

**Source:** Tsukida, N. (2014). "Correlative clauses in Seediq." In *Papers from 12-ICAL, Volume 2: Argument realisations and related constructions in Austronesian languages* (pp. 69-79). Asia-Pacific Linguistics.

**License:** Copyright held by the authors, released under Creative Commons Attribution Licence (CC BY 4.0).

This corpus accounts for all 39 reviewed source units on the article's 11 pages. It publishes 26 Seediq source units and documents 13 comparison, duplicate, or source-starred exclusions. Optional constituents in examples 6 and 9 expand into four explicit sentence variants under POL-026.

## Reproducibility

The XML is generated from the reviewed inputs under `CodeAndDocs/raw_data/`. Source coverage and output alignments live under `CodeAndDocs/evidence/`. The build preserves original FORM tiers, gives every W at least one M, keeps source gloss TRANSL elements untiered, and adds reviewed canonical infix glosses as `kindOf="standard"`. The corpus-scoped source profile gives the sole `ŋ` to `ng` standard conversion a passing transitive audit.

From the FormosanBank repository root, run:

```bash
bash Corpora/Naomi-Tsukida-Correlative-Clauses-Seediq/CodeAndDocs/reproduce.sh
```

The script runs the current cleaning, standardization, phonology, source-alignment, XML, text, and gloss checks twice and requires byte-identical output.

## QC status

Final counts: 1 TEXT, 28 S, 201 W, 268 M, 497 original PHON, and 497 standard PHON. Current XML, text, and gloss validation has zero unresolved HARD findings. The corpus has no audio.

The build was validated with FormosanBank tooling at `ef1ebb62126337c3603e8b4f71359986b80d9494`. The TEXT id and deterministic source-based S/W/M ids are stable across rebuilds and checked against published corpora.

## Citation

Tsukida, N. (2014). "Correlative clauses in Seediq." In I Wayan Arka & N. L. K. Mas Indrawati (Eds.), *Papers from 12-ICAL, Volume 2: Argument realisations and related constructions in Austronesian languages* (pp. 69-79). Asia-Pacific Linguistics.

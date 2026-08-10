# Naomi-Tsukida-Correlative-Clauses-Seediq

**Language:** Seediq (`trv`), Truku dialect

**Source:** Tsukida, N. (2014). “Correlative clauses in Seediq.” In *Papers from 12-ICAL, Volume 2: Argument realisations and related constructions in Austronesian languages* (pp. 69–79). Asia-Pacific Linguistics.

**License:** Copyright held by the authors, released under Creative Commons Attribution Licence (CC BY 4.0).

This corpus contains 26 source-reviewed Seediq examples with aligned word and morpheme glosses. The source article is available from [ANU Open Research](https://openresearch-repository.anu.edu.au/items/8bfb8bf0-2f58-4eae-947c-bf9af50faf9f).

## Reproducibility

`XML/Seediq/tsukida_2014_correlative_clauses_in_seediq.xml` is generated from the reviewed inputs under `CodeAndDocs/raw_data/`. The build preserves the source original tier, maps the reviewed Tsukida Truku notation to the Ortho113 standard tier, restores source brackets removed by shared cleaning, and applies the reviewed PHON policy.

From the FormosanBank repository root, run:

```bash
FORMOSANBANK_PATH=/path/to/FormosanBank \
  bash Corpora/Naomi-Tsukida-Correlative-Clauses-Seediq/CodeAndDocs/reproduce.sh
```

The script runs the build twice, checks source coverage and reviewed alignments, validates XML, text, and gloss tiers, and requires byte-identical output between runs.

## QC status

The latest development QC found 1 TEXT, 26 sentences, 188 W elements, 115 M elements, 329 PHON tiers, zero hard findings, and zero gloss findings. The corpus has no audio.

## Citation

Tsukida, N. (2014). “Correlative clauses in Seediq.” In I Wayan Arka & N. L. K. Mas Indrawati (Eds.), *Papers from 12-ICAL, Volume 2: Argument realisations and related constructions in Austronesian languages* (pp. 69–79). Asia-Pacific Linguistics.

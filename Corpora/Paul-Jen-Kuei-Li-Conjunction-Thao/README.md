# Conjunction in Thao

This corpus contains Paul Jen-Kuei Li's Thao examples from “Conjunction in
Thao” (2014), pp. 401–409 in *Papers from 12-ICAL, Volume 2*.

This corpus is subject to its source license and the central FormosanBank terms
in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md).

| Field | Value |
|---|---|
| Language | Thao (`ssf`, dialect `Thao`, glottocode `thao1240`) |
| Source | [Li, “Conjunction in Thao”](https://openresearch-repository.anu.edu.au/items/8bfb8bf0-2f58-4eae-947c-bf9af50faf9f) |
| Source license | Creative Commons Attribution 4.0 International (CC BY 4.0) |
| Scope | 24 numbered examples and three examples from footnote 7 |
| XML | [`XML/Thao/li_2014_conjunction_in_thao.xml`](XML/Thao/li_2014_conjunction_in_thao.xml) |
| Development repository | [Formosan-Paul-Jen-Kuei-Li-Conjunction-Thao](https://github.com/FormosanBank/Formosan-Paul-Jen-Kuei-Li-Conjunction-Thao) |

The corpus contains 27 sentences, 211 source-aligned W nodes, and 169
source-supported M nodes. Examples 1–24 retain the printed word/gloss
alignment. The three unglossed footnote examples remain sentence-only.

Sentence-level `FORM[@kindOf="original"]` preserves the source transcription.
Sentence-level standard forms remove source segmentation markers. W-level
standard forms retain printed segmentation so the gloss and M tiers remain
aligned. No PHON or AUDIO tier is inferred.

## Reproduce

The committed reviewed ledger is sufficient; the original PDF is not required.
From this corpus directory, run:

```bash
bash CodeAndDocs/reproduce.sh
```

This writes a scratch `Final_XML/` tree, compares it byte-for-byte with the
published `XML/` tree, and runs the independent source-fidelity checks.

## Citation

Li, P. J.-K. (2014). Conjunction in Thao. In I Wayan Arka & N. L. K. Mas
Indrawati (Eds.), *Papers from 12-ICAL, Volume 2: Argument realisations and
related constructions in Austronesian languages* (pp. 401–409). Asia-Pacific
Linguistics.

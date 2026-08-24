# Wakelin Yami texts (1958)

## License and AI Use

This corpus is subject to its source rights and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

Publication rights were confirmed by the FormosanBank maintainer on 2026-08-23. No open license is asserted. The source notice is: `All rights reserved; FormosanBank has permission to publish.`

## Source and contents

This corpus contains six Yami (`xml:lang="tao"`, `dialect="Yami"`) narrative texts from:

> Indosan, S., Wakelin, G., Dararyaw, S., and Kalaku, S. (1958). Yami texts. Work Papers of the Summer Institute of Linguistics, University of North Dakota Session: Vol. 2, Article 7. 10.31356/silwp.vol02.07

The exact 22-page source is stored at [`CodeAndDocs/Original.pdf`](CodeAndDocs/Original.pdf). The checked ledger contains 171 printed source records and emits 190 independently aligned sentence variants, 926 words, and 1,183 morphemes. There is no audio.

| File | Text | Informant | Sentences | Words | Morphemes |
|---|---|---|---:|---:|---:|
| `XML/Yami/Kangkang.xml` | A. *Ji Kangkang* | Samen Indosan, April 1955 | 44 | 219 | 263 |
| `XML/Yami/Kwaway.xml` | B. *Kwaway* | Sinan Dararyaw, May 1957 | 67 | 290 | 354 |
| `XML/Yami/Kalaku1.xml` | C. | Saman Kalaku, 6 September 1956 | 30 | 124 | 177 |
| `XML/Yami/Kalaku2.xml` | D. | Samen Kalaku, 6 September 1956 | 14 | 76 | 114 |
| `XML/Yami/Kalaku3.xml` | E. | Saman Kalaku, 13 September 1956 | 11 | 56 | 89 |
| `XML/Yami/Kalaku4.xml` | F. | Saman Sunagu, January 1957 | 24 | 161 | 186 |

Text F was given by Saman Sunagu. Its historical `Kalaku4` filename and TEXT ID remain unchanged.

## Source fidelity and alternatives

The source audit accounts for all 22 pages and applies the publication's errata. It restores printed Kwaway sentence 40, preserves the source's partial word and morpheme analysis, and types later same-language gloss readings with `ver="alt"`. Missing glosses or morphemes are not invented.

Eighteen printed slash expressions are expanded into 37 fully aligned variants under POL-027. Each output sentence contains only its own FORM, W/M analysis, and source glosses. The 171 primary S IDs remain stable. Published `Kwaway/S48b` is also retained; 18 genuinely new variants use deterministic `v2` or `v3` suffixes. `public_id_ledger.json` preserves inherited W/M IDs wherever a source-faithful successor exists. It also records seven retired child IDs whose fused or errata-replaced structures have no source-faithful successor.

Parentheses remain where the source key marks probable discrepancies. The `?` character is a source letter, not a sentence-level marginality marker or punctuation to strip.

## Derived tiers

The source orthography has not been identified, so no modern conversion is asserted. `standardize.py --copy` creates a utility standard FORM that exactly matches every source-owned original FORM. No PHON tier is published because the tested profiles are not approved for this historical transcription.

## Reproduction and evidence

The public package is derived from the authoritative private revision recorded in `source_manifest.json`. Rebuild and validate it from the repository root with:

```bash
WAKELIN_PYTHON=.venv/bin/python \
  Corpora/WakelinTexts/CodeAndDocs/scripts/reproduce.sh
```

The script verifies the source PDF hash, expands the recorded alternatives, applies the public ID ledger, generates XML, runs the canonical cleaner, creates copied standard tiers, and validates source fixtures and exact counts. A second run is byte-identical.

`CodeAndDocs/pre_correction_snapshot/` is retained unchanged as historical POL-035 evidence from the earlier hand-entered publication. It is no longer an active source because the reviewed `source_records.json` and its deterministic builder now reproduce the corpus directly.

See `CodeAndDocs/QC_SUMMARY.md` for the final source, validator, duplicate, privacy, and port-readiness evidence. The reconciliation follows POL-001, POL-002, POL-003, POL-022, POL-025, POL-027, POL-030, POL-035, POL-036, POL-037, and POL-038.

## Known source-backed findings

- Kwaway S36 and S40 are identical, independently printed narrative records and are both retained under POL-022.
- The source supplies selective morpheme analysis and some words without glosses. Validators report those as reviewed soft findings; the corpus does not manufacture missing analysis.

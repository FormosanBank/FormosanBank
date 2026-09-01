# Rau and Dong 2006 QC summary

## Scope

This review covers only the 20 Yami texts published by Rau and Dong in 2006. It does not add material from the 2018 grammar or any other later source.

## Source authority

- D. Victoria Rau and Maa-Neu Dong. 2006. *Yami texts with reference grammar and dictionary*. Institute of Linguistics, Academia Sinica.
- Official record: <https://www.ling.sinica.edu.tw/item/en?act=publish_book&bookID=80&code=view>
- Official full-book PDF checked on 2026-08-22: 704 pages, SHA-256 `dc299560557deb70aa11d21a0dff4da009be6348fb1fc7dd4c2ea192ffa9efbc`
- The text section is PDF pages 153 through 467, inclusive. The temporary 315-page audit slice had SHA-256 `54c73a9f44f87915bb2aa63599b1dcefec95f1fb61b17f4ab02407e7952b09bf`.

The source PDF is not vendored. The existing copyright and license terms are unchanged.

## Audited inventory

| Item | Count |
| --- | ---: |
| XML files | 20 |
| S elements | 794 |
| W elements | 13,295 |
| M elements | 16,731 |

Every XML sentence was matched to the official 2006 text section with `audit_gloss_scrape.py` at the default threshold of 82. The extractor reported 9,841 lines, 18,067 matchable candidates, 794 of 794 XML sentences matched, and 0 unmatched. The PDF layout did not expose reliable numbered-example regions, so the audit makes no source-region completeness claim beyond the complete XML-to-source sentence match.

The one duplicate sentence group is present twice in the source, at printed examples 23 and 55 in text 16. It is retained.

## Remediation

Both PHON tiers were regenerated from their FORM tiers with the current central generator:

```bash
python QC/utilities/add_phonology.py \
  --corpora_path Corpora/RauDong/XML \
  --orthography Ortho94
```

- Original PHON uses `Orthographies/Ortho94/Yami.tsv`, which reproduces the source-era phonetic mapping.
- Standard PHON uses `Orthographies/Ortho113/Yami.tsv`, selected by `standards.csv`.
- 12,212 original PHON and 12,569 standard PHON elements changed.
- All 31,984 legacy `o~u` occurrences became canonical `[o|u]` groups.
- PHON punctuation and segmentation markers were removed by the current generator.
- The regenerated original PHON matches every prior original PHON after only legacy variant notation and non-phonetic punctuation or segmentation markers are normalized. There were no phonetic mapping disagreements.
- IDs, metadata, FORM, TRANSL, W, and M content were unchanged.

`CodeAndDocs/scripts/reproduce.sh` applies the existing standard-tier accent normalization and this PHON regeneration. The corpus-specific tests verify the 2006-only inventory and every generated PHON value.

## Validation record

Current validators report no corpus-blocking findings. Expected soft findings are retained instead of changing source content by inference:

- `V122`: 205 source-faithful parentheses or slashes in translations.
- `V061`: 66 W-to-M count warnings. Of these, 61 reflect the source's infix and split-root notation, such as `k-om-an` represented by M forms `om` and `k:an`. Five involve explicit `UNK` M placeholders where the source word and gloss cannot be aligned into individual morphemes without analysis not supplied by the source.
- `V068`: 9 reconstruction warnings, all caused by those same explicit `UNK` M placeholders.
- `G012`: 1 source-faithful parenthetical in a Chinese free translation.
- Duplicate validation: 1 source-attested within-file group on both original and standard tiers.

The explicit `UNK` entries remain visible because replacing them would require an unrecorded linguistic analysis. They are not treated as reconstructed source data.

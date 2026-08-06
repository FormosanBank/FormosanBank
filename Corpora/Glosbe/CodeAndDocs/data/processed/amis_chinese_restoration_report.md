# Amis Chinese Restoration

Reviewed source: `work/reference_glosbe/amis_glosbe_traditional.xml`

Reviewed source SHA-256: `2a0a0a03f849332e84e8e191ed9d3fbf0ce656d31acf5045e8d757b80596a764`

Contributor: Joseph Lin ([source pull request](https://github.com/FormosanBank/Formosan-Glosbe/pull/1))

## Result

- Historical input rows: 5860
- Unique historical Amis-Traditional Chinese pairs: 2321
- Exact historical duplicate rows omitted: 3539
- Current scrape rows: 25
- Current rows matched to Joseph's reviewed conversions: 25
- New current rows converted with `chinese-converter==1.1.1`: 0
- Final unique Amis-Traditional Chinese pairs: 2321
- Final sentence elements: 2296

## Merge Rules

1. Preserve every distinct Traditional Chinese translation from Joseph's reviewed file.
2. Collapse only exact duplicate Amis-translation pairs. Distinct translations for the same Amis form remain as `ver="alt"` translations on one sentence element.
3. Prefer the newer scrape row when its converted translation matches a reviewed pair after punctuation-insensitive comparison.
4. Convert only current rows that have no reviewed counterpart. Simplified Chinese is not emitted in final XML.
5. Remove Glosbe asterisk footnote markers from both aligned tiers.

Row-level provenance is in `data/processed/amis_chinese_restoration_audit.csv`.

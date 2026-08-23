# QC summary

## Scope and result

This reconciliation updates only the three Montgomery 1962 Amis texts already present in the public `MontgomeryTexts` corpus. The result contains 3 XML files, 37 source-numbered sentences, 351 word elements, and no morpheme or audio elements.

No record from another collection is included in the source ledger, XML, metadata, or package.

## Source evidence

The checked source is the five-page `Original.pdf` already stored with this public corpus. It is 874,535 bytes with SHA-256 `7a9ad6482f4d1c38a45e2ba50b4a037155d4e771ce4586d64f06852e8bf8e2bd`, matching the development source manifest.

The four content pages were reviewed visually. They contain 37 numbered examples and three unnumbered titles. The titles are headings rather than sentence records. The scan also confirms the printed Silo form `mi-salrama`, which replaces the unsupported public normalization `mi-salama`.

## Stable identifiers and tiers

All three public TEXT IDs, all 37 surviving S IDs, and all 351 surviving W IDs are unchanged from public commit `3a3c47c220520113f747e6a2d441494000e13c4b`. Only the title-heading ID `S1` is removed from each file. Surviving records are not renumbered.

The previous unpinned PHON tiers are removed. Standard FORM tiers copy the historical original FORM because no source-specific standardization or phonology profile is approved. The source does not provide an M analysis, so none is invented.

## Validation

| Check | Result |
|---|---|
| XML validator | 0 findings |
| Text validator | 47 source-notation soft findings, 0 hard |
| Gloss validator | 172 source-tiering soft findings, 0 hard |
| Duplicate sentences | 0 groups in original and standard tiers |
| Port readiness | 0 hard, 0 warnings |
| Corpus tests | 5 passed |
| Full repository suite | 1,025 passed, 4 skipped |
| Ruff and shell syntax | passed |
| Statistics | 3 files, 37 sentences, 351 words, 0 parse errors |

The specialized gloss-scrape audit is not a gate for this source's lexical word tier. Its G001 and G002 rows treat hyphens in lexical translations as morpheme-boundary notation, but this publication provides no M analysis. Its G020 rows are an extraction limitation: the four content pages are image-only scans, so `pdfplumber` extracts page headers rather than the examples and G023 self-reports that limitation. Source coverage rests on the page ledger, source records, direct fixtures, and visual review.

## Reproduction

`scripts/reproduce.sh` verifies the source PDF hash, rebuilds the three XML files from `source_records.json`, runs the canonical cleaner, and creates copied standard tiers. `public_id_ledger.json` records the stable-ID mapping.

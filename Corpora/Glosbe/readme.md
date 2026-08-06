# Glosbe Formosan Corpus

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

The published corpus contains Glosbe lexical and translation-memory material for Amis, Atayal, Saisiyat, and Truku. The XML includes English translations and restored Traditional Chinese translations for Amis.

## Restored Amis Chinese

The newer Glosbe scrape retained only 25 Amis-Chinese rows because its build path did not merge the earlier reviewed conversion. This update restores the Traditional Chinese file contributed by Joseph Lin in [Formosan-Glosbe PR #1](https://github.com/FormosanBank/Formosan-Glosbe/pull/1) and makes the merge reproducible.

Restoration result:

- 5,860 historical input rows
- 2,321 distinct Amis-Traditional Chinese translations
- 2,296 sentence elements
- 3,539 exact duplicate historical rows omitted
- 25 distinct alternate translations retained with `ver="alt"`
- all 25 rows from the newer scrape matched Joseph's reviewed conversions

The build preserves every distinct reviewed translation and removes only exact Amis-translation duplicates. It converts a current Simplified Chinese row only when no reviewed Traditional Chinese counterpart exists. No new conversion was needed for the current 25 rows.

## ILRDF Reference Audit

The files previously described as the "Zheng dictionary" are ILRDF dictionary data curated and repackaged by Zheng et al. They are not an independent lexical source. The comparison applies only to Glosbe dictionary and headword candidates. It does not filter sentence-level translation-memory data, including the restored Amis-Chinese sentences.

The corrected policy uses the selected ILRDF-derived files as reference metadata:

- every structurally valid Glosbe source-target pair is retained
- exact source-form overlap and the Chinese-to-English mapping are recorded only as review signals
- distinct targets for one source form are preserved as separate translations, with `ver="alt"` after the first
- missing, wrong-language, or non-ILRDF reference files stop the audit instead of silently producing non-matches
- `trv` uses the Truku reference file only; Seediq is not mixed into the comparison

Final lexical result:

- 1,319 deduplicated candidates
- 1,305 retained translations in 1,156 sentence elements
- 149 alternate translations
- 14 concrete structural or cross-reference rejections
- 0 exclusions based on ILRDF absence or gloss mapping

Reference status is informational: 529 translations have an unattested source form, 528 have no applicable gloss mapping, 209 are mapping-supported, and 39 map to a different reference sense. All four statuses remain in XML. See `CodeAndDocs/data/processed/ildrf_glosbe_lexical_audit_report.md` for provenance, reference-file hashes, rule definitions, and pair counts.

## Reproducibility

The canonical development repository is [FormosanBank/Formosan-Glosbe](https://github.com/FormosanBank/Formosan-Glosbe). `CodeAndDocs/` preserves the current pipeline, configuration, reviewed Amis-Chinese source file, tests, and compact audit evidence used for this publication. The older one-off workflow remains under `CodeAndDocs/work/scripts/` for historical context.

The published copy of `scripts/config.yaml` writes generated XML to `../XML`, matching this repository's standard corpus layout. The development repository uses its own `Final_XML` directory.

For a full rebuild, clone `Formosan-Glosbe` and `Formosan-Zheng-ACL-2024` as siblings, retain the private Glosbe crawl cache and processed sidecars in the development repository, then run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/glosbe_pipeline.py rebuild_lexical_reference_audit --config scripts/config.yaml
python scripts/glosbe_pipeline.py validate_formosanbank_xml --config scripts/config.yaml
```

Run the full rebuild in the development repository, not from this published checkout. It requires the private Glosbe crawl cache, processed sidecars, and the sibling `Formosan-Zheng-ACL-2024` reference repository. Those inputs are not published. The public port retains the reviewed source, row-level restoration and lexical-policy evidence, compact reports, final XML, reference hashes, and concrete rejection list. Adjust `ildrf_reference_lexicon.derived_repo` in `scripts/config.yaml` if the reference repository is elsewhere.

Key evidence files:

- `CodeAndDocs/data/processed/amis_chinese_restoration_report.md`
- `CodeAndDocs/data/processed/amis_chinese_restoration_audit.csv`
- `CodeAndDocs/data/processed/final_xml_translation_audit_report.md`
- `CodeAndDocs/data/processed/ildrf_glosbe_lexical_audit_report.md`
- `CodeAndDocs/data/processed/ildrf_glosbe_lexical_audit.csv`
- `CodeAndDocs/data/processed/lexical_xml_rejected.csv`

The full final-XML row audit and grouped ILRDF review are generated development-side artifacts. Their compact results are retained in the published reports; the complete files remain in the development repository's QC output.

## Rights and Source Notes

FormosanBank records project-owner permission to scrape Glosbe for this work. Glosbe content can include third-party translation-memory sources, so users must also follow the source-corpus rights and the central FormosanBank terms.

## Acknowledgments

- Joseph Lin prepared the reviewed Traditional Chinese conversion restored here.
- Glosbe and its contributors provided the dictionary and translation-memory source material.

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

## Zheng Lexical Audit

The Zheng comparison applies only to Glosbe dictionary and headword candidates. It does not filter sentence-level translation-memory data, including the restored Amis-Chinese sentences.

The audit uses Zheng as corroborating evidence:

- a source form missing from Zheng is excluded from lexical XML under the conservative publication policy, but it is not declared linguistically wrong
- a target is excluded when Zheng attests the source form but its mapped gloss supports a different sense
- source and sense matches are retained, and multiple supported targets are merged
- a single Glosbe target is retained when the Zheng source is attested but no curated Chinese-to-English sense rule applies

The current audit covers 1,305 Glosbe lexical candidates. It retains 729 candidate rows, excludes 576 under the policy, and emits 667 merged lexical entries. See `CodeAndDocs/data/processed/zheng_glosbe_lexical_audit_report.md` for the rule definitions and counts.

## Reproducibility

The canonical development repository is [FormosanBank/Formosan-Glosbe](https://github.com/FormosanBank/Formosan-Glosbe). `CodeAndDocs/` preserves the current scripts, configuration, reviewed source file, tests, and audit sidecars used for this publication. The older one-off workflow remains under `CodeAndDocs/work/scripts/` for historical context.

From `Corpora/Glosbe/CodeAndDocs`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/build_formosanbank_xml.py --config scripts/config.yaml
python scripts/validate_formosanbank_xml.py --config scripts/config.yaml
python scripts/audit_final_xml_translations.py
```

The Zheng lexical rebuild expects `Formosan-Zheng-ACL-2024` as a sibling clone of the public FormosanBank repository. Adjust `trusted_lexicon.zheng_repo` in `scripts/config.yaml` if the repositories are elsewhere.

Key evidence files:

- `CodeAndDocs/data/processed/amis_chinese_restoration_report.md`
- `CodeAndDocs/data/processed/amis_chinese_restoration_audit.csv`
- `CodeAndDocs/data/processed/final_xml_translation_audit_report.md`
- `CodeAndDocs/data/processed/final_xml_translation_audit.csv`
- `CodeAndDocs/data/processed/zheng_glosbe_lexical_audit_report.md`

## Rights and Source Notes

FormosanBank records project-owner permission to scrape Glosbe for this work. Glosbe content can include third-party translation-memory sources, so users must also follow the source-corpus rights and the central FormosanBank terms.

## Acknowledgments

- Joseph Lin prepared the reviewed Traditional Chinese conversion restored here.
- Glosbe and its contributors provided the dictionary and translation-memory source material.

# Glosbe Formosan Corpus

## License and AI Use

This corpus is subject to its source terms and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI use is prohibited without prior written permission.

## Scope

The corpus contains Glosbe lexical and translation-memory material for Amis, Atayal, Saisiyat, and Truku. Eight canonical XML files contain 7,609 sentence elements and 7,830 translations. Most translations are English. The Amis collection also includes reviewed Traditional Chinese translations.

The XML uses ISO 639-3 directories and keeps lexical entries separate from translation-memory examples. Each source record has an original FORM. FormosanBank tooling adds the standard FORM and PHON tiers.

## Restored Amis Chinese

The Amis-Chinese build merges the current scrape with the Traditional Chinese file contributed by Joseph Lin in [Formosan-Glosbe PR #1](https://github.com/FormosanBank/Formosan-Glosbe/pull/1). It preserves every distinct reviewed translation and removes only exact source-translation duplicates.

The historical input contains 5,860 rows and 2,321 distinct Amis-Traditional Chinese pairs. Current normalization removes 15 additional pairs that become exact duplicates. After the shared duplicate policy, canonical XML contains 2,305 translations in 2,295 sentence elements, including 10 alternate translations.

## ILRDF Reference Audit

The lexical audit compares Glosbe headwords with ILRDF dictionary data distributed through the Zheng et al. ACL 2024 dataset. This is reference metadata, not an independent lexical source. It never excludes an otherwise valid Glosbe row.

The final lexical set contains 1,305 translations in 1,156 sentence elements, including 149 alternate translations. Fourteen candidates were rejected for concrete structural or cross-reference failures. The retained reference statuses are 529 source forms not attested, 526 attested with no applicable gloss mapping, 210 mapping-supported targets, and 40 targets mapped to another sense.

The audit selects reference files explicitly. In particular, `trv` uses the Truku file only, because Truku and Seediq share the same XML language code.

## Reproducibility

`CodeAndDocs/` contains the compact reviewed build boundary rather than the 233 MB crawl cache. It includes:

- 4,245 quality-filtered translation-memory records
- 1,319 deduplicated lexical candidates
- the reviewed Amis-Chinese inputs
- the build and validation code
- file hashes and pinned repository commits in `source_manifest.json`

The raw HTML, request headers, logs, and quarantined legacy XML are intentionally excluded. The retained records preserve source URLs, record IDs, and raw-source hashes.

To rebuild, install `CodeAndDocs/requirements.txt`, check out the pinned FormosanBank and Formosan-Zheng-ACL-2024 commits recorded in `source_manifest.json`, then run:

```bash
export FORMOSANBANK_AUTHORITY=/path/to/FormosanBank-at-3a3c47c
export GLOSBE_ILRDF_REFERENCE_REPO=/path/to/Formosan-Zheng-ACL-2024-at-face1e1
export FORMOSANBANK_PYTHON=/path/to/python3
Corpora/Glosbe/CodeAndDocs/reproduce.sh
```

The script rebuilds source XML, applies the pinned FormosanBank cleaner, standardizer, duplicate policy, and phonology tools, then runs the corpus validator and tests. It aborts if either authority checkout is at the wrong commit.

## Source and Processing Notes

- Glosbe is crowdsourced, so linguistic accuracy and entry-level rights can vary. Treat entries as review leads rather than expert-verified dictionary records.
- Dialect is unknown for Amis, Atayal, and Saisiyat. The `trv` files are identified as Truku.
- Distinct translations for one source form are retained as separate TRANSL elements, with `ver="alt"` after the first.
- The standard tier uses FormosanBank Ortho113 conventions. The original tier preserves source spelling after documented Unicode, punctuation, and footnote-marker cleanup.
- Glosbe and its contributors or named source corpora remain the content sources and rights holders recorded in the XML.

## Publication Authorization

On 2026-08-23, the FormosanBank maintainer authorized public FormosanBank publication of this existing Glosbe corpus update. That project authorization does not relicense Glosbe or third-party translation-memory material. Downstream users must follow the source terms, source-corpus rights, attribution requirements, and central FormosanBank terms.

## Citation

In addition to FormosanBank, cite Glosbe for the language pair and retrieval date recorded in each XML file:

Glosbe. (2026). *Glosbe [language]-[translation language] dictionary and translation memory*.

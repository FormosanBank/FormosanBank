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

## Cleaning and Quote Correction

Before standardization, a shared cleaning pass normalizes punctuation and
Unicode debris in the original tier and translations: dash look-alikes
(em/en dashes) become `-`, non-breaking spaces become spaces, and HTML
entity residue is decoded. The source spelling is not changed.

**Notes for data users:**

- In the Amis files, the letter `'` (the glottal stop) is also used by the
  source as a quotation mark. Disambiguating apostrophe vs. quotation mark
  in the Amis data was done **automatically** (a classifier compares each
  sentence against its translations and an attested-word list and rewrites
  apostrophes it judges to be quotation marks to `"`). Occasional false
  positives are possible and misses are certain — some real quotation
  marks remain written as `'`, and a few glottal-stop letters may have
  been rewritten to `"`.
- Every correction is logged with the full before/after sentence text in
  [`CodeAndDocs/quote_corrections.csv`](CodeAndDocs/quote_corrections.csv).
- The XML exactly as it was before any automated correction first touched
  it is preserved in `CodeAndDocs/pre_correction_snapshot/`. Because the
  initial scrape cannot be re-run (see [Reproducibility](#reproducibility)),
  that snapshot is the pre-correction baseline.
- Atayal and Saisiyat go through the same classifier; it made no changes
  there. Truku contains no apostrophes and is not evaluated.

## Standardization and Phonology

Each `<S>` carries three sentence-tier layers: `FORM kindOf="original"` (the source spelling, cleaned as described above), `FORM kindOf="standard"` (FormosanBank's Ortho113 orthography), and `PHON` (IPA) on **both** tiers.

Glosbe is crowd-sourced, so the dialect of each entry is generally unknown and a single file likely mixes dialects. We therefore assumed the following source orthographies and standardized each language to Ortho113:

| Language | Source orthography | Conversion table / column | Dialect assumption |
| --- | --- | --- | --- |
| Amis (`ami`) | Ortho94 | `Amis_94_113.tsv`, non-Southern (`Coastal`) column | dialect unknown; the non-Southern columns are identical and the source is `f`/`o`-dominant (not Southern). Net effect: `u`→`o` |
| Atayal (`tay`) | Church | `Atayal_Church_113.tsv` (single `standard` column) | dialect unknown; the Church table is dialect-agnostic |
| Truku (`trv`) | Ortho94 | `Seediq_94_113.tsv`, `Truku` column | `dialect="Truku"` (Truku, not Seediq) |
| Saisiyat (`xsy`) | Ortho94 | `Saisiyat_94_113.tsv` (single `standard` column) | single dialect |

No Formosan orthography uses accents phonemically, so accents (e.g. Glosbe's stress marks on Truku `dálix`) are **deleted from the standard tier** during standardization; the original tier keeps them exactly. IPA is generated for the standard tier from `Orthographies/Ortho113/<Language>.tsv` (including that language's dialect-scoped pronunciation rules, e.g. Truku's) and for the original tier from the source orthography above. For the unknown-dialect Amis and Atayal originals, a `default` column in `Orthographies/Ortho94/Amis.tsv` and `Orthographies/Church/Atayal.tsv` supplies the IPA.

## Rebuilding the XML

[`CodeAndDocs/make_xml.sh`](CodeAndDocs/make_xml.sh) reruns the whole
post-scrape pipeline over `XML/` — everything derived from the published
original tier. Its steps, in order:

1. **Cleaning + quote correction** (`QC/cleaning/clean_xml.py` over
   `XML/`): the punctuation/Unicode cleanup and the Amis
   apostrophe-vs-quotation-mark correction described above. New
   corrections append to `CodeAndDocs/quote_corrections.csv`.
2. **Standardization** (`QC/utilities/standardize.py`, once per language):
   rebuilds the standard tier from the cleaned original tier using the
   conversion tables in the table above; strips accents from the standard
   tier only.
3. **Phonology** (`QC/utilities/add_phonology.py`, once per language):
   regenerates IPA on both tiers (standard from Ortho113, original from
   the source orthography).

Run it from anywhere; it locates the FormosanBank repo from its own path.
Set `PYTHON` to override the interpreter (defaults to the repo `.venv`)
and `BANK` to point at a different FormosanBank checkout:

```bash
PYTHON=/path/to/python Corpora/Glosbe/CodeAndDocs/make_xml.sh
```

All steps are idempotent; rerunning the script is safe.

## Reproducibility

The former development repository [FormosanBank/Formosan-Glosbe](https://github.com/FormosanBank/Formosan-Glosbe) is deprecated; the corpus is now maintained here. `CodeAndDocs/` preserves the current pipeline, configuration, reviewed Amis-Chinese source file, tests, and compact audit evidence used for this publication. The older one-off workflow remains under `CodeAndDocs/work/scripts/` for historical context.

Reproducibility is partial, by layer:

- **Cleaning, standard tier, and both-tier phonology** — fully reproducible from the published `original` tier with [`CodeAndDocs/make_xml.sh`](CodeAndDocs/make_xml.sh) (see [Rebuilding the XML](#rebuilding-the-xml) above).
- **Restored Amis-Chinese translations** — reproducible from the committed reviewed source (`CodeAndDocs/work/reference_glosbe/amis_glosbe_traditional.xml` and `work/json/`), which the pipeline merges into the `ami/zh` translation memory.
- **The initial scrape** (Glosbe lexical and English translation-memory rows) — **not** reproducible from this checkout. It is a retained snapshot of a 2026 Glosbe crawl; the raw crawl cache and processed `.jsonl` sidecars are not published, and the former development repository is deprecated. Re-crawling Glosbe would yield different data. `CodeAndDocs/pre_correction_snapshot/` therefore preserves the XML as it stood before automated corrections first modified it.

The lexical ILRDF audit (`glosbe_pipeline.py rebuild_lexical_reference_audit`) additionally requires the sibling `Formosan-Zheng-ACL-2024` reference repository; adjust `ildrf_reference_lexicon.derived_repo` in `scripts/config.yaml` if it is elsewhere. `config.yaml` writes generated XML to `../XML`, matching this repository's standard corpus layout.

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

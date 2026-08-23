# ePark

This corpus contains educational material from [族語E樂園](https://web.klokah.tw/), maintained by the Indigenous Languages Research and Development Foundation. It has 285,346 sentence records in 436 XML files and covers 42 named varieties across 16 FormosanBank language labels. Truku and Seediq share ISO 639-3 code `trv` but are routed separately in FormosanBank.

## License and attribution

The source's [official licensing page](https://web.klokah.tw/creativeCommons/) releases site content under CC BY-NC-SA 4.0, subject to its listed exceptions. The source sections represented here are not among the named exceptions for self-authored teaching materials, the audiovisual center, or twelve-year curriculum materials.

Each XML file records the source, citation, and `CC-BY-NC-SA` rights label. Reuse must preserve attribution, noncommercial use, and share-alike terms. The corpus is also subject to the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI use requires prior written permission.

## Source coverage

The public reproduction inputs are under `CodeAndDocs/`:

- `ePark_1/`: 145,209 CSV rows from the nine-level materials
- `ePark_2/`: 182,449 CSV rows from six educational sections
- `ePark_3/`: 48,503 source XML items and 22,692 source CSV rows from sentence-pattern, picture-story, and picture-book sections

`CodeAndDocs/source_audit.py` maps every included sentence to a source file and row or item. The audited parser reconstructs 217 malformed CSV rows whose unescaped source commas created extra columns. It intentionally excludes 115 blank ePark 3 rows, 140 translation-only ePark 3 rows, and 33 empty ePark 3 XML items.

The source review also excludes 126,239 ePark 1 word rows because their segmentation, translations, and audio alignment are unreliable. No W or M tiers are published. Original FORM and TRANSL values remain source-owned, subject only to FormosanBank quote normalization and removal of source annotation asterisks. Standard FORM and standard PHON are generated with the pinned FormosanBank tools. The source does not supply authoritative original PHON.

TEXT IDs use `{topic_slug}_{dialect}`. Sentence IDs preserve the source record identifier within each TEXT. The refresh retains the same 436 TEXT IDs and 285,346 sentence IDs as the prior public package.

## Audio

The corpus has 264,642 source-verified AUDIO references. All ePark 1 sentence audio is excluded because its alignment is unreliable. Another 1,734 source audio candidates are omitted because no usable downloaded file was available. `CodeAndDocs/audio_inventory.tsv.gz` records the complete 266,376-candidate review, including 96 retained references for which the source inventory did not provide a duration.

Download the published audio package with:

```bash
bash download_audio_data.sh
```

## Reproduction

The canonical workflow is pinned to FormosanBank commit `3a3c47c220520113f747e6a2d441494000e13c4b` and private development commit `e891e4a67cdf230c7afb38c8066670d6991980ef`.

From `Corpora/ePark/`, run:

```bash
python3 -m unittest discover -s CodeAndDocs/tests
bash CodeAndDocs/reproduce.sh
```

The script builds in a temporary directory, runs the pinned cleaner once, restores source-owned tiers, generates standard FORM and standard PHON, runs source and XML validation, and requires all 436 reproduced XML files to match `XML/` byte for byte. It uses the enclosing FormosanBank checkout when its `QC/` and `Orthographies/` trees match the pinned authority. Set `EPARK_AUTHORITY` to another checkout when needed. Set `EPARK_PYTHON` to select a Python 3 environment with the FormosanBank requirements installed.

Audit and QC logs are external review artifacts and are not committed. The final development audit found zero source-alignment defects, and the current QC verdict is `ready to port`.

# Formosan-RauDong

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

This corpus contains only the 20 glossed texts from the 2006 publication:

Rau, D. V., and Dong, M. N. (2006). *Yami texts with reference grammar and dictionary*. Institute of Linguistics, Academia Sinica.

The initial conversion to machine-readable XML is not reproducible from files in this repository. The current PHON normalization is reproducible, and the committed sentences were checked against the [official open-access book](https://www.ling.sinica.edu.tw/item/en?act=publish_book&bookID=80&code=view). See [CodeAndDocs/QC_SUMMARY.md](CodeAndDocs/QC_SUMMARY.md) for the source-alignment and validation record.

## Processing

### Removing lexical accent from the standard tier

Rau & Dong (2006) mark lexical accent with an acute accent on vowels (`á é í ó`). This is faithful to the source, so it is retained in the `original` tier, but FormosanBank's common orthography does not write the accent, so it is stripped from the `standard` tier. [CodeAndDocs/remove_accents.py](CodeAndDocs/remove_accents.py) removes the acute accent from every `FORM kindOf="standard"` element (at the S, W, and M levels), leaving the `original` tier and all `PHON`/`TRANSL` elements untouched. It edits the XML in place using the same lxml serialization as the QC tooling, so the only change is the removed accents.

```bash
python CodeAndDocs/remove_accents.py            # defaults to ../XML
python CodeAndDocs/remove_accents.py --corpora_path <dir>
```

### Regenerating phonology

The original tier follows the Yami profile from the 1994 official orthography, matching the source-era transcription. The standard tier follows the current 2024 official orthography. Both are generated with the repository's current PHON rules, including marker-free output and canonical `[o|u]` variant notation.

```bash
bash CodeAndDocs/scripts/reproduce.sh
```

The script removes lexical accents from standard FORM tiers and regenerates original and standard PHON tiers. It does not alter IDs, source forms, translations, W tiers, or M tiers.

## References

Rau, D. V., and Dong, M. N. (2006). *Yami texts with reference grammar and dictionary*. Institute of Linguistics, Academia Sinica.


## License

The copyright holder made this corpus available CC BY-NC.

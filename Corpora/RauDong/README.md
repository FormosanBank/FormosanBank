# Formosan-RauDong

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited without prior written permission.

This repository contains the 20 glossed texts from 

Rau, D. V., and Dong, M. N. (2006). Yami texts with reference grammar and dictionary. Institute of Linguistics, Academia Sinica.

The nature of how the machine-readable version was obtained is such that we do not have a reproducible pipeline. 

## Processing

### Removing lexical accent from the standard tier

Rau & Dong (2006) mark lexical accent with an acute accent on vowels (`á é í ó`). This is faithful to the source, so it is retained in the `original` tier, but FormosanBank's common orthography does not write the accent, so it is stripped from the `standard` tier. [CodeAndDocs/remove_accents.py](CodeAndDocs/remove_accents.py) removes the acute accent from every `FORM kindOf="standard"` element (at the S, W, and M levels), leaving the `original` tier and all `PHON`/`TRANSL` elements untouched. It edits the XML in place using the same lxml serialization as the QC tooling, so the only change is the removed accents.

```bash
python CodeAndDocs/remove_accents.py            # defaults to ../XML
python CodeAndDocs/remove_accents.py --corpora_path <dir>
```

## References

Rau, D. V., and Dong, M. N. (2006). Yami texts with reference grammar and dictionary. Institute of Linguistics, Academia Sinica.


## License

The copyright holder made this corpus available CC BY-NC.
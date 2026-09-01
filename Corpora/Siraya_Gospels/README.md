# Siraya Gospels of Gravius

## License and AI use

This corpus is subject to its source rights and the central FormosanBank terms in [LICENSE.md](../../LICENSE.md) and [AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI use is prohibited without prior written permission.

The 1661 Gravius Gospels, the King James Bible, and the Chinese Union Version materials used here are public domain.

## Source and contents

Daniël Gravius and Anthonius Hambrouck. 1661. *Het Heylige Euangelium Matthei en Johannis*. Amsterdam: Michiel Hartogh.

The corpus contains the printed Siraya verse columns from Matthew and John:

- Matthew: 28 chapters and 1,071 verse units
- John: 21 chapters and 880 printed verse units
- Total: 49 XML files and 1,951 sentence records

All 1,951 Siraya forms were reviewed against 314 rendered scan pages. Chapter-level and corpus-level hashes protect the completed review. The accompanying source ledger records the printed locator and page range for every sentence.

The Dutch parallel columns and book or chapter headings are outside the reviewed verse-corpus scope. Earlier Dutch OCR was incomplete and unreliable, so it is not retained as corpus data.

## Translations

- English: 1,951 aligned King James Bible tiers from 1,950 reference units
- Mandarin: 1,947 aligned Chinese Union Version tiers and four documented source-edition omissions

Gravius divides modern John 1:38 into two printed verses. The English and Mandarin reference text is partitioned across source verses 38 and 39 without rewriting it.

## Orthography and identifiers

The `original` FORM preserves the historical printed Siraya spelling, punctuation, spacing, diacritics, and hyphenation. FormosanBank currently designates no Siraya standard orthography and has no `fos` phonology profile, so this corpus intentionally has no standard FORM or PHON tier.

The 49 published `TEXT/@id` values and all 1,951 verse IDs are preserved under POL-037. TEXT IDs follow `Siraya_Dutch_<Book>_Chapter<N>`; sentence IDs follow the printed `verse<N>` numbering within each chapter.

## Reproduction and QC

The public structured source snapshot, reference inputs, correction rules, source-review manifests, ledger, and generator are under `CodeAndDocs/`. Reproduce the XML with:

```bash
PYTHON=python3 Corpora/Siraya_Gospels/CodeAndDocs/reproduce.sh
```

The source scans are not distributed in FormosanBank. Their names, sizes, hashes, page scope, and full-review evidence are recorded under `CodeAndDocs/data/`.

The reconciliation completed private development audit on 2026-08-23 and uses FormosanBank tooling commit `3a3c47c220520113f747e6a2d441494000e13c4b`. Validation reports 0 HARD findings, 0 port-readiness HARD or WARN findings, no within-corpus original duplicates, and no cross-corpus original match against the other published Siraya corpus.

The remaining SOFT findings are expected and reviewed: no designated standard tier, source or reference parentheses, and no W/M segmentation.

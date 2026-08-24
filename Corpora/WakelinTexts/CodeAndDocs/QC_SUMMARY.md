# QC summary

## Scope and result

This PR reconciles only the six Wakelin et al. 1958 Yami texts already published in `Corpora/WakelinTexts`. The result contains 6 XML files, 190 aligned sentence variants from 171 printed source records, 926 W elements, 1,183 M elements, and no audio.

The public package is derived from private repository `FormosanBank/Formosan-Old_Texts` at commit `e1f52f43ab9e17b1d9a99329964b2ab64fbe864a`. That revision is source-faithful, reproducible, approved for publication, and has a current `ready to port` verdict against FormosanBank commit `3a3c47c220520113f747e6a2d441494000e13c4b`.

## Source and rights evidence

The checked source is the 22-page `Original.pdf` already stored with the public corpus. It is 1,006,822 bytes with SHA-256 `4ce50f141aa2f90ce97c19fff61454625a308846ac0df5d9632095ac65aa2083`, matching the private source manifest. Twenty-one content, translation, and errata pages are represented; the repository cover is excluded.

The FormosanBank maintainer confirmed publication rights on 2026-08-23. No open license is asserted. The XML notice is `All rights reserved; FormosanBank has permission to publish.`

## Source repairs and alternatives

- Restored printed Kwaway sentence 40, which was absent from the earlier top-level XML.
- Applied the publication's recorded errata without modernizing its historical transcription.
- Typed later same-language gloss readings with `ver="alt"` while preserving their text and order.
- Expanded 18 sentence-level slash decisions into 37 independently aligned variants under POL-027. No emitted S original FORM retains a slash alternative.
- Preserved parenthetical probable-discrepancy notation and ordinary slash notation below the S tier where the source does not define a sentence alternative.
- Preserved selective source W/M analysis and absent glosses. No missing morpheme, gloss, translation, or PHON is invented.

`source_records.json`, `alternative_expansions.json`, and `source_checks.csv` retain the exact source-owned content and nine direct fixtures across all six texts.

## Stable public identifiers

All six established TEXT IDs and all 171 primary S IDs remain unchanged. The previously published alternative `Kwaway/S48b` also remains unchanged. Eighteen new alternatives use deterministic `v2` or `v3` suffixes.

`public_id_ledger.json` applies 18 W/M overrides to preserve inherited public IDs when a source-faithful successor exists. Seven child IDs are explicitly retired: four belonged to a single fused Kalaku 3 alternative W/M structure that POL-027 replaces with three aligned W records, and three belonged to a Kalaku 4 morpheme analysis replaced by the publication's errata. Neither obsolete structure has a source-faithful successor. The breaking structural change is recorded rather than silently renumbered under POL-037.

## Derived tiers

The historical source orthography remains unidentified. The pinned pipeline uses `standardize.py --copy` to create 2,299 utility standard FORM tiers that exactly match the 190 S, 926 W, and 1,183 M original FORMs. No modern conversion is asserted. No PHON is committed because neither tested profile is approved for this exact transcription.

## Validation

| Check | Result | Disposition |
|---|---|---|
| XML validator | 453 V144 soft, 0 hard | The source provides selective M analysis; M children are not invented for 453 unparsed words inside otherwise parsed sentences. |
| Text validator | 563 V122 and 184 V133 soft, 0 hard | Parentheses and below-S slashes are source notation; copied standard FORMs retain source segmentation. |
| Gloss validator | 1 V060 and 3 V061 soft, 0 hard | Four documented source alignments do not match mechanical token or hyphen counts; source tiers are retained. |
| Dialect validator | 6 `tao` / `Yami` files | Passed. |
| Within-corpus duplicates | 1 group in original and standard | Kwaway S36 and S40 are independently printed narrative records and remain under POL-022. |
| Cross-corpus duplicates | 3 reported matches | All three match only the retained `CodeAndDocs/pre_correction_snapshot/` in this same corpus; no other published corpus matches. |
| Port readiness | 0 hard, 0 warnings | Passed. |
| Corpus tests | 7 passed | Exact source, variants, tiers, rights, counts, PDF, and stable-ID fixtures passed. |
| Full repository suite | 1,025 passed, 4 skipped | Passed. |
| Ruff, JSON, and shell syntax | passed | No findings. |
| Statistics | 6 files, 190 sentences, 925 counted words, 926 W elements, 0 parse errors | Regenerated successfully. |
| Privacy scan | 0 findings | No private directory, private-source file, credential pattern, or local absolute path is present. |

The validator counts and row-level dispositions match the private final QC evidence. All findings are source-backed and reviewed; none is unresolved.

## Reproduction

`scripts/reproduce.sh` verifies the public source PDF, rebuilds the six XML files from the checked ledgers, applies stable public IDs, runs the canonical cleaner, creates copied standard FORM tiers, and validates the complete result. Two consecutive runs produced aggregate XML SHA-256 `627a25c238299adea3077cb7e7e318adc49cb16465d9583d0b15811796d7b4d4`.

All non-ID XML content matches the private final across every file. Public TEXT IDs and recorded public child-ID exceptions are the only intentional differences.

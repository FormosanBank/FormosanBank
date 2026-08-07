# Exact standard-surface review

This review replaces the earlier marker-driven normalization with exact decisions keyed by record ID and expected source input.

## Source evidence

- Reader pages 31 through 44 give the current inventory with `ʉ`, `r`, and no `l`, and explain that `r` covers the former `l` and `r` values. This supports the current shared Ortho113 mapping `r -> r~ɾ`.
- The same section identifies acute vowels as stress notation rather than separate segments and says stress should not be written in standard orthography. Original forms therefore preserve acute vowels, while standard and alternate forms fold them to their base vowels.
- Reader page 193 defines `/` as separating pronunciation variants or forms whose roots vary under affixation. It defines `;` as separating related words or pronoun case forms. These are source-supplied lexical forms, not pieces to concatenate.
- Reader pages 81, 109, and 225 attest both `'akia` and the two-word surface `'akia na`. The dictionary entry `'akia (na)` therefore has those two exact outputs.
- Eleven Appendix 2A entries end in a hyphen. The source supplies bound citation forms, not unattached words. Per the reviewer decision of 2026-08-07, these entries are deleted from the published XML entirely: the dictionary ledger records each with `included=no` and an exclusion reason, and normalization verifies their absence. (An earlier revision retained them as original-only entries.)
- Reader page 190 defines the song hyphens as lyric divisions for fitting text to music. It separately defines the double hyphen as break punctuation.
- Reader page 69 prints `takananga` in sentence 4-9 but `takanaga=kasu` in its aligned analysis. Original tiers preserve both printed spellings. Only the analysis standard tiers resolve the non-Ortho113 `g` to `takananga=kasu` and `takananga=`.
- The song's word boundaries were not inferred by deleting every hyphen. `Formosan-LangShengSiQi-ALR` commit `40d89c1640f8cafec9576f3a748b13b07c770149`, raw HTML `data/raw/html/articles/year=108/mid=558/group=C_lang=15_no=1/col2.html`, independently attests `mati'ara'aravang`, `'aravang vatu`, and `tisa'ʉ ku 'apasʉ`. That file has SHA-256 `d5614078ea137b704a3f023cf589be26416266ee5ce0bba8e1ba35111ae8abc3`.

## Errors corrected

The earlier implementation recursively expanded any parentheses, split every slash or semicolon, removed any terminal hyphen, and removed every hyphen in the song. Three parts were unsafe.

1. `tisa'ʉku'apasʉ` incorrectly joined a verb, the pronoun `ku`, and `'apasʉ` “crab.” The exact standard is `tisa'ʉ ku 'apasʉ`.
2. The two punctuation examples were changed to colons. The source identifies the mark as break punctuation. An earlier revision used an em dash; per the reviewer decision of 2026-08-07, the source's typewriter `--` is meant as a single dash, corrected to `-` at build in the original tier so it carries through the standard and PHON tiers: `sumasima'ʉ-nguai` and `ikim-'atai`.
3. Eleven bound forms were turned into invented hostless words, such as `ara-` to `ara` and `'ap(a)-` to `'apa` or `'ap`. These entries are now excluded from the published XML altogether.

## Reproducible decisions

`intermediate/standard_surface_decisions.tsv` contains all 125 marked dictionary records and all three marked grammar records. Each row records:

- scope and stable record ID;
- source page;
- exact expected input after canonical cleaning;
- decision class;
- complete JSON output list, including an empty list when no surface exists;
- source evidence.

The runtime code does not split, expand, concatenate, or delete markers. It only applies the listed outputs after checking the record ID, source page, expected input, manifest counts, and complete marker-bearing record coverage.

Two additional analysis-tier standards are exact ID- and input-checked decisions for reader page 69. They are kept in code because they apply to W/M standard tiers rather than direct S surfaces. No original analysis form is changed.

Decision totals:

| Decision class | Records |
|---|---:|
| Slash variants | 100 |
| Semicolon lexemes or pronoun forms | 12 |
| Mixed slash and semicolon forms | 1 |
| Source-attested optional word | 1 |
| Bound forms with no unattached surface | 11 |
| Break punctuation | 2 |
| Lyric layout with independently attested boundaries | 1 |
| Total | 128 |

The resulting dictionary contains 870 published entries, each with exactly one direct standard form. Per the reviewer decision of 2026-08-07, the 114 records with source-defined multiple forms are split into separate S entries (IDs suffixed `a`, `b`, ... beyond the first) rather than carrying `alternate` FORM tiers; each split entry repeats the record's TRANSL and notes the printed apparatus on its original tier. Twenty-six split variants duplicate another record's form and translation — the source prints those forms as their own records (for example, the pronoun case-form lists in records 0070-0074 repeat the standalone pronoun entries, and record pairs such as 0209 `manguru / umanguru` and 0644 `umanguru / manguru` list each other's headword) — so the owning record keeps the form and the duplicate variant entry is dropped, leaving 228 entries from the split records (114 suffixed variants) and globally unique (form, translation) pairs. The 11 source-bound citation entries are excluded from the XML and documented in the ledger. The grammar contains 699 direct standard forms.

# Conversion-Table Audit Findings — 2026-08-09

First run of `QC/validation/validate_conversion_table.py` across all existing conversion tables.

## Summary counts

| Language | Scheme | Dialects | Exit | Confirmed | Warnings | Mismatches | Unknown-src | Untokenizable |
|---|---|---|---|---|---|---|---|---|
| Amis | 94 | 5 | 1 | 0–1 | 0 | 2–3 | 2 | 0 |
| Amis | Church | 5 | 1 | 1 | 0 | 2 | 5 | 1 |
| Amis | Huang | 5 | **0** | 2 | 0 | 0 | 0 | 0 |
| Amis | MinEd | 5 | 1 | 2 | 0 | 0 | 1 | 0 |
| Amis | Montgomery | 5 | 1 | 4–5 | 0 | 0–1 | 0 | 0 |
| Atayal | 94 | 6 | **0** | 0 | 0 | 0 | 0 | 0 |
| Atayal | Church | 6 | 1 | 1 | 0 | 0 | 1 | 0 |
| Bunun | Huang | 5 | **0** | 3 | 0 | 0 | 0 | 0 |
| Bunun | MinEd | 5 | 1 | 0–1 | 0 | 0–1 | 1 | 0 |
| Kanakanavu | MinEd | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| Kavalan | 94 | 1 | **0** | 0 | 0 | 0 | 0 | 0 |
| Paiwan | Church | 4 | **0** | 4 | 0 | 0 | 0 | 0 |
| Paiwan | Ferrell | 4 | 1 | 4 | 0 | 0 | 3 | 0 |
| Paiwan | MinEd | 4 | 1 | 1–2 | 0 | 0–1 | 0 | 0 |
| Puyuma | 94 | 4 | **0** | 0 | 0 | 0 | 0 | 0 |
| Puyuma | Folk | 4 | 1 | 3–4 | 0 | 2–3 | 1 | 0 |
| Puyuma | MinEd | 4 | 1 | 18–21 | 0 | 4–5 | 4–5 | 0–1 |
| Rukai | 94 | — | CRASH | — | — | — | — | — |
| Rukai | Church | — | CRASH | — | — | — | — | — |
| Rukai | Li | 6 | 1 | 5–7 | 0 | 0–2 | 8 | 1–2 |
| Rukai | MinEd | — | CRASH | — | — | — | — | — |
| Saaroa | MinEd | 1 | 1 | 1 | 0 | 1 | 1 | 0 |
| Saisiyat | 94 | 1 | **0** | 0 | 0 | 0 | 0 | 0 |
| Sakizaya | 94 | 1 | **0** | 0 | 0 | 0 | 0 | 0 |
| Seediq | 94 | — | CRASH | — | — | — | — | — |
| Seediq | Church | — | CRASH | — | — | — | — | — |
| Seediq | Ochiai | 4 | **0** | 1 | 0 | 0 | 0 | 0 |
| Thao | 94 | 1 | **0** | 0 | 0 | 0 | 0 | 0 |
| Thao | Li | 1 | **0** | 8 | 0 | 0 | 0 | 0 |
| Thao | MinEd | 1 | **0** | 0 | 0 | 0 | 0 | 0 |
| Tsou | Folk | 1 | **0** | 0 | 0 | 0 | 0 | 0 |
| Tsou | MinEd | 1 | **0** | 0 | 0 | 0 | 0 | 0 |
| Yami | 94 | 1 | **0** | 0 | 0 | 0 | 0 | 0 |
| Yami | MinEd | 1 | **0** | 0 | 0 | 0 | 0 | 0 |

**Result: 34 tables run; 16 exited nonzero (13 via report, 5 via crash/ValueError).**

Note: "Exit" for CRASH tables was actually 0 from the Python crash (uncaught ValueError), but they produced no report and are effectively broken. True blocking count is 18 (13 reported failures + 5 crashes).

## Profiles missing (skipped — cannot run)

| Conversion table | Reason |
|---|---|
| `Amis_113lib_113.tsv` | Self-mapping table (source = Ortho113); no source-scheme profile needed |
| `Kavalan_MinEd_113.tsv` | Source profile `Orthographies/MinEd/Kavalan.tsv` missing |
| `Pazeh_Tsuchida_113.tsv` | Output profile `Orthographies/Ortho113/Pazeh.tsv` missing |
| `Saisiyat_Tsuchida_113.tsv` | Source profile `Orthographies/Tsuchida/Saisiyat.tsv` missing |
| `Yami_Wakelin_113.tsv` | Source profile `Orthographies/Wakelin/Yami.tsv` missing |

## Notable findings

### 1. Dialect name mismatches cause crashes (5 tables)

Three Rukai tables (`Rukai_94`, `Rukai_Church`, `Rukai_MinEd`) and two Seediq tables (`Seediq_94`, `Seediq_Church`) crash with an uncaught `ValueError` because the dialect names in the conversion table header don't match those in the orthography profile.

- **Rukai_94**: table header has `"Dawu    Dona"` (a space-merged column — these should be two separate `Dawu` and `Dona` columns, tab-separated). The profile has both `Dawu` and `Dona` as separate columns.
- **Rukai_Church / Rukai_MinEd**: table has no `Dawu` column at all (only Wutai, Eastern, Dona, Wanshan, Maolin). The profile includes Dawu. This is a **table defect**: the Church and MinEd schemes may not distinguish Dawu, but the profile expects it.
- **Seediq_94 / Seediq_Church**: table headers use abbreviated names `Tgdaya` / `Toda`, while the Ortho94 profile uses `Tegudaya` / `Duda`. **Table defect**: abbreviated dialect names in the conversion table are inconsistent with the canonical profile dialect names.

**Classification:** All 5 crashes are **real table/profile defects** (naming inconsistency), not checker limitations.

### 2. Rukai_Li: long-vowel sources unknown to source profile (8 per dialect)

All six Rukai dialects have 8 `unknown source` findings: `a:`, `e:`, `i:`, `o:`, `u:`, `ə:`, `ɨ:`, `ʉ:` — Li's long-vowel digraphs. These are not listed in the Li Rukai orthography profile. **Classification:** **Real profile defect** — the Li profile is missing the long-vowel graphemes, or the table maps a notation the profile doesn't cover.

### 3. Rukai_Li + Rukai_94/Church/MinEd: untokenizable targets with accented vowels / missing ' (glottal)

- `é` as a target grapheme (appears in multiple dialects): `é` is not in the Ortho113 Rukai profile. **Real table defect** — the conversion produces a character the output orthography doesn't recognize.
- `'` as a target (glottal stop marker) missing from some dialects' Ortho113 profile. **Real profile/table defect** — profile doesn't list `'` for those dialects, but the table produces it.

### 4. Rukai_Li mismatches: `T→tr`, `θ→th` for Wanshan/Maolin

Wanshan and Maolin dialects show `T → tr` as mismatch (source IPA `ʈ`, target IPA `tr` — not equivalent in the checker's model). `θ → th` similarly mismatch for Wanshan. **Classification:** Likely a **checker IPA model limitation** — `ʈ` vs `tr` (retroflex stop vs consonant cluster) is a borderline case; the orthography may intentionally approximate `ʈ` with `tr`, which is a legitimate notational choice that the IPA normalizer doesn't treat as equivalent.

### 5. Amis_94: o/u merge and uppercase O/U as unknown sources

All dialects: `u→u` and `o→u` both resolve to `o~u` in the target (merge), and the table has `U`, `O` as uppercase entries not in the source profile. **Real table defect**: uppercase `O`/`U` are not valid source graphemes in the Ortho94 Amis profile; they should be removed or the profile should be updated.

### 6. Amis_Church: `ɟ` as untokenizable target

The Church→113 table maps something to `ɟ` (voiced palatal stop), which is not in the Ortho113 Amis profile. Also uppercase `Ng`, `G`, `ɟ` as unknown sources. **Real table defect.**

### 7. Paiwan_Ferrell: uppercase `Ts`, `Ḍ`, `Ɫ` as unknown sources

Ferrell table has capitalized versions of digraphs/special chars not in the Ferrell profile. **Real table defect** — casing inconsistency (profile has `ts`, `ḍ`, `ɫ`; table also lists `Ts`, `Ḍ`, `Ɫ` which are likely sentence-initial capitals that shouldn't be separate entries).

### 8. Paiwan_MinEd Southern: `L→l` mismatch (ɭ / ɣ)

In the Southern dialect, the table maps `L` to `l` but the source IPA is `ɭ` while the target IPA is `ɣ`. This is a **real table or profile defect** — either the Southern Ortho113 Paiwan profile has the wrong IPA for `l`, or the conversion is wrong for this dialect.

### 9. Puyuma_Folk: `H→'` and `R→'` mismatches (ʔ~R / ʔ)

The Folk source has `R` (pharyngeal-like approximant) while Ortho113 uses `ʔ` (glottal stop). The checker treats these as different sounds. **Classification:** Borderline — may be a legitimate phonological equivalence (uvular trill collapsed to glottal stop in standardization), but the IPA model doesn't confirm it. Informational defect, not necessarily a mapping error.

### 10. Puyuma_MinEd: `y→y` (y / j) mismatch, `d→d` (d / ð)

Source profile has `y` = /y/ (close front rounded vowel) but target has `y` = /j/ (palatal approximant). Also `d` maps to /d/ in source vs /ð/ in target. **Real profile or table defect** — IPA values for these graphemes are inconsistent across the two profiles.

### 11. Bunun_MinEd: `ch→c` mismatch for Zhuoqun/Kaqun (ʨ / ʦ~ʨ)

The MinEd source has `ch` = /ʨ/ but the target Ortho113 `c` = /ʦ~ʨ/ (an alternation). In Zhuoqun/Kaqun the target `c` is specifically /ʦ~ʨ/, so the checker flags it as unresolved mismatch. **Borderline** — the alternation notation in Ortho113 likely covers /ʨ/, but the checker's IPA model requires exact or canonically equivalent strings.

### 12. Saaroa_MinEd: `e→ʉ` mismatch (Ə / ɨ)

Source `e` maps to IPA /Ə/ (capital schwa — unusual) while target `ʉ` = /ɨ/. **Real profile defect** — source profile likely has a typo (capital `Ə` instead of lowercase `ə`), and the mapping `e→ʉ` may also be wrong phonologically.

### 13. Tables with zero confirmed equivalences (Atayal_94, Kavalan_94, Puyuma_94, etc.)

These pass (exit 0) but with zero confirmed equivalences. This means the conversion tables for these language/scheme pairs have no mappings — the tables are essentially empty or contain only trivial identity mappings that weren't flagged. These pass because there are no blocking findings, not because the tables are well-validated.

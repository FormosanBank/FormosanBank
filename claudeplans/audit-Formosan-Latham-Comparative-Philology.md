# Dev-repo audit — Formosan-Latham-Comparative-Philology

**Audit date:** 2026-08-02
**Auditor:** Claude (audit-dev-repo skill), with maintainer sign-off on each judgment call
**Dev repo:** `../Formosan-Latham-Comparative-Philology/`
**Corpus:** Formosan lexical tables in R. G. Latham, *Elements of Comparative Philology* (1862), printed pp. 315–318
**XML audited:**
- `Final_XML/Siraya/latham_1862_sideia_sida.xml` — 38 records, `xml:lang="fos"`, `dialect="Siraya"`
- `Final_XML/Babuza/latham_1862_favorlang.xml` — 24 records, `xml:lang="bzg"`, `dialect="Favorlang"`

---

## TL;DR

- **PORT-READY after convention remediation** (scope confirmed in-scope by maintainer). Data handling is exemplary: the XML is a faithful, reproducible copy of a manually reviewed source ledger.
- **All data-fidelity concerns (a, b, d) are clean.** 0 mismatches between XML and the source ledger; historical diacritics preserved; no punctuation loss; no artifacts; `validate_xml` 0 findings.
- **Three convention items**, all resolved with maintainer decisions:
  1. **Scope** — Siraya (`fos`, ISO-Extinct) + Babuza (`bzg`): **in scope, proceed.**
  2. **HARD duplicate** (`rahpal`) — **keep both, accept as source-authentic.**
  3. **Language/dialect model** — rename Babuza language to **`Babuza-Favorlang`** (ISO `bzg`), `dialect="Favorlang"` + `glottocode="favo1235"`; add `dialects.csv` rows for both dialects.
- **Rights:** public domain (1862). Clean.

---

## 1. What the assistant did (preprocessing summary)

`CodeAndDocs/build_lexical_xml.py` reads a single authoritative, human-transcribed TSV (`CodeAndDocs/source_ledger.tsv`; the 1862 scan has no text layer) and emits two XML files. The build is a strict copy with structural validation, not a text transformation:

| Step | Transformation | Notes |
|---|---|---|
| Load ledger | 64 reviewed cells; assert 62 included + 2 omitted dashes; assert 16 cells/page; assert 38 Siraya + 24 Babuza | Fails closed on any count drift |
| `FORM original`/`standard` | Both set to the ledger `form` **verbatim** (historical spelling; no modern conversion) | original == standard (copy) |
| `FORM alternate` | Comma-separated source variants become separate `kindOf="alternate"` FORMs | punctuation not embedded |
| `TRANSL xml:lang="eng"` | English gloss, **lowercased** | gloss is metadata |
| Omit | 2 dash cells (Sida Forehead, Beard) dropped | source has no data |
| No PHON/W/M | none inferred | correct for a wordlist |

Independent checks: `audit_source_coverage.py` re-verifies every XML field against the ledger; `source_checks.tsv` (12 exact checks); `reviewer_feedback.tsv` (regression coverage of two reviewer rounds); reproduction rebuilds twice and byte-compares.

## 2. Mapping to our pipeline

| Assistant step | Our pipeline equivalent | Verdict |
|---|---|---|
| standard = copy of original | `standardize.py --copy` (no TSV conversion exists) | ✅ Correct |
| comma variants → `alternate` FORMs | matches `kindOf="alternate"` schema use | ✅ Correct |
| no PHON/W/M | n/a for lexical table | ✅ Correct |
| historical spelling preserved | our `clean_xml` would only normalize punctuation/entities | ✅ No conflict |
| dialect labeling | `dialects.csv` + V036 | ⚠️ `Favorlang` not registered — see §4.3 |

## 3. Findings by concern (validators run 2026-08-02; CSVs in `/tmp/latham_audit/`)

**(a) Dropped orthography characters — CLEAN.** Char inventory of all FORM tiers: `a–z` plus historical diacritics `à á â é ó`, **no digits, no stray punctuation**. All 9 diacritics preserved (= the 9 V116 SOFT `non_ascii_in_form` findings; source-authentic, e.g. `avâu`, `àmagh`, `tâu`, `chárrina`).

**(b) Suppressed punctuation — CLEAN.** No embedded punctuation in forms; comma-separated variants correctly split into `alternate` FORMs; the `arribórri-`/`bon` line-wrap correctly joined to `arribórribon` (per reviewer feedback).

**(d) Extraction artifacts — CLEAN.** Two dash cells correctly omitted; no digit/page-number leaks; no out-of-scope (Malay/Philippine/Micronesian) forms leaked; `validate_xml` 0 findings. **XML matches the source ledger with 0 mismatches** across all 62 records (form + alternates + gloss-lowercasing).

**(c) Convention — three items (see §4).** `validate_text`: 9 SOFT (diacritics). `validate_glosses`: 62 V060 SOFT (no W/M — expected for a wordlist). `validate_duplicate_sentences`: 1 HARD group + 1 SOFT group (both tiers).

## 4. Convention items & maintainer decisions (2026-08-02)

### 4.1 Scope — IN SCOPE, PROCEED
Siraya (`fos`, marked **E**=Extinct in ISO 639-3) and Babuza (`bzg`) are historical/dormant Formosan varieties outside the 16 living languages, with **no reference orthography/vocabulary profiles** (so `validate_orthography`/`validate_vocabulary` correctly report "no reference" and skip). Maintainer confirmed these are in scope for FormosanBank.

### 4.2 HARD duplicate `rahpal` — KEEP BOTH, ACCEPT
`rahpal` (Foot) appears in two records within the Siraya file — `S_klaproth_formosan_sideia_foot` (printed p. 315) and `S_sida_foot` (printed p. 318, alternate `tiltil`). These are **distinct source attestations** (different source variety + page, recorded in each `@source`). Our `validate_duplicate_sentences` flags within-file exact FORM matches as **HARD** (exit 1), which would fail CI on port. Maintainer decision: **keep both records** (they are source-authentic); the port must accommodate this via a lexical-corpus exception or `--no-exit-on-hard`. (`rima` Hand is a cross-file SOFT — Siraya `S_sida_hand` + Babuza `S_favorlang_*`; benign.)

### 4.3 Language/dialect model — REMEDIATE BEFORE PORT
Current: Babuza file has `dialect="Favorlang"`, which is **not** in `dialects.csv` (only a bare `Siraya,,,,` row exists; no Babuza/Favorlang). `dialects.csv` columns are `Language, Official, Chinese, glottocode, OtherNames`. Maintainer decision:

- **Language name → `Babuza-Favorlang`** (mapped to ISO `bzg`), replacing the current `Babuza` label/folder.
- **Corpus dialect stays `Favorlang`**, add **`glottocode="favo1235"`** to the TEXT.
- **Add two `dialects.csv` rows** under language `Babuza-Favorlang` — one per dialect of the language:
  - `Babuza-Favorlang,Babuza,,babu1242,`
  - `Babuza-Favorlang,Favorlang,,favo1235,`
- Update the FormosanBank ISO↔language-name mapping so `bzg → Babuza-Favorlang` (wherever language identity is resolved, e.g. `QC/corpus_counts.py`).

Concrete port changes:
- Dev repo: `source_ledger.tsv` `language_label` → `Babuza-Favorlang`; `build_lexical_xml.py` set `glottocode="favo1235"` on the Babuza TEXT; move `Final_XML/Babuza/` → `Final_XML/Babuza-Favorlang/`.
- FormosanBank: add the two `dialects.csv` rows; wire the ISO map.

## 5. Minor / informational
- **No `glottocode`** on either TEXT currently. Add `favo1235` (Babuza-Favorlang, per §4.3) and `sira1267` (Siraya) at port.
- English glosses are lowercased vs source Title-case — acceptable (gloss is metadata; source case retained in `@source`).
- Reproducible: builder asserts strict counts; `reproduce.sh` verifies PDF checksum/pages, rebuilds twice, byte-compares. Pinned validator commit referenced (`da88673d…`).

## 6. Verdict
**Port-ready after the §4.3 language/dialect remediation** and provided the port pipeline accepts the §4.2 source-authentic HARD duplicate. Rights are clean, the schema validates, and the data is a faithful, independently-audited, reproducible transcription of the 1862 source. Concerns (a)/(b)/(d) require no changes.

*This audit did not modify the dev repo, `Corpora/`, or `dialects.csv`. Validator output was written to a transient `/tmp/latham_audit/` and is not committed.*

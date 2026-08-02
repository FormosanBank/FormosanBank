# Dev-repo audit — Formosan-Hala-Saku-La-Videos

**Audit date:** 2026-08-02
**Auditor:** Claude (audit-dev-repo skill), with maintainer sign-off on each judgment call
**Dev repo:** `../Formosan-Hala-Saku-La-Videos/`
**Corpus:** *Hala Saku La / Pinsgayan na Tayal* by 劉宇陽 / qmalup (Wix site `qmalup.wixsite.com/pinsgayan`)
**XML audited:** `Final_XML/tay/HalaSakuLa_Pinsgayan_food_tay_zho.xml` — 51 `<S>`, `xml:lang="tay"` (Atayal), `dialect="Sekolik"`; tiers: original+standard FORM, standard PHON, zho TRANSL (51), eng TRANSL (8)

---

## TL;DR

- **PORT-READY after minor cleanup.** Rights are cleared (CC BY-NC; `permission_confirmed`; granted by 劉宇陽/qmalup 2024-12-26). Data handling is careful and well-documented.
- **All four concerns (a–d) come back clean.** Our validators: `validate_xml` 0 findings; `validate_text` 1 SOFT (a proper-name dash); `validate_glosses` N/A (sentence-level). No orthographic letters lost; footnote anchors correctly removed; no artifacts.
- **One judgment call, resolved:** the `original` FORM tier holds *cleaned* text (ASCII apostrophes, footnote anchors stripped), not raw source — **accepted as-is** by the maintainer.
- **Remediation before port:** delete the dead `scripts/make_xml.py` (copy-paste cruft from the Wilang-Yutas repo). Optional: expert spot-check of the 51-unit sentence alignment/translations.

---

## 1. What the assistant did (preprocessing summary)

Pipeline is a chain of thin stage scripts (`scripts/*.py`) that all delegate to `scripts/pinsgayan_common.py` (125 KB, the real logic). Order: crawl Wix → extract rendered text blocks → parse food/facilities/reading → normalize → map language → align units → quality filter → dedupe (within, then against FormosanBank) → build XML → validate → reports.

Data-touching transformations:

| Step | Transformation | Where |
|---|---|---|
| `clean_text` | NFC normalize; NBSP/narrow-NBSP→space; collapse whitespace | `pinsgayan_common.py:223` |
| `clean_corpus_text` | remove `(N)` parenthetical anchors; remove 1–2 digit runs after a letter/apostrophe (footnote anchors); **curly `'`/`'` → ASCII `'`** | `:231` |
| Sentence split | split at `.!?` (tay/eng) or `。！？` (zho); regroup per manual map | `:254`, `:278` |
| `split_aligned_units` | 22 paragraphs → 51 units via `data/reference/food_sentence_alignment.json`, **hash-guarded, fails closed** if source changes | `:309` |
| `atayal_standard_to_phon` | Sekolik Ortho113 table → IPA; non-IPA/non-punct char → `*` | `:409` |
| `stage_build_xml` | writes S/FORM(original,standard)/PHON/TRANSL | `:2188` |
| facilities merge | `/facilities` repeats first two `/food` entries; merge English translations into canonical `/food`; **delete the facilities XML**; retain duplicates + explanatory notes in sidecars | `:1712`, `:2095` |

## 2. Mapping to our pipeline

| Assistant step | Our pipeline equivalent | Verdict |
|---|---|---|
| Curly→ASCII apostrophe | `clean_xml.py` normalizes apostrophe variants identically | ✅ Consistent (QC_REMAINING confirms our `clean_xml` did the same when run) |
| standard = copy of original (no lossy Church table) | `standardize.py --copy` when no transliteration | ✅ Correct choice for Atayal |
| PHON from Ortho113 | `add_phonology.py` | ✅ Equivalent; generator now emits PHON so rebuilds can't drop it |
| Footnote-anchor removal | *No pipeline equivalent* — our `clean_xml` would not strip these | ⚠️ Preprocessing decision; accepted (see §4) |
| Sentence re-segmentation | n/a (source-specific manual alignment) | ✅ Hash-pinned, fails closed |
| `make_xml.py` | n/a | ❌ Dead code from another corpus — remove |

## 3. Findings by concern (validators run 2026-08-02; CSVs in `/tmp/hsl_audit/`)

**(a) Dropped orthography characters — CLEAN.** No orthographic letters lost. Char inventory of the original tier is pure Atayal Latin plus `! ' , - . : ? _`. The 28 curly apostrophes were converted to ASCII `'` — the glottal stop is **preserved**, only codepoint-normalized (matches our `clean_xml`). Underscore `_` is a legitimate Atayal disambiguator (`n_git`, `Pn_gyan` — separates `n+g` from the `ng`/ŋ digraph), faithfully preserved from source. PHON has **0 `*`** unmapped-char leaks.

**(b) Suppressed punctuation — CLEAN.** 1 SOFT only — V133 `-` in S-standard FORM at `…_U0015`: source proper names `lk-Buta`/`lk-Ayan`/`lk-Yabux`, not segmentation. Acceptable.

**(c) Convention breaks — CLEAN (schema) + 2 notes.** `validate_xml` 0 findings; `dialect="Sekolik"` valid per `dialects.csv`. Notes: (i) original tier = cleaned text — see §4; (ii) `make_xml.py` dead code — see §5.

**(d) Extraction artifacts — CLEAN.** Exactly 6 footnote digit anchors removed (CH07/09/10/15/19: `Menibu1.`, `msqolu1`, `cbil la1.`, `hinqilan1`, `qalang1,`, `Tayal2`). Confirmed non-linguistic: the same words appear digit-free elsewhere in the source; there are 0 `<sup>` tags and no footnote-definition block on the rendered food page, so no footnote *content* existed to lose. Anchors survive in `atayal_unit_raw` sidecars. 0 digits remain in the tier.

**Source diff:** 24/51 tay units differ raw→clean; every difference is either a curly→ASCII apostrophe (28 total) or one of the 6 footnote-anchor removals. Nothing else changed.

## 4. Judgment call — original tier = cleaned text — ACCEPTED (maintainer, 2026-08-02)

`stage_build_xml` sets **both** `FORM[@kindOf="original"]` and `FORM[@kindOf="standard"]` to `atayal_unit_clean` (`pinsgayan_common.py:2228,2231`). The byte-faithful raw (curly apostrophes + footnote anchors) is retained only in sidecars (`aligned_units.jsonl:atayal_unit_raw`), not in the XML.

Accepted because: (1) the apostrophe normalization is exactly what our own `clean_xml` does; (2) the removed footnote anchors are editorial apparatus, not orthography, and their content was never present in the rendered source; (3) the original tier is therefore faithful to the *linguistic* content of the source. Recorded as reviewed-and-accepted.

## 5. Remediation

1. **Before port (required):** delete `scripts/make_xml.py` — it is copy-paste cruft from the Wilang-Yutas repo (`source="Wilang Yutas Atayal Videos"`, `dialect="UNKNOWN"`, .txt-transcript logic) and is **not** on the build path (`build_formosanbank_xml.py` → `stage_build_xml`). Leaving it invites confusion about how the XML is produced.
2. **Optional:** expert spot-check of the 51-unit sentence alignment and the zho/eng translation groupings (no automated validator covers translation quality or boundary correctness). Consider `sample-sentences-for-expert-review`.
3. **No action needed:** apostrophe/footnote handling (§4, accepted); facilities merge (documented; sidecars retain duplicates + the 3 explanatory notes; 8 English translations merged correctly); dialect label; hash-pinned alignment.

## 6. Verdict

**Port-ready** once `make_xml.py` is removed. Rights are cleared, the schema is clean, the original tier is faithful to the source's linguistic content, and every transformation is documented and reproducible (rebuild digest `4cc9858c…`, verified byte-identical across two runs).

*This audit did not modify the dev repo or `Corpora/`. Validator output was written to a transient `/tmp/hsl_audit/` and is not committed.*

# Dev-repo audit — Formosan-Kucapungane

**Date:** 2026-06-12
**Auditor:** Claude (audit-dev-repo skill), with maintainer sign-off at each stage.
**Repo:** `../Formosan-Kucapungane/`
**Language / dialect:** Rukai (`dru`), **Wutai** dialect — Haocha (好茶 / Kucapungane) tribe.
**Source:** `Original/kucapungane.pdf` — 台邦撒沙. (2016). *KUCAPUNGANE: 魯凱族好茶部落歷史研究.*
原住民族委員會 / 國史館 / 國史館臺灣文獻館. **170-page scanned book, image-only (no text layer).**
**Output audited:** `Final_XML/Rukai/` — 5 files, 57 sentences total.

## HUMAN CHECKLIST — verify against the PDF

### Priority 1 — `wusilapekidauwane.xml`: systematic detached-apostrophe + lowercase-start pattern  *(concern b)*

This file is a clear outlier and looks transcribed under a different convention than
the other four:

- **95 of the 97 standalone `'` tokens** in the whole corpus are in this file
  (space-isolated apostrophes, e.g. `… ki sua Taiman ' iakai ku tai Ruzangilan …`).
  The other four files have 0–2 each.
- **15 of its 26 sentences start with a lowercase letter** (vs ~1 each elsewhere).

The ASCII apostrophe `'` (U+0027) is the Rukai glottal stop and is correctly **not**
a curly quote (no orthography loss). The question is whether the source writes the
glottal **attached** to its word (as `Keleleele'` appears elsewhere in the same file)
or as a free-standing mark — and whether the lowercase sentence starts reflect the
source or are transcription slips.
**→ Human: open the `wusilapekidauwane` story in the PDF and confirm the intended
apostrophe placement and capitalization. This likely needs re-transcription, not a
mechanical fix.**

### Priority 2 — discrete OCR artifacts in the `original` tier  *(concern d)*

Concrete, low-ambiguity — but confirm the correct spelling against the PDF. The
`add_phonology` pass (pipeline run below) independently confirmed each by emitting a
`*` placeholder in the generated PHON at exactly these spots:

| File / id | Artifact | Codepoints | Likely intended |
|---|---|---|---|
| `DilringukaCepecepe` S6 | `pu Сересере` (Cyrillic letters) | С/е/р/с = U+0421/0435/0440/0441 | Latin `Cerecere` / `Cepecepe`? |
| `wusilapekidauwane` S20 | `kakaiaianga•` (stray bullet) | • = U+2022 | drop the `•` |
| `wusilapekidauwane` S21 | `kalüdrusa` (`ü` not in Rukai) | ü = U+00FC | `kaludrusa` / `ka...`? |
| `wusilapekidauwane` S26 | `sauliflivan` — ASCII **`f`** (not in Rukai orthography); same name also appears as `sauliuilivan` and `Sauliulivan` **in the same sentence** | f = U+0066 | `sauliulivan` |
| `kiamalrakibadha2` S2 | `Takaivn` vs `Takaivan`; `tumutumu` (FORM) vs `tumsutumu` (TRANSL) | — | reconcile spelling |

These are OCR-misrecognition leftovers. The non-ASCII ones (`ü`, `•`, Cyrillic) were
**NOT auto-caught** until the standard tier existed (see V116 gap below); the ASCII
`f` is invisible to V116 entirely and was caught only by `add_phonology`'s `*`.
**Proper-name spelling is unstable** — the same name is rendered 2–3 ways within one
sentence (S26), so a human should normalize names against the PDF, not just fix the
flagged characters.

### Priority 3 — translation alignment & punctuation  *(review, likely acceptable)*

- `TRANSL` (`zho`) is frequently a **paragraph-level free translation** much longer
  than the single Rukai `FORM` it sits under (e.g. `DilringukaCepecepe` S1). Confirm
  this loose alignment is acceptable for this corpus, or whether translations should
  be split to match sentences.
- Mixed full/half-width punctuation in the Chinese gloss (222 half-width `,` vs 3
  full-width `，`). Cosmetic; note for consistency.
- **`clean_xml` rewrites Chinese corner-bracket quotes `「…」` → `＂…＂` (U+FF02)** in
  every `zho` TRANSL (seen across all 5 files when clean_xml ran below). The corner
  brackets are the *standard* Chinese quotation marks; the fullwidth straight quote is
  a degradation. This is a **clean_xml behavior, not the corpus's** — flag for whether
  clean_xml's quote-normalization should exempt CJK corner brackets.

### Priority 5 — orthography of the reference vocabulary  *(review)*

Vocabulary overlap vs `reference/Rukai/Wutai/` is only **0.26**. Part is genre, but
part is an **orthographic-convention difference in the reference data itself**: the
reference vocab uses w/y-glide spellings (`kavay`, `katwase`, `acilay`, `kwini`,
`bwala`) while this corpus uses u/i vowels (`kavai`, `katuase`, `acilai`, `kuini`,
`buala`). The character-level detector still scored the corpus as Ortho113-Wutai
(84%, 1.3% unexpected), so the corpus is internally consistent — but a human should
confirm the project's intended Rukai standard spelling, and whether the *reference
vocabulary* (not the corpus) needs updating to the u/i convention.

### Priority 4 — minor / mechanical

- `Pakuulruurlulu` S4: trailing whitespace in FORM (V130 HARD) — trivial fix, also
  handled by our cleaning step.
- No `standard` tier yet (expected) — built by `standardize.py --copy` in our pipeline.

---

## Concern roll-up

| Concern | Status |
|---|---|
| **(a) eliminated orthography chars** | **None found.** Extracted inventory ⊆ reference Rukai; glottal `'` preserved as ASCII (no curly-quote loss). |
| **(b) suppressed punctuation** | **`wusilapekidauwane` detached-apostrophe / lowercase pattern** — Priority 1, needs source check. |
| **(c) convention breaks** | Schema/dialect/ids clean. Tooling gap recorded below. |
| **(d) extraction artifacts** | Cyrillic run, stray `•`, stray `ü`, OCR typos — Priority 2. |

## Tooling finding → roadmap item

**`validate_text` V116 (non-ASCII-in-FORM) skips `kindOf="original"`** by policy
([`QC/validation/rules/text.py:457-472`](../QC/validation/rules/text.py#L457-L472),
added 2026-06-11: the original tier is source-faithful and may legitimately carry
annotation chars). **Consequence:** a corpus that has *only* an original tier — i.e.
any OCR/hand-authored corpus audited *before* its standard tier is built — gets **no
non-ASCII safety net at all**. That is precisely why the `ü` and `•` here passed
silently; only V136 (mixed-script, which does not skip original) caught the Cyrillic.

**Recommended roadmap follow-up:** when a file has no `standard` tier, run V116 over
the `original` tier (or add a dedicated pre-standard-tier non-ASCII sweep), so OCR
junk in single-tier corpora is caught automatically instead of by hand.

## Notes / scope

- This is an audit, not a fix. No edits were made to `Formosan-Kucapungane/` or to
  `Corpora/` during the read phase.
- The maintainer asked to then **run the full QC pipeline up to (not including) the
  port** and append anything new it surfaces — see the running log below.

# Corpus cleanup tasks — surfaced during validator audits

**Date:** 2026-05-31
**Purpose:** Track data-level issues surfaced by validator runs against `Corpora/` that must NOT be fixed by ad-hoc edits in the published tree. Any change to a published corpus must be part of that corpus's reproducible pipeline (per user direction): we change the reproduction script, then re-run, then commit the changed XML.

**Workflow:** Each entry lists the corpus, the issue, the affected count, and the proposed pipeline change. When a corpus's reproduction is being reworked, the maintainer consults this list to ensure the surfaced issues are addressed.

---

## V023 (TRANSL missing xml:lang) — HardPaiwanStories

**Count:** ~35,310 TRANSL elements (M-level).

**Pattern:** M-level TRANSLs in this corpus have no `xml:lang` attribute at all. The W-level TRANSLs DO have `xml:lang`, but the M-level glosses don't.

**Rule it violates:** V023 (every TRANSL must have `xml:lang`). The XSD also enforces this via `#REQUIRED` on the DTD (no enforcement in XSD because TRANSL's xml:lang is declared without `use="required"` to accommodate this corpus during the transition — but the Python v023 rule catches it).

**Proposed pipeline change:** the corpus's `convert.py` / `script.ipynb` (per `Corpora/HundredPaiwanStories/CodeAndDocs/README.md`) should emit `xml:lang="pwn"` on M-level TRANSL elements where the gloss is Paiwan-language and `xml:lang="eng"` where the gloss is English-language. Inspect the source data structure to determine which is which; the JSON cache from the conversion may already mark them.

**Open question:** Some M-level TRANSLs may be intended as morpheme-level English glosses (`OR-four` style) where the language label is implicit. Confirm with maintainer whether to emit `xml:lang="eng"` for those or leave the convention "M-TRANSL without xml:lang means morpheme English gloss" and remove V023's coverage of M-TRANSLs.

---

## V023 + missing kindOf on TRANSL — NTUFormosanCorpus

**Count:** ~14,411 M-level TRANSLs missing `kindOf`. (`xml:lang` is present.)

**Pattern:** M-level TRANSLs in NTUFormosanCorpus carry `xml:lang` but no `kindOf` attribute. No xml:lang issue.

**Proposed pipeline change:** the `parse_*.py` scripts under `Corpora/NTUFormosanCorpus/DocsAndCode/` should emit `kindOf="original"` (or whichever kindOf is appropriate per the gloss provenance) on M-level TRANSLs. Alternatively, leave kindOf unset and rely on the project convention that "no kindOf means original" — but this convention is not currently documented.

**Note:** V021 (the rule that would have flagged "lone M-TRANSL without kindOf=original") was REMOVED on 2026-05-31. TRANSLs do not need to have kindOf at all per user direction. So this is no longer a validator finding — but the user may still want kindOf set explicitly for clarity. Decision at corpus-reproduction time.

---

## TRANSL has wrong kindOf value — WakelinTexts

**Count:** ~1,092 M-level TRANSLs with `kindOf` set to non-canonical values (e.g., `kindOf="english"` instead of the canonical `"original"` / `"standard"`).

**Pattern:** the kindOf attribute is being used as a language label, not as a tier marker.

**Proposed pipeline change:** the corpus's reproduction script (if recovered — currently WakelinTexts has NO reproduction scripts per `2026-05-31-b1-codeanddocs-readme-discovery.md`) should map the existing `kindOf="english"` etc. to `kindOf="original" xml:lang="eng"` etc., separating the language label from the tier marker.

**Open question:** Without a reproduction script, this corpus may need a one-off cleanup rewrite committed directly (with that rewrite itself becoming the "reproduction": a `fix_kindOf_to_canonical.py` added to CodeAndDocs).

---

## Unknown attributes (`audio_url`, `source`) — YeddaPalemeqBlog

**Pattern:** S elements have `audio_url="..."` and `source="..."` attributes that are not in the canonical XML schema. AUDIO elements also have `source="..."`. Visible across all 668 S elements + 1 file.

**Affected counts (verified 2026-05-31):**
- 668 × `S/@audio_url`
- 668 × `S/@source`
- 668 × `AUDIO/@source`
  Total V000 hits from this pattern: 2,004.

**Proposed pipeline change:** the corpus's `Scripts/make_xml.py` adds these attributes. Decision needed: either (a) extend the canonical schema to allow `source` (and possibly `audio_url`) on S/AUDIO, OR (b) move the provenance metadata into existing schema-allowed attributes (e.g., `TEXT/@source` is already in the schema; per-S provenance could be flattened into a single `TEXT/@source` URL or moved out-of-band). Option (b) is cleaner architecturally but loses per-S granularity.

---

## Duplicate M ids within file — YeddaPalemeqBlog

**Count:** 68 M-element id collisions within single files (V000 from XSD's xs:unique constraint, plus 68 V039 Python rule findings — same underlying issue, two findings each).

**Pattern:** Sample ids that collide: `S6_1W18M3`, `S6_1W15M3`, `S659_1W3M2`, `S641642_1W7M1`, `S618619_2W6M1`, `S610_1W8M1`, `S607_1W8M1`. Each appears twice on `<M>` elements in the same XML file. The id scheme is `S<sentence>_<num>W<word>M<morpheme>`, so this is likely a make_xml.py bug where the same morpheme id is emitted twice when a W element has multiple identical-looking sub-morphemes.

**Proposed pipeline change:** the corpus's `Scripts/make_xml.py` needs to ensure unique M ids within each file. Either use a per-W counter to generate `M0`/`M1`/`M2` ids cleanly, or post-process to detect+rename collisions.

---

## Infix morphemes without angle-bracket gloss — YeddaPalemeqBlog

**Count:** 285 V062 findings (M elements with infix-shaped FORM like `-em-` but the parent W has no TRANSL with `<X>` angle-bracket gloss notation).

**Pattern:** Sample M ids: `S668_1W5M2`, `S660661662663_1W4M2`, `S660661662663_2W6M2`. The morpheme tier marks the infix correctly but the word-level English translation doesn't surface it with the expected `<...>` convention. Example: an infix morpheme like `-em-` should be glossed as `<AV>` (Actor Voice) in the W-level TRANSL.

**Proposed pipeline change:** the corpus's `Scripts/make_xml.py` or a subsequent gloss-formatting script needs to emit angle-bracket glosses on the W TRANSL when M-level infix morphology is present. Alternatively, if the source data doesn't include the gloss info, V062 may need to be downgraded to SOFT/WARN for this corpus until the gloss info can be sourced.

---

## YeddaPalemeqBlog &amp;amp; double-encoded entities (informational)

**Pattern (informational, not a validator finding):** The TRANSL text in this corpus contains literal `&amp;amp;` and `&amp;apos;` sequences — double-encoded HTML entities from the scrape. After the B7 fix (commit `fac85b55d`), the orthography extraction now correctly decodes these via `html.unescape`. The underlying XML files still carry the double-encoded forms, but downstream consumers (orthography stats, similarity metrics) are no longer polluted.

**Proposed pipeline change:** the corpus's `download_html.py` or `Scripts/make_xml.py` should call `html.unescape()` on extracted text before writing the XML. Not blocking — the validator doesn't complain — but the data would be cleaner.

---

## Empty PHON / empty FORM — multiple corpora

**Counts:** V017 (empty FORM): ~4,616. V073 (empty PHON): ~4,495.

**Pattern:** These are real bugs — the reproduction scripts emitted PHON or FORM elements with no text content. Likely sources: failed transliteration, missing source data for a particular morpheme, etc.

**Proposed pipeline change:** the per-corpus reproduction scripts should either fill in the missing content (if recoverable from the source) or omit the empty element entirely. Per-corpus investigation needed.

---

## Cross-corpus id collisions (V081) — 9 cases

**Pattern:** 9 TEXT/@id collisions across published Corpora/. Need to enumerate and resolve.

**Proposed action:** rename the colliding IDs in whichever corpus is more recent / less foundational. Document the rename in the corpus's CodeAndDocs/README.md.

---

## Open-source typo (FIXED 2026-05-31)

The FormosanBankGitBook "open-soorce" typo was fixed directly (commit `6c0a0d7a5`) BEFORE this policy of "all data changes via pipeline" was articulated. The fix is correct but the pipeline (`process_raw.py`) was not updated to prevent re-emergence on re-run. **TODO:** Update `process_raw.py` so it doesn't apply the u→o transform to recognized English loanwords (or to anything in `kindOf="standard"` that originated as ASCII Latin in the original tier).

---

## Tooling bugs (non-validator, address when next touching the script)

### `orthography_extract.py`: `unique_chars.remove(" ")` crashes on space-free input

**Surfaced:** commit `fac85b55d` (B7 — html.unescape fix) noted but did not fix.

**Pattern:** `extract_orthographic_info` in `QC/orthography/orthography_extract.py` calls `unique_chars.remove(" ")` unconditionally. If the input FORM text contains no whitespace at all (single-token corpus, or anything that reaches the function with all-glued text), the `set.remove()` raises `KeyError`.

**Proposed fix:** change to `unique_chars.discard(" ")`. One-line edit. Add a regression test using a space-free fixture.

**Not a validator issue.** Handle when next working on `orthography_extract.py` (will come up in B9.6 work).

---

## Process notes

- This list is appended to (not replaced) as new validator audits surface new issues.
- Items move to a "DONE" subsection once the pipeline change lands AND the corpus has been re-run with the updated script.
- The validator-side rule removals (e.g., V021 deletion) are NOT on this list — they live in the design doc + commit history.

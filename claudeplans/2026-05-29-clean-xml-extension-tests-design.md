# clean_xml.py Extension Tests — Design

**Date:** 2026-05-29
**Status:** Draft for user review
**Parent:** [2026-05-28-a-test-infrastructure-design.md](2026-05-28-a-test-infrastructure-design.md), sub-project A Task 6

## Goal

Extend the basic test round for [`QC/cleaning/clean_xml.py`](../../QC/cleaning/clean_xml.py) with positive and negative fixtures derived from patterns Joshua flagged while hand-reviewing students' XML conversions of Formosan-language texts. The basic round already covers byte-exact non-mutation, whitespace, idempotency, and a round-trip test for HTML-entity-shaped input. This round adds (a) tests for cleaner behaviors that the source code clearly intends but does not currently exercise, (b) tests pinning behaviors the cleaner currently *should not* perform on the original tier (so future "improvements" do not silently corrupt source-faithful text), and (c) negative pins documenting patterns that surface in real student XML but belong to other stages of the pipeline (scraping, standardization, validators) rather than to `clean_xml.py`. Each rule documents the source transcript it came from so reviewers can sanity-check our interpretation against Joshua's original wording.

## Sources

- **`temp/(Amis) Adversative and experiential applicative constructions in Northern Amis (Austronesian).pdf`** — Basecamp card export for Dorothy P.'s conversion of the Bril (2024) Amis paper. Discussion thread covers null-morpheme (`Ø`) handling, clitic-vs-affix segmentation (`=` vs `-`), multiple-translation conventions (`ver="alt"`), and footnote intrusion into morphemes.
- **`temp/(Amis) Joy Wu. The analysis of pa-verbs in Amis_.pdf`** — Basecamp card for the Wu pa-verbs paper. Covers loss of the `ø` null-morpheme marker at the W/M level, segmentation hyphens left in the S-level FORM but stripped from W FORMs (Joshua wants it the other way around for `standard` but says "leave `ø` markers in the W FORM while deleting them from the S FORM").
- **`temp/(Amis) Serial Verb Constructions in Amis (Yi-Ting Chen).pdf`** — Basecamp card for the Chen serial-verb paper. Covers `<AV>` infix notation that collides with XML tag syntax (must be escaped as `&lt;AV&gt;` or removed), apostrophes in S/W/M `id` attributes breaking XML readability, infix vs circumfix vs clitic distinctions, and out-of-language examples (Fongbe, Japanese) mistakenly included in an Amis corpus.
- **`temp/(Bunun) Jeng (1992) Topic and focus in Bunun.pdf`** — Basecamp card for Dorothy's conversion of Jeng's Bunun monograph. Notes parentheses in free translations (page-68 convention: parenthesised English words have no Bunun counterpart and may be safe to delete, but check context), underline-as-segmentation-marker (author used `_` instead of `-`), single quotes in sentence IDs, a stray `d`-with-stroke character that is non-standard but intentional, multi-word glosses that should be joined with `.` (e.g. `go.to`), and missing glosses for some morphemes.
- **`temp/Lowking Nowbucyang's thesis.pdf`** — Basecamp card for Hunter's conversion of Hsu's Truku word-formation thesis. Covers Chinese-character glosses (`xml:lang="zho"`), explicit null morphemes `Ø`/`ø` written in the source, `=` clitic notation that must survive cleaning, sentence-initial `*` marking ungrammaticality (whole sentence should be excluded), `*` interacting with `/` (only one alternative is ungrammatical), parentheses for omitted subjects, and angle-bracket infix markup `<AF>` in glosses that collides with XML. Most explicit guidance in this card on "what `clean_xml` should and should not touch": Joshua specifies that `-` segmentation should be removed from `<FORM kindOf="standard">` at the `<S>` level but left in W FORMs and not relevant at M level.
- **`QC/cleaning/clean_xml.py`** — current cleaner implementation; the body of this design refers to it by function name.
- **`tests/cleaners/test_clean_xml.py`** — basic round (already written); this design extends it.
- **`CLAUDE.md`** — project conventions, especially the `original` vs `standard` tier semantics and the rule that `--kindOf standard` is the comparable form.

## How tests are structured

Following the basic round's convention: `clean_xml.py` is an in-place mutator, so each test (a) copies a fixture from `tests/fixtures/` into `tmp_path` via the `copy_fixture` conftest helper, (b) invokes the script via `subprocess.run` with `--corpora_path tmp_path`, and (c) asserts on the parsed `FORM` text values using `lxml`, not on raw file bytes (parsing avoids false positives from comment text and attribute indentation). For tier-asymmetric rules we read `FORM` elements with an XPath that filters on the `kindOf` attribute and the parent element name (e.g. `S/FORM[@kindOf="original"]` vs `S/FORM[@kindOf="standard"]` vs `.//W/FORM`). Every positive ("cleaner should change X to Y") is paired with an idempotency check (running the cleaner twice yields the same result as once), and where the rule is tier-asymmetric or scope-asymmetric a *negative pin* is added (e.g. "running the cleaner must leave the `=` in this W-level FORM untouched"). See [tests/cleaners/test_clean_xml.py](../../tests/cleaners/test_clean_xml.py) for the existing helpers (`_run_clean`, `_form_texts`).

## What clean_xml.py currently does

Reading the source: the cleaner walks every `*.xml` under `--corpora_path`, processes each file with:

1. ` ` (non-breaking space) → regular space, applied at raw-text level before XML parsing.
2. Parse with `lxml`, iterate `.//S`.
3. For each `FORM` under `S` (the XPath `.//FORM` actually matches W/M FORMs too, so M and W FORMs are co-processed; this is implicit and probably unintentional — see open questions):
   - NFC-normalise the text.
   - Skip empty FORMs (but the code has a contradictory branch that *also* tries to remove `<S>` if the FORM is empty; the `continue` above prevents that branch from firing — likely dead code).
   - Remove the entire `<S>` if the FORM text contains the literal sentinel `"456otca"`.
   - `html.unescape` the FORM text if it changes anything (logged to `html_entities.log`).
   - Run `clean_text` on the FORM text: `swap_punctuation` (full-width and curly-quote → ASCII, plus `[`/`]` → `(`/`)`, plus `⌃` → `^`, plus a handful of modifier-letter apostrophes → `'`), `normalize_whitespace` (collapse runs of whitespace, strip leading/trailing), `trim_repeated_punctuation` (`!!`→`!`, `??`→`?`, `---`→`-`), then `remove_junk_chars` (removes the bopomofo letter `ㄇ`).
4. For each `TRANSL` directly under `S` (the cleaner does **not** descend into W/M for TRANSL): run `clean_trans` (only `normalize_whitespace` + `trim_repeated_punctuation`; intentionally does *not* run `swap_punctuation` on translations).
5. Only write the file back if any of the above changed it; otherwise it leaves byte-exact.

Things it explicitly does *not* do, that the source code makes clear are deliberate omissions:

- `clean_trans` skips `swap_punctuation` — so translations keep their full-width punctuation, curly quotes, etc. The probable rationale is that translations are in `zh` or `en` and should not have, e.g., `（` rewritten to `(` in Chinese text. **But** the cleaner does run `swap_punctuation` on every `FORM` regardless of `xml:lang`, including FORMs whose text is Chinese (because `clean_text` is called for any S-level FORM and `.//FORM` also matches W/M FORMs, some of which carry `zho` translations on a *sibling* element rather than on the FORM itself). The cleaner doesn't look at `xml:lang` on the parent or sibling.
- `remove_nonlatin` is defined but never called (commented out in `clean_text` and `clean_trans`). Currently dead code.
- `process_punctuation` and `fix_parentheses` are commented out at the top of the file.
- It does not touch attributes, `id`s, BibTeX text, or comments.
- It does not distinguish `kindOf="original"` from `kindOf="standard"`; the same cleaning is applied to both tiers. This is the largest divergence from what the transcripts make clear Joshua wants (see C012, C013).
- It does not touch element text inside W or M directly via the `S/TRANSL` loop, but it *does* touch FORM text inside W and M because of the `.//FORM` XPath. This dual-asymmetry is currently undocumented in the code.

Gaps the basic-round tests have already identified or that surface from reading the code: the HTML-unescape branch can almost never fire in normal flow because `lxml` decodes entities at parse time; the cleaner relies on the rare case where the source has *double-encoded* entities like `&amp;amp;`. The 456otca sentinel has no explanation in code or docstring. Whitespace normalisation runs after `swap_punctuation`, which means a full-width space (which `swap_punctuation` does not list) survives until `normalize_whitespace` collapses it via `\s+` — this works incidentally because U+3000 matches `\s` in Python's default regex. Worth pinning.

## Patterns Joshua flagged

Rules are grouped by category. "Source" references the file in `temp/` and paraphrases Joshua's wording; "Currently handled" reflects our read of the source as of this design.

### Category 1: Punctuation and special-character handling in FORM

#### C001 — Full-width punctuation → ASCII (language-aware)
- **Pattern:** Per user direction (2026-05-29), the rule is language-conditional:
  - **In FORM (any tier, S/W/M)**: all full-width punctuation collapses to ASCII (`（`→`(`, `，`→`,`, `。`→`.`, `；`→`;`, `：`→`:`, `？`→`?`, `！`→`!`, etc.).
  - **In TRANSL where `xml:lang` is NOT Chinese** (i.e., not `zh*`, `cmn`, `yue`, `wuu`, etc.): same as FORM — collapse to ASCII.
  - **In TRANSL where `xml:lang` IS Chinese**: leave full-width punctuation alone (Chinese-style punctuation is the locale convention).
  - Rationale (user): full-width punctuation in non-Chinese text is treated as a typist error caused by switching IMEs between Chinese and other languages. Existing corpora will need fixing where Chinese TRANSL was previously incorrectly stripped of full-width.
- **Source:** User direction (2026-05-29).
- **Currently handled by clean_xml.py?** Partial. The cleaner runs `swap_punctuation` on every FORM (S/W/M, via `.//FORM`) unconditionally — that's CORRECT for FORM. It does NOT run `swap_punctuation` on TRANSL at all (`clean_trans` skips it). The desired behavior requires `clean_trans` to become language-aware: collapse on non-Chinese TRANSL, leave alone on Chinese TRANSL.
- **Test approach:**
  - Positive (passes today): non-Chinese FORM with `（X）` → `(X)`. Plus W- and M-level FORM positives per OQ1.
  - Positive (passes today): Chinese TRANSL with `（X）` → unchanged (because `clean_trans` doesn't touch it).
  - **xfail**: non-Chinese TRANSL with `（X）` → expect `(X)` (currently unchanged because `clean_trans` is unconditional; will pass when B implements language-awareness).
- **Follow-up:** Existing corpora may need remediation if non-Chinese TRANSL ever got full-width punctuation through — flag as follow-up corpus work (see Deferred to B section).

#### C002 — Quote and apostrophe rules (language-aware, with warnings)
- **Pattern:** Per user direction (2026-05-29), two-branch rule:

  **Branch A — In FORM (any tier) and TRANSL where `xml:lang` is NOT Chinese:**
  - All single-quote / apostrophe variants (`'` U+2019, `'` U+2018, `ʼ` U+02BC, `ʻ` U+02BB, `` ` `` U+0060, full-width `'` U+FF07 if any, etc.) → collapse to `'` ASCII U+0027.
  - All double-quote variants (`"` U+201C, `"` U+201D, `「`, `」`, `『`, `』`, `《`, `》`, full-width `"` U+FF02 etc.) → collapse to `"` ASCII U+0022.

  **Branch B — In TRANSL where `xml:lang` IS Chinese:**
  - Full-width DOUBLE quotes (`"` U+201C, `"` U+201D, `「`, `」`, `『`, `』`, `《`, `》`) → collapse to **`"` U+201D** (single canonical full-width right double quote).
  - Full-width SINGLE quotes / apostrophes (`'` U+2018, `'` U+2019, etc.) → **WARN** with a CSV row (file, S id, character, position). NO collapse.
  - Latin (ASCII) quotes and apostrophes (`'`, `"`) → **WARN** with a CSV row (Latin punctuation in Chinese text is suspicious). NO collapse.

  Rationale (user): we assume any single-quote-shaped variant in non-Chinese text is a glottal stop; in Chinese text we don't have enough training data to disambiguate so we warn and preserve. Chinese double-quote variants collapse to a single canonical form because we want simplification but not destruction. Latin quotes appearing in Chinese text are typically IME mistakes worth flagging.

- **Source:** User direction (2026-05-29). This rule addresses the apostrophe-collision concern surfaced when looking at `Orthographies/Ortho113Liberal/Amis.tsv` (where `'` represents IPA `ʡ` and `^` represents IPA `ʔ`) — by treating all single-quote variants in non-Chinese FORM as a glottal stop, we avoid linguistic data loss.

- **Currently handled?** Partial. The cleaner's existing `swap_punctuation` unconditionally collapses all the variants to ASCII on FORM. This is correct for Branch A's FORM path. It is NOT correct for Branch A's non-Chinese TRANSL (cleaner skips TRANSL entirely), and it is NOT correct for Branch B (cleaner doesn't know about Chinese). Warning + CSV output infrastructure does not exist at all.

- **Test approach:**
  - Positive (passes today): non-Chinese FORM with mixed apostrophe / quote variants → all collapsed to ASCII.
  - **xfail**: non-Chinese TRANSL with `'` → `'` (cleaner currently leaves it alone).
  - **xfail**: Chinese TRANSL with `"` and `"` siblings → both become `"` U+201D.
  - **xfail**: Chinese TRANSL with `ʼ` → unchanged, WARN emitted, CSV row appended.
  - **xfail**: Chinese TRANSL with ASCII `'` → unchanged, WARN emitted, CSV row appended.

- **Follow-up:** Existing corpora may need remediation where Chinese TRANSL was previously stripped of language-appropriate punctuation. Flag as follow-up corpus work (see Deferred to B section).

#### C002b — IPA primary stress mark U+02C8 → ASCII `'` with warning
- **Pattern:** `ˈ` U+02C8 (IPA PRIMARY STRESS MARK) in FORM or TRANSL text.
- **Source:** User direction (2026-05-29).
- **Expected:** Collapse to `'` ASCII U+0027 (same as other single-quote variants per C002 Branch A). Additionally, emit a warning with CSV row naming the file and element. Stress markers should not normally appear in Formosan corpora; visibility helps catch unexpected use.
- **Currently handled?** Partial. The cleaner's `swap_punctuation` already collapses U+02C8 → `'` on FORM. The warning + CSV output does not exist.
- **Test approach:**
  - Positive (passes today): FORM with `ˈ` → `'` (current behavior).
  - **xfail**: warning row emitted to CSV (no warning infrastructure yet).
- **Notes:** U+02CB (`ˋ` MODIFIER LETTER GRAVE ACCENT) is a different character (tone mark, not IPA stress) and is NOT covered by this rule. If U+02CB ever needs special treatment, it warrants a separate rule.

#### C003 — Repeated terminal punctuation collapsed
- **Pattern:** `!!`→`!`, `??`→`?`, `---`→`-` in FORM and TRANSL.
- **Source:** Cleaner has explicit logic; not separately flagged in transcripts but consistent with the OCR-noise reality of student scrapes.
- **Expected:** Single mark, both tiers.
- **Currently handled?** Yes, for both FORM and TRANSL.
- **Test approach:** Positive on FORM and TRANSL; idempotency.

#### C004 — Non-breaking space (U+00A0) collapses to ASCII space
- **Pattern:** NBSPs in any text node become regular spaces (then normalised).
- **Source:** Cleaner explicitly does `re.sub(' ', ' ', content)` on raw bytes before parsing.
- **Expected:** No U+00A0 anywhere in cleaned file.
- **Currently handled?** Yes.
- **Test approach:** Positive on a fixture with embedded NBSPs in S/FORM and TRANSL.
- **Notes:** This happens *before* XML parsing, so it also catches NBSPs in attribute values and comments. Worth pinning that attribute values are also affected (or pinning the opposite if Joshua would prefer attributes be left alone — see OQ5).

#### C005 — Full-width space (U+3000) collapses incidentally
- **Pattern:** U+3000 is not in `swap_punctuation`'s table but matches `\s+` in `normalize_whitespace`, so it disappears.
- **Source:** Reading the code, not transcripts.
- **Expected:** No U+3000 in cleaned FORM text.
- **Currently handled?** Yes, incidentally.
- **Test approach:** Positive pin so we notice if a future refactor to a stricter whitespace regex breaks this.

#### C006 — Caret variant `⌃` (U+2303) → `^` in FORM
- **Pattern:** Mentioned in cleaner's `fullwidth_to_regular` table.
- **Source:** Implicit; no transcript example surfaced.
- **Expected:** `⌃` → `^` in FORM text.
- **Currently handled?** Yes.
- **Test approach:** Positive on FORM. Negative pin on TRANSL (since `clean_trans` skips this mapping).
- **Notes:** Unclear when `⌃` appears in real Formosan data; this may be a historical artefact of an earlier corpus. Worth a brief comment in the test.

#### C007 — Bopomofo `ㄇ` retained, with warning (REVISED 2026-05-29)
- **Pattern:** Per user direction (2026-05-29): the cleaner should NOT silently remove Bopomofo characters. Instead, it should preserve them and emit a WARNING with CSV row (file, S id, character, position). Bopomofo in FORM is *probably* an error (Bopomofo is a Mandarin phonetic system; it shouldn't be in Formosan-language FORM text), but it might be intentional phonetic transcription. Visibility matters more than silent deletion.
- **Source:** User direction (2026-05-29). Reverses the current cleaner's behavior, which silently deletes `ㄇ` via `remove_junk_chars`.
- **Expected:** `ㄇ` (and other Bopomofo characters, per OQ at end) preserved verbatim. WARN emitted with CSV row.
- **Currently handled?** **No.** The cleaner currently silently deletes `ㄇ`. This rule reverses that. `remove_junk_chars` either becomes a no-op (if it only ever handled `ㄇ`) or restricts to genuinely-junk characters (which would need enumeration).
- **Test approach:**
  - **xfail (positive)**: FORM with `ㄇ` → `ㄇ` survives unchanged.
  - **xfail (warning)**: same fixture → CSV row emitted naming the file and S id.
- **Notes:** This is a behavior change. Existing corpora that had `ㄇ` silently removed are unaffected (the character is already gone). New corpora with `ㄇ` will now generate warnings instead of silently losing the character. Open question on whether the rule should extend to the full Bopomofo block (U+3100–U+312F) or stay restricted to `ㄇ`; current cleaner only knows about `ㄇ`.

### Category 2: Structural cleaning

#### C008 — Sentences containing the literal `"456otca"` are removed (no test, per user direction)
- **Pattern:** If FORM text contains `"456otca"`, the entire `<S>` is removed.
- **Source:** Hardcoded in cleaner.
- **Expected:** S element removed; sibling Ss preserved.
- **Currently handled?** Yes.
- **Test approach:** **NO TEST** per user direction (2026-05-29). The sentinel is meaningful (user confirmed) but does not warrant test coverage. Documented here for completeness so future readers know the behavior is intentional, not a bug.
- **Notes:** OQ2 resolved — sentinel is meaningful (user knows its provenance); no further investigation needed.

#### C009 — HTML entities in FORM text are unescaped
- **Pattern:** Text like `&amp;` (literal double-encoded in the file on disk) should become `&` in the cleaned FORM. Logged to `html_entities.log`.
- **Source:** Cleaner code; basic-round test note observes this branch is hard to exercise via normal lxml-parsed input.
- **Expected:** `html.unescape(form.text) == form.text` after cleaning.
- **Currently handled?** Yes, but only fires when the input is double-encoded.
- **Test approach:** Positive — write a fixture with literal `&amp;amp;` in FORM text (which lxml decodes once to `&amp;`, which `html.unescape` then decodes to `&`). Idempotency check on the cleaned output.
- **Notes:** The basic-round test deferred this. Worth adding here. **See OQ3** on whether `&lt;`/`&gt;` should also be unescaped (which would be problematic for the C014 angle-bracket case).

### Category 3: Unicode normalisation

#### C010 — FORM text is NFC-normalised
- **Pattern:** Pre-composed vs combining-character forms collapse to NFC.
- **Source:** Cleaner code; matters for Formosan orthographies that use diacritics.
- **Expected:** `unicodedata.normalize("NFC", form.text) == form.text` after cleaning.
- **Currently handled?** Yes, at S/FORM, W/FORM, M/FORM via the `.//FORM` XPath.
- **Test approach:** Positive on a fixture with NFD-decomposed accented characters at all three tier levels. Negative pin: TRANSL text is *not* NFC-normalised by `clean_trans` (verify by writing NFD text in TRANSL and asserting it survives unchanged — or flag if this is undesirable, see OQ6).

### Category 4: Tier-asymmetric "do not touch" pins (`original` vs `standard`)

These are the rules most clearly stated in the transcripts. They are also the rules `clean_xml.py` currently does **not** implement — the cleaner applies the same logic to both tiers. We test them as **negative pins on `original`** (cleaner must not touch this) and **negative pins on `standard`** (cleaner should be silently tolerant if the input already lacks segmentation). They document desired future behaviour and currently-required tolerance.

#### C011 — Segmentation hyphens are preserved in `S/FORM[@kindOf="original"]`
- **Pattern:** Hyphens marking morpheme boundaries in the source-faithful tier must survive cleaning. The cleaner already does this (it has no rule against `-`), but the basic round does not pin it.
- **Source:** Lowking thesis card, Joshua May 20: "the `-`s ... should only be removed from the `<FORM kindOf="standard">` text at the `<S>` level. They should remain at the `<W>` level and shouldn't be relevant for the `<M>` level. (We are actually inconsistent about whether we remove them from the `<FORM kindOf="original">` at the `<S>` level, but in general I'd prefer to keep the 'original' as close to the actual original as possible!)"
- **Expected:** Hyphens in `S/FORM[@kindOf="original"]` survive cleaning byte-exact.
- **Currently handled?** Yes (trivially, since cleaner has no segmentation logic). The pin is to ensure future segmentation-stripping logic *targets the standard tier only*.
- **Test approach:** Fixture with `M-kan =ku n-hapuy.` in `S/FORM[@kindOf="original"]` → expect identical text out. Idempotency.
- **Notes:** This is a *positive* test today and a *negative pin* against future regression.

#### C012 — Segmentation hyphens in `S/FORM[@kindOf="standard"]`: strip OR warn, data-driven on the canonical orthography
- **Pattern:** Per user direction (2026-05-29), the cleaner's behavior on hyphens in S-level standard FORM depends on whether `-` appears as a "letter" row in the canonical orthography TSV for the file's `xml:lang`:
  - **If `-` is NOT a letter in the canonical orthography for the language**: hyphens are morpheme-boundary markers and must be stripped from `S/FORM[@kindOf="standard"]`. `M-kan =ku n-hapuy.` → `Mkan ku nhapuy.`
  - **If `-` IS a letter in the canonical orthography**: hyphens are part of the orthography and must be preserved. The cleaner emits a WARNING listing each occurrence in a CSV (since morpheme-boundary hyphens cannot be reliably distinguished from orthographic hyphens without context). The warning is suppressed when `clean_xml.py` is run with a `--hard-remove-segmentation` flag (which currently does not exist — this is a B-deferred feature).
- **Implementation must be data-driven, not hardcoded.** The cleaner looks up `Orthographies/<canonical>/<Language>.tsv` (currently `<canonical>` = `Ortho113`) and checks whether `-` appears as a row in column 1 (the "letter" column). This way, switching to a different canonical orthography (e.g., `Ortho94`) only requires changing the lookup path, not editing a hardcoded language list.
- **Empirically (verified 2026-05-29)**, `-` is a letter in:
  - `Orthographies/Ortho113/Bunun.tsv` (`xml:lang="bnn"`)
  - `Orthographies/Ortho113/Thao.tsv` (`xml:lang="ssf"`)
  Both rows have empty IPA mapping columns, consistent with `-` being a literal orthographic character rather than a phoneme. The list may change if the canonical orthography is updated; that's fine — the data-driven lookup handles it automatically.
- **Source:** Lowking thesis card (Joshua May 20) + user direction (2026-05-29).
- **Currently handled?** **No.** The cleaner currently leaves S-standard hyphens alone in all cases. The new behavior requires (a) reading the canonical orthography TSV to check `-` membership for the file's `xml:lang`, (b) conditional stripping, (c) CSV warning infrastructure, (d) a `--hard-remove-segmentation` CLI flag.
- **Test approach:** All `xfail` until B implements:
  - **xfail**: Amis fixture (`xml:lang="ami"`, `-` not in Ortho113/Amis) with `M-kan =ku n-hapuy.` in `S/FORM[@kindOf="standard"]` → expect `Mkan ku nhapuy.`.
  - **xfail**: Bunun fixture (`xml:lang="bnn"`) with hyphens in standard → unchanged, WARN emitted, CSV row appended.
  - **xfail**: Thao fixture (`xml:lang="ssf"`) — same as Bunun (negative pin against any future hardcoded "Bunun only" implementation).
  - **xfail**: any of the above + simulated `--hard-remove-segmentation` flag → hyphens stripped regardless of orthography.
- **Notes:** The W-level case is C013 (hyphens preserved at all tiers). The M-level case is moot per Joshua ("shouldn't be relevant for `<M>` level"). Looking up the canonical-orthography TSV at clean time is new infrastructure for the cleaner; the design assumes B will add this.

#### C013 — Segmentation in `W/FORM` is preserved at both tiers
- **Pattern:** The W tier must keep its `-`, `<`, `>`, `=` segmentation markers regardless of `kindOf`.
- **Source:** Amis Adversative card Apr 3: "We actually want the segmentation (the -, <, >, and =) in the W FORMs, too." Also Amis pa-verbs card Apr 3: "leave ø markers in the W FORM".
- **Expected:** A W-level FORM containing `Pa-rakat-en` or `r<um>akat` or `=ku` survives cleaning unchanged.
- **Currently handled?** Mostly yes (cleaner does not strip `-` or `=`). However: `swap_punctuation` does not touch `<` or `>` directly, but if they appear as escaped XML entities `&lt;` / `&gt;` the html.unescape branch may interact (see OQ3). And `[` / `]` *are* in the swap table and get rewritten to `(` / `)` — which would corrupt any W-level FORM that uses square brackets for some other purpose.
- **Test approach:** Three positive pins: W/FORM with `-`, with `=`, with `<um>` literal angle brackets. Idempotency.
- **Notes:** The `<um>`-in-W-FORM case requires the input to use escaped entities (since the file must be parseable XML); on disk the FORM text would be `<FORM>r&lt;um&gt;akat</FORM>` which lxml reads as `r<um>akat`. Joshua's instruction (Serial Verbs card, Mar 3, "Issue #2 ... you can't have `<AV>` in the gloss because the brackets will be read as XML tags! If you need to include `<AV>` in a gloss, you need to escape the brackets") is a *student instruction* about how to *write* such content in XML, not a cleaner rule — but if the cleaner ever changes to unescape `&lt;`/`&gt;` it would silently corrupt these W-level FORMs. That's exactly what the pin guards against. See OQ3.

### Category 5: Tag-like content in glosses (TRANSL on W/M)

#### C014 — Angle-bracket-shaped gloss labels survive cleaning
- **Pattern:** Glosses like `walk<AV>-FAC` (with literal `<AV>` from the source's infix notation, stored on disk as `walk&lt;AV&gt;-FAC`) must survive cleaning intact.
- **Source:** Serial Verbs card, Issue #6 / Mar 3 edit Apr 3: "the < and > need to be escaped in the first line ... So it should end up looking like `<TRANSL xml:lang="en">walk&lt;AV&gt;-FAC</TRANSL>`."
- **Expected:** A TRANSL whose on-disk text is `walk&lt;AV&gt;-FAC` parses to `walk<AV>-FAC` and stays `walk<AV>-FAC` after cleaning (and the on-disk re-serialisation re-escapes the angle brackets).
- **Currently handled?** Yes for the *content* (cleaner doesn't touch angle brackets in TRANSL), but it's worth pinning because of the html.unescape branch (which is currently scoped to FORM only, not TRANSL — confirm in test). **Critically**, this is *not* exercised by the basic-round HTML-entities test, which only checks FORM and only for `&amp;`.
- **Test approach:** Positive pin — fixture with `walk&lt;AV&gt;-FAC` in W/TRANSL; assert parsed text is preserved verbatim. Re-serialised file should still parse the same way.
- **Notes:** This is a cleaner-side pin against a future change to "unescape entities" in TRANSL or to remove angle-bracket-like tokens.

### Category 6: Out-of-scope patterns from transcripts (negative pins, document only)

These are patterns Joshua flagged that are real corpus issues but are **not** `clean_xml.py`'s responsibility. We list them here so future Joshua-or-Claude reads of the transcripts won't accidentally redirect `clean_xml.py` to handle them. Each lists the scope owner.

**Per user direction (2026-05-29)**: many of the patterns in this category SHOULD be automated somewhere — they're real issues, just not the cleaner's job. They are tracked as candidates for sub-project B's planning under "Category 6 candidates for B" in B's roadmap section. See [2026-05-27-roadmap.md](2026-05-27-roadmap.md) section B for the consolidated list of which ones B should consider automating (e.g., footnote-residue detection, out-of-language flagging, multi-word-gloss normalisation).

#### C015 — Footnote numbers stuck onto morphemes (e.g. `uwal` → `speak12`)
- **Source:** Amis Adversative card Apr 3 (`s13w4m2`: "See the 12?"). Hunter's Truku card May 18 lists "stripped footnote nums / doubled-period artifacts" as fixed in *scraping*.
- **Owner:** Scraper / `CodeAndDocs/`. Not `clean_xml`.

#### C016 — Out-of-language examples (Japanese, Fongbe, Tagalog in an "Amis" or "Bunun" file)
- **Source:** Amis Adversative card Apr 3, Bunun card Chapter 1, Serial Verbs Issue #10.
- **Owner:** Scraping decisions / per-language XML split. Not `clean_xml`.

#### C017 — Apostrophes / quote characters in `id` attributes — **MOVED to XML validation design (2026-05-29)**
- **Source:** Bunun card, item 13: "Don't use `'` in sentence IDs."
- **Owner:** XML validator (per user direction 2026-05-29). The cleaner does not and should not touch attributes; this is an XML structural correctness concern. A corresponding rule has been added to [2026-05-29-xml-validation-design.md](2026-05-29-xml-validation-design.md). No test needed in the clean_xml suite.

#### C018 — `=` clitic markers vs `-` morpheme markers
- **Source:** Amis Adversative card (`=` retained in glosses, `=` and `-` both split on); Lowking card May 20 (extensive discussion); Bunun card item 11.
- **Owner:** Scraping / linguistic encoding. Cleaner must preserve both (covered by C011, C013).

#### C019 — Stroke-through `đ` and similar non-standard letterforms — **NEGATIVE PIN (per user direction 2026-05-29)**
- **Pattern:** Non-standard letterforms like `đ` (Latin small letter d with stroke, U+0111) appear in some Bunun corpora as intentional orthographic choices, not OCR mistakes.
- **Source:** Bunun card item 8: "the `d`s with the line through them are not mistakes. ... I don't think this letter exists in modern orthographies. The closest is `đ`." User direction (2026-05-29): "Yes, let's add that negative pin test."
- **Expected:** `đ` in FORM text survives cleaning byte-exact. The cleaner must not silently substitute it for `d` or similar.
- **Currently handled?** Yes (trivially — cleaner has no rule against `đ`). The pin guards against (a) future re-enabling of the dead `remove_nonlatin` function, or (b) addition of a "standardize-non-ASCII-letters" rule that would conflate `đ` with `d`.
- **Test approach:** Positive pin — fixture with `đ` in `S/FORM[@kindOf="original"]` for an `xml:lang="bnn"` corpus. After cleaning, assert `đ` survives. Idempotency.
- **Notes:** Owner of the linguistic decision (is `đ` a legitimate Bunun letter?) is the per-language reference orthography (`Orthographies/Ortho113/Bunun.tsv` or successor). Standardisation work belongs to `QC/utilities/standardize.py`, not the cleaner. The cleaner's job is to NOT corrupt the source.

#### C020 — Underscores in FORM are preserved — **NEGATIVE PIN (per user direction 2026-05-29)**
- **Pattern:** Underscores (`_`, U+005F) in FORM text are preserved verbatim by the cleaner. Some languages may use underscores as part of spelling rules; the cleaner must not substitute them for hyphens, spaces, or anything else.
- **Source:** Bunun card item 9-10: "he's segmenting using underlines instead of dashes ... I would do this in the TXTs directly and rerun your code." User direction (2026-05-29): "Just want to make sure that clean_xml.py is not removing any underscores, since those can be part of spelling rules for a number of languages. Better to leave in during clean_xml.py."
- **Expected:** `_` in FORM text survives cleaning byte-exact.
- **Currently handled?** Yes (trivially — cleaner has no rule against `_`). The pin guards against future "normalize underscores to hyphens" or similar rewrites.
- **Test approach:** Positive pin — fixture with `is_saiv` in `S/FORM[@kindOf="original"]`. After cleaning, assert `is_saiv` survives. Idempotency.
- **Notes:** If a scrape has used `_` as a segmentation marker by mistake (Bunun card item 9-10 case), the fix belongs in the scraper, not the cleaner. The cleaner's job is to NOT silently transform user-meaningful characters.

#### C021 — Multi-word glosses that should be joined with `.` (e.g. `go to` → `go.to`)
- **Source:** Bunun card item 14.
- **Owner:** Scraper / linguistic conventions doc. Cleaner does not (and should not) parse gloss structure.

#### C022 — Sentence-initial `*` (ungrammaticality marker): warn with CSV, do NOT remove
- **Pattern:** Per user direction (2026-05-29): when a `*` appears anywhere in an S-level FORM (sentence-initial or otherwise), the cleaner emits a WARNING listing each case in a CSV (file, S id, position). The cleaner does NOT structurally remove the `<S>` (unlike the `456otca` sentinel of C008). The `*` usually indicates an error earlier in the pipeline that should be rectified upstream, not silenced in the cleaner.
- **Source:** Lowking card May 18 ("If the `*` is at the beginning of the sentence, that means the whole thing is ungrammatical and should be excluded") + user direction (2026-05-29 — the cleaner's job is to surface, not to delete).
- **Currently handled?** No.
- **Test approach:** **xfail** until B adds warning + CSV infrastructure. Fixture: a corpus with one S whose FORM contains `*Mu ka patas nii.` and one normal S → cleaner runs cleanly (returncode 0), the `*`-containing S is preserved verbatim, a CSV row for the occurrence is emitted.
- **Notes:** Contrast with C008's `456otca` sentinel which DOES trigger structural removal. The difference: `456otca` is a known corpus-specific artefact with no linguistic meaning; `*` is a linguistic annotation whose presence informs upstream debugging.

#### C023 — `/` indicates alternative forms; both should produce separate sentence entries
- **Source:** Lowking card May 18 (multiple sub-discussions about `/`); Amis Adversative card on `ver="alt"` TRANSL convention.
- **Owner:** Scraper. Cleaner sees the result, not the slashes.

#### C024 — Parentheses in free translations: sometimes drop, sometimes keep
- **Source:** Bunun card item 7 ("page 68 ... words enclosed in parentheses ... are necessary to make it a grammatical English sentence ... you can *probably* delete parentheses throughout"); Serial Verbs Issue #3 ("two possible translations, one with `has` and one without ... I would *not* update your code for all files"); Lowking card on `(ka yaku)` for omitted subjects.
- **Owner:** Scraper / corpus-specific decisions. Joshua explicitly says this is too idiosyncratic to generalise. Cleaner must leave parentheses alone in TRANSL.
- **Negative pin worth adding:** TRANSL containing `(has)` survives cleaning unchanged.

### Category 7: Cross-cutting

#### C025 — Idempotency on every positive
- **Pattern:** Running the cleaner twice on the same file yields the same result as running it once.
- **Source:** Basic round already pins this for one fixture; this round pins it for every new positive.
- **Test approach:** Parametrise an idempotency wrapper over all positive fixtures introduced above.

#### C026 — Non-mutation on every negative pin
- **Pattern:** When the cleaner *should not* change something, the file's content must be byte-exact (or at minimum, every relevant FORM/TRANSL text must be byte-exact). Joshua's bar from CLAUDE.md ("never claim work is done ... without quoting the actual output") translates here to "negative pins must be byte-exact, not just 'no obvious change'".
- **Source:** Basic round's `test_already_clean_xml_is_left_intact` already does this for one whole file.
- **Test approach:** For tier-asymmetric negative pins, prefer asserting on the parsed text of a specific `kindOf` FORM (not whole-file byte equality), because the cleaner *will* legitimately rewrite serialisation whitespace if any element in the file changes. Whole-file byte equality is the right assertion only when no element should change.

## Out of scope (deferred or unclear)

- **Corpus-mined positive/negative fixtures from `Corpora/`.** Per user direction (2026-05-29), this work belongs to sub-project B. The parent design (`2026-05-28-a-test-infrastructure-design.md`, line 316) also defers "deep fixtures" as their own round. This design intentionally restricts itself to transcript-derived patterns and code-derived behaviours.
- **Validators (`validate_xml.py`, `validate_punct.py`, `validate_glosses.py`).** Several patterns (gloss-count vs morpheme-count mismatch on Bunun item 9, ISO-639-3 attribute checks, DTD conformance) are validator territory, not cleaner. **Per user direction (2026-05-29): if any such checks currently live in `clean_xml.py` they should be moved out — audit during B5 (see Deferred to B).**
- **Standardisation (`standardize.py`).** C012 (segmentation stripping from standard tier, partial) and broadly the original→standard transliteration are standardisation, not cleaning. The cleaner's job is character-level cruft removal; transliteration mapping belongs to standardisation. (C019's `đ` pin is now IN-scope per user direction — see C019.)
- **`remove_nonlatin` re-enabling.** Per user direction (2026-05-29): `remove_nonlatin` should be DELETED from the source, not preserved as dead code. It was mainly for the Wikipedia corpora and has been incorporated into the dedicated pipeline there. Captured as a B5 item (see Deferred to B).
- **The two commented-out functions** (`fix_parentheses`, `process_punctuation`) at the top of the source. Not behaviour. Possibly worth deleting in a follow-up cleanup PR but not part of this test design.
- **Bunun item 9's "underline as segmentation" auto-conversion.** Per user direction (2026-05-29): handled in B, not the cleaner. Joshua's original instruction was that the fix lives in the TXT-preparation step before scraping.

## Open questions

OQ1, OQ2, OQ4, OQ5, OQ6, OQ7, OQ8 resolved by user direction (2026-05-29) — resolutions are reflected inline in the affected rules (C001, C002, C008, C010, C012, C022).

1. **OQ3 — Should `&lt;` and `&gt;` be unescaped on TRANSL/FORM? (CONDITIONAL)** User direction (2026-05-29): "We tried to unescape everything at an early step because we ran into problems with our removal of junk characters. If that's no longer an issue, then I'm OK not doing it." So the resolution is conditional on whether the original junk-char-removal problem still exists. Investigation needed before B can decide whether to keep, restrict, or remove the `html.unescape` branch. **Also note (user, 2026-05-29):** orthography extraction and testing definitely DO need to handle escapes — without that, each part of an escape sequence is treated as a separate character. This is a downstream concern, separate from the cleaner. Capture as a follow-up note for the orthography extraction pipeline.

2. **OQ9 — `clean_trans` skips `swap_punctuation` and `remove_junk_chars`; is this by design?** User direction (2026-05-29): user is not certain. The asymmetry exists in the code but is uncommented. Best inference: the author wanted to avoid mangling translation text (Chinese full-width punctuation, English curly quotes). The 2026-05-29 language-aware rules (C001 / C002) effectively codify this intent with explicit `xml:lang` branching, replacing the implicit asymmetry. Decision pending: document the asymmetry as a docstring now, OR let the asymmetry evolve into the C001/C002 language-aware behavior in B5 and update the docstring then.

## Deferred to sub-project B

The 2026-05-29 user resolutions imply substantial new infrastructure that the current `clean_xml.py` does not have. Tracked here so the tests can be written as `xfail` against the desired behavior and will flip to pass automatically when B implements:

1. **Language-aware cleaning.** `clean_text` and `clean_trans` (or their successor) must consult `xml:lang` on the parent or sibling and branch behavior accordingly. Affects C001 (FORM/non-Chinese TRANSL only) and C002 (Branch A vs Branch B). Required: a helper that resolves the "effective" `xml:lang` for any FORM or TRANSL element (walk up to the nearest ancestor with `xml:lang`, fall back to the root `<TEXT xml:lang>`).

2. **Warning + CSV output infrastructure.** When a rule emits a warning rather than a transformation, the cleaner must append a row to a per-rule CSV (or one consolidated CSV with rule-ID column). Used by C002 Branch B (single-quote / Latin-quote warnings in Chinese TRANSL), C002b (U+02C8 IPA stress), C012 (segmentation hyphens in orthographies that include `-`), C022 (sentence-initial `*`).

3. **Canonical-orthography TSV lookup at clean time.** C012's data-driven hyphen rule requires the cleaner to read `Orthographies/<canonical>/<Language>.tsv` for the file's `xml:lang` and check whether `-` appears as a letter. The lookup path (currently `Orthographies/Ortho113/`) should be configurable so switching the canonical orthography in the future requires only a config change.

4. **`--hard-remove-segmentation` CLI flag.** Overrides C012's "preserve and warn" branch for orthographies that include `-`, forcing stripping regardless. Default off.

5. **Transformation counter output.** Per user direction (2026-05-29): the cleaner should keep counts of every character it transformed (including deletions) and emit a list with counts to the terminal at the end of each run, so the operator notices unexpected changes. Suggested format: a table of (input character → output character → count), one row per distinct transformation, sorted by count descending.

6. **Existing-corpora remediation.** Joshua noted at C001 and C002 that some existing corpora may have been incorrectly stripped of language-appropriate Chinese punctuation by the unconditional `swap_punctuation`. After B implements language-awareness, a one-off corpus audit will be needed to find and fix affected TRANSL elements. This is a B-Phase remediation item, not part of clean_xml itself.

7. **Delete `remove_nonlatin`.** Per user direction (2026-05-29): `remove_nonlatin` is dead code in `clean_xml.py`, originally for the Wikipedia corpora but since incorporated into the Wikipedia-dedicated pipeline. Delete it from the source.

8. **Audit `clean_xml.py` for validator-territory checks.** Per user direction (2026-05-29): if `clean_xml.py` currently performs any checks that belong to a validator (gloss-count vs morpheme-count mismatch, ISO-639-3 attribute checks, DTD conformance, etc.), move those checks into the appropriate `validate_*.py` script and remove them from the cleaner. Test them in the validator's test suite. The cleaner's responsibility is character-level cruft removal, nothing more.

9. **OQ9 docstring update.** Per user direction (2026-05-29): after B5's language-aware C001/C002 rules land, add a docstring to `clean_text`/`clean_trans` (or their successors) documenting the asymmetry. Update follows the implementation; doc it then.

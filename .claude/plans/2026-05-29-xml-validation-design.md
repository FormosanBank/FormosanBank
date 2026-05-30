# XML Validation Design

**Date:** 2026-05-29
**Status:** Draft for user review
**Parent:** [2026-05-28-a-test-infrastructure-design.md](2026-05-28-a-test-infrastructure-design.md), sub-project A Task 6

## Goal

Enumerate every check the FormosanBank XML validator *should* perform, so the next iteration of `QC/validation/validate_xml.py` (and its tests) is driven by an explicit, reviewable spec rather than by whatever the DTD + XSD + Python currently happen to enforce. This document is the source of truth for the new validator. Each rule has a stable ID, a severity, a source citation, and a note on whether the current validator catches it — so the test fixtures can target rules one-to-one and we can see at a glance where the existing implementation is silent, partial, or wrong. Where the GitBook spec, DTD, and XSD have drifted, this document records both positions and defers the resolution to the user via numbered open questions; it does not invent a winner.

## Sources

- GitBook spec: `/Users/jkhartshorne/Documents/Projects/Formosan/FormosanBankGitbook/en-us/the-bank-architecture/formosanbank-xml-format.md`
- DTD: `/Users/jkhartshorne/Documents/Projects/Formosan/FormosanBank/QC/validation/xml_template.dtd`
- XSD: `/Users/jkhartshorne/Documents/Projects/Formosan/FormosanBank/QC/validation/xml_template.xsd`
- Current validator: `/Users/jkhartshorne/Documents/Projects/Formosan/FormosanBank/QC/validation/validate_xml.py`
- ISO 639-3 reference: `/Users/jkhartshorne/Documents/Projects/Formosan/FormosanBank/QC/validation/iso-639-3.txt`
- Dialect reference: `/Users/jkhartshorne/Documents/Projects/Formosan/FormosanBank/dialects.csv`
- Project conventions: `/Users/jkhartshorne/Documents/Projects/Formosan/FormosanBank/CLAUDE.md`
- User-specified rules (verbatim in the parent task brief, 2026-05-28)

## Glossary of severity levels

- **HARD**: validation fails on any violation. The test asserts the validator returns a non-empty list of findings for that rule, and (in production) the validator exits non-zero.
- **SOFT (counted)**: validation does NOT fail; the validator emits a count and identifies the offending elements so an operator can review. The canonical example is "missing `standard` FORM": some corpora legitimately ship without a standard tier because the orthography is unsettled, but we still want to know how many elements are missing it so we can spot the case where the standard tier exists for most items and is missing for just a handful.
- **WARN**: validation surfaces a note but does not fail and does not contribute to the "things that need triage" count. Used for stylistic or near-future-deprecation issues.

## Rules

Each rule below has:
- **ID** — stable identifier (V001…)
- **Rule** — one-line statement
- **Severity** — HARD / SOFT / WARN
- **Description** — what the rule actually checks
- **Source** — GitBook / DTD / XSD / user / CLAUDE.md / convention
- **Currently checked by `validate_xml.py`?** — Yes / Partial / No (with brief reason)
- **Example violation** — what a fixture targeting this rule would look like

### Structural / hierarchy

#### V001 — Root element must be `<TEXT>`
- **Severity:** HARD
- **Description:** The document root must be `TEXT`. No other root is acceptable.
- **Source:** GitBook ("The `<TEXT>` represents the entire document. It is the root element"); DTD; XSD.
- **Currently checked?** Yes (via XSD).
- **Example violation:** Document rooted at `<S>` directly.

#### V002 — `<TEXT>` is the only required element
- **Severity:** HARD (a file with no `<TEXT>` fails V001; a `<TEXT>` with zero children passes V002)
- **Description:** Per the user-supplied rules, the only element that *must* exist is `<TEXT>`. A `<TEXT>` containing no `<S>` is permitted by this rule (e.g., a stub or metadata-only file). This is a deliberate relaxation of the DTD/XSD, which both require `S+` / `S` with `maxOccurs="unbounded"` (the minimum is therefore 1).
- **Source:** User-supplied rules (verbatim). Conflicts with DTD `(S+)` and XSD `minOccurs` default of 1 on `S`. See OQ1.
- **Currently checked?** No — current validator (via XSD) *rejects* a `<TEXT>` with zero `<S>`. The proposed rule would *accept* it.
- **Example violation:** None directly; this rule loosens an existing one. See OQ1.

#### V003 — `<S>` only appears as a child of `<TEXT>`
- **Severity:** HARD
- **Description:** No `<S>` may appear anywhere except as a direct child of `<TEXT>`. Nesting `<S>` inside `<S>`, `<W>`, `<M>`, or anywhere else is forbidden.
- **Source:** GitBook ("It can only be a sub-element of the `<TEXT>` element"); user-supplied rules.
- **Currently checked?** Yes (via XSD content model).
- **Example violation:** `<W><S>...</S></W>`.

#### V004 — `<W>` only appears as a child of `<S>`
- **Severity:** HARD
- **Description:** No `<W>` may appear except as a direct child of `<S>`. Nesting `<W>` inside `<W>`, `<M>`, or `<TEXT>` directly is forbidden.
- **Source:** GitBook; user-supplied rules.
- **Currently checked?** Yes (via XSD content model).
- **Example violation:** `<TEXT><W>...</W></TEXT>` without an intervening `<S>`.

#### V005 — `<M>` only appears as a child of `<W>`
- **Severity:** HARD
- **Description:** No `<M>` may appear except as a direct child of `<W>`. Forbidden: `<S><M>…</M></S>`, `<M><M>…</M></M>`, `<TEXT><M>…</M></TEXT>`.
- **Source:** GitBook; user-supplied rules.
- **Currently checked?** Yes (via XSD content model).
- **Example violation:** `<S><M>...</M></S>`.

#### V006 — Sister element order does NOT matter; only nesting hierarchy is constrained
- **Severity:** N/A (informational; no rule violation possible from sibling order alone)
- **Description:** Per user direction (2026-05-29): the nesting hierarchy (V003–V005: `<M>` in `<W>`, `<W>` in `<S>`, `<S>` in `<TEXT>`) is the load-bearing structural rule. The order of sister elements (FORM, TRANSL, AUDIO, W/M) within a parent is NOT a validation concern. The XSD currently enforces a specific order via `xs:sequence`; this is incorrect and the constraint should be removed.
- **Source:** User direction (2026-05-29).
- **Currently checked?** Yes — incorrectly — via XSD.
- **Example violation:** None; this rule documents the relaxation.
- **Follow-up:** XSD needs an edit to remove the `xs:sequence` order constraint on `<S>`, `<W>`, `<M>` content models (e.g., switch to `xs:all` or `xs:choice` with `maxOccurs="unbounded"`).

### FORM tier rules

#### V010 — `<S>` has at least one `<FORM>`
- **Severity:** SOFT
- **Description:** Every `<S>` will typically contain at least one `<FORM>` child. However, it is possible in the future there will be diarized audio that is untrascribed, in which case there may be <S>s without a <FORM>. Warn the user and count the occurrences so that they can confirm the missing <FORM>s are expected to be missing. 
- **Source:** User-supplied rules; GitBook ("`<FORM>` must be included at the lowest level of the hierarchy"); XSD (`minOccurs="1"`).
- **Currently checked?** Yes (via XSD).
- **Example violation:** `<S id="S1"><W>…</W></S>` (no FORM under S).

#### V011 — `<W>` has at least one `<FORM>`
- **Severity:** HARD
- **Description:** Every `<W>` must contain at least one `<FORM>` child.
- **Source:** User-supplied rules; GitBook; XSD.
- **Currently checked?** Yes (via XSD; `minOccurs` defaults to 1).
- **Example violation:** `<W id="S1W1"><M>…</M></W>`.

#### V012 — `<M>` has at least one `<FORM>`
- **Severity:** HARD
- **Description:** Every `<M>` must contain at least one `<FORM>` child.
- **Source:** User-supplied rules; GitBook; DTD; XSD.
- **Currently checked?** Yes (via XSD; via DTD).
- **Example violation:** `<M id="S1W1M1"><TRANSL xml:lang="en">…</TRANSL></M>`.

#### V013 — Every `<S>`, `<W>`, `<M>` has an `<FORM kindOf="original">`
- **Severity:** HARD
- **Description:** For each `<S>`, `<W>`, and `<M>`, exactly one of its direct child `<FORM>` elements must have `kindOf="original"`. The "original" tier is mandatory at every annotated level.
- **Source:** User-supplied rules ("There should always be an 'original' tier"); GitBook.
- **Currently checked?** Partial — the commented-out `validated_form` function in `validate_xml.py` did roughly this check at the S and W (and ambiguously M) levels, but it is disabled. The XSD allows up to 2 FORMs with `kindOf in {original, standard, alternate}` but does *not* require the `original` value to be present.
- **Example violation:** `<S id="S1"><FORM kindOf="standard">…</FORM></S>` (only a standard FORM, no original).

#### V014 — Missing `<FORM kindOf="standard">` is counted, not fatal
- **Severity:** SOFT (counted)
- **Description:** For each `<S>`, `<W>`, and `<M>` that lacks a child `<FORM kindOf="standard">`, the validator records the element id and contributes to a per-file and per-corpus count of "missing standard FORM". Validation does NOT fail when this count is non-zero. The point is to surface the difference between "this corpus has no standard tier at all" (expected for unsettled orthographies) and "this corpus has a standard tier for most items but is missing it for these N items" (very probably a bug).
- **Source:** User-supplied rules (verbatim and emphatic).
- **Currently checked?** No. The disabled `validated_form` would have made this HARD, not SOFT. The current active code does not check it at all.
- **Example violation (for the counter, not for failure):** `<W id="S1W1"><FORM kindOf="original">…</FORM></W>` — contributes 1 to the missing-standard count.
- **Output format:** SOFT-count reports emit CSV (per user direction 2026-05-29: easier for humans, parseable by downstream skills).

#### V015 — At most one `<FORM>` per `kindOf` value at each level
- **Severity:** HARD
- **Description:** Within a single `<S>`, `<W>`, or `<M>`, you may not have two `<FORM>` children with the same `kindOf` (e.g., two `original` FORMs under the same `<S>` is forbidden).
- **Source:** Implied by GitBook (each tier represents one canonical form for that element); XSD enforces `maxOccurs="2"` but does not enforce distinctness of `kindOf`.
- **Currently checked?** No.
- **Example violation:** `<W><FORM kindOf="original">a</FORM><FORM kindOf="original">b</FORM></W>`.

#### V016 — `FORM/@kindOf` is a known value
- **Severity:** HARD
- **Description:** `FORM/@kindOf` must be one of `original`, `standard`, `alternate`. The XSD currently enumerates these three; the GitBook spec only mentions `original` and `standard`.
- **Source:** XSD enumeration; user direction confirms `alternate` is real (2026-05-29).
- **Currently checked?** Yes (via XSD).
- **Example violation:** `<FORM kindOf="draft">…</FORM>`.
- **Follow-up:** GitBook needs an update to document `alternate` as a valid `kindOf` value (per user direction 2026-05-29).

#### V017 — `FORM` has non-empty text content
- **Severity:** HARD
- **Description:** A `<FORM>` whose text content is empty or whitespace-only is a bug — there is no legitimate use for an empty FORM.
- **Source:** User direction (2026-05-29); convention. XSD currently allows empty content (`xs:string`) and should be tightened.
- **Currently checked?** No.
- **Example violation:** `<FORM kindOf="original"></FORM>`.
- **Follow-up:** XSD should constrain `FORM` text to non-empty (e.g., via `xs:simpleType` with `xs:minLength="1"` after whitespace stripping).

### TRANSL rules

#### V020 — `<TRANSL>` count on `<S>` and `<W>` is unconstrained
- **Severity:** N/A (informational; no rule violation possible)
- **Description:** `<S>` and `<W>` may have 0..N `<TRANSL>` children with no constraints on count or `kindOf`.
- **Source:** GitBook; XSD (`maxOccurs="unbounded"`).
- **Currently checked?** N/A.

#### V021 — On `<M>`, if exactly 1 `<TRANSL>`, it must be `kindOf="original"`
- **Severity:** HARD
- **Description:** Per the user-supplied rules: an `<M>` may have 0 or N `<TRANSL>` children. If it has exactly 1, that one TRANSL must be marked `kindOf="original"`. (Rationale: a single morpheme-level gloss is always the original gloss; an updated/standardized gloss makes no sense without an original to standardize from.)
- **Source:** User-supplied rules (verbatim).
- **Currently checked?** No.
- **Example violation:** `<M><FORM kindOf="original">ʕa</FORM><TRANSL xml:lang="en">1SG</TRANSL></M>` (the lone TRANSL lacks `kindOf="original"`).

#### V022 — On `<M>`, multiple `kindOf="original"` TRANSLs must have distinct `xml:lang`
- **Severity:** HARD
- **Description:** Per the user-supplied rules: if an `<M>` has more than one `<TRANSL kindOf="original">`, each such TRANSL must have a different `xml:lang` value. (Use case: morphological glosses provided in multiple languages, e.g., English and Mandarin; "original" here marks each as the original-language gloss in its respective language, not as a standardized rendering.)
- **Source:** User-supplied rules (verbatim).
- **Currently checked?** No.
- **Example violation:** Two `<TRANSL kindOf="original" xml:lang="eng">` siblings under the same `<M>`.

#### V023 — `TRANSL/@xml:lang` is required when present
- **Severity:** HARD
- **Description:** Every `<TRANSL>` element must have an `xml:lang` attribute. The DTD declares it `#REQUIRED`; the XSD declares it as a referenced attribute but without `use="required"`, so the XSD does NOT enforce this. See OQ5.
- **Source:** DTD (`xml:lang CDATA #REQUIRED`); GitBook ("Attributes: `xml:lang`: The language code…"); XSD does not require.
- **Currently checked?** Partial — only the DTD enforces this, and the active validator uses the XSD, not the DTD. So in practice this is **not** enforced.
- **Example violation:** `<TRANSL>…</TRANSL>` with no `xml:lang`.

#### V024 — `TRANSL/@xml:lang` must be a valid ISO 639-3 code
- **Severity:** HARD
- **Description:** The `xml:lang` value on every `<TRANSL>` must match an `Id` in `QC/validation/iso-639-3.txt`. Currently the validator only checks the `xml:lang` on `<TEXT>`, not on `<TRANSL>`.
- **Source:** GitBook ("`xml:lang`: The language code for the translation, using the ISO 639-3 standard").
- **Currently checked?** No — `validate_lang_code` only inspects the root.
- **Example violation:** `<TRANSL xml:lang="eng-US">…</TRANSL>` or `<TRANSL xml:lang="zz">…</TRANSL>`.

#### V025 — `TRANSL/@kindOf` at `<S>` and `<W>` is free-form or absent
- **Severity:** WARN (informational only)
- **Description:** On `<TRANSL>` elements that are children of `<S>` or `<W>`, the `kindOf` attribute is free-form or absent. Typical values describe the translation tool/method (e.g., `kindOf="DeepL"`, `kindOf="manual"`). The validator does not enforce a vocabulary but can produce a per-corpus frequency report so operators notice typos like `kindOf="orginal"`.
- **Source:** User direction (2026-05-29); GitBook ("`kindOf` (optional): Specifies the method or tool used to generate the translation").
- **Currently checked?** No.
- **Example violation:** None (free-form). Spurious values like `"orginal"` would surface as low-frequency in a report.
- **Follow-up:** GitBook should make the S/W vs M asymmetry explicit if not already.

#### V026 — `TRANSL/@kindOf` at `<M>` must be `original` or `standard`
- **Severity:** HARD
- **Description:** On `<TRANSL>` elements that are children of `<M>` (morpheme-level), `kindOf` must be either `original` or `standard`. No free-form values, no other enumerated values. This is stricter than the GitBook's current generic TRANSL `kindOf` documentation and the S/W rule in V025.
- **Source:** User direction (2026-05-29).
- **Currently checked?** No.
- **Example violation:** `<M><FORM>…</FORM><TRANSL kindOf="DeepL" xml:lang="eng">…</TRANSL></M>`.
- **Follow-up:** GitBook needs an update to document the M-level `kindOf` controlled vocabulary (per user direction 2026-05-29).

### Attribute rules (xml:lang, kindOf, ids, TEXT metadata)

#### V030 — `TEXT/@id` is present and non-empty
- **Severity:** HARD
- **Description:** Every `<TEXT>` must have a non-empty `id` attribute (unique across resources, per GitBook — but cross-file uniqueness is V068 below).
- **Source:** GitBook; DTD; XSD.
- **Currently checked?** Yes (via XSD `nonEmptyString` + `use="required"`).
- **Example violation:** `<TEXT citation="…" …>` (no `id`).

#### V031 — `TEXT/@citation` is present and non-empty
- **Severity:** HARD
- **Description:** Required APA-style citation. May contain multiple citations separated by `|`.
- **Source:** GitBook; DTD; XSD.
- **Currently checked?** Yes (XSD).
- **Example violation:** `<TEXT citation=""/>`.

#### V032 — `TEXT/@BibTeX_citation` is present and non-empty
- **Severity:** HARD
- **Description:** Required BibTeX citation. Multiple entries separated by `,`.
- **Source:** GitBook; DTD; XSD.
- **Currently checked?** Yes (XSD).
- **Example violation:** Missing attribute.

#### V033 — `TEXT/@copyright` is present and non-empty
- **Severity:** HARD
- **Description:** Required license/copyright (e.g., `CC BY`).
- **Source:** GitBook; DTD; XSD.
- **Currently checked?** Yes (XSD).
- **Example violation:** Missing attribute.

#### V034 — `TEXT/@xml:lang` is present
- **Severity:** HARD
- **Description:** Required language code on root.
- **Source:** GitBook; DTD; XSD.
- **Currently checked?** Yes (XSD).
- **Example violation:** Missing attribute.

#### V035 — `TEXT/@xml:lang` is a valid ISO 639-3 code
- **Severity:** HARD
- **Description:** `xml:lang` value must match a row Id in `QC/validation/iso-639-3.txt`.
- **Source:** GitBook ("The language code using the ISO 639-3 standard"); CLAUDE.md.
- **Currently checked?** Yes (`validate_lang_code`).
- **Example violation:** `<TEXT xml:lang="en">` (en is 639-1, not 639-3) or `<TEXT xml:lang="zz">`.

#### V036 — `TEXT/@dialect`: present-and-valid OR absent-when-language-has-multiple-dialects
- **Severity:** HARD (invalid value) + WARN (missing when language has multiple dialects)
- **Description:** Two-way check:
  1. **HARD** — If `TEXT/@dialect` is set, it must match a dialect name in `dialects.csv` for the language identified by `TEXT/@xml:lang`.
  2. **WARN** — If `TEXT/@xml:lang` corresponds to a language that has multiple dialects in `dialects.csv` and `TEXT/@dialect` is NOT set, emit a warning. The corpus is plausibly missing dialect information that future analyses will want.
- **Source:** User direction (2026-05-29); GitBook ("Will only be used if the dialect name corresponds to one of the 42 official dialects."); CLAUDE.md; `dialects.csv`.
- **Currently checked?** No (neither direction).
- **Example violation:** `<TEXT … xml:lang="ami" dialect="MadeUpDialect">` (HARD — invalid dialect for Amis). Also: `<TEXT … xml:lang="ami">` with no `dialect` attribute (WARN — Amis has multiple dialects in dialects.csv).

#### V037 — `TEXT/@glottocode`, if present, is well-formed
- **Severity:** WARN
- **Description:** Glottocode format (per Glottolog) is `[a-z]{4}\d{4}`. We can validate the shape; validating against the live Glottolog database is out of scope.
- **Source:** GitBook ("Glottolog code").
- **Currently checked?** No.
- **Example violation:** `<TEXT … glottocode="not-a-code">`.

#### V038 — Every `<S>`, `<W>`, `<M>` has a non-empty `id`
- **Severity:** HARD
- **Description:** `id` is `#REQUIRED` on `<S>`, `<W>`, `<M>` per both DTD and XSD; XSD enforces `nonEmptyString`.
- **Source:** GitBook ("The only attribute these three elements take (and require) is the `id` attribute"); DTD; XSD.
- **Currently checked?** Yes (XSD).
- **Example violation:** `<S>…</S>` without an `id`.

#### V039 — `id` values are globally unique within a file
- **Severity:** HARD
- **Description:** Per user direction (2026-05-29): no two elements within a single XML file may share the same `id`, regardless of element type. This is stricter than per-element-type uniqueness — an `<S id="X">` and a `<W id="X">` in the same file is also forbidden. The GitBook example pattern (`S1`, `S1W1`, `S1W1M1`) makes collisions structurally unlikely, so the rule is cheap to enforce and tightens authoring discipline.
- **Source:** User direction (2026-05-29); convention.
- **Currently checked?** No.
- **Example violation:** Two `<W id="S1W1">` siblings, OR `<S id="X">` co-existing with `<W id="X">` anywhere in the same file.

#### V040 — Child id pattern is consistent with parent id (recommended)
- **Severity:** WARN
- **Description:** Per the GitBook example, `<W>` ids are prefixed by their `<S>` id (e.g., `S1W1`), and `<M>` ids by their `<W>` id (e.g., `S1W1M1`). This is a convention, not a hard rule. Flag deviations but do not fail.
- **Source:** GitBook example.
- **Currently checked?** No.
- **Example violation:** `<S id="S1"><W id="apple"><M id="banana">…</M></W></S>`.

#### V041 — `id` attributes contain no quote characters
- **Severity:** HARD
- **Description:** Per user direction (2026-05-29): `id` attribute values on `<TEXT>`, `<S>`, `<W>`, and `<M>` must not contain apostrophes (`'`), single quotes (`'`/`'`), double quotes (`"`/`"`/`"`), or backticks. Such characters are valid XML but break downstream tooling: they require escaping in XPath/CSS selectors, complicate cross-file references, and cause confusion in tools that grep for ids. Originally surfaced by the Bunun card (item 13: "Don't use `'` in sentence IDs") and confirmed as a validation concern (not a cleaner concern — cleaners don't touch attributes).
- **Source:** User direction (2026-05-29); Bunun student-review transcript.
- **Currently checked?** No.
- **Example violation:** `<S id="S1'a">` or `<W id='S1"W2'>` (the latter would also be a quote-mismatch XML well-formedness issue but is theoretically expressible via XML escaping).

### AUDIO rules

#### V050 — `<AUDIO>` presence is optional; mode is determined by `AUDIO/@file`, NOT by `TEXT/@audio`
- **Severity:** N/A (informational framework)
- **Description:** Per user direction (2026-05-29): the previous framing ("AUDIO only appears when TEXT/@audio is set") was wrong. `<AUDIO>` is optional and appears in one of two modes determined by the presence of `AUDIO/@file`:
  - **Segmented mode**: `AUDIO/@file` is set on each `<AUDIO>`, referencing a per-element audio file. `TEXT/@audio` may or may not be set in this mode — the AUDIO/@file values are sufficient.
  - **Single-file mode**: `AUDIO/@file` is absent. `TEXT/@audio` must then be set to a single audio file covering the whole document, and each `<AUDIO>` carries `start`/`end` indicating its segment within that file.
- **Source:** User direction (2026-05-29); GitBook.
- **Currently checked?** No — the current `validate_audio_attr` uses `TEXT/@audio` as the mode indicator and a magic value `"diarized"`, both of which are wrong.
- **Example violation:** None directly; this rule establishes the mode framework that V051–V053 enforce.

#### V051 — Segmented mode: every `<AUDIO>` with `@file` has a non-empty file path
- **Severity:** HARD
- **Description:** When an `<AUDIO>` has the `file` attribute set, the attribute value must be a non-empty path. Existence-on-disk is NOT checked (audio files are pulled per-corpus and may not be local; see Out of scope).
- **Source:** User direction (2026-05-29); GitBook.
- **Currently checked?** No (the current validator's `"diarized"` check is the wrong indicator entirely).
- **Example violation:** `<AUDIO file=""/>` or `<AUDIO file="   "/>`.

#### V052 — Single-file mode: when `AUDIO/@file` is absent, `TEXT/@audio` AND `AUDIO/@start` AND `AUDIO/@end` must all be set
- **Severity:** HARD
- **Description:** When an `<AUDIO>` has no `file` attribute, the validator infers single-file mode: there must be a `TEXT/@audio` attribute (specifying the single audio file for the document) AND the AUDIO must have `start` and `end` attributes (specifying its segment within that file). Missing any one of these three is a violation.
- **Source:** User direction (2026-05-29); GitBook.
- **Currently checked?** Partial — current validator requires start/end when TEXT/@audio is set to a non-"diarized" value, but the mode entry condition is wrong.
- **Example violation:** `<TEXT audio="lecture.wav"><S><AUDIO/></S></TEXT>` (no start/end). Also: `<TEXT><S><AUDIO start="0" end="1"/></S></TEXT>` (TEXT/@audio missing).

#### V053 — Orphan AUDIO: `AUDIO` with no `@file` AND `TEXT/@audio` not set
- **Severity:** HARD
- **Description:** Per user direction (2026-05-29): an `<AUDIO>` with no `file` attribute, in a document whose `<TEXT>` has no `audio` attribute, is unmoored — there is no way to determine which audio is being referenced. This is a violation regardless of whether `start`/`end` are present.
- **Source:** User direction (2026-05-29).
- **Currently checked?** No.
- **Example violation:** `<TEXT … (no audio attr) …><S><AUDIO start="0" end="1"/></S></TEXT>`.

#### V054 — `AUDIO/@start` and `@end` are non-negative numbers, `end >= start`
- **Severity:** HARD
- **Description:** `start` and `end` are seconds from the beginning of the audio. They must parse as non-negative floats and `end >= start`.
- **Source:** GitBook ("start and end times of the audio segment in seconds").
- **Currently checked?** No (XSD types them as `xs:string`).
- **Example violation:** `<AUDIO start="10" end="5"/>` or `<AUDIO start="abc" end="def"/>`.

#### V055 — `AUDIO/@url`, if present, is a syntactically valid URL
- **Severity:** WARN
- **Description:** Liveness checking is out of scope; syntactic check only.
- **Source:** GitBook (`url` attribute).
- **Currently checked?** No.
- **Example violation:** `<AUDIO url="not a url"/>`.

#### V056 — `AUDIO` is legal under `<TEXT>`, `<S>`, `<W>`, `<M>`
- **Severity:** HARD
- **Description:** Per user direction (2026-05-29): `<AUDIO>` may appear as a direct child of `<TEXT>`, `<S>`, `<W>`, or `<M>`. Placement elsewhere is a structural violation. The XSD currently allows AUDIO only on S/W/M and must be updated to also permit AUDIO at the TEXT level.
- **Source:** User direction (2026-05-29); GitBook.
- **Currently checked?** Partial — XSD allows S/W/M but not TEXT-level. XSD needs update.
- **Example violation:** `<TEXT><FORM>…</FORM><AUDIO/></TEXT>` — currently rejected by XSD but should be valid. Conversely, `<TEXT><AUDIO/>…</TEXT>`'s schema-rejection is currently coincident with what would be a real violation if `AUDIO` appeared somewhere truly invalid like inside `<FORM>`.

### W/M segmentation rules

#### V060 — `W` and `M` segmentation is optional
- **Severity:** N/A (informational; no rule violation possible)
- **Description:** `<S>` may have zero `<W>` children; `<W>` may have zero `<M>` children. Word- and morpheme-segmentation is provided only for corpora that have been segmented.
- **Source:** GitBook; XSD (`minOccurs="0"`); user-supplied rules.

#### V061 — `W/@class` and `W/@sclass`, if present, are non-empty
- **Severity:** WARN
- **Description:** The DTD/XSD permit `class` and `sclass` on `<W>` and `<M>` but don't enumerate valid values. Empty `class=""` is almost certainly an authoring mistake.
- **Source:** DTD; XSD.
- **Currently checked?** No.
- **Example violation:** `<W id="…" class="">…</W>`.

#### V062 — Infix marker on `<M>` requires angle-bracket gloss on parent `<W>`'s TRANSL
- **Severity:** HARD
- **Description:** Per user direction (2026-05-29): when an `<M>` has a FORM whose text starts AND ends with `-` (e.g., `-um-`, `-en-`) — indicating it represents an infix per GitBook's "Infixes and circumfixes" convention — the parent `<W>` must contain at least one `<TRANSL>` whose text includes a substring wrapped in `<` and `>` (e.g., `<um>`, `<AV>`). This pairing documents the infix at both the morpheme structural level (M FORM with `-X-` shape) and the gloss level (W TRANSL with `<X>` shape). Note: the angle-bracketed content does not need to textually match the infix; only the presence of *some* `<…>` substring is required.
- **Source:** User direction (2026-05-29); GitBook ("Infixes and circumfixes").
- **Currently checked?** No.
- **Example violation:** `<W><FORM>rumakat</FORM><TRANSL>walk</TRANSL><M><FORM>-um-</FORM></M></W>` — the M has an infix-shaped FORM but the W's TRANSL contains no `<…>` gloss.

#### V063 — Clitic `FORM`s preserve `=` markers (no mechanical check)
- **Severity:** N/A (deferred — no automatable check defined)
- **Description:** Per GitBook "Clitics": when writing the `M` FORM for a clitic, include `=` whether or not it was attached to the head word. Per user direction (2026-05-29): no mechanical check is enforced because false-positive rate is too high. Deferred to a future skill that can apply linguistic judgement.
- **Source:** GitBook ("Clitics"); user direction (2026-05-29 — deferred).
- **Currently checked?** No (and won't be at this layer).

### PHON rules

Per user direction (2026-05-29): GitBook is authoritative. `<PHON>` is permitted (optionally) as a child of `<S>`, `<W>`, or `<M>`. The DTD and XSD must be updated as part of this work to add `<PHON>` to their content models.

#### V070 — `<PHON>` is permitted (optional) as a child of `<S>`, `<W>`, `<M>`
- **Severity:** HARD (structural placement; absence is not a violation)
- **Description:** `<PHON>` is an optional element that may appear as a child of `<S>`, `<W>`, or `<M>`, analogous to `<FORM>`. It is not required at any level. Its placement outside those parents is a structural violation.
- **Source:** GitBook ("The `<PHON>` Element"); user direction (2026-05-29).
- **Currently checked?** No.
- **Example violation:** `<TEXT><PHON>…</PHON></TEXT>` (PHON directly under TEXT, not under S/W/M).

#### V071 — `PHON/@kindOf` is `original` or `standard`
- **Severity:** HARD
- **Description:** Per GitBook: "`<PHON>` should have a `kindOf` attribute set to `original` or `standard`, indicating which text it is transliterated from. If this is a transcription not a transliteration, use `standard`."
- **Source:** GitBook.
- **Currently checked?** No.
- **Example violation:** `<PHON kindOf="alternate">…</PHON>`.

#### V072 — At most one `<PHON>` per `kindOf` per element
- **Severity:** HARD
- **Description:** Analogous to V015. No element should have two `<PHON kindOf="original">` siblings.
- **Source:** Convention by analogy with FORM.
- **Currently checked?** No.

#### V073 — `<PHON>` text content is non-empty
- **Severity:** HARD
- **Description:** Analogous to V017 (per OQ4 resolution). An empty `<PHON>` is a bug.
- **Source:** Convention; user direction (2026-05-29).
- **Currently checked?** No.
- **Example violation:** `<PHON kindOf="original"></PHON>`.

### Cross-corpus / metadata / file conventions

#### V080 — File discovery: `/XML/` path segment, never `CodeAndDocs/`
- **Severity:** N/A (discovery filter, not a rule violation)
- **Description:** Per user direction (2026-05-29): the validator discovers files under `Corpora/<Name>/XML/...` only. Anything under `CodeAndDocs/` is ignored — those XMLs are illustrative/intermediate artefacts, not corpus content. The existing `get_files` substring filter (`"XML" in path`) is too loose and would incorrectly walk into `CodeAndDocs/XML/`-like paths; harden it to require `/XML/` as a literal path segment (e.g., `os.sep + "XML" + os.sep in path`).
- **Source:** User direction (2026-05-29); CLAUDE.md.
- **Currently checked?** Partial — `get_files` matches the substring `"XML"` rather than the path segment, so a `CodeAndDocs/.../XML/...` would be picked up incorrectly.

#### V081 — `TEXT/@id` is unique across the corpus-under-test AND all already-published corpora
- **Severity:** HARD (cross-corpus check)
- **Description:** Per user direction (2026-05-29): when validating a corpus, the validator must aggregate `TEXT/@id` values from (a) the corpus-under-test plus (b) every already-published corpus under `FormosanBank/Corpora/` and report any collisions. The check is across the *union*, not just within the corpus-under-test — a new corpus is invalid if it reuses a `TEXT/@id` that already exists in any published corpus.
- **Source:** User direction (2026-05-29); GitBook ("`id`: The unique identifier of the text; unique across resources").
- **Currently checked?** No.
- **Example violation:** A new corpus contains `<TEXT id="story1" …>` and `FormosanBank/Corpora/SomeOtherCorpus/XML/...` already contains `<TEXT id="story1" …>`.
- **Implementation note:** The check requires the validator to walk `FormosanBank/Corpora/` (read-only) when given a single corpus to validate, in addition to its primary target. For pre-port dev-repo validation, the primary target is the dev repo and `FormosanBank/Corpora/` is the reference set.

#### V082 — XML declaration and encoding
- **Severity:** WARN
- **Description:** Files should be UTF-8 and start with an `<?xml version="1.0" encoding="UTF-8"?>` declaration. lxml will handle non-UTF-8 gracefully, but a missing declaration / wrong encoding deserves a warning so we don't accumulate Latin-1 files silently.
- **Source:** Convention.
- **Currently checked?** No (the existing validator parses without complaint).

#### V083 — Files validate against the schema (XSD)
- **Severity:** HARD
- **Description:** Every XML file must parse and validate against the FormosanBank schema. The validator currently uses the XSD; per OQ2 resolution, the GitBook spec is authoritative and the XSD/DTD must be brought into alignment with it. Schema-level violations (malformed XML, unknown elements, missing required attributes) surface as HARD findings independent of the other V0xx rules.
- **Source:** CLAUDE.md; XSD (what code uses).
- **Currently checked?** Yes (via XSD).

## Out of scope (deferred)

The following are intentionally not part of this validator and should remain in their existing scripts or be added separately:

- **Punctuation validation** (lives in `QC/validation/validate_punct.py`).
- **Orthography validation** (`QC/validation/validate_orthography.py`).
- **Vocabulary validation** (`QC/validation/validate_vocabulary.py`).
- **Gloss validation** (`QC/validation/validate_glosses.py`).
- **Token counts and corpus metrics** (`QC/count_tokens.py`, `QC/corpus_metrics.py`).
- **Audio file existence on disk** — V051 checks the attribute is set; it does not check the file is downloaded, because audio is pulled per-corpus and may be absent locally.
- **Liveness checks for URLs / Glottocodes** (V055, V037).
- **`class` / `sclass` controlled vocabularies** beyond non-emptiness (V061).
- **Standardization itself** — the validator surfaces the count of missing-standard items (V014). The actual transliteration step is `QC/utilities/standardize.py`.

## Open questions

All open questions were resolved by user direction (2026-05-29). Resolutions are reflected inline in the affected rules (V002, V006, V010, V014, V016, V017, V023, V025/V026, V039, V062, V063, V070–V073, V080, V081).

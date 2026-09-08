# Alternate FORMs, TRANSL attributes, and attribute governance

Date: 2026-09-08
Status: approved design, ready for implementation planning

## Problem

FormosanBank XML carries two unrelated "alternate" mechanisms, and neither is
governed:

1. `FORM[@kindOf="alternate"]` — spelling variants, usable at S, W or M.
2. `TRANSL[@ver="alt"]` — a second translation of the same sentence.

The second is already specified (POL-025) and enforced (V084, V085). The first
has **no policy and no validation rule at all**. Separately, nothing requires a
new XML attribute to be documented before it appears in the schema.

## What the audit found

Scanned all 14,571 published XML files under `Corpora/*/XML/`, plus the whole
`Corpora/` tree including `CodeAndDocs/`, plus git history across all branches.

### The attribute marking is already consistent

Every `FORM/@kindOf` in the repository is one of exactly three values:
`original` (1,182,526), `standard` (1,177,721), `alternate` (140). No `<FORM>`
anywhere carries a `ver` attribute. `kindOf="alternative"` has never been
committed on any branch. The marking has been `kindOf="alternate"` since
commit 77966510a added it to the template.

Of those 140 alternates, **116 are in published `XML/`**; the other 24 sit in
POL-035 pre-correction snapshots under `CodeAndDocs/` (Latham-1862 8,
WakelinTexts 16) and are not published data. All counts below are the
published 116.

The `-opt` string does occur, but as an `S` id suffix and never as a `kindOf`
value — see "Optional material" below.

### The semantics are not consistent

116 alternates in published XML, across three corpora, meaning three different
things:

| Corpus | n | Level | What `alternate` means there |
| --- | --- | --- | --- |
| WakelinTexts | 26 | W, M (never S, deliberately) | spelling variant / optional material on the node that varies |
| UtrechtManuscriptWordList | 82 | S | a different witness (van der Vlis 1842) whose reading differs |
| Latham-1862 | 8 | S | a comma-separated variant in the source cell |

Latham's are frequently not spelling variants but **competing lexemes** for the
same gloss: `mouth` = `ranied` / `sabbacha`, `foot` = `rahpal` / `tiltil`,
`breast` = `arrabis` / `zido`. POL-027 already rules that a source offering
alternatives becomes one `S` block per option, so these are defects.

Latham's `totto`/`tutta` (0.60) and `so`/`soa` (0.80) *are* genuine spelling
variants. The defect count there is 5–6, not 8.

### No similarity threshold separates cleanly

Similarity computed as `difflib.SequenceMatcher` ratio over NFD-stripped,
casefolded text, against the closest non-alternate sibling. Distribution over
the 116: 8 below 0.5, 13 below 0.6, 21 below 0.7, median 0.86.

Short strings guarantee false positives: Wakelin's `a`/`u` scores 0.00 and is a
correct one-letter variant; `nem`/`namen` scores 0.50 and is the same morpheme.
Character-overlap and longest-common-substring metrics were tested and are
worse — they rank Utrecht's obviously-fine `couva`/`cauwa` below Latham's
`sabbacha`/`ranied`.

A threshold of 0.6 yields 13 findings repo-wide: 6 Latham (real), 2 Utrecht
(`tigpapahoang`/`tigp` likely real, `iit`/`jih` a judgment call), 5 Wakelin (all
legitimate). Exempting pairs whose shorter form is ≤2 characters removes two of
the Wakelin five (`u`/`a`, `namen`/`am`) and no real defect, giving **11**. This
is the basis for a SOFT rule, not a HARD one.

### Structural invariants are clean and worth locking in

Every one of the 116 alternates has at least one non-alternate FORM sibling on
the same parent. Zero exceptions. Nothing currently enforces this.

### TRANSL is already governed, with one doc error

V084 restricts `TRANSL/@ver` to `{"alt"}`; V085 requires all but one of a
parent's same-language TRANSLs to carry `ver`. Data is 100% clean — zero
violations repo-wide.

POL-025 states "The XSD already requires a `ver` when a parent has two
same-language TRANSLs." This is false; XSD 1.0 cannot express it. V085 does.

`ver="alt"` is **not** confined to the S level: MontgomeryTexts (W), RauDong
(W and M) and WakelinTexts (W and M) use it below S. 1,264 instances across 9
corpora. This is correct usage and the policy should say so.

### TRANSL/@kindOf is unenumerated and inconsistently applied

`TRANSL/@kindOf` is `xs:string` in the XSD — any value passes. In practice only
`"original"` occurs, 65,650 times, in two corpora. Glosbe applies it to 4,157
S-level translations and omits it from 3,452 others of the same kind, in the
same corpus. HundredPaiwanStories applies it to every W and M gloss and never
to S. Only V026 constrains it, and only at M level.

### The attribute whitelist mostly already exists

The XSD declares no `anyAttribute`, so an undeclared attribute already fails
`validate_xml.py`. Published XML uses zero undeclared attributes today. The
gaps are governance, not enforcement:

- `TRANSL/@kindOf` accepts any string (above).
- `W/@class`, `W/@sclass`, `M/@class`, `M/@sclass` are declared, described in
  GitBook, read by `QC/utilities/sample_sentences.py`, and emitted by no
  corpus. Harmless dead surface, but undocumented in-repo.
- Nothing links the XSD to POLICIES. An attribute can be added to the schema
  with no policy entry and no test notices.

### Optional material is resolved two different ways

NTUFormosanCorpus resolves a whole optional *word* (`x y (z)`) into a second
`S` block whose id is the first's plus `-opt`
(`CodeAndDocs/scripts/split_optional_parentheticals.py`) — 119 such S blocks,
with descendant W/M ids rewritten to match (835 W, 1,191 M). This is POL-026.

WakelinTexts resolves optional material *inside* a word (`puken-(en)`,
`(u)m-lavi`, `ku(a)`) into an `alternate` FORM on the word — 7 words.

These are reconcilable and both are right, but the boundary is written down
nowhere, so Wakelin's 7 currently read as POL-026 violations. The `-opt` id
suffix is also a public identifier under POL-037 and is recorded only in a
corpus script's docstring.

## Rulings taken

| Question | Ruling |
| --- | --- |
| What may an `alternate` hold? | Spelling variants only. Competing lexemes become separate `S` blocks per POL-027. |
| How is the overlap check enforced? | SOFT similarity flagging plus HARD structural invariants. |
| Where does attribute documentation live? | Annotated XSD, with a generated `ATTRIBUTES.md`, mirroring `rules_catalogue.py` → `RULES.md`. |
| What happens to `TRANSL/@kindOf`? | Enumerate, document, and SOFT-flag within-corpus inconsistency. |
| Scope of this work | Tests and policy only. Latham remediation is a tracked worklist item; no published XML changes. |

## Design

### 1. Policy

**POL-028 (new, §3 Structure)** — FORM alternates. Placed with POL-025/026/027,
which are all about alternatives.

- `FORM[@kindOf="alternate"]` records a **spelling variant** of a sibling FORM
  on the same node. It is the only marking for this: not `ver`, not
  `"alternative"`, not an `-opt` suffix.
- Every alternate must have at least one non-alternate FORM sibling on the same
  parent, and must **either overlap it highly or be very short** — short forms
  being the case where overlap cannot be measured meaningfully. The policy
  states this in words; the operative threshold and short-form cutoff live in
  V150 and are deliberately not written into POLICIES, so they can be tuned
  from evidence without a re-ruling.
- **The variation may span the whole form.** A one-letter word alternating
  `a`/`u` (WakelinTexts `Kwaway/S2W3`) is as valid an alternate as a letter
  changing inside a longer word. Nothing requires the variation to be
  word-internal.
- A competing **lexeme** for the same meaning, or a different gloss, is not an
  alternate; per POL-027 it becomes its own `S` block.
- Alternates may sit at S, W or M, and belong on the node that actually varies.
  A word-list corpus whose `S` is a word is the S-level case.
- **Scope clause for optional material.** What forces a separate `S` block is
  not whether the variation sits inside a word, but whether the **sentence's
  word inventory changes**. A whole optional *word* — `x y (z)` — changes the
  W tier and the gloss alignment, so it becomes two `S` blocks (POL-026), the
  second taking the first's id plus `-opt`. Optional material that leaves the
  word count unchanged — `puken-(en)`, `(u)m-lavi`, and equally a whole short
  word alternating `a`/`u` — becomes an `alternate` FORM on the word that
  varies, never a second sentence. Neither mechanism leaves parentheses in a
  published FORM.

**POL-053 (new, §6 Development)** — XML attributes are a closed, documented set.

- Every attribute declared in the XSD carries an `xs:annotation/xs:documentation`
  giving its meaning and its allowed values.
- `QC/validation/ATTRIBUTES.md` is generated from the XSD and never hand-edited.
- Adding an attribute requires: XSD declaration, annotation, regenerated
  catalogue, and a policy entry. A test enforces the first three; review
  enforces the fourth.
- The XSD declares no `anyAttribute`, so undeclared attributes already fail
  `validate_xml.py`. POL-053 names that as the whitelist so it is a deliberate
  guarantee rather than an accident of the schema.

**POL-025 amendment** — strike the parenthetical "(The XSD already requires a
`ver` when a parent has two same-language TRANSLs.)" and attribute the rule to
V085. Add that `ver="alt"` is valid at W and M, not only S.

### 2. Schema

In `QC/validation/xml_template.xsd`:

- Add `xs:annotation/xs:documentation` to all 30 attribute declarations. Two
  of the 30 are `ref="xml:lang"` into the bundled W3C `xml.xsd`; the
  referencing declarations take our own local annotation, since what
  `xml:lang` means *here* (ISO 639-3, validated against
  `QC/validation/iso-639-3.txt`) is a project fact, not a W3C one.
- Add a `TRANSL_kindOf_Type` restricting `TRANSL/@kindOf` to
  `original | standard`. This promotes V026's M-level check to every level at
  schema time. V026 stays — it produces a friendlier finding than a raw XSD
  error — and becomes partly redundant, which is noted in its docstring.
- Leave `TRANSL/@ver` as `xs:string`. V084 owns that allowlist; duplicating it
  in the XSD would create two places to update. The annotation says so.

`xml_template.dtd` is a retained fallback only and is not updated.

### 3. Tooling

`QC/validation/attributes_catalogue.py`, mirroring `rules_catalogue.py`:

- Parses the XSD, emits `QC/validation/ATTRIBUTES.md` — a table of element,
  attribute, required/optional, allowed values, and the documentation string.
- `--check` exits 1 if the catalogue is stale **or** if any declared attribute
  lacks documentation.
- `tests/validators/test_attributes_catalogue.py` runs `--check`, so a new
  attribute fails CI until documented and regenerated.

### 4. Validation rules

Next free id is V149.

| id | severity | module | mnemonic | current findings |
| --- | --- | --- | --- | --- |
| V149 | HARD | `hard.py` | `alternate_FORM_requires_base_sibling` | 0 |
| V150 | SOFT | `soft.py` | `alternate_FORM_low_overlap` | 11 |
| V151 | SOFT | `soft.py` | `transl_kindof_inconsistent` | Glosbe's 4157/3452 split |

- **V149** — a `FORM[@kindOf="alternate"]` must have at least one non-alternate
  FORM sibling on the same parent. Locks in today's clean state; also covers
  "an alternate must not be a parent's only FORM."
- **V150** — similarity between an alternate and its closest non-alternate
  sibling, below 0.6, using `SequenceMatcher` over NFD-stripped casefolded
  text, **exempting pairs whose shorter form is 2 characters or fewer**.
  Reports both strings, their lengths and the ratio so a reviewer can judge.

  The exemption encodes POL-028's "or very short" and is cut at 2 on evidence,
  not taste. At ≤2 it suppresses exactly two pairs, both legitimate (`u`/`a`,
  `namen`/`am`), and no real defect. At ≤3 it would also suppress
  `ratta`/`tâu`, a genuine Latham cross-lexeme defect; at ≤4, three more
  (`zido`/`arrabis`, `sjam`/`bahosa`, `tigp`/`tigpapahoang`). Anything above 2
  hides real findings and must not be adopted without new evidence.

  No length rule rescues `pipangengne-eben`/`pipangn-epen` (ratio 0.57, both
  long, legitimate). Such cases are irreducible, and are the reason V150 is
  SOFT rather than HARD.
- **V151** — within one file, some but not all `TRANSL` elements at a given
  parent-element level carry `@kindOf`.

Regenerate `RULES.md` afterwards.

### 5. Worklist, not remediation

`claudeplans/2026-09-08-alternate-form-worklist.md` triages all 11 V150
findings by element id:

- 6 Latham-1862 cross-lexeme alternates — defects, to be fixed in a later
  change that rebuilds the corpus per POL-027 and POL-037.
- 2 UtrechtManuscriptWordList — `tigpapahoang`/`tigp` (likely a truncation) and
  `iit`/`jih` (judgment).
- 3 WakelinTexts — reviewed and confirmed legitimate (`namen`/`nem` twice and
  `pipangengne-eben`/`pipangn-epen`); the other two are exempted by the
  short-form cutoff and never reach the report.

No published XML changes in this work.

## Testing

Test-driven, one rule at a time:

- Unit tests per rule, covering the positive case and the clean case. V150
  additionally pins the short-form behaviour in both directions: `u`/`a`
  (minlen 1) must be **exempted**, and `nem`/`namen` (minlen 3, ratio 0.50)
  must still **flag** — the pair that fixes the cutoff at 2 rather than 3.
  A regression test asserts `ratta`/`tâu` stays flagged, since that is the
  real defect a looser cutoff would hide.
- `test_attributes_catalogue.py` staleness and missing-documentation checks.
- A full `validate_xml.py` sweep across all corpora, asserting **zero new HARD
  findings** and exactly the expected SOFT counts (11 V150, plus V151 on
  Glosbe).

## Out of scope

- **Latham-1862 remediation** — worklist item, own change.
- **GitBook sync.** `en-us/the-bank-architecture/formosanbank-xml-format.md`
  describes `alternate` as "a genuine alternate form retained alongside the main
  tiers", vaguer than POL-028, and documents no attribute inventory. That is a
  separate repo and a follow-up, especially given the pending GitHub Pages
  migration.
- **Deprecating `TRANSL/@kindOf`** — considered and rejected; it would mean
  65,650 edits across two published corpora and a POL-051 removal review.
- **Removing `class`/`sclass`** — declared, documented and unused; they get
  annotations like every other attribute and stay.

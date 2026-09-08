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
legitimate). Exempting pairs where **both** forms are ≤2 characters removes one
of the Wakelin five (`a`/`u`) and no real defect, giving **12**. This is the
basis for a SOFT rule, not a HARD one.

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

### TRANSL/@kindOf is unenumerated, and wrong at the S level

`TRANSL/@kindOf` is `xs:string` in the XSD — any value passes. Only V026
constrains it, and only at M level. GitBook licenses the looseness explicitly,
calling it "the translation type, method, or provenance" — an open-ended
description that is the reason anything got attached to it at all.

In practice only `"original"` occurs, 65,650 times, and the two corpora split
perfectly by level:

| Corpus | S | W | M | Verdict |
| --- | --- | --- | --- | --- |
| Glosbe | 4,157 | 0 | 0 | **wrong** — remediate |
| HundredPaiwanStories | 0 | 24,556 | 36,937 | correct — keep |

The distinction is real. At W and M level a `TRANSL` carries a **gloss**, and
`kindOf` distinguishes the source's own gloss from a standardized one — exactly
the axis a future gloss-standardization pass will use, and already documented in
GitBook ("Original source glosses should be preserved. A standardized gloss can
be added as a separate `kindOf="standard"` translation"). At S level a `TRANSL`
is a free translation, there is no original-vs-standard axis, and `kindOf` means
nothing. Glosbe's 4,157 are therefore noise, not a convention.

They sit in three files — `Glosbe_{ami,tay,xsy}_eng_tmem.xml` — and the current
`glosbe_pipeline.py` does not emit them; it writes only `xml:lang` and `ver`.
They are legacy. Glosbe's `make_xml.sh` operates in place on the published XML
(its scrape is explicitly not reproducible), so a strip step added to that
script both removes them and keeps them from returning, satisfying POL-038.

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
| What happens to `TRANSL/@kindOf`? | Enumerate and document. **Forbidden at S level; permitted at W/M**, where TRANSL carries a gloss. Glosbe's 4,157 S-level uses go on the remediation worklist. |
| Scope of this work | Tests and policy only. Latham and Glosbe remediation are tracked worklist items; no published XML changes. **GitBook is in scope** (added 2026-09-08). |

## Design

### 1. Policy

**POL-028 (new, §3 Structure)** — FORM alternates. Placed with POL-025/026/027,
which are all about alternatives.

- `FORM[@kindOf="alternate"]` records a **spelling variant** of a sibling FORM
  on the same node. It is the only marking for this: not `ver`, not
  `"alternative"`, not an `-opt` suffix.
- Every alternate must have at least one non-alternate FORM sibling on the same
  parent, and must **either overlap it highly, or be short together with that
  sibling** — the short case being where overlap cannot be measured
  meaningfully. **Both forms must be short, not just one.** A short form paired
  with a long one is not an alternate: `dog`/`supercalifragilisticexpialidocious`
  shares a short member but is obviously two different words. The policy states
  this in words; the operative threshold and length cutoff live in V150 and are
  deliberately not written into POLICIES, so they can be tuned from evidence
  without a re-ruling.
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
  XSD 1.0 cannot also express "and not on an S-level TRANSL", because `S`, `W`
  and `M` share one `TRANSL_Type`; that half is V151's job.
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
| V150 | SOFT | `soft.py` | `alternate_FORM_low_overlap` | 12 |
| V151 | SOFT → HARD | `soft.py` → `hard.py` | `S_TRANSL_has_no_kindOf` | 4,157 (Glosbe) |

- **V149** — a `FORM[@kindOf="alternate"]` must have at least one non-alternate
  FORM sibling on the same parent. Locks in today's clean state; also covers
  "an alternate must not be a parent's only FORM."
- **V150** — similarity between an alternate and its closest non-alternate
  sibling, below 0.6, using `SequenceMatcher` over NFD-stripped casefolded
  text, **exempting pairs where the LONGER form is 2 characters or fewer** —
  that is, where both forms are short. Reports both strings, their lengths and
  the ratio so a reviewer can judge.

  The exemption tests `max(len(a), len(b))`, never `min`. Testing the shorter
  member would exempt any short form paired with any long one:
  `dog`/`supercalifragilisticexpialidocious` has a shorter member of 3 and
  would slip through a `min`-based cutoff of 3, while its longer member of 34
  correctly fails a `max`-based one.

  Cut at 2 on evidence. At ≤2 it suppresses exactly one pair, `a`/`u`, and no
  real defect. At ≤3 and ≤4 it additionally suppresses `iit`/`jih`, an Utrecht
  pair that wants a reviewer's eye rather than silence. At ≤5 it suppresses
  `tâu`/`ratta`, a genuine Latham cross-lexeme defect, so 4 is the hard ceiling
  and 2 is the recommended setting.

  No length rule rescues `pipangengne-eben`/`pipangn-epen` (ratio 0.57, both
  long, legitimate) or `am`/`namen` (0.57, longer member 5). Such cases are
  irreducible, and are the reason V150 is SOFT rather than HARD.
- **V151** — an S-level `TRANSL` must not carry `@kindOf`. W- and M-level
  TRANSLs may, since there it marks a source gloss against a standardized one.

  Lands **SOFT**, because Glosbe's 4,157 legacy attributes would otherwise fail
  CI the moment the rule ships, and the earlier ruling keeps remediation out of
  this change. It is **promoted to HARD in the same change that remediates
  Glosbe** — that promotion is the worklist item's definition of done, not an
  optional follow-up.

Regenerate `RULES.md` afterwards.

### 5. Worklist, not remediation

`claudeplans/2026-09-08-alternate-form-worklist.md` carries two remediation
items and the triage behind them.

**V150 — all 12 findings, by element id:**

- 6 Latham-1862 cross-lexeme alternates — defects, to be fixed in a later
  change that rebuilds the corpus per POL-027 and POL-037.
- 2 UtrechtManuscriptWordList — `tigpapahoang`/`tigp` (likely a truncation) and
  `iit`/`jih` (judgment).
- 4 WakelinTexts — reviewed and confirmed legitimate (`nem`/`namen` twice,
  `am`/`namen`, and `pipangn-epen`/`pipangengne-eben`). Recorded as
  confirmed-fine so reviewers do not re-litigate them each sweep. Only `a`/`u`
  is exempted by the length cutoff and never reaches the report.

**V151 — Glosbe:** strip `@kindOf` from 4,157 S-level TRANSLs across
`Glosbe_{ami,tay,xsy}_eng_tmem.xml`, via a step added to Glosbe's
`make_xml.sh` (POL-038), then promote V151 to HARD.

**Also recorded for the future:** W/M-level `TRANSL/@kindOf` is the axis a
gloss-standardization pass will use — source gloss as `original`, standardized
gloss added as `standard`. HundredPaiwanStories' 61,493 W/M uses are the
existing precedent and must not be stripped.

No published XML changes in this work.

### 6. GitBook

`../FormosanBankGitbook/en-us/the-bank-architecture/formosanbank-xml-format.md`
is where a corpus author learns the format, so an attribute that is legal in
the XSD but absent from that page becomes a validation surprise. Three edits,
in the English canonical version:

- **Remove the ad-hoc licence.** The page currently describes `TRANSL/@kindOf`
  as "The translation type, method, or provenance. At morpheme level, the
  validator limits this to `original` or `standard`." Read plainly, that invites
  an author to put any provenance string on any TRANSL, and it is the reason
  Glosbe's S-level uses exist. Replace with the closed enumeration
  (`original | standard`), the S-level prohibition, and a pointer to V151.
  This is the only permissive attribute language found: repo `POLICIES.md`
  contains no attribute rule at all, and the "never ad hoc" phrasing in GitBook
  `policies.md` is POL-038 about data files, unrelated.
- **Publish the full attribute inventory** — one table per element, generated
  from the same XSD annotations that produce `ATTRIBUTES.md`, so the public
  documentation and the schema cannot drift apart.
- **Sharpen `alternate`.** "A genuine alternate form retained alongside the
  main tiers" becomes POL-028's definition: a spelling variant of a sibling
  FORM, highly overlapping or short together with it, never a competing lexeme.

The existing W/M gloss text ("Original source glosses should be preserved. A
standardized gloss can be added as a separate `kindOf="standard"` translation")
is already correct and stays.

Sync mechanics follow the established path (`sync_upstream_docs.py`); the
pending GitHub Pages migration does not block this, since the English pages
carry over.

## Testing

Test-driven, one rule at a time:

- Unit tests per rule, covering the positive case and the clean case. V150
  additionally pins the length behaviour in three directions: `a`/`u`
  (both length 1) must be **exempted**; `am`/`namen` (shorter 2, longer 5) must
  still **flag**, which is the case that forces `max` rather than `min`; and a
  synthetic `dog`/`supercalifragilisticexpialidocious` must **flag**, guarding
  the same thing against a future refactor. A regression test asserts
  `tâu`/`ratta` stays flagged, since that is the real defect a looser cutoff
  would hide.
- V151 tests both levels: `@kindOf` on an S-level TRANSL flags; the same
  attribute on a W- or M-level TRANSL does not.
- `test_attributes_catalogue.py` staleness and missing-documentation checks.
- A full `validate_xml.py` sweep across all corpora, asserting **zero new HARD
  findings** and exactly the expected SOFT counts: 12 V150, and 4,157 V151 all
  in Glosbe's three `_tmem.xml` files.

## Out of scope

- **Latham-1862 remediation** — worklist item, own change.
- **Deprecating `TRANSL/@kindOf` outright** — considered and rejected. At W/M
  it is correct and forward-looking; only the S-level uses are wrong.
- **Removing `class`/`sclass`** — declared, documented and unused; they get
  annotations like every other attribute and stay.

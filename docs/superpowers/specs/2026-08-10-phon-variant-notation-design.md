# PHON variant notation: `x~y` → `[x|y]` (design)

**Status:** approved 2026-08-10 (maintainer: "spec and implement").
Resolves the semantics half of POL-013.

## Problem

Orthography profiles write phonemic alternatives in their IPA value cells
with a bare tilde — `b~v`, `ɬ~ɮ`, `o~u` (30+ cells across Ortho113, Ortho94,
Church, MinEd, Folk, Montgomery profiles). `add_phonology.py` copies values
verbatim, so generated PHON carries `b~v` inline in words. Two defects:

1. **No grouping scope.** In a longer value, nothing says where the
   alternation starts and ends — `ab~cd` could be `a[b~c]d` or `[ab~cd]`.
2. **`~` does double duty.** The same character is the Leipzig-style
   reduplication marker on FORM tiers of glossed corpora. Freeing `~` for
   reduplication removes the collision.

## Decision

Phonemic variants are written **`[x|y]`** (two or more alternatives,
pipe-separated, in square brackets — regex-alternation style): `[b|v]`,
`[ɬ|ɮ]`, `[o|u]`, `[ʦ|ʨ]`, multi-char alternatives welcome (`[l|ll]`).
This is the canonical notation in profile IPA value cells and therefore in
generated PHON. `~` no longer appears in profile values or PHON.

## Why it composes safely

- **add_phonology needs no change.** Mapping values are emitted verbatim
  (`apply_phonology_mappings` appends the replacement string untouched);
  the punctuation-dropping rule applies to unmapped *input* characters
  from FORM, never to mapping outputs. And FORM text can never smuggle a
  collision in: `clean_xml` converts `[`/`]` to parentheses in FORM.
- **Rules sidecars keep working — with escaping.** `.rules.tsv` patterns
  are compiled regexes that post-process PHON; the two Bunun rules exist
  precisely to *resolve* the ʦ/ʨ variant contextually. Since `[`, `]`,
  `|` are regex metacharacters, patterns referencing a variant group must
  escape it: `ʦ~ʨ(?=i)` becomes `\[ʦ\|ʨ\](?=i)`.
- **validate_conversion_table is agnostic.** It compares profile IPA
  values as opaque strings (no `~` parsing anywhere); comparisons stay
  consistent because all profiles migrate in one commit.
- **Nothing else touches PHON** (clean_xml and standardize process
  FORM/TRANSL only; PHON is regenerated wholesale).

## Migration

1. Rewrite every whole TSV cell matching `^X(~X)+$` — where `X` is a
   nonempty run without whitespace, parens, brackets, or pipes — to
   `[X|X|…]`, across `Orthographies/**/*.tsv` (profiles only; verified no
   conversion table contains `~`). The pattern's exclusions keep it away
   from rule regex cells (`(?=…)` contains parens).
2. Hand-migrate the two `Bunun.rules.tsv` patterns to the escaped form.
3. Published PHON still carries legacy `~` until the planned regeneration
   sweep re-runs add_phonology; V147 (below) makes that visible.

## Guards

- **V154** (validate_registries, SOFT): a profile IPA cell still using
  legacy `x~y` — keeps future profile additions on the new notation.
- **V146** (validate_text, SOFT): malformed variant group in PHON —
  unbalanced brackets, nesting, `|` outside a group, fewer than two
  alternatives, or an empty alternative.
- **V147** (validate_text, SOFT): legacy `~` inside PHON — "regenerate
  PHON with the migrated profiles".

## Out of scope

- The codepoint half of POL-013 (mapping U+223C → `~` in
  `swap_punctuation`) — still a pending recommendation, unaffected.
- Regenerating published PHON — belongs to the regeneration sweep.
- Any change to reduplication notation on FORM tiers.

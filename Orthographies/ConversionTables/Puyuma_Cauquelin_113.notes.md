# Puyuma_Cauquelin_113.tsv — construction notes

Maps the **Cauquelin** Puyuma orthography → **Ortho113** Puyuma. Cauquelin
transcribes a single dialect, **Nanwang**, so the table targets Ortho113's
Nanwang column (header `original`/`Nanwang`); validate with `--dialect Nanwang`:

```
python QC/validation/validate_conversion_table.py \
  Orthographies/Cauquelin/Puyuma.tsv \
  Orthographies/Ortho113/Puyuma.tsv \
  Orthographies/ConversionTables/Puyuma_Cauquelin_113.tsv --dialect Nanwang
```

By convention the table lists **only actual spelling changes**; a grapheme whose
Ortho113 spelling is identical is omitted and kept as-is during standardization.
Latest run: 11 confirmed, 4 mismatches (approved assumed equivalences, §2),
7 coverage gaps (§3–§4), 0 untokenizable.

## 1. Listed spelling changes, IPA-confirmed

`ŋ→ng` · `T→tr` `ʈ→tr` · `D→dr` `ɖ→dr` (Nanwang `dr`=/ɖ/) · `ʔ→'` · `ə→e` ·
`j→y` · and the laterals `L→l` `ɭ→l` (Nanwang `l`=/ɭ/) and **`l→ll`** (Nanwang
`ll`=/l/). The lateral handling is confirmed by the Ortho113 source doc: [ɭ] is
written `l` in all varieties; Nanwang adds the new letter `ll` (replacing `lr`)
for [l], while Zhiben/Xiqun/Jianhe keep `lr` for [ɮ].

Graphemes unchanged in both spelling and IPA (`a b e g i k m n ng p r s t u w '`
— including the Latin/IPA pairs like `ng`, `'`, `e`) are **not listed**, per
convention.

## 2. Listed spelling changes that are assumed equivalences (distinct IPA)

Reviewer-approved 2026-08-09. The checker flags these as mismatches because the
annotated IPA differs; the intended Nanwang phoneme is the same.

- **`sh→s`, `ʃ→s`** — Cauquelin /ʃ/ vs Ortho113 /s/. Ortho113 has no /ʃ/; it is
  rare and mostly rule-derived (§5), so it collapses to `s`.
- **`o→u`** — Cauquelin /o/ vs Ortho113 /u/. Ortho113 Puyuma has no /o/ (treated
  as an allophone of /u/).
- **`ɛ→e`** — Cauquelin /ɛ/ vs Ortho113 /ə/. Ortho113 has no /ɛ/ (treated as an
  allophone of /ə/).

## 3. Same-spelling assumed equivalences — NOT listed (convention)

Same letter in both orthographies, so omitted from the table even though the two
profiles annotate different IPA. They appear as "coverage gaps" in the checker
(spelling preserved, IPA unverified):

- **`d`** — Cauquelin /d/ vs Ortho113 /ð/; one voiced dental obstruent, spelled
  `d` in both (matches the reviewed `Puyuma_MinEd_113` treatment).
- **`c`** — Cauquelin /c/ (palatal stop) vs Ortho113 /ʦ/, spelled `c` in both.
  (Also loanword-only, §4.)
- **`y`** — Cauquelin profile annotates `y`=/y/, but it is the glide /j/
  (Ortho113 `y`=/j/), spelled `y` in both.

## 4. Loanword-only graphemes

`c`, `h`, `v`, `f`, `ʤ` occur only in loanwords, not the native Nanwang
inventory. They are not listed in the table (spelling preserved for `c`/`h`/`v`;
no target asserted for `f`/`ʤ`) and appear as coverage gaps — expected, not
defects. No edit to `Orthographies/Ortho113/Puyuma.tsv` is warranted.

## 5. /ʃ/ in the source

`Orthographies/Cauquelin/Puyuma.tsv` lists /ʃ/ under **both** `sh`→/ʃ/ and
`ʃ`→/ʃ/ on purpose: the author writes it either way. /ʃ/ is also mostly produced
by the rule in `Puyuma.rules.tsv`: `(?<=[ui])s|s(?=[ui]) → ʃ` (s palatalized next
to i/u).

## 6. Removed from the Cauquelin profile

`q` and `x` were removed from `Orthographies/Cauquelin/Puyuma.tsv` (not Puyuma
graphemes).

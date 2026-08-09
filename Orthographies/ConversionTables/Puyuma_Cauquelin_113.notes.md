# Puyuma_Cauquelin_113.tsv — construction notes

Maps the **Cauquelin** Puyuma orthography → **Ortho113** Puyuma. Cauquelin
transcribes a **single dialect, Nanwang**, so the table targets Ortho113's
**Nanwang** column (header `original`/`Nanwang`); validate with
`--dialect Nanwang`:

```
python QC/validation/validate_conversion_table.py \
  Orthographies/Cauquelin/Puyuma.tsv \
  Orthographies/Ortho113/Puyuma.tsv \
  Orthographies/ConversionTables/Puyuma_Cauquelin_113.tsv --dialect Nanwang
```

Built by aligning `Orthographies/Cauquelin/Puyuma.tsv` (single `IPA` column)
against the Nanwang column of `Orthographies/Ortho113/Puyuma.tsv`, cross-checked
with the reviewed `Puyuma_MinEd_113`/`Puyuma_Folk_113`. Latest run: 27 confirmed,
5 mismatches (all the approved assumed equivalences below), 3 untokenizable
(profile gap, §4), 4 coverage gaps (§5).

## 1. Exact IPA matches (no assumption)

`ng→ng` `ŋ→ng` · `T→tr` `ʈ→tr` · `D→dr` `ɖ→dr` (Nanwang `dr`=/ɖ/) ·
`'→'` `ʔ→'` · `e→e` `ə→e` · `j→y` (/j/) ·
`L→l` `ɭ→l` (Nanwang `l`=/ɭ/) and **`l→ll`** (Nanwang `ll`=/l/) — targeting
Nanwang preserves the /ɭ/ vs /l/ distinction that is lost in the default column.
Confirmed by the Ortho113 source doc: [ɭ] is written `l` in all varieties;
Nanwang adds the new letter `ll` (replacing `lr`) for [l], while Zhiben/Xiqun/
Jianhe keep `lr` for [ɮ]. ·
`a b g i k m n p r s t u w` → themselves.

## 2. Assumed equivalences (distinct IPA, same phoneme) — APPROVED

Reviewer-approved 2026-08-09; follow the reviewed `Puyuma_MinEd_113` precedent.
The checker reports these as mismatches because the annotated IPA differs; the
intended Nanwang phoneme is the same.

- **`d → d`** — Cauquelin /d/ vs Ortho113 /ð/. One voiced dental obstruent.
- **`c → c`** — Cauquelin /c/ (palatal stop) vs Ortho113 /ʦ/ (affricate).
  (Also untokenizable in Nanwang — see §4.)
- **`sh → s`** — Cauquelin /ʃ/ vs Ortho113 /s/. Ortho113 has no /ʃ/; `sh` is
  rare in the source and mostly rule-derived (see §3), so collapsing to `s` is
  the only available target.
- **`o → u`** — Cauquelin /o/ vs Ortho113 /u/. Ortho113 Puyuma has no /o/;
  treated as an allophone of /u/.
- **`ɛ → e`** — Cauquelin /ɛ/ vs Ortho113 /ə/. Ortho113 Puyuma has no /ɛ/;
  treated as an allophone of /ə/.
- **`y → y`** — Cauquelin profile annotated `y`=/y/, but Puyuma has no front
  rounded vowel; treated as the glide /j/ (Ortho113 `y`=/j/).

These produce four benign merges the checker reports under "information loss":
`s ← s, ʃ` (ʃ rare/rule-derived), `j ← j, y` (two spellings of the glide),
`u ← o, u`, `ə ← ə, ɛ` — each is the intended consequence of an approved
equivalence, not accidental loss.

## 3. /ʃ/ in the Cauquelin source

`Orthographies/Cauquelin/Puyuma.tsv` lists /ʃ/ under **both** `sh`→/ʃ/ and
`ʃ`→/ʃ/ on purpose: the author is inconsistent and uses either spelling in the
text. The conversion table therefore maps both `sh→s` and `ʃ→s`. /ʃ/ is also
rare overall and mostly produced by the existing rule in `Puyuma.rules.tsv`:
`(?<=[ui])s|s(?=[ui]) → ʃ` (s palatalized next to i/u).

## 4. Ortho113 Nanwang profile gap (finding — needs a decision)

`c`, `h`, `v` are marked **`NA`** in the Ortho113 Puyuma **Nanwang** column, so
the checker reports `c→c`, `h→h`, `v→v` as untokenizable for Nanwang — yet the
Cauquelin Nanwang source attests all three (/ʦ~c/, /h/, /v/). Either the Ortho113
Nanwang profile is missing these graphemes, or they occur only in loanwords in
Cauquelin. The mappings are kept (they are the canonical Ortho113 spellings, per
the `default` column); resolving the flag means editing
`Orthographies/Ortho113/Puyuma.tsv` — held for reviewer sign-off, not done here.

## 5. Unresolved — deliberately NOT in the table

`q` and `x` were removed from `Orthographies/Cauquelin/Puyuma.tsv` entirely
(not Puyuma graphemes). `f` /f/ and `ʤ` /ʤ/ remain in the Cauquelin profile but
have no Ortho113 target, so the checker surfaces them as coverage gaps. Provide
targets if either should map.

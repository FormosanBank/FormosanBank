# Cauquelin vs. Ortho113 — Puyuma

Describes how the **Cauquelin** Puyuma orthography (`Cauquelin/Puyuma.tsv`)
differs from **Ortho113** (`Ortho113/Puyuma.tsv`). Cauquelin transcribes a single
dialect, **Nanwang**, so all comparisons below are against Ortho113's **Nanwang**
column. The machine-readable correspondence lives in
`ConversionTables/Puyuma_Cauquelin_113.tsv` (validate with
`QC/validation/validate_conversion_table.py … --dialect Nanwang`).

## 1. Same sound, different spelling

These are the actual conversions (Cauquelin → Ortho113); the IPA is identical on
both sides.

| Sound | Cauquelin | Ortho113 (Nanwang) |
|---|---|---|
| /ŋ/ | `ng` or `ŋ` | `ng` |
| /ʈ/ | `T` or `ʈ` | `tr` |
| /ɖ/ | `D` or `ɖ` | `dr` |
| /ʔ/ | `'` or `ʔ` | `'` |
| /ə/ | `e` or `ə` | `e` |
| /j/ | `j` | `y` |
| /ɭ/ | `L` or `ɭ` | `l` |
| /l/ | `l` | `ll` |

**Laterals** are the intricate case. Puyuma has three lateral phonemes: alveolar
[l], voiced lateral fricative [ɮ], and retroflex [ɭ]. Per the Ortho113 source
documentation, [ɭ] is written `l` in **all** varieties; Nanwang uses the new
letter `ll` (replacing the older `lr`) for [l], while Zhiben/Xiqun/Jianhe keep
`lr` for [ɮ]. So in Nanwang the two orthographies line up as: Cauquelin `L`/`ɭ`
(/ɭ/) → Ortho113 `l`, and Cauquelin `l` (/l/) → Ortho113 `ll`. The distinction is
**preserved**.

Graphemes that are spelled *and* pronounced the same in both systems —
`a b g i k m n p r s t u w` — are unchanged.

## 2. Same spelling, different IPA annotation

The two profiles use the same letter but annotate slightly different IPA. These
are treated as the same Puyuma phoneme (the letter is kept unchanged during
standardization, so they are **not** listed in the conversion table).

| Letter | Cauquelin IPA | Ortho113 IPA | Note |
|---|---|---|---|
| `d` | /d/ | /ð/ | one voiced dental obstruent |
| `c` | /c/ (palatal stop) | /ʦ/ (affricate) | one affricate/palatal (also loanword-only, §4) |
| `y` | /y/ | /j/ | Cauquelin `y` is the glide /j/, not a front rounded vowel |

## 3. Distinctions Cauquelin makes that Ortho113 merges

Cauquelin keeps these pairs apart; Ortho113 (Nanwang) writes each pair with a
single grapheme, so the contrast is lost on conversion.

| Cauquelin (distinct) | → Ortho113 | Reason |
|---|---|---|
| /s/ (`s`) vs /ʃ/ (`sh`, `ʃ`) | `s` | Ortho113 has no /ʃ/ |
| /u/ (`u`) vs /o/ (`o`) | `u` | Ortho113 Puyuma has no /o/ |
| /ə/ (`e`, `ə`) vs /ɛ/ (`ɛ`) | `e` | Ortho113 has no /ɛ/ |

## 4. Inventory differences

**Cauquelin has, Ortho113 (Puyuma) does not.** `f` /f/ and `ʤ` /ʤ/ have no
Ortho113 Puyuma equivalent at all; `c`, `h`, `v` exist in Ortho113 generally but
are absent (`NA`) from the **Nanwang** column. All five are assumed to occur
**only in loanwords**. On conversion they pass through the standardized FORM
unchanged; because they are not in the Ortho113 Nanwang profile they receive no
phonology and surface as `*` in the standard-tier PHON. This is expected — adding
real phonology for them would require a profile entry or rule.

**Ortho113 annotates, Cauquelin never produces.** Ortho113 spells the voiced
dental `d` and annotates it /ð/, but Cauquelin only ever supplies /d/ (see §2), so
the phoneme /ð/ is never independently generated. This is a notational artifact of
the shared `d` spelling, not a coverage gap.

## 5. /ʃ/ in the source

Cauquelin transcribes /ʃ/ inconsistently, as either `sh` or the literal `ʃ`;
both are listed in `Cauquelin/Puyuma.tsv` and both convert to `s`. /ʃ/ is also
mostly predictable and produced by a rule in `Cauquelin/Puyuma.rules.tsv`:
`(?<=[ui])s | s(?=[ui]) → ʃ` (i.e. /s/ palatalizes next to /i/ or /u/).

## 6. Not Puyuma graphemes

`q` and `x` were removed from `Cauquelin/Puyuma.tsv`; they are not Puyuma
graphemes.

# Puyuma_Cauquelin_113.tsv — construction notes (DRAFT for review)

Maps the **Cauquelin** Puyuma orthography → **Ortho113** Puyuma. Built by
aligning `Orthographies/Cauquelin/Puyuma.tsv` (single `IPA` column) against
`Orthographies/Ortho113/Puyuma.tsv` (per-dialect: Nanwang, Zhiben, Xiqun,
Jianhe, default), and cross-checked with the reviewed `Puyuma_MinEd_113.tsv`
and `Puyuma_Folk_113.tsv`. Verified with
`QC/validation/validate_conversion_table.py`.

Single `original`/`standard` column: the table targets the **standard Ortho113
spelling**, which is dialect-invariant at the spelling level even though the
per-dialect IPA (and phoneme inventory) differ. The validator still checks the
one mapping against every dialect column, so per-dialect `NA`/mismatch notes
below are expected artifacts, not necessarily table errors.

## 1. Exact IPA matches (no assumption)

`ng→ng` `ŋ→ng` · `T→tr` `ʈ→tr` (ʈ) · `D→dr` `ɖ→dr` (ɖ, but see §4) ·
`'→'` `ʔ→'` (ʔ) · `e→e` `ə→e` (ə) · `j→y` (j) ·
`a b g h i k m n p r s t u v w` → themselves. These carry identical IPA in
both profiles.

## 2. Assumed equivalences already in the table (distinct IPA, same phoneme)

These follow the reviewed `Puyuma_MinEd_113` precedent, where the same
letter-preserving mappings are accepted despite the profiles annotating
slightly different IPA. The IPA differs; the intended Puyuma phoneme is the
same.

- **`d → d` (Cauquelin /d/ vs Ortho113 /ð/).** One voiced dental obstruent.
  Ortho113 writes it `d` and annotates /ð/ (its realization is an
  interdental/voiced fricative ~ stop); Cauquelin writes the same segment `d`
  and annotates the plosive /d/. `Puyuma_MinEd_113` also maps `d→d` (and
  `z→d`). Kept.
- **`c → c` (Cauquelin /c/ palatal stop vs Ortho113 /ʦ/ alveolar affricate).**
  One Puyuma affricate/palatal obstruent, spelled `c` in both. `MinEd` maps
  `c→c`. Kept. (Flagged as a mismatch by the checker in Jianhe, where the
  Ortho113 profile assigns `c`=/ʦ/.)
- **`L → l`, `ɭ → l` (retroflex lateral /ɭ/).** Ortho113 spells the retroflex
  lateral `l` (its `l` = /ɭ/ in Nanwang/Zhiben/Xiqun, /l/ in Jianhe/default).
  `MinEd` and `Folk` both map `L→l`. Kept.

## 3. Information loss the checker flagged (needs a decision)

- **`ɭ`/`l` merge.** Cauquelin distinguishes `L` (/ɭ/) and `l` (/l/); Ortho113
  spells **both** `l` in the default column, so the distinction is lost there
  (preserved only in the dialects where `l`=/ɭ/ and a separate `ll`=/l/
  exists — e.g. Nanwang). If preserving /ɭ/ vs /l/ matters, this table needs
  per-dialect columns like `MinEd` (Nanwang: `L→l`, `l→ll`).

## 4. Dialect-scope issue: `dr` outside Nanwang

Ortho113 `dr` (/ɖ/) is defined only for **Nanwang** and `default`; it is `NA`
in Zhiben/Xiqun/Jianhe. So `D→dr` is exact in Nanwang but, in the other three
dialects, the checker tokenizes `dr` as `d`+`r` (→ /ðr/) and flags a mismatch.
Question for review: do Zhiben/Xiqun/Jianhe have /ɖ/ at all, and if so how is
it spelled in Ortho113? If they lack it, `D`/`ɖ` simply won't occur in those
dialects' text and the mapping is harmless; if they have it, the profile is
missing a `dr` value.

## 5. Unresolved — deliberately NOT in the table (need your call)

No confident Ortho113 target; left out so the validator reports them as
coverage gaps rather than guessing. My candidate resolutions + reasoning:

| Cauquelin | IPA | Candidate | Reasoning (needs confirmation) |
|---|---|---|---|
| `o` | /o/ | `o → u`? | Ortho113 Puyuma has no /o/; if [o] is an allophone of /u/ (as `o`/`u` are treated as one phoneme in several Formosan orthographies), `o→u`. This is the "unresolved vowel correspondence" the readme flags for Cauquelin. |
| `ɛ` | /ɛ/ | `ɛ → e`? | No Ortho113 /ɛ/; if [ɛ] is an allophone of /ə/ (Ortho113 `e`), `ɛ→e`. Same readme caveat. |
| `sh`/`ʃ` | /ʃ/ | `sh → s`? | No Ortho113 /ʃ/; if [ʃ] is an allophone/variant of /s/, map to `s`. Otherwise Puyuma may genuinely lack /ʃ/ and these are non-native. |
| `y` | /y/ | `y → y`? | The profile annotates `y`=/y/ (a front rounded vowel Puyuma lacks); almost certainly a stand-in for the glide /j/. If Cauquelin text uses `y` for the glide, `y→y` (Ortho113 `y`=/j/). If it's a real vowel, unresolved. Likely a profile error. |
| `ʤ` | /ʤ/ | — | No Ortho113 voiced affricate. No confident target; needs a phonological call. |
| `f` `q` `x` | /f/ /q/ /x/ | — | Not Ortho113 Puyuma phonemes; likely loan/foreign letters that don't occur in native text. Leave unmapped unless they appear in the source. |

## Open questions for the reviewer

1. Accept the §2 assumed equivalences (`d→d`, `c→c`, `L/ɭ→l`)? (They match the
   reviewed MinEd table.)
2. §5 candidates: accept `o→u`, `ɛ→e`, `sh→s`, `y→y`? Reject any?
3. `ʤ`, and `f`/`q`/`x`: drop entirely, or is there an intended target?
4. Single-column (this draft) or per-dialect columns to preserve the `ɭ`/`l`
   distinction and handle `dr`/`v`/`b` dialect variation?

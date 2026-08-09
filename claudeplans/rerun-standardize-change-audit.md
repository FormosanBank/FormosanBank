# Rerun standardize + add_phonology — change audit (Group 1)

Branch `feature/rerun-standardize-phonology`. Reran the documented
`standardize.py` + `add_phonology.py` on the 7 "clean" Group 1 corpora (no
post-standardization edits) and diffed the result against committed HEAD.

## Method / caveats

- Baseline = committed HEAD; scripts modify XML in place, so the working-tree
  diff is the change set.
- Changes are compared on **FORM/PHON text content, whitespace-normalized**, to
  filter out serialization noise (see below). Tool: `/tmp/audit_diff.py`.
- The rerun ran **only** `standardize.py` + `add_phonology.py` — **not**
  `clean_xml.py` or any post-standardize step. This matters (see §A).
- **All Group 1 corpora are S-level only** (no `W`/`M` elements), so there are no
  word/morpheme-level changes to report separately.

## Serialization noise (ignore)

Every rewritten file changes the XML declaration (`'1.0'`→`"1.0"`), drops the
trailing newline, and reflows indentation. Multiline FORM/PHON text also gets
re-indented. None of this is a content change. **Latham-1862** and
**Virginia_Fey_Dictionary** have *only* serialization noise — zero real change.

## Change types

### A. Standard-tier FORM reversions — LIKELY UNINTENDED (flag)

The current `standardize.py --copy` is a **pure copy** of the original tier
(`_copy_mixed_content`; no transformation). Wherever the committed *standard*
tier differed from the *original*, that difference was made by a **separate step
the rerun did not run**, so a pure `--copy` reverts standard back to the raw
original. Two such cleanups are undone:

1. **Hyphen / clitic stripping** — done by `clean_xml.py` (`_process_standard_hyphens`,
   rule C012: strip `-` and `=` from S-level standard FORM when `-` is not a
   letter in that orthography). The rerun skipped `clean_xml`, so source hyphens
   reappear in standard FORM.
   - SEALS33 (Saisiyat/Seediq): `renkoy → ren-koy`, `ProtoAustronesian → Proto-Austronesian`, `rape:  ray → rape: - ray`.
   - WilangYutasVideos (Atayal): `Karenko → Karen-ko`, `PinTon → Pin-Ton`, `nglgan → n-glgan`, `Taywan → Tay-wan`.
2. **u→o normalization** — the old `standardize --copy` converted `u→o` (the
   READMEs note "all u's are converted to o's"); the current `--copy` does not,
   so `u` reappears where standard had `o`.
   - FormosanBankGitBook (Eastern Paiwan): `kiteko→kiteku`, `toa→tua`, `zirio→ziriu`, `namadjolo→namadjulu`.

**These are reversions of the published standard-tier cleanup, not improvements.**
Committing them would make the standard tier less clean than the published
corpora. → Flag; do not commit without re-running `clean_xml` afterward.

### B. PHON regeneration — genuine improvements (good)

Independent of FORM, `add_phonology` on this branch changes PHON for the better:

1. **`ng`→`ŋ` fix.** The old run emitted `n*` (the `g` left unmapped as `*`);
   the new run maps the `ng` digraph correctly to `ŋ`.
   - Glosbe (Amis): `matən*iɾ → matəŋiɾ`, `n*aʡajaj → ŋaʡajaj`, `tapan* → tapaŋ`.
   - Glosbe's standard FORM is **unchanged**, so its 83 original- + 94
     standard-PHON changes are a **pure phonology improvement** (fewer `*`).
2. **New dialect-scoped phonology rules.** SEALS33 Seediq:
   - original PHON (Ortho94): glide insertion `pnəəaħ → pnəəjaħ`, `slməan → slməjan`.
   - standard PHON (Ortho113): vowel shift `pnəəaħ → pnəeaħ`, `slməan → slmean`.
   These are the intended output of the shared-source-phonology /
   dialect-scoped-phon-rules work (original vs standard use different profiles).

### C. PHON downstream of the FORM reversions

Where standard FORM reverted (§A), the standard PHON follows it (hyphens and
`u`/`o` reflected). Entangled with §A, not an independent change.

### D. PHON tier newly populated (addition)

**FormosanBankGitBook** had **no S-level PHON at all** in the committed XML;
`add_phonology` added both original and standard PHON (102 sentences). A pure
addition — worth noting that this corpus shipped without phonology.

### E. Wikipedias — PHON markup/segmentation stripping + o~u fix (large-scale)

Wikipedias standard **FORM is unchanged** (its original tier has no morpheme
hyphens and already uses `o`, so the pure `--copy` is a no-op there). But **7998
sentences changed in both PHON tiers** — the current `add_phonology` now strips,
from the generated PHON:

- **wiki-heading `==` and clitic `=`**: `== takaraj a soːwaɾ == …` → `takaraj a soːwaɾ …`
- **hyphens**: `tatapaŋan-ʡajam → tatapaŋanʡajam`, `ħoːŋ-jən-ʦi → ħoːŋjən ʦi`
- plus an **o~u notation fix**: `*aɾɾo~u~us → *aɾɾo~us` (spurious `~u` doubling removed).

These are PHON-side cleanups/bug-fixes (the stripped `=`/`-` are markup/segmentation,
not phonemes). **Separate data-quality flag:** the `==` Wikipedia heading markup is
still present in the **FORM** tiers (a scrape artifact); the PHON change only hides
it from phonology. Worth cleaning in FORM independently of this rerun.

## Per-corpus summary

| Corpus | std FORM Δ | orig PHON Δ | std PHON Δ | Nature |
|---|---|---|---|---|
| Latham-1862 | 0 | 0 | 0 | serialization only |
| Virginia_Fey_Dictionary | 0 | 0 | 0 | serialization only |
| Glosbe | 0 | 83 | 94 | **PHON improvement only** (ng→ŋ) — clean win |
| SEALS33 | 9 | 11 | 11 | FORM hyphen reversion (§A1) + Seediq phon rules (§B2) |
| WilangYutasVideos | 26 | 40 | 40 | FORM hyphen reversion (§A1) + downstream PHON |
| FormosanBankGitBook | 99 | 102 (added) | 102 (added) | FORM u→o reversion (§A2) + PHON newly added (§D) |
| Wikipedias | 0 | 7998 | 7998 | **PHON improvement only** — markup/hyphen strip + o~u fix (§E); FORM `==` flagged |

## Flags (likely problematic / unintended)

- **All standard-FORM changes (§A)** are reversions of `clean_xml`/u→o cleanups.
  Rerunning `standardize --copy` + `add_phonology` **alone does not reproduce the
  committed standard tier** for any corpus whose orthography strips hyphens (or
  that relied on u→o). Do not commit the standard-FORM changes without running
  `clean_xml` after `standardize`.
- **FormosanBankGitBook** shipped **without any PHON** — that itself may be worth
  addressing regardless of this rerun.

## Recommendation

The genuine value of the rerun is the **PHON improvements** (§B): the `ng→ŋ` fix
and the new dialect-scoped rules. To capture those without the standard-FORM
reversions, the rerun sequence should be `standardize` → **`clean_xml`** →
`add_phonology` (clean_xml re-strips hyphens/normalizes the standard tier before
phonology). Glosbe is the one corpus where std+phon alone is already a clean win
(no FORM change, only PHON improvement).

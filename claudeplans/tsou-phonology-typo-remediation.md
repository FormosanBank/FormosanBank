# Tsou phonology typo — fix + targeted remediation

**Date:** 2026-06-14
**Discovered during:** add_phonology run on the Taiwan-Bible-Society Bibles dev repo.

## The bug

The Tsou orthography tables mapped the **letter `a` to IPA `s`** (a mistyped IPA
column) in *four* files:

- `Orthographies/Ortho113/Tsou.tsv`
- `Orthographies/Folk/Tsou.tsv`
- `Orthographies/MinEd/Tsou.tsv`
- `Orthographies/Ortho94/Tsou.tsv`

`add_phonology.py` does ordered string replacement letter→IPA, so **every `a`
became `s`** in generated Tsou `<PHON>` (e.g. `'a'ahaesa'u` → `ʔsʔshsessʔu`,
`ta` → `ts`). This affects any Tsou `<PHON>` ever generated from these tables, and
also any tool that reads them (orthography_detector, validate phonology) — but the
only **persisted** artifact is `<PHON>` text in corpora.

A repo-wide scan for `letter 'a' → non-/a/ IPA` found **no other language affected**
— the bug is isolated to Tsou.

## The fix (done, pushed)

Changed the `a` row in all four tables from `a⇥s` to `a⇥a`. One-line correction per
file; no other rows touched. Verified:

```bash
for f in Orthographies/*/Tsou.tsv; do printf "%-32s " "$f"; awk -F'\t' 'NR>1&&$1=="a"{print "a -> "$2}' "$f"; done
# all four now report: a -> a
```

## What needs re-running (audit of Corpora/)

Tsou `<PHON>` exists (both `kindOf="original"` and `kindOf="standard"`) and is
corrupted in **4 corpora / 25 files**:

| Corpus | Tsou files w/ PHON |
|---|---|
| `Corpora/ILRDF_Dicts` | 1 |
| `Corpora/NTUFormosanCorpus` | 12 |
| `Corpora/Presidential_Apologies` | 1 |
| `Corpora/ePark` | 11 |

In all sampled files the existing `original` and `standard` PHON were generated with
the **Ortho113** Tsou table (evidence: `ʉ → ɨ`, the Ortho113 mapping; Folk would give
`ɯ`). So regeneration uses `--orthography Ortho113` for both tiers.

Nothing else needs touching: `<FORM>` text is unaffected (the typo only hits PHON),
and no non-Tsou content is involved.

> The Bibles dev repo's Tsou (`Formosan-Taiwan-Bible-Society-Bibles`) was also
> regenerated, but there the original tier is **Folk** (`--orthography Folk`), so use
> Folk for that repo, Ortho113 for the published corpora above.

## Method — fix only the Tsou PHON, per corpus

`add_phonology.py --language Tsou` filters to Tsou-path files and **overwrites**
existing `<PHON>` text in place (it reuses the existing PHON element, just rewrites
`.text`). Run from the repo root with the venv active:

```bash
source .venv/bin/activate
for C in ILRDF_Dicts NTUFormosanCorpus Presidential_Apologies ePark; do
  python QC/utilities/add_phonology.py \
    --corpora_path "Corpora/$C/XML" \
    --language Tsou \
    --orthography Ortho113
done
```

Notes / caveats:
- Standard-tier PHON always uses `Ortho113/Tsou.tsv`; `--orthography Ortho113` makes
  the original tier use the same table (matching how these corpora were built).
- Only files whose path matches `Tsou` are touched; other languages' PHON are left
  alone. add_phonology picks the IPA table from each file's own `xml:lang`, so a path
  match on a non-Tsou file would still be harmless.
- Side effect: each touched file is re-serialized (pretty-printed), so the git diff
  shows whole-file reformatting even though only `<PHON>` text changed. Review with
  `git diff --word-diff` and confirm `<FORM>`/`<TRANSL>` text is unchanged.

## Verification after re-running

```bash
# No Tsou PHON should turn a source 'a' into 's'. Spot-check FORM vs PHON:
python3 - <<'PY'
import glob; from lxml import etree
for f in glob.glob("Corpora/**/Tsou/**/*.xml", recursive=True) + glob.glob("Corpora/**/Tsou/*.xml", recursive=True):
    for s in etree.parse(f).getroot().iter('S'):
        forms={x.get('kindOf'):(x.text or '') for x in s.findall('FORM')}
        phons={x.get('kindOf'):(x.text or '') for x in s.findall('PHON')}
        # a word containing 'a' in FORM should keep 'a' (→/a/) in PHON, never become 's'
        if 'a' in forms.get('standard','') and 's' in phons.get('standard','') and 'a' not in phons.get('standard',''):
            print("SUSPECT", f, s.get('id')); break
PY
```

Then run the normal phonology-aware validators if desired
(`QC/validation/validate_xml.py`, orthography checks).

## Token/metrics impact

None. `<PHON>` is not counted by `QC/corpus_counts.py` (tokens come from `<FORM>`),
so corpus-size/token CI is unaffected by this regeneration.

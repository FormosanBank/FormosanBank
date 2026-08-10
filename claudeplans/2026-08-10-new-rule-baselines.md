# Baseline runs of the 2026-08-10 rules over published corpora

First run of each new check against `Corpora/` (and the registries) on
branch `proposal/qc-improvements`. These are the "corpora that will trip
this" worklists the rules were expected to produce. Nothing here blocks
CI; every item is review material.

## V142 unmarked grammaticality (SOFT) — 8 findings, 4 sentences

Each is a leading `? ` in FORM, on both tiers. In these narrative /
e-learning corpora the marker is more plausibly stray punctuation (a
question mark split from the preceding sentence) than a marginality
judgment — review and fix the text rather than adding grammaticality
marking:

- `NTUFormosanCorpus/.../Kanakanavu_kkvNr_millet_Muu.xml` S `…_S_23`
- `Wikipedias/XML/Sakizaya/miladlad_tu_udip.xml` S `0`
- `ePark/.../gao_zhong…/Bunun/Luanqun_Bunun.xml` S `213_14285`
- `ePark/.../guo_zhong…/Bunun/Luanqun_Bunun.xml` S `213_27157`

## V143 TRANSL language/script mismatch — 0 findings

No swapped-language files currently published (the NTU Bunun swap was
already remediated). The rule is a tripwire for future intakes.

## V144/V145 M-tier consistency (POL-023) — V145 clean; V144 four corpora

V145 (spurious all-single-M tier): **zero** — the Yedda case was already
fixed. V144 (M-less W in a segmented file), occurrences = W elements
lacking an M:

| Corpus | occurrences | files |
| --- | --- | --- |
| NTUFormosanCorpus | 477 | 7 (Grammar/Seediq 243, Grammar/Kanakanavu 26, …) |
| WakelinTexts (Yami) | 428 | 6 |
| Li-Conjunction-Thao | 140 (of 211 W) | 1 |
| Song-Kanakanavu-Grammar | 7 (of 3477 W) | 1 |

Li-Conjunction-Thao's 66% rate suggests a corpus where only some words
were segmented — maintainer review needed on whether to complete the
segmentation, add single Ms, or accept the finding as documented.

## V070 gloss-code-as-FORM (WARN) — 16 occurrences, 6 files

All in `NTUFormosanCorpus/XML/Stories/Seediq/`: M FORMs that are the bare
code `RED` (reduplication) — plausible genuine impostors where the
reduplicant's form was replaced by its gloss label.

## validate_port_readiness over all 26 published corpora

HARD (exit 1):
- **Latham-1862**: P002 — `xml:lang="bzg"` (Babuza) not in the Formosan
  ISO map. The known §4.3 naming remediation (rename/wire ISO map).
- **Wikipedias**: P003 ×5 — TEXTs with no `dialect` attribute
  (`'ayam.xml`, `'Etolan.xml`, `1984.xml`, `'Oponoho.xml` ×2).

WARN:
- P005 stale audio counts: ILRDF_Dicts (98825 vs 98827), NTUFormosanCorpus
  (14663 vs 14666), ePark (409078 vs 409081) — matches CI's STALE AUDIO
  signal; refresh via `refresh_audio_stats.py`.
- P006: Li-Conjunction-Thao uses `Thao_Li_113.tsv` — validate before
  trusting the standard tier.

## validate_registries (V150–V153 SOFT) — 4 findings

- V152 ×2: `Seediq_94_113.tsv` / `Seediq_Church_113.tsv` value column
  `Truku` not canonical under dialects.csv's Seediq entry (the
  Seediq/Truku modeling wrinkle).
- V153 ×2: `Bunun.rules.tsv` scopes rules to dialect `Zhuoqun` —
  dialects.csv spells it `Junqun` (romanization drift); `Seediq.rules.tsv`
  scopes to `Truku` (same wrinkle as V152).

## run_conversion_table_checks — 20 OK, 5 structural, 16 phoneme-level (of 41)

Structural (fix): `Kavalan_MinEd_113.tsv`, `Saisiyat_Tsuchida_113.tsv`,
`Yami_Wakelin_113.tsv` (source profile missing), `Pazeh_Tsuchida_113.tsv`
(no Ortho113 Pazeh target profile — consistent with blank standards.csv
entry), `Saisiyat_folk_113 2.tsv` (stray filename with a space — known).
Phoneme-level (review, may be legitimate): 16 tables listed in the CI
driver output; includes the open `Paiwan_Ferrell` `Ḍ` question and the
`Seediq_Church` Truku column-resolution failure (same root as V152).

## Also flagged during test-plan execution

`apply_manual_edits.py` **prunes** a record from `manual_edits.xml` when
it no-ops (XML already matches). Correct for the fresh-rebuild flow; but
running pipeline step 0 over *already-edited published XML* would prune
every record, losing the reproducibility trail. Maintainer ruling needed:
prune at apply time vs warn-only (pinned as a characterization test in
`tests/cleaners/test_manual_edits_survival.py`).

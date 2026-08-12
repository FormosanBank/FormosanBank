# Phase B regeneration report — Li-Conjunction-Thao

**Date:** 2026-08-12 · **Branch:** `sweep/b2-lithao` · **Group:** 2 (bespoke
post-standardize step)
**Corpus:** `Corpora/Li-Conjunction-Thao` — Li (2014), *Conjunction in Thao*.
Thao (`ssf`, dialect="Thao"), 1 XML file, 27 S / 211 W / 169 M. No audio.
Original tier = Li's scholarly IPA-style transcription; standard tier =
Ortho113 via the `Thao_Li_113.tsv` conversion table.

## 1. POL-035 snapshot: NOT REQUIRED (fully regenerable)

The corpus is rebuilt end-to-end from a committed input —
`CodeAndDocs/raw_data/reviewed_examples.tsv` (the reviewed transcription
records) — by `CodeAndDocs/scripts/build_xml.py`. Per POL-035, regenerable
corpora need no pre-correction snapshot: the pipeline *is* the baseline.
Additionally, no correction machinery modifies this corpus's original tier —
`clean_xml` now runs (§4) and changes nothing — so there is nothing a snapshot
would guard.

## 2. P006 conversion-table verification (ruling 3): PASS

```
validate_conversion_table.py Orthographies/Li/Thao.tsv \
    Orthographies/Ortho113/Thao.tsv \
    Orthographies/ConversionTables/Thao_Li_113.tsv
```

**Result: PASS — confirmed=8, warning=0, mismatch=0, unknown_source=0,
untokenizable=0; no merges, no information loss, no coverage gaps, no
integrity errors.** All 8 rows confirmed transitively through IPA, including
the two guard rows `lh→l.h` / `th→t.h` (which protect literal source `l+h` /
`t+h` sequences from being misread as Ortho113 digraphs). No phoneme-level
review material; nothing to fix. The standard tier can be trusted as far as
the table is concerned.

## 3. Standardize-mode reconciliation (`--copy` → `--remove_accents` ruling)

The blanket ruling replaces README `--copy` steps with `--remove_accents`.
**Not applicable here — TSV mode kept**, as the ruling's own exception
provides: this pipeline's standardize step is a real orthography *conversion*
(`--tsv_path Thao_Li_113.tsv --target_column standard`, Li transcription →
Ortho113), not a copy. TSV mode already strips the stress accents (`á`/`ú`)
as part of conversion, so `--remove_accents` would be both redundant and
wrong (it would skip the Li→Ortho113 mapping). Documented in the README.

## 4. Pipeline: one entry point, `CodeAndDocs/make_xml.sh`

**Script consolidation (maintainer ruling: no wrapper spaghetti).** The first
pass added `make_xml.sh` as a thin wrapper around `scripts/reproduce.sh`. That
was two scripts for one pipeline. `scripts/reproduce.sh` is now **deleted**
(`git rm`) and its body absorbed into `make_xml.sh`, which is the single,
self-contained entry point — matching the `CodeAndDocs/make_xml.sh` convention
already used by Glosbe, Latham-1862, SEALS33, Virginia_Fey_Dictionary,
WilangYutasVideos and FormosanBankGitBook. The README documents exactly one
command. No other duplicated wrapper exists in this corpus: `scripts/` holds
three genuine single-purpose steps (`build_xml.py`,
`audit_source_fidelity.py`, `flatten_standard_segmentation.py`), and
`download_source_data.sh` is source acquisition, not a rebuild path.

Steps:

1. `scripts/build_xml.py` — build draft + Final_XML from the reviewed TSV
   (includes the two scripted Blust-typo corrections `S→ʃ` ×1, `D→ð` ×6,
   README-documented; POL-038-compliant: in committed code, not hand edits)
2. `scripts/audit_source_fidelity.py` — source-fidelity audit (PASS: 5 fixed
   checks, 27 structural checks, all 24 glossed examples align)
3. **`QC/cleaning/clean_xml.py`** — added this pass (see below)
4. `standardize.py --tsv_path Thao_Li_113.tsv --target_column standard`
   (TSV mode, see §3)
5. `scripts/flatten_standard_segmentation.py` — the Group 2 bespoke step:
   strips `- = < >` from S-level standard FORMs. Still required after C012
   because (a) C012 exempts Thao hyphens (`-` is a letter in the reference
   orthography — but in this source `-` is only ever Li's morpheme boundary;
   glottal is `ʔ`) and (b) no shared code strips infix `<`/`>` from S-level
   standard FORMs. W/M tiers keep all markers (they carry the analysis).
6. `add_phonology.py --orthography Li` (standard PHON from Ortho113,
   original PHON from `Orthographies/Li`)
7. draft/final byte-match check (`cmp`) — PASS; install `Final_XML` →
   corpus-level `XML/`; remove scratch (`CodeAndDocs/XML`, `Final_XML`,
   `intermediate`, sidecars)

Steps 3–6 run over both trees (draft `XML/` and `Final_XML/`).

### `clean_xml` is now in the pipeline (maintainer ruling)

The first pass omitted `clean_xml` and justified it with "no quote-correction
machinery runs here". **That justification was wrong and is retracted.**
`clean_xml` does far more than quote correction: dash/tilde/quote
canonicalization, HTML-entity and double-encoded-entity decoding, null-glyph
canonicalization, Unicode flattening, empty-element removal, and
translation-metadata normalization. None of that is inapplicable to this
corpus in principle.

- **Position:** after the build, **before `standardize`** — verified against
  the other corpora that run it (`Glosbe` step 1 → standardize step 2;
  `Latham-1862` step 1 → standardize step 2; `SEALS33` step 1 → standardize
  step 2). Rationale: the standard tier is rebuilt *from* the original tier,
  so the original must be cleaned first.
- **Result: no-op, confirmed empirically.** Running the full pipeline with
  `clean_xml` in place reproduces the published XML byte-identically (md5
  `fc06971575dc19abcf2b0c1361b7d1ae`, unchanged from the pre-ruling run), and
  the diff vs `main` is still **exactly the 54 PHON punctuation-drop values**
  (§6) — nothing added, nothing else touched. `make_xml.sh` cmp's each tree
  before/after `clean_xml` and prints `clean_xml (<tree>): no-op` per run, so
  a future regression is visible rather than silent.
- **Correct justification:** `clean_xml` is a no-op here **because the XML is
  born clean from the reviewed TSV** — the input is a hand-reviewed record
  with no entities, no smart quotes, no stray Unicode — not because the
  machinery is absent or disarmed.
- **Thao's letter `-` is safe.** `-` is a letter in the Thao reference
  orthography; `clean_xml`'s dash rule maps only dash *look-alikes* (en dash,
  em dash, minus sign, …) onto ASCII `-` and never rewrites an ASCII `-` that
  is already present. Confirmed by the zero diff: all 88 c012-flagged hyphens
  survive `clean_xml` untouched and are removed later, as designed, by
  `flatten_standard_segmentation.py`.
- **Sidecars:** no `cleaner_warnings.csv` was produced (the writer skips empty
  runs). `make_xml.sh` additionally **fails loudly** if a
  `quote_corrections.csv` ever appears, since `clean_xml` derives that durable
  POL-035 log's location from a published `XML/` tree and would misplace it
  when run against the scratch trees. Today it never fires.

Still deliberately absent: **`apply_manual_edits`** (no `manual_edits.xml`
exists — a true no-op step with nothing to apply).

**Idempotence verified:** re-running the consolidated `make_xml.sh` reproduces
the published XML byte-identically (md5 `fc06971575dc19abcf2b0c1361b7d1ae`,
`cmp` clean against the pre-run copy).

## 5. Warning sidecars (POL-033: reviewed, then deleted)

`standardize_warnings.csv` (one per tree, XML + Final_XML): **exactly 88 rows
each, all `c012`** — the transient Thao-hyphen-exemption warnings the README
predicts (flatten strips those hyphens immediately after). Nothing else.
Deleted with the scratch trees; nothing committed.

`cleaner_warnings.csv`: **not produced** — `clean_xml` found nothing, and its
writer skips empty runs. `quote_corrections.csv`: **not produced** — no
quote/glottal rewrite fired (Thao has no attestation dictionary, so the
quote-correction rule never arms), and `make_xml.sh` now hard-fails if one ever
appears rather than discarding it with the scratch trees. Verified zero
`*_warnings.csv` / `quote_corrections.csv` anywhere under the corpus after the
run — nothing UNEXPLAINED.

## 6. Diff audit vs git HEAD — 100% classified

Element-by-element comparison (every FORM/PHON/TRANSL of every S/W/M matched
by id + kindOf). Structure identical: 27 S / 211 W / 169 M both sides, zero
elements added/removed/reordered, TEXT attributes unchanged. 2,036 leaf
elements compared:

| tier | compared | differing |
|---|---:|---:|
| S FORM orig/std | 27 + 27 | 0 |
| S PHON orig | 27 | **27** |
| S PHON std | 27 | **27** |
| S TRANSL | 27 | 0 |
| W FORM/PHON/TRANSL (orig+std) | 1,055 | 0 |
| M FORM/PHON/TRANSL (orig+std) | 845 | 0 |

**54 differences, one class, 100% classified (0 UNEXPLAINED):**

- **PHON punctuation drop ×54** (27 original + 27 standard, S-level only):
  removing the sentence `.`/`,` from the old PHON yields the new PHON exactly,
  character for character. This is the shared-source-phonology "punctuation is
  not sound" policy, the precise diff the README's 2026-08-10 verification
  predicted, and the same expected class as HPS/Presidential_Apologies.
  W/M PHON are unaffected because `build_xml.py` already strips edge
  punctuation from word tokens.

No original-tier text changed anywhere. No FORM, TRANSL, or gloss changed.

## 7. Token delta and validators

Re-measured after the `clean_xml` addition and the script consolidation, with
"before" = the `main` blob restored into place and re-validated:

| check | before (`main`) | after | HARD |
|---|---|---|---|
| tokens (Thao/Thao) | 227 | 227 (**delta 0**) | — |
| `validate_xml` | SOFT 140 × V144 | SOFT 140 × V144 | 0 / 0 |
| `validate_text` | SOFT 86 (V122 ×44, V134 ×20, V136 ×22) | identical, 86 | 0 / 0 |
| `validate_glosses` | SOFT 3 × V060 | identical, 3 | 0 / 0 |

Structure unchanged: 27 S / 211 W / 169 M. V122 = English parens in TRANSL;
V134 = the 10 infix `<...>` pairs in original S FORMs (source notation,
faithful); V136 = Greek-block θ in Li's transcription mixing with Latin
(scholarly transcription, faithful). All previously accepted; the README now
records the concrete baseline, including `validate_glosses`.

## 8. Issue #102 disposition (NON-AUTHORITATIVE input — verified locally)

**The two measured facts, plainly:**

1. The corpus has **211 W elements, of which 140 have no M child** (counted
   directly from the published XML; matches the 140 SOFT V144 findings).
2. **`validate_glosses` reports 0 HARD findings** — only 3 SOFT V060
   (`W_count_matches_word_count`).

So issue #102's **gloss-validator concern is satisfied** (the gloss tier is
HARD-clean, before and after this regen) while its **M-coverage concern is
not** (V144 SOFT ×140 stands). M coverage remains an **unruled linguistic
worklist item**: **no M elements were added**, per instruction, and none should
be added to close the issue until the maintainer rules on the analysis. Both
facts are now stated in the README's QC-baseline note and its M-coverage note.

State of its other claims against this regen:

- "140 of 211 W have no M; POL-023 V144" — **reproduced exactly** (140 SOFT
  V144, before and after). The issue's "Done when V144 is cleared" framing is
  *not* actionable in this sweep — completing source-supported morphology is
  expert linguistic work awaiting a maintainer ruling.
- "review 20 V134 / 22 V136 against the source" — both counts reproduced;
  both are documented, accepted source-fidelity characteristics (infix
  notation; Li's IPA θ). No characters were deleted (the issue itself warns
  against bulk deletion). Dispositions recorded in the README QC section.
- "Validate the documented Thao conversion before regenerating" — done, §2,
  PASS.
- "no current HARD finding" — confirmed before and after.

Issue remains open; its only outstanding substance is the V144 worklist.

## 9. Files changed

- `Corpora/Li-Conjunction-Thao/XML/Thao/li_2014_conjunction_in_thao.xml` —
  regenerated (54 PHON values)
- `Corpora/Li-Conjunction-Thao/CodeAndDocs/make_xml.sh` — new, and now the
  **single** entry point: the whole pipeline inline, with `clean_xml` added
  before `standardize`, a per-run no-op check on it, and a guard against a
  misplaced `quote_corrections.csv`
- `Corpora/Li-Conjunction-Thao/CodeAndDocs/scripts/reproduce.sh` — **deleted**
  (absorbed into `make_xml.sh`; no wrapper layer)
- `Corpora/Li-Conjunction-Thao/README.md` — one documented command; pipeline
  listed step by step incl. `clean_xml` with the corrected justification
  ("born clean from the reviewed TSV", not "no quote machinery") and the
  Thao-`-`-is-a-letter safety note; TSV-mode + conversion-table-PASS note;
  regen note updated from "verified" to "applied"; M-coverage note now gives
  both issue-#102 facts (140/211 M-less; `validate_glosses` 0 HARD); QC
  section restated as the current concrete validator baseline for all three
  validators (stale dev-repo `docs/qc_report.md` / `logs/final_qc/`
  references dropped)
- `claudeplans/phase-b-reports/Li-Conjunction-Thao.md` — this report

**UNEXPLAINED: none.** GitBook page update (procedure step 9) is post-approval
and not part of this branch.

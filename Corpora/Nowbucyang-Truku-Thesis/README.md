# Nowbucyang-Truku-Thesis

Truku linguistic examples extracted from Lowking Wei-Cheng Hsu / 許韋晟, 2008,
太魯閣語構詞法研究 [Word Formation in Truku], MA thesis, National Hsin-Chu
University of Education. 278 sentences (`xml:lang="trv"`, `dialect="Truku"`)
with Chinese translations; word (W) and morpheme (M) segmentation where the
thesis's interlinear gloss line aligned reliably with the Truku tokens.

## License and AI Use

This corpus is subject to its source license and the central FormosanBank terms
in [LICENSE.md](../../LICENSE.md) and
[AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI Use is prohibited
without prior written permission. The thesis is used with the author's
permission (`rights_status=full_rights_obtained` in `TEXT@source`).

## Orthography

The thesis writes Truku in Ortho94 (recorded in `TEXT@source` and
`CodeAndDocs/data/processed/orthography_report.md`). The `original` FORM tier
preserves the thesis's spelling and segmentation notation — except for the nine
sentences that carry no W/M tier, whose original FORMs are written without
segmentation markers (see "Manual edits"); the `standard` tier
is the machine-owned de-segmented form (see pipeline below). PHON tiers are
IPA: `original` from the Ortho94 Seediq profile, `standard` from the Ortho113
Seediq profile (both via their `Truku` dialect columns, including the Truku
phonotactic rules — e.g. i/u lowering next to q/h, palatal [c] before i/y).

## Reproducing the XML

```bash
Corpora/Nowbucyang-Truku-Thesis/CodeAndDocs/make_xml.sh
```

`make_xml.sh` is the **single entry point** — it invokes
`scripts/pipeline.py --step <name>` directly (there are no per-step wrapper
scripts) and then the FormosanBank QC tools. It rebuilds
`XML/Truku/Hsu_Lowking_Truku_WordFormation_2008.xml` end-to-end from
**committed inputs** (no PDF work needed) and is idempotent:

1. **Build** (`scripts/pipeline.py --step build_formosanbank_xml`): emits the
   raw corpus XML from the committed parse intermediates under
   `data/processed/` (`quality_filtered_examples.jsonl`, `gloss_records.jsonl`,
   `duplicates.csv`, `overlap_candidates.csv`), then merges
   `data/manual/manual_sentences.xml` (see "Manual edits"). The internal
   structural check (`--step validate_formosanbank_xml`) runs next.
2. **FormosanBank QC** (run from the repo root with its `.venv`):
   `apply_manual_edits --manual_file CodeAndDocs/manual_edits.xml` (recorded
   hand edits first, POL-030; see "Manual edits") →
   `clean_xml` (typography/character canonicalization; POL-010/011/012/013) →
   `standardize --tsv_path Orthographies/ConversionTables/Seediq_94_113.tsv`
   (the `Truku` column, selected by `TEXT@dialect`) →
   `remove_duplicate_sentences --tier original --scope file --apply` (residual
   duplicate merge, POL-022/POL-025; see "Duplicates") →
   `add_phonology --orthography Ortho94`.

`clean_xml` runs **once**. Older documented orders for this corpus ran it a
second time after `standardize`, to strip the segmentation markers the standard
tier used to carry; since POL-002 `standardize` owns all standard-tier cleaning
(its C012 step strips `-` and `=` from the S-level standard FORM of every
morpheme-segmented sentence — `trv` is not one of the hyphen-is-a-letter
orthographies), so the second pass had nothing left to do. Removing it
reproduces the published file byte-identically; do not re-add it.

The `Seediq_94_113.tsv` `Truku` column currently contains **no letter
conversions** (verified with `validate_conversion_table.py`, PASS), so the
standard tier is the original minus segmentation hyphens, clitic `=`, and null
morphemes (C012), with accents stripped. If Ortho94→Ortho113 letter mappings
for Truku are ever added to that table, rerunning `make_xml.sh` applies them.

Only if the *parse itself* must change (e.g. a new PDF extraction) do the
earlier pipeline steps matter; they are all in `scripts/pipeline.py`
(`--step inspect_pdf` … `dedupe_against_formosanbank`, in the order listed in
`STEP_FUNCS`) with the source PDFs committed under `data/raw/pdf/`. No OCR is
used anywhere. Deduplication (`dedupe_examples`,
`dedupe_against_formosanbank`) removes exact Truku+translation pairs
within-thesis and flags overlaps with other FormosanBank Truku corpora — see
"Duplicates" below for what that leaves behind and how Phase 2 handles it.

## Manual edits

Two mechanisms, applied in this order:

1. [`CodeAndDocs/data/manual/manual_sentences.xml`](CodeAndDocs/data/manual/manual_sentences.xml)
   — the corpus's own *additions/overrides* file, merged by sentence id inside
   the Phase 1 build. Each `<S>` there is appended verbatim and **overrides**
   any automated sentence with the same id, so hand-added sentences survive
   rebuilds. It predates `manual_edits.xml`; per the 2026-08-11 ruling it stays
   as-is.
2. [`CodeAndDocs/manual_edits.xml`](CodeAndDocs/manual_edits.xml) — the
   repo-standard POL-030 record, re-applied first in Phase 2 by
   `QC/cleaning/apply_manual_edits.py` (changelog:
   [`CodeAndDocs/manual_edits.md`](CodeAndDocs/manual_edits.md)). It holds
   **nine** sentences (`C01_E008Bb`, `C01_E008Cb`, `C01_E011Fb`, `C01_E021Ab`,
   `C01_E027Ab`, `C01_E027Cb`, `C03_E034b`, `C01_E011K`, `C01_E011L`) —
   seven automated slash/parenthesis-variant expansions plus two hand
   additions. None of them was ever fully glossed, so per the maintainer's
   2026-08-12 ruling they get **no W/M tier and no segmentation notation at
   all**: their `original` FORMs are rewritten marker-free
   (`M-gay =ku pila…` → `Mgay ku pila…`) rather than carrying `-`/`=` that
   nothing downstream can resolve. Recording it as a manual edit keeps the
   change reproducible instead of a hand edit lost on the next rebuild.

In both files the records carry only the `original` FORM and the TRANSLs;
standard-FORM and PHON tiers are regenerated downstream (POL-002/003).

## Duplicates

The Phase 1 pipeline declares a dedup step (`dedupe_examples`,
`dedupe_against_formosanbank`), so POL-022 treats residual duplicates in this
corpus as HARD findings. That step's key is the exact (Truku form, Chinese
translation) **pair**, which leaves two kinds of leftover behind. The Phase 2
`remove_duplicate_sentences --tier original` step separates them:

- **Same original FORM, different free translation → merged** (POL-025). The
  same source sentence recurs in two thesis examples with a differently-worded
  Chinese translation; the survivor keeps the extra translations as
  `ver="alt"` and the duplicate `<S>` is deleted. **5 groups merged**
  (5 `<S>` removed, 6 TRANSLs merged as `ver="alt"`).
- **Same standard FORM, different original segmentation → retained
  deliberately.** **3 groups** (`Mgay ku pila sunan ka yaku.`,
  `Mtgsa laqi ka Lowking.`, `Nnima ka srus nii?`) coincide only *after*
  de-segmentation: the thesis writes them with different morpheme notation in
  the two places (`N-nima` vs `Nnima`, `M-tgsa` vs the marker-free variant
  expansion, `Mgay =ku` vs `Mgay ku`). Under POL-022's distinct-provenance
  nuance these are separate attestations of how the source renders the word,
  not a pipeline defect, so they are **kept on purpose** — the residual HARD
  duplicate finding for these three groups is expected and is not to be
  "fixed" by deleting one member.

  All three retentions are **settled maintainer decisions**, including
  `C01_E026A_0079_01` / `C03_E034b`: that pair differs in *both* its
  segmentation (`M-tgsa` vs the marker-free variant expansion) and its Chinese
  translation, and the maintainer ruled (2026-08-12) to **keep both members**
  on exactly that basis — differing on two independent axes makes them two
  distinct attestations, not one sentence recorded twice. It is not an open
  question and must not be merged by a later pass.

## Known QC state (2026-08-12)

- `validate_xml`: clean. 278 sentences, 1,130 W, 1,424 M; token count 1,192.
- `validate_text`: SOFT 16 (V116 non-ASCII ×4, V122 parens/slashes ×12). No
  V126/V133 segmentation findings — the nine W/M-less sentences are
  marker-free on both tiers (see "Manual edits").
- Gloss worklist (GitHub issue #81, linguistic work, open): 120 M without
  TRANSL (V064 HARD), 83 W without gloss (V065), 14 V060 W-count mismatches.
- Duplicates: 3 within-file groups retained deliberately — see "Duplicates".
- V152 (`Seediq_94_113.tsv` value column `Truku` "is not a canonical dialect"):
  a **defect in the V152 rule**, not in the CSVs (maintainer ruling
  2026-08-12). `Truku` is its own language in `languages.csv`
  (`trv` covers both Seediq and Truku, and `dialect="Truku"` resolves the
  column at run time); `validate_conversion_table.py … --dialect Truku`
  returns PASS. No registry change is warranted here; fixing V152 is a
  separate repo-wide task.
- Truku has no attestation dictionary by design (quote-glottal correction
  disarmed for this corpus).

Manual QC review lists from the build are under `CodeAndDocs/data/processed/`
(`manual_qc_slash_options.txt`, `manual_qc_parentheses.txt`,
`gloss_alignment_audit.csv`).

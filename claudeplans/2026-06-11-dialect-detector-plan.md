# Dialect detector — design spec

**Date:** 2026-06-11
**Status:** approved design (pre-implementation)
**Supersedes:** the initial Copilot draft of this file and `QC/utilities/dialect_detector.py`
(both are discarded except for the ideas noted in §10).
**Roadmap home:** §F "Dialect detector".

## 1. Goal & scope

An informational maintainer utility that **guesses `TEXT/@dialect`** when `xml:lang`
is known but the dialect is missing, `unknown`, or untrusted. It ranks the candidate
dialects for a whole XML file and explains why. It **never mutates XML** and **never
gates CI**.

- **Standard tier only.** Uses `FORM[@kindOf="standard"]`. If the standard tier is
  absent, the detector says so and stops — it does **not** fall back to original text.
- **Multi-dialect languages only.** Single-dialect languages (where `dialect` ==
  language name) are out of scope; the tool reports them as unsupported. In-scope
  languages are those with ≥2 Official dialects in `dialects.csv`, plus `trv`
  (ambiguous Truku/Seediq) — i.e. Amis, Atayal, Bunun, Paiwan, Puyuma, Rukai, and
  `trv` (Truku + Seediq's three dialects).
- **Detection unit = the whole TEXT file** (matches the evaluation definition in §8:
  "how many already-labeled XMLs get the right dialect"). Per-sentence scoring is a
  possible later mode, not v1.

## 2. Grounding data (measured 2026-06-11)

Census of labeled standard-tier data under `Corpora/**/XML/*.xml` confirms every
in-scope language has ≥4 dialects with thousands of sentences — per-language modeling
is feasible everywhere. Baseline (Copilot's detector, file-level, train=test):

| Language | top-1 | Weak spot |
|---|---|---|
| Rukai | 1.000 | — |
| Atayal | 0.981 | — |
| Puyuma | 0.977 | — |
| Seediq (`trv`) | 0.973 | Truku 11/13 (2→DeluValley) |
| Bunun | 0.896 | — |
| Paiwan | 0.729 | Northern/Southern/Eastern bleed |
| Amis | 0.625 | Coastal collapses into Southern |

`trv` works because `Seediq.tsv` has a `Truku` column (so Truku gets a letter
inventory and its labeled texts join correctly). **Amis and Paiwan are the targets.**
Both are cases where dialects share nearly identical orthography (e.g. Amis 通用版 =
Xiuguluan/Coastal/Malan/Hengchun share one spelling; only Southern/南勢 differs), so
the discriminator must be **lexical (word choice)**, which the baseline lacked.

## 3. Architecture (approach B: components + learned combiner)

One model per language. Four named, auditable evidence components feed a small learned
per-language combiner that outputs a calibrated probability per candidate dialect.

```
standard text ──► grapheme tokenizer ──► component scorers ──► per-language combiner ──► ranked dialects
                  (longest-match,          orthography             (multinomial logistic     + calibrated P
                   TSV-letter-aware)        char / bigram / word     regression over the      + unknown gate
                                                                     4 component scores)
```

### 3.1 Candidate set + label reconciliation
- Candidates = `_dialect_inventory.valid_dialects(lang_code)` minus `unknown`,
  intersected with the dialects that actually have training data. Reuse
  `_dialect_inventory.py` as the single source of truth (so the tool stays consistent
  with V036 / `fix_dialects.py`). `trv` → `{Truku, Duda, Tegudaya, DeluValley}`.
- Every `dialect=` label encountered is reconciled against TSV columns + `dialects.csv`
  names + a curated alias table (seeded from the PDF renaming notes, §6). **Any label
  that fails to map is logged, never silently dropped** (fixes the current silent join).

### 3.2 Grapheme tokenizer (shared primitive)
A single function converts a standard-tier string into a grapheme sequence by
**longest-match** against the language's TSV letter set, so multi-character letters
(`ng`, `ey`, `ow`, `ci`, `lh`, …) are one unit. All downstream features operate on
graphemes (fixes the digraph bug where scoring iterated single chars). Characters not
in any dialect inventory collapse to one `<unk>` grapheme but are still counted — an
out-of-language letter can be distributionally informative even though it is neutral
for the orthography component (per the maintainer's point #5).

### 3.3 Component scorers
Per candidate dialect `d`, given the tokenized text:
- **`orthography`** — from the TSV. Graphemes attested in *other* dialects but **not**
  in `d` incur a graded penalty proportional to their frequency; graphemes in `d`'s
  inventory give mild support; graphemes in *no* dialect are neutral. This is the
  "hard evidence" channel (the maintainer's point #5: a letter exclusive to dialect X
  is strong independent evidence). PDF hints that are concrete grapheme rules augment
  this channel.
- **`char`** — smoothed log-probability of the text's grapheme **unigrams** under `d`'s
  trained profile.
- **`bigram`** — same for grapheme **bigrams**.
- **`word`** — smoothed log-probability of whitespace **tokens** under `d`'s trained
  word profile. **New vs. baseline**; the lever for unified-spelling dialect groups.

### 3.4 Learned combiner + `unknown`
A per-language **multinomial logistic regression** (scikit-learn) maps the 4 component
scores → a probability distribution over candidate dialects. This *learns* the
orthography-vs-distribution weighting the maintainer flagged as unknown. `predict`
emits `unknown` when top-1 probability < a configurable threshold (default tuned on the
eval score distribution). The winner's explanation reports each component's
contribution, so a maintainer can see "orthography ruled out X; word evidence chose Y."

Overfitting (train == test) is accepted per the maintainer; the combiner is tiny
(4 features) so the risk is low, and the model retrains as the corpus grows.

## 4. CLI

Thin entry `QC/utilities/dialect_detector.py` (package in `QC/utilities/dialect_detector/`):

- **`train`** — walk `Corpora/**/XML/*.xml`, build + persist one model per in-scope
  language from labeled standard-tier text. The "retrain as FormosanBank grows" entry.
- **`predict --path <file|dir> [--lang <iso>]`** — load the cached model for each
  file's `xml:lang`; print a full ranked dialect list with calibrated probability,
  per-component breakdown, and a short "why"; `unknown` when below threshold. Reports
  (not mutates) any existing `dialect=` for comparison.
- **`evaluate [--feature-set all|orthography|distribution|…] [--language <iso>]`** —
  file-level train=test report per §8.

## 5. Model persistence

Per-language models persist as **small committed JSON** under
`QC/utilities/dialect_models/<Language>.json` (decided 2026-06-11): the tool works out
of the box, the eval is auditable in git, and `train` regenerates them. To keep blobs
small, distribution profiles are **pruned** (top-N graphemes/bigrams/words by frequency
plus a smoothing floor) rather than full counts; the combiner is a handful of
coefficients. A `train`-time summary prints document/feature counts per dialect.

## 6. PDF-mined hints (`Ortho113.pdf`)

Mined up front per maintainer direction, with **honest scope**: the Ortho113 **TSVs are
already the structured distillation of this PDF's letter tables**, so ~95% of its
dialect-orthography content is captured by the TSVs the components already use. Reading
the prose (注意事項 / appendix) confirms this — e.g. the Amis notes (PDF p.38) say
Southern/南勢 uses `v`/`b` and `u` while the others use `f` and `o`, which is exactly
what `Amis.tsv` encodes.

The PDF's **genuinely additional** value, captured in committed curated files
`QC/utilities/dialect_hints/<Language>.md` (+ a machine-readable companion):
- which dialect is orthographically "odd-one-out" vs. a unified-spelling group
  (interpretation surfaced in `predict`);
- dialect-conditioned spellings the TSV misses (feed the `orthography` component);
- **naming/alias reconciliation** (appendix p.74: 都達語→都達賽德克語,
  初鹿卑南語→西群卑南語, 北部阿美語→南勢阿美語, etc.) → §3.1 alias table.

**Expectation set explicitly:** measured accuracy gains come from §3.2–§3.4 (working
orthography veto + word features + learned combiner), not from the PDF.

## 7. Module structure

Split the 620-line monolith into focused units under `QC/utilities/dialect_detector/`:

- `graphemes.py` — TSV loading + longest-match grapheme tokenizer
- `features.py` — the four component scorers
- `model.py` — per-language model: profiles + combiner; train / persist / load
- `hints.py` — load curated PDF hints + alias table
- `evaluate.py` — metrics + reports
- `cli.py` — argparse (with the thin `QC/utilities/dialect_detector.py` shim)

## 8. Evaluation harness

Train == test on the already-labeled XMLs (overfit accepted; no K-fold). Per language:
top-1 and **top-2** accuracy; per-dialect precision/recall/F; confusion matrix (file
granularity); a ranked **most-ambiguous XMLs** list (smallest top-1−top-2 margin).
`--feature-set` ablation compares component families so we can see where orthography
alone suffices vs. where word evidence carries it.

**Success criterion:** hold Rukai/Atayal/Puyuma/Seediq ≥0.95 top-1; **materially lift
Amis (0.625) and Paiwan (0.729)** via word features + a working orthography veto;
report results honestly per language (no silent caps).

## 9. Tests (`tests/utilities/`)

Tiny synthetic corpora (as the current tests do) plus one real-data smoke test:
- grapheme longest-match handles digraphs;
- out-of-dialect letters penalize; out-of-*language* letters stay neutral;
- scope guard: single-dialect language → no model;
- `trv` builds a 4-candidate model including Truku;
- a synthetic unified-spelling pair is separated only once word features are on;
- `predict` emits `unknown` on deliberately ambiguous input;
- evaluation metric math (P/R/F, top-2, confusion);
- real-data smoke: Rukai stays ≈1.0.

## 10. Disposition of the existing code

**Keep the ideas:** per-language model, named component scores, `--evaluate` mode,
the single-dialect scope guard, tests-as-pins. **Discard:** the single 620-line module,
char-only (non-grapheme) features, the unguarded label join, and the missing word
signal. The roadmap §F entry and this plan are rewritten; the unrelated "B5 item 24"
roadmap edit Copilot added is left for the maintainer to adjudicate separately.

## 11. Open items

- Final `unknown` probability threshold — set from the eval score distribution during
  implementation.
- Pruning size N for persisted profiles — pick the smallest N that holds eval accuracy.
- Whether to commit the curated PDF-hint files now or as a follow-up once the
  TSV+distribution model's residual confusions are known (informs which hints matter).

# Phase B regeneration report — WakelinTexts

**Date:** 2026-08-12 · **Branch:** `work/b3-wakelin` · **Group:** 2 (batch 3)
**Corpus:** `Corpora/WakelinTexts` — six Yami narrative texts (`tao`,
`dialect="Yami"`) hand-transferred from Indosan/Wakelin/Dararyaw/Kalaku 1958,
*Yami texts*, SIL-UND Work Papers 2(7). 172 S, 851 W, 1097 M, English
translations on all three tiers. No audio.

**Revised 2026-08-12 per maintainer ruling.** The first pass rebuilt the
standard tier with `standardize.py --remove_accents` (copy of the original,
minus S-level hyphens). The maintainer's ruling supersedes that: we do not
know this corpus's orthography and do not know how to convert it, so the
corpus gets **no standard tier at all**. §2.4, §3, §5 and §6 are rewritten;
§2.1–2.3 stand and are the evidence the ruling rests on. The one item the
first pass got materially wrong is called out in §6: the V063 improvement it
claimed does not survive, and is in fact an artifact.

## 1. POL-035 snapshot: TAKEN (before any cleaning)

The corpus was transferred to XML **by hand** from the printed article
(`CodeAndDocs/Original.pdf` is the only committed source artifact) — there is
no scrape or OCR stage, so it is non-regenerable and the hand-typed XML *is*
the source. Pristine `XML/` was copied to
`CodeAndDocs/pre_correction_snapshot/XML/` before any pipeline step and
verified byte-identical (`diff -r`, clean). Documented in the corpus README.
Per POL-038, `make_xml.sh` rebuilds `XML/` from the snapshot; nothing is
hand-edited.

Note the snapshot **contains** the old standard tier (2120 FORMs). It is not
stripped from the snapshot — the snapshot is the baseline and POL-038 forbids
editing it — so the removal happens as a pipeline step on the way out of it
(§3, step 2).

## 2. The orthography question — the corpus's central finding

### 2.1 Conversion-table verdict: `Yami_Wakelin_113.tsv` was not an orthography table — DELETED

Evidence:

- **Content.** The table had exactly one data row: `-` → *(empty)*. It mapped
  no letters at all. Even with a source profile, running it could never
  convert Wakelin spelling into Ortho113 — every letter passes through
  unchanged. It was a de-segmentation rule wearing a conversion table's name.
- **`validate_conversion_table.py` verdict.** It could not run:
  `FileNotFoundError: Orthographies/Wakelin/Yami.tsv`. Issue #80's claim that
  this profile is missing is **CONFIRMED**.

**Deleted this pass** (`git rm Orthographies/ConversionTables/Yami_Wakelin_113.tsv`).
Before deleting, the whole tree was grepped for `Yami_Wakelin` and for
`Wakelin` across `*.py *.sh *.yaml *.yml *.csv *.tsv *.json *.txt *.xsd
*.dtd`, plus targeted greps of `QC/`, `tests/`, `.github/` and
`Orthographies/`: **zero references** anywhere outside `claudeplans/` and
`docs/` prose. Nothing consumed it.

Effect on the registry checks:

| check | with table | without table |
|---|---|---|
| `run_conversion_table_checks.py` | 41 tables, **4 structural defects** (incl. `Yami_Wakelin_113.tsv: source profile missing`) | 40 tables, **3 structural defects** |
| `validate_registries.py` | V152 ×2, V153 ×1 | V152 ×2, V153 ×1 (**identical** — the table was not implicated) |

Both are happy afterwards; the deletion removes one permanent structural
defect and introduces nothing.

### 2.2 What the source orthography actually is — partially established, not invented

The article states no writing system. The transcription does not match any
profile in `Orthographies/`: it uses `u` (1207 occurrences) where modern Yami
writes `o` (11 occurrences), `e` for a vowel the article describes only as
"free fluctuation between phonemes /e/ and /a/", and it has no `'`, `j`, or
`z`. One symbol *was* positively identified:

- **`?` is a letter, not punctuation** — **47 occurrences** in FORM elements
  (20 at S level, **27 inside W and M FORMs**). It sits word-internally and
  word-finally inside single words (`tau?` 'person', `uvi?` 'potato', `lavi?`
  'cry', `kayu?` 'tree', `ina?` 'mother') and appears in plainly declarative
  sentences (`amyan su tau? nu-kakwa i-m-angay mang-aep su uvi?` = "A long
  time ago, there was a person who went to get some potatoes."). It is a
  segment the modern orthography leaves unwritten — on the 1958 SIL
  convention, almost certainly the glottal stop. **Still awaiting the
  maintainer's confirmation**; this is the single item whose resolution would
  most advance identifying the writing system.

### 2.3 Consequence: no `add_phonology` step (evidence-backed, not a punt)

Probed empirically in the first pass; the probe stands and is now recorded in
the README and in `make_xml.sh`. Running `add_phonology --orthography
Ortho113` (Yami's `standards.csv` entry) produces 4240 PHON values with
**zero** `*` markers — i.e. it fails silently rather than loudly:

| source | Ortho113 PHON | what happened |
|---|---|---|
| `tau?` | `tau` | **the glottal-stop letter is deleted** — `?` is treated as punctuation and dropped |
| `uvi?` | `ufi` | `v`→`f`, plus the same deletion |
| `su` | `ʂu` | asserts a retroflex sibilant the 1958 transcription never claims |
| `s-ina-na` | `ɕinana` | asserts an alveolo-palatal |
| `-em` | `-əm` | asserts schwa for the vowel the article calls unstable |

`standards.csv` is untouched.

### 2.4 Pipeline choice (RULED): no standard tier at all

The first pass reasoned that `--remove_accents` asserts no orthography and so
was safe. The ruling rejects the premise that a `standard` FORM can be
content-free: a standard FORM *is* a claim that the text has been
transliterated into FormosanBank's common orthography, and we cannot make
that claim about a text whose writing system is unidentified. A tier that
duplicates the original minus some hyphens states nothing true and invites
downstream consumers to treat it as comparable across corpora, which it is
not.

So: **every `FORM[@kindOf="standard"]` is removed, at S, W and M level**, and
neither `standardize.py` nor `add_phonology.py` runs. PHON is removed by the
same step for the same reason (there is none in the snapshot; see §3). The
published corpus carries only the `original` tier.

Hyphens are therefore kept everywhere, exactly as printed — with no standard
tier there is no de-hyphenated reading tier and nothing is de-hyphenated.

## 3. Single entry point: `CodeAndDocs/make_xml.sh` (executable, committed)

There was no script of any kind in `CodeAndDocs/` before this work — only
`Original.pdf`. The wrapper is the one documented command
(`./CodeAndDocs/make_xml.sh [FORMOSANBANK_ROOT]`):

0. restore `XML/` from the POL-035 snapshot (the pipeline's only starting point)
1. `QC/cleaning/clean_xml.py`
2. `CodeAndDocs/drop_derived_tiers.py` **(new this pass)**

Root/interpreter parameterized as in SEALS33 (`FORMOSANBANK_ROOT` arg or env,
`PYTHON` override). `apply_manual_edits`, `standardize` and `add_phonology`
are deliberately absent — the first has no records to apply, the other two are
§2.4/§2.3.

**Step 2, `drop_derived_tiers.py`** — a corpus-local one-off script, the form
POL-038 prescribes for exactly this ("a one-off script committed to
`CodeAndDocs/`"). It deletes every `FORM[@kindOf="standard"]` and every `PHON`
at S/W/M level, preserving indentation by hand (an element's tail is the
whitespace preceding its *next* sibling, so dropping a non-final child drops
exactly the right whitespace; dropping a final child hands its tail to the
sibling that becomes final). It writes through the shared
`QC/utilities/_prettify.prettify` with standardize.py's blank-line-stripping
idiom, so serialization is byte-identical to house style — corroborated in §5
by a diff with **zero** added lines.

It removes PHON although the snapshot has none, so that "this corpus asserts
no orthography and no pronunciation" is a guarantee of the pipeline rather
than an accident of the input — the same reasoning that keeps the (currently
no-op) `clean_xml` step.

**Verified idempotent** three ways: a second full `make_xml.sh` run is
byte-identical (`diff -r` clean); a third run after the docs edits is
byte-identical to both; and re-applying step 2 alone to already-processed
output removes `0 standard FORM, 0 PHON` and changes no byte.

Run output: `TOTAL: removed 2120 standard FORM, 0 PHON across 6 files`
(Kalaku1 227, Kalaku2 204, Kalaku3 140, Kalaku4 366, Kangkang 514, Kwaway 669).

## 4. Warning sidecars (POL-033) and quote correction

**No sidecar of any kind was produced** — no `cleaner_warnings.csv`, no
`standardize_warnings.csv`, anywhere in the repo. Nothing to review or delete,
nothing committed.

**Yami is DISARMED and stayed disarmed.** No `QC/validation/reference/Yami/
attestation.txt` exists (only `default/`), and **no `quote_corrections.csv`
was created** anywhere in the tree. This is over-determined here: the original
tier contains **zero apostrophes** of any kind (full character inventory:
`a n u i m k e y t g r s l w d p c h v b o D` plus `- ( ) / ? . ` and space —
pure ASCII, no curly quotes, no dash look-alikes, no tildes, no null glyphs).
There is no quote question in this corpus to get wrong.

## 5. Diff audit vs `main` — 100% classified

Scripted element-by-element comparison of every atomic datum in all 6 files:
TEXT/S/W/M attribute sets, child-element lists, and every FORM/PHON/TRANSL
value and attribute set keyed by element id and `kindOf`.

**17,020 data points on `main` → 12,780 now. 0 added, 4240 removed, 2120
changed.**

| class | count | notes |
|---|---|---|
| **REMOVED standard FORM — M level** | 2194 | 1097 elements × (`@attrs` + `@text`) |
| **REMOVED standard FORM — W level** | 1702 | 851 elements |
| **REMOVED standard FORM — S level** | 344 | 172 elements |
| **REMOVED PHON** | **0** | expected: neither `main` nor the snapshot has ever had a PHON tier |
| **CHILD LIST: standard FORM dropped — M level** | 1097 | the parent M's child sequence, minus one FORM |
| **CHILD LIST: standard FORM dropped — W level** | 851 | same, at W |
| **CHILD LIST: standard FORM dropped — S level** | 172 | same, at S |
| | **6360** | **TOTAL classified** |

**0 UNEXPLAINED (100%).** Element removal accounts for 2120 standard FORMs
exactly (172 S + 851 W + 1097 M), and the only *changed* data points are the
child lists of the elements those FORMs were removed from.

Everything that survives is byte-identical: **10,660 / 10,660** surviving data
points unchanged, including **all 2120 `original` FORM texts** and **all 2128
TRANSL texts**, every TEXT/S/W/M attribute set, and every id.

Corroborated at the byte level: `git diff main --numstat` is `0 added / 227,
204, 140, 366, 514, 669 deleted` = **2120 deleted lines, 0 added**, and every
deleted line matches `<FORM kindOf="standard"`. No XML-declaration rewrite,
no re-indentation, no trailing-newline change, no serializer churn.

## 6. Token counts and validators

Three states: `main` (the published corpus), *pass 1* (the superseded
`--remove_accents` build), and *now*.

| metric | main | pass 1 | **now** | Δ vs main |
|---|---|---|---|---|
| tokens (Yami / dialect Yami) | 852 | 852 | **852** | **0** |
| S / W / M elements | 172 / 851 / 1097 | same | same | 0 |
| `validate_xml` HARD | 0 | 0 | **0** | 0 |
| `validate_xml` SOFT | 428 | 428 | **2548** | **+2120** |
| `validate_text` HARD | 56 | 56 | **28** | **−28** |
| `validate_text` SOFT | 656 | 657 | **567** | **−89** |
| `validate_glosses` HARD | 91 | 0 | **91** | **0** |
| `validate_glosses` SOFT | 22 | 22 | **22** | 0 |

No validator errored. All three ran to completion and exited 0 under
`--no-exit-on-hard`; every difference below is a rule reporting differently,
not tooling breaking.

**Tokens: 852 → 852, no change.** `QC/corpus_counts.select_sentence_form`
tries `standard` then falls back to `original`, so removing the standard tier
just moves every sentence onto the fallback. It is exactly a wash here for a
second reason: the pass-1 S-level standard FORMs differed from the originals
*only* by deleted hyphens, and a hyphen never splits a whitespace token —
`mang-anak-u-em` is one token either way. Verified by running the counter
against all three states.

Rule-by-rule:

- **V014 `count_missing_standard_form` 0 → 2120** (6 SOFT findings, one per
  file, counts 227/204/140/366/514/669). This is the designed signal for
  exactly this situation, and its own docstring authorizes it: *"Some corpora
  legitimately lack a standard tier because the orthography is unsettled."*
  It is the whole of the validate_xml SOFT delta.
- **V121 `parens_slashes_in_W_or_M_FORM` 56 → 28 (HARD).** On `main` the 56
  split 28 `original` / 28 `standard` — the standard tier duplicated every
  one. The surviving 28 are the original-tier findings, unchanged: the
  article's own `( )` "probable discrepancy" and `/` alternation notation
  (§7 item 3), not defects.
- **V122 `parens_slashes_anywhere` 655 → 566 (SOFT), −89.** Same cause: the
  standard tier's copies of those characters are gone.
- **V133 `dash_in_S_standard_FORM` 1 → 0 (SOFT).** Pass 1's single finding was
  on `Kangkang.xml` S17. With no standard FORM anywhere, the rule has nothing
  to fire on. This is the "standard-tier rules simply go quiet" category.
- **V141 `W_reconstructs_S` 1, V144 `M_less_W_in_segmented_file` 428,
  V060/V061/V068 (4/16/2)** — all unchanged; they read the original tier.
- **V147** (legacy PHON tildes), the sweep's target metric, is 0 in all three
  states — the corpus has never had a PHON tier.

### 6.1 CORRECTION to pass 1, and one item to ESCALATE

**V063 `W_FORM_retains_segmentation` is 91 HARD on `main` and 91 HARD now.**
Pass 1 reported 91 → 0 as its headline win and as the fix for issue #80's
item 1. That improvement **does not survive**, and the honest reading is that
it was never as solid as it looked:

- All 91 findings on `main`, and all 91 now, are the **standard-tier branch**
  of the rule (`W FORM[@kindOf='standard'] retains 0 segmentation markers but
  S-level FORM has N`). The `original` branch has never fired — the original
  tier's hyphens were never in question.
- Pass 1 zeroed them by *creating* a standard tier that copied the original's
  hyphens. Removing the tier restores the count, at the same severity.

But the two 91s are not the same finding. On `main` the tier existed and had
been stripped of hyphens — a real defect. Now the tier does not exist, and the
rule computes `standard_sum = 0` from an empty set and compares it against a
threshold anyway (`QC/validation/rules/gloss.py:250–320`). **A corpus with no
standard tier cannot pass V063.**

That is a rule bug, and it contradicts V014's stated design in the same
codebase ("some corpora legitimately lack a standard tier"). The guard is one
condition — skip the standard-tier comparison when no W carries a standard
FORM — but it is a shared validator affecting every corpus, so **it was not
patched here**: silencing a HARD rule to make this branch look clean is
precisely the papering-over the ruling forbids.

**ESCALATED to the maintainer**, with two consequences to weigh:
1. This corpus now carries 91 HARD `validate_glosses` findings that are
   false positives. `.github/workflows/xml-validation.yaml` runs
   `validate_glosses` with baseline/candidate comparison; net-new HARD
   findings against the `main` baseline are **zero** (91 → 91), so CI should
   not newly fail — but the corpus is permanently red on this rule.
2. Any future corpus that legitimately declines a standard tier will hit the
   same wall.

## 7. Issue #80 — claim-by-claim disposition

Each claim was re-verified against the current tree; none was taken on trust.

| # | claim | verified? | disposition |
|---|---|---|---|
| 1 | 91 V063 segmentation-preservation findings, all 6 files | **yes** | **NOT FIXED — REOPENED as a rule bug.** 91 before, 91 after; see §6.1. The underlying data concern (was segmentation lost?) is **moot**: the original tier's hyphens are intact and always were, and the tier that had lost them no longer exists. |
| 2 | missing `Orthographies/Wakelin/Yami.tsv` source profile; "resolve source orthography before derived-tier regeneration" | **yes** | **CLOSED** — the orthography is not resolvable from available evidence, so no derived tier is generated at all, and the table has been **deleted** (§2.1). |
| 3 | 56 V121 parens/slashes in W/M FORMs, 5 files | **yes** (56, now 28) | **NOT A DEFECT — REPORTED.** Both notations are the article's own. `( )` is defined in the article's key as "in data, probable discrepancy" (`(n)aku`, `ku(a)`, `puken-(en)`) — not POL-026 optional material, so the "split into two S blocks" remedy does not apply. `/` marks alternative forms the article itself offers (`am/namen`, `varit/yaked`). POL-027 applies to the slashes, but splitting them needs glosses and a word tier per option — linguistic judgement. The count halved only because the duplicate standard-tier findings went away. |
| 4 | "Kalaku1 S1 has 6 S-level markers while W-standard retains 0" | **yes** | **MOOT** — there is no W-standard FORM to compare. The W *original* reads `anu-i-k-angay-namen`, hyphens intact, as it always did. |
| 5 | 6 V144 findings / W without M children | **partly** — the count is **428** M-less W (6 *files*), matching the baselines doc, not 6 findings | **OUT OF SCOPE by instruction** — no M elements added. Noted in the README caveats. |
| 6 | 1 V141 likely S/W misalignment, S20 | **yes** (`Kalaku1` S20) | **REPORTED** — the sentence is a bare three-way `/` alternation `pipangn-epen/pipangungn-epen/pipangengne-eben`; the W tier segments one alternative, so it reconstructs 28% of the sentence. Needs POL-027 splitting. |
| 7 | 16 V061 morpheme-count + 2 V068 reconstruction findings | **yes** (16 and 2) | **REPORTED** — see §8. |
| 8 | one within-file duplicate group in `Kwaway.xml`, S36/S40 | **yes** — both are `chichyarana mukipung` | **NOT A DEFECT.** The article prints the same line at 36, 40 *and* 45. Narrative corpus, no dedup step declared → SOFT per POL-022, correctly kept. |
| 9 | "repair segmentation … and lower-tier alternatives" | **yes, and quantified** | **REPORTED, not fixed** — see §8. |

## 8. Verified findings referred to the maintainer (not fixed here)

All are original-tier or morpheme-tier content questions requiring a committed
fix script and a linguistic call, so none was touched (POL-038).

1. **Lower-tier alternatives are dropped in 11 sentences.** Of 17 sentences
   whose S FORM carries a source `/` alternation, **11** have a word tier that
   contains no `/` at all: `Kalaku1` S6/S13/S16/S20, `Kalaku3` S8, `Kalaku4`
   S2, `Kwaway` S2/S4/S9/S39/S48. Issue #80's "lower-tier alternatives" claim
   is real and this is its size.
2. **`Kalaku1` S13W1 is truncated.** Source line C13 is `katu-nem/namen-rana
   nukaden a-m-angay tu di-taytu`; the W FORM is just `katu`, while its three M
   children are `katu`, `nem`, `rana` — i.e. the word lost `-nem/namen-rana`
   but kept its morphemes. This is the V068 36%-reconstruction finding and one
   of the V061 findings; it is a genuine transcription defect, not a
   segmentation opinion.
3. **`Kwaway` S4W2M2 kept a pre-errata spelling.** M FORM is `agep` where the
   parent W is `tunanal-aep-an`. The article's *Errata Addenda* B4 corrects
   `tunanal-a~ep-an` → `tunanal-aep-an`; the correction was applied at the word
   tier but not at the morpheme tier.
4. **`Kalaku4` S16W4M1 is a typo:** `cbyaa?` under a W FORM of `chyaa?`
   (`b`/`h` slip). Together with 2 and 3 these are the only four morphemes in
   the corpus whose letters do not occur in their parent word.
5. **`Kalaku4` S2 has unbalanced parentheses at word level** — `(imurud`,
   `tau)`, `(tau`, `d-imurud)`. In the article the "probable discrepancy"
   parentheses span several words; the word tier splits them. Faithful but
   awkward; a `notes` attribute may be the better home.
6. **`Kalaku4.xml` is misattributed.** It is text **F**, given by **Saman
   Sunagu** (January 1957), not by Saman Kalaku; its `source` attribute reads
   `"Yami text. Kalaku"`. The file name and `TEXT/@id` must stay (POL-037), but
   the `source` attribute is wrong and could be corrected by script. The
   correct text↔informant mapping for all six files is now documented in the
   README table.
7. **What `?` writes.** §2.2. The corpus does not depend on the answer, but it
   is the one finding that could unlock a real orthography profile — and with
   it, eventually, a standard tier and a PHON tier.
8. **V063's standard-tier branch fires on an absent tier.** §6.1. A shared
   validator change, deliberately left to the maintainer.

## 9. README

Rewritten in pass 1 (it was previously a 27-line fragment with no title, no
contents section, no pipeline, and a note pointing at the discredited
conversion table) and revised again here. It now carries:

- **A prominent up-front notice for data users**: this corpus has an
  `original` tier and nothing else — no standard tier, no IPA, at any level —
  because the orthography is unidentified and no trustworthy conversion
  exists.
- A dedicated **"Why there is no standard tier and no IPA"** section: what a
  standard FORM and a PHON each *claim*; the deleted conversion table and what
  it actually contained; the `add_phonology` probe with its concrete outputs;
  and what would have to change for either tier to become possible.
- The `?`-as-letter finding kept prominent, with the count (47), its
  distribution across tiers, the example sentence, and an explicit statement
  that the glottal-stop reading is **not confirmed**.
- The corpus description with the six texts mapped to their article sections,
  informants and dates; the two source notations (`( )` "probable
  discrepancy", `/` alternatives) that data users would otherwise misread as
  conversion noise; the article's symbol key; the known caveats.
- **Full reproduction documentation, not trimmed**: provenance and the
  snapshot's role; the single `make_xml.sh` entry point with its arguments and
  environment overrides; step 0 (restore) and both pipeline steps written out
  as runnable commands with what each does and the counts it produces; why
  `standardize.py` and `add_phonology.py` are absent; and the sidecar policy.
  `XML/` is reproducible from committed inputs by one command.

Per the README content policy it carries no sweep narrative and no rule
numbers.

## 10. Closing steps not done here

- GitBook corpus-page update (per-corpus procedure step 9) — deferred to
  post-merge with the other closing steps. Note the page will need the
  no-standard-tier statement.
- No push, no merge; one amended commit on `work/b3-wakelin`.

**UNEXPLAINED items: none.**

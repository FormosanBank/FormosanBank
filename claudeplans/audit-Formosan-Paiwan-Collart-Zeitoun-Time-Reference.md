# Dev-repo audit — Formosan-Paiwan-Collart-Zeitoun-Time-Reference

**Audit date:** 2026-08-02
**Auditor:** Claude (audit-dev-repo skill), with maintainer sign-off on each judgment call
**Dev repo:** `../Formosan-Paiwan-Collart-Zeitoun-Time-Reference/`
**Corpus:** Collart & Zeitoun (2024), "Past and future time reference processing teased apart in Paiwan, an endangered Formosan language" (*Language and Cognition* 16(3):574–599, doi:10.1017/langcog.2023.49)
**XML audited:** `Final_XML/Paiwan/collart_zeitoun_2024_paiwan_time_reference.xml` (304 `<S>`, 304 standard FORM, 304 PHON, 303 AUDIO; `xml:lang="pwn"`, `dialect="unknown"`, `glottocode="paiw1248"`)

---

## TL;DR

- **DO NOT PORT.** This is a hard blocker and it is **not** a data-quality problem. The corpus is derived from OSF node `q35sz` (experimental workbook + audio), which exposes **no license metadata** (`node_license: null`, checked 2026-07-22 and 2026-07-27), and there is **no recorded publication approval**. The article's CC BY 4.0 covers the paper, not the separately-hosted data.
- **Preprocessing fidelity is excellent.** On all four highlighted concerns (a dropped chars, b suppressed punctuation, c convention breaks, d extraction artifacts) the corpus is clean. Our current validators produce **zero HARD findings**; the original tier is character-for-character faithful to the source workbook.
- **Two source-overrides required human judgment:**
  1. **Item-160 lexical/translation correction** — reviewed and **ACCEPTED** (well-evidenced).
  2. **Audio-condition remapping (33 records)** — **OPEN ITEM**: rests on an unverified assumption; must be checked before any future port.

---

## 1. What the assistant did (preprocessing summary)

Single build script `CodeAndDocs/build_xml.py` reads the OSF workbook `Private/source/osf/PaiwanPsycho_Materials.xlsx` (Sheet1, 608 stimulus rows) and a cached OSF audio inventory, and emits the XML plus audit artifacts (`extracted_stimuli.tsv`, `audio_manifest.tsv`, `extraction_summary.md`). PHON is added downstream by the pinned public-FormosanBank reference pipeline.

Transformations applied to the data:

| Step | Transformation | Notes |
|---|---|---|
| Whitespace | `clean_space` collapses whitespace runs / NBSP → single space, strips ends | Applied to all fields |
| **Original tier** (`normalize_paiwan_original`) | Workbook Paiwan preserved **exactly** — infix `<em>`, clitic `=`, hyphen `-` all retained | Faithfulness anchor |
| **Standard tier** (`standardize_paiwan`) | Strips `<…>` brackets (keeps inner text), removes `=` and `-`; applies item-160 `ajlak`→`aljak` | Not a TSV transliteration — desegmentation + one lexical fix |
| **Exclusions** | 304 intentionally ungrammatical experimental stimuli (Past-`uri=`, Fut-`na=`) dropped from XML, retained in audit TSV with `exclusion_reason` | Inclusion rule independently confirmed against article Table 3 (pp. 583–584) |
| **Audio remap** | Audio re-resolved by `(item, surface_condition)` where surface_condition is derived from the visible sentence text; 33 emitted records received corrected AUDIO file/duration/id | See §4 — OPEN ITEM |
| **Item-160 correction** | standard FORM `ajlak`→`aljak`; Chinese `狗`→`小孩`, `other`→`醫生`; original tier keeps `ajlak` | See §4 — ACCEPTED |
| Metadata | `dialect="unknown"` (article never names village/dialect); generic Paiwan glottocode | Honest, source-backed |

## 2. Mapping to our pipeline

| Assistant step | Our pipeline equivalent | Verdict |
|---|---|---|
| Standard-tier desegmentation (`< > = -` removal) | `clean_xml.py` C012 hyphen rule + standardize | ✅ Matches convention (Paiwan does not list `-` as a letter) |
| Original tier kept faithful | Our `original` tier convention | ✅ Correct |
| PHON generation | `add_phonology.py` via `Orthographies/Ortho113/` | ✅ Uses our pinned pipeline |
| No W/M segmentation invented | n/a (unsegmented corpus) | ✅ Correct — workbook has no token-aligned glosses |
| Ungrammatical exclusion | Concern (d) convention (`*`/ungrammatical excluded) | ✅ Correct (condition-based rather than `*`-based) |
| Standardization as transliteration | `standardize.py --tsv` | ⚠️ Not done — standard tier is desegmented-original, not transliterated into common orthography. Acceptable given `dialect="unknown"` has no reference orthography to map to. |

## 3. Findings by concern (our current validators + source diff)

Validators run 2026-08-02 from `FormosanBank` `.venv` against `Final_XML/`. Findings CSVs in `/tmp/cz_audit/` (transient).

- `validate_xml`: **0 findings** (schema, ids, kindOf, ver, dialect all pass).
- `validate_text`: **0 HARD**, 618 SOFT — V134 angle brackets (532) all in **original** Paiwan FORM; V122 parens/slashes (86) all in **Chinese TRANSL**. Both are source-faithful notation.
- `validate_glosses`: **0 HARD**, V060 SOFT (304) — no W/M analysis (correct; not invented).
- `validate_orthography`: skipped — no `QC/validation/reference/Paiwan/unknown` folder (consequence of the honest `dialect="unknown"` label, not a bug).

**(a) Dropped orthography characters — CLEAN.** Original-tier character inventory is *identical* to the source workbook (0 dropped, 0 added). Letters are a plain-ASCII Paiwan set (`a b c d e g i j k l m n p q r s t u v w y z`); no apostrophes, diacritics, or glottal-stop letters, so none of the curly-apostrophe / `ŋ`/`ə`/`ɬ` loss hazards apply. Standard tier removes only `< > = -`, adds nothing.

**(b) Suppressed punctuation — CLEAN.** Original tier preserves all source punctuation (only `.` plus segmentation markers present). Standard tier strips only segmentation, per C012. Verified: **0** standard FORMs contain `< > = -`; 264 original FORMs correctly retain `<`.

**(c) Convention breaks — CLEAN.** Schema passes. `kindOf ∈ {original, standard}`. `dialect="unknown"` accepted by validator and source-backed. Segmentation confined to original tier.

**(d) Extraction artifacts — CLEAN.** 0 sentence-initial `*`, 0 stray digits, no out-of-language runs in the original tier. 304 ungrammatical stimuli excluded by experimental condition, retained in audit TSV.

**Source diff (faithfulness anchor):** all 304 XML original FORMs match a workbook Paiwan string verbatim after whitespace normalization (0 mismatches). The dev repo's own `audit_source_alignment.py` corroborates (line-by-line workbook↔TSV comparison: 0 errors; 528/528 infix rows preserved; 608→0 clitic-equals original→standard; 140/140 and 16/16 Chinese `/` and `()` preserved).

## 4. Source-overrides requiring judgment

### 4a. Item-160 lexical + translation correction — ACCEPTED (maintainer, 2026-08-02)

Workbook item 160 is internally contradictory: Paiwan `ajlak` with Chinese `other…狗` (dog). The build keeps workbook `ajlak` in the **original** tier but corrects the **standard** tier to `aljak` and the Chinese to `醫生…小孩` (doctor…child). Evidence (`item160_source_correction.md`):
- All four item-160 recordings match OSF SHA-256 hashes, and MFCC/DTW (final 1.25 s) favor `aljak` over `vatu` by margin 1.739–2.253.
- Three independent ILRDF Paiwan lexical lists: `kuisang`=醫生(doctor), `aljak`=小孩(child), `vatu`=狗(dog).

Maintainer reviewed and accepted. Recorded here as reviewed-and-accepted.

### 4b. Audio-condition remapping — OPEN ITEM (maintainer, 2026-08-02)

**What it is.** The workbook is internally inconsistent: for 64–66 rows, a row's own `Condition` label and/or its `Audio_Files` filename disagree with the condition legible from the **visible Paiwan sentence** (time adverb `katiaw`=Past / `nutiaw`=Fut, marker `na=` / `uri=`). Example — sheet row 2 (item 1): sentence `katiaw na=k<em>an…` = Past-Na, but `Condition`=Fut-Na and `Audio_Files`=`001_FutNa.mp3`. The build treats the **sentence text as authoritative**, derives the surface condition, and re-links audio to `(item, surface_condition)` — for row 2, `List D/001_PastNa.mp3`. This remapped audio on **33** emitted grammatical records (reconciled precisely: 33 filename-driven remaps + 1 label-only mismatch = 34 emitted conflict rows; full list exported to `/tmp/cz_audit/workbook_condition_conflicts.csv` with 1-based sheet-row numbers).

**Why it is open.** The remap trusts the **condition encoded in the audio filename** as the key for fetching the correct clip — but **no documentation shows anyone verified the audio filenames are named correctly** (i.e. that `001_PastNa.mp3` actually *contains* a Past-Na utterance). Audit trail:
- SHA-256 checks → **file integrity only**, not content.
- MFCC/DTW audit → **item 160 only, and only a lexical question** (`aljak` vs `vatu`); says nothing about condition-naming.
- `validate_audio.py` → existence/loadability/silence/duration, not content-vs-condition.
- `audit_source_alignment.py:633` "manifest mismatches: 0" → **circular**: the manifest was resolved *by* filename condition, so this checks the build's bookkeeping, not reality.

Because the remap's whole justification is that this very source is unreliable about condition pairing, using another field from the same source (the filename's condition string) as the trusted key is not self-evidently safe. It is a reasonable heuristic (the sentence text is legible and probably ground truth), but the audio leg was never checked by ear or by ASR.

**Required before any future port:** a Paiwan listener or a forced-alignment / ASR pass over at least the 33 remapped clips (ideally plus a control sample of non-remapped clips) to confirm each clip's audible condition (leading `katiaw`/`nutiaw` + `na=`/`uri=`) matches its filename. The condition is audible, so this is verifiable in principle.

## 5. Minor / informational

- **Missing audio:** `List D/012_PastNa.mp3` is workbook-referenced but absent from the 640-file OSF inventory; its record (`S0040_item012_listD_012_PastNa`) correctly has no `<AUDIO>` (303 AUDIO for 304 records).
- **Doc inconsistency (non-blocking):** the pinned public-FormosanBank reference commit differs between docs — README + `qc_status.json` say `4f5fa364…`, `reproducibility.md` says `da88673d…`. Reconcile before relying on the reproduce script.
- Reproduction is deterministic (byte-identical Final_XML across two passes; independent-clone verification recorded in `qc_status.json`).

## 6. Recommendation

1. **Do not port** into `Corpora/` until BOTH:
   - (rights) OSF `q35sz` materials gain a redistributable license **or** the authors grant documented permission, AND an explicit publication approval is recorded; and
   - (open item 4b) the audio-condition remapping is verified by a Paiwan listener or ASR/forced-alignment over the 33 remapped clips.
2. If/when ported: standardization is currently desegmentation-only; decide whether a true common-orthography transliteration is wanted (blocked today by `dialect="unknown"` → no reference orthography). Fix the reference-commit doc inconsistency.
3. Item-160 correction (4a) needs no further action — reviewed and accepted.

*This audit did not modify the dev repo or `Corpora/`. Validator output was written to a transient `/tmp/cz_audit/` and is not committed.*

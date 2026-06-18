# NTU Paiwan — update, QC, and port plan

**Date:** 2026-06-12 · **Status:** plan drafted; awaiting maintainer go-ahead + one external dependency (NTU).
**Dev repo:** `../Formosan-NTU_Paiwan/` (PRIVATE — holds the real-name key; to be archived after port).
**Repo of record (target):** `FormosanBank/Corpora/NTU_Paiwan_ASR/` (PUBLIC — pseudonyms only).
**Driver:** `audit-dev-repo` skill, expanded into a full bring-up-to-date + port effort per maintainer.

> Privacy rule for this document and everything under `FormosanBank/`: **no real participant
> names**. The verified real-name↔pseudonym key lives only in the private dev repo.

## Goals (maintainer)
1. Update `Final_XML` so it contains **all** current data (Y1 + Y2 + the 1-min "perfect" transcriptions).
2. Get **all** audio (old Y1 + new Y2) onto HuggingFace (one or more datasets; mind HF file-count limits).
3. Run the **current** QC pipeline over everything (old and new) to meet current standards.
4. Port the final result into `Corpora/NTU_Paiwan_ASR` (pseudonyms only) as the repo of record; archive the dev repo (private key stays there).

## Verified current state (2026-06-12)

| Area | Finding |
|---|---|
| **Y1 published == dev** | `Corpora/NTU_Paiwan_ASR` and `Formosan-NTU_Paiwan/Final_XML/Paiwan` both = 98 XMLs, 6 pseudonyms (Belmira 8, Falin 5, Loris 19, Nira 29, Sarnix 8, Zendar 29). Full structure (orig+std FORM, PHON, AUDIO, dialect, citation). Built with the **old** QC pipeline. |
| **Y1 dialects** | Belmira=Central, Falin=Eastern, Loris=Eastern, Nira=Northern, Sarnix=Eastern, Zendar=Northern — consistent with the recording-code dialect letter (C/E/N). No error. |
| **Y1 name key** | VERIFIED 6/6 from EAF `MEDIA_URL` embedded original filenames (+ Y1 spreadsheet). Stored privately. EAF paths also leak researcher usernames / folder names → never port the raw eaf; the XML does not carry them. |
| **Y2 regular** (`NTU_NewDownload/NTU_Y2/`) | 10 subjects `se01…wuh01`, 88 recordings, ~52 `.eaf` transcribed (7 subjects) + audio-only for 3 subjects (`ma01,pulj01,tji01`); ~1800 annotations total. Same ELAN structure as Y1; transcription tier renamed `default`→`Transcription`. Coverage ragged → mixed transcribed/untranscribed audio. |
| **"1-min perfect" transcriptions** | Y1: 16 eaf / 5 speakers; Y2: ~42 eaf / 10 subjects. **Independent audio** (e.g. `frog_ge01.wav`), NOT re-transcriptions of the regular recordings → new material. For Y2 `ma01,pulj01,tji01` the perfect set is the **only** transcription. |
| **Dialects vocab** | `dialects.csv` Paiwan = Northern/Central/Eastern/Southern (all valid). Y2 introduces **Southern**. |
| **Language code** | `pwn`. |
| **Audio infra in dev repo** | NONE — no `download_audio_data.sh`, no upload code. Reusable uploader exists: `FormosanBank/QC/utilities/upload_to_hf.py` (+ `.hf_dataset.yaml`). |
| **HF (Y1)** | Published `download_audio_data.sh` dynamically pulls any `FormosanBank/NTU_Paiwan_ASR_*` dataset. **Live split unknown without network** — must check. Y1 ≈ 1535 clips + 98 full recordings. Y2 ≈ ~1800 clips + 49 raw. |
| **Hunter's work** (`Formosan-NTU`) | Wrong repo; 202 minimal FORM-only XMLs (no kindOf/standard/PHON, bad dialect labels, mismapped speakers). **Discard.** Keep only the lesson: source eaf have tier-name typos (`Trancription`, `Transcrption`) and fragile audio resolution. |

## `Temp/` (gitignored, private) — Y1 originals by real name
Added by maintainer 2026-06-12; original NTU data in 4 messy download chunks (`NTU_Y1`, `NTU_Y1 2/3/4`).
- Contents: **Y1 only**, organized by the 6 real names (= the 6 pseudonyms). 114 `.wav` + 98 `.eaf` + 98 `.TextGrid` (the eaf/TextGrid all in chunk "NTU_Y1 2"), incl. perfect-transcription wavs.
- Value: (1) independently **confirms the Y1 real-name↔pseudonym key**; (2) **supplies the Y1 source audio** that `Data/` lacked for 5/6 speakers.
- Does **not** contain Y2 → does **not** resolve Y2↔Y1 continuity. (No Y2 subject codes present.)

## ~~The blocker~~ RESOLVED: Y1 and Y2 are distinct individuals
Originally feared we'd need a Y2→Y1 *same-person-same-pseudonym* mapping. The spreadsheets
(`…NTU_Y2/NTU_BC recording details 2024 Y1*.xlsx` and `…2025 Y2*.xlsx`) settle it: **treat Y2 as
new people.** Evidence:
- **Combined roster is exactly additive:** Y1 6 + Y2 10 = 16 speakers, M 3+5=8 / F 3+5=8,
  Nor 2+4=6 / Sou 0+2=2 / Cen 1+1=2 / Eas 3+3=6. No dedup ⇒ NTU counts 16 distinct individuals.
- **Injective Y1↔Y2 match is impossible:** Y2 has 2 Eastern males (ku01, tja01) vs 1 in Y1 (udjuy);
  2 Northern females (se01, il01) vs 1 (Dremedreman); **Southern** (ma01, yed01) has no Y1 counterpart.
- **Shared codes are prompt IDs, not identity:** ku01 (Eastern *male*) recorded `02SE111-1`/`02SE112-1`,
  which in Y1 only Gesi (Eastern *female*) recorded → code reuse ≠ returning speaker.

**Decision:** assign Y2 its own 10 fresh Belmira-style pseudonyms; no cross-year continuity. If NTU
later confirms a specific returner, alias that pseudonym then (cheap), rather than risk merging two
different people now. The verified **Y1** real-name↔pseudonym key (6/6) still lives privately in the dev repo.

### Verified rosters (real names kept in the private dev-repo key only)
- **Y1 (6):** Gesi=Eastern/F, Dremedreman=Northern/F, Ljalja'u=Northern/M, Milingan=Central/M,
  udjuy=Eastern/M, sawniyaw=Eastern/F → pseudonyms Loris/Zendar/Nira/Belmira/Falin/Sarnix respectively.
  (All dialects now reconcile with the published Y1 corpus.)
- **Y2 (10):** se01=Nor/F, ma01=Sou/F, ve01=Nor/M, tji01=Cen/M, ku01=Eas/M, tja01=Eas/M, il01=Nor/F,
  pulj01=Nor/M, yed01=Sou/F, wuh01=Eas/F. (`se01`-style codes are already NTU's anonymization → safe to
  carry as internal keys; assign friendly pseudonyms for publication.)

## Phased plan

### Phase 0 — Dev-repo hygiene + lock the private key  *(unblocked)*
- Record the verified Y1 real-name↔pseudonym map as a private `CodeAndDocs/speaker_key.csv` (stays in dev repo only).
- Reorganize scripts into `CodeAndDocs/` (convention); keep `Data/`, `NTU_NewDownload/`, spreadsheets private.
- Note the `_untranscribed`/partial-audio conventions to follow (Tang/Whitehorn = fully-untranscribed `TEXT`+`AUDIO` no `S`; WilangYutas = partial → `{id}.xml` + `{id}_untranscribed.xml`).

### Phase 1 — Speaker pseudonyms  *(unblocked)*
- Y1: reuse existing 6 pseudonyms (verified key). Y2: assign 10 fresh Belmira-style pseudonyms
  (a simple `se01→Pseudonym` table; the `se01…` codes are NTU's own anonymization, fine as internal keys).
- No cross-year continuity (Y1/Y2 distinct — see above).

### Y1 gap (found 2026-06-12): the 16 untranscribed spontaneous recordings have NO XML
The published Y1 corpus = 98 read-speech XMLs only. The Y1 spreadsheet's "Untranscribed spontaneous
speech" sheet lists **16** spontaneous recordings (frog/pear/my father/my life/my mother/Our cattle/
White owl/drungdrung/hunting-god/when-I-was-7, per speaker; Milingan=0) that are **absent** from the
corpus. Audio exists in `Temp/` (under real-name folders; mixed `_ge01`/`_<name>` naming). These are
**partial**: e.g. `frog_ge01.wav` is 457s but only 69–131s is transcribed (interior window) by the
"1-min perfect transcription". So Phase 2 must add them as transcribed-window `S` + untranscribed
remainder (before AND after the window). Same shape applies to the Y2 topic recordings.

### Y2 data inventory & AUDIO GAP (found 2026-06-12)
NTU_Y2 coverage is ragged and the **audio is substantially incomplete** (eaf `MEDIA_URL`s point at the
transcriber's `C:/Users/…/Downloads/`, so audio was not all delivered):
- **Transcriptions present:** read-speech eaf for 7 subjects (il01 5, ku01 4, se01 3, tja01 6, ve01 3,
  wuh01 10, yed01 15 = 46) + 42 "1-min perfect" eaf. (ma01/pulj01/tji01 have **no** read-speech eaf.)
- **Audio present:** 49 wav total (all under NTU_Y2/ + perfect folders); nowhere else in the repo.
- **Gaps:** **24** transcribed read-speech recordings have **no audio** (wuh01 all 10, il01 all 5, yed01 7,
  ku01 2); **15** of the 42 perfect transcriptions have **no source audio**; 27 topic recordings have audio
  but only a 1-min transcription (fine → partial).
- **Implication:** XML can be built now (transcription-driven, referencing audio filenames like the
  published Y1 corpus does), but Goal 2 ("all audio to HF") **cannot be fully met** without ~24+ more Y2
  audio files from NTU (a Temp-like drop for Y2). Decision pending with maintainer.

### Phase 2 — Build Y2 + perfect-transcription XML in the dev repo  *(mostly unblocked)*
- Extend/replace the ELAN→XML converter to handle: Y2 regular eaf, Y1+Y2 perfect eaf, tier-name variants, **partial** transcription (transcribed `S` + `_untranscribed.xml` remainder), and **fully-untranscribed** audio-only subjects (boring `TEXT`+`AUDIO`).
- Apply pseudonyms (Y1 verified now; Y2 via `y2_speaker_map` once known). Dialect from spreadsheet/code. `xml:lang="pwn"`, citation/BibTeX/copyright per Y1.
- Keep faithful: strip only newlines/NBSP + collapse whitespace (match Y1 `main.py`); preserve all orthography chars and punctuation in the original tier.

### Phase 2 — DONE (XML build) 2026-06-12
Converter: `CodeAndDocs/build_y2_and_spontaneous.py` → staging dir `new_xml/Paiwan/<Pseudonym>/`.
- **162 new XMLs**, schema-valid (`validate_xml`: 0 HARD; only SOFT V014 missing-standard-tier, added in Phase 3).
  - Y2 read-speech: 46 transcribed. Y1 spontaneous: 16→32 (window + `_untranscribed`). Y2 spontaneous: 42→84.
- Verified: glottal-stop apostrophe `’` preserved; **full pseudonymisation** (0 real-name/code in any id/source/audio
  attribute; "milingan" hits are the Paiwan vocabulary word in FORM text, not metadata); orphan-audio check = **0**
  truly-untranscribed Y2 wavs (all 49 covered). Y1 audio fully accounted (98 read + 16 spontaneous = 114 in Temp).
- Existing 98 Y1 read-speech XMLs are left untouched (just need re-QC).
- **Open nuance:** the `_untranscribed.xml` companion points at the FULL recording (the transcribed 1-min window
  sits inside it). Acceptable per the two-file model; could later clip the untranscribed remainder when audio is present.
- **Missing source audio** (39 Y2 wavs) listed in `CodeAndDocs/missing_audio.txt` for the maintainer to fetch.

### Phase 3 — DONE (QC on new XML) 2026-06-12
Ran clean_xml → standardize --copy → add_phonology (Ortho113) → validators on `new_xml` (162 files):
- **validate_xml: 0 issues. validate_text: 0 issues.** Apostrophe `’`→`'` normalised; glottal stop → IPA `ʔ`.
- **Orthography vs reference/Paiwan:** Overlap Coefficient 1.00 (no Paiwan letters dropped — concern (a) clean),
  cosine 1.00. The CJK chars in the validator output are in the *reference*, not ours; our FORM text has
  **zero** non-standard characters (direct audit). PHON `*` = 2 = the English names "Mary/Paul/**John**" the
  speaker recites (faithful; FORM keeps "John", only its IPA stars the J). Published Y1 had 28 such.
- Two converter bugs found & fixed: (1) `yed01` read files `02 yed NN` lost the recording number → split the
  regex; (2) numbering-tier digits (`001`) leaked as FORMs (tiers are inconsistently named — some files put
  transcription on `default`, others on `default-cp`) → now take any time-aligned annotation with ≥1 letter.
- **Re-QC of published Y1 (98):** validate_xml 0 HARD; validate_text **19 files with SOFT issues only**
  (V116 non-ASCII ×20, V122 parens/slashes ×22, V133 dash-in-standard ×15, V136 mixed-script ×14) — pre-existing
  old-pipeline review items, not gates. **Port decision:** re-run current clean_xml on Y1 to clear V133 (and
  some V116/V136), accepting minor churn, vs leave as-is.
- **Audio after Temp/MissingWavs drop:** 27/39 recovered; **12 still missing** (see `CodeAndDocs/missing_audio.txt`):
  yed01 ×8 (02 yed 10/12/13/14/15, Learning languages, hand tattoos, naming, self-introduction), il01 ×2
  (frog, local daycare…), wuh01 ×1 (labor exchage). Temp is untracked → audio needs a tracked home (Phase 4).

### Phase 3b (if needed) — re-run current QC pipeline on Y1
- `clean_xml` → `standardize --copy` → `add_phonology` (Ortho113) → validators: `validate_xml`, `validate_text`, `validate_dialect`, `orthography_extract --kindOf original`+`validate_orthography` vs `reference/Paiwan`. Re-QC Y1 too (built on old pipeline).
- Triage findings by the four audit concerns (dropped chars / suppressed punct / convention breaks / extraction artifacts). Record in this doc.

### Phase 3b — DONE: Y1 re-clean + full assembly 2026-06-12
- **Y1 re-clean** (approved): current `clean_xml` on the canonical Corpora Y1 → 19→8 files-with-issues;
  cleared V133 (dash-in-standard ×15) and V136 (mixed-script ×14), halved V116 (20→11). 13 Y1 files changed
  (mostly stray backtick → apostrophe); PHON refreshed for those 13 only.
- **Assembled corpus** = canonical Corpora Y1 (98, re-cleaned) + 162 new = **260 XMLs** at
  `Formosan-NTU_Paiwan/Final_XML_assembled/Paiwan/`. validate_text: 8 SOFT-only (legit Y1 parens/non-ASCII).
  validate_xml: 98 HARD **V081 only**, which is a staging artifact (the copied Y1 ids collide with their own
  published versions; 0 involve new Y2 pseudonyms) — resolves on port since it *replaces* the published Y1.
- New material adds **22,955 Paiwan tokens**. Dialects: Central 8 / Eastern 66 / Northern 57 / Southern 31.
- Canonical Y1 source = Corpora (dev `Final_XML` was 3 Zendar files stale — missing AUDIO @file clip refs).

### Phase 4 — Audio → HuggingFace
- Check live `FormosanBank/NTU_Paiwan_ASR_*` state (don't re-upload Y1).
- Extract Y2 sentence clips (reuse `extract_audio_clips.py`); generate `_untranscribed.wav` remainders per WilangYutas.
- Recommend + create the HF split (likely by year/dialect, ≲~1700 files/repo); upload via `upload_to_hf.py` + `.hf_dataset.yaml`; write `download_audio_data.sh` for the corpus.

### Phase 4 — DONE (audio prep) 2026-06-12
All Y2 audio recovered (0 missing after the maintainer's Drive downloads). Scripts: `CodeAndDocs/stage_audio.py`.
- **Staged 202 full recordings** under pseudonymised names → `Audio/Paiwan/<Pseudonym>/`, matching every TEXT
  `@audio` (coverage check: 0 missing, 0 extra). HF stores **full recordings only**; per-sentence clips are
  generated client-side by `extract_audio_clips.py` (validated end-to-end: 3112 clips, 0 failures).
- **Upload package** `hf_upload_new/` (Audio/ + `.hf_dataset.yaml` → `FormosanBank/NTU_Paiwan_ASR_Y2`): the
  **104 NEW** recordings (16 Y1 spontaneous + 88 Y2), 5.3 GB; the 98 Y1 read-speech are already on HF.
  File count is tiny → no split needed; one new dataset suffices. The published `download_audio_data.sh` globs
  `NTU_Paiwan_ASR_*` so it auto-discovers the new dataset; no script change needed.
- **Maintainer action (needs HF auth):** `hf auth login` then
  `python QC/utilities/upload_to_hf.py --path Formosan-NTU_Paiwan/hf_upload_new --yes`. Verify against existing
  `NTU_Paiwan_ASR_*` datasets. (Audio dirs are gitignored; HF is the tracked home for the bytes.)
- **dev `Final_XML` updated** to the full 260-XML corpus (goal #1).

### Phase 5 — Port to `Corpora/NTU_Paiwan_ASR` (repo of record)
- Standard layout: `README.md`, `CodeAndDocs/` (repro scripts, **no real names**), `XML/Paiwan/`, `download_audio_data.sh`.
- Scrub any real-name traces; verify pseudonyms only. Refresh `get_corpus_stats`. Citation/BibTeX.
- Archive/retire the dev repo (private key retained there).

### Phase 5 — DONE (port) 2026-06-12  *(working tree only — not committed/pushed)*
- **XML:** `Corpora/NTU_Paiwan_ASR/XML/Paiwan` replaced with the assembled 260. validate_xml **0 issues**
  (V081 self-collision gone, as predicted), validate_text 8 SOFT-only.
- **README:** rewritten for the published corpus (Y1+Y2, read vs spontaneous, two-file untranscribed
  convention, 4 dialects incl. Southern, audio-on-HF, privacy note, private-reproduction note).
- **CodeAndDocs:** initially Y1 scripts only; then (on maintainer request for reproducibility) the build
  scripts were **refactored to be name-free** — the real-name→pseudonym filename patterns moved into the
  private `speaker_key.csv` (new `filename_regex` column), which the script loads at runtime. The name-free
  `build_y2_and_spontaneous.py` + `stage_audio.py` are now **published** in `CodeAndDocs/`; `speaker_key.csv`
  and `missing_audio.txt` stay **private**. Refactor verified identical output (162 files). Running the
  published scripts requires the private key + private ELAN/audio sources (documented in the README).
- **Privacy sweep:** clean — no real name / NTU code / source path in any identifying attribute; the only
  hits are the Paiwan vocab word "milingan" in FORM text and the word "Downloads" in the audio script.
- **Stats:** `statistics/NTU_Paiwan_ASR_corpora_stats.csv` refreshed (260 files; Central 16 / Eastern 98 /
  Northern 115 / Southern 31). Audio-seconds were already 0.0 (need `update_audio_stats.py` with audio
  downloaded; CI also refreshes token stats on push).
- **Remaining (maintainer):** review the working-tree diff; commit + push (CI regenerates metrics);
  run `update_audio_stats.py` once audio is local; archive/retire the private dev repo (keeps the key).

## Decisions log
- 2026-06-12: Perfect transcriptions = independent new material (keep, don't merge). Untranscribed audio → boring XML (Tang/Whitehorn); partial → two-file (WilangYutas). HF split: recommend after live check.
- 2026-06-12: Partial recordings → **two-file (WilangYutas) model**: `{pseud}_{topic}.xml` (transcribed window S) + `{pseud}_{topic}_untranscribed.xml` (TEXT+AUDIO, full wav). Missing Y2 audio exists on a large public Google Drive (needs Google auth; maintainer/credentialed run to fetch) — XML is built transcription-driven now, audio/HF backfills later. Converter must PRESERVE curly apostrophe ’ (=glottal stop); perfect-transcription timestamps are full-file timeline.
- 2026-06-12: **Y1 and Y2 are distinct individuals** (additive 16-speaker count + impossible injective dialect/gender match + codes are prompt IDs). Y2 gets 10 fresh pseudonyms; no cross-year continuity. Supersedes the earlier "same person → same pseudonym" goal, which the spreadsheet data contradicts.

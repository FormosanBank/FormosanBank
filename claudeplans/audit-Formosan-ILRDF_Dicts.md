# Audit — Formosan-ILRDF_Dicts (`Formosan-Update-Apr_2026` branch)

**Date:** 2026-06-14
**Repo:** `../Formosan-ILRDF_Dicts/`
**Branch audited:** `Formosan-Update-Apr_2026` (tip `1e4b63a`) — Jacob Ye's new-API update
**Baseline:** merge-base `df6d397` (last shared commit before the branch); `main` also assessed
**Coverage:** all 16 languages

All quantitative claims come from parsing the actual XML/pickles on disk and from **live ILRDF
API calls** (the API is reachable from the sandbox; no credentials needed).

---

## What Jacob did

Re-scraped all 16 ILRDF online dictionaries against the **new API** and rebuilt the XML:

- **`scrape.py`** — rewritten for the new API. Headword discovery changed from "search a
  PDF/ODT-extracted word list" to **symbol-index enumeration** (`get-symbol` →
  `get-list-by-symbol`), walking the API's own complete index. The `*_fails_END.pkl` files are
  now all empty (5 bytes), i.e. no failed lookups — coverage is far more complete.
- **`xmlify.py`** — rewritten for the new JSON shape; adds an `is_published()` filter that
  **drops `frequency==0` drafts** (the entries Jacob found to carry misattributed audio).
- **`audioDL.py`** — rewritten for the new `/Data/api/Storage/<uuid>/download` audio URLs.
- **`data_validation/`** — a new, well-built acoustic audio-QC pipeline (CTC + WER + CER + PDM
  mismatch scoring → rank/flag → interactive listen-and-verdict). **Only run on Amis so far.**
- Deleted several old porting/conversion utilities (`download_audio_data.sh`,
  `upload_hf_datasets.sh`, `mp3_to_wav.py`, `rename_audio.py`, `add_dialects.py`,
  `verify_audio_files.py`); added `validate_audio.py`, `retry_failed_audio.py`.

## Answers to the five questions

**1. Does it work?** Yes — the pipeline runs and the design is sound; symbol enumeration is a
real improvement. Caveat: the acoustic audio-QC was run on Amis only.

**2. More text/audio?** Text grew a lot: sentences **98,838 → 168,296 (+70%)**, tokens
**658k → 1.16M (+76%)**, every language up; Truku **4,682 → 29,626** (the old scrape had badly
under-collected it). Audio grew modestly: AUDIO elements **98,827 → 106,834 (+8%)**.

**3. Prior content retained?** Text: **97.9%** of old sentences survive (matching on normalized
text; the raw-match figure looked far worse only because the branch uses modifier-letter
apostrophe `ʼ` U+02BC where the old standardized data used ASCII `'`). Audio: of 98,602 old
audio-bearing sentences, **90% kept audio; ~7,300 surviving sentences are now text-only** — some
intentional (freq=0 removal), but concentrations in non-freq0 languages (Saisiyat 712, Puyuma
481) are worth a spot-check. *Audio comparison is on AUDIO elements only; files are gitignored.*

**4. Original issues addressed?**

| Issue | Status |
|---|---|
| Wrong audio on `frequency=0` drafts | ✅ Addressed by excluding freq=0 (Jacob verified ~10 Amis cases) |
| Wrong audio at plausible length | ⚠️ Tooling built; run on Amis only |
| Spurious `?` mid-word | ❌ **Not fixed — it is a SOURCE-DATA defect** (see below) |
| **Structural regression** | ❌ Output is raw scraper XML: no `standard` tier, no PHON/IPA, audio de-segmented |

**5. main vs the branch?** main's 3 post-merge-base commits are **fully superseded**:
`93a2cca` README format (branch rewrote the README), `7c2dcce` "conservative XML remediation"
(cosmetic re-indent of Truku.xml only — and it incidentally dropped `dialect="Truku"`; branch
regenerates Truku wholesale), `a9e6925` "Fixed some scraping" (expanded the **old** scrape.py's
language list, with a `Puyma` typo; branch replaced scrape.py entirely). Nothing in main needs
porting. The one thing neither carries is `TEXT/@dialect` — must be (re)added during QC.

## Root cause of the `?` corruption — confirmed source-side at the byte level

Querying the live API for the Saaroa headword `hliangahli` returns three example sentences:
`…mʉcʉkʉhlʉ?` (correct, `ʉ` transmitted as JSON `ʉ`), `…mucukuhlu.` (a plain-`u` variant),
and `…m?c?k?hl?` — **literal `?` (0x3F) bytes from the server**. The server returns clean
`ʉ` and corrupted `?` *in the same response*, so our scraper decodes correctly; the
corruption is in **ILRDF's database**, not our pipeline. (This corrects an earlier guess that it
was a `requests`/`.text` decoding bug in `scrape.py` — it is not.) The corruption is specifically
the loss of **`ʉ` (U+0289)** in the three orthographies that use it (Saaroa, Kanakanavu, Tsou).
Re-scraping cannot recover it.

## `?` self-repair — deliverables for the maintainers

Detector: a `?` flanked by Latin/IPA letters on both sides (excludes real `?` punctuation and
CJK). Repair: directional `ʉ`-substitution accepted only when the result is a word that occurs
**uncorrupted** elsewhere in the corpus (branch XML + branch pickles + old XML); spot-checked
against the live API (e.g. `man?ng → manʉng`, a real headword, freq 18).

- **110** corrupted tokens (letter-`?`-letter) corpus-wide, in Saaroa/Kanakanavu/Tsou.
- **`claudeplans/ilrdf-q-corruption-FIXED.csv`** — **61 distinct word repairs (71 occurrences)**
  with the recovered spelling + ILRDF headword + evidence count. These can be applied
  mechanically.
- **`claudeplans/ilrdf-q-corruption-NOTFIXED.csv`** — **24** `ʉ`-corrupted tokens with **no clean
  counterpart** anywhere; these need ILRDF (or a language expert) to restore the original. Each
  row has the headword, corrupted token, and full sentence so the source record can be located.
- **`claudeplans/ilrdf-questionmark-spacing-artifacts.csv`** — **15** non-`ʉ` cases (Kavalan,
  Yami, Puyuma, Rukai, Truku). These are a *different* issue: a real `?` run together with the
  next token (e.g. Kavalan `tangi?B` = `tangi? B:` dialogue speaker label, lost space). Lower
  priority; flagged separately so they aren't confused with dropped-letter corruption.

## `?` fixes applied (2026-06-14)

The 71 occurrences (61 distinct word forms, 64 sentences) in the FIXED list were applied
directly to the branch working tree — `Final_XML/{Kanakanavu,Saaroa,Tsou}.xml` — via targeted
per-sentence FORM-text replacement (64 insertions / 64 deletions; all three files still
well-formed). Corpus-wide letter-`?`-letter tokens dropped **110 → 39** (the 39 remaining are the
24 unrecoverable `ʉ` cases + 15 non-`ʉ` spacing artifacts). Changes are **uncommitted**. The
repair logic should also be added to the reproduction pipeline (e.g. a post-`xmlify` step) so a
re-scrape doesn't reintroduce the corruption.

## Lost-audio investigation (the ~7,300)

Branch audio coverage is 63.6% (61,462 sentences with no audio). Breakdown:

- **59,089** are **genuinely audio-less in the new ILRDF API** — the new API exposes far more
  text-only dictionary entries (Truku alone adds ~23,700). Expected, not a bug.
- **2,373** sentences have audio in the new source that the XML **failed to emit** — a **fixable
  processing bug**: [xmlify.py:85-96](../Formosan-ILRDF_Dicts/xmlify.py#L85-L96) (`wrapperXML`)
  dedups by exact FORM text and keeps the **first** occurrence regardless of audio, so an
  audio-less copy seen first discards the audio-bearing duplicate. Fix: prefer the audio-bearing
  occurrence (or graft its `<AUDIO>` onto the kept `<S>`).

Of the specific **7,340** sentences that had audio in the old corpus and lost it: **949** are the
recoverable dedup case above; the other **6,391** are texts the new API no longer serves audio for
(a source/API coverage change — worth flagging to ILRDF, not our bug).

## Audio source-vs-processing check

- **Processing fidelity = 100.00%**: all 106,834 XML `AUDIO/@url` values exactly equal the
  source's `audioItems[0].audioUrl` for the same transcript. Our pipeline introduces **zero**
  mispairing. The live API returns the same URL today for a sampled transcript, and the URL
  serves real MP3 (`HTTP 206, audio/mpeg`).
- **No crude file reuse**: among published entries, **no** audio URL is attached to more than one
  distinct sentence — so a wrong pairing is not detectable from metadata; it requires acoustic
  comparison (hence the `data_validation` CTC/WER/PDM pipeline).
- **Conclusion**: any remaining wrong-audio is the **source's** transcript↔file pairing, not our
  processing. Jacob's freq=0 exclusion removes the systematically-wrong drafts; residual mislabels
  inside freq>0 must be found acoustically (pipeline exists, run on Amis only).

## Recommended path before porting

1. Apply the 61 FIXED `?`→`ʉ` repairs; send the 24 NOT-FIXED + 15 spacing artifacts to ILRDF.
2. Re-run the FormosanBank QC pipeline so the XML is publishable again: `clean_xml` →
   `standardize` (rebuild the `standard` tier — currently every `<FORM>` is bare, **failing the
   XSD's `kindOf use="required"`**) → `add_phonology` (PHON/IPA is entirely gone); fix the now-
   inaccurate `TEXT/@audio="segmented"`.
3. Run the `data_validation` acoustic pipeline on **all 16** languages, not just Amis; commit the
   verdict/exclusion logs.
4. Spot-check the ~7,300 sentences that lost audio (intended freq=0 removal vs. dropped URLs).
5. Re-add `TEXT/@dialect`.

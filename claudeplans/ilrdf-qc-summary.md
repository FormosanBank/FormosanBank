# Formosan-ILRDF_Dicts — QC pipeline run & findings (2026-06-14)

Branch `qc-fixes-questionmark-and-audio-dedup`. Pipeline run in this order (your
specified ordering — standardize before clean_xml):

```
xmlify.py (kindOf="original", dialects, dedup-audio recovery, drop placeholders)
  → repair_questionmark.py --apply        (restore ʉ from source-side '?')
  → standardize.py --copy                 (build the standard tier)
  → clean_xml.py                          (normalize: ʼ→', ??→?, trailing ws, …)
  → add_phonology.py                      (standard-tier PHON / IPA)
  → validators
```

## Final corpus shape (all 16 languages)

| | |
|---|---|
| Sentences (`<S>`) | 168,290 (6 empty-placeholder entries dropped) |
| FORM tiers | original + standard (168,290 each) |
| PHON | 168,290 (`kindOf="standard"`, one per S — see note) |
| AUDIO refs | 109,207 (incl. +2,373 recovered from the dedup fix) |
| Dialects | set on all 16, valid per `dialects.csv` |

*PHON note:* `add_phonology` with Ortho113 `--copy` emits only the standard-tier
PHON (original-tier PHON is produced only when a custom source-orthography TSV is
supplied). Since original == standard in copy mode, this is complete and correct.

## Validator results — characterized

### HARD
| Rule | n | Status / cause | Fix |
|---|---|---|---|
| V036 dialect missing | 16→**0** | xmlify set no `TEXT/@dialect` | **Fixed** — dialect map in xmlify |
| V017 empty FORM | 9→**0** | source placeholder text (`''`,`' '`,`-`,`---`) | **Fixed** — xmlify skips non-alphanumeric entries |
| V073 empty PHON | 5→**0** | downstream of the empty FORMs | **Fixed** (same) |
| V081 id collision | **16** | TEXT id matches the **already-published** `Corpora/ILRDF_Dicts/` copy | **Not a defect** — the re-port overwrites that copy; collision disappears on port |

### SOFT (review-only; all benign or expected)
| Rule | n | What it is | Recommendation |
|---|---|---|---|
| V122 parens/slashes | 20,936 | overwhelmingly in the `zho` TRANSL (Chinese glosses); some in FORM | accept (normal for a dictionary) |
| V133 dash in standard | 3,704 | **100% Bunun (4,687 dashes) + Thao (127)** — orthographies that keep `-` | accept (C012 correctly retains `-` for these) |
| V137 footnote leak | 233 | source codes like `H1`,`N1` trailing in FORM/TRANSL | optional cleanup; report to ILRDF (extraction artifact) |
| V116 non-ASCII | 64 | `ē` (U+0113), `＿` (fullwidth underscore) — source typos/artifacts | optional cleanup; spot-fix or report |
| V134 angle brackets | 4 | `<…>` in 4 Saaroa FORMs | inspect; likely source markup to strip |
| V111 / V114 | 1 / 5 | one imbalanced paren; five double-spaces | trivial |

### Orthography / vocabulary (informational)
- Character-frequency distributions match the reference closely (cosine ≈ 1.00,
  overlap-coefficient 1.00). Character-set Jaccard 0.60–0.89 — the corpus carries
  extra **rare** characters (footnote digits, the residual unrecoverable `?`,
  punctuation), not missing reference letters.
- **Reference data missing** for Kavalan, Thao, Truku (`QC/validation/reference/<L>/`
  absent) — a reference-side gap to fill, not a corpus problem.

## Audio — status & required work

- **References are valid/live**: 32/32 sampled URLs return real audio.
- **Smoke-test** (25 Amis clips downloaded + `validate_audio.py --check_silence`)
  surfaced a real systematic issue: **~16% of files are WebM containers served and
  saved as `.mp3`.** ILRDF's `/download` endpoint returns mixed containers
  (MP3 + WebM), all labeled `audio/mpeg`; `audioDL.py` hardcodes `.mp3`
  ([audioDL.py get_audio_ext](../Formosan-ILRDF_Dicts/audioDL.py)). mutagen's MP3
  loader then can't read the WebM ones → V101 "unloadable". The audio is valid;
  the container/extension is wrong. (The old, deleted `mp3_to_wav.py` transcode
  step used to mask this — the merge-base stored `.wav`.)
  - **Fix:** sniff the container (magic bytes) in `audioDL.py` and either name
    correctly (`.webm`/`.mp3`) or transcode to a uniform format (WAV/MP3) via
    ffmpeg.
- `ffmpeg`/`ffprobe` is **not installed in this environment**, so MP3 silence
  detection couldn't run here; a full audio pass needs ffmpeg.

### Full audio validation + HF push (follow-up plan)
1. Fix `audioDL.py` container handling (above).
2. `python audioDL.py` — download all ~109k clips (hours, several GB; 100 workers).
3. `python validate_audio.py --xml_path Final_XML --path Final_audio --check_silence`
   on a host with ffmpeg → triage `broken_audio.csv` (missing/unloadable/silent).
4. Optionally run `data_validation/` acoustic mismatch screening (CTC/WER/CER/PDM)
   across all 16 languages (currently Amis-only).
5. HF push: `upload_hf_datasets.sh` was **deleted** on this branch and must be
   restored (or use the FormosanBank `download_audio_data.sh` convention for the
   ported corpus).

## Port-readiness verdict: **YES, with two caveats**

XML hard-gates pass (V081 is the expected already-published self-collision). The
two open items before/at publication:
1. **Audio**: run the full download + validation with the `audioDL` container fix,
   and restore the HF push path.
2. **Reference orthographies** for Kavalan/Thao/Truku are absent (informational
   validators skip them).

# Wilang Yutas Videos

Wilang Yutas and his collaborator 劉宇陽 recorded these [Atayal videos](https://www.youtube.com/@wilangyutas9297). The corpus contains Sekolik Atayal (`tay`), with some Mandarin translations: 82 XML files, 34 transcripts, 48 audio-only files and 3,014 sentences.

## Rights

**License:** CC BY-NC 4.0

**Rights source:** 劉宇陽, 2024-12-26; evidence: ask maintainer

The grant specifies CC By-NC; POL-042 supplies the canonical 4.0 spelling. The corpus remains subject to FormosanBank's [central terms](https://github.com/FormosanBank/FormosanBank/blob/main/LICENSE.md) and [AI use addendum](https://github.com/FormosanBank/FormosanBank/blob/main/AI-USE-ADDENDUM.md).

## Reproduction

Required inputs, source hashes, build code and tests are under `CodeAndDocs/`. The canonical output is `XML/Atayal/`. Install the current FormosanBank requirements and `CodeAndDocs/requirements.txt`, then run:

```bash
./CodeAndDocs/generate_xml.sh
```

From a separate development checkout, select the current tools explicitly:

```bash
FORMOSANBANK_ROOT=/path/to/FormosanBank PYTHON=python3 \
  QC_OUTPUT_DIR=/path/to/external/reports ./CodeAndDocs/generate_xml.sh
```

The build starts from the committed transcripts in a fresh staging directory, then runs the shared cleaner, `standardize.py --remove_accents`, and `add_phonology.py --orthography Ortho94`. Ortho94 and accent removal retain the published processing decision. The standard tier follows current `standards.csv`. Code-switched Japanese and Mandarin are retained; the Atayal phonology profile does not transcribe those languages correctly.

**POL-047 deviation:** After standardization, copy source FORM notes onto standard FORM to preserve the published speaker qualifications. This changes notes only; shared tools still generate all standard text and PHON.

The build uses the selected checkout's tools and records their actual revision in [provenance.json](CodeAndDocs/provenance.json). That record is informational, not a tool pin. A Git-free export retains its supplied provenance. Warnings are saved outside the corpus; the printed directory must be reviewed. Source refresh, validators and audio acquisition are separate from the XML build.

Run the corpus regression checks separately:

```bash
python3 -m unittest discover -s CodeAndDocs/tests -v
```

`CodeAndDocs/audit_source_alignment.py --xml-root /path/to/pre-clean/XML` checks a separate pre-clean build from `CodeAndDocs/make_xml.py --output-dir /path/to/empty/XML`. This checks parser coverage, not independent source fidelity or final QC. Current FormosanBank validators and source review are still required; historical test counts are not a readiness gate.

## Source processing

[video_manifest.tsv](CodeAndDocs/video_manifest.tsv) lists every output, video ID and source hash. The 34 committed transcripts preserve Joshua Hartshorne's published corrections from [the June source repair](https://github.com/FormosanBank/FormosanBank/commit/5dbd832e245ff1f34078aa2c8e8bb314957556b8). `CodeAndDocs/import_reviewed_sources.py` performed this one-time import and updated the hashes. It is not called by regeneration.

The reviewed inputs contain 3,014 non-empty timestamp rows, 237 translation lines and five wrapped caption continuations. The earlier development scrape's 3,441 empty timestamps are absent from the reviewed inputs. Restoring those empty rows would change 22 published audio endpoints. All published TEXT/S IDs, recording filenames, audio-only entries and endpoints are retained.

Each timestamped caption becomes one S. An indented continuation, or a continuation of an open speaker parenthesis, belongs to that caption. Unindented translation lines stay translations, including two instances of the name `Wilang`. Parentheses identify a second speaker in this source; their content is retained and the speaker boundary becomes punctuation. They do not indicate optional words.

Transcription gaps retain the published word boundary after `UNCLEAR`, so regeneration cannot join the words on either side. The gap supplies no invented text or phonemes.

The [issue #1 source review](CodeAndDocs/issue_1_review.tsv) retains all 20 flagged instances of source-authentic Japanese/Mandarin content. Two pure `(再確認)` recheck markers are recorded in FORM notes rather than emitted as translations. Two similar annotations attached to real translations move to translation notes. No spoken text is deleted. The complete earlier acquisition and processing versions remain in Git history; the development-only scripts under `scripts/` are not reproduction entrypoints.

## Audio

`download_audio_data.sh` downloads the published audio revision selected by FormosanBank's shared manifest and checks its XML inventory. It preserves the published files without resampling or segmentation. It is optional for text regeneration; `--dry-run` checks the remote inventory without downloading. Use the same `FORMOSANBANK_ROOT` and `PYTHON` settings from a private development checkout.

## Notes and Issues

- Many videos have no transcript. Their XML points to audio without inventing S records. Partly transcribed recordings retain their `_untranscribed` companions.
- Subtitle timestamps are not guaranteed to align perfectly with the recording. Multi-speaker passages have no separate speaker timestamps.
- Source question-mark runs mark attempted but unrecoverable transcription and become `UNCLEAR`. There is no word or morpheme analysis.
- Japanese songs, Mandarin speech and annotations, and the Bopomofo fragment `ㄇ` are intentional source content. Orthography, vocabulary and phonology warnings involving them need source-aware review.
- Repeated utterances are narrative evidence. Do not deduplicate them for corpus publication.

## Citation

Wilang Yutas. 2019. *Wilang Yutas YouTube Channel*. YouTube. https://www.youtube.com/@wilangyutas9297.

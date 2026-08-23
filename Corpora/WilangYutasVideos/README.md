# Wilang Yutas Videos

FormosanBank publication corpus for Wilang Yutas's Atayal video transcripts
and audio-only recording inventory.

## Repository At A Glance

| Field | Value |
| --- | --- |
| Language | Atayal (`tay`), Sekolik dialect |
| Source | [Wilang Yutas YouTube channel](https://www.youtube.com/@wilangyutas9297) |
| Permission | Republish permission provided by collaborator 劉宇陽; XML records use `CC-BY-NC` |
| Canonical output | 82 XML files under `XML/Atayal/` |
| Current content | 34 transcript files, 48 audio-only files, 3,014 sentence records |
| Status | Reconciled publication candidate under current-authority QC |

Wilang Yutas was an Atayal elder who recorded these materials with 劉宇陽.
Some videos are fully or partly transcribed, while others have no transcript.
An audio-only XML file preserves every recording without inventing text.

## License and AI Use

This corpus is subject to its source license and the central FormosanBank
terms in [LICENSE.md](../../LICENSE.md) and
[AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI use is
prohibited without prior written permission.

## Pinned Source Model

The 34 files under `CodeAndDocs/raw_scrape/` are the tracked transcript inputs.
`CodeAndDocs/video_manifest.tsv` pins each input by path, byte count, and
SHA256 and declares all 82 output paths. It also records the 48 audio-only
files and their YouTube video IDs, so rebuilding never depends on a live
channel listing.

Every non-empty timestamped source row becomes one `S`. Empty timestamp rows
are explicitly omitted while their recording remains represented by audio.
Unindented follow-up lines are Mandarin translations, including two source
translations whose complete text is the name `Wilang`. Five wrapped source
lines are continuations and are restored to their preceding timestamp.

Source parentheses mark multiple speakers but lack separate timestamps. Their
content is retained in the FORM text and `notes="multiple speakers"` records
the source convention. Strings of three or more question marks become
`UNCLEAR` markers.

## Rebuild

From the FormosanBank repository root, install the corpus requirements and run
the public two-pass rebuild:

```bash
python -m pip install -r Corpora/WilangYutasVideos/CodeAndDocs/requirements.txt
PYTHON=python Corpora/WilangYutasVideos/CodeAndDocs/reproduce.sh
```

The rebuild performs these fail-closed stages:

1. Verify all source hashes and regenerate all 82 XML files from the manifest.
2. Match every pre-clean XML element to the pinned source inputs.
3. Run the current FormosanBank cleaner.
4. Copy the reviewed historical transcription into the standard tier.
5. Regenerate original Ortho94 and current standard phonology tiers.
6. Run the nine repository regression tests.

`CodeAndDocs/reproduce.sh` runs two complete rebuilds, byte-compares the
canonical XML before and after each pass, and verifies that the required
FormosanBank tool files still match tooling commit
`3a3c47c220520113f747e6a2d441494000e13c4b`. Network access is not used.

The cleaner emits one reviewed C007 warning for the source-authentic `ㄇ` in
`Atayal_28`. The build requires that exact warning, verifies that the character
survives in both FORM tiers, and discards the ephemeral warning CSV.

Live upstream refresh is intentionally outside the pinned rebuild. The corpus
root audio-download script retrieves the reviewed public Hugging Face dataset.

## Issue 1 Review

All 21 MT quality findings are dispositioned in
`CodeAndDocs/issue_1_review.tsv` with exact XML and source evidence.

- Findings 1 through 20 are source-authentic Mandarin or Japanese
  code-switching, annotations, speech, and song lyrics. They remain in FORM
  instead of being deleted as MT noise.
- Finding 21 is a real typing defect. The source line `(再確認)` is an editorial
  recheck marker, not a free translation. The marker is retained in FORM
  notes and no `TRANSL` is emitted. The other pure recheck marker is handled
  the same way. Two recheck annotations attached to real translations move to
  `TRANSL/@notes` while the translation text remains intact.

## Current QC Result

The August 23 run against the pinned current authority reports:

- source alignment: 82/82 output files, 3,014/3,014 included rows, 3,441
  explicit blank-row omissions, 237 translation lines, and five wrapped
  continuations, with zero mismatches;
- regression tests: 9 passed;
- update-mode structural XML: zero findings after excluding only the existing
  `WilangYutasVideos` publication target;
- text: 183 source-authentic or current-authority SOFT findings, zero HARD;
- gloss structure: 3,010 expected V060 SOFT findings because the source has no
  token-aligned W/M analysis, zero HARD;
- duplicates: 11 reviewed source-backed narrative groups in each tier, all
  SOFT under the current policy;
- exact adjudication: 3,215 accepted finding occurrences or groups, zero
  unresolved;
- private development-layout port readiness: zero HARD and one expected P005
  warning because audio statistics are keyed to the published corpus name;
- published-layout port readiness: zero HARD and zero warnings. All 3,062
  AUDIO references are unchanged from the current published target, and the
  stored duration statistics remain anchored to the current 3,014 transcribed
  and 48 untranscribed AUDIO counts.

The 48 audio-only files have no text for orthography analysis. The detector
therefore analyzes the 34 transcript files and identifies Atayal Sekolik as
the best profile; the empty files are expected non-text inputs.

## Audio Notes

Many videos have only partial transcripts. A companion `_untranscribed.xml`
file references the remaining recording without creating empty sentences.
Downloaded or segmented WAV files are ignored by Git. Subtitle timestamps are
source-provided and may not align perfectly with the recording.

## Citation

Wilang Yutas. 2019. *Wilang Yutas YouTube Channel*. YouTube.
https://www.youtube.com/@wilangyutas9297.

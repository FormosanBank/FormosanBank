# Audit: Formosan-ILRDF-YouTube-Videos

Date: 2026-07-21  
Dev repository: `../Formosan-ILRDF-YouTube-Videos`  
Auditor: Codex, with maintainer authorization to proceed through all audit checkpoints

## Scope and result

This audit reviewed every data-touching scraper/build transformation, mapped it to the current FormosanBank pipeline, rebuilt all output, ran the canonical validators, and compared final original tiers against a fresh source-derived build. A second live-source investigation on 2026-07-21 replaced manual listing capture with direct paginated discovery and rescraped every public record.

Technical hard gates pass. The corpus is **not ready to port** because redistribution permission is unconfirmed.

## Preprocessing reviewed

1. Fetch all pages of ILRDF's public `/colloquial/list` endpoint and require the unique-card count to equal the source's advertised total.
2. Scrape current page titles, description, all labeled source metadata, ISO code, raw ILRDF/ePark dialect payload, subtitles, translations, source line numbers, and start times.
3. Resolve the selected canonical dialect ID and Glottocode from maintained CSV snapshots.
4. Repair one documented source timestamp typo and sort the few out-of-order subtitle elements by playback time.
5. Recover rows where the Indigenous and Mandarin columns are visibly swapped.
6. Exclude sentence-initial `*` examples, exact non-speech rows, and unrecoverable CJK-only source rows.
7. Preserve visible source punctuation/segmentation; remove only internal `*` correction markers while retaining their parenthesized correction text, per V129.
8. Build one XML text per transcribed video, attach verified local whole-video audio when available, and derive interval ends from the next source subtitle start.
9. Run canonical cleaning, copy the mixed official source tier to standard, and generate phonology.

## Pipeline mapping

| Transformation | Classification | Audit conclusion |
|---|---|---|
| HTML entity, NFC, and whitespace normalization | Canonical pipeline overlap | Representation-only in the builder; canonical `clean_xml.py` remains authoritative |
| Manual expanded-listing capture | Reproducibility gap, remediated | Live paginated discovery now fetches all 47 pages and validates the advertised record total; the saved HTML is offline recovery only |
| Detail-page metadata selection | Corpus-specific, expanded | All visible labeled fields are now retained, including previously omitted titles, descriptions, language labels, keywords, locations, speakers, interviewers, contributors, and provenance |
| Old punctuation deletion | Conflict, remediated | Removed from the builder; original now retains hyphens, `=`, slashes, parentheses, and other visible punctuation |
| Old apostrophe conversion | Canonical pipeline overlap | Deferred to `clean_xml.py`; source extraction retains the original glyph first |
| Dialect/ISO inference | Corpus-specific | Now table-driven, retains raw source payload, and resolves every page |
| CJK/Latin column swap | Corpus-specific extraction repair | 1,139 visibly swapped rows recovered |
| CJK-only source exclusion | Corpus-specific language filtering | 294 rows excluded; samples are Mandarin-only turns, not Formosan transcription |
| Non-speech filtering | Formosan convention | 41 exact notes excluded without substring guessing |
| Asterisk handling | Formosan V129 | One sentence-initial ungrammatical row excluded; internal correction marker removed while correction content remains |
| Standard tier | Mixed corpus, no single mapping | `standardize.py --copy`; detector results vary by language/dialect and the previous standards were exact copies |
| Audio interval derivation | Source limitation | ILRDF provides whole-second starts only; end is next source start, final end is probed duration |
| Glottocodes | Canonical metadata | Invalid Xiuguluan/Dona codes corrected to `cent2104`/`tona1238` upstream and locally |

## Findings by highlighted concern

### (a) Eliminated orthography characters

The old builder/cleaned output differed from the fresh source-faithful build in 38,255 matched original tiers and had removed or changed substantial source detail, including 2,570 hyphens, 311 slashes, 3,732 opening parentheses, 3,759 closing parentheses, and the source modifier-letter apostrophe inventory.

Remediation moved destructive normalization out of the builder. After the final canonical cleaning pass, all 104,049 original forms exactly match an independently rebuilt-and-cleaned tree: 0 missing, 0 extra, 0 differing.

Concrete sample:

- `JSON/Atayal/247.json`, `sentence_92`
- Source/final: `curin-ciy sawa nku mhu hani hya lga`
- Old output: `curinciy sawa nku mhu hani hya lga`

### (b) Suppressed punctuation and segmentation

Remediated. Concrete samples retained in final originals:

- `JSON/Truku/748.json`, `sentence_145`: `sib=naw`
- `JSON/Atayal/755.json`, `sentence_8`: `oyume/kekong`
- `JSON/Seediq/39.json`, `sentence_12`: `( kari Tgdaya)`
- `JSON/Atayal/271.json`, `sentence_198`: source `*(nha)`, final `(nha)` (V129 marker removed; correction retained)

The remaining text findings are SOFT: V122 parentheses/slashes 26,784; V133 hyphens 1,537; V126 one equals sign; V134 angle brackets 18.

### (c) Other convention breaks

- XML/XSD: 465 files, 0 issues.
- Dialects: all 32 language/dialect buckets are populated and canonical.
- Asterisk hard gate: remediated; final V129 count is 0.
- No W/M tiers; gloss validation is not applicable.
- Duplicate validator reports 646 within-file groups and 988 cross-file groups. Source inspection shows distinct-timestamp repetitions (backchannels, songs, repeated elicitation lines), so these were retained rather than deleting genuine transcript events.
- Orthography extraction initially exposed an upstream empty-punctuation plotting crash; FormosanBank now handles empty inventories and has a regression test.

### (d) Source-extraction artifacts

- The live endpoint advertises 468 records over 47 pages. All pages were fetched,
  yielding 468 unique IDs that exactly match the prior checkout; no additional
  public colloquial records were found.
- 468 current detail pages scraped; all carry ISO and resolved dialect metadata,
  Chinese titles, source language labels, and the complete available source-field
  inventory. The rescrape adds 216 Indigenous titles and 233 descriptions plus
  optional keywords, locations/communities, speakers, interviewers, contributors,
  and provenance.
- 104,385 subtitle rows inspected and source-line-numbered. After ignoring the new
  metadata, their transcription, translation, and timestamp content is unchanged
  from the prior checkout. The builder retains 104,049; 1 sentence-initial `*`, 41
  exact non-speech notes, and 294 Mandarin-only rows are excluded.
- 1,139 swapped language columns recovered.
- Four timestamp-order defects found. Three are adjacent DOM-order swaps. Video 341's source `970` occurs between `527` and `535` and exceeds the 905.683-second media duration; it is explicitly corrected to `530`, with `source_start_time: 970` retained.
- V137 samples are real numeric content, not footnote leakage: e.g. `I nu70ay a mihcaan` / “70幾年” and `ta19 歲` / “從19到21歲”.
- Cleaner warnings retain 676 quote/apostrophe notices and 54 Bopomofo intrusions for human review.

## Validator results

| Check | Result |
|---|---|
| Unit tests in dev repo | 12 passed |
| `validate_xml.py` | PASS — 465 files, 0 issues |
| `validate_text.py` | PASS hard gate — 0 HARD, 30,165 SOFT |
| `validate_audio.py` | PASS hard gate — 0 broken-audio findings; 8,590 SOFT rate outliers |
| Orthography comparison | Character overlap 0.72–1.00 (median 0.865); frequency cosine 0.98–1.00 |
| Vocabulary comparison | Top-100 overlap 0.28–0.68 (median 0.495) |
| Source-to-final reproducibility | Fresh final XML is identical to the prior independently audited output; 104,049/104,049 originals remain source-faithful after canonical cleaning |

The audio validator was corrected upstream to calculate rate checks from each clip's `start/end` interval rather than the duration of the whole shared media file. Its regression suite passes. The always-on audio gate was rerun. The optional silence mode was stopped after confirming it would launch 103,246 independent `ffmpeg` checks (about six hours); the 464 local media files are unchanged from the prior completed silence pass.

## Audio and permission

Of 468 source videos, 464 MP3s downloaded and probed successfully. YouTube reports 302, 308, and 669 unavailable; 275 is age-gated and local browser cookies could not be decrypted. Video 302 has no subtitle rows. XML 275, 308, and 669 omit audio references rather than pointing to nonexistent files; the other 462 XML texts contain 103,246 valid intervals. A further 168 retained subtitle rows begin beyond the duration of their current YouTube media and intentionally omit intervals.

No open redistribution license was found. The ILRDF corpus site reserves copyright, and the related ILRDF AI site requires formal authorization. Keep audio local and do not port/publish until written permission covers XML/transcriptions, translations, metadata, and audio.

## Recommendation

Keep the remediated dev repository as the reproducible source and retain the QC artifacts. Do not port into `FormosanBank/Corpora` until redistribution permission is documented. If permission is obtained, review the 54 Bopomofo warnings and the four unavailable/age-gated videos before publication.

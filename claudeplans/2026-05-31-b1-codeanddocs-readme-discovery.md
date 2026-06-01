# B1 discovery: CodeAndDocs READMEs and reproducibility scripts

**Date:** 2026-05-31
**Source:** Read `Corpora/<corpus>/CodeAndDocs/README.md` (or top-level `readme.md` where that was the actual location) plus script file headers/comments. Did not execute any reproduction code.

**Naming note:** Three corpora (NTUFormosanCorpus, TangRecordingsOfTaroko, WilangYutasVideos) use `DocsAndCode` instead of `CodeAndDocs`. One corpus (UtrechtManuscriptWordList) is a raw XML file, not a directory. READMEs for Glosbe, NTUFormosanCorpus, WilangYutasVideos, and YeddaPalemeqBlog live at the corpus root, not inside CodeAndDocs.

---

## Per-corpus summary

| Corpus | Has README | Has repro scripts | Flow documented | Risks |
|---|---|---|---|---|
| ePark | yes (CodeAndDocs/) | yes (ePark1and2.py, ePark3.py + 10+ helpers) | yes, detailed | Most complex corpus; audio pipeline is fragile; several steps acknowledged as "should have been done earlier"; dialect/ID-fixing steps are post-hoc patches |
| ILRDF_Dicts | yes (CodeAndDocs/) | yes (scrape.py, xmlify.py, audioDL.py) | yes | Scrape depends on live ILRDF API; API changes would break reproduction; step 5 note says kindOf="original" was added in a late patch rather than at creation time |
| HundredPaiwanStories | yes (CodeAndDocs/) | partial (convert.py, fix_ferrell.py, script.ipynb) | partial | Several sentences fixed by hand with no programmatic record; character encoding fix not recorded ("probably regex") |
| MontgomeryTexts | yes (CodeAndDocs/) | no (only Original.pdf) | no pipeline | OCR + hand correction; one typo fix noted; no scripts present |
| NTU_Paiwan_ASR | yes (CodeAndDocs/) | yes (main.py, add_citations.py, add_dialect.py, extract_audio_clips.py, normalize_audio_filenames.py) | yes | Audio is in continuous files split post hoc; 2 audio segments silently removed from one file |
| Paiwan_Stories | yes (CodeAndDocs/) | no | no pipeline | XMLs created by hand from PDF; no scripts |
| Presidential_Apologies | yes (CodeAndDocs/) | yes (main.py) | yes | Step 2 ("Code Breakdown") is empty — README cuts off mid-section |
| RauDong | yes (CodeAndDocs/) | no | explicitly non-reproducible | README states pipeline is not reproducible; no scripts |
| SEALS33 | yes (top-level README.md) | no (only raw text files in CodeAndDocs; no .py/.sh) | partial | XMLs created by copy-paste; no automated scripts |
| Glosbe | yes (root readme.md, not in CodeAndDocs/) | yes (scrape_zh.py, dedupe_zh.py, make_xml.py, fix_colon_quote.py, validate.py) | yes | Step 8 ("Add Traditional Chinese") explicitly noted as "not easily reproducible"; scraping may violate Glosbe ToS |
| NTUFormosanCorpus | yes (root readme.md; uses DocsAndCode/) | yes (run_parsers.py, parse_grammar.py, parse_stories.py, parse_sentences.py, download_grammar_audio.py, download_stories_audio.py, remove_no_audio_elements.py, utils.py) | yes, detailed | Multiple documented known issues (audio mismatch, 56 bad-gloss sentences removed, 819 clitic alignment cases, 366 W-count mismatches, 1415 M-segment mismatches); audio for some entries simply missing |
| TangRecordingsOfTaroko | yes (root README.md; uses DocsAndCode/) | yes (make_xml.py, upload_hf_datasets.sh) | yes | No transcription; XML is just audio metadata; strict reproduction requires Paradisec access |
| Virginia_Fey_Dictionary | yes (CodeAndDocs/) | no | no pipeline | XML created from miaoski/amis-data CSV + hand cleaning; no script preserved |
| WakelinTexts | yes (CodeAndDocs/) | no | no pipeline | Transferred to XML by hand; orthographic system not yet identified |
| Whitehorn_Collection | yes (root README.md) | no (CodeAndDocs/ contains only per-tape PDF subdirs) | no pipeline | XMLs compiled by hand; README says "not entirely reproducible" |
| Wikipedias | yes (CodeAndDocs/) | yes (download.py, clean_articles.py, remove_other_langs.py, MakeListOfMarkers.py, check_nonlatin.py) | yes, detailed | Non-Formosan text removal is heuristic (parentheses, character frequency); may over- or under-remove |
| WilangYutasVideos | yes (root readme.md; uses DocsAndCode/) | yes (scrape_videos.py, make_xml.py, analyze_xml.py, download_audio.py) | yes | YouTube API dependency; question-marks-as-unclear handled via sed one-liner in README (fragile); orthography assumed (Ortho94) |
| YeddaPalemeqBlog | yes (root readme.md) | yes (download_html.py, analyze_blog_structure.py, download_audio.py, Scripts/make_xml.py, Scripts/test_xml_baseline.py, Scripts/test_runner.py) | yes | Step 2 calls `analyze_blog_structure.py` but the file is in root CodeAndDocs, not Scripts/; WARNING in README flags complex scraping |
| Siraya_Gospels | yes (root README.md) | yes (referenced fix_linebreak_hyphens.py, though no CodeAndDocs dir exists) | partial | No CodeAndDocs directory at all; scripts referenced in README not present in the corpus directory; OCR + extensive manual hyphen corrections |
| FormosanBankGitBook | yes (CodeAndDocs/) | yes (process_raw.py) | yes | README says `python main.py` but the script is named `process_raw.py` — stale reference; only Eastern Paiwan currently implemented |
| UtrechtManuscriptWordList | n/a — is a raw XML file, not a directory | n/a | n/a | The entry `Corpora/UtrechtManuscriptWordList` is a bare XML file, not a corpus directory. No CodeAndDocs. |

---

## Cross-corpus patterns

### Corpora without CodeAndDocs (or equivalent)
- **Siraya_Gospels** — no CodeAndDocs directory at all; scripts referenced in README but absent
- **UtrechtManuscriptWordList** — is a bare XML file at the path where a directory is expected; not a corpus directory

### Corpora with DocsAndCode instead of CodeAndDocs (naming inconsistency)
- NTUFormosanCorpus, TangRecordingsOfTaroko, WilangYutasVideos

### Corpora with README at corpus root rather than inside CodeAndDocs/
- Glosbe, NTUFormosanCorpus, WilangYutasVideos, YeddaPalemeqBlog, Siraya_Gospels, Whitehorn_Collection, TangRecordingsOfTaroko

### Corpora with no reproduction scripts (documentation only or hand-done)
- MontgomeryTexts (OCR + hand)
- Paiwan_Stories (hand XML from PDF)
- RauDong (explicitly non-reproducible)
- SEALS33 (copy-paste, no scripts)
- Virginia_Fey_Dictionary (hand cleaning from CSV)
- WakelinTexts (hand XML)
- Whitehorn_Collection (hand XML, audio metadata only)

### Corpora with stale or incomplete READMEs
- **FormosanBankGitBook**: README says `python main.py`; script is `process_raw.py`
- **Presidential_Apologies**: "Code Breakdown" section is empty (section header only)
- **ILRDF_Dicts**: "Download Audio" step duplicated verbatim
- **Siraya_Gospels**: References `fix_linebreak_hyphens.py` but that script is absent from the corpus directory
- **Glosbe**: Step 8 (Traditional Chinese) says "not easily reproducible" — partially undocumented

### Common transformations across corpora (B3 invariant candidates)

These appear in 5+ corpora and are strong candidates for invariant tests:

1. **`clean_xml.py`** — unicode NFC flattening, HTML escape replacement, empty element removal, punctuation standardization. Present in: ePark, ILRDF, HundredPaiwan, NTU_Paiwan_ASR, Paiwan_Stories, Presidential_Apologies, Wikipedias, WilangYutasVideos, YeddaPalemeqBlog, SEALS33, Glosbe, FormosanBankGitBook.
2. **`standardize.py --copy`** — duplicates `original` FORM tier as `standard` tier. Present in nearly every corpus that has a standard tier at all.
3. **Retroactive `add_original.py`** — adds `kindOf="original"` to existing `<FORM>` elements not created with that attribute. Present in: ILRDF_Dicts, NTU_Paiwan_ASR, Paiwan_Stories, Presidential_Apologies, Virginia_Fey_Dictionary. (A marker that the initial script omitted the attribute.)
4. **`add_phonology.py`** — generates IPA `<PHON>` elements. Present in: ePark, NTU_Paiwan_ASR, Presidential_Apologies, Wikipedias, WilangYutasVideos, YeddaPalemeqBlog, NTUFormosanCorpus, SEALS33, Virginia_Fey_Dictionary, Glosbe, TangRecordingsOfTaroko (implicitly).
5. **Orthography detection + TSV-based conversion** (standardize.py with a `--tsv_path`) — present in ePark (multiple per-language TSVs), HundredPaiwanStories (Ferrell→113), WilangYutasVideos (Ortho94), Glosbe (Ortho94→same). Key invariant: `standard` tier should differ from `original` tier only where the TSV has a mapping.
6. **Concurrent audio download with failure logging** — ePark, ILRDF, NTU_Paiwan_ASR, WilangYutasVideos, YeddaPalemeqBlog. Failed downloads should produce a log; XML should not reference files that aren't present.

### Reproducibility gaps worth fixing

1. **Siraya_Gospels**: References `fix_linebreak_hyphens.py` in README but no CodeAndDocs directory and no scripts exist in the corpus. Script needs to be located and added, or README corrected.
2. **HundredPaiwanStories**: Character encoding fix was "probably regex" and not recorded. This is an unrecoverable gap unless the original Word doc and final XML are diffed.
3. **RauDong**: README explicitly says non-reproducible. Even a note about what was done (OCR? hand entry? received pre-processed?) would reduce the knowledge gap.
4. **FormosanBankGitBook**: `main.py` vs `process_raw.py` mismatch needs correcting in README.
5. **UtrechtManuscriptWordList**: The path `Corpora/UtrechtManuscriptWordList` resolves to a raw XML file, not a directory. There is no CodeAndDocs, no README, and no provenance information at all in the repo. This is the largest documentation gap.
6. **Glosbe step 8**: Traditional Chinese addition not reproducible; should at minimum be documented as a manual step with a description of what was done.
7. **Presidential_Apologies README**: Empty "Code Breakdown" section should either be filled in or removed.
8. **DocsAndCode vs CodeAndDocs**: Three corpora use `DocsAndCode` instead of the standard `CodeAndDocs` — worth normalizing for tooling consistency (the port-corpus-in skill and any scripts scanning for CodeAndDocs/ will miss them).

---

*Per-corpus details (script enumerations, transformations applied, etc.) preserved in the original subagent output. The summary tables and cross-corpus patterns above are the actionable distillation.*

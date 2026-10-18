# Checklist: every corpus

**Source and extraction**

1. **The extraction is counted against the source's own extent, not its own inventory.**
   How: the corpus's `test_source_accounting.py` (emitted ∪ rejected = every source unit, each rejection with a reason); if absent, enumerate the source's units yourself (numbered examples, rows, verses, pages) and diff. Compare the source's declared extent (lemma count, page count, chapter list) with what the build found.
   Acceptable: every unit accounted for; a test that cannot fail is not a test (plant a missing unit and watch it go red).
   Example: Seediq-Chang reported 353 of 353 blocks "reviewed" while chapters 5 and 6 were never extracted; the marker-driven parser could not see narrative.

2. **Layout read as content.** Wrapped lines as new records, headings spliced into text, page-top orphans, column interleaving, splits driven by typeface.
   How: for a PDF source, decide wrap-vs-new-record by cell geometry (left edge, column width), never by content; check alphabetical or numerical order for breaks; look at page tops and bottoms in the rendered page.
   Acceptable: an invariant per entry format with its defect list, stated in the README.
   Example: Poinsot — 36 wrapped printed lines became headwords; Utrecht — page-top continuation lines silently dropped.

3. **Letters lost or substituted by OCR or the text layer**, including a space swallowed next to an apostrophe.
   How: character inventory against `QC/validation/reference/<Language>/` and against the source; a distributional check (share of vowel-less words: Tsou 16% when `x` was read for `ʉ`, under 2% elsewhere); attest both halves of a split token across the bank, per language; render the page at 300 dpi and put the crop beside the data.
   Acceptable: the original tier matches the printed page (an OCR correction toward the page is expected, POL-001); spelling is never changed.
   Example: Wu 2018 scrape — the space beside the glottal `'` swallowed in 12% of sentences; Presidential Apologies — Tsou `x` for `ʉ` in seven words.

4. **Upstream drift in a living source; a damaged middle hop in a digitisation chain.**
   How: pin the upstream (sha256 manifest per file, release pin), diff pin against HEAD and classify against the print; re-verify against the earliest raw text.
   Acceptable: `refresh_source.sh` separate from `generate_xml.sh` (POL-047); a letter change under three letters adopted unless a new letter appears, else asked (maintainer rule).
   Example: Safolu — 204 sentences follow g0v editors' revisions, not the book; ILRDF 2026 withdrew 1,256 published sentences.

**Notation**

5. **Starred parentheses.** `*(X)` = X obligatory (must be in FORM, unstarred); `(*X)` = X forbidden (must not be). POL-017.
   How: grep the source and extraction ledgers for `*(` and `(*`; trace every hit into the XML; flag a script that treats the two alike.
   Example: NTU Rukai published `*(malra)` dropped; Shih Rukai inverted 6 of 18.

6. **Slash, brace, bracket, parenthesis mean different things per source, and the shared cleaner rewrites some.**
   How: build a notation key from the source's own legend before any normalisation; then decide what `clean_xml` does to each symbol (`[ ]` → `( )`, for instance); cite POL-025/026/027/028; use `QC/utilities/slash_alternatives.py` and `parentheticals.py` where they fit.
   Acceptable: a key in the README, every symbol with its meaning and its fate.
   Example: Wakelin — slashes are transcriber doubt, never alternatives; Seediq-Chang — `{a/b}` braces scope the slash and `[ ]` is an embedded clause.

7. **Null-morpheme glyphs and placeholders added in processing, not printed.**
   How: a provenance census of every `∅`/`ø`/`Ø`/`?` against the scan; read the build for where they are created.
   Acceptable: POL-012 (the cleaner canonicalises a separated null to `∅`), POL-060 (a shared gloss is one W), POL-061 (an unglossed word is glossed `?`). POL-061 and the 2026-09-04 HundredPaiwanStories ruling point opposite ways; surface both, do not pick.
   Example: Seediq-Chang — 41 `∅` none of which the book or the raw OCR has.

8. **Segmentation markers stripped from the original or W tier; infix notation rewritten; `standardize` fusing hyphenated pronouns.**
   How: vocabulary overlap against the reference (`validate_vocabulary.py --quiet`); cross-corpus counts of spelling pairs (`sapah-mu` vs `sapah mu`).
   Acceptable: the source orthography recorded as a ruling; differences filed under spelling normalisation, later (maintainer: "not now").
   Example: Amis SVC stripped `-`/`=`/`<>` from FORMs; Seediq-Chang fused 155 pronoun tokens.

**Identity**

9. **Ids that move.** Positional ids renumber when one record is added; rulings keyed on ids stop matching.
   How: derive ids from the source record before first publication; key rulings on content; on a re-port, `content_delta.py` (see `re-port.md`).
   Acceptable: POL-037 — stable ids; `-opt` ids assigned after dedup (POL-028).
   Example: Seediq-Chang — fixing the star bug renumbered 179 sentences; Blust — 31 verdicts stopped matching.

10. **Dialect labels without a source.**
    How: cite the source's own statement of dialect (its prose, its map, its title page); run `validate_dialect.py` and `declared_vs_detected.py`; on a re-port diff `TEXT/@dialect` against the merge base.
    Acceptable: a dialect the source states, or the maintainer's ruling quoted; `trv` is Seediq or Truku by the dialect attribute, never by the code.
    Example: Seediq-Chang — "Tegudaya" set with no reason while the book says 霧社方言; ILRDF v2 relabelled 62,484 Truku records `unknown`.

11. **Rights.** `TEXT/@copyright` an exact value from `rights_vocabulary.csv`; the README's Rights block (POL-042/043/044).
    How: the 4b table rows; `rights_delta.py` is red by design on any change.
    Acceptable: never downgrade from absence (POL-043) — a claim replaced by prose because the evidence was not found is a finding against the PR.

**Build and reproduction code**

12. **The build runs from a FormosanBank checkout alone and reproduces the published bytes.** POL-047/048/052.
    How: run `generate_xml.sh` twice from a clean copy; byte-identical; diff against the published XML; `git status` empty. Run main's tool on main's XML to separate tool drift from edits.
    Example: Safolu's build exited 2 on main; Fey's rebuild drifted by 97 lines; Wikipedias changed 741 files with unchanged code (tool drift the provenance file exists to explain).

13. **Build shape.** One entry point (no Makefile or second script beside it, at the corpus root too); no validators inside the build; provenance written by the build; a deviation stated with the literal `**POL-047 deviation:**` line.
    How: `pytest tests/corpora -k <Name>` runs the static tests; read the scripts.

14. **Hand edits a rebuild cannot reproduce.** Edits to source text files, correction tables as Python literals, `manual_edits.xml` with a FILE path that matches nothing.
    How: `lint_hidden_tables.py --corpus`; `apply_manual_edits.py` now fails on a dangling path; look for a content-gated decision table (record id + expected input text + reason + date + the maintainer's words, refused when the input drifts — Safolu's `safolu_source_overrides.json`, Seediq-Chang's `review_corrections.tsv`).
    Acceptable: POL-030/038/039; decisions in a reviewable table, not in code.

15. **Checks that cannot fail.** Completeness keyed to the extractor's own output, a test that compares the FORM to what it was built from, a fixture that cannot exercise the code path, hard-coded totals.
    How: plant a violation and watch for red; keep a positive control; every check ships with its own non-vacuity proof.
    Example: Seediq-Chang's `audit_source_alignment.py` hard-coded W/M totals and reported 0/0/0 on the very bug it should catch.

16. **Shared-tool side effects.** The cleaner's quote rule on glottal `'`, a chained conversion rule, PHON taken from a variant FORM.
    How: replay the cleaner step by step on one file; before changing a shared tool, replay the change over the whole bank and every dev repo (blast radius), and carry the `Shared-change-approved:` trailer.

17. **Duplicates.** Key = base FORM + every TRANSL, compared after cleaning, per language; every removal has a survivor; policy by corpus type (POL-022).
    How: `validate_duplicate_sentences.py` (within), `find_duplicate_sentences.py` (across); classify groups (identical / notes / translations / analysis).
    Example: Blust — 10 of 15 merged copies carried a different Mandarin translation.

18. **Stray and stale files.** Report CSVs, logs, backups, extract_logs, `.cache/` inside `XML/` or `CodeAndDocs/`.
    How: `git ls-files Corpora/<Name>`; `tests/corpora/test_xml_dir_holds_only_xml.py`; always pass `--log_dir`/`--warnings_dir`.

**Documentation**

19. **README drift.** Stale claims, prose counts nobody lints, missing or misordered required sections.
    How: `tests/corpora/test_readme_sections.py` (layout and License block); derive every count in prose from the XML and compare; the README is user-facing, since the documentation site renders it as the corpus page (maintainer rule).
    Example: Wakelin's README said 52 words lost their M tier; the file had 5.

20. **How questions are put to the maintainer.** State the question; show the full record as printed with the printed and PDF page; never truncate; regenerate open-only; read the store back before saying "consumed"; no own linguistic analysis on the card.

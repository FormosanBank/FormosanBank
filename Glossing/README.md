# Glossing

Standardization of morphological glosses across FormosanBank corpora. The
standard glosses live in the published XML as `TRANSL[@kindOf="standard"]` at
W/M level, added **alongside** the source's own glosses, which are never
modified (POL-036, POL-062).

## The standard

- **Base**: the Leipzig Glossing Rules — [Leipzig-Glossing-Rules.pdf](Leipzig-Glossing-Rules.pdf).
  Where Leipzig is silent (voice-label inventories, discourse codes, …) we add
  our own supplementary rules, recorded in the conversion tables' `basis`
  column and in the scoping reviews.
- **Codes are Latin-only in every standard tier**, including Chinese-language
  gloss tiers; the lexical part of a gloss stays in its tier's language,
  marked by `xml:lang`.
- **Voice names**: `AV` (actor), `PV` (patient), `LV` (locative), and `OV`
  ("other voice") for the cross-linguistically variable fourth voice
  (instrumental / benefactive / referential / reason), so comparison across
  languages does not depend on taking a stand on its characterization.
- **Language-specific codes** default to the usage of the language's reference
  grammar, overridable in favor of cross-language consistency where feasible.
- *Proposed, not yet ruled*: verbs in moods where two voices collapse are
  glossed with a pair notation (e.g. `PV/LV`) rather than left unglossed —
  such tokens are excluded from voice *analysis* but must still be glossed.

## The files

- **`ConversionTables/<Corpus>.tsv`** — one row per atomic gloss code:
  `source_code · count · status · standard · basis · notes`. Status is
  `CONVERT` (mapped), `KEEP` (decided: no change), or `UNDECIDED` (copied
  verbatim into the standard tier until decided). The UNDECIDED rows of a
  table are exactly what remains to investigate for that corpus. Lexical
  glosses get no rows and are copied verbatim.
- **`ConversionTables/<Corpus>.rules.tsv`** — the corpus's structural
  conventions (separators, parentheses, brackets), as ordered rules, on the
  model of `Orthographies/Ortho113/<Language>.rules.tsv`. Strings these rules
  cannot segment are copied verbatim and surface in the conversion run's
  residue report.
- **`supplementary_codes.tsv`** — the vocabulary of all non-Leipzig codes we
  standardize to (RULED vs PROPOSED, each with its basis). Grows as rulings
  land; nothing enters a conversion table's `standard` column unless it is
  Leipzig-listed or in this file.
- **`ScopingReview/<Corpus>.md`** — the corpus's scoping findings: its
  documented glossing conventions (with sources), code inventory, internal
  inconsistencies, and deviations from Leipzig.
- **`GlossDictionaries/<Language>.tsv`** — the language's ruled gloss codes:
  two columns, `gloss · definition`, one row for every code the conversion
  tables map onto for that language. A code that is not in the table is an
  original source gloss whose meaning is still to be decided.
  `GlossDictionaries/corpus_languages.tsv` records which languages each
  corpus covers. `tests/glossing/test_gloss_dictionaries.py` enforces that
  every mapped-to code of every corpus/language pair is defined here, and
  the documentation site renders each language's table directly from its
  TSV (`docs/tools/language_pages.py`), so there is nothing to sync by hand.

### Cross-source flagging (single-source codes)

Run when a corpus's table is seeded:
1. If a smaller source has a code that a larger one (at least 1,000 glossed
   words) does not, flag it for inspection.
2. If two sources each have at least 1,000 glossed words and one uses a gloss
   code that the other does not, flag it.
3. For a single-source gloss code, check the other corpora for that language
   for the same word; if it appears, flag it, counting how many times it
   appears and with what gloss. Step 3 is performed regardless of the outcome
   of steps 1 and 2.

Definitions come from the corpus's own documentation and original sources
first; project-wide design decisions are recorded in
`claudeplans/2026-11-11-gloss-standardization-design.md`.

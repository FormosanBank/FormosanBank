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

## Voice on forms with no voice affix (Leipzig Rule 7)

Ruled by the maintainer on 2026-11-15 (unvoiced-verbs audit, https://claude.ai/artifact/HLiGFJQqfFCxAbFAZm8CDy):
"Rule 7 (see(AV))", in FormosanBank, for "All 12,001 with a lexical gloss; the 3,684 on affixes/auxiliaries stay
as they are".

- When a gloss fuses one voice code with a lexical gloss (Leipzig Rule 4, `AV.see`, `say.AF`), the standard tier
  writes it as an inherent category in round brackets (Leipzig Rule 7): `see(AV)`, `say(AV)`, `FUT.go(AV)`.
  A group whose other pieces are all codes (an affix or auxiliary such as `AUX.AV`, `PV.IMP`) keeps the period.
- Exception to the 2026-11-11 ruling "parens/brackets shouldn't be in glosses": a parenthesis attached to a gloss
  and holding only codes (`die(AV)`, `打（AF）`) is a Rule 7 category; it is converted (`打(AV)`) instead of being
  copied as residue. Every other parenthesis is still flagged (rules files: `RULE7-PARENS`).
- A rules file may also replace one exact whole gloss: `<exact gloss>  WHOLE-GLOSS→<CODE>` (maintainer,
  2026-11-16: "Yes"). Only a gloss that is exactly that text converts; the pattern is literal, not a regular
  expression. In use: HundredPaiwanStories `(name)` and `(place)` → `PN` ("A: standard tier → PN; original
  unchanged"); YeddaPalemeqBlog `ligature (LIG)` → `LNK` ("LNK, as ruled on 2026-11-11 (no new code)").
- `validate_text` rule V122 (parentheses and slashes) skips these brackets (maintainer, 2026-11-16: "exempt any
  gloss registered gloss code (including Leipzig codes) found inside parentheses when there is also other content
  in the gloss"): in a word or morpheme gloss, a parenthesis whose content is only codes from
  `leipzig_codes.tsv` or RULED rows of `supplementary_codes.tsv`, joined by periods, is not flagged when the gloss
  has other text. A gloss that is only `(OBL)`, or a parenthesis holding an undecided code such as `他(屬格)`, is
  still flagged.
- Bare forms the sources leave without a voice gloss get one only by an explicit rule,
  `<gloss>&=<stem>  CONTEXT-ADD→<VOICE>` in the corpus's rules file: on a word whose form (lower case, `=` clitics
  removed) is `<stem>` and which carries no voice code at all, the morpheme glossed `<gloss>` gets `(<VOICE>)`.
  The rules come from the audit's rulings: HundredPaiwanStories bare aya/vaik ("Add them as AV (780 words)");
  NTU Bunun bare tupa/ta'aza/huud ("Those plus huud (74)"); and, in six corpora, stems voice-glossed elsewhere
  ("Only when the stem is voice-glossed at least 3 times AND at least twice as often as it is not
  voice-glossed."). The stems that did not qualify are listed in `ScopingReview/bare_forms_not_given_voice.tsv`
  (see OutstandingIssues.md).
- `QC/glossing/apply_gloss_standard.py --redo-changed` re-derives existing standard glosses under these rules,
  replacing one only if it is exactly what the tool produced before (hand-made standards are left alone).

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
- **`leipzig_codes.tsv`** — the 83 standard abbreviations of the Leipzig
  Glossing Rules (`code · meaning`), copied from the appendix "List of
  Standard Abbreviations" of `Leipzig-Glossing-Rules.pdf` (PDF pages 8–10).
  Read by `validate_text` rule V122.
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

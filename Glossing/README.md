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
  marked by `xml:lang` (maintainer, 2026-11-11).
- **Voice names**: `AV` (actor), `PV` (patient), `LV` (locative), and `OV`
  ("other voice") for the cross-linguistically variable fourth voice
  (instrumental / benefactive / referential / reason), so comparison across
  languages does not depend on taking a stand on its characterization
  (maintainer, 2026-11-11).
- **Language-specific codes** default to the usage of the language's reference
  grammar; the maintainer may override, preferring cross-language consistency
  where feasible (maintainer, 2026-11-11).
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
- **`ScopingReview/<Corpus>.md`** — the corpus's scoping findings: its
  documented glossing conventions (with sources), code inventory, internal
  inconsistencies, and deviations from Leipzig.

Definitions come from the corpus's own documentation and original sources
first; project-wide design decisions are recorded in
`claudeplans/2026-11-11-gloss-standardization-design.md`.

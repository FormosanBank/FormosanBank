# Source decisions and remaining work

Source: the committed *Kanakanavu Texts* PDF, SHA-256
`785058bad6a8495f8b5fb51ed3d0eaf7da1736e791b308611d9442c010d93c03`.
Use printed example numbers and physical PDF pages below as stable locators.

## Preserve

- Footnote 37, physical page 157, replaces field-note ŋanai with vanai in
  Not Eating Eels II, examples 2, 4 and 6. All three corrected readings remain.
- The Basecamp review accepts four printed gloss-notation inconsistencies:
  Text 10 example 45; Text 11 example 82; Text 28 example 8; Text 36 example 9.
  Text 40 example 20 has the single English gloss priest-shaman. Preserve the
  original glosses; a marker-skeleton warning does not authorize rewriting them.
- [Private issue 1](https://github.com/FormosanBank/Formosan-Kanakanavu-Texts/issues/1)
  preserves Sumio 澄男 on physical page 206 and the long source translation of
  masuuvuuvu on page 209. Neither is an extraction error.
- Keep the 17 repeated narrative groups. Repetition in a story is source data.
- On physical page 90, Naparamaci example 68, interjection aligns with əhə.
  The parser previously put it on kai and padded əhə with UNCLEAR. The source
  parser now keeps the printed column alignment and leaves kai's gloss absent.
  The multiword gloss sibling's spouse on page 72 is preserved unchanged.
  Final XML still awaits the shared build; the correction is in the parser.
- The introduction's two starred constructions use the scoped grammatical
  reading/exclusion, retained with the raw source in the notation report:
  page 24 example 23b and page 25 example 26a (POL-016/POL-017).

## Phonology dependency

The source key on physical pages 16–17 states that c and s palatalize before i.
Madeline's 2026-08-12 Basecamp review supplies the source-to-Ortho113 mapping;
its examples demonstrate that environment despite the message saying "after".
It also accepts l/r merging to standard r and ə mapping to standard e.
Those scoped decisions do not authorize arbitrary new conversion mismatches.

The old wrapper supplied its own Asai2026 profile, removed analytical brackets
from four S-only readings and added standard palatalization by replacing shared
functions. Current canonical Ortho113 does not reproduce those conditioned
standard PHON values. Do not silently revert the reviewed output or restore the
private override to make a current build pass. The retained mapping files are
historical evidence for separate shared-tool work, not build inputs.

## Representation and coverage review

All 24 parenthetical source examples were checked against the PDF on 2026-09-12.
Six retain the same W/M inventory and gloss and now use same-tier FORM variants:
page 53 example 4, page 55 example 1 (tee/tia, explicitly a variation in footnote
14), page 71 example 14, page 93 example 88, page 95 example 102, and page 231
example 9. Both readings remain on the affected W and M in source output;
the retained final XML awaits regeneration. The locators and decisions are in
[notation_decisions.tsv](notation_decisions.tsv). Nine cases have optional whole
words and five have different glosses or analyses; these retain two S readings.
Four classifications remain open: page 64 example 31 (ha/sua), page 65 example
42 (mu-usa/mu-kusa), page 189 example 13 (ha/sua), and page 200 example 35
(ha/sua and iihaa/iisua). Preserve their two readings pending resolution.
Source generation now uses base IDs and -opt instead of V1/V2; the corpus is
not yet published (POL-028/037).
The tee/tia root triggers V150 SOFT for low overlap; footnote 14 establishes
the pronunciation relationship, so both readings remain (POL-028).

Physical page 24 examples 23a-d use square brackets to delimit pseudo-cleft
clauses. Source generation preserves those brackets at S and restores the
15 aligned W and 24 M previously omitted. In 23b the starred kaən-ən=musu
and its 2SG.GEN gloss stay excluded; the admitted kaən-a keeps eat-NMLZ.UV.
This is scoped to the four printed rows, not a general bracket-removal rule.

The affixation section on physical pages 18–19 identifies PFV and AV as separate
infixes. Eight narrative words use `<in-um>`, `<in-əm>` or `<in-m>` with `<PFV-AV>`:
page/example 66/47, 138/62, 142/12, 176/17, 193/34, 229/22 and 242/20,27.
Source generation now splits each into two M while preserving the gap root,
W notation and following clitics (POL-014/015/036). Five following M IDs shift
by one across three words; S/W IDs and all source readings remain unchanged.
The single-infix and priest-shaman controls remain unchanged. Current G002/V061
count a bracketed pair as one slot; retain the source-backed two-infix analysis.

Preserve the 16 short sentences whose 57 M mirror their W. Equal forms alone
do not establish an invented tier; the source supplies aligned word/gloss rows,
and POL-023 permits monomorphemic words in otherwise parsed narratives.

The 87 footnotes, four introduction tables and unnumbered lexical examples
need explicit coverage accounting. Table 1 uses three historical orthographies;
the other tables mix pronouns, affixes and schematic stems. Page 20 also cites
Saaroa forms. Preserve these distinctions instead of applying the narrative
Kanakanavu profile to every item.

## Review evidence

The old source audit stored 31 fixed checks and a seeded 30-unit sample. The
sample IDs are retained for comparison, but equal IDs do not prove that the
content or tools are unchanged. New automatic reports mark visual review as
NOT RUN, and extraction warning queues remain needs_review. Mechanical
agreement is reported separately from source review and QC.

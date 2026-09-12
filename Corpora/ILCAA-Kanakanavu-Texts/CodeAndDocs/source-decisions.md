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
standard PHON values. The earlier review does not explicitly distinguish source
from standard PHON, so this difference alone does not establish a shared-tool
defect. Do not silently revert the previous output or restore the
private override to make a current build pass. The existing `--tsv_path` and
`--orthography` flags can read the committed source tables directly. With those
flags, current tools produce source PHON `ʂiʂiʔinamaku` and `taʔitʂikikani`,
but standard PHON `sisiʔinamaku` and `taʔiʦikikani` for the reviewer's examples.
The source rules work; the unresolved choice concerns canonical standard PHON.
Changing the table paths alone therefore does not make the build ready. The
entry point passes the committed narrative tables through those flags, without
requiring copies in FormosanBank. It retains final XML pending the standard-tier
decision and reviewed routes for the additional introduction profiles.

The Saaroa comparison `iɫakia` has a separate, four-grapheme source profile.
The cited [Saaroa Texts (2023)](https://doi.org/10.15026/125201), section 2,
printed page 3 (PDF page 16), identifies its `ɫ` as a voiceless lateral fricative;
the form itself appears on printed page 6. Preserve `ɫ` in original FORM and
derive IPA `ɬ` and Ortho113 `hl`: `iɫakia` -> `ihlakia`, with `iɬakia` in
both PHON tiers (POL-001/002/003). This profile covers only that comparison,
not Saaroa generally. The build processes its language directory separately.
The Tsuchida 1969/1976, Szakos 1999 and Basic Vocabulary 2007 groups still need
their own routes; the narrative profile does not cover their sound descriptions.

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

The [footnote ledger](footnote_lexemes.jsonl) anchors all 87 notes by source
hash. It emits 57 lexical records from 49 notes, with the full note as context
and page/note IDs in the source index. Note 21 explicitly supplies variants;
note 35 describes a shortened form; note 52 distinguishes general variants
from an archaic word. Separate readings use base/-opt/-opt3 IDs (POL-028).
Printed English/Chinese meanings are retained, including both readings in
notes 53 and 56. No translation or aligned W/M analysis is invented.
Grammar explanations, bound forms, other-language comparisons and editorial
notes remain in the ledger. Note 37's correction is preserved in the narratives,
not emitted as its rejected field-note reading. Note 29 identifies the title
ʔənnaŋ on physical page 146; the introduction ledger now admits the title's
English reading and the note's Chinese meaning together.

The [introduction ledger](introduction_lexemes.json) admits 100 S from 101
page-anchored entries, with six files separated by transcription group.
Table 1's Tsuchida 1969, Szakos 1999 and Basic Vocabulary 2007 columns stay
separate. The printed Tsuchida cells ta’ɨ́lɨmɨ and ranɨ́ngɨ correct the PDF text
layer's v́ to ɨ́ in those two cells only (physical page 16, POL-001).
Table 2 supplies 16 distinct free-pronoun forms from 17 cells; repeated íikia
and the prose reuse of kumakaɨn share reference records with both contexts
retained (POL-022). Stress is preserved and row labels are not invented English
translations. Bound pronouns, affix templates, phoneme inventories and Table 4
remain context. The Saaroa comparison iɫakia has its own sxr file (languages.csv). The prior
xsr tag identified Sherpa and caused shared phonology to skip it; correct the
source language code while preserving its Saaroa path and IDs (POL-039).

The pronoun distinction is resolved by Tsuchida's *Reconstruction of Proto-Tsouic
Phonology*, 1975 Yale dissertation, section 2.1.2.2, printed pages 37–38
(PDF pages 71–72): iimukásu and iimukámu are vocatives; the other independent
pronouns occur in noun positions. Keep íikasu/iimukásu and íikamu/iimukámu as
four separate S records, not spelling variants (POL-027/028). The inspected
copy is the 1975 dissertation, not the 1976 published edition cited by the
2026 book; its Figure 5 contains the same four forms. This resolves their
classification without changing source spellings, IDs or translations.

On physical page 24, mu-caanə/AV-go, um-avici/AV-bring and
k<um>a-kili/RED<AV>-tie supply three W and seven M, including the k-a gap root
and -um- infix. No free S translation is supplied or invented (POL-014/023/036).
The two phonetic representations on pages 15–16 stay explicit decisions.
Four historical profiles require separate conversion review. The full build
rejects unsupported profile routing before touching final XML. Source changes
affect four pronoun notes and the Saaroa language tag; forms, IDs, retained
final XML and provenance remain unchanged.

## Review evidence

The old source audit stored 31 fixed checks and a seeded 30-unit sample. The
sample IDs are retained for comparison, but equal IDs do not prove that the
content or tools are unchanged. New automatic reports mark visual review as
NOT RUN, and extraction warning queues remain needs_review. Mechanical
agreement is reported separately from source review and QC.

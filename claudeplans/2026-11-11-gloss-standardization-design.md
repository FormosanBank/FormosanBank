# Gloss standardization — plan decisions and conversion design (2026-11-11)

Project: a `TRANSL[@kindOf="standard"]` gloss tier following the Leipzig
Glossing Rules (`Glossing/Leipzig-Glossing-Rules.pdf`), with conversion tables
in `Glossing/ConversionTables/` documenting every decision, including
determined-no-change entries; pipeline converts what is decided and copies the
rest verbatim; scoping review per corpus first; voice markers asap.

Plan page: https://claude.ai/artifact/7r6meGsAXd1gEQet1jGJr2 (db `gloss_plan`).
Design page: https://claude.ai/artifact/4q7cgjMzxd5NARRsJpkd6E (db `gloss_design`).

## Maintainer decisions (2026-11-11, read back from the plan page's database)

- **g1 — table format: amend.** "I don't see why W and M would have different
  rules. M is derived from W. I think for simplicity we can just not have
  "NOT-A-GLOSS" rows. Only morphosyntactic codes are candidates for
  standardization." → no tier column; statuses CONVERT/KEEP/UNDECIDED only.
  Interpretation check d1 open: do lexical glosses get KEEP rows (recommended)
  or no rows?
- **g2 — granularity: combined.** "We should default to a single column and
  only use multiple language columns when we have good reason to believe the
  same gloss codes are used differently for different languages in a corpus."
  Interpretation check d2 open: read as object languages (orthography-table
  model), default one standard column per corpus.
- **g3 — zho-glossed corpora: codes-only-converted.** Category codes become
  Leipzig-format; lexical material stays Chinese; xml:lang stays zho.
- **g4 — NTU bilingual: two-standards.** "But we should standardize the gloss
  code vocabulary: for all corpora, the standard tier should use only latin
  characters for gloss codes. (The translation glosses can be in English or
  Chinese, but specified as such in the XML attributes.)" → eng+zho standard
  tiers both using one Latin code vocabulary (1IPL.屬格 → 1IPL.GEN in both).
- **g5 — bare kindOf: stamp.** Add `kindOf="original"` explicitly, corpus by
  corpus (10 corpora, per-corpus PRs, diffs shown).
- **g6 — word-level translation corpora: out of scope** (ePark nine-level,
  MontgomeryTexts, YeddaPalemeqBlog W-tier, Blust-Thao W-tier) — recorded
  exclusion, revisit if lexical-gloss policy changes.
- **g7 — order: voice-first.** NTU → ILCAA-Kanakanavu → HundredPaiwanStories →
  Wild-Lehmann → Seediq-Chang/Kavalan-Chang/Song/Sakizaya-Affixes/Nowbucyang →
  RauDong → small eng corpora.
- **g8 — scoping reports: both.** Review artifact first; distilled
  `Glossing/ScopingReview/<Corpus>.md` committed once settled.

## Design round 1 answers (d1–d3, 2026-11-11)

- **d1: codes-only-rows.** "Also, I think we need handle `.` convention
  smartly. In your example above, you give `打（AF）` it's own row. But this is
  going to cause chaos! Really, what we need is something to handle `AF` and
  something to handle the use of parentheses. I almost think formatting
  questions are handled through some other, corpus-specific convention. Maybe
  almost like our "rules" docs for conversion for PHON."
- **d2: object-langs** (one standard column default; per-object-language
  columns only on demonstrated divergence).
- **d3: hold.** "Let's confirm the above decisions." → design revised to v2
  (below), awaiting d4/d5 on the design page.

## Conversion spec v2 — two layers, on the PHON model (supersedes v1)

Mirrors the verified PHON conversion shape (`add_phonology.py` reads
`Orthographies/Ortho113/<Language>.tsv` atomic mappings + ordered
`<Language>.rules.tsv` sidecar with pattern · replacement · description):

- **Layer A** `Glossing/ConversionTables/<Corpus>.tsv` — one row per ATOMIC
  morphosyntactic code (lexical glosses get no rows, copied verbatim):
  `source_code · count · status(CONVERT|KEEP|UNDECIDED) · standard · basis · notes`.
- **Layer B** `<Corpus>.rules.tsv` — the corpus's formatting conventions as
  ordered structural rules (full-width parens 打（AF）→打.AV per LGR Rule 4;
  `.`-compounds split into atoms; `<X>` infix brackets kept per LGR Rule 9,
  inner code mapped; HPS lowercase handled in Layer A atoms, not rules).
- **Pipeline**: Layer B segments → Layer A maps atoms (UNDECIDED copied) →
  assemble; unsegmentable strings copied verbatim + listed in a per-run
  **residue report**. "What's left" = UNDECIDED rows + residue. Scoping builds
  each corpus's code inventory from source docs first (catches HPS-style
  lowercase inventories).

## Conversion-table spec v1 (superseded by v2 above; kept for the record)

`Glossing/ConversionTables/<Corpus>.tsv`, one row per distinct source gloss
string (W+M summed), columns:
`source_gloss · count · status(CONVERT|KEEP|UNDECIDED) · standard · basis · notes`.
`basis` = Leipzig rule §, our supplementary rule id, or the maintainer's ruling
quoted with date. "What's left for corpus X" = its UNDECIDED rows. Pre-filling
of composite glosses allowed where all pieces are ruled; every row keeps its
own status.

## Standard-tier shape

For each original gloss TRANSL, one `kindOf="standard"` TRANSL in the same
xml:lang (NTU: two). Codes: shared Latin vocabulary everywhere; lexical parts
untranslated. Originals untouched (POL-036/POL-062). V085 verified fixed on
main (groups by lang+kindOf) — pairs publish with no `ver`. UNDECIDED strings
copied verbatim into the standard tier. Same pass stamps `kindOf="original"`
where bare (g5).

## Scoping protocol (per corpus)

1. Inventory → the seeded conversion table (all rows UNDECIDED at birth).
2. Definitions from `Glossing/Private/` + dev-repo PDFs; every PDF scrape shown
   beside a page screenshot before recording; extracted content recorded
   outside Private (maintainer's rule 2026-11-11); undefinable codes listed.
3. Internal inconsistencies with frequencies; low-frequency parked.
4. Leipzig comparison per code: conforms / deviates (rule cited) / silent /
   unsure; silent+unsure accumulate into the supplementary-standard agenda
   (known members already: voice-label inventory, NTU FIL/FS/DM, bilingual
   tiers, prose glosses).

## Approvals to ask for, each individually, before creation

1. Commit Leipzig PDF; create `Glossing/ConversionTables/` + `Glossing/ScopingReview/`.
2. The conversion/stamping tool (likely `QC/glossing/`).
3. Each corpus's stamping + standard-tier PR.
4. Any validator additions.

Voice fast-track dependency: 10 open voice-label decisions on
https://claude.ai/artifact/FpZXD4kKyfcTfh4KHFVEe1 — they are the CONVERT
targets for every voice code.

## Design round 2 (2026-11-11): d4 confirm, d5 go → NTU scoping started

Scoping round-1 page: https://claude.ai/artifact/XcoAzNK8i4gwsVsGdW7ngw
(db `ntu_scoping`, cards s1 scrape-check, s2 proceed/redirect). Measured:
620,328 NTU gloss entries; draft Layer-B segmentation (strip `<>`, split
`.-=`) covers 99.7% of tokens; 554 eng code atoms (54 LGR, 10 NTU-doc, 8
voice-audit, 482 undocumented), 163 zho codes via positional eng↔zho pairing
(主焦↔AF 19,520). Headline inconsistencies: CAUS 539 vs documented cau;
NMLZ 1,257 vs documented nmz (undocumented form MORE frequent); AF 22,208 vs
AV 1,468 same category; 1SG/1S, 3SG/3S, 1IPL/1EPL vs 1P(IN) residue;
zho-tier variants 完成/完成貌, 工焦/工具焦/工具焦點, 名物化/名物話(typo); Latin codes inside
the zho tier (FIL 7,636); `<n>`/`<m>` infix forms as glosses; TOP,/主題, typos.
Open classes flagged, not guessed: caps particles (KA/SA/AY/HAN/NI/MAZA…) —
code or lexical?; clusivity shape; voice targets pending the affix page.

**Definition-source order (his ruling 2026-11-11):** Glossing/Private/<Corpus>
first (sometimes an actual gloss list); else dev repo; else pull dev repo
(Hunter deleted sources from most, says all restored); else dev-repo git
history. Private holds (as of 2026-11-11): NTUFormosan, HundredPaiwanStories
(Ch1+Ch5 docx), ILCAA (B602 pdf), RauDong (Yami Texts pdf), Song (source.pdf),
Wild-Lehmann (wild.pdf). Extracted content always recorded outside Private.

## Per-corpus rulings (running)

- **Huteson-Rukai-Survey — no conversion table.** Maintainer 2026-11-11:
  "Huteson does not explain source of glosses. So no table for them."
  Original glosses stay as published; the standard tier copies them verbatim.
- **Lin 2015 glosses are documented in its footnote 1** (maintainer's catch
  2026-11-11): "Glossing conventions in this paper follow the Leipzig
  Glossing Rules. Additional glossing conventions are as follows: AV, agent
  voice; CN, common noun; CP, completive aspect; ENC, enclitic; FAC,
  factual; HUM, human; IA, instrumental applicative; LA, locative
  applicative; LNK, linker; NCM, non-common noun marker; NHUM, non-human;
  PN, proper noun; PREP, preposition; PV, patient voice." NCM = NON-common
  noun (name) marker — corrects the earlier common-noun clustering; these
  definitions double as evidence for NTU's identical undocumented codes
  (FAC, HUM, NHUM, CN, NCM, LNK, PREP).
- **Wakelin gloss codes** supplied by the maintainer 2026-11-11
  (Glossing/Private/Wakelin/WakelinGlosses.rtf): CM construction marker,
  NM name marker, unan unanalyzed, VR verbalizer, unctn uncertain,
  rdpl reduplication, intrg interrogative, pl, incl, imp; `( )` marks a
  probable data discrepancy; EA = added from Erin Asai's data. Only PAR
  (×74) is undocumented in the corpus.

## Landscape facts behind the design (measured 2026-11-11 on main)

20 corpora with W/M glosses, ~1.9M entries. NTU 623k entries / 43,857 distinct
strings, bilingual (3SG.GEN ↔ 3SG.屬格). HPS codes lowercase (af/pf/lf/red/...).
Seediq-Chang embeds codes in zho lexical glosses (打（AF）). NTU FIL×7,883,
DM×4,533, FS×3,284 not in Leipzig. 10 corpora have bare-kindOf gloss TRANSLs.
Precedents: Amis-Pa-Verbs 2 + Tsukida-Seediq 11 kindOf="standard" glosses.

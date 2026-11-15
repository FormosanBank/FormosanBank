# NTUFormosanCorpus — gloss scoping review

Scoped 2026-11-11 (all 193 published XML files; 620,328 word/morpheme gloss
entries with text: 298,596 eng + 322,732 zho). Interactive version with
source-page images: https://claude.ai/artifact/XcoAzNK8i4gwsVsGdW7ngw

## Documented conventions

Source: the corpus's own coding page (corpus.linguistics.ntu.edu.tw/#/coding/),
captured as `NTUGlossingRules.pdf`. It states the corpus "basically follows
the Leipzig Glossing Rules" with these deviations:

- **A.** No coding of inherent categories (Leipzig Rule 7 unused).
- **B.** No `[ ]`/`Ø` for non-overt elements (Rule 6 unused); e.g. Saisiyat
  *'akoy* = `AF.many`, Tsou *bonu* = `eat.AF`.
- **C.** Reduplication not marked `~` (Rule 10): `Ca-` (Ca-reduplication),
  `red-` (word-initial), `<red>` (medial).
- **D.** Voice abbreviations: `af`, `pf`, `rf` (`if`), `lf` = Agent, Patient,
  Referential (Instrumental), Locative Focus.
- **E.** Tsou focus is suffixal/fused, so its focus gloss follows the stem
  (`eat.AF`, `eat.PF`) even for *m-* AF forms; in practice single morphemes
  carry `.AF` with no separable affix (observed: *uh* `go.AF`, *baito*
  `see.AF`), including on auxiliaries (*mo* `AUX.AF`) and adverbs.
- **F.** Abbreviation departures from Leipzig: caus→`cau`, dem→`'this'/'that'`,
  nmlz→`nmz`, recp→`rec`. **Ruled 2026-11-11: these convert back to the
  Leipzig forms** (CAUS, NMLZ, RECP) in the standard tier.
- Discourse marking followed DuBois (1993) with modifications; it has been
  deliberately removed from the published corpus. Residue found in a full
  sweep: 7 sentences (two Kavalan `%` glottal-stop marks, one Seediq `##`,
  one Rukai `,+`, three Sakizaya ellipsis-like `...` in the written Grammar
  subcorpus).

## Inventory

Segmentation (draft structural rules: strip `<>`, split on `.` `-` `=`)
covers 99.7% of tokens. Results:

- **eng tier**: 4,727 distinct atoms; 554 code-shaped (227,639 tokens):
  54 Leipzig-listed or Leipzig-composed, 10 documented by the corpus,
  8 further voice labels, 482 undocumented.
- **zho tier**: 7,376 distinct atoms; 163 identified as codes via positional
  alignment with the eng tier (e.g. 主焦↔AF ×19,520). The zho tier also uses
  Latin codes directly (FIL ×7,636, 3SG ×7,198, DM ×4,525).
- `FIL` = "filler word" (maintainer, 2026-11-11), specific to the spoken
  subcorpus — confirmed: Stories 15,765 / Sentences 4 (one sentence,
  Bunun 37_S_5) / Grammar 0; zho twin 填補詞 corroborates.

## Internal inconsistencies (with frequencies)

- Violations of the corpus's own point F: `CAUS` 539 beside documented `CAU`
  1,751; `NMLZ` 1,257 beside documented `NMZ` 1,080 (the undocumented form
  more frequent). `RECP` unattested.
- Two voice-label systems: `AF` 22,208 / `PF` 5,960 / `LF` 3,880 beside
  undocumented `AV` 1,468 / `PV` 437 (same zho twins → same categories);
  plus `NAF` 944, `BF` 120, `BN/BG/BC` 980/852/583 beyond the documented four.
- Person codes in competing shapes: `1SG` 5,841 vs `1S` 840; `3SG` 7,222 vs
  `3S` 454; `3PL` 2,354 vs `3P` 108; clusivity as `1IPL`/`1EPL` beside
  residue `1P(IN)`/`1P(EX)`.
- zho variants per category: 完成/完成貌 (both PFV), 工焦/工具焦/工具焦點,
  指焦/參焦/參考焦, 使役/使動, 名物化 beside typo 名物話 (6).
- Infix slot sometimes holds the morpheme's form, not a gloss: `<n>` ×131,
  `<m>` ×107.
- Punctuation typos: `TOP,` 26 · `主題,` 20 · fullwidth `＋/＝/＞` · `¬` 2 ·
  `∅` 1.

## Leipzig comparison

Conforms: period-joined categories (Rule 4), hyphens (Rule 2), `=` clitics,
`<>` infixes (Rule 9); 54 codes exactly Leipzig. Documented deviations: A–C,
F above. Leipzig silent: voice-label inventory; discourse codes (FIL, DM, FS,
BC); LNK/PART; RLS; EXIST; CN/PN; clusivity shape. Flagged unsure: caps
particles glossed as themselves (KA 1,306, SA 716, AY 496, HAN 462, NI,
MAZA, …) — arguably lexical, not category codes; class-level ruling pending.

## Conversion state

See [`../ConversionTables/NTUFormosanCorpus.tsv`](../ConversionTables/NTUFormosanCorpus.tsv)
(717 code rows; the ruled voice, point-F, Leipzig-listed and zho-pair
conversions cover 63.8% of code-atom tokens) and
[`NTUFormosanCorpus.rules.tsv`](../ConversionTables/NTUFormosanCorpus.rules.tsv)
(draft structural rules; `(Mandarin)` and parenthesized clusivity codes
pending).

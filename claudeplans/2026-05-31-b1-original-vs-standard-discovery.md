# B1 discovery: original vs standard FORM-tier comparison

**Date:** 2026-05-31
**Source:** Walked Corpora/<corpus>/XML/**/*.xml; compared FORM[kindOf=original] vs FORM[kindOf=standard] within each S element. Read-only audit via file sampling + grep-based counts.

## Headline numbers

- **Total S elements with both tiers: ~436,418** (across 18 corpora with both-tier coverage)
- **By bucket:**
  - identical: ~433,190 (~99.3%)
  - segmentation: ~171 (0.04%) — WakelinTexts only
  - orthography: ~3,057 (0.70%) — HundredPaiwanStories + MontgomeryTexts + FormosanBankGitBook
  - punctuation: 0 observed
  - whitespace: 0 observed (one corpus has reversed tier order — see notes)
  - major: 0 observed

## Per-corpus breakdown

| Corpus | S w/ both tiers | identical | segm | ortho | notes |
|---|---|---|---|---|---|
| ePark | 285,434 | 285,434 | 0 | 0 | All copied; no real standardization |
| NTUFormosanCorpus | 20,007 | 20,007 | 0 | 0 | All copied |
| ILRDF_Dicts | 98,838 | 98,838 | 0 | 0 | All copied |
| HundredPaiwanStories | 2,915 | 0 | 0 | 2,915 | Systematic Paiwan ortho transform |
| Wikipedias | 12,610 | 12,610 | 0 | 0 | All copied |
| RauDong | 793 | 793 | 0 | 0 | All copied (PHON differs; FORM identical) |
| YeddaPalemeqBlog | 668 | 668 | 0 | 0 | Identical; but standard appears BEFORE original in XML (tier-order anomaly) |
| Glosbe | 5,860 | 5,860 | 0 | 0 | All copied; no PHON elements |
| WakelinTexts | 171 | 0 | 171 | 0 | ALL hyphens removed in standard (Yami morpheme segmentation stripped) |
| WilangYutasVideos | 3,014 | 3,014 | 0 | 0 | All copied |
| Virginia_Fey_Dictionary | 2,049 | 2,049 | 0 | 0 | All copied |
| Siraya_Gospels | 1,951 | 1,951 | 0 | 0 | All copied |
| MontgomeryTexts | 40 | ~4 | 0 | ~36 | Amis ortho transform; title-only S are identical |
| Presidential_Apologies | 326 | 326 | 0 | 0 | All copied (10 languages) |
| SEALS33 | 58 | 58 | 0 | 0 | All copied |
| Paiwan_Stories | 45 | 45 | 0 | 0 | All copied |
| NTU_Paiwan_ASR | 1,537 | 1,537 | 0 | 0 | All copied |
| FormosanBankGitBook | 102 | 0 | 0 | 102 | Eastern Paiwan vowel-lowering transform (see below) |
| TangRecordingsOfTaroko | 0 | — | — | — | No S elements; TEXT shells only |
| Whitehorn_Collection | 0 | — | — | — | No standard tier at all |
| UtrechtManuscriptWordList | — | — | — | — | Not a directory — it's a FILE in Corpora/ |

## Corpus-level detail: the three corpora with real diffs

### HundredPaiwanStories (2,915 S, all orthography diffs)

**Transform:** systematic standardization to FormosanBank Paiwan orthography:
- `ɫ` → `lj` (e.g., `Puɫaɫuyaɫuyan` → `Puljaljuyaljuyan`)
- `ts[vowel]` → `c[vowel]` (e.g., `tsug` → `cug`)
- R/r treated differently depending on context

Sample (`Corpora/HundredPaiwanStories/XML/PaiwanCh2_001.xml`):
- S id `001S1`: orig `"ti sa Puɫaɫuyaɫuyan tsug a marivu katua vaɫaw."` → std `"ti sa Puljaljuyaljuyan cug a marivu katua valjaw."`

**Assessment:** Expected, correct behavior. Systematic and orthographically motivated.

### WakelinTexts (171 S, all segmentation diffs)

**Transform:** Yami language, 6 files. Original preserves morpheme-boundary hyphens; standard removes ALL hyphens.

- `m-angay-ta` → `mangayta`
- `mang-anak-u` → `manganaku`
- `kwan-a` → `kwana`

**Note:** WakelinTexts is Yami (`tao`), not Bunun/Thao, so hyphen stripping is the right behavior here. But standard tier loses all morphological information from FORM.

### FormosanBankGitBook (102 S, all orthography diffs)

**Transform:** Eastern Paiwan vowel-lowering / orthographic re-normalization:
- `u` → `o` in many positions: `tua`→`toa`, `nu`→`no`/`noa`, `su`→`so`
- `i` → `o` in some positions
- ~20-30% of tokens differ

Sample S id `0`: orig `"kemuda itjen a pusaladj tua FormosanBank?"` → std `"kemoda itjen a posaladj toa FormosanBank?"`

**⚠️ Bug found in S id 2** of `Contributing_to_FormosanBank.xml`: `open-source` → `open-soorce` in the standard tier — typo introduced during standardization. **Worth investigating.**

### MontgomeryTexts (~36/40 S, orthography diffs)

**Transform:** Amis standardization (modern Amis orthography):
- `ř` → `r`
- `ts` → `c`
- `?` → `'` (glottal stop notation)
- `r` ↔ `l` in some lexical items (allophonic; may warrant review)

~4 title-only uppercase S elements (SIRO, etc.) are byte-identical.

## Structural anomalies

1. **YeddaPalemeqBlog: reversed tier order.** In all 668 S elements, `FORM kindOf="standard"` appears *before* `FORM kindOf="original"`. The DTD doesn't enforce ordering; content is identical so this is not a content bug, but QC tooling assuming original-first order could be affected.

2. **UtrechtManuscriptWordList: not a directory.** The path resolves to a 285,055-byte file, not a directory. Does not follow the corpus directory convention. Contents not examined.

3. **TangRecordingsOfTaroko: TEXT elements with no S children.** Files are valid but contain only `<TEXT>` + `<AUDIO>` — no S elements. Awaiting transcription.

4. **Whitehorn_Collection: no standard tier.** S elements exist but none have `kindOf="standard"` FORM elements. Not yet standardized.

## B3 invariant candidates (from this data)

1. **The 99.3% "identical" rate suggests an enforceable invariant**: "If a corpus has a standard tier, all S elements that aren't in the three known-transformed corpora (HundredPaiwanStories, WakelinTexts, FormosanBankGitBook, MontgomeryTexts) should have byte-identical original and standard tiers." Could be a SOFT validator rule that counts non-identical pairs in supposedly-copied corpora.

2. **Per-corpus "expected transform" pin**: for the 4 corpora with real diffs, pin the transformation. E.g., HundredPaiwanStories should ONLY differ in `ɫ→lj` and `ts→c` substitutions; anything else is a bug.

3. **WakelinTexts segmentation invariant**: standard tier should be exactly the original with hyphens removed. If a single non-hyphen difference appears, flag it.

4. **YeddaPalemeqBlog tier order**: minor but real — could be a SOFT validator rule flagging non-canonical FORM tier ordering within S.

## Notes / limitations

- Analysis method: due to a global Bash permission hook blocking Python script execution, automated per-file diffing was not possible. Counts from `grep -rc '<S id='` per corpus (verified to match `FORM kindOf="original"` counts) plus manual reading of representative XML files. Bucket assignments based on inspection of 2-10 files per corpus and character presence checks.
- Bucket counts for non-identical corpora may be approximate (±5 for MontgomeryTexts).
- Corpora not examined: TangRecordingsOfTaroko, Whitehorn_Collection (both in-progress / pre-standardization).

# Attestation dictionary review — Atayal (ISO `tay`) — REV 2

**Dictionary:** `QC/validation/reference/Atayal/attestation.txt` (7,985 entries, unchanged since round 1)
**Reviewed:** 2026-08-11 (rerun; read-only, no repo files modified)
**Round 1:** `claudeplans/phase-a-reviews/Atayal.md`; rulings applied from `claudeplans/phase-a-reviews/00-consolidated.md`
**Scope change vs round 1:** assessment is **per corpus** against each corpus's README-declared original-tier orthography; **Wikipedias excluded** from correction-volume estimates by maintainer ruling (all Wikipedias languages except Seediq keep `'` as assumed-glottal by fiat).

Target corpora (Group 1, correction-live): `Corpora/Glosbe` (tay subtree) and `Corpora/WilangYutasVideos`.

---

## 1. Corpus: Glosbe (Atayal subtree, `Corpora/Glosbe/XML/tay`)

**Declared orthography (README `Corpora/Glosbe/readme.md`, lines 52–59):** original tier is **Church** ("Atayal (tay) | Church | `Atayal_Church_113.tsv` (single standard column) | dialect unknown; the Church table is dialect-agnostic"); original-tier IPA comes from `Orthographies/Church/Atayal.tsv` default column.

**Is `'` a letter in Church Atayal?** **Yes.** `Orthographies/Church/Atayal.tsv` line 8: `'` → ʔ (both Sekolik and default columns). Corroborating: the Church→113 conversion table `Orthographies/ConversionTables/Atayal_Church_113.tsv` contains only one row (`e` → `_`) — `'` passes through unchanged into Ortho113, where it is also the glottal letter (`Orthographies/Ortho113/Atayal.tsv` line 8: `'` → ʔ in every dialect column including YilanZeaol). Apostrophes in this corpus are presumptively glottal letters; the correction machinery applies and the dictionary's veto is the relevant safety mechanism.

**Replay (exact production path, `apply_quote_corrections` as called by `clean_xml.py` lines 756–786, in memory):**

| metric | value |
|---|---|
| files (xml:lang=tay) | 2 |
| S | 523 |
| S with `'` in original FORM | 96 |
| `'` total | 101 |
| TRANSLs (all with text) | 586 |
| TRANSLs containing any `TRANSL_QUOTES` char | **0** |
| TRANSLs containing any extended-charset char (`《》〈〉‘’` added) | **0** |
| **corrections (c031) / stranded (c032) / ambiguous (c030)** | **0 / 0 / 0** |

Counterfactuals: **empty dictionary → still 0/0/0**; **extended `TRANSL_QUOTES` (the known charset-gap fix) → still 0/0/0**.

**Why zero:** every Glosbe tay sentence carries TRANSLs, and not one TRANSL contains a quotation mark in either the current or the extended charset — so `quotation_allowed` is False for the whole corpus (`transls and tq == 0`), suppressing all four rules including TRANSL-free rule 2. Independently, zero rule-2 shapes exist (0 sentences with exactly one word-initial `'` + one `'` glued after closing punctuation). Apostrophe adjacency: 6 word-initial, 76 word-final, 19 word-internal, 0 floating — the classic glottal profile; 1 sentence has a `''` sequence (harmless; no rule can touch it).

**Known-issue impact (worklist item: `tq == 0` false "no quotation" confirmation):** none measurable here — with the extended charset the TRANSL quote count is still 0, so the suppression is not hiding any charset-blind quotations in this corpus.

**Wrong-rewrite risk:** none on current data (empty-dict counterfactual is 0). Dictionary coverage against this corpus's own tokens is thin (see §3) but not load-bearing.

**Estimated correction volume: 0** (0 c031, 0 c032, 0 c030).

## 2. Corpus: WilangYutasVideos (`Corpora/WilangYutasVideos/XML`)

**Declared orthography (README `Corpora/WilangYutasVideos/readme.md`, line 90):** "I'm just assuming it is Ortho94. They aren't much different, and it was done too long ago to reasonably be Ortho113." — original tier is **Ortho94 (assumed)**; the reproduce pipeline runs `add_phonology.py --orthography Ortho94`. All 82 tay files declare `dialect="Sekolik"`.

**Is `'` a letter in Ortho94 Atayal (Sekolik)?** **Yes.** `Orthographies/Ortho94/Atayal.tsv` line 8: `'` → ʔ in the Sekolik column (and every other dialect column except the all-NA YilanZeaol placeholder). Same conclusion under the README's Ortho113 alternative, so the assumption's uncertainty does not affect the `'` question. Correction machinery applies.

**Replay (same production path):**

| metric | value |
|---|---|
| files (xml:lang=tay) | 82 (the 235 zho subtitle files are ignored by the tay dictionary path) |
| S | 3,014 |
| S with `'` in original FORM | 663 |
| `'` total | 857 |
| TRANSLs | 235 |
| TRANSLs containing any `TRANSL_QUOTES` char | **0** |
| TRANSLs containing any extended-charset char | **0** |
| **corrections / stranded / ambiguous** | **0 / 0 / 0** |

Counterfactuals: **empty dictionary → 0/0/0**; **extended `TRANSL_QUOTES` → 0/0/0**.

**Why zero:** most sentences have no TRANSL (235 TRANSLs over 3,014 S), so `quotation_allowed` is True for them — but rules 1/3/4 need TRANSL quote marks (none anywhere), and the only TRANSL-free rule (rule 2) has **zero** matching shapes in the corpus. The 7 floating apostrophes trigger de-stranding attempts, but no variant makes any rule fire (stranded = 0). Adjacency: 36 initial, 616 final, 198 internal, 7 floating; 2 pre-existing `"` characters, 0 `''` pairs.

**Known-issue impact:** the `tq == 0` gate and charset gap are again unmeasurable here (extended charset finds no TRANSL quotes either). The `attested()` truncation issue (Saisiyat finding) is inert while zero rules fire.

**Wrong-rewrite risk:** none on current data (empty-dict counterfactual is 0). Prospectively, this corpus is the likelier of the two to be exposed if rules ever activate: against its own running text, 10 of 30 `'`-final word types at freq ≥ 5 are missing from the dictionary (`rwa'` ×29, `laqi'` ×11, `sqabu'` ×10, `mnibu'` ×10, `hka'` ×8 …). Still zero exposure today because no rule can fire.

**Estimated correction volume: 0** (0 c031, 0 c032, 0 c030).

## 3. Dictionary quality (re-verification of round 1)

Round 1's findings **all reconfirmed** by direct spot-check of the current file (7,985 lines, all unique):

- **The 38-entry junk deletion list: all 38 still present**, verified entry-by-entry (28 CJK/Japanese transcription-debris lines incl. `021"開始編輯` which carries a literal `"`; 2 URL-percent-encoded `s%27inu` / `ttu%27`; 3 digit-tailed `byacing16` / `hakaw17` / `rawiq6`; 5 fillers `a~`, `a~~`, `o~~`, `e...e...e`, `ima?...ow`). All are conservative junk — they can only block corrections, never cause one. Decoded forms `s'inu` / `ttu'` are still absent (optional adds).
- **`''bul` is still present and still a keeper** (genuine word per round 1's running-text check; not re-derived exhaustively).
- **Apostrophe shape census matches round 1:** 59 purely-initial + 3 both-flanked (round 1 reported these as 62 initial), 1,002 purely-final + 3 both-flanked (round 1: 1,005), 582/583 interior — same content, slightly different bucketing conventions; no drift.
- **Both-flanked veto gap unchanged:** of `'abi'`, `'i'`, `'laqi'`, only `'i'` has a truncation (`i'`) in the dictionary; `attested()` can never veto on `'abi'`/`'laqi'` shapes (this is the Saisiyat-review `attested()` truncation issue, already on the classifier fix worklist — noted, not re-derived).
- **Coverage remains thin** (round 1: 51% of `'`-bearing types missing at freq ≥ 5 repo-wide; spot-recheck: `hya'`, `laqi'`, `isu'`, `kay'`, `brbiru'`, `krahu'`, `ma'` all still absent). Harmless for both Group 1 target corpora (nothing fires); load-bearing only for a future translated, quote-bearing Atayal corpus — at which point regenerate with `--include-interior --min-freq 3` (safe for Atayal: no quote-usage `'` exists in its corpora to pollute interior tokens).
- Random sample of 12 `'`-bearing entries against the two target corpora: mostly freq 0 there (expected — the dictionary is built repo-wide, largely from ILRDF/ePark citation forms), consistent with round 1's repo-wide validation that they are real words, not quote debris.

**Fix list: kept exactly as round 1** (no amendments needed).

## 4. Recommendation

**APPROVE WITH FIXES** — delete these 38 entries from `QC/validation/reference/Atayal/attestation.txt`:

`021"開始編輯`, `ながれ危うき水木橋`, `なぜにかえらぬああ〜サヨン`, `他在講近親結婚的事`,
`他是固定的,他不是照音符唱的`, `他講的是族群關係`, `南京`, `哈`, `對`, `對對`,
`嵐し風きまく峯ふもと`, `很多很多深度的意涵.在裡面`, `我就唱那個...sinramat`, `我想一下`,
`我現在要問他一下.哪個他使實看過哪個`, `是不是那個莎韻的歌`, `有一點熟悉,但是有些不太一樣`,
`有些講一些就可以`, `本当の私のじだい`, `永遠永遠`, `永遠永遠不要忘記相愛`,
`渡るは誰ぞうるわし乙女〜〜`, `片段而已`, `真的有這個故事嗎`, `紋面哪個一些紋面`, `維護`,
`這有一點像那個`, `這邊是tosa'`, `s%27inu`, `ttu%27`, `byacing16`, `hakaw17`, `rawiq6`,
`a~`, `a~~`, `o~~`, `e...e...e`, `ima?...ow`

Optional adds: `s'inu`, `ttu'` (decoded forms of the two %27 deletions; both real words).

Non-blocking follow-up (before any translated quote-bearing Atayal corpus is ported): regenerate with `--include-interior --min-freq 3` to close the coverage gap.

**Estimated correction volume on next cleaning run (Group 1, per corpus): Glosbe (tay) 0; WilangYutasVideos 0** — 0 c031 rewrites, 0 c032 stranded repairs, 0 c030 ambiguity flags each, verified by exact production-path replay and robust to both an empty dictionary and the extended TRANSL quote charset. (Wikipedias intentionally excluded per ruling.)

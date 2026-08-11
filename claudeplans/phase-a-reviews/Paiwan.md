# Attestation dictionary review — Paiwan (pwn) — REV 2

**Rerun of the Phase A review** (round 1: `claudeplans/phase-a-reviews/Paiwan.md`), under the
maintainer rulings in `claudeplans/phase-a-reviews/00-consolidated.md`:

1. Orthography is assessed **per corpus**, against the README-declared original-tier orthography —
   never per language. The round-1 key-question premise ("standard Paiwan writes the glottal as `q`")
   was wrong and came from the coordinator's prompt; round 1 itself already rebutted it.
2. **Wikipedias are out of scope for correction** (fiat: `'` assumed glottal for all non-Seediq wiki
   languages). `Corpora/Wikipedias/XML/Paiwan/` is therefore excluded from volume and risk here.
3. Classifier issues already on the fix worklist (cited, not re-derived): `TRANSL_QUOTES` lacks
   `《》〈〉` and curly singles `‘’`; `tq == 0` suppresses all conversion for a sentence
   (`QC/utilities/classify_quotes.py` line 486).

Scope of this rerun: the **only correction-live Group 1 target corpus for Paiwan is
`Corpora/FormosanBankGitBook`** (pwn). Read-only throughout; the replay below was a pure in-memory
call of `classify_quotes.apply_quote_corrections()` on extracted strings — no XML touched.

## 1. Per-corpus assessment — FormosanBankGitBook (pwn)

**Declared orthography (README, `Corpora/FormosanBankGitBook/README.md`):** Eastern Paiwan,
contributed by Ruan Xuan; step 4's notes state standardize.py "makes no changes, since the
transcription is **already the 113 Orthography**", and step 5 adds IPA with `--orthography Ortho113`.
So the original tier is declared **Ortho113**.

**Is `'` a letter in Ortho113 Paiwan?** Yes — confirmed directly:
`Orthographies/Ortho113/Paiwan.tsv` line 14 maps `'` → ʔ in **every** dialect column
(Eastern/Northern/Central/Southern/default); line 13 keeps `q` → q as the distinct uvular. `'` IS
the Ortho113 Paiwan glottal letter. The dictionary veto is therefore meaningful for this corpus,
and no skip-per-orthography rule applies.

**Corpus contents:** 6 XML files, **102 S elements**, all `xml:lang="pwn"`. Exactly **one
apostrophe** in the Paiwan tier (the ~25 other `'` characters in the files are XML declarations
`version='1.0'` and English TRANSL possessives/contractions — not Paiwan text).

**The one apostrophe**, `Contributing_to_FormosanBank.xml`, S id="25":

- original: `… mapaqulid tu neka pasaliw. nu pu'ui sun, maqati sun a ljemizaw tua su tjaucikel.`
- standard: `… no po'oi son, …` (the standard tier vowel-shifts u→o and keeps the `'`)
- TRANSLs: zho `我們會仔細檢查資料，確保沒有錯誤。如果您願意，您也可以審查語料。` /
  eng `We carefully check the data … If you wish, you can also review the data.`

Characterization: `pu'ui` ("wish/be willing", rendering 願意) is **word-internal, letter-flanked
(`L'L`)** — a canonical glottal-letter position, with an exactly matching apostrophe in the standard
tier. Neither TRANSL contains any quotation mark, so `tq == 0` and conversion is wholly suppressed;
independent of that, no `_quotation_targets` rule geometry matches a word-internal `'`. (`pu'ui` /
`po'oi` are not themselves in the attestation dictionary — only `ui` is — but no guard is ever
consulted because no rule reaches it.)

**Known classifier gaps are moot here:** the corpus contains zero `《》〈〉‘’` (and zero CJK corner
quotes) in any TRANSL, so the missing-charset issue cannot bite; the `tq == 0` suppression acts in
the safe direction (it can only block conversion, and the one `'` is genuinely a glottal).

**Read-only replay of the production entry point** (`apply_quote_corrections(ft, transls,
dictionary)` per `clean_xml.py`'s call, over all 102 sentences with the 5,234-entry dictionary):

```
sentences=102  apostrophes(original tier)=1  corrected=0  stranded=0  ambiguous=0
```

**Volume for this corpus: 0 rewrites, 0 stranded repairs, 0 ambiguity flags.** Arming the Paiwan
dictionary is a no-op on the only correction-live Group 1 Paiwan corpus.

## 2. Dictionary quality — round-1 findings re-verified (spot-check)

`QC/validation/reference/Paiwan/attestation.txt`: 5,234 entries, 0 duplicates, sorted,
all-lowercase. Every round-1 finding reproduced exactly:

| Finding | Round 1 | Rechecked | Status |
|---|---|---|---|
| CJK sentence entries (`我覺得怪怪的`, `我覺得是錯的`, lines 5233–5234) | 2 | 2 | confirmed — remove |
| Digit run-togethers (`1tacavilj`, `5cavilj`, `6aqiljas`, lines 86–88) | 3 | 3 | confirmed — remove |
| Punctuation-bearing (`'em~`, `aii…anga`, `sau!ljagayu`, lines 62/100/3826) | 3 | 3 | confirmed — remove |
| Slash-joined variant-list entries (inert: `/` not in PUNCT strip set) | 209 | 209 | confirmed — optional split |
| `q`/`'` doublet pairs among 85 `'`-initial entries (`'acang`/`qacang`, `'inaljan`/`qinaljan`, …) | 55 | 55 | confirmed — legitimate dialect doublets, keep |
| Apostrophe-bearing entries (85 initial / 46 final / 99 interior) | 217 | 217 | confirmed |
| Wikipedia apostrophe-token attestation coverage | 11% (819 occ / 360 types) | 11% (815 occ / 359 types; trivial tokenization delta) | confirmed |

**Fix list (unchanged from round 1 / consolidated):** delete the 8 junk entries (2 CJK + 3 digit +
3 punctuation). All are conservative-side hygiene — junk can only block a correction, never cause
one — so none are safety-blocking for arming.

## 3. Findings that only matter for FUTURE translated Paiwan corpora (later groups)

With Wikipedias out of scope and GitBook's exposure a single confirmed glottal, the following
round-1 concerns have **zero Group 1 effect** and transfer to later-group sweep turns:

- **11% apostrophe-token coverage**: the attestation guard in rules 1/3/4 fails open on most
  lenited-dialect and loan-name vocabulary (`ma'linpan`, `nan'ao`, `ren'ai`, `'u`, `ini'a`,
  `tatoba'`, `macau'`, …). Matters only when a TRANSL-bearing Paiwan corpus (ePark, NTU, ILRDF
  style) is cleaned while armed. Recommended then: regenerate the dictionary after each pwn port
  and dry-run per corpus first.
- **Slash-compound splitting** (209 entries): would add real attested vocabulary (`aqumaya`,
  `cekelj`, `valjaw`) that is currently unreachable by the guard — pure future-coverage gain.
- **`TRANSL_QUOTES` charset gap (`《》〈〉‘’`) and `tq == 0` suppression**: already on the classifier
  fix worklist (consolidated §"Classifier charset gap"); relevant once Chinese-TRANSL Paiwan
  corpora are swept. Both err toward missed corrections, never wrong rewrites.
- **Audit-mode `classify()` over-flags** (~11 wrong QUOTATION labels on Wikipedia Paiwan, round 1
  §3): keep `classify()` audit-only; only `apply_quote_corrections` may drive rewrites.
- **4 Ferrell-orthography entries** (`kiqiɫau` etc.): harmless leakage; can only match
  Ferrell-orthography original text, where a veto is fine.

## 4. Recommendation

The per-corpus question resolves cleanly: FormosanBankGitBook's original tier is declared Ortho113,
where `'` is the glottal letter (`Ortho113/Paiwan.tsv` line 14, all dialects), the corpus's single
apostrophe (`pu'ui`) is a confirmed word-internal glottal, and the production replay produces
nothing. The dictionary's 8 junk entries remain worth deleting as hygiene; everything else on the
list is future-group material.

**APPROVE WITH FIXES** — volume for Group 1 Paiwan: **FormosanBankGitBook (pwn): 0 rewrites,
0 stranded, 0 ambiguity flags** (Wikipedias/Paiwan excluded by fiat, out of correction scope).

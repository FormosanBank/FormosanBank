# Tsuchida Collection — tape-catalogue glosses

Built 2026-11-06 in the development repo `../Formosan-Tsuchida/`
(`~/Documents/Projects/Formosan/Formosan-Tsuchida/`) and ported here on
2026-11-06.

> **The licence is not yet confirmed in writing.** `@copyright="CC BY 4.0"`
> rests on a reading of the source site's licence statement, not on a statement
> about the catalogue itself. An enquiry is out to ILCAA. See "Rights" below
> before relying on this corpus or citing its licence.

This corpus is the lexical data embedded in the *catalogue* of the Shigeru
Tsuchida collection — not in the collection's recordings or notebooks, which are
not released. The project's public catalogue
([formosa.aa-ken.jp](https://formosa.aa-ken.jp/), and its linked Google Sheet)
describes each tape side in a Japanese content-summary column, and those
summaries quote the words the tape reads out, with Japanese glosses:

```
TSFC-AudioB-16A  Rukai  "RUKAI (Kocapongan) Vocabulary 1"
  summary : [aolo](頭)~[dilaŋ](さび), [moadiladilaŋ](サビ取っている)
  notebook: TSFC-PDF-106 p.4~40
```

363 `S` records across 20 files, in 11 languages, are extracted from those cells. The name is
deliberately narrow — `Tsuchida_TapeGlosses_*` — because this is one slice of
the collection, and the collection has a great deal more in it that is not
released. Further slices can be added to this repo under their own names.

## Languages and dialects

| File | Language | ISO | `dialect` | Catalogue's label | S |
| --- | --- | --- | --- | --- | --- |
| `Amis/…_Amis.xml` | Amis | `ami` | unknown | — | 4 |
| `Atayal/…_Atayal.xml` | Atayal | `tay` | unknown | — | 7 |
| `Atayal/…_Atayal_Bandai.xml` | Atayal | `tay` | unknown | Bandai | 6 |
| `Atayal/…_Atayal_Lonpia.xml` | Atayal | `tay` | unknown | Lonpia | 4 |
| `Atayal/…_Atayal_Shipazii.xml` | Atayal | `tay` | unknown | Shipazii | 5 |
| `Atayal/…_Atayal_Sikikun.xml` | Atayal | `tay` | unknown | Sikikun | 7 |
| `Atayal/…_Atayal_Sqoyaw.xml` | Atayal | `tay` | unknown | Sqoyaw | 14 |
| `Bunun/…_Bunun.xml` | Bunun | `bnn` | unknown | — | 6 |
| `Bunun/…_Bunun_Takivatan.xml` | Bunun | `bnn` | unknown | Takivatan | 8 |
| `Kanakanavu/…_Kanakanavu.xml` | Kanakanavu | `xnb` | Kanakanavu | — | 23 |
| `Kavalan/…_Kavalan.xml` | Kavalan | `ckv` | Kavalan | — | 75 |
| `Rukai/…_Rukai.xml` | Rukai | `dru` | unknown | — | 15 |
| `Rukai/…_Rukai_Mantauran.xml` | Rukai | `dru` | **Wanshan** | Mantauran | 17 |
| `Saaroa/…_Saaroa.xml` | Saaroa | `sxr` | Saaroa | — | 34 |
| `Saisiyat/…_Saisiyat.xml` | Saisiyat | `xsy` | Saisiyat | — | 34 |
| `Seediq/…_Seediq.xml` | Seediq | `trv` | unknown | — | 20 |
| `Seediq/…_Seediq_Soasal.xml` | Seediq | `trv` | unknown | Soasal | 24 |
| `Tsou/…_Tsou_Duhtu.xml` | Tsou | `tsu` | Tsou | **Duhtu** | 28 |
| `Yami/…_Yami.xml` | Yami | `tao` | Yami | — | 21 |
| `Yami/…_Yami_Imorod.xml` | Yami | `tao` | Yami | Imorod | 11 |
| | | | | **total** | **363** |

Single-dialect languages take the language name as the `dialect` value, as
every single-dialect language in `dialects.csv` does. Multi-dialect languages
get `dialect="unknown"` unless the catalogue's label maps to a `dialects.csv`
row **without a judgement call** — which happens exactly once: `dialects.csv`
lists `Rukai,Wanshan` with `OtherNames` `Mantauran`, so the catalogue's
"Mantauran" is published as `dialect="Wanshan"`.

Every other dialect label is kept in the file name and in each `S/@source`, but
is **not** written to `@dialect`, because none of them is in `dialects.csv`.

Two of them are worth singling out, because the single-dialect rule above
*overwrites* rather than merely omits them. Tsou and Yami each have no dialect
rows in `dialects.csv`, so they take the language name — which means
`Tsuchida_TapeGlosses_Tsou_Duhtu.xml` carries `dialect="Tsou"`, not
`dialect="unknown"`, and the Imorod file carries `dialect="Yami"`. The labels
survive only in the file name and in `S/@source`. Seven labels get
`dialect="unknown"`: Sqoyaw, Sikikun, Lonpia, Shipazii, Bandai, Soasal and
Takivatan.

| Catalogue label | Language | My reading, *not applied* |
| --- | --- | --- |
| Duhtu | Tsou | a real Tsou dialect; `dialects.csv` has no Tsou rows at all |
| Soasal | Seediq | unresolved against Duda / Tegudaya / DeluValley |
| Imorod | Yami | a village on Orchid Island, not a dialect row |
| Sqoyaw, Sikikun, Lonpia, Shipazii, Bandai | Atayal | village/subgroup names; Sqoyaw ≈ 環山 and Sikikun ≈ Skikun are Squliq-area, but `dialects.csv` has Sekolik/Zeaol/Wenshui/Wanda/FourSeasons/YilanZeaol |
| Takivatan | Bunun | Takivatan ≈ 卡社群 Kaqun is the standard equivalence, but it is still an equivalence |

**The Tsou Duhtu material is the notable one**: FormosanBank has no
Duhtu-dialect data at all, and 28 of these records are Duhtu.

Adding any of these to `dialects.csv` is a shared-file change needing the
maintainer's approval. Deferred by the maintainer, 2026-11-06: "Deal with when
data arrives."

## Source

The catalogue of the Tsuchida collection, published by the Information
Resources Center, ILCAA, Tokyo University of Foreign Studies:

- site: https://formosa.aa-ken.jp
- catalogue: `docs.google.com/spreadsheets/d/1zh3IUYoI7YQoXXnxLxrjo7za20bjbKExSShX8DMNAFg`
- tabs used: `TSFC音源リスト-カセットテープリスト` (280 sides) and
  `TSFC音源リスト-6mmテープリスト` (78 sides), downloaded 2026-11-06

All six tabs of the sheet as downloaded are bundled under
`CodeAndDocs/source/sheet_tabs/` (172 KB), so the build reproduces without
network access and without re-exporting the sheet. Only the two tape-list tabs
are read; the other four are kept because they are the catalogue's own
cross-reference material (`TSFCフィールドノート_カード目録` is the notebook/card
catalogue, `基礎語彙調査票とpdf対応_のコピー` is the basic-vocabulary
questionnaire index that the item numbers in `S/@source` point into).

### Rights — read this before porting

`@copyright` is set to `CC BY 4.0`. **That is an inference, not a statement.**
The site says:

> このサイトの文章の著作権は各執筆者に帰属します。ただしコンテンツはすべて
> クリエイティブ・コモンズ 表示 4.0 国際 (CC BY 4.0)の元に提供されています。
>
> "Copyright in the text of this site belongs to the respective authors.
> However, all content is provided under CC BY 4.0."

The second sentence says *all content* without restricting itself to text, and
the research group compiled this catalogue, so the group is the 執筆者 whose
grant applies. But the first sentence scopes the statement to "the text of this
site", and the spreadsheet is hosted on `docs.google.com`, not on the site. The
spreadsheet carries no licence notice of its own; all six tabs were checked.

Written confirmation has been requested from ILCAA (question 1 of the enquiry
to Asako Shiohara, `asako [at] aa.tufs.ac.jp`, cc the ILCAA desk
`ilcadj1 [at] aa.tufs.ac.jp`). **That reply has not arrived.** The corpus was
ported ahead of it on the maintainer's instruction, 2026-11-06 ("I want to open
the pull request"), so that review could begin; `@copyright` must be re-checked
against the reply when it comes.

Nothing in this repo touches the notebook scans or the recordings, whose rights
are a separate and less favourable question.

### Audio

None. The recordings these glosses were transcribed from are catalogued but not
released. Every record does carry its tape side in `S/@source`, so the data can
be aligned to audio later without re-deriving anything.

## Reproducing

```bash
python3 CodeAndDocs/extract_forms.py --tsv-dir CodeAndDocs/source/sheet_tabs \
    --audit CodeAndDocs/source/audited_glosses.tsv \
    --out CodeAndDocs/source/extracted_forms.tsv
python3 CodeAndDocs/generate_xml.py --forms CodeAndDocs/source/extracted_forms.tsv \
    --xml-dir XML
```

`CodeAndDocs/source/extracted_forms.tsv` holds **all 572** extracted forms,
including the ones not published, with the reason recoverable from its
`gloss_flag` and `record_type` columns. The XML is built only from rows that are
a glossed lexeme in a Formosan language.

`CodeAndDocs/source/audited_glosses.tsv` holds the **79 reviewed decisions**
that override the automatic rules — see "Every candidate was read against its
source cell" below. `extract_forms.py` requires it (`--audit`) and refuses to
run if any decision no longer lands on exactly one extracted row, so a change
in the source sheet cannot silently carry a stale decision.

| Extracted | 572 |
| --- | --- |
| no gloss at all in the source cell | 121 |
| non-Formosan language (Tagalog, Ibanag, Hausa) | 25 |
| classified `incipit` — the opening words of a song or narrative | 23 |
| gloss flagged `metadata_phrase` — prose about the recording | 18 |
| **excluded by the hand audit**, reason recorded per row | 12 |
| gloss flagged `unbalanced_paren_gloss` — the capture ran past a parenthesis | 10 |
| gloss flagged `long_bare_before` — over 5 characters in the ambiguous layout | 5 |
| **published** | **358 rows → 363 S** |

Three of the 23 unpublished openings are Tagalog or Ibanag, so **20 of them are
Formosan**; the other three are counted in the non-Formosan row as well and are
not double-counted in the published total.

## QC

Run from the FormosanBank repo root:

```bash
python QC/validation/validate_xml.py by_path --path Corpora/Tsuchida-TapeGlosses/XML
python QC/validation/validate_text.py by_path --path Corpora/Tsuchida-TapeGlosses/XML
python QC/count_tokens.py Corpora/Tsuchida-TapeGlosses
```

- `validate_xml.py`: **20 files, 363 SOFT, 0 HARD.** Every SOFT finding is
  `V014 count_missing_standard_form`, one per `S` — the expected and intended
  consequence of there being no `standard` tier (see below).
- `validate_text.py`: 20 files, **33 SOFT, 0 HARD**:
  - `V122 parens_slashes_anywhere` (25) — 21 are parentheses the catalogue
    itself wrote inside a gloss, e.g. `切る(木でも人でも)` "to cut (whether wood
    or a person)". **The other 4 are parentheses inside a FORM**, in two
    records where the source writes an optional segment that way:
    Yami `rangən wo(a) lobaŋbaŋ` and Atayal `pusi(y)a` "water". See "Known
    limits" 6.
  - `V136 mixed_script_confusables` (8) — Latin and IPA in one form
- `count_tokens.py`: **376 tokens** — Kavalan 75, Seediq 47, Atayal 44, Yami 37,
  Saaroa 36, Saisiyat 34, Rukai 33 (Wanshan 18 / unknown 15), Tsou 29,
  Kanakanavu 23, Bunun 14, Amis 4. Unchanged by the removal of the
  `standard` tier: `QC/corpus_counts.py` counts the standard sentence `FORM`
  with the original as fallback.

**Do not read the fall in `validate_text.py` SOFT findings — 195 for the first
build, 36 after the `standard` tier went, 33 now — as the data getting
cleaner.** It is not. `V116 non_ascii_in_form` skips `kindOf="original"` by design (the
original tier is source-faithful by policy and may carry annotation
characters), and `V136`/`V122` were each counting the same string twice
because the two FORM tiers were identical. Removing the duplicate tier removed
the findings that inspected it. The IPA characters `ʉ ŋ θ ː ʔ ə ɬ` are all
still in the data, exactly as before.

### There is no `standard` tier, on purpose

Maintainer's ruling, 2026-11-06: **"No standard until we've decided how to
standardize."**

Each `S` carries `FORM kindOf="original"`, `PHON kindOf="original"` and a
`TRANSL`, and nothing else. The `TRANSL` is `xml:lang="jpn"` on 353 records and
`xml:lang="eng"` on 10, because three tape sides were surveyed in English
rather than Japanese. The earlier build had a
`kindOf="standard"` FORM holding a byte-identical copy of the original, made
with the project's documented `standardize.py --copy` placeholder. That copy
asserted that Tsuchida's phonetic notation already *is* FormosanBank's common
standard orthography, which it is not — there is no conversion table for his
notation, so no real transliteration was possible.

The visible consequence is that `V014 count_missing_standard_form` (SOFT)
reports every one of the 363 `S` elements. That is the correct signal: the
corpus is genuinely missing a standard tier, and the validator should say so
until someone who knows these orthographies supplies a conversion table. The
placeholder copy can be re-created at any time with:

```bash
python QC/utilities/standardize.py --copy --corpora_path <path>
```

## Known limits

1. **There is no `standard` tier at all** (above), so every cross-corpus
   orthographic comparison will skip this corpus, and `V014` reports all 363
   records. Deliberate, per the maintainer's ruling.
2. **Glosses are Japanese, with ten exceptions.** `TRANSL/@xml:lang="jpn"` on
   353 records. The schema and the statistics already have a
   `jpn_transl_count` column, but no published corpus uses it, so this would be
   the bank's first Japanese-glossed material. Ten records are
   `xml:lang="eng"`: `TSFC-AudioA-21B` (Amis) and part of `TSFC-AudioA-18A`
   (Bunun) were surveyed in English, and four Kanakanavu and Tsou records carry
   English glosses the catalogue wrote in parentheses. There is no Chinese
   translation, and no English for the other 353.
3. **20 Formosan incipits are left unpublished** but are interesting in their own right:
   they are the opening words of recorded songs and narratives — 子守唄
   "lullaby", 猿とありくいの話 "the story of the monkey and the anteater", 太陽と月
   "sun and moon" — each tied to a tape side. They are truncated with `…` in the
   source and have no translation, so they are not lexemes and not sentences.
   `record_type=incipit` in the source TSV finds them; 23 rows carry that type
   with a usable gloss, of which 3 are Tagalog or Ibanag.
4. **Every candidate was read against its source cell; 79 decisions overrode
   the automatic rules.** The automatic rules are a candidate generator: they
   find bracketed forms and guess which neighbouring text is the gloss. On
   2026-11-06 all 194 candidates in the two ambiguous layouts (`gloss[form]`
   and `[form]gloss`), plus every row the filters had discarded, were read
   against their own source cells, and the remaining 136 explicit
   `[form](gloss)` and `「gloss」[form]` candidates were read as well — so every
   row in the corpus has been looked at. The decisions live in
   `CodeAndDocs/source/audited_glosses.tsv`, one row each with its reason.

   What they found, in four kinds:

   - **The filters were discarding rows that only needed trimming.** When a
     cell begins with survey metadata, the capture swallows it, and the real
     gloss is the last segment: `tunux ← 「フ」と対応。頭` is simply 頭 "head".
     39 rows had been thrown away whole; 28 of them are now published with the
     trimmed gloss.
   - **Two tape sides contain a language other than the one they are catalogued
     under.** `TSFC-AudioA-21A` is catalogued Atayal, and its cell reads
     `23m41s: Saisiyat女性話者` — from that point the material is Saisiyat.
     `TSFC-AudioB-55A` is catalogued Hausa and switches at 31m35s to a Formosan
     list. 11 records moved to Saisiyat as a result. The notebook
     cross-references corroborate this independently of the Japanese: the
     Saisiyat stretches of both sides point to `TSFC-PDF-119`/`120`/`121`, while
     the Atayal stretch of `21A` points to `TSFC-PDF-005`.
   - **Ten glosses are English, not Japanese**, and had been published tagged
     `xml:lang="jpn"`. `TSFC-AudioA-21B` says of itself 英語による語彙調査, "a
     vocabulary survey in English", and gives `head[fongoh]`, `face[laway]`,
     `neck[liər]`, `person[tamlau]` — the four records that put Amis back in
     this corpus.
   - **Eight published glosses were wrong and are corrected**, and three more
     were excluded. Two Tsou records had been given the voice labels `P.` and
     `Act.` as their meaning, where the cell
     `[reməta](P.), [remətə](Act.)(閉める)` makes 閉める "to close" the gloss of
     both. `poŋuo ← 〜星` had captured the *next* item and is 白髪 "white hair".
     `sii ← 」` had captured a closing quote mark and is 肉 "meat". One excluded
     row, `tariŋan`, had a book title for a gloss — the 「」 around it holds the
     name of a fish-and-plant field guide.

   **The residual risk is now the opposite of what it was.** The automatic
   filters are still in place and still discard 33 rows; 12 of those were
   checked and confirmed unrecoverable (no gloss exists in the source), and the
   rest are flagged prose. What has *not* been independently checked is my own
   reading: a second reader of Japanese would be checking 79 decisions and 363
   glosses, not sifting 572 candidates. See
   `../Tsuchida-survey/basecamp-japanese-review-todo.md`.

5. **No morpheme or word tier.** Each `S` is a single lexical item, so `W`/`M`
   segmentation would be one `W` per `S` and adds nothing.
6. **Two FORMs contain parentheses.** The Yami record
   `Tsuchida_TapeGlosses_Yami_TSFC-AudioB-45A_002` is published exactly as the
   catalogue writes it, `rangən wo(a) lobaŋbaŋ` "to cook flying fish", where
   `(a)` marks a segment Tsuchida recorded as optional. That is faithful to the
   source but puts a parenthesis in a FORM, which `V122` flags. The same thing
   happens in the Atayal record `pusi(y)a` "water" on `TSFC-AudioA-21A`, so
   4 of the 25 V122 findings are in a FORM rather than a gloss. The
   alternatives are to publish `rangən wo lobaŋbaŋ` and record the optionality
   in `@notes`, or to publish both readings. Left as the source has it, pending
   the maintainer.

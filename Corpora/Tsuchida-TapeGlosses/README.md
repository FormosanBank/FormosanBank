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

313 `S` records across 19 files, in 10 languages, are extracted from those cells. The name is
deliberately narrow — `Tsuchida_TapeGlosses_*` — because this is one slice of
the collection, and the collection has a great deal more in it that is not
released. Further slices can be added to this repo under their own names.

## Languages and dialects

| File | Language | ISO | `dialect` | Catalogue's label | S |
| --- | --- | --- | --- | --- | --- |
| `Atayal/…_Atayal.xml` | Atayal | `tay` | unknown | — | 10 |
| `Atayal/…_Atayal_Bandai.xml` | Atayal | `tay` | unknown | Bandai | 3 |
| `Atayal/…_Atayal_Lonpia.xml` | Atayal | `tay` | unknown | Lonpia | 4 |
| `Atayal/…_Atayal_Shipazii.xml` | Atayal | `tay` | unknown | Shipazii | 3 |
| `Atayal/…_Atayal_Sikikun.xml` | Atayal | `tay` | unknown | Sikikun | 4 |
| `Atayal/…_Atayal_Sqoyaw.xml` | Atayal | `tay` | unknown | Sqoyaw | 10 |
| `Bunun/…_Bunun.xml` | Bunun | `bnn` | unknown | — | 3 |
| `Bunun/…_Bunun_Takivatan.xml` | Bunun | `bnn` | unknown | Takivatan | 6 |
| `Kanakanavu/…_Kanakanavu.xml` | Kanakanavu | `xnb` | Kanakanavu | — | 20 |
| `Kavalan/…_Kavalan.xml` | Kavalan | `ckv` | Kavalan | — | 62 |
| `Rukai/…_Rukai.xml` | Rukai | `dru` | unknown | — | 15 |
| `Rukai/…_Rukai_Mantauran.xml` | Rukai | `dru` | **Wanshan** | Mantauran | 18 |
| `Saaroa/…_Saaroa.xml` | Saaroa | `sxr` | Saaroa | — | 34 |
| `Saisiyat/…_Saisiyat.xml` | Saisiyat | `xsy` | Saisiyat | — | 20 |
| `Seediq/…_Seediq.xml` | Seediq | `trv` | unknown | — | 19 |
| `Seediq/…_Seediq_Soasal.xml` | Seediq | `trv` | unknown | Soasal | 23 |
| `Tsou/…_Tsou_Duhtu.xml` | Tsou | `tsu` | Tsou | **Duhtu** | 27 |
| `Yami/…_Yami.xml` | Yami | `tao` | Yami | — | 21 |
| `Yami/…_Yami_Imorod.xml` | Yami | `tao` | Yami | Imorod | 11 |

Single-dialect languages take the language name as the `dialect` value, as
every single-dialect language in `dialects.csv` does. Multi-dialect languages
get `dialect="unknown"` unless the catalogue's label maps to a `dialects.csv`
row **without a judgement call** — which happens exactly once: `dialects.csv`
lists `Rukai,Wanshan` with `OtherNames` `Mantauran`, so the catalogue's
"Mantauran" is published as `dialect="Wanshan"`.

Every other dialect label is kept in the file name and in each `S/@source`, but
is **not** written to `@dialect`, because none of them is in `dialects.csv`:

| Catalogue label | Language | My reading, *not applied* |
| --- | --- | --- |
| Duhtu | Tsou | a real Tsou dialect; `dialects.csv` has no Tsou rows at all |
| Soasal | Seediq | unresolved against Duda / Tegudaya / DeluValley |
| Imorod | Yami | a village on Orchid Island, not a dialect row |
| Sqoyaw, Sikikun, Lonpia, Shipazii, Bandai | Atayal | village/subgroup names; Sqoyaw ≈ 環山 and Sikikun ≈ Skikun are Squliq-area, but `dialects.csv` has Sekolik/Zeaol/Wenshui/Wanda/FourSeasons/YilanZeaol |
| Takivatan | Bunun | Takivatan ≈ 卡社群 Kaqun is the standard equivalence, but it is still an equivalence |

**The Tsou Duhtu material is the notable one**: FormosanBank has no
Duhtu-dialect data at all, and 27 of these records are Duhtu.

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
    --out CodeAndDocs/source/extracted_forms.tsv
python3 CodeAndDocs/generate_xml.py --forms CodeAndDocs/source/extracted_forms.tsv \
    --xml-dir XML
```

`CodeAndDocs/source/extracted_forms.tsv` holds **all 572** extracted forms,
including the ones not published, with the reason recoverable from its
`gloss_flag` and `record_type` columns. The XML is built only from rows that are
a glossed lexeme in a Formosan language.

| Extracted | 572 |
| --- | --- |
| no Japanese gloss at all | 125 |
| gloss flagged `metadata_phrase` — prose about the recording | 46 |
| non-Formosan language (Tagalog, Ibanag, Hausa) | 28 |
| classified `incipit` — the opening words of a song or narrative | 23 |
| gloss flagged `long_bare_before` — over 5 characters in the ambiguous layout | 20 |
| gloss flagged `unbalanced_paren_gloss` — the capture ran past a parenthesis | 12 |
| gloss flagged `contains_timecode` | 10 |
| **published** | **308 rows → 313 S** |

## QC

Run from the FormosanBank repo root:

```bash
python QC/validation/validate_xml.py by_path --path Corpora/Tsuchida-TapeGlosses/XML
python QC/validation/validate_text.py by_path --path Corpora/Tsuchida-TapeGlosses/XML
python QC/count_tokens.py Corpora/Tsuchida-TapeGlosses
```

- `validate_xml.py`: **19 files, 313 SOFT, 0 HARD.** Every SOFT finding is
  `V014 count_missing_standard_form`, one per `S` — the expected and intended
  consequence of there being no `standard` tier (see below).
- `validate_text.py`: 19 files, **27 SOFT, 0 HARD**:
  - `V122 parens_slashes_anywhere` (19) — 17 are parentheses inside the
    Japanese gloss, e.g. `切る(木でも人でも)` "to cut (whether wood or a
    person)". **The other 2 are parentheses inside the FORM** of one Yami
    record, where the source writes an optional segment that way:
    `rangən wo(a) lobaŋbaŋ`. See "Known limits" 6.
  - `V136 mixed_script_confusables` (8) — Latin and IPA in one form
- `count_tokens.py`: **326 tokens** — Kavalan 62, Seediq 45, Yami 37,
  Saaroa 36, Atayal 35, Rukai 34 (Wanshan 19 / unknown 15), Tsou 28,
  Kanakanavu 20, Saisiyat 20, Bunun 9. Unchanged by the removal of the
  `standard` tier: `QC/corpus_counts.py` counts the standard sentence `FORM`
  with the original as fallback.

**Do not read the fall in `validate_text.py` SOFT findings — 195 for the first
build, 36 after the `standard` tier went, 27 now — as the data getting
cleaner.** It is not. `V116 non_ascii_in_form` skips `kindOf="original"` by design (the
original tier is source-faithful by policy and may carry annotation
characters), and `V136`/`V122` were each counting the same string twice
because the two FORM tiers were identical. Removing the duplicate tier removed
the findings that inspected it. The IPA characters `ʉ ŋ θ ː ʔ ə ɬ` are all
still in the data, exactly as before.

### There is no `standard` tier, on purpose

Maintainer's ruling, 2026-11-06: **"No standard until we've decided how to
standardize."**

Each `S` carries `FORM kindOf="original"`, `PHON kindOf="original"` and
`TRANSL xml:lang="jpn"`, and nothing else. The earlier build had a
`kindOf="standard"` FORM holding a byte-identical copy of the original, made
with the project's documented `standardize.py --copy` placeholder. That copy
asserted that Tsuchida's phonetic notation already *is* FormosanBank's common
standard orthography, which it is not — there is no conversion table for his
notation, so no real transliteration was possible.

The visible consequence is that `V014 count_missing_standard_form` (SOFT)
reports every one of the 313 `S` elements. That is the correct signal: the
corpus is genuinely missing a standard tier, and the validator should say so
until someone who knows these orthographies supplies a conversion table. The
placeholder copy can be re-created at any time with:

```bash
python QC/utilities/standardize.py --copy --corpora_path <path>
```

## Known limits

1. **There is no `standard` tier at all** (above), so every cross-corpus
   orthographic comparison will skip this corpus, and `V014` reports all 313
   records. Deliberate, per the maintainer's ruling.
2. **Japanese glosses.** `TRANSL/@xml:lang="jpn"`. The schema and the statistics
   already have a `jpn_transl_count` column, but no published corpus uses it, so
   this would be the bank's first Japanese-glossed material. There is no English
   or Chinese translation; adding one means translating 313 glosses.
3. **23 incipits are left unpublished** but are interesting in their own right:
   they are the opening words of recorded songs and narratives — 子守唄
   "lullaby", 猿とありくいの話 "the story of the monkey and the anteater", 太陽と月
   "sun and moon" — each tied to a tape side. They are truncated with `…` in the
   source and have no translation, so they are not lexemes and not sentences.
   `record_type=incipit` in the source TSV finds them.
4. **`bare_before` glosses are a heuristic, now measured rather than
   asserted.** The commonest layout in the source is `gloss[form]`, which
   cannot be told from surrounding prose by position alone. On 2026-11-06 every
   published `bare_before` row with a gloss of 6 or more characters — 19 of
   them — was read against its source cell. **About 10 were wrong**: section
   headings (`人, 親族名詞` "person, kinship nouns"), the interviewer's own
   question (`頭は何ていうんですか？頭`), and glosses captured across an ellipsis
   run so that they belonged to an earlier form (`背中, 腰...おび`, where the
   form `kapakthəl` goes with おび "sash"). The 4–5 character band was audited
   too and is clean (20 of 21 correct). So the flag threshold is now 5
   characters, not 14, and a gloss with an unmatched closing parenthesis is
   flagged outright.

   **What remains unmeasured** is the 1–5 character band: 160 published rows.
   These are single words — 頭 "head", 髪 "hair", ふけ "dandruff", ろうそく
   "candle" — and prose metadata is not 1–5 characters long, so the expected
   error rate is low, but it has not been checked row by row. A reviewer who
   reads Japanese should pass over the 313 published glosses; see
   the Japanese-review todo in `~/Documents/Projects/Formosan/Tsuchida-survey/`.
5. **No morpheme or word tier.** Each `S` is a single lexical item, so `W`/`M`
   segmentation would be one `W` per `S` and adds nothing.
6. **One FORM contains parentheses.** The Yami record
   `Tsuchida_TapeGlosses_Yami_TSFC-AudioB-45A_002` is published exactly as the
   catalogue writes it, `rangən wo(a) lobaŋbaŋ` "to cook flying fish", where
   `(a)` marks a segment Tsuchida recorded as optional. That is faithful to the
   source but puts a parenthesis in a FORM, which `V122` flags (2 of the 27
   V122 findings). The alternatives are to publish `rangən wo lobaŋbaŋ` and
   record the optionality in `@notes`, or to publish both readings. Left as the
   source has it, pending the maintainer.

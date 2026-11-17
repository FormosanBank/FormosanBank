# ePark errata lists (問題回報修改清冊): work in progress, 2026-10-18

For the **published** `Corpora/ePark` corpus, not for Formosan-ePark-Additions.

## What these are

The ePark resource page (https://klokah.iformosa.com.tw/resource, 教材檔案 tab) offers
"problem-report revision registers" for six sections. Each list records corrections that ePark's
language reviewers made to the **online** materials (revisions dated 2024-09-15, lists dated
2025-03-03). The lists' own preface:

> 修訂內容僅於族語E樂園網站線上教材進行更新，原四套教材…之紙本教材(含PDF檔)內容不變。
> (Revisions are applied only to the online materials; the printed books and PDFs are unchanged.)

`pdf/` holds the 105 lists for the four sections our ePark corpus has (file name `{section}_{did}.pdf`,
`did` = ePark dialect number, see `Corpora/ePark/CodeAndDocs/dialects.csv`):
conversation 31 (生活會話篇), culture 25 (文化篇), picture_story 21 (圖畫故事篇), read_write 28 (閱讀書寫篇).
Lists for 字母篇 (25) and 歌謠篇 (16) exist too, but we have neither section.

## Maintainer rulings

- 2026-10-18, round-1 artifact, errata card: chose **"Apply to ePark"**.
- 2026-10-18, round-2 artifact, errata note: *"This edits the original tier. Only show me matches that
  aren't trivially easy to match."*
- Route (round-3 card 2) is still **open**: wait for the old site and diff against the corrected online
  text, or fix the PDF route first, or both.

## Files

| file | what |
|---|---|
| `errata_all.tsv` | every correction row extracted from the PDFs' tables with pdfplumber (2,154 rows) |
| `errata_all_k2.tsv` | same + `kind2`: formosan_text 1,741 · vocabulary 85 · zh_translation 64 · audio 9 · no_change 3 · other_fix 7 · unclassified 245 |
| `errata_matched2.tsv` | each correction (2,403 units; one row can fix several sentences) located in our XML; columns `cls`, `located_by`, `flags`, `target_sid`, `target_text`, `proposed` |
| `scripts/extract_errata.py` | PDFs → `errata_all.tsv` |
| `scripts/classify_errata.py` | → `errata_all_k2.tsv` (NFKC-folds Kangxi-radical lookalikes such as ⽣→生 used in some lists) |
| `scripts/match_errata2.py` | → `errata_matched2.tsv`. Patched after the run that produced the TSV: fuzzy-only matches now get a `proposed` text |

## How corrections are located (works; checked by hand on two)

The lists cite lesson + sentence (第N課 第M句) or vocabulary item (單字 … (n)). Our `AUDIO/@url` values carry
the same numbers:

- conversation: `…/con_data/sound/{did}/sentence/{did}c{L}s{n}.mp3` and `…/word/{did}c{L}w{n}.mp3`
- culture / read_write vocabulary: `…/{cu,rd}_data/audio/{did}/{did}_{L}_V{n}.mp3`
- lesson texts (culture, read_write, picture story): `…/text/sound/{textId}/{sid}.mp3`; consecutive
  textId groups, in order, are lessons 1, 2, 3, …

Checks: Southern Amis conversation lesson 1 sentence 8 = our S 7 `Haelis, ka'urunan tu.` (errata: `kaurunan`);
culture lesson 1 sentence 12 = our S 11 `Na itiraay i Palidaw ku aru', …` (errata: `Naitiraay`).

## Why nothing has been applied

Located counts: trivial (located, similar) 1,023 · fuzzy-only 52 · clean phrase-level fixes 68 · already
correct 161 · not a text edit 76 · **hard 1,023** (742 Toda Seediq, 88 Thao, 193 others). A random sample of
20 "easy" edits (seed 20261018) showed:

1. heavy rewrites counted as easy because the location is certain (Toda);
2. conflicts — two corrections to one sentence with different text (Toda lesson 19);
3. PDF table-cell line wraps insert spaces or truncate words (`kiyadremedremako` → `kiyadremedre mako`;
   `pongan` → `ngan`) — text alone can't tell a wrap from a real correction;
4. fuzzy-only matches had no proposed text (fixed since).

Recommended route (not yet ruled): once web.klokah.tw is back, fetch the corrected online lessons and diff
them against our XML, using these lists only as the index of what changed.

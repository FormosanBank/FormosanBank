# Source decisions — Tsuchida tape-catalogue glosses

Built 2026-11-06. Every decision below is mine unless marked as a maintainer
ruling; nothing here has been reviewed.

## What the source cells look like

The content-summary column of each tape-list row mixes four gloss patterns with
free Japanese prose about the recording. All four, as they actually appear:

```
paren_after    [kodaːli](昼食)                      form, then gloss in parentheses
bare_after     [oaθiabə]切る(木でも人でも)            form, then gloss with no parentheses
corner_before  154「猟に行く, 狩にいく」[muruatsuka]   item no., gloss in 「」, then form
bare_before    頭[taʔoeloeh]                        gloss, then form
```

`paren_after` glosses nest: `[tsəːtsəvəkə](小さいやつ(里芋の収穫など))`, so the
closing parenthesis must be matched by depth, not by the first `)`.

## Four bugs found by reading the output against the source

The first pass was wrong in four ways. Recording them because each says
something about the data, and because the first three were invisible in
aggregate counts.

1. **Truncated nested glosses.** Stopping at the first `)` cut
   `小さいやつ(里芋の収穫など)` to `小さいやつ(里芋の収穫など`. Fixed with
   `balanced_paren()`.
2. **`bare_after` not handled.** Requiring parentheses lost the gloss of
   `[oaθiabə]切る(木でも人でも)` entirely.
3. **`corner_before` mis-captured.** `154「猟に行く, 狩にいく」[muruatsuka]` gave
   the fragment `狩にいく」`, with a stray bracket, because the `「…」` span was
   not matched. Fixing it also surfaced the **basic-vocabulary item numbers**
   (7 rows have one), which tie a recorded word to its position in the
   questionnaire that tab 4 of the sheet indexes.
4. **Language forward-filled across tapes.** Language is stated once per tape,
   on its A side, so blank rows inherit it — but only within that tape. Filling
   across tape boundaries attributed six tapes' material to the wrong language.
   Now scoped to the tape number parsed out of the side ID.

## Three classes of row, and why only one is published

`record_type` distinguishes them:

- **`lexeme`** — a form with a meaning. Published.
- **`incipit`** — the opening words of a recorded song or narrative, where the
  "gloss" is a genre label rather than a meaning: `歌` "song", `子守唄`
  "lullaby", `猿とありくいの話` "the story of the monkey and the anteater". The
  form is truncated with `…`. Not published: it is neither a lexeme nor a
  sentence, and publishing it in a wordlist would misrepresent both tiers.
  Classified by: form ends in an ellipsis, or has three or more tokens (but
  not when the source itself bracketed the form and parenthesised its gloss —
  see below), or the gloss matches
  `歌(?!う)|唄|テキスト|話$|話\)|モノローグ|声|ハーモニー|掛け声|語り`.
- **flagged gloss** — the "gloss" is prose about the recording. Not published.
  Caught by `音声|話者|調査|対応|繰り返|入り混|会話|歌と|最後|途中|以下|不明|finish|END|TOP`,
  by an embedded timecode, or by a `bare_before` gloss over 14 characters.
  Real examples:

```
malakak    → 単語を2回ずつ発音していく音声      "audio where each word is said twice"
macuka…    → 女性話者                          "female speaker"
paŋəh      → と対応) 14m32s:語彙調査(男性,英語) finish
```

### Three records this classifier wrongly excluded

Found 2026-11-06 by reading all 32 excluded rows against their source cells,
after the maintainer asked to see them. All three are genuine lexemes and are
now published; the corpus went from 331 to 334 `S`, and the excluded incipits
from 32 to 29.

```
Kavalan  TSFC-AudioB-112A  sazzai  歌う  "to sing"
  source cell: 鉄[valis]...枯れる[maisun], 歌う[sazzai],捨てる[muani],濁る[mətədo]
  why wrong  : the genre pattern 歌 "song" also matches 歌う "to sing". The
               cell is a plain verb list -- wither, discard, become turbid.
  fix        : 歌 -> 歌(?!う). Checked against all 572 glosses: 歌う was the
               only false match the whole genre pattern produced.

Yami  TSFC-AudioB-45A  rangən wo(a) lobaŋbaŋ  飛び魚をたく  "to cook flying fish"
  source cell: [ogo](頭)...[rangən wo(a) lobaŋbaŋ](飛び魚をたく)
Yami  TSFC-AudioB-45B  mangoto so kayo  切った薪を乾かす  "to dry cut firewood"
  source cell: 0m0s~36m47s: [mangoto so kayo](切った薪を乾かす)...
  why wrong  : excluded by the three-or-more-tokens rule, which exists to catch
               unmarked prose. But the source bracketed the form and
               parenthesised the gloss, which is an explicit form-and-meaning
               pair -- these are phrasal lexemes, not song openings.
  fix        : the token rule no longer fires on the `paren_after` pattern.
               Those were the only two rows the token rule caught on its own.
```

The first Yami record puts parentheses inside a FORM (`wo(a)`, an optional
segment). `V122` flags that four times. Published as the source has it; see
README "Known limits" 6.

### The `bare_before` weak point, measured

`gloss[form]` cannot be told from surrounding prose by position alone, so this
filter is a heuristic. On 2026-11-06 it was measured rather than asserted:
every published `bare_before` row with a gloss of 6+ characters (19 rows) was
read against its source cell, and **about 10 were wrong**. Verbatim:

```
Ami      tamlau            <- 人, 親族名詞            a section heading in the
  cell: ... 17m15s: 用例 ... 18m01s: 人, 親族名詞      recording, not a meaning
Tayal    tunuh             <- 頭は何ていうんですか？頭   the interviewer's question
  cell: 頭は何ていうんですか？頭 [tunuh], ...            plus the real gloss 頭
Saisiyat kapakthəl         <- 背中, 腰...おび           an ellipsis run; the form
  cell: 臍の緒[pudaʔan, kaldipudaʔan],背中, 腰...おび[kapakthəl]   goes with おび
Atayal   spmumuʔ           <- 生きている...結ぶ          same; goes with 結ぶ
Saaroa   muaaŋiaŋilapasu   <- 横に歩く),                belongs to the PREVIOUS
  cell: [muaaŋiaŋila](横に歩く), [muaaŋiaŋilapasu],      form; this one has none
Bunun    tasa              <- 数詞, 日本語なし)          explicit metadata: the
  cell: 49m30s: (数詞, 日本語なし) [tasa] [dusa] [tao]   numerals have no Japanese
```

The 4-5 character band was audited too and is clean -- 20 of 21 correct
(`ろうそく` "candle", `ハンノキ` "alder", `腐っている` "rotten", `横目で見る`
"look sideways"); the one failure was `pasamoŋa <- 深い),`, caught by the
parenthesis rule.

**Two filters added as a result**, replacing the old `len(gloss) > 14`:

1. `unbalanced_paren_gloss` -- more closing than opening parentheses in the
   gloss, which means the capture ran past a boundary. 12 rows.
2. `long_bare_before` at **more than 5** characters, not 14. 20 rows.

Published went from 329 rows / 334 S to 308 rows / 313 S, and the Amis file
disappeared entirely: its only record was `tamlau <- 人, 親族名詞` above. This
discards roughly 8 correct records along with the bad ones, which is the
intended trade -- a wrong gloss is worse than a missing one, and every
excluded row stays in `extracted_forms.tsv` with its reason in `gloss_flag`.

**Still unmeasured:** the 1-5 character band, 160 published rows. Single words
like 頭 "head" and ふけ "dandruff"; prose metadata is not 1-5 characters long,
so the expected error rate is low, but no row-by-row check has been done.

## Two forms against one gloss

Four cells list two forms for one Japanese gloss, separated by `,` or `~`:

```
Kavalan   bi, bugas              米          "rice"
Kavalan   qulas~qunnah           はげ         "bald"
Saisiyat  pudaʔan, kaldipudaʔan  臍の緒       "umbilical cord"
Saisiyat  tonoʔ, ...a...adoŋ     脳          "brain"
Seediq    səburaw, sbəŋox        腐っている    "rotten"
```

First attempt wrote the second form as a POL-028 variant
(`kindOf="original" ver="alt"`) with a POL-013 `[x|y]` PHON. **`V150
alternate_FORM_low_overlap` rejected all of them, correctly**: `bi` and `bugas`
are two different Kavalan words for rice, not two spellings of one word. A
variant FORM asserts a relationship the data does not support.

Now each form gets its own `S` sharing the gloss, with ids suffixed `a`/`b` and
`S/@source` recording that the cell listed them together. `validate_xml` is
clean after this change.

## Dialect

See the README table. The rule applied: write `@dialect` only where the
catalogue's label maps to a `dialects.csv` row with no judgement call. That is
true exactly once — `dialects.csv` lists `Rukai,Wanshan` with `OtherNames`
`Mantauran` — so "Mantauran" becomes `dialect="Wanshan"` and everything else
(Duhtu, Soasal, Imorod, Sqoyaw, Sikikun, Lonpia, Shipazii, Bandai, Takivatan)
stays `unknown` with the label preserved in the file name and in `@source`.

Nothing is lost by this: the catalogue's own string is in every `S/@source`, so
a later ruling can be applied by regenerating.

## Tier assignments

| Tier | Content | Why |
| --- | --- | --- |
| `FORM kindOf="original"` | the form as the catalogue gives it | fidelity to the source |
| `PHON kindOf="original"` | the form again | the source string *is* a phonetic transcription, so it belongs on PHON as much as on FORM |
| `TRANSL xml:lang="jpn"` | the Japanese gloss | the gloss language is Japanese; no English or Chinese exists |

**No `standard` tier.** Maintainer's ruling, 2026-11-06: "No standard until
we've decided how to standardize." The first build had one, holding a
byte-identical copy of the original via `standardize.py --copy`. It is gone.
`V014 count_missing_standard_form` (SOFT) now reports all 313 `S` elements,
which is the intended signal.

One consequence to read carefully: `validate_text.py` SOFT findings fell from
195 to 36 when the tier went (and to 27 after the gloss-filter tightening
below), and **that is not the data improving**. `V116 non_ascii_in_form` skips
`kindOf="original"` by policy, and `V136`/`V122` were double-counting one
string across two identical tiers. Nothing changed in the transcriptions.

Putting the same string on `FORM` and `PHON` is deliberate and is the honest
reading: Tsuchida wrote IPA, and the bank has no separate orthographic form to
put on `FORM`. Flagging it because a reviewer may prefer `PHON` only.

## Provenance kept on every record

`S/@source` carries, in order: the tape side ID, the catalogue's own language
string, the catalogue's dialect label where there is one, the cross-referenced
notebook IDs with their page ranges, the basic-vocabulary item number where
there is one, and — for split cells — the original combined string. Example:

```
tape side TSFC-AudioB-57A; catalogued as "Tsou"; catalogued dialect "Duhtu";
notebook TSFC-PDF-021; TSFC-PDF-137; TSFC-PDF-138 (TSFC-PDF-021 語彙p.27~48,
ノートに音声の何分何秒あたりかメモあり; …)
```

This is what makes the corpus alignable to the recordings if they are ever
released, without re-deriving anything from the sheet.

## Open for the maintainer

1. **Rights.** `@copyright="CC BY 4.0"` is an inference about the scope of the
   site's licence statement. Confirmation requested from ILCAA. Do not port
   before the reply.
2. **The `standard` tier** — settled by the maintainer 2026-11-06: there is
   none until a standardization scheme is decided.
3. **Dialect rows** for Tsou Duhtu and the Atayal/Seediq/Yami village labels —
   deferred by the maintainer 2026-11-06 ("Deal with when data arrives").
4. **Whether `PHON` and `FORM` should hold the same string.**
5. **Whether the 29 song and narrative incipits** should become their own
   small corpus rather than being dropped.
7. **The parenthesised Yami FORM** `rangən wo(a) lobaŋbaŋ` (above).
6. **A Japanese-reading review** of the published 313, for the 1-5 character
   `bare_before` residue (above).

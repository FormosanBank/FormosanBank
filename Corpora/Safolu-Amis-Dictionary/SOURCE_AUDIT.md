# Safolu source review

**Development status: needs remediation.** Current shared orthography and
unresolved source readings block final regeneration and QC. This document
records durable source decisions, not a ready-to-port verdict.

The [source manifest](CodeAndDocs/source_manifest.json) fixes the 49,419
example fields from `g0v/amis-moedict/docs/s`. The snapshot is a lossless
inventory of those fields and their locators, including the excluded fields.
Moedict link markup and U+FFF9/U+FFFA/U+FFFB delimiters are representation
syntax, not Amis spelling. Source originals, translations and correction
evidence are retained separately from derived tiers.

## Repairs

- Retain different meanings with the same FORM. The previous local merger
  removed 261 records; 143 of those pairs have different current shared
  translation keys. The parser now preserves all source occurrences and lets
  shared dedup perform the reviewed final step (POL-022/POL-046).
- Keep the Japanese quotation in source field 35031, confirmed on the
  [publisher's pangcah page](https://new-amis.moedict.tw/terms/pangcah).
  A Han character in an Amis sentence is not automatically a field boundary.
- Restore the Chinese subject `Panay` in S14824. The older `dict/10-M.txt`,
  lines 10006-10009, and SQLite `raw_contents` row 10717 in
  `miaoski/amis-safolu@f512d5ba0d08f81b26093a9b7b4a85acac760a30` preserve
  the sequence `Mangalay ci Panay a malakangkofo. Panay. 想當護士。`.
  The first sentence is Amis; the following name belongs with the translation.
- Recover the two lexical examples and explicit pronunciations in the
  [e entry](https://new-amis.moedict.tw/terms/e); resolve the two explicit
  pronunciation examples in [i](https://new-amis.moedict.tw/terms/i) as
  original-tier `ver="alt"` FORMs (POL-028).
- Preserve the second lexeme `samado` in S32641 as a separate reading.
  SQLite `raw_contents` row 22537 and the current pinned source both print
  `karapanay（samado 稗子）`. The previous correction removed this source reading.
- Resolve the complete alternative constructions in S00036, S00621 and
  S00689, and the optional words in S11242, into separate aligned S records.
- Keep the explicit lexical alternatives in S01889, S29086 and S42957 as
  separate S. S42869 pairs fail/orad with the source's Chinese wind/rain
  readings, preserving the current source spellings. Dictionary entries and
  historical raw text support these four decisions (POL-027/028).
- Preserve three further lexical pairs in S07828 (finacadan/tamdaw),
  S29374 (cokowi/parad) and S39092 ('irang/remes). Their example fields and
  separate source dictionary entries support both readings and the unchanged
  Chinese translations; these are not pronunciation variants (POL-027/028).
- Restore the published base IDs S41674 and S42031 for the first source
  readings. Their new companions use `-opt` and `-opt3`; the 71 already
  published underscore-suffixed IDs from other fields remain unchanged.

Each revised decision in
[safolu_source_overrides.json](CodeAndDocs/safolu_source_overrides.json)
asserts the exact original source fields before applying. All prior correction
records remain, including the unresolved published correction at S37193.

## Remaining evidence

Forty-two parenthesis/slash cases remain unresolved; they are preserved, not
treated as accepted merely because old validators called them SOFT. Field 35128
contains unexplained `久` even on the current publisher's page. S37193's
completed Chinese translation is already published but lacks a verified source
witness; do not replace it with another inferred translation.

The upstream SQLite raw text and 22 older TXT files were inspected for targeted
comparisons. They are historical witnesses: newer authorial corrections still
take precedence. The current source covers examples added after those witnesses,
so absence there is not evidence that a current example is spurious.

The previous ledgers under `data/formosanbank_audit/` describe the retained
49,179-record XML and are historical evidence only. Revised source parsing
produces 49,455 records before shared dedup, plus 20 excluded fields; this is
not a prediction of the final corpus count. Runtime reports remain external.

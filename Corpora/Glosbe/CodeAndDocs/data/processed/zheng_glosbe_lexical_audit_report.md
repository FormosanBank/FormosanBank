# Zheng Cross-Source Lexical Audit

Generated: 2026-08-03T00:50:56Z

Trusted source: `../Formosan-Zheng-ACL-2024`

Policy:

- require Zheng source-form attestation for Glosbe lexical XML: True
- use curated Zheng Chinese gloss sense evidence for English lexical targets: True
- merge multiple Zheng-supported Glosbe English targets into a single lexical XML entry: True
- no machine translation is used; Zheng Chinese glosses are used only as source-form/sense evidence in sidecars.

## What This Audit Shows

This audit covers Glosbe dictionary/headword rows only. It does not filter sentence-level translation-memory data. Each CSV row records one Glosbe source-target candidate, the Zheng evidence consulted, the inclusion decision, and the exact reason code. An exclusion means the row did not meet this corpus's conservative corroboration threshold; it does not prove that the Glosbe entry is wrong.

The group review CSV combines every Glosbe target found for one source form so reviewers can see which senses were retained, merged, or excluded together.

## Decision Rules

- Basic structural problems such as empty text, invalid notes, source-target identity, or the wrong writing system are excluded before the Zheng comparison.
- `source_not_attested_in_zheng_dictionary`: Zheng has no matching source form. This is missing corroboration, not evidence that Glosbe is incorrect.
- `target_not_supported_by_zheng_gloss`: Zheng attests the source form, but its Chinese gloss evidence maps to a different English sense.
- `zheng_sense_attested_*`: the source and English sense are supported by the curated Zheng gloss evidence. Multiple supported targets are merged.
- `single_glosbe_target_and_zheng_source_attested_unmapped_sense`: the source form is attested and Glosbe has one target, but no curated Chinese-to-English sense rule applies. The row is kept rather than guessed about.

## Main CSV Columns

- `source_phrase_clean` / `target_phrase_clean`: the Glosbe lexical candidate under review.
- `action`: `keep_in_xml` or `exclude_from_xml`.
- `reason`: the rule that produced the action.
- `zheng_source_found`: whether the normalized source form occurs in the Zheng dictionary.
- `zheng_chinese_glosses`: all Zheng Chinese glosses used as corroborating evidence.
- `glosbe_targets_for_source`: all Glosbe English targets grouped under the same source form.
- `sense_evidence`: the specific curated Zheng gloss fragments that mapped to an English target.
- `xml_record_id` / `xml_target_text`: the emitted merged lexical entry when the row was retained.
- `source_url` / `raw_path`: provenance back to the scraped Glosbe material.

## Totals

- audited Glosbe lexical rows: 1305
- row-level kept/supported: 729
- row-level excluded: 576
- lexical XML entries emitted after target merging: 667

## Reasons

- source_not_attested_in_zheng_dictionary: 542
- single_glosbe_target_and_zheng_source_attested_unmapped_sense: 519
- zheng_sense_attested_multi_target_merged: 111
- zheng_sense_attested_single_target: 81
- target_not_supported_by_zheng_gloss: 34
- zheng_sense_attested_target_subset: 18

## Pair Counts

- ami,en exclude_from_xml: 22
- ami,en keep_in_xml: 42
- tay,en exclude_from_xml: 357
- tay,en keep_in_xml: 227
- trv,en exclude_from_xml: 120
- trv,en keep_in_xml: 23
- xsy,en exclude_from_xml: 77
- xsy,en keep_in_xml: 437

## Lexical XML Entry Counts

- ami,en: 27
- tay,en: 206
- trv,en: 19
- xsy,en: 415

## Rescued / Merged Examples

- ami,en `Kawas` => `God` kept as `God; ghost`; Zheng glosses: 上帝、神、鬼; evidence: 上帝; 神; 鬼
- ami,en `Kawas` => `ghost` kept as `God; ghost`; Zheng glosses: 上帝、神、鬼; evidence: 上帝; 神; 鬼
- ami,en `ciira` => `he` kept as `he; him`; Zheng glosses: 他; evidence: 他
- ami,en `ciira` => `him` kept as `he; him`; Zheng glosses: 他; evidence: 他
- ami,en `ina` => `mom` kept as `mom; mother; mum`; Zheng glosses: 媽媽; evidence: 媽媽
- ami,en `ina` => `mother` kept as `mom; mother; mum`; Zheng glosses: 媽媽; evidence: 媽媽
- ami,en `ina` => `mum` kept as `mom; mother; mum`; Zheng glosses: 媽媽; evidence: 媽媽
- ami,en `kaka` => `brother` kept as `brother; older brother`; Zheng glosses: 哥; evidence: 哥
- ami,en `kaka` => `older brother` kept as `brother; older brother`; Zheng glosses: 哥; evidence: 哥
- ami,en `kako` => `I` kept as `I; me`; Zheng glosses: 我; evidence: 我
- ami,en `kako` => `me` kept as `I; me`; Zheng glosses: 我; evidence: 我
- ami,en `kami` => `we` kept as `we`; Zheng glosses: 我們(排除式; 手紙; evidence: 我; 我們; 手
- ami,en `miheca` => `age` kept as `age; year`; Zheng glosses: 年; evidence: 年
- ami,en `miheca` => `year` kept as `age; year`; Zheng glosses: 年; evidence: 年
- ami,en `nira` => `his` kept as `his`; Zheng glosses: 他的; evidence: 他; 他的
- ami,en `roma` => `another` kept as `another; different; other`; Zheng glosses: 另外; evidence: 另外
- ami,en `roma` => `different` kept as `another; different; other`; Zheng glosses: 另外; evidence: 另外
- ami,en `roma` => `other` kept as `another; different; other`; Zheng glosses: 另外; evidence: 另外
- ami,en `salikaka` => `siblings` kept as `siblings; sister`; Zheng glosses: 兄弟姐妹; evidence: 兄弟姐妹
- ami,en `salikaka` => `sister` kept as `siblings; sister`; Zheng glosses: 兄弟姐妹; evidence: 兄弟姐妹
- ami,en `sowal` => `language` kept as `language; say; state`; Zheng glosses: 話語; evidence: 話語; 話
- ami,en `sowal` => `say` kept as `language; say; state`; Zheng glosses: 話語; evidence: 話語; 話
- ami,en `sowal` => `state` kept as `language; say; state`; Zheng glosses: 話語; evidence: 話語; 話
- ami,en `tamdaw` => `man` kept as `man`; Zheng glosses: 人; evidence: 人
- ami,en `wawa` => `child` kept as `child; children; kids; offspring`; Zheng glosses: 孩子; evidence: 孩子
- ami,en `wawa` => `children` kept as `child; children; kids; offspring`; Zheng glosses: 孩子; evidence: 孩子
- ami,en `wawa` => `kids` kept as `child; children; kids; offspring`; Zheng glosses: 孩子; evidence: 孩子
- ami,en `wawa` => `offspring` kept as `child; children; kids; offspring`; Zheng glosses: 孩子; evidence: 孩子
- tay,en `blaq` => `good` kept as `good; well`; Zheng glosses: 好; evidence: 好
- tay,en `blaq` => `well` kept as `good; well`; Zheng glosses: 好; evidence: 好

## Excluded Examples

- ami,en `Cudad` => `book`: source_not_attested_in_zheng_dictionary; Zheng glosses: none; Glosbe targets: book; evidence: none
- ami,en `Kawas` => `heaven`: target_not_supported_by_zheng_gloss; Zheng glosses: 上帝、神、鬼; Glosbe targets: ghost; god; heaven; evidence: 上帝; 神; 鬼
- ami,en `Yihofa` => `Jehovah`: source_not_attested_in_zheng_dictionary; Zheng glosses: none; Glosbe targets: jehovah; evidence: none
- ami,en `ciira` => `she`: target_not_supported_by_zheng_gloss; Zheng glosses: 他; Glosbe targets: he; him; she; evidence: 他
- ami,en `cingra` => `create`: source_not_attested_in_zheng_dictionary; Zheng glosses: none; Glosbe targets: create; he; evidence: none
- ami,en `cingra` => `he`: source_not_attested_in_zheng_dictionary; Zheng glosses: none; Glosbe targets: create; he; evidence: none
- ami,en `cowa` => `little`: target_not_supported_by_zheng_gloss; Zheng glosses: 哪裡; Glosbe targets: little; evidence: 哪裡
- ami,en `futing` => `fish`: source_not_attested_in_zheng_dictionary; Zheng glosses: none; Glosbe targets: fish; evidence: none
- ami,en `kaka` => `older sibling`: target_not_supported_by_zheng_gloss; Zheng glosses: 哥; Glosbe targets: brother; older brother; older sibling; older sister; evidence: 哥
- ami,en `kaka` => `older sister`: target_not_supported_by_zheng_gloss; Zheng glosses: 哥; Glosbe targets: brother; older brother; older sibling; older sister; evidence: 哥
- ami,en `kami` => `go`: target_not_supported_by_zheng_gloss; Zheng glosses: 我們(排除式; 手紙; Glosbe targets: go; we; evidence: 我; 我們; 手
- ami,en `kawra` => `but`: source_not_attested_in_zheng_dictionary; Zheng glosses: none; Glosbe targets: but; evidence: none
- ami,en `ko` => `do`: target_not_supported_by_zheng_gloss; Zheng glosses: 格位標記（主格）; Glosbe targets: do; from; evidence: 格位標記; 主格
- ami,en `ko` => `from`: target_not_supported_by_zheng_gloss; Zheng glosses: 格位標記（主格）; Glosbe targets: do; from; evidence: 格位標記; 主格
- ami,en `miheca` => `since`: target_not_supported_by_zheng_gloss; Zheng glosses: 年; Glosbe targets: age; since; year; evidence: 年
- ami,en `ngaˈay` => `if`: source_not_attested_in_zheng_dictionary; Zheng glosses: none; Glosbe targets: if; evidence: none
- ami,en `ngaˈayay` => `respect`: source_not_attested_in_zheng_dictionary; Zheng glosses: none; Glosbe targets: respect; evidence: none
- ami,en `nira` => `her`: target_not_supported_by_zheng_gloss; Zheng glosses: 他的; Glosbe targets: her; his; evidence: 他; 他的
- ami,en `tamdaw` => `perfect`: target_not_supported_by_zheng_gloss; Zheng glosses: 人; Glosbe targets: man; perfect; root; evidence: 人
- ami,en `tamdaw` => `root`: target_not_supported_by_zheng_gloss; Zheng glosses: 人; Glosbe targets: man; perfect; root; evidence: 人
- ami,en `to` => `when`: target_not_supported_by_zheng_gloss; Zheng glosses: 格位標記(受格或斜格); Glosbe targets: when; evidence: 或; 格位標記
- ami,en `wina` => `mother`: source_not_attested_in_zheng_dictionary; Zheng glosses: none; Glosbe targets: mother; evidence: none
- tay,en `'bli` => `bury`: source_not_attested_in_zheng_dictionary; Zheng glosses: none; Glosbe targets: bury; evidence: none
- tay,en `'law` => `righthanded`: source_not_attested_in_zheng_dictionary; Zheng glosses: none; Glosbe targets: righthanded; evidence: none
- tay,en `'txan utux` => `land of the spirits`: source_not_attested_in_zheng_dictionary; Zheng glosses: none; Glosbe targets: land of the spirits; evidence: none
- tay,en `Mrhuw Wagiq` => `God`: source_not_attested_in_zheng_dictionary; Zheng glosses: none; Glosbe targets: god; evidence: none
- tay,en `aba` => `father`: source_not_attested_in_zheng_dictionary; Zheng glosses: none; Glosbe targets: father; evidence: none
- tay,en `abau` => `leaf`: source_not_attested_in_zheng_dictionary; Zheng glosses: none; Glosbe targets: leaf; evidence: none
- tay,en `amuy` => `flour`: target_not_supported_by_zheng_gloss; Zheng glosses: 女子名; Glosbe targets: flour; powder; evidence: 女子名
- tay,en `amuy` => `powder`: target_not_supported_by_zheng_gloss; Zheng glosses: 女子名; Glosbe targets: flour; powder; evidence: 女子名

Full row-level audit: `data/processed/zheng_glosbe_lexical_audit.csv`

Group-level decisions: `data/processed/zheng_glosbe_lexical_group_review.csv`

Rejected lexical rows: `data/processed/lexical_xml_rejected.csv`

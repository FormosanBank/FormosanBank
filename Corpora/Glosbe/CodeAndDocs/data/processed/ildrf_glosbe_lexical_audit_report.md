# ILRDF Reference Audit For Glosbe Lexical Entries

Generated: 2026-08-03T03:47:06Z

Reference repository: `../Formosan-Zheng-ACL-2024`

## Provenance Finding

The files previously called the "Zheng dictionary" are not an independent dictionary. Zheng et al. state that they downloaded the Formosan lexicons from the ILRDF online dictionary, converted ILRDF PDFs to HTML, and extracted the Formosan-Mandarin entries. The local reference XML identifies ILRDF as its source and Zheng et al. as the curator of that derived release.

Primary paper: https://aclanthology.org/2024.findings-acl.670/

This audit therefore calls the data an **ILRDF-derived reference**. It does not treat a match as independent corroboration and does not treat absence or a different mapped gloss as proof that a Glosbe entry is wrong.

## Corrected Policy

- Exclude only concrete structural or provenance failures detected before reference comparison.
- Keep every structurally valid Glosbe lexical source-target pair.
- Record exact source-form overlap with the selected ILRDF-derived file as metadata.
- Record the hand-built Chinese-to-English mapping as a heuristic review signal only. It is incomplete, substring-based, and cannot rule out homography, polysemy, or additional Glosbe senses.
- Preserve distinct same-language targets as separate `TRANSL` elements. The first is primary and every additional target uses `ver="alt"`.
- Abort when a configured reference repository or file is missing, has the wrong language, or lacks ILRDF provenance. A broken reference path can no longer silently turn every row into a non-match.
- For `trv`, compare against the Truku dictionary only. The previous loader also included Seediq because both files use `xml:lang="trv"`.

## Selected ILRDF-Derived Files

| Language | File | SHA-256 | S | TRANSL | Unique source forms | Unique source-gloss pairs |
|---|---|---|---:|---:|---:|---:|
| ami | `Final_XML/Amis/Dictionary_Amis_ami.xml` | `1eb7439f2ecd0d9f25621859b932e937b75c601183b10ced64c20bbc95b4e47c` | 7800 | 7918 | 7795 | 7917 |
| tay | `Final_XML/Atayal/Dictionary_Atayal_tay.xml` | `d44d8c8d83708b42d4f60fec3cd922de298c8e8e531442e1f99f77baba334943` | 6638 | 7320 | 6634 | 7319 |
| trv | `Final_XML/Truku/Dictionary_Truku_trv.xml` | `59dcea834e59a8a287029bcf3ca2814730197b6dd02a1d2bb1fe0c12837462b2` | 32417 | 35025 | 32413 | 35025 |
| xsy | `Final_XML/Saisiyat/Dictionary_Saisiyat_xsy.xml` | `c1d866a9689c351fab8c5cff3b5ce207320d24dbc598aea996cacb165276058a` | 6423 | 7186 | 6392 | 7169 |

## Scope

This audit covers Glosbe dictionary/headword rows only. It does not filter sentence-level translation-memory data, including the restored Amis-Chinese material. The row-level CSV records one candidate translation and its ILRDF reference status. The group review CSV places all Glosbe targets for one source form together.

## Final Counts

- deduplicated Glosbe lexical candidates before structural filtering: 1319
- structurally valid candidate translations retained: 1305
- structurally invalid/cross-reference rows rejected: 14
- candidate translations rejected because of ILRDF absence or gloss mapping: 0
- lexical sentence elements emitted: 1156
- lexical `TRANSL` elements emitted: 1305
- alternate `TRANSL ver="alt"` elements: 149

### Reference status

- source_not_attested: 529
- gloss_unmapped: 528
- target_supported_by_mapping: 209
- different_from_mapping: 39

### Pair counts

- ami,en: 64 translations in 38 sentence elements
- tay,en: 584 translations in 521 sentence elements
- trv,en: 143 translations in 112 sentence elements
- xsy,en: 514 translations in 485 sentence elements

### Structural rejection reasons

- target_cross_reference_or_invalid_note: 12
- source_numeric_or_punct_only: 1
- identical_source_target: 1

## Reference Status Codes

- `source_not_attested`: the exact normalized Glosbe source form is absent from the selected ILRDF-derived file. This is coverage metadata only.
- `target_supported_by_mapping`: a hand-built mapping connects part of the ILRDF Chinese gloss to the Glosbe English target. This is heuristic support, not independent verification.
- `gloss_unmapped`: the source is present, but no hand-built mapping applies to its Chinese gloss.
- `different_from_mapping`: a mapping applies but points to another English target. The Glosbe target is retained because the mapping cannot rule out additional senses or homographs.

## Different-Mapping Review Examples

- ami,en `Kawas` => `heaven`; ILRDF glosses: 上帝、神、鬼; mapping evidence: 上帝; 神; 鬼
- ami,en `ciira` => `she`; ILRDF glosses: 他; mapping evidence: 他
- ami,en `cowa` => `little`; ILRDF glosses: 哪裡; mapping evidence: 哪裡
- ami,en `kaka` => `older sibling`; ILRDF glosses: 哥; mapping evidence: 哥
- ami,en `kaka` => `older sister`; ILRDF glosses: 哥; mapping evidence: 哥
- ami,en `kami` => `go`; ILRDF glosses: 我們(排除式; 手紙; mapping evidence: 我; 我們; 手
- ami,en `ko` => `do`; ILRDF glosses: 格位標記（主格）; mapping evidence: 格位標記; 主格
- ami,en `ko` => `from`; ILRDF glosses: 格位標記（主格）; mapping evidence: 格位標記; 主格
- ami,en `miheca` => `since`; ILRDF glosses: 年; mapping evidence: 年
- ami,en `ngaˈay` => `if`; ILRDF glosses: 好; mapping evidence: 好
- ami,en `ngaˈayay` => `respect`; ILRDF glosses: 好的; mapping evidence: 好的; 好
- ami,en `nira` => `her`; ILRDF glosses: 他的; mapping evidence: 他; 他的
- ami,en `tamdaw` => `perfect`; ILRDF glosses: 人; mapping evidence: 人
- ami,en `tamdaw` => `root`; ILRDF glosses: 人; mapping evidence: 人
- ami,en `to` => `when`; ILRDF glosses: 格位標記(受格或斜格); mapping evidence: 或; 格位標記
- tay,en `amuy` => `flour`; ILRDF glosses: 女子名; mapping evidence: 女子名
- tay,en `amuy` => `powder`; ILRDF glosses: 女子名; mapping evidence: 女子名
- tay,en `lmom` => `refire`; ILRDF glosses: (放火)燒; 燒(如燒稻草); mapping evidence: 燒
- tay,en `miquy` => `weeds`; ILRDF glosses: 男子名; mapping evidence: 男子名
- tay,en `mrhuw` => `ancestors`; ILRDF glosses: 智者; 長官; mapping evidence: 智者; 長官
- tay,en `nana'` => `woman's older sister's husband`; ILRDF glosses: 夫之兄; mapping evidence: 夫之兄
- tay,en `pali'` => `feather`; ILRDF glosses: 翅膀; mapping evidence: 翅膀
- tay,en `pitay` => `bedbug`; ILRDF glosses: 女子名; mapping evidence: 女子名
- tay,en `puqing` => `yam sprouts`; ILRDF glosses: 根部、源頭; 樹頭; mapping evidence: 根部; 源頭; 樹頭; 樹
- tay,en `qba'` => `foreleg`; ILRDF glosses: 手; mapping evidence: 手
- tay,en `qmes` => `magic`; ILRDF glosses: 劃清界線; mapping evidence: 劃清界線
- tay,en `rgyax` => `forest`; ILRDF glosses: 山、山脊; mapping evidence: 山、山脊; 山脊; 山
- tay,en `smyax` => `clean`; ILRDF glosses: 明亮; 照亮、光亮; mapping evidence: 明亮; 照亮; 光亮
- tay,en `turu'` => `stalk side`; ILRDF glosses: 背部; mapping evidence: 背部
- tay,en `utux` => `one`; ILRDF glosses: 神、靈、鬼、魂; 鬼魂; mapping evidence: 神; 靈; 鬼魂; 鬼

## Evidence Files

Full row-level audit: `data/processed/ildrf_glosbe_lexical_audit.csv`

Group review: `data/processed/ildrf_glosbe_lexical_group_review.csv`

Concrete structural rejections: `data/processed/lexical_xml_rejected.csv`

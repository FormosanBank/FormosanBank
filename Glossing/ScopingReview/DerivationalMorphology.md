# Derivational morphology: candidate inventory (causative, stative, inchoative, reflexive)

Scoping review across all glossed corpora for the four verb-derivational functions
relevant to verb individuation in the voice analysis — causation, stativity,
inchoativity, reflexivity — plus reciprocal, which the reference grammars bundle
with reflexive. Review artifact (round 1, with decision cards):
https://claude.ai/artifact/TaLCcmnb2HjxiYmC7zRaZB

Three evidence sources, kept distinct:
- **Grammar** — the 語法概論 reference-grammar series, one volume per language
  (PDF pages cited on the artifact).
- **Collaborators** — the AffixCategorization spreadsheet (Paiwan/Amis/Atayal/Yami
  sheets); its `SEPARATOR?` column records their verb-individuation call per affix.
- **Corpora** — gloss-code counts (audit rule: M-level, W when unsegmented, per
  tier) with the morpheme forms behind each code. Full per-(corpus, language,
  code) rows with top-5 forms: `deriv_counts.json` in this directory.

## Standard vocabulary status

| Code | Meaning | Status |
|---|---|---|
| CAUS | causative | Leipzig; CAU/使役/使動 → CAUS ruled bank-wide (v8) |
| STAT | stative | registered (v3); STA/SV → STAT |
| COS | change of state | registered |
| REFL | reflexive | Leipzig |
| RECP | reciprocal | Leipzig; NTU REC → RECP ruled |
| INCH | inchoative | folded into COS (card C choice `fold`, 2026-11-15); stays unregistered |

## Candidate affixes by language

Grammar claims are the 語法概論 volume's; corpus counts are audit-rule tier-tokens.

| Language | Causative | Stative | Inchoative | Reflexive | Reciprocal |
|---|---|---|---|---|---|
| Amis | pa-, pa-pi-; mi-/-en causativize statives | ma-/ø AF; ka- dependent | mala- 'become' (gloss-only) | none (tireng, =to) | ma-+Ca-redup; mala- |
| Atayal | p- (also s-); ⚠ p-/s- homophonous with reciprocal and future/inchoative | m-/ø; k- in dependent forms | s-/t- 'spontaneous change' (table-only) | none (nanak) | p-/s-/t-; C1-redup |
| Bunun | p(a)-; stacks p-is- | ka- (k drops in AF); NTU zho 狀態 ×42 on unexplained form al | in-/i-/is- 「變」; corpus min- 'become' ×81; =in phase clitic = COS | pronoun anak'anak + prefix concord; NTU REFL = mu- ×42 (not in grammar's list) | pa- (homophonous with causative; split by transitivity) |
| Kanakanavu | 'ap-/'apa-/'api-/'apu-/pa- | no affix (AF class); ILCAA STA → STAT | ara- 「變」 ×83 'become'; =cu/=ci phase clitic = COS; Wild INCH mari-/maru- | not in grammar; no corpus rows | 'arupa-; ⚠ NTU REC ×34 = ⟨n⟩ glossed 重現 'recurrence', not reciprocal (artifact card B) |
| Kavalan | pa- | none (AF me-; ma- is NOT stative here) | =ti aspect clitic only | **explicitly denied** | sim- (verbs), nan- (nouns) — corpus matches |
| Paiwan | pa- (HPS `cause` ×649 = pa); pa-pe- 'make become' | no affix in grammar; HPS `stat` ×970 = ma (collaborators: ma only, separator yes) | me- 'become' (grammar); HPS `become` = ka ×64 | 'i- (list-only); HPS `self` = ki ×32, collaborators separator **no** | none discussed |
| Rukai (grammar = Mantauran) | pa-; pi- locative, po- motion; apaa-/apa'a- caus-of-recp | ma- finite / ka- non-finite — corpus ka ×395 + ma ×297 matches | 'aa- (list-only); to- dynamicizer | 'ini-+Ca (middle-like readings); NTU ngi- ×152 | maa-/ma'a-(+ka-)/ma-Ca-/ma'a-pa- |
| Saisiyat | pa-; pak- for statives; kin-/'al-/Sil- manner | ø AF tendency, no prefix | 'in- (AF min-) change-of-state intransitives | not discussed | makak-; Ca-redup — corpus makak ×5 matches |
| Sakizaya | pa-; pa-pi- dynamic / pa-ka- stative; pa-pa- double | ø/ma- AF; ka- under negation | mala- 「變得」, -sa (table-only) | none (word tu) | masasi-; ma-+Ca-redup |
| Seediq | p-; statives p-k-/p-q- | k-/q- (zho-only glosses 靜態 ×20, no eng twin) | mg- 'become' (table-only); di/da particle | none (naq/nanaq — glossed lexically 'self' ×206) | m-+C1-redup; kin ms-/mt- |
| Thao | ia-/pia-/pa-/pi-/pu-/pish- (+kashi-, shu-) | ma- 狀態; ka- in imperatives/negatives | min-/mim- gloss-only; Li's INCH ×2 = min- | none (ananak, -anak- verbs) | mapa- |
| Truku | pe-; statives pe-se- | k-/q- (ke-) | **none found in the volume** | **no section in the volume** | t-; p-+C1ə-redup |
| Tsou | free word poa (primary) + pa'-/p'- | **no stative affix** (auxiliary/negator diagnosis) | =cu aspect clitic only | none (iachi, glosses only) | yupa- (glosses only) — corpus matches |
| Yami | pa-; -en on statives; maka-/paka-/pipa-/pi-/pika-/mapa-… | ma- three-ways ambiguous (plain/abilitative) + ka-…-an; RauDong SV → STAT | micya-/mipa- 「愈來愈」; -om- inception | one mi- side-remark only | masi- (table-only); RauDong REC = mi- forms |

## Proposals: still open (artifact cards, round 3)

- A: NTU zho derivational codes → Latin twins (使役/使動/役使/使→CAUS, 狀態/靜態→STAT,
  改變狀態/狀態改變→COS, 反身→REFL, 交互/互相→RECP); 重現 excluded; Bunun 狀態 carved out to A2.
- A2: Bunun 狀態/state ×42, forms al ×40 / tal ×1 / a-l ×1. The maintainer asked (card A note,
  2026-11-15) what the grammar says about `al`. Answer: 布農語語法概論 §6 (PDF 146) —
  「姿勢動詞和某些動詞可以附加前綴al-來凸顯持續的姿態或動作，相當於中文的「著」」, glossed
  持續貌2 "durative 2" (fn.26: 「用「持續」來標註持續貌標記-al」; 持續貌1 = clitic =ang); the
  grammar's own example 6-30b m-al-'anuhu 主事焦點-持續貌2-坐 is the very word NTU glosses
  AF-state-sit. So NTU's 狀態/state here names the grammar's durative, not a stative. Options
  on the card: Bunun-only override → DUR (Leipzig) / STAT with card A / leave / other.
- B: NTU Kanakanavu REC ×34 (重現, ⟨n⟩) — mis-covered by the bank-wide REC→RECP ruling.
  2026-11-15: maintainer clicked `modify` with an empty note — asked what change he intends.
- P1–P3 (Wild-Lehmann parenthesized glosses, maintainer-requested cards 2026-11-15): 81 tokens,
  39 distinct (W 63 / M 18), all verbatim+flagged under the parens-INVESTIGATE rule. P1 voice/mood
  tags ×55 (go (AV), hear(UV), try (HORT), …); P2 numeral(person) ×22; P3 sikaisiisi (ritual) ×4.
  Context on the cards: Leipzig Rule 7 sanctions round parens for inherent categories (tree(G4));
  Rule 6 square brackets; any rewrite option needs a small shared-converter extension (parens
  handling), which the card choice would be the approval request for.

## Ruled on the decision page 2026-11-15, applied the same day

Answers read from the page database (choice values quoted); applied by
stripping the affected corpora's generated standard tiers and re-running
`QC/glossing/apply_gloss_standard.py` with the updated tables, verified by
diff (every changed line involves the target atoms; 0 HARD validator
findings; `tests/glossing` 30 passed).

- C (`fold`): INCH → COS in Li-Conjunction-Thao (2 tokens) and
  Wild-Lehmann-Kanakanavu. Every M-level INCH converted; the one leftover
  atom is in the W-level whole-word gloss `INCH-ring-ring(AV)` (word
  mari-kirling-kirling), copied verbatim per the parentheses-residue rule
  while its M child mari is glossed COS. INCH stays unregistered.
- D (`approve`): Song-Kanakanavu 使動 → CAUS, 86/86 tokens.
- E (`approve`): HPS new row `cause` → CAUS. Every M-level `cause`
  converted (M-level leftovers: 0). 39 atoms remain only in W-level
  whole-word glosses like `cause<af>-lack` (word p<en>a-ula), whose M
  children are fully segmented and converted (M -en- → AV, M p-a → CAUS,
  M ula → lack): HPS writes the W gloss in Leipzig infix-bracket notation
  and its rules file lacks the KEEP-BRACKETS row every other corpus has,
  so `cause<af>` is one unsplittable atom there. W-tier-consistency
  follow-up only; no morpheme data is unconverted.
- F (`approve`): HPS `stat` → STAT — same situation, 9 W-level bracket
  atoms, M-level leftovers 0. ⚠ The maintainer's note on this card was cut
  off mid-sentence ("Do they say ") — asked in chat.
- H (`approve`): NTU STAV → STAT, 4/4 (Rukai); zho twins 狀態 wait on card A.

Dictionary entries added for coverage: Paiwan CAUS + STAT, Thao COS.

Round-3 additions (2026-11-15, applied the same way, diff-verified):

- G (`approve`): RauDong REC ×18 + 互相 ×16 → RECP; Seediq-Chang 互相 ×2 →
  RECP. 34 + 2 changed pairs, zero unrelated lines. Yami dictionary: +RECP.
- HPS KEEP-BRACKETS (maintainer, chat 2026-11-15: "OK, let's add
  KEEP-BRACKETS for HPS."): row added to the HPS rules file; standard tier
  rebuilt; 1,073 W-line glosses re-aligned with their M lines (eat<af> →
  eat<AV>, cause<af>-lack → CAUS<AV>-lack); every changed line contains a
  bracket. Codes inside brackets still UNDECIDED (perf ×367 proposed PFV,
  red, qal) stay lowercase until the HPS batch is ruled.

## Notes for the verb-individuation list

- The grammars treat the COS mass (=cu/=ci, =in, =ti, di/da) as clause-level phase
  marking, not verb derivation.
- Verb-deriving 'become' affixes with corpus presence: Bunun min-, Kanakanavu ara-,
  Thao min-, Paiwan ka (HPS gloss `become`) — all carried by lexical glosses, no code.
- The only robust affixal reflexive in the bank is Rukai ngi- (×152); the Mantauran
  grammar's examples of its cognate read as spontaneous/middle rather than agent-on-self.
- Excluded as out of scope: Sakizaya FAC (factual mood), Wakelin VR (verbalizer),
  RauDong VF (catch-all "verbal affix"; its forms include causative material — open
  item), ePark (word-translation corpus, outside gloss standardization per g6).

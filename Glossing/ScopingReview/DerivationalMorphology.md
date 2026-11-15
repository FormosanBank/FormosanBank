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

## Proposals: still open (artifact cards, round 2)

- A: NTU zho derivational codes → Latin twins (使役/使動/役使/使→CAUS, 狀態/靜態→STAT,
  改變狀態/狀態改變→COS, 反身→REFL, 交互/互相→RECP); 重現 excluded.
- B: NTU Kanakanavu REC ×34 (重現, ⟨n⟩) — mis-covered by the bank-wide REC→RECP ruling.
- G: remaining reciprocal codes → RECP (RauDong REC ×18 + 互相 ×16; Seediq-Chang 互相 ×2).

## Ruled on the decision page 2026-11-15, applied the same day

Answers read from the page database (choice values quoted); applied by
stripping the affected corpora's generated standard tiers and re-running
`QC/glossing/apply_gloss_standard.py` with the updated tables, verified by
diff (every changed line involves the target atoms; 0 HARD validator
findings; `tests/glossing` 30 passed).

- C (`fold`): INCH → COS in Li-Conjunction-Thao (2 tokens) and
  Wild-Lehmann-Kanakanavu (3 of 4; the 4th is inside the residue gloss
  `INCH-ring-ring(AV)`, copied verbatim per the parentheses rule). INCH
  stays unregistered.
- D (`approve`): Song-Kanakanavu 使動 → CAUS, 86/86 tokens.
- E (`approve`): HPS new row `cause` → CAUS; 1,259/1,298 atoms. The other
  39 sit in infix-bracket atoms (`cause<af>`), which the HPS converter has
  never split (pre-existing: `eat<af>` etc., 2,723 standard-tier lines) —
  follow-up, not silently fixed.
- F (`approve`): HPS `stat` → STAT, 1,931/1,940 atoms (9 in the same
  infix-bracket situation). ⚠ The maintainer's note on this card was cut
  off mid-sentence ("Do they say ") — asked in chat.
- H (`approve`): NTU STAV → STAT, 4/4 (Rukai); zho twins 狀態 wait on card A.

Dictionary entries added for coverage: Paiwan CAUS + STAT, Thao COS.

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

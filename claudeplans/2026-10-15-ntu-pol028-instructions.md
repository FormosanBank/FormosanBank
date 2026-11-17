# Instructions for the NTU agent: POL-028 amendment (split glossed optional morphemes)

Written 2026-10-15 by the Seediq-Chang audit session, from the maintainer's rulings on its decision page
(https://claude.ai/artifact/CxSysfW7yq4jPamZBubEt3). The maintainer asked for this to be handed to you
because you are working on NTU (branch `analysis/ntu-residual-gloss-shift`). The supporting research,
with every source record quoted and the step-14 code cited by line, is
`claudeplans/2026-10-15-ntu-variant-research.md` (same directory as this file); case numbers below are
its numbers. That research was done read-only against **origin/main `646653cd9`**, not your branch, so
line numbers and ids may have moved.

## 1. The policy change

POL-028 ("variant FORMs") has an amended rule for optional material, on branch
`policy/pol-028-segmentation-splits` (FormosanBank commits `58106174f`, `7805bc757`; PR to be opened by
the maintainer, not yet on main). In short:

- A whole optional **word** (`x y (z)`) was already two S blocks (POL-026). Unchanged.
- An optional **morpheme or clitic** inside a word now becomes **two S blocks** — the base id and
  `<id>-opt` (POL-028 naming; a third reading `-opt3`, never `-opt2`) — **when the source glosses it, so
  the two readings would be glossed differently**. Maintainer, verbatim: *"differences in morphemes
  necessitate different sentence blocks only if they are glossed and would result in different glossing.
  Basically, I want the glossing to be clear."* The reason: a `ver="alt"` FORM has no W or M tier of its
  own, so today `kangavas(=an)` publishes W gloss `mango(=MED.NOM)` with parentheses and no M for `=an`.
  Split, the `-opt` sentence has W `kangavas=an` 'mango=MED.NOM' with M `kangavas` 'mango' + `=an`
  'MED.NOM', and the base sentence has W `kangavas` 'mango'.
- Optional **letters inside one morpheme** (`ka(z)`, `(s)aiv=ik`) stay `ver="alt"` variants, exactly as
  step 14 does now. Of NTU's 190 original-tier variant FORMs, 129 are of this kind and do not change.
- Existing published ids do not move (POL-037): the base reading keeps the id, the new reading takes
  `-opt`.

## 2. What the maintainer ruled for NTU

*"I want to split into two sentences. But the agent that is currently working with NTU should handle
that. Please write me full instructions to give to that agent, including an explanation of the new
policy."*

All of the following are glossed optional morphemes/clitics, so each becomes two S blocks instead of
one S with `ver="alt"` FORMs. The research found 61 such FORMs in 32 published sentences = 22 distinct
source examples (10 Bunun examples are published twice, from their own file and from `63.json`). Every
affected sentence has exactly one such word, so each split yields two sentences, not 2^n.

### 2a. Optional morphemes and clitics (15 examples, 23 published sentences)

| # | S id | W id | base | variant | source text verbatim (file + locator) | source gloss | class | note |
|---|---|---|---|---|---|---|---|---|
| 1 | `26_S_4`, `63_S_460` | `26_S_4_W3`, `63_S_460_W3` | `ma-hansiap` | `na=ma-hansiap` | `sentence/Bunun_Isbukun/26.json` rec 4 row 3: `(na=)ma-hansiap`; `63.json` rec 460 row 3: `(na=)ma-hansiap`. No ori line (`[]` / `["."]`) | `(IRR=)AF-knowledge` / `(非實現=)主焦-知識` | a (proclitic `na=` irrealis) | "The teacher definitely knows how to speak Bunun." The morpheme tier holds only the base (`ma` AF, `hansiap` knowledge). |
| 2 | `28_S_6`, `63_S_478` | `28_S_6_W0`, `63_S_478_W0` | `kangavas` | `kangavas=an` | `28.json` rec 6 row 0: `kangavas(=an)`; `63.json` rec 478 row 0: same | `mango(=MED.NOM)` / `芒果(=近距.主格)` | a (enclitic `=an`) | Source note, published as `@notes` on the base FORM: "加上LOC–an語意較明確，但省略也可以" (my reading: adding -an makes the meaning clearer, but leaving it out is also fine). The note calls it LOC, but the gloss says MED.NOM. |
| 3 | `28_S_7`, `63_S_479` | `28_S_7_W0`, `63_S_479_W0` | `kangavas` | `kangavas=an` | `28.json` rec 7 row 0: `kangavas(=an)`; `63.json` rec 479 row 0: same | `mango(=MED.NOM)` / `芒果(=近距.主格)` | a | Same word as #2, but a different sentence (`kaun-un=ta`, "we can eat it"). |
| 5 | `34_S_7`, `63_S_537` | `34_S_7_W0`, `63_S_537_W0` | `kalin-lumah=in` | `kalin-na-lumah=in` | `34.json` rec 7 row 0: `kalin(-na)-lumah=in`; `63.json` rec 537 row 0: same | `blow(-to)-house=COS` / `吹(-到)-家=改變狀態` | a (word-medial affix `-na-` "to") | Source note: "kalin-‘iv’iv-na-lumah 風吹到家 (blow-breeze-to-house)". The morpheme tier has no glosses. |
| 6 | `36_S_1`, `63_S_552` | `36_S_1_W7`, `63_S_552_W7` | `ma-'ansum.` | `ma-'ansum=dau.` | `36.json` rec 1 row 7: `ma-‘ansum(=dau).\`; `63.json` rec 552 row 7: `ma-‘ansum(=dau).` | `AF-taste(=EVI)` / `主焦-味道(=知識詞)` | a (enclitic `=dau` evidential) | The source writes the glottal stop as ‘ (U+2018); the published form uses `'`. |
| 7 | `36_S_3`, `63_S_554` | `36_S_3_W2`, `63_S_554_W2` | `'utung=an` | `'utung=an=dau` | `36.json` rec 3 row 2: `‘utung=an(=dau)`; `63.json` rec 554 row 2: same | `monkey=MED.NOM(=EVI)` / `猴子=中距.主格(=知識詞)` | a (`=dau`) | The 63.json copy has HTML-escaped `ta&lt;i&gt;’aza` in row 0. It is published correctly as `ta<i>'aza`. |
| 8 | `36_S_15`, `63_S_566` | `36_S_15_W0`, `63_S_566_W0` | `tupa` | `tupa=dau` | `36.json` rec 15 row 0: `tupa(=dau)`; `63.json` rec 566 row 0: same | `to.say(=EVI)` / `說(=知識詞)` | a (`=dau`) | The morpheme `tupa` is glossed `say` / `說`. |
| 10 | `48_S_22`, `63_S_686` | `48_S_22_W0`, `63_S_686_W0` | `cis-maz` | `cis-maz=a` | `48.json` rec 22 row 0: `cis-maz(=a)`; `63.json` rec 686 row 0: same | `for-what(=DIST.NOM)` / `為了-什麼(=遠距.主格)` | a (`=a` distal nominative) | The two copies differ: 63.json ends `ma-subnuh?/` with "Why/for what are you angry?", while 48.json ends `ma-subnuh` with "Why are you angry?". The morpheme `cis` is published as `due.to` / `由於`, not the source's `for` / `為了`. |
| 11 | `3_S_1` | (no W tier published) | `ʉsʉ'ʉ-ʉn na takuacapa paici Cuma (tia iima cuma).` | `ʉsʉ'ʉ-ʉn=maku na takuacapa paici Cuma (tia iima cuma).` | `sentence/Kanakanavu_Kanakanavu/3.json` rec 1 row 0: `ʉsʉ’ʉ-ʉn(=maku)`; ori `["."]`; rows 5-7: `(tia`, `iima/imʉ-ʉn`, `cuma).` | eng `put-PF=1SG.GEN` (**no parentheses**) / zho `放-受焦(=1SG.屬格)` | a (enclitic `=maku` 1SG.GEN) | The source's two gloss columns disagree on whether `=maku` is optional. A second parenthetical spans three words (`(tia … cuma).`). Step 14 cannot see it, so both base and variant keep `(tia iima cuma)` with parentheses, and the slash reading `imʉ-ʉn` is gone. No W tier is published; I did not trace why. |
| 12 | `3_S_38` | `3_S_38_W1` | `nguain` | `nguain=kee` | `3.json` rec 38 row 1: `nguain(=kee)`; ori `["."]` | `3SG.NOM(=3SG.GEN)` / `3SG.主格(=3SG.屬格)` | a (enclitic `=kee`) | — |
| 13 | `20200508-CL-7_S_19` | `…_S_19_W2` | `naw=siulri` (S: `ini, kai naw=siulri mua musuane.`) | `naw=lri-siulri` | `sentence/Rukai_Vedai/20200508-CL-7.json` rec 19 row 2: `naw=(lri-)siulri`; ori: `ini, kainaw (lri)siulri mua musuane.` | `1S.BN=(FUT-)back` / `第一人稱單數.附著主格=(未來式-)回` | a (prefix `lri-` future) | The free translations mark the same option: "No, I don’t (/will not) want to go back to you." and "不，我（將）不會回去你那邊。". The published Chinese translation is "不，我 不會回去你那邊。", with a stray space where （將） was cut out. The S FORM comes from the gloss line, not the source's sentence line (`kainaw (lri)siulri`). The morpheme tier has no glosses. |
| 14 | `20200528-FW-Ludwig_S_23` | `…_S_23_W0` | `mua-lrumay-a` (S: `mua-lrumay-a iniane.`) | `lu-mua-lrumay-a` | `20200528-FW-Ludwig.json` rec 23 row 0: `(lu-)mua-lrumay-a`; ori: `(lu)mua lrumadha iniane.` | `(go-)go-hit-IMP` / `(去-)去-打-命令式` | a (prefix `lu-` "go") | The source's sentence line has two words with the surface spelling **lrumadha**. The published original S FORM is built from the analysis line instead: one word, spelled `lrumay-a`. The source's surface spelling does not appear anywhere in the S tier. The morpheme tier has no glosses. |
| 16 | `20200529-FW-Lixing-1_S_17` | `…_S_17_W0` | `ki-a-malra` | `ki-a-malra-nga` | `20200529-FW-Lixing-1.json` rec 17 row 0: `ki-a-malra(-nga)`; ori: `kiamalra(nga) patuelre/*makanaelre kay kidringi.` | `PASS-RLS-take(-PFV)` / `被動-拿(-完成貌)` | a (suffix `-nga` perfective) | The S FORM comes from the segmented gloss line, not the ori line. |
| 17 | `20200529-FW-Lixing-1_S_23` | `…_S_23_W1` | `tara-tulru` | `tara-mu-tulru` | same file rec 23 row 1: `tara-(mu-)tulru`; ori: `wailuku tara(mu)tulru kay lalasu ku karadrare.` | `NEC.MOD-(go-)three` / `必要.一定.情態-(去-)三` | a (prefix `mu-`) | The source's English free translation is cut off ("All the boys brought three (different) baskets (and each of them must brought three"), and there is no Chinese translation. The morpheme tier has no glosses. |
| 18 | `20200529-FW-Ryan_S_6` | `…_S_6_W5` | `pa-twaramarama` | `ma-pa-twaramarama` | `20200529-FW-Ryan.json` rec 6 row 5: `(ma-)pa-twaramarama`; ori: `kay yakay danne kay lasitu mapatwaramarama kay dinva.` (**no parentheses**) | `(RECP-)CAUS-pass` / `(互相-)使役-傳` | a (prefix `ma-` reciprocal) | **The source's sentence line has `ma-` and no parentheses**, so the published *base* (without `ma-`) is a reading the source sentence never gives. The Chinese free translation also marks it: "這房間裡的人把這個電話(互相)傳了下去。". It is published as "這房間裡的人把這個電話 傳了下去。", with a stray space where (互相) was cut. The morpheme tier has no glosses. |

### 2b. Two where the source says the readings mean different things

| # | S id | W id | base | variant | source text verbatim (file + locator) | source gloss | class | note |
|---|---|---|---|---|---|---|---|---|
| 4 | `30_S_5`, `63_S_499` | `30_S_5_W2`, `63_S_499_W2` | `ma-klang` | `na=ma-klang` | `30.json` rec 5 row 2: `(na=)ma-klang`; `63.json` rec 499 row 2: same | `(IRR=)AF-hot` / `(非實現=)主焦-熱` | a (proclitic `na=`) | **The source says the two readings mean different things.** Note in 30.json: "省略 irrealis na= 意思為「隨口說說」，不強調預測的天氣狀況" (my reading: leaving out irrealis na= means "just saying it casually", without stressing a prediction about the weather). The 63.json copy's note stops before that sentence. The Chinese free translation gives two renderings, "外面一定很熱；外面本來就很熱". The source doesn't say which reading each one belongs to. The morpheme tier has no glosses. |
| 9 | `36_S_16`, `63_S_567` | `36_S_16_W0`, `63_S_567_W0` | `mi-kua` | `mi-kua=dau` | `36.json` rec 16 row 0: `mi-kua(=dau)`; `63.json` rec 567 row 0: same | `AF-how(=EVI)` / `主焦-怎麼(=知識詞)` | a (`=dau`) | **The source says the readings differ in meaning.** Note: "mikua……指對方有跌倒機率100%；mikua dau指對方有跌倒機率80%。mikua dau指「是為什麼」；mikua指「怎樣」。mikua dau 是幫別人問的。" (my reading: mikua = the person has certainly fallen, mikua dau = 80% likely; mikua dau means "why", mikua means "how"; mikua dau is asked on someone else's behalf). The Chinese translation gives two renderings, "你是什麼原因跌倒/你為什麼跌倒？". The morpheme tier has no glosses. |

The maintainer ruled the translations (verbatim):

- **#4:** *"The first translation is for the version with the na=. (It's irrealis). So the split can
  happen."* The free translation is "外面一定很熱；外面本來就很熱": **外面一定很熱 goes with the reading
  with `na=`** (`na=ma-klang`), **外面本來就很熱 with the reading without it** (`ma-klang`). *"(I assume it
  is obvious how to handle the glosses.)"*
- **#9:** *"Here, the two translations are alternate translations. The readings differ in meaning, but
  the Chinese translation is the same either way."* So **both readings** (`mi-kua` and `mi-kua=dau`)
  carry the record's translation 你是什麼原因跌倒/你為什麼跌倒？ the way NTU already publishes alternate
  translations.

For the other cases the maintainer gave no translation ruling. Where a source translation marks the
optional part itself (see flagged item D4 below: #13 "（將）", #18 "(互相)"), ask the maintainer rather
than deciding which reading gets which wording.

### 2c. Saisiyat: parentheses meaning "inaudible, but the speaker thinks it belongs" (3 examples)

| # | S id | W id | base | variant | source text verbatim (file + locator) | source gloss | class | note |
|---|---|---|---|---|---|---|---|---|
| 20 | `SaiNr-frog5__awi_ a basi__S_202` | `…_S_202_W16` | `hinolaong.` | `hinolaong-an.` | `story/Saisiyat_Tong-he/SaiNr-frog5__awi_ a basi_.json` rec 208 row 1: `hinolaong(-an).\` | `shade(-location)` / `蔭涼(-處所)` | a (suffix `-an`), **but in this source the parentheses do not mean "optional"** | Source notes on this record: "(an)指音檔中聽不見但發音人覺得應該有的部份" and "Note: -an- is inaudible in the sound file, but Informant feels it should be there." So the base is what the recording has, and the variant is the speaker's judgement. The morpheme tier is `hinolaong.` glossed `蔭涼處` / `shade`. |
| 21 | `SaiNr-frog5__awi_ a basi__S_209` | `…_S_209_W13` | `hinolaong,` | `hinolaong-an,` | same file rec 212 row 6: `hinolaong(-an),/` | `shade(-location)` / `蔭涼(-處)` | a (same convention as #20 — my inference; the note sits on rec 208 only) | Separate defect (D5): the S FORM reads `"inaray … ahoe".`, while the source and the W tier have `'inaray … ahoe'.`. No morpheme tier. |
| 22 | `SaiNr-frog7_kalaeh a taro__S_88` | `…_S_88_W18` | `mari'` | `mari'-in` | `story/Saisiyat_Tong-he/SaiNr-frog7_kalaeh a taro_.json` rec 91 row 7: `mari'(-in)` | eng `take(-pf)` / zho `拿-受焦` (**no parentheses**) | a (suffix `-in` patient focus) | The gloss columns disagree on whether `-in` is optional. This is a different story and speaker from #20, and there is no note here, so the meaning of the parentheses is unstated. The morpheme is published as `AF.get` / `主焦.拿` (agent focus), which contradicts the word's own gloss marking patient focus. |

The source note on #20: "(an)指音檔中聽不見但發音人覺得應該有的部份" / "Note: -an- is inaudible in the sound
file, but Informant feels it should be there." The maintainer ruled these are **split too** (the decision
above covers them). The base sentence is what the recording has; the `-opt` sentence is the speaker's
reading. #21's convention is inferred (same story, no note of its own); #22 is a different story and its
two gloss columns disagree on whether `-in` is optional.

## 3. Items to check — not instructions

The maintainer: *"Flag these items for the other agent. It has probably already handled them, so do not
provide instructions on what to do, just note the issue and ask it to check whether it is already
handled."* For each, please check whether your branch already handles it, and tell the maintainer.

- **#15** `20200528-FW-Ryan_S_19`: a whole optional word `(ngi-palay).` reached step 14 because of the
  period after the parenthesis; published base `kuini la-adhadhame ma-tuase-nga .` (stray " ."; PHON ends
  in a space) and no W tier.
- **#19** `KavNr-frog_abas_S_138`: `((VOICEOVER:mai=ti))` (a transcriber's label) published as base `().`,
  variant `(VOICEOVERmai=ti).`; the old `_fix_voiceover_label` hand fix is keyed to `S_80` and its
  script runs only for Grammar.
- **D1** step 14 rebuilds the S original FORM from the analysis line whenever a word has a parenthesis, so
  all 6 Rukai cases (#13–18) lose the source's sentence line; in #18 the published base contradicts it.
- **D2** the S level has no whole-word-optional guard (the W level does) — the cause of #15 and #19.
- **D3** the Kavalan VOICEOVER hand fix is dead (id change; Grammar-only script).
- **D4** translations lose the optional words and keep the gap: "不，我 不會回去你那邊。" (#13), "這房間裡的人
  把這個電話 傳了下去。" (#18).
- **D5** Saisiyat `S_209`: the sentence-edge glottal apostrophes became double quotes.
- **D6** `sentence/Bunun_Isbukun/63.json`: 613 of 920 records repeat a record in another Bunun file; both
  copies are published.
- **D7** morpheme glosses missing in 7 examples (#4, 5, 9, 13, 14, 17, 18); in #10 and #22 the M gloss
  disagrees with the record (`due.to` vs `for`; `AF.get` under a word glossed `take(-pf)`).
- **D8** Kanakanavu: 2,819 of 16,412 original-tier PHON contain `*` (unmapped `ʉ`).
- **D9** source defects: gloss columns disagree on optionality in #11 and #22; #17's English translation
  is cut off and has no Chinese.
- **D10** Kanakanavu `3_S_1` keeps a three-word parenthesis `(tia iima cuma)` in both tiers and has no W tier.
- **D11** Bunun standard S tier removes `=` but keeps `-` and `<…>` (observed, not judged).
- **D12** README says 191 variants (190 counted); README lines ~494–496 on manual review of optional
  segments look stale.

Full detail for every item is in sections 3–4 of `claudeplans/2026-10-15-ntu-variant-research.md`.

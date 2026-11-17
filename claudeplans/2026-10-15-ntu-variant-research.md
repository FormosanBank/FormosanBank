# NTUFormosanCorpus: where the 61 segmentation-changing `ver="alt"` FORMs come from

Read-only research against `/workspace/FormosanBank` at `646653cd9` (origin/main). Nothing in the repo was modified
(`git status --porcelain Corpora/NTUFormosanCorpus` printed nothing after my checks). All code paths are relative to
`Corpora/NTUFormosanCorpus/CodeAndDocs/` unless they start with `Corpora/` or `XML/`.

## 1. Mechanism

### 1.1 Which code writes `ver="alt"`

Four places in the NTU build can write an original-tier `ver="alt"` FORM:

| code | what triggers it | did any of the 61 come from it? |
|---|---|---|
| `pipeline/pipeline_sentences.py` step 14 (S level :647-675, W level :775-797) | a parenthesised piece inside a gloss-row form cell, e.g. `kangavas(=an)` | **yes, 54 of 61** (all Sentences cases: 28 S + 26 W) |
| `pipeline/pipeline_stories.py` step 14 (S level :573-600, W level :731-753) — a line-for-line copy of the above | same | **yes, 7 of 61** (all Stories cases: 4 S + 3 W) |
| `pipeline/resolve_slash_alternatives.py:131-137` | a slash between readings that pass a "looks like a spelling variant" test, e.g. `x/y` | no (every one of the 61 traces to a parenthesis in the source, not a slash) |
| `scripts/resolve_inline_parentheticals.py:166,170` | parentheses, but `build.sh` runs this script only for the Grammar subcorpus (`pipeline/build.sh:95`) | no |

Step 14 is enabled in the build: `pipeline/build.sh:108` `steps=0,1,2,3,4,5,7,8,9,10,11,14,15,18` (Sentences) and
`:110` `steps=0,1,2,3,4,5,7,8,9,10,11,14,15,16,18` (Stories).

### 1.2 The step-14 code, quoted

The step's own description (`pipeline/pipeline_sentences.py:49-64`):

```
  14 record word-internal optional material as an alternate form
     The sources mark optional material inside a word -- 'ka(z)', '(s)aiv=ik',
     'kangavas(=an)' -- which has no W of its own, so it cannot be treated as an
     optional word. main's resolve_inline_parentheticals.py materialises every
     combination as a separate sentence: 119 sentences gain variants, and one
     with five optional groups becomes 32 near-identical readings. That is not
     a useful corpus.

     Instead each affected word keeps ONE base FORM (kindOf="original", the
     reading WITHOUT the optional material) and one variant FORM of the same
     tier, kindOf="original" ver="alt" (WITH it) -- the POL-028 spelling as
     revised 2026-09-09. The sentence gets the same pair, built from the same
     choice, so the base forms agree across the two tiers and the variants
     agree too -- one extra form per word and per sentence, never 2^n
     sentences. standardize.py then derives the matching standard-tier
     variants, because a variant names the tier it varies from.
```

So, per this docstring, the "make it a separate sentence" treatment the new policy asks for is what the earlier
published build ("main") did, via `scripts/resolve_inline_parentheticals.py`. That script's own docstring says
"Additional readings receive deterministic `-optN` suffixes". This rebuild deliberately replaced it with `ver="alt"`.

What counts as "optional material" (`pipeline/pipeline_sentences.py:188-203`):

```python
# Optional material written INSIDE a word: 'ka(z)', '(s)aiv=ik', 'kangavas(=an)',
# '(na=)ma-hansiap'. Distinguished from a free-standing optional word by having
# other characters outside the parentheses.
_INLINE_OPTIONAL = re.compile(r"\(([^()*]*)\)")


def has_inline_optional(form: str) -> bool:
    text = (form or "").strip()
    return bool(_INLINE_OPTIONAL.search(text)) and not re.fullmatch(
        r"\([^()]*\)", text)


def inline_readings(form: str) -> tuple:
    """(without the optional material, with it) -- both parenthesis-free."""
    return (_INLINE_OPTIONAL.sub("", form).strip(),
            _INLINE_OPTIONAL.sub(r"\1", form).strip())
```

Sentence level (`pipeline/pipeline_sentences.py:647-675`). Note that `s_form` is **rebuilt from the gloss rows**
(`rows`, column 0), replacing the source's own sentence line (`ori`) if it had one:

```python
        alt_s_form = None
        if 14 in steps and any(has_inline_optional(str(r[0])) for r in rows):
            main_words, alt_words = [], []
            for r in rows:
                f = str(r[0])
                if has_inline_optional(f):
                    a, b = inline_readings(f)
                    main_words.append(a)
                    alt_words.append(b)
                else:
                    main_words.append(f)
                    alt_words.append(f)
            s_form = " ".join(w for w in main_words if w)
            alt_s_form = " ".join(w for w in alt_words if w)
            ...
        form.text = clean_text(s_form)
        if alt_s_form and alt_s_form != s_form:
            alt = ET.SubElement(s, "FORM")
            alt.set("kindOf", "original")
            alt.set("ver", "alt")
            alt.text = swap_punctuation(alt_s_form) if 8 in steps else alt_s_form
```

Word level (`pipeline/pipeline_sentences.py:775-797`). Unlike the sentence level, it has a guard that refuses when the
whole word was optional:

```python
            elif 14 in steps and has_inline_optional(w_form):
                base, alt = inline_readings(w_form)
                # POL-028/V150: an alternate is a SPELLING VARIANT of its
                # sibling. When removing the optional material leaves nothing
                # but punctuation, the whole WORD was optional -- the sentence's
                # word inventory changes, so POL-026 makes it a separate S
                # block, not an alternate. Writing one here produced pairs like
                # base ',' / alternate 'ia,'.
                if any(unicodedata.category(c)[0] in ("L", "N") for c in base):
                    w_form, w_alt = base, alt
                    ...
                else:
                    stats["14   whole-word optional left for POL-026"] = ...
            wf = ET.SubElement(w, "FORM")
            wf.set("kindOf", "original")
            wf.text = clean_text(w_form)
            if w_alt and w_alt != w_form:
                wa = ET.SubElement(w, "FORM")
                wa.set("kindOf", "original")
                wa.set("ver", "alt")
                wa.text = w_alt
```

(POL-028 = the repo policy that a variant must be a spelling variant of its base; POL-026 = whole optional words become
a separate sentence.) The sentence level has no matching guard; that gap produces two of the garbled cases below
(#15 and #19).

### 1.3 Step 14 on real source cells

I copied the three helpers above and ran them, after the builder's own markup stripper `strip_prosodic_markers`
(`scripts/utils.py:100`, which the docstring says runs first), on source cells. Command run with `python3 -B` and no
writes. Output:

```
'((VOICEOVER:mai=ti)).\\' -> stripped '((VOICEOVERmai=ti)).' | has_inline_optional True | readings ('().', '(VOICEOVERmai=ti).')
'…(1.5)' -> stripped '' | has_inline_optional False | readings None
'(ngi-palay).' -> stripped '(ngi-palay).' | has_inline_optional True | readings ('.', 'ngi-palay.')
'kangavas(=an)' -> stripped 'kangavas(=an)' | has_inline_optional True | readings ('kangavas', 'kangavas=an')
'hinolaong(-an),/' -> stripped 'hinolaong(-an),/' | has_inline_optional True | readings ('hinolaong,/', 'hinolaong-an,/')
'ma-‘ansum(=dau).\\' -> stripped 'ma-‘ansum(=dau).' | has_inline_optional True | readings ('ma-‘ansum.', 'ma-‘ansum=dau.')
'(tia' -> stripped '(tia' | has_inline_optional False | readings None
'cuma).' -> stripped 'cuma).' | has_inline_optional False | readings None
```

These match the published base and variant forms, including the garbled Kavalan `().` / `(VOICEOVERmai=ti).`.

### 1.4 README passage (`Corpora/NTUFormosanCorpus/readme.md:72-87`)

> **Variant readings use the POL-028 `ver="alt"` spelling.** Where the source records a second acceptable reading of a
> word or sentence — word-internal optional material (`ka(z)`, `kangavas(=an)`) or a slash alternation the readings of
> which are spelling variants of one another — the node carries its tier's base FORM plus a sibling
> `FORM[@kindOf="original" ver="alt"]`, and `standardize.py` derives the matching `FORM[@kindOf="standard" ver="alt"]`.
> **191 variants**, in 21 files across all three subcorpora.
>
> Until 2026-09-10 these were written `kindOf="alternate"`, … Competing *lexemes* are not variants; they keep the first
> reading and record the rest in `@notes` for a POL-027 pass.

My count of original-tier `ver="alt"` FORMs in `Corpora/NTUFormosanCorpus/XML` is **190**, not 191: Grammar W 3,
Sentences S 60, Sentences W 66, Stories S 30, Stories W 31. The 61 flagged cases are a subset of these 190.

## 2. Counts

- 61 flagged FORMs = 32 at S level + 29 at W level.
- They sit in **32 published sentences**. In 29 of them the S variant just repeats the W variant (the sentence differs
  only at that word). The other 3 (#11, #15, #19) have **no W tier at all**, so only the S variant exists.
- The 32 sentences are **22 distinct source examples**: the 10 Bunun examples are each published twice, once from their
  own source file and once from `sentence/Bunun_Isbukun/63.json`, which repeats them (see defect D6).
- Classification of the 22:
  - **(a) whole morpheme or clitic in parentheses: 20.** 11 are clitics (`=an`, `=dau`, `=a`, `=kee`, `=maku`, `na=`)
    and 9 are affixes (`-na-`, `lri-`, `lu-`, `-nga`, `mu-`, `ma-`, `-an` ×2, `-in`). In 3 of the 20 (#20-22, Saisiyat
    stories) the parentheses may mean something other than "optional": for #20 the source says the material is
    *inaudible on the recording but the speaker thinks it belongs there*.
  - **(b) optional letters inside one morpheme: 0.** (This is expected. Letter-only cases like `ka(z)` don't change
    segmentation, so the heuristic would not have flagged them.)
  - **(c) something else: 2.** #15 is a whole optional *word* whose trailing period kept it out of the separate-sentence
    step. #19 is a transcriber's voice-over label in double parentheses, `((VOICEOVER:mai=ti))`, which is not optional
    material at all.

## 3. Table (one row per distinct source example)

"row N" = 0-based index into the record's `gloss` list. Source cells are quoted as the actual string value (a JSON `\\`
is shown as one `\`). Where the source record also has a sentence line (`ori`), I quote it, because it is the source's
running sentence. Glosses are given as eng / zho.

| # | S id | W id | base | variant | source text verbatim (file + locator) | source gloss | class | note |
|---|---|---|---|---|---|---|---|---|
| 1 | `26_S_4`, `63_S_460` | `26_S_4_W3`, `63_S_460_W3` | `ma-hansiap` | `na=ma-hansiap` | `sentence/Bunun_Isbukun/26.json` rec 4 row 3: `(na=)ma-hansiap`; `63.json` rec 460 row 3: `(na=)ma-hansiap`. No ori line (`[]` / `["."]`) | `(IRR=)AF-knowledge` / `(非實現=)主焦-知識` | a (proclitic `na=` irrealis) | "The teacher definitely knows how to speak Bunun." The morpheme tier holds only the base (`ma` AF, `hansiap` knowledge). |
| 2 | `28_S_6`, `63_S_478` | `28_S_6_W0`, `63_S_478_W0` | `kangavas` | `kangavas=an` | `28.json` rec 6 row 0: `kangavas(=an)`; `63.json` rec 478 row 0: same | `mango(=MED.NOM)` / `芒果(=近距.主格)` | a (enclitic `=an`) | Source note, published as `@notes` on the base FORM: "加上LOC–an語意較明確，但省略也可以" (my reading: adding -an makes the meaning clearer, but leaving it out is also fine). The note calls it LOC, but the gloss says MED.NOM. |
| 3 | `28_S_7`, `63_S_479` | `28_S_7_W0`, `63_S_479_W0` | `kangavas` | `kangavas=an` | `28.json` rec 7 row 0: `kangavas(=an)`; `63.json` rec 479 row 0: same | `mango(=MED.NOM)` / `芒果(=近距.主格)` | a | Same word as #2, but a different sentence (`kaun-un=ta`, "we can eat it"). |
| 4 | `30_S_5`, `63_S_499` | `30_S_5_W2`, `63_S_499_W2` | `ma-klang` | `na=ma-klang` | `30.json` rec 5 row 2: `(na=)ma-klang`; `63.json` rec 499 row 2: same | `(IRR=)AF-hot` / `(非實現=)主焦-熱` | a (proclitic `na=`) | **The source says the two readings mean different things.** Note in 30.json: "省略 irrealis na= 意思為「隨口說說」，不強調預測的天氣狀況" (my reading: leaving out irrealis na= means "just saying it casually", without stressing a prediction about the weather). The 63.json copy's note stops before that sentence. The Chinese free translation gives two renderings, "外面一定很熱；外面本來就很熱". The source doesn't say which reading each one belongs to. The morpheme tier has no glosses. |
| 5 | `34_S_7`, `63_S_537` | `34_S_7_W0`, `63_S_537_W0` | `kalin-lumah=in` | `kalin-na-lumah=in` | `34.json` rec 7 row 0: `kalin(-na)-lumah=in`; `63.json` rec 537 row 0: same | `blow(-to)-house=COS` / `吹(-到)-家=改變狀態` | a (word-medial affix `-na-` "to") | Source note: "kalin-‘iv’iv-na-lumah 風吹到家 (blow-breeze-to-house)". The morpheme tier has no glosses. |
| 6 | `36_S_1`, `63_S_552` | `36_S_1_W7`, `63_S_552_W7` | `ma-'ansum.` | `ma-'ansum=dau.` | `36.json` rec 1 row 7: `ma-‘ansum(=dau).\`; `63.json` rec 552 row 7: `ma-‘ansum(=dau).` | `AF-taste(=EVI)` / `主焦-味道(=知識詞)` | a (enclitic `=dau` evidential) | The source writes the glottal stop as ‘ (U+2018); the published form uses `'`. |
| 7 | `36_S_3`, `63_S_554` | `36_S_3_W2`, `63_S_554_W2` | `'utung=an` | `'utung=an=dau` | `36.json` rec 3 row 2: `‘utung=an(=dau)`; `63.json` rec 554 row 2: same | `monkey=MED.NOM(=EVI)` / `猴子=中距.主格(=知識詞)` | a (`=dau`) | The 63.json copy has HTML-escaped `ta&lt;i&gt;’aza` in row 0. It is published correctly as `ta<i>'aza`. |
| 8 | `36_S_15`, `63_S_566` | `36_S_15_W0`, `63_S_566_W0` | `tupa` | `tupa=dau` | `36.json` rec 15 row 0: `tupa(=dau)`; `63.json` rec 566 row 0: same | `to.say(=EVI)` / `說(=知識詞)` | a (`=dau`) | The morpheme `tupa` is glossed `say` / `說`. |
| 9 | `36_S_16`, `63_S_567` | `36_S_16_W0`, `63_S_567_W0` | `mi-kua` | `mi-kua=dau` | `36.json` rec 16 row 0: `mi-kua(=dau)`; `63.json` rec 567 row 0: same | `AF-how(=EVI)` / `主焦-怎麼(=知識詞)` | a (`=dau`) | **The source says the readings differ in meaning.** Note: "mikua……指對方有跌倒機率100%；mikua dau指對方有跌倒機率80%。mikua dau指「是為什麼」；mikua指「怎樣」。mikua dau 是幫別人問的。" (my reading: mikua = the person has certainly fallen, mikua dau = 80% likely; mikua dau means "why", mikua means "how"; mikua dau is asked on someone else's behalf). The Chinese translation gives two renderings, "你是什麼原因跌倒/你為什麼跌倒？". The morpheme tier has no glosses. |
| 10 | `48_S_22`, `63_S_686` | `48_S_22_W0`, `63_S_686_W0` | `cis-maz` | `cis-maz=a` | `48.json` rec 22 row 0: `cis-maz(=a)`; `63.json` rec 686 row 0: same | `for-what(=DIST.NOM)` / `為了-什麼(=遠距.主格)` | a (`=a` distal nominative) | The two copies differ: 63.json ends `ma-subnuh?/` with "Why/for what are you angry?", while 48.json ends `ma-subnuh` with "Why are you angry?". The morpheme `cis` is published as `due.to` / `由於`, not the source's `for` / `為了`. |
| 11 | `3_S_1` | (no W tier published) | `ʉsʉ'ʉ-ʉn na takuacapa paici Cuma (tia iima cuma).` | `ʉsʉ'ʉ-ʉn=maku na takuacapa paici Cuma (tia iima cuma).` | `sentence/Kanakanavu_Kanakanavu/3.json` rec 1 row 0: `ʉsʉ’ʉ-ʉn(=maku)`; ori `["."]`; rows 5-7: `(tia`, `iima/imʉ-ʉn`, `cuma).` | eng `put-PF=1SG.GEN` (**no parentheses**) / zho `放-受焦(=1SG.屬格)` | a (enclitic `=maku` 1SG.GEN) | The source's two gloss columns disagree on whether `=maku` is optional. A second parenthetical spans three words (`(tia … cuma).`). Step 14 cannot see it, so both base and variant keep `(tia iima cuma)` with parentheses, and the slash reading `imʉ-ʉn` is gone. No W tier is published; I did not trace why. |
| 12 | `3_S_38` | `3_S_38_W1` | `nguain` | `nguain=kee` | `3.json` rec 38 row 1: `nguain(=kee)`; ori `["."]` | `3SG.NOM(=3SG.GEN)` / `3SG.主格(=3SG.屬格)` | a (enclitic `=kee`) | — |
| 13 | `20200508-CL-7_S_19` | `…_S_19_W2` | `naw=siulri` (S: `ini, kai naw=siulri mua musuane.`) | `naw=lri-siulri` | `sentence/Rukai_Vedai/20200508-CL-7.json` rec 19 row 2: `naw=(lri-)siulri`; ori: `ini, kainaw (lri)siulri mua musuane.` | `1S.BN=(FUT-)back` / `第一人稱單數.附著主格=(未來式-)回` | a (prefix `lri-` future) | The free translations mark the same option: "No, I don’t (/will not) want to go back to you." and "不，我（將）不會回去你那邊。". The published Chinese translation is "不，我 不會回去你那邊。", with a stray space where （將） was cut out. The S FORM comes from the gloss line, not the source's sentence line (`kainaw (lri)siulri`). The morpheme tier has no glosses. |
| 14 | `20200528-FW-Ludwig_S_23` | `…_S_23_W0` | `mua-lrumay-a` (S: `mua-lrumay-a iniane.`) | `lu-mua-lrumay-a` | `20200528-FW-Ludwig.json` rec 23 row 0: `(lu-)mua-lrumay-a`; ori: `(lu)mua lrumadha iniane.` | `(go-)go-hit-IMP` / `(去-)去-打-命令式` | a (prefix `lu-` "go") | The source's sentence line has two words with the surface spelling **lrumadha**. The published original S FORM is built from the analysis line instead: one word, spelled `lrumay-a`. The source's surface spelling does not appear anywhere in the S tier. The morpheme tier has no glosses. |
| 15 | `20200528-FW-Ryan_S_19` | (no W tier published) | `kuini la-adhadhame ma-tuase-nga .` | `kuini la-adhadhame ma-tuase-nga ngi-palay.` | `20200528-FW-Ryan.json` rec 19 row 3: `(ngi-palay).`; ori: `kuini ladhadhame matwasenga (ngipalay).` | `(REFL-blow)` / `(反身-吹)` | **c** (a whole optional *word*, not material inside a word) | The variant adds a word. The step that should make a separate sentence (`pipeline_sentences.py:697`, `re.fullmatch(r"\([^()]*\)", …)`) missed it because of the `.` after the `)`. The W-level step 14 then refused it via its whole-word guard, but the S level went ahead. Result: the base has a stray ` .`, and its PHON (`kuini laaðaðamə matuasəŋa `) has a trailing space. The W tier was then withdrawn: I reproduced that the word-tier alignment check returns False for S `kuini la-adhadhame ma-tuase-nga .` against words `[kuini, la-adhadhame, ma-tuase-nga, (ngi-palay).]` (those word forms are my reconstruction). |
| 16 | `20200529-FW-Lixing-1_S_17` | `…_S_17_W0` | `ki-a-malra` | `ki-a-malra-nga` | `20200529-FW-Lixing-1.json` rec 17 row 0: `ki-a-malra(-nga)`; ori: `kiamalra(nga) patuelre/*makanaelre kay kidringi.` | `PASS-RLS-take(-PFV)` / `被動-拿(-完成貌)` | a (suffix `-nga` perfective) | The S FORM comes from the segmented gloss line, not the ori line. |
| 17 | `20200529-FW-Lixing-1_S_23` | `…_S_23_W1` | `tara-tulru` | `tara-mu-tulru` | same file rec 23 row 1: `tara-(mu-)tulru`; ori: `wailuku tara(mu)tulru kay lalasu ku karadrare.` | `NEC.MOD-(go-)three` / `必要.一定.情態-(去-)三` | a (prefix `mu-`) | The source's English free translation is cut off ("All the boys brought three (different) baskets (and each of them must brought three"), and there is no Chinese translation. The morpheme tier has no glosses. |
| 18 | `20200529-FW-Ryan_S_6` | `…_S_6_W5` | `pa-twaramarama` | `ma-pa-twaramarama` | `20200529-FW-Ryan.json` rec 6 row 5: `(ma-)pa-twaramarama`; ori: `kay yakay danne kay lasitu mapatwaramarama kay dinva.` (**no parentheses**) | `(RECP-)CAUS-pass` / `(互相-)使役-傳` | a (prefix `ma-` reciprocal) | **The source's sentence line has `ma-` and no parentheses**, so the published *base* (without `ma-`) is a reading the source sentence never gives. The Chinese free translation also marks it: "這房間裡的人把這個電話(互相)傳了下去。". It is published as "這房間裡的人把這個電話 傳了下去。", with a stray space where (互相) was cut. The morpheme tier has no glosses. |
| 19 | `KavNr-frog_abas_S_138` | (no W tier published) | `().` | `(VOICEOVERmai=ti).` | `story/Kavalan_Xinshe/KavNr-frog_abas.json` rec 138: row 0 `…(1.5)`, row 1 `((VOICEOVER:mai=ti)).\` | `NEG=PFV` / `否定=完成` | **c** (transcriber's voice-over label in double parentheses, not optional material) | Translations: "Is it over?" / "沒了嗎?". The markup stripper drops the `:`. The inner `(...)` matches the optional-material pattern, so the base keeps only the outer `()`. An older hand fix exists (`scripts/resolve_inline_parentheticals.py:248-262`, `_fix_voiceover_label`), but it is keyed to the old id `KavNr-frog_abas_S_80` and its script is not run for Stories, so it never fires. That fix wrote S `maiti.` and W `mai=ti`. The AUDIO `@file` is still `KavNr-frog_abas_S80.mp3`. The next sentence, `S_139`, is `mai=ti haw.` "It’s over." |
| 20 | `SaiNr-frog5__awi_ a basi__S_202` | `…_S_202_W16` | `hinolaong.` | `hinolaong-an.` | `story/Saisiyat_Tong-he/SaiNr-frog5__awi_ a basi_.json` rec 208 row 1: `hinolaong(-an).\` | `shade(-location)` / `蔭涼(-處所)` | a (suffix `-an`), **but in this source the parentheses do not mean "optional"** | Source notes on this record: "(an)指音檔中聽不見但發音人覺得應該有的部份" and "Note: -an- is inaudible in the sound file, but Informant feels it should be there." So the base is what the recording has, and the variant is the speaker's judgement. The morpheme tier is `hinolaong.` glossed `蔭涼處` / `shade`. |
| 21 | `SaiNr-frog5__awi_ a basi__S_209` | `…_S_209_W13` | `hinolaong,` | `hinolaong-an,` | same file rec 212 row 6: `hinolaong(-an),/` | `shade(-location)` / `蔭涼(-處)` | a (same convention as #20 — my inference; the note sits on rec 208 only) | Separate defect (D5): the S FORM reads `"inaray … ahoe".`, while the source and the W tier have `'inaray … ahoe'.`. No morpheme tier. |
| 22 | `SaiNr-frog7_kalaeh a taro__S_88` | `…_S_88_W18` | `mari'` | `mari'-in` | `story/Saisiyat_Tong-he/SaiNr-frog7_kalaeh a taro_.json` rec 91 row 7: `mari'(-in)` | eng `take(-pf)` / zho `拿-受焦` (**no parentheses**) | a (suffix `-in` patient focus) | The gloss columns disagree on whether `-in` is optional. This is a different story and speaker from #20, and there is no note here, so the meaning of the parentheses is unstated. The morpheme is published as `AF.get` / `主焦.拿` (agent focus), which contradicts the word's own gloss marking patient focus. |

## 4. Data defects not about the variant policy

- **D1. Step 14 throws away the source's own sentence line.** `pipeline_sentences.py:659` rebuilds the S original FORM
  from the analysis (gloss) column whenever any word has a parenthesis. Bunun and Kanakanavu records have no sentence
  line anyway, so nothing is lost there. Rukai records do have one, and in all 6 Rukai rows (#13-18) the S "original"
  is now the segmented analysis line instead. Compare `20200528-FW-Ludwig_S_22`, which has no parenthesis: it is
  published from its sentence line as `lripadalrunga si udale.`, while `S_23` (#14) is published as `mua-lrumay-a
  iniane.` rather than the source's `(lu)mua lrumadha iniane.`. In #18 the published base contradicts the source
  sentence line.
- **D2. The sentence level has no "whole word was optional" guard**, though the word level does. This caused #15 (a
  stray ` .` in the base and the W tier lost) and #19 (base `().`).
- **D3. The Kavalan VOICEOVER hand fix is dead.** Its id changed (`S_80` became `S_138`), and its script runs only for
  Grammar (#19).
- **D4. Translations of the optional morpheme are cut out of the Chinese TRANSL**, leaving a space: `不，我 不會…` (#13)
  and `電話 傳了下去` (#18). The original text is kept in `@notes`.
- **D5. Saisiyat `S_209` sentence tier: glottal-stop apostrophes at the sentence edges became double quotes**
  (`"inaray … ahoe".`). The W tier is correct. `CodeAndDocs/quote_corrections.csv` (44 data rows) records this
  clean_xml apostrophe-pair-to-double-quote conversion. Its line 38 is this same sentence under an older id (`S_69`).
- **D6. `sentence/Bunun_Isbukun/63.json` largely duplicates the other Bunun files.** 613 of its 920 records have a
  word-form column identical to a record in another Bunun JSON. I compared form columns only, after unescaping `&lt;`
  and `&gt;` and dropping a trailing `\`. Both copies are published, so every Bunun example here appears twice. I
  found no mention of this in `readme.md` (`grep "63\.json\|63_S\|duplicate"` matched only the unrelated duplicate-id
  and borrow-segmentation passages).
- **D7. Morpheme tier.** In 7 distinct examples (#4, 5, 9, 13, 14, 17, 18) the morpheme FORMs have no glosses. My
  guess at the cause, not traced: the source gloss has one more piece than the base form. In #10 and #22 the morpheme
  gloss comes from elsewhere and disagrees with the record's own gloss (`due.to` vs `for`; `AF.get` vs `take(-pf)`).
- **D8. Kanakanavu original-tier PHON uses `*` for ʉ.** 2,819 of 16,412 original-tier PHON elements in
  `XML/Sentences/Kanakanavu/Kanakanavu.xml` contain `*`, e.g. `kumak**n`, and #11 has `*s*ʔ**n`. I observed this only
  and did not investigate it.
- **D9. Source defects:** the gloss columns disagree on optionality in #11 and #22. #17's English translation is cut
  off and it has no Chinese translation.
- **D10. Kanakanavu `3_S_1`** keeps a three-word parenthetical with its parentheses in both the original and standard S
  FORMs, and has no W tier (#11).
- **D11. Bunun standard S tier (observed, not judged).** It removes `=` but keeps `-` and `<…>`, e.g. standard base
  `ma-s<na>nava … ma-hansiap`, variant `nama-hansiap`, and `kaun-unsu`. I don't know whether this is intended.
- **D12. Documentation.** The README says 191 variants and I count 190. README line 496 still lists "optional
  sub-morphemic segments inside a word (`k(a)-u`, `a(ʉ)lʉ`, `(=dau)`; ~152 elements)" as open for manual review. Step
  14 now resolves these automatically, so that passage looks stale, but I have not verified the whole Processing
  section against `build.sh`.

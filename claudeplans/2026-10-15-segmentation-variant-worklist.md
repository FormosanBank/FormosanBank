# Published variant FORMs whose segmentation differs from their base

Candidates for the POL-028 amendment of 2026-10-15 ("Changes to segmentation
should also be treated as additional S-blocks, not merely an alt"). Published
before the amendment, under the wording it supersedes. **Not remediated by the
amendment**: each corpus needs its own ruling.

**How found.** Every `FORM kindOf="original"` with `@ver` in published
`Corpora/**/XML`, at FormosanBank `646653cd9bb42bceacbec0e9acaecf3f3b2ed1ef`, compared with the one base FORM of
its node: a candidate when the whitespace word count or the sequence of
segmentation marks (`-`, `=`, `<`, `>`) differs. This is a heuristic and
over-counts: a variant that differs only in a hyphen the source printed
inconsistently is listed even if no morpheme was added. The standard tier is
derived from the original (POL-028), so it is not listed separately.

**WakelinTexts' rows are a separate question.** They come from the article's
`( )` notation, which its key defines as "in data, probable discrepancy"
(`Corpora/WakelinTexts/README.md` line 102; line 263 of the same README calls
it optional material). Whether the amendment reaches that notation is open.

## Rulings (maintainer, 2026-10-15, decision page round 3)

Each corpus was traced to its source and build code first (22 NTU source examples, 8 Blust,
7 Utrecht, 4 Wakelin). Under the amendment as refined — split only where the optional
morpheme is glossed and the readings would be glossed differently:

| corpus | ruling | maintainer's words |
|---|---|---|
| NTUFormosanCorpus | **split** the optional-morpheme cases, including the Saisiyat "inaudible" ones; done by the agent working on NTU (branch `analysis/ntu-residual-gloss-shift`) | "I want to split into two sentences. But the agent that is currently working with NTU should handle that." |
| Blust-Thao-Dictionary | **keep** all 8 as variants (example words carry no glosses) | "keep" ×3 cards |
| UtrechtManuscriptWordList | **keep** the 6 variants (no word tier); 2 suspected defects (W121, W1054) await a look at the page | "keep" ×2 cards; "I need you to show me what's going on, with screenshots." |
| WakelinTexts | **not variants**: `( )` kept in the original tier's sentence FORM only, removed from words, morphemes and the standard tier; `mikabak-abay-u/mikabakabayu` publishes the segmented reading only, with a note | "Not variants. The parentheses should be retained in the original tier, removed in the standard tier." · "sentence FORM only, not the Ws or Ms." · "I meant the unsegmented version." |

**80 candidates:**

| corpus | node | count |
|---|---|---|
| Blust-Thao-Dictionary | S | 8 |
| NTUFormosanCorpus | S | 32 |
| NTUFormosanCorpus | W | 29 |
| UtrechtManuscriptWordList | S | 7 |
| WakelinTexts | W | 4 |

| corpus | node | id | base | variant | differs in |
|---|---|---|---|---|---|
| Blust-Thao-Dictionary | S | `blust-entry-p0442-s007` | `m-alhus` | `k-m-alhus` | morpheme marks |
| Blust-Thao-Dictionary | S | `blust-entry-p0589-s003` | `masa-rima` | `masay rima` | word count |
| Blust-Thao-Dictionary | S | `blust-ex-p0446-e014` | `cicu kan mamuri` | `cicu kan ma-mamuri` | morpheme marks |
| Blust-Thao-Dictionary | S | `blust-ex-p0474-e015` | `yaku masug-kitaz ihu` | `yaku masug-kitaz ihu-n` | morpheme marks |
| Blust-Thao-Dictionary | S | `blust-ex-p0578-e010` | `manu sa i-zay a aniamin` | `manu-manu sa i-zay a aniamin` | morpheme marks |
| Blust-Thao-Dictionary | S | `blust-ex-p0588-e002` | `m-ihu a shi-a-ucuc ma-quliush mas nak` | `m-ihu a shi-a-ucuc-an ma-quliush mas nak` | morpheme marks |
| Blust-Thao-Dictionary | S | `blust-ex-p0821-e002` | `haya wa rusaw m-acay ranaw-in` | `haya wa rusaw m-acay kit-ranaw-in` | morpheme marks |
| Blust-Thao-Dictionary | S | `blust-ex-p0821-e003` | `i-suhúy saran yanan sa ranaw m-acay ranaw-in` | `i-suhúy saran yanan sa ranaw m-acay kit-ranaw-in` | morpheme marks |
| NTUFormosanCorpus | S | `26_S_4` | `ma-s<na>nava hai nautu ma-hansiap malas-bunun.` | `ma-s<na>nava hai nautu na=ma-hansiap malas-bunun.` | morpheme marks |
| NTUFormosanCorpus | W | `26_S_4_W3` | `ma-hansiap` | `na=ma-hansiap` | morpheme marks |
| NTUFormosanCorpus | S | `28_S_6` | `kangavas hai mahtu=in kaun-un=su.` | `kangavas=an hai mahtu=in kaun-un=su.` | morpheme marks |
| NTUFormosanCorpus | W | `28_S_6_W0` | `kangavas` | `kangavas=an` | morpheme marks |
| NTUFormosanCorpus | S | `28_S_7` | `kangavas hai mahtu=in kaun-un=ta.` | `kangavas=an hai mahtu=in kaun-un=ta.` | morpheme marks |
| NTUFormosanCorpus | W | `28_S_7_W0` | `kangavas` | `kangavas=an` | morpheme marks |
| NTUFormosanCorpus | S | `30_S_5` | `nau tu ma-klang i-nata.` | `nau tu na=ma-klang i-nata.` | morpheme marks |
| NTUFormosanCorpus | W | `30_S_5_W2` | `ma-klang` | `na=ma-klang` | morpheme marks |
| NTUFormosanCorpus | S | `34_S_7` | `kalin-lumah=in 'iv'iv=a.` | `kalin-na-lumah=in 'iv'iv=a.` | morpheme marks |
| NTUFormosanCorpus | W | `34_S_7_W0` | `kalin-lumah=in` | `kalin-na-lumah=in` | morpheme marks |
| NTUFormosanCorpus | S | `36_S_1` | `i-sia ku'pu davus=an hai mais sak-un hai ma-'ansum.` | `i-sia ku'pu davus=an hai mais sak-un hai ma-'ansum=dau.` | morpheme marks |
| NTUFormosanCorpus | W | `36_S_1_W7` | `ma-'ansum.` | `ma-'ansum=dau.` | morpheme marks |
| NTUFormosanCorpus | S | `36_S_3` | `ta<i>'aza tu 'utung=an hai cis'uni ma-simuav tu bunun min-'utung.` | `ta<i>'aza tu 'utung=an=dau hai cis'uni ma-simuav tu bunun min-'utung.` | morpheme marks |
| NTUFormosanCorpus | W | `36_S_3_W2` | `'utung=an` | `'utung=an=dau` | morpheme marks |
| NTUFormosanCorpus | S | `36_S_15` | `tupa cina tu ma-si-tuhas hai na=ku-sia Tainan kuzakuza.` | `tupa=dau cina tu ma-si-tuhas hai na=ku-sia Tainan kuzakuza.` | morpheme marks |
| NTUFormosanCorpus | W | `36_S_15_W0` | `tupa` | `tupa=dau` | morpheme marks |
| NTUFormosanCorpus | S | `36_S_16` | `mi-kua kasu tu mu-cingkul?` | `mi-kua=dau kasu tu mu-cingkul?` | morpheme marks |
| NTUFormosanCorpus | W | `36_S_16_W0` | `mi-kua` | `mi-kua=dau` | morpheme marks |
| NTUFormosanCorpus | S | `48_S_22` | `cis-maz kasu ma-subnuh` | `cis-maz=a kasu ma-subnuh` | morpheme marks |
| NTUFormosanCorpus | W | `48_S_22_W0` | `cis-maz` | `cis-maz=a` | morpheme marks |
| NTUFormosanCorpus | S | `63_S_460` | `ma-s<na>nava hai nautu ma-hansiap malas-bunun.` | `ma-s<na>nava hai nautu na=ma-hansiap malas-bunun.` | morpheme marks |
| NTUFormosanCorpus | W | `63_S_460_W3` | `ma-hansiap` | `na=ma-hansiap` | morpheme marks |
| NTUFormosanCorpus | S | `63_S_478` | `kangavas hai mahtu=in kaun-un=su.` | `kangavas=an hai mahtu=in kaun-un=su.` | morpheme marks |
| NTUFormosanCorpus | W | `63_S_478_W0` | `kangavas` | `kangavas=an` | morpheme marks |
| NTUFormosanCorpus | S | `63_S_479` | `kangavas hai mahtu=in kaun-un=ta.` | `kangavas=an hai mahtu=in kaun-un=ta.` | morpheme marks |
| NTUFormosanCorpus | W | `63_S_479_W0` | `kangavas` | `kangavas=an` | morpheme marks |
| NTUFormosanCorpus | S | `63_S_499` | `nau tu ma-klang i-nata.` | `nau tu na=ma-klang i-nata.` | morpheme marks |
| NTUFormosanCorpus | W | `63_S_499_W2` | `ma-klang` | `na=ma-klang` | morpheme marks |
| NTUFormosanCorpus | S | `63_S_537` | `kalin-lumah=in 'iv'iv=a.` | `kalin-na-lumah=in 'iv'iv=a.` | morpheme marks |
| NTUFormosanCorpus | W | `63_S_537_W0` | `kalin-lumah=in` | `kalin-na-lumah=in` | morpheme marks |
| NTUFormosanCorpus | S | `63_S_552` | `i-sia ku'pu davus=an hai mais sak-un hai ma-'ansum.` | `i-sia ku'pu davus=an hai mais sak-un hai ma-'ansum=dau.` | morpheme marks |
| NTUFormosanCorpus | W | `63_S_552_W7` | `ma-'ansum.` | `ma-'ansum=dau.` | morpheme marks |
| NTUFormosanCorpus | S | `63_S_554` | `ta<i>'aza tu 'utung=an hai cis'uni ma-simuav tu bunun min-'utung.` | `ta<i>'aza tu 'utung=an=dau hai cis'uni ma-simuav tu bunun min-'utung.` | morpheme marks |
| NTUFormosanCorpus | W | `63_S_554_W2` | `'utung=an` | `'utung=an=dau` | morpheme marks |
| NTUFormosanCorpus | S | `63_S_566` | `tupa cina tu ma-si-tuhas hai na=ku-sia Tainan kuzakuza.` | `tupa=dau cina tu ma-si-tuhas hai na=ku-sia Tainan kuzakuza.` | morpheme marks |
| NTUFormosanCorpus | W | `63_S_566_W0` | `tupa` | `tupa=dau` | morpheme marks |
| NTUFormosanCorpus | S | `63_S_567` | `mi-kua kasu tu mu-cingkul?` | `mi-kua=dau kasu tu mu-cingkul?` | morpheme marks |
| NTUFormosanCorpus | W | `63_S_567_W0` | `mi-kua` | `mi-kua=dau` | morpheme marks |
| NTUFormosanCorpus | S | `63_S_686` | `cis-maz kasu ma-subnuh?` | `cis-maz=a kasu ma-subnuh?` | morpheme marks |
| NTUFormosanCorpus | W | `63_S_686_W0` | `cis-maz` | `cis-maz=a` | morpheme marks |
| NTUFormosanCorpus | S | `3_S_1` | `ʉsʉ'ʉ-ʉn na takuacapa paici Cuma (tia iima cuma).` | `ʉsʉ'ʉ-ʉn=maku na takuacapa paici Cuma (tia iima cuma).` | morpheme marks |
| NTUFormosanCorpus | S | `3_S_38` | `cʉ'ʉrʉ-ʉn nguain vuanʉ, 'acuu ara-vavuru` | `cʉ'ʉrʉ-ʉn nguain=kee vuanʉ, 'acuu ara-vavuru` | morpheme marks |
| NTUFormosanCorpus | W | `3_S_38_W1` | `nguain` | `nguain=kee` | morpheme marks |
| NTUFormosanCorpus | S | `20200508-CL-7_S_19` | `ini, kai naw=siulri mua musuane.` | `ini, kai naw=lri-siulri mua musuane.` | morpheme marks |
| NTUFormosanCorpus | W | `20200508-CL-7_S_19_W2` | `naw=siulri` | `naw=lri-siulri` | morpheme marks |
| NTUFormosanCorpus | S | `20200528-FW-Ludwig_S_23` | `mua-lrumay-a iniane.` | `lu-mua-lrumay-a iniane.` | morpheme marks |
| NTUFormosanCorpus | W | `20200528-FW-Ludwig_S_23_W0` | `mua-lrumay-a` | `lu-mua-lrumay-a` | morpheme marks |
| NTUFormosanCorpus | S | `20200528-FW-Ryan_S_19` | `kuini la-adhadhame ma-tuase-nga .` | `kuini la-adhadhame ma-tuase-nga ngi-palay.` | morpheme marks |
| NTUFormosanCorpus | S | `20200529-FW-Lixing-1_S_17` | `ki-a-malra patuelre kay kidringi.` | `ki-a-malra-nga patuelre kay kidringi.` | morpheme marks |
| NTUFormosanCorpus | W | `20200529-FW-Lixing-1_S_17_W0` | `ki-a-malra` | `ki-a-malra-nga` | morpheme marks |
| NTUFormosanCorpus | S | `20200529-FW-Lixing-1_S_23` | `w-a-iluku tara-tulru kay la-lasu ku karadrare.` | `w-a-iluku tara-mu-tulru kay la-lasu ku karadrare.` | morpheme marks |
| NTUFormosanCorpus | W | `20200529-FW-Lixing-1_S_23_W1` | `tara-tulru` | `tara-mu-tulru` | morpheme marks |
| NTUFormosanCorpus | S | `20200529-FW-Ryan_S_6` | `kay y-a-kay danne kay la-situ pa-twaramarama kay dinva.` | `kay y-a-kay danne kay la-situ ma-pa-twaramarama kay dinva.` | morpheme marks |
| NTUFormosanCorpus | W | `20200529-FW-Ryan_S_6_W5` | `pa-twaramarama` | `ma-pa-twaramarama` | morpheme marks |
| NTUFormosanCorpus | S | `KavNr-frog_abas_S_138` | `().` | `(VOICEOVERmai=ti).` | morpheme marks |
| NTUFormosanCorpus | S | `SaiNr-frog5__awi_ a basi__S_202` | `hiza ka, a korkoring ma' sahae' ila sa'oewaz sahae' ila isaa o ray, 'ima, 'izo', ka, hinolaong.` | `hiza ka, a korkoring ma' sahae' ila sa'oewaz sahae' ila isaa o ray, 'ima, 'izo', ka, hinolaong-an.` | morpheme marks |
| NTUFormosanCorpus | W | `SaiNr-frog5__awi_ a basi__S_202_W16` | `hinolaong.` | `hinolaong-an.` | morpheme marks |
| NTUFormosanCorpus | S | `SaiNr-frog5__awi_ a basi__S_209` | `"inaray hinolaw langi hayza ka kaehoey, sa, korkoring, sahae' ila ila haw ray hinolaong, ki, ahoe".` | `"inaray hinolaw langi hayza ka kaehoey, sa, korkoring, sahae' ila ila haw ray hinolaong-an, ki, ahoe".` | morpheme marks |
| NTUFormosanCorpus | W | `SaiNr-frog5__awi_ a basi__S_209_W13` | `hinolaong,` | `hinolaong-an,` | morpheme marks |
| NTUFormosanCorpus | S | `SaiNr-frog7_kalaeh a taro__S_88` | `wae'ae', 'ima sakosiza ka mae'iyaeh 'ima sahae' ray waSal, a k ki 'aehoe', m 'aehoe' ma' sahae' 'oyae' mari' noka mae'iyaeh.` | `wae'ae', 'ima sakosiza ka mae'iyaeh 'ima sahae' ray waSal, a k ki 'aehoe', m 'aehoe' ma' sahae' 'oyae' mari'-in noka mae'iyaeh.` | morpheme marks |
| NTUFormosanCorpus | W | `SaiNr-frog7_kalaeh a taro__S_88_W18` | `mari'` | `mari'-in` | morpheme marks |
| UtrechtManuscriptWordList | S | `W103` | `ratta kivadoch` | `ratta ki vadoch` | word count |
| UtrechtManuscriptWordList | S | `W121` | `pasagoualalingaua ng` | `pasagoualalingauang` | word count |
| UtrechtManuscriptWordList | S | `W138` | `pasiougingang` | `pasi ongingang` | word count |
| UtrechtManuscriptWordList | S | `W230` | `kinikapateijang kitbong` | `ki nikapateijang ki tbong` | word count |
| UtrechtManuscriptWordList | S | `W564` | `kaki` | `ka, ki` | word count |
| UtrechtManuscriptWordList | S | `W611` | `heso, so` | `ho io, so` | word count |
| UtrechtManuscriptWordList | S | `W1054` | `vougot` | `vougot vuxot` | word count |
| WakelinTexts | W | `S10W1` | `puken-en` | `puken` | morpheme marks |
| WakelinTexts | W | `S18W3` | `kan` | `kan-u` | morpheme marks |
| WakelinTexts | W | `S21W1` | `manuyung-e` | `manuyung` | morpheme marks |
| WakelinTexts | W | `S51W1` | `mikabak-abay-u` | `mikabakabayu` | morpheme marks |

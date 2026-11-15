# Where the data was collected: NTUFormosanCorpus and ILRDF_Dicts

Read-only research, 2026-11-07. Every file was read from the worktree at current `main`,
`/tmp/claude-1000/-workspace-FormosanBank/e78edf4a-c5b9-400e-864e-ff685648c37f/scratchpad/fb-main`
(HEAD `2a345f0d9`). No web access. Nothing in any repo was changed.

**Deviation to report.** While searching I wrote one scratch file that the brief does not allow:
`/tmp/claude-1000/-workspace-FormosanBank/e78edf4a-c5b9-400e-864e-ff685648c37f/scratchpad/ntu_free_hits.txt`
(188,119 bytes: the raw output of a keyword search over the NTU translations and notes). It is in the
scratchpad, not in any repo. I left it in place and did not delete it. It can be deleted.

How to read the NTU evidence: each NTU JSON has a top-level `meta` object and a `glosses` list. Each
entry `glosses[i]` is `[record number, {ori, gloss, free, meta, ...}]`. `free` holds lines that start
with `#e` (English translation), `#c` (Chinese translation) or `#n` (a transcriber's note). Below,
`glosses[i][1].free` plus the line's prefix tells you exactly where a quote is. The per-record `meta` is
identical to the file's `meta` in all 41,509 records (checked by script: 0 records differ).

---

### NTUFormosanCorpus

- Dialect label(s) in XML (xml:lang + dialect, with file counts), read from all 193 `XML/**/*.xml` `<TEXT>` elements:
  ami Coastal 18 · bnn Junqun 14 · ckv Kavalan 31 · dru Wutai 23 · szy Sakizaya 16 · tay Wenshui 11 ·
  trv Tegudaya 27 (Seediq, since the dialect is not Truku) · tsu Tsou 12 · xnb Kanakanavu 21 · xsy Saisiyat 20.
  The `<TEXT>` element carries only `id`, `citation` ("NTU Corpus of Formosan Languages" in all 193),
  `BibTeX_citation` (empty in all 193), `copyright`, `xml:lang` and `dialect`. There is **no `source`
  attribute, and no place on any `<TEXT>`.**
- README statement about place:
  `/tmp/claude-1000/-workspace-FormosanBank/e78edf4a-c5b9-400e-864e-ff685648c37f/scratchpad/fb-main/Corpora/NTUFormosanCorpus/README.md`
  lines 17–33 give NTU's source-folder names (`story/Amis_Ciwkangan`, `story/Atayal_Mayrinax`, `Bunun_Isbukun`,
  `story/Kavalan_Xinshe`, `Rukai_Vedai`, `story/Saisiyat_Tong-he`, `Seediq_Tgdaya`, `story/Tsou_Tsou`, ...), and lines 28–33:
  "NTU's folder names give the dialect as NTU names it: [dialects.csv](../../dialects.csv) lists Ciwkangan, Mayrinax,
  Isbukun, Vedai and Tgdaya as other names of Coastal, Wenshui, Junqun, Wutai and Tegudaya. For Kavalan (folder
  `Xinshe`) and Saisiyat (folder `Tong-he`) the XML records the language name as the dialect."
  Lines 43 and 45: Sentences are "individual sentences recorded during fieldwork", Stories "narratives recorded
  during fieldwork". **The README never says where the fieldwork was done.**
- Sources searched:
  - all 378 NTU JSONs under
    `/tmp/claude-1000/-workspace-FormosanBank/e78edf4a-c5b9-400e-864e-ff685648c37f/scratchpad/fb-main/Corpora/NTUFormosanCorpus/CodeAndDocs/{grammar,sentence,story}/`:
    every `meta` field dumped in full (`type`, `language`, `speaker`, `collected`, `topic`, `revised`, `video`);
  - every `free` line (`#e`/`#c`/`#n`) searched by script for 村|部落|社區|鄉|縣|鎮|里|出生|故鄉|家鄉|住在|發音人|採集|錄音,
    for born|hometown|village|recorded|collected|informant|Taipei, and for county/township/village names
    relevant to each language; every hit read, and the context around the relevant ones read;
  - all 193 XML `<TEXT>` attributes;
  - `source_release.tsv`, `source_snapshot.json`, `provenance.json`, `source_repairs.xml`, the other `CodeAndDocs/*.tsv`,
    `pipeline/*.tsv`, `pipeline/README.md`, `qa/README.md`: grep for place terms. Only hits are folder names
    (`story/Kavalan_Xinshe/...`, `story/Saisiyat_Tong-he/...`, `story/Amis_Ciwkangan/...`).
  - There is no NTU dev repo among the `/workspace/Formosan-*` siblings.
- What the `meta.speaker` field holds: a masked name, sometimes sex and birth year, never a place
  (e.g. `"潘〇〇, male, 1933"`, `"顏〇〇, 1950"`, `"柯〇〇, female, 1961"`). `meta.collected` is a date. Grammar
  JSONs have no `speaker` or `collected` at all (only `topic`, a chapter title such as `"第三章 詞彙與構詞"`).
- **The place information lives in `meta.language`**, a comma-separated string "Chinese language name, English
  language name, third item". In some files the third item is a place. Full tally (all 378 JSONs):

  | NTU folder | `meta.language` value (verbatim) | JSONs |
  |---|---|---:|
  | Amis_Ciwkangan | `阿美語, Amis, Ciwkangan` | 12 |
  | Amis_Ciwkangan | `阿美語, Amis, Ciwkangan (長光)` | 1 |
  | Amis_Ciwkangan | `阿美語, Amis, Ciwkangan(長光)` | 1 |
  | Amis_Ciwkangan | `阿美語, Amis, Ciwkangan(台東縣長光社區)` | 4 |
  | Atayal_Mayrinax | `泰雅語, Atayal, Mayrinax` | 10 |
  | Atayal_Mayrinax | `泰雅語, Atayal, Mayrinax (汶水)` | 1 |
  | Bunun_Isbukun | `郡群布農語, Bunun, Isbukun` | 93 |
  | Kanakanavu_Kanakanavu | `卡那卡那富語, Kanakanavu, Kanakanavu` | 42 |
  | Kavalan_Xinshe | `噶瑪蘭語, Kavalan, Xinshe (新社)` | 17 |
  | Kavalan_Xinshe | `噶瑪蘭語, Kavalan, Xinshe(新社)` | 12 |
  | Kavalan_Xinshe | `噶瑪蘭語, Kavalan, Kavalan` | 1 |
  | Kavalan_Xinshe | `噶瑪蘭語, Kavalan, Pear Story` | 1 |
  | Rukai_Vedai | `霧台魯凱語, Rukai, Budai` | 54 (all sentence JSONs) |
  | Rukai_Vedai | `魯凱語, Rukai, Vedai` | 21 |
  | Rukai_Vedai | `魯凱語, Rukai, Budai` | 1 |
  | Saisiyat_Tong-he | `賽夏語, Saisiyat, Saisiyat` | 17 |
  | Saisiyat_Tong-he | `賽夏語, Saisiyat, saisiyat` | 1 |
  | Saisiyat_Tong-he | `賽夏語, Saisiyat, Saisiayt` | 1 |
  | Saisiyat_Tong-he | `賽夏語, Saisiyat, Tong-he(東河)` | 1 |
  | Sakizaya_Sakizaya | `撒奇萊雅語, Sakizaya, Sakizaya` | 32 |
  | Seediq_Tgdaya | `賽德克語, Seediq, Tgdaya` | 43 |
  | Tsou_Tsou | `鄒語, Tsou, TapangU` | 7 |
  | Tsou_Tsou | `鄒語, Tsou, Tfya` | 5 |

  **None of this `meta.language` text reaches the published XML** (grep of `XML/`: `台東縣長光社區` 0 files, `Tfya` 0 files).
- Second source of place information: the story texts themselves. Several speakers say where they are from, or
  where "here" is, and some transcriber notes (`#n`) say so too. These are quoted per language below. They are
  translations (`#e`/`#c`) or notes (`#n`) inside the NTU data, so they are the corpus's own source, but they
  describe single speakers or single texts, not the whole language.

#### NTU Amis (ami, dialect Coastal, 18 XML files, all Stories)
All files: `/tmp/claude-1000/-workspace-FormosanBank/e78edf4a-c5b9-400e-864e-ff685648c37f/scratchpad/fb-main/Corpora/NTUFormosanCorpus/CodeAndDocs/story/Amis_Ciwkangan/`
- Files with place info in metadata: **18 of 18** name `Ciwkangan`; 6 of 18 also give Chinese (`長光`); 4 of 18 give county and community (`台東縣長光社區`).
- LOCATION EVIDENCE:
  - "阿美語, Amis, Ciwkangan(台東縣長光社區)" — `meta.language` of `Amis_Nr-frog_minzhu.json`, `Amis_Nr-frog_ofad.json`, `Amis_Nr-frog_zuomei.json`, `Amis_Nr-intro_ofad.json`
    applies to: those 4 files (speakers 嚴〇〇 female; 陳〇〇 male; 嚴〇〇〇 female; 陳〇〇 male)
    places named: 台東縣 (county) / 長光社區 (community); romanized Ciwkangan
  - "阿美語, Amis, Ciwkangan (長光)" — `meta.language` of `Amis_Conv-farming_marang_furayang.json`; "阿美語, Amis, Ciwkangan(長光)" — `meta.language` of `Amis_Nr-custom_Liu.json`
    applies to: those 2 files. places named: 長光 / Ciwkangan
  - "阿美語, Amis, Ciwkangan" — `meta.language` of the other 12 files. applies to: those 12. places named: Ciwkangan (no Chinese in these files)
  - "#e I was born in Ciwkangan." / "#c 我出生在長光這裡。" — `Amis_Nr-intro_Panay.json` `glosses[4][1].free` (record 5)
    applies to: speaker 李〇〇, female, 1949 (her files: `Amis_Conv-talking_tamih_panay`, `Amis_Nr-crab_panay`, `Amis_Nr-intro_Panay`, `Amis_Nr-peanut_panay`, `Amis_Nr-pear_panay`; matched by the masked name + year in `meta.speaker`, an inference)
    places named: 長光 / Ciwkangan. The Chinese says "here in 長光" (這裡).
  - "#e My hometown is in Ciwkangan, in Taitung, in Kakacawan." / "#c 我的故鄉在台東長濱長光。" — `Amis_Nr-intro_ofad.json` `glosses[7][1].free` (record 8); same file record 13: "#c 我從小就在長光部落長大，一直到十三歲。"; record 34: "#e After I got married, I came to Taipei immediately." / "#c 我結婚之後沒多久就到台北。"
    applies to: speaker 陳〇〇, male (files `Amis_Nr-frog_ofad`, `Amis_Nr-intro_ofad`)
    places named: 台東 (county) / 長濱 = Kakacawan (township) / 長光 = Ciwkangan (village/部落); later lived in 台北
  - "#e Yes, Ciwkangan is our tribe." / "#c 是的，長光是我們的部落。" — `Amis_Nr-custom_Liu.json` `glosses[1][1].free` (record 2)
    applies to: speaker 劉〇〇, male (this one file). places named: 長光 / Ciwkangan
- Observed vs inferred: The county/community wording is observed only in 4 files; that the other 14 files' "Ciwkangan" means the same 台東縣長光社區 is a reading of the same string, not stated for those files. Where each recording was made is not stated; "長光這裡" in `intro_Panay` suggests that one was recorded in 長光 (inferred). The `intro_ofad` speaker says he moved to Taipei, so where his texts were recorded is unknown.
- Proposed README addition: "NTU's metadata places the Amis stories in Ciwkangan, 台東縣長光社區 (`meta.language` of 4 story JSONs, e.g. `story/Amis_Ciwkangan/Amis_Nr-intro_ofad.json`); one speaker gives his hometown as 台東長濱長光 (`Amis_Nr-intro_ofad.json`, record 8)."

#### NTU Atayal (tay, dialect Wenshui, 11 XML files, all Stories)
All files: `.../CodeAndDocs/story/Atayal_Mayrinax/` (full prefix as for Amis)
- Files with place info in metadata: 1 of 11 (`Mayrinax (汶水)`); all 11 carry a transcriber note naming 清安村.
- LOCATION EVIDENCE:
  - "泰雅語, Atayal, Mayrinax (汶水)" — `meta.language` of `AtaNr-moving_Takun.json`. applies to: that file. places named: 汶水
  - "#n 汶水泰雅不同村之間有b/v, c/s等發音上的差異。清安村發音人較年輕一輩的詞彙已無b和c的音，但較年長的發音人的部分詞彙仍保留b和c的音。此篇語料係依照發音人的發音而給予標記。" — the same note in **all 11 files**, e.g. `AtaNr-dailylife1_Iwan.json` `glosses[0][1].free` (record 1); also dailylife2, dailylife3_Tauyu, hunting1_Kainu, hunting2_Buyung, hunting3_Takun, moving_Kainu, moving_Takun, proposal_Takun, sowing_Kainu, weaving_Kagaw. It is also in the published XML (11 files contain `清安村發音人`).
    applies to: all 11 files (it speaks of "清安村發音人" generally)
    places named: 清安村 (village)
  - "#n 此處腔調重的族群指的是Matu'uwal(即清安村、此篇語料發音人的方言)，由於該方言保留較多的喉塞音，因此聽起來較艱澀難懂。Matu'au的方言(清安村族人稱其為"澤敖利")則是較少喉塞音，因此聽起來較滑順、溫和。" — `AtaNr-moving_Takun.json` `glosses[35][1].free` (record 36)
    applies to: the speaker of this file (劉〇〇, male, 1946, "Takun": files hunting3_Takun, moving_Takun, proposal_Takun)
    places named: 清安村. Says outright that this text's speaker speaks the 清安村 dialect.
  - "#c 然後就到了Sugu'ivu'，然後Sugu'ivu'再往下就是我們所稱呼的Savawqil，也就是我們現在所在的地方。" plus "#n "我們現在所在的地方"，指的是此篇語料所採集之處。" — `AtaNr-moving_Takun.json` `glosses[145][1].free` (record 146). Also record 121, a note: "#n 發音人所指的Mavatu'an其實是部落聚集人口最多處還要再往深山上去的地方，為該族族人最早在此地的住處。現人口最多處(草莓園、餐廳前後較平的路段，為後來停留開墾田地處)稱為Savawqil。"
    applies to: the recording `AtaNr-moving_Takun`. **This is the only explicit statement of a recording place in the NTU data.**
    places named: Savawqil (部落), where the text was collected
  - "#c 之所以叫Mabatuan，真的是因為我們祖先曾經住在叫Mabatuan的地方，後來才搬到現在的大坪這裡。" — `AtaNr-moving_Kainu.json` `glosses[115][1].free` (record 116); also record 138: "#c 我真的覺得我們這個叫做大坪的地方，生活真的很不好。"
    applies to: speaker 劉〇〇, male, 1941 ("Kainu": hunting1_Kainu, moving_Kainu, sowing_Kainu). places named: 大坪 ("here")
  - "#e When I was a child, I was born here in the tribe of Mavatu'an." / "#c 我小時候時出生在馬都安部落。" — `AtaNr-dailylife3_Tauyu.json` `glosses[6][1].free` (record 7); record 57: "#c 在馬都安這裡的所有女人，就算是長輩，都非常勤奮地工作。"
    applies to: speaker 龍〇〇, female, 1942 (this one file). places named: 馬都安部落 / Mavatu'an ("here")
- Observed vs inferred: The 清安村 note is observed in all 11 files, but only `moving_Takun` ties it to that file's speaker. That Savawqil, 大坪 and 馬都安 are within 清安村 is not stated in the data. Whether the other speakers (Iwan, Buyung, Kagaw) are from 清安村 is implied by the general note, not stated per speaker.
- Proposed README addition: "NTU's Atayal (Mayrinax/汶水) stories come from speakers of 清安村 (transcriber's note in all 11 story JSONs, e.g. `story/Atayal_Mayrinax/AtaNr-dailylife1_Iwan.json`, record 1); `AtaNr-moving_Takun.json` (record 146) says that text was collected at Savawqil."

#### NTU Bunun (bnn, dialect Junqun, 14 XML files: 1 Sentences (built from 80 JSONs) + 13 Stories)
Files: `.../CodeAndDocs/sentence/Bunun_Isbukun/` and `.../CodeAndDocs/story/Bunun_Isbukun/`
- Files with place info in metadata: **0 of 93 JSONs.** `meta.language` is always `郡群布農語, Bunun, Isbukun` (a dialect name). Speakers are all `顏〇〇` / `顏〇` / `顏` with birth years 1943, 1944, 1950, 1958; dates 2016-03 to 2017-01.
- LOCATION EVIDENCE: none that describes the speakers or the recording place. Content hits, all weak:
  - "#c 我是桃源的布農人。" / "#e I'm a Bunun from Taoyuan (Kalavung)." — `sentence/Bunun_Isbukun/63.json` `glosses[890][1].free` (record 891). It is an elicited example: the next record (892) is "#c 我是真正的布農人。" and record 893 is "#c 我是來自歐洲的人。 / #e I come from Europe." So it says nothing reliable about the speaker.
  - "#n 假設我在高雄，老師在桃源，要到台北，這句是指高雄出發" — `sentence/Bunun_Isbukun/19.json` `glosses[0][1].free` (record 1). A hypothetical set up to elicit a sentence.
  - "#c 我記得常來到我們部落的學生。" / "#e I remember the students who came to the village." — `sentence/Bunun_Isbukun/61.json` `glosses[3][1].free` (record 4). Elicited; the village is not named.
- Could not find: where the 2016–2017 sessions took place, and where the 顏 family speakers live. Not in any committed file.
- Proposed README addition: "NTU's Bunun data names no place; its metadata gives only the dialect (Isbukun) and the speakers' birth years."

#### NTU Kanakanavu (xnb, dialect Kanakanavu, 21 XML files: 1 Grammar (18 JSONs) + 1 Sentences (5 JSONs) + 19 Stories)
Files: `.../CodeAndDocs/{grammar,sentence,story}/Kanakanavu_Kanakanavu/`
- Files with place info in metadata: **0 of 42 JSONs** (`卡那卡那富語, Kanakanavu, Kanakanavu` in all).
- LOCATION EVIDENCE (story content):
  - "#e I live in Namasia." / "#c 我是那瑪夏的人。" — `story/.../kkvNr_hunting1_Muu.json` `glosses[0][1].free` (record 1); record 4: "#e That’s it. I was born here." / "#c 就這樣我是在這裡出生的。"
    applies to: speaker 翁〇, male ("Mu'u"; meta years 1932 or 1947; files fishing_Muu, puratu_Muu, domestic_troubles_Muu, farming_Muu, hunting1_Muu, millet_Muu, sad_song_Muu). places named: 那瑪夏 / Namasia
  - "#e During the rice ceremony, I went from NU'Uvana to Tanganua to visit my older sister Miciku." / "#c 若要米貢的時候，我就從瑪雅里去達卡努瓦里去拜訪我姊姊Miciku。" — `story/.../kkvNr_mikon_Kuatu.json` `glosses[2][1].free` (record 3)
    applies to: speaker 蕭〇〇〇, female, 1941 ("KuatU": life_Kuatu, mikon_Kuatu, sowing_Kuatu); her sister Paicʉ (翁〇〇〇, female, 1939: family_Paicu, sowing_Paicu). places named: 瑪雅里 (KuatU's), 達卡努瓦里 (her sister's)
  - "#n 瑪雅里指的是高雄那瑪夏區的瑪雅里。" — `story/.../kkvNr_family_Paicu.json` `glosses[45][1].free` (record 46). This explains where the brother's wife came from, not the speaker. places named: 高雄 / 那瑪夏區 / 瑪雅里
  - "#c 那般之後，卡那卡那富族人就住在那瑪夏這裡。" — `story/.../kkvNr-story_pani.json` `glosses[133][1].free` (record 134); and "#e At that time, our tribe Namaasia was called Sanminsiang." / "#c 當時我們的部落納瑪夏被稱為三民鄉。" — `kkvNr_the man from china_Pani.json` `glosses[18][1].free` (record 19)
    applies to: speaker 孔〇〇, male, 1951 ("Pani": story_pani, fishing_Pani, the man from china_Pani). places named: 那瑪夏 / 三民鄉 ("here")
  - Elicited sentences in `sentence/Kanakanavu_Kanakanavu/1.json`, e.g. "#c 當我第三次來到那瑪夏時，我遇見了'angai叔叔。" (record 188) and "#c 我來那瑪夏第二次而已。" (record 60). They are written from a visitor's point of view; that the elicitation happened in 那瑪夏 is an inference.
- Grammar subcorpus: the JSONs are example sentences from a grammar book (note in `grammar/.../ap3.json`: "#n 《卡那卡那富語語法概論》 長篇語料三　楠梓仙溪的故事"). The book's preface or consultant list is not committed here. The examples name 那瑪夏 (e.g. `A1.json` record 1 "#c 我的故鄉在那瑪夏。"), but they are teaching examples, not speaker metadata.
- Proposed README addition: "NTU's Kanakanavu metadata names no place; in the stories, speakers say they live in 那瑪夏 (e.g. `story/Kanakanavu_Kanakanavu/kkvNr_hunting1_Muu.json`, record 1) and name 瑪雅里 and 達卡努瓦里 (`kkvNr_mikon_Kuatu.json`, record 3)."

#### NTU Kavalan (ckv, dialect Kavalan, 31 XML files, all Stories)
Files: `.../CodeAndDocs/story/Kavalan_Xinshe/`
- Files with place info in metadata: **29 of 31** (`Xinshe (新社)` 17, `Xinshe(新社)` 12). The 2 without a place: `KavCon-relatives_buya_ngengi.json` (`Kavalan`) and `KavNr-pear_imuy.json` (`Pear Story`). The folder name `Kavalan_Xinshe` covers all 31.
- LOCATION EVIDENCE:
  - "噶瑪蘭語, Kavalan, Xinshe (新社)" / "噶瑪蘭語, Kavalan, Xinshe(新社)" — `meta.language` of 29 files. applies to: those 29. places named: 新社 / Xinshe
  - "#e Like in the past when we were still in our village, in Xinshe." / "#c 就像過去我們還在故鄉,在新社時。" — `KavCon-relatives_buya_ngengi.json` `glosses[942][1].free` (record 943). Same file, record 371: "#c 有在台北的,有在板橋的,有在新莊的。"; record 348: "#c 我們為什麼要成立這個同鄉會?"
    applies to: this conversation (speakers buya 謝〇〇 male 1957 and ngengi 林〇〇 female 1941). Hometown 新社; now living in the Taipei area.
  - "#e We will work hard here in Taipei." / "#c 我們在台北這裡會認真工作。" — `KavNr-ancestor_buya.json` `glosses[178][1].free` (record 179)
    applies to: this recording (speaker buya). places named: 台北 ("here")
  - "#e I think our Harvest Festival here (in Taipei) is different." + "#n 指台北的豐年祭和故鄉的不一樣。" — `kavCon-speech_buya_syulan.json` `glosses[54][1].free` (record 55); record 57: "#c (和)我們新社部落的(豐年祭)不一樣。"
    applies to: this recording. places named: 台北 ("here"), 新社部落 (hometown)
  - "#e All of us will go back to Xinshe tomorrow." / "#c 我們明天全部要回去新社。" — `KavCon-home_buya_imuy.json` `glosses[152][1].free` (record 153)
    applies to: this recording (made somewhere other than 新社, inferred). places named: 新社
  - "#e I said to you, ‘How was the earthquake here in PakteRung?’" / "#c 我跟你說，「新社這裡的地震情形是如何」。" — `KavCon-earthquake_abas_haciang.json` `glosses[12][1].free` (record 13)
    applies to: this recording (speakers abas 潘〇〇 male 1933 and haciang). places named: 新社 = PakteRung ("here")
  - "#c 我們明天八點早點來，有從台北來的人。" — `KacCon-Teaching Weaving_abas_ipay.json` `glosses[11][1].free` (record 12). People are coming from Taipei, so this was probably recorded outside Taipei (inferred).
  - "#n Lalu'ung是另一個新社的部落。" — `KavCon-marriage_abas_pilaw.json` `glosses[191][1].free` (record 192). places named: Lalu'ung, a 部落 of 新社
- Observed vs inferred: The speakers' home place 新社 is observed (metadata in 29 files, plus speakers' own words). **The recording place differs between texts.** Several texts were evidently recorded in Taipei (the speakers say "here in Taipei"), and at least one in 新社 ("新社這裡"). Inferred: the 2 files without a place label belong to the same speakers as labelled files (ngengi also in `KavNr-ancestor_ngengi`, labelled `Xinshe(新社)`; imuy 潘〇〇 female 1952 also in `KavNr-frog_imuy2`, labelled `Xinshe(新社)`).
- Proposed README addition: "NTU labels 29 of the 31 Kavalan stories `Xinshe (新社)` (`meta.language`). The speakers' hometown is 新社, but some texts were recorded among Kavalan living in Taipei (e.g. `story/Kavalan_Xinshe/KavNr-ancestor_buya.json`, record 179: 我們在台北這裡)."

#### NTU Rukai (dru, dialect Wutai, 23 XML files: 1 Sentences (54 JSONs) + 22 Stories)
Files: `.../CodeAndDocs/sentence/Rukai_Vedai/` and `.../CodeAndDocs/story/Rukai_Vedai/`
- Files with place info in metadata: the third item is `Budai` (55) or `Vedai` (21) in **all 76 JSONs**, and the 54 sentence JSONs' Chinese name is `霧台魯凱語`. These are dialect names that are also a place name (霧台). Nothing in the metadata says the recordings were made in 霧台.
- LOCATION EVIDENCE:
  - "霧台魯凱語, Rukai, Budai" — `meta.language` of all 54 sentence JSONs (2020-03-18 to 2020-05-31; speakers 柯〇〇 female 1961, 許〇〇 male 1950, 巴〇〇 male 1946, 麥〇〇 male 1958, 賴〇〇 male 1959, 宋〇〇 male 1936). applies to: the Sentences XML. places named: 霧台 (as a dialect name)
  - "#e Today, I would like to say… that when I was a little child in Vedai." / "#c 今天。這個，我要說…就是當時我小時候在霧台的時候。" — `story/.../RukaiNr-childhood_balenge.json` `glosses[3][1].free` (record 4); record 110 note: "...據發音人表示十點就算晚睡，迄今(2011)霧台鄉依舊如此。"
    applies to: speaker 潘〇〇〇, female, 1961 ("Balenge": childhood_balenge, ghost lake_Balenge, pear_Balenge, princess balenge_balenge). places named: 霧台 / Vedai; 霧台鄉
  - "#n vai(太陽)在此借代時間，發音人表示從霧台部落至小鬼湖要兩天的時間..." — `story/.../RukaiNr-ghost lake_Balenge.json` `glosses[11][1].free` (record 12). applies to: the same speaker. places named: 霧台部落
  - "su-a Vedai=aku." "#e I am Vudai-ese." / "#c 我是霧台人。" — `sentence/Rukai_Vedai/20200415-CL-4.json` `glosses[17][1].free` (record 18). An elicited sentence (speaker 柯〇〇, female, 1961), so weak.
  - "#e Muni is married to our Vedai tribe. (coming to the Vedai tribe)" / "#c Muni嫁來我們的霧台部落。" — `sentence/Rukai_Vedai/20200529-FW-Ken-2.json` `glosses[6][1].free` (record 7; record 6, `glosses[5]`, is the 嫁去 "going" version). Elicited. "嫁來" ("marry into, coming here") hints that the session was held in 霧台 (weak inference).
- Could not find: where the 2009–2011 story recordings and the 2020 "FW" (field-work) sessions took place.
- Proposed README addition: "NTU names its Rukai `Vedai`/`Budai` (霧台魯凱語) but records no recording place; one storyteller says she grew up in 霧台 (`story/Rukai_Vedai/RukaiNr-childhood_balenge.json`, record 4)."

#### NTU Saisiyat (xsy, dialect Saisiyat, 20 XML files, all Stories)
Files: `.../CodeAndDocs/story/Saisiyat_Tong-he/`
- Files with place info in metadata: **1 of 20** (`SaiNr-Molaw.json`: `Tong-he(東河)`). The folder name `Saisiyat_Tong-he` covers all 20.
- LOCATION EVIDENCE:
  - "賽夏語, Saisiyat, Tong-he(東河)" — `meta.language` of `SaiNr-Molaw.json` (speaker 高〇〇, 1928). applies to: that file. places named: 東河 / Tong-he
  - "#n Note: C: kalih a 'oemaw, M, 77K: paran a 'oemaw, M, 77" (the Chinese note beside it gives the two men's full names; not reproduced here) and "#e "How do you pay respects to the dead in Tungho?"" / "#c 「你們東河的人是怎樣祭祖掃墓呢。」" — `SaiNr-holiday_kalaeh a _oemaw.json` `glosses[1][1].free` (record 2) and `glosses[4][1].free` (record 5). Speaker C asks speaker K about "you 東河 people".
    applies to: speaker K = paran a 'oemaw (高, male, 77; meta of `SaiNr-frog8_parain a _oemaw` and `SaiNr-kathethel_parain a _oemaw` gives 高〇〇, male, 1928; the match is inferred). places named: 東河 / Tungho
  - "#e "Here in Xiangtianhu, each clan buys their own things for offering."" / "#c 「我們向天湖這兒是 ... ... 我們每個姓的人呀 ... ... 。」" — same file `glosses[113][1].free` (record 114); record 116: "#c 「向天湖這兒有三個姓 ... ..。」"
    applies to: speaker C = kalih a 'oemaw (朱, male, 77; meta 朱〇〇, male, 1928; his files: frog6, holiday, kathethel2). places named: 向天湖 / Xiangtianhu ("here")
  - "#e One is from Xiangtianhu." / "#c 有一個來自向天湖。" — `SaiNr-life_waon a boong.json` `glosses[275][1].free` (record 276). About third persons, not the speaker.
- Observed vs inferred: Two different home communities are observed among the speakers: 東河 (K) and 向天湖 (C). For the other speakers (風〇〇, 日〇〇, 趙〇〇, 徐〇〇, 高〇〇 female 1967) nothing is stated, apart from the folder name `Tong-he`.
- Proposed README addition: "NTU's Saisiyat folder is named `Tong-he` (東河), and one story is labelled `Tong-he(東河)` (`story/Saisiyat_Tong-he/SaiNr-Molaw.json`); in `SaiNr-holiday_kalaeh a _oemaw.json` one speaker is addressed as from 東河 (record 5) and the other speaks of 向天湖 as 'here' (record 114)."

#### NTU Sakizaya (szy, dialect Sakizaya, 16 XML files: 1 Grammar (17 JSONs) + 15 Stories)
Files: `.../CodeAndDocs/{grammar,story}/Sakizaya_Sakizaya/`
- Files with place info in metadata: **0 of 32 JSONs**.
- LOCATION EVIDENCE (story content):
  - "#e Sakizaya people in Maibul only shot birds." / "#c 我們馬立雲的sakizaya 人只有射鳥。" — `story/.../skzyNr-class_sinay.json` `glosses[176][1].free` (record 177); record 180: "#c 我們馬立雲的Sakizaya人沒有仿效大家一起去捕魚的祭典。"
    applies to: speaker 林〇〇, male ("Sinay": class_sinay, frog_sinay, tribalhistory_sinay). places named: 馬立雲 / Maibul ("we of 馬立雲")
  - "#n IU 71 中ngabul 為鹿的總稱(主要在馬立雲部落)；而在花蓮市，鹿的總稱是kalalayan。" — `story/.../skzyNr-frog_sinay.json` `glosses[72][1].free` (record 73). A note on a word as used in 馬立雲部落, said of this speaker's word. places named: 馬立雲部落, 花蓮市
- Could not find: the home of the other storytellers (Bunuk, Dungi, Panay, Kaniw) or where anything was recorded. The grammar-book JSONs carry no consultant information.
- Proposed README addition: "NTU's Sakizaya metadata names no place; one storyteller identifies as from 馬立雲 (`story/Sakizaya_Sakizaya/skzyNr-class_sinay.json`, record 177)."

#### NTU Seediq (trv, dialect Tegudaya, so Seediq; 27 XML files: 1 Grammar (17 JSONs) + 26 Stories)
Files: `.../CodeAndDocs/{grammar,story}/Seediq_Tgdaya/`
- Files with place info in metadata: **0 of 43 JSONs** (`Tgdaya`, a dialect-group name).
- LOCATION EVIDENCE (story content):
  - "#e I come from Meixi tribe, Renai village. I'm now still living in Meixi tribe." / "#c 我來自仁愛鄉的眉溪部落，而且現在還住在眉溪這裡。" + "#n Tongan及Bayke各為眉溪部落之族語名及日語名。" — `story/.../sdqNr-mother_iwan 2020s.json` `glosses[4][1].free` (record 5)
    applies to: speaker 田〇〇, female, 1939 (this file). places named: 仁愛鄉 (township) / 眉溪部落 = Tongan ("here")
  - "#e In the past, as a child, I had come from Nakahara-- I was in the fourth grade then-- and came to Tongan here." / "#c 過去，我小時候呢，四年級時就從中原部落來到眉溪部落這裡。" — `story/.../sdqNr-childhood_micang 2020s.json` `glosses[3][1].free` (record 4); record 266: "#e We are truly from the Tongan tribe." / "#c 我們真的是來自南豐部落。"
    applies to: speaker 周〇〇, female, 1942 (this file). places named: 中原部落 (childhood), 眉溪部落/Tongan ("here"). **The source contradicts itself at record 266**: the Seediq says `tongan`, the English "Tongan", the Chinese "南豐部落". Quoted as printed.
  - "#e There is a story told by the elderly people of our Gluban tribe." / "#c 有個我們清流部落的族老流傳下來的故事。" + "#n Gluban「清流部落」。" — `story/.../sdqNr-sisin_dakis 2020s.json` `glosses[5][1].free` (record 6); `sdqNr-tradition_dakis 2021s.json` record 11: "#c 這不僅僅是(流傳在)我們清流部落，還有中原部落和眉溪部落。"
    applies to: speaker 郭〇〇, male, 1953 ("Dakis": pear-dakis, seediq_dakis, sisin_dakis, tradition_dakis; `sdqCon-dialog5_dakis_takun` is NOT his by `meta.speaker`, which gives 邱〇〇, male, 1952). places named: 清流部落 / Gluban
  - "#e Long time ago, I grew up to be a young man here." / "#c 我從前在這裡長成青年。" + "#n hini refers to Gluban/指「清流部落」。" — `story/.../sdqNr-south_pawan 2021s.json` `glosses[3][1].free` (record 4)
    applies to: speaker 王〇〇, male, 1926 ("Pawan": rain_pawan, south_pawan). places named: 清流部落 / Gluban ("here")
  - "#e You moved from there (Mhebu) to here (Gluban)." / "#c 妳從...妳從那裡（馬赫坡部落）直到這裡（清流部落）。" — `story/.../sdqCon-dialog1_ciwas_tiwas 2021s.json` `glosses[204][1].free` (record 205)
    applies to: this conversation (speaker 蔡〇〇, female, 1915; recorded 1991-08-09). places named: 馬赫坡部落 (earlier home), 清流部落 ("here")
- Observed vs inferred: Speakers come from at least two different communities: 眉溪 (Tongan) and 清流 (Gluban). Where a text says "here" (這裡/hini), the recording was presumably made in that community (inferred).
- Proposed README addition: "NTU's Seediq metadata names no place; in the stories, speakers place themselves in 眉溪部落, 仁愛鄉 (`story/Seediq_Tgdaya/sdqNr-mother_iwan 2020s.json`, record 5) and 清流部落/Gluban (`sdqNr-sisin_dakis 2020s.json`, record 6)."

#### NTU Tsou (tsu, dialect Tsou, 12 XML files, all Stories)
Files: `.../CodeAndDocs/story/Tsou_Tsou/`
- Files with place info in metadata: **12 of 12**. `TapangU` in 7 files (`Tsou-frog-story-wang-1`, `TsouConv-typhoon`, `TsouNr-frog-story-shi`, `TsouNr-frog-story-tu`, `TsouNr-love-story-zhuang`, `TsouNr-lovestory-zheng`, `TsouNr-pear-An`); `Tfya` in 5 (`None-1`, `TsouConv-informants`, `TsouNr-pear-story-3`, `TsouNr-pear-wang-3`, `TsouNr_lovestry_wang-2`).
- LOCATION EVIDENCE:
  - "鄒語, Tsou, TapangU" — `meta.language` of 7 files; "鄒語, Tsou, Tfya" — `meta.language` of 5 files. places named: TapangU, Tfya (no Chinese given)
  - "#e Moreover, so much work... I cannot do so as I wish; so much work in TapangU." / "#c 而且有很多工作...我不能照我想的...達邦有很多工作。" — `TsouConv-informants.json` `glosses[8][1].free` (record 9). **The source's own translation equates TapangU with 達邦.** (Also `None-1.json` record 202: "#e Unexpectedly, (he) walked from Tapangu." / "#c 竟然是從達邦走過來的。")
  - "#n T 和M 是親戚，M 經常來台北出差..." — `TsouConv-informants.json` `glosses[2][1].free` (record 3); record 21: "#e When I arrive here, I feel surprised at people in Taipei." / "#c 當我來到這裡，台北的人讓我很驚訝。"
    applies to: this conversation (labelled `Tfya`). It was evidently recorded in Taipei (inferred from "here" plus the note), with a speaker (M) whose work is in 達邦.
  - "#e Grandfather knows (this), because he is also from Tapangu." / "#c 外公也知道，因為他也是達邦人。" — `None-1.json` `glosses[284][1].free` (record 285). "也" (also) hints that the speaker is from 達邦 too (inference).
- Observed vs inferred: `Tfya` is never glossed in the committed data. That it means 特富野 is GENERAL KNOWLEDGE, NOT FROM THE SOURCE. The published XML collapses both labels into `dialect="Tsou"`.
- Proposed README addition: "NTU labels 7 Tsou stories `TapangU` (達邦, as the source's own translation renders it in `story/Tsou_Tsou/TsouConv-informants.json`, record 9) and 5 `Tfya`; at least one conversation (`TsouConv-informants`) was recorded in Taipei."

---

### ILRDF_Dicts

- Dialect label(s) in XML (xml:lang + dialect, with file counts): ami Xiuguluan 2 · tay Sekolik 2 · bnn Junqun 2 · pwn Northern 2 · pyu Nanwang 2 · dru Wutai 2 · trv Tegudaya 2 (Seediq) · trv Truku 2 (Truku). Each language has `XML/<Language>/<Language>.xml` (sentences) and `<Language>_dictionary.xml` (headwords), and both carry the same `<TEXT>` values. Out of scope, dialect `unknown`: Kanakanavu, Kavalan, Saaroa, Saisiyat, Sakizaya, Thao, Tsou, Yami.
- README statement about place:
  `/tmp/claude-1000/-workspace-FormosanBank/e78edf4a-c5b9-400e-864e-ff685648c37f/scratchpad/fb-main/Corpora/ILRDF_Dicts/README.md`
  - Lines 43–47 (where the dialect labels come from): "The build takes these values from FormosanBank's 2024 publication of the corpus (`generate_xml.py`, `text_attributes`); where that publication had none, the dialect is `unknown`. The rebuild does not read a dialect from the ILRDF source; whether the source distinguishes dialects for these eight languages is not documented in this repository."
  - Line 441 (Yami, quoted to show what ILRDF metadata can carry): "* **Yami: the village is in the file name.** The source records most Yami sentences in three villages. They are published as three `S` (朗島 first, then 野銀, then 漁人), with files named `<id>_<village>.<ext>`, e.g. `Yami_4596_野銀.mp3`."
  - Lines 480–488: "- **Yami: the village is in the file name.** The source records most Yami sentences in three villages. They are published as three `S`, 朗島 first (it keeps the id; main's recording is the 朗島 one), then 野銀, then 漁人, with files `<id>_<village>.<ext>` (`Yami_4596_野銀.mp3` on `Yami_4596-opt`). Where one sentence has two *different* recordings from the same village (267 files), the second is named `<id>_<village>_2.<ext>`; Yami recordings with no village in the source (652 files, 644 sentences) are named after their `S`, like the other languages (both "OK as built", maintainer, 2026-10-18)."
  - Nothing in the README says where any of the 8 dialect-labelled languages was recorded.
- Sources searched:
  - API snapshots `.../ILRDF_Dicts/CodeAndDocs/source_data/snapshots/<Language>.json.gz` for all 8 languages plus Yami: every key path enumerated. Top-level keys: `language`, `responses`, `schema_version`, `snapshot_origin_commit`. Per headword: `audioItems`, `derivativeRoot`, `explanationItems`, `formationWord`, `frequency`, `id`, `name`, `pinyin`, `sources`, `variant`. Per audio item: `audioClass`, `audioUrl`, `id`. Per example sentence: `audioItems`, `chineseSentence`, `id`, `originalSentence`. **There is no dialect, village, speaker or place field.**
  - The `audioClass` values counted, the `sources` values counted, `variant` values sampled;
  - `chineseExplanation` and `chineseSentence` searched for dialect/place terms (方言, 部落, 村, 鄉, 社區, 腔, and each language's dialect names) and for parenthesised usage tags;
  - published XML: `<TEXT>` attributes, every `S/@source`, `AUDIO/@source`, `AUDIO/@file`, `*/@notes` (all 16 files of the 8 languages);
  - the 2024 snapshot `.../source_data/main_2024/<Language>.xml.gz`: attribute inventory;
  - `docs/audio_upload_manifest.csv` and `source_data/audio_fingerprints.tsv` column headers; `source_data/RIGHTS.md`;
  - `git log -S'dialect="Xiuguluan"'` on `XML/Amis/Amis.xml`, to see when the dialect labels appeared.
- LOCATION EVIDENCE (the same for all 8 languages unless noted):
  - **`audioClass` is the field that holds the Yami village, and it is null for every recording of the 8 languages.** Counts (headword-level audio / sentence-level audio, all `None`): Amis 8,259 / 8,152 · Atayal 6,621 / 7,888 · Bunun 7,777 / 11,990 · Paiwan 6,713 / 6,893 · Puyuma 8,691 / 9,184 · Rukai 13,109 / 14,296 · Seediq 5,958 / 7,048 · Truku 10,973 / 6,843. For comparison, Yami sentence-level audio: `朗島` 7,236, `漁人` 7,205, `野銀` 7,202, `None` 776. Key path: `responses[].words[].explanationItems[].sentenceItems[].audioItems[].audioClass`. The build code that reads it: `.../ILRDF_Dicts/CodeAndDocs/ilrdf_source.py` line 74: "#: The source's audioClass of each recording (Yami: the village)."
  - `sources` (the material an entry comes from) never names a place. Values seen: 線上辭典, 學習詞表, 九階教材, 閱讀書寫篇, 生活會話篇, 高中句型篇, 國中句型篇, 族語E樂園文化篇.
  - Published XML audio file names are `<Language>_<id>.mp3` (or `-opt`, `_2`, GUID forms). **0** of the AUDIO `file` values in the 8 languages' sentence files contain a Chinese character (Amis 6,592; Atayal 7,057; Bunun 10,503; Paiwan 5,893; Puyuma 8,342; Rukai 12,971; Seediq 6,158; Truku 5,834). Yami: 13,279 of 20,370 do (the village names).
  - XML `<TEXT>` carries `source="Indigenous Languages Research and Development Foundation Dictionaries"` and a citation to 原住民族語言線上辭典: <language>. No place.
  - Per-entry usage tags (these mark individual words as another dialect's; they do not say where anything was recorded):
    - Seediq: 75 explanations mention "德鹿谷賽德克語" (74 as the tag "（德鹿谷賽德克語）", 1 as the whole explanation "德鹿谷賽德克語"), and 1 is tagged "（都達賽德克語）", e.g. `Krawah` "珍惜 （德鹿谷賽德克語）" (`snapshots/Seediq.json.gz` `responses[51].words[0].explanationItems[0].chineseExplanation`) and `mlatac` "分離（都達賽德克語）". So the corpus labelled `Tegudaya` contains some entries the source itself marks as Truku-Seediq (德鹿谷) or Toda (都達).
    - Amis: single entries tagged "（北阿美用法）" (`rarid`), "（北阿美用語）" (`simsim`), "（太巴塱用語）" (`tafiling`), "（太巴塱部落）" (`ʼalecam`), "（太巴塱）" (`kiling`), "（恆春）" (`cidap`, `responses[476].words[0].explanationItems[0].chineseExplanation`).
    - Truku: "燒烤（東部太魯閣為sqrul）" (`bagu`), "麵條（西部賽德克用語）。" (`bisur`).
    - Atayal, Bunun, Paiwan, Puyuma, Rukai: no such dialect or region tags (only loanword or register tags such as "（從日本語）", "（各族用語）"). Bunun and Puyuma explanations name places only as glosses of place-name headwords (e.g. Bunun `Haitutuan` "地名（台東縣海端鄉）", Puyuma `Puyuma` "南王（部落名）").
  - The example sentences name many villages as content (e.g. Rukai "霧台部落的土地有很多石壁。", Amis "我的部落在水漣。"). These are sentence content, not where the sentence was recorded or who said it.
  - Where the dialect labels came from (observed in git, read-only): the labels are absent from `XML/Amis/Amis.xml` at `7d9aaa908^` and present at `7d9aaa908` (`dialect="Xiuguluan" glottocode="nat1254"`). Commit `7d9aaa908`, Joshua Hartshorne, 2026-03-14, message "Full revamp of ePark.", touched all 16 ILRDF XML files plus ePark. The message gives no reason for the ILRDF labels.
- Per language (all eight are the same):

  | Language | xml:lang / dialect | place per entry in committed data? | where it would be |
  |---|---|---|---|
  | Amis | ami / Xiuguluan | NO (audioClass null 16,411×; 6 regional usage tags on single words) | ILRDF website/compilers, online only |
  | Atayal | tay / Sekolik | NO (audioClass null 14,509×) | online only |
  | Bunun | bnn / Junqun | NO (audioClass null 19,767×) | online only |
  | Paiwan | pwn / Northern | NO (audioClass null 13,606×) | online only |
  | Puyuma | pyu / Nanwang | NO (audioClass null 17,875×) | online only |
  | Rukai | dru / Wutai | NO (audioClass null 27,405×) | online only |
  | Seediq | trv / Tegudaya | NO (audioClass null 13,006×; 76 entries tagged 德鹿谷/都達) | online only |
  | Truku | trv / Truku | NO (audioClass null 17,816×; 2 usage tags) | online only |

- Observed vs inferred notes: It is observed that the API has a per-recording place slot (`audioClass`) and fills it only for Yami. That ILRDF therefore did not record a village for the other languages is an inference; the API might simply not expose it. The dialect labels are FormosanBank's, not ILRDF's (README lines 43–47, and the 2026-03-14 commit).
- Could not find / not knowable locally: who recorded the 8 languages and where; whether ILRDF's dictionary for each language follows one dialect. Any such statement would be on the ILRDF site (e.g. an "about"/編輯群 page; `source_data/RIGHTS.md` cites `https://e-dictionary.ilrdf.org.tw/about?id=6c987092-47c7-ef11-bd58-00155db40116` for the copyright statement only), which cannot be fetched from this container.
- Proposed README addition: "The ILRDF source records no village or place for the Amis, Atayal, Bunun, Paiwan, Puyuma, Rukai, Seediq and Truku entries: the API's per-recording `audioClass` field, which holds the village for Yami, is empty for all their recordings (`CodeAndDocs/source_data/snapshots/<Language>.json.gz`). Their `dialect` values are FormosanBank's own labels, not read from the source."

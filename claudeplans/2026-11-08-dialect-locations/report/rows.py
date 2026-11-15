# Verdict rows for the dialect-location report. One row per (corpus, xml:lang, dialect) unit, or several units
# sharing one card. Every key in published_dialect_counts.txt must be covered exactly once (checked by build.py).
#
# verdict: nomatch | partial | village | township | county | unplaced | notfound | notlisted
# link: how the place connects to the list: "source" (the source's own words name a place the list names),
#       "roman" (my reading of a romanized place name), "outside" (my outside knowledge of where a place is),
#       "secondhand" (FormosanBank's own summary of a source we could not see)

FB = "fb-main"  # paths below are relative to the worktree at main 2a345f0d9

ROWS = [
# ------------------------------------------------------------------ DOESN'T MATCH
dict(keys=[("WilangYutasVideos", "tay", "Sekolik")], verdict="nomatch", link=["source"],
  title="Wilang Yutas videos: labelled Sekolik, but the elder says he is from 南山 (大同鄉, 宜蘭縣), and the list has no Sekolik in 宜蘭縣",
  readme="Nothing about place. README line 9: “Neither the earlier README nor the earlier GitBook page says how the Sekolik dialect label was determined.”",
  evidence=[
    ("aw, Wilang Simaw. / 是的，我叫 Wilang Simaw", "2016-05-25 interview, caption at 54.2 s — CodeAndDocs/raw_scrape/目前先做這篇_20160525_濱咖啡訪談_Yutas_Wilang_目前先做這篇_U9I0GGy_pz0.txt"),
    ("kahul saku son mha Piyanan. / 我來自於一個稱為南山的地方", "same file, 61.42 s"),
    ("Piyanan puqing balay Taytogo … / 南山是大同鄉的最後面", "same file, 70.84 s"),
    ("… Gilang Keng ru Taycyu Keng … / 宜蘭縣和臺中縣 … 很靠近兩縣的邊界", "same file, 75.6–81.82 s"),
  ],
  places="宜蘭縣 大同鄉 南山部落 (Piyanan)",
  listsays="宜蘭縣 大同鄉 南山村 is listed under 四季泰雅語 and 宜蘭澤敖利泰雅語 (and under Seediq 都達語). 賽考利克泰雅語 appears only in 新北市, 桃園縣, 新竹縣, 苗栗縣, 台中市 and 南投縣, never in 宜蘭縣.",
  caveat="Only this one captioned video states the place. That the interviewee “Wilang Simaw” is the channel’s “Yutas Wilang” is my inference (the video title says Yutas_Wilang). Some uncaptioned Atayal lines in other videos also mention Piyanan / Nansan, but reading them as “my village” is the agent’s low-confidence reading. No file says where any video was filmed.",
  add="In the 2016-05-25 interview (video U9I0GGy_pz0) the elder, who gives his name as Wilang Simaw, says he comes from Piyanan, 南山部落 at the back of 大同鄉 in 宜蘭縣 (captions: 「我來自於一個稱為南山的地方」「南山是大同鄉的最後面」). The recording locations are not stated."),

# ------------------------------------------------------------------ PARTLY MATCHES
dict(keys=[("HundredPaiwanStories", "pwn", "Central")], verdict="partial", link=["outside"],
  title="Hundred Paiwan Stories, Central: 13 texts come from villages the list puts in Central Paiwan; text 095 (“Makazayazaya dialect”) comes from 瑪家, which the list puts in Northern Paiwan",
  readme="Nothing about place.",
  evidence=[
    ("The title also indicates the village or dialect of the original narrator of the story", "book introduction, CodeAndDocs/Paiwan Ch2.docx"),
    ("042–051 … (Kuɫaɫau village, p.224 …)   ·   060–062 … (Kaviangan village, p.268 …)   ·   058–059 … (Tjaɫakavus village)", "story headings, Paiwan Ch2.docx"),
    ("095 PRAYER — Makazayazaya dialect   ·   098 FAREWELL MESSAGE (2) — Kazazaɫan dialect", "story headings, Paiwan Ch2.docx"),
  ],
  places="Kuɫaɫau (10 texts), Kaviangan (3), Tjaɫakavus (2), Makazayazaya (1: text 095), Kazazaɫan (1: text 098)",
  listsays="If my identifications are right: Kuɫaɫau = 古樓 → 屏東縣 來義鄉 古樓村, listed under 中排灣語 ✓. Kaviangan = 佳平 → 泰武鄉 佳平村, 中排灣語 ✓. Makazayazaya = 瑪家 → 瑪家鄉 瑪家村, listed under 北排灣語 (and 霧臺魯凱語), not 中排灣語 ✗.",
  caveat="The book gives Paiwan village names only, with no township, county or Chinese name. Matching them to the list’s Chinese village names is my own identification, not the book’s. I am confident of 古樓, 佳平 and 瑪家. I could not place Tjaɫakavus or Kazazaɫan. The Central/Northern/Southern/Eastern labels are FormosanBank’s own grouping: a village→dialect table in the first build script (commit c2583be56), which cites no source. Texts 095 and 098 are not in that table. Commit 90094b232 (2026-03-15) added dialect=\"Central\" to both, with no reason given in the commit.",
  add="Each story heading names the narrator’s village or dialect (e.g. “Kuɫaɫau village”, “Makazayazaya dialect”); the Northern/Central/Southern/Eastern labels are FormosanBank’s grouping of those villages."),

dict(keys=[("Virginia_Fey_Dictionary", "ami", "Xiuguluan")], verdict="partial", link=["secondhand", "roman"],
  title="Fey’s Amis dictionary: Fey is said to name a range from Fuyuan to Fuli and from Fengbin to Iwan. The list puts 富源 and 富里 in Xiuguluan but 豐濱 in Coastal Amis",
  readme="README lines 22–24: “the dictionary’s introduction (printed page 13) identifies the main text as Central Amis; the FormosanBank registry calls this dialect Xiuguluan.” No place.",
  evidence=[
    ("Fey identifies the main text as Standard Central Dialect, Fuyuan to Fuli and Fengbin to Iwan; dialects.csv maps Central to Xiuguluan.", "CodeAndDocs/source_decisions.json, key dialect.evidence_summary — this is FormosanBank’s own summary, not Fey’s words"),
  ],
  places="Fuyuan, Fuli, Fengbin, Iwan (romanized, as in our summary)",
  listsays="Fuyuan = 富源 → 花蓮縣 瑞穗鄉 富源村: 秀姑巒 ✓.  Fuli = 富里 → 富里鄉: 秀姑巒 (and 馬蘭) ✓.  Fengbin = 豐濱 → 豐濱鄉: 海岸, 噶瑪蘭, 撒奇萊雅, not 秀姑巒 ✗.  Iwan: I can’t place it from the source.",
  caveat="Fey’s introduction PDF is only online (new-amis.moedict.tw), which the container can’t reach. It is not in the GitHub mirrors g0v/amis-moedict or miaoski/amis-data (I checked both file lists). So Fey’s exact words are unverified. Reading Fuyuan/Fuli/Fengbin as 富源/富里/豐濱 is mine.",
  add="Fey’s introduction (printed p. 13) is summarized in source_decisions.json as naming the standard Central dialect “Fuyuan to Fuli and Fengbin to Iwan”; quote her exact words here once the PDF has been checked."),

dict(keys=[("Cuerq-Pourrias-Poinsot-Amis-Dictionary", "ami", "Xiuguluan")], verdict="partial", link=["source"],
  title="Poinsot dictionary, Xiuguluan files: only the 鳳林話 entries carry a place the list puts in Xiuguluan; the places the authors say they lived are Coastal and 南勢 in the list",
  readme="README lines 16–18 and 26–28: {F} 鳳林話, {T} 富田語 and unmarked entries are filed as Xiuguluan. No collection place.",
  evidence=[
    ("我和阿美族人一起住在豐濱、壽豐與富田等地區共四年，然後在台北、基隆及桃園等地區住了二十八年，因此學過花東各地不同的阿美語方言。", "authors’ preface 自序 (2002), scan page 3 — github.com/miaoski/amis-chinese-poinsot, pic/img-117110211_頁面_003.tiff (fetched for this check)"),
    ("累積了三年的資料，我特別感謝李慶雄先生 (Mioshy) 和張徒會先生 (Agay) …", "same page"),
    ("縮寫詞： … F：鳳林話 … N：北方話 … S：南方話 … T：富田語 … Z：Zakiraya 話", "same page: the book’s own abbreviation key"),
  ],
  places="鳳林 (from the label 鳳林話); 富田 (label 富田語; not located by the book); preface: 豐濱, 壽豐, 富田, then 台北, 基隆, 桃園",
  listsays="鳳林鎮 → 秀姑巒 only ✓ (918 sentences).  富田 is not a township and is not named in the list.  豐濱鄉 → 海岸 / 噶瑪蘭 / 撒奇萊雅; 壽豐鄉 → 南勢 / 撒奇萊雅. Neither lists 秀姑巒.",
  caveat="The 23,304 unmarked sentences (85% of the corpus) have no place in the book; filing them as Xiuguluan has no stated source basis. The preface says where the authors lived and learned Amis, not where each entry was collected. Sentence counts by file: F 918, T 343, unmarked 23,304.",
  add="The authors’ preface (自序, 2002) says they lived with Amis people in 豐濱, 壽豐 and 富田 for four years and then 28 years in Taipei, Keelung and Taoyuan; the abbreviation key on the same page defines F 鳳林話, T 富田語, N 北方話, S 南方話, Z Zakiraya 話."),

# ------------------------------------------------------------------ MATCHES: VILLAGE / COMMUNITY
dict(keys=[("Nowbucyang-Truku-Thesis", "trv", "Truku")], verdict="village", link=["source"],
  title="Nowbucyang Truku thesis: 銅門 and 崇德, 秀林鄉, 花蓮縣",
  readme="README lines 16–18 cite only the build config: “community locations as Dumung / 銅門 and Tkijig / 崇德”. No county or township.",
  evidence=[
    ("本論文研究花蓮縣秀林鄉銅門部落(Dumung)與崇德部落(Tkijig)太魯閣語(Truku)的構詞法", "Chinese abstract, PDF p. 3 — /workspace/Formosan-Nowbucyang-Truku-Thesis/data/raw/pdf/許韋晟全文.decrypted.pdf"),
    ("Nobucyang 許勝賀 … 銅門 · Silung 許珍碧 … 銅門 · Tusi Yudaw 李季生 … 崇德", "Table 1.1 本論文發音人, printed p. 2 / PDF p. 18"),
  ],
  places="花蓮縣 秀林鄉 銅門部落, 崇德部落",
  listsays="太魯閣語 · 花蓮縣 秀林鄉: … 崇德村 … 銅門村 … ✓",
  caveat="Printed p. 1 says some data also came from teaching materials (九階教材, 鄉公所族語教材, 太魯閣語初級辭典). The XML does not say which sentence came from which consultant.",
  add="The thesis’s data come mainly from fieldwork in 花蓮縣秀林鄉 with three consultants: 許勝賀 (Nobucyang) and 許珍碧 (Silung) of 銅門部落 and 李季生 (Tusi Yudaw) of 崇德部落 (Table 1.1, printed p. 2); some forms come from Truku teaching materials (printed p. 1)."),

dict(keys=[("RauDong", "tao", "Yami")], verdict="village", link=["source"],
  title="Rau & Dong Yami texts: 椰油村 (8 texts) and 東清村 (12 texts)",
  readme="README lines 11–13 already say this: “Yayo (椰油村) for texts 1–6, 14 and 16, Iranmilek (東清村) for the other twelve.”",
  evidence=[
    ("si Tonosen (M, 53, Yayo) … 賴金龍，男，53，椰油村", "TEXT/@source of text 1 (each of the 20 published files carries its storyteller and village)"),
    ("tally of all 20 published files: 椰油村 8 (texts 1–6, 14, 16), 東清村 12 (texts 7–13, 15, 17–20)", "my count, XML/Yami/*.xml"),
  ],
  places="臺東縣 蘭嶼鄉 椰油村, 東清村 (township and county not printed)",
  listsays="雅美語 · 臺東縣 蘭嶼鄉: 朗島村、東清村、椰油村、紅頭村 ✓",
  caveat="The village is the storyteller’s, as printed with the text; where the recording was made is not stated.",
  add=""),

dict(keys=[("Seediq-Chang-Reference-Grammar", "trv", "Tegudaya")], verdict="village", link=["source"],
  title="Chang Seediq grammar: consultants from 互助村, 仁愛鄉, 南投縣",
  readme="README lines 15–19 already say this, and it matches the book: 霧社方言, “spoken in 南豐 and 互助 villages, with consultants from 互助村”.",
  evidence=[
    ("…霧社方言則通行於南豐和互助兩村。本文研究的是霧社方言，在此我要感謝互助村發音人慷慨地提供語料和協助，我的發音人包括：傅景賢…", "printed p. 37 / PDF p. 53 (page image read; the text layer is garbled)"),
    ("另外，講春陽方言的張秋雄牧師(walis ukan)也提供了許多寶貴的意見", "printed p. 38 / PDF p. 54"),
  ],
  places="南投縣 仁愛鄉 互助村 (consultants); 南豐村 (the 霧社 dialect area)",
  listsays="德固達雅語 · 南投縣 仁愛鄉: 互助村（中原、清流、梅子林部落）、南豐村（天主堂、南山溪部落） ✓",
  caveat="The book thanks the consultants collectively as 互助村發音人. 張秋雄 speaks 春陽方言 (春陽 is 都達語 in the list), but he is thanked for comments, not listed as a consultant. Some chapter 3–4 examples are taken from 谷口龍子 (1994) and 張仲良 (1994), whose collection places are not given.",
  add="Name the five consultants (傅景賢, 錢成鏡, 詹秋木, 莊進利, 郭明正) and the county/township (南投縣仁愛鄉), and note that some chapter 3–4 examples come from 谷口龍子 (1994) and 張仲良 (1994) (printed pp. 54, 115)."),

dict(keys=[("Blust-Thao-Dictionary", "ssf", "Thao")], verdict="village", link=["source", "outside"],
  title="Blust Thao dictionary: Te-hua village (Barawbaw), Sun-Moon Lake, Nantou County",
  readme="README line 24: “a Formosan language of central Taiwan spoken around Sun-Moon Lake.” No village or consultant.",
  evidence=[
    ("Most of the Thao who still maintain their language reside in Te-hua village (Thao: Barawbaw), a mixed Taiwanese-Thao community on the southeast shore of Sun-Moon Lake, in Nantou County", "Introduction, printed p. 1 / PDF p. 11 — /workspace/Formosan-Robert-Blust-Thao-Dictionary/Private/[OA] Thao Dictionary.pdf"),
    ("About 65% of the material was collected from Kilash, another 25–30% from Lujan, and perhaps 5% from Ishul. A tiny portion was obtained from Puni", "printed p. 11 / PDF p. 21"),
    ("the Min-hu Club where much of the Thao data was collected", "printed p. 4 / PDF p. 14"),
  ],
  places="Nantou County; Te-hua village (Barawbaw); Sun-Moon Lake",
  listsays="邵語 · 南投縣 魚池鄉 日月村; 水里鄉 大平林. County ✓ from the book. Village ✓ only if Te-hua (德化社) = today’s 日月村 — that equation is mine; the book prints no Chinese place names.",
  caveat="Three of the four consultants were born in Tarigkuan and moved to Te-hua in 1935. The book also mentions a second community at Ta-p’ing-lin (Twapina = the list’s 大平林) with a “slightly different dialect”, but does not say any data came from there.",
  add="Blust’s consultants lived in Te-hua village (Barawbaw) on Sun-Moon Lake, Nantou County: Kilash (about 65% of the material and all five texts), Lujan (25–30%), Ishul (about 5%) and Puni (a tiny portion); much of the data was collected at the lakeside Min-hu Club (Blust 2003: 1, 4, 9–11, 244)."),

dict(keys=[("Song-Kanakanavu-Grammar", "xnb", "Kanakanavu")], verdict="village", link=["source"],
  title="Song Kanakanavu grammar: fieldwork in 達卡努瓦, 那瑪夏區; elders of 那瑪夏區 thanked",
  readme="Nothing about place.",
  evidence=[
    ("二〇一二年一個霪雨霏霏的十二月天，我和三位研究生帶著美聯社(Associated Press)記者及攝影團隊二度進入那瑪夏區的達卡努瓦村落。", "作者序, printed p. x / PDF p. 14 (page image read; this PDF has no text layer) — CodeAndDocs/raw_data/source.pdf"),
    ("感謝那瑪夏區部落的翁博學長老、翁坤長老、翁德才老師的知識分享及台灣卡那卡那富文教產業發展促進會的蔡運福、翁美英，余瑞娥等族人各式的協助與支持。", "same page"),
  ],
  places="高雄市 那瑪夏區 達卡努瓦 (村落)",
  listsays="卡那卡那富語 · 高雄市 那瑪夏區: 瑪雅里、達卡努瓦里、南沙魯里 ✓",
  caveat="The preface describes one field trip and thanks elders of the 那瑪夏區 communities; it does not say that all the book’s data was collected in 達卡努瓦. I did not read chapter 1 (§1.1 分布與現況).",
  add="The author’s preface (printed p. x) describes fieldwork in 達卡努瓦 village, 那瑪夏區 (2012), and thanks the 那瑪夏區 elders 翁博學, 翁坤 and 翁德才 for sharing their knowledge."),

dict(keys=[("YeddaPalemeqBlog", "pwn", "Southern")], verdict="village", link=["source", "roman"],
  title="Yedda Palemeq blog: she grew up in “spungudan” = Damei Village, Mudan Township, Pingtung",
  readme="Nothing about place.",
  evidence=[
    ("When I was a child, I lived in spungudan.  [gloss of spungudan:] Damei Village Mudan Township Pingtung Taiwan, a very small Paiwan village of around 50-80 households.", "XML S346_1 (her own gloss)"),
    ("our township sinvaudjan [gloss:] Mudan Township in Pingtung County  ·  In my dialect sinvaudjan Paiwan", "XML S195_1, S462_1"),
  ],
  places="屏東縣 牡丹鄉, Damei village",
  listsays="南排灣語 · 屏東縣 牡丹鄉: 石門村（上、下部落、中間路、茄芝路、大梅村）… ✓ (township from her words; Damei = 大梅 is my reading of the romanization)",
  caveat="This is where the author grew up and what she calls her dialect; the blog does not say where each post’s Paiwan was “collected”.",
  add="The author says she grew up in spungudan, which she glosses “Damei Village Mudan Township Pingtung Taiwan”, and calls her dialect sinvaudjan (Mudan Township) Paiwan (sentences S346_1, S195_1, S462_1)."),

dict(keys=[("NTUFormosanCorpus", "tay", "Wenshui")], verdict="village", link=["source"],
  title="NTU corpus, Atayal (Wenshui): 清安村",
  readme="Nothing about place.",
  evidence=[
    ("汶水泰雅不同村之間有b/v, c/s等發音上的差異。清安村發音人較年輕一輩的詞彙已無b和c的音…", "transcriber note present in all 11 source JSONs, e.g. CodeAndDocs/…/AtaNr-dailylife1_Iwan.json"),
    ("此處腔調重的族群指的是Matu'uwal(即清安村、此篇語料發音人的方言)", "AtaNr-moving_Takun.json, gloss note"),
    ("泰雅語, Atayal, Mayrinax (汶水)", "meta.language of 1 file"),
  ],
  places="清安村 (township and county not printed)",
  listsays="汶水泰雅語 · 苗栗縣 泰安鄉: 錦水村、清安村 ✓",
  caveat="Only AtaNr-moving_Takun ties 清安村 to its own speaker; for the other speakers it is implied by the general note. None of NTU’s place metadata reaches the published XML. The same text names its recording place: 「…我們所稱呼的Savawqil，也就是我們現在所在的地方。」 with the note 「“我們現在所在的地方”，指的是此篇語料所採集之處。」 (record 146). Savawqil is not named in the list and I can’t place it.",
  add=""),

dict(keys=[("NTUFormosanCorpus", "ckv", "Kavalan")], verdict="village", link=["source"],
  title="NTU corpus, Kavalan: 新社 (29 of 31 files)",
  readme="Nothing about place.",
  evidence=[
    ("噶瑪蘭語, Kavalan, Xinshe (新社)", "meta.language of 29 of the 31 source JSONs (17 + 12 spelling variants)"),
    ("就像過去我們還在故鄉,在新社時。  ·  我們在台北這裡會認真工作。", "KavCon-relatives_buya_ngengi.json record 943; KavNr-ancestor_buya.json record 179"),
  ],
  places="新社 (hometown); some recordings say “here in Taipei”",
  listsays="噶瑪蘭語 · 花蓮縣 豐濱鄉: 新社村（新社）… ✓",
  caveat="新社 is the speakers’ hometown; several recordings were evidently made in Taipei.",
  add=""),

dict(keys=[("NTUFormosanCorpus", "tsu", "Tsou")], verdict="village", link=["source"],
  title="NTU corpus, Tsou: TapangU = 達邦 (7 files); Tfya (5 files)",
  readme="Nothing about place.",
  evidence=[
    ("鄒語, Tsou, TapangU (7 files) / 鄒語, Tsou, Tfya (5 files)", "meta.language of all 12 source JSONs"),
    ("so much work in TapangU. / …達邦有很多工作。", "TsouConv-informants.json record 9 — NTU’s own translation renders TapangU as 達邦"),
  ],
  places="達邦 (7 files); Tfya (5 files, never glossed in the source)",
  listsays="鄒語 · 嘉義縣 阿里山鄉: 達邦村 … ✓ for TapangU. “Tfya” (特富野) is not named in the list, and the source doesn’t gloss it.",
  caveat="TsouConv-informants was evidently recorded in Taipei.",
  add=""),

dict(keys=[("NTUFormosanCorpus", "xsy", "Saisiyat")], verdict="village", link=["source"],
  title="NTU corpus, Saisiyat: 東河 (1 file) and 向天湖",
  readme="Nothing about place.",
  evidence=[
    ("賽夏語, Saisiyat, Tong-he(東河)", "meta.language of SaiNr-Molaw.json (1 of 20); the source folder is named Saisiyat_Tong-he"),
    ("我們向天湖這兒是 …", "SaiNr-holiday_kalaeh a _oemaw.json record 114 (speaker kalih a 'oemaw)"),
  ],
  places="東河; 向天湖",
  listsays="賽夏語 · 苗栗縣 南庄鄉: 東河村 … ✓. 向天湖 is not named in the list.",
  caveat="Only 1 of 20 files names a place in its metadata.",
  add=""),

dict(keys=[("NTUFormosanCorpus", "trv", "Tegudaya")], verdict="village", link=["source"],
  title="NTU corpus, Seediq (Tegudaya): speakers mention 眉溪, 清流, 中原 and 南豐 in 仁愛鄉",
  readme="Nothing about place.",
  evidence=[
    ("我來自仁愛鄉的眉溪部落，而且現在還住在眉溪這裡。", "sdqNr-mother_iwan 2020s.json record 5"),
    ("有個我們清流部落的族老流傳下來的故事。", "sdqNr-sisin_dakis 2020s.json record 6"),
    ("四年級時就從中原部落來到眉溪部落這裡。", "sdqNr-childhood_micang 2020s.json (English “Tongan”, Chinese “南豐部落” at record 266 — the source contradicts itself)"),
  ],
  places="仁愛鄉; 眉溪, 清流, 中原, 南豐 部落 (in speakers’ own words, not metadata)",
  listsays="德固達雅語 · 南投縣 仁愛鄉: 互助村（中原、清流、梅子林部落）、南豐村（天主堂、南山溪部落） ✓ for 清流, 中原, 南豐. 眉溪 is not named in the list (township 仁愛鄉 ✓).",
  caveat="These are what three speakers say about themselves inside the texts; the metadata (0 of 43 JSONs) names no place.",
  add=""),

dict(keys=[("NTUFormosanCorpus", "xnb", "Kanakanavu")], verdict="township", link=["source"],
  title="NTU corpus, Kanakanavu: one speaker says “我是那瑪夏的人”; another travels from 瑪雅里 to 達卡努瓦里",
  readme="Nothing about place.",
  evidence=[
    ("I live in Namasia. / 我是那瑪夏的人。  ·  (record 4) 就這樣我是在這裡出生的。", "kkvNr_hunting1_Muu.json records 1 and 4"),
    ("…I went from NU'Uvana to Tanganua to visit my older sister Miciku. / 若要米貢的時候，我就從瑪雅里去達卡努瓦里去拜訪我姊姊Miciku。", "kkvNr_mikon_Kuatu.json record 3"),
  ],
  places="那瑪夏 (one speaker’s own origin); 瑪雅里, 達卡努瓦里 (another speaker’s trip)",
  listsays="卡那卡那富語 · 高雄市 那瑪夏區: 瑪雅里、達卡努瓦里、南沙魯里 ✓ (township from one speaker; that the second speaker lives in 瑪雅里 is implied, not stated)",
  caveat="What two speakers say inside the texts; the metadata (0 of 42 JSONs) names no place.",
  add=""),

dict(keys=[("NTUFormosanCorpus", "dru", "Wutai")], verdict="village", link=["source"],
  title="NTU corpus, Rukai (Wutai): one storyteller grew up in 霧台",
  readme="Nothing about place.",
  evidence=[
    ("今天。這個，我要說…就是當時我小時候在霧台的時候。", "RukaiNr-childhood_balenge.json record 4"),
    ("霧台魯凱語, Rukai, Budai / Vedai", "meta.language of all 76 source JSONs (a dialect name, which is also the place name)"),
  ],
  places="霧台",
  listsays="霧臺魯凱語 · 屏東縣 霧臺鄉: 霧臺村 … ✓",
  caveat="Weak: one storyteller’s childhood place. Nothing says where the recordings were made.",
  add=""),

dict(keys=[("NTUFormosanCorpus", "szy", "Sakizaya")], verdict="village", link=["source", "outside"],
  title="NTU corpus, Sakizaya: one speaker says “我們馬立雲的 Sakizaya 人”",
  readme="Nothing about place.",
  evidence=[
    ("Sakizaya people in Maibul only shot birds. / 我們馬立雲的sakizaya 人只有射鳥。", "skzyNr-class_sinay.json record 177"),
  ],
  places="馬立雲 (Maibul)",
  listsays="馬立雲 is not named in the list. If 馬立雲 is in 瑞穗鄉 舞鶴村 (my outside knowledge, not the source’s), the list has 撒奇萊雅語 · 花蓮縣 瑞穗鄉: … 舞鶴村 … ✓",
  caveat="Weak: one speaker’s community, in story content. The metadata (0 of 32 JSONs) names no place.",
  add=""),

dict(keys=[("HundredPaiwanStories", "pwn", "Northern")], verdict="village", link=["outside"],
  title="Hundred Paiwan Stories, Northern: the 7 Kapayuanan texts fit the list; the other 25 I can’t place",
  readme="Nothing about place.",
  evidence=[
    ("063 THE PEOPLE OF PADAIN AND KAPAYUANAN … (Kapayuanan village, p.273)", "story heading, Paiwan Ch2.docx (texts 063–069)"),
    ("070 … (Tjukuvuɫ village, p.280)   ·   082 … told by Giɫgiɫaw of Vaɫulu village   ·   096 … Vaɫulu dialect", "story headings (070–074, 075–088, 089/092–094/096/100)"),
  ],
  places="Kapayuanan (7 texts), Tjukuvuɫ (5), Vaɫulu (20)",
  listsays="If Kapayuanan = 筏灣 (屏東縣 瑪家鄉 排灣村; my identification): 北排灣語 · 瑪家鄉: … 排灣村 ✓. Tjukuvuɫ and Vaɫulu: I can’t place them with confidence.",
  caveat="Paiwan village names only in the book; the identification is mine.",
  add=""),

# ------------------------------------------------------------------ MATCHES: TOWNSHIP ONLY
dict(keys=[("Amis-Pa-Verbs", "ami", "Coastal")], verdict="township", link=["source", "roman"],
  title="Amis pa- verbs (Wu 2006): Changpin, Taitung County",
  readme="README lines 3 and 9 already say this: “Haian/Coastal Amis from Changpin, Taitung.”",
  evidence=[
    ("The data discussed in this paper was collected from Haian Amis (i.e. Coastal Amis), one of the Central dialects spoken in Changpin, Taitung County.", "footnote, PDF p. 1 — read from /workspace/Formosan-Amis-Pa-Verbs git history, c70dbdb:data/pa-verbs.pdf"),
  ],
  places="Taitung County; Changpin (長濱)",
  listsays="海岸阿美語 · 臺東縣 長濱鄉: 樟原村、三間村、長濱村、竹湖村、寧埔村、忠勇村 ✓ (township; Changpin = 長濱 is my reading of the romanization)",
  caveat="No village is named; five informants are thanked (Panay, Ofad, Ngaday, Talod, Ohay) without places.",
  add=""),

dict(keys=[("NTUFormosanCorpus", "ami", "Coastal")], verdict="township", link=["source"],
  title="NTU corpus, Amis (Coastal): Ciwkangan = 長光, 長濱, 台東縣",
  readme="Nothing about place.",
  evidence=[
    ("阿美語, Amis, Ciwkangan(台東縣長光社區)", "meta.language of 4 source JSONs; all 18 say Ciwkangan, 6 add 長光"),
    ("My hometown is in Ciwkangan, in Taitung, in Kakacawan. / 我的故鄉在台東長濱長光。", "Amis_Nr-intro_ofad.json record 8"),
  ],
  places="台東 長濱 長光 (Ciwkangan)",
  listsays="海岸阿美語 · 臺東縣 長濱鄉 ✓ (township). 長光 is a community name, not one of the 村 the list names.",
  caveat="One speaker later lived in Taipei; where each recording was made is not stated.",
  add=""),

dict(keys=[("Safolu-Amis-Dictionary", "ami", "Coastal")], verdict="township", link=["secondhand"],
  title="Safolu Amis dictionary: the author’s community, Madawdaw (麻荖漏), Chenggong",
  readme="README lines 14–17 already say this: “it records the author’s documented community (Madawdaw, Chenggong) …”",
  evidence=[
    ("An interview with author Safolu Kacaw (蔡中涵) describes his dictionary work in the Madawdaw community in Chenggong", "docs/dialect_evidence.md lines 8–10 (our paraphrase of an online interview, not checked here)"),
  ],
  places="成功 (Chenggong); 麻荖漏部落 (Madawdaw)",
  listsays="海岸阿美語 · 臺東縣 成功鎮 ✓ (township). 麻荖漏 is a community, not one of the 里 the list names.",
  caveat="Secondhand: the interview is online and its wording was not checked.",
  add=""),

dict(keys=[("TangRecordingsOfTaroko", "trv", "Truku")], verdict="township", link=["source", "roman"],
  title="Tang recordings of Taroko: Paradisec lists “Siyu-Lin, Hualien”",
  readme="Nothing about place.",
  evidence=[
    ("\"contentLocation\": [ { \"@id\": \"#place-Siyu-Lin, Hualien\" } ]", "CodeAndDocs/Metadata/AIT1-00{1,2,3,4}-ro-crate-metadata.json (same in all 4)"),
  ],
  places="Hualien; Siyu-Lin (秀林)",
  listsays="太魯閣語 · 花蓮縣 秀林鄉 ✓ (township; Siyu-Lin = 秀林 is my reading of the romanization)",
  caveat="Paradisec’s place record itself is not in the committed extract; no village or speaker origin is recorded locally.",
  add="PARADISEC catalogues all four items (AIT1-001 to AIT1-004) with the content location “Siyu-Lin, Hualien”; no village or speaker information is recorded locally."),

dict(keys=[("Cuerq-Pourrias-Poinsot-Amis-Dictionary", "ami", "Coastal")], verdict="township", link=["source"],
  title="Poinsot dictionary, Coastal file (2 entries): marked {豐濱} and {Tingalaw}",
  readme="README lines 17–18 and 29: “two readings labelled with places on the coast (豐濱, Tingalaw) as Coastal.”",
  evidence=[
    ("{豐濱}", "place mark on one reading (book p. 16)"),
    ("Tigalaw … 花蓮縣豐濱鄉豐富村 - 台東縣東河鄉德高老村", "the book’s own entry Tigalaw, p. 556 (treating Tigalaw as Tingalaw is the agent’s inference: the book writes ŋ as g)"),
  ],
  places="豐濱鄉; Tingalaw (豐濱鄉豐富 / 東河鄉德高老)",
  listsays="海岸阿美語 · 花蓮縣 豐濱鄉 ✓ and 臺東縣 東河鄉 ✓ (township). 豐富 and 德高老 are not among the villages the list names.",
  caveat="2 entries only.",
  add=""),

# ------------------------------------------------------------------ COUNTY ONLY
dict(keys=[("Whitehorn_Collection", "pwn", "Southern")], verdict="county", link=["source"],
  title="Whitehorn collection, Southern (2 files): recorded in Pingtung, 1954",
  readme="Nothing about place.",
  evidence=[
    ("Recorded summer of 1954 in Pingtung Taiwan.", "TEXT/@source of both files"),
    ("Place of recording: Pingtung, Taiwan · performer Rapi · place of birth: (blank) · Language: Paiwan (southern dialect)", "handwritten accession forms, CodeAndDocs/Whitehorn_Paiwan_01A_04 and 02A_02"),
  ],
  places="屏東 (Pingtung)",
  listsays="屏東縣 has 北排灣語, 中排灣語 and 南排灣語, so the county alone can’t confirm Southern. The label itself comes from Whitehorn’s form (“southern dialect”).",
  caveat="Both files are the same performer, Rapi.",
  add="The two Southern Paiwan recordings are both of one speaker, Rapi (female, c. 26), recorded in summer 1954 in Pingtung; Whitehorn’s accession forms give the language as “Paiwan (southern dialect)” and leave her place of birth blank."),

# ------------------------------------------------------------------ NAMED BUT UNPLACED
dict(keys=[("HundredPaiwanStories", "pwn", "Southern"), ("HundredPaiwanStories", "pwn", "Eastern")], verdict="unplaced", link=[],
  title="Hundred Paiwan Stories, Southern (41) and Eastern (6): villages are named in Paiwan, but I can’t place them on the list",
  readme="Nothing about place.",
  evidence=[
    ("001–017 (Qatsiɫay village) · 018–034 (Tjakuvukuvuɫ village) · 035–041 (Ɫaleklek village)", "Southern story headings"),
    ("052–054 (Patjavaɫ village) · 055–057 (Tjauvaɫi [or Tjavuaɫi] village)", "Eastern story headings"),
  ],
  places="Qatsiɫay, Tjakuvukuvuɫ, Ɫaleklek; Patjavaɫ, Tjauvaɫi",
  listsays="Not comparable without a Paiwan → Chinese village-name list, which neither the book nor the repo has.",
  caveat="I could guess some of these, but not confidently enough to report.",
  add=""),
]

# ------------------------------------------------------------------ NO LOCATION FOUND (table rows)
NOTFOUND = [
  (("FormosanBankGitBook", "pwn", "Eastern"), "Translator Xuan Ruan; no committed file says where the translator is from. README: “Eastern Paiwan was confirmed on 2025-02-24”, with no basis recorded.", "Ask the translator."),
  (("Glosbe", "trv", "Truku"), "The frozen crawl records no place, contributor or source per entry; “Truku” is the name of Glosbe’s language page (“Taroko”).", "glosbe.com only."),
  (("Glosbe", "xsy", "Saisiyat"), "Same as above (“Saisiyat” page).", "glosbe.com only."),
  (("Huteson-Rukai-Survey", "dru", "Dona"), "Only the wordlists were transcribed; the XML carries the source’s labels “Tona”/“Maga”. The report body with maps (pp. 4–32) and questionnaires (pp. 33–37) was not transcribed, and no PDF is on this machine.", "SIL archive; Basecamp card 8255603132."),
  (("Huteson-Rukai-Survey", "dru", "Maolin"), "Same as above.", "Same."),
  (("ILRDF_Dicts", "ami", "Xiuguluan"), "The API data has no place or dialect field; audioClass (the Yami village field) is null for every recording of these 8 languages. README lines 43–47: the labels are FormosanBank’s own.", "ILRDF website (not reachable)."),
  (("ILRDF_Dicts", "bnn", "Junqun"), "Same.", ""),
  (("ILRDF_Dicts", "dru", "Wutai"), "Same.", ""),
  (("ILRDF_Dicts", "pwn", "Northern"), "Same.", ""),
  (("ILRDF_Dicts", "pyu", "Nanwang"), "Same.", ""),
  (("ILRDF_Dicts", "tay", "Sekolik"), "Same.", ""),
  (("ILRDF_Dicts", "trv", "Tegudaya"), "Same. (Side note: the source tags 76 Seediq entries as 德鹿谷 (75) or 都達 (1), not Tegudaya.)", ""),
  (("ILRDF_Dicts", "trv", "Truku"), "Same.", ""),
  (("NTUFormosanCorpus", "bnn", "Junqun"), "0 of 93 source JSONs name a place: meta.language is always “郡群布農語, Bunun, Isbukun”.", ""),
  (("NTU_Paiwan_ASR", "pwn", "Central"), "No committed file records a home village for any of the 16 pseudonymous speakers; the build reads only pseudonym and dialect from the private speaker key, which is not on this machine.", "Private speaker key / Prof. Sung."),
  (("NTU_Paiwan_ASR", "pwn", "Eastern"), "Same.", ""),
  (("NTU_Paiwan_ASR", "pwn", "Northern"), "Same.", ""),
  (("NTU_Paiwan_ASR", "pwn", "Southern"), "Same.", ""),
  (("Paiwan_Stories", "pwn", "Eastern"), "Colophons name the author (gesi giling 阮翠芳) but no village; the only address is the publisher’s (新北市汐止區).", "Ask the author."),
  (("SEALS33", "xsy", "Saisiyat"), "The page does not name the Saisiyat translator; the only place (台北市 集思台大會議中心) is the conference venue.", "Live page credits / permission correspondence."),
  (("WakelinTexts", "tao", "Yami"), "The article gives only “Informant: <name>, <date>” (6 texts, 1955–1957). README lines 17 and 21 say “collected on Orchid Island”, but the article never says so (0 hits for Orchid, Island, Botel, Lanyu, Taiwan, Formosa).", ""),
  (("Li-Conjunction-Thao", "ssf", "Thao"), "Li (2014) names his two informants, Puni (1975–76; texts 1–30 except 4) and Kilaʃ (1996–2003; texts 31–42), but no village (printed pp. 401, 408). The only place is about the language: “Thao is a Formosan language spoken at Sun-Moon Lake in central Taiwan” (printed p. 401). That agrees with the list (邵語 · 南投縣 魚池鄉), but it is not a collection place. Li also says Blust collected from “the same informant, Kilaʃ”, and Blust places Kilash in Te-hua village. Carrying that over is my inference.", "Li (2011), the text collection the article cites; not on this machine."),
  (("ILCAA-Kanakanavu-Texts", "xnb", "Kanakanavu"), "The book says the texts were “collected by Erin Asai in 1931, Kuang Mei in 1977-78, Paul Li in 1999-2000, and Shigeru Tsuchida in the early 2000s” but gives no place per text (PDF p. 13). The only places are about the language: “only spoken by very few older speakers in Namasia, Kaohsiung today”. That agrees with the list (卡那卡那富語 · 高雄市 那瑪夏區). The villages named, Tanganua 民生村, Minquan 民權里 and Takanua 達卡努瓦里, come up in historical and phonetic remarks (PDF pp. 13, 15). 民生村 and 民權里 are older names that the list doesn’t use.", "Per-text field notes of the four collectors."),
  (("Cuerq-Pourrias-Poinsot-Amis-Dictionary", "ami", "Southern"), "The book’s key defines N：北方話 and S：南方話 but gives no places. Our build files both as “Southern” = 南勢, which the list calls 南勢阿美語(原北部阿美語), i.e. the former Northern dialect: fits 北方話, but not obviously 南方話.", ""),
  (("Cuerq-Pourrias-Poinsot-Amis-Dictionary", "szy", "Sakizaya"), "Key: Z：Zakiraya 話. No place.", ""),
]

NOTLISTED = [
  (("Campbell-Favorlang", "bzg", "Favorlang"), "Favorlang (extinct)"),
  (("Latham-1862", "bzg", "Favorlang"), "Favorlang (extinct)"),
  (("Latham-1862", "fos", "Siraya"), "Siraya"),
  (("Siraya_Gospels", "fos", "Siraya"), "Siraya"),
  (("UtrechtManuscriptWordList", "fos", "Siraya"), "Siraya"),
]

# ======================================================================== RESPONSES (round 1)
import re as _re
def _slug(k): return _re.sub(r"[^a-z0-9]+", "-", f"{k[0]}-{k[1]}-{k[2]}".lower()).strip("-")

# README text for the NTU cards (from the research notes; not yet in any README)
_NTU_ADD = {
  ("NTUFormosanCorpus","ami","Coastal"): "NTU’s metadata places the Amis stories in Ciwkangan, 台東縣長光社區 (meta.language of 4 story JSONs, e.g. story/Amis_Ciwkangan/Amis_Nr-intro_ofad.json); one speaker gives his hometown as 台東長濱長光 (same file, record 8).",
  ("NTUFormosanCorpus","tay","Wenshui"): "NTU’s Atayal (Mayrinax/汶水) stories come from speakers of 清安村 (transcriber’s note in all 11 story JSONs, e.g. AtaNr-dailylife1_Iwan.json); AtaNr-moving_Takun.json (record 146) says that text was collected at Savawqil.",
  ("NTUFormosanCorpus","ckv","Kavalan"): "NTU labels 29 of the 31 Kavalan stories “Xinshe (新社)” (meta.language). The speakers’ hometown is 新社, but some texts were recorded among Kavalan living in Taipei (e.g. KavNr-ancestor_buya.json, record 179: 我們在台北這裡).",
  ("NTUFormosanCorpus","tsu","Tsou"): "NTU labels 7 Tsou stories “TapangU” (達邦, as NTU’s own translation renders it in TsouConv-informants.json, record 9) and 5 “Tfya”; at least one conversation (TsouConv-informants) was recorded in Taipei.",
  ("NTUFormosanCorpus","xsy","Saisiyat"): "NTU’s Saisiyat folder is named “Tong-he” (東河) and one story is labelled “Tong-he(東河)” (SaiNr-Molaw.json); in SaiNr-holiday_kalaeh a _oemaw.json one speaker speaks of 向天湖 as “here” (record 114).",
  ("NTUFormosanCorpus","trv","Tegudaya"): "NTU’s Seediq metadata names no place; in the stories, speakers place themselves in 眉溪部落, 仁愛鄉 (sdqNr-mother_iwan 2020s.json, record 5) and 清流部落/Gluban (sdqNr-sisin_dakis 2020s.json, record 6).",
  ("NTUFormosanCorpus","xnb","Kanakanavu"): "NTU’s Kanakanavu metadata names no place; in the stories, one speaker says 我是那瑪夏的人 (kkvNr_hunting1_Muu.json, record 1) and another travels from 瑪雅里 to 達卡努瓦里 (kkvNr_mikon_Kuatu.json, record 3).",
  ("NTUFormosanCorpus","dru","Wutai"): "NTU names its Rukai “Vedai”/“Budai” (霧台魯凱語) but records no recording place; one storyteller says she grew up in 霧台 (RukaiNr-childhood_balenge.json, record 4).",
  ("NTUFormosanCorpus","szy","Sakizaya"): "NTU’s Sakizaya metadata names no place; one storyteller identifies as from 馬立雲 (skzyNr-class_sinay.json, record 177).",
}

# --- option sets. Each option: (key, button label, what it would do)
README_Q = lambda corpus: dict(key="readme", prompt="README text above",
  options=[("add", "Add it", f"Adds the proposed text to Corpora/{corpus}/README.md. I’d show you the diff before committing."),
           ("add-edit", "Add it with my edits", "Same, using the wording in your note."),
           ("leave", "Leave the README as is", "No change.")])
GENERAL_Q = dict(key="action", prompt="What should happen",
  options=[("leave", "Leave as is", "No change."),
           ("followup", "Follow up", "Say what in the note.")])
RESEARCH = ("research", "Needs more evidence first", "Say what evidence in the note; nothing changes meanwhile.")

SPECIAL_Q = {
  "wilangyutasvideos-tay-sekolik": [dict(key="label", prompt="Dialect label (83 files)", options=[
      ("keep", "Keep Sekolik", "No change."),
      ("fourseasons", "Relabel FourSeasons (四季泰雅語)", "dialect=\"Sekolik\" → \"FourSeasons\" on all 83 files; anything built from the dialect (standard tier, statistics) is rebuilt. Diff shown before applying."),
      ("yilanzeaol", "Relabel YilanZeaol (宜蘭澤敖利泰雅語)", "dialect=\"Sekolik\" → \"YilanZeaol\" on all 83 files; same rebuild. Diff shown before applying."),
      RESEARCH])],
  "hundredpaiwanstories-pwn-central": [
      dict(key="text095", prompt="Text 095 “Makazayazaya dialect” (now Central)", options=[
        ("northern", "Move to Northern", "PaiwanCh2_095.xml: dialect=\"Central\" → \"Northern\" (1 file)."),
        ("unknown", "Set to unknown", "PaiwanCh2_095.xml: dialect=\"Central\" → \"unknown\" (1 file)."),
        ("keep", "Keep Central", "No change."), RESEARCH]),
      dict(key="text098", prompt="Text 098 “Kazazaɫan dialect” (now Central; I can’t place it)", options=[
        ("keep", "Keep Central", "No change."),
        ("unknown", "Set to unknown", "PaiwanCh2_098.xml: dialect=\"Central\" → \"unknown\" (1 file)."), RESEARCH])],
  "virginia-fey-dictionary-ami-xiuguluan": [dict(key="label", prompt="Dialect label (1 file)", options=[
      ("keep", "Keep Xiuguluan", "No change."),
      ("recheck", "Get Fey’s introduction and recheck", "I’d need the front-matter PDF (online only); nothing changes meanwhile."),
      RESEARCH])],
  "cuerq-pourrias-poinsot-amis-dictionary-ami-xiuguluan": [dict(key="label", prompt="Label of the 23,304 unmarked sentences (now Xiuguluan)", options=[
      ("keep", "Keep Xiuguluan", "No change."),
      ("unknown", "Set them to unknown", "poinsot_chinese_unmarked_headwords.xml and _examples.xml (23,304 S): dialect=\"Xiuguluan\" → \"unknown\". The {F} and {T} files keep Xiuguluan."),
      RESEARCH])],
}

def _questions(r, rid, corpus):
    qs = list(SPECIAL_Q.get(rid, []))
    if r.get("add"): qs.append(README_Q(corpus))
    if not qs: qs.append(GENERAL_Q)
    return qs

for r in ROWS:
    r["id"] = _slug(r["keys"][0])
    if not r.get("add") and r["keys"][0] in _NTU_ADD:
        r["add"] = _NTU_ADD[r["keys"][0]]
    r["questions"] = _questions(r, r["id"], r["keys"][0][0])

# --- not-found rows grouped into answerable items
_nf = {k: (why, where) for k, why, where in NOTFOUND}
def _nfitem(iid, title, keys, questions, add=""):
    return dict(id=iid, title=title, keys=keys, why=[(_k, _nf[_k][0], _nf[_k][1]) for _k in keys], questions=questions, add=add)

NOTFOUND_ITEMS = [
  _nfitem("nf-wakelin", "WakelinTexts (Yami): the README says “collected on Orchid Island”, the article doesn’t", [("WakelinTexts","tao","Yami")],
    [dict(key="claim", prompt="The README’s “collected on Orchid Island” (lines 17 and 21)", options=[
      ("remove", "Remove it", "Replace with: “The article does not say where the texts were recorded; it gives each informant’s name and the date (1955–1957).”"),
      ("keep", "Keep it", "No change."),
      ("reword", "Reword it", "Use the wording in your note.")])]),
  _nfitem("nf-poinsot-southern", "Poinsot dictionary, Southern: the book’s “southern speech” is filed under 南勢 (former Northern Amis)", [("Cuerq-Pourrias-Poinsot-Amis-Dictionary","ami","Southern")],
    [dict(key="slabel", prompt="Label of the {S} 南方話 entries (1,169 sentences; now Southern = 南勢)", options=[
      ("keep", "Keep Southern", "No change."),
      ("unknown", "Set them to unknown", "poinsot_chinese_S_headwords.xml and _examples.xml (1,169 S): dialect=\"Southern\" → \"unknown\". The {N} 北方話 files keep Southern."),
      RESEARCH])]),
  _nfitem("nf-li", "Li Thao conjunction: informants named, no village", [("Li-Conjunction-Thao","ssf","Thao")],
    [README_Q("Li-Conjunction-Thao")],
    add="Li’s examples come from 42 texts he collected from two informants: Puni (1975–1976; texts 1–30 except 4) and Kilaʃ (1996–2003; texts 31–42) (Li 2014: 401, 408). The article says only that Thao is “spoken at Sun-Moon Lake in central Taiwan”; it does not name the informants’ village."),
  _nfitem("nf-ilcaa", "ILCAA Kanakanavu texts: collectors named, no place per text", [("ILCAA-Kanakanavu-Texts","xnb","Kanakanavu")],
    [README_Q("ILCAA-Kanakanavu-Texts")],
    add="The book says its texts were collected by Erin Asai (1931), Kuang Mei (1977–78), Paul Li (1999–2000) and Shigeru Tsuchida (early 2000s) but does not say where each was recorded; it says Kanakanavu is spoken only by a few older speakers in Namasia, Kaohsiung (PDF p. 13)."),
  _nfitem("nf-ilrdf", "ILRDF dictionaries (8 dialect-labelled languages): no place in the data", [k for k in _nf if k[0]=="ILRDF_Dicts"],
    [README_Q("ILRDF_Dicts")],
    add="The ILRDF source records no village or place for the Amis, Atayal, Bunun, Paiwan, Puyuma, Rukai, Seediq and Truku entries: the API’s per-recording audioClass field, which holds the village for Yami, is empty for all their recordings. Their dialect values are FormosanBank’s own labels, not read from the source."),
  _nfitem("nf-ntu-bunun", "NTU corpus, Bunun: no place anywhere", [("NTUFormosanCorpus","bnn","Junqun")],
    [README_Q("NTUFormosanCorpus")],
    add="NTU’s Bunun data names no place; its metadata gives only the dialect (Isbukun) and the speakers’ birth years."),
  _nfitem("nf-ntu-asr", "NTU Paiwan ASR (4 dialects): speakers’ villages are only in the private key", [k for k in _nf if k[0]=="NTU_Paiwan_ASR"],
    [dict(key="action", prompt="What should happen", options=[
      ("leave", "Leave as is", "No change."),
      ("key", "Check the private speaker key", "You’d give me access to the key; I’d report each pseudonym’s village against the list (pseudonyms only)."),
      ("followup", "Follow up another way", "Say how in the note.")])]),
  _nfitem("nf-huteson", "Huteson Rukai survey (Dona, Maolin): places are in report pages we didn’t transcribe", [k for k in _nf if k[0]=="Huteson-Rukai-Survey"],
    [dict(key="action", prompt="What should happen", options=[
      ("leave", "Leave as is", "No change."),
      ("pdf", "Get the survey PDF and check", "You’d put the PDF somewhere I can read (it’s on Basecamp card 8255603132); I’d quote the villages."),
      ("followup", "Follow up another way", "Say how in the note.")])]),
  _nfitem("nf-gitbook", "FormosanBankGitBook (Eastern Paiwan): translator’s community not recorded", [("FormosanBankGitBook","pwn","Eastern")], [GENERAL_Q]),
  _nfitem("nf-paiwan-stories", "Paiwan_Stories (Eastern): author named, no village", [("Paiwan_Stories","pwn","Eastern")], [GENERAL_Q]),
  _nfitem("nf-glosbe", "Glosbe (Truku, Saisiyat): no per-entry source", [("Glosbe","trv","Truku"), ("Glosbe","xsy","Saisiyat")], [GENERAL_Q]),
  _nfitem("nf-seals33", "SEALS33 (Saisiyat): translator not named", [("SEALS33","xsy","Saisiyat")], [GENERAL_Q]),
  _nfitem("nf-poinsot-sakizaya", "Poinsot dictionary, Sakizaya: {Z} entries carry no place", [("Cuerq-Pourrias-Poinsot-Amis-Dictionary","szy","Sakizaya")], [GENERAL_Q]),
]
_cov = [k for it in NOTFOUND_ITEMS for k in it["keys"]]
assert sorted(_cov) == sorted(_nf), (set(_nf) - set(_cov), set(_cov) - set(_nf))

NOTICED_ITEMS = [
  dict(id="noticed-ilrdf-seediq", title="ILRDF Seediq: the source itself tags 76 entries 德鹿谷 (75) or 都達 (1), but the file is labelled Tegudaya",
       questions=[dict(key="action", prompt="What should happen", options=[
         ("leave", "Leave as is", "No change."),
         ("look", "Look into those 76 entries", "I’d list them with the source’s tag and report back; nothing changes."),
         ("followup", "Something else", "Say what in the note.")])]),
]

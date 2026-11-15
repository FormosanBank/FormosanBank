# Where the data was collected: Seediq / Truku / Atayal / Saisiyat group (agent C)

Read-only research for the 2026-11-07 dialect-location request. FormosanBank files were read only from the worktree at
`main` (`/tmp/claude-1000/-workspace-FormosanBank/e78edf4a-c5b9-400e-864e-ff685648c37f/scratchpad/fb-main`,
HEAD `2a345f0d9 Merge pull request #317`). The XML dialect counts below come from reading each file's `<TEXT>` tag.

## Deviations and discrepancies to report first

1. **Files I wrote besides this one (a deviation from "the only file you may write").** To view scanned pages, I
   rendered PDF pages to PNG files in a new scratchpad folder outside every repo:
   `/tmp/claude-1000/-workspace-FormosanBank/e78edf4a-c5b9-400e-864e-ff685648c37f/scratchpad/locC_img/`, which now holds 15 files:
   `chang_pdf53.png chang_pdf54.png chang_pdf55.png chang_pdf56.png chang_pdf167.png chang_pdf168.png
   chang_crop69.png chang_crop70.png chang_crop131.png six_pdf1.png six_pdf2.png six_pdf10.png hsu_pdf3.png
   hsu_pdf18.png hsu_pdf21.png`. Brief rule 4 asks for rendered images, but rule 1 says this output file is the only
   file I may write. I should have used the Read tool's `pages` parameter on the PDF instead. I have NOT deleted
   them, because deleting is a further file operation. They are safe to delete.
   No repo was touched: `git status --short` is empty for the fb-main worktree. The two dev repos show only untracked files
   that were already there: `Formosan-Seediq-Chang-Reference-Grammar/Review/` (dated 2026-10-14) and
   `Formosan-Nowbucyang-Truku-Thesis/.DS_Store` (dated 2026-08-04).
2. **SEALS33 file count.** The task said "xsy Saisiyat (2 files)". In fact there is **1** xsy file
   (`XML/Saisiyat/saisiyat_seals.xml`). The corpus's second file is the trv/unknown Seediq file, which I ignored
   as instructed.

---

### Nowbucyang-Truku-Thesis
- Dialect label(s) in XML (xml:lang + dialect, with file counts): `xml:lang="trv" dialect="Truku"`: 1 file
  (`/tmp/claude-1000/-workspace-FormosanBank/e78edf4a-c5b9-400e-864e-ff685648c37f/scratchpad/fb-main/Corpora/Nowbucyang-Truku-Thesis/XML/Truku/Hsu_Lowking_Truku_WordFormation_2008.xml`).
  The `<TEXT>` attributes (`citation`, `BibTeX_citation`, `source`) name no place apart from `address = {Hsinchu}`,
  which is the university's location.
- README statement about place (verbatim + line):
  README.md lines 16–18: "The build configuration (`CodeAndDocs/scripts/config.yaml`) lists the community locations as Dumung / 銅門 and Tkijig / 崇德; the XML does not record a location or a finer dialect."
  (The README cites only the build config, not the thesis. It gives no county or township and no per-speaker information.)
- Sources searched:
  - README.md. The XML `<TEXT>`.
  - `CodeAndDocs/scripts/config.yaml` line 35: `community_locations: ["Dumung / 銅門", "Tkijig / 崇德"]`.
  - `CodeAndDocs/scripts/pipeline.py` line 1257: `"community_location_raw": "Dumung / 銅門; Tkijig / 崇德; Sioulin Township, Hualien County"`. Lines 1304–1305 are a "source facts" note citing PDF pp. 5 and 17–18.
  - The thesis PDF `/workspace/Formosan-Nowbucyang-Truku-Thesis/data/raw/pdf/許韋晟全文.decrypted.pdf` (164 pp.; born-digital text layer).
    - I read the text layer of PDF pp. 1–22 in full.
    - I searched every page's text for 引自|九階|教材|辭典|銅門|崇德|Dumung|Tkijig|Tkijil|秀林|部落人|發音人.
    - I viewed PDF pp. 3, 18 and 21 as images to confirm what is printed.
  - Page mapping: PDF p. 17 carries printed folio "1", so printed = PDF − 16 in the main text. The abstract pages, PDF 3 and 5, carry no folio.
- LOCATION EVIDENCE:
  - "本論文研究花蓮縣秀林鄉銅門部落(Dumung)與崇德部落(Tkijig)太魯閣語(Truku)的構詞法" — Chinese abstract 摘要, PDF p. 3 (no printed folio; image checked)
    applies to: whole thesis, so the whole corpus
    places named (as printed): 花蓮縣 / 秀林鄉 / 銅門部落(Dumung), 崇德部落(Tkijig)
  - "This thesis studies the word formation processes of the Truku language spoken in Dumung and Tkijig Tribes located in Sioulin Township, Hualien County." — English Abstract, PDF p. 5 (no printed folio)
    applies to: whole thesis / whole corpus
    places named (as printed): Hualien County / Sioulin Township / Dumung, Tkijig Tribes
  - "本論文田野調查的對象以秀林鄉的太魯閣族為主，包括銅門部落(Dumung)與崇德部落(Tkijil)共三位發音人，都屬於中年以上且熟諳太魯閣語及華語者" — §1.2 研究方法, printed p. 2 / PDF p. 18 (image checked: it really prints "Tkijil" here, while the abstract, §1.3.3 and footnote 9 print "Tkijig")
    applies to: the thesis's fieldwork data (three consultants)
    places named (as printed): 秀林鄉 / 銅門部落(Dumung), 崇德部落(Tkijil)
  - Table 1.1 本論文發音人, printed p. 2 / PDF p. 18 (image checked), verbatim rows:
    `太魯閣族名 | 漢名 | 職業 | 年齡 | 性別 | 部落`
    `Nobucyang | 許勝賀 | 吊卡車司機 | 59 | 男 | 銅門`
    `Silung | 許珍碧 | 退休國小老師 | 61 | 女 | 銅門`
    `Tusi Yudaw | 李季生 | 長老教會牧師 | 57 | 男 | 崇德`
    applies to: each consultant individually. Two are from 銅門 and one from 崇德. The XML does not record which sentence came from which consultant.
    places named (as printed): 銅門, 崇德
  - Footnote 8, which starts on printed p. 4 / PDF p. 20 and continues on printed p. 5 / PDF p. 21 (image of p. 5 checked): "本文發音人許勝賀先生和許珍碧女士為銅門(Dumung)部落人，據兩位表示，銅門部落的三個區域應該是榕樹(Kiibuh)、五鄰(Goring)和銅門(Dumung)，反而沒有聽過阿佑(Ayug)的稱呼。就我們觀察，文獻中的區域劃分，阿佑(Ayug)就是這兩位發音人居住的地方，即五鄰(Goring)，為何名稱上會有差異，我們也不清楚，有可能是調查過程的記音問題。……Goring 的由來是因為該部落起初在行政區的劃分上是屬銅門村 5 鄰，而現今已改成銅門村 7 鄰。"
    applies to: consultants 許勝賀 (Nobucyang) and 許珍碧 (Silung)
    places named (as printed): 銅門(Dumung)部落; 銅門村; the sub-area where they live is 五鄰(Goring) = 阿佑(Ayug) in the literature, today 銅門村 7 鄰. The other areas named are 榕樹(Kiibuh) and 銅門(Dumung). The body text of §1.3.2 on PDF p. 20 instead gives 榕樹 as "(Mklibuh)".
  - Footnote 9, printed p. 5 / PDF p. 21 (image checked): "本文發音人李季生先生為崇德部落(Tkijig)人，據他表示，崇德部落的由來就如文獻提到的一樣。"
    applies to: consultant 李季生 (Tusi Yudaw)
    places named (as printed): 崇德部落(Tkijig)
  - "本論文要研究的是花蓮縣秀林鄉太魯閣語的構詞法(word-formation)研究" — §1.6, printed p. 33 / PDF p. 49
    applies to: whole thesis
    places named (as printed): 花蓮縣 / 秀林鄉
  - About the author, who is not a consultant: "筆者是花蓮縣秀林鄉銅門部落(Dumung)的太魯閣族，因家庭環境的因素，就讀國小時即搬離開部落" — §1.1, printed p. 1 / PDF p. 17
    applies to: the author only
    places named (as printed): 花蓮縣 / 秀林鄉 / 銅門部落(Dumung)
- Observed vs inferred notes:
  - Observed: county, township, communities and the per-consultant 部落 are all stated in the thesis itself.
  - Caveat (observed): not all of the data comes from fieldwork. Printed p. 1 / PDF p. 17 says: "在語料的取得上，以實際田野調查為主，其它還參考了九年一貫德路固語九階教材、鄉公所出版的族語教材、太魯閣語初級辭典、學術期刊及論文等資料。"
    Footnote 71, printed p. 45 / PDF p. 61, says: "本文的複合詞語料，幾乎都是從田野調查中得來，少部分取自族語教材或課本".
    So a minority of examples may come from published teaching materials, not from the three consultants. I did not try to identify which examples those are.
  - Some usages are attributed per speaker in footnotes, e.g. footnote 31, PDF p. 39: "yamu(因為)是發音人許勝賀先生和許珍碧小姐的用法，另外還有 yaasa(yasa)也是「因為」，是發音人李季生先生的用法". The XML has no speaker attribute, so the corpus cannot be split by village from the XML alone.
  - The XML contains content (not metadata) that mentions a place: S `HSU_LOWKING_TRUKU_WORDFORMATION_2008_C01_E003B`, "Dumung ka sapah =mu" / "我的家在銅門。" It is an example sentence. I do not count it as location evidence.
- Could not find / not knowable locally: which individual example came from which consultant (or from a textbook). The thesis does not mark this per example in the parts I read.
- Proposed README addition (do NOT add): "The thesis's data come mainly from fieldwork in 花蓮縣秀林鄉 with three consultants: 許勝賀 (Nobucyang) and 許珍碧 (Silung) of 銅門部落 (Dumung; they live in the 五鄰/Goring area, 銅門村 7 鄰), and 李季生 (Tusi Yudaw) of 崇德部落 (Tkijig) (Table 1.1, printed p. 2; footnotes 8–9, pp. 4–5). Some forms were also taken from Truku teaching materials (printed p. 1)."

---

### TangRecordingsOfTaroko
- Dialect label(s) in XML (xml:lang + dialect, with file counts): `xml:lang="trv" dialect="Truku"`: 30 files under `XML/Truku/`. These are AIT1-001-1, AIT1-002-1, AIT1-003-1, and 27 files from AIT1-004. The `<TEXT>` attributes hold only the Paradisec item URL, the citation and the BibTeX entry, with no place. For example, `AIT1-004-10A.xml` has `source="https://catalog.paradisec.org.au/repository/AIT1/004"` and `citation="Tang, Apay. (1998). Tama visitation. Paradisec. https://dx.doi.org/10.4225/72/56EC2221E2713"`.
- README statement about place (verbatim + line): README: none. Line 3 is the nearest statement: "These audio files were collected by Prof. Apay Tang, a member of the Truku tribe … There is slightly more meta-data at Paradisec, but not much." It names no place.
- Sources searched:
  - README.md (all 141 lines; lines 120–141 describe the build steps and name no place).
  - All four `CodeAndDocs/Metadata/AIT1-00[1-4]-ro-crate-metadata.json`. 001–003 were read in full; 004 was read field by field, skipping its 54 `hasPart` entries.
  - `CodeAndDocs/audio_manifest.json`, searched for place|geo|location|speaker|contributor|consult|village|部落|Siyu|Hualien|lat|long: no hits.
  - All 30 XML `<TEXT>` tags, searched for Siyu|Hualien|秀林|place: 0 files.
  - `make_xml.py`: no place handling.
  - There is no local dev repo: `/workspace/` has no Tang/Taroko/Paradisec folder.
- LOCATION EVIDENCE:
  - `"contentLocation": [ { "@id": "#place-Siyu-Lin, Hualien" } ]` — `/tmp/claude-1000/-workspace-FormosanBank/e78edf4a-c5b9-400e-864e-ff685648c37f/scratchpad/fb-main/Corpora/TangRecordingsOfTaroko/CodeAndDocs/Metadata/AIT1-001-ro-crate-metadata.json` lines 33–37, key `metadata.contentLocation[0]["@id"]`. Identical at lines 33–37 of `AIT1-002-…json`, `AIT1-003-…json` and `AIT1-004-…json`.
    applies to: all four Paradisec items, so all 30 files (001: 1 file, 002: 1, 003: 1, 004: 27)
    places named (as printed): "Siyu-Lin, Hualien". There is also `"countries": [{"@id": "#country-Taiwan"}]`. AIT1-001 alone has `"languageAsGiven": "Truku"`.
- Observed vs inferred notes:
  - Observed: Paradisec's item-level `contentLocation` is "Siyu-Lin, Hualien" for every item.
  - This is a dangling graph reference: the `#place-…` node itself, which would carry geo coordinates or a fuller name, is not in the committed flattened extracts. README line 77 says "Unresolved graph references…".
  - No village, no 部落 and no speaker name or origin appear anywhere locally. `collector` and `recorder` are only an email address.
  - GENERAL KNOWLEDGE, NOT FROM THE SOURCE: "Siyu-Lin" looks like a romanization of 秀林 (秀林鄉, Hualien County).
- Could not find / not knowable locally:
  - The resolved Paradisec place record.
  - Any speaker or village information, which would only be on the Paradisec catalogue pages (online, unreachable from the container).
  - The uninspected item file `AIT1-001-2df.pdf`, which is listed in `hasPart` but not committed and not local. The README says it "has not been inspected or included", and it might contain notes.
- Proposed README addition (do NOT add): "PARADISEC catalogues all four items (AIT1-001 to AIT1-004) with the content location 'Siyu-Lin, Hualien' (`contentLocation` in `CodeAndDocs/Metadata/*.json`); no village or speaker information is recorded locally."

---

### WilangYutasVideos
- Dialect label(s) in XML (xml:lang + dialect, with file counts): `xml:lang="tay" dialect="Sekolik"`: 83 files (all of `XML/Atayal/`). All 83 `<TEXT>` tags carry the same `source="Wilang Yutas Atayal Videos"` and the channel citation, with no place.
- README statement about place (verbatim + line): README: none. Line 9: "Neither the earlier README nor the earlier GitBook page says how the Sekolik dialect label was determined." Line 13: "Wilang Yutas was an Atayal elder who, with his collaborator 劉宇陽, recorded a large number of videos speaking in Atayal." No place is given.
- Sources searched:
  - README.md.
  - `CodeAndDocs/video_manifest.tsv` (83 rows: output path, video id, transcript path, hash, kind). It has no title or description column.
  - All 34 `CodeAndDocs/raw_scrape/*.txt` caption files. `scripts/scrape.py` lines 41–46 and 72–73 show that each filename is the YouTube video title with punctuation stripped, followed by the video id.
  - I searched all transcripts with `grep -a` for 天祥|西寶|部落|村|鄉|縣|宜蘭|南澳|大同|秀林|花蓮|新竹|尖石|五峰|復興|桃園|烏來|苗栗|泰安|台中|臺中|和平|南投|仁愛|濱, and for Piyanan|Pyanan|南山|kahul|來自|從哪|qalang|Gilang|Taytogo|Nanaw|Mnibu|Skikun|Tosa|Truku|Lowsing|Sayun|Yagu.
  - I read the opening lines of 8 transcripts.
  - The other CodeAndDocs TSVs and scripts, searched for Piyanan|南山|宜蘭|大同|Nansan|Gilang: no hits.
- LOCATION EVIDENCE:
  - Captions of the 2016-05-25 interview at 濱咖啡 (Atayal line followed by its Mandarin caption line), `/tmp/claude-1000/-workspace-FormosanBank/e78edf4a-c5b9-400e-864e-ff685648c37f/scratchpad/fb-main/Corpora/WilangYutasVideos/CodeAndDocs/raw_scrape/目前先做這篇_20160525_濱咖啡訪談_Yutas_Wilang_目前先做這篇_U9I0GGy_pz0.txt`:
    lines 9–10 "nanu lalu su Tayal hiya? ima lalu su Tayal? / 你的泰雅名字是什麼？"; lines 15–16 "aw, Wilang Simaw. / 是的，我叫 Wilang Simaw";
    lines 21–24 "minkahul su inu? wah isu! / 你是從哪裡來的？請你來說一下吧" — "kahul saku son mha Piyanan. / 我來自於一個稱為南山的地方";
    lines 27–28 "cyux qenu qalang qasa, Piyanan? / 南山部落在哪裡？"; lines 31–32 "Piyanan puqing balay Taytogo no puqing pucing na  Taycyu na  takay. / 南山是大同鄉的最後面";
    lines 33–36 "aw, nanu yasa iwal su mha muci Gilang, Gilang Keng ru Taycyu Keng ru / 是，所以您的意思是說，宜蘭縣和臺中縣" — "syaw na bih cyux sobih balay rwa. / 很靠近兩縣的邊界";
    lines 37–38 "… / 如同你說的宜蘭縣最裡面的地方"; lines 87–88 "yonensey lga, kblayun nha gako qalang Piyanan la. / 四年級的時候，他們建造了南山部落的學校".
    applies to: the interviewee of this one video, who names himself Wilang Simaw. That is XML files `muqianxianzuozhepian_20160525_binkafeifangtan_Yutas_Wilang_muqianxianzuozhepian.xml` and `…_untranscribed.xml`.
    places named (as printed): 宜蘭縣 (Gilang Keng) / 大同鄉 (Taytogo) / 南山部落 (Piyanan); near the 臺中縣 (Taycyu Keng) border.
  - "qalang mu hiya ga Tayhocu Rato gun, Piyanan mu hiya." (line 6) and "baha hmswa' Gilang keng hiya ga,raral hiya ne Tayhukcu son nya Nansan" (line 12) — `…/raw_scrape/20190407_Yutas_Wilang_第1段_Sayun_MVI_1699_6VK6KU3zHD0.txt`. These lines are Atayal only, with no Mandarin caption. They are not in parentheses, which by the README (line 50) marks them as the main speaker.
    applies to: the main speaker of video MVI_1699 (`20190407_Yutas_Wilang_di1duan_Sayun_MVI_1699.xml`)
    places named (as printed): Tayhocu Rato gun, Tayhukcu, Gilang keng, Nansan, Piyanan
  - "ryax soni qani ga, kayal ta cikay mha qalang su ga. / 今天呢，我們來談一下關於你的部落。" (lines 2–3). Then, Atayal only: "qnxal Piyanan nanak ga" (line 105); "a~Maray ,Momaw knan ga kahul  saku qalang Mnibu'," (line 109); "Nibu' qani ga sami son Gilang ken  sami hiya pi." (line 111); "qalang myan i Piyanan ga,tqutux balay ay" (line 316); "son ta Piyanan hiya ga, puqin balay na Mnibu' ay." (line 387) — `…/raw_scrape/20181228_yutasWilang_01_kinhulan_族語字幕完成_SPmGl-aV3Q8.txt`
    applies to: video `20181228_yutasWilang_01_kinhulan_zuyuzimuwancheng.xml`. It is unclear from the text which speaker says line 109.
    places named (as printed): Piyanan, Mnibu' / Nibu', Gilang ken (also Nansan at line 20: "maki Nansan ga")
  - "(lalu' mu ga Yagu' Tanga')" (line 3) and "(minkahul saku Piyasan)a..baqun maku qalang yasa hiya wei,nwahan mu uzi." (line 4) — `…/raw_scrape/20190209_YutasWilang_ki_Yagu_01_第一段_0CBToN3jp4o.txt`. The words in parentheses are a second speaker; there is no Mandarin.
    applies to: second speaker Yagu' Tanga' in the "ki Yagu" series (Yagu_01 … Yagu_10, 14 XML files including companions)
    places named (as printed): "Piyasan" (spelled with an s; I cannot tell whether it is a different place from Piyanan or a caption variant)
  - Video titles (taken from filenames; no description text is committed):
    - `20180728_Yutas_Wilang_MVI_1081_族語字幕已完成到天祥西寶提親`
    - `目前先做這篇_20160525_濱咖啡訪談_Yutas_Wilang_目前先做這篇`
    applies to: those two videos. 天祥/西寶 name the topic of a passage (a marriage proposal, 提親). 濱咖啡 names the interview venue, with no town. Neither is a statement of where the speaker is from.
    places named (as printed): 天祥, 西寶; 濱咖啡
- Observed vs inferred notes:
  - **Observed** (Mandarin captions): the 2016 interviewee "Wilang Simaw" says he comes from Piyanan = 南山部落, at the back of 大同鄉, in the innermost part of 宜蘭縣, near the 臺中縣 border.
  - **Inferred:** that "Wilang Simaw" is the same person as the channel's "Wilang Yutas". The video title says "Yutas_Wilang" and the age (97) fits "elder", but the source never equates the two names.
  - **Inferred:** that he is the main speaker in the other videos.
  - **Inferred, low confidence:** my readings of the Atayal-only lines (MVI_1699 "qalang mu … Piyanan" = "my village … Piyanan"; Yagu "minkahul saku Piyasan" = "I came from Piyasan"). They rest only on parallels with the captioned 2016 lines: "kahul saku son mha Piyanan" = 我來自於…南山, and "qalang" = 部落. I am not an Atayal reader. Line 109 of the kinhulan file ("Momaw … kahul saku qalang Mnibu'") could be a different person or a different place, and I cannot resolve it.
  - Other place mentions in the transcripts are story content, not speaker origin: 南澳 in Yagu_04 line 13 "南澳那附近所流傳的歌" is about a song; Truku/Tosa/Skikun/Gogan appear in MVI_1081 and MVI_1115.
  - **Not location of recording:** no transcript or committed file says where any video was filmed.
- Could not find / not knowable locally:
  - Where each video was recorded.
  - Any YouTube video descriptions or channel "About" text, which exist only online.
  - The original Chinese titles of the 49 audio-only videos: only pinyin filenames are committed, e.g. `20180723_fangwenYutas_Wilan_08_hongu_utux_ru_ssiliq`.
  - The origin of the other named speakers (Sayun-series interlocutors, Lowsing Watan, Maray, Momaw), apart from the uncaptioned Yagu line above.
- Proposed README addition (do NOT add): "In the 2016-05-25 interview (video U9I0GGy_pz0) the elder, who gives his name as Wilang Simaw, says he comes from Piyanan, 南山部落 at the back of 大同鄉 in 宜蘭縣 (Mandarin captions: 「我來自於一個稱為南山的地方」「南山是大同鄉的最後面」). The recording locations of the videos are not stated."

---

### Seediq-Chang-Reference-Grammar
- Dialect label(s) in XML (xml:lang + dialect, with file counts): `xml:lang="trv" dialect="Tegudaya"`: 2 files (`XML/Seediq/chang-2000-seediq-reference-grammar.xml`, `XML/Seediq/chang-2000-seediq-long-texts.xml`). The long-texts `<TEXT source>` says: "…the sumuladuc 祭祀 narrative, told by 傅景賢 walis wadan and retold by 錢成鏡 pawan torih…". Neither `<TEXT>` names a place.
- README statement about place (verbatim + line):
  README.md lines 15–19: "**Dialect.** The book says it describes the 霧社方言 (Wushe dialect), spoken in 南豐 and 互助 villages, with consultants from 互助村 (printed p. 37: 本文研究的是霧社方言). FormosanBank tags this dialect `Tegudaya` (德固達雅; also called Tgdaya, Paran, 霧社). The book also thanks a speaker of the 春陽 dialect, Pastor 張秋雄 (walis ukan), for "許多寶貴的意見" (p. 38)."
  Lines 68–70: "…the `sumuladuc` 祭祀 ritual account told by 傅景賢 (walis wadan) and retold by 錢成鏡 (pawan torih)."
- Sources searched:
  - README.md (lines 1–80, plus a search for 互助|南豐|霧社|春陽|村|仁愛|南投|consultant|發音人|傅景賢|錢成鏡|Tegudaya).
  - The book `/workspace/Formosan-Seediq-Chang-Reference-Grammar/Private/source/basecamp/Chang_2000_Seediq_RG.original.pdf` (208 pp.). Its OCR text layer is garbled, so I searched it for 互助|南豐|南學|霧社|春陽|春楊|清流|眉溪|仁愛|部落|發音人|田野|Paran|Tgdaya|Tegudaya|Hoga|Alang. I then viewed as images PDF pp. 53–56 (printed 37–40), 167 (printed 151) and 168, and crops of PDF pp. 69, 70 and 131 (printed 53, 54, 115).
  - Page mapping: printed = PDF − 16. PDF p. 54 carries folio "38", PDF p. 55 "39", PDF p. 56 "40". PDF p. 53 is the chapter-1 opening page with no folio, so "printed p. 37" is inferred from the sequence.
  - Secondary scan `…/basecamp/6.original.pdf` (105 pp.). It has no text layer. Images of PDF pp. 1–2 show it is a two-page-spread scan of the same book (colophon "2000 年 3 月 1 日 初版一刷"). I did not read it further.
- LOCATION EVIDENCE:
  - "賽德克語是泰雅語群的一支，分佈在花蓮縣秀林鄉、萬榮鄉及南投縣仁愛鄉合作、精英、春陽、南豐、互助五個村，人口約有一萬四千人。賽德克語有三個次方言，即太魯閣方言、春陽方言及霧社方言。² 太魯閣方言通行於花蓮縣的兩個鄉，春陽方言通行於南投縣仁愛鄉的精英、春陽等村，而霧社方言則通行於南豐和互助兩村。本文研究的是霧社方言，在此我要感謝互助村發音人慷慨地提供語料和協助，我的發音人包括：
    傅景賢：民國三年生，族名 walis wadan。" — 第1章 導論 §一 賽德克語的分布與現況, printed p. 37 (no folio) / PDF p. 53 (image read)
    applies to: the whole book, so both corpus files. The dialect studied is 霧社方言, and the consultants are thanked as 互助村發音人.
    places named (as printed): 南投縣 / 仁愛鄉 / 互助村 (consultants); the 霧社方言 area is 南豐、互助兩村
  - "錢成鏡：民國十六年生，族名 pawan torih。
    詹秋木：民國二十二年生，族名 pawan tado。
    莊進利：民國十六年生，族名 walis neyung。
    郭明正：民國三十三年生，族名 dakis pawan。
    另外，講春陽方言的張秋雄牧師(walis ukan，民國四十七年生)也提供了許多寶貴的意見，在此一併致謝。" — printed p. 38 / PDF p. 54 (image read; the scan has a stray mark above the "p" of "pawan torih")
    applies to: the list continues the "我的發音人包括" sentence (5 consultants in all). 張秋雄 is thanked separately: he speaks 春陽方言, but the book gives no village for him.
    places named (as printed): none for the four consultants on this page (they fall under the p. 37 互助村 sentence); 春陽方言 for 張秋雄
  - "第 5 章是長篇語料，筆者在發音人錢成鏡(pawan torih)先生的協助下，訪問了族裡的耆老傅景賢(walis wadan)老先生，記錄了珍貴的祭祀資料。" — printed pp. 39–40 / PDF pp. 55–56 (images read)
    applies to: chapter 5, i.e. `chang-2000-seediq-long-texts.xml`
    places named (as printed): none (both men are on the p. 37–38 consultant list)
  - "說明：以下故事由傅景賢先生(walis wadan)口述，錢成鏡先生(pawan torih)轉述說明，經筆者記錄而成。" — 第5章 賽德克語的長篇語料, printed p. 151 (no folio) / PDF p. 167 (image read)
    applies to: `chang-2000-seediq-long-texts.xml` (37 S)
    places named (as printed): none
- Observed vs inferred notes:
  - **Verification of the README against the book:** the README's location statements match the printed text.
    - "霧社方言 … spoken in 南豐 and 互助 villages" = "霧社方言則通行於南豐和互助兩村".
    - "consultants from 互助村" = "感謝互助村發音人".
    - The quote "本文研究的是霧社方言" is exact.
    - The 春陽 sentence matches p. 38: the book's words are "講春陽方言的張秋雄牧師(walis ukan，民國四十七年生)也提供了許多寶貴的意見". The README drops the birth year but has nothing wrong.
    - The chapter 5 narrator and reteller are correct.
  - **Differences and gaps (none of them errors):**
    1. "printed p. 37" is an unnumbered page (PDF 53). The number is correct by sequence, but no folio is printed on it.
    2. The README omits the county and township. The book places 互助 among "南投縣仁愛鄉合作、精英、春陽、南豐、互助五個村".
    3. The README does not name the five consultants (傅景賢, 錢成鏡, 詹秋木, 莊進利, 郭明正).
    4. The README line 17 names "Tegudaya (德固達雅; also called Tgdaya, Paran, 霧社)" are FormosanBank's own labels. The book's passage uses only 霧社方言, and my search of the (garbled) text layer found no Paran/Tgdaya/Tegudaya.
    5. The book uses some data that is not from its own consultants, and the README does not say so:
       - Printed p. 38: "本書除了少部份是引用前人的研究外，大部份的語言材料都是筆者親自調查記錄的".
       - Printed pp. 53–54 / PDF pp. 69–70 (images read): "關於賽德克語的加綴詞，谷口龍子(1994)曾有系統地做過分析，……這裡我們除參考她的語料外，同時加入我們自己田野調查的資料".
       - Printed p. 115 / PDF p. 131 (image read): "有關賽德克語的疑問詞，張仲良(1994)有很詳細的討論，這裡我們僅參考他的語料，再配合我們自己田野調查的資料". (The text layer misreads this name as 張仲泉; the image shows 張仲良.)
       Some chapter 3–4 examples may therefore come from 谷口龍子 1994 or 張仲良 1994, whose collection places the book does not give.
  - **Inferred:** that each of the five listed consultants individually lives in 互助村. The book says so only collectively: it thanks "互助村發音人" and then lists "我的發音人包括".
- Could not find / not knowable locally:
  - The individual villages of the five consultants.
  - Where 張秋雄 lives.
  - Where 谷口龍子 (1994) and 張仲良 (1994) collected their data. Those works are not local.
  - Which corpus sentences came from those two works. Not determined.
- Proposed README addition (do NOT add): "The consultants are thanked as 互助村 speakers (南投縣仁愛鄉): 傅景賢 walis wadan, 錢成鏡 pawan torih, 詹秋木 pawan tado, 莊進利 walis neyung and 郭明正 dakis pawan (printed pp. 37–38). Some chapter 3–4 examples are drawn from 谷口龍子 (1994) and 張仲良 (1994) (printed pp. 54, 115)."

---

### SEALS33
- Dialect label(s) in XML (xml:lang + dialect, with file counts): `xml:lang="xsy" dialect="Saisiyat"`: **1** file (`XML/Saisiyat/saisiyat_seals.xml`). The other file is `xml:lang="trv" dialect="unknown"` (`XML/Seediq/seediq_SEALS.xml`), which I ignored as instructed. The xsy `<TEXT>` carries the citation "SEALS 33 Organizing Committee. (2024). 國家語言專區. SEALS 33. https://sites.google.com/view/seals33/national-languages" and `source="…; structured snapshot retrieved 2026-08-23T00:32:50+00:00; source_orthography=Ortho94"`, with no place.
- README statement about place (verbatim + line): README: none about the translators or speakers. Line 5: "for the 2024 Southeast Asian Linguistics Society meeting in Taipei." This is the conference venue. Line 23: "graciously provided by the authors". Line 58: "**Rights source:** Hsiu-chuan Liao, 2025-04-16; evidence: ask maintainer". This is a person, not a place.
- Sources searched:
  - README.md (all 277 lines).
  - `CodeAndDocs/source_snapshot.json`: all 29 rows, plus `excluded_presenter_blocks` and `excluded_non_corpus_sections`.
  - `CodeAndDocs/pre_correction_snapshot/*/*.xml` `<TEXT>` tags.
  - `CodeAndDocs/provenance.json`.
  - `CodeAndDocs/scripts/*.py`, searched for translat|author|liao|consult|譯|翻.
  - README and snapshot, searched for 村|鄉|部落|苗栗|新竹|南庄|五峰|向天湖|village|consultant|speaker|發音. The only hit was 部落 inside a talk title (row 26).
  - The git log of `Corpora/SEALS33`.
  - `/workspace/` contains no SEALS dev repo, and neither the README nor `provenance.json` names one.
- LOCATION EVIDENCE:
  - Snapshot row 4: `"zho": "地點：台北市 集思台大會議中心"`, `"xsy": "rape: -- ray taypae’ ziSe’ taywan kakiSsobae:oehan ka’a’iyalaehoe:an"` — `/tmp/claude-1000/-workspace-FormosanBank/e78edf4a-c5b9-400e-864e-ff685648c37f/scratchpad/fb-main/Corpora/SEALS33/CodeAndDocs/source_snapshot.json`, key `rows[3]` (source_row 4)
    applies to: content of S4 only. It is the **conference venue**, NOT where the Saisiyat text was translated or by whom.
    places named (as printed): 台北市 / 集思台大會議中心
- Observed vs inferred notes: nothing in the local material names the Saisiyat translator(s), let alone their village. The snapshot explicitly excludes "presenter names and affiliations", "organizer list" and "contact address" (`excluded_non_corpus_sections`). If the page credits a translator, the credit would sit in those excluded sections.
- Could not find / not knowable locally:
  - Who translated the page into Saisiyat, and from which community. This could only come from the live page (online; its organizer/credits sections were not captured) or from the permission correspondence with Hsiu-chuan Liao, which the README marks "evidence: ask maintainer".
  - The Saisiyat dialect area is not stated anywhere.
- Proposed README addition (do NOT add): none is possible from local sources. At most: "The source page does not identify the Saisiyat translator or their community; the Taipei location in S4 is the conference venue."

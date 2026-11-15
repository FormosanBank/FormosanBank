# Where was the data collected? Agent A (Amis group + Glosbe trv/xsy)

Read-only research. FormosanBank files were read from the main worktree
`/tmp/claude-1000/-workspace-FormosanBank/e78edf4a-c5b9-400e-864e-ff685648c37f/scratchpad/fb-main`
(HEAD `2a345f0d9 Merge pull request #317 ...`). Dev repos were read in place, and their git history with `git -C <path> show` (output to stdout only). I wrote no files except this one. No temporary files, images or extractions: the one PDF I read (Wu 2006) was piped from `git show` straight into pdfplumber.

**File counts.** The task listed "Virginia_Fey 2 files", "Glosbe trv 2 files" and "Glosbe xsy 4 files". Each count is double the published files: it also includes the copies under `CodeAndDocs/pre_correction_snapshot/`, which are unpublished baselines. The published counts are below.

---

### Amis-Pa-Verbs
- Dialect label(s) in XML (xml:lang + dialect, with file counts): `xml:lang="ami"` `dialect="Coastal"`: 1 file, `XML/Amis/pa-verbs.xml` (29 S). The `<TEXT>` `citation`, `BibTeX_citation` and `source` attributes name no place except the conference venue ("Puerto Princesa City, Palawan, Philippines"), which is not where the data was collected.
- README statement about place (verbatim + line):
  - `.../fb-main/Corpora/Amis-Pa-Verbs/README.md` line 3: "The paper identifies Haian/Coastal Amis from Changpin, Taitung."
  - same file line 9: "Page 1 identifies Haian/Coastal Amis from Changpin, Taitung."
  - `.../fb-main/Corpora/Amis-Pa-Verbs/CodeAndDocs/README.md` line 19 (about a different work, Wu's 2006 dissertation, which is not this corpus's source and not available locally): "p.4 identifies the same Haian/Coastal Changpin variety."
- Sources searched:
  - corpus folder (all files): grep for `changpin|taitung|haian|長濱|台東|臺東|consultant|informant|speaker|village|native`.
  - dev repo `/workspace/Formosan-Amis-Pa-Verbs`: the same grep. The PDF is not in the working tree (`Private/` is gitignored and absent), but it is in the dev repo's git history as blob `c70dbdb:data/pa-verbs.pdf`. Its sha256 is `9ba94321d9c8e926cf8cca3b0b81814400d2bb7194ba48574d77ad54490308f5`, which equals the hash recorded in `CodeAndDocs/source_manifest.tsv` and `TEXT/@source`.
  - PDF text layer: all 13 pages, grep for `changpin|taitung|hualien|village|informant|consultant|speaker|dialect|haian|collected|fieldwork|county`; read pp. 1–2 in full. The hits are on page 1 and page 12 (references) only.
- LOCATION EVIDENCE:
  - "The data discussed in this paper was collected from Haian Amis (i.e. Coastal Amis), one of the Central dialects spoken in Changpin, Taitung County. The author would like to thank the major Amis informants Ms. Jin-Mei Li (Panay in Amis), Mr. Jin-long Chen (Ofad in Amis), Ms. Hsiu-mei Lin (Ngaday in Amis), Mr. Wan-shuey Lin (Talod in Amis), and Ms. Jiun-jiu Lin (Ohay in Amis) for providing the data." — Wu (2006), footnote `*` on PDF p. 1 (the title page; the text layer has no printed page number, while pp. 2–3 print "2" and "3" at the top); PDF read from `git -C /workspace/Formosan-Amis-Pa-Verbs show c70dbdb:data/pa-verbs.pdf`
    applies to: the whole corpus (all 29 S; the paper's data as a whole). The five informants are named together, with no per-informant place and no per-example attribution.
    places named (as printed): county "Taitung County"; township/place "Changpin". Variety names as printed: "Haian Amis (i.e. Coastal Amis)", "one of the Central dialects".
  - Same footnote, context sentence: "According to Tsuchida (1982), Amis has five major dialects: Sakizaya (or Sakiraya), Northern (or Nansh i Amis), Tavalong-Vataan, Central, (Haian Amis and Hsiukulan Amis excluding Tavalong-Vataan) and Southern (Peinan Amis and Hengchun Amis)." — same location
    applies to: background classification, not data provenance.
    places named (as printed): none beyond the dialect names.
- Observed vs inferred notes: Observed: the paper states the data was collected from Haian (Coastal) Amis spoken in Changpin, Taitung County. Note that Wu calls Haian/Coastal "one of the Central dialects", following Tsuchida. Not stated: a village (村/部落) within Changpin, and where each informant lives. Page 1 also has a map, captioned "Amis / Revised from ccms.ntu.edu.tw/~danatang/word/kid2.doc". I did not render it as an image (the text layer was enough), so I don't know whether it marks a location.
- Could not find / not knowable locally: the village within Changpin; per-informant locations. Wu's dissertation (cited in CodeAndDocs/README.md line 19, "p.4") is online only (buffalo.edu) and is a different work.
- Proposed README addition (do NOT add): "Wu (2006, footnote on p. 1): 'The data discussed in this paper was collected from Haian Amis (i.e. Coastal Amis), one of the Central dialects spoken in Changpin, Taitung County.' It names five informants (Panay, Ofad, Ngaday, Talod, Ohay) but no village."

---

### Cuerq-Pourrias-Poinsot-Amis-Dictionary
- Dialect label(s) in XML (xml:lang + dialect, with file counts). Each file has one TEXT, and its `source` attribute ends "source label X":
  - `ami` + `Coastal`: 1 file (`poinsot_chinese_Coastal_headwords.xml`, 2 S; source labels {豐濱}, {Tingalaw})
  - `ami` + `Southern`: 4 files (`N_headwords` 1001 S, `N_examples` 91, `S_headwords` 1077, `S_examples` 92)
  - `ami` + `Xiuguluan`: 6 files (`F_headwords` 856, `F_examples` 62, `T_headwords` 308, `T_examples` 35, `unmarked_headwords` 19401, `unmarked_examples` 3903)
  - `szy` + `Sakizaya`: 2 files (`Z_headwords` 671, `Z_examples` 27)
- README statement about place (verbatim + line), `.../fb-main/Corpora/Cuerq-Pourrias-Poinsot-Amis-Dictionary/README.md`:
  - lines 16–18: "Entries marked {Z} are Sakizaya (698) and are published as Sakizaya. The others are Amis, filed by the book's labels: {N} and {S} as Southern, {F}, {T} and unmarked entries as Xiuguluan, and two readings labelled with places on the coast (豐濱, Tingalaw) as Coastal."
  - lines 22–30, the table headed "Label in the book | Meaning (book's own key)": "{S} | 南方話", "{N} | 北方話", "{F} | 鳳林話", "{T} | 富田語", "(none) | —", "{豐濱}, {Tingalaw} | places", "{Z} | Zakiraya 話".
  - lines 37–38: "The book labels many entries and readings with the variety they belong to: 南方話 {S}, 北方話 {N}, 鳳林話 {F}, 富田語 {T} and Zakiraya 話 {Z}."
  - The README says nothing about where the compilers collected the material, or where their consultants were from.
- Sources searched:
  - the corpus build text `.../CodeAndDocs/source/pourrias-poinsot.txt` (17,929 lines): grep for `南方話|北方話|鳳林|富田|Zakiraya|豐濱|Tingalaw|台東|臺東|花蓮|部落`, and for every `{…}` marker.
  - the proofreading database `.../CodeAndDocs/source/toufu.sq3`, opened read-only (`mode=ro&immutable=1`): the pages present are p=5..599 (27,621 rows). There are no rows for pp. 1–4, so the front matter is not transcribed. Searched `ans` for the key words.
  - the XML: every `notes="... source label: ..."` value.
  - dev repo `/workspace/Formosan-Poinsot`: README, docs/, the git history of README (all commits), and the upstream clones in `_sources/`:
    - `amis-chinese-poinsot-onefile`: README, `amis_parser.rb`, `check`
    - `amis-chinese-poinsot-toufu`: branch toufu only; no scans
    - `amis-francais`: README, txt/001–353
    - `amis-moedict`: README, `about.html` via `git show HEAD:about.html`
  - No local copy of the scan images exists. The onefile README says letter a starts at scan image `img-117110211_頁面_005.tiff`, so pages 001–004 are front matter, and they are only online.
- LOCATION EVIDENCE:
  - "Tigalaw：花蓮縣豐濱鄉豐富村 - 台東縣東河鄉德高老村" — the book's own head-word entry, `pourrias-poinsot.txt` line 16738; XML `unmarked-L16738-01`, notes "printed p.556 l.26"
    applies to: this is a dictionary entry *defining the place name*. It is not a statement about where the data came from. The corpus files the one reading labelled {Tingalaw} (`podok - <4> {Tingalaw}：米酒`, source line 13029, "printed p.426 l.40", S `Coastal-L13029-01`) as Coastal. Reading {Tingalaw} as the same place as head word "Tigalaw" is INFERRED: the book writes ŋ as `g`, so Tigalaw = Tingalaw.
    places named (as printed): 花蓮縣 豐濱鄉 豐富村; 台東縣 東河鄉 德高老村 (the entry gives two places with this name).
  - "(小蟒蛇 = alomdas {豐濱})" — `pourrias-poinsot.txt` line 373; XML `Coastal-L00373-03`, notes "printed p.016 l.19; source label: 豐濱"
    applies to: 1 reading (`alomdas`), filed Coastal.
    places named (as printed): 豐濱 (no level given; the book's other entries print "豐濱鄕"/"豐濱鄉").
  - "= na'op {玉里}" — line 8672 (`lenlen = lelen：淹沒，洪水；…；= freg {N} = na'op {玉里} = fodo' {S}`); XML notes "printed p.281 l.19–p.281 l.20; source label: 玉里"
    applies to: 1 reading (`na'op`), filed in the *unmarked* (Xiuguluan) file, not a place-specific file.
    places named (as printed): 玉里.
  - "tireg - <3>：{光復鄉} 停止…" — line 16912; XML notes "source label: 光復鄉" on the TRANSL 停止
    applies to: 1 sense, in the unmarked (Xiuguluan) file.
    places named (as printed): 光復鄉.
  - "karo' - {T} = kamoraw = wirok：(花蓮語)柚子；{S}榕樹" — line 6766; XML notes "source label: 花蓮語" on 3 TRANSL 柚子 (T_headwords `T-L06766-01`, "printed p.219 l.21", plus 2 in the unmarked file)
    applies to: 1 sense.
    places named (as printed): 花蓮 (in "花蓮語").
  - The dialect-label meanings (鳳林話, 富田語, 南方話, 北方話). The README calls these "the book's own key", but the key is NOT in any local copy of the book: the transcription starts at scan p.5, and pp. 1–4 are not local. The only local file that spells them out is the upstream transcriber's parser, `/workspace/Formosan-Poinsot/_sources/amis-chinese-poinsot-onefile/amis_parser.rb` lines 3–18: `"S" => "南方話"`, `"F" => "鳳林話"`, `"T" => "富田語"`, `"N" => "北方話"`, `"Z" => "撒奇萊雅語"`, `"豐濱" => "豐濱"`, `"玉里" => "玉里"`, `"Tingalaw" => "豐濱豐富部落"`, `"光復鄉" => "光復鄉"`. Git log on that file: "655ee01 wildjcrt 2025-09-27 Add amis_parser.rb from Claude". So this is a 2025 transcriber's (AI-assisted) code, not the book.
    applies to: the label files. {F} covers F_* (918 S), {T} covers T_* (343 S), {S}/{N} cover S_*/N_* (2,261 S), {Z} covers Z_* (698 S).
    places named (as given there): 鳳林 (in 鳳林話), 富田 (in 富田語), 豐濱豐富部落 (for Tingalaw). 南方/北方 are directions, not places.
  - The book's own entries locating 富田 and 鳳林 (these are entries, not provenance): "Tafalog：花蓮縣光復鄉富田村" (line 15730, "printed p.521 l.29"); "'Adif：花連縣鳳林鎭山民村" (line 120, "printed p.008 l.31"); 鳳林 occurs on 11 source lines and 富田 on 6.
    applies to: nothing directly. Linking {T} 富田語 to 光復鄉富田村, or {F} 鳳林話 to 鳳林鎭, is INFERRED from matching names.
  - "本字典由在花蓮鐵份部落服務的巴黎外方會潘世光神父慨允釋出，供非商業使用。" — `/workspace/Formosan-Poinsot/_sources/amis-francais/README.md` line 3 (upstream miaoski/amis-francais README, first committed 2014-12-24 by Lin Zhemin)
    applies to: where Maurice Poinsot (co-author of the companion **Amis–French** volume) was serving when he released it. It is not a statement about where the Amis–Chinese volume's data was collected, nor about its compiler Cuerq (顧向前). It also comes from the transcribers' README, not from the book.
    places named (as printed): 花蓮 鐵份部落.
- Observed vs inferred notes:
  - Observed: the book marks 4 readings and senses with place names: {豐濱}, {Tingalaw}, {玉里}, {光復鄉}, plus "(花蓮語)" once. The corpus filed only {豐濱} and {Tingalaw} as Coastal. {玉里} and {光復鄉} stayed in the Xiuguluan "unmarked" file, with notes.
  - Not found anywhere local: the meanings of {F}/{T}/{S}/{N}/{Z} printed in the book itself. The README's "book's own key" may well be right (it writes "Zakiraya 話", which differs from the parser's "撒奇萊雅語", so someone probably read a scan), but I could not verify it.
  - The code that sets these labels is `/workspace/Formosan-Poinsot/CodeAndDocs/build_amis_chinese_xml.py` lines 53–54, where `FILE_DIALECT = {"S": "Southern", "N": "Southern", "F": "Xiuguluan", "T": "Xiuguluan", "unmarked": "Xiuguluan", ...}`. So {N}, whose gloss is 北方話 ("northern speech"), is filed as Southern; neither the README nor that code says why. Unmarked entries (23,304 S, about 85% of the corpus) are filed Xiuguluan with no stated source basis. An earlier dev README (commit b680d65, 2026-09-04) said: "The file dialect is inferred as Xiuguluan from the reported fieldwork location, following the recorded Sifo and Joshua review. This inference is useful but not certain." That was a FormosanBank inference, not a source statement.
  - Not provenance: the entry "Sakiraya：阿美的小姐(住在左倉，新社村…)，族氏名稱" (line 14270, S_headwords, "printed p.471 l.12–l.13") is a dictionary definition. It does not say where the {Z} material was collected.
- Could not find / not knowable locally: any statement of where Cuerq/Pourrias (or Poinsot) collected the material or who their consultants were, and the book's printed label key. Both would be in the front matter (preface 序 / key 凡例), scan images 頁面_001–004. Those exist only online: the onefile README points to `https://github.com/miaoski/amis-chinese-poinsot/tree/master/pic` and a Google Drive folder. GitHub is reachable from the container, but the brief says to use local copies, so I did not fetch it. The Amis–French volume's local scans (`_sources/amis-francais/pic/001–353`) start at the dictionary entries (txt/001.txt begins "a / futur : …"), so its front matter is not local either.
- Proposed README addition (do NOT add): "The book prints place labels on a handful of readings: {豐濱} (p.16 l.19), {Tingalaw} (p.426 l.40; the book's own entry Tigalaw reads 花蓮縣豐濱鄉豐富村 - 台東縣東河鄉德高老村, p.556 l.26), {玉里} (p.281) and {光復鄉}. The book's statement of where its material was collected, and its key for {S}/{N}/{F}/{T}/{Z}, would be in the front matter (scan pages 1–4), which has not been checked."

---

### Safolu-Amis-Dictionary
- Dialect label(s) in XML (xml:lang + dialect, with file counts): `xml:lang="ami"` `dialect="Coastal"`: 1 file, `XML/Amis/Safolu/amis_safolu_examples.xml` (49,406 S). The `<TEXT>` attributes give citation "Tsai, Chung-Han (Safolu Kacaw Lalanges). (n.d.). Amis dictionary. Provided to the g0v Amis Moedict project." and source "Safolu/Tsai dictionary, g0v/amis-moedict@e7c6976… docs/s.". No place.
- README statement about place (verbatim + line), `.../fb-main/Corpora/Safolu-Amis-Dictionary/README.md`:
  - line 9: "Amis (`ami`), Coastal provenance."
  - lines 14–17: "`Coastal` is a source-provenance label: it records the author's documented community (Madawdaw, Chenggong) and its language variety, not a dialect classification of each of the 49,000-plus examples. The evidence is in [docs/dialect_evidence.md](docs/dialect_evidence.md)."
  - `.../Corpora/Safolu-Amis-Dictionary/docs/dialect_evidence.md` lines 8–10: "An interview with author Safolu Kacaw (蔡中涵) describes his dictionary work in the Madawdaw community in Chenggong: https://ngiha-mag.com/special-site/tracingrootsrecordoforigins/dialogue/amis-moedict"
  - same file lines 11–16 cite two further web pages (the Council of Indigenous Peoples index placing "Madawdaw (麻荖漏部落, Chenggong Township)" under 海岸阿美語, and aborgpedia). Those pages describe the community, not this dictionary.
  - same file lines 18–21: "The dictionary is large and may contain broader Amis material. `Coastal` therefore records the author's documented community and language variety; it does not claim that dialect membership was inferred independently for all 49,000-plus examples."
- Sources searched:
  - corpus folder: README.md, SOURCE_AUDIT.md, docs/*.md, CodeAndDocs/source_manifest.json, printed_additions.json, data/formosanbank_audit/*. grep for `madawdaw|麻荖漏|chenggong|成功|interview|born|出生|hometown|家鄉` and for `coastal|dialect`.
  - `source_manifest.json`: source, commit, path and counts only; no place.
  - the g0v amis-moedict clone at `/workspace/Formosan-Poinsot/_sources/amis-moedict` (shallow, commit e7c6976a0 = the corpus's pinned commit): README.md and `about.html` (via `git show`). The only thing they say about the author is "蔡中涵阿美語大辭典，由蔡中涵博士 (Safolu Kacaw Lalanges) 提供 g0v 及萌典無償使用。" (about.html). No place.
  - No dev repo for Safolu exists under /workspace, and no local copy of the printed book or of `miaoski/amis-safolu` `dict/*.txt` (searched for `12-M-2.txt` and `*safolu*` / `*蔡中涵*`).
- LOCATION EVIDENCE:
  - "An interview with author Safolu Kacaw (蔡中涵) describes his dictionary work in the Madawdaw community in Chenggong" — `.../Corpora/Safolu-Amis-Dictionary/docs/dialect_evidence.md` lines 8–10
    applies to: the whole corpus (the author's community), and the doc itself says it is not a per-example claim.
    places named (as printed): "Madawdaw community", "Chenggong" (the CIP line in the same file adds "麻荖漏部落, Chenggong Township").
    CAVEAT: this is FormosanBank's own *paraphrase* of an online interview. I could not read the interview (ngiha-mag.com is not reachable), so its wording is unverified.
- Observed vs inferred notes: Observed only that the corpus doc says this. The dictionary text itself (the g0v JSON) contains example sentences with first-person birthplaces (e.g. "我出生在鶴岡部落。", "麒麟部落是我出生的地方。" in `data/formosanbank_audit/Safolu/amis_safolu_examples.metadata.json` lines 29068 and 73728). These are example sentences, not biography, and must not be read as the author's origin.
- Could not find / not knowable locally: the interview text (online only); any preface (序) of the printed dictionary stating where the material was collected or who the contributors were. That would be in the printed book or in `miaoski/amis-safolu` on GitHub, which is not local.
- Proposed README addition (do NOT add): "Once the interview has been checked, quote its own words on where Tsai Chung-Han compiled the dictionary, and cite the printed book's preface if it names the communities the examples come from (not yet checked)."

---

### Virginia_Fey_Dictionary
- Dialect label(s) in XML (xml:lang + dialect, with file counts): `xml:lang="ami"` `dialect="Xiuguluan"`: 1 published file, `XML/Amis/Amis.xml` (2,042 S). A second copy with the same TEXT attributes, `CodeAndDocs/pre_correction_snapshot/Amis/Amis.xml`, is the unpublished baseline. The `<TEXT>` citation is "Fey, V. (1986). Amis dictionary. Taipei: The Bible Society. | miaoski. (2023). miaoski/amis-data …". "Taipei" is the publisher's city, not the data location.
- README statement about place (verbatim + line): `.../fb-main/Corpora/Virginia_Fey_Dictionary/README.md` lines 22–24: "The source is routed to Xiuguluan: the dictionary's introduction (printed page 13) identifies the main text as Central Amis; the FormosanBank registry calls this dialect Xiuguluan." The README names no place.
- Sources searched:
  - corpus folder, all non-XML files: grep for `central|fuyuan|fuli|fengbin|iwan|dialect|introduction|preface|導論|序|方言|富源|富里|豐濱|花蓮|台東|臺東|village|informant|consultant`.
  - `CodeAndDocs/source_decisions.json` (`dialect` block, lines 30–38).
  - `CodeAndDocs/source/upstream/{d,h,i,n,t}.txt`: dictionary letter sections only, beginning at "# p.74" etc., with no preface or introduction. The upstream README has no place.
  - `CodeAndDocs/source/virginia_fey_source.csv` (6,899 lines): every dialect or place tag on a definition.
  - Search for a local copy of the front-matter PDF by name (`*方敏英*`, `*封面序*`, `*用法指引*`, `*fey*.pdf`) under /workspace, /tmp/claude-1000 and /home/vscode: none found. No Fey dev repo under /workspace. The FormosanBank git history for this corpus never contained a PDF.
- LOCATION EVIDENCE:
  - "Fey identifies the main text as Standard Central Dialect, Fuyuan to Fuli and Fengbin to Iwan; dialects.csv maps Central to Xiuguluan." — `.../Corpora/Virginia_Fey_Dictionary/CodeAndDocs/source_decisions.json`, key `dialect.evidence_summary` (line 37). Its evidence fields: `dialect.evidence_url` = `https://new-amis.moedict.tw/files/方敏英阿美語字典-封面序前言導論.pdf` (URL-encoded in the file), `evidence_sha256` = `def0ee9785797aecd090efb02c5b5509af5d96e0ed6624b5cc75f649344b1c84`, `evidence_pdf_page` 14, `evidence_printed_page` 13.
    applies to: "the main text", i.e. the whole dictionary and so the whole corpus.
    places named (as printed in the summary): Fuyuan, Fuli, Fengbin, Iwan (as ranges: "Fuyuan to Fuli", "Fengbin to Iwan").
    CAVEAT: this is a FormosanBank paraphrase ("evidence_summary"), not a quote of Fey. The PDF is online only, so I could not check Fey's own wording, script, or whether she names speakers or villages.
  - Entry-level tags in the dictionary itself (`CodeAndDocs/source/virginia_fey_source.csv`): 28 definition rows carry a dialect or place tag. Counts per tag string: "(花蓮語)" 10; "(南部阿美語)" 5; "(花蓮光復語)" 3; "(Hualien dialect)" 3; "(北部阿美語)" 2; and 1 each of "(花蓮話)", "(花蓮南勢阿美語)", "(海岸)", "(台東)", "(Kwangfu-Hualien dialect)", "(Northern dialect)", "(used in Hualien dialect)", "central dialect", "southern dialect". Two of these rows also carry an example sentence that is in the corpus:
    - csv line 2860: definition "space * crack (Hualien dialect)" / "空間，空隙，破裂 (花蓮語)", example "lala'em a ngiha'" → XML `S2859`
    - csv line 6128: definition "extended family members (south)" / "延伸至涵蓋家庭的成員 (南部阿美語)", example "Maala no tao ko paliding niyam." → XML `S6127`
    applies to: individual senses only; 2 corpus S as listed.
    places named (as printed): 花蓮, 光復 (in 花蓮光復語), 南勢 (in 花蓮南勢阿美語), 台東, "Hualien", "Kwangfu-Hualien".
- Observed vs inferred notes: Observed: the corpus's own decision file paraphrases Fey's introduction as naming "Fuyuan to Fuli and Fengbin to Iwan". The verbatim text is unverified. Treating the two S above (S2859, S6127) as non-central-dialect sentences is INFERRED, from the tag on the sense they illustrate. The dictionary marks some words as Hualien/Kwangfu, southern or northern, which suggests the main text is not one village's speech. That is also an inference.
- Could not find / not knowable locally: Fey's verbatim introduction (printed p. 13 / PDF p. 14 of 方敏英阿美語字典-封面序前言導論.pdf). It is online only, at new-amis.moedict.tw, which is unreachable from the container. Any named consultants or villages would be there too.
- Proposed README addition (do NOT add): "Fey's introduction (printed p. 13; PDF p. 14 of the front-matter PDF, sha256 def0ee97…) is summarized in source_decisions.json as naming the standard Central dialect from Fuyuan to Fuli and from Fengbin to Iwan. Quote her exact words here once the PDF has been checked."

---

### Glosbe (dialect-labelled files only: trv Truku, xsy Saisiyat)
- Dialect label(s) in XML (xml:lang + dialect, with file counts):
  - `trv` + `Truku`: 1 published file, `XML/Truku/Glosbe_trv_eng_lexical.xml` (111 S), plus 1 unpublished baseline copy in `CodeAndDocs/pre_correction_snapshot/trv/`.
  - `xsy` + `Saisiyat`: 2 published files, `XML/Saisiyat/Glosbe_xsy_eng_lexical.xml` (486 S) and `Glosbe_xsy_eng_tmem.xml` (5 S), plus 2 baseline copies in `CodeAndDocs/pre_correction_snapshot/xsy/`.
  - `<TEXT>` attributes: citation "Glosbe Taroko-English dictionary and translation memory. Retrieved 2026-06-29, from https://glosbe.com/trv/en"; source "Glosbe pair trv/en; lexical dictionary/headword entries from public static pages and iapi3 responses; crawl date 2026-06-29." The xsy files are the same apart from the pair (xsy/en) and the tmem crawl date (2026-05-14). No place. No S has any `notes`.
- README statement about place (verbatim + line): `.../fb-main/Corpora/Glosbe/README.md` lines 21–23: "The source does not record the dialect of the Amis or Atayal material, and the files carry `dialect="unknown"`. Glosbe entries generally do not identify a dialect, and a single file likely mixes dialects". Nothing about where the trv or xsy entries came from. "README: none" as to place.
- Sources searched:
  - README.md: grep for `dialect|truku|taroko|saisiyat|source|provenance|collected|village|部落|鄉|ILRDF|…`.
  - `CodeAndDocs/source_records.jsonl`: 7,832 records. Every record has exactly the fields `file, sid, record, kind, source_key, source, target, url, locator, sha256, asterisks` (trv 143 records, xsy 520).
  - `CodeAndDocs/scripts/config.yaml` (lines 79–87: `xsy: name: "Saisiyat"`, `trv: name: "Taroko"`).
  - `CodeAndDocs/data/processed/ildrf_glosbe_lexical_audit_report.md`; the XML `notes`.
  - Searched /workspace and /tmp/claude-1000 for the raw crawl HTML directories (`trv_en`, `xsy_en`, `*glosbe*`): not present. There is no Glosbe dev repo locally.
- LOCATION EVIDENCE: none. The crawl records no place, community or contributor for any trv or xsy entry. What it records per entry is: the Glosbe URL (e.g. `"url": "https://glosbe.com/trv/en/abarao"`), a locator into raw HTML that is not committed (`"locator": "data/raw/html/static/trv_en/abarao.html#839806057784672286"`), and that HTML's sha256.
  - The labels come from Glosbe's language pages, not from any place. Glosbe names the trv page "Taroko" (config.yaml line 86; TEXT citation "Glosbe Taroko-English"); xsy is "Saisiyat" (config.yaml line 80). `dialect="Saisiyat"` is the language name used as a dialect value, not a sub-dialect.
    applies to: the trv and xsy files as wholes.
    places named: none.
- Observed vs inferred notes: Observed: no provenance field exists in the frozen crawl. The ILRDF audit report compares Glosbe head words with an ILRDF-derived dictionary, and says of itself that it "does not treat a match as independent corroboration" (report line 13). So overlap with ILRDF is not evidence of where an entry came from. The first trv record is `"source": "Kari Seediq", "target": "Seediq"` (a head word on the Glosbe Taroko page). I note it only as content.
- Could not find / not knowable locally: Glosbe's per-entry source attributions (Glosbe pages usually show which translation memory or dictionary an item came from). These would be in the raw HTML (`data/raw/html/static/{trv_en,xsy_en}/…`, in the private dev repo, not local) or on glosbe.com (unreachable). Place of collection is almost certainly not recorded by Glosbe at all; that is INFERRED from the nature of the site, not checked.
- Proposed README addition (do NOT add): "Glosbe records no place of collection or dialect for its Truku (Glosbe 'Taroko') and Saisiyat entries; `dialect` here is the language label of Glosbe's page, not a location."

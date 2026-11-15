# Where was the data collected? Group B (Paiwan): six corpora

Read-only research. Everything FormosanBank-side was read from the worktree at current `main`,
`/tmp/claude-1000/-workspace-FormosanBank/e78edf4a-c5b9-400e-864e-ff685648c37f/scratchpad/fb-main`
(HEAD `2a345f0d9 Merge pull request #317 ...`). Below, `<FB>` = that path.
No comparison against the 110年 dialect list is made here (the coordinating session does that).

Short answer per corpus:

| Corpus | Place information found? |
| --- | --- |
| FormosanBankGitBook | NOT FOUND: nothing in README, XML, ledgers, PDF, contributors.tsv or git history says where the translator or the dialect is from |
| HundredPaiwanStories | FOUND for 94 of 100 texts: each title in the source names the narrator's village (or the dialect). Full table below |
| NTU_Paiwan_ASR | NOT FOUND: no committed home-village metadata for any of the 16 pseudonymous speakers; the private speaker key is not available; some untranscribed-language self-introductions contain words that may be place names (leads only, untranslated) |
| Paiwan_Stories | NOT FOUND: the two book colophons and the Word file name the author but no village; only the publisher's address (新北市汐止區) |
| Whitehorn_Collection (2 Southern files) | FOUND: "Place of recording: Pingtung, Taiwan" on both accession forms; performer Rapi; place of birth left blank |
| YeddaPalemeqBlog | FOUND: the author says she grew up in "spungudan", which she glosses "Damei Village Mudan Township Pingtung Taiwan", and calls her own dialect "sinvaudjan Paiwan", glossed "Mudan Township in Pingtung County" |

---

### FormosanBankGitBook
- Dialect label(s) in XML (xml:lang + dialect, with file counts): `pwn` + `Eastern`: 6 files (`<FB>/Corpora/FormosanBankGitBook/XML/Paiwan/{Welcome,FormosanBank,Formosan_Languages,Contributors,Terms_of_Use,Contributing_to_FormosanBank}.xml`). No other labels.
- README statement about place (verbatim + line), or "README: none": README: none about place. The only dialect statement is `<FB>/Corpora/FormosanBankGitBook/README.md` lines 9-11: "Paiwan (ISO 639-3 `pwn`), Eastern dialect. All six files in `XML/Paiwan/` declare `xml:lang="pwn"` and `dialect="Eastern"` on `<TEXT>`. The source was supplied by Xuan; Eastern Paiwan was confirmed on 2025-02-24." (No place, and no record of who confirmed it or on what basis.)
- Sources searched:
  - `<FB>/Corpora/FormosanBankGitBook/README.md` (all 327 lines; grep for 村|鄉|部落|社|縣|市|village|community|Taitung|Pingtung|臺東|台東|屏東|方言|dialect|Xuan|阮).
  - `<FB>/Corpora/FormosanBankGitBook/CodeAndDocs/contributors.tsv` (2 lines, read in full): `Xuan Ruan  Ruan  Xuan  X.  2025-02-11  Eastern Paiwan translation of the 2025 manual (raw_data/Paiwan); permission recorded 2025-02-11`. No place.
  - `<FB>/Corpora/FormosanBankGitBook/CodeAndDocs/source_sections.tsv` (7 lines, read in full; only GitBook URLs and hashes), `source_records.tsv` (106 lines; section/record/S id/PDF page only).
  - The six ledgers `<FB>/Corpora/FormosanBankGitBook/CodeAndDocs/raw_data/Paiwan/*.txt` (same grep; `Contributors.txt` read in full). Place words that occur are about the project, not the translator (e.g. "Indigenous Languages Research and Development Foundation (ILRDF), based in Taipei, Taiwan", `Contributors.txt` line 13).
  - The PDF `<FB>/Corpora/FormosanBankGitBook/CodeAndDocs/raw_data/Paiwan/Website PWN-v1.2.pdf`: text layer of all 9 pages extracted with pdfplumber (every page has a text layer, 2,529-3,501 characters each) and grepped for the same terms. PDF metadata: `Author: 'Xuan'`, `Creator: 'WPS Office 繁體中文專業版'`. No header, footer or colophon naming a place.
  - XML `<TEXT>` attributes (`source="translation of FormosanBank gitbook in Paiwan"`, citation "Ruan, X. (2025). Translations of the FormosanBank documentation v1.") — no place.
  - git history of `Corpora/FormosanBankGitBook` in `<FB>` (commit messages grepped for Eastern|village|dialect|confirm|Xuan). The label `dialect="Eastern"` first appears in commit `98890e51b` (2026-03-16, "Added FormosanBankGitBook corpus.") with no stated basis. No commit records where "2025-02-24" confirmation came from.
  - No dev repo for this corpus exists under `/workspace/Formosan-*`.
- LOCATION EVIDENCE: none.
- Observed vs inferred notes: Observed: the corpus names the translator (Xuan Ruan) and asserts Eastern Paiwan, but no committed file says where the translator is from or which community's speech the translation represents. (Side note, not location evidence: the name "Ruan X." also appears in the Paiwan_Stories citation; I did not use that corpus to infer anything here.)
- Could not find / not knowable locally: the translator's home village/township. It would only be knowable by asking the translator / maintainer (the 2025-02-24 "confirmed" note suggests a conversation that is not committed).
- Proposed README addition (do NOT add): "The source does not record where the translator is from or which community's Eastern Paiwan the translation represents; the Eastern label was confirmed with the translator on 2025-02-24 (basis not recorded)."

---

### HundredPaiwanStories
- Dialect label(s) in XML (xml:lang + dialect, with file counts): all `pwn`. `Southern` 41, `Northern` 32, `Central` 17, `Eastern` 6, `unknown` 4 (total 100, `<FB>/Corpora/HundredPaiwanStories/XML/Paiwan/PaiwanCh2_NNN.xml`). Counts re-computed from the XML and match README lines 10-16.
- README statement about place (verbatim + line), or "README: none": README: none about place. `<FB>/Corpora/HundredPaiwanStories/README.md` lines 18-21: "The dialect values are not in the Word document the corpus is built from; the build takes them from the previously published corpus ..., and writes `unknown` where that record has none." Line 25: "The source does not identify a supported dialect for texts `090`, `091`, `097`, and `099`."
- Sources searched:
  - `<FB>/Corpora/HundredPaiwanStories/README.md` (664 lines; grep for 村|鄉|部落|village|place|storyteller|narrat|told by|dialect|Pingtung|Taitung).
  - The source Word file `<FB>/Corpora/HundredPaiwanStories/CodeAndDocs/Paiwan Ch2.docx` (= Chapter 2 "The texts" of Early & Whitehorn 2003; 14,276 paragraphs): read the introduction paragraphs and every one of the 100 story headings; grepped all paragraphs for village|dialect|Pingtung|Taitung|county|township and for Northern|Southern|Central|Eastern; read the full English translations of texts 079, 089-100; checked headers/footers/footnotes. Also grepped `Paiwan Ch2 Preprocessed.docx` (same results).
  - `<FB>/Corpora/HundredPaiwanStories/CodeAndDocs/data/baseline_text_metadata.tsv` (the `source` and `dialect` columns, 100 rows) and `data/text_metadata_corrections.tsv` (4 rows).
  - The published XML `<TEXT source=... dialect=...>` of all 100 files.
  - git history in `<FB>`: first commit `c2583be562` (2025-11-25, "Adding 100 Paiwan Stories.") including its `CodeAndDocs/script.ipynb` and `CodeAndDocs/README.md`; commit `90094b232` (2026-03-15).
  - Dev repo `/workspace/Formosan-100_Paiwan_Texts` (README, file list): it holds only the same two Word files (`Original/`), no book PDF. No copy of the full book (with Chapter 1) exists anywhere on local disk (searched `/workspace`, `/home/vscode`, `/tmp/claude-1000`).
- LOCATION EVIDENCE:
  - "The title also indicates the village or dialect of the original narrator of the story, a page number reference for the OA stories, and where known, an indication of the dialect of Paiwan used." — `<FB>/Corpora/HundredPaiwanStories/CodeAndDocs/Paiwan Ch2.docx`, `word/document.xml` paragraph 3 (index 2), the introduction directly under the chapter heading "2 The texts" (printed page not available in the .docx)
    applies to: the whole corpus; says what the place in each title means (the narrator's village or dialect)
    places named (as printed): none in this sentence
  - Per-story title lines. Quoted as published in each file's `TEXT/@source` (identical to the second line of each heading in the .docx; the .docx stores ɫ/Ɫ in a legacy font as î/ï, e.g. "Qatsiîay"). Grouped by dialect label (counts verified by script over the 100 XML files):

    | XML `dialect` | Place as printed in the source title | Kind | Files | Text numbers |
    | --- | --- | --- | ---: | --- |
    | Southern | Qatsiɫay village | village | 17 | 001-017 |
    | Southern | Tjakuvukuvuɫ village | village | 17 | 018-034 |
    | Southern | Ɫaleklek village | village | 7 | 035-041 |
    | Central | Kuɫaɫau village | village | 10 | 042-051 |
    | Central | Tjaɫakavus village | village | 2 | 058-059 |
    | Central | Kaviangan village | village | 3 | 060-062 |
    | Central | Makazayazaya dialect | dialect (no village) | 1 | 095 |
    | Central | Kazazaɫan dialect | dialect (no village) | 1 | 098 |
    | Eastern | Patjavaɫ village | village | 3 | 052-054 |
    | Eastern | Tjauvaɫi [or Tjavuaɫi] village | village | 3 | 055-057 |
    | Northern | Kapayuanan village | village | 7 | 063-069 |
    | Northern | Tjukuvuɫ village | village | 5 | 070-074 |
    | Northern | "told by Giɫgiɫaw of Vaɫulu village" | storyteller + village | 14 | 075-088 |
    | Northern | "conversation piece, Vaɫulu dialect" | dialect | 1 | 089 |
    | Northern | "Vaɫulu dialect" (092 adds "(meaning of text obscure in many places)") | dialect | 5 | 092, 093, 094, 096, 100 |
    | unknown | "conversation piece" | none | 1 | 090 |
    | unknown | (no second title line; title "KUⱢEⱢEⱢEⱢE AND PULELELELENGAN") | none | 1 | 091 |
    | unknown | "Dialect not noted" | none | 2 | 097, 099 |

    (Northern total: 7 + 5 + 14 + 1 + 5 = 32. Central: 10 + 2 + 3 + 1 + 1 = 17. Southern: 17 + 17 + 7 = 41. Eastern: 3 + 3 = 6. Unknown: 4.)

    Exact `source` strings, one example per place (all 100 are listed in `<FB>/Corpora/HundredPaiwanStories/CodeAndDocs/data/baseline_text_metadata.tsv`, column `source`, rows 2-101):
    - 001 "ti sa Puɫaɫuyaɫuyan (Qatsiɫay village, p.141)" — `XML/Paiwan/PaiwanCh2_001.xml` line 2
    - 018 "ti Savaɫi (Tjakuvukuvuɫ village, p.190)"
    - 035 "se Tjauvalivali (Ɫaleklek village, p.209)"
    - 042 "ti ḍail kati gagang (Kuɫaɫau village, p.224)"
    - 052 "ti sa Vatjuɫayan (Patjavaɫ village, p.244)"
    - 055 "tjatjiw (Tjauvaɫi [or Tjavuaɫi] village, p.250)"; 057 is printed with a stray parenthesis: "ti Valuliaw (Tjauvaɫi ([or Tjavuaɫi] village, p.254)" (docx heading paragraph index 7270)
    - 058 "Puɫaɫuɫaɫuyan kati Tjukutjuku (Tjaɫakavus village, p.255)"
    - 060 "Quzang kati Tjingangaḍuy (Kaviangan village, p.268)"
    - 063 "se Padain kata se Kapayuanan (Kapayuanan village, p.273)"
    - 070 "Tail kati Piri (Tjukuvuɫ village, p.280)"
    - 075 "told by Giɫgiɫaw of Vaɫulu village" (075-088 identical; 081 adds "(possibly a story originally from Japan)")
    - 089 "conversation piece, Vaɫulu dialect"; 092 "Vaɫulu dialect (meaning of text obscure in many places)"; 093, 094, 096, 100 "Vaɫulu dialect"
    - 095 "Makazayazaya dialect"; 098 "Kazazaɫan dialect"
    - 090 "conversation piece"; 097, 099 "Dialect not noted"; 091 no place line
    applies to: per text, as tabulated (the place is the "original narrator's" village or dialect, per the introduction quote above)
    places named (as printed): Qatsiɫay, Tjakuvukuvuɫ, Ɫaleklek, Kuɫaɫau, Tjaɫakavus, Kaviangan, Patjavaɫ, Tjauvaɫi / Tjavuaɫi, Kapayuanan, Tjukuvuɫ, Vaɫulu (all "village"); Makazayazaya, Kazazaɫan, Vaɫulu ("dialect"). No county or township is named anywhere in the chapter.
  - "When you have left (us) here in Pingtung, how will you be in your concern for us?" — `Paiwan Ch2.docx`, full English translation of text 097 "FAREWELL MESSAGE (1)" (heading paragraph index 13717)
    applies to: text 097 only (one of the four `unknown` texts); it is the speaker's own words, saying the speakers are in Pingtung
    places named (as printed): Pingtung
  - "Thank you very much, teacher Whitehorn, during your time in Taiwan you came to us, you also reached us in Kazazaɫan." — `Paiwan Ch2.docx`, full English translation of text 098 (heading paragraph index 13901)
    applies to: text 098 (consistent with its title "Kazazaɫan dialect")
    places named (as printed): Kazazaɫan
- Observed vs inferred notes:
  - Observed: the source itself never uses the words Northern / Central / Southern / Eastern for any text (grep of all 14,276 paragraphs of both .docx files found only "the Lower Paiwan area" and "the Vutsuɫ area" inside story content). So there is no story whose place contradicts a dialect label *in the source*: the four-way labels are FormosanBank's, not the authors'.
  - Observed: where the labels came from. The first commit `c2583be562` (2025-11-25) built them with this map in `CodeAndDocs/script.ipynb` (`git show c2583be562:Corpora/HundredPaiwanStories/CodeAndDocs/script.ipynb`, lines 64-80): Eastern = "Tjauvałi", "Tjavuałi", "Patjavał"; Southern = "Qatsiłay", "Tjakuvukuvuł", "Łaleklek"; Central = "Kułałau", "Tjałakavus", "Kaviangan"; Northern = "Kapayuanan", "Vałulu", "Tjukuvuł". The script assigns a dialect when one of these strings occurs in the title line. No source for the map is cited.
  - Observed: 095 ("Makazayazaya dialect") and 098 ("Kazazaɫan dialect") are not in that map and had no `dialect` attribute in the first commit. Both became `dialect="Central"` in commit `90094b232` (2026-03-15, message "Update Rau and Dong. Update Hundred Paiwan Stories. Create new standard comparisons for QC."), which gives no reason. These two Central labels therefore have no recorded basis.
  - Observed: "Tjukuvuɫ" (Northern, 070-074) and "Tjakuvukuvuɫ" (Southern, 018-034) are different names in the source; easy to conflate when comparing.
  - Observed: 079 "MY LIFE" (told by Giɫgiɫaw of Vaɫulu village) says "When I arrived in Makazayazaya I went straight round to the police station ..." — this is where he went to preach, not his home; it does not change the village attribution.
  - Inferred / GENERAL KNOWLEDGE, NOT FROM THE SOURCE: "OA" (the source of the page numbers "p.141" etc. for texts 001-074) is presumably Ogawa & Asai (1935); Chapter 2 never expands the abbreviation (79 mentions of "OA", e.g. "[kiɫavaranan: originally kiɫavaran in OA]"), so for 001-074 the named village is that of the narrator in that earlier collection, not necessarily anyone Early & Whitehorn recorded.
- Could not find / not knowable locally: (1) Chapter 1 of the book, which "described" the corpus ("described in the previous chapter") and presumably expands "OA" and may explain the villages/dialects — only in the full book PDF at the ANU repository (README line 36; online only). (2) Any place for 090, 091, 097 (beyond "here in Pingtung" in its content), 099. (3) Modern Chinese names / townships for the romanized villages — the source gives none.
- Proposed README addition (do NOT add): "Each text's title in the source names the village or dialect of its original narrator (Early & Whitehorn 2003, Chapter 2 introduction): Southern texts come from Qatsiɫay (001-017), Tjakuvukuvuɫ (018-034) and Ɫaleklek (035-041) villages; Central from Kuɫaɫau (042-051), Tjaɫakavus (058-059) and Kaviangan (060-062) villages plus one text each in the Makazayazaya (095) and Kazazaɫan (098) dialects; Eastern from Patjavaɫ (052-054) and Tjauvaɫi [or Tjavuaɫi] (055-057) villages; Northern from Kapayuanan (063-069) and Tjukuvuɫ (070-074) villages and Vaɫulu village/dialect (075-089, 092-094, 096, 100). The four-way dialect labels themselves are FormosanBank's grouping of these villages, not the authors'."

---

### NTU_Paiwan_ASR
- Dialect label(s) in XML (xml:lang + dialect, with file counts): all `pwn`. `Northern` 115 (Calina 9, Edran 7, Kerris 11, Maron 16, Nira 31, Zendar 41); `Eastern` 98 (Falin 9, Halmir 14, Ilvane 12, Loris 27, Sarnix 14, Tavora 22); `Southern` 31 (Doriel 8, Orsen 23); `Central` 16 (Belmira 8, Garven 8). Folder counts computed from `<FB>/Corpora/NTU_Paiwan_ASR/XML/Paiwan/<Speaker>/`; each speaker's files all carry one dialect. Totals match README lines 14-19.
- README statement about place (verbatim + line), or "README: none": README: none. `<FB>/Corpora/NTU_Paiwan_ASR/README.md` lines 3-6 name only the institution: "Paiwan (`pwn`) speech data collected by [Professor Li-May Sung](...) at National Taiwan University ...". Lines 25-28: "For Year 1 the dialect was set by `CodeAndDocs/add_dialect.py`, which takes the value as a command-line flag, so the published scripts do not record which value was passed for which speaker. For Year 2 and the spontaneous speech the dialect comes from the private `speaker_key.csv`".
- Sources searched:
  - `<FB>/Corpora/NTU_Paiwan_ASR/README.md` (304 lines; grep village|村|鄉|部落|place|location|home|from|speaker|dialect|region|county|縣).
  - `<FB>/Corpora/NTU_Paiwan_ASR/CodeAndDocs/non_sp_data.json` (whole file; keys per pseudonym: `record_count`, `enteries` → `wave`, `eaf`, `TextGrid`, `Topic` only). No location key. No real names in it.
  - `<FB>/Corpora/NTU_Paiwan_ASR/CodeAndDocs/*.py` (grep). `build_y2_and_spontaneous.py` lines 56-58 read only three columns of the private key: `row["filename_regex"]`, `row["pseudonym"]`, `row["dialect"]`.
  - XML `<TEXT>` attributes of every speaker folder (`source="NTU Paiwan Data, Participant <Pseudonym>, file <file>"`, citation, audio) — no place.
  - git history (`28006eefa` 2026-06-12 message: speaker key "kept only in the private dev repo"). No NTU dev repo exists under `/workspace`.
  - Original-tier FORM text of the spontaneous-speech files whose topic suggests personal background (self-introductions, "my life", "my father/mother/parents", "when I was eight/7", place-name topics), with lines containing `ngadan` ("name") or the personal article `ti` filtered out so as not to read real names.
- LOCATION EVIDENCE: none (no committed statement of any speaker's home village, recording location, or region).
- Observed vs inferred notes:
  - Observed: Year-1 file names carry codes such as `02SE105`, `02JN105`, `02SC105`, `02EN106`, `02JE105`, `02SN105`; their meaning is not documented anywhere in the corpus (I did not use them).
  - Observed, but untranslated (the corpus has no translations). Leads only — the reading of these words as place names is mine (GENERAL KNOWLEDGE, NOT FROM THE SOURCE: Paiwan `qinaljan` = village, `se X` = person of X, `kemasi` = from). Quoted verbatim from `FORM kindOf="original"`:
    - Tavora (Eastern), `XML/Paiwan/Tavora/self-introduction_Tavora.xml` S `a10`: "sa a niaken a qinaljan imaza i singding aicu a i singding a mavan a izua anan a dripung ta zua e pinisetjavat imaza i lizuk." and S `a20`: "... a na izua sema maza i imaza i lizuk i singding."
    - Ilvane (Eastern), `XML/Paiwan/Ilvane/self_introduction_Ilvane.xml` S `a2`: "se tjavukel aken kemasi kanalun." Ilvane also has a recording titled (file name) `the_placename_of_tjavuqel_Ilvane.xml`.
    - Kerris (Northern), `XML/Paiwan/Kerris/self_introduction_Kerris.xml` S `a1`: "nana i tjulivar imaza i i tua i ka piuman." and S `a5`: "sa kitevelj anga tua se piuma." (context unclear; may be about an ancestor).
    - Falin (Eastern), `XML/Paiwan/Falin/my_life_Falin.xml` S `a12`: "imaza ni e imazi aken i i i izua i i lizuk"
    - Zendar (Northern), `XML/Paiwan/Zendar/my_life_Zendar.xml` S `a16`: "au, ay a nia kinazuanan angata, imaza i timung"
    - Maron (Northern): recordings titled `the_migration_history_of_tjavuqel_Maron.xml` and `past_interactions_with_Kasavakan_Maron.xml` (titles only; topic, not a stated home).
    - No such lead for Belmira, Calina (one line "na pucikelj aken a pasa ma gaku i izuci." in `self_introduction_Calina.xml` S `a19`, place unclear), Doriel, Edran, Garven, Halmir, Loris, Nira, Orsen, Sarnix.
    Only a one-minute window of each spontaneous recording is transcribed, so a self-introduction may omit the village.
- Could not find / not knowable locally: speakers' home villages. They would be in the private speaker key / NTU field records (private dev repo, not on this machine) or by asking Prof. Sung's team; also possibly in the untranscribed audio (Hugging Face; not reachable from this container). Translating the leads above needs a Paiwan speaker.
- Proposed README addition (do NOT add): "The public corpus does not record where each speaker is from; speaker home communities are held only in the private speaker records."

---

### Paiwan_Stories
- Dialect label(s) in XML (xml:lang + dialect, with file counts): `pwn` + `Eastern`: 3 files (`<FB>/Corpora/Paiwan_Stories/XML/Paiwan/DingDing.xml`, `kavatjes_ni_vuvu.xml`, `maljialjian_a_qaciljay.xml`).
- README statement about place (verbatim + line), or "README: none": README: none. `<FB>/Corpora/Paiwan_Stories/README.md` line 9: "Paiwan (ISO 639-3 `pwn`), Eastern dialect." Line 24: "Gesi Giling (2020), *Dingding* and *Kavatjes ni vuvu*, illustrated by Tjaiwan Giling. Both PDF colophons date the first printing to November 2020." Line 62: "**Rights source:** Gesi Giling (阮翠芳), 2024-04-13".
- Sources searched:
  - `<FB>/Corpora/Paiwan_Stories/README.md` (204 lines; grep village|村|鄉|部落|place|台東|臺東|屏東|east|dialect|colophon|author).
  - `<FB>/Corpora/Paiwan_Stories/CodeAndDocs/data/texts.tsv` (4 lines, full), `data/source_manifest.json` (full; file names, hashes, durations only), `data/source_exclusions.tsv` (full).
  - XML `<TEXT>` attributes of all 3 files (source = "Gesi Giling (text) and Tjaiwan Giling (illustrations) (2020), Dingding. ..." etc.; no place).
  - The original sources, which are no longer in the tree but are in `<FB>` git history at commit `b57b718f4` (2024-12-14, "add paiwan stories original"); read in memory with `git show` piped to Python (nothing written): `Corpora/Paiwan_Stories/CodeAndDocs/Original/dingding蝸牛.pdf` (32 pp.), `.../kavatjes ni vuvu奶奶的寶物.pdf` (32 pp.), `.../maljialjian a qaciljay(black stone).doc`. PDF text layer extracted for all pages and grepped for 村|鄉|鎮|部落|縣|市|臺東|台東|屏東|台北|臺北|qinaljan|kakudan|Taitung|Pingtung|village; colophon (PDF p. 32) read in full; the .doc's UTF-16 text runs read in full.
  - git history: `dialect="Eastern"` is present from the first commit of the XML, `abaccc649` (2024-12-13), with no stated basis.
- LOCATION EVIDENCE (no place of collection or author's home found; the only places in the sources are these):
  - "族語文字 gesi giling 阮翠芳" / "文字協力 buka lja ladan 謝清治" / "出版發行 百通科技股份有限公司" / "出版地址 新北市汐止區大同路二段171 號" — colophon, `git show b57b718f4:"Corpora/Paiwan_Stories/CodeAndDocs/Original/dingding蝸牛.pdf"`, PDF p. 32 (printed page number not in the text layer); the same lines on PDF p. 32 of the kavatjes PDF
    applies to: Dingding and Kavatjes ni vuvu; the address is the publisher's (Beltom Co., Ltd.), not where the text was written or where the author is from
    places named (as printed): 新北市汐止區 (publisher address only)
  - "部落裡的人都很喜歡吃這一道菜。" — Dingding PDF p. 32 (Chinese story text); "有一年部落正舉辦五年祭，" — Maljialjian .doc; "想念時就會打電話給在台北工作的我。" — Kavatjes PDF p. 32
    applies to: story content only; the 部落 is never named; 台北 is where the narrator-character works
    places named (as printed): 台北 (story content)
- Observed vs inferred notes: Observed: the sources name the Indigenous-text author (gesi giling 阮翠芳) and text-correction contributor (buka lja ladan 謝清治) but no village, township or county. Not done: the odd PDF pages (3-31) have no text layer; the corpus's own `source_exclusions.tsv` says they are "illustration-only pages"; I did not render them, because the PDFs exist only as git blobs and rendering would mean writing them out.
- Could not find / not knowable locally: the author's home community / where the Eastern Paiwan in these books comes from. Would need the author or the maintainer (permission was "recorded directly"; evidence "ask maintainer", README line 62). Possibly on the publisher's website (online only).
- Proposed README addition (do NOT add): "The sources do not say where the author is from or where the texts were written; the colophons give only the publisher's address (新北市汐止區)."

---

### Whitehorn_Collection (Southern-labelled Paiwan files only)
- Dialect label(s) in XML (xml:lang + dialect, with file counts): in scope: `pwn` + `Southern`: 2 files, `<FB>/Corpora/Whitehorn_Collection/XML/Paiwan/Whitehorn_Paiwan_01A_4.xml` and `.../Whitehorn_Paiwan_02A_2.xml`. (Rest of the corpus, out of scope: `pwn`+`unknown` 80, `tay`+`unknown` 3, `ami`+`unknown` 1, `trv`+`unknown` 1.)
- README statement about place (verbatim + line), or "README: none": README: none about place. `<FB>/Corpora/Whitehorn_Collection/README.md` line 80: "Only two recordings state a dialect FormosanBank recognises, and both are Southern Paiwan."
- Sources searched: README (154 lines); the two XML files in full; the two matching accession forms `<FB>/Corpora/Whitehorn_Collection/CodeAndDocs/Whitehorn_Paiwan_01A_04/Whitehorn_Paiwan_01A_04.pdf` and `.../Whitehorn_Paiwan_02A_02/Whitehorn_Paiwan_02A_02.pdf` (one page each, scanned, no text layer: rendered with pypdfium2 and read as images; PDF annotations extracted: "Track 04 / Total length 1:47" and "Track 02 / Total length 06:39"); the `source` attribute of the other 15 records from the same 1954 tapes (`Whitehorn_Paiwan_01A_*`, `02A_*`) grepped for "Rapi".
- LOCATION EVIDENCE:
  - "Recorded summer of 1954 in Pingtung Taiwan." — `<FB>/Corpora/Whitehorn_Collection/XML/Paiwan/Whitehorn_Paiwan_01A_4.xml` line 2 (`TEXT/@source`), full description: "A farewell address to John Whitehorn made by Rapi a 26 year old female. Recorded summer of 1954 in Pingtung Taiwan."
    applies to: Whitehorn_Paiwan_01A_4.xml
    places named (as printed): Pingtung, Taiwan
  - "Recorded summer of 1954 in Pingtung Taiwan." — `<FB>/Corpora/Whitehorn_Collection/XML/Paiwan/Whitehorn_Paiwan_02A_2.xml` line 2 (`TEXT/@source`), full description: "Lists of Paiwan words, chosen to illustrate the pronunciation of letters, diphthongs etc. The recording is of Rapi, a female speaking in a Paiwan. Recorded summer of 1954 in Pingtung Taiwan."
    applies to: Whitehorn_Paiwan_02A_2.xml
    places named (as printed): Pingtung, Taiwan
  - Handwritten accession form, tape "[A] Paiwan Material, 1954", side 1, track 6.25-8.05: "Place of recording: Pingtung, Taiwan"; "Name(s), age, sex, place of birth of performer(s): Rapi, c.26, Female," (place of birth left blank); "Language of recording: Paiwan (southern dialect)" — `Whitehorn_Paiwan_01A_04.pdf`, PDF p. 1 (single page, no printed page number)
    applies to: Whitehorn_Paiwan_01A_4.xml (speaker Rapi)
    places named (as printed): Pingtung, Taiwan
  - Handwritten accession form, tape "[B] Paiwan Material, 1954", side 1, track 21.19-27.40: "Place of recording: Pingtung, Taiwan"; "Name(s), age, sex, place of birth of performer(s): Rapi  Female" (no age, no place of birth); "Language of recording: Paiwan (south)" — `Whitehorn_Paiwan_02A_02.pdf`, PDF p. 1 (single page, no printed page number)
    applies to: Whitehorn_Paiwan_02A_2.xml (speaker Rapi)
    places named (as printed): Pingtung, Taiwan
- Observed vs inferred notes: Observed: both Southern files are the same performer (Rapi), recorded in "Pingtung" (county level only; no township or village). The Southern label comes from Whitehorn's own "southern dialect" / "south". Out of scope but noticed in the same tape set (dialect `unknown` files, so they won't enter the comparison): `Whitehorn_Paiwan_01A_1.xml` and `01A_6.xml` say "Pari, a 26 year old male from Valoro village".
- Could not find / not knowable locally: Rapi's village or township; the forms leave place of birth blank. The Cambridge repository record pages are online only (not fetched).
- Proposed README addition (do NOT add): "The two Southern Paiwan recordings are both of one speaker, Rapi (female, c. 26), recorded in summer 1954 in Pingtung, Taiwan; Whitehorn's accession forms give the language as 'Paiwan (southern dialect)' / 'Paiwan (south)' and leave her place of birth blank (CodeAndDocs/Whitehorn_Paiwan_01A_04, 02A_02)."

---

### YeddaPalemeqBlog
- Dialect label(s) in XML (xml:lang + dialect, with file counts): `pwn` + `Southern`: 1 published file, `<FB>/Corpora/YeddaPalemeqBlog/XML/Paiwan/Paiwan_Yedda_Blog.xml` (671 `S`). The task said 2 files: the second `pwn`/`Southern` file is the frozen scrape `<FB>/Corpora/YeddaPalemeqBlog/CodeAndDocs/data/source_snapshot/Paiwan_Yedda_Blog.xml` (668 `S`), a build input under CodeAndDocs, not published data.
- README statement about place (verbatim + line), or "README: none": README: none about place. `<FB>/Corpora/YeddaPalemeqBlog/README.md` line 26: "Yedda Palemeq, a Paiwan speaker and linguist, maintained a [blog](https://yeddapalemeq.blogspot.com/) with short Southern Paiwan examples ..."
- Sources searched: README (540 lines) and all CodeAndDocs `.md/.py/.json/.tsv` (grep village|村|鄉|部落|county|縣|township|Pingtung|屏東|Taitung|Mudan|牡丹|hometown|tribe|dialect|...); the published XML: every sentence- and word-level `TRANSL` and `notes` scanned by script for village|tribe|our dialect|my dialect|Pingtung|Taitung|hometown|south|north|county|dialect, then the hits read in context. The frozen snapshot also contains the same `spungudan`/`sinvaudjan` passages (18 matching lines). `/workspace/wt-b3-yedda` checked: it is NOT a dev checkout but a FormosanBank worktree on branch `work/b3-yedda` (git common dir `/workspace/FormosanBank/.git`); its YeddaPalemeqBlog folder holds an older version of the same corpus files (scripts, `raw_xml/`, `manual_edits.*`) and no blog "about" page or HTML; per the brief's main-only rule I compared file names only and did not read its contents.
- LOCATION EVIDENCE (all from the author's own blog text as published in the XML; blog URL = the `S/@source`):
  - FORM "kakedrian anan a'en, nakemaizuanan a'en i spungudan." / TRANSL "When I was a child, I lived in spungudan." / word gloss of `spungudan`: "Damei Village Mudan Township Pingtung Taiwan, a very small Paiwan village of around 50-80 households." — `Paiwan_Yedda_Blog.xml` S `S346_1`, lines 44094, 44098, 44145; post https://yeddapalemeq.blogspot.com/2021/02/paiwan-every-day-346-anan.html
    applies to: the author (the single speaker/writer of the whole corpus)
    places named (as printed): spungudan = "Damei Village", "Mudan Township", "Pingtung", "Taiwan"
  - FORM "... i pungudan a ku umaq. kivalavalaanga a sema tua ku qinaljan." / TRANSL "... My home is in pungudan. Welcome to my village." — S `S13_1`, lines 79909, 79913; post https://yeddapalemeq.blogspot.com/2020/03/paiwan-every-day-13.html (the word `pungudan`, W `S13_1W29`, has no gloss)
    applies to: the author
    places named (as printed): pungudan
  - FORM "matjaunem a qinaljan imaza i tua nia kinaguan a sinvaudjan." / TRANSL "There are six villages here in our township sinvaudjan." / word gloss of `sinvaudjan`: "Mudan Township in Pingtung County" — S `S195_1`, lines 64363, 64367, 64496; post https://yeddapalemeq.blogspot.com/2020/09/paiwan-every-day-195-qinaljan.html
    applies to: the author ("our township")
    places named (as printed): sinvaudjan = "Mudan Township in Pingtung County"
  - Word gloss: "how much, for value or price. The root iskuda'what'. In my dialect sinvaudjan Paiwan, we use 'pida'." and "clothes. We useitungin southern Paiwan." — S `S462_1`, lines 26908, 27003
    applies to: the author's own dialect, named by her as "sinvaudjan Paiwan" and placed in "southern Paiwan"
    places named (as printed): sinvaudjan
  - Word gloss: "... In my dialect (sinvudjan), we sound more likepulingaworpulingalingaw." — S `S217_1`, line 62098 (spelled "sinvudjan" here)
    applies to: the author's dialect
    places named (as printed): sinvudjan
  - Further "sinvaudjan Paiwan" glosses: S `S551552553_1` line 13808 ("Usually in sinvaudjan Paiwan,haiyarefers to taxi or cab"), S `S464_1` line 26733 ("uma'is also heard in sinvaudjan paiwan."), S `S122_1` line 69288 ("land, earth, weather (in sinvaudjan paiwan)"), S `S113_1` line 69715 ("... is used in Sinvaudjan Paiwan.")
    applies to: the author's dialect
    places named (as printed): sinvaudjan
  - "In southern Paiwan, we saysanguaqmore often." — S `S377_1` line 40611; "I was looking for throat, it istjigerawordriaqulanin southern Paiwan. But in norther Paiwan,liquis used to also mean throat." — S `S451_1` line 28468
    applies to: the author identifies her usage with southern Paiwan
    places named (as printed): none (dialect area only)
  - TRANSL "We Paiwan live in the south of Taiwan." — S `S88_1` line 71097 (general statement, not her village)
- Observed vs inferred notes: Observed: the author places her childhood home in spungudan (her gloss: Damei Village, Mudan Township, Pingtung) and her dialect in sinvaudjan (her gloss: Mudan Township, Pingtung County). Inferred (mine): that "pungudan" (S13_1, her current "home") is the same place as "spungudan" (S346_1) — the spellings differ by the initial s- and S13_1's word has no gloss. Note also that S13_1 contains the names of her parents (published blog content; not reproduced here beyond what is quoted in the TRANSL above).
- Could not find / not knowable locally: the blog's "About" / profile page (online only, not in the frozen snapshot); any statement that every example is from Damei rather than her general Mudan usage.
- Proposed README addition (do NOT add): "The author writes that she grew up in spungudan, which she glosses 'Damei Village Mudan Township Pingtung Taiwan' (S346_1; see also S13_1), and calls her dialect 'sinvaudjan Paiwan', glossing sinvaudjan as 'Mudan Township in Pingtung County' (S195_1, S462_1)."

---

## Process note (deviation to report)

The brief says the output file is the only file I may write. I also wrote, outside any repository, into
`/tmp/claude-1000/-workspace-FormosanBank/e78edf4a-c5b9-400e-864e-ff685648c37f/scratchpad/locB_tmp/`:
`hps_titles.txt` (a list of the 100 story headings extracted from the .docx; this one was not sanctioned) and
`Whitehorn_Paiwan_01A_04.png`, `Whitehorn_Paiwan_02A_02.png` (renders of the two scanned accession forms, which the
brief's rule 4 asks for; the Read tool could not render PDFs because `pdftoppm` is not installed). Nothing was
written inside any repo; no git write commands were run. These three files can be deleted.

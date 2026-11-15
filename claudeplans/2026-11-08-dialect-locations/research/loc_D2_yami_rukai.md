# Where the data was collected: RauDong, WakelinTexts, Huteson-Rukai-Survey (read-only research)

Worktree read: `/tmp/claude-1000/-workspace-FormosanBank/e78edf4a-c5b9-400e-864e-ff685648c37f/scratchpad/fb-main`
(HEAD `2a345f0d9 Merge pull request #317 from FormosanBank/feature/proofreading-page-images`). Below, `<W>` stands
for that path; every path written with `<W>` is that absolute path plus the rest.

Nothing was edited anywhere. This file is the only file I wrote (see the note at the end about two output files the
tool harness created on its own).

---

### RauDong
- Dialect label(s) in XML (xml:lang + dialect, with file counts): `xml:lang="tao"` + `dialect="Yami"` in all 40 files:
  20 published (`<W>/Corpora/RauDong/XML/Yami/*.xml`) and 20 frozen copies (`<W>/Corpora/RauDong/CodeAndDocs/pre_correction_snapshot/XML/Yami/*.xml`).
  - **Files vs. texts:** there is one file per text. The 40 files are the 20 texts twice: the published `XML/Yami/` set
    plus the snapshot set the build starts from (README lines 200-203: "`CodeAndDocs/generate_xml.sh` starts from a
    frozen snapshot of the XML as it was published (`CodeAndDocs/pre_correction_snapshot/`)"). Same 20 file names in
    both folders, and I checked that `TEXT/@source` is identical in all 20 pairs (script output: "files whose
    TEXT/@source differs pub vs snapshot: []").
  - **The README says 20 texts, not 18.** Line 3: "contains 20 morphologically parsed and glossed texts"; line 8:
    "All 20 files carry `xml:lang="tao"`"; line 17: "The 20 glossed Yami (Tao, `tao`) narrative texts". Lines 11-13
    split them 8 + 12 = 20 (texts 1–6, 14 and 16 = 8; "the other twelve" = 12). I found no "18" in the README.
- README statement about place (verbatim + line): `<W>/Corpora/RauDong/README.md` lines 11-13:
  "Each file's `TEXT/@source` names the storyteller and village as the source prints them: Yayo (椰油村) for texts
  1–6, 14 and 16, Iranmilek (東清村) for the other twelve. The corpus does not treat these villages as separate
  dialects."
  **VERIFIED against all 20 published files and all 20 snapshot files: correct.** Tally from the files:
  Yayo / 椰油村 = 8 texts (1, 2, 3, 4, 5, 6, 14, 16), 384 sentences; Iranmilek / 東清村 = 12 texts (7, 8, 9, 10, 11,
  12, 13, 15, 17, 18, 19, 20), 410 sentences; 794 in all, which is the README's own count (line 22).
- Sources searched:
  - `TEXT` attributes (`source`, `citation`, `BibTeX_citation`, `id`, `copyright`, `dialect`) of all 40 XML files,
    parsed with ElementTree. `citation`/`BibTeX_citation` name only the book (no place). No `notes=` attribute exists
    in any published file (grep count 0 in all 20).
  - `<W>/Corpora/RauDong/README.md` (read in full).
  - `<W>/Corpora/RauDong/CodeAndDocs/*` grep for `yayo|iranmilek|椰油|東清|village|蘭嶼|orchid`: only hit is a word
    list (`orthographic_info` line 59 contains the Yami word `jiranmilek`), not a statement of provenance.
  - Original delivery (git read, `git show 0d0df4710:...`): the delivered XML carries the same `source` string (e.g.
    text 1: `'si Tonosen (M, 53, Yayo)', '賴金龍，男，53，椰油村'`); the delivered `CodeAndDocs/README.md` has no
    place statement (grep for yayo/iranmilek/椰油/東清/village/orchid/蘭嶼/speaker/storytell/consult/record/collect:
    no hits about place).
  - Dev checkout `/workspace/wt-b4-raudong` (branch `work/b4-raudong`, HEAD `b3c8dd48e`): it is an older FormosanBank
    worktree, not a separate dev repo; `Corpora/RauDong/CodeAndDocs/` there holds only the PNGs, `make_xml.sh`,
    `orthographic_info`, `unique_characters.txt` and the snapshot. Nothing new about place.
  - Searched `/workspace` and `/home/vscode` for a copy of the Rau & Dong (2006) book (`find -iname '*rau*dong*'`,
    `'*yami*text*'`, `'*yami*grammar*'`, and all PDFs with yami/tao/rau/dong in the path): **no copy found**.
- LOCATION EVIDENCE (one bullet per speaker; every quote is `TEXT/@source` at **line 2** of the named file in
  `<W>/Corpora/RauDong/XML/Yami/`, and identically at line 2 of the snapshot copy):
  - "'si Tonosen (M, 53, Yayo)', '賴金龍，男，53，椰油村'" — `1. niomahas a longtsang si Kaojinzhong.xml` line 2
    and "'si Tonasen (M, 52, Yayo)', '賴金龍，男，52，椰油村'" — `16. kavavatanen no kotat.xml` line 2
    applies to: texts 1 and 16 (43 + 133 = 176 sentences), storyteller 賴金龍
    places named (as printed): Yayo / 椰油村
  - "'si apen Kotan/Jinovoy (M, 75, Yayo)', '王仁德，男，75，椰油村'" — files `2. mapakazakazakat a yalalaw so sinsi.xml`,
    `3. aney o ango ko.xml`, `4. man’acing so kois.xml`, `5. miarap.xml`, `6. teymangangasien ko ya.xml`, line 2 each
    applies to: texts 2, 3, 4, 5, 6 (160 sentences), storyteller 王仁德
    places named (as printed): Yayo / 椰油村
  - "'si apen Ngalaod (F, 58, Yayo)', '王秋閱，女，58，椰油村'" — `14. makarakep so panganpen.xml` line 2
    applies to: text 14 (48 sentences), storyteller 王秋閱
    places named (as printed): Yayo / 椰油村
  - "'si apen Ogaog (M, 69, Iranmilek)', '黃馬期，男，69，東清村'" — `7. Akay, kayokay rana na koman so nimay!.xml`,
    `8. ko nimanokzos so asa ka kois.xml`, `9. podpoden o ngepen ni Akay.xml`, line 2 each
    applies to: texts 7, 8, 9 (63 sentences), storyteller 黃馬期
    places named (as printed): Iranmilek / 東清村
  - "'si apen Yohani (F, 49, Iranmilek)', '江秀玉，女，49，東清村'" — `10. nisomlet do kakawan a lima no kanakan.xml`,
    `11. Akay, mi namen rana an!.xml`, `12. rarakeh kanakan a ka no cai.xml`, `15. kavavatanen no tazokok.xml`, line 2 each
    applies to: texts 10, 11, 12, 15 (128 sentences), storyteller 江秀玉
    places named (as printed): Iranmilek / 東清村
  - "'si apen Manidong (F, 54, Iranmilek)', '黃堅里，女，54，東清村'" — `13. to ko rana ngaro.xml` line 2
    applies to: text 13 (39 sentences), storyteller 黃堅里
    places named (as printed): Iranmilek / 東清村
  - "'si apen Kazyaz (M, 66, Iranmilek)', '王金玉，男，66，東清村'" — `17. pitareken o pangtoktoan so raroa ka miketeh.xml`,
    `19. nimapo do kalilian a tao.xml`, line 2 each
    applies to: texts 17, 19 (99 sentences), storyteller 王金玉
    places named (as printed): Iranmilek / 東清村
  - "'si apen Kotan/Manokos (F, 74, Iranmilek)', '謝芹容，女，74，東清村'" — `18. manazataza ka no anito.xml` line 2
    applies to: text 18 (60 sentences), storyteller 謝芹容
    places named (as printed): Iranmilek / 東清村
  - "'si apen Maveyvow (F, 58, Iranmilek)', '黃月娥，女，58，東清村'" — `20. piramosen no kakawan a kanakan.xml` line 2
    applies to: text 20 (21 sentences), storyteller 黃月娥
    places named (as printed): Iranmilek / 東清村
  - Full example of one attribute, verbatim (text 1, line 2):
    `source="['1. niomahas a longtsang si Kaojinzhong', '越獄犯高進忠', 'An escaped convict', '', 'si Tonosen (M, 53, Yayo)', '賴金龍，男，53，椰油村', '']"`
- Observed vs inferred notes:
  - OBSERVED: each text's header names one storyteller with sex, age and a village (romanized + Chinese 村). Only the
    village level is printed; no county or township (no 蘭嶼鄉 / 臺東縣) appears anywhere in the corpus folder.
  - OBSERVED: the header is in the form "name (sex, age, village)". It does not say "recorded at". Reading the village
    as the storyteller's home village is the natural reading; reading it as the *recording* place is INFERRED.
  - OBSERVED: texts 1 and 16 spell the storyteller differently and give different ages (`Tonosen`, 53 vs `Tonasen`,
    52) with the same Chinese name 賴金龍 and the same village. That they are one person is INFERRED from the
    identical Chinese name; the village is 椰油村 either way.
  - The README's statement is accurate as written; it gives no speaker names.
- Could not find / not knowable locally: the book's introduction (Rau & Dong 2006, Academia Sinica), which would say
  how and where the stories were recorded, is not in the container. README lines 27-29 say the corpus "was scraped from
  a website prepared by the original authors"; that website cannot be fetched (GitHub/PyPI-only network).
- Proposed README addition (text the maintainer could add later; do NOT add it): "Storytellers, as each file's
  `TEXT/@source` prints them: Yayo (椰油村): 賴金龍 (texts 1, 16), 王仁德 (texts 2–6), 王秋閱 (text 14); Iranmilek
  (東清村): 黃馬期 (texts 7–9), 江秀玉 (texts 10–12, 15), 黃堅里 (text 13), 王金玉 (texts 17, 19), 謝芹容 (text 18),
  黃月娥 (text 20). The source gives each storyteller's village, not the place of recording."

---

### WakelinTexts
- Dialect label(s) in XML (xml:lang + dialect, with file counts): `xml:lang="tao"` + `dialect="Yami"` in all 12 files:
  6 published (`<W>/Corpora/WakelinTexts/XML/Yami/{Kangkang,Kwaway,Kalaku1,Kalaku2,Kalaku3,Sunagu}.xml`) and the same 6
  as frozen copies (`<W>/Corpora/WakelinTexts/CodeAndDocs/pre_correction_snapshot/Yami/*.xml`). 12 files = 6 texts × 2.
- README statement about place (verbatim + line): `<W>/Corpora/WakelinTexts/README.md`
  - line 17: "They were collected on Orchid Island between 1955 and 1957."
  - line 21: "Six Yami (`xml:lang="tao"`, `dialect="Yami"`) narrative texts, collected on Orchid Island between 1955
    and 1957 and published in the 1958 SIL Work Papers article …"
  - lines 23-30, informant table (no places): `Kangkang.xml` "Samen Indosan, April 1955"; `Kwaway.xml` "Sinan
    Dararyaw, May 1957"; `Kalaku1.xml` "Saman Kalaku, 6 September 1956"; `Kalaku2.xml` "Samen Kalaku, 6 September
    1956"; `Kalaku3.xml` "Saman Kalaku, 13 September 1956"; `Sunagu.xml` "Saman Sunagu, January 1957".
  - **"Orchid Island" is NOT in the article.** See "Observed vs inferred" below. Git history (read-only `git log -S`):
    the phrase entered the corpus docs in commit `f64dc5c0a` (2026-08-12, "WakelinTexts: publish original tier only; no
    standard tier, no phonology") and was carried into the merged README by `fdf697d3a` (2026-10-18). The README added
    with the corpus (`cc836af71`, 2026-03-19) had no place statement.
- Sources searched:
  - `<W>/Corpora/WakelinTexts/CodeAndDocs/Original.pdf` (22 PDF pages; PDF p.1 is the UND Scholarly Commons cover sheet,
    PDF pp.2-21 the article, PDF p.22 the errata). The PDF has a text layer (OCR of a typescript; every page returned
    643-2,510 characters). I printed the full text of PDF pp. 1, 2, 5, 6, 7, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22 and
    grepped every page for `imur|imor|irat|yayu|yayo|irar|iran|ival|orchid|botel|tobago|island|village|recorded|collected|informant|lanyu|kotosho|hongtou|taiwan|formosa|taytu|titiwen|here|this country`.
    **I did not render page images**: the Read tool cannot render PDFs here (pdftoppm missing), and rendering with
    pypdfium2 would mean writing image files, which the brief forbids. The text layer captured every header, footer,
    page number and the key, so I judge the risk of a missed statement to be low, but it is not zero.
  - `TEXT` attributes of all 12 XML files: `source` is only "Yami text. Kalaku." / "Yami text. Kangkang." / "Yami text.
    Kwaway" / "Yami text. Sunagu" (line 2 of each file); `citation` and `BibTeX_citation` name only the article. The
    only `notes` values in the published XML are "source annotation: (unctn)" (102×) and one note on a word reading
    (Kwaway S51). No place in any attribute.
  - `<W>/Corpora/WakelinTexts/CodeAndDocs/{source_discrepancies.md, alternative_decisions.json, generate_xml.py, provenance.json, *.tsv, *.sh, *.py}`
    and `<W>/Orthographies/Wakelin/README.md`: only hits are the narrative word `imurud` (source_discrepancies.md
    lines 159-163; alternative_decisions.json lines 198-217; generate_xml.py lines 144-145) and the Yami word `pongso`
    'island' (Orthographies README line 62). No provenance statement.
  - No Wakelin dev repo exists under `/workspace` (`ls -d /workspace/Formosan-*akelin* /workspace/*akelin*`: none).
- LOCATION EVIDENCE:
  - **No statement in the article of where any text was recorded or where any informant lived or came from.** Every
    text header gives only informant + date:
    - "TEXTS Submitted by: Grace Wakelin / Language: Yami / Informant: Samen Indosan, April, 1955 / Ji• Kangkang (The
      Rooster)" — Original.pdf, first article page (no printed number at top; footer "- 140 -") / PDF p.2
    - "Informant: Sinan Dararyaw, May, 1957 / B. Kwaway (The Spirit)" — printed p. 6 / PDF p.7; footnote on the same
      page: "A variation of text A by a different informant."
    - "c. Informant: Saman Kalaku, September 6, 1956" — printed p. 13 / PDF p.14
    - "D. Informant: Samen Kalaku, September 6, 1956" — printed p. 15 / PDF p.16
    - "E. Informant: Saman Kalaku, September 13, 1956" — printed p. 17 / PDF p.18
    - "F. Informant: Saman Sunagu, January, 1957" — printed p. 18 / PDF p.19
    - The key (printed p. 4 / PDF p.5) has one more provenance line, no place: "EA added from data of Erin Asai".
    places named (as printed): none
  - Places that occur **inside the narratives** (story content, NOT statements of where the text was recorded; listed
    so the coordinator can see them, not as evidence of provenance):
    - "8 tusira man-manma u iranmiluk / don't-want rdpl-first unan Iranmiluk" and free translation "They didn't want
      the man from Iranmiluk to go first." — printed pp. 13 and 14 / PDF pp.14 and 15. In the XML:
      `<W>/Corpora/WakelinTexts/XML/Yami/Kalaku1.xml` line 641 `tusya man-manma u iranmiluk` (errata C8 corrects
      `tusira`→`tusya`).
      applies to: text C (`Kalaku1.xml`), Saman Kalaku. places named (as printed): Iranmiluk
    - "3 ni-misa-namen lu ditanasay … tu vagay Darikud", "13 … a-m-angay tu di-taytu / … unan-Taytu", "14 …
      di-sinku / … unan-Sinku"; free translation "we spent the night at Ditanasay, and we slept in Darikud's(unctn)
      house … We all traveled by bus 13 to Taytu. 14 We arrived at Sinku … 18 We gave over one hundred dollars and fifty
      cents over there to get here." — printed pp. 13-14 / PDF pp.14-15. XML: `Kalaku1.xml` lines 126, 1114, 1212, 1618.
      applies to: text C (`Kalaku1.xml`). places named (as printed): Ditanasay, Taytu, Sinku
    - "1 s-ama-n-kalaku ni-mai lu ilaud / NM-father-unan-Kalaku past(unctn)-come to foreign-countr[y]" and free
      translation "1 When I was getting ready to come to this country, … 4 to teach in two other villages. 5 After the
      house had been all swept (and we had made our trip here), 6 I, Saman Kalaku, …" — printed pp. 15-16 / PDF pp.16-17.
      applies to: text D (`Kalaku2.xml`). places named (as printed): none ("this country", "two other villages")
    - "2 … nu tau·d-imurud a-dewdew / … unan person from-Imurud unan-foreigner" and free translation "My dear
      children, when the foreigner in Imurud is lecturing all of you" — printed p. 17 / PDF p.18. XML:
      `Kalaku3.xml` line 114.
      applies to: text E (`Kalaku3.xml`). places named (as printed): Imurud
    - "1 tau nu kakwa amyan su avang tu titiwen", "2 … (imurud nu tau)/(tau d-imurud) / … (Imurud CM persons)/(persons
      from Imurud)", "8 … ni-m-angay lu katyan"; free translation "1 A long time ago, there was a ship at Titiwen. 2 Early
      in the morning, the people from Imurud saw them … 8 All the people from the ship had gone to Katyan … 23 and went
      to their villages." — printed pp. 18 and 20 / PDF pp.19 and 21. XML: `Sunagu.xml` lines 4, 95, 171, 571, 735.
      applies to: text F (`Sunagu.xml`). places named (as printed): Titiwen, Imurud, Katyan
- Observed vs inferred notes:
  - OBSERVED: the article names informants and dates only. It never says "Orchid Island", "Botel Tobago", "Lanyu",
    "Kotosho", "Taiwan" or "Formosa" (all grepped, zero hits), and names no village as a recording site or as an
    informant's home.
  - The README's "collected on Orchid Island" (lines 17, 21) is therefore not supported by the article. Where the
    README author got it is not recorded. It may be general knowledge that Yami is spoken on Orchid Island; that is not
    a statement from the source.
  - INFERRED, and it cuts against the README: texts C and D (Saman Kalaku, September 1956) describe the narrator's own
    trip *to* "the foreign country" / "this country" by boat and bus, ending "to get here" (C, sentence 18) and "we had
    made our trip here" (D, sentence 5). Read literally, the narrator is telling these from somewhere reached by that
    trip, which suggests texts C and D (and maybe E, recorded a week later by the same informant) were recorded *away
    from* the island. This is my reading of narrative content, not a statement by the article.
  - INFERRED, weak: text E addresses "my dear children" about "the foreigner in Imurud", and text F is about "the people
    from Imurud". A story about Imurud does not show the speaker is from Imurud.
  - GENERAL KNOWLEDGE, NOT FROM THE SOURCE (stated once, not evidence): Imurud is the village known today as Imorod
    (紅頭), Iranmiluk as Iranmilek (東清); Taytu is Taitung (臺東) and Sinku is probably 新港 (today 成功) on Taiwan's east
    coast.
- Could not find / not knowable locally: where the six texts were recorded and where the four informants lived. The
  article does not say. Grace Wakelin's field notes, or SIL's records of where she was posted in 1955-57, would be the
  place to look. None are in the container, and SIL/UND sites can't be fetched.
- Proposed README addition (text the maintainer could add later; do NOT add it): "The article names each text's
  informant and date (Original.pdf PDF pp. 2, 7, 14, 16, 18, 19) but does not say where the texts were recorded or where
  the informants lived." Possibly also: lines 17 and 21's "collected on Orchid Island" could be removed or marked as not
  from the source, given that texts C and D describe the narrator travelling to Taitung "to get here" (printed pp. 14,
  16 / PDF pp. 15, 17).

---

### Huteson-Rukai-Survey
- Dialect label(s) in XML (xml:lang + dialect, with file counts): `xml:lang="dru"`, 2 files:
  - `<W>/Corpora/Huteson-Rukai-Survey/XML/Rukai/huteson_2003_rukai_maga_imitation_test.xml`: `dialect="Maolin"` (1 file, 14 S)
  - `<W>/Corpora/Huteson-Rukai-Survey/XML/Rukai/huteson_2003_rukai_tona_imitation_test.xml`: `dialect="Dona"` (1 file, 15 S)
- README statement about place: **README: none.** The only related statements are dialect-label mappings, not places
  of collection: `<W>/Corpora/Huteson-Rukai-Survey/README.md` lines 18-21: "`XML/Rukai/huteson_2003_rukai_maga_imitation_test.xml`:
  `dialect="Maolin"` (the source's label is Maga), 14 sentences." / "`XML/Rukai/huteson_2003_rukai_tona_imitation_test.xml`:
  `dialect="Dona"` (the source's label is Tona), 15 sentences."
- Sources searched:
  - `<W>/Corpora/Huteson-Rukai-Survey/README.md` and `CodeAndDocs/README.md` (both read in full).
  - `CodeAndDocs/source_manifest.md` (read in full): citation, SIL archive URL, PDF SHA-256
    `adf8c6124f46ed414c61c7d121fab22f489c6b98fb17dcd584dbc2eac210b91f`, and line 26 "Internal copy: Basecamp card
    8255603132 (maintainer only; not a build input)." No place.
  - `CodeAndDocs/source_page_coverage.tsv` (read in full), `manual_source_review.tsv`, `extraction_report.tsv`,
    `provenance.json`, `build_xml.py`, `tests/test_corpus.py`, `audit_source_alignment.py`, `validate.sh`,
    `generate_xml.sh`: grep for `村|鄉|部落|社|village|茂林|萬山|多納|kaohsiung|高雄|elicit|record|consult|informant|speaker|subject|resident|born|grew`.
    Only hits are dialect labels ("Maolin", "Maga", "Tona") and one gloss `to:village` in Maga example 14 (sentence
    content). No place of elicitation.
  - XML `TEXT` attributes (line 2 of each file): `source="Huteson 2003 Appendix B, Maga Dialect Imitation Test; source
    label Maga; https://www.sil.org/resources/archives/9008"` and the Tona equivalent; `citation`/`BibTeX_citation`
    name only the report. S-level `source` attributes give only example number and page ("Appendix B MAGA 1; test list
    p. 38; translation p. 39"). The only `notes` are "gloss inferred: …" and "literal translation".
  - `<W>/Orthographies/Huteson/Rukai.tsv` (letter table, columns `Maolin`, `Dona`): no place.
  - Searched for the survey PDF: `find /workspace /home/vscode /tmp/claude-1000 -iname '*huteson*' -o -iname
    '*rukai*survey*' -o -iname '*9008*' -o -iname '*tona*maga*' -o -iname '*maga*tona*'` (excluding .git, venvs,
    site-packages). **No PDF found.** Hits were only corpus copies in other worktrees, orthography tables, statistics
    CSVs, `/workspace/austronesian-voice/docs/audit/voice-conventions/huteson-rukai-survey_dru_*.tsv` (derived from the
    corpus), and ePark audio whose numbers contain 9008.
  - No local dev repo (`ls -d /workspace/Formosan-*uteson*`: none). `CodeAndDocs/README.md` line 43 names
    `https://github.com/FormosanBank/Formosan-Huteson-Rukai-Survey`; an unauthenticated read-only `git ls-remote`
    returned "403" and the GitHub API returned 404, so it is private and I could not see whether it holds the PDF.
    (Cloning it would also have meant writing files.)
  - Found by file name but **NOT read**, per brief rule 2 (it is in the shared checkout): an untracked
    `/workspace/FormosanBank/claudeplans/audit-Huteson-Rukai-Survey.md`. It may quote the report; the coordinator can
    decide whether to look.
- LOCATION EVIDENCE:
  - None found locally. The only place-like content in the corpus is the source's dialect labels:
    - "Huteson 2003 Appendix B, Maga Dialect Imitation Test; source label Maga" — `huteson_2003_rukai_maga_imitation_test.xml` line 2 (`TEXT/@source`)
      applies to: the Maga/Maolin file (14 S). places named (as printed): "Maga" (given as a dialect label, not as an
      elicitation site)
    - "Huteson 2003 Appendix B, Tona Dialect Imitation Test; source label Tona" — `huteson_2003_rukai_tona_imitation_test.xml` line 2 (`TEXT/@source`)
      applies to: the Tona/Dona file (15 S). places named (as printed): "Tona" (dialect label)
  - Where the information would be in the report, per our own page inventory (`CodeAndDocs/source_page_coverage.tsv`
    lines 4-5): "4-32	Survey report body	excluded_non_corpus	0	Rendered prose, maps, tables, and analysis; …" and
    "33-37	Appendix A questionnaires	excluded_non_corpus	0	Rendered questionnaire response tables; demographic
    responses, not Rukai sentence records." The maps and the demographic questionnaires are where the survey villages
    and the respondents' home villages would appear. Neither was transcribed, and the PDF is not here.
- Observed vs inferred notes:
  - OBSERVED: nothing in the corpus folder says where the Appendix B imitation-test sentences were elicited or who gave
    them.
  - The mapping Maga → `Maolin`, Tona → `Dona` is FormosanBank's labelling (README lines 18-21), not a statement of
    collection site.
  - GENERAL KNOWLEDGE, NOT FROM THE SOURCE (stated once, not evidence): Maga and Tona are village-based dialect names;
    茂林 (Maolin) and 多納 (Duona/Dona) are villages in 茂林區, 高雄市.
- Could not find / not knowable locally: the elicitation villages and speakers' home villages. They would be in report
  pp. 4-32 (body, maps) and pp. 33-37 (Appendix A demographic questionnaires). The PDF exists at the SIL archive
  (https://www.sil.org/resources/archives/9008, not reachable from the container), on Basecamp card 8255603132
  (maintainer only), and possibly in the private dev repo `FormosanBank/Formosan-Huteson-Rukai-Survey`.
- Proposed README addition (text the maintainer could add later; do NOT add it): none can be written from local
  evidence. Once the PDF is consulted: "Huteson's survey sites and the respondents' home villages are described on
  pp. [X] (map p. [Y]); the Maga imitation-test sentences were elicited in [village], the Tona ones in [village]."

---

## Note on files written
The only file I wrote is this one. Two of my read-only searches (a `find` over `/workspace`, and a `git log -S` over
all branches) went past the shell's 2-minute limit, and the tool harness moved them to the background on its own. When
it does that, it writes the command's output to its own task folder
(`/tmp/claude-1000/-workspace-FormosanBank/e78edf4a-c5b9-400e-864e-ff685648c37f/tasks/ba23caic7.output` and
`.../tasks/buva1z80g.output`; I stopped the second one). Those are the harness's files, not repo files, and nothing in
any repo was touched.

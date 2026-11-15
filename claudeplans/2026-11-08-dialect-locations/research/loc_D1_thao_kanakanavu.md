# Where the data was collected: Thao and Kanakanavu corpora (agent D1)

Read-only research. Nothing was changed in any repo. FormosanBank files were read only from the worktree at current
`main` (`/tmp/claude-1000/-workspace-FormosanBank/e78edf4a-c5b9-400e-864e-ff685648c37f/scratchpad/fb-main`, HEAD
`2a345f0d9 Merge pull request #317 ...`). PDF text was read through the text layer (pypdfium2), restricted to the
visible area of each page (cropbox). Page images were NOT viewed: the Read tool cannot render PDFs in this container
("pdftoppm is not installed"), and rendering with pypdfium2 would mean writing image files, which the brief forbids
(only this file may be written). All four PDFs used here have a usable text layer, so this was not needed for the
quotes below; it matters only where noted (one map page in Blust).

Text-layer artefact to be aware of: the Blust PDF drops the "fi"/"fl"/"ff" ligatures (e.g. it reads "eldwork",
"uent", "dierent"). In quotes below such letters are restored in square brackets, e.g. "[fi]eldwork".

---

### Blust-Thao-Dictionary
- Dialect label(s) in XML (xml:lang + dialect, with file counts): `xml:lang="ssf"` + `dialect="Thao"` (+ `glottocode="thao1240"`) in all 21 files under `fb-main/Corpora/Blust-Thao-Dictionary/XML/Thao/` (8 `entries_*`, 8 `examples_*`, 5 `text_0*`). `<TEXT>` `citation`/`BibTeX_citation`/`source` name only the book, page ranges, URLs and a Basecamp card; no place or speaker.
- README statement about place (verbatim + line): `fb-main/Corpora/Blust-Thao-Dictionary/README.md` line 24: "Robert Blust's *Thao Dictionary* (2003) is the standard reference work for Thao, a Formosan language of central Taiwan spoken around Sun-Moon Lake." No village, consultant or place of collection is named anywhere in the README (grep of the whole README for Barawbaw|Te-hua|德化|日月|Tarigkuan|Kilash|Lujan|Ishul|Min-hu|consultant|informant: only lines 24 and 28 hit, neither names a place beyond Sun-Moon Lake).
- Sources searched: `/workspace/Formosan-Robert-Blust-Thao-Dictionary/Private/[OA] Thao Dictionary.pdf` (1,117 PDF pages; SHA-256 bd769bc6…2f95, identical to the copy in that repo's `CodeAndDocs/`). Printed page = PDF page − 10 in the body (printed p. 1 = PDF p. 11). Read in full: PDF pp. 3, 8–22 (dedication, photo caption, Preface pp. vii–viii, Introduction pp. 1–5, "1 General background" pp. 6–12 incl. "1.2 Data collection"), PDF p. 254 (printed 244, opening of "8 Texts"); headers of every page PDF 254–285 grepped for narrator/place words. Grep of PDF pp. 1–30 for Chinese characters / Nantou / Ita Thao: no Chinese place names at all (only "Pu-li … Nantou county" and "Nantou County"). Grep of the 21 XML files for speaker names.
- LOCATION EVIDENCE:
  - "Most of the Thao who still maintain their language reside in Te-hua village (Thao: Barawbaw), a mixed Taiwanese-Thao community on the southeast shore of Sun-Moon Lake, in Nantou County, near the geographical center of Taiwan." — printed p. 1 / PDF p. 11 (Introduction)
    applies to: the speech community as a whole (where the speakers live), so the whole corpus by context
    places named (as printed): Nantou County / — / Te-hua village (Thao: Barawbaw) / Sun-Moon Lake
  - "A second, smaller community of Thao who reportedly speak a slightly di[ff]erent dialect was still found at Ta-p'ing-lin (Twapina), some 14 km. from Sun-Moon Lake in 1976, whence they had emigrated from the village of T'ou-she (Shtafari) earlier in this century (Li 1983). Its present status is unknown." — printed p. 1 / PDF p. 11
    applies to: NOT to this corpus's data (Blust does not say he worked there); quoted because the brief names 大平林. Blust names a dialect difference for this community.
    places named (as printed): Ta-p'ing-lin (Twapina); village of T'ou-she (Shtafari)
  - "including the collapse of the Min-hu Club where much of the Thao data was collected during various [fi]eldwork trips, preliminary reports indicate few if any human casualties in Te-Hua village." — printed p. 4 / PDF p. 14
    applies to: "much of" the data (whole corpus, not per file)
    places named (as printed): Min-hu Club (Sun-Moon Lake area); Te-Hua village
  - "Mr. Peng Hsin-chin and his family, owners of the charming lakeside `Min-hu Club' where I often stayed" — Preface, printed p. viii / PDF p. 10
    applies to: fieldwork base (context for the quote above)
    places named (as printed): lakeside `Min-hu Club'
  - "According to information obtained principally from Mr. and Mrs. Shih, the following persons at Te-hua village still are able to converse in Thao." — printed p. 9 / PDF p. 19 (list of 15 speakers follows, pp. 9–11)
    applies to: all speakers Blust lists, including his consultants
    places named (as printed): Te-hua village
  - Consultants, as printed (printed pp. 10–11 / PDF pp. 20–21):
    "(4) Ishul (Yuan Chang-erh, Mrs. Shih): b. 1926 in Tarigkuan village, … Ishul reportedly spoke only Thao until she went to school in Tou-she at the age of 12."
    "(5) Kilash (Shih A-sung, Mr. Shih): b. 1922 in Tarigkuan village, … Both Kilash and Ishul were children (he 13 and she 9) when the Japanese administration rounded up the Thao from all over Sun-Moon Lake and relocated them in Te-hua village in 1935."
    "(8) Lujan (Kao Chang-feng, Mr. Kao): b. 1937 in Te-hua village shortly after the relocation."
    "(11) Puni (Mao Chiu-hsiang): a female, b. 1922 in Tarigkuan village. The wife of Raushian."
    applies to: the four people the data came from (see share quote next)
    places named (as printed): Tarigkuan village (birthplace, old village flooded by the 1935 dam); Te-hua village (residence after 1935; Lujan's birthplace); Tou-she (Ishul's school)
  - "About 65% of the material was collected from Kilash, another 25{30% from Lujan, and perhaps 5% from Ishul. A tiny portion was obtained from Puni (Mrs. Mao) in two or three sessions." — printed p. 11 / PDF p. 21 ("{" is the text layer's rendering of an en dash)
    applies to: whole corpus (dictionary entries + example sentences). The book does not attribute each sentence to a speaker; the XML has no speaker field. Speaker names appear only inside some entry notes, e.g. `entries_0380_0479.xml` line 1739: `notes="Source note: Mrs. Shih gave /frit/ for /firit/…"`, line 2220: `notes="Source note: Mr. Kao gave /mu–lhkat/…"`.
  - "The [fi]ve texts which follow … All [fi]ve were related by Mr. Shih at various times during the period 1995-1998." — printed p. 244 / PDF p. 254 (opening of "8 Texts")
    applies to: the 5 files `blust_2003_thao_text_01.xml` … `text_05.xml` (narrator = Kilash / Mr. Shih)
    places named: none in this sentence
  - "Mr. Shih learned this story when he was a boy in Shtafari (modern Tou-she) from the man he called Apu Pashulan (Grandfather Pashulan), of Raushian's lineage, and from Apu Ilash." — printed p. 244 / PDF p. 254
    applies to: `blust_2003_thao_text_05.xml` (The White Deer) — where the narrator learned the story, not where it was recorded
    places named (as printed): Shtafari (modern Tou-she)
  - "Thao informants, Kilash and his wife, Ishul, in the porch of their new house, May 2002." — photo caption, unnumbered page, PDF p. 8 (no place named)
  - "the frontispiece map of traditional Thao village sites and other important locations around the perimeter of Sun-Moon Lake" — Preface, printed p. vii / PDF p. 9. The map itself (PDF p. 7, one image object, no text layer) was NOT viewed (no rendering possible without writing an image file).
- Observed vs inferred notes: Observed: consultants live(d) in Te-hua village (Barawbaw) on Sun-Moon Lake, Nantou County; three of the four were born in Tarigkuan and moved to Te-hua in 1935; "much of" the data was collected at the Min-hu Club (Sun-Moon Lake area). Not stated: a Chinese name for Te-hua/Barawbaw — the book never prints 德化社 or 日月村 (grep of PDF pp. 1–30 for Chinese characters found none). GENERAL KNOWLEDGE, NOT FROM THE SOURCE: Te-hua (德化社) is the former name of present-day 日月村 (Ita Thao), 魚池鄉. That equation is not in the book and should not be used as evidence.
- Could not find / not knowable locally: no per-sentence speaker attribution (only percentages); the frontispiece map (PDF p. 7) unviewed. The book never says the Ta-p'ing-lin (大平林) community contributed data.
- Proposed README addition (do NOT add): "Blust's consultants lived in Te-hua village (Thao: Barawbaw) on the southeast shore of Sun-Moon Lake, Nantou County; Kilash (Shih A-sung, about 65% of the material and all five texts), Lujan (Kao Chang-feng, 25–30%), Ishul (Yuan Chang-erh, about 5%) and Puni (Mao Chiu-hsiang, a tiny portion). Kilash, Ishul and Puni were born in the old village of Tarigkuan and moved to Te-hua in 1935, and much of the data was collected at the Min-hu Club by the lake (Blust 2003: 1, 4, 9–11, 244)."


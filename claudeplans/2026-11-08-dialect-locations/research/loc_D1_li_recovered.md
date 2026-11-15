### Li-Conjunction-Thao
- Dialect label(s) in XML (xml:lang + dialect, with file counts): `xml:lang="ssf"` + `dialect="Thao"` (+ `glottocode="thao1240"`) in its 1 file, `fb-main/Corpora/Li-Conjunction-Thao/XML/Thao/li_2014_conjunction_in_thao.xml`. `<TEXT>` `source="Li 2014 PDF pp. 394-402 (printed pp. 401-409)"`; `citation`/`BibTeX_citation` name only the article. No place or speaker.
- README statement about place (verbatim + line): `fb-main/Corpora/Li-Conjunction-Thao/README.md` line 3: "… a study of coordination and subordination in Thao — a Formosan language spoken at Sun-Moon Lake in central Taiwan." No village or informant named in the README or in `CodeAndDocs/` (grep of *.md, *.json, *.tsv, *.csv for village|Barawbaw|Te-hua|德化|日月|Ita Thao|informant|Puni|Kila: no hits).
- Sources searched: `/workspace/Formosan-Naomi-Tsukida-Correlative-Clauses-Seediq/Private/source/anu/Papers from 12-ICAL, Volume 2.pdf` (402 PDF pages; SHA-256 fab9b60c…248f1, which equals the sha256 in `fb-main/Corpora/Li-Conjunction-Thao/CodeAndDocs/source_manifest.json`). Only Li's article read: PDF pp. 394–402 = printed pp. 401–409 (printed = PDF + 7). Full text of PDF pp. 394, 395, 399, 401 read; all nine pages grepped for village|Barawbaw|Te-hua|Ita Thao|Sun-Moon|Lake|Nantou|informant|speaker|Puni|Kila|collected|record|Twapina|Shtafari|Tou-she|county|township. Dev repo `/workspace/Formosan-Paul-Jen-Kuei-Li-Conjunction-Thao` (HEAD a2f4c59) grepped (non-XML files): hits only in its own text extractions of the same pages (`intermediate/article_pages_394_402_layout.txt`), nothing new.
- LOCATION EVIDENCE:
  - "Thao is a Formosan language spoken at Sun-Moon Lake in central Taiwan, with a small population of 728." — printed p. 401 / PDF p. 394
    applies to: the language as a whole (not a statement of where the examples were recorded)
    places named (as printed): Sun-Moon Lake, central Taiwan
  - "All examples are based on the 42 Thao texts I collected from two main informants, one female and one male, over two different periods: 1975-1976 with the female informant, Puni, and 1996-2003 with the male informant, Kilaʃ (Li 2011)." — printed p. 401 / PDF p. 394
    applies to: the 24 numbered examples (+ footnote 5) — see per-text split below
    places named: none
  - "Texts 1-30 except 4 in Part I are based on Puni, while Texts 31-42 in Part II are based on Kilaʃ." — printed p. 408 / PDF p. 401 (Appendix)
    applies to: per-example split, using each example's printed "(text-sentence)" reference recorded in `CodeAndDocs/reviewed_examples.tsv` column `source_ref`:
      - Puni (texts 1–30 except 4), 12 S: S001 (5-7), S002 (5-8), S003 (5-2), S004 (2-3), S006 (8-10), S007 (1-5), S011 (10-16), S012 (10-17), S017 (6-9), S018 (6-12), S019 (8-14), S020 (13-5)
      - Kilaʃ (texts 31–42), 9 S: S009 (37-25), S010 (37-26), S013 (33-34), S014 (39-51), S015 (32-9), S021 (39-50), S022 (39-57), S023 (39-211), S024 (39-236)
      - Text 4 (the article excludes it from Puni's texts but does not say whose it is), 3 S: S005 (4-21), S008 (4-7), S016 (4-5)
      - Footnote 5 inline example, no text reference, 1 S: `li2014_thao_fn5_1` ("tu sa suma wa anyamin")
      - Footnote 7, quoted by Li from Blust (2003: 1043, 398, 393), not from Li's own texts, 3 S: S025, S026, S027
      (12 + 9 + 3 + 1 + 3 = 28 = all S in the file)
  - "Minor changes were made in a few examples, as suggested by my informant, Kilaʃ (2013/8/1)." — footnote 3, printed p. 402 / PDF p. 395 (no place)
  - "Since F. K. Li collected his two short texts from an older Thao informant, while Blust and Wang collected theirs from the same informant, Kilaʃ" — printed p. 401 / PDF p. 394. States that Kilaʃ is the same informant Blust used. That is the article's own statement; it does not say where Kilaʃ lived.
- Observed vs inferred notes: Observed: the two informants' names (Puni, Kilaʃ), years, and which texts are whose. NOT stated anywhere in Li's article: any village, township or county for either informant or for the recording sessions. The only place is "spoken at Sun-Moon Lake in central Taiwan" for the language. INFERRED (do not use as evidence for this corpus): the names Puni and Kilaʃ match two consultants in Blust's dictionary, where they are described as living in Te-hua village; per the brief's rule 3 that is another corpus's source and is not evidence for this one.
- Could not find / not knowable locally: the place of collection would most likely be in Li (2011), the text collection the article cites for its 42 texts ("(Li 2011)"); that publication is not in this container (not searched beyond the files named above).
- Proposed README addition (do NOT add): "Li's examples come from 42 texts he collected from two informants: Puni (1975–1976; texts 1–30 except 4) and Kilaʃ (1996–2003; texts 31–42) (Li 2014: 401, 408). The article says only that Thao is 'spoken at Sun-Moon Lake in central Taiwan'; it does not name the informants' village."


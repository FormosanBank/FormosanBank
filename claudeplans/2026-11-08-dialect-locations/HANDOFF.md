# Dialect locations check — handoff (state on 2026-11-15)

## The task (maintainer, 2026-11-07, verbatim)

> "I just added a new doc "110年原度原住民族語言能力認證測驗輔導班方言別" to QC/reference. It lists where various
> dialects are currently spoken. I'd like you to go through every corpus for which we have a dialect specified OTHER
> than ePark and Presidential Apologies. Check whether the corpus doc says where the data was collected. If so,
> compare against this list. If not, see if you can the PDF (you may need to look at the dev repo to get the PDF).
> Add that information to the corpus documentation if you find it. Then compare against the new list.
>
> I don't want anything changed now. I just want to know what matches and what doesn't. And what we don't know
> because we can't find the info."

Then (2026-11-08): "Can you plese update the artifact so I can respond to each card?"

## Where things stand

| Step | State |
|---|---|
| Reference PDF into the repo | DONE — merged as PR #320 (`QC/reference/110年原度原住民族語言能力認證測驗輔導班方言別.pdf`, sha256 `3c7c3e74…68174cf`). The maintainer kept the filename as given (年原度, not 年度). |
| Research (where each corpus's data came from) | DONE — 29 corpora / 57 corpus×label units / 866 published files. Notes with verbatim quotes and page numbers in `research/`. |
| Report page | PUBLISHED, version 2 with a response panel on every card: https://claude.ai/artifact/TuYPc3SGu4RUDBGZU5QnmV |
| Maintainer's answers | IN PROGRESS — 13 of 40 items answered, "I'm done" not pressed (`responses_snapshot_2026-11-15.json`). Live record = the artifact's `responses` collection (doc id = item id); `meta/status` doc gets `{done:true}` when he presses the button. |
| Any change to corpora/READMEs | NONE. Nothing may change until he has finished answering, been shown a plan, and agreed to it. |

## What the next agent does

1. Wait until the maintainer says he has responded. Then read **every** doc in the artifact's `responses`
   collection (`ArtifactData list`, url above) — the snapshot here may be stale.
2. Quote back each answer and what it would change, as a plan; get agreement before editing anything.
   Option meanings are defined in `report/rows.py` (`SPECIAL_Q`, `README_Q`, `GENERAL_Q`, `NOTFOUND_ITEMS`);
   implement only what the chosen option's text says.
3. Answered so far: `readme: add` on Blust, Song, and 7 NTU cards (Kavalan, Wutai, Sakizaya, Wenshui, Tegudaya,
   Tsou, Saisiyat); `readme: leave` on Nowbucyang, Seediq-Chang, Yedda; `leave` on RauDong. The README text for
   each "add" is the card's `add` field in `report/rows.py`. Before writing it, check it against the README rules
   in memory ("no history; caveats only for real decisions") — it may belong in a source/provenance section rather
   than Notes & caveats.
4. Still open (27 items), including all the label questions: Wilang Yutas (Sekolik vs 南山/大同鄉 → 四季 or
   宜蘭澤敖利 in the list), HundredPaiwanStories texts 095/098, Fey, Poinsot unmarked and {S} entries, Wakelin's
   "collected on Orchid Island", and the not-found groups.
5. Publish the next round with only what is still open (rebuild with `python3 report/build.py` after editing
   `report/rows.py`; it fails if any of the 57 units is missing or duplicated).

## Files

- `report/rows.py` — every card: verdict, evidence quotes, what the list says, caveats, proposed README text,
  response options. `report/build.py` + `report/template.html` build `report/dialect-locations.html`
  (byte-identical to the published version 2). Run from `report/`: `python3 build.py`.
- `dialect_locations.tsv` — the PDF's 12 tables flattened (133 rows, 42 dialects; blank cells filled from the row
  above, including across page breaks). Extracted with pdfplumber.
- `published_dialect_counts.txt` — per corpus/lang/dialect counts of files directly under `Corpora/<c>/XML/` on
  main 2a345f0d9 (CodeAndDocs snapshots excluded).
- `research/loc_*.md` — the research agents' per-corpus notes (verbatim quotes, file paths, printed + PDF pages,
  observed vs inferred, proposed README text). `loc_D1_li_recovered.md` was recovered from a hung agent's last
  command. `agent_brief.md` is the brief they worked from.

## Method notes a successor needs

- A statement of where a *language* is spoken ("Thao is spoken at Sun-Moon Lake") was not counted as a collection
  place; only statements tied to the data or its speakers were.
- Several matches rest on the author's own identification of a place (romanized names such as Changpin = 長濱,
  Siyu-Lin = 秀林; outside knowledge such as Paiwan Kuɫaɫau = 古樓, Te-hua = 日月村). Each card labels which.
- Sources checked directly, beyond the agents: the Poinsot preface + abbreviation key (scan page 3 of
  github.com/miaoski/amis-chinese-poinsot, `pic/img-117110211_頁面_003.tiff`), Song's 作者序 (PDF p. 14, no text
  layer), ILCAA intro (PDF pp. 13, 15, 31), Li 2014 (PDF p. 394), Pa-Verbs footnote, Wakelin full text, NTU
  `meta.language` tally, HundredPaiwanStories headings.
- Not reachable from the container: ILRDF/Glosbe sites, YouTube descriptions, Paradisec pages, SIL archive
  (Huteson), new-amis.moedict.tw (Fey's introduction; not in the GitHub mirrors g0v/amis-moedict or
  miaoski/amis-data).

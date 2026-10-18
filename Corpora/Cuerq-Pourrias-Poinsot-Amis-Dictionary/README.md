# Cuerq-Pourrias-Poinsot-Amis-Dictionary

The Amis–Chinese dictionary of Gérard Cuerq and Louis Pourrias (2002), with French translations for its first four
pages from the Poinsot/Pourrias Amis–French dictionary: 27,526 entries and examples in Amis and Sakizaya, each with its
Chinese translation, printed page and line.

**Languages:** Amis (`ami`, glottocode `amis1246`); Sakizaya (`szy`, glottocode `saki1247`) for the entries the book marks {Z}
**Status:** built, cleaned, standardized, tested and validated (2026-10-18). Open items deliberately left for later are
listed under [Notes and Issues](#notes-and-issues).
**History:** first built from the Amis–French volume (2026-06-12); rebuilt from the Amis–Chinese volume on 2026-10-17,
and the French build was retired.

## Source

Cuerq, Gérard (顧向前, Ci Ka Ogto) & Pourrias, Louis (博利亞) (2002). *O Citig no Amis: 阿美語－漢語字典*
(博利亞潘世光阿漢字典), a 600-page Amis–Chinese dictionary from the Paris Foreign Missions Society (Missions Étrangères de Paris).
The French translations of pages 1–4 come from the companion Amis–French dictionary: Poinsot, Maurice & Pourrias,
Louis, *Amis-French dictionary*, n.d. The XML cites both.

The text is the g0v crowd transcription, typed twice (2017 and 2020) line by line against the page scans:

| Source | Pinned commit | Used for |
|---|---|---|
| [wildjcrt/amis-chinese-poinsot-onefile](https://github.com/wildjcrt/amis-chinese-poinsot-onefile) `pourrias-poinsot.txt` | `365cfce` | the text, one entry per line |
| [miaoski/amis-chinese-poinsot](https://github.com/miaoski/amis-chinese-poinsot) branch `toufu`, `toufu.sq3` | `a35e2cb` | printed page and line of every line (2020 proofreading database) |
| [miaoski/amis-francais](https://github.com/miaoski/amis-francais) `txt/001–004.txt` | `8d74f90` | French pages 1–4, hand-checked upstream in 2015 → `CodeAndDocs/data/french_pages_1_4.json` |
| miaoski/amis-chinese-poinsot branch `master`, `convert/` | — | page scans, used to check decisions (not needed to build) |

The two files the build reads are committed under `CodeAndDocs/source/` (`pourrias-poinsot.txt` and the whole
`toufu.sq3`, 5.4 MB), with their SHA-256 pinned in `CodeAndDocs/build_amis_chinese_xml.py`.

## Rights

**License:** CC BY-NC 4.0
**Rights source:** [`g0v/amis-moedict@e7c6976` README](https://github.com/g0v/amis-moedict/blob/e7c6976a0766e9b0aeb7083e2c06db60f5485252/README.md#%E6%8E%88%E6%AC%8A),
which says that Maurice Poinsot and Louis Pourrias, through the Missions Étrangères de Paris, provided the Amis–French
and Amis–Chinese dictionaries under CC BY-NC, with no version given. The maintainer's ruling of 2026-10-17: "CC BY-NC
4.0, as we do elsewhere. Their fault that they didn't say."

The text comes from the g0v crowd transcription (`miaoski/amis-chinese-poinsot`, `wildjcrt/amis-chinese-poinsot-onefile`)
and the French pages from `miaoski/amis-francais` (pinned commits above). Use and redistribution of the XML must follow
CC BY-NC, including attribution and the non-commercial restriction. The scripts and tests under `CodeAndDocs/` are not
covered by the dictionary's licence. This section records source evidence and scope; it is not legal advice.

## Output

13 files under `XML/`, one head-word file and one example file per source label:

| Label in the book | Meaning (book's own key) | Files | `xml:lang` | `dialect` |
|---|---|---|---|---|
| {S} | 南方話 | `XML/Amis/poinsot_chinese_S_*.xml` | ami | Southern |
| {N} | 北方話 | `XML/Amis/poinsot_chinese_N_*.xml` | ami | Southern |
| {F} | 鳳林話 | `XML/Amis/poinsot_chinese_F_*.xml` | ami | Xiuguluan |
| {T} | 富田語 | `XML/Amis/poinsot_chinese_T_*.xml` | ami | Xiuguluan |
| (none) | — | `XML/Amis/poinsot_chinese_unmarked_*.xml` | ami | Xiuguluan |
| {豐濱}, {Tingalaw} | places | `XML/Amis/poinsot_chinese_Coastal_headwords.xml` (2 entries; no examples) | ami | Coastal |
| {Z} | Zakiraya 話 | `XML/Sakizaya/poinsot_chinese_Z_*.xml` | szy | Sakizaya |

Every `S` has a `kindOf="original"` `FORM` (the book's spelling), a `kindOf="standard"` `FORM` (Ortho113), a standard
`PHON`, and one or more Chinese `TRANSL` (the first is the main reading, the rest `ver="alt"`). Some also have Latin, English, French or German `TRANSL` for names printed in the book. The `FORM`
notes give the printed page and line (`printed p.123 l.04`).

## How the build reads the book

All the rules below were set by the maintainer, card by card, on the decision page
(https://claude.ai/artifact/Jjv2qdtPzyDcvRHiZaSt7Y). Each is quoted in `FormosanBank/claudeplans/sweep-qa-decision-log.md`
("Poinsot" entries, 2026-10-16/17) and in the data file that carries it. Nothing in `XML/` is edited by hand.

- **Entries.** One source line is one entry. Printed lines that the typists split are joined (`line_wraps.tsv`), and
  entries glued onto the line before are split off (`line_splits.tsv`). Both are checked against the 2020 database's
  page and line numbers.
- **One `S` per defined form.** A derived form or an equivalent (`X - Y = Z`) gets its own entry. The root is not an
  entry; it is named in the notes (`root: X`). A root that has no translated entry of its own anywhere in the book gets
  no entry (it may be a bound root).
- **Dialect markers.** Before the colon, a marker belongs to its `=` group. After the colon, it belongs to its `；` piece.
  An item marked with several dialects goes into each of their files, and a reading marked for one dialect goes into
  that file only.
- **Inheritance.** Words written after the colon of a marked head word, with no marker of their own, take the head
  word's dialect. Example: `ciyak - {N}：西瓜：cak, lidaw, kacawas, sinar` puts all five in the N file.
- **Alternative forms.** Within one entry and one dialect file, forms that differ by at most 2 characters and have
  identical translations become one `S`. The first form is the main `FORM`, the others `FORM ver="alt"`. A form with
  notes of its own, such as a borrowing marker, is not merged.
- **Borrowings.** {J} → note "Japanese borrowing", {Tw} → "Hokkien borrowing", {Ch} → "Mandarin borrowing", and so on.
- **Names in translations** (`latin_runs.tsv`, one row per name) become their own `TRANSL`: scientific names →
  `xml:lang="lat"`, English → `eng`, French → `fra`. Two Amis terms stay inside the Chinese (`mama no kapah`,
  `’Na Taolan’`), and the rest go to notes. German glosses → `deu`.
- **The compiler's "(？)"** → note "translation uncertain" on that sense.
- **Bible references, cross-references, and Chinese remarks in parentheses** go to notes, not the translation. The label
  `[宗]` is dropped.
- **A dangling "("** closes just before the next example, or at the end of the entry.
- **Typing errors** checked on the scan are corrected (`text_corrections.tsv`). Printed lines that the 2020 database
  marked blank but that have text were restored from the scan (`restored_lines.tsv`, 4 lines).
- **Lines the maintainer ruled out** of the corpus: `exclusions.tsv`, 10 lines.
- **Lines whose result the maintainer specified word by word:** `card_rulings.json`, 32 lines.
- **French pages 1–4** attach to the matching Chinese entries (`french_decisions.tsv` records the exceptions).

## How to reproduce

```bash
bash CodeAndDocs/generate_xml.sh      # build, clean, standardize, add phonology, install XML/ (POL-047)
bash CodeAndDocs/refresh_source.sh    # optional: re-pull the two source files from their pinned commits (GitHub access)
python -m pytest CodeAndDocs/tests    # the corpus tests (see Tests)
python CodeAndDocs/audit_entry_format.py   # optional: re-run the entry-format audit (CodeAndDocs/data/format_audit.tsv)
```

`CodeAndDocs/generate_xml.sh` is the entry point in the POL-047 shape:

1. `CodeAndDocs/build_amis_chinese_xml.py` builds the original tier into a staging folder from `CodeAndDocs/source/`
   and the decision tables in `CodeAndDocs/data/`.
2. `QC/cleaning/apply_manual_edits.py` (a no-op: there are no manual edits).
3. `QC/cleaning/clean_xml.py`.
4. `QC/utilities/standardize.py`, with `Amis_Church_113.tsv` for Amis and `Sakizaya_Church_113.tsv` for Sakizaya.
5. `QC/utilities/add_phonology.py`.

It reads only `CodeAndDocs/` and the FormosanBank checkout it sits in (POL-048), installs `XML/` only when every step
succeeds, and a second run leaves `git status` unchanged. The FormosanBank commit the published XML was built against is
recorded in [`CodeAndDocs/provenance.json`](CodeAndDocs/provenance.json) (POL-052). Python 3.13, with FormosanBank's
`.venv`.

## Orthography and standardization (QC, 2026-10-17)

- **Original spelling.** The book's spelling is Church-style. The orthography detector ranks Church first in every Amis
  file it can score (93.3% Xiuguluan, 93.2% Southern). The letters agree: `g` 6,516 times against `ng` 19 (Church `g` =
  ŋ), `o` 26,070 against `u` 8, and no `^`. The maintainer ruled Amis = Church.
- **Amis standard tier.** `Amis_Church_113.tsv` with the file's dialect column: `g`→`ng` everywhere; `o`→`u` and `f`→`v`
  in the Southern files (N, S) only. The Southern `f`→`v` rule was added for this corpus (approved 2026-10-17, decision
  page card m1; FormosanBank PR #298): of 370 Southern standard words with `f`, 0 are in the Southern reference as
  written and 46 with `f`→`v`. It took Southern PHON with an unmapped `*` from 407 entries to 1.
- **Sakizaya standard tier.** The compiler wrote Sakizaya in the same Church-style spelling, and no table existed for it.
  The new `Sakizaya_Church_113.tsv` (ruled: *"Let's go with option 2."*) has `g`→`ng`, `o`→`u`, `f`→`b`, `r`→`l`.
  Against FormosanBank's Sakizaya reference vocabulary (10,484 words), 247 of the book's 728 distinct Sakizaya words are
  found after conversion, against 114 as written and 145 with the Ortho94 table. No rule breaks a word that was found
  before.
- **Letters with no standard mapping**, shown as `*` in PHON (POL-003):
  - `ù` in `tansù` (the one Southern entry left).
  - `b`, `z`, `v` in names and loans (`Abraham`, `caliber`), and in the book's short z-section (`zadan`, `mizaao`).

## QC

Validators run on `XML/` on 2026-10-18 (full logs under `qc-output/`, not committed):

- **`validate_xml`:** 0 HARD after the fixes below. 178 SOFT V150: alternative spellings that look quite different, which
  are expected where forms 1–2 letters apart were merged.
- **`validate_text`:** SOFT only.
  - V122 parentheses in Chinese translations: these are the book's own explanatory notes.
  - V126 `=` in an example (1): line 13861 `raro’itan = o sapihafay a lisin`, a pair printed without a translation,
    which stays an example (see "Word pairs" below).
  - V133 dashes: prefixes listed as head words (`aki-`) and printed hyphens.
  - V116: the printed `…`, and `ù` in `tansù`.
  - V135: 0. Before FormosanBank PR #304 (2026-10-18) it reported 164 false alarms: both tiers end in `?`, but the rule
    read the original tier with the letters of every Amis spelling profile, including Montgomery's, where `?` is a
    letter. It now uses the spelling the corpus declares in `CodeAndDocs/generate_xml.sh` (Church).
- **Orthography vs reference** (standard tier, character overlap coefficient / cosine):
  - Xiuguluan: 0.90 / 0.991.
  - Southern: 0.96 / 0.986.
  - Sakizaya: 1.00 / 0.974 (against `reference/Sakizaya/default`).
- **Vocabulary vs reference (top-100 words, overlap coefficient):** Xiuguluan 0.55, Southern 0.31, Sakizaya 0.18. Low
  is expected for a dictionary against references made from running text: their top words are function words
  (Sakizaya `u atu ayza kiya …`), and a dictionary lists each word once.
- **Coastal** (2 entries, `alomdas podok`) is too small to profile and is skipped with a warning.
- The Sakizaya comparison and the Coastal skip use the FormosanBank fixes merged in PR #301 (2026-10-18, cards r2-m4a
  and r2-m4c). With older QC code, Sakizaya is not compared (the validators looked for `reference/Sakizaya/Sakizaya`)
  and `orthography_extract.py` crashes on Coastal.

### Word pairs

Examples printed as two forms with one translation (`sasoalen = sasowalen：話，要講的話`) are head-word entries, one S
per form, listed under the line's head word and in its dialects (ruled 2026-10-17, card m5; 2026-10-18, card r3-pairs).
Forms 1–2 letters apart merge into one S with an alternative spelling. Every Chinese-only `；` piece after the pair is the
pair's (card r2-m5: *"Please try reparsing assuming the mandarin is a translation/definition"*; lines 16113 and 17211
confirmed, cards r3-16113 and r3-17211). 50 of the 52 pair lines convert. Two stay examples: line 13861
`raro’itan = o sapihafay a lisin`, which has no translation, and line 12604, printed `ccay a pawti = 26 斗`, which
is the example `ccay a pawti` with translation `26 斗` (card r3-12604).

Fixed in this repository's build after the first QC run:
- V085 (23 entries with two Latin, English or French translations, now `ver="alt"` on the second).
- The Safolu `?`/`!` spacing rule, which had not been applied to the full-width `？！` the source uses.
- POL-027: an example printed as two alternative sentences (`dada kiso = tanam kiso`) is now one `S` per option (41
  examples).
- Sub-entries printed `X = Y：gloss` now give one `S` per form.
- `ma’deg - (夠了！：ma’deg to！)：適當，足夠` (line 9710; the only entry of this shape): the parenthesised `(Chinese：Amis)`
  is now read as an example of the head word. Previously the two translations were swapped.

## Tests

`CodeAndDocs/tests/test_amis_chinese_volume.py` checks the XML against the source with its own small parser,
independent of the build. It covers the pinned source files (hashes), the file layout, dialect assignment, that nothing
is lost (every source line, Amis word and Chinese run appears somewhere), the rulings, and reproducibility.
`CodeAndDocs/tests/test_source_accounting.py` checks that every one of the source's 17,930 lines is in `XML/` (17,877)
or rejected with a reason (53: 10 ruled exclusions in `exclusions.tsv`, 43 printed continuations joined to the line
above in `line_wraps.tsv`). Current result: **61 of 63 pass**. The 2 failing tests
(`test_mixed_marker_pieces_are_accounted_for`, `test_every_item_in_a_dialect_file_was_marked_with_that_dialect`) are the
25 unruled mixed-marker lines under Notes and Issues. They are expected to fail until those lines are decided.

## Notes and Issues

The maintainer decided on 2026-10-17 to publish what is built now and leave these for later. Each item says where it
stands and how to pick it up.

1. **54 printed lines the 2020 volunteers marked blank, but which have text on the scan.** They are not in the data yet.
   A student transcription page is ready: https://claude.ai/artifact/2nBDcNWUcujmqFkNzTW71k (the maintainer must share
   it). Each card shows five scan lines and the database text of the lines above and below. The student types the
   missing line, downloads their work as a JSON file (`format: poinsot-blank-lines/1`, edits keyed `p###-l##`), and can
   reload a partial file to continue. The card list is in `CodeAndDocs/data/blank_line_transcription_cards.json` and
   the page template in `CodeAndDocs/transcription_page/template.html`. To apply: check each transcription against the
   scan, then add it to `restored_lines.tsv` (page, line, the source line it follows, text, evidence). Some may
   continue the entry above rather than start a new one; in that case join them through `line_wraps.tsv` or a text
   correction. Pages: 23, 77, 90, 126, 164, 293, 315, 317, 341, 342, 346, 356, 358, 359, 363, 365, 366, 371–373, 375,
   377, 379, 380, 383–385, 455, 460, 469, 480, 489, 491, 507, 514, 517, 519–522, 529, 530, 572.
2. **25 lines where a dialect marker shares a `；` piece with Amis forms or examples**, so the scope rule doesn't settle
   which words it marks. The build applies the scope rule as written, which may be wrong for these. Source lines
   (`pourrias-poinsot.txt`): 9058, 10491, 10649, 11394, 11960, 12258, 12279, 12453, 12542, 12550, 12564, 13375,
   14276, 15332, 15352, 15498, 15581, 15585, 15687, 15773, 16002, 16231, 16861, 17023, 17567. To decide one, record
   it in `marker_scope.tsv` (`accepted`), or give its result in `card_rulings.json` (`corrected`). The two failing
   tests then pass.
3. **30 lines with Amis text inside a Chinese translation**, often a whole Amis sentence the parser didn't recognise as
   an example. Until decided, each run is cut from the Chinese and kept in a note `source text: …`. They are listed in
   `latin_runs.tsv` with class `amis-in-chinese`. Source lines: 103, 1368, 3234, 3370, 3766, 4514, 4662, 4775, 4898,
   5238, 5311, 5869, 9909, 11034, 11145, 11961, 12053, 12971, 13154, 13885, 13987, 14260, 14574, 15083, 15478,
   15881, 16607, 16756, 16886, 17254. Per line, decide whether the run stays in the Chinese (class `keep`), becomes an
   example (`card_rulings.json`), or stays a note (class `note`).
4. **Line 4827** (`hakowa = hacowa：很多 …`) starts on the same printed line (p.157 l.24) where line 4826 ends. It looks like
   a real separate entry printed on the same line, but this hasn't been checked against the scan.
5. **Line 8651** (`ldi’ - {N} = di’i：睡在別人旁邊 Ido = rdo：滿的；…`): `Ido` sits among `l`-words under the head `ldi’`,
   so the book may print `ldo` (a typed capital I for a lowercase l). Kept as typed; not checked against the scan.

## Files

Everything the build needs is under `CodeAndDocs/`:

- `generate_xml.sh`: the entry point (above). `refresh_source.sh` and `fetch_sources.py`: re-pull the pinned sources.
- `build_amis_chinese_xml.py`: the corpus-local build of the original tier.
- `source/`: `pourrias-poinsot.txt` and `toufu.sq3`, the two build inputs.
- `data/`: every hand decision (see "How the build reads the book"), the French pages 1–4
  (`french_pages_1_4.json`), and `french_reference_pages_1_4.json`, the old French build's pages 1–4 that the tests
  compare against (written by `snapshot_french_reference.py`, which needs the private dev repo's history).
- `data/manual_ocr/Poinsot/004.txt`: an earlier re-typing of French page 4. It is not used, and is kept because only
  pages 5–353 were ruled for deletion.
- `audit_entry_format.py`: reports entries that depart from the expected format (`data/format_audit.tsv`).
  `find_glued_entries.py`: regenerates `data/line_splits.tsv`.
- `transcription_page/`: the student transcription page for the 54 blank-marked lines (Notes and Issues, item 1).
- `tests/`: the corpus tests.
- `provenance.json`: the FormosanBank commit of the last build (POL-052).

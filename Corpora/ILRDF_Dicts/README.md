# ILRDF Dictionaries

Example sentences and headword entries for all sixteen Formosan languages,
drawn from the Council of Indigenous Peoples / Indigenous Languages Research
and Development Foundation (ILRDF) online dictionary,
<https://e-dictionary.ilrdf.org.tw/>.

Rebuilt in 2026 from committed snapshots of the ILRDF dictionary API
(retrieved 2026-05-04), keeping the sentence ids FormosanBank had already
published from its 2024 scrape.

| | Sentences | Dictionaries |
|---|---:|---:|
| Files | 16 | 16 |
| `S` records | 184,119 | 139,579 |
| `TRANSL` | 187,314 | 164,849 |
| `AUDIO` in an `S` (at most one per `S`) | 130,763 | — |
| untranscribed `AUDIO` (direct child of `TEXT`) | 1,438 | — |
| variant readings (`FORM kindOf="original" ver="alt"`) | 2,024 | 134 |

| Language | `S` (sentences) | under a main id | new (GUID id) | of which 2024-only | `AUDIO` in an `S` | untranscribed `AUDIO` | headword entries |
|---|---:|---:|---:|---:|---:|---:|---:|
| Amis | 9,037 | 5,615 | 3,422 | 4 | 6,560 | 32 | 8,444 |
| Atayal | 9,191 | 6,410 | 2,781 | 89 | 6,885 | 172 | 6,496 |
| Bunun | 12,368 | 9,022 | 3,346 | 6 | 10,444 | 59 | 7,564 |
| Kanakanavu | 8,837 | 5,647 | 3,190 | 537 | 6,609 | 160 | 4,415 |
| Kavalan | 10,647 | 8,384 | 2,263 | 138 | 9,287 | 62 | 7,291 |
| Paiwan | 7,837 | 5,424 | 2,413 | 3 | 5,812 | 81 | 6,625 |
| Puyuma | 9,631 | 7,279 | 2,352 | 36 | 8,208 | 134 | 8,636 |
| Rukai | 15,236 | 10,474 | 4,762 | 2 | 12,958 | 13 | 12,997 |
| Saaroa | 7,161 | 4,156 | 3,005 | 209 | 4,837 | 130 | 6,092 |
| Saisiyat | 9,339 | 6,211 | 3,128 | 38 | 7,600 | 93 | 6,268 |
| Sakizaya | 8,495 | 5,565 | 2,930 | 1 | 6,766 | 118 | 7,078 |
| Seediq | 7,660 | 5,495 | 2,165 | 29 | 6,115 | 43 | 5,977 |
| Thao | 9,860 | 6,660 | 3,200 | 22 | 7,658 | 127 | 5,165 |
| Truku | 29,718 | 4,762 | 24,956 | 6 | 5,810 | 24 | 32,892 |
| Tsou | 7,186 | 2,956 | 4,230 | 116 | 4,885 | 149 | 5,768 |
| Yami | 21,916 | 19,158 | 2,758 | 15 | 20,329 | 41 | 7,871 |
| **Total** | **184,119** | **113,218** | **70,901** | **1,251** | **130,763** | **1,438** | **139,579** |

"Under a main id" includes the `-opt` records split from a main sentence
(alternatives, and one `S` per recording); "2024-only" sentences are
explained below.

## Rights

**License:** CC BY-NC 4.0
**Rights source:** the Indigenous Languages Research and Development Foundation (ILRDF), which publishes these dictionaries under this licence; date not recorded in this repository; evidence: ask maintainer

The `@copyright` value was recorded without a version (`CC-BY-NC`) until
2026-10-16, when it was normalized to `CC BY-NC 4.0` under POL-042 (a value
that names no version is 4.0).

Every `TEXT` carries `copyright="CC BY-NC 4.0"`. See also
[CodeAndDocs/source_data/RIGHTS.md](CodeAndDocs/source_data/RIGHTS.md).

## What is in it

**Sentences** — `XML/<Language>/<Language>.xml`, one `<S>` per example
sentence, with the source's Chinese translation and its recordings.

**Dictionaries** — `XML/<Language>/<Language>_dictionary.xml`, one `<S>` per
headword and one `<TRANSL>` per sense; each sense after the first is a
`ver="alt"` TRANSL (POL-025). A sense's part of speech rides on that sense's
`TRANSL/@notes`. There is no `W` or `M` tier: the source carries no
morphological analysis.

**Language and dialect.** `xml:lang`, `dialect` and `glottocode` are as
FormosanBank published them before the rebuild: Amis `Xiuguluan`
(`cent2104`), Atayal `Sekolik`, Bunun `Junqun` (`sout2930`), Paiwan
`Northern`, Puyuma `Nanwang` (`nanw1237`), Rukai `Wutai` (`buda1252`),
Seediq `Tegudaya` (`teke1282`), Truku `Truku`; the other eight `unknown`.
Seediq and Truku share `xml:lang="trv"`; `dialect="Truku"` is what makes the
Truku files count as Truku.

## Ids

Sentences FormosanBank published before the rebuild keep their ids
(`Amis_0` …); sentences new in 2026 carry the source's GUID
(`Amis_20a69646-e70a-f011-bd65-00155db40116`); dictionary entries carry
`d` + GUID. A record split into several `S` keeps its id on the first and
adds `-opt`, `-opt3` … to the others (POL-028). A sentence with several
different recordings is also split this way, one `S` per recording (see
"Recordings" below); those 15,599 added ids are listed in
[CodeAndDocs/docs/recording_split_ids.csv](CodeAndDocs/docs/recording_split_ids.csv). The matching of old sentences
to the 2026 source was done once and frozen in
[CodeAndDocs/source_data/main_id_ledger.csv](CodeAndDocs/source_data/main_id_ledger.csv);
see [CodeAndDocs/docs/id_scheme.md](CodeAndDocs/docs/id_scheme.md).

Every previously published id that is no longer published, and why, is in
[CodeAndDocs/old_to_new_ids.csv](CodeAndDocs/old_to_new_ids.csv) (284 rows):
261 duplicates merged into the lowest id of their group, 4 sentences whose
printed alternatives cannot be published as one sentence, Puyuma_888
(source repair #3), and 18 sentences printed twice with one recording
(see "One recording printed for several sentences" below).

## Sentences from the 2024 scrape — 1,251

1,251 sentences FormosanBank published from its 2024 scrape are no longer in
ILRDF's current dictionary. They are kept as published then — same id,
original text, translation and recording — from a committed snapshot of that
XML ([CodeAndDocs/source_data/main_2024/](CodeAndDocs/source_data/main_2024/),
POL-035), and marked with `S/@source="ILRDF online dictionary, 2024 scrape …;
no longer in ILRDF's current dictionary"`. Their standard tier and phonology
are regenerated like every other record's.

| Amis | Atayal | Bunun | Kanakanavu | Kavalan | Paiwan | Puyuma | Rukai | Saaroa | Saisiyat | Sakizaya | Seediq | Thao | Truku | Tsou | Yami |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 89 | 6 | 537 | 138 | 3 | 36 | 2 | 209 | 38 | 1 | 29 | 22 | 6 | 116 | 15 |

## Reproducing the XML

```bash
Corpora/ILRDF_Dicts/CodeAndDocs/generate_xml.sh
```

This rebuilds everything from committed files and needs no network access and
no environment variables (`PYTHON` optionally selects the interpreter). The
shared QC tools come from the FormosanBank checkout the script sits in. The
FormosanBank commit the published XML was built against is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052).
`CodeAndDocs/validate.sh` runs the published-id audit and the corpus tests.

**POL-047 deviation:** besides the canonical steps, the build runs five
corpus-local steps — `generate_dictionary.py` (headword files),
`build_manual_edits.py` (renders `manual_edits.xml` from the reviewed repair
table), `split_alternatives.py` (source-side alternatives, after the
manual edits and before `clean_xml.py`, because the repairs must match the
unsplit text), `one_recording_per_s.py` (after the split, so that only
sentences that keep their recordings are split by recording) and
`tidy_edge_spaces.py` (after `clean_xml.py`, which turns full-width
`？！．` into ASCII and so exposes some of these spaces).

The steps, in order:

1. `generate_xml.py generate` — sentences from the snapshots; main's ids from
   the frozen ledger; main's withdrawn sentences from the 2024 snapshot;
   recordings (below); dialects from main.
2. `generate_dictionary.py` — headword entries.
3. `build_manual_edits.py`, then the shared `QC/cleaning/apply_manual_edits.py`.
4. `split_alternatives.py --apply`.
5. `one_recording_per_s.py` — one `S` per distinct recording.
6. `QC/cleaning/clean_xml.py`.
7. `tidy_edge_spaces.py` — spaces next to punctuation at the edges of a form.
8. `QC/utilities/standardize.py --remove_accents --ortho-path Orthographies/Ortho113`.
9. `QC/utilities/add_phonology.py --orthography Ortho113`.

### Phonology

Both PHON tiers are generated, never hand-edited. **The original tier is
assumed to be written in Ortho113** for all sixteen languages (maintainer,
2026-10-16), so original and standard PHON are generated from the same
Ortho113 table, with the column chosen by each file's `dialect`. To add
phonology to these files yourself, from the repository root:

```bash
python QC/utilities/standardize.py --corpora_path Corpora/ILRDF_Dicts/XML \
    --remove_accents --ortho-path Orthographies/Ortho113
python QC/utilities/add_phonology.py --corpora_path Corpora/ILRDF_Dicts/XML \
    --orthography Ortho113
```

**Full regeneration** re-scrapes the ILRDF API first; see
[CodeAndDocs/docs/reproduction.md](CodeAndDocs/docs/reproduction.md).

## Changes we make to the source

Everything below is reproducible from committed code and data. Nothing was
edited by hand.

### Source-fidelity repairs — 15 records

The ILRDF API sometimes returns material that is not Formosan text. 14 are
corrected on the **original** tier through the manual-edits mechanism
(POL-030), recorded in [CodeAndDocs/manual_edits.xml](CodeAndDocs/manual_edits.xml)
with a changelog in [CodeAndDocs/manual_edits.md](CodeAndDocs/manual_edits.md);
the reviewed table is
[CodeAndDocs/source_data/source_repairs.json](CodeAndDocs/source_data/source_repairs.json).

| Class | Records | Example |
|---|---:|---|
| Part-of-speech label standing in for a word | 5 | `u數詞u paapuhla…` → `ʉnʉmʉ paapuhla…` |
| Chinese editorial text welded onto a sentence | 8 | `…mawtu zau.這` → `…mawtu zau.` |
| Place name welded on without its parentheses | 1 | `…muntal mzai 水裏坑.` → `…muntal mzai (水裏坑).` |
| Editor note "請刪除" ("please delete") | 1 | Puyuma_888: not published; its recording is published as untranscribed audio |

**The 數詞 repairs (Saaroa).** In five Saaroa sentences the API replaced a
word containing the numeral root `nʉm` with the part-of-speech label 數詞
("numeral"), and turned the `ʉ` on either side into `u`: `u數詞u paapuhla…`.
Four repairs undo exactly that, restoring `ʉnʉmʉ`
(`ʉnʉmʉ paapuhla ualuia laihla upatu.`, `apuaʉnʉmʉ …`, `aʉnʉmʉ …`,
`tʉnʉmʉa …`). The fifth, Saaroa_3575 `kapita數詞ia`, is read as `nʉ`:
`hlaʼalua maci kapitanʉia …` (`kapitanʉ` is a Saaroa headword and appears in
16 sentences).

### Spaces next to punctuation at the edges of a form — 1,165 forms

The source often leaves a space before sentence-final punctuation
(`tukamia .`) or next to a quotation mark or bracket at the start or end of
a sentence, and a few sentences open with a stray period (`. Aiza …`).
Phonology drops punctuation, so these spaces ended up at the edge of the
PHON tier. On the original tier (the standard tier follows), the build
removes exactly that space and nothing else (maintainer, 2026-10-18:
"Revert; fix ILRDF text (Recommended)" and "Same treatment
(Recommended)"), in `CodeAndDocs/tidy_edge_spaces.py`:

| Pattern | Forms | Example |
|---|---:|---|
| space before final `.` `?` `!` | 1,136 | `… fafahiyan ako .` → `… fafahiyan ako.` |
| stray leading period | 12 | `. Aiza bunun masuaz …` → `Aiza bunun masuaz …` |
| space after an opening `"` | 7 | `" Dopohen a matayal!" …` → `"Dopohen a matayal!" …` |
| space before a closing `"` `,` `…` `-` at the end | 9 | `… mas ismut ,` → `… mas ismut,`; headword `caca -` → `caca-` |
| spaces inside a final bracket | 1 | `… a zaljum ( vava ).` → `… a zaljum (vava).` |

Every changed form, before and after, is in
[CodeAndDocs/docs/edge_space_report.csv](CodeAndDocs/docs/edge_space_report.csv)
(3 of them are headwords). No PHON value has a space at either edge.

### Recovered `?` corruption — 61 tokens

The source has lost the letter **ʉ** in places, leaving a literal `?`. Where
the intended word can be confirmed, it is restored automatically; where it
cannot, the `?` is left visible rather than guessed at. The repair applies
only to Kanakanavu, Saaroa and Tsou, and only to a `?` with a Formosan letter
on **both** sides. The candidate must already occur, intact, elsewhere in the
same language's snapshot. Of 85 candidates, **61 were repaired — every one to
ʉ** — and **24 were left unrepaired**.

### Source-side alternatives

The source packs alternative wordings into one record three ways: `=` ("same
as"), parentheses, and slashes.

- a **spelling variant** stays one record, the other spelling carried as a
  variant FORM, `kindOf="original" ver="alt"` (POL-028); `standardize.py`
  derives the matching standard variant. 2,006 in the sentence files.
- a **lexical alternative** becomes separate `<S>` records, named `-opt`,
  `-opt3` ….
- a parenthesis is kept as written when it is annotation: Chinese, a place or
  person name, a Japanese loanword in Romaji (listed in
  [CodeAndDocs/source_data/bracket_annotations.csv](CodeAndDocs/source_data/bracket_annotations.csv)),
  or a number.
- where the reading is not clear the record is not published as text; 620
  records, every one listed in
  [CodeAndDocs/docs/split_report.csv](CodeAndDocs/docs/split_report.csv).

For 73 previously published sentences the maintainer ruled on each one
(2026-10-15/16), and those rulings replace the automatic resolution:
[CodeAndDocs/source_data/alternative_rulings.json](CodeAndDocs/source_data/alternative_rulings.json).
9 are kept as printed, parentheses included (where the source prints the
alternative in both the sentence and its translation, POL-028 allows this for
ILRDF_Dicts); 35 lose the parenthesised alternative; 7 become two sentences
with the same translation; 1 becomes two sentences with their own
translations; 3 keep one sentence with a `ver="alt"` variant; 2 are published
without a translation; 4 are not published as text; and 12 Thao records are
resolved as listed there.

**Recordings of alternatives.** When the source prints alternatives in one
item, its recording is not attached to any of the resulting sentences: it is
published as untranscribed audio, an `AUDIO` that is a direct child of
`TEXT`, with `AUDIO/@source` naming the example it belongs to (maintainer
ruling 2026-10-16, ILRDF only). 486 recordings are published this way;
with the 708 replaced 2024 recordings and the 244 recordings printed for
several sentences (below), 1,438 untranscribed recordings in all.

Headword notation is left as the source writes it (`uculru(wa)` marks an
optional ending).

### Recordings

Every recording was fingerprinted once (SHA-256 and real file type, read from
the file's first bytes) and the result is frozen in
[CodeAndDocs/source_data/audio_fingerprints.tsv](CodeAndDocs/source_data/audio_fingerprints.tsv);
the build never downloads anything. The rules (maintainer rulings
2026-10-17; code in `CodeAndDocs/audio_recordings.py`):

- **One `S` per distinct recording; identical copies kept once.** The same
  sentence is often printed under several headwords, each copy with its own
  recording; byte-identical copies are published once (98,529 copies). A
  sentence with *k* different recordings becomes *k* `S` with the same text
  and translations: the first keeps the id, the others take `-opt`, `-opt3`
  … (15,599 added `S`: 8,808 `-opt`, 6,326 `-opt3`, 465 `-opt4` or higher).
- **Main's recording first.** Where FormosanBank's 2024 recording is
  byte-identical to a 2026 one, the file keeps its existing name
  (`<Language>_<n>.mp3`, with its `start`/`end`) and the `AUDIO` carries the
  2026 source URL (maintainer, 2026-10-18: "Use the 2026 URL"). Where the
  2026 source has a different usable recording, the 2026 one goes on the
  `S` under a new file name, and the 2024 recording is kept as untranscribed
  audio (maintainer, 2026-10-18: "Give replacements new names" and "add the
  recordings as untranscribed audio"): 708 recordings, with
  `AUDIO/@source` "ILRDF example <id>; FormosanBank's 2024 recording,
  replaced by a different recording in the 2026 source" (5 more were
  byte-identical copies of those and are kept once). Where the 2026 source
  has no usable recording, main's is kept. For
  Kanakanavu_2310 and Kanakanavu_5468 both are published (main's on the main
  id, the 2026 one on `-opt`; [source_data/audio_rulings.json](CodeAndDocs/source_data/audio_rulings.json)).
- **File names.** A 2026 recording is named after its `S`
  (`Bunun_1995-opt.mp3`), with the extension of its real type: 2,162 are
  WebM (`.webm`) and 16 MP4 (`.mp4`); they are not converted. A name that a
  2024 file with different content already has is never reused: the new
  recording takes `_2` (`Amis_137_2.mp3`), as the Yami same-village names
  do.
- **Yami: the village is in the file name.** The source records most Yami
  sentences in three villages. They are published as three `S`, 朗島 first
  (it keeps the id; main's recording is the 朗島 one), then 野銀, then 漁人,
  with files `<id>_<village>.<ext>` (`Yami_4596_野銀.mp3` on `Yami_4596-opt`).
  Where one sentence has two *different* recordings from the same village
  (267 files), the second is named `<id>_<village>_2.<ext>`; Yami recordings
  with no village in the source (652 files, 644 sentences) are named after
  their `S`, like the other languages (both "OK as built", maintainer,
  2026-10-18).
- **Broken recordings are dropped.** 157 2026 files are empty (all zero
  bytes, or no recognisable audio header) and 3 Paiwan files could not be
  downloaded. Where the sentence has another working recording (2026 or
  main's) that one is used; **13 sentences are left with no recording**
  (Paiwan 1, Puyuma 1, Saaroa 5, Tsou 5, Yami 1).
- **Recordings dropped by ruling.** Kanakanavu_2270, Saisiyat_1174,
  Saisiyat_4707, Saisiyat_5198 and Tsou_2810 are published with the 2026
  text and no recording ("Use only 2026 version. Drop the audio.",
  maintainer, 2026-10-16;
  [source_data/audio_rulings.json](CodeAndDocs/source_data/audio_rulings.json)).

**One recording printed for several sentences.** In 285 cases
FormosanBank's 2024 publication attached one recording (byte-identical
files, the same 2024 URL and segment) to two to four different sentences
(validate_xml.py V162). Maintainer ruling 2026-10-18 ("2026 source decides;
merge the 18"), frozen with every member in
[source_data/shared_clips.json](CodeAndDocs/source_data/shared_clips.json):

| Case | Groups | What is published |
|---|---:|---|
| near-identical or same wording (one sentence printed twice) | 18 | merged into the first id, the other reading as a `ver="alt"` FORM, translations merged, recording kept; the 18 retired ids are in `old_to_new_ids.csv` |
| different sentences; the 2026 source attaches the recording to another sentence, which already carries it | 23 | no member keeps it |
| different sentences; the 2026 source has no copy of the recording | 244 | no member keeps it; published once as untranscribed audio |

The 2026 source attaches none of these recordings to any of their members.
Where a removed recording was a sentence's second recording, its `-opt`
`S` is no longer published (10 ids; one, Kanakanavu_4483, keeps its other
recording on the base id).

Every recording that is not published, and why, is listed in
[CodeAndDocs/docs/audio_not_published.csv](CodeAndDocs/docs/audio_not_published.csv)
(99,963 rows: 98,534 identical copies, 708 2024 recordings moved to
untranscribed audio, 555 removed from sentences that shared one recording,
157 broken, 3 unreachable, 5 dropped by ruling, and 1 note where main's
recording replaced broken 2026 ones).

Hugging Face allows at most 10,000 files in one folder, so the three
largest languages (Bunun, Rukai, Yami; `sharded_languages` in the repo-root
`audio_sources.json`) are stored in 16 subfolders each, `<Lang>/<Lang>/0/`
to `<Lang>/<Lang>/f/`, chosen by the first hex digit of the SHA-256 of the
file name (`name_shard` in `QC/validation/validate_hf_audio.py`). This
replaces Rukai's earlier `batch_1/` and `batch_2/` folders ("Shard big
languages by name (Recommended)", maintainer, 2026-10-18). Files the XML
references that are not yet at their Hugging Face path are listed by
`audio_upload_manifest.py` in
[CodeAndDocs/docs/audio_upload_manifest.csv](CodeAndDocs/docs/audio_upload_manifest.csv)
(59,407 rows: 33,817 new files to upload, 4.0 GB, and 25,590 Bunun, Rukai
and Yami files already on Hugging Face under the old layout, column
`hf_old_path`, which move into the subfolders by a copy on Hugging Face).

### Excluded content

- 820 all-zero audio ids (found before the 2026 fingerprinting; the 157
  found by it are under "Recordings" above), two confirmed transcript mismatches, and both uses
  of 40 audio ids assigned to different forms in different languages
  ([source_data/audio_exclusions.json](CodeAndDocs/source_data/audio_exclusions.json)).
- Three Kanakanavu lesson numbers that are not translations, and one Saisiyat
  headword sense that is an editor note (`不小心按到，請刪除！…`)
  ([source_data/source_content_exclusions.json](CodeAndDocs/source_data/source_content_exclusions.json)).

## Notes and Issues

Each item is described in full in the section named in brackets.

- **1,251 sentences are no longer in ILRDF's current dictionary.** They are
  kept as FormosanBank published them from its 2024 scrape and carry an
  `S/@source` saying so. ["Sentences from the 2024 scrape — 1,251"]
- **24 `?` are left where the source lost a letter.** In Kanakanavu, Saaroa
  and Tsou the source sometimes has a literal `?` where **ʉ** was lost; 61
  were restored, but these 24 could not be confirmed and are left visible
  rather than guessed. ["Recovered `?` corruption — 61 tokens"]
- **1,438 recordings are published without a transcription** (as `AUDIO`
  directly under `TEXT`), including the 244 that FormosanBank's 2024
  publication had attached to several different sentences. ["Recordings"]
- **99,963 recordings are not published**; every one, and why, is in
  [CodeAndDocs/docs/audio_not_published.csv](CodeAndDocs/docs/audio_not_published.csv).
  ["Recordings", "Excluded content"]

## Code

| | |
|---|---|
| `generate_xml.sh` | the reproduction entry point (build only) |
| `validate.sh` | id audit + corpus tests |
| `generate_xml.py` | sentences; also the `ledger` and `audit` modes |
| `generate_dictionary.py` | headword entries |
| `split_alternatives.py` | source-side alternatives and the per-sentence rulings |
| `build_manual_edits.py` | renders `manual_edits.xml` from the repair table |
| `match_main_ids.py` | one-off: matched main's sentences to the 2026 source; wrote `main_id_ledger.csv` |
| `snapshot_main_xml.py` | one-off: wrote the POL-035 snapshot in `source_data/main_2024/` |
| `audio_recordings.py` | which recordings each sentence carries, and their file names |
| `one_recording_per_s.py` | build step: one `S` per distinct recording |
| `tidy_edge_spaces.py` | build step: the space next to punctuation at the start/end of an original FORM |
| `freeze_audio_fingerprints.py` | one-off: wrote `source_data/audio_fingerprints.tsv` from the fingerprinting run |
| `audio_upload_manifest.py` | lists referenced audio not yet at its Hugging Face path (`docs/audio_upload_manifest.csv`: new files, and files that only move into the sharded folders), offline, from the frozen listing; uploads nothing |
| `refresh_source.py` / `.sh` | re-scrape the API into snapshots (not part of reproduction) |
| `tests/` | `python -m pytest CodeAndDocs/tests` |

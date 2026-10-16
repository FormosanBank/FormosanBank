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
| `S` records | 168,548 | 139,579 |
| `TRANSL` | 170,673 | 164,849 |
| `AUDIO` in an `S` | 139,914 | — |
| untranscribed `AUDIO` (direct child of `TEXT`) | 493 | — |
| variant readings (`FORM kindOf="original" ver="alt"`) | 2,006 | 134 |

| Language | `S` (sentences) | under a main id | new (GUID id) | of which 2024-only | `AUDIO` in an `S` | untranscribed `AUDIO` | headword entries |
|---|---:|---:|---:|---:|---:|---:|---:|
| Amis | 8,849 | 5,430 | 3,419 | 4 | 7,192 | 0 | 8,444 |
| Atayal | 9,161 | 6,384 | 2,777 | 89 | 7,235 | 127 | 6,496 |
| Bunun | 11,971 | 8,697 | 3,274 | 6 | 10,700 | 20 | 7,564 |
| Kanakanavu | 8,717 | 5,616 | 3,101 | 538 | 6,866 | 0 | 4,415 |
| Kavalan | 10,413 | 8,209 | 2,204 | 138 | 9,624 | 5 | 7,291 |
| Paiwan | 7,764 | 5,359 | 2,405 | 3 | 6,155 | 33 | 6,625 |
| Puyuma | 9,389 | 7,066 | 2,323 | 37 | 9,052 | 7 | 8,636 |
| Rukai | 15,179 | 10,449 | 4,730 | 2 | 13,690 | 6 | 12,997 |
| Saaroa | 7,056 | 4,067 | 2,989 | 211 | 5,156 | 1 | 6,092 |
| Saisiyat | 9,080 | 6,095 | 2,985 | 38 | 8,061 | 5 | 6,268 |
| Sakizaya | 8,195 | 5,346 | 2,849 | 1 | 7,325 | 98 | 7,078 |
| Seediq | 7,560 | 5,463 | 2,097 | 29 | 6,591 | 2 | 5,977 |
| Thao | 9,593 | 6,419 | 3,174 | 22 | 7,928 | 93 | 5,165 |
| Truku | 29,608 | 4,669 | 24,939 | 6 | 6,621 | 19 | 32,892 |
| Tsou | 7,027 | 2,878 | 4,149 | 116 | 5,312 | 65 | 5,768 |
| Yami | 8,986 | 6,432 | 2,554 | 15 | 22,406 | 12 | 7,871 |
| **Total** | **168,548** | **98,579** | **69,969** | **1,255** | **139,914** | **493** | **139,579** |

"Under a main id" includes the `-opt` records split from a main sentence;
"2024-only" sentences are explained below.

## Rights

**License:** CC BY-NC 4.0
**Rights source:** the Indigenous Languages Research and Development Foundation (ILRDF), which publishes these dictionaries under this licence; date not recorded in this repository; evidence: ask maintainer

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
adds `-opt`, `-opt3` … to the others (POL-028). The matching of old sentences
to the 2026 source was done once and frozen in
[CodeAndDocs/source_data/main_id_ledger.csv](CodeAndDocs/source_data/main_id_ledger.csv);
see [CodeAndDocs/docs/id_scheme.md](CodeAndDocs/docs/id_scheme.md).

Every previously published id that is no longer published, and why, is in
[CodeAndDocs/old_to_new_ids.csv](CodeAndDocs/old_to_new_ids.csv) (266 rows):
261 duplicates merged into the lowest id of their group, 4 sentences whose
printed alternatives cannot be published as one sentence, and Puyuma_888
(source repair #3).

## Sentences from the 2024 scrape — 1,255

1,255 sentences FormosanBank published from its 2024 scrape are no longer in
ILRDF's current dictionary. They are kept as published then — same id,
original text, translation and recording — from a committed snapshot of that
XML ([CodeAndDocs/source_data/main_2024/](CodeAndDocs/source_data/main_2024/),
POL-035), and marked with `S/@source="ILRDF online dictionary, 2024 scrape …;
no longer in ILRDF's current dictionary"`. Their standard tier and phonology
are regenerated like every other record's.

| Amis | Atayal | Bunun | Kanakanavu | Kavalan | Paiwan | Puyuma | Rukai | Saaroa | Saisiyat | Sakizaya | Seediq | Thao | Truku | Tsou | Yami |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 89 | 6 | 538 | 138 | 3 | 37 | 2 | 211 | 38 | 1 | 29 | 22 | 6 | 116 | 15 |

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

**POL-047 deviation:** besides the canonical steps, the build runs three
corpus-local steps — `generate_dictionary.py` (headword files),
`build_manual_edits.py` (renders `manual_edits.xml` from the reviewed repair
table) and `split_alternatives.py` (source-side alternatives, after the
manual edits and before `clean_xml.py`, because the repairs must match the
unsplit text).

The steps, in order:

1. `generate_xml.py generate` — sentences from the snapshots; main's ids from
   the frozen ledger; main's withdrawn sentences from the 2024 snapshot;
   recordings (below); dialects from main.
2. `generate_dictionary.py` — headword entries.
3. `build_manual_edits.py`, then the shared `QC/cleaning/apply_manual_edits.py`.
4. `split_alternatives.py --apply`.
5. `QC/cleaning/clean_xml.py`.
6. `QC/utilities/standardize.py --remove_accents --ortho-path Orthographies/Ortho113`.
7. `QC/utilities/add_phonology.py --orthography Ortho113`.

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
ruling 2026-10-16, ILRDF only). 493 recordings are published this way.

Headword notation is left as the source writes it (`uculru(wa)` marks an
optional ending).

### Recordings

Each sentence uses the 2026 ILRDF recording where the 2026 source has a
usable one (`<id-of-the-2026-record>.mp3`). Where it has none — no recording
at all, an all-zero file, or one excluded in
[source_data/audio_exclusions.json](CodeAndDocs/source_data/audio_exclusions.json)
— the sentence keeps the recording FormosanBank already published
(`<Language>_<n>.mp3`, with its `start`/`end`). Where main published one
sentence twice and the 2026 record has no recording, both old recordings are
attached (an open question to the maintainer; one constant in
`generate_xml.py`).

### Excluded content

- 820 all-zero audio ids, two confirmed transcript mismatches, and both uses
  of 40 audio ids assigned to different forms in different languages
  ([source_data/audio_exclusions.json](CodeAndDocs/source_data/audio_exclusions.json)).
- Three Kanakanavu lesson numbers that are not translations, and one Saisiyat
  headword sense that is an editor note (`不小心按到，請刪除！…`)
  ([source_data/source_content_exclusions.json](CodeAndDocs/source_data/source_content_exclusions.json)).

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
| `audio_upload_manifest.py` | lists referenced audio missing from Hugging Face (`docs/audio_upload_manifest.csv`); uploads nothing |
| `refresh_source.py` / `.sh` | re-scrape the API into snapshots (not part of reproduction) |
| `tests/` | `python -m pytest CodeAndDocs/tests` |

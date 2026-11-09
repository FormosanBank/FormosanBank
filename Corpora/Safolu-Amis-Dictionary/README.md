# Safolu Amis Dictionary

The Safolu Amis Dictionary is a collection of 50,322 Amis example sentences with Mandarin (Chinese) translations, drawn from the dictionary compiled by Safolu Kacaw Lalanges / Tsai Chung-Han (蔡中涵). The data comes from the generated JSON of the [g0v Amis Moedict](https://github.com/g0v/amis-moedict) project (`docs/s`; see [amis.moedict.tw](https://amis.moedict.tw/)), checked against the dictionary's printed text.
Safolu Kacaw Lalanges (Tsai Chung-Han) dictionary examples, distributed by
the g0v Amis Moedict project. Virginia Fey and Poinsot are separate corpora.

## Languages and dialects

Amis (`ami`), Coastal provenance. The corpus is one file,
[XML/Amis/Safolu/amis_safolu_examples.xml](XML/Amis/Safolu/amis_safolu_examples.xml),
whose `TEXT` carries `xml:lang="ami"`, `glottocode="amis1246"` and
`dialect="Coastal"`.

`Coastal` is a source-provenance label: it records the author's documented
community (Madawdaw, Chenggong) and its language variety, not a dialect
classification of each of the 49,000-plus examples. The evidence is in
[docs/dialect_evidence.md](docs/dialect_evidence.md).

## Source

Each sentence carries the source text (`original` tier), a copy in the FormosanBank standard orthography (`standard` tier, Ortho113), and an IPA transcription of each. The corpus stops at the sentence level: it has no audio and no word or morpheme segmentation, because the dictionary's examples carry none.
No source W/M annotation or audio.

[The source manifest](CodeAndDocs/source_manifest.json) identifies the pinned
`g0v/amis-moedict` `docs/s` input: 42,273 lexical files, 57,361 definitions and
49,419 example fields. The committed compressed snapshot retains each complete
raw example, definition, title and stable source locator. The examples the
dictionary editors added upstream after that snapshot are held, in the same raw
form, in [CodeAndDocs/upstream_additions.json](CodeAndDocs/upstream_additions.json)
(914 examples at `g0v/amis-moedict` commit `4cb82539d`). The g0v project
files every example in `docs/s` under 蔡中涵大辭典 (Tsai Chung-Han's dictionary),
including the examples its dictionary editors have added since the 2022 import,
and this corpus follows that labelling. Headwords and
definitions provide context; there is no word segmentation or glossing, so the
corpus has no W or M tier.

The build emits 50,444 records: 49,522 from the 49,419 snapshot fields (20 fields
are excluded and recorded; some fields yield two sentences), 4 examples added
from the printed book, and 918 from the editors' 914 added examples (1 is
excluded and recorded; some yield two sentences). Shared dictionary dedup then
removes 122 exact duplicates, leaving **50,322 sentences**. Published ids stay fixed; a second
reading of a source example keeps the base id and adds `-opt`, `-opt3`, etc.

#### Audio

None.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Safolu-Amis-Dictionary_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

Tsai, Chung-Han (Safolu Kacaw Lalanges). (n.d.). *Amis dictionary*. Provided to the g0v Amis Moedict project. https://amis.moedict.tw/

## License

**License:** CC BY-NC-SA 3.0 TW
**Rights source:** Tsai Chung-Han (蔡中涵), date not recorded in this repository; evidence: ask maintainer

**CC BY-NC-SA 3.0 TW**, the licence as granted by Tsai Chung-Han; the grant is held in FormosanBank's records.

The licence is the version as granted (CC BY-NC-SA 3.0 Taiwan), kept as granted
by maintainer ruling 2026-10-16 rather than mapped to 4.0 (POL-042). Until
2026-10-16 each `TEXT/@copyright` held the prose "CC BY-NC according to the
frozen amis-safolu README; current data source is g0v/amis-moedict docs/s.";
POL-042 allows only a vocabulary value there, so that statement is preserved
here. The grant itself (CC BY-NC-SA 3.0 Taiwan, from Tsai Chung-Han) is held in
FormosanBank's records; ask the maintainer for it. For comparison, the frozen
[miaoski/amis-safolu](https://github.com/miaoski/amis-safolu) README's licence line
reads 蔡中涵委員 g0v 阿美語萌典計劃使用本字典，以 CC BY-NC 授權宣告。 (CC BY-NC, no version);
the grant held by FormosanBank is the authority.

The frozen upstream README says CC BY-NC without a version. The
[publisher README](https://github.com/g0v/amis-moedict-new/blob/20d9718b362e046c8a79454d3710efa4fe404afe/README.md#license-授權)
identifies Tsai Chung-Han's dictionary as CC BY-NC-SA 3.0 TW and links his
[signed licence deed](https://drive.google.com/file/d/1IQykXGWtaWAL0pH0xlE0pi5My0Onlji2/view),
which names that licence. Its printed footer says 2015/4/9; this does not establish
the signature or grant date.

## Notes and caveats

- **204 sentences follow the dictionary editors' later revision, not the
  printed book** (see "Upstream editors' edits" under
  [Per-sentence decisions](#per-sentence-decisions)).
- **916 sentences (`S49424`–`S50337`) are examples the dictionary editors
  added; the printed book does not have them.**
- The source history includes both PDF-to-TXT and DOCX conversion. A clean JSON
  file does not establish that it is free of earlier extraction errors.

## Reproduction and processing

The build reads a committed snapshot of the source (49,419 example fields at `g0v/amis-moedict` commit `e7c6976`, 2026-05-08) and never fetches anything. Its steps, all in the repository:

* **Parsing** into one sentence per example. Where a source field holds two readings (a parenthesised or slashed alternative), it becomes either one sentence with an alternative form or two sentences, as decided example by example in a maintainer review.
* **Per-sentence decisions** from that review (2026-10-16/17), each recorded with its reason: full translations from the printed text where the digitised source cut them short, and decisions on 48 parenthesis and slash examples.
* **The dictionary editors' later corrections.** The editors have kept revising the dictionary upstream since our snapshot. 204 of their edits are adopted (pinned at `g0v/amis-moedict` commit `4cb82539d`, 2026-10-16), so **these 204 sentences follow the editors' revision, not the printed book**. Four examples printed in the book but missing from the source are added.
* **The dictionary editors' added examples.** At the same pin the editors have added 914 examples that the printed book does not have; they are published as 916 sentences, `S49424`–`S50337` (one empty field is excluded and recorded; 2 are exact duplicates).
* **Spacing:** no space before `?` or `!`, and a space after them before the next word.
* **Standard tier** via the Church-to-Ortho113 conversion table (Coastal), and **pronunciation** from the Church orthography table.
* **Duplicates** are removed only when both the standard text and the translations are identical (122 sentences).

The [README](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/Safolu-Amis-Dictionary/README.md) gives the details, the full list of decisions, and how to reproduce the corpus.
(This page is that README; the details follow.)

### How to reproduce

```bash
bash Corpora/Safolu-Amis-Dictionary/CodeAndDocs/generate_xml.sh
```

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

From the corpus folder, with an explicit FormosanBank checkout and the corpus's
own tests:

```sh
PYTHON=python3 CodeAndDocs/generate_xml.sh /path/to/FormosanBank
FORMOSANBANK_ROOT=/path/to/FormosanBank python3 -m pytest Corpora/Safolu-Amis-Dictionary/tests
```

`generate_xml.sh` finds FormosanBank from `FORMOSANBANK_ROOT`, else its first
argument, else the checkout two folders up, else a sibling `../FormosanBank`. It
needs Python with the FormosanBank requirements, and it stops (exit 2) if
`Orthographies/Church/Amis.tsv` or
`Orthographies/ConversionTables/Amis_Church_113.tsv` is missing. There is no
`validate.sh`; the build runs no validators.

Generation, shared cleaning, standardization, PHON and dedup run in temporary
staging; only a completed build installs XML and its
[provenance record](CodeAndDocs/provenance.json) (the FormosanBank commit whose
tools built it; recorded, never used to gate a build, per POL-052). The build never
fetches a source. To refresh the source deliberately, run
`python3 CodeAndDocs/source_snapshot.py /path/to/clean/amis-moedict` and review
the new manifest and every change; overrides whose expected text no longer
matches stop the build.

**POL-047 deviation:** shared dictionary dedup runs after derived tiers.

### What each step does

In order (`CodeAndDocs/generate_xml.sh`), all inside a temporary staging folder
`CodeAndDocs/.build-XXXXXX/` that is deleted when the script exits:

1. `CodeAndDocs/generate_xml.py` parses the snapshot and applies the
   per-sentence decisions in
   [`safolu_source_overrides.json`](CodeAndDocs/safolu_source_overrides.json)
   and [`printed_additions.json`](CodeAndDocs/printed_additions.json) (below),
   then the spacing rule: no space before `?` or `!`, and a space after them
   when a letter, digit or opening quote follows. Maintainer: "There should be
   no space before a ? or a ! and there should be space between any ! or ? and a
   following Amis character."
   In detail (run as `generate_xml.py --xml-out-dir <staging>/XML`):
   - It reads `CodeAndDocs/source_examples.jsonl.gz` and refuses to run if its
     SHA-256 differs from `source_manifest.json` or if the source ordinals are
     not exactly 1 to 49,419 ([source_snapshot.py](CodeAndDocs/source_snapshot.py)).
   - Each example field is split at the Moedict markers U+FFF9 / U+FFFA /
     U+FFFB into the Amis form, a middle translation and the Chinese
     translation; Moedict link markup (`` ` `` and `~`) is removed. A middle
     translation would be published as English unless it reads `undefined`;
     the published XML has no English translation.
   - A stray `)` / `）` at the start of a form is dropped.
   - Where an override exists for the field, the cleaned form and translation
     must equal the override's `expected_cleaned_*` text or the build stops;
     the override's `emitted` list then gives the sentence(s), translation(s),
     any alternative FORMs (`ver="alt"`) and any note on the FORM (`notes`).
   - Where the form is empty, the Amis is recovered from the start of the
     Chinese field (a leading loanword note such as `(閩南語借詞)` stays with the
     translation), or from a single `` `…~ ``-marked Amis phrase inside it.
     Otherwise the field is excluded (`empty_form`).
   - Where the form contains Chinese, it is split into Amis + Chinese pairs
     (one sentence each); if it cannot be split cleanly the field is excluded
     (`cjk_in_form_unsplittable`).
   - Sentence ids are `S` + the five-digit source ordinal; ids given to extra
     sentences by earlier builds are kept from
     [legacy_expansion_ids.json](CodeAndDocs/legacy_expansion_ids.json), new
     ones get `-opt`, `-opt3`, ….
   - The 4 printed additions are appended as `S49420`–`S49423`, then the
     editors' added examples from `upstream_additions.json`, whose ordinals
     continue from 49424 (so their ids are `S49424`–`S50337`); they go through
     the same parsing, overrides and exclusions as the snapshot's fields.
   - It writes `XML/Amis/Safolu/amis_safolu_examples.xml` (original FORM and
     TRANSL only) with the `TEXT` attributes above. The excluded fields are
     written out only when `--report-dir <folder outside the repository>` is
     passed (`excluded-fields.json`); `generate_xml.sh` does not pass it.
2. `QC/cleaning/clean_xml.py` (shared cleaning: quote style, stray spaces).
   Run as `--corpora_path <staging>/XML`. It also strips zero-width
   characters, decodes leftover HTML entities, normalizes caret variants to
   `^`, converts full-width punctuation to ASCII in FORM (Chinese translations
   keep their punctuation), collapses whitespace and trims repeated `!`, `?`
   and `-`.
3. `QC/utilities/standardize.py` with `Orthographies/ConversionTables/Amis_Church_113.tsv`,
   column `Coastal`, makes the standard tier (it also turns `u` into `o` and
   `g` into `ng`).
   Alternative FORMs get a standard copy too (25 in the published XML).
4. `QC/utilities/add_phonology.py --orthography Church` writes PHON. Maintainer:
   original PHON from "Church/Amis.tsv as is — And then use the Church_113
   converter to make the standard tier."
   Original PHON comes from `Orthographies/Church/Amis.tsv`; standard PHON
   comes from the Ortho113 Amis table, column resolved from the dialect.
5. `QC/cleaning/remove_duplicate_sentences.py` removes a sentence only when its
   standard FORM **and** its translations equal another's; differing
   translations keep both sentences, as separate sentences (they are not
   merged into one as alternative translations). Maintainer: "Don't dedup based on
   the original tier. Dedup if standard tiers are identical."
   Run as `by_path --path <staging>/XML --apply` (defaults `--scope file`,
   `--tier standard`): it compares the base standard FORM (never a `ver="alt"`
   one) plus all translations, keeps the first sentence by id and deletes the
   rest (122 in this build).
6. An inline Python step writes `provenance.json` with the FormosanBank
   checkout's `git rev-parse HEAD` (without Git metadata it keeps the previous
   file and prints a warning).
7. The staged XML is copied to `XML/Amis/Safolu/amis_safolu_examples.xml` and
   the provenance to `CodeAndDocs/provenance.json`.

#### Per-sentence decisions

Every entry in `safolu_source_overrides.json` names the cleaned source text it
expects (the build stops if upstream text no longer matches) and its reason.
343 entries: 48 earlier source repairs, 288 sentences decided in the
maintainer's review (2026-10-16/17), and 7 of the editors' added examples
(2026-11-09):

- **Parentheses and slashes (48):** 41 parenthesis examples, 5 slash
  alternatives, S42869 (keeps its parenthetical in FORM and translation) and
  S07064 (two sentences). Each is kept as printed, has the parenthetical removed,
  becomes one sentence with an alternative FORM (`ver="alt"`), or becomes two
  sentences, as decided per example. Rule used for the undecided ones: "if the
  paranthetical contains a single word that differs from the previous word in
  less than 25% of it's letters AND there is no paranthetical in the
  translation, then also go with `One S + alt variant`."
- **Translations (36):** where the g0v source broke an example at an internal
  `!` or `?` (the second Amis clause landed in the Chinese field and the Chinese
  was cut), the full translation from the printed text
  ([miaoski/amis-safolu](https://github.com/miaoski/amis-safolu) `dict/*.txt`)
  is used, or the maintainer's own text.
- **Upstream editors' edits (204).** Since our snapshot (2026-05-08) the
  dictionary's editors have revised examples in `g0v/amis-moedict` (pinned here at
  `4cb82539d`, 2026-10-16). Maintainer: "Look at fixes by the editors since our
  download. See if there are any that we don't have. If so, adopt their fix."
  Edits changing at most 3 letters and 1 character were adopted; Chinese-only
  edits were adopted unless they only added a parenthetical; where both the
  Amis and the Chinese changed by 25% or more, the editors' version is published
  as a separate sentence (`-opt`) beside the original; the rest were decided one
  by one. **These 204 sentences follow the editors' revision, not the printed
  book.** List them with
  `grep -o '"reason": "Upstream editors[^"]*"' CodeAndDocs/safolu_source_overrides.json`
  (each entry's `expected_cleaned_*` fields hold the pinned text, `emitted` what
  is published).
- **Printed examples the source lacked (4):** `S49420`–`S49423` (mikapkapan,
  miparoay, miwingawingay, paro), with the editors' Chinese; each entry in
  `printed_additions.json` records where the book prints it.
- **Examples the editors added (914):** the 918 examples in `docs/s` at
  `4cb82539d` that are not in the snapshot, less the 4 that equal a printed
  addition, captured by
  [`upstream_additions.py`](CodeAndDocs/upstream_additions.py) into
  `upstream_additions.json`. Entry by entry, an example only in the snapshot is
  paired with the most similar example only at the pin (difflib ratio of Amis +
  Chinese above 0.6) and counted as an edit (above); every unpaired example at
  the pin is an addition.
  Recapture with `python3 CodeAndDocs/upstream_additions.py /path/to/clean/amis-moedict`
  (the checkout must be at `4cb82539d`).

The review itself (questions, examples and answers) is recorded in FormosanBank's
`claudeplans/sweep-qa-decision-log.md`.

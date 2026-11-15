# Chang (2000) Kavalan Reference Grammar

This corpus is the Kavalan (`ckv`) material from Chang Yung-li's 張永利 2000 *噶瑪蘭語參考語法* [Kavalan Reference
Grammar] (Yuan-Liou Publishing): 450 printed example sentences and 11 alternative readings of them, transcribed from a
scan of the book and proofread against the printed pages. Each sentence has the book's word and morpheme glosses and
its free translation, in Mandarin (`zho`).

## Languages and dialects

**Language:** Kavalan (`ckv`).

The one file, `XML/Kavalan/chang-2000-kavalan-reference-grammar.xml`, carries `xml:lang="ckv"` and
`dialect="Kavalan"` on its `TEXT` element. FormosanBank records Kavalan as a single dialect (`dialects.csv`).

## Source

Chang, Yung-li 張永利. 2000. 噶瑪蘭語參考語法 (*Gamalanyu cankao yufa*) [Kavalan Reference Grammar]. Yuan-Liou
Publishing 遠流出版事業股份有限公司. The author romanizes his name in Wade-Giles, *Chang Yung-li* (pinyin: Zhang Yongli),
and the corpus uses that form.

The source is a 122-page scan of the book, two photographed book pages to a PDF page, with no text layer. It is kept in
the private development repository and is not needed for a build. The examples were transcribed from it page by page
(`CodeAndDocs/source_units.tsv`), and a proofreader then checked every example against the book; notes that begin
`Review (2026-10):` are her comments, published verbatim.

What is published: the grammar's Kavalan examples, one sentence per example (an example printed more than once is one
sentence whose `source` attribute lists every printing; 37 sentences have more than one), each with the Kavalan line,
its Chinese translation, and a word tier (1,661 words) and morpheme tier (2,502 morphemes) from the book's gloss line.
What is not: the 277 entries of the book's basic-vocabulary list, starred (ungrammatical) examples (POL-016), and the
non-Kavalan material of the introduction (Paiwan sentences, comparative tables). `CodeAndDocs/source_coverage.tsv`
records, page by page, what each page holds and what was left out.

The book's spelling is Li Jen-kuei's symbol system for Formosan languages as used by the 台灣南島語言 series (p. 43,
note 2), FormosanBank's `TaiwanNandao` profile. The standard tier is the same text in Ortho113, which writes two
letters differently: the book's `r` (the flap) is `l`, and its `l` (the lateral fricative) is `d`.

There is no audio: the book is print only.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Kavalan-Chang-Reference-Grammar_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

Chang, Yung-li 張永利. 2000. 噶瑪蘭語參考語法 [Kavalan Reference Grammar]. Yuan-Liou Publishing 遠流出版事業股份有限公司.

The same reference as the XML's `citation` attribute gives it:

Chang, Y. (2000). Gamalanyu cankao yufa. Yuan liu chuban shiye gufen.

See the FormosanBank [Terms of Use](https://formosanbank.github.io/FormosanBank/additional-resources/terms-of-use/).

## License

**License:** CC BY-NC 4.0

**Rights source:** Henry Chang, 2024-01-07; evidence: ask maintainer

Henry Chang granted permission to publish the book's Kavalan text, translations and glosses under Creative Commons
Attribution-NonCommercial 4.0 International (CC BY-NC 4.0), with citation to the book.

## Notes and caveats

- **Handwriting.** The scanned copy has a later reader's handwritten corrections. Twelve examples follow the
  handwriting rather than the print; each says so in its note.
- **Departures from the print.** `ta-paw-an-su` (p. 181) is printed `ta=paw-an-su`; `quni-pa=isu` (pp. 119, 156,
  158, 181, 183) is printed `quni=pa=isu` and segmented here as its gloss `去哪裡-未來式=你` is; 18a's gloss
  (p. 78) is `處所格-豐濱-處所格=動貌=我` where the book prints `處所格-豐濱=動貌=我`.
- **`sa-kasaw-an`** (pp. 183, 185). The book glosses it `終點-長濱-`, in the format it uses elsewhere for a
  circumfix. However, the grammar states that `sa-` is not part of a circumfix. So it is glossed
  `終點-長濱-<UNCLEAR/>`, with the morphemes `sa` 終點, `kasaw` 長濱 and `an` `<UNCLEAR/>`.
- **The letter `o`.** This corpus has three instances of the use of the letter `o`, which appears in the Kavalan
  word for 苗栗. It is not currently known to the maintainers how this should be pronounced.

## Reproduction and processing

### How to reproduce

```bash
bash Corpora/Kavalan-Chang-Reference-Grammar/CodeAndDocs/generate_xml.sh   # the build: source -> XML/
bash Corpora/Kavalan-Chang-Reference-Grammar/CodeAndDocs/validate.sh       # the checks; reads XML/, never writes it
```

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

Both scripts find the FormosanBank checkout themselves (`CodeAndDocs/formosanbank_path.sh`: the checkout this corpus
sits in, or `FORMOSANBANK_PATH`) and run its `.venv/bin/python3` (or `FORMOSANBANK_PYTHON`). They need no network and
no private file: every input is committed under `CodeAndDocs/`. `generate_xml.sh` writes
`XML/Kavalan/chang-2000-kavalan-reference-grammar.xml`, and rewrites `CodeAndDocs/provenance.json` when the XML
changes; run twice on a clean checkout, it leaves `git status` empty. `validate.sh` writes its reports under
`qc-output/<run-id>/` (Git-ignored) and stops at the first step that fails.

### What each step does

**1. `build_xml.py`** turns the transcription into the original tier, the glosses and the translations. It reads:

- `source_units.tsv`: the transcription, one record per printed example (478 included) or vocabulary entry (277,
  kept as coverage records and not published); `source_units_additions.tsv`: 14 printed examples the transcription
  missed; `source_coverage.tsv`: its page-by-page record. The build stops unless every record says it was verified
  against the scan and the page counts agree with the records.
- `review_corrections.tsv`, `review_adjudication.tsv`, `review_log.tsv`: the proofreader's corrections, applied
  only while the transcription still says what she corrected; the places where the published result departs from
  them, each with its ruling; and her notes.
- `source_variant_decisions.tsv`: a decision for each of the 22 printed alternatives, with the gloss line and id of
  each one published as a sentence.
- `decisions_*.tsv`: the other record-level decisions, one file per kind, each row with the example or word it
  applies to and the ruling it applies (or that none exists): `word_glosses` (gloss lines that line up with the
  words), `morphemes` (morphemes written out, circumfixes, words without morphemes), `spellings` (two respellings and
  which printing two sentences take their words from), `clitics` (clitics written before their word), `notes` (notes
  added, replaced or dropped) and `song_lines` (song lines that keep a comma). A row that changes nothing stops the
  build.

What it writes, by convention:

- **Sentence ends.** A Kavalan line ends as its Chinese translation ends: `?` with `？`, `!` with `！`, otherwise
  `.` with `。`. The book's song lines (pp. 181-183), whose translation ends in `，` because the song goes on, end in
  `,` and `，` (POL-063).
- **Parentheses** are ASCII in the Kavalan and full-width in the Chinese. Parentheses that mark optional material
  are removed, and the reading without the optional piece is a sentence of its own.
- **Brackets and subscripts** the book prints in a Kavalan line (clause brackets, coreference subscripts) are left
  out of the original tier.
- **Infixes.** The sentence line and the word FORM write an infix in angle brackets (`p<um>ukun`), where the book
  prints `p-um-ukun`. Its morphemes are the root, written with a hyphen where the infix goes, and the infix
  (`p-ukun` 打, `-um-` AF); its word gloss is `打<AF>`.
- **The locative frame `ta-...-an`.** Where the book glosses it once (`處所格-苗栗-`), it is one morpheme, `ta-an`;
  where the book glosses both halves, two (`ta`, `an`).
- **Clitics** keep their `=` in the morphemes, on the clitic's own side: `pun` · `=ita`, and, for a clitic before
  its word, `qa=` · `patay`.
- **Morphemes carry no punctuation**; words and sentences keep theirs.
- **Glosses.** A trailing hyphen on a gloss is dropped where the gloss then has as many pieces as the word has
  morphemes. A word or morpheme the book leaves unglossed in a glossed sentence is glossed `<UNCLEAR/>`; the three
  sentences the book does not gloss at all have no word glosses (POL-061). A word whose printed gloss does not divide
  the way the word does (`ti-buya` 人名) has no morphemes, except the two locative pronouns of p. 96, `ti-maiku-an`
  and `ta-maiku` (glossed `我（處所）`), which are split as the book glosses `ti-maisu-an` on p. 80 (`ti` 類別詞,
  `maiku` 我, `an` 處所格).
- **Alternatives.** A one-word alternative the book prints with a slash under one gloss (`ya/a`) is a second FORM
  on that word, `ver="alt"`, with no pronunciation of its own. Any other alternative is a sentence of its own with
  its own words: a second reading takes its example's id plus `-opt`; a separate example the book prints beside
  it takes its printed label (`S-p059l-e002-b`, `S-p047l-e005-ia`). One alternative the book marks unacceptable
  (`*iku`) is left out.

**2. `clean_xml.py`** (FormosanBank's shared cleaner) normalizes characters and punctuation on the original tier. On
this corpus it changes nothing today; it runs so that a change to the shared cleaner reaches the corpus.

**3. `standardize.py`** with `Orthographies/ConversionTables/Kavalan_TaiwanNandao_113.tsv` writes the standard tier:
`r → l` and `l → d`, applied together. The standard sentence line also drops the segmentation marks `-`, `=`, `<` and
`>`.

**4. `add_phonology.py --orthography TaiwanNandao`** writes PHON: the original tier from the `TaiwanNandao` profile,
the standard tier from Ortho113. Ortho113 Kavalan has no `o`, so the three `o`s of 苗栗 are `*` in standard PHON.

**5.** `generate_xml.sh` then checks that it left the FormosanBank checkout unchanged and, if the XML changed,
records the FormosanBank commit in `provenance.json`.

#### Validation (`validate.sh`)

`build_xml.py --check` (the XML is what a fresh build gives), `audit_source.py` (the inventory and the conventions
above, checked in the output; with the scan absent it checks the tracked records only), the orthography detector, the
three FormosanBank validators, the dialect and duplicate-sentence checks, `audit_qc_findings.py` (every FormosanBank
finding must be one it expects, with its recorded reason; `qc_summary.md` lists them), the orthography and vocabulary
comparison with the Kavalan reference, and the corpus's tests (`CodeAndDocs/tests/`, including the source-accounting
test: every record is published or left out with a reason).

#### Review round trip

The Kavalan words, their glosses and the Chinese translations were read off the scan, so a reviewer checks them
against the book in a web page, and two scripts carry the corrections back:

```bash
python CodeAndDocs/export_review.py      # -> review_baseline.json + review_page.html

**Standard gloss tier** (final step): `QC/glossing/apply_gloss_standard.py` adds `TRANSL kindOf="standard"` glosses beside every original gloss (POL-036 — the original tier is never changed), converting each gloss code according to this corpus's standardization list, [Glossing/ConversionTables/Kavalan-Chang-Reference-Grammar.tsv](https://github.com/FormosanBank/FormosanBank/blob/main/Glossing/ConversionTables/Kavalan-Chang-Reference-Grammar.tsv) (segmentation conventions in [Kavalan-Chang-Reference-Grammar.rules.tsv](https://github.com/FormosanBank/FormosanBank/blob/main/Glossing/ConversionTables/Kavalan-Chang-Reference-Grammar.rules.tsv)). Codes without a ruled mapping are copied verbatim, so the standard tier is always complete; the project-wide approach, vocabulary and per-language gloss dictionaries are documented in [Glossing/README.md](https://github.com/FormosanBank/FormosanBank/blob/main/Glossing/README.md).
#   ... review_page.html is published as a claude.ai artifact; the reviewer works there ...
python CodeAndDocs/apply_review.py <downloaded.json | dumped edits/ directory>
                                         # -> review_corrections.tsv + review_log.tsv
bash CodeAndDocs/generate_xml.sh         # publishes the corrections
```

The page shows one card per printed example: the words, the gloss under each word, then the translation, exactly
as `build_xml.py` aligns them. The returned file is kept as `CodeAndDocs/kavalan-review-2026-10-30.json`.
`apply_review.py` writes `review_corrections.tsv` (one row per changed field) and `review_log.tsv` (every unit
touched); the corrections are not written back into `source_units.tsv`, which keeps recording what the transcription
read. An edit against a different baseline, or a correction whose `was` no longer matches, stops the build.

#### Inventory

- 461 S elements: 450 printed examples and 11 alternative readings
- 1,661 W and 2,502 M elements
- 4,632 original FORM elements (8 of them a word's second FORM, `ver="alt"`) and 4,624 original PHON elements
- 4,632 standard FORM and 4,624 standard PHON elements

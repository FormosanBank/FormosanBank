# Glosbe Formosan Corpus

This corpus contains Glosbe dictionary and translation-memory examples for Amis,
Atayal, Saisiyat and Truku. It has seven XML files, 5,670 S, 7,659 TRANSL,
11,340 FORM and 11,340 PHON. There is no W/M analysis or Formosan audio.
Glosbe is crowdsourced; preserving a source pair does not establish that its
translation or language label is correct. Religious/JW material predominates.

## Languages and dialects

| File | Language | `xml:lang` | `dialect` |
| --- | --- | --- | --- |
| `XML/Amis/Amis.xml` (translation memory) | Amis | `ami` | `unknown` |
| `XML/Amis/Glosbe_ami_eng_lexical.xml` (dictionary) | Amis | `ami` | `unknown` |
| `XML/Atayal/Glosbe_tay_eng_tmem.xml` (translation memory) | Atayal | `tay` | `unknown` |
| `XML/Atayal/Glosbe_tay_eng_lexical.xml` (dictionary) | Atayal | `tay` | `unknown` |
| `XML/Truku/Glosbe_trv_eng_lexical.xml` (dictionary) | Truku | `trv` | `Truku` |
| `XML/Saisiyat/Glosbe_xsy_eng_tmem.xml` (translation memory) | Saisiyat | `xsy` | `Saisiyat` |
| `XML/Saisiyat/Glosbe_xsy_eng_lexical.xml` (dictionary) | Saisiyat | `xsy` | `Saisiyat` |

The source does not record the dialect of the Amis or Atayal material, and the
files carry `dialect="unknown"`. Glosbe entries generally do not identify a
dialect, and a single file likely mixes dialects; the standardization
assumptions per language are documented in the corpus README (this page, in the
table below).

#### Standardization and phonology

Joshua's merged source-profile decisions in `c2ce265ba` and `8fe8575e3` apply:

| Language | Original profile | Conversion table / column | XML dialect |
| --- | --- | --- | --- |
| Amis | Ortho94 | `Amis_94_113.tsv` / Coastal | unknown |
| Atayal | Church | `Atayal_Church_113.tsv` / standard | unknown |
| Truku | Ortho94 | `Seediq_94_113.tsv` / Truku | Truku |
| Saisiyat | Ortho94 | `Saisiyat_94_113.tsv` / standard | Saisiyat |

Amis is f/o-dominant. The approved non-Southern columns are identical; Coastal is
an explicit conversion route, not a claim that every speaker is Coastal. Its u→o
standardization is intentional. Unknown-dialect Atayal pronunciation, and Amis
original PHON, use the supported profile defaults; Amis standard PHON uses the
Ortho113 Coastal column (`--target_column Coastal`). Standard PHON follows
Ortho113, and original PHON uses the source profile. Accents remain in originals
and follow current shared vowel-folding rules in derived tiers. Saisiyat S and s
remain distinct.

## Source

This corpus contains dictionary and translation-memory entries collected from the
crowdsourced online dictionary Glosbe, for Amis, Atayal, Saisiyat and Truku: seven
XML files with 5,670 sentences. Amis has one translation-memory file,
`XML/Amis/Amis.xml` (4,508 sentences): 2,358 with an English translation only,
1,791 with English and Traditional Chinese, and 359 with Chinese only. The other
files are the Amis, Atayal, Saisiyat and Truku dictionary entries and two small
Atayal and Saisiyat translation memories, all translated into English. Religious
(JW) material predominates in the translation memories.

The source is a frozen Glosbe crawl (captured 2026-05-14) recorded in
`CodeAndDocs/source_records.jsonl`; the Traditional Chinese translations come from
Joseph Lin's reviewed copy of the Amis–Chinese translation memory.

The frozen crawl was captured on 2026-05-14. Its 4,245 translation-memory pairs
and 1,319 dictionary candidates were checked against 1,618 cached HTML pages by
immutable Glosbe translation ID and page SHA-256. The Chinese output instead uses
Joseph Lin's reviewed Traditional Chinese witness from
[development PR #1](https://github.com/FormosanBank/Formosan-Glosbe/pull/1),
retained at `CodeAndDocs/work/reference_glosbe/amis_glosbe_traditional.xml`.
All 25 Chinese pairs in the newer crawl have reviewed counterparts. The build
performs no new Chinese conversion and never replaces the reviewed translations
with the newer Simplified Chinese scrape.

`CodeAndDocs/source_records.jsonl` freezes the source fields, source keys,
locators, hashes and assigned S IDs. The full 5,860-row Chinese witness and
historical inputs remain available for tracing repeated and typographic variants.
`CodeAndDocs/source_labels.csv` records the 753 reviewed English pairs whose
matching page, paragraph or outline labels are editorial locators. Those labels
remain in the frozen source and are published as `notes=` on the FORM and the
English TRANSL. `CodeAndDocs/source_notes.csv` moves sixteen matching
journal-citation suffixes into FORM/TRANSL notes.

There are 1,304 lexical translations in 1,155 S, including 149 alternate readings.
Twelve candidates are excluded: one numeric-only entry, nine explicit invalid
entry/cross-reference notes, and two source-language spelling references without
an English definition. The source definitions `see (the road)` and `usb` are kept.

Audio: no Formosan audio is included.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/Glosbe_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

* Glosbe. (2026). *Glosbe [language]-[translation language] dictionary and translation memory*. Cite the language pair, URL, and retrieval date recorded in the XML file used.

## License

**License:** CC BY-NC-SA 4.0

**Rights source:** Glosbe Terms and Conditions, 2024-04-17; evidence: ask maintainer

This corpus is published under the License CC BY-NC-SA 4.0, the licence under which Glosbe's terms of use make
user-uploaded content available to other users. Every `TEXT` element records
`copyright="CC BY-NC-SA 4.0"`. Glosbe content can include third-party
translation-memory sources, so users must also follow those sources' rights, as
well as the central FormosanBank
[Terms of Use](https://formosanbank.github.io/FormosanBank/additional-resources/terms-of-use/).

Joshua's 2024-04-17 decision identifies the contributor licence in clause 4.4 of
the archived terms and requires share-alike distribution. Permission to scrape is
separate from this licence. Glosbe aggregates material from third-party sources;
retain the source attribution and follow the central FormosanBank terms in
[LICENSE.md](https://github.com/FormosanBank/FormosanBank/blob/main/LICENSE.md) and
[AI-USE-ADDENDUM.md](https://github.com/FormosanBank/FormosanBank/blob/main/AI-USE-ADDENDUM.md).
Until 2026-10-17 `TEXT/@copyright` carried a prose rights notice; the maintainer
ruled the value CC BY-NC-SA 4.0 on 2026-10-15.

Joseph Lin prepared the reviewed Traditional Chinese conversion. Glosbe and its
contributors supplied the dictionary and translation-memory material.

## Notes and caveats

Because this is a crowdsourced dictionary and translation memory, the linguistic
accuracy and the rights attached to individual entries can vary. Treat entries as
leads for review rather than as expert-verified dictionary records.

Glosbe is crowdsourced and contains incorrect or incomplete translations and
language labels; religious/JW examples dominate. Amis and Atayal dialects are
unknown, and the approved Amis conversion does not resolve every o/u pronunciation.
Recorded quotation repairs preserve reviewed readings, but automatic quotation
classification can still miss errors. Distinct source spellings remain separate
even when their standard forms coincide.

* Glosbe's own pages write the Amis glottal stop as `ˈ` and quotation marks as
  `‘ ’`; FormosanBank writes the glottal stop as `'` and quotations with `"`.
  Quotation repairs are recorded hand edits (`CodeAndDocs/manual_edits.xml`,
  logged in `CodeAndDocs/quote_corrections.csv`) checked against those Glosbe
  pages; the XML as it stood before any correction is preserved in
  `CodeAndDocs/pre_correction_snapshot/`.
* Absence from ILRDF or disagreement with an ILRDF gloss is never an exclusion
  rule. Historical ILRDF comparison reports are reference evidence, not current QC
  verdicts. They concern dictionary candidates only; `trv` means Truku in that
  comparison.
* Import decisions that not everyone would agree with are made by recorded
  maintainer rulings and are described step by step under "What each step does"
  below: editorial material (scripture references, cross-references, labels,
  captions) moved out of the text into `notes=`; main's typography kept where the
  source spelling was rejected; the Amis–English and Amis–Chinese translation
  memories joined into one file; and the identifiers withdrawn as a result.

Open as of 2026-10-18 (not ruled): Amis-Chinese S that differ from an Amis-English S
by a word, a list number written "(1)" vs "1.", a slashed date or a menu symbol are
not joined. Paragraph numbers, cross-references and citations inside Chinese TRANSL
text are left as published (ruling: "Leave as is"), apart from the page-reference
copies described under step 8 below.

## Reproduction and processing

### How to reproduce

Use the current FormosanBank Python environment and shared checkout:

```bash
PYTHON=/path/to/FormosanBank/.venv/bin/python3 \
FORMOSANBANK_ROOT=/path/to/FormosanBank \
  CodeAndDocs/generate_xml.sh
```

From the FormosanBank root, with `python3` being the repository's environment,
`bash Corpora/Glosbe/CodeAndDocs/generate_xml.sh` is equivalent: `PYTHON`
defaults to `python3` and `FORMOSANBANK_ROOT` to the checkout that contains the
corpus. There is no `validate.sh`.

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).
[Build provenance](CodeAndDocs/provenance.json) records the actual shared checkout
commit without selecting or requiring that version. A Git-free export can supply
its verified revision through `FORMOSANBANK_COMMIT`; absent revision information
leaves the last reviewed provenance unchanged and prints a notice.

The entry point starts from committed source records, applies recorded edits,
cleans, removes within-file duplicates, moves editorial material to notes, replays
reviewed source aliases, restores main's typography, joins the Amis files,
standardizes with the tables above, and generates both PHON tiers. It uses no network, private sibling or
historical tools checkout. Run validation separately using the current QC tools.
Run `python -m pytest tests` from `CodeAndDocs/` with the same
`FORMOSANBANK_ROOT`; root-level tests exercise the historical acquisition code.
Cleaner and standardizer warning CSVs are disposable per-run reports; the quote
ledger is durable. Set `QC_OUTPUT_DIR` to put cleaner warnings outside the repository.
Review the full generated diff after changing any input or tool.

Final XML uses the shared registry's Amis, Atayal, Truku and Saisiyat directories
(POL-059). Frozen source locators and the pristine baseline retain their historical
ISO paths. Unexpected XML outside the declared output paths stops a rebuild.

Source refresh is separate. `CodeAndDocs/capture_source.py --dev <dev-repo>` reads
the preserved crawl and reviewed index; it never fetches. `--refresh-labels` also
replaces the editorial-label candidates and requires their source review before
use. Historical acquisition scripts and reports are retained as evidence. They
are not alternate instructions for rebuilding the current XML.

### What each step does

`CodeAndDocs/generate_xml.sh` rebuilds every XML file from those records with
the current FormosanBank tools and no network access: it applies the recorded
hand edits, runs the shared cleaner, removes within-file duplicates, moves
editorial material to notes, joins the Amis files, standardizes to Ortho113 and
generates both pronunciation (`PHON`) tiers. In summary:

* **One Amis file.** An Amis sentence that appeared in both the Amis–English and
  the Amis–Chinese translation memory is one sentence carrying both translations.
  Sentences join when their Amis text is identical, or identical apart from
  spaces, commas, periods and dashes; texts that differ by a word, a letter, an
  apostrophe or a quotation mark are kept apart.
* **Editorial material goes to notes.** Scripture references, paragraph
  cross-references, list labels, captions and journal-citation tails are in the
  `notes` attribute of the FORM or translation, not in the text; bare list
  enumerators such as `(b)` are removed.
* **Search-highlight spaces removed.** The Chinese copy was scraped from Glosbe
  search pages that pad the searched word with spaces (`" o wacay`); the build
  removes that padding.
* **Withdrawn identifiers.** Every sentence id no longer published (joined
  Amis–Chinese sentences, grouped copies, three duplicate dictionary entries) is
  listed with the id that replaces it in `CodeAndDocs/withdrawn_ids.csv`.

Where one source form has several distinct translations, the additional ones are
kept as separate `TRANSL` elements marked `ver="alt"`.

In detail, `generate_xml.sh` first checks that `QC/cleaning/clean_xml.py` exists
in the FormosanBank checkout, then runs these steps in this order. Steps 1, 4–8
and 11 are modes of the corpus script
[`CodeAndDocs/process_source.py`](CodeAndDocs/process_source.py); the others are
shared FormosanBank tools.

#### 1. Render the original tier from the frozen source

`process_source.py --formosanbank-root <FormosanBank>` reads
`CodeAndDocs/source_records.jsonl` and writes one XML file per source file. Ids
that `withdrawn_ids.csv` marks `deleted` are skipped (the build stops if one of
them is not in the frozen source). Ids listed in `keep_published_ids.csv` are
rendered from their witness copy. Each file's `TEXT` attributes are copied from
its counterpart in `CodeAndDocs/pre_correction_snapshot/`, `copyright` is set to
`CC BY-NC-SA 4.0`, and the output folder is the language name the shared registry
gives the file's `xml:lang` and `dialect`. Records sharing an S id become one S
with one original FORM; distinct translations become TRANSL elements, `ver="alt"`
after the first (the build stops if two records with one id have different source
forms). While rendering, each field is cleaned as follows.

* Asterisks: only explicitly reviewed footnote stars and three
  keyword-highlighting pairs are removed; a previously unreviewed star stops
  source capture. `CodeAndDocs/source_markers.csv` records the reviewed footnote
  and highlight roles used during source capture; it does not authorize stripping
  unreviewed markers. Literal grammaticality judgments must not be admitted by
  stripping their markers (POL-016).
* Search-highlight spaces: the parser preserves word spaces around apostrophes,
  including the 26 dictionary entries damaged by the old cleanup. Joseph's witness
  was scraped from Glosbe search pages that pad the searched word with spaces; the
  build removes that padding where it shows (`i ,`, `han ?`, `( Nengnengen`,
  `" o wacay`) (maintainer, 2026-10-18: "Fix the whole highlight-space class
  (426 S) before merge"; "No space after \"").
  [`CodeAndDocs/highlight_space_keep.csv`](CodeAndDocs/highlight_space_keep.csv)
  keeps only `'Olic 118 ,`, which the English-paired capture also prints; the 92
  spaces main had published are removed too (ruling: "Yes, remove them").
* Source labels and citation suffixes listed in `source_labels.csv` and
  `source_notes.csv` are cut from the text (the build stops if the capture hash or
  the text no longer matches); the citation suffixes go into `notes=` here, the
  labels in step 5.

Before writing, any existing `XML/Amis/Amis.xml` is deleted, and the build stops
if any other XML file is present that it would not write.

#### 2. Re-apply recorded hand edits

`QC/cleaning/apply_manual_edits.py --corpora_path XML` replays
`CodeAndDocs/manual_edits.xml`. `CodeAndDocs/manual_edits.xml` replays 194
reviewed S blocks before cleaning so fresh source builds preserve corrections
without appending the same classifier events on every run. It preserves three
repairs that the restored context otherwise defeats, separates the two quotations
in Chinese S U001443, and protects the glottal-stop letters in `ilaloma'` and
`mipaino'` from two classifier errors. Hand edits restore the space after a comma
in Amis-English U000916 and U001027 and in Amis-Chinese U000059 and U002061
(rulings: "Restore the space (manual edit)"; "Yes" + "And merge as needed").

Joshua's accepted quotation corrections are retained in
`CodeAndDocs/quote_corrections.csv`. The original pre-correction XML remains
unchanged in `CodeAndDocs/pre_correction_snapshot/` (POL-035). The complete
119-record source-typography review identifies 57 English quotation repairs;
parallel-witness and Chinese source review add 28 Chinese repairs, including
quotation/glottal boundaries missed by the classifier. It also excludes the
redundant U003118 heading whose only remaining difference is dash spacing. The
source witnesses and translations support these decisions (POL-018/025/030/050).
Quote classification can still miss quotations; neither its output nor a passing
validator establishes source quality.

#### 3. Shared cleaning

`QC/cleaning/clean_xml.py --corpora_path XML`, with `--warnings_dir
$QC_OUTPUT_DIR` when that variable is set. Shared cleaning owns Unicode typography
and quotation handling.

#### 4. Remove within-file duplicates

`process_source.py --remove-duplicates <FormosanBank>` (with `--write-ledger`
only when `GLOSBE_WRITE_MERGE_LEDGER` is set).

**POL-047 deviation:** Right after cleaning, the shared duplicate removal
(`plan_removals`/`apply_removals`, original tier, within each file) runs through a
corpus-local wrapper that honours `keep_published_ids.csv` and stops if it would
withdraw a published id that `withdrawn_ids.csv` does not list (79 are listed). It
runs before the editorial step, so it compares the texts as cleaned, not after
references move to notes. After that, the shared removal
helper applies the exact associations in `source_aliases.csv`, preserving distinct
translations as alternate readings (POL-025); standard spelling collisions do not
authorize deletion of distinct source spellings.

#### 5. Move source labels and editorial material to notes

`process_source.py --apply-rulings <FormosanBank>` first adds each
`source_labels.csv` label to the `notes=` of its S's FORM and TRANSL, then moves
editorial material in the two Amis translation-memory files.

**Editorial material goes to notes** (maintainer, 2026-10-18: "Move to notes=
(both files)"; "Consistency is good. Putting in notes is fine."). In the Amis
translation memory, the build moves out of the Amis original FORM and the English
TRANSL, into that element's `notes=`: scripture and reading references in
parentheses or after a final dash (`(Loma 8:35)`, ` -Luka 12:15.`,
` -'Osien ko Isaya 40:26.`, an English segment's leading `33:12-17) `),
paragraph/picture/box cross-references (`(Nengnengen ko saka 12 fatac)`,
`(See paragraph 12)`, `(See opening picture.)`), leading paragraph, page and list
labels (`9 `, `6, 7. (1) `, `(b) `) and a list label that opens a second question,
and the captions `(no Kowaping)` / `(no Padaka)`. In the 2026-10-18 build: 312
citations, 159 cross-references, 528 labels and 17 captions, plus the 1,457
source-label notes. A segment that is nothing but such a reference stays as text.
Years and numerals that belong to the sentence (`1943 miheca`, `17 ko mihecaan`)
stay. Chinese TRANSL text is not changed. Notes are not passed to PHON.

#### 6. Replay reviewed source aliases

`process_source.py --apply-aliases <FormosanBank>`.
`CodeAndDocs/source_aliases.csv` also accounts for 49 redundant English records
in the old proposal. These are repeated reference examples, not repeated
occurrences in a continuous story (POL-022). Distinct translations remain in one
S with `ver="alt"` after the first (POL-025). The build stops if an alias no
longer joins two S in the same file with the same original FORM.

#### 7. Restore main's typography

`process_source.py --apply-typography <FormosanBank>`.

**Main's typography is kept where the PR's was rejected** (maintainer, 2026-10-18:
dashes, dates, symbols "Reject"; ellipsis "Reject").
`CodeAndDocs/main_typography.csv` restores main's commas for source em-dashes,
`1988.11.1` dates, `,` for menu ` > `, no `®`, and `...` for `. . .` in 202 fields,
and main's text for five quotation sentences without independent evidence
(U001264, U001777, U001790, U002107, U002127; ruling: "the 5 stay as main has
them"). Each row names the exact text it replaces and the build stops if that text
has changed. [`CodeAndDocs/joined_translations.csv`](CodeAndDocs/joined_translations.csv)
rejoins five English alternative pairs into main's single "; "-joined translation
(U000011, U001000, U002829, U003827, U003922; ruling: "Join them back as main had
them"); other English alternatives stay separate `ver="alt"` TRANSL.

#### 8. Join the Amis files into one

`process_source.py --merge-translations <FormosanBank>` (with `--write-ledger`
only when `GLOSBE_WRITE_MERGE_LEDGER` is set) writes `XML/Amis/Amis.xml` and
removes `Glosbe_ami_eng_tmem.xml` and `Glosbe_ami_zho_tmem.xml`.

**One Amis translation-memory file** (maintainer, 2026-10-18: "If we have
Mandarin and English translations for the same Amis, is it one S or two? It
should be one, with both English and Mandarin translations."; "For Glosbe, I
think we can have just one file. Some Ss have translations in English, some in
Mandarin, and some in both."; on its name: "Just call it Amis.xml. Obviously fix
the citation and BibTeX as appropriate."). `XML/Amis/Amis.xml` (TEXT id
`GLOSBE_ami_TMEM`) holds 4,508 S: 2,358 with English only, 1,791 with English and
Chinese, 359 with Chinese only. An Amis-Chinese S joins an Amis-English S when
their Amis original FORMs are identical (1,800), or, failing that, equal once
spaces, commas, periods and dashes are ignored (53; ruling: "commas and periods
and dashes can be ignored"), plus one ruled join in
[`CodeAndDocs/ruled_joins.csv`](CodeAndDocs/ruled_joins.csv) (U001151 into U002332,
keeping "Faloco'"; ruling: "we clearly should join and should go with `Faloco'`
and not `Faloco` on the join"; both Glosbe pages print `Falocoˈ`). The joined S keeps the Amis-English id and FORM; the
Chinese-file FORM of a non-identical join is quoted in the ledger. Texts that
differ by an Amis word, a letter, an apostrophe or a quotation mark are not
joined (ruling: "If the two versions differ in the addition or subtraction of an
Amis word, then they are different records and should not be merged";
"Differences in ' vs \" vs curly versions of either must be discussed").
Every other Amis-Chinese S moved over with its own id. The five S reading "Oniya
lalakaw wa milengo to maanan?" are one S, U000875, with four English and two
Chinese translations ([`CodeAndDocs/grouped_sentences.csv`](CodeAndDocs/grouped_sentences.csv);
ruling: "One S (keep U000875) ... withdraw the other 4 ids -> U000875" + "But clean
up these letters: )(乙)"): the Chinese labels 乙) 丙) )(乙) are removed and the
caption reference 見課文開頭的圖片 is in that translation's notes.

The build deletes the 17 list enumerators (`(2)`, `(b)`) in the 15 fields
where main had written `2.` / `b.` (ruling: "Delete the enumerators entirely.").
The build now deletes every note part that is only an enumerator (`(x)` with one
letter or 1-2 digits, or `x.`) in every file: 229 in Amis.xml, none elsewhere
(ruling: "Delete all 212", the count left after the first 17). A Chinese
translation that only adds a page reference
(`18頁 上帝的話必萬世長存` next to `上帝的話必萬世長存`) is dropped (ruling: "One
translation, drop the page"): 18 copies; 19 `N頁` translations with no clean twin
stay. In the code the page copies are dropped first, in the joined file, and the
enumerators are deleted afterwards in every file.

**Corrections and identifiers.** **Withdrawn identifiers** (POL-037, POL-051) are
listed with the id kept in their place, the reason and the maintainer's words in
[`CodeAndDocs/withdrawn_ids.csv`](CodeAndDocs/withdrawn_ids.csv): 1,854 joined
Amis-Chinese S ids; 4 ids grouped into U000875; `GLOSBE_ami_zho_TMEM_U000046`
(-> U003882; ruling: "Withdraw (-> U003882)"; the same Glosbe record as U000012,
which joined U003882); 79 Amis-Chinese copies of a sentence that were identical to
another copy once the search-highlight spaces were removed (ruling: "Yes, remove
them (and join the 79)"; this includes U000801 -> U000669); the TEXT ids
`GLOSBE_ami_eng_TMEM` and `GLOSBE_ami_zho_TMEM` (both kept as `GLOSBE_ami_TMEM`);
and three duplicate dictionary entries deleted by ruling:
`GLOSBE_tay_eng_LEXICAL_U000030` btunux "stone" (kept U000029 btúnux),
`GLOSBE_tay_eng_LEXICAL_U000104` kayal "sky" (kept U000093 kāyal) and the Truku
`GLOSBE_trv_eng_LEXICAL_U000111` yako "I" (kept the Saisiyat
`GLOSBE_xsy_eng_LEXICAL_U000475`). The build stops if its join plan differs from
the ledger, or if `withdrawn_ids.csv` lists an id that is still published or
points to one that is not.

[`CodeAndDocs/keep_published_ids.csv`](CodeAndDocs/keep_published_ids.csv) can hold a
published id pending a ruling (rendered from its witness copy and kept out of the
alias replay, duplicate removal and the join); it is empty now.
The two new lexical S use immutable Glosbe translation IDs. Text corrections do
not renumber records or generate new identities from their spelling.

#### 9. Standardize

`QC/utilities/standardize.py` runs once per language folder with the conversion
table and column in the "Standardization and phonology" table above
(`--tsv_path Orthographies/ConversionTables/<table> --target_column <column>
--corpora_path XML/<Language>`), writing the standard FORM tier.

#### 10. Generate both PHON tiers

`QC/utilities/add_phonology.py` runs once per language folder: Amis
`--orthography Ortho94 --target_column Coastal`, Atayal `--orthography Church`,
Truku and Saisiyat `--orthography Ortho94`. `--orthography` selects the profile
for original PHON; standard PHON uses Ortho113, and `--target_column` selects its
column (otherwise it is resolved from the file's `dialect`).

#### 11. Record provenance

`process_source.py --record-provenance <FormosanBank>` writes the checkout's
`git rev-parse HEAD` (or `FORMOSANBANK_COMMIT` when there is no `.git`) to
`CodeAndDocs/provenance.json`.

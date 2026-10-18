# Glosbe Formosan Corpus

This corpus contains Glosbe dictionary and translation-memory examples for Amis,
Atayal, Saisiyat and Truku. It has seven XML files, 5,670 S, 7,677 TRANSL,
11,340 FORM and 11,340 PHON. There is no W/M analysis or Formosan audio.
Glosbe is crowdsourced; preserving a source pair does not establish that its
translation or language label is correct. Religious/JW material predominates.

## Source and coverage

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
[`CodeAndDocs/drop_enumerators.csv`](CodeAndDocs/drop_enumerators.csv) deletes the 17
list enumerators (`(2)`, `(b)`) in the 15 fields where main had written `2.` /
`b.` (ruling: "Delete the enumerators entirely.").
`CodeAndDocs/source_markers.csv` records the reviewed footnote and highlight roles
used during source capture; it does not authorize stripping unreviewed markers.

There are 1,307 lexical translations in 1,158 S, including 149 alternate readings.
Twelve candidates are excluded: one numeric-only entry, nine explicit invalid
entry/cross-reference notes, and two source-language spelling references without
an English definition. The source definitions `see (the road)` and `usb` are kept.
Absence from ILRDF or disagreement with an ILRDF gloss is never an exclusion rule.
Historical ILRDF comparison reports are reference evidence, not current QC verdicts.
They concern dictionary candidates only; `trv` means Truku in that comparison.

## Corrections and identifiers

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

**Withdrawn identifiers** (POL-037, POL-051) are listed with the id kept in their
place, the reason and the maintainer's words in
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
the ledger.

[`CodeAndDocs/keep_published_ids.csv`](CodeAndDocs/keep_published_ids.csv) can hold a
published id pending a ruling (rendered from its witness copy and kept out of the
alias replay, duplicate removal and the join); it is empty now.
`CodeAndDocs/source_aliases.csv` also
accounts for 49 redundant English records in the old proposal. These are repeated
reference examples, not repeated occurrences in a continuous story (POL-022).
Distinct translations remain in one S with `ver="alt"` after the first (POL-025).
The two new lexical S use immutable Glosbe translation IDs. Text corrections do
not renumber records or generate new identities from their spelling.

The parser preserves word spaces around apostrophes, including the 26 dictionary
entries damaged by the old cleanup. Joseph's witness was scraped from Glosbe search
pages that pad the searched word with spaces; the build removes that padding where
it shows (`i ,`, `han ?`, `( Nengnengen`, `" o wacay`) (maintainer, 2026-10-18:
"Fix the whole highlight-space class (426 S) before merge"; "No space after \"").
[`CodeAndDocs/highlight_space_keep.csv`](CodeAndDocs/highlight_space_keep.csv)
keeps only `'Olic 118 ,`, which the English-paired capture also prints; the 92
spaces main had published are removed too (ruling: "Yes, remove them"). Hand edits
restore the space after a comma in Amis-English U000916 and U001027 and in
Amis-Chinese U000059 and U002061 (rulings: "Restore the space (manual edit)";
"Yes" + "And merge as needed"). Shared cleaning owns Unicode typography and quotation handling.
Only explicitly reviewed footnote stars and three keyword-highlighting pairs are
removed; a previously unreviewed star stops source capture. Literal grammaticality
judgments must not be admitted by stripping their markers (POL-016).

Joshua's accepted quotation corrections are retained in
`CodeAndDocs/quote_corrections.csv`. The original pre-correction XML remains
unchanged in `CodeAndDocs/pre_correction_snapshot/` (POL-035).
`CodeAndDocs/manual_edits.xml` replays 194 reviewed S blocks before cleaning so
fresh source builds preserve corrections without appending the same classifier
events on every run. It preserves three repairs that the restored context otherwise
defeats, separates the two quotations in Chinese S U001443,
and protects the glottal-stop letters in `ilaloma'` and `mipaino'` from two
classifier errors. The complete 119-record source-typography review identifies
57 English quotation repairs; parallel-witness and Chinese source review add
28 Chinese repairs, including
quotation/glottal boundaries missed by the classifier. It also excludes the redundant U003118 heading whose only
remaining difference is dash spacing. The source witnesses and translations
support these decisions (POL-018/025/030/050). Quote classification can still miss
quotations; neither its output nor a passing validator establishes source quality.

## Standardization and phonology

Joshua's merged source-profile decisions in `c2ce265ba` and `8fe8575e3` apply:

| Language | Original profile | Conversion table / column | XML dialect |
| --- | --- | --- | --- |
| Amis | Ortho94 | `Amis_94_113.tsv` / Coastal | unknown |
| Atayal | Church | `Atayal_Church_113.tsv` / standard | unknown |
| Truku | Ortho94 | `Seediq_94_113.tsv` / Truku | Truku |
| Saisiyat | Ortho94 | `Saisiyat_94_113.tsv` / standard | Saisiyat |

Amis is f/o-dominant. The approved non-Southern columns are identical; Coastal is
an explicit conversion route, not a claim that every speaker is Coastal. Its u→o
standardization is intentional. Unknown-dialect Amis and Atayal pronunciation uses
the supported profile defaults. Standard PHON follows Ortho113, and original PHON
uses the source profile. Accents remain in originals and follow current shared
vowel-folding rules in derived tiers. Saisiyat S and s remain distinct.

## Audio

No Formosan audio is included.

## Notes and Issues

Glosbe is crowdsourced and contains incorrect or incomplete translations and
language labels; religious/JW examples dominate. Amis and Atayal dialects are
unknown, and the approved Amis conversion does not resolve every o/u pronunciation.
Recorded quotation repairs preserve reviewed readings, but automatic quotation
classification can still miss errors. Distinct source spellings remain separate
even when their standard forms coincide.

Open as of 2026-10-18 (not ruled): Amis-Chinese S that differ from an Amis-English S
by a word, a list number written "(1)" vs "1.", a slashed date or a menu symbol are
not joined. Paragraph numbers, cross-references and citations inside Chinese TRANSL
text are left as published (ruling: "Leave as is"), e.g. the joined U002332 has
Chinese "16頁 用上帝的律法和原則鍛煉良心" and the alternative without "16頁".

## Reproduction

Use the current FormosanBank Python environment and shared checkout:

```bash
PYTHON=/path/to/FormosanBank/.venv/bin/python3 \
FORMOSANBANK_ROOT=/path/to/FormosanBank \
  CodeAndDocs/generate_xml.sh
```

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

**POL-047 deviation:** Right after cleaning, the shared duplicate removal
(`plan_removals`/`apply_removals`, original tier, within each file) runs through a
corpus-local wrapper that honours `keep_published_ids.csv` and stops if it would
withdraw a published id that `withdrawn_ids.csv` does not list (79 are listed). It
runs before the editorial step, so it compares the texts as cleaned, not after
references move to notes. After that, the shared removal
helper applies the exact associations in `source_aliases.csv`, preserving distinct
translations as alternate readings (POL-025); standard spelling collisions do not
authorize deletion of distinct source spellings.

[Build provenance](CodeAndDocs/provenance.json) records the actual shared checkout
commit without selecting or requiring that version. A Git-free export can supply
its verified revision through `FORMOSANBANK_COMMIT`; absent revision information
leaves the last reviewed provenance unchanged and prints a notice.

Source refresh is separate. `CodeAndDocs/capture_source.py --dev <dev-repo>` reads
the preserved crawl and reviewed index; it never fetches. `--refresh-labels` also
replaces the editorial-label candidates and requires their source review before
use. Historical acquisition scripts and reports are retained as evidence. They
are not alternate instructions for rebuilding the current XML.

## Rights

**License:** CC BY-NC-SA 4.0

**Rights source:** Glosbe Terms and Conditions, 2024-04-17; evidence: ask maintainer

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

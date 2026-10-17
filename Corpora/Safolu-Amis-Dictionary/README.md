# Safolu Amis dictionary

Safolu Kacaw Lalanges (Tsai Chung-Han) dictionary examples, distributed by
the g0v Amis Moedict project. Amis (`ami`), Coastal provenance; no source W/M
annotation or audio. Virginia Fey and Poinsot are separate corpora.

**Status:** rebuilt 2026-10-17 from the pinned source with every decision from the
maintainer's Safolu review applied (PR #157). Two rebuilds are byte-identical;
validate_xml, validate_text and validate_glosses report 0 HARD findings.

[Basecamp card](https://app.basecamp.com/3340659/buckets/31258415/card_tables/cards/7112980917)
and [corpus PR #157](https://github.com/FormosanBank/FormosanBank/pull/157).

## Rights

**License:** CC BY-NC-SA 3.0 TW
**Rights source:** Tsai Chung-Han (蔡中涵), date not recorded in this repository; evidence: ask maintainer

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

## Source and coverage

[The source manifest](CodeAndDocs/source_manifest.json) identifies the pinned
`g0v/amis-moedict` `docs/s` input: 42,273 lexical files, 57,361 definitions and
49,419 example fields. The committed compressed snapshot retains each complete
raw example, definition, title and stable source locator. Headwords and
definitions provide context; there is no word segmentation or glossing, so the
corpus has no W or M tier.

The build emits 49,526 records: 49,522 from the 49,419 source fields (20 fields
are excluded and recorded; some fields yield two sentences) plus 4 examples
added from the printed book. Shared dictionary dedup then removes 120 exact
duplicates, leaving **49,406 sentences**. Published ids stay fixed; a second
reading of a source example keeps the base id and adds `-opt`, `-opt3`, etc.

## Processing

In order (`CodeAndDocs/generate_xml.sh`):

1. `CodeAndDocs/generate_xml.py` parses the snapshot and applies the
   per-sentence decisions in
   [`safolu_source_overrides.json`](CodeAndDocs/safolu_source_overrides.json)
   and [`printed_additions.json`](CodeAndDocs/printed_additions.json) (below),
   then the spacing rule: no space before `?` or `!`, and a space after them
   when a letter, digit or opening quote follows. Maintainer: "There should be
   no space before a ? or a ! and there should be space between any ! or ? and a
   following Amis character."
2. `QC/cleaning/clean_xml.py` (shared cleaning: quote style, stray spaces).
3. `QC/utilities/standardize.py` with `Orthographies/ConversionTables/Amis_Church_113.tsv`,
   column `Coastal`, makes the standard tier (it also turns `u` into `o` and
   `g` into `ng`).
4. `QC/utilities/add_phonology.py --orthography Church` writes PHON. Maintainer:
   original PHON from "Church/Amis.tsv as is — And then use the Church_113
   converter to make the standard tier."
5. `QC/cleaning/remove_duplicate_sentences.py` removes a sentence only when its
   standard FORM **and** its translations equal another's; differing
   translations would be kept as alternatives. Maintainer: "Don't dedup based on
   the original tier. Dedup if standard tiers are identical."

### Per-sentence decisions

Every entry in `safolu_source_overrides.json` names the cleaned source text it
expects (the build stops if upstream text no longer matches) and its reason.
336 entries: 48 earlier source repairs, and 288 sentences decided in the
maintainer's review (2026-10-16/17):

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

The review itself (questions, examples and answers) is recorded in FormosanBank's
`claudeplans/sweep-qa-decision-log.md`.

## Changes from the previous release

Compared with the previously published file (49,181 sentences):

- **Removed (4):** S00401, S00623, S00692, S00869, exact duplicates of other
  sentences under the standard-tier rule.
- **Added (229):** 142 source examples the old build had lost (140 were merged
  into another sentence with the same FORM, often with a different meaning; 2
  were dropped), 83 second readings (`-opt`), and the 4 printed examples.
- **Changed:** 164 original FORMs and 128 translations (the decisions above and
  the source repairs); 25 sentences have an alternative FORM and 7 an
  alternative translation. PHON is regenerated from the Church table.

## Reproduction

```sh
PYTHON=python3 CodeAndDocs/generate_xml.sh /path/to/FormosanBank
FORMOSANBANK_ROOT=/path/to/FormosanBank python3 -m pytest Corpora/Safolu-Amis-Dictionary/tests
```

Generation, shared cleaning, standardization, PHON and dedup run in temporary
staging; only a completed build installs XML and provenance. The build never
fetches a source. To refresh the source deliberately, run
`python3 CodeAndDocs/source_snapshot.py /path/to/clean/amis-moedict` and review
the new manifest and every change; overrides whose expected text no longer
matches stop the build.

**POL-047 deviation:** shared dictionary dedup runs after derived tiers.

## Audio

None.

## Notes and Issues

- Source field 35128 still contains an unexplained `久` on the publisher's page
  and stays excluded.
- The upstream editors have also added about 900 examples that are not in the
  printed book. They are not included.
- The source history includes both PDF-to-TXT and DOCX conversion. A clean JSON
  file does not establish that it is free of earlier extraction errors.

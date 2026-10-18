# Yedda Palemeq Blog

Southern Paiwan examples from Yedda Palemeq's public "Paiwan Every Day" blog
posts, with English translations, prose word explanations, and recordings. The
source is [Yedda Palemeq's blog](https://yeddapalemeq.blogspot.com/).

**Many sentences are segmented into morphemes, but nothing is glossed at the
morpheme level.** The `M` tier records the author's own segmentation; it carries
no translations, and never has. Word-level glosses are prose explanations rather
than interlinear glosses. See "Reading the tiers" below before using either
tier.

## Languages and dialects

- Language: Paiwan, ISO 639-3 `pwn`
- Dialect: Southern
- XML: `XML/Paiwan/Paiwan_Yedda_Blog.xml`

The corpus is one XML file. Its `TEXT` element declares `xml:lang="pwn"` and
`dialect="Southern"`.

## Source

#### Overview

Yedda Palemeq, a Paiwan speaker and linguist, maintained a
[blog](https://yeddapalemeq.blogspot.com/) with short Southern Paiwan examples,
English translations, prose word explanations, and recordings. The corpus
contains 668 source records represented as 671 sentences after three
source-defined alternative splits. Some examples also occur in independently
sourced FormosanBank collections; they are retained here with their blog
provenance.

**Many sentences are segmented into morphemes, but nothing is glossed at the morpheme level.** The `<M>` tier records the author's own segmentation and carries no translations — it never has. Word-level glosses are prose explanations rather than interlinear glosses. See *Corpus Notes* below before using either tier.

#### Corpus inventory

- 668 frozen source records
- 671 canonical sentence records after three source-defined alternative splits
- 5,643 W elements and 6,492 M elements
- 5,585 TRANSL elements
- 665 AUDIO references
- Canonical XML SHA-256:
  `0ede251235c455644e540aa67e32df5e3f8fcb68925ac85ef776f20c5be2b43f`

The original transcription uses the established Yedda Ortho113 route. The
standard FORM tier is derived from the original tier, and both PHON tiers are
regenerated with the current FormosanBank tooling (the commit last used is
recorded in [CodeAndDocs/provenance.json](CodeAndDocs/provenance.json)).

#### Source coverage

The corpus targets the author's numbered "Paiwan Every Day" series, not the
whole blog. Three numbers to keep apart:

- **846** — every post in the live Blogger feed, including essays,
  announcements, and other non-series posts. The 2026-08-23 audit fetched all
  of them in order to *locate* the corpus's source URLs, not to add them.
- **668** — the frozen source records this corpus is built from, drawn from
  641 distinct post URLs. Every one of them was matched against the live feed;
  none is omitted from the build. This is what `source_records_omitted: 0` in
  the manifest means, and it is a statement about the snapshot, not the blog.
- **662** — the series numbers actually represented. Six are absent:
  **66, 183, 197, 480, 519, and 543.** They have been absent since the corpus
  was first added and no record says why; they may be posts an early scrape
  missed, or numbers the author skipped. Anyone treating this corpus as a
  complete run of the series should check those six against the live blog.

One record, `Sunknown_1`, comes from a series post whose slug carries no number.

#### Source reconciliation

The frozen source snapshot contains every one of the 668 source records used by
the builder — see "Source coverage" above for what those 668 do and do not
cover of the blog.

The source-defined alternatives in `S24_1`, `S483_1`, and `S535_1` are
represented as six explicit records: the source prints `qali/drava`,
`tjangtjang / siyak`, and `abar (yasi)` as alternative wordings of one
sentence, and each pair becomes an `_1` and an `_1b` record carrying the same
translation. **Their three recordings are omitted from the corpus**, because in
each the author pronounces both alternatives in turn — as audio for either
single record it would be wrong, and as audio for a sentence containing both it
would be ungrammatical. FormosanBank does not carry ungrammatical sentences, so
the recording is dropped rather than the sentence being kept in its
both-alternatives form. The three files stay available as declared extras of
the public audio dataset (see "Audio" below); each affected record states this
in its `FORM/@notes`.

A 2026-08-23 audit matched all 668 frozen source URLs against all 846 posts in
the live Blogger feed. It restored 24 sentence-level translation blocks and 41
exact word glosses across 31 pages. Phrase-level definitions were not assigned
to individual words, and genuinely absent word or morpheme glosses remain
absent. Two duplicate sentence groups come from separate posts with distinct
source URLs and audio.

All 671 published sentence IDs are stable against the predecessor. W and M IDs
are deterministically derived from their source sentence and reviewed
segmentation. The three alternative expansions use explicit suffixes rather
than renumbering unrelated records.

#### Audio

Run `download_audio_data.sh` from this directory to download the referenced
public YouTube audio through the central FormosanBank downloader. Downloaded
audio is not tracked. The 665 referenced files total 4,217.7 seconds; the three
shared alternative recordings are declared public dataset extras and excluded
from corpus totals.

## Statistics

The table of word counts, audio, translations and glossing is generated from
`statistics/YeddaPalemeqBlog_corpora_stats.csv` and appears on this corpus's page
on the [FormosanBank site](https://formosanbank.github.io/FormosanBank/).

## How to cite

If you use this corpus, or anything derived from it, in a publication, cite both
FormosanBank and:

> Palemeq, Y. (2021). Yedda Palemeq. Retrieved May 19, 2026, from
> https://yeddapalemeq.blogspot.com/

The XML citation is: the text above, exactly as it appears in the `citation`
attribute of the XML's `TEXT` element.

## License

**License:** CC BY-NC 4.0
**Rights source:** Yedda Palemeq (the author), date not recorded in this repository; evidence: ask maintainer

CC BY-NC 4.0, by permission of the author.

**Permission to license this material was given by the author, Yedda Palemeq.**
The corpus is distributed under CC BY-NC 4.0, which is the value recorded in
the `copyright` attribute of the XML's `TEXT` element. The blog itself does not
carry a public licence notice; the licence here rests on the author's grant,
not on anything stated on the site.

Yedda Palemeq gave FormosanBank permission to license this material. The blog
itself carries no public licence notice, so the licence rests on the author's
grant rather than on anything stated on the site.

The XML also retains the source URL, citation, and BibTeX metadata. This corpus
is subject to the central FormosanBank terms in
[LICENSE.md](../../LICENSE.md) and
[AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI use is
prohibited without prior written permission.

## Notes and caveats

#### In brief

Each item is described in full in the section named in brackets.

- **No morpheme is glossed.** All 6,492 `M` elements have no `TRANSL`; the
  blog segments words but glosses only whole words, in prose. ["Reading the
  tiers"]
- **731 of the 5,643 `W` elements have no `TRANSL`**, because the source gave
  no explanation for that word in that example; glosses are never borrowed
  from another post. ["Reading the tiers"]
- **Sixteen sentences have no `W` tier** (`S268_1`, `S269_1`,
  `S378_1`–`S381_1`, `S393_1`, `S533_1`, `S545_1`–`S545_8`): the blog prints
  them as bare phrases. ["Reading the tiers"]
- **Eight word glosses the blogger marked as unknown are `<UNCLEAR/>`**, with
  her comment moved to `notes` where there was one; one more (`S313_1W3`) is
  glossed `to find` with her explanation in `notes`. All 9 are listed in
  `CodeAndDocs/data/formosanbank_audit/unclear_gloss_review.tsv`. ["Reading
  the tiers"]
- **Infixes are escaped text, not markup** (`s&lt;em&gt;eljec-an`); a consumer
  that strips tags naively will corrupt these words. ["Reading the tiers"]
- **Six series numbers are absent: 66, 183, 197, 480, 519 and 543.** The
  corpus is not a complete run of the series. ["Source coverage"]
- **Three recordings are omitted** (`S24_1`, `S483_1`, `S535_1` and their
  `_1b` alternatives), because each recording reads both alternative
  wordings. ["Source reconciliation"]
- **The standard tier drops two Mandarin accents** in `S303_1` (`yípó` →
  `yipo`, `āyí` → `ayi`), and `S652653654_2`'s standard FORM drops the
  source's segmentation hyphens. ["Morpheme tier and standard-tier accents"]

#### Reading the tiers

What is present and what is absent in this corpus is mostly a property of the
blog, which glosses informally and inconsistently. The rules below are the ones
the scrape applied; they matter for anyone counting coverage.

**Glosses are matched within one example, never across examples.** The blog
lists word explanations under each post, but not always for every word, and
repeated words and common function words are often listed once or not at all.
The scrape matched each explanation to a word in that same example only. A
gloss from another post is never reused, because there is no guarantee it is
contextually right.

**A `W` with no `TRANSL` means the source gave no explanation for that word**,
not that the word is meaningless or that a gloss was lost. 731 of the 5,643 `W`
elements are in that position; their `FORM` is simply the word as it appears in
the example.

**The corpus is segmented but not glossed at the morpheme level. No `M`
element carries a `TRANSL`, and none ever has.** This is the single most
important thing to know before using the `M` tier. The blog analyses many words
into morphemes — writing infixes inline in angle brackets, `s<em>eljec-an`,
`p<in>a-cun-an` — and that segmentation is what the `M` tier records. But Yedda
glosses **words**, in prose, and never glosses the individual morphemes. So a
morpheme has a form and a position and nothing else: all 6,492 `M` elements have
zero translations, which is why `glossed_words` in the published statistics is
`0` while `segmented_words` is 4,475.

Segmentation and glossing are separate things here, and only the first is
present. This is a property of the source, not a gap in processing: every
version of this corpus back to its first commit has had zero morpheme glosses,
both frozen scrape snapshots have zero, and the scraper only ever attaches a
`TRANSL` to a sentence or a word — it has no code path that could produce one on
a morpheme. `validate_glosses` reports the situation as 6,492 SOFT V064
findings; they are accepted, and supplying those glosses would be original
linguistic work. Under POL-036 any gloss added later must be a *new*
`TRANSL[@kindOf="standard"]`, never a rewrite of what the source wrote.

A related consequence: `validate_glosses` also raises 274 SOFT V062, asking that
a word containing an infix carry angle-bracket (`<AV>`-style) notation in its
`TRANSL`. Yedda explains her infixes in prose instead — `S288_1W3`'s gloss says
"-em- is actor voice (AV) case marker, and -in- is undergoer voice" — so the
information is present and correct, merely written another way. V062 is a
notation difference, not missing data.

**Unknown word glosses are `<UNCLEAR/>`.** Where Yedda marks a word's meaning
as unknown, the gloss is `<TRANSL xml:lang="eng"><UNCLEAR/></TRANSL>` rather
than a literal question mark (maintainer's rulings, 2026-10-17). `build_xml.py`
does this in three ways, and lists every change in
`CodeAndDocs/data/formosanbank_audit/unclear_gloss_review.tsv` (9 rows):

- A word or morpheme gloss that is exactly `?`, `??` or `???` (also full-width
  `？`) becomes `<UNCLEAR/>`, keeping the TRANSL's attributes. One gloss:
  `S77_1W5` `nu`.
- `CodeAndDocs/gloss_to_notes.tsv` lists eight word glosses ruled one by one.
  Seven start with `?` followed by Yedda's own comment (`? I cannot find this
  word.`): the gloss becomes `<UNCLEAR/>` and the whole original text moves to
  the TRANSL's `notes` attribute (`S419_1W20`, `S425_1W4`, `S425_1W27`,
  `S427_1W7`, `S430_1W7`, `S617_1W4`, `S640_1W6`). The eighth, `S313_1W3`
  `k<ar>im`, is glossed `to find`, with the original explanation in `notes`;
  its two morphemes stay unglossed.
- `CodeAndDocs/unclear_gloss_placeholders.tsv` (header `gloss<TAB>lang`) lists
  glosses in which a `?` standing as a whole piece — bounded by `-`, `=`, `.`,
  whitespace or the ends — is a placeholder; each such `?` becomes
  `<UNCLEAR/>` and the rest of the gloss is kept. **It ships with no rows**;
  rows are added only as the maintainer rules on them. A `?` attached to a word
  (`LIG?`, `right?`, `clitic?`) is the author's own hedge and is kept as
  written.

Sentence translations are never converted, and no sentence or word `FORM` is
`<UNCLEAR/>` in this corpus, so no W or M tier is affected. The shared
pretty-printer puts a whole-gloss `<UNCLEAR/>` on its own indented line; the
surrounding whitespace is formatting only.

**Sixteen sentences carry no `W` tier at all.** The blog prints them as bare
phrase entries with no word breakdown — `S268_1`, `S269_1`, `S378_1`–`S381_1`,
`S393_1`, `S533_1` and `S545_1`–`S545_8`. There is nothing to segment, so they
have no words and no morphemes. `validate_xml` reports this as a single SOFT
V148 (POL-041) and it is accepted as source-backed.

**Where the sentence and the gloss list spell a word differently, the sentence
wins.** The blog sometimes writes a word one way in the Paiwan text and another
way in the explanation below it. The scrape treats the sentence as correct and
drops the mismatched explanation rather than attaching a gloss to a form that
does not appear.

**Infixes are written with angle brackets, escaped.** Paiwan marks several
categories with infixes, and the source writes them inline: `s<em>eljec-an`,
`p<in>a-cun-an`. Because `<em>` and `<in>` would otherwise be markup, they are
XML-escaped in the file, so a raw grep sees `s&lt;em&gt;eljec-an`. Any XML
parser returns the angle brackets as text. There are 341 escaped `<em>` and 205
escaped `<in>` in the published XML file: 322 and 190 of them in the FORM
tiers, the rest in word glosses and their `notes`. They are source notation,
not tags — a consumer that strips markup naively will corrupt these words.

#### Morpheme tier and standard-tier accents

Two corpus-wide decisions shape the tiers beyond the source reconciliation
described under "Source".

**The M tier is per-sentence consistent (POL-023).** The blog analyses some
sentences morphologically and leaves others unparsed, but the parser emitted
one M per W either way. In an unparsed sentence that M is a bare mirror of its
word, which adds no information and asserts an analysis Yedda never made.
`CodeAndDocs/scripts/fix_m_tier.py` therefore drops the M tier from the 161
sentences with no analysis at all (1,165 morphemes) and requires every W in an
analysed sentence to keep at least one M. No gloss is invented or discarded.
One consequence to know about: `standardize.py` applies its C012 hyphen step
only to sentences that still have an M tier, so a sentence stripped here keeps
any segmentation hyphen in its standard FORM.

**One sentence's two tiers differ by design.** `S652653654_2` is the only
sentence whose source text carries segmentation hyphens in running sentence
text (`seman-neka-aravac`). Per POL-014/015 those markers belong on the W and M
tiers, so `standardize.py`'s C012 step removes them from the standard tier by
rule; the original keeps the source surface. The reason is recorded as a
`notes` attribute on that sentence's **original** FORM. Nothing in this build
edits a standard FORM after `standardize.py` runs — the standard tier is
machine-owned (POL-002).

**The standard tier drops source accents.** The build runs
`standardize.py --remove_accents`, so the standard tier is the original minus
the diacritics FormosanBank treats as prosody rather than spelling — the
combining acute, breve and macron. In practice this touches only the two
Mandarin kin terms quoted in `S303_1`: `yípó` becomes `yipo`, `āyí` becomes
`ayi`. The original tier keeps the source spelling untouched in every case.

Stripping is filtered through a keep set of accented letters the language
attests as real letters, drawn from `QC/validation/reference/<Language>/`.
Paiwan attests none, so nothing here is protected and both words flatten
completely. In a language that does spell with an accented letter the outcome
differs — Puyuma's `ē`, for instance, survives untouched.

#### Corpus notes

These notes were first written for the corpus's GitBook page; they overlap with
the sections above.

**Coverage**

* The corpus covers the author's numbered "Paiwan Every Day" series, not the whole blog. The live Blogger feed holds 846 posts; the other posts are essays, announcements, and other non-series material that was never in scope.
* The corpus holds 668 source records drawn from 641 post URLs, and the 2026-08-23 live-source audit matched every one of them against the feed. Six numbers in the series are nevertheless absent — 66, 183, 197, 480, 519, and 543. They have been missing since the corpus was first added and the reason is not recorded, so treat this as very nearly, but not quite, a complete run of the series.
* The audit restored 24 incomplete or omitted sentence translations and 41 exact word glosses. Phrase-level definitions were not assigned to individual words.

**Glossing**

* Examples are not necessarily glossed word by word; repeated words and common function words are often unglossed in the source. Glosses were matched within a single example only — a gloss is never reused from another example, since it may not be contextually correct. Where no gloss can be found, the `<W>` element's `<FORM>` is just a copy of the word in the example and no `<TRANSL>` is provided.
* Sometimes the same word is spelled differently in the main text and in the glosses. We have assumed the main text is correct and the gloss is incorrect; in those cases the gloss is ignored.
* Word glosses the author marks as unknown are published as `<UNCLEAR/>` rather than a literal `?`: one gloss that is only `?` (`S77_1W5` `nu`), and seven that begin with `?` followed by the author's comment (`? I cannot find this word.`), whose full text moves to the gloss's `notes` attribute. One more, `S313_1W3` `k<ar>im`, is glossed `to find` with the author's explanation in `notes`. All nine are listed in `CodeAndDocs/data/formosanbank_audit/unclear_gloss_review.tsv`. A `?` attached to a word in a gloss (`LIG?`, `right?`) is the author's own hedge and is kept.
* **This corpus is segmented but not glossed at the morpheme level.** The author glosses *words*, in prose, and never glosses individual morphemes, so no `<M>` element carries a `<TRANSL>` — and none ever has, in any version of this corpus. A morpheme has a form and a position and nothing else. That is why "Glossed words" above reads 0 while "Morphologically segmented" reads 4,475: segmentation and glossing are separate things here and only the first is present. Supplying morpheme glosses would be original linguistic work rather than data recovery.
* Sixteen sentences carry no `<W>` tier at all — the blog prints them as bare phrase entries with no word breakdown, so there is nothing to segment. They have no words and no morphemes.

**Morpheme (`<M>`) elements**

* Where the author parsed words into segments, those segments are preserved in `<M>` elements. Within such a sentence, a word we could not find a parse for is assumed to be monomorphemic and gets a single `<M>` — which is almost certainly incorrect in some cases.
* Where the author parsed *nothing* in a sentence, that sentence carries **no `<M>` elements at all**. An earlier version of this corpus gave every word a single `<M>` mirroring the word, which asserted a monomorphemic analysis the author never made. Those mirror morphemes have been removed, so 1,165 of the 5,643 `<W>` elements now have no `<M>` child. This is why "Morphologically segmented" above counts 4,475 rather than the full word count.
* Where a word contains an infix, the author marks it inline in the word itself with angle brackets — `s<em>eljec-an`, `p<in>a-cun-an` — and that notation is what the `<M>` tier is derived from. She then explains the infix in prose in the word's gloss rather than in Leipzig `<AV>` notation, so the analysis is present but written differently from most glossed corpora.
* In short: the presence of an `<M>` tier is itself information — it tells you the author analysed that sentence. This follows the bank-wide rule that morphological analysis is scoped per sentence, not per file; see [The FormosanBank XML format](https://formosanbank.github.io/FormosanBank/the-bank-architecture/formosanbank-xml-format/) for POL-023.

**Orthography**

* The `original` tier keeps the source spelling exactly as the blog writes it. The `standard` tier is derived from it with FormosanBank's common conventions applied: source segmentation hyphens are removed (they belong on the `<W>` and `<M>` tiers), and diacritics that mark prosody rather than spelling are stripped. In this corpus that affects exactly two words — the Mandarin kin terms quoted in one sentence, where `yípó` and `āyí` become `yipo` and `ayi` in the standard tier only. Paiwan spells with no accented letter, so nothing here is protected; in a language that does, such as Puyuma with its `ē`, the letter survives.

**Notation**

* Infixes are written with angle brackets inside the word, as the source writes them: `s<em>eljec-an`, `p<in>a-cun-an`. These are XML-escaped in the file (`s&lt;em&gt;eljec-an`), so any XML parser returns them as text. They are source notation, not markup — stripping tags naively will corrupt these words.

**Alternatives, audio, and duplicates**

* Where the source offers alternative wordings of one sentence — `qali/drava`, `tjangtjang / siyak`, `abar (yasi)` — each alternative becomes its own sentence record. The recordings for those three are excluded from the corpus: the author pronounces both alternatives in turn, which is not a recording of either single sentence and would be an ungrammatical utterance of the combined one. The files remain available as declared extras of the public audio dataset.
* Two duplicate sentence groups come from separate blog posts with distinct source URLs and audio, so both attestations are retained.

## Reproduction and processing

### How to reproduce

```bash
bash Corpora/YeddaPalemeqBlog/CodeAndDocs/generate_xml.sh
```

The FormosanBank commit the published XML was last built with is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052; provenance
only, a rebuild always runs the current tools).

The corpus XML and retained processing code are available
[in FormosanBank](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/YeddaPalemeqBlog).
`CodeAndDocs/generate_xml.sh` (with the scripts in `CodeAndDocs/scripts/`)
rebuilds the published XML from a frozen snapshot of the scrape, with no
network access; `CodeAndDocs/validate.sh` runs the checks separately.
`CodeAndDocs/scrape/` holds the code that read the blog in the first place; the
build does not run it, and a fresh scrape of a live blog will not reproduce the
snapshot byte-for-byte.

`CodeAndDocs/` holds two separate things, and the distinction matters:

- **`CodeAndDocs/generate_xml.sh`, `CodeAndDocs/scripts/` and
  `CodeAndDocs/data/` — the reproduction path.** The frozen source snapshot,
  audit tables, builder, tests, and QC disposition. These rebuild the canonical
  XML deterministically with no network access.
- **`CodeAndDocs/scrape/` — the scrape code.** `download_html.py`,
  `analyze_blog_structure.py`, and `download_audio.py`: the scripts that
  derived the corpus from the live blog in the first place, including the
  sentence segmentation, the W tier, the gloss matching described above, and
  the hand-maintained per-post exception lists. **The build does not run
  them.** They are kept so the scrape stays inspectable and can be repeated,
  but a fresh scrape is a new observation of a live blog and will not be
  byte-identical to the frozen snapshot. See
  [CodeAndDocs/scrape/README.md](CodeAndDocs/scrape/README.md).

Reproducing the published corpus therefore means rebuilding from the frozen
snapshot, not re-scraping. The **source** is pinned — development source commit
`25ed1f1ec56584e4a3e9fc960269c72d0e892a58`. The frozen snapshot file is
verified by its SHA-256 at build time. The
**tooling is not** (POL-048): a rebuild uses the shared QC utilities from
whatever FormosanBank checkout contains this corpus, so the corpus tracks
improvements to `clean_xml.py`, `standardize.py` and `add_phonology.py` like
every other corpus. The FormosanBank commit the published `XML/` was last built
against is recorded in
[CodeAndDocs/provenance.json](CodeAndDocs/provenance.json) (POL-052);
`generate_xml.sh` rewrites that file when it runs at a different commit. It is
a record, not a gate: the build never compares against it.

From the repository root, rebuild with:

```bash
Corpora/YeddaPalemeqBlog/CodeAndDocs/generate_xml.sh
```

`PYTHON` (default `python3`) and `BUILD_LOG_DIR` (default: a fresh temp dir,
where the cleaner's warnings go) are optional. To check reproduction, run it
twice and confirm `git status --porcelain Corpora/YeddaPalemeqBlog/XML` prints
nothing.

**POL-047 deviation:** the corpus-local generator is `scripts/build_xml.py`
rather than `generate_xml.py`, and two corpus-local steps sit inside the
canonical order: `scripts/fix_m_tier.py` runs between `clean_xml.py` and
`standardize.py` (it applies POL-023 per sentence, and `standardize.py`'s C012
hyphen step depends on which sentences keep an M tier — see "Morpheme tier and
standard-tier accents" above), and `scripts/finalize_manifest.py` runs after
`add_phonology.py` to record hashes and counts of the output. No validator runs
inside the build.

Run the QC suite with:

```bash
Corpora/YeddaPalemeqBlog/CodeAndDocs/validate.sh
```

`validate.sh` runs the corpus regression tests (`CodeAndDocs/tests/`),
`scripts/verify_handoff.py`, `scripts/audit_issue_1.py --check-only`, the
shared validators (`validate_xml`, `validate_text`, `validate_glosses`,
`validate_dialect`, `validate_duplicate_sentences` on both tiers),
`orthography_detector`, `validate_port_readiness`, and finally
`scripts/adjudicate_qc.py`, which fails unless every finding matches the
reviewed inventory by exact rule counts. `PYTHON` and `OUTPUT_DIR` (default: a
fresh temp path) are optional. Twenty-three corpus regression tests cover
source hashes, source coverage, reviewed repairs, stable tier shape,
per-sentence M-tier consistency, standard-tier accent removal, unknown-gloss
`<UNCLEAR/>` handling, and canonical XML identity.

The reviewed inventory has zero structural, text, or gloss HARD findings and
9,913 SOFT finding occurrences, all source-backed — including one file-level
V148 recording that 16 sentences are bare phrase entries the blog never broke
into words. It was first reviewed on 2026-09-04 (`CodeAndDocs/QC_STATUS.md`).
Run on 2026-10-18 with the tools at the commit in `provenance.json`, the
validators still report zero HARD findings, but four SOFT rules newer than that
review report 72 findings the inventory does not list (V135 ×69, V153 ×1,
V158 ×1, V163 ×1),
and port readiness reports one P004 warning (the development source commit
named above is not reachable in this repository, which is expected: dev repos
are private); `adjudicate_qc.py` therefore stops at its first check. Those findings
have not been reviewed.

### What each step does

`generate_xml.sh` is the entry point. It runs `scripts/build_xml.py` (frozen
snapshot → original tier),
`QC/cleaning/clean_xml.py`, `scripts/fix_m_tier.py`,
`QC/utilities/standardize.py --remove_accents`,
`QC/utilities/add_phonology.py --orthography Ortho113`, and
`scripts/finalize_manifest.py` (writes the output hashes and counts to
`CodeAndDocs/data/formosanbank_audit/manifest.json`). It stops at the first
command that fails (`set -euo pipefail`). Step by step, in the order it runs
them:

1. **`scripts/build_xml.py`** (no flags) builds the original tier from the
   frozen snapshot `CodeAndDocs/data/source_snapshot/Paiwan_Yedda_Blog.xml`:
   - It refuses to run unless the snapshot's SHA-256 is
     `e18d0aa67893278cb7754e9725e68a81075760961391b3db941eca7d873ddba6` and it
     holds exactly 668 distinct sentence IDs.
   - It deletes every `PHON` and every `FORM kindOf="standard"` the snapshot
     carries; the later shared steps regenerate them.
   - It splits `S24_1`, `S483_1` and `S535_1` into `_1` and `_1b` records (one
     per alternative), removes their audio, rewrites the original FORM of each,
     drops the word for the other alternative (for `S24_1`, rewrites word 5 and
     its morpheme instead), glosses the remaining alternative word (`male
     friend`/`female friend`, `coconut tree`, `pumpkin`), and records the
     source text in `FORM/@notes`. For `S483_1`/`S483_1b` it publishes the
     source's two free translations as a main `TRANSL` and a `ver="alt"`
     `TRANSL`.
   - It checks that `S652653654_2`'s original FORM is exactly
     `pai, maya manu seman-neka-aravac tua zuma.` (the build fails otherwise)
     and writes the reason the tiers will differ into that FORM's `notes`.
   - It replaces the sentence translation of the nine sentences in its
     `ISSUE_REPAIRS` table (`S493_1`, `S491_1`, `S481_1`, `S413_1`, `S412_1`,
     `S305_1`, `S169_1`, `S159_1`, `S62_1`), keeping the frozen text in
     `notes` as `Frozen scrape target: …`.
   - It writes the 24 sentence translations of `SOURCE_TRANSLATION_REPAIRS`
     (restored or completed from the live blog), again keeping any frozen text
     in `notes`, and adds the 41 word glosses of
     `SOURCE_WORD_TRANSLATION_REPAIRS` to words that had none, with
     `notes="Restored from the live source after frozen-scrape review."`.
   - It requires exactly 671 distinct sentence IDs, indents the tree, applies
     `gloss_to_notes.tsv` (each row must match the word's form and its exact
     gloss, or the build stops), then turns whole-`?` word and morpheme glosses
     and any `unclear_gloss_placeholders.tsv` rows into `<UNCLEAR/>` (a table
     row that matches no gloss stops the build).
   - It writes `XML/Paiwan/Paiwan_Yedda_Blog.xml` and the audit tables in
     `CodeAndDocs/data/formosanbank_audit/`: `unclear_gloss_review.tsv`,
     `source_coverage.tsv`, `issue_1_review.tsv`, `source_variant_review.tsv`,
     `source_translation_review.tsv`, `source_word_translation_review.tsv` and
     `source_review_summary.md`.
2. **Manual edits:** none. The corpus has no `CodeAndDocs/manual_edits.xml`,
   and `generate_xml.sh` does not call `apply_manual_edits.py`.
3. **`QC/cleaning/clean_xml.py --corpora_path XML --warnings_dir
   $BUILD_LOG_DIR`**, the shared cleaner. It replaces non-breaking spaces,
   normalizes `TRANSL` language codes `en`/`zh` to `eng`/`zho`, normalizes the
   original-tier `FORM` text (sentence, word and morpheme) to NFC, unescapes
   HTML entities and applies the shared punctuation and Unicode clean-up,
   cleans sentence-level `TRANSL` text, and, when the language has an
   attestation list in `QC/validation/reference/`, runs the shared
   apostrophe/glottal check on the sentence-level original FORM. It writes the file back only if
   something changed. Its per-run `cleaner_warnings.csv` goes to
   `BUILD_LOG_DIR`, outside the published tree; any apostrophe it actually
   rewrites is appended to `CodeAndDocs/quote_corrections.csv` (no such file
   exists for this corpus).
4. **`scripts/fix_m_tier.py --corpora_path XML --formosanbank_root <repo>`**
   applies POL-023 per sentence. A sentence counts as analysed if some word has
   two or more `M`, or some `M`'s FORM differs from its word's FORM. In an
   analysed sentence, every word without an `M` gets one `M` copying the
   word's FORM; in any other sentence, all `M` are removed. It rewrites the
   file with the shared pretty-printer only if it changed something, and
   prints the counts.
5. **`QC/utilities/standardize.py --corpora_path XML --remove_accents`**
   writes the standard tier: a copy of the original FORM (at sentence level
   with null units removed) with the combining acute, breve and macron removed (except letters the language's reference attests; none for
   Paiwan), and the C012 step removing segmentation hyphens in sentences that
   still have an `M` tier. No conversion table is used.
6. **`QC/utilities/add_phonology.py --corpora_path XML --orthography
   Ortho113`** writes both `PHON` tiers from the original and standard FORMs
   using the Ortho113 tables in `Orthographies/`.
7. **`scripts/finalize_manifest.py`** writes
   `CodeAndDocs/data/formosanbank_audit/manifest.json`: the SHA-256 of the
   snapshot, of the XML and of each audit file, the element counts (`S`, `W`,
   `M`, `FORM`, `PHON`, `TRANSL`, `AUDIO`) and the fixed review totals. Its
   printout goes to `$BUILD_LOG_DIR/manifest.log`. `validate.sh`'s
   `verify_handoff.py` later checks the XML against this manifest.
8. **Provenance:** if the FormosanBank checkout is a git repository and its
   current commit differs from the one in `CodeAndDocs/provenance.json`, the
   script rewrites that file with the new commit and today's date.

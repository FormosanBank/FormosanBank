# Yedda Palemeq Blog

Southern Paiwan examples from Yedda Palemeq's public "Paiwan Every Day" blog
posts. The source is [Yedda Palemeq's blog](https://yeddapalemeq.blogspot.com/).

## License and AI use

**Permission to license this material was given by the author, Yedda Palemeq.**
The corpus is distributed under CC BY-NC 4.0, which is the value recorded in
the `copyright` attribute of the XML's `TEXT` element. The blog itself does not
carry a public licence notice; the licence here rests on the author's grant,
not on anything stated on the site.

The XML also retains the source URL, citation, and BibTeX metadata. This corpus
is subject to the central FormosanBank terms in
[LICENSE.md](../../LICENSE.md) and
[AI-USE-ADDENDUM.md](../../AI-USE-ADDENDUM.md). Commercial AI use is
prohibited without prior written permission.

## Corpus inventory

- Language: Paiwan, ISO 639-3 `pwn`
- Dialect: Southern
- XML: `XML/Paiwan/Paiwan_Yedda_Blog.xml`
- 668 frozen source records
- 671 canonical sentence records after three source-defined alternative splits
- 5,643 W elements and 6,492 M elements
- 5,585 TRANSL elements
- 665 AUDIO references
- Canonical XML SHA-256:
  `202dcfe2d117ebe12644bdd76332b2c02fffbd0d1c26ace0aa3f843d489f1aa4`

The original transcription uses the established Yedda Ortho113 route. The
standard FORM tier is derived from the original tier, and both PHON tiers are
regenerated with the pinned FormosanBank tooling.

## Reading the tiers

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
escaped `<in>` in the published FORM tiers. They are source notation, not
tags — a consumer that strips markup naively will corrupt these words.

## Source coverage

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

## Morpheme tier and standard-tier accents

Two corpus-wide decisions shape the tiers beyond the source reconciliation
below.

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

**The standard tier drops source acute accents.** The build runs
`standardize.py --remove_accents`, so the standard tier is the original minus
the accents FormosanBank treats as prosodic. In practice this touches only the
two Mandarin kin terms quoted in `S303_1`: `yípó` becomes `yipo` and `āyí`
becomes `āyi`. The macron survives because `QC/utilities/_accents.py` strips
only the combining acute and breve. The original tier keeps the source
spelling untouched in every case.

## Source reconciliation

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

## Reproduction

`CodeAndDocs/` holds two separate things, and the distinction matters:

- **`CodeAndDocs/scripts/` + `CodeAndDocs/data/` — the reproduction path.**
  The frozen source snapshot, audit tables, builder, tests, and QC disposition.
  These rebuild the canonical XML deterministically with no network access, and
  are what the commands below run.
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
snapshot, not re-scraping. The pipeline is pinned to FormosanBank commit
`e00edf3d83ecfdce37392a73b3d2796446f44195` and to development source commit
`25ed1f1ec56584e4a3e9fc960269c72d0e892a58`.

From a clean FormosanBank checkout, rebuild with:

```bash
VALIDATOR_ROOT=/path/to/pinned/FormosanBank \
VALIDATOR_PYTHON=/path/to/python \
RUN_LOG_DIR=/absolute/new/path/outside/repo \
Corpora/YeddaPalemeqBlog/CodeAndDocs/scripts/rebuild_xml.sh
```

Run the full pinned QC suite with:

```bash
VALIDATOR_ROOT=/path/to/pinned/FormosanBank \
VALIDATOR_PYTHON=/path/to/python \
OUTPUT_DIR=/absolute/new/path/outside/repo \
Corpora/YeddaPalemeqBlog/CodeAndDocs/scripts/run_final_qc.sh
```

Run two clean committed-tree rebuilds and final QC with:

```bash
VALIDATOR_ROOT=/path/to/pinned/FormosanBank \
VALIDATOR_PYTHON=/path/to/python \
OUTPUT_DIR=/absolute/new/path/outside/repo \
Corpora/YeddaPalemeqBlog/CodeAndDocs/scripts/reproduce.sh
```

The pinned handoff has zero structural, text, or gloss HARD findings. Its
9,918 soft finding occurrences are source-backed and fail-closed by exact
rule counts — including one file-level V148 recording that 16 sentences are
bare phrase entries the blog never broke into words. Eleven corpus regression tests cover source hashes, source
coverage, reviewed repairs, stable tier shape, per-sentence M-tier
consistency, standard-tier accent removal, and canonical XML identity.
Published port readiness has zero HARD findings and zero warnings.

## Audio

Run `download_audio_data.sh` from this directory to download the referenced
public YouTube audio through the central FormosanBank downloader. Downloaded
audio is not tracked. The 665 referenced files total 4,217.7 seconds; the three
shared alternative recordings are declared public dataset extras and excluded
from corpus totals.

## Citation

The XML citation is:

> Palemeq, Y. (2021). Yedda Palemeq. Retrieved May 19, 2026, from
> https://yeddapalemeq.blogspot.com/

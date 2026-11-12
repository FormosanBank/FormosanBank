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

#### Corpus notes

* Where the author parsed words into segments, those segments are preserved in `<M>` elements. Within such a sentence, a word we could not find a parse for is assumed to be monomorphemic and gets a single `<M>` — which is almost certainly incorrect in some cases.

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
     gloss, or the build stops), then `uncertain_glosses.tsv`: 8 word glosses
     where the author's `?` marks doubt about the gloss she gives (`LIG?`,
     `ligature (?)`, `to, towards?`, …) lose the mark and get
     `notes="uncertain"` (`LIG`, `ligature`, `to/towards`; POL-021), then turns whole-`?` word and morpheme glosses
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

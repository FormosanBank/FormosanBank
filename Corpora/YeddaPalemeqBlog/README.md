# Yedda Palemeq Blog

Southern Paiwan examples from Yedda Palemeq's public "Paiwan Every Day" blog
posts. The source is [Yedda Palemeq's blog](https://yeddapalemeq.blogspot.com/).

## License and AI use

The XML records the source license as CC BY-NC 4.0 and retains the source
citation, URL, and BibTeX metadata. This corpus is also subject to the central
FormosanBank terms in [LICENSE.md](../../LICENSE.md) and
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

**The standard tier drops source acute accents.** The build runs
`standardize.py --remove_accents`, so the standard tier is the original minus
the accents FormosanBank treats as prosodic. In practice this touches only the
two Mandarin kin terms quoted in `S303_1`: `yípó` becomes `yipo` and `āyí`
becomes `āyi`. The macron survives because `QC/utilities/_accents.py` strips
only the combining acute and breve. The original tier keeps the source
spelling untouched in every case.

## Source reconciliation

The frozen source snapshot contains every one of the 668 source records used by
the builder. The source-defined alternatives in `S24_1`, `S483_1`, and
`S535_1` are represented as six explicit records. Their three shared recordings
are omitted because each recording pronounces both alternatives.

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

The public source snapshot, audit tables, builder, tests, and QC disposition are
under `CodeAndDocs/`. They reproduce the canonical XML without a network
dependency. The pipeline is pinned to FormosanBank commit
`3a3c47c220520113f747e6a2d441494000e13c4b` and to development source commit
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
9,933 soft finding occurrences are source-backed and fail-closed by exact
rule counts. Eleven corpus regression tests cover source hashes, source
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

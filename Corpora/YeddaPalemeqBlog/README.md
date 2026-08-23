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
- 5,643 W elements and 7,657 M elements
- 5,585 TRANSL elements
- 665 AUDIO references
- Canonical XML SHA-256:
  `b452f10f520053370d090ae95b2e7013006249f7e3b5931d366f0cfce304fb7a`

The original transcription uses the established Yedda Ortho113 route. The
standard FORM tier is derived from the original tier, and both PHON tiers are
regenerated with the pinned FormosanBank tooling.

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
11,107 soft finding occurrences are source-backed and fail-closed by exact
rule counts. Nine corpus regression tests cover source hashes, source coverage,
reviewed repairs, stable tier shape, and canonical XML identity. Published port
readiness has zero HARD findings and zero warnings.

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

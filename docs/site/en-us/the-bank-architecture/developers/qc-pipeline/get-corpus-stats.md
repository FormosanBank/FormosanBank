---
icon: chart-line
---

# get_corpus_stats.py

> Writes the per-corpus statistics CSV that the documentation site reads, counting tokens, sentences, elements, and audio from a corpus's XML and filling audio seconds from the audio-durations source of truth.

## What it's for

`QC/utilities/get_corpus_stats.py` produces one `statistics/<CorpusName>_corpora_stats.csv` per corpus, broken down by `(language, dialect)`. Each row carries token counts, sentence counts, segmented/glossed word counts, English/Mandarin translation token counts, audio element counts, audio seconds, and structural element tallies. These CSVs are the published interface the documentation site's `docs/tools/site_stats.py` (and anyone downloading them) reads by column name, and the file [`corpus_metrics.py`](corpus-metrics.md) aggregates with `--stats-dir`.

All counting rules come from [`corpus_counts.py`](token-counting.md) — the single source of truth — so this script and the token/metrics tooling always agree. Audio *seconds* are never computed here (CI runners have no audio files): they are read from `statistics/audio_durations.csv`, the audio-seconds source of truth maintained by [`update_audio_stats.py` / `refresh_audio_stats.py`](audio-duration-stats.md).

## How it works

For each corpus it parses every `*.xml` under the corpus's `XML/` directory via `corpus_counts.collect_records`, buckets the per-file records by `(language, dialect)`, and sums the count fields. Audio *element counts* (transcribed = `AUDIO` under `S`/`W`; untranscribed = `AUDIO` directly under `TEXT`) are recomputed from XML on every run.

It then loads the matching corpus's rows from `audio_durations.csv` and copies their `transcribed_audio_seconds` / `untranscribed_audio_seconds` into each bucket. If a bucket currently has audio but its XML audio-count no longer matches the `count_at_compute` anchor stored in `audio_durations.csv` (or there is no entry, or the seconds are still 0), it prints a `STALE AUDIO` warning to stderr telling you to run `refresh_audio_stats.py`. Parse errors are reported to stderr and, with `--strict`, cause a nonzero exit; a parse-error count is recorded in a sentinel empty-language row.

The CSV columns through `file_count` are a frozen published interface — only appended-to, never renamed. The appended columns (`sentences`, `word_elements`, `morpheme_elements`, `translation_elements`, `audio_elements`, `parse_errors`) are safe for `DictReader` consumers.

## Usage

Run from the repo root after `source .venv/bin/activate`.

```bash
# One corpus
python QC/utilities/get_corpus_stats.py Corpora/ePark

# Every corpus under Corpora/ (what CI runs)
python QC/utilities/get_corpus_stats.py --all --strict

# Just list every stale (corpus, language, dialect) audio bucket; write nothing
python QC/utilities/get_corpus_stats.py --report-stale-audio
```

| Flag | Default | Purpose |
| --- | --- | --- |
| `corpora_path` (positional) | — | Path to a single corpus directory (e.g. `Corpora/ePark`). Mutually exclusive with `--all` / `--report-stale-audio`. |
| `--all` | off | Run on every corpus with an `XML/` directory under `--corpora_root`. |
| `--report-stale-audio` | off | Scan all corpora, print every stale audio bucket, write nothing; exit 1 if any are stale. |
| `--corpora_root` | repo `Corpora/` | Collection root used with `--all` and `--report-stale-audio`. |
| `--strict` | off | Exit nonzero if any XML file fails to parse. |

One of `corpora_path`, `--all`, or `--report-stale-audio` is required.

## Output & side effects

- Writes `statistics/<CorpusName>_corpora_stats.csv` (per corpus). With `--all`, writes one per corpus.
- `--report-stale-audio` writes nothing; it only prints a `STALE …` worklist.
- Never writes `audio_durations.csv` — it only reads it. CI never writes `audio_durations.csv` either.
- In CI, the [Corpus Metrics workflow](corpus-metrics.md) (`.github/workflows/corpus-metrics.yaml`) runs `--all --strict` and auto-commits the regenerated `*_corpora_stats.csv` files. **Do not hand-edit them.**

## When to run it

Run after porting or changing a corpus's XML, or whenever you need fresh per-corpus stats. CI runs it automatically on every push to `main` that touches `Corpora/` (or the counting scripts). Humans run it locally mostly via `--report-stale-audio` to find audio buckets whose seconds need a [refresh](audio-duration-stats.md), or as the stats step at the end of [Porting a Corpus In](../porting-a-corpus.md). Prerequisite: a `standard` (or at least `original`) sentence-tier `FORM` so token counting has something to count.

## Related

- [QC Pipeline overview](README.md)
- [corpus_metrics.py](corpus-metrics.md) — aggregates these CSVs
- [Token counting & counting rules](token-counting.md) — `corpus_counts.py` source of truth
- [Audio duration stats](audio-duration-stats.md) — `audio_durations.csv` and refresh tooling
- [Porting a Corpus In](../porting-a-corpus.md)

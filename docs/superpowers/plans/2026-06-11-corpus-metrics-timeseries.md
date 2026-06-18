# Additional Corpus Time-Series Metrics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three metrics — transcribed-audio duration, Mandarin-translated words, and glossed words — to the size-over-time history CSV and emit a PNG for each, alongside the existing token graph.

**Architecture:** Extend `QC/corpus_metrics.py` only. The two existing record-building paths (`read_stats_dir` from committed per-corpus CSVs; `analyze_xml_root` from XML / git blobs) each surface the three fields; `aggregate_records` sums them into `totals`; the history-row writers and `write_history_csv` carry three new columns; `plot_history` is generalized over a list of series specs to emit four PNGs. `transcribed_audio_seconds` is real only on the CSV path (XML/rebuild path writes 0).

**Tech Stack:** Python 3.10 stdlib (`csv`, `xml.etree`), matplotlib, pytest. All work happens in the worktree `../FormosanBank-metrics-timeseries` on branch `feature/corpus-metrics-timeseries`.

---

## Conventions for every task

- **Run tests** with `/Users/jkhartshorne/Documents/Projects/Formosan/FormosanBank-metrics-timeseries/.venv/bin/python -m pytest <args>` from the worktree root, or `pytest <args>` if on PATH. The worktree's `.venv` is a symlink to the main checkout's venv.
- **Working directory** is the worktree: `/Users/jkhartshorne/Documents/Projects/Formosan/FormosanBank-metrics-timeseries`. All paths below are relative to it unless absolute.
- **Never** `git add -A` / `git add .` / `git commit -a`. Stage only the exact paths named. Commit with explicit pathspecs.
- End every commit message with: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`
- The seed per-corpus CSVs (`statistics/*_corpora_stats.csv`) and the existing `statistics/corpus_size_history.csv` already exist in this worktree (committed).

## Current code facts (verified, so the diffs below are exact)

`QC/corpus_metrics.py` currently has:

```python
COUNT_FIELDS = (
    "tokens", "sentences", "xml_files", "word_elements",
    "morpheme_elements", "translation_elements", "audio_elements",
)

def empty_counts() -> dict[str, int]:
    return {field: 0 for field in COUNT_FIELDS}

def add_counts(target: dict[str, int], record: dict[str, Any]) -> None:
    for field in COUNT_FIELDS:
        target[field] += int(record.get(field, 0))
```

`aggregate_records` loops records calling `add_counts`, then `totals.update({"sources":..., "languages":..., "language_dialects":..., "parse_errors":...})`.

`analyze_xml_root` returns a dict with keys: `source, language, language_code, dialect, path, tokens, sentences, xml_files, word_elements, morpheme_elements, translation_elements, audio_elements`. The underlying `corpus_counts.analyze_root(root)` record already contains `glossed_words`, `zho_transl_count`, `transcribed_audio_count` (but NOT `transcribed_audio_seconds`).

`read_stats_dir` builds records with the same metric keys via an `as_int(field)` helper reading the per-corpus CSV row.

`history_row`, `history_row_from_records`, and `append_history_row` each return a dict with keys `commit, date, tokens, sentences, xml_files, sources, languages, parse_errors`.

`write_history_csv` uses `fieldnames = ["date", "commit", "tokens", "sentences", "xml_files", "sources", "languages", "parse_errors"]`.

`plot_history(rows, output_dir)` plots `int(row["tokens"])` vs date to `corpus_size_over_time.png`. `main` calls `plot_history(history_rows, output_dir)` in both the `--history-rebuild` and `--history` branches.

The fixture corpus `tests/fixtures/stats_corpus/MiniCorpus/XML/` has `ami_haian.xml` with `glossed_words=3`, `zho_transl_count=3`; the other valid files contribute 0 to both; `bad.xml` is a parse error. So an XML walk over `tests/fixtures/stats_corpus` totals `glossed_words=3`, `zho_transl_count=3`, `transcribed_audio_seconds=0`.

---

### Task 1: Surface and aggregate the three new metrics into `totals`

**Files:**
- Modify: `QC/corpus_metrics.py`
- Test: `tests/utilities/test_corpus_metrics.py`

**Decision (the spec's one non-mechanical point):** `glossed_words` and `zho_transl_count` are integer word counts — add them to `COUNT_FIELDS` so the existing int summation handles them. `transcribed_audio_seconds` is a float and is only needed in `totals` (not the per-language/source breakdowns), so sum it separately into `totals` as a float in `aggregate_records`. This keeps `COUNT_FIELDS`/`add_counts` integer-typed and untouched in behavior for the other maps.

- [ ] **Step 1: Write the failing tests**

Append to `tests/utilities/test_corpus_metrics.py`:

```python
def test_snapshot_aggregates_new_metrics(tmp_path):
    # _write_stats seeds: ami,Haian has glossed_words=3, zho_transl_count=3;
    # trv,Truku has transcribed_audio_seconds=1.0; everything else 0.
    _write_stats(tmp_path / "statistics")
    result = _run(["Corpora", "--stats-dir", str(tmp_path / "statistics"),
                   "--output-dir", str(tmp_path / "out"), "--no-plots"])
    assert result.returncode == 0, result.stderr
    totals = json.loads((tmp_path / "out" / "corpus_metrics.json").read_text())["totals"]
    assert totals["glossed_words"] == 3
    assert totals["zho_transl_count"] == 3
    assert totals["transcribed_audio_seconds"] == 1.0


def test_xml_path_aggregates_glossed_and_mandarin_but_zero_seconds(tmp_path):
    # XML walk over the fixture corpus: ami_haian contributes glossed=3, zho=3.
    # transcribed_audio_seconds is uncomputable from XML, so it must be 0.
    result = _run(["tests/fixtures/stats_corpus",
                   "--output-dir", str(tmp_path / "out"), "--no-plots"])
    assert result.returncode == 0, result.stderr
    totals = json.loads((tmp_path / "out" / "corpus_metrics.json").read_text())["totals"]
    assert totals["glossed_words"] == 3
    assert totals["zho_transl_count"] == 3
    assert totals["transcribed_audio_seconds"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/utilities/test_corpus_metrics.py::test_snapshot_aggregates_new_metrics tests/utilities/test_corpus_metrics.py::test_xml_path_aggregates_glossed_and_mandarin_but_zero_seconds -v`
Expected: FAIL with `KeyError: 'glossed_words'` (totals lacks the new keys).

- [ ] **Step 3: Add the two int metrics to `COUNT_FIELDS`**

In `QC/corpus_metrics.py`, change `COUNT_FIELDS` to:

```python
COUNT_FIELDS = (
    "tokens",
    "sentences",
    "xml_files",
    "word_elements",
    "morpheme_elements",
    "translation_elements",
    "audio_elements",
    "zho_transl_count",
    "glossed_words",
)
```

- [ ] **Step 4: Sum `transcribed_audio_seconds` as a float into `totals`**

In `aggregate_records`, replace the `totals.update({...})` call with one that also includes the float seconds sum:

```python
    totals.update(
        {
            "transcribed_audio_seconds": round(
                sum(float(record.get("transcribed_audio_seconds", 0) or 0) for record in records), 1
            ),
            "sources": len(source_names),
            "languages": len(languages),
            "language_dialects": len(dialects),
            "parse_errors": len(parse_errors),
        }
    )
```

- [ ] **Step 5: Surface the fields on both record paths**

In `analyze_xml_root`, add three keys to the returned dict (after `"audio_elements": record["audio_elements"],`):

```python
        "zho_transl_count": record["zho_transl_count"],
        "glossed_words": record["glossed_words"],
        "transcribed_audio_seconds": 0,
```

In `read_stats_dir`, add three keys to the appended record dict (after its `"audio_elements": as_int("audio_elements"),` line):

```python
                    "zho_transl_count": as_int("zho_transl_count"),
                    "glossed_words": as_int("glossed_words"),
                    "transcribed_audio_seconds": float(row.get("transcribed_audio_seconds") or 0),
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/utilities/test_corpus_metrics.py -v`
Expected: all pass (the two new tests plus the existing ones — the existing `test_snapshot_from_stats_dir` still passes because `add_counts` now also sums the two new int fields, which are 0 or matching in its assertions which don't check them).

- [ ] **Step 7: Commit**

```bash
git add QC/corpus_metrics.py tests/utilities/test_corpus_metrics.py
git commit -m "feat(QC): aggregate glossed_words, zho_transl_count, transcribed_audio_seconds into totals"
```

---

### Task 2: Write the three new columns into the history CSV

**Files:**
- Modify: `QC/corpus_metrics.py`
- Test: `tests/utilities/test_corpus_metrics.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/utilities/test_corpus_metrics.py`:

```python
def test_history_row_carries_new_metric_columns(tmp_path):
    _write_stats(tmp_path / "statistics")
    cache = tmp_path / "cache.csv"
    result = _run(["Corpora", "--stats-dir", str(tmp_path / "statistics"),
                   "--output-dir", str(tmp_path / "out"), "--no-plots",
                   "--history", "--history-cache", str(cache)])
    assert result.returncode == 0, result.stderr
    with open(tmp_path / "out" / "corpus_size_history.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    head = rows[-1]
    assert "transcribed_audio_seconds" in head
    assert "zho_transl_count" in head
    assert "glossed_words" in head
    assert int(head["glossed_words"]) == 3
    assert int(head["zho_transl_count"]) == 3
    assert float(head["transcribed_audio_seconds"]) == 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/utilities/test_corpus_metrics.py::test_history_row_carries_new_metric_columns -v`
Expected: FAIL — `KeyError`/`assert "transcribed_audio_seconds" in head` is False (column not written), or DictWriter would drop it.

- [ ] **Step 3: Add the columns to `write_history_csv`**

Change its `fieldnames` to:

```python
    fieldnames = ["date", "commit", "tokens", "sentences", "xml_files", "sources",
                  "languages", "parse_errors", "transcribed_audio_seconds",
                  "zho_transl_count", "glossed_words"]
```

- [ ] **Step 4: Populate the columns in all three row builders**

In `history_row`, add three entries to the returned dict (after `"parse_errors": metrics["totals"]["parse_errors"],`):

```python
        "transcribed_audio_seconds": metrics["totals"]["transcribed_audio_seconds"],
        "zho_transl_count": metrics["totals"]["zho_transl_count"],
        "glossed_words": metrics["totals"]["glossed_words"],
```

In `history_row_from_records`, add three entries (after `"parse_errors": totals["parse_errors"],`):

```python
        "transcribed_audio_seconds": totals["transcribed_audio_seconds"],
        "zho_transl_count": totals["zho_transl_count"],
        "glossed_words": totals["glossed_words"],
```

In `append_history_row`, add three entries to the `row` dict (after `"parse_errors": metrics["totals"]["parse_errors"],`):

```python
        "transcribed_audio_seconds": metrics["totals"]["transcribed_audio_seconds"],
        "zho_transl_count": metrics["totals"]["zho_transl_count"],
        "glossed_words": metrics["totals"]["glossed_words"],
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/utilities/test_corpus_metrics.py -v`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add QC/corpus_metrics.py tests/utilities/test_corpus_metrics.py
git commit -m "feat(QC): write audio-seconds/Mandarin/glossed columns to corpus_size_history.csv"
```

---

### Task 3: Generalize `plot_history` to emit four PNGs

**Files:**
- Modify: `QC/corpus_metrics.py`
- Test: `tests/utilities/test_corpus_metrics.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/utilities/test_corpus_metrics.py` (top of file already imports `csv`, `json`, `subprocess`, `sys`, `Path`):

```python
def test_history_plots_emit_four_pngs(tmp_path):
    # Use the real subprocess path WITH plots (omit --no-plots). Seed stats and
    # a one-row cache so there is a dated row to plot.
    _write_stats(tmp_path / "statistics")
    out = tmp_path / "out"
    result = _run(["Corpora", "--stats-dir", str(tmp_path / "statistics"),
                   "--output-dir", str(out), "--history",
                   "--history-cache", str(tmp_path / "cache.csv")])
    assert result.returncode == 0, result.stderr
    for name in ("corpus_size_over_time.png",
                 "corpus_transcribed_audio_over_time.png",
                 "corpus_mandarin_words_over_time.png",
                 "corpus_glossed_words_over_time.png"):
        assert (out / name).is_file(), f"missing {name}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/utilities/test_corpus_metrics.py::test_history_plots_emit_four_pngs -v`
Expected: FAIL — only `corpus_size_over_time.png` is produced; the three new files are missing.

- [ ] **Step 3: Add an hours formatter**

In `QC/corpus_metrics.py`, just after the existing `format_short` function, add:

```python
def format_hours(value: int | float) -> str:
    return f"{value:,.0f}"
```

- [ ] **Step 4: Replace `plot_history` with a generalized version**

Replace the entire existing `plot_history` function with the following. It keeps the same public signature (`plot_history(rows, output_dir)`) and the same look for the tokens chart, and loops over a series table for the rest. `to_y` converts the stored column value to the plotted value (seconds→hours for audio); `fmt` formats axis ticks and the end annotation.

```python
HISTORY_SERIES = (
    {
        "column": "tokens",
        "title": "FormosanBank Size Over Time",
        "ylabel": "Tokens",
        "filename": "corpus_size_over_time.png",
        "to_y": None,
        "fmt": format_short,
        "caption": None,
    },
    {
        "column": "transcribed_audio_seconds",
        "title": "Transcribed Audio Over Time",
        "ylabel": "Hours",
        "filename": "corpus_transcribed_audio_over_time.png",
        "to_y": lambda seconds: seconds / 3600.0,
        "fmt": format_hours,
        "caption": "Duration tracking begins at rollout; earlier points may be sparse.",
    },
    {
        "column": "zho_transl_count",
        "title": "Mandarin-Translated Words Over Time",
        "ylabel": "Words",
        "filename": "corpus_mandarin_words_over_time.png",
        "to_y": None,
        "fmt": format_short,
        "caption": None,
    },
    {
        "column": "glossed_words",
        "title": "Glossed Words Over Time",
        "ylabel": "Words",
        "filename": "corpus_glossed_words_over_time.png",
        "to_y": None,
        "fmt": format_short,
        "caption": None,
    },
)


def plot_series(rows: list[dict[str, Any]], output_dir: Path, spec: dict[str, Any]) -> None:
    output_path = output_dir / spec["filename"]
    if not rows:
        plot_empty_state(spec["title"], "No history rows were generated.", output_path)
        return

    plt = require_matplotlib()
    dates = []
    values = []
    for row in rows:
        if not row.get("date"):
            continue
        raw = float(row.get(spec["column"], 0) or 0)
        y = spec["to_y"](raw) if spec["to_y"] else raw
        dates.append(dt.datetime.fromisoformat(row["date"].replace("Z", "+00:00")))
        values.append(y)
    if not dates:
        plot_empty_state(spec["title"], "No dated history rows were available.", output_path)
        return

    fmt = spec["fmt"]
    fig, ax = plt.subplots(figsize=(11, 5.8), facecolor=PLOT_BG)
    ax.set_facecolor(PLOT_BG)
    ax.plot(dates, values, color=PLOT_COLORS[0], marker="o", markersize=5, linewidth=2.4)
    ax.fill_between(dates, values, min(values), color=PLOT_COLORS[0], alpha=0.12)
    ax.set_title(spec["title"], loc="left", fontsize=18, fontweight="bold", color=PLOT_TEXT, pad=16)
    subtitle = f"{len(values)} commits sampled."
    if spec["caption"]:
        subtitle = f"{subtitle} {spec['caption']}"
    ax.text(0, 1.01, subtitle, transform=ax.transAxes, ha="left", va="bottom", fontsize=10, color=PLOT_MUTED)
    ax.set_ylabel(spec["ylabel"], color=PLOT_MUTED, labelpad=10)
    ax.grid(color=PLOT_GRID, linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(lambda value, _pos: fmt(value))
    ax.tick_params(axis="x", colors=PLOT_MUTED, labelsize=9)
    ax.tick_params(axis="y", colors=PLOT_MUTED, labelsize=9)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(PLOT_GRID)
    ax.spines["bottom"].set_color(PLOT_GRID)
    ax.annotate(
        fmt(values[-1]),
        xy=(dates[-1], values[-1]),
        xytext=(8, 0),
        textcoords="offset points",
        va="center",
        fontsize=10,
        color=PLOT_TEXT,
        fontweight="bold",
    )
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight", facecolor=PLOT_BG)
    plt.close(fig)


def plot_history(rows: list[dict[str, Any]], output_dir: Path) -> None:
    for spec in HISTORY_SERIES:
        plot_series(rows, output_dir, spec)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/utilities/test_corpus_metrics.py -v`
Expected: all pass, including `test_history_plots_emit_four_pngs`.

- [ ] **Step 6: Pyright check (repo configures pyright; keep it clean)**

Run: `npx --no-install pyright QC/corpus_metrics.py` (or the globally-installed `pyright QC/corpus_metrics.py`). If pyright is unavailable, state that and skip.
Expected: no new errors. (Pre-existing underscore "_pos"/"_by_source" informational hints are acceptable.)

- [ ] **Step 7: Commit**

```bash
git add QC/corpus_metrics.py tests/utilities/test_corpus_metrics.py
git commit -m "feat(QC): generalize plot_history to emit audio/Mandarin/glossed PNGs"
```

---

### Task 4: CI — commit the three new PNGs

**Files:**
- Modify: `.github/workflows/corpus-metrics.yaml`

- [ ] **Step 1: Update the commit step's copy + add list**

In `.github/workflows/corpus-metrics.yaml`, the "Commit updated statistics" step currently does:

```yaml
          mkdir -p statistics
          cp corpus-metrics/corpus_size_history.csv statistics/corpus_size_history.csv
          cp corpus-metrics/corpus_size_over_time.png statistics/corpus_size_over_time.png

          git add statistics/corpus_size_history.csv statistics/corpus_size_over_time.png statistics/*_corpora_stats.csv
```

Replace those lines with:

```yaml
          mkdir -p statistics
          cp corpus-metrics/corpus_size_history.csv statistics/corpus_size_history.csv
          cp corpus-metrics/corpus_size_over_time.png statistics/corpus_size_over_time.png
          cp corpus-metrics/corpus_transcribed_audio_over_time.png statistics/corpus_transcribed_audio_over_time.png
          cp corpus-metrics/corpus_mandarin_words_over_time.png statistics/corpus_mandarin_words_over_time.png
          cp corpus-metrics/corpus_glossed_words_over_time.png statistics/corpus_glossed_words_over_time.png

          git add statistics/corpus_size_history.csv \
            statistics/corpus_size_over_time.png \
            statistics/corpus_transcribed_audio_over_time.png \
            statistics/corpus_mandarin_words_over_time.png \
            statistics/corpus_glossed_words_over_time.png \
            statistics/*_corpora_stats.csv
```

- [ ] **Step 2: Validate YAML**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/corpus-metrics.yaml')); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/corpus-metrics.yaml
git commit -m "ci: commit the three new corpus time-series PNGs"
```

---

### Task 5: Docs — embed the new graphs

**Files:**
- Modify: `README.md`
- Modify: `QC/README.md`

- [ ] **Step 1: Find where the existing graph is embedded**

Run: `grep -n "corpus_size_over_time.png" README.md QC/README.md`
This shows the exact markdown image line(s) to anchor next to.

- [ ] **Step 2: Add the three images in `README.md`**

Immediately after the existing `![...](statistics/corpus_size_over_time.png)` line (or its HTML `<img>` equivalent — match whatever form is there), add three lines in the same form, e.g. if the existing line is markdown:

```markdown
![Transcribed audio over time](statistics/corpus_transcribed_audio_over_time.png)
![Mandarin-translated words over time](statistics/corpus_mandarin_words_over_time.png)
![Glossed words over time](statistics/corpus_glossed_words_over_time.png)
```

(If the existing embed uses an HTML `<img src=...>` tag, mirror that tag form instead so styling stays consistent.)

- [ ] **Step 3: Add the same three images + a note in `QC/README.md`**

After the existing `corpus_size_over_time.png` reference in `QC/README.md`, add the same three image lines, then a one-line note:

```markdown
The `transcribed_audio_seconds` series is forward-only: audio durations cannot be reconstructed from git history (audio files are not in the repo), so historical rows show 0 and the series accumulates from rollout onward. Keep it current by running `QC/utilities/update_audio_stats.py` against downloaded audio so the per-corpus CSVs carry real seconds.
```

- [ ] **Step 4: Commit**

```bash
git add README.md QC/README.md
git commit -m "docs: embed audio/Mandarin/glossed growth graphs"
```

---

### Task 6: Rollout — rebuild history, capture audio seconds, regenerate PNGs, commit

This task is verification-heavy and runs real commands against the full corpora in the worktree. Read the actual outputs; quote evidence.

**Files:**
- Regenerate + commit: `statistics/corpus_size_history.csv`, `statistics/corpus_size_over_time.png`, `statistics/corpus_transcribed_audio_over_time.png`, `statistics/corpus_mandarin_words_over_time.png`, `statistics/corpus_glossed_words_over_time.png`, and any changed `statistics/*_corpora_stats.csv`.

- [ ] **Step 1: Refresh the per-corpus CSVs (counts fresh, seconds carried)**

Run: `python QC/utilities/get_corpus_stats.py --all --strict 2> /tmp/ts_gcs.log`
Expected: exit 0, 20 CSVs written, 0 parse errors. (Warnings are the known missing-dialect ones.) Confirm the seeded audio seconds survived: `grep -c "." statistics/Whitehorn_Collection_corpora_stats.csv` and spot-check that `transcribed_audio_seconds` for ILRDF/Tang/Wilang and Whitehorn's `untranscribed_audio_seconds` are still nonzero. NOTE: Whitehorn audio is *untranscribed*, so it does NOT feed `transcribed_audio_seconds` — the transcribed series draws only from `transcribed_audio_count`-bearing corpora's seconds.

- [ ] **Step 2: Rebuild the full history from git blobs (backfills tokens/Mandarin/glossed)**

Run: `python QC/corpus_metrics.py Corpora --history-rebuild --output-dir /tmp/ts_rebuild --no-plots 2> /tmp/ts_rebuild.log`
Expected: exit 0; this is slow (full first-parent walk). Read `/tmp/ts_rebuild/corpus_size_history.csv`: every row now has the 11 columns; `transcribed_audio_seconds` is 0 for all rows (XML path); `zho_transl_count`/`glossed_words` vary across history; the final row's `tokens` is the new-rule total (~7,979,648). Quote the header and last two rows.

- [ ] **Step 3: Append the HEAD row WITH real audio seconds from the committed CSVs**

Run: `python QC/corpus_metrics.py Corpora --stats-dir statistics --history --history-cache /tmp/ts_rebuild/corpus_size_history.csv --output-dir /tmp/ts_final`
Expected: exit 0; produces `/tmp/ts_final/corpus_size_history.csv` (same rows, but the HEAD row replaced by one whose `transcribed_audio_seconds` reflects today's per-corpus CSV totals) and all four PNGs. Read the last row and confirm `transcribed_audio_seconds` is now nonzero (the sum of transcribed seconds across corpora; today that is whatever ILRDF/Tang/Wilang's *transcribed* seconds are — verify which corpora contribute, since several only have untranscribed audio). Quote the last row.

- [ ] **Step 4: Sanity-check the four PNGs exist and look right**

Run: `ls -la /tmp/ts_final/*.png` and open/Read each PNG to eyeball: tokens trends up; Mandarin/glossed show their history; audio shows a flat-zero line with a single nonzero point at the end (expected, captioned). Report what you see.

- [ ] **Step 5: Copy regenerated artifacts into `statistics/` and stage**

```bash
cp /tmp/ts_final/corpus_size_history.csv statistics/corpus_size_history.csv
cp /tmp/ts_final/corpus_size_over_time.png statistics/corpus_size_over_time.png
cp /tmp/ts_final/corpus_transcribed_audio_over_time.png statistics/corpus_transcribed_audio_over_time.png
cp /tmp/ts_final/corpus_mandarin_words_over_time.png statistics/corpus_mandarin_words_over_time.png
cp /tmp/ts_final/corpus_glossed_words_over_time.png statistics/corpus_glossed_words_over_time.png
git add statistics/corpus_size_history.csv \
  statistics/corpus_size_over_time.png \
  statistics/corpus_transcribed_audio_over_time.png \
  statistics/corpus_mandarin_words_over_time.png \
  statistics/corpus_glossed_words_over_time.png
```

Also stage any per-corpus CSVs that changed under the fresh `get_corpus_stats` run: `git add statistics/*_corpora_stats.csv` (only if `git status --porcelain statistics/` shows modifications).

- [ ] **Step 6: Final full suite + commit**

Run: `pytest tests -q`
Expected: all pass. Quote the summary.

```bash
git commit -m "stats: backfill history with Mandarin/glossed; add audio/Mandarin/glossed growth graphs"
```

(The `corpus_size_history.csv` token column is now restated under the new counting rules — the previously-accepted discontinuity is resolved by this rebuild. Note this in the eventual PR description.)

---

## Self-review checklist (run after drafting, before handoff)

- **Spec coverage:** metric definitions → Task 1 (aggregation) + Task 6 (real data); single-CSV-with-3-columns → Tasks 1–2; CSV-path-has-seconds / XML-path-zero → Task 1 (both tests); three PNGs + hours axis + caption → Task 3; CI commits PNGs → Task 4; README/QC docs + forward-only note → Task 5; one-time rebuild then append-for-seconds → Task 6.
- **Float-vs-int risk (spec's flagged point):** handled in Task 1 Step 4 — seconds summed as float into `totals` only; `COUNT_FIELDS` stays int. Tested by `test_snapshot_aggregates_new_metrics` (1.0) and `test_xml_path_...` (0).
- **Type consistency:** column names identical everywhere — `transcribed_audio_seconds`, `zho_transl_count`, `glossed_words` — across `COUNT_FIELDS`, `aggregate_records`, `analyze_xml_root`, `read_stats_dir`, the three row builders, `write_history_csv` fieldnames, and `HISTORY_SERIES`. `plot_history(rows, output_dir)` keeps its signature so `main` is untouched.
- **No placeholders:** every code step shows the exact code; the only run-time-chosen values are `/tmp` output dirs in Task 6.
- **Known risk to flag in PR:** Task 6 restates the token column under new rules (resolves the earlier discontinuity); the audio series is a single nonzero point at first.

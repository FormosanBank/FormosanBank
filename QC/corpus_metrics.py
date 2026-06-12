#!/usr/bin/env python3
"""Generate FormosanBank corpus metrics from XML files under Corpora/."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import subprocess
import sys
import textwrap
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any, NamedTuple

import corpus_counts

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

XML_HISTORY_PATHSPEC = ":(glob)Corpora/**/XML/**/*.xml"
ZERO_OID = "0" * 40
PLOT_BG = "#fbfbf8"
PLOT_TEXT = "#24292f"
PLOT_MUTED = "#6e7781"
PLOT_GRID = "#d8dee4"
PLOT_COLORS = ["#4f6f91", "#2f7f73", "#c58b2a", "#b05c4b", "#7467a8", "#3f8f9f"]

DEFAULT_BENCHMARKS = [
    {
        "name": "Brown Corpus",
        "tokens": None,
        "unit": "words",
        "source": "CoRD Brown Corpus overview",
        "url": "https://varieng.helsinki.fi/CoRD/corpora/BROWN/",
        "note": "Exact count not yet source-verified for this comparison.",
    },
    {
        "name": "Penn Treebank WSJ",
        "tokens": None,
        "unit": "words",
        "source": "LDC Treebank-3 catalog entry",
        "url": "https://catalog.ldc.upenn.edu/LDC99T42",
        "note": "Exact count not yet source-verified for this comparison.",
    },
]


class XmlChange(NamedTuple):
    status: str
    path: str
    old_oid: str | None
    new_oid: str | None


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def run_git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def run_git_bytes(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def git_value(args: list[str], cwd: Path) -> str | None:
    try:
        result = run_git(args, cwd)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return result.stdout.strip() or None


def progress(message: str) -> None:
    print(f"[corpus-metrics] {message}", file=sys.stderr, flush=True)


def repo_root_from(path: Path) -> Path:
    root = git_value(["rev-parse", "--show-toplevel"], path)
    return Path(root) if root else path.resolve()


def find_xml_files(corpora_path: Path) -> list[Path]:
    xml_files = []
    for xml_file in corpora_path.rglob("*.xml"):
        if "XML" in xml_file.parts:
            xml_files.append(xml_file)
    return sorted(xml_files)


def source_for(corpora_path: Path, xml_file: Path) -> str:
    try:
        rel = xml_file.relative_to(corpora_path)
    except ValueError:
        return "Unknown"
    return rel.parts[0] if rel.parts else corpora_path.name


def display_language(language_code: str, dialect: str) -> str:
    resolved = corpus_counts.resolve_language(language_code, dialect)
    if resolved:
        return resolved
    return f"Unknown ({language_code})" if language_code else "Unknown"


def analyze_xml_root(corpora_path: Path, xml_file: Path, root: ET.Element) -> dict[str, Any]:
    record = corpus_counts.analyze_root(root)
    return {
        "source": source_for(corpora_path, xml_file),
        "language": display_language(record["language"], record["dialect"]),
        "language_code": record["language"] or None,
        "dialect": record["dialect"] or "Not Specified",
        "path": str(xml_file.relative_to(corpora_path.parent)),
        "tokens": record["word_count"],
        "sentences": record["sentences"],
        "xml_files": 1,
        "word_elements": record["word_elements"],
        "morpheme_elements": record["morpheme_elements"],
        "translation_elements": record["translation_elements"],
        "audio_elements": record["audio_elements"],
        "zho_transl_count": record["zho_transl_count"],
        "glossed_words": record["glossed_words"],
        "transcribed_audio_seconds": 0,
    }


def analyze_xml_file(corpora_path: Path, xml_file: Path) -> dict[str, Any]:
    tree = ET.parse(xml_file)
    return analyze_xml_root(corpora_path, xml_file, tree.getroot())


def analyze_xml_bytes(corpora_path: Path, relative_path: str, content: bytes) -> dict[str, Any]:
    root = ET.fromstring(content)
    xml_file = corpora_path.parent / relative_path
    return analyze_xml_root(corpora_path, xml_file, root)


def empty_counts() -> dict[str, int]:
    return {field: 0 for field in COUNT_FIELDS}


def add_counts(target: dict[str, int], record: dict[str, Any]) -> None:
    for field in COUNT_FIELDS:
        target[field] += int(record.get(field, 0))


def sorted_counts_map(data: dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
    return dict(sorted(data.items(), key=lambda item: (-item[1]["tokens"], item[0])))


def sorted_dialect_counts(data: dict[tuple[str, str], dict[str, int]]) -> list[dict[str, Any]]:
    rows = []
    for (language, dialect), counts in data.items():
        rows.append({"language": language, "dialect": dialect, **counts})
    return sorted(rows, key=lambda row: (-row["tokens"], row["language"], row["dialect"]))


def aggregate_records(
    records: list[dict[str, Any]],
    parse_errors: list[dict[str, str]],
) -> tuple[dict[str, Any], dict[str, dict[str, int]], dict[str, dict[str, int]], list[dict[str, Any]]]:
    totals: dict[str, Any] = empty_counts()
    by_source: dict[str, dict[str, int]] = defaultdict(empty_counts)
    by_language: dict[str, dict[str, int]] = defaultdict(empty_counts)
    by_language_dialect: dict[tuple[str, str], dict[str, int]] = defaultdict(empty_counts)

    source_names: set[str] = set()
    languages: set[str] = set()
    dialects: set[tuple[str, str]] = set()

    for record in records:
        add_counts(totals, record)
        add_counts(by_source[record["source"]], record)
        add_counts(by_language[record["language"]], record)
        add_counts(by_language_dialect[(record["language"], record["dialect"])], record)
        source_names.add(record["source"])
        languages.add(record["language"])
        dialects.add((record["language"], record["dialect"]))

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

    return totals, sorted_counts_map(by_source), sorted_counts_map(by_language), sorted_dialect_counts(by_language_dialect)


def build_metrics(corpora_path: Path, records: list[dict[str, Any]], parse_errors: list[dict[str, str]]) -> dict[str, Any]:
    totals, by_source, by_language, by_language_dialect = aggregate_records(records, parse_errors)
    return {
        "generated_at": now_utc(),
        "corpora_path": str(corpora_path),
        "counting": "standard tier (original fallback); tokens are whitespace chunks containing a letter or digit",
        "git": {
            "commit": os.environ.get("GITHUB_SHA")
            or git_value(["rev-parse", "HEAD"], corpora_path),
            "ref": os.environ.get("GITHUB_REF_NAME")
            or git_value(["branch", "--show-current"], corpora_path),
        },
        "totals": totals,
        "by_source": by_source,
        "by_language": by_language,
        "by_language_dialect": by_language_dialect,
        "parse_errors": parse_errors,
    }


def collect_corpus_records(corpora_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    corpora_path = corpora_path.resolve()
    records: list[dict[str, Any]] = []
    parse_errors: list[dict[str, str]] = []

    for xml_file in find_xml_files(corpora_path):
        try:
            records.append(analyze_xml_file(corpora_path, xml_file))
        except Exception as exc:
            parse_errors.append(
                {
                    "path": str(xml_file.relative_to(corpora_path.parent)),
                    "error": str(exc),
                }
            )

    return records, parse_errors


STATS_SUFFIX = "_corpora_stats.csv"


def read_stats_dir(stats_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Build per-(corpus, language, dialect) records from the per-corpus CSVs
    written by QC/utilities/get_corpus_stats.py (the inverted pipeline:
    that script counts, this one aggregates)."""
    records: list[dict[str, Any]] = []
    parse_errors: list[dict[str, str]] = []
    csv_paths = sorted(Path(stats_dir).glob(f"*{STATS_SUFFIX}"))
    if not csv_paths:
        raise FileNotFoundError(f"No *{STATS_SUFFIX} files found in {stats_dir}")

    for csv_path in csv_paths:
        source = csv_path.name[: -len(STATS_SUFFIX)]
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):

                def as_int(field: str) -> int:
                    return int(float(row.get(field) or 0))

                if not (row.get("language") or "").strip() and as_int("parse_errors"):
                    parse_errors.extend(
                        {"path": f"{source} (file unknown; see get_corpus_stats log)",
                         "error": "XML parse error"}
                        for _ in range(as_int("parse_errors"))
                    )
                    continue
                language_code = (row.get("language") or "").strip()
                dialect = (row.get("dialect") or "").strip()
                records.append({
                    "source": source,
                    "language": display_language(language_code, dialect),
                    "language_code": language_code or None,
                    "dialect": dialect or "Not Specified",
                    "path": f"{source}:{language_code or 'unknown'}:{dialect or 'unknown'}",
                    "tokens": as_int("word_count"),
                    "sentences": as_int("sentences"),
                    "xml_files": as_int("file_count"),
                    "word_elements": as_int("word_elements"),
                    "morpheme_elements": as_int("morpheme_elements"),
                    "translation_elements": as_int("translation_elements"),
                    "audio_elements": as_int("audio_elements"),
                    "zho_transl_count": as_int("zho_transl_count"),
                    "glossed_words": as_int("glossed_words"),
                    "transcribed_audio_seconds": float(row.get("transcribed_audio_seconds") or 0),
                })
    return records, parse_errors


def load_benchmarks(path: Path | None) -> list[dict[str, Any]]:
    if path and path.is_file():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_BENCHMARKS


def write_json(metrics: dict[str, Any], output_dir: Path) -> Path:
    path = output_dir / "corpus_metrics.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return path


def format_int(value: int | float) -> str:
    return f"{int(value):,}"


def format_short(value: int | float) -> str:
    value = int(value)
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000:
        return f"{sign}{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{sign}{value / 1_000:.1f}K"
    return f"{sign}{value:,}"


def format_hours(value: int | float) -> str:
    return f"{value:,.0f}"


def pct_of(value: int, total: int) -> str:
    if total <= 0:
        return "n/a"
    return f"{(value / total) * 100:.1f}%"


def markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return lines


def benchmark_rows(metrics: dict[str, Any], benchmarks: list[dict[str, Any]]) -> list[list[str]]:
    current_tokens = int(metrics["totals"]["tokens"])
    rows = [
        [
            "FormosanBank current",
            format_int(current_tokens),
            "tokens",
            "1.00x",
            "Generated from Corpora/ XML",
        ]
    ]
    for benchmark in benchmarks:
        tokens = benchmark.get("tokens")
        token_count = int(tokens) if tokens is not None else None
        ratio = f"{current_tokens / token_count:.2f}x" if token_count else "n/a"
        source = benchmark.get("source", "")
        url = benchmark.get("url")
        if url:
            source = f"[{source}]({url})"
        rows.append(
            [
                benchmark["name"],
                format_int(token_count) if token_count else "TBD",
                benchmark.get("unit", "tokens"),
                ratio,
                source,
            ]
        )
    return rows


def write_markdown(metrics: dict[str, Any], benchmarks: list[dict[str, Any]], output_dir: Path) -> Path:
    totals = metrics["totals"]
    lines = [
        "# FormosanBank Corpus Metrics",
        "",
        f"Generated at: `{metrics['generated_at']}`",
        f"Git ref: `{metrics['git'].get('ref') or 'unknown'}`",
        f"Git commit: `{metrics['git'].get('commit') or 'unknown'}`",
        f"Token source: sentence-level FORM, standard tier with original fallback.",
        "",
        "## Totals",
        "",
    ]
    lines.extend(
        markdown_table(
            ["Metric", "Count"],
            [
                ["Tokens", format_int(totals["tokens"])],
                ["Sentences", format_int(totals["sentences"])],
                ["XML files", format_int(totals["xml_files"])],
                ["Corpus sources", format_int(totals["sources"])],
                ["Languages", format_int(totals["languages"])],
                ["Language/dialect pairs", format_int(totals["language_dialects"])],
                ["Word elements", format_int(totals["word_elements"])],
                ["Morpheme elements", format_int(totals["morpheme_elements"])],
                ["Translation elements", format_int(totals["translation_elements"])],
                ["Audio elements", format_int(totals["audio_elements"])],
                ["Parse errors", format_int(totals["parse_errors"])],
            ],
        )
    )

    lines.extend(["", "## Top Languages", ""])
    language_rows = []
    for language, counts in list(metrics["by_language"].items())[:15]:
        language_rows.append(
            [
                language,
                format_int(counts["tokens"]),
                pct_of(counts["tokens"], totals["tokens"]),
                format_int(counts["xml_files"]),
                format_int(counts["sentences"]),
            ]
        )
    lines.extend(markdown_table(["Language", "Tokens", "Share", "XML files", "Sentences"], language_rows))

    lines.extend(["", "## Top Sources", ""])
    source_rows = []
    for source, counts in list(metrics["by_source"].items())[:15]:
        source_rows.append(
            [
                source,
                format_int(counts["tokens"]),
                pct_of(counts["tokens"], totals["tokens"]),
                format_int(counts["xml_files"]),
                format_int(counts["sentences"]),
            ]
        )
    lines.extend(markdown_table(["Source", "Tokens", "Share", "XML files", "Sentences"], source_rows))

    lines.extend(["", "## Benchmark Comparison", ""])
    lines.extend(markdown_table(["Corpus", "Size", "Unit", "FormosanBank / corpus", "Source"], benchmark_rows(metrics, benchmarks)))

    benchmark_notes = [b for b in benchmarks if b.get("note")]
    if benchmark_notes:
        lines.extend(["", "Benchmark notes:"])
        for benchmark in benchmark_notes:
            lines.append(f"- {benchmark['name']}: {benchmark['note']}")

    if metrics["parse_errors"]:
        lines.extend(["", "## Parse Errors", ""])
        rows = [[item["path"], item["error"]] for item in metrics["parse_errors"][:20]]
        lines.extend(markdown_table(["Path", "Error"], rows))
        if len(metrics["parse_errors"]) > 20:
            lines.append("")
            lines.append(f"Only the first 20 of {len(metrics['parse_errors'])} parse errors are shown.")

    path = output_dir / "corpus_metrics.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")
    return path


def require_matplotlib() -> Any:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "figure.facecolor": PLOT_BG,
            "axes.facecolor": PLOT_BG,
            "axes.edgecolor": PLOT_GRID,
            "axes.labelcolor": PLOT_MUTED,
            "xtick.color": PLOT_MUTED,
            "ytick.color": PLOT_TEXT,
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "savefig.facecolor": PLOT_BG,
        }
    )
    return plt


def wrap_plot_label(label: str, width: int = 28) -> str:
    return textwrap.fill(label, width=width, break_long_words=False)


def plot_empty_state(title: str, message: str, output_path: Path) -> None:
    plt = require_matplotlib()
    fig, ax = plt.subplots(figsize=(10, 4), facecolor=PLOT_BG)
    ax.set_facecolor(PLOT_BG)
    ax.axis("off")
    ax.text(0.02, 0.70, title, transform=ax.transAxes, color=PLOT_TEXT, fontsize=18, fontweight="bold")
    ax.text(0.02, 0.46, message, transform=ax.transAxes, color=PLOT_MUTED, fontsize=11, wrap=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight", facecolor=PLOT_BG)
    plt.close(fig)


def plot_horizontal_bars(
    rows: list[tuple[str, int]],
    title: str,
    output_path: Path,
    max_rows: int | None = None,
    note: str | None = None,
) -> None:
    if not rows:
        plot_empty_state(title, "No non-zero values to plot.", output_path)
        return

    plt = require_matplotlib()
    total_rows = len(rows)
    rows = sorted(rows, key=lambda item: item[1], reverse=True)
    if max_rows:
        rows = rows[:max_rows]
    rows = list(reversed(rows))

    labels = [wrap_plot_label(row[0]) for row in rows]
    values = [row[1] for row in rows]
    colors = [PLOT_COLORS[i % len(PLOT_COLORS)] for i in range(len(rows))]
    height = max(5, min(16, 0.38 * len(rows) + 2.4))

    fig, ax = plt.subplots(figsize=(11, height), facecolor=PLOT_BG)
    ax.set_facecolor(PLOT_BG)
    bars = ax.barh(labels, values, color=colors, height=0.68)
    ax.set_title(title, loc="left", fontsize=18, fontweight="bold", color=PLOT_TEXT, pad=16)
    if note is None and max_rows and total_rows > len(rows):
        note = f"Showing top {len(rows)} of {total_rows} rows by token count."
    if note:
        ax.text(0, 1.01, note, transform=ax.transAxes, ha="left", va="bottom", fontsize=10, color=PLOT_MUTED)

    ax.set_xlabel("Tokens", labelpad=10)
    ax.xaxis.set_major_formatter(lambda value, _pos: format_short(value))
    ax.grid(axis="x", color=PLOT_GRID, linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", colors=PLOT_MUTED, labelsize=9)
    ax.tick_params(axis="y", colors=PLOT_TEXT, labelsize=9, length=0)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(PLOT_GRID)

    xmax = max(values) * 1.16 if values else 1
    ax.set_xlim(0, xmax)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_width() + xmax * 0.01,
            bar.get_y() + bar.get_height() / 2,
            format_short(value),
            va="center",
            ha="left",
            fontsize=9,
            color=PLOT_MUTED,
        )
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight", facecolor=PLOT_BG)
    plt.close(fig)


def plot_benchmarks(metrics: dict[str, Any], benchmarks: list[dict[str, Any]], output_path: Path) -> None:
    current_tokens = int(metrics["totals"]["tokens"])
    rows = [("FormosanBank current", current_tokens)]
    rows.extend(
        (benchmark["name"], int(benchmark["tokens"]))
        for benchmark in benchmarks
        if benchmark.get("tokens") is not None
    )
    if len(rows) == 1:
        plot_empty_state(
            "Corpus Size Benchmarks",
            (
                f"FormosanBank current corpus: {format_short(current_tokens)} tokens. "
                "External benchmark counts are marked TBD until exact source-confirmed values "
                "are filled in QC/reference/corpus_benchmarks.json."
            ),
            output_path,
        )
        return

    plot_horizontal_bars(rows, "Corpus Size Benchmarks", output_path)


def write_current_plots(metrics: dict[str, Any], benchmarks: list[dict[str, Any]], output_dir: Path) -> None:
    language_rows = [(language, int(counts["tokens"])) for language, counts in list(metrics["by_language"].items())[:20]]
    source_rows = [(source, int(counts["tokens"])) for source, counts in list(metrics["by_source"].items())[:20]]
    plot_horizontal_bars(language_rows, "Tokens by Language", output_dir / "corpus_language_tokens.png", max_rows=20)
    plot_horizontal_bars(source_rows, "Tokens by Corpus Source", output_dir / "corpus_source_tokens.png", max_rows=20)
    plot_benchmarks(metrics, benchmarks, output_dir / "corpus_benchmark_comparison.png")


def history_commits(repo_root: Path, max_commits: int) -> list[str]:
    args = ["log", "--first-parent", "--no-renames", "--diff-filter=ADM", "--format=%H"]
    if max_commits > 0:
        args.append(f"--max-count={max_commits}")
    args.extend(["HEAD", "--", XML_HISTORY_PATHSPEC])
    raw = git_value(args, repo_root)
    return list(reversed(raw.splitlines())) if raw else []



def commit_date(repo_root: Path, commit: str) -> str:
    return git_value(["show", "-s", "--format=%cI", commit], repo_root) or ""


def history_row(repo_root: Path, commit: str, metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "commit": commit,
        "date": commit_date(repo_root, commit),
        "tokens": metrics["totals"]["tokens"],
        "sentences": metrics["totals"]["sentences"],
        "xml_files": metrics["totals"]["xml_files"],
        "sources": metrics["totals"]["sources"],
        "languages": metrics["totals"]["languages"],
        "parse_errors": metrics["totals"]["parse_errors"],
        "transcribed_audio_seconds": metrics["totals"]["transcribed_audio_seconds"],
        "zho_transl_count": metrics["totals"]["zho_transl_count"],
        "glossed_words": metrics["totals"]["glossed_words"],
    }


def history_row_from_records(
    repo_root: Path,
    commit: str,
    records_by_path: dict[str, dict[str, Any]],
    parse_errors_by_path: dict[str, dict[str, str]],
) -> dict[str, Any]:
    totals, _by_source, _by_language, _by_language_dialect = aggregate_records(
        list(records_by_path.values()),
        list(parse_errors_by_path.values()),
    )
    return {
        "commit": commit,
        "date": commit_date(repo_root, commit),
        "tokens": totals["tokens"],
        "sentences": totals["sentences"],
        "xml_files": totals["xml_files"],
        "sources": totals["sources"],
        "languages": totals["languages"],
        "parse_errors": totals["parse_errors"],
        "transcribed_audio_seconds": totals["transcribed_audio_seconds"],
        "zho_transl_count": totals["zho_transl_count"],
        "glossed_words": totals["glossed_words"],
    }


def changed_xml_files(repo_root: Path, commit: str) -> list[XmlChange]:
    result = run_git_bytes(
        [
            "show",
            "--first-parent",
            "--raw",
            "--abbrev=40",
            "--no-renames",
            "--format=",
            "-z",
            "--diff-filter=ADM",
            commit,
            "--",
            XML_HISTORY_PATHSPEC,
        ],
        repo_root,
    )
    parts = result.stdout.split(b"\0")
    changes: list[XmlChange] = []
    index = 0
    while index + 1 < len(parts):
        meta = parts[index].decode("utf-8", errors="replace").strip()
        path = parts[index + 1].decode("utf-8", errors="replace")
        index += 2
        if not meta or not path:
            continue
        fields = meta.split()
        if len(fields) < 5:
            continue
        status = fields[4][0]
        old_oid = fields[2] if fields[2] != ZERO_OID else None
        new_oid = fields[3] if fields[3] != ZERO_OID else None
        changes.append(XmlChange(status, path, old_oid, new_oid))
    return changes


def read_git_blobs(repo_root: Path, object_ids: list[str]) -> dict[str, bytes]:
    unique_ids = list(dict.fromkeys(object_ids))
    if not unique_ids:
        return {}

    process = subprocess.Popen(
        ["git", "cat-file", "--batch"],
        cwd=repo_root,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate(("\n".join(unique_ids) + "\n").encode("ascii"))
    if process.returncode:
        raise subprocess.CalledProcessError(process.returncode, process.args, output=stdout, stderr=stderr)

    blobs: dict[str, bytes] = {}
    cursor = 0
    for _object_id in unique_ids:
        header_end = stdout.find(b"\n", cursor)
        if header_end == -1:
            break
        header = stdout[cursor:header_end].decode("ascii", errors="replace")
        cursor = header_end + 1
        header_parts = header.split()
        if len(header_parts) < 3:
            continue
        object_id, object_type, size_text = header_parts[:3]
        size = int(size_text)
        content = stdout[cursor:cursor + size]
        cursor += size + 1
        if object_type == "blob":
            blobs[object_id] = content
    return blobs


def records_by_path(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {record["path"]: record for record in records}


def parse_errors_by_path(parse_errors: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {item["path"]: item for item in parse_errors}


def load_history_csv(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        rows = [dict(row) for row in csv.DictReader(f)]
    return [row for row in rows if row.get("commit")]


def append_history_row(repo_root: Path, cache_path: Path, metrics: dict[str, Any]) -> list[dict[str, Any]]:
    """One history row per run, at HEAD, from the current snapshot totals.
    Re-running on the same commit replaces the row instead of duplicating."""
    rows = load_history_csv(cache_path)
    head = metrics["git"].get("commit") or git_value(["rev-parse", "HEAD"], repo_root) or ""
    row = {
        "commit": head,
        "date": commit_date(repo_root, head),
        "tokens": metrics["totals"]["tokens"],
        "sentences": metrics["totals"]["sentences"],
        "xml_files": metrics["totals"]["xml_files"],
        "sources": metrics["totals"]["sources"],
        "languages": metrics["totals"]["languages"],
        "parse_errors": metrics["totals"]["parse_errors"],
        "transcribed_audio_seconds": metrics["totals"]["transcribed_audio_seconds"],
        "zho_transl_count": metrics["totals"]["zho_transl_count"],
        "glossed_words": metrics["totals"]["glossed_words"],
    }
    if rows and rows[-1].get("commit") == head:
        rows[-1] = row
    else:
        rows.append(row)
    return rows


def apply_commit_changes(
    repo_root: Path,
    commit: str,
    records_by_path: dict[str, dict[str, Any]],
    parse_errors_by_path: dict[str, dict[str, str]],
    corpora_path: Path,
    progress_prefix: str = "",
) -> int:
    """Advance the running per-path record/parse-error maps by applying one
    commit's XML diff (vs its first parent), in place. Returns the file count."""
    changes = changed_xml_files(repo_root, commit)
    blob_ids = [change.new_oid for change in changes if change.status != "D" and change.new_oid]
    blobs = read_git_blobs(repo_root, blob_ids)

    for change_index, change in enumerate(changes, start=1):
        if change.status == "D":
            records_by_path.pop(change.path, None)
            parse_errors_by_path.pop(change.path, None)
        else:
            try:
                if not change.new_oid or change.new_oid not in blobs:
                    raise ValueError(f"Could not read git blob for {change.path}")
                record = analyze_xml_bytes(corpora_path, change.path, blobs[change.new_oid])
                records_by_path[change.path] = record
                parse_errors_by_path.pop(change.path, None)
            except Exception as exc:
                records_by_path.pop(change.path, None)
                parse_errors_by_path[change.path] = {"path": change.path, "error": str(exc)}

        if len(changes) >= 1000 and (change_index % 1000 == 0 or change_index == len(changes)):
            progress(f"{progress_prefix}processed {change_index}/{len(changes)} XML changes.")
    return len(changes)


def snapshot_records(
    repo_root: Path,
    commit: str,
    corpora_path: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, str]]]:
    """Analyze every tracked XML file as it existed at `commit`, returning the
    per-path record/parse-error maps — the seed state for an incremental walk."""
    # ls-tree does not accept :(glob) pathspec magic (unlike git show), so list
    # everything under Corpora/ and filter to the same .../XML/.../*.xml set.
    result = run_git_bytes(
        ["ls-tree", "-r", "-z", commit, "--", "Corpora"],
        repo_root,
    )
    oid_by_path: dict[str, str] = {}
    for entry in result.stdout.split(b"\0"):
        if not entry:
            continue
        meta, _, raw_path = entry.partition(b"\t")
        fields = meta.decode("utf-8", errors="replace").split()
        if len(fields) < 3 or fields[1] != "blob":
            continue
        path = raw_path.decode("utf-8", errors="replace")
        parts = path.split("/")
        if not path.endswith(".xml") or "XML" not in parts:
            continue
        oid_by_path[path] = fields[2]

    blobs = read_git_blobs(repo_root, list(oid_by_path.values()))
    records_by_path: dict[str, dict[str, Any]] = {}
    parse_errors_by_path: dict[str, dict[str, str]] = {}
    for path, oid in oid_by_path.items():
        try:
            if oid not in blobs:
                raise ValueError(f"Could not read git blob for {path}")
            records_by_path[path] = analyze_xml_bytes(corpora_path, path, blobs[oid])
        except Exception as exc:
            parse_errors_by_path[path] = {"path": path, "error": str(exc)}
    return records_by_path, parse_errors_by_path


def is_ancestor(repo_root: Path, commit: str, descendant: str = "HEAD") -> bool:
    """True if `commit` is an ancestor of (or equal to) `descendant`."""
    if not commit:
        return False
    proc = run_git(["merge-base", "--is-ancestor", commit, descendant], repo_root, check=False)
    return proc.returncode == 0


def commits_after(repo_root: Path, base_commit: str, max_commits: int) -> list[str]:
    """XML-changing first-parent commits in (base_commit, HEAD], oldest first."""
    args = ["log", "--first-parent", "--no-renames", "--diff-filter=ADM", "--format=%H"]
    if max_commits > 0:
        args.append(f"--max-count={max_commits}")
    args.extend([f"{base_commit}..HEAD", "--", XML_HISTORY_PATHSPEC])
    raw = git_value(args, repo_root)
    return list(reversed(raw.splitlines())) if raw else []


def generate_history(
    repo_root: Path,
    max_commits: int,
    current_metrics: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    rows = []
    commits = history_commits(repo_root, max_commits)
    current_commit = current_metrics.get("git", {}).get("commit") if current_metrics else None
    total_commits = len(commits)
    records_by_path: dict[str, dict[str, Any]] = {}
    parse_errors_by_path: dict[str, dict[str, str]] = {}
    corpora_path = repo_root / "Corpora"

    progress(f"History mode: incrementally sampling {total_commits} XML-changing commit(s).")
    for index, commit in enumerate(commits):
        position = index + 1
        short_commit = commit[:8]
        if current_metrics and commit == current_commit:
            row = history_row(repo_root, commit, current_metrics)
            rows.append(row)
            progress(
                f"[{position}/{total_commits}] {short_commit} reused current checkout: "
                f"{format_short(row['tokens'])} tokens, {format_int(row['xml_files'])} XML files."
            )
            continue

        count = apply_commit_changes(
            repo_root, commit, records_by_path, parse_errors_by_path, corpora_path,
            progress_prefix=f"[{position}/{total_commits}] {short_commit} ",
        )
        row = history_row_from_records(repo_root, commit, records_by_path, parse_errors_by_path)
        rows.append(row)
        progress(
            f"[{position}/{total_commits}] {short_commit} applied {count} change(s): "
            f"{format_short(row['tokens'])} tokens, {format_int(row['xml_files'])} XML files."
        )
    progress(f"History mode complete: wrote {len(rows)} sampled row(s).")
    return rows


def extend_history(
    repo_root: Path,
    cache_path: Path,
    current_metrics: dict[str, Any],
    max_commits: int = 0,
) -> list[dict[str, Any]]:
    """Extend the cached size-over-time CSV by sampling each XML-changing commit
    that landed since the last cached row, seeded from the corpus state at that
    cached commit. Falls back to a single HEAD append when there is no usable
    cache tip (empty/diverged) or no gap to fill (<=1 new commit)."""
    rows = load_history_csv(cache_path)
    base_commit = rows[-1]["commit"] if rows else ""
    head = current_metrics["git"].get("commit") or git_value(["rev-parse", "HEAD"], repo_root) or ""

    if not base_commit:
        progress("History extend: empty cache; appending a single HEAD row.")
        return append_history_row(repo_root, cache_path, current_metrics)
    if not is_ancestor(repo_root, base_commit):
        progress(
            f"History extend: cached tip {base_commit[:8]} is not an ancestor of HEAD; "
            "appending a single HEAD row instead of walking."
        )
        return append_history_row(repo_root, cache_path, current_metrics)

    new_commits = commits_after(repo_root, base_commit, max_commits)
    if len(new_commits) <= 1:
        progress("History extend: no gap to fill (<=1 new XML-changing commit); appending a single HEAD row.")
        return append_history_row(repo_root, cache_path, current_metrics)

    corpora_path = repo_root / "Corpora"
    total = len(new_commits)
    progress(f"History extend: seeding from {base_commit[:8]}, filling {total} new commit(s).")
    records_by_path, parse_errors_by_path = snapshot_records(repo_root, base_commit, corpora_path)

    for index, commit in enumerate(new_commits, start=1):
        short_commit = commit[:8]
        if commit == head:
            row = history_row(repo_root, commit, current_metrics)
        else:
            apply_commit_changes(
                repo_root, commit, records_by_path, parse_errors_by_path, corpora_path,
                progress_prefix=f"[{index}/{total}] {short_commit} ",
            )
            row = history_row_from_records(repo_root, commit, records_by_path, parse_errors_by_path)
        rows.append(row)
        progress(
            f"[{index}/{total}] {short_commit} done: "
            f"{format_short(row['tokens'])} tokens, {format_int(row['xml_files'])} XML files."
        )
    return rows


def write_history_csv(rows: list[dict[str, Any]], output_dir: Path) -> Path:
    path = output_dir / "corpus_size_history.csv"
    fieldnames = ["date", "commit", "tokens", "sentences", "xml_files", "sources",
                  "languages", "parse_errors", "transcribed_audio_seconds",
                  "zho_transl_count", "glossed_words"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


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


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate corpus metrics from FormosanBank XML files.")
    parser.add_argument("corpora_path", nargs="?", default="Corpora", help="Path to the Corpora directory.")
    parser.add_argument("--output-dir", default="corpus_metrics", help="Directory for metrics artifacts.")
    parser.add_argument(
        "--benchmarks",
        default=str(Path(__file__).resolve().parent / "reference" / "corpus_benchmarks.json"),
        help="Optional benchmark JSON file.",
    )
    parser.add_argument("--history", action="store_true", help="Append one history row at HEAD to the size-over-time CSV.")
    parser.add_argument(
        "--history-extend",
        action="store_true",
        help="Resume from the cached size-over-time CSV and add a row for every "
             "XML-changing commit since its last entry (fills gaps cheaply). Falls "
             "back to a single HEAD append when the cache is empty/diverged or there "
             "is no gap.",
    )
    parser.add_argument("--max-history-commits", type=int, default=0, help="Maximum XML-changing commits to sample (with --history-rebuild, or to cap the fill window of --history-extend). Use 0 for no limit.")
    parser.add_argument(
        "--history-cache",
        default=None,
        help="Existing corpus_size_history.csv to read and append to.",
    )
    parser.add_argument("--no-plots", action="store_true", help="Skip PNG plot generation.")
    parser.add_argument("--fail-on-parse-error", action="store_true", help="Exit nonzero if any XML file cannot be parsed.")
    parser.add_argument(
        "--stats-dir",
        default=None,
        help="Aggregate per-corpus CSVs from this directory (written by "
             "QC/utilities/get_corpus_stats.py) instead of parsing XML.",
    )
    parser.add_argument(
        "--history-rebuild",
        action="store_true",
        help="Rebuild the full size-over-time CSV from git history (slow; "
             "restates all rows under the current counting rules).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    corpora_path = Path(args.corpora_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    benchmarks = load_benchmarks(Path(args.benchmarks) if args.benchmarks else None)

    if args.stats_dir:
        progress(f"Aggregating per-corpus CSVs from {args.stats_dir}.")
        current_records, current_parse_errors = read_stats_dir(Path(args.stats_dir))
    else:
        progress(f"Counting current corpus XML from {corpora_path}.")
        current_records, current_parse_errors = collect_corpus_records(corpora_path)
    metrics = build_metrics(corpora_path.resolve(), current_records, current_parse_errors)
    progress(
        "Current corpus counted: "
        f"{format_short(metrics['totals']['tokens'])} tokens, "
        f"{format_int(metrics['totals']['xml_files'])} XML files."
    )
    json_path = write_json(metrics, output_dir)
    md_path = write_markdown(metrics, benchmarks, output_dir)

    if not args.no_plots:
        write_current_plots(metrics, benchmarks, output_dir)

    if args.history_rebuild and args.history_extend:
        print("--history-rebuild and --history-extend are mutually exclusive.", file=sys.stderr)
        return 2

    if args.history_rebuild:
        if args.stats_dir:
            print("--history-rebuild requires XML mode (omit --stats-dir).", file=sys.stderr)
            return 2
        repo_root = repo_root_from(corpora_path.resolve())
        history_rows = generate_history(repo_root, args.max_history_commits, metrics)
        write_history_csv(history_rows, output_dir)
        if not args.no_plots:
            plot_history(history_rows, output_dir)
    elif args.history_extend:
        repo_root = repo_root_from(corpora_path.resolve())
        cache = Path(args.history_cache) if args.history_cache else output_dir / "corpus_size_history.csv"
        history_rows = extend_history(repo_root, cache, metrics, args.max_history_commits)
        write_history_csv(history_rows, output_dir)
        if not args.no_plots:
            plot_history(history_rows, output_dir)
    elif args.history:
        repo_root = repo_root_from(corpora_path.resolve())
        cache = Path(args.history_cache) if args.history_cache else output_dir / "corpus_size_history.csv"
        history_rows = append_history_row(repo_root, cache, metrics)
        write_history_csv(history_rows, output_dir)
        if not args.no_plots:
            plot_history(history_rows, output_dir)

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(
        "Totals: "
        f"{format_int(metrics['totals']['tokens'])} tokens, "
        f"{format_int(metrics['totals']['sentences'])} sentences, "
        f"{format_int(metrics['totals']['xml_files'])} XML files"
    )
    if metrics["parse_errors"]:
        print(f"Parse errors: {len(metrics['parse_errors'])}", file=sys.stderr)
        if args.fail_on_parse_error:
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
) -> tuple[dict[str, int], dict[str, dict[str, int]], dict[str, dict[str, int]], list[dict[str, Any]]]:
    totals = empty_counts()
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


def analyze_corpora(corpora_path: Path) -> dict[str, Any]:
    corpora_path = corpora_path.resolve()
    records, parse_errors = collect_corpus_records(corpora_path)
    return build_metrics(corpora_path, records, parse_errors)


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


def history_commits_after(repo_root: Path, base_commit: str) -> list[str]:
    raw = git_value(
        [
            "log",
            "--first-parent",
            "--no-renames",
            "--diff-filter=ADM",
            "--format=%H",
            f"{base_commit}..HEAD",
            "--",
            XML_HISTORY_PATHSPEC,
        ],
        repo_root,
    )
    return list(reversed(raw.splitlines())) if raw else []


def is_ancestor(repo_root: Path, commit: str) -> bool:
    if not commit:
        return False
    result = run_git(["merge-base", "--is-ancestor", commit, "HEAD"], repo_root, check=False)
    return result.returncode == 0


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


def restore_xml_blob(
    corpora_path: Path,
    path: str,
    content: bytes,
    records: dict[str, dict[str, Any]],
    parse_errors: dict[str, dict[str, str]],
) -> None:
    try:
        records[path] = analyze_xml_bytes(corpora_path, path, content)
        parse_errors.pop(path, None)
    except Exception as exc:
        records.pop(path, None)
        parse_errors[path] = {"path": path, "error": str(exc)}


def roll_back_xml_commit(
    repo_root: Path,
    corpora_path: Path,
    changes: list[XmlChange],
    records: dict[str, dict[str, Any]],
    parse_errors: dict[str, dict[str, str]],
) -> None:
    old_blob_ids = [change.old_oid for change in changes if change.status in {"D", "M"} and change.old_oid]
    old_blobs = read_git_blobs(repo_root, old_blob_ids)

    for change in changes:
        if change.status == "A":
            records.pop(change.path, None)
            parse_errors.pop(change.path, None)
            continue

        if not change.old_oid or change.old_oid not in old_blobs:
            raise ValueError(f"Could not read previous git blob for {change.path}")
        restore_xml_blob(corpora_path, change.path, old_blobs[change.old_oid], records, parse_errors)


def load_history_csv(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        rows = [dict(row) for row in csv.DictReader(f)]
    return [row for row in rows if row.get("commit")]


def cached_history_base(repo_root: Path, rows: list[dict[str, Any]]) -> tuple[int, str] | None:
    for index in range(len(rows) - 1, -1, -1):
        commit = rows[index].get("commit", "")
        if is_ancestor(repo_root, commit):
            return index, commit
    return None


def generate_history_from_cache(
    repo_root: Path,
    cache_path: Path,
    current_records: list[dict[str, Any]],
    current_parse_errors: list[dict[str, str]],
) -> list[dict[str, Any]] | None:
    cached_rows = load_history_csv(cache_path)
    if not cached_rows:
        progress(f"History cache not found at {cache_path}; generating full history.")
        return None

    base = cached_history_base(repo_root, cached_rows)
    if not base:
        progress(f"History cache at {cache_path} has no commit on this branch; generating full history.")
        return None

    base_index, base_commit = base
    rows = cached_rows[: base_index + 1]
    new_commits = history_commits_after(repo_root, base_commit)
    if not new_commits:
        progress(f"History cache is current through {base_commit[:8]}; no new XML-changing commits.")
        return rows

    corpora_path = repo_root / "Corpora"
    records = records_by_path(current_records)
    parse_errors = parse_errors_by_path(current_parse_errors)
    rows_by_commit: dict[str, dict[str, Any]] = {}
    total_commits = len(new_commits)

    progress(
        f"History cache found {len(rows)} existing row(s) through {base_commit[:8]}; "
        f"updating {total_commits} new XML-changing commit(s)."
    )
    for reverse_index, commit in enumerate(reversed(new_commits), start=1):
        short_commit = commit[:8]
        changes = changed_xml_files(repo_root, commit)
        row = history_row_from_records(repo_root, commit, records, parse_errors)
        rows_by_commit[commit] = row
        progress(
            f"[{reverse_index}/{total_commits}] {short_commit} cached row: "
            f"{format_short(row['tokens'])} tokens, {format_int(row['xml_files'])} XML files; "
            f"rolling back {len(changes)} XML change(s)."
        )
        roll_back_xml_commit(repo_root, corpora_path, changes, records, parse_errors)

    new_rows = [rows_by_commit[commit] for commit in new_commits]
    progress(f"History cache update complete: kept {len(rows)} row(s), appended {len(new_rows)} row(s).")
    return rows + new_rows


def generate_history(
    repo_root: Path,
    max_commits: int,
    current_metrics: dict[str, Any] | None = None,
    current_records: list[dict[str, Any]] | None = None,
    current_parse_errors: list[dict[str, str]] | None = None,
    cache_path: Path | None = None,
) -> list[dict[str, Any]]:
    if cache_path and max_commits == 0 and current_records is not None and current_parse_errors is not None:
        cached_rows = generate_history_from_cache(repo_root, cache_path, current_records, current_parse_errors)
        if cached_rows is not None:
            return cached_rows
    elif cache_path and max_commits > 0:
        progress("History cache ignored because --max-history-commits is set.")

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

        changes = changed_xml_files(repo_root, commit)
        progress(f"[{position}/{total_commits}] {short_commit} applying {len(changes)} XML file change(s).")
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
                progress(f"[{position}/{total_commits}] {short_commit} processed {change_index}/{len(changes)} XML changes.")

        row = history_row_from_records(repo_root, commit, records_by_path, parse_errors_by_path)
        rows.append(row)
        progress(
            f"[{position}/{total_commits}] {short_commit} done: "
            f"{format_short(row['tokens'])} tokens, {format_int(row['xml_files'])} XML files."
        )
    progress(f"History mode complete: wrote {len(rows)} sampled row(s).")
    return rows


def write_history_csv(rows: list[dict[str, Any]], output_dir: Path) -> Path:
    path = output_dir / "corpus_size_history.csv"
    fieldnames = ["date", "commit", "tokens", "sentences", "xml_files", "sources", "languages", "parse_errors"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def plot_history(rows: list[dict[str, Any]], output_dir: Path) -> None:
    if not rows:
        plot_empty_state("FormosanBank Size Over Time", "No history rows were generated.", output_dir / "corpus_size_over_time.png")
        return

    plt = require_matplotlib()
    dates = []
    tokens = []
    for row in rows:
        if not row["date"]:
            continue
        dates.append(dt.datetime.fromisoformat(row["date"].replace("Z", "+00:00")))
        tokens.append(int(row["tokens"]))
    if not dates:
        plot_empty_state("FormosanBank Size Over Time", "No dated history rows were available.", output_dir / "corpus_size_over_time.png")
        return

    fig, ax = plt.subplots(figsize=(11, 5.8), facecolor=PLOT_BG)
    ax.set_facecolor(PLOT_BG)
    ax.plot(dates, tokens, color=PLOT_COLORS[0], marker="o", markersize=5, linewidth=2.4)
    ax.fill_between(dates, tokens, min(tokens), color=PLOT_COLORS[0], alpha=0.12)
    ax.set_title("FormosanBank Size Over Time", loc="left", fontsize=18, fontweight="bold", color=PLOT_TEXT, pad=16)
    ax.text(
        0,
        1.01,
        f"{len(tokens)} XML-changing commits sampled.",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=10,
        color=PLOT_MUTED,
    )
    ax.set_ylabel("Tokens", color=PLOT_MUTED, labelpad=10)
    ax.grid(color=PLOT_GRID, linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(lambda value, _pos: format_short(value))
    ax.tick_params(axis="x", colors=PLOT_MUTED, labelsize=9)
    ax.tick_params(axis="y", colors=PLOT_MUTED, labelsize=9)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(PLOT_GRID)
    ax.spines["bottom"].set_color(PLOT_GRID)
    ax.annotate(
        format_short(tokens[-1]),
        xy=(dates[-1], tokens[-1]),
        xytext=(8, 0),
        textcoords="offset points",
        va="center",
        fontsize=10,
        color=PLOT_TEXT,
        fontweight="bold",
    )
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_dir / "corpus_size_over_time.png", dpi=180, bbox_inches="tight", facecolor=PLOT_BG)
    plt.close(fig)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate corpus metrics from FormosanBank XML files.")
    parser.add_argument("corpora_path", nargs="?", default="Corpora", help="Path to the Corpora directory.")
    parser.add_argument("--output-dir", default="corpus_metrics", help="Directory for metrics artifacts.")
    parser.add_argument(
        "--benchmarks",
        default=str(Path(__file__).resolve().parent / "reference" / "corpus_benchmarks.json"),
        help="Optional benchmark JSON file.",
    )
    parser.add_argument("--history", action="store_true", help="Generate a size-over-time CSV and plot from git history.")
    parser.add_argument("--max-history-commits", type=int, default=0, help="Maximum XML-changing commits to sample. Use 0 for full history.")
    parser.add_argument(
        "--history-cache",
        default=None,
        help="Existing corpus_size_history.csv to update incrementally when full history is requested.",
    )
    parser.add_argument("--no-plots", action="store_true", help="Skip PNG plot generation.")
    parser.add_argument("--fail-on-parse-error", action="store_true", help="Exit nonzero if any XML file cannot be parsed.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    corpora_path = Path(args.corpora_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    benchmarks = load_benchmarks(Path(args.benchmarks) if args.benchmarks else None)
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

    if args.history:
        repo_root = repo_root_from(corpora_path.resolve())
        history_rows = generate_history(
            repo_root,
            args.max_history_commits,
            metrics,
            current_records=current_records,
            current_parse_errors=current_parse_errors,
            cache_path=Path(args.history_cache) if args.history_cache else None,
        )
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

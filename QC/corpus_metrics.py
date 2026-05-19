#!/usr/bin/env python3
"""Generate FormosanBank corpus metrics from XML files under Corpora/."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

LANG_CODE_TO_NAME = {
    "ami": "Amis",
    "tay": "Atayal",
    "pwn": "Paiwan",
    "bnn": "Bunun",
    "pyu": "Puyuma",
    "dru": "Rukai",
    "tsu": "Tsou",
    "xsy": "Saisiyat",
    "tao": "Yami",
    "ssf": "Thao",
    "ckv": "Kavalan",
    "trv": "Seediq",
    "szy": "Sakizaya",
    "sxr": "Saaroa",
    "xnb": "Kanakanavu",
    "fos": "Siraya",
}

KNOWN_LANGUAGES = {
    "Amis",
    "Atayal",
    "Paiwan",
    "Bunun",
    "Puyuma",
    "Rukai",
    "Tsou",
    "Saisiyat",
    "Yami",
    "Thao",
    "Kavalan",
    "Truku",
    "Sakizaya",
    "Seediq",
    "Saaroa",
    "Kanakanavu",
    "Siraya",
}

COUNT_FIELDS = (
    "tokens",
    "sentences",
    "xml_files",
    "word_elements",
    "morpheme_elements",
    "translation_elements",
    "audio_elements",
)

XML_HISTORY_PATHSPEC = ":(glob)Corpora/**/*.xml"
PLOT_BG = "#fbfbf8"
PLOT_TEXT = "#24292f"
PLOT_MUTED = "#6e7781"
PLOT_GRID = "#d8dee4"
PLOT_COLORS = ["#4f6f91", "#2f7f73", "#c58b2a", "#b05c4b", "#7467a8", "#3f8f9f"]

DEFAULT_BENCHMARKS = [
    {
        "name": "Brown Corpus",
        "tokens": 1000000,
        "unit": "words",
        "source": "CoRD Brown Corpus overview",
        "url": "https://varieng.helsinki.fi/CoRD/corpora/BROWN/",
        "note": "Rounded benchmark; Brown is commonly described as over one million words.",
    },
    {
        "name": "Penn Treebank WSJ",
        "tokens": 1000000,
        "unit": "words",
        "source": "LDC Treebank-3 catalog entry",
        "url": "https://catalog.ldc.upenn.edu/LDC99T42",
        "note": "Rounded benchmark for the one-million-word Wall Street Journal material.",
    },
]


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


def language_from_path(corpora_path: Path, xml_file: Path) -> str | None:
    language_lookup = {lang.casefold(): lang for lang in KNOWN_LANGUAGES}
    try:
        parts = xml_file.relative_to(corpora_path).parts
    except ValueError:
        parts = xml_file.parts
    for part in parts:
        language = language_lookup.get(part.casefold())
        if language:
            return language
    return None


def language_for(root: ET.Element, corpora_path: Path, xml_file: Path) -> tuple[str, str | None]:
    path_language = language_from_path(corpora_path, xml_file)
    if path_language:
        return path_language, root.get(XML_LANG)

    lang_code = (root.get(XML_LANG) or "").lower()
    if lang_code in LANG_CODE_TO_NAME:
        return LANG_CODE_TO_NAME[lang_code], lang_code
    return f"Unknown ({lang_code})" if lang_code else "Unknown", lang_code or None


def dialect_for(root: ET.Element) -> str:
    dialect = (root.get("dialect") or "").strip()
    return dialect or "Not Specified"


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def select_sentence_form(sentence: ET.Element, form_kind: str) -> str | None:
    forms = sentence.findall("FORM")
    if not forms:
        return None

    if form_kind == "first":
        for form in forms:
            if form.text and form.text.strip():
                return form.text
        return None

    preferred_kinds = [form_kind]
    if form_kind == "auto":
        preferred_kinds = ["standard", "original"]

    for kind in preferred_kinds:
        for form in forms:
            if form.get("kindOf") == kind and form.text and form.text.strip():
                return form.text

    if form_kind == "auto":
        for form in forms:
            if form.text and form.text.strip():
                return form.text
    return None


def analyze_xml_file(corpora_path: Path, xml_file: Path, form_kind: str) -> dict[str, Any]:
    tree = ET.parse(xml_file)
    root = tree.getroot()
    language, language_code = language_for(root, corpora_path, xml_file)
    dialect = dialect_for(root)

    sentences = root.findall(".//S")
    tokens = 0
    for sentence in sentences:
        form_text = select_sentence_form(sentence, form_kind)
        if form_text:
            tokens += word_count(form_text)

    return {
        "source": source_for(corpora_path, xml_file),
        "language": language,
        "language_code": language_code,
        "dialect": dialect,
        "path": str(xml_file.relative_to(corpora_path.parent)),
        "tokens": tokens,
        "sentences": len(sentences),
        "xml_files": 1,
        "word_elements": len(root.findall(".//W")),
        "morpheme_elements": len(root.findall(".//M")),
        "translation_elements": len(root.findall(".//TRANSL")),
        "audio_elements": len(root.findall(".//AUDIO")),
    }


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


def analyze_corpora(corpora_path: Path, form_kind: str = "first") -> dict[str, Any]:
    corpora_path = corpora_path.resolve()
    records: list[dict[str, Any]] = []
    parse_errors: list[dict[str, str]] = []

    for xml_file in find_xml_files(corpora_path):
        try:
            records.append(analyze_xml_file(corpora_path, xml_file, form_kind))
        except Exception as exc:
            parse_errors.append(
                {
                    "path": str(xml_file.relative_to(corpora_path.parent)),
                    "error": str(exc),
                }
            )

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

    return {
        "generated_at": now_utc(),
        "corpora_path": str(corpora_path),
        "form_kind": form_kind,
        "git": {
            "commit": os.environ.get("GITHUB_SHA")
            or git_value(["rev-parse", "HEAD"], corpora_path),
            "ref": os.environ.get("GITHUB_REF_NAME")
            or git_value(["branch", "--show-current"], corpora_path),
        },
        "totals": totals,
        "by_source": sorted_counts_map(by_source),
        "by_language": sorted_counts_map(by_language),
        "by_language_dialect": sorted_dialect_counts(by_language_dialect),
        "parse_errors": parse_errors,
    }


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
        f"Token source: sentence-level `FORM` elements using form mode `{metrics['form_kind']}`.",
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
    raw = git_value(
        [
            "log",
            "--first-parent",
            "--diff-filter=ADM",
            "--format=%H",
            f"--max-count={max_commits}",
            "HEAD",
            "--",
            XML_HISTORY_PATHSPEC,
        ],
        repo_root,
    )
    commits = list(reversed(raw.splitlines())) if raw else []
    head = git_value(["rev-parse", "HEAD"], repo_root)
    if head and head not in commits:
        commits.append(head)
    return commits


def commit_date(repo_root: Path, commit: str) -> str:
    return git_value(["show", "-s", "--format=%cI", commit], repo_root) or ""


def add_worktree(repo_root: Path, commit: str, path: Path) -> None:
    run_git(["worktree", "add", "--detach", "--quiet", str(path), commit], repo_root)


def remove_worktree(repo_root: Path, path: Path) -> None:
    result = run_git(["worktree", "remove", "--force", str(path)], repo_root, check=False)
    if result.returncode != 0 and path.exists():
        shutil.rmtree(path)


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


def generate_history(
    repo_root: Path,
    form_kind: str,
    max_commits: int,
    current_metrics: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    rows = []
    commits = history_commits(repo_root, max_commits)
    current_commit = current_metrics.get("git", {}).get("commit") if current_metrics else None
    total_commits = len(commits)
    progress(f"History mode: sampling {total_commits} XML-changing commit(s).")
    with tempfile.TemporaryDirectory(prefix="formosanbank-metrics-") as tmp:
        tmp_root = Path(tmp)
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

            worktree = tmp_root / f"commit-{index}"
            try:
                progress(f"[{position}/{total_commits}] {short_commit} checking out temporary worktree.")
                add_worktree(repo_root, commit, worktree)
                corpora_path = worktree / "Corpora"
                if not corpora_path.exists():
                    progress(f"[{position}/{total_commits}] {short_commit} skipped: no Corpora directory.")
                    continue
                progress(f"[{position}/{total_commits}] {short_commit} counting Corpora XML.")
                metrics = analyze_corpora(corpora_path, form_kind=form_kind)
                row = history_row(repo_root, commit, metrics)
                rows.append(row)
                progress(
                    f"[{position}/{total_commits}] {short_commit} done: "
                    f"{format_short(row['tokens'])} tokens, {format_int(row['xml_files'])} XML files."
                )
            finally:
                if worktree.exists():
                    remove_worktree(repo_root, worktree)
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
        "--form-kind",
        choices=["first", "auto", "standard", "original"],
        default="first",
        help="Sentence-level FORM selection mode. 'first' matches the legacy token counter.",
    )
    parser.add_argument(
        "--benchmarks",
        default=str(Path(__file__).resolve().parent / "reference" / "corpus_benchmarks.json"),
        help="Optional benchmark JSON file.",
    )
    parser.add_argument("--history", action="store_true", help="Generate a size-over-time CSV and plot from git history.")
    parser.add_argument("--max-history-commits", type=int, default=12, help="Maximum Corpora-changing commits to sample.")
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
    metrics = analyze_corpora(corpora_path, form_kind=args.form_kind)
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
        history_rows = generate_history(repo_root, args.form_kind, args.max_history_commits, metrics)
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

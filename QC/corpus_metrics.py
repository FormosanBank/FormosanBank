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

    return plt


def plot_horizontal_bars(rows: list[tuple[str, int]], title: str, output_path: Path) -> None:
    if not rows:
        return

    plt = require_matplotlib()
    rows = sorted(rows, key=lambda item: item[1])
    labels = [row[0] for row in rows]
    values = [row[1] for row in rows]
    height = max(4, min(14, 0.42 * len(rows) + 1.5))

    fig, ax = plt.subplots(figsize=(10, height))
    ax.barh(labels, values, color="#4C78A8")
    ax.set_title(title)
    ax.set_xlabel("Tokens")
    ax.grid(axis="x", alpha=0.25)
    ax.bar_label(ax.containers[0], labels=[format_int(v) for v in values], padding=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_benchmarks(metrics: dict[str, Any], benchmarks: list[dict[str, Any]], output_path: Path) -> None:
    current_tokens = int(metrics["totals"]["tokens"])
    rows = [("FormosanBank current", current_tokens)]
    rows.extend(
        (benchmark["name"], int(benchmark["tokens"]))
        for benchmark in benchmarks
        if benchmark.get("tokens") is not None
    )
    plot_horizontal_bars(rows, "Corpus Size Benchmarks", output_path)


def write_current_plots(metrics: dict[str, Any], benchmarks: list[dict[str, Any]], output_dir: Path) -> None:
    language_rows = [(language, int(counts["tokens"])) for language, counts in list(metrics["by_language"].items())[:20]]
    source_rows = [(source, int(counts["tokens"])) for source, counts in list(metrics["by_source"].items())[:20]]
    plot_horizontal_bars(language_rows, "Tokens by Language", output_dir / "corpus_language_tokens.png")
    plot_horizontal_bars(source_rows, "Tokens by Corpus Source", output_dir / "corpus_source_tokens.png")
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
    with tempfile.TemporaryDirectory(prefix="formosanbank-metrics-") as tmp:
        tmp_root = Path(tmp)
        for index, commit in enumerate(commits):
            if current_metrics and commit == current_commit:
                rows.append(history_row(repo_root, commit, current_metrics))
                continue

            worktree = tmp_root / f"commit-{index}"
            try:
                add_worktree(repo_root, commit, worktree)
                corpora_path = worktree / "Corpora"
                if not corpora_path.exists():
                    continue
                metrics = analyze_corpora(corpora_path, form_kind=form_kind)
                rows.append(history_row(repo_root, commit, metrics))
            finally:
                if worktree.exists():
                    remove_worktree(repo_root, worktree)
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
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(dates, tokens, color="#4C78A8", marker="o", linewidth=2)
    ax.set_title("FormosanBank Size Over Time")
    ax.set_ylabel("Tokens")
    ax.grid(alpha=0.25)
    ax.yaxis.set_major_formatter(lambda value, _pos: format_int(value))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_dir / "corpus_size_over_time.png", dpi=180)
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
    metrics = analyze_corpora(corpora_path, form_kind=args.form_kind)
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

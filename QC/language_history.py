#!/usr/bin/env python3
"""Per-corpus, per-language word-count history, reconstructed from git.

One row per (commit, corpus, language, dialect) for every first-parent commit
on the current branch that changed published corpus XML. The documentation
site draws its growth figures from this file (statistics/language_history.csv):
per language, and summed over all languages with and without a corpus.

    python QC/language_history.py rebuild --csv statistics/language_history.csv
    python QC/language_history.py extend  --csv statistics/language_history.csv

``rebuild`` walks the whole history (once; about 130,000 file versions as of
2026-10). ``extend`` resumes from the CSV's last commit and adds only newer
commits; if that commit is no longer an ancestor of HEAD (main was reset or
force-pushed) it rebuilds instead, rather than append rows that don't belong
to this history.

Counts come from corpus_counts.analyze_root, the single source of counting
rules, applied to every past commit -- so the lines don't jump where the rules
changed. A file's corpus is its Corpora/<dir> at that commit; its language and
dialect are what its xml:lang and dialect attributes said then (no dialect ->
"unknown"). Each git blob is parsed once, however many commits contain it.
"""

from __future__ import annotations

import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import corpus_counts  # noqa: E402
import corpus_metrics  # noqa: E402  (git helpers; imported, not changed)

HISTORY_FIELDS = (
    "date", "commit", "corpus", "language", "dialect",
    "words", "transcribed_words", "segmented_words", "glossed_words",
    "zho_transl_count", "eng_transl_count",
)
VALUE_FIELDS = HISTORY_FIELDS[5:]
SOURCE_FIELDS = {
    "words": "word_count",
    "transcribed_words": "transcribed_words",
    "segmented_words": "segmented_words",
    "glossed_words": "glossed_words",
    "zho_transl_count": "zho_transl_count",
    "eng_transl_count": "eng_transl_count",
}
UNKNOWN_DIALECT = "unknown"


def progress(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def record_for(path: str, content: bytes) -> dict:
    """The counted values of one XML file version, keyed for aggregation."""
    record = corpus_counts.analyze_root(ET.fromstring(content))
    code, dialect = record["language"], record["dialect"]
    language = corpus_counts.resolve_language(code, dialect)
    if language is None:
        language = f"Unknown ({code})" if code else "Unknown"
    values = {field: record[source] for field, source in SOURCE_FIELDS.items()}
    return {
        "corpus": path.split("/")[1],
        "language": language,
        "dialect": dialect or UNKNOWN_DIALECT,
        **values,
    }


class Walker:
    """Corpus state (path -> record) advanced commit by commit, with a blob memo."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.memo: dict[str, dict | None] = {}
        self.state: dict[str, dict] = {}
        self.parse_errors = 0

    def _records(self, items: list[tuple[str, str]]) -> dict[str, dict | None]:
        """(path, blob id) -> record, reading and parsing only unseen blobs."""
        missing = [oid for _path, oid in items if oid not in self.memo]
        blobs = corpus_metrics.read_git_blobs(self.repo_root, missing) if missing else {}
        for path, oid in items:
            if oid in self.memo:
                continue
            try:
                self.memo[oid] = record_for(path, blobs[oid])
            except Exception as exc:  # malformed XML at some past commit
                progress(f"  parse error in {path} ({oid[:8]}): {exc}")
                self.parse_errors += 1
                self.memo[oid] = None
        return {path: self.memo[oid] for path, oid in items}

    def _set(self, path: str, record: dict | None) -> None:
        if record is None:
            self.state.pop(path, None)
        else:
            # A corpus is named by the path it sits at in *this* commit.
            self.state[path] = {**record, "corpus": path.split("/")[1]}

    def seed(self, commit: str) -> None:
        """Load the whole corpus as it was at ``commit``."""
        listing = corpus_metrics.run_git_bytes(
            ["ls-tree", "-r", "-z", commit, "--", "Corpora"], self.repo_root
        ).stdout
        items = []
        for entry in listing.split(b"\0"):
            if not entry:
                continue
            meta, _, raw = entry.partition(b"\t")
            fields = meta.decode().split()
            path = raw.decode("utf-8", errors="replace")
            if len(fields) >= 3 and fields[1] == "blob" and corpus_counts.is_published_xml(path):
                items.append((path, fields[2]))
        self.state = {}
        for path, record in self._records(items).items():
            self._set(path, record)

    def apply(self, commit: str) -> int:
        """Apply one commit's XML changes (against its first parent)."""
        changes = corpus_metrics.changed_xml_files(self.repo_root, commit)
        updated = [
            (c.path, c.new_oid) for c in changes
            if c.status != "D" and c.new_oid and corpus_counts.is_published_xml(c.path)
        ]
        for change in changes:
            if change.status == "D":
                self.state.pop(change.path, None)
        for path, record in self._records(updated).items():
            self._set(path, record)
        return len(changes)

    def rows(self, commit: str) -> list[dict]:
        totals: dict[tuple, dict] = defaultdict(lambda: dict.fromkeys(VALUE_FIELDS, 0))
        for record in self.state.values():
            bucket = totals[(record["corpus"], record["language"], record["dialect"])]
            for field in VALUE_FIELDS:
                bucket[field] += record[field]
        date = corpus_metrics.commit_date(self.repo_root, commit)
        return [
            {"date": date, "commit": commit, "corpus": corpus, "language": language,
             "dialect": dialect, **values}
            for (corpus, language, dialect), values in sorted(totals.items())
        ]


def _walk(walker: Walker, commits: list[str]) -> list[dict]:
    rows: list[dict] = []
    for index, commit in enumerate(commits, start=1):
        changed = walker.apply(commit)
        commit_rows = walker.rows(commit)
        rows.extend(commit_rows)
        words = sum(row["words"] for row in commit_rows)
        progress(
            f"[{index}/{len(commits)}] {commit[:9]} {changed} XML change(s); "
            f"{words:,} words; {len(walker.memo):,} blobs parsed"
        )
    return rows


def rebuild(repo_root: Path) -> list[dict]:
    """History rows for every XML-changing first-parent commit up to HEAD."""
    repo_root = Path(repo_root)
    commits = corpus_metrics.history_commits(repo_root, 0)
    progress(f"rebuild: {len(commits)} XML-changing commit(s)")
    return _walk(Walker(repo_root), commits)


def _as_text(rows: list[dict]) -> list[dict]:
    return [{field: str(row[field]) for field in HISTORY_FIELDS} for row in rows]


def load_csv(path: Path) -> list[dict]:
    if not Path(path).is_file():
        return []
    with open(path, newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(rows: list[dict], path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HISTORY_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(_as_text(rows))


def extend(repo_root: Path, csv_path: Path) -> list[dict]:
    """The cached rows plus rows for XML-changing commits after the cached tip."""
    repo_root = Path(repo_root)
    rows = load_csv(csv_path)
    tip = rows[-1]["commit"] if rows else ""
    if not tip or not corpus_metrics.is_ancestor(repo_root, tip):
        progress(
            f"extend: cached tip {tip[:9] or '(none)'} is not an ancestor of HEAD; rebuilding"
        )
        return _as_text(rebuild(repo_root))
    commits = corpus_metrics.commits_after(repo_root, tip, 0)
    if not commits:
        progress("extend: no new XML-changing commits")
        return rows
    progress(f"extend: seeding from {tip[:9]}, adding {len(commits)} commit(s)")
    walker = Walker(repo_root)
    walker.seed(tip)
    return rows + _as_text(_walk(walker, commits))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=("rebuild", "extend"))
    parser.add_argument("--csv", type=Path, default=Path("statistics/language_history.csv"))
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    rows = rebuild(args.repo) if args.mode == "rebuild" else extend(args.repo, args.csv)
    write_csv(rows, args.csv)
    progress(f"wrote {len(rows):,} row(s) to {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

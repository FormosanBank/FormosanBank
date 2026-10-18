"""Statistics tables for the documentation site, read from ``statistics/*.csv``.

The per-corpus CSVs are written by ``QC/utilities/get_corpus_stats.py`` (run by
the corpus-metrics workflow on every push to main). This module only reads
them: tables are rendered when the site is built and never committed, so a
page can't show numbers older than the CSVs it was built from.

Language identity comes from ``QC/corpus_counts.resolve_language`` (xml:lang
plus dialect; trv + Truku is Truku). Whether a language gets a per-dialect
table comes from ``dialects.csv``: two or more listed dialects.
"""

from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "QC"))
import corpus_counts  # noqa: E402

STATS_SUFFIX = "_corpora_stats.csv"
UNKNOWN_DIALECT = "unknown"
INDENT = "&nbsp;" * 8

NUMERIC_FIELDS = (
    "word_count",
    "transcribed_words",
    "transcribed_audio_seconds",
    "untranscribed_audio_seconds",
    "eng_transl_count",
    "zho_transl_count",
    "jpn_transl_count",
    "nld_transl_count",
    "segmented_words",
    "glossed_words",
)
NOT_YET_COMPUTED = (
    "*Statistics for this corpus have not been computed yet. They appear "
    "automatically once the corpus-metrics workflow has run on `main`.*"
)


def fmt_count(value) -> str:
    """58782 -> '58,782'; a missing value -> '—'."""
    if value is None:
        return "—"
    return f"{int(value):,}"


def fmt_audio(seconds) -> str:
    """48071.9 -> '13.4h'; zero -> '0'; missing -> '—'."""
    if seconds is None:
        return "—"
    if seconds == 0:
        return "0"
    return f"{seconds / 3600:.1f}h"


def _audio_total(bucket: dict) -> float | None:
    parts = [bucket.get("transcribed_audio_seconds"), bucket.get("untranscribed_audio_seconds")]
    if all(part is None for part in parts):
        return None
    return sum(part or 0 for part in parts)


# (label, value function, formatter). Labels are English; the translated
# editions look them up in docs/translations/labels.tsv.
ROW_DEFS = (
    ("Word count", lambda b: b.get("word_count"), fmt_count),
    (f"{INDENT}Transcribed words", lambda b: b.get("transcribed_words"), fmt_count),
    ("Total audio", _audio_total, fmt_audio),
    (f"{INDENT}Transcribed", lambda b: b.get("transcribed_audio_seconds"), fmt_audio),
    (f"{INDENT}Untranscribed", lambda b: b.get("untranscribed_audio_seconds"), fmt_audio),
    ("Translated words", None, None),
    (f"{INDENT}English", lambda b: b.get("eng_transl_count"), fmt_count),
    (f"{INDENT}Mandarin", lambda b: b.get("zho_transl_count"), fmt_count),
    (f"{INDENT}Japanese", lambda b: b.get("jpn_transl_count"), fmt_count),
    (f"{INDENT}Dutch", lambda b: b.get("nld_transl_count"), fmt_count),
    ("Morphologically segmented", lambda b: b.get("segmented_words"), fmt_count),
    ("Glossed words", lambda b: b.get("glossed_words"), fmt_count),
)


def _number(value: str | None):
    if value is None or value == "":
        return None
    number = float(value)
    return int(number) if number.is_integer() else number


def load_stats(stats_dir: Path) -> list[dict]:
    """Every row of every per-corpus CSV, with ``corpus`` and ``language_name`` added.

    Rows with no language and no words (the parse-error placeholder) are
    dropped. A language code with no name in languages.csv is an error: a
    page must never show a bare ISO code.
    """
    rows: list[dict] = []
    for path in sorted(Path(stats_dir).glob(f"*{STATS_SUFFIX}")):
        corpus = path.name[: -len(STATS_SUFFIX)]
        with open(path, newline="", encoding="utf-8") as handle:
            for raw in csv.DictReader(handle):
                row = {field: _number(raw.get(field)) for field in NUMERIC_FIELDS}
                code = (raw.get("language") or "").strip().lower()
                dialect = (raw.get("dialect") or "").strip()
                if not code and not row["word_count"]:
                    continue
                name = corpus_counts.resolve_language(code, dialect)
                if name is None:
                    raise KeyError(
                        f"{path.name}: language code {code!r} has no name in languages.csv"
                    )
                row.update(corpus=corpus, language=code, dialect=dialect, language_name=name)
                rows.append(row)
    return rows


def _has_data(row: dict) -> bool:
    return any(row.get(field) for field in NUMERIC_FIELDS)


def multi_dialect_languages(dialects_csv: Path | None = None) -> set[str]:
    """Languages (display names) with two or more dialects in dialects.csv."""
    path = dialects_csv or REPO_ROOT / "dialects.csv"
    counts: dict[str, int] = defaultdict(int)
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            counts[row["Language"].strip()] += 1
    return {language for language, count in counts.items() if count >= 2}


def dialect_label(row: dict) -> str:
    return row["dialect"] or UNKNOWN_DIALECT


def aggregate(rows: list[dict], key) -> dict:
    """Sum the numeric fields of ``rows`` grouped by ``key(row)``.

    A field stays None for a group only when every row in it lacks the
    column (an older CSV written before the column existed).
    """
    buckets: dict = {}
    for row in rows:
        bucket = buckets.setdefault(key(row), {field: None for field in NUMERIC_FIELDS})
        for field in NUMERIC_FIELDS:
            value = row.get(field)
            if value is not None:
                bucket[field] = (bucket[field] or 0) + value
    return buckets


def markdown_table(headers: list[str], buckets: list[dict]) -> str:
    lines = [
        "| | " + " | ".join(headers) + " |",
        "| --- | " + " | ".join("---" for _ in headers) + " |",
    ]
    for label, value, formatter in ROW_DEFS:
        if value is None:
            cells = ["" for _ in buckets]
        else:
            cells = [formatter(value(bucket)) for bucket in buckets]
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def corpus_table(rows: list[dict], corpus: str, multi: set[str] | None = None) -> str:
    """One column per language (and dialect, for multi-dialect languages) in one corpus."""
    multi = multi_dialect_languages() if multi is None else multi
    corpus_rows = [row for row in rows if row["corpus"] == corpus and _has_data(row)]
    if not corpus_rows:
        return NOT_YET_COMPUTED

    def key(row):
        if row["language_name"] in multi:
            return (row["language_name"], dialect_label(row))
        return (row["language_name"], "")

    buckets = aggregate(corpus_rows, key)
    keys = sorted(buckets)
    headers = [name if not dialect else f"{name}<br>{dialect}" for name, dialect in keys]
    return markdown_table(headers, [buckets[k] for k in keys])


def language_table(rows: list[dict], link=None) -> str:
    """One column per language, summed over all corpora (and dialects).

    ``link(language_name)`` optionally returns a URL to wrap the header in.
    """
    buckets = aggregate([row for row in rows if _has_data(row)], lambda row: row["language_name"])
    names = sorted(buckets)
    headers = [f"[{name}]({link(name)})" if link else name for name in names]
    return markdown_table(headers, [buckets[name] for name in names])


def dialect_table(rows: list[dict], language: str | None = None, multi: set[str] | None = None) -> str | None:
    """One column per dialect of multi-dialect languages (one language, or all).

    Files without a dialect attribute form the ``unknown`` column. Returns None
    when the requested language has fewer than two dialects in dialects.csv.
    """
    multi = multi_dialect_languages() if multi is None else multi
    if language is not None and language not in multi:
        return None
    selected = [
        row for row in rows
        if _has_data(row) and row["language_name"] in multi
        and (language is None or row["language_name"] == language)
    ]
    if not selected:
        return None
    buckets = aggregate(selected, lambda row: (row["language_name"], dialect_label(row)))
    keys = sorted(buckets, key=lambda k: (k[0], k[1] == UNKNOWN_DIALECT, k[1]))
    if language is None:
        headers = [f"{name}<br>{dialect}" for name, dialect in keys]
    else:
        headers = [dialect for _name, dialect in keys]
    return markdown_table(headers, [buckets[k] for k in keys])


STATS_START = "<!-- CORPUS STATS START -->"
STATS_END = "<!-- CORPUS STATS END -->"
CORPUS_LIST = re.compile(r"(?m)(?:^\* \[[^\]]+\]\([^)]+\.md\).*\n)+")


def fill_corpora_index(text: str, rows: list[dict], pages, link=None, figures: str = "") -> str:
    """Regenerate the corpus list and the statistics block of the corpora index page."""
    bullets = "".join(
        f"* [{page.nav_label}]({page.slug}.md)"
        + (f" ({page.descriptors})" if page.descriptors else "")
        + "\n"
        for page in pages
    )
    if not CORPUS_LIST.search(text):
        raise ValueError("corpora index page has no corpus list to regenerate")
    text = CORPUS_LIST.sub(lambda _m: bullets, text, count=1)

    start, end = text.find(STATS_START), text.find(STATS_END)
    if start == -1 or end == -1:
        raise ValueError("corpora index page has no statistics markers")
    block = (
        f"{STATS_START}\n### Corpus Statistics\n\n"
        + (f"{figures.strip()}\n\n" if figures else "")
        + f"#### By language\n\n{language_table(rows, link)}\n\n"
        + f"#### By dialect\n\n{dialect_table(rows) or ''}\n\n***\n\n"
    )
    return text[:start] + block + text[end:]

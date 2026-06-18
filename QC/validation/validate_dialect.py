"""validate_dialect.py — summarize TEXT/@dialect values across a path.

Walks every .xml file under --path, reads the root TEXT element's
xml:lang and dialect attributes, and prints a (xml:lang, dialect) ->
count table to stdout. Companion to QC/validation/validate_xml.py V036:
this is the informative side that a human reads to decide whether the
distribution looks right (too many "unknown" in one language? a dialect
leaked into the wrong language? more files for X dialect than expected?).

Usage:
    python QC/validation/validate_dialect.py --path <file-or-dir>

Output:
    xml:lang  dialect      count
    --------  -----------  -----
    ami       Coastal      12
    ami       Southern     8
    ami       unknown      3
    tsu       Tsou         47
    trv       Truku        22
    trv       Duda         5
    ...
    (missing)              N    (if any TEXT elements lacked @dialect)
    (not-TEXT)             M    (if any roots weren't <TEXT>)

Exit code: 0 unless --path is missing or no .xml files were found. The
script does not flag any dialect value as invalid — that's V036's job.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from lxml import etree

_XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
_MISSING = "(missing)"
_NOT_TEXT = "(not-TEXT)"
_PARSE_ERROR = "(parse-error)"


def _discover_xml(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix == ".xml" else []
    return sorted(path.rglob("*.xml"))


def collect_dialects(files: list[Path]) -> Counter[tuple[str, str]]:
    """Return a Counter keyed by (xml:lang, dialect).

    For TEXT roots with no @dialect: dialect column is "(missing)".
    For files where the root isn't <TEXT>: ("", "(not-TEXT)").
    For unparseable files: ("", "(parse-error)").
    """
    counts: Counter[tuple[str, str]] = Counter()
    for file in files:
        try:
            tree = etree.parse(str(file))
        except etree.XMLSyntaxError:
            counts[("", _PARSE_ERROR)] += 1
            continue
        root = tree.getroot()
        if root.tag != "TEXT":
            counts[("", _NOT_TEXT)] += 1
            continue
        lang = root.get(_XML_LANG) or ""
        dialect = root.get("dialect") or _MISSING
        counts[(lang, dialect)] += 1
    return counts


def format_table(counts: Counter[tuple[str, str]]) -> str:
    """Render counts as a fixed-width table sorted by xml:lang, then dialect."""
    if not counts:
        return "(no TEXT elements found)"
    rows = sorted(counts.items(), key=lambda item: (item[0][0], item[0][1]))
    lang_w = max(len("xml:lang"), max(len(k[0]) for k in counts))
    dialect_w = max(len("dialect"), max(len(k[1]) for k in counts))
    count_w = max(len("count"), max(len(str(v)) for v in counts.values()))
    out = []
    out.append(f"{'xml:lang':<{lang_w}}  {'dialect':<{dialect_w}}  {'count':>{count_w}}")
    out.append(f"{'-' * lang_w}  {'-' * dialect_w}  {'-' * count_w}")
    for (lang, dialect), n in rows:
        out.append(f"{lang:<{lang_w}}  {dialect:<{dialect_w}}  {n:>{count_w}}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Count TEXT/@dialect values across a path.",
    )
    parser.add_argument(
        "--path",
        required=True,
        type=Path,
        help="File or directory to walk recursively for .xml files.",
    )
    args = parser.parse_args(argv)

    if not args.path.exists():
        print(f"Error: path does not exist: {args.path}", file=sys.stderr)
        return 1

    files = _discover_xml(args.path)
    if not files:
        print(f"No .xml files found under {args.path}", file=sys.stderr)
        return 1

    counts = collect_dialects(files)
    print(format_table(counts))
    print(f"\nFiles scanned: {len(files)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

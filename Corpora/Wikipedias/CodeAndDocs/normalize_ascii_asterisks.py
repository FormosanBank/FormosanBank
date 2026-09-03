#!/usr/bin/env python3
"""Normalize ASCII asterisks in original Wikipedia FORMs.

ASCII ``*`` is meaningful in the scrape as wiki list markup, a footnote or
reconstruction marker, a separator, or a multiplication symbol. FormosanBank's
text validator reserves that code point for acceptability notation, however.
Replace it with the visually and semantically equivalent Unicode asterisk
operator ``∗`` (U+2217) in the active original tier. The immutable
``pre_correction_snapshot`` retains the exact scraped bytes.

Only ``FORM kindOf="original"`` content is touched. Standard and PHON tiers
regenerate later in the pipeline. The edit is byte-minimal and idempotent.
"""

import argparse
import re
import sys
from pathlib import Path


FORM_RE = re.compile(r'(<FORM kindOf="original">)(.*?)(</FORM>)', re.DOTALL)
ASCII_ASTERISK = "*"
UNICODE_ASTERISK = "∗"


def process_file(path: Path, apply: bool) -> tuple[int, int]:
    """Return the numbers of changed FORMs and characters in *path*."""
    raw = path.read_text(encoding="utf-8")
    changed_forms = 0
    changed_chars = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal changed_forms, changed_chars
        form = match.group(2)
        count = form.count(ASCII_ASTERISK)
        if count:
            changed_forms += 1
            changed_chars += count
            form = form.replace(ASCII_ASTERISK, UNICODE_ASTERISK)
        return match.group(1) + form + match.group(3)

    normalized = FORM_RE.sub(replace, raw)
    if apply and normalized != raw:
        path.write_text(normalized, encoding="utf-8")
    return changed_forms, changed_chars


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--corpora_path",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "XML",
        help="Wikipedias XML root (default: sibling XML/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would change without writing",
    )
    args = parser.parse_args()

    if not args.corpora_path.is_dir():
        sys.exit(f"not found: {args.corpora_path}")

    total_files = 0
    total_forms = 0
    total_chars = 0
    for path in sorted(args.corpora_path.glob("*/*.xml")):
        forms, chars = process_file(path, apply=not args.dry_run)
        if forms:
            total_files += 1
            total_forms += forms
            total_chars += chars

    verb = "would change" if args.dry_run else "changed"
    print(
        f"{verb} {total_chars} ASCII asterisks in {total_forms} "
        f"original FORMs across {total_files} files"
    )


if __name__ == "__main__":
    main()

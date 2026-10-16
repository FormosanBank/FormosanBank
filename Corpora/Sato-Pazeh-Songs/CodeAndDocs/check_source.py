#!/usr/bin/env python3
"""Verify that the committed scan is the complete reviewed source."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys

from corpus_config import SOURCE_BYTES, SOURCE_PAGES, SOURCE_PATH, SOURCE_SHA256


def main() -> int:
    if not SOURCE_PATH.is_file():
        print(f"ERROR: missing source: {SOURCE_PATH}", file=sys.stderr)
        return 1

    size = SOURCE_PATH.stat().st_size
    digest = hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()
    if size != SOURCE_BYTES:
        print(f"ERROR: source size {size} != expected {SOURCE_BYTES}", file=sys.stderr)
        return 1
    if digest != SOURCE_SHA256:
        print(f"ERROR: source SHA-256 {digest} != expected {SOURCE_SHA256}", file=sys.stderr)
        return 1

    print(f"source={SOURCE_PATH}")
    print(f"bytes={size}")
    print(f"sha256={digest}")

    pdfinfo = shutil.which("pdfinfo")
    if pdfinfo:
        result = subprocess.run(
            [pdfinfo, str(SOURCE_PATH)],
            check=True,
            capture_output=True,
            text=True,
        )
        page_line = next(
            (line for line in result.stdout.splitlines() if line.startswith("Pages:")),
            "",
        )
        pages = int(page_line.split(":", 1)[1].strip()) if page_line else -1
        if pages != SOURCE_PAGES:
            print(f"ERROR: PDF page count {pages} != expected {SOURCE_PAGES}", file=sys.stderr)
            return 1
        print(f"pages={pages}")
    else:
        print("pages=not checked (pdfinfo is unavailable)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

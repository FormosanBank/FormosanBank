#!/usr/bin/env python3
"""Extract Matthew and John from NLTK Gutenberg ``bible-kjv.txt``."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reference_translations" / "eng-kjv-nltk-gutenberg.tsv"
ARCHIVE_MEMBER = "gutenberg/bible-kjv.txt"
EXPECTED_ARCHIVE_SHA256 = "2d3c3ab548c653944310f37f536443ec85d0a0ad855fcae217a0c9efdce2d611"
EXPECTED_RAW_SHA256 = "3f56c9f0bbc796312aacc5fcb49a799f5c5f729f00db3f86bff26319a93bfede"


def parse_book(raw: str, book: str, next_heading: str) -> dict[tuple[int, int], str]:
    start = raw.index(f"The Gospel According to Saint {book}")
    end = raw.index(next_heading, start + 10)
    parts = re.split(r"(\d+):(\d+)\s+", raw[start:end])
    verses: dict[tuple[int, int], str] = {}
    for index in range(1, len(parts) - 2, 3):
        chapter = int(parts[index])
        verse = int(parts[index + 1])
        text = re.sub(r"\s+", " ", parts[index + 2].strip())
        verses[(chapter, verse)] = text
    return verses


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="NLTK Gutenberg corpus ZIP archive")
    args = parser.parse_args()

    archive = args.source.read_bytes()
    actual_archive = hashlib.sha256(archive).hexdigest()
    if actual_archive != EXPECTED_ARCHIVE_SHA256:
        raise SystemExit(f"KJV archive SHA-256 mismatch: {actual_archive}")
    with zipfile.ZipFile(args.source) as handle:
        payload = handle.read(ARCHIVE_MEMBER)
    actual_raw = hashlib.sha256(payload).hexdigest()
    if actual_raw != EXPECTED_RAW_SHA256:
        raise SystemExit(f"KJV raw source SHA-256 mismatch: {actual_raw}")
    raw = payload.decode("utf-8")
    books = {
        "Matthew": parse_book(raw, "Matthew", "The Gospel According to Saint Mark"),
        "John": parse_book(raw, "John", "The Acts of the Apostles"),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["book", "chapter", "verse", "text"])
        for book, verses in books.items():
            for (chapter, verse), text in sorted(verses.items()):
                writer.writerow([book, chapter, verse, text])
    print(f"Wrote {sum(map(len, books.values()))} KJV reference rows to {OUTPUT}")


if __name__ == "__main__":
    main()

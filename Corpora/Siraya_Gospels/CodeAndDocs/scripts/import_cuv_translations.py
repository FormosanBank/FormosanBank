#!/usr/bin/env python3
"""Refresh Mandarin translations in the reviewed intermediate from CUV USFM.

The earlier importer ignored ``\\q`` poetry continuation lines.  This parser
retains those lines and only omits the four verses absent from this CUV edition.
"""

from __future__ import annotations

import gzip
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTERMEDIATE = ROOT / "data" / "verses.jsonl"
USFM = ROOT / "reference_translations" / "cmn-cu89t_usfm"
XML_LANG = "cmn"

INLINE = re.compile(r"\\(?:pn|add|nd|wj|qt|sig|sls|tl|dc|bk|k|ord|bd|it|em|sc|sup|no|ior|iqt|rq|rb|rt|wa|wg|wh|xt|fk|fq|fqa|fl|fr|ft|fdc|fm|xo|xk|xq|xdc|xnt|xot)(?:\s|\*)?")
FOOTNOTE = re.compile(r"\\f\s.*?\\f\*", re.DOTALL)
XREF = re.compile(r"\\x\s.*?\\x\*", re.DOTALL)
CONTINUATION = re.compile(r"^\\(?:q\d*|m|mi|li\d*|b)\s*(.*)$")
OMITTED = {("Matthew", 18, 11), ("Matthew", 23, 14), ("John", 5, 4), ("John", 7, 53)}


def clean(text: str) -> str:
    text = FOOTNOTE.sub("", text)
    text = XREF.sub("", text)
    text = INLINE.sub("", text)
    text = re.sub(r"\\[A-Za-z]+\d*\*?", "", text)
    return re.sub(r"\s+", " ", text).strip()


def parse(path: Path) -> dict[tuple[int, int], str]:
    verses: dict[tuple[int, int], str] = {}
    chapter: int | None = None
    current: tuple[int, int] | None = None
    lines: list[str] = []

    def flush() -> None:
        if current is not None:
            verses[current] = clean(" ".join(lines))

    with gzip.open(path, "rt", encoding="utf-8") as handle:
        source_lines = handle.read().splitlines()

    for raw in source_lines:
        chapter_match = re.match(r"^\\c\s+(\d+)", raw)
        if chapter_match:
            flush()
            chapter = int(chapter_match.group(1))
            current, lines = None, []
            continue
        verse_match = re.match(r"^\\v\s+(\d+)(?:-\d+)?\s*(.*)$", raw)
        if verse_match and chapter is not None:
            flush()
            current = (chapter, int(verse_match.group(1)))
            lines = [verse_match.group(2)]
            continue
        continuation = CONTINUATION.match(raw)
        if current is not None and continuation:
            lines.append(continuation.group(1))
    flush()
    return verses


def mapped_verse(book: str, chapter: int, verse: int) -> int:
    # The 1661 John 1 splits modern verse 38 across XML verses 38 and 39.
    return verse - 1 if book == "John" and chapter == 1 and verse >= 39 else verse


def aligned_text(book: str, chapter: int, verse: int, source: str) -> str:
    """Partition CUV John 1:38 across the source's two printed verse units."""

    if (book, chapter, verse) not in {("John", 1, 38), ("John", 1, 39)}:
        return source
    marker = "「你們要甚麼？」"
    if marker not in source:
        raise SystemExit("CUV John 1:38 no longer contains the reviewed split marker")
    prefix, suffix = source.split(marker, 1)
    return prefix if verse == 38 else marker + suffix


def main() -> None:
    sources = {
        "Matthew": parse(USFM / "70-MATcmn-cu89t.usfm.gz"),
        "John": parse(USFM / "73-JHNcmn-cu89t.usfm.gz"),
    }
    rows = [json.loads(line) for line in INTERMEDIATE.read_text(encoding="utf-8").splitlines()]
    changed = missing = 0
    for row in rows:
        book, file_name = Path(row["path"]).parts
        chapter = int(Path(file_name).stem.removeprefix("chapter"))
        verse = int(str(row["sentence_id"]).removeprefix("verse"))
        key = (book, chapter, verse)
        source_key = (chapter, mapped_verse(book, chapter, verse))
        fields = [field for field in row["fields"] if not (field["tag"] == "TRANSL" and field["xml_lang"] == XML_LANG)]
        if key in OMITTED:
            missing += 1
        else:
            try:
                source = sources[book][source_key]
                fields.append(
                    {
                        "tag": "TRANSL",
                        "kindOf": "",
                        "xml_lang": XML_LANG,
                        "text": aligned_text(book, chapter, verse, source),
                    }
                )
            except KeyError as error:
                raise SystemExit(f"Missing CUV translation for {book} {chapter}:{verse} -> {source_key}") from error
        row["fields"] = fields
        changed += 1
    with INTERMEDIATE.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"Updated Mandarin translations for {changed - missing} rows; {missing} edition omissions retained.")


if __name__ == "__main__":
    main()

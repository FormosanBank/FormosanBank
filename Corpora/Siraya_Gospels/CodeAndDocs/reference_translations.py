"""Read the retained KJV and CUV editions, including verse continuations."""

from __future__ import annotations

import csv
import re
from pathlib import Path

FOOTNOTE = re.compile(r"\\f\s+(.*?)\\f\*", re.DOTALL)
INLINE = re.compile(r"\\\+?(?:pn|add|fv|ft)\*?\s*")


def plain(text: str) -> str:
    text = INLINE.sub("", text)
    if "\\" in text:
        raise ValueError(f"Unparsed USFM markup: {text}")
    return " ".join(text.split())


def read_cuv(path: Path) -> dict[tuple[int, int], tuple[str, str]]:
    verses: dict[tuple[int, int], tuple[str, str]] = {}
    chapter = None
    current = None
    chunks: list[str] = []
    notes: list[str] = []
    section_refs: list[str] = []

    def flush() -> None:
        if current is None:
            return
        text = " ".join(chunks)
        all_notes = list(notes)
        for footnote in FOOTNOTE.findall(text):
            match = re.fullmatch(r"[-+]\s+\\fr\s+([^\\]+)\\ft\s+(.*)", footnote)
            if match is None:
                raise ValueError(f"Unparsed CUV footnote: {footnote}")
            all_notes.append(plain(match[2]))
        if current in verses:
            raise ValueError(f"Duplicate CUV verse: {current}")
        verses[current] = plain(FOOTNOTE.sub("", text)), " / ".join(all_notes)

    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        if not raw.strip():
            continue
        match = re.fullmatch(r"\\(\w+)\s*(.*)", raw.strip())
        if match is None:
            raise ValueError(f"Unparsed USFM line: {raw}")
        marker, content = match.groups()
        if marker == "c":
            flush()
            chapter, current = int(content), None
            section_refs = []
        elif marker == "s1":
            # A section heading can interrupt a numbered verse (John 12:36).
            # Only the next v/c marker ends that verse.
            section_refs = []
        elif marker == "r":
            section_refs.append("Parallel passages: " + content)
        elif marker == "v":
            flush()
            number, text = content.split(maxsplit=1)
            if chapter is None:
                raise ValueError("Verse precedes its chapter")
            current = chapter, int(number)
            chunks, notes = [text], section_refs
            section_refs = []
        elif marker in {"q1", "m", "p"}:
            if current is not None and content:
                chunks.append(content)
                notes.extend(section_refs)
                section_refs = []
        elif marker not in {"id", "h", "toc1", "toc2", "mt1"}:
            raise ValueError(f"Unsupported USFM block: {marker}")
    flush()
    return verses


def read_kjv(path: Path) -> dict[tuple[str, int, int], str]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    verses = {
        (r["book"], int(r["chapter"]), int(r["verse"])): r["text"] for r in rows
    }
    if len(verses) != len(rows):
        raise ValueError("Duplicate KJV verse")
    return verses

#!/usr/bin/env python3
"""Build canonical Wilang Yutas XML from pinned transcript inputs."""

from __future__ import annotations

import csv
import hashlib
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "CodeAndDocs"
MANIFEST = ROOT / "CodeAndDocs" / "video_manifest.tsv"
XML_ROOT = ROOT / "XML"
XML_NS = "http://www.w3.org/XML/1998/namespace"
CITATION = (
    "Wilang Yutas. (2019). YouTube channel. YouTube. "
    "https://www.youtube.com/@wilangyutas9297"
)
BIBTEX = (
    "@misc{wilangyutas_channel, author = {{Wilang Yutas}}, "
    "title = {Wilang Yutas YouTube Channel}, year = {2019}, "
    "howpublished = {\\url{https://www.youtube.com/@wilangyutas9297}}, "
    "note = {YouTube channel} }"
)

_TIMESTAMP_RE = re.compile(r"^(\d+(?:\.\d+)?):\s?(.*)$")
_PUNCT_SPACING_RE = re.compile(r"(?<=[a-zA-Z'\u2019])([,.])(?=[a-zA-Z'\u2019])")
_PAREN_BEFORE_RE = re.compile(r"(?<=[^\s(])\(")
_PAREN_AFTER_RE = re.compile(r"\)(?=[^\s),.:;!?'\u2019])")
_MULTI_SPACE_RE = re.compile(r" {2,}")
_TRAIL_SPACE_BEFORE_PUNCT_RE = re.compile(r" +([,.!?:;]+)\s*$")
_OPEN_PAREN_WORD_RE = re.compile(r"(?<=[\w''])\s*\(")
_CLOSE_PAREN_RE = re.compile(r" *\)[,.!?:;]*")
_LEADING_COMMA_RE = re.compile(r"(?<=\S) +(,+) *")
_LEADING_PERIOD_RE = re.compile(r"(?<=\S) +(\.+)(?=[^\s,.])")
_UNCLEAR_RE = re.compile(r"[?\uff1f]{3,}")
_EDITORIAL_RECHECK_RE = re.compile(r"\s*([（(][^（）()]*再確認[^（）()]*[）)])\s*$")


@dataclass(frozen=True)
class ManifestRow:
    output_path: Path
    video_id: str
    source_path: Path | None
    source_sha256: str
    source_bytes: int | None
    audio_only_file: str
    output_kind: str


@dataclass
class SourceEntry:
    line_number: int
    start: str
    text: str
    translation: str | None = None


@dataclass(frozen=True)
class SourceStats:
    timestamp_lines: int
    included_entries: int
    blank_entries: int
    translation_lines: int
    continuation_lines: int


def load_manifest(path: Path = MANIFEST) -> list[ManifestRow]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    manifest: list[ManifestRow] = []
    for row in rows:
        source = SOURCE_ROOT / row["source_path"] if row["source_path"] else None
        manifest.append(
            ManifestRow(
                output_path=ROOT / row["output_path"],
                video_id=row["video_id"],
                source_path=source,
                source_sha256=row["source_sha256"],
                source_bytes=int(row["source_bytes"]) if row["source_bytes"] else None,
                audio_only_file=row["audio_only_file"],
                output_kind=row["output_kind"],
            )
        )
    paths = [row.output_path for row in manifest]
    if len(manifest) != 82 or len(set(paths)) != 82:
        raise ValueError("Video manifest must contain 82 unique output paths")
    if sum(row.source_path is not None for row in manifest) != 34:
        raise ValueError("Video manifest must contain 34 transcript sources")
    if sum(bool(row.audio_only_file) for row in manifest) != 48:
        raise ValueError("Video manifest must contain 48 audio-only outputs")
    for row in manifest:
        expected_kind = "transcript" if row.source_path is not None else "audio_only"
        if row.output_kind != expected_kind:
            raise ValueError(f"Manifest output kind mismatch: {row.output_path}")
        if (row.source_path is None) == (not row.audio_only_file):
            raise ValueError(
                f"Manifest row must select one output mode: {row.output_path}"
            )
        if row.output_path.suffix != ".xml" or XML_ROOT not in row.output_path.parents:
            raise ValueError(f"Manifest output is outside canonical XML/: {row.output_path}")
    return manifest


def verify_source(row: ManifestRow) -> None:
    if row.source_path is None or row.source_bytes is None:
        raise ValueError(f"Transcript row is missing source metadata: {row.output_path}")
    data = row.source_path.read_bytes()
    if len(data) != row.source_bytes:
        raise ValueError(
            f"Source byte-count mismatch for {row.source_path}: "
            f"expected {row.source_bytes}, got {len(data)}"
        )
    digest = hashlib.sha256(data).hexdigest()
    if digest != row.source_sha256:
        raise ValueError(
            f"Source checksum mismatch for {row.source_path}: "
            f"expected {row.source_sha256}, got {digest}"
        )


def parse_source(path: Path) -> tuple[list[SourceEntry], SourceStats]:
    """Parse every source line or fail if its role is ambiguous.

    Timestamped lines are source captions. A following unindented line is the
    translation for that caption. An indented line, or a line continuing an
    unmatched source parenthesis, is a wrapped source continuation. This
    accounts for the two unindented ``Wilang`` translations and five wrapped
    source lines in the pinned data.
    """

    entries: list[SourceEntry] = []
    translation_lines = 0
    continuation_lines = 0
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        stripped = raw_line.strip()
        if not stripped:
            continue
        match = _TIMESTAMP_RE.match(stripped)
        if match:
            entries.append(
                SourceEntry(
                    line_number=line_number,
                    start=match.group(1),
                    text=match.group(2).strip(),
                )
            )
            continue
        if not entries:
            raise ValueError(f"{path}:{line_number}: content before first timestamp")
        continues_open_paren = entries[-1].text.count("(") > entries[-1].text.count(")")
        if raw_line[0].isspace() or continues_open_paren:
            if not entries[-1].text:
                raise ValueError(
                    f"{path}:{line_number}: continuation follows a blank caption"
                )
            entries[-1].text = f"{entries[-1].text} {stripped}"
            continuation_lines += 1
            continue
        if entries[-1].translation is not None:
            raise ValueError(f"{path}:{line_number}: multiple translation lines")
        if not entries[-1].text:
            raise ValueError(f"{path}:{line_number}: translation follows a blank caption")
        entries[-1].translation = stripped
        translation_lines += 1

    included = sum(bool(entry.text) for entry in entries)
    stats = SourceStats(
        timestamp_lines=len(entries),
        included_entries=included,
        blank_entries=len(entries) - included,
        translation_lines=translation_lines,
        continuation_lines=continuation_lines,
    )
    return entries, stats


def _close_paren_repl(match: re.Match[str]) -> str:
    preceding = match.string[: match.start()].rstrip()
    return " " if preceding and preceding[-1] in "?!." else ". "


def fix_punctuation_spacing(text: str) -> str:
    text = _PUNCT_SPACING_RE.sub(r"\1 ", text)
    text = _PAREN_BEFORE_RE.sub(" (", text)
    text = _PAREN_AFTER_RE.sub(") ", text)
    text = _LEADING_COMMA_RE.sub(r"\1 ", text)
    text = _LEADING_PERIOD_RE.sub(r"\1 ", text)
    return _TRAIL_SPACE_BEFORE_PUNCT_RE.sub(r"\1", text)


def remove_parens(text: str) -> tuple[str, bool]:
    had_parens = "(" in text or ")" in text
    cleaned = _OPEN_PAREN_WORD_RE.sub(". ", text)
    cleaned = cleaned.replace("(", "")
    cleaned = _CLOSE_PAREN_RE.sub(_close_paren_repl, cleaned)
    return _MULTI_SPACE_RE.sub(" ", cleaned).strip(), had_parens


def normalize_form(text: str) -> tuple[str, bool]:
    normalized, had_parens = remove_parens(fix_punctuation_spacing(text))
    return _TRAIL_SPACE_BEFORE_PUNCT_RE.sub(r"\1", normalized), had_parens


def split_editorial_recheck(translation: str) -> tuple[str, str | None]:
    match = _EDITORIAL_RECHECK_RE.search(translation)
    if not match:
        return translation, None
    return translation[: match.start()].rstrip(), match.group(1)


def set_mixed_text(element: etree._Element, text: str) -> None:
    parts = _UNCLEAR_RE.split(text)
    element.text = parts[0]
    for part in parts[1:]:
        unclear = etree.SubElement(element, "UNCLEAR")
        unclear.tail = part


def create_root(output_stem: str, video_id: str) -> etree._Element:
    root = etree.Element("TEXT")
    root.set("id", output_stem)
    root.set(f"{{{XML_NS}}}lang", "tay")
    root.set("dialect", "Sekolik")
    root.set("audio", f"https://www.youtube.com/watch?v={video_id}")
    root.set("source", "Wilang Yutas Atayal Videos")
    root.set("copyright", "CC-BY-NC")
    root.set("citation", CITATION)
    root.set("BibTeX_citation", BIBTEX)
    return root


def _join_notes(*values: str | None) -> str | None:
    notes = [value for value in values if value]
    return "; ".join(notes) if notes else None


def build_transcript(row: ManifestRow) -> tuple[etree._Element, SourceStats]:
    verify_source(row)
    assert row.source_path is not None
    entries, stats = parse_source(row.source_path)
    output_stem = row.output_path.stem
    root = create_root(output_stem, row.video_id)
    included = [(index, entry) for index, entry in enumerate(entries) if entry.text]
    for sentence_number, (raw_index, entry) in enumerate(included, start=1):
        sentence_id = f"Atayal_{sentence_number}"
        sentence = etree.SubElement(root, "S", id=sentence_id)
        normalized, had_parens = normalize_form(entry.text)
        translation = entry.translation
        editorial_note = None
        if translation is not None:
            translation, editorial_note = split_editorial_recheck(translation)
        form_note = _join_notes(
            "multiple speakers" if had_parens else None,
            (
                f"source translation field contains editorial marker "
                f"{editorial_note}; no free translation supplied"
                if editorial_note and not translation
                else None
            ),
        )
        for kind in ("original", "standard"):
            form = etree.SubElement(sentence, "FORM", kindOf=kind)
            if form_note:
                form.set("notes", form_note)
            set_mixed_text(form, normalized)
        if translation:
            transl = etree.SubElement(sentence, "TRANSL")
            transl.set(f"{{{XML_NS}}}lang", "zho")
            if editorial_note:
                transl.set("notes", f"source editorial marker: {editorial_note}")
            transl.text = translation
        audio = etree.SubElement(sentence, "AUDIO")
        audio.set("start", entry.start)
        if raw_index + 1 < len(entries):
            audio.set("end", entries[raw_index + 1].start)
        audio.set("file", f"{output_stem}_{sentence_id}.wav")
    return root, stats


def build_audio_only(row: ManifestRow) -> etree._Element:
    root = create_root(row.output_path.stem, row.video_id)
    etree.SubElement(root, "AUDIO", file=row.audio_only_file)
    return root


def write_xml(root: etree._Element, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    etree.ElementTree(root).write(
        str(path), encoding="utf-8", pretty_print=True, xml_declaration=True
    )


def main() -> None:
    manifest = load_manifest()
    if XML_ROOT.exists():
        shutil.rmtree(XML_ROOT)
    totals = SourceStats(0, 0, 0, 0, 0)
    transcript_files = 0
    for row in manifest:
        if row.source_path is not None:
            root, stats = build_transcript(row)
            transcript_files += 1
            totals = SourceStats(
                totals.timestamp_lines + stats.timestamp_lines,
                totals.included_entries + stats.included_entries,
                totals.blank_entries + stats.blank_entries,
                totals.translation_lines + stats.translation_lines,
                totals.continuation_lines + stats.continuation_lines,
            )
        else:
            root = build_audio_only(row)
        write_xml(root, row.output_path)
    print(f"Wrote {len(manifest)} XML files under XML/")
    print(f"Transcript files: {transcript_files}; audio-only files: 48")
    print(
        f"Source timestamps: {totals.timestamp_lines}; "
        f"included: {totals.included_entries}; blank: {totals.blank_entries}"
    )
    print(
        f"Translation lines: {totals.translation_lines}; "
        f"wrapped source continuations: {totals.continuation_lines}"
    )


if __name__ == "__main__":
    main()

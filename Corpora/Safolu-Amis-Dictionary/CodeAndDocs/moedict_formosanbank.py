#!/usr/bin/env python3
"""Shared helpers for converting Moedict examples to FormosanBank XML."""

from __future__ import annotations

import json
import re
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("xml", XML_NS)

MOEDICT_FORM_START = "\ufff9"
MOEDICT_MIDDLE_TRANSL = "\ufffa"
MOEDICT_FINAL_TRANSL = "\ufffb"

SPECIAL_MOEDICT_FILES = {
    "=.json",
    "ch-mapping.json",
    "index.json",
    "lenToRegex.json",
    "precomputed.json",
    "stem-words.json",
}

FORM_ORIGINAL_ATTR = {"kindOf": "original"}


@dataclass(frozen=True)
class Translation:
    lang: str
    text: str


@dataclass(frozen=True)
class ExampleRecord:
    sentence_id: str
    source_file: str
    source_line: int | None
    entry_title: str
    definition: str
    form: str
    translations: list[Translation]
    raw_example: str
    notes: dict[str, Any]

    def to_metadata(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["translations"] = [asdict(translation) for translation in self.translations]
        return payload


@dataclass(frozen=True)
class Corpus:
    text_id: str
    folder_name: str
    citation: str
    bibtex_citation: str
    copyright: str
    source: str
    glottocode: str
    extraction_note: str
    source_repositories: dict[str, str]
    # FormosanBank requires TEXT/@dialect (validate_xml V036). Amis is a
    # multi-dialect language and these dictionaries do not record a single
    # source dialect, so we emit the schema-sanctioned "unknown" sentinel.
    # A maintainer should refine this during QC (e.g. via the dialect
    # detector) before the corpus is ported into FormosanBank/Corpora/.
    dialect: str = "unknown"


def git_commit(path: Path) -> str:
    if not (path / ".git").exists():
        return "unknown"
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        check=True,
        text=True,
        capture_output=True,
    )
    return proc.stdout.strip()


def relative_to_root(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def collapse_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_invalid_xml_chars(text: str) -> str:
    return "".join(ch for ch in text if is_valid_xml_char(ord(ch)))


def is_valid_xml_char(codepoint: int) -> bool:
    return (
        codepoint in {0x09, 0x0A, 0x0D}
        or 0x20 <= codepoint <= 0xD7FF
        or 0xE000 <= codepoint <= 0xFFFD
        or 0x10000 <= codepoint <= 0x10FFFF
    )


def clean_text(text: str) -> str:
    return collapse_space(strip_invalid_xml_chars(text))


def clean_moedict_link_markup(text: str) -> str:
    text = text.replace("`", "").replace("~", "")
    text = re.sub(r"\s+([,.;:!?，。；：！？])", r"\1", text)
    return clean_text(text)


def parse_marked_example(raw_example: str) -> tuple[str, str, str]:
    if not raw_example.startswith(MOEDICT_FORM_START):
        raise ValueError(f"Example does not start with U+FFF9: {raw_example!r}")
    body = raw_example[len(MOEDICT_FORM_START) :]
    if MOEDICT_MIDDLE_TRANSL not in body or MOEDICT_FINAL_TRANSL not in body:
        raise ValueError(f"Example is missing U+FFFA/U+FFFB separators: {raw_example!r}")
    form, rest = body.split(MOEDICT_MIDDLE_TRANSL, 1)
    middle_translation, final_translation = rest.split(MOEDICT_FINAL_TRANSL, 1)
    return form, middle_translation, final_translation


def iter_moedict_json_files(directory: Path) -> Iterable[Path]:
    for path in sorted(directory.glob("*.json"), key=lambda item: item.name):
        if path.name in SPECIAL_MOEDICT_FILES:
            continue
        yield path


def assign_sentence_ids(text_id: str, records: Iterable[ExampleRecord]) -> list[ExampleRecord]:
    assigned: list[ExampleRecord] = []
    for index, record in enumerate(records, 1):
        assigned.append(
            ExampleRecord(
                sentence_id=f"S{index:05d}",
                source_file=record.source_file,
                source_line=record.source_line,
                entry_title=record.entry_title,
                definition=record.definition,
                form=record.form,
                translations=record.translations,
                raw_example=record.raw_example,
                notes={**record.notes, "text_id": text_id},
            )
        )
    return assigned


def build_text_tree(corpus: Corpus, records: list[ExampleRecord]) -> ET.ElementTree:
    root = ET.Element(
        "TEXT",
        {
            "id": corpus.text_id,
            "citation": corpus.citation,
            "BibTeX_citation": corpus.bibtex_citation,
            "copyright": corpus.copyright,
            f"{{{XML_NS}}}lang": "ami",
            "source": corpus.source,
            "glottocode": corpus.glottocode,
            "dialect": corpus.dialect,
        },
    )

    for record in records:
        sentence = ET.SubElement(root, "S", {"id": record.sentence_id})
        ET.SubElement(sentence, "FORM", FORM_ORIGINAL_ATTR).text = record.form
        for translation in record.translations:
            ET.SubElement(sentence, "TRANSL", {f"{{{XML_NS}}}lang": translation.lang}).text = translation.text

    ET.indent(root, space="  ")
    return ET.ElementTree(root)


def write_xml(corpus: Corpus, records: list[ExampleRecord], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    build_text_tree(corpus, records).write(output_path, encoding="utf-8", xml_declaration=True)


def write_metadata(
    corpus: Corpus,
    records: list[ExampleRecord],
    output_path: Path,
    rejected_records: list[dict[str, Any]] | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "text_id": corpus.text_id,
        "language": {"iso_639_3": "ami", "glottocode": corpus.glottocode},
        "translation_languages": sorted({translation.lang for record in records for translation in record.translations}),
        "source": corpus.source,
        "citation": corpus.citation,
        "BibTeX_citation": corpus.bibtex_citation,
        "copyright": corpus.copyright,
        "source_repositories": corpus.source_repositories,
        "extraction_note": corpus.extraction_note,
        "example_count": len(records),
        "rejected_example_count": len(rejected_records or []),
        "examples": [record.to_metadata() for record in records],
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_rejected_records(rejected_records: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "description": (
            "Source example fields that were parsed but excluded from XML because they do not have "
            "the non-empty Amis FORM and translation required by FormosanBank."
        ),
        "rejected_example_count": len(rejected_records),
        "examples": rejected_records,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

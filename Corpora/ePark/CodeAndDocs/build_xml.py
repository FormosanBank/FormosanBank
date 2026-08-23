#!/usr/bin/env python3
"""Build the complete ePark source-owned XML tree from committed inputs."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import TextIO

import source_audit

LANGUAGE_CODES = {
    "Amis": "ami",
    "Atayal": "tay",
    "Bunun": "bnn",
    "Kanakanavu": "xnb",
    "Kavalan": "ckv",
    "Paiwan": "pwn",
    "Puyuma": "pyu",
    "Rukai": "dru",
    "Saaroa": "sxr",
    "Saisiyat": "xsy",
    "Sakizaya": "szy",
    "Seediq": "trv",
    "Thao": "ssf",
    "Truku": "trv",
    "Tsou": "tsu",
    "Yami": "tao",
}
SORTED_RECORD_TOPICS = {
    source_audit.TOPIC_SLUGS["圖畫故事篇"],
    source_audit.TOPIC_SLUGS["繪本平台"],
}
TOPIC_NAMES = {slug: name for name, slug in source_audit.TOPIC_SLUGS.items()}
CITATION = (
    "Indigenous Languages Research and Development Foundation. (2020). "
    "族語E樂園. https://web.klokah.tw/"
)
BIBTEX_CITATION = (
    "@misc{ePark, author = {Indigenous Languages Research and Development Foundation}, "
    "title = {族語E樂園}, year = {2020}, url = {https://web.klokah.tw/} }"
)
AUDIO_MANIFEST_FIELDS = ("topic", "dialect", "s_id", "status", "end")


def natural_key(value: str) -> tuple[tuple[int, int | str], ...]:
    return tuple(
        (0, int(part)) if part.isdigit() else (1, part)
        for part in re.split(r"(\d+)", value)
    )


def language_for_dialect(dialect: str) -> str:
    matches = [
        language
        for language in LANGUAGE_CODES
        if dialect == language or dialect.endswith(f"_{language}")
    ]
    if len(matches) != 1:
        raise ValueError(f"cannot resolve one language for dialect {dialect!r}: {matches}")
    return matches[0]


def load_dialect_metadata(repo: Path) -> dict[str, str]:
    with (repo / "dialects.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    metadata = {row["dialect"]: row["glottocode"] for row in rows}
    if len(metadata) != len(rows):
        raise ValueError("dialects.csv contains duplicate dialect names")
    return metadata


def open_manifest(path: Path) -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, mode="rt", encoding="utf-8", newline="")
    return path.open(encoding="utf-8", newline="")


def load_audio_manifest(
    path: Path,
    inventory: source_audit.Inventory,
) -> dict[tuple[str, str, str, str], tuple[str, str]]:
    candidates = {
        record.key: record
        for record in inventory.records.values()
        if record.audio_file is not None
    }
    decisions: dict[tuple[str, str, str, str], tuple[str, str]] = {}
    with open_manifest(path) as handle:
        reader = csv.DictReader(handle, dialect="excel-tab")
        if tuple(reader.fieldnames or ()) != AUDIO_MANIFEST_FIELDS:
            raise ValueError(
                f"unexpected audio manifest columns: {reader.fieldnames}; "
                f"expected {AUDIO_MANIFEST_FIELDS}"
            )
        for row in reader:
            key = row["topic"], row["dialect"], "S", row["s_id"]
            if key in decisions:
                raise ValueError(f"duplicate audio decision for {key}")
            if key not in candidates:
                raise ValueError(f"audio decision has no matching source record: {key}")
            status = row["status"]
            end = row["end"]
            if status not in {"retained", "unavailable"}:
                raise ValueError(f"invalid audio status {status!r} for {key}")
            if status == "unavailable" and end:
                raise ValueError(f"unavailable audio cannot have a duration: {key}")
            decisions[key] = status, end

    missing = candidates.keys() - decisions.keys()
    extra = decisions.keys() - candidates.keys()
    if missing or extra:
        raise ValueError(
            f"audio manifest coverage mismatch: missing={len(missing)}, extra={len(extra)}"
        )
    return decisions


def grouped_records(
    inventory: source_audit.Inventory,
) -> dict[tuple[str, str], list[source_audit.SourceRecord]]:
    groups: dict[tuple[str, str], list[source_audit.SourceRecord]] = defaultdict(list)
    for record in inventory.records.values():
        groups[(record.slug, record.dialect)].append(record)
    for (topic, _dialect), records in groups.items():
        if topic in SORTED_RECORD_TOPICS:
            records.sort(key=lambda record: natural_key(record.record_id))
    return groups


def build_xml(repo: Path, output: Path, audio_manifest: Path) -> dict[str, int]:
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"refusing to write into non-empty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)

    inventory = source_audit.build_inventory(repo)
    audio_decisions = load_audio_manifest(audio_manifest, inventory)
    dialect_metadata = load_dialect_metadata(repo)
    groups = grouped_records(inventory)
    counts = {
        "files": 0,
        "sentences": 0,
        "audio_retained": 0,
        "audio_unavailable": 0,
        "audio_without_duration": 0,
    }

    for (topic, dialect), records in sorted(groups.items()):
        language = language_for_dialect(dialect)
        if dialect not in dialect_metadata:
            raise ValueError(f"missing dialect metadata for {dialect}")
        dialect_label = dialect.rsplit("_", 1)[0] if "_" in dialect else dialect
        root = ET.Element(
            "TEXT",
            {
                "id": f"{topic}_{dialect}",
                source_audit.XML_LANG: LANGUAGE_CODES[language],
                "source": f"{TOPIC_NAMES[topic]} {dialect}",
                "audio": "diarized",
                "copyright": "CC-BY-NC-SA",
                "citation": CITATION,
                "BibTeX_citation": BIBTEX_CITATION,
                "glottocode": dialect_metadata[dialect],
                "dialect": dialect_label,
            },
        )

        for record in records:
            sentence = ET.SubElement(root, "S", {"id": record.record_id})
            form = ET.SubElement(sentence, "FORM", {"kindOf": "original"})
            form.text = source_audit.canonical_form_text(record.form)
            for translation_language, translation_text in record.translations:
                translation = ET.SubElement(
                    sentence,
                    "TRANSL",
                    {source_audit.XML_LANG: translation_language},
                )
                translation.text = translation_text

            if record.audio_file is not None:
                status, end = audio_decisions[record.key]
                if status == "unavailable":
                    counts["audio_unavailable"] += 1
                else:
                    attributes = {"file": record.audio_file}
                    if record.audio_url is not None:
                        attributes["url"] = record.audio_url
                    if end:
                        attributes.update({"start": "0", "end": end})
                    else:
                        counts["audio_without_duration"] += 1
                    ET.SubElement(sentence, "AUDIO", attributes)
                    counts["audio_retained"] += 1
            counts["sentences"] += 1

        tree = ET.ElementTree(root)
        ET.indent(tree, space="    ")
        path = output / topic / language / f"{dialect}.xml"
        path.parent.mkdir(parents=True, exist_ok=True)
        tree.write(path, encoding="utf-8", xml_declaration=True, short_empty_elements=True)
        counts["files"] += 1

    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--audio-manifest",
        type=Path,
        default=Path("audio_inventory.tsv.gz"),
    )
    args = parser.parse_args()

    repo = args.repo.resolve()
    output = args.output if args.output.is_absolute() else repo / args.output
    manifest = (
        args.audio_manifest
        if args.audio_manifest.is_absolute()
        else repo / args.audio_manifest
    )
    counts = build_xml(repo, output, manifest)
    print(json.dumps(counts, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

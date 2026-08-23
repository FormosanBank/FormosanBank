#!/usr/bin/env python3
"""Generate Whitehorn FormosanBank XML from the reviewed source ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


@dataclass(frozen=True)
class Metadata:
    corpus: str
    copyright: str
    citation: str
    bibtex_citation: str


@dataclass(frozen=True)
class SourceUnit:
    path: str
    sha256: str
    pages: int
    status: str
    record_ids: tuple[str, ...]
    disposition: str


@dataclass(frozen=True)
class Record:
    output: str
    text_id: str
    language: str
    dialect: str
    source_dialect_label: str | None
    source: str
    recording_date: str
    audio_url: str
    audio_file: str
    source_file: str


@dataclass(frozen=True)
class Manifest:
    metadata: Metadata
    sources: tuple[SourceUnit, ...]
    records: tuple[Record, ...]


def _mapping(value: object, location: str) -> dict[str, object]:
    if not isinstance(value, dict) or not all(
        isinstance(key, str) for key in value
    ):
        raise ValueError(f"{location} must be an object with string keys")
    return value


def _sequence(value: object, location: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{location} must be an array")
    return value


def _string(mapping: dict[str, object], key: str, location: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{location}.{key} must be a non-empty string")
    return value


def _optional_string(
    mapping: dict[str, object], key: str, location: str
) -> str | None:
    value = mapping.get(key)
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{location}.{key} must be a string or null")
    return value


def _integer(mapping: dict[str, object], key: str, location: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{location}.{key} must be an integer")
    return value


def _string_tuple(
    mapping: dict[str, object], key: str, location: str
) -> tuple[str, ...]:
    values = _sequence(mapping.get(key), f"{location}.{key}")
    if not all(isinstance(value, str) and value for value in values):
        raise ValueError(f"{location}.{key} must contain non-empty strings")
    return tuple(values)


def load_manifest(path: Path) -> Manifest:
    raw = _mapping(json.loads(path.read_text(encoding="utf-8")), "manifest")
    if raw.get("schema_version") != 1:
        raise ValueError("manifest.schema_version must be 1")

    metadata_raw = _mapping(raw.get("metadata"), "manifest.metadata")
    metadata = Metadata(
        corpus=_string(metadata_raw, "corpus", "manifest.metadata"),
        copyright=_string(metadata_raw, "copyright", "manifest.metadata"),
        citation=_string(metadata_raw, "citation", "manifest.metadata"),
        bibtex_citation=_string(
            metadata_raw, "bibtex_citation", "manifest.metadata"
        ),
    )

    sources: list[SourceUnit] = []
    for index, value in enumerate(
        _sequence(raw.get("source_files"), "manifest.source_files")
    ):
        location = f"manifest.source_files[{index}]"
        item = _mapping(value, location)
        sources.append(
            SourceUnit(
                path=_string(item, "path", location),
                sha256=_string(item, "sha256", location),
                pages=_integer(item, "pages", location),
                status=_string(item, "status", location),
                record_ids=_string_tuple(item, "record_ids", location),
                disposition=_string(item, "disposition", location),
            )
        )

    records: list[Record] = []
    for index, value in enumerate(
        _sequence(raw.get("records"), "manifest.records")
    ):
        location = f"manifest.records[{index}]"
        item = _mapping(value, location)
        records.append(
            Record(
                output=_string(item, "output", location),
                text_id=_string(item, "id", location),
                language=_string(item, "language", location),
                dialect=_string(item, "dialect", location),
                source_dialect_label=_optional_string(
                    item, "source_dialect_label", location
                ),
                source=_string(item, "source", location),
                recording_date=_string(item, "recording_date", location),
                audio_url=_string(item, "audio_url", location),
                audio_file=_string(item, "audio_file", location),
                source_file=_string(item, "source_file", location),
            )
        )

    manifest = Manifest(metadata, tuple(sources), tuple(records))
    validate_manifest(manifest, path.parents[1])
    return manifest


def _safe_relative(path: str, location: str) -> PurePosixPath:
    relative = PurePosixPath(path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"{location} must be a safe relative path: {path!r}")
    return relative


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_manifest(manifest: Manifest, repo_root: Path) -> None:
    if manifest.metadata.corpus != "Whitehorn_Collection":
        raise ValueError("metadata.corpus must be Whitehorn_Collection")
    if manifest.metadata.copyright != "CC BY-NC 4.0":
        raise ValueError("metadata.copyright must match the granted license")

    source_by_path: dict[str, SourceUnit] = {}
    manifest_ids: set[str] = set()
    for source in manifest.sources:
        relative = _safe_relative(source.path, "source_files.path")
        if relative.parts[0] != "CodeAndDocs" or relative.suffix.lower() != ".pdf":
            raise ValueError(
                f"source path must name a PDF under CodeAndDocs/: {source.path}"
            )
        if source.path in source_by_path:
            raise ValueError(f"duplicate source path: {source.path}")
        if source.pages < 1:
            raise ValueError(f"source page count must be positive: {source.path}")
        if source.status not in {"included", "excluded"}:
            raise ValueError(f"invalid source status for {source.path}: {source.status}")
        if source.status == "excluded" and source.record_ids:
            raise ValueError(f"excluded source has record IDs: {source.path}")
        if source.status == "included" and not source.record_ids:
            raise ValueError(f"included source has no record IDs: {source.path}")
        source_path = repo_root / Path(*relative.parts)
        if not source_path.is_file():
            raise ValueError(f"source file is missing: {source.path}")
        actual_hash = _sha256(source_path)
        if actual_hash != source.sha256:
            raise ValueError(
                f"source hash mismatch for {source.path}: "
                f"expected {source.sha256}, got {actual_hash}"
            )
        source_by_path[source.path] = source
        manifest_ids.update(source.record_ids)

    actual_sources = {
        path.relative_to(repo_root).as_posix()
        for path in (repo_root / "CodeAndDocs").rglob("*.pdf")
    }
    if actual_sources != set(source_by_path):
        missing = sorted(actual_sources - set(source_by_path))
        stale = sorted(set(source_by_path) - actual_sources)
        raise ValueError(
            f"source inventory mismatch; unlisted={missing}, missing={stale}"
        )

    record_ids: set[str] = set()
    outputs: set[str] = set()
    audio_files: set[str] = set()
    for record in manifest.records:
        output = _safe_relative(record.output, "records.output")
        if output.suffix.lower() != ".xml":
            raise ValueError(f"record output must be XML: {record.output}")
        if record.output in outputs:
            raise ValueError(f"duplicate record output: {record.output}")
        if record.text_id in record_ids:
            raise ValueError(f"duplicate TEXT id: {record.text_id}")
        if record.audio_file in audio_files:
            raise ValueError(f"duplicate AUDIO file: {record.audio_file}")
        source = source_by_path.get(record.source_file)
        if source is None or source.status != "included":
            raise ValueError(
                f"record references a missing or excluded source: {record.text_id}"
            )
        if record.text_id not in source.record_ids:
            raise ValueError(
                f"record is absent from its source unit: {record.text_id}"
            )
        if not record.source.startswith(("http://", "https://")):
            raise ValueError(f"record source must begin with a URL: {record.text_id}")
        if not record.audio_url.startswith("https://"):
            raise ValueError(f"record audio URL must use HTTPS: {record.text_id}")
        if record.recording_date not in record.source:
            raise ValueError(
                f"recording date is not preserved in TEXT/@source: {record.text_id}"
            )
        outputs.add(record.output)
        record_ids.add(record.text_id)
        audio_files.add(record.audio_file)

    if record_ids != manifest_ids:
        unreferenced = sorted(record_ids - manifest_ids)
        missing = sorted(manifest_ids - record_ids)
        raise ValueError(
            f"source/record ID mismatch; unreferenced={unreferenced}, missing={missing}"
        )


def _render_record(record: Record, metadata: Metadata, path: Path) -> None:
    root = ET.Element(
        "TEXT",
        {
            "id": record.text_id,
            XML_LANG: record.language,
            "source": record.source,
            "audio": record.audio_url,
            "copyright": metadata.copyright,
            "citation": metadata.citation,
            "BibTeX_citation": metadata.bibtex_citation,
            "dialect": record.dialect,
        },
    )
    ET.SubElement(root, "AUDIO", {"file": record.audio_file})
    ET.indent(root, space="  ")
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(
        path,
        encoding="utf-8",
        xml_declaration=True,
        short_empty_elements=True,
    )
    with path.open("ab") as output:
        output.write(b"\n")


def render(manifest: Manifest, output_dir: Path) -> None:
    for record in manifest.records:
        relative = _safe_relative(record.output, "records.output")
        _render_record(record, manifest.metadata, output_dir / Path(*relative.parts))


def _xml_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*.xml"))
    }


def check_output(manifest: Manifest, repo_root: Path) -> None:
    committed = repo_root / "XML"
    with tempfile.TemporaryDirectory(prefix="whitehorn-check-") as directory:
        generated = Path(directory) / "XML"
        render(manifest, generated)
        expected = _xml_bytes(generated)
    actual = _xml_bytes(committed) if committed.is_dir() else {}
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        stale = sorted(set(actual) - set(expected))
        changed = sorted(
            path for path in set(actual) & set(expected) if actual[path] != expected[path]
        )
        raise ValueError(
            "XML/ is not reproducible from source_records.json; "
            f"missing={missing}, stale={stale}, changed={changed}"
        )


def sync_output(manifest: Manifest, repo_root: Path) -> None:
    output = repo_root / "XML"
    with tempfile.TemporaryDirectory(prefix="whitehorn-generate-") as directory:
        generated = Path(directory) / "XML"
        render(manifest, generated)
        expected = _xml_bytes(generated)

    output.mkdir(exist_ok=True)
    for relative, content in expected.items():
        destination = output / Path(*PurePosixPath(relative).parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

    for stale in sorted(output.rglob("*.xml")):
        if stale.relative_to(output).as_posix() not in expected:
            stale.unlink()
    for directory in sorted(
        (path for path in output.rglob("*") if path.is_dir()), reverse=True
    ):
        if not any(directory.iterdir()):
            directory.rmdir()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify that XML/ exactly matches a clean regeneration",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(repo_root / "CodeAndDocs" / "source_records.json")
    if args.check:
        check_output(manifest, repo_root)
        print(f"verified {len(manifest.sources)} sources and {len(manifest.records)} XML files")
    else:
        sync_output(manifest, repo_root)
        print(f"generated {len(manifest.records)} XML files in {repo_root / 'XML'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

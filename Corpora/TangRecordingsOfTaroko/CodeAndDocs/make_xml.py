#!/usr/bin/env python3
"""Generate the complete audio-only XML corpus from pinned source evidence."""

from __future__ import annotations

import io
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent
CORPUS_ROOT = ROOT.parent
MANIFEST = ROOT / "audio_manifest.json"
METADATA_DIR = ROOT / "Metadata"
XML_DIR = CORPUS_ROOT / "XML" / "Truku"


def format_citation(credit_text: str) -> str:
    """Convert a PARADISEC creditText string to the published citation."""

    names = list(dict.fromkeys(re.findall(r"([A-Z][^,(]+?) \(\w+\)", credit_text)))
    year_match = re.search(r"\b(\d{4})\b", credit_text)
    title_match = re.search(r"\d{4}\.\s+(.+?)\.", credit_text)
    doi_match = re.search(r"(https?://\S+)", credit_text)
    if not names or not year_match or not title_match or not doi_match:
        raise ValueError(f"incomplete PARADISEC creditText: {credit_text!r}")

    authors = "; ".join(invert_name(name.strip()) for name in names)
    title = sentence_case(title_match.group(1).strip())
    return (
        f"{authors}. ({year_match.group(1)}). {title}. Paradisec. "
        f"{doi_match.group(1)}"
    )


def format_bibtex(credit_text: str) -> str:
    """Convert a PARADISEC creditText string to the published BibTeX value."""

    names = list(dict.fromkeys(re.findall(r"([A-Z][^,(]+?) \(\w+\)", credit_text)))
    year_match = re.search(r"\b(\d{4})\b", credit_text)
    title_match = re.search(r"\d{4}\.\s+(.+?)\.", credit_text)
    doi_match = re.search(r"(https?://\S+)", credit_text)
    if not names or not year_match or not title_match or not doi_match:
        raise ValueError(f"incomplete PARADISEC creditText: {credit_text!r}")

    authors = " and ".join(invert_name(name.strip()) for name in names)
    year = year_match.group(1)
    title = sentence_case(title_match.group(1).strip())
    first_last = names[0].split()[-1].lower()
    title_word = re.sub(r"[^a-z]", "", title.split()[0].lower())
    citekey = f"{first_last}{year}{title_word}"
    return (
        f"@misc{{{citekey}, author = {{{authors}}}, title = {{{title}}}, "
        f"year = {{{year}}}, publisher = {{Paradisec}}, "
        f"howpublished = {{\\url{{{doi_match.group(1)}}}}}}}"
    )


def invert_name(name: str) -> str:
    parts = name.split()
    return f"{parts[-1]}, {' '.join(parts[:-1])}" if len(parts) >= 2 else name


def sentence_case(value: str) -> str:
    return value[:1].upper() + value[1:] if value else value


def load_manifest(path: Path = MANIFEST) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_metadata(directory: Path = METADATA_DIR) -> dict[str, dict[str, object]]:
    metadata = {}
    for metadata_file in sorted(directory.glob("*-ro-crate-metadata.json")):
        item_id = metadata_file.name.removesuffix("-ro-crate-metadata.json")
        metadata[item_id] = json.loads(
            metadata_file.read_text(encoding="utf-8")
        )["metadata"]
    return metadata


def metadata_wavs(metadata: dict[str, object]) -> set[str]:
    return {
        Path(part["@id"]).name
        for part in metadata.get("hasPart", [])
        if str(part.get("@id", "")).lower().endswith(".wav")
    }


def validate_manifest(
    manifest: dict[str, object], metadata: dict[str, dict[str, object]]
) -> None:
    if manifest.get("schema_version") != 1:
        raise ValueError("audio manifest schema_version must be 1")
    entries = manifest.get("files")
    if not isinstance(entries, list) or len(entries) != 30:
        raise ValueError("audio manifest must contain exactly 30 files")

    names = [entry.get("file") for entry in entries]
    if len(names) != len(set(names)) or any(
        not isinstance(name, str) or Path(name).name != name for name in names
    ):
        raise ValueError("audio manifest filenames must be unique basenames")

    expected_by_item: dict[str, set[str]] = {}
    for entry in entries:
        name = entry["file"]
        item_id = entry.get("paradisec_item")
        if item_id not in metadata:
            raise ValueError(f"unknown PARADISEC item for {name}: {item_id}")
        item = metadata[item_id]
        if entry.get("source_url") != item.get("@id"):
            raise ValueError(f"source URL drift for {name}")
        if entry.get("hf_path") != f"Truku/{name}":
            raise ValueError(f"unexpected Hugging Face path for {name}")
        if name not in metadata_wavs(item):
            raise ValueError(f"metadata does not enumerate {name}")
        expected_by_item.setdefault(item_id, set()).add(name)

    if set(expected_by_item) != set(metadata):
        raise ValueError("manifest and committed metadata item sets differ")
    for item_id, item in metadata.items():
        if expected_by_item[item_id] != metadata_wavs(item):
            raise ValueError(f"incomplete WAV coverage for {item_id}")


def build_text(entry: dict[str, object], metadata: dict[str, object]) -> ET.Element:
    filename = str(entry["file"])
    stem = Path(filename).stem
    text = ET.Element(
        "TEXT",
        attrib={
            "id": stem,
            "xml:lang": "trv",
            "dialect": "Truku",
            "audio": filename,
            "source": str(metadata["@id"]),
            "copyright": "CC BY-NC",
            "citation": format_citation(str(metadata["creditText"])),
            "BibTeX_citation": format_bibtex(str(metadata["creditText"])),
        },
    )
    ET.SubElement(text, "AUDIO", file=filename)
    ET.indent(text, space="    ")
    return text


def serialize_text(text: ET.Element) -> str:
    output = io.StringIO()
    ET.ElementTree(text).write(output, encoding="unicode", xml_declaration=False)
    return "<?xml version='1.0' encoding='UTF-8'?>\n" + output.getvalue() + "\n"


def main() -> None:
    manifest = load_manifest()
    metadata = load_metadata()
    validate_manifest(manifest, metadata)
    entries = manifest["files"]
    expected_names = {Path(entry["file"]).with_suffix(".xml").name for entry in entries}

    XML_DIR.mkdir(parents=True, exist_ok=True)
    unexpected = {path.name for path in XML_DIR.glob("*.xml")} - expected_names
    if unexpected:
        raise SystemExit(f"unexpected generated XML files: {sorted(unexpected)}")

    for entry in entries:
        item = metadata[entry["paradisec_item"]]
        xml_path = XML_DIR / Path(entry["file"]).with_suffix(".xml").name
        xml_path.write_text(serialize_text(build_text(entry, item)), encoding="utf-8")
        print(f"wrote {xml_path.relative_to(CORPUS_ROOT)}")
    print(f"Generated {len(entries)} complete audio-only XML files.")


if __name__ == "__main__":
    main()

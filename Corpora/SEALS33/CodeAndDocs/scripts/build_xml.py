#!/usr/bin/env python3
"""Build source-tier SEALS 33 XML from the committed structured snapshot."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from lxml import etree


CODEDOCS_ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SNAPSHOT = CODEDOCS_ROOT / "data" / "source_snapshot.json"
DEFAULT_OUTPUT = CORPUS_ROOT / "XML"
SOURCE_ROW_EXCLUSIONS = {
    25: "POL-016: source reconstruction title contains asterisks",
}
ENGLISH_ROWS = frozenset({11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 24, 25, 26, 27, 28})
COPYRIGHT = "© 2023-2024 SEALS 33 organizing committee. Used by FormosanBank with permission."
CITATION = (
    "SEALS 33 Organizing Committee. (2024). 國家語言專區. SEALS 33. "
    "https://sites.google.com/view/seals33/national-languages"
)
BIBTEX = (
    "@misc{seals33, author = {SEALS 33 Organizing Committee}, "
    "title = {國家語言專區. SEALS 33}, year = {2024}, "
    "url = {https://sites.google.com/view/seals33/national-languages}}"
)
LANGUAGES = {
    "xsy": {
        "name": "Saisiyat",
        "text_id": "saisiyat_seals",
        "filename": "saisiyat_seals.xml",
        "dialect": "Saisiyat",
    },
    "trv": {
        "name": "Seediq",
        "text_id": "seediq_SEALS",
        "filename": "seediq_SEALS.xml",
        "dialect": "unknown",
    },
}


class SnapshotError(ValueError):
    """Raised when structured source data violates the corpus contract."""


def load_snapshot(path: Path) -> dict[str, Any]:
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    validate_snapshot(snapshot)
    return snapshot


def validate_snapshot(snapshot: dict[str, Any]) -> None:
    if snapshot.get("schema_version") != 1:
        raise SnapshotError("unsupported source snapshot schema")
    rows = snapshot.get("rows")
    if not isinstance(rows, list) or len(rows) != 29:
        raise SnapshotError("source snapshot must contain 29 rows")
    ids = [row.get("source_row") for row in rows]
    if ids != list(range(1, 30)):
        raise SnapshotError(f"unexpected source row sequence: {ids}")
    for row in rows:
        source_row = row["source_row"]
        for key in ("zho", "xsy", "trv"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise SnapshotError(f"row {source_row} has invalid {key}")
        has_english = isinstance(row.get("eng"), str) and bool(row["eng"].strip())
        if has_english != (source_row in ENGLISH_ROWS):
            raise SnapshotError(f"row {source_row} has unexpected English coverage")
    policy_row = rows[24]
    if policy_row["source_row"] != 25 or "*" not in policy_row["xsy"] or "*" not in policy_row["trv"]:
        raise SnapshotError("POL-016 exclusion row no longer contains both source asterisks")


def source_attribute(snapshot: dict[str, Any]) -> str:
    return (
        f"{snapshot['source_url']}; structured snapshot retrieved "
        f"{snapshot['retrieved_at']}; permission recorded on Basecamp card "
        "8570924312; source_orthography=Ortho94"
    )


def build(snapshot_path: Path = DEFAULT_SNAPSHOT, output_dir: Path = DEFAULT_OUTPUT) -> list[Path]:
    snapshot = load_snapshot(snapshot_path)
    output_dir = output_dir.resolve()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    written: list[Path] = []
    for lang_code, config in LANGUAGES.items():
        root = etree.Element("TEXT")
        root.set("id", config["text_id"])
        root.set("{http://www.w3.org/XML/1998/namespace}lang", lang_code)
        root.set("dialect", config["dialect"])
        root.set("citation", CITATION)
        root.set("BibTeX_citation", BIBTEX)
        root.set("copyright", COPYRIGHT)
        root.set("source", source_attribute(snapshot))

        for row in snapshot["rows"]:
            source_row = row["source_row"]
            if source_row in SOURCE_ROW_EXCLUSIONS:
                continue
            sentence = etree.SubElement(root, "S", id=str(source_row))
            form = etree.SubElement(sentence, "FORM", kindOf="original")
            form.text = row[lang_code]
            zho = etree.SubElement(sentence, "TRANSL")
            zho.set("{http://www.w3.org/XML/1998/namespace}lang", "zho")
            zho.text = row["zho"]
            if "eng" in row:
                eng = etree.SubElement(sentence, "TRANSL")
                eng.set("{http://www.w3.org/XML/1998/namespace}lang", "eng")
                eng.text = row["eng"]

        destination = output_dir / config["name"] / config["filename"]
        destination.parent.mkdir(parents=True)
        tree = etree.ElementTree(root)
        etree.indent(tree, space="  ")
        tree.write(
            str(destination),
            encoding="UTF-8",
            xml_declaration=True,
            pretty_print=True,
        )
        written.append(destination)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    paths = build(args.snapshot, args.output)
    for path in paths:
        print(path)
    print("source rows included per language: 28; POL-016 exclusions: 1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

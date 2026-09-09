#!/usr/bin/env python3
"""Build source-tier SEALS 33 XML from the committed structured snapshot."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from lxml import etree


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SNAPSHOT = REPO_ROOT / "CodeAndDocs" / "source_snapshot.json"
DEFAULT_OUTPUT = REPO_ROOT / "XML"
ENGLISH_ROWS = frozenset({11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 24, 25, 26, 27, 28})
COPYRIGHT = "CC BY-NC 4.0"
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
        # Published TEXT id is lower-case; the filename is not. Both stay as
        # published (POL-037) — only the two S ids below change.
        "text_id": "seediq_seals",
        "filename": "seediq_SEALS.xml",
        "dialect": "unknown",
    },
}

# S id == source row number, in both languages. This is a deliberate,
# maintainer-approved break of POL-037 for two Seediq sentences (2026-09-09).
#
# The hand-built Seediq file had rows 21 and 22 transposed relative to the
# page and relative to the Saisiyat file, so published Seediq S21 carried the
# Piuma Paiwan title while Saisiyat S21 carried the Yami one. Holding those
# ids in place (as an earlier revision of this build did, via a published_id()
# mapping) kept the ids stable but left the two "parallel" files describing
# different source rows under the same id, and forced a non-monotonic id
# sequence in the Seediq output. The maintainer ruled that matching content
# across the two languages is worth the id break:
#
#     "we do want to change the IDs so the two S21s match on content, and
#      same for the S22s. That does mean the ID isn't stable, but this is a
#      fix worth doing."  (maintainer, 2026-09-09)
#
# Consequence to announce with the release: Seediq S21 now means the Yami
# stress title (was Piuma Paiwan) and Seediq S22 the Piuma Paiwan title (was
# Yami). No other id in either file moves.


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


def source_attribute(snapshot: dict[str, Any]) -> str:
    return (
        f"{snapshot['source_url']}; structured snapshot retrieved "
        f"{snapshot['retrieved_at']}; source_orthography=Ortho94"
    )


def build(snapshot_path: Path = DEFAULT_SNAPSHOT, output_dir: Path = DEFAULT_OUTPUT) -> list[Path]:
    snapshot = load_snapshot(snapshot_path)
    output_dir = output_dir.resolve()
    if snapshot_path.resolve().is_relative_to(output_dir):
        raise SnapshotError("output directory would remove the source snapshot")
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
    print("source rows included per language: 29; source exclusions: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

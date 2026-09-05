"""The rights vocabulary: one registry, one loader (POL-039, POL-042).

Every published TEXT/@copyright must equal one entry in the repo-root
rights_vocabulary.csv exactly. This module is the only place that file is
read, and the only place a corpus's licence is resolved from its XML.
Consumers: rules/hard.py (V160/V161), rights_delta.py, validate_hf_audio.py,
tests/corpora/test_rights_documentation.py.
"""
from __future__ import annotations

import csv
from pathlib import Path

from lxml import etree

REPO_ROOT = Path(__file__).resolve().parents[2]
VOCABULARY_PATH = REPO_ROOT / "rights_vocabulary.csv"


def load_rights_vocabulary(path: Path | None = None) -> dict[str, str]:
    """Licence value -> Hugging Face slug ("" where the value has none)."""
    source = Path(path) if path else VOCABULARY_PATH
    vocabulary: dict[str, str] = {}
    with open(source, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            value = (row["value"] or "").strip()
            if not value:
                continue
            if value in vocabulary:
                raise ValueError(f"{source}: duplicate value {value!r}")
            vocabulary[value] = (row["hf_license"] or "").strip()
    if not vocabulary:
        raise ValueError(f"{source}: no vocabulary entries")
    return vocabulary


def corpus_license(corpus_dir: Path) -> str | None:
    """The single @copyright shared by a corpus's published XML.

    None when the corpus publishes no XML. Raises when it carries more than
    one distinct value: POL-042 assumes one licence per corpus, so an
    inconsistent corpus is a question for a human, not a value to pick from.
    """
    values: set[str] = set()
    for xml_path in sorted((Path(corpus_dir) / "XML").rglob("*.xml")):
        try:
            root = etree.parse(str(xml_path)).getroot()
        except etree.XMLSyntaxError:
            continue
        values.add((root.get("copyright") or "").strip())
    if not values:
        return None
    if len(values) > 1:
        raise ValueError(
            f"{corpus_dir.name} carries more than one copyright value: "
            f"{sorted(values)}"
        )
    return values.pop()

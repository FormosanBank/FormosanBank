"""Read the POL-035 snapshot of main's 2024 ILRDF_Dicts XML (source_data/main_2024/).

See snapshot_main_xml.py for how the snapshot was taken.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import gzip
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
MAIN_DIR = BASE / "source_data" / "main_2024"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
_NUMBER = re.compile(r"_(\d+)$")


@dataclass
class MainSentence:
    identifier: str
    original: str
    translations: list[dict[str, str]] = field(default_factory=list)
    audio: list[dict[str, str]] = field(default_factory=list)

    @property
    def number(self) -> int:
        """Main ids are <Language>_<n>; n orders them ("the lowest id")."""
        match = _NUMBER.search(self.identifier)
        if match is None:
            raise ValueError(f"unexpected main id {self.identifier!r}")
        return int(match.group(1))


def _manifest() -> dict:
    return json.loads((MAIN_DIR / "manifest.json").read_text(encoding="utf-8"))


def load(language: str) -> tuple[dict[str, str], list[MainSentence]]:
    """Return main's TEXT attributes and its sentences, in file order."""
    entries = {item["language"]: item for item in _manifest()["files"]}
    entry = entries[language]
    compressed = (MAIN_DIR / entry["file"]).read_bytes()
    if hashlib.sha256(compressed).hexdigest() != entry["sha256"]:
        raise ValueError(f"{language}: main_2024 snapshot hash mismatch")
    raw = gzip.decompress(compressed)
    if hashlib.sha256(raw).hexdigest() != entry["uncompressed_sha256"]:
        raise ValueError(f"{language}: main_2024 snapshot content hash mismatch")
    root = ET.fromstring(raw)
    sentences: list[MainSentence] = []
    for element in root.findall("S"):
        original = next(
            (f.text or "" for f in element.findall("FORM")
             if f.get("kindOf") == "original" and f.get("ver") is None),
            "",
        )
        sentences.append(MainSentence(
            identifier=element.get("id"),
            original=original,
            translations=[
                {**{k: v for k, v in t.attrib.items()}, "_text": t.text or ""}
                for t in element.findall("TRANSL")
            ],
            audio=[dict(a.attrib) for a in element.findall("AUDIO")],
        ))
    return dict(root.attrib), sentences

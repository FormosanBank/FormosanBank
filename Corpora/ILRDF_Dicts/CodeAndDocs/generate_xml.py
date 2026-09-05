#!/usr/bin/env python3
"""Generate, restore, or audit canonical XML from committed ILRDF snapshots."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

from ilrdf_source import (
    LANGUAGES,
    XML_LANG,
    Sentence,
    extract_sentences,
    load_audio_exclusions,
    load_translation_exclusions,
    load_translation_overrides,
    root_attributes,
    verify_and_load_snapshot,
)


BASE = Path(__file__).resolve().parent
SOURCE_DATA = BASE / "source_data"
SNAPSHOT_DIR = SOURCE_DATA / "snapshots"
XML_DIR = BASE.parent / "XML"


def _build_tree(language: str, sentences: list[Sentence], snapshot_date: str) -> ET.Element:
    root = ET.Element("TEXT", root_attributes(language, snapshot_date))
    for sentence in sentences:
        identifier = sentence.identifier
        element = ET.SubElement(root, "S", {"id": identifier})
        ET.SubElement(element, "FORM", {"kindOf": "original"}).text = sentence.original
        translation_counts: dict[str, int] = {}
        for lang_code, text in sentence.translations:
            attributes = {XML_LANG: lang_code}
            if translation_counts.get(lang_code, 0):
                attributes["ver"] = "alt"
            translation_counts[lang_code] = translation_counts.get(lang_code, 0) + 1
            ET.SubElement(element, "TRANSL", attributes).text = text
        for index, url in enumerate(sentence.audio_urls, start=1):
            suffix = "" if index == 1 else f"_{index}"
            ET.SubElement(
                element,
                "AUDIO",
                {"url": url, "file": f"{identifier}{suffix}.mp3"},
            )
    return root


def _write_tree(root: ET.Element, path: Path) -> None:
    ET.indent(root, space="    ")
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(
        path, encoding="utf-8", xml_declaration=True, short_empty_elements=True
    )
    with path.open("ab") as handle:
        handle.write(b"\n")


LEDGER_PATH = SOURCE_DATA / "published_ids.csv"
MODES = ("generate", "audit", "ledger")
_SPLIT_SUFFIX = re.compile(r"_[a-z]$")


@dataclass
class LedgerRow:
    """One published id, as declared in source_data/published_ids.csv."""
    identifier: str
    source_guids: set[str] = field(default_factory=set)
    status: str = "active"
    note: str = ""


def _parse_ledger(handle) -> dict[str, LedgerRow]:
    rows: dict[str, LedgerRow] = {}
    for record in csv.DictReader(handle):
        identifier = (record.get("id") or "").strip()
        if not identifier:
            continue
        rows[identifier] = LedgerRow(
            identifier=identifier,
            source_guids=set((record.get("source_guids") or "").split()),
            status=(record.get("status") or "active").strip() or "active",
            note=(record.get("note") or "").strip(),
        )
    return rows


def load_ledger(path: Path) -> dict[str, LedgerRow]:
    if not path.exists():
        raise ValueError(
            f"missing id ledger {path}; run `generate_xml.py ledger --write` "
            "and review the diff before committing it"
        )
    with path.open(encoding="utf-8", newline="") as handle:
        return _parse_ledger(handle)


def render_ledger(rows: dict[str, LedgerRow]) -> str:
    lines = ["id,source_guids,status,note"]
    for identifier in sorted(rows):
        row = rows[identifier]
        note = row.note.replace('"', "'")
        if "," in note:
            note = f'"{note}"'
        lines.append(
            f"{identifier},{' '.join(sorted(row.source_guids))},{row.status},{note}"
        )
    return "\n".join(lines) + "\n"


def _base_id(identifier: str) -> str:
    """A split child's id resolves to the source record it came from."""
    return _SPLIT_SUFFIX.sub("", identifier)


def audit_ids(
    ledger: dict[str, LedgerRow],
    xml_ids: set[str],
    extracted: dict[str, set[str]],
) -> list[str]:
    """Ids may be deleted or added, never silently changed.

    Fails on exactly three things:
      - an id declared active that is no longer in the XML
      - an id in the XML that the ledger does not declare
      - a ledger id whose source GUIDs no longer match the source
    """
    errors: list[str] = []
    for identifier, row in sorted(ledger.items()):
        if row.status == "active" and identifier not in xml_ids:
            errors.append(
                f"{identifier}: declared active but silently deleted from the "
                "XML; suppress it in the ledger if that is intended"
            )
    for identifier in sorted(xml_ids):
        if identifier not in ledger:
            errors.append(
                f"{identifier}: present in the XML but not in the ledger; add "
                "a row deliberately if this is a new or split record"
            )
    for identifier, row in sorted(ledger.items()):
        source = extracted.get(_base_id(identifier))
        if source is None or not row.source_guids:
            continue
        if row.source_guids != source:
            errors.append(
                f"{identifier}: source GUIDs changed "
                f"{sorted(row.source_guids)} -> {sorted(source)}; the id now "
                "points at different source material"
            )
    return errors


def _audit_structure(expected: ET.Element, path: Path) -> list[str]:
    """Structural checks that survive the drop of source-drift auditing."""
    if not path.exists():
        return [f"missing XML: {path}"]
    actual = ET.parse(path).getroot()
    errors: list[str] = []
    sentences = actual.findall("S")
    ids = [item.get("id") for item in sentences]
    if None in ids:
        errors.append("sentence without an id")
    if len(set(ids)) != len(ids):
        errors.append("duplicate sentence ids")
    for sentence in sentences:
        if sentence.find("FORM[@kindOf='original']") is None:
            errors.append(f"{sentence.get('id')}: no original FORM")
            break
    return errors


def _select_languages(requested: list[str] | None) -> list[str]:
    if not requested:
        return list(LANGUAGES)
    invalid = sorted(set(requested) - LANGUAGES.keys())
    if invalid:
        raise ValueError(f"unknown languages: {', '.join(invalid)}")
    return [language for language in LANGUAGES if language in requested]


def run(mode: str, languages: list[str], write_ledger: bool = False) -> int:
    manifest = json.loads((SOURCE_DATA / "source_manifest.json").read_text(encoding="utf-8"))
    snapshot_date = manifest["snapshot_commit_date"]
    excluded_audio = load_audio_exclusions(SOURCE_DATA / "audio_exclusions.json")
    overrides = load_translation_overrides(
        SOURCE_DATA / "translation_language_overrides.json"
    )
    exclusions = load_translation_exclusions(
        SOURCE_DATA / "source_content_exclusions.json"
    )
    used_overrides: set[tuple[str, str, str]] = set()
    used_exclusions: set[tuple[str, str, str]] = set()
    audit_errors: list[str] = []
    audio_owners: dict[str, set[tuple[str, str]]] = {}
    extracted: dict[str, set[str]] = {}
    xml_ids: set[str] = set()

    for language in languages:
        snapshot = verify_and_load_snapshot(language, SNAPSHOT_DIR, manifest)
        sentences, stats = extract_sentences(
            language,
            snapshot,
            excluded_audio,
            overrides,
            used_overrides,
            exclusions,
            used_exclusions,
        )
        expected = _build_tree(language, sentences, snapshot_date)
        for sentence in sentences:
            extracted[sentence.identifier] = set(sentence.source_ids)
            for url in sentence.audio_urls:
                audio_owners.setdefault(url, set()).add((language, sentence.original))
        path = XML_DIR / language / f"{language}.xml"
        if mode == "generate":
            _write_tree(expected, path)
        else:
            audit_errors.extend(
                f"{language}: {error}" for error in _audit_structure(expected, path)
            )
            if path.exists():
                xml_ids.update(
                    item.get("id")
                    for item in ET.parse(path).getroot().findall("S")
                    if item.get("id")
                )
                for extra in sorted(path.parent.glob(f"{language}_*.xml")):
                    xml_ids.update(
                        item.get("id")
                        for item in ET.parse(extra).getroot().findall("S")
                        if item.get("id")
                    )
        print(f"{language}: {json.dumps(asdict(stats), sort_keys=True)}")

    relevant_overrides = {key for key in overrides if key[0] in languages}
    unused = sorted(relevant_overrides - used_overrides)
    if unused:
        audit_errors.extend(f"unused translation-language override: {key!r}" for key in unused)
    relevant_exclusions = {key for key in exclusions if key[0] in languages}
    unused_exclusions = sorted(relevant_exclusions - used_exclusions)
    if unused_exclusions:
        audit_errors.extend(
            f"unused source-content exclusion: {key!r}" for key in unused_exclusions
        )
    if mode == "ledger":
        rows = {
            identifier: LedgerRow(identifier=identifier, source_guids=guids)
            for identifier, guids in extracted.items()
        }
        if write_ledger:
            LEDGER_PATH.write_text(render_ledger(rows), encoding="utf-8")
            print(f"wrote {LEDGER_PATH} ({len(rows)} ids) — review the diff "
                  "before committing")
        else:
            print(f"{len(rows)} ids would be written to {LEDGER_PATH}")
        return 0

    if mode == "audit":
        audit_errors.extend(audit_ids(load_ledger(LEDGER_PATH), xml_ids, extracted))

    ambiguous_audio = {
        url: owners for url, owners in audio_owners.items() if len(owners) > 1
    }
    if ambiguous_audio:
        for url, owners in sorted(ambiguous_audio.items())[:20]:
            audit_errors.append(
                f"audio URL belongs to multiple sentence forms: {url!r} -> {sorted(owners)!r}"
            )
        if len(ambiguous_audio) > 20:
            audit_errors.append(
                f"{len(ambiguous_audio) - 20} additional ambiguous audio URLs omitted"
            )
    if audit_errors:
        print("Audit failed:", file=sys.stderr)
        for error in audit_errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    if mode == "audit":
        print(f"Audit passed: {len(xml_ids)} published ids across "
              f"{len(languages)} languages.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode", nargs="?", choices=MODES, default="generate"
    )
    parser.add_argument("--language", action="append", dest="languages")
    parser.add_argument(
        "--write", action="store_true",
        help="with mode 'ledger', rewrite source_data/published_ids.csv",
    )
    args = parser.parse_args()
    try:
        return run(args.mode, _select_languages(args.languages), args.write)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, ET.ParseError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate, restore, or audit canonical XML from committed ILRDF snapshots."""

from __future__ import annotations

import argparse
from dataclasses import asdict
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
    sentence_id,
    verify_and_load_snapshot,
)


BASE = Path(__file__).resolve().parent
SOURCE_DATA = BASE / "source_data"
SNAPSHOT_DIR = SOURCE_DATA / "snapshots"
XML_DIR = BASE.parent / "XML"


def _build_tree(language: str, sentences: list[Sentence], snapshot_date: str) -> ET.Element:
    root = ET.Element("TEXT", root_attributes(language, snapshot_date))
    for sentence in sentences:
        identifier = sentence_id(language, sentence.original)
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


def _source_children(element: ET.Element) -> tuple[object, ...]:
    original = element.find("FORM[@kindOf='original']")
    translations = tuple(
        (
            item.get(XML_LANG) or item.get("xml:lang"),
            item.get("ver"),
            item.text or "",
        )
        for item in element.findall("TRANSL")
    )
    audios = tuple(
        (item.get("url"), item.get("file")) for item in element.findall("AUDIO")
    )
    return (original.text if original is not None else None, translations, audios)


def _restore_processed(expected: ET.Element, path: Path) -> None:
    if not path.exists():
        raise ValueError(f"cannot restore absent XML: {path}")
    actual = ET.parse(path).getroot()
    expected_by_id = {item.get("id"): item for item in expected.findall("S")}
    actual_by_id = {item.get("id"): item for item in actual.findall("S")}
    if None in expected_by_id or None in actual_by_id:
        raise ValueError(f"{path}: sentence without ID")
    if expected_by_id.keys() != actual_by_id.keys():
        missing = sorted(expected_by_id.keys() - actual_by_id.keys())[:5]
        extra = sorted(actual_by_id.keys() - expected_by_id.keys())[:5]
        raise ValueError(f"{path}: ID drift; missing={missing}, extra={extra}")

    actual.attrib.clear()
    actual.attrib.update(expected.attrib)
    for identifier, expected_sentence in expected_by_id.items():
        actual_sentence = actual_by_id[identifier]
        standard_form = actual_sentence.find("FORM[@kindOf='standard']")
        standard_phon = actual_sentence.find("PHON[@kindOf='standard']")
        if standard_form is None:
            raise ValueError(f"{path}: {identifier} has no standard FORM")
        if standard_form.text:
            standard_form.text = re.sub(r"\s+", " ", standard_form.text).strip()
        if standard_phon is not None and standard_phon.text is None:
            raise ValueError(f"{path}: {identifier} has empty standard PHON")
        source_original = expected_sentence.find("FORM[@kindOf='original']")
        if source_original is None:
            raise ValueError(f"{path}: {identifier} has no source FORM")
        children: list[ET.Element] = [source_original, standard_form]
        if standard_phon is not None:
            children.append(standard_phon)
        children.extend(expected_sentence.findall("TRANSL"))
        children.extend(expected_sentence.findall("AUDIO"))
        actual_sentence[:] = children
    _write_tree(actual, path)


def _audit(expected: ET.Element, path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"missing XML: {path}"]
    actual = ET.parse(path).getroot()
    if actual.attrib != expected.attrib:
        errors.append("root metadata differs from the source build")
    expected_by_id = {item.get("id"): item for item in expected.findall("S")}
    actual_sentences = actual.findall("S")
    actual_by_id = {item.get("id"): item for item in actual_sentences}
    if len(actual_by_id) != len(actual_sentences):
        errors.append("duplicate or absent sentence IDs")
    missing = expected_by_id.keys() - actual_by_id.keys()
    extra = actual_by_id.keys() - expected_by_id.keys()
    if missing:
        errors.append(f"missing {len(missing)} source sentences")
    if extra:
        errors.append(f"contains {len(extra)} non-source sentences")
    for identifier in expected_by_id.keys() & actual_by_id.keys():
        if _source_children(expected_by_id[identifier]) != _source_children(
            actual_by_id[identifier]
        ):
            errors.append(f"{identifier}: source FORM, TRANSL, or AUDIO drift")
            if len(errors) >= 20:
                errors.append("additional source drift omitted")
                break
    return errors


def _select_languages(requested: list[str] | None) -> list[str]:
    if not requested:
        return list(LANGUAGES)
    invalid = sorted(set(requested) - LANGUAGES.keys())
    if invalid:
        raise ValueError(f"unknown languages: {', '.join(invalid)}")
    return [language for language in LANGUAGES if language in requested]


def run(mode: str, languages: list[str]) -> int:
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
            for url in sentence.audio_urls:
                audio_owners.setdefault(url, set()).add((language, sentence.original))
        path = XML_DIR / language / f"{language}.xml"
        if mode == "generate":
            _write_tree(expected, path)
        elif mode == "restore-source":
            _restore_processed(expected, path)
        else:
            errors = _audit(expected, path)
            audit_errors.extend(f"{language}: {error}" for error in errors)
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
        print("Source audit failed:", file=sys.stderr)
        for error in audit_errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    if mode == "audit":
        print(f"Source audit passed for {len(languages)} language files.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode", nargs="?", choices=("generate", "restore-source", "audit"), default="generate"
    )
    parser.add_argument("--language", action="append", dest="languages")
    args = parser.parse_args()
    try:
        return run(args.mode, _select_languages(args.languages))
    except (OSError, ValueError, KeyError, json.JSONDecodeError, ET.ParseError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

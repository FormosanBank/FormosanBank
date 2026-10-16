#!/usr/bin/env python3
"""Verify that every tracked NTU source is represented in generated XML."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


EXPECTED_JSON_FILES = {
    "Grammar": 52,
    "Sentences": 139,
    "Stories": 187,
}
EXPECTED_JSON_RECORDS = {
    "Grammar": 3_869,
    "Sentences": 4_430,
    "Stories": 33_209,
}
EXPECTED_STAGING_XML = {
    "Grammar": 3,
    "Sentences": 3,
    "Stories": 187,
}
EXPECTED_STAGING_SENTENCES = {
    "Grammar": 3_918,
    "Sentences": 4_478,
    "Stories": 11_621,
}
EXPECTED_CANONICAL_XML = 193
EXPECTED_CANONICAL_SENTENCES = 20_255

EXPECTED_RECOVERED_SLASH_FORMS = {
    "1_S_18_v3": "macangcangarʉ nguain.",
    "1_S_19_v4": "putukikio nguani.",
    "1_S_22_v3": "tarakanang nguain Pani.",
    "1_S_23_v4": "manmaan nguani Mu'u.",
    "1_S_199_v1": "pira'itumuroo 'Uva movua vaantuku.",
    "1_S_199_v2": "piramakangʉcoo 'Uva movua vaantuku.",
    "3_S_67_v1": "kumakʉʉn tammi nguain.",
    "3_S_67_v2": "kumakʉʉn tammi nguani.",
    "3_S_444_v1": "Tia urupaca tarisi momuun.",
    "3_S_444_v2": "Tia urupaca tarisi tumating.",
    "3_S_512_v1": "matikusaa karu iisi karu.",
    "3_S_512_v2": "matikusaa karu ramisi karu.",
}

EXPECTED_CANONICAL_MORPHEME_SLASH_FORMS = {
    "20200529-FW-Ken-1_S_6":
        "kiacilri ka ngiau pualebe ki sataetaetale.",
    "20200529-FW-Ken-1_S_6-alt2":
        "kiacilri ka ngiau mualebe ki sataetaetale.",
    "20200529-FW-Ken-1_S_6-alt3":
        "kiacilri ka ngiau mulebe ki sataetaetale.",
}

SOURCE_SECTIONS = {
    "grammar": "Grammar",
    "sentence": "Sentences",
    "story": "Stories",
}


class CoverageError(RuntimeError):
    """Raised when generated output does not cover the pinned source inventory."""


def parse_xml(path: Path) -> ET.Element:
    try:
        return ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise CoverageError(f"cannot parse {path}: {exc}") from exc


def check_equal(failures: list[str], label: str, actual: object, expected: object) -> None:
    if actual != expected:
        failures.append(f"{label}: found {actual!r}, expected {expected!r}")


def source_output_path(staging: Path, section: str, source: Path, source_root: Path) -> Path:
    relative = source.relative_to(source_root)
    if len(relative.parts) < 2:
        raise CoverageError(f"source is not inside a language directory: {source}")
    language = relative.parts[0].split("_", 1)[0]
    if section == "Stories":
        return staging / section / language / f"{language}_{source.stem}.xml"
    return staging / section / language / f"{language}.xml"


def audit(repo_root: Path) -> dict[str, int]:
    repo_root = repo_root.resolve()
    source_base = repo_root / "CodeAndDocs"
    staging = repo_root / "CodeAndDocs" / "Final_XML"
    canonical = repo_root / "XML"
    failures: list[str] = []

    if not staging.is_dir():
        failures.append(f"generated staging directory is missing: {staging}")
    if not canonical.is_dir():
        failures.append(f"canonical XML directory is missing: {canonical}")
    if failures:
        raise CoverageError("\n".join(failures))

    json_file_counts: Counter[str] = Counter()
    json_record_counts: Counter[str] = Counter()
    source_files: dict[str, list[tuple[Path, Path]]] = {
        section: [] for section in SOURCE_SECTIONS.values()
    }

    for source_name, section in SOURCE_SECTIONS.items():
        source_root = source_base / source_name
        paths = sorted(source_root.rglob("*.json"))
        for path in paths:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                failures.append(f"cannot read source JSON {path}: {exc}")
                continue
            records = payload.get("glosses") if isinstance(payload, dict) else None
            if not isinstance(records, list) or not records:
                failures.append(f"source JSON has no non-empty glosses list: {path}")
                continue
            json_file_counts[section] += 1
            json_record_counts[section] += len(records)
            try:
                output = source_output_path(staging, section, path, source_root)
            except CoverageError as exc:
                failures.append(str(exc))
                continue
            source_files[section].append((path, output))

    check_equal(failures, "JSON file counts", dict(json_file_counts), EXPECTED_JSON_FILES)
    check_equal(
        failures,
        "JSON gloss-record counts",
        dict(json_record_counts),
        EXPECTED_JSON_RECORDS,
    )

    staging_xml: dict[str, list[Path]] = {}
    staging_roots: dict[Path, ET.Element] = {}
    for section in EXPECTED_STAGING_XML:
        paths = sorted((staging / section).rglob("*.xml"))
        staging_xml[section] = paths
        check_equal(
            failures,
            f"{section} staging XML files",
            len(paths),
            EXPECTED_STAGING_XML[section],
        )
        sentence_count = 0
        for path in paths:
            try:
                root = parse_xml(path)
            except CoverageError as exc:
                failures.append(str(exc))
                continue
            staging_roots[path] = root
            sentence_count += len(root.findall(".//S"))
        check_equal(
            failures,
            f"{section} staging sentences",
            sentence_count,
            EXPECTED_STAGING_SENTENCES[section],
        )

    recovered_path = staging / "Sentences" / "Kanakanavu" / "Kanakanavu.xml"
    recovered_root = staging_roots.get(recovered_path)
    if recovered_root is not None:
        recovered = {
            sentence.get("id"): (
                sentence.find("FORM[@kindOf='original']").text
                if sentence.find("FORM[@kindOf='original']") is not None
                else None
            )
            for sentence in recovered_root.findall("S")
            if sentence.get("id") in EXPECTED_RECOVERED_SLASH_FORMS
        }
        check_equal(
            failures,
            "recovered slash-alternative forms",
            recovered,
            EXPECTED_RECOVERED_SLASH_FORMS,
        )

    missing_sources: list[str] = []
    for section, mappings in source_files.items():
        for source, output in mappings:
            root = staging_roots.get(output)
            if root is None:
                missing_sources.append(f"{source}: expected output {output}")
                continue
            prefix = f"{source.stem}_S_"
            if not any((sentence.get("id") or "").startswith(prefix) for sentence in root.findall(".//S")):
                missing_sources.append(f"{source}: no sentence ID beginning {prefix!r}")
    if missing_sources:
        failures.append(
            f"{len(missing_sources)} JSON sources are not mapped to staging XML:\n  "
            + "\n  ".join(missing_sources)
        )

    canonical_files = sorted(path for path in canonical.rglob("*") if path.is_file())
    non_xml = [str(path.relative_to(repo_root)) for path in canonical_files if path.suffix != ".xml"]
    if non_xml:
        failures.append("canonical XML tree contains non-XML files: " + ", ".join(non_xml))
    canonical_xml = [path for path in canonical_files if path.suffix == ".xml"]
    check_equal(failures, "canonical XML files", len(canonical_xml), EXPECTED_CANONICAL_XML)

    rukai_path = canonical / "Sentences" / "Rukai" / "Rukai.xml"
    if rukai_path in canonical_xml:
        try:
            rukai_root = parse_xml(rukai_path)
        except CoverageError as exc:
            failures.append(str(exc))
        else:
            recovered = {
                sentence.get("id"): (
                    sentence.find("FORM[@kindOf='original']").text
                    if sentence.find("FORM[@kindOf='original']") is not None
                    else None
                )
                for sentence in rukai_root.findall("S")
                if sentence.get("id")
                in EXPECTED_CANONICAL_MORPHEME_SLASH_FORMS
            }
            check_equal(
                failures,
                "canonical morpheme slash-alternative forms",
                recovered,
                EXPECTED_CANONICAL_MORPHEME_SLASH_FORMS,
            )

    staging_relative = {
        path.relative_to(staging) for paths in staging_xml.values() for path in paths
    }
    canonical_legacy_relative = {
        path.relative_to(canonical)
        for path in canonical_xml
    }
    if staging_relative != canonical_legacy_relative:
        missing = sorted(str(path) for path in staging_relative - canonical_legacy_relative)
        extra = sorted(str(path) for path in canonical_legacy_relative - staging_relative)
        failures.append(
            "legacy staging/canonical file mapping differs; "
            f"missing={missing!r}, extra={extra!r}"
        )

    canonical_sentences = 0
    for path in canonical_xml:
        try:
            root = parse_xml(path)
        except CoverageError as exc:
            failures.append(str(exc))
            continue
        canonical_sentences += len(root.findall(".//S"))

    check_equal(
        failures,
        "canonical sentences",
        canonical_sentences,
        EXPECTED_CANONICAL_SENTENCES,
    )

    if failures:
        raise CoverageError("source coverage audit failed:\n- " + "\n- ".join(failures))

    return {
        "json_files": sum(json_file_counts.values()),
        "json_records": sum(json_record_counts.values()),
        "legacy_xml": sum(len(paths) for paths in staging_xml.values()),
        "legacy_sentences": sum(EXPECTED_STAGING_SENTENCES.values()),
        "canonical_xml": len(canonical_xml),
        "canonical_sentences": canonical_sentences,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Formosan-NTU repository root",
    )
    args = parser.parse_args()
    try:
        stats = audit(args.repo_root)
    except CoverageError as exc:
        print(exc, file=sys.stderr)
        return 1

    print("Source coverage audit passed")
    for label, value in stats.items():
        print(f"  {label}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

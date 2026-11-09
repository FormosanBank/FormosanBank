"""Every record of the source is accounted for: published, or left out with a reason.

The units are the transcription's records (source_units.tsv: one per printed example or vocabulary entry, read off
the scan page by page) and the 14 printed examples it missed (source_units_additions.tsv). source_coverage.tsv states
the source's own extent: PDF pages 001 to 122, with each page's count of included examples and vocabulary entries.

What this checks: each included record is in the published XML (its sentence's @source names it); each excluded
record carries a reason; no published sentence comes from anything else; and the per-page counts match the records.
It reads only tracked files, so it runs without the private scan.

What it cannot check: a printed example that no record captures. The coverage file's notes list the starred
examples left out (11, on 8 pages); 14 examples the transcription missed were found later and added.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

CODE = Path(__file__).resolve().parents[1]
CORPUS = CODE.parent
sys.path.insert(0, str(CODE))

import build_xml  # noqa: E402


def records() -> list[dict[str, str]]:
    rows = []
    for name in ("source_units.tsv", "source_units_additions.tsv"):
        with (CODE / name).open(encoding="utf-8", newline="") as handle:
            rows += list(csv.DictReader(handle, delimiter="\t"))
    return rows


def published_sources() -> dict[str, set[str]]:
    """Sentence id -> the source records its @source names."""
    root = ET.parse(build_xml.OUT_XML).getroot()
    return {s.get("id"): set(re.findall(r"source unit (\S+?)(?:;|$|\s)", s.get("source", "") + " "))
            for s in root.findall("S")}


def test_record_ids_are_unique():
    ids = [row["unit_id"] for row in records()]
    assert len(ids) == len(set(ids)), "a record id appears twice"


def test_every_included_record_is_published():
    named = set().union(*published_sources().values())
    missing = sorted(row["unit_id"] for row in records() if row["decision"] == "include" and row["unit_id"] not in named)
    assert not missing, f"{len(missing)} included records are in no published sentence: {missing[:10]}"


def test_every_excluded_record_has_a_reason():
    empty = sorted(row["unit_id"] for row in records() if row["decision"] == "exclude" and not row["decision_reason"].strip())
    assert not empty, f"excluded without a reason: {empty[:10]}"
    unknown = sorted({row["decision"] for row in records()} - {"include", "exclude"})
    assert not unknown, f"records that are neither included nor excluded: {unknown}"


def test_nothing_published_comes_from_outside_the_records():
    included = {row["unit_id"] for row in records() if row["decision"] == "include"}
    excluded = {row["unit_id"] for row in records() if row["decision"] == "exclude"}
    for sentence, named in published_sources().items():
        assert named, f"{sentence} names no source record"
        assert not named & excluded, f"{sentence} comes from an excluded record: {sorted(named & excluded)}"
        assert named <= included, f"{sentence} names records that do not exist: {sorted(named - included)}"


def test_the_source_extent_matches_the_records():
    """122 PDF pages, each page's included and vocabulary counts equal to its records' (validate_coverage)."""
    with (CODE / "source_coverage.tsv").open(encoding="utf-8", newline="") as handle:
        pages = [row["pdf_page"] for row in csv.DictReader(handle, delimiter="\t")]
    assert pages == [f"{page:03d}" for page in range(1, 123)]
    build_xml.validate_coverage(build_xml.load_source_units())

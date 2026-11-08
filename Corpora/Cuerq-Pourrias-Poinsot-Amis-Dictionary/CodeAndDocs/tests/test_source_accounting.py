"""Every source unit is accounted for: emitted, or rejected with a reason.

A "complete" inventory that is complete only of itself is the defect this test exists for (Seediq-Chang: 353 of
353 blocks "reviewed" while chapters 5 and 6 were never extracted). The unit here is one line of the pinned source
text, source/pourrias-poinsot.txt (one dictionary entry per line; S ids carry it as -L<line>). Each line is either
in XML/ or rejected with a reason: ruled out (data/exclusions.tsv, with the ruling as the reason) or a printed
continuation joined to the line above (data/line_wraps.tsv, decision "joined"). The extent is checked against
the source itself: 17,930 lines.
"""
import csv
import re
from pathlib import Path

import pytest
from lxml import etree

HERE = Path(__file__).resolve().parent
CODE = HERE.parent                      # CodeAndDocs/
CORPUS = CODE.parent
SOURCE = CODE / "source" / "pourrias-poinsot.txt"
DATA = CODE / "data"
XML_DIR = CORPUS / "XML"


def source_units() -> set[int]:
    """Every non-empty line of the source text, by line number."""
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    return {n for n, line in enumerate(lines, start=1) if line.strip()}


def emitted_units() -> set[int]:
    lines = set()
    for path in XML_DIR.rglob("*.xml"):
        for s in etree.parse(str(path)).iter("S"):
            m = re.search(r"-L(\d{5})", s.get("id"))
            if m:
                lines.add(int(m.group(1)))
    return lines


def _tsv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def rejected_units() -> dict[int, str]:
    rejected = {int(r["line"]): f"excluded: {r['reason']}" for r in _tsv("exclusions.tsv")}
    for r in _tsv("line_wraps.tsv"):
        if r["decision"] == "joined":
            rejected[int(r["line"])] = f"joined to line {int(r['line']) - 1}: {r['evidence']}"
    return rejected


needs_source = pytest.mark.skipif(not SOURCE.exists(), reason="source not on disk")


@needs_source
def test_source_declares_the_same_extent():
    assert len(source_units()) == 17930, "the pinned source has 17,930 entry lines"


@needs_source
def test_every_source_unit_is_emitted_or_rejected():
    units = source_units()
    unaccounted = sorted(units - emitted_units() - set(rejected_units()))
    assert unaccounted[:20] == [], f"{len(unaccounted)} source lines are neither in XML/ nor rejected"


def test_emitted_and_rejected_are_disjoint():
    both = sorted(emitted_units() & set(rejected_units()))
    assert both[:20] == [], f"{len(both)} lines are both emitted and rejected"


def test_every_rejection_has_a_reason():
    empty = [n for n, reason in rejected_units().items() if not reason.split(":", 1)[1].strip()]
    assert empty == [], f"rejections without a reason: {empty[:20]}"

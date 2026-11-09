"""Every source unit is accounted for: emitted, or rejected with a reason.

A "complete" inventory that is complete only of itself is the defect this
test exists for (Seediq-Chang: 353 of 353 blocks "reviewed" while chapters 5
and 6 were never extracted). The test enumerates the SOURCE's own units and
checks that each is either in the published XML or in the rejected list, that
the two sets are disjoint, and that every rejection carries a reason. It skips
when the source is not on disk (a private PDF does not ship with the corpus).

Unit here: one interlinear table on a text page of kanakanavu.info, named by
its `rf` row. The source side is read with a plain regular expression over the
raw HTML, deliberately not with generate_xml.py's parser, so the two can
disagree.
"""
from pathlib import Path
import csv
import json
import re

import pytest
from lxml import etree

HERE = Path(__file__).resolve().parent
CODE = HERE.parent                      # CodeAndDocs/
CORPUS = CODE.parent
SOURCE = CODE / "source"
REJECTED = CODE / "rejected.tsv"        # unit<TAB>reason, written by generate_xml.py
XML_DIR = CORPUS / "XML"


PAGES = SOURCE / "html" / "language-documentation"
PREFIX = json.loads((CODE / "corpus_metadata.json").read_text(encoding="utf-8"))["text_id_prefix"]
RF_CELL = re.compile(r'<td class="label">rf\s*</td>\s*<td[^>]*>([^<]*)</td>', re.S)
TABLE = re.compile(r'<table>(.*?)</table>', re.S)


def text_pages() -> list[Path]:
    return sorted(p for p in PAGES.glob("*.html") if p.name != "index.html")


def source_units() -> set[str]:
    """Every inner table on every text page, as <TEXT id>_<rf without apostrophes>."""
    units = set()
    for page in text_pages():
        raw = page.read_text(encoding="latin-1")
        text_id = f"{PREFIX}_{page.stem.replace('-', '_')}"
        for k, table in enumerate(TABLE.findall(raw)):
            m = RF_CELL.search(table)
            assert m, f"{page.name}: table {k} has no rf row"
            rf = m.group(1).strip().replace("&#39;", "'").replace("'", "")
            units.add(f"{text_id}_{rf}")
    return units


def emitted_units() -> set[str]:
    """S/@id of every sentence in XML/, a second reading (<id>-opt, POL-028)
    counted as its source table."""
    ids = set()
    for path in XML_DIR.rglob("*.xml"):
        for s in etree.parse(str(path)).iter("S"):
            ids.add(s.get("id").removesuffix("-opt"))
    return ids


def rejected_units() -> dict[str, str]:
    if not REJECTED.exists():
        return {}
    with REJECTED.open(encoding="utf-8", newline="") as handle:
        return {row["unit"]: row["reason"] for row in csv.DictReader(handle, delimiter="\t")}


needs_source = pytest.mark.skipif(not SOURCE.exists(), reason="source not on disk (private)")


@needs_source
def test_every_source_unit_is_emitted_or_rejected():
    units = source_units()
    emitted, rejected = emitted_units(), rejected_units()
    missing = sorted(units - emitted - set(rejected))
    assert not missing, f"{len(missing)} source units neither emitted nor rejected: {missing[:10]}"
    both = sorted(emitted & set(rejected))
    assert not both, f"emitted AND rejected: {both[:10]}"
    unknown = sorted((emitted | set(rejected)) - units)
    assert not unknown, f"not in the source at all: {unknown[:10]}"


def test_every_rejection_has_a_reason():
    empty = sorted(u for u, reason in rejected_units().items() if not reason.strip())
    assert not empty, f"rejected without a reason: {empty[:10]}"


@needs_source
def test_source_declares_the_same_extent():
    """The site's own menu (the Language Documentation index) lists its text
    pages; the scrape must hold exactly those, and the build one file each."""
    index = (PAGES / "index.html").read_text(encoding="latin-1")
    listed = set(re.findall(r'href="([a-z0-9-]+\.html)"', index))
    present = {p.name for p in text_pages()}
    print(f"menu lists {len(listed)} text pages; scrape holds {len(present)}")
    assert listed == present
    built = {p.name for p in XML_DIR.rglob("*.xml")}
    assert len(built) == len(present), f"{len(built)} XML files for {len(present)} pages"

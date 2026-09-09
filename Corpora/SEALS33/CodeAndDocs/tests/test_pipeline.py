from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
from lxml import etree

from scripts.build_xml import BIBTEX, DEFAULT_SNAPSHOT, SnapshotError, build, load_snapshot
from scripts.source_audit import AuditError, audit

CORPUS_ROOT = Path(__file__).resolve().parents[2]


def test_snapshot_has_complete_parallel_coverage() -> None:
    snapshot = load_snapshot(DEFAULT_SNAPSHOT)
    rows = snapshot["rows"]
    assert [row["source_row"] for row in rows] == list(range(1, 30))
    assert sum("eng" in row for row in rows) == 16
    assert len(snapshot["excluded_presenter_blocks"]) == 16
    assert rows[1]["zho"].endswith("(SEALS 33)")
    assert "). ’isahini" in rows[8]["xsy"]
    assert rows[24]["xsy"].startswith("pinaskayzaeh naehan")
    assert "*-ʔ" in rows[24]["xsy"]
    # Source order: row 21 is the Yami title, row 22 the Piuma Paiwan one.
    assert rows[20]["trv"] == "Hengak chedil na kari Yami (Tao)"
    assert rows[21]["trv"].startswith("Pnseengan hengak")


def test_build_aligns_s_ids_with_source_rows_in_both_languages(tmp_path: Path) -> None:
    """S id == source row number, identically in both files.

    The published Seediq file had rows 21/22 transposed, so Seediq S21 and
    Saisiyat S21 described different talks. The maintainer ruled on
    2026-09-09 that matching content across the two languages is worth the
    POL-037 id break, so both files now key straight off the source row and
    the ids run monotonically.
    """
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_files = build(output_dir=first)
    second_files = build(output_dir=second)
    assert [path.relative_to(first) for path in first_files] == [
        path.relative_to(second) for path in second_files
    ]
    titles_by_id: dict[str, dict[int, str]] = {}
    for left, right in zip(first_files, second_files, strict=True):
        assert left.read_bytes() == right.read_bytes()
        root = etree.parse(str(left)).getroot()
        text_id = root.get("id")
        assert text_id in {"saisiyat_seals", "seediq_seals"}
        ids = [int(sentence.get("id")) for sentence in root.findall("S")]
        assert ids == list(range(1, 30))
        if text_id == "seediq_seals":
            assert root.findtext("S[@id='21']/FORM") == "Hengak chedil na kari Yami (Tao)"
            assert root.findtext("S[@id='22']/FORM").startswith("Pnseengan hengak")
        title = root.findtext("S[@id='25']/FORM")
        if text_id == "saisiyat_seals":
            assert title.startswith("pinaskayzaeh naehan noka ka:i’ ka hikor")
        assert all(marker in title for marker in ("*-ʔ", "*-h", "*-∅"))
        assert root.get("copyright") == "CC BY-NC 4.0"
        # One BibTeX string for the corpus: the published Saisiyat value had a
        # stray period after "SEALS 33" that the Seediq one lacked.
        assert root.get("BibTeX_citation") == BIBTEX
        assert "SEALS 33.}" not in root.get("BibTeX_citation")
        titles_by_id[text_id] = {
            int(s.get("id")): (s.findtext("TRANSL[@{http://www.w3.org/XML/1998/namespace}lang='eng']") or "")
            for s in root.findall("S")
        }
    # The point of the id change: the same id names the same talk in both files.
    assert titles_by_id["saisiyat_seals"] == titles_by_id["seediq_seals"]


def test_source_audit_accepts_raw_build(tmp_path: Path) -> None:
    output = tmp_path / "XML"
    build(output_dir=output)
    result = audit(xml_dir=output)
    assert result["status"] == "pass"
    assert result["included_original_forms"] == 58
    assert result["included_translations"] == 90


def test_source_audit_rejects_changed_original_form(tmp_path: Path) -> None:
    output = tmp_path / "XML"
    paths = build(output_dir=output)
    tree = etree.parse(str(paths[0]))
    tree.xpath('//S[@id="24"]/FORM[@kindOf="original"]')[0].text = "changed"
    tree.write(str(paths[0]), encoding="UTF-8", xml_declaration=True)
    with pytest.raises(AuditError, match="source FORM mismatch"):
        audit(xml_dir=output)


def test_build_cannot_remove_its_source_snapshot(tmp_path: Path) -> None:
    snapshot = tmp_path / "source.json"
    before = DEFAULT_SNAPSHOT.read_bytes()
    snapshot.write_bytes(before)
    with pytest.raises(SnapshotError, match="would remove the source"):
        build(snapshot_path=snapshot, output_dir=tmp_path)
    assert snapshot.read_bytes() == before


def test_waivers_cover_the_reconstruction_title_only() -> None:
    """The S25 asterisks are waived; nothing else is.

    Replaces the corpus-owned check_hard_findings.py guard, folded into the
    shared mechanism in QC/validation/_waivers.py (POL-054). The validators
    enforce the rest: an unwaived HARD finding fails, and a waiver matching
    no current finding fails as stale.
    """
    path = CORPUS_ROOT / "CodeAndDocs" / "qc_waivers.tsv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    assert {(r["rule_id"], r["file"], r["location"]) for r in rows} == {
        ("V129", "Saisiyat/saisiyat_seals.xml", "S=25"),
        ("V129", "Seediq/seediq_SEALS.xml", "S=25"),
    }
    assert all("reconstruction" in r["reason"].lower() for r in rows)


def test_snapshot_validation_rejects_missing_source_row(tmp_path: Path) -> None:
    snapshot = json.loads(DEFAULT_SNAPSHOT.read_text(encoding="utf-8"))
    snapshot["rows"].pop()
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(snapshot), encoding="utf-8")
    with pytest.raises(SnapshotError, match="29 rows"):
        load_snapshot(path)

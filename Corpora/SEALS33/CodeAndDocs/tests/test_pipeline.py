from __future__ import annotations

import json
import csv
from pathlib import Path

import pytest
from lxml import etree

from scripts.build_xml import DEFAULT_SNAPSHOT, SnapshotError, build, load_snapshot
from scripts.source_audit import AuditError, audit
from scripts.check_hard_findings import check


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
    assert rows[20]["trv"] == "Hengak chedil na kari Yami (Tao)"
    assert rows[21]["trv"].startswith("Pnseengan hengak")


def test_build_preserves_reconstruction_titles_and_published_ids(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_files = build(output_dir=first)
    second_files = build(output_dir=second)
    assert [path.relative_to(first) for path in first_files] == [
        path.relative_to(second) for path in second_files
    ]
    for left, right in zip(first_files, second_files, strict=True):
        assert left.read_bytes() == right.read_bytes()
        root = etree.parse(str(left)).getroot()
        ids = [int(sentence.get("id")) for sentence in root.findall("S")]
        expected = list(range(1, 30))
        if root.get("id") == "seediq_seals":
            expected[20:22] = [22, 21]
            assert root.findtext("S[@id='22']/FORM") == "Hengak chedil na kari Yami (Tao)"
            assert root.findtext("S[@id='21']/FORM").startswith("Pnseengan hengak")
        else:
            assert root.get("id") == "saisiyat_seals"
        assert ids == expected
        title = root.findtext("S[@id='25']/FORM")
        if root.get("id") == "saisiyat_seals":
            assert title.startswith("pinaskayzaeh naehan noka ka:i’ ka hikor")
        assert all(marker in title for marker in ("*-ʔ", "*-h", "*-∅"))
        assert root.get("copyright") == "CC BY-NC 4.0"


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


def test_hard_exception_rejects_another_sentence(tmp_path: Path) -> None:
    fields = ["file", "severity", "rule_id", "location", "message", "count"]
    rows = [
        [name, "HARD", "V129", "S=25", f"kindOf='{tier}'", "1"]
        for name in ("saisiyat_seals.xml", "seediq_SEALS.xml")
        for tier in ("original", "standard")
    ]
    with (tmp_path / "xml.csv").open("w", newline="") as handle:
        csv.writer(handle).writerow(fields)

    def write_text_findings() -> None:
        with (tmp_path / "text.csv").open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(fields)
            writer.writerows(rows)

    write_text_findings()
    check(tmp_path)
    rows[0][3] = "S=24"
    write_text_findings()
    with pytest.raises(ValueError, match="Unreviewed HARD"):
        check(tmp_path)
    rows.clear()
    write_text_findings()
    with pytest.raises(ValueError, match="Expected four scoped"):
        check(tmp_path)


def test_snapshot_validation_rejects_missing_source_row(tmp_path: Path) -> None:
    snapshot = json.loads(DEFAULT_SNAPSHOT.read_text(encoding="utf-8"))
    snapshot["rows"].pop()
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(snapshot), encoding="utf-8")
    with pytest.raises(SnapshotError, match="29 rows"):
        load_snapshot(path)

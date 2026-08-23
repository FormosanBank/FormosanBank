from __future__ import annotations

import json
from pathlib import Path

import pytest
from lxml import etree

from scripts.build_xml import DEFAULT_SNAPSHOT, SnapshotError, build, load_snapshot
from scripts.source_audit import AuditError, audit


def test_snapshot_has_complete_parallel_coverage() -> None:
    snapshot = load_snapshot(DEFAULT_SNAPSHOT)
    rows = snapshot["rows"]
    assert [row["source_row"] for row in rows] == list(range(1, 30))
    assert sum("eng" in row for row in rows) == 16
    assert len(snapshot["excluded_presenter_blocks"]) == 16
    assert rows[24]["xsy"].startswith("pinaskayzaeh naehan")
    assert "*-ʔ" in rows[24]["xsy"]
    assert rows[20]["trv"] == "Hengak chedil na kari Yami (Tao)"
    assert rows[21]["trv"].startswith("Pnseengan hengak")


def test_build_is_deterministic_and_excludes_policy_row(tmp_path: Path) -> None:
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
        assert ids == [row for row in range(1, 30) if row != 25]
        assert "*" not in "".join(root.xpath("//FORM/text()"))


def test_source_audit_accepts_raw_build(tmp_path: Path) -> None:
    output = tmp_path / "XML"
    build(output_dir=output)
    result = audit(xml_dir=output)
    assert result["status"] == "pass"
    assert result["included_original_forms"] == 56
    assert result["included_translations"] == 86


def test_source_audit_rejects_changed_original_form(tmp_path: Path) -> None:
    output = tmp_path / "XML"
    paths = build(output_dir=output)
    tree = etree.parse(str(paths[0]))
    tree.xpath('//S[@id="24"]/FORM[@kindOf="original"]')[0].text = "changed"
    tree.write(str(paths[0]), encoding="UTF-8", xml_declaration=True)
    with pytest.raises(AuditError, match="source FORM mismatch"):
        audit(xml_dir=output)


def test_snapshot_validation_rejects_missing_source_row(tmp_path: Path) -> None:
    snapshot = json.loads(DEFAULT_SNAPSHOT.read_text(encoding="utf-8"))
    snapshot["rows"].pop()
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(snapshot), encoding="utf-8")
    with pytest.raises(SnapshotError, match="29 rows"):
        load_snapshot(path)

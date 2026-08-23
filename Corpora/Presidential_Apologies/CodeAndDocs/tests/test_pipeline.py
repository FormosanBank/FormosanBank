from __future__ import annotations

import csv
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from CodeAndDocs.main import generate_all, load_specs, read_sections
from CodeAndDocs.scripts.remove_standard_cjk_annotations import remove_annotations

REPO_ROOT = Path(__file__).resolve().parents[2]
CODE_ROOT = REPO_ROOT / "CodeAndDocs"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def xml_root() -> Path:
    return Path(os.environ.get("PRESIDENTIAL_XML_ROOT", REPO_ROOT / "XML"))


def public_xml_root() -> Path | None:
    value = os.environ.get("PRESIDENTIAL_PUBLIC_XML_ROOT")
    return Path(value) if value else None


def element_signature(element: ET.Element) -> tuple:
    return (
        element.tag,
        tuple(sorted(element.attrib.items())),
        element.text or "",
        tuple(element_signature(child) for child in element),
    )


def test_external_mapping_is_complete_and_unique() -> None:
    specs = load_specs()
    assert len(specs) == 16
    assert sum(spec.sections for spec in specs) == 524
    assert len({spec.language for spec in specs}) == 16
    assert len({spec.text_id for spec in specs}) == 16
    assert all(len(spec.iso_639_3) == 3 for spec in specs)
    assert all(spec.dialect for spec in specs)


def test_source_generator_preserves_recorded_sections(tmp_path: Path) -> None:
    specs = load_specs()
    assert generate_all(tmp_path, specs) == 524
    for spec in specs:
        root = ET.parse(tmp_path / spec.language / f"{spec.language}.xml").getroot()
        sentences = root.findall("S")
        assert root.get("id") == spec.text_id
        assert root.get(XML_LANG) == spec.iso_639_3
        assert root.get("dialect") == spec.dialect
        assert [sentence.get("id") for sentence in sentences] == [
            str(index) for index in range(spec.sections)
        ]
        originals = read_sections(spec.source_file, spec.sections)
        chinese = read_sections(spec.chinese_file, spec.sections)
        english = read_sections(spec.english_file, spec.sections)
        for index, sentence in enumerate(sentences):
            assert sentence.findtext('FORM[@kindOf="original"]') == originals[index]
            translations = {
                item.get(XML_LANG): item.text for item in sentence.findall("TRANSL")
            }
            assert translations == {"zho": chinese[index], "eng": english[index]}


def test_committed_xml_has_complete_owned_tiers() -> None:
    total = 0
    files = sorted(xml_root().glob("*/*.xml"))
    assert len(files) == 16
    for path in files:
        root = ET.parse(path).getroot()
        assert root.tag == "TEXT"
        assert root.get("copyright") == "public domain"
        assert root.get("dialect")
        for sentence in root.findall("S"):
            total += 1
            assert {item.get("kindOf") for item in sentence.findall("FORM")} == {
                "original",
                "standard",
            }
            assert {item.get("kindOf") for item in sentence.findall("PHON")} == {
                "original",
                "standard",
            }
            assert {item.get(XML_LANG) for item in sentence.findall("TRANSL")} == {
                "zho",
                "eng",
            }
            assert not sentence.findall("W")
            assert not sentence.findall("M")
    assert total == 524


def test_published_ids_are_stable_and_only_source_corrections_change() -> None:
    baseline_root = public_xml_root()
    if baseline_root is None:
        pytest.skip("PRESIDENTIAL_PUBLIC_XML_ROOT is not set")
    allowed = {("Saaroa", "0"), ("Truku", "25")}
    changed: set[tuple[str, str]] = set()
    for spec in load_specs():
        current = ET.parse(
            xml_root() / spec.language / f"{spec.language}.xml"
        ).getroot()
        baseline = ET.parse(
            baseline_root / spec.language / f"{spec.language}.xml"
        ).getroot()
        assert current.attrib == baseline.attrib
        current_sentences = current.findall("S")
        baseline_sentences = baseline.findall("S")
        assert [item.get("id") for item in current_sentences] == [
            item.get("id") for item in baseline_sentences
        ]
        for current_sentence, baseline_sentence in zip(
            current_sentences, baseline_sentences, strict=True
        ):
            if element_signature(current_sentence) != element_signature(baseline_sentence):
                key = (spec.language, current_sentence.get("id", ""))
                changed.add(key)
                assert key in allowed
                current_translations = [
                    element_signature(item)
                    for item in current_sentence.findall("TRANSL")
                ]
                baseline_translations = [
                    element_signature(item)
                    for item in baseline_sentence.findall("TRANSL")
                ]
                assert current_translations == baseline_translations
    assert changed == allowed


def test_source_corrections_are_explicit() -> None:
    with (CODE_ROOT / "data" / "source_corrections.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert {(row["language"], row["section_id"]) for row in rows} == {
        ("Kavalan", "6"),
        ("Saaroa", "0"),
        ("Truku", "25"),
    }
    saaroa = read_sections(
        CODE_ROOT / "Apologies" / "Saaroa" / "Saaroa.txt", 33
    )[0]
    truku = read_sections(CODE_ROOT / "Apologies" / "Truku" / "Truku.txt", 33)[25]
    assert "mualiuhlu" in saaroa
    assert "mualiuhlʉ" not in saaroa
    assert "tnpusu＇,“" in truku
    assert "tnpusu;,“" not in truku


def test_source_manifest_and_alignment_inventory() -> None:
    with (CODE_ROOT / "data" / "source_manifest.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        manifest = list(csv.DictReader(handle))
    assert len(manifest) == 36
    assert len({row["path"] for row in manifest}) == 36
    assert sum(row["kind"] == "official_bilingual_pdf" for row in manifest) == 16

    report_path = Path(
        os.environ.get(
            "PRESIDENTIAL_ALIGNMENT_REPORT",
            CODE_ROOT / "data" / "source_alignment.csv",
        )
    )
    with report_path.open(encoding="utf-8", newline="") as handle:
        alignment = list(csv.DictReader(handle))
    assert len(alignment) == 1048
    assert {row["score"] for row in alignment} == {"100.000"}
    assert {row["channel"] for row in alignment} == {"native", "chinese"}
    saaroa_pages = {
        row["section_id"]: row["pdf_page_start"]
        for row in alignment
        if row["language"] == "Saaroa"
        and row["channel"] == "native"
        and row["section_id"] in {"22", "23"}
    }
    assert saaroa_pages == {"22": "22", "23": "23"}


@pytest.mark.parametrize(
    ("source", "expected", "removed"),
    [
        ("zipun( 日 本 ) kari", "zipun kari", 1),
        ("taa'uzva(taa'uiva)", "taa'uzva(taa'uiva)", 0),
        ("行政院 ho", "行政院 ho", 0),
    ],
)
def test_cjk_annotation_removal(
    source: str, expected: str, removed: int
) -> None:
    assert remove_annotations(source) == (expected, removed)


def test_qc_findings_match_reviewed_expectations() -> None:
    report_value = os.environ.get("PRESIDENTIAL_QC_REPORT_ROOT")
    if not report_value:
        pytest.skip("PRESIDENTIAL_QC_REPORT_ROOT is not set")
    report_root = Path(report_value)
    expectations = json.loads(
        (CODE_ROOT / "data" / "qc_expectations.json").read_text(encoding="utf-8")
    )

    def rule_counts(filename: str) -> dict[str, int]:
        with (report_root / filename).open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        counts: dict[str, int] = {}
        for row in rows:
            rule_id = row["rule_id"]
            counts[rule_id] = counts.get(rule_id, 0) + 1
        return counts

    assert rule_counts("cleaner_warnings.csv") == expectations["cleaner_warnings"]
    assert rule_counts("validate_xml.csv") == expectations["validate_xml"]
    assert rule_counts("validate_text.csv") == expectations["validate_text"]
    assert rule_counts("validate_glosses.csv") == expectations["validate_glosses"]

    with (report_root / "duplicate_sentences.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        duplicates = list(csv.DictReader(handle))
    expected_duplicate = expectations["duplicate_sentences"]
    assert len(duplicates) == expected_duplicate["rows"]
    assert {row["severity"] for row in duplicates} == {
        expected_duplicate["severity"]
    }
    assert {row["scope"] for row in duplicates} == {expected_duplicate["scope"]}
    assert {row["file"] for row in duplicates} == {expected_duplicate["file"]}
    assert sorted(row["s_id"] for row in duplicates) == expected_duplicate[
        "sentence_ids"
    ]


def test_no_legacy_generated_xml_layout() -> None:
    directory_names = {path.name for path in REPO_ROOT.iterdir() if path.is_dir()}
    assert "Final_XML" not in directory_names
    assert "xml" not in directory_names
    assert not list(REPO_ROOT.glob("*.xml"))

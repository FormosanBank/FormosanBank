from __future__ import annotations

import csv
import os
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from CodeAndDocs.main import generate_all, load_specs, read_sections
from CodeAndDocs.scripts.audit_source_alignment import (
    missing_word_boundaries,
    normalize_for_alignment,
    uncovered_text,
)
from CodeAndDocs.scripts.apply_standard_corrections import load_corrections
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


def test_published_ids_translations_and_unchanged_originals_are_preserved() -> None:
    baseline_root = public_xml_root()
    if baseline_root is None:
        pytest.skip("PRESIDENTIAL_PUBLIC_XML_ROOT is not set")
    allowed = {
        ("Saaroa", "0"), ("Truku", "25"), ("Amis", "20"), ("Atayal", "4"),
        ("Bunun", "18"), ("Tsou", "6"), ("Tsou", "20"), ("Tsou", "25"),
        ("Saaroa", "31"), ("Kanakanavu", "17"), ("Saisiyat", "20"),
        # Base reading = the one outside the parentheses (ruling 2026-10-16).
        ("Puyuma", "28"), ("Tsou", "2"), ("Tsou", "9"),
    }
    changed: set[tuple[str, str]] = set()
    for spec in load_specs():
        relative = Path(spec.language) / f"{spec.language}.xml"
        current = ET.parse(xml_root() / relative).getroot()
        baseline = ET.parse(baseline_root / relative).getroot()
        assert current.attrib == baseline.attrib
        current_sentences = current.findall("S")
        baseline_sentences = baseline.findall("S")
        assert [s.attrib for s in current_sentences] == [s.attrib for s in baseline_sentences]
        for actual, previous in zip(current_sentences, baseline_sentences, strict=True):
            assert [element_signature(t) for t in actual.findall("TRANSL")] == [
                element_signature(t) for t in previous.findall("TRANSL")
            ]
            current_form = actual.findtext('FORM[@kindOf="original"]')
            baseline_form = previous.findtext('FORM[@kindOf="original"]')
            if current_form != baseline_form:
                changed.add((spec.language, actual.attrib["id"]))
    assert changed == allowed


def test_source_corrections_are_explicit() -> None:
    with (CODE_ROOT / "data" / "source_corrections.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    manual = ET.parse(CODE_ROOT / "manual_edits.xml").getroot()
    recorded = {
        (Path(file.attrib["path"]).parts[0], s.attrib["id"])
        for file in manual.findall("FILE") for s in file.findall("S")
    }
    # Every correction is a manual_edits.xml record (maintainer ruling
    # 2026-10-16); the source transcripts themselves stay as transcribed.
    assert {(row["language"], row["section_id"]) for row in rows} == recorded - {
        ("Puyuma", "28"),
        ("Tsou", "2"),
        ("Tsou", "9"),
    }
    saaroa = read_sections(
        CODE_ROOT / "Apologies" / "Saaroa" / "Saaroa.txt", 33
    )[0]
    truku = read_sections(CODE_ROOT / "Apologies" / "Truku" / "Truku.txt", 33)[25]
    assert "mualiuhlʉ" in saaroa
    assert "tnpusu;,“" in truku


def test_standard_corrections_change_only_the_standard_tier() -> None:
    rows = load_corrections(CODE_ROOT / "data" / "standard_corrections.tsv")
    # Tsou x printed for ʉ: standard tier only (maintainer ruling 2026-10-16).
    assert len(rows) == 7
    root = ET.parse(xml_root() / "Tsou" / "Tsou.xml").getroot()
    for row in rows:
        sentence = root.find(f'S[@id="{row["section_id"]}"]')
        original = sentence.findtext('FORM[@kindOf="original"]')
        standard = sentence.findtext('FORM[@kindOf="standard"]')
        assert row["printed"] in original
        assert row["printed"] not in standard
        assert row["standard"] in standard
        # The corrected word no longer has an untranscribable letter.
        assert sentence.findtext('PHON[@kindOf="standard"]').count("*") < sentence.findtext(
            'PHON[@kindOf="original"]'
        ).count("*")


def test_source_manifest_inventory() -> None:
    with (CODE_ROOT / "data" / "source_manifest.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        manifest = list(csv.DictReader(handle))
    assert len(manifest) == 36
    assert len({row["path"] for row in manifest}) == 36
    assert sum(row["kind"] == "official_bilingual_pdf" for row in manifest) == 16


def test_external_alignment_report() -> None:
    report = os.environ.get("PRESIDENTIAL_ALIGNMENT_REPORT")
    if not report:
        pytest.skip("PRESIDENTIAL_ALIGNMENT_REPORT is not set")
    report_path = Path(report)
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


@pytest.mark.parametrize(
    ("block", "sections", "expected"),
    [
        ("missing opening retained words", ["retained words"], "missingopening"),
        ("first paragraph second paragraph", ["first paragraph", "second paragraph"], ""),
        ("middle of paragraph", ["the middle of paragraph continues"], ""),
    ],
)
def test_body_coverage_detects_truncated_sections(
    block: str, sections: list[str], expected: str
) -> None:
    assert uncovered_text(block, sections) == expected


@pytest.mark.parametrize(
    ("source", "pdf", "missing"),
    [
        ("comahadnosaka’orip,pirayray", "comahad no saka ’orip, pirayray", 4),
        ("no saka’orip", "no saka ’orip", 1),
        ("mualiuhlu", "mualiuhlu", 0),
        ("治 理", "治  理", 0),
        ("（masasulul）Sbalay", "（masasulul）Sbalay", 0),
    ],
)
def test_embedded_word_boundaries(source: str, pdf: str, missing: int) -> None:
    assert len(missing_word_boundaries(source, pdf)) == missing


def test_recorded_repairs_preserve_translations_and_survive_generation() -> None:
    records = ET.parse(CODE_ROOT / "manual_edits.xml").getroot()
    specs = {spec.language: spec for spec in load_specs()}
    # 9 source repairs, 3 corrections moved out of the .txt sources, and 3
    # parenthetical readings published as ver="alt" variants (2026-10-16).
    assert len(records.findall(".//S")) == 15
    for file in records.findall("FILE"):
        language = Path(file.attrib["path"]).parts[0]
        spec = specs[language]
        generated = ET.parse(xml_root() / file.attrib["path"]).getroot()
        chinese = read_sections(spec.chinese_file, spec.sections)
        english = read_sections(spec.english_file, spec.sections)
        for record in file.findall("S"):
            sid = record.attrib["id"]
            forms = record.findall("FORM")
            assert [item.get("kindOf") for item in forms] == ["original"] * len(forms)
            assert [item.get("ver") for item in forms] == [None] + ["alt"] * (len(forms) - 1)
            original = forms[0].text
            assert original
            assert not record.findall("PHON")
            generated_variants = [
                item.text for item in generated.findall(f'S[@id="{sid}"]/FORM[@kindOf="original"][@ver="alt"]')
            ]
            assert [normalize_for_alignment(t) for t in generated_variants] == [
                normalize_for_alignment(item.text) for item in forms[1:]
            ]
            assert {t.get(XML_LANG): t.text for t in record.findall("TRANSL")} == {
                "zho": chinese[int(sid)], "eng": english[int(sid)]
            }
            actual = generated.findtext(f'S[@id="{sid}"]/FORM[@kindOf="original"]')
            assert actual
            assert normalize_for_alignment(actual) == normalize_for_alignment(original)
            assert not missing_word_boundaries(actual, original)
    saaroa = ET.parse(xml_root() / "Saaroa" / "Saaroa.xml").getroot()
    assert saaroa.findtext('S[@id="31"]/FORM[@kindOf="original"]').startswith(
        "malitʉnʉlʉ patasuuru cucukokana umuhlipasamia"
    )


def test_no_legacy_generated_xml_layout() -> None:
    directory_names = {path.name for path in REPO_ROOT.iterdir() if path.is_dir()}
    assert "Final_XML" not in directory_names
    assert "xml" not in directory_names
    assert not list(REPO_ROOT.glob("*.xml"))

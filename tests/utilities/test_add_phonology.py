"""Tests for QC/utilities/add_phonology.py dialect/column resolution.

add_phonology.py adds <PHON> elements by transliterating <FORM> text via
Orthographies/Ortho113/<Language>.tsv. Which column it reads is chosen by
whether the language has multiple dialects (per dialects.csv):

  - single-dialect language (e.g. Yami): the dialect attribute is the
    language name by convention (dialect="Yami"), which is NOT a column in
    Yami.tsv (columns: letter, IPA). The script must ignore the dialect
    label and use the lone value column. This is the regression for the
    2026-06 bug where dialect="Yami" produced
    "Error: Dialect 'Yami' not found and no 'default' column in TSV".
  - multi-dialect language (e.g. Amis): the dialect attribute selects the
    column (Amis.tsv has per-dialect columns + default).

The script mutates XML in place, so each test builds a throwaway corpus
tree under tmp_path and never touches Corpora/. The orthography TSVs are
resolved relative to the repo, so cwd does not matter.
"""
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ADD_PHONOLOGY = (
    Path(__file__).resolve().parents[2] / "QC" / "utilities" / "add_phonology.py"
)


def _write_corpus(root: Path, language_dir: str, filename: str, xml_text: str) -> Path:
    """Place an XML at root/XML/<language_dir>/<filename> and return its path."""
    xml_path = root / "XML" / language_dir / filename
    xml_path.parent.mkdir(parents=True, exist_ok=True)
    xml_path.write_text(xml_text, encoding="utf-8")
    return xml_path


def _run(corpora_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(ADD_PHONOLOGY),
            "--corpora_path",
            str(corpora_path),
            "--orthography",
            "Ortho113",
        ],
        capture_output=True,
        text=True,
    )


def _phon_texts(xml_path: Path, kind: str) -> list[str]:
    root = ET.parse(xml_path).getroot()
    return [
        p.text
        for p in root.findall(".//PHON")
        if p.get("kindOf") == kind and p.text is not None
    ]


def test_single_dialect_label_resolves_to_lone_ipa_column(tmp_path):
    """Yami (single-dialect) with dialect="Yami" must use the lone IPA column.

    Before the fix the run printed "Error: Dialect 'Yami' not found and no
    'default' column" and added no PHON. After the fix it resolves to the IPA
    column, adds PHON, and the IPA reflects the Yami.tsv ng -> ŋ mapping.
    """
    corpus = tmp_path / "corpus"
    xml_path = _write_corpus(
        corpus,
        "Yami",
        "y.xml",
        '<TEXT xml:lang="tao" dialect="Yami">'
        '<S id="1">'
        '<FORM kindOf="original">ngaro</FORM>'
        '<FORM kindOf="standard">ngaro</FORM>'
        "</S></TEXT>",
    )
    proc = _run(corpus)
    combined = proc.stdout + proc.stderr
    assert "Error" not in combined, f"unexpected error: {combined!r}"
    # PHON must have been added (resolution succeeded; the file was not skipped).
    standard_phon = _phon_texts(xml_path, "standard")
    assert standard_phon, f"no standard PHON added; output was: {combined!r}"
    # ...and the IPA reflects the Yami.tsv mapping ng -> ŋ.
    assert any("ŋ" in p for p in standard_phon), (
        f"expected ng->ŋ in standard PHON, got {standard_phon!r}"
    )


def test_accepts_single_xml_corpora_path(tmp_path):
    xml_path = tmp_path / "y.xml"
    xml_path.write_text(
        '<TEXT xml:lang="tao" dialect="Yami">'
        '<S id="1">'
        '<FORM kindOf="original">ngaro</FORM>'
        '<FORM kindOf="standard">ngaro</FORM>'
        "</S></TEXT>",
        encoding="utf-8",
    )
    proc = _run(xml_path)
    combined = proc.stdout + proc.stderr
    assert "Error" not in combined, f"unexpected error: {combined!r}"
    assert _phon_texts(xml_path, "standard"), (
        f"no standard PHON added for direct XML path; output: {combined!r}"
    )


def test_multi_dialect_resolves_via_dialect_column(tmp_path):
    """Amis (multi-dialect) with dialect="Coastal" resolves the Coastal column.

    Sanity pin for the multi-dialect branch: a real dialect label that matches
    a TSV column must resolve and produce PHON without error.
    """
    corpus = tmp_path / "corpus"
    xml_path = _write_corpus(
        corpus,
        "Amis",
        "a.xml",
        '<TEXT xml:lang="ami" dialect="Coastal">'
        '<S id="1">'
        '<FORM kindOf="original">cecay</FORM>'
        '<FORM kindOf="standard">cecay</FORM>'
        "</S></TEXT>",
    )
    proc = _run(corpus)
    combined = proc.stdout + proc.stderr
    assert "Error" not in combined, f"unexpected error: {combined!r}"
    assert _phon_texts(xml_path, "standard"), (
        f"no standard PHON added for multi-dialect Amis; output: {combined!r}"
    )


def test_does_not_inject_whitespace_into_partial_UNCLEAR(tmp_path):
    corpus = tmp_path / "corpus"
    xml_path = _write_corpus(
        corpus,
        "Paiwan",
        "p.xml",
        '<TEXT xml:lang="pwn" dialect="Eastern"><S id="1">'
        '<FORM kindOf="original">sa izua<UNCLEAR/></FORM>'
        '<FORM kindOf="standard">sa izua<UNCLEAR/></FORM>'
        "</S></TEXT>",
    )
    proc = _run(corpus)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    proc = _run(corpus)
    assert proc.returncode == 0, f"second run stderr: {proc.stderr}"
    root = ET.parse(xml_path).getroot()
    assert ["".join(form.itertext()) for form in root.findall(".//FORM")] == [
        "sa izua",
        "sa izua",
    ]
    serialized = xml_path.read_text(encoding="utf-8")
    assert "\n    <S id=\"1\">" in serialized
    assert "\n        <FORM" in serialized
    assert serialized.count("sa izua<UNCLEAR/></FORM>") == 2

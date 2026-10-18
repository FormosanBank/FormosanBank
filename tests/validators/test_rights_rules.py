"""V160/V161: TEXT/@copyright must be a vocabulary value (POL-042).

Subprocess-invoked through validate_xml.py, the suite-wide convention, so
the test sees argv parsing and exit codes as shipped.
"""
import csv
from pathlib import Path

from tests._helpers import run_qc_script

SCRIPT = "QC/validation/validate_xml.py"


def _corpus(tmp_path: Path, attribute: str) -> Path:
    xml_dir = tmp_path / "XML"
    xml_dir.mkdir(parents=True, exist_ok=True)
    (xml_dir / "t.xml").write_text(
        f'<TEXT id="t1" citation="c" BibTeX_citation="b" {attribute} '
        f'xml:lang="ami"><S id="s1">'
        f'<FORM kindOf="original">tayal</FORM></S></TEXT>',
        encoding="utf-8",
    )
    return xml_dir


def _rules(tmp_path: Path, xml_dir: Path) -> set[str]:
    csv_path = tmp_path / "findings.csv"
    run_qc_script(SCRIPT, ["by_path", "--path", str(xml_dir),
                           "--csv", str(csv_path), "--no-exit-on-hard"])
    with open(csv_path, newline="", encoding="utf-8") as handle:
        return {row["rule_id"] for row in csv.DictReader(handle)}


def test_V160_fires_when_copyright_is_absent(tmp_path):
    assert "V160" in _rules(tmp_path, _corpus(tmp_path, ""))


def test_V160_fires_when_copyright_is_empty(tmp_path):
    assert "V160" in _rules(tmp_path, _corpus(tmp_path, 'copyright=""'))


def test_V161_fires_on_a_hyphenation_variant(tmp_path):
    rules = _rules(tmp_path, _corpus(tmp_path, 'copyright="CC-BY-NC"'))
    assert "V161" in rules


def test_V161_fires_on_the_transposed_typo(tmp_path):
    assert "V161" in _rules(tmp_path, _corpus(tmp_path, 'copyright="CC NC-BY"'))


def test_V161_fires_on_prose_that_mentions_a_licence(tmp_path):
    xml_dir = _corpus(tmp_path, 'copyright="CC BY-NC per the README"')
    assert "V161" in _rules(tmp_path, xml_dir)


def test_a_canonical_value_fires_neither_rule(tmp_path):
    rules = _rules(tmp_path, _corpus(tmp_path, 'copyright="CC BY-NC 4.0"'))
    assert "V160" not in rules and "V161" not in rules


def test_public_domain_fires_neither_rule(tmp_path):
    rules = _rules(tmp_path, _corpus(tmp_path, 'copyright="public domain"'))
    assert "V160" not in rules and "V161" not in rules


def test_a_hard_finding_exits_nonzero(tmp_path):
    xml_dir = _corpus(tmp_path, 'copyright="CC NC-BY"')
    proc = run_qc_script(SCRIPT, ["by_path", "--path", str(xml_dir)])
    assert proc.returncode == 1

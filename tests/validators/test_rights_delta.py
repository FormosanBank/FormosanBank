"""rights_delta: any licence change is a finding (POL-044).

There is no baseline file. A merge check already has both sides available,
and a stored baseline is redundant state that can itself drift.
"""
from pathlib import Path

from QC.validation.rights_delta import compare, licenses_at


def _tree(tmp_path: Path, name: str, corpora: dict) -> Path:
    root = tmp_path / name
    for corpus, value in corpora.items():
        xml_dir = root / corpus / "XML"
        xml_dir.mkdir(parents=True)
        (xml_dir / "t.xml").write_text(
            f'<TEXT id="t" copyright="{value}" xml:lang="ami"></TEXT>',
            encoding="utf-8",
        )
    return root


def test_licenses_at_reads_every_corpus(tmp_path):
    root = _tree(tmp_path, "base", {"A": "CC BY 4.0", "B": "public domain"})
    assert licenses_at(root) == {"A": "CC BY 4.0", "B": "public domain"}


def test_no_change_reports_nothing():
    assert compare({"A": "CC BY 4.0"}, {"A": "CC BY 4.0"}) == []


def test_a_changed_licence_is_reported():
    lines = compare({"A": "CC BY 4.0"}, {"A": "CC BY-NC-ND 4.0"})
    assert len(lines) == 1
    assert "A" in lines[0] and "CC BY 4.0" in lines[0] and "CC BY-NC-ND 4.0" in lines[0]


def test_a_removed_corpus_is_reported():
    lines = compare({"A": "CC BY 4.0"}, {})
    assert len(lines) == 1 and "removed" in lines[0].lower()


def test_an_added_corpus_is_reported():
    lines = compare({}, {"A": "CC BY 4.0"})
    assert len(lines) == 1 and "added" in lines[0].lower()

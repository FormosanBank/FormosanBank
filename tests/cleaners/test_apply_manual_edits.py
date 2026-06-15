"""Integration tests for QC/cleaning/apply_manual_edits.py.

apply runs first in the cleaning pipeline, on the pre-manual build output
(O). It applies upsert/insert/delete, prunes no-op entries (with a console
warning), and regenerates CodeAndDocs/manual_edits.md.
"""
import subprocess
import sys
from pathlib import Path

from lxml import etree

APPLY = Path(__file__).resolve().parents[2] / "QC" / "cleaning" / "apply_manual_edits.py"


def _doc(*sentences: str) -> str:
    body = "".join(sentences)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<TEXT id="T" xml:lang="ami">{body}</TEXT>\n'


def _sent(sid: str, original: str) -> str:
    return f'<S id="{sid}"><FORM kindOf="original">{original}</FORM></S>'


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run_apply(corpora_path: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(APPLY), "--corpora_path", str(corpora_path), *extra],
        capture_output=True, text=True,
    )


def _ids(xml_path: Path) -> list[str]:
    root = etree.parse(str(xml_path)).getroot()
    return [s.get("id") for s in root.findall(".//S")]


def _form(xml_path: Path, sid: str) -> str:
    root = etree.parse(str(xml_path)).getroot()
    s = root.find(f".//S[@id='{sid}']")
    return s.find("FORM[@kindOf='original']").text


def test_missing_manual_file_is_a_clean_noop(tmp_path):
    xml = tmp_path / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "x")))
    before = xml.read_bytes()
    proc = _run_apply(tmp_path / "XML")
    assert proc.returncode == 0
    assert "nothing to do" in proc.stdout.lower()
    assert xml.read_bytes() == before


def test_upsert_replaces_existing_sentence(tmp_path):
    xml = tmp_path / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "build")))
    man = tmp_path / "CodeAndDocs" / "manual_edits.xml"
    _write(man, '<MANUAL_EDITS><FILE path="a.xml">'
                '<S id="S1"><FORM kindOf="original">manual</FORM></S>'
                "</FILE></MANUAL_EDITS>")
    proc = _run_apply(tmp_path / "XML")
    assert proc.returncode == 0, proc.stderr
    assert _form(xml, "S1") == "manual"


def test_new_id_with_after_inserts_adjacent(tmp_path):
    xml = tmp_path / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "a"), _sent("S2", "c")))
    man = tmp_path / "CodeAndDocs" / "manual_edits.xml"
    _write(man, '<MANUAL_EDITS><FILE path="a.xml">'
                '<S id="S1b" after="S1"><FORM kindOf="original">b</FORM></S>'
                "</FILE></MANUAL_EDITS>")
    proc = _run_apply(tmp_path / "XML")
    assert proc.returncode == 0, proc.stderr
    assert _ids(xml) == ["S1", "S1b", "S2"]


def test_new_id_without_resolvable_anchor_appends(tmp_path):
    xml = tmp_path / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "a")))
    man = tmp_path / "CodeAndDocs" / "manual_edits.xml"
    _write(man, '<MANUAL_EDITS><FILE path="a.xml">'
                '<S id="SX" after="DOES_NOT_EXIST"><FORM kindOf="original">x</FORM></S>'
                "</FILE></MANUAL_EDITS>")
    proc = _run_apply(tmp_path / "XML")
    assert proc.returncode == 0, proc.stderr
    assert _ids(xml) == ["S1", "SX"]

"""declared_vs_detected.py: reading the declaration, and the two comparison tables.

The detectors themselves are tested in their own suites; here they are
injected, so the tables are checked for what they say about agreement,
mismatch, and the cases where no verdict is possible.
"""
from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "QC" / "validation" / "declared_vs_detected.py"
spec = importlib.util.spec_from_file_location("declared_vs_detected", SCRIPT)
dvd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dvd)


@pytest.mark.parametrize("script, expected", [
    ("python add_phonology.py --language Amis --orthography Ortho113", "Ortho113"),
    ('--orthography "$FB/Orthographies/Ortho94"', "Ortho94"),
    ("--orthography Orthographies/Ortho94 \\", "Ortho94"),
    ("--orthography Wakelin", "Wakelin"),
    ('standardize.py --tsv_path "$FB/Orthographies/ConversionTables/Amis_94_113.tsv"', "Ortho94"),
    ("--tsv_path Thao_Blust2003_113.tsv", "Blust2003"),
    ("--tsv_path Orthographies/ConversionTables/Rukai_Huteson_113.tsv", "Huteson"),
])
def test_declared_orthography_is_read_from_the_build_script(script, expected):
    name, how = dvd.declared_orthography_from_script(script)
    assert name == expected, how


def test_declared_orthography_reports_what_it_could_not_resolve():
    name, how = dvd.declared_orthography_from_script("standardize.py --tsv_path $TABLE")
    assert name is None and "$TABLE" in how and "--declared-orthography" in how
    name, how = dvd.declared_orthography_from_script("python build.py")
    assert name is None and "no --orthography or --tsv_path" in how


TEXT = ('<?xml version="1.0" encoding="UTF-8"?>\n<TEXT id="{tid}" citation="c" BibTeX_citation="b" '
        'copyright="CC BY-NC 4.0" xml:lang="{lang}"{dialect}><S id="S1"><FORM kindOf="original">x</FORM>'
        '<FORM kindOf="standard">x</FORM></S></TEXT>\n')


def _corpus(tmp_path: Path) -> Path:
    xml = tmp_path / "XML"
    (xml / "Amis").mkdir(parents=True)
    for i, dialect in enumerate(["Coastal", "Coastal", "Coastal", "Southern"]):
        (xml / "Amis" / f"a{i}.xml").write_text(
            TEXT.format(tid=f"a{i}", lang="ami", dialect=f' dialect="{dialect}"'), encoding="utf-8")
    (xml / "Amis" / "nodialect.xml").write_text(TEXT.format(tid="n", lang="ami", dialect=""), encoding="utf-8")
    (xml / "Thao").mkdir()
    (xml / "Thao" / "t.xml").write_text(TEXT.format(tid="t", lang="ssf", dialect=' dialect="Thao"'), encoding="utf-8")
    # a POL-035 snapshot under CodeAndDocs must not be counted
    snap = tmp_path / "CodeAndDocs" / "snapshot" / "XML" / "Amis"
    snap.mkdir(parents=True)
    (snap / "old.xml").write_text(TEXT.format(tid="old", lang="ami", dialect=' dialect="Coastal"'), encoding="utf-8")
    return xml


def test_dialect_table_marks_only_the_disagreeing_files(tmp_path):
    files = dvd.xml_files(_corpus(tmp_path))
    assert [f.name for f in files] == ["a0.xml", "a1.xml", "a2.xml", "a3.xml", "nodialect.xml", "t.xml"]
    verdicts = {"a0": "Coastal", "a1": "Southern", "a2": "unknown", "a3": "Southern", "n": "Coastal", "t": None}
    rows = dvd.dialect_rows(files, lambda root: verdicts[root.get("id")])
    assert rows == Counter({
        ("ami", "Coastal", "Coastal"): 1,
        ("ami", "Coastal", "Southern"): 1,
        ("ami", "Coastal", "unknown"): 1,
        ("ami", "Southern", "Southern"): 1,
        ("ami", "(missing)", "Coastal"): 1,
        ("ssf", "Thao", "(no verdict)"): 1,
    })
    table = dvd.format_dialect_table(rows)
    mismatch_lines = [l for l in table.splitlines() if "MISMATCH" in l]
    assert len(mismatch_lines) == 2, table          # Coastal→Southern and (missing)→Coastal
    assert "Coastal         Southern             1  MISMATCH" in table
    assert "unknown              1  detector below its threshold" in table
    assert "(no verdict)         1  no model / no standard tier" in table
    assert table.endswith("dialect mismatches: 2 file(s)")


def _combined(best: str, score: float = 0.97, unexpected: float = 0.4) -> dict:
    ranked = [{"orthography": best, "score": score, "unexpected_percentage": unexpected},
              {"orthography": "Church", "score": 0.80, "unexpected_percentage": 3.0}]
    return {"Coastal": {"best_match": ranked[0], "orthography_analysis": ranked, "file_count": 4},
            "error_info": {"error_files": ["x.xml"], "error_count": 1}}


def test_orthography_table_agrees_when_the_pipeline_declares_what_is_detected():
    rows = dvd.orthography_rows(_combined("Ortho94"), "Ortho94")
    table = dvd.format_orthography_table(rows, "original", "declared source orthography")
    assert "Coastal              4  Ortho94     Ortho94       0.97         0.4  agree  (next: Church 0.80)" in table
    assert table.endswith("orthography mismatches (original): 0 group(s)")


def test_orthography_table_flags_a_mismatch_and_an_unresolved_declaration():
    rows = dvd.orthography_rows(_combined("Church", score=0.91), "Ortho94")
    table = dvd.format_orthography_table(rows, "original", "declared source orthography")
    assert "Ortho94     Church        0.91         0.4  MISMATCH" in table
    assert table.endswith("orthography mismatches (original): 1 group(s)")
    rows = dvd.orthography_rows(_combined("Ortho113"), None)
    table = dvd.format_orthography_table(rows, "original", "declared source orthography")
    assert "(unresolved)Ortho113" in table.replace("  ", "") and "declaration unresolved" in table


def test_cli_runs_the_real_detectors_on_a_small_corpus_and_exits_zero(tmp_path, capsys):
    """Smoke only: the verdicts on a one-sentence corpus are not asserted."""
    xml = _corpus(tmp_path)
    build = tmp_path / "generate_xml.sh"
    build.write_text("python QC/utilities/add_phonology.py --language Amis --orthography Ortho113\n")
    assert dvd.main(["--xml", str(xml), "--generate-xml", str(build)]) == 0
    out = capsys.readouterr().out
    assert "declared source orthography: Ortho113  [--orthography Ortho113]" in out
    assert "== Dialect: declared" in out and "dialect mismatches:" in out
    assert "== Orthography, original tier" in out and "== Orthography, standard tier" in out

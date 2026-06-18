"""Tests for QC/validation/validate_dialect.py.

The script is informative (it summarizes TEXT/@dialect values; it doesn't
enforce anything — V036 does that). Two small tests:
  1. End-to-end: a directory with mixed (xml:lang, dialect) values produces
     a table with the expected counts.
  2. Error path: a non-existent --path exits 1.
"""
import subprocess
import sys
from pathlib import Path

VALIDATE_DIALECT = (
    Path(__file__).resolve().parents[2]
    / "QC" / "validation" / "validate_dialect.py"
)


def _run(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATE_DIALECT), "--path", str(path)],
        capture_output=True,
        text=True,
    )


def _write_xml(path: Path, xml_lang: str | None, dialect: str | None) -> None:
    lang_attr = f' xml:lang="{xml_lang}"' if xml_lang is not None else ""
    dialect_attr = f' dialect="{dialect}"' if dialect is not None else ""
    path.write_text(
        f'<?xml version="1.0" encoding="utf-8"?>\n'
        f'<TEXT id="t" citation="c" BibTeX_citation="@b{{b}}" copyright="r"'
        f"{lang_attr}{dialect_attr}>\n"
        f'  <S id="s1"><FORM kindOf="original">x</FORM></S>\n'
        f"</TEXT>\n",
        encoding="utf-8",
    )


def test_counts_match_input(tmp_path):
    """A mixed-dialect directory yields a (xml:lang, dialect) -> count table."""
    _write_xml(tmp_path / "a.xml", "ami", "Coastal")
    _write_xml(tmp_path / "b.xml", "ami", "Coastal")
    _write_xml(tmp_path / "c.xml", "ami", "unknown")
    _write_xml(tmp_path / "d.xml", "tsu", "Tsou")
    _write_xml(tmp_path / "e.xml", "tsu", None)  # missing dialect

    proc = _run(tmp_path)
    assert proc.returncode == 0, (
        f"validate_dialect exited {proc.returncode}; stderr={proc.stderr!r}"
    )
    out = proc.stdout

    # Each line is "lang  dialect  count" with variable spacing; match
    # token-by-token rather than asserting exact whitespace.
    def row_count(lang: str, dialect: str) -> int:
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[0] == lang and parts[1] == dialect:
                return int(parts[-1])
        raise AssertionError(
            f"no row for lang={lang!r} dialect={dialect!r} in output:\n{out}"
        )

    assert row_count("ami", "Coastal") == 2
    assert row_count("ami", "unknown") == 1
    assert row_count("tsu", "Tsou") == 1
    assert row_count("tsu", "(missing)") == 1


def test_nonexistent_path_exits_1(tmp_path):
    """--path that doesn't exist returns 1 with an error on stderr."""
    proc = _run(tmp_path / "no_such_dir")
    assert proc.returncode == 1, (
        f"expected exit 1 for missing path, got {proc.returncode}; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    assert "does not exist" in proc.stderr.lower()

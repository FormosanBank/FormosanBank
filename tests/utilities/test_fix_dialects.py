from pathlib import Path

from lxml import etree

from QC.utilities.fix_dialects import fix_file


XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def _write_text(path: Path, *, language: str, dialect: str | None) -> None:
    dialect_attr = f' dialect="{dialect}"' if dialect is not None else ""
    path.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<TEXT id="T" xml:lang="{language}"{dialect_attr}></TEXT>\n',
        encoding="utf-8",
    )


def test_normalizes_documented_paiwan_alias_without_reserializing(tmp_path):
    path = tmp_path / "paiwan.xml"
    _write_text(path, language="pwn", dialect="North Western")

    status, value = fix_file(path)

    assert (status, value) == ("normalized", "Northern")
    assert b'dialect="Northern"' in path.read_bytes()
    assert etree.parse(str(path)).getroot().get("dialect") == "Northern"


def test_preserves_canonical_dialect(tmp_path):
    path = tmp_path / "paiwan.xml"
    _write_text(path, language="pwn", dialect="Southern")
    before = path.read_bytes()

    assert fix_file(path) == ("kept", None)
    assert path.read_bytes() == before


def test_sets_missing_single_language_dialect(tmp_path):
    path = tmp_path / "tsou.xml"
    _write_text(path, language="tsu", dialect=None)

    assert fix_file(path) == ("set", "Tsou")
    root = etree.parse(str(path)).getroot()
    assert root.get(XML_LANG) == "tsu"
    assert root.get("dialect") == "Tsou"

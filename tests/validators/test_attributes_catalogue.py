"""QC/validation/ATTRIBUTES.md must match the XSD that actually validates.

Same contract as test_rules_catalogue.py: the documented attribute set is
generated, so it cannot drift from the schema. POL-053 requires an
attribute to be declared, annotated, catalogued and given a policy entry;
this test enforces the first three.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "QC/validation/attributes_catalogue.py"
CATALOGUE = REPO_ROOT / "QC/validation/ATTRIBUTES.md"

sys.path.insert(0, str(REPO_ROOT))

_SECTION_HEADING = re.compile(r"^## `<(\w+)>`$")


def _sections(text: str) -> dict[str, str]:
    """element -> the text of its '## <ELEMENT>' section (its table)."""
    sections: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in text.splitlines():
        match = _SECTION_HEADING.match(line)
        if match:
            if current is not None:
                sections[current] = "\n".join(buf)
            current = match.group(1)
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf)
    return sections


def test_catalogue_is_current():
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        f"{CATALOGUE.name} is stale — run "
        f"`python QC/validation/attributes_catalogue.py`.\n"
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_every_attribute_is_documented():
    from QC.validation.attributes_catalogue import collect

    missing = [
        f"{element}/@{attribute}"
        for element, attribute, _use, _values, doc in collect()
        if not doc.strip()
    ]
    assert not missing, f"attributes with no xs:documentation: {missing}"


def test_catalogue_names_every_attribute():
    """Every (element, attribute) pair has a row under its *own* section.

    Several attribute names (id, source, class, sclass, kindOf) recur
    across multiple elements. A bare substring search for an attribute's
    table-row marker anywhere in the file would pass even if that
    element's own row were dropped or corrupted, as long as some other
    element's same-named row survived — so this scopes the check to the
    matching '## <ELEMENT>' section, mirroring how test_rules_catalogue.py
    pairs rule_id with mnemonic to make the key effectively unique.
    """
    from QC.validation.attributes_catalogue import collect

    sections = _sections(CATALOGUE.read_text(encoding="utf-8"))
    for element, attribute, _use, _values, _doc in collect():
        assert element in sections, (
            f"no '## <{element}>' section in {CATALOGUE.name}"
        )
        assert f"| `{attribute}` |" in sections[element], (
            f"{element}/@{attribute} row is missing from its own "
            f"'## <{element}>' section in {CATALOGUE.name}"
        )


def test_enumerated_values_are_surfaced():
    from QC.validation.attributes_catalogue import collect

    rows = {(e, a): v for e, a, _u, v, _d in collect()}
    assert rows[("FORM", "kindOf")] == "original | standard | alternate"
    assert rows[("TRANSL", "kindOf")] == "original | standard"
    assert rows[("PHON", "kindOf")] == "original | standard"


def test_required_attributes_are_marked():
    from QC.validation.attributes_catalogue import collect

    rows = {(e, a): u for e, a, u, _v, _d in collect()}
    assert rows[("TEXT", "id")] == "required"
    assert rows[("FORM", "kindOf")] == "required"
    assert rows[("TEXT", "source")] == "optional"


def test_inline_anonymous_enum_is_surfaced(tmp_path, monkeypatch):
    """An attribute whose enumeration is an inline <xs:simpleType> child

    (rather than a `type="Named_Type"` reference to a separately declared
    simpleType) must still surface its allowed values. `_enumerations()`
    only indexes *named* simpleTypes, so this exercises the `_inline_enum`
    fallback in `collect()` against a real (if minimal) schema — the shape
    the XSD legally permits and that the reviewer flagged as untested.
    """
    from QC.validation import attributes_catalogue as ac

    schema = tmp_path / "mini.xsd"
    schema.write_text(
        '<?xml version="1.0"?>\n'
        '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">\n'
        '  <xs:complexType name="ZZZ_Type">\n'
        '    <xs:attribute name="mode">\n'
        '      <xs:annotation><xs:documentation>inline enum test'
        "</xs:documentation></xs:annotation>\n"
        "      <xs:simpleType>\n"
        '        <xs:restriction base="xs:string">\n'
        '          <xs:enumeration value="a"/>\n'
        '          <xs:enumeration value="b"/>\n'
        "        </xs:restriction>\n"
        "      </xs:simpleType>\n"
        "    </xs:attribute>\n"
        "  </xs:complexType>\n"
        "</xs:schema>\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(ac, "SCHEMA", schema)

    rows = ac.collect()

    assert rows == [("ZZZ", "mode", "optional", "a | b", "inline enum test")]


def test_every_row_has_same_delimiter_count_as_header():
    """No table row may carry more unescaped '|' than its header.

    GFM tables split on unescaped `|`; backticks do not protect one, so
    a literal `|` in any cell — not just documentation, but also an
    "Allowed values" cell built from an enum like `original | standard`
    — must be escaped as `\\|` or it reads as extra column delimiters
    and misaligns or spills the row. This checks every generated data
    row against its section header's delimiter count, so it catches any
    future column-splitting content, not just the enum case.
    """
    text = CATALOGUE.read_text(encoding="utf-8")
    header_delimiters = None
    for line in text.splitlines():
        if line.startswith("| ---"):
            header_delimiters = line.count("|")
            continue
        if line.startswith("| `") and header_delimiters is not None:
            row_delimiters = line.count("|") - line.count("\\|")
            assert row_delimiters == header_delimiters, (
                f"row has {row_delimiters} unescaped '|' delimiters, "
                f"expected {header_delimiters}: {line}"
            )


def test_pipe_in_documentation_does_not_break_table_row(monkeypatch):
    """A literal '|' in an xs:documentation string must not corrupt the

    table: `render()` builds rows as
    `| attribute | use | values | documentation |`, so an unescaped pipe
    inside the documentation column would be read as an extra column
    delimiter and misalign or split the row. No current attribute's
    documentation contains one (nothing here fires against the real
    schema), so this synthesizes a row via a monkeypatched `collect()` to
    pin the escaping behavior the reviewer flagged as untested.
    """
    from QC.validation import attributes_catalogue as ac

    fake_row = ("TEXT", "zzz", "optional", "", "has a | pipe | in it")
    monkeypatch.setattr(ac, "collect", lambda: [fake_row])

    rendered = ac.render()

    lines = [line for line in rendered.splitlines() if line.startswith("| `zzz`")]
    assert len(lines) == 1, rendered
    row = lines[0]
    # Exactly 4 columns -> 5 unescaped '|' delimiters. The 2 literal pipes
    # in the documentation must be escaped, not counted as delimiters.
    assert row.count("|") - row.count("\\|") == 5, row
    assert "has a \\| pipe \\| in it" in row

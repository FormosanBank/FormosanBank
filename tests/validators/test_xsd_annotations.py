"""POL-053: every attribute in the XSD carries documentation.

The XSD declares no anyAttribute, so it is already a closed whitelist —
an undeclared attribute fails validate_xml. This test makes the other half
true: the closed set is also a *documented* set, so an attribute cannot be
added without saying what it means.
"""
from __future__ import annotations

from pathlib import Path

from lxml import etree

XSD = Path(__file__).resolve().parents[2] / "QC/validation/xml_template.xsd"
XS = "{http://www.w3.org/2001/XMLSchema}"


def _attributes():
    tree = etree.parse(str(XSD))
    return list(tree.iter(f"{XS}attribute"))


def test_every_attribute_has_documentation():
    undocumented = []
    for attr in _attributes():
        name = attr.get("name") or attr.get("ref")
        doc = attr.find(f"{XS}annotation/{XS}documentation")
        if doc is None or not (doc.text or "").strip():
            undocumented.append(name)
    assert not undocumented, (
        "POL-053: these XSD attributes have no xs:documentation: "
        f"{undocumented}"
    )


def test_transl_kindof_is_enumerated():
    tree = etree.parse(str(XSD))
    simple = [
        t for t in tree.iter(f"{XS}simpleType")
        if t.get("name") == "TRANSL_kindOf_Type"
    ]
    assert simple, "TRANSL_kindOf_Type is not defined"
    values = {
        e.get("value")
        for e in simple[0].iter(f"{XS}enumeration")
    }
    assert values == {"original", "standard"}


def test_schema_still_compiles():
    etree.XMLSchema(etree.parse(str(XSD)))


def test_schema_still_accepts_a_representative_document():
    from io import BytesIO

    schema = etree.XMLSchema(etree.parse(str(XSD)))
    doc = etree.parse(BytesIO(
        b'<?xml version="1.0" encoding="utf-8"?>'
        b'<TEXT id="T1" citation="t" BibTeX_citation="@t{t}" copyright="t" '
        b'xml:lang="pwn" source="s" dialect="d">'
        b'<S id="S1">'
        b'<FORM kindOf="original" notes="n">so</FORM>'
        b'<FORM kindOf="alternate">soa</FORM>'
        b'<PHON kindOf="original">so</PHON>'
        b'<TRANSL xml:lang="eng" ver="alt">two</TRANSL>'
        b'<W id="S1W1" class="num" sclass="card">'
        b'<FORM kindOf="original">so</FORM>'
        b'<TRANSL xml:lang="eng" kindOf="original">two</TRANSL>'
        b'</W>'
        b'</S></TEXT>'
    ))
    schema.assertValid(doc)


def test_schema_declares_no_any_attribute():
    """POL-053's whitelist claim rests on there being no xs:anyAttribute
    escape hatch anywhere in the schema, not just on FORM (the one element
    test_schema_rejects_an_undeclared_attribute probes). Checked repo-wide
    so the guarantee POL-053, attributes_catalogue.py's docstring,
    ATTRIBUTES.md's preamble, and the GitBook page all assert is actually
    tested, not just assumed."""
    tree = etree.parse(str(XSD))
    any_attrs = list(tree.iter(f"{XS}anyAttribute"))
    assert not any_attrs, (
        "POL-053: the schema must declare no xs:anyAttribute anywhere, "
        f"found {len(any_attrs)}"
    )


def test_schema_rejects_an_undeclared_attribute():
    """The whitelist half of POL-053, asserted rather than assumed."""
    from io import BytesIO

    schema = etree.XMLSchema(etree.parse(str(XSD)))
    doc = etree.parse(BytesIO(
        b'<?xml version="1.0" encoding="utf-8"?>'
        b'<TEXT id="T1" citation="t" BibTeX_citation="@t{t}" copyright="t" '
        b'xml:lang="pwn">'
        b'<S id="S1"><FORM kindOf="original" mood="jussive">so</FORM></S>'
        b'</TEXT>'
    ))
    assert not schema.validate(doc)


def test_schema_rejects_a_bad_transl_kindof():
    from io import BytesIO

    schema = etree.XMLSchema(etree.parse(str(XSD)))
    doc = etree.parse(BytesIO(
        b'<?xml version="1.0" encoding="utf-8"?>'
        b'<TEXT id="T1" citation="t" BibTeX_citation="@t{t}" copyright="t" '
        b'xml:lang="pwn">'
        b'<S id="S1"><FORM kindOf="original">so</FORM>'
        b'<TRANSL xml:lang="eng" kindOf="provenance">two</TRANSL></S>'
        b'</TEXT>'
    ))
    assert not schema.validate(doc)

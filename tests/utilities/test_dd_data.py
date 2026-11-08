from pathlib import Path
from QC.utilities.dialect_detector.data import iter_labeled_documents, extract_standard_text
import xml.etree.ElementTree as ET

def _xml(lang, dialect, *std):
    forms = "".join(f'<S id="{i}"><FORM kindOf="standard">{t}</FORM></S>'
                    for i, t in enumerate(std))
    d = f' dialect="{dialect}"' if dialect is not None else ""
    return f'<TEXT xml:lang="{lang}"{d}>{forms}</TEXT>'

def _write(root: Path, rel: str, content: str):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

def test_iterates_labeled_standard_text_and_skips_unknown_empty(tmp_path):
    _write(tmp_path, "XML/a.xml", _xml("ami", "Coastal", "fafa", "tata"))
    _write(tmp_path, "XML/b.xml", _xml("ami", "unknown", "zzzz"))   # skipped
    _write(tmp_path, "XML/c.xml", _xml("ami", None, "qqqq"))        # skipped (no dialect)
    _write(tmp_path, "XML/d.xml", _xml("pwn", "Northern", "lala"))  # wrong lang
    docs, dropped = iter_labeled_documents(tmp_path, "ami")
    assert [d.dialect for d in docs] == ["Coastal"]
    assert docs[0].text == "fafa tata"
    assert dropped == []

def test_unmappable_label_is_reported_not_silently_dropped(tmp_path):
    _write(tmp_path, "XML/x.xml", _xml("pyu", "Bogus", "aaaa"))
    docs, dropped = iter_labeled_documents(tmp_path, "pyu")
    assert docs == []
    assert dropped and dropped[0].dialect == "Bogus"

def test_extract_standard_text_only_standard_tier():
    root = ET.fromstring(
        '<TEXT xml:lang="ami" dialect="Coastal">'
        '<S id="1"><FORM kindOf="original">ORIG</FORM>'
        '<FORM kindOf="standard">STD</FORM></S></TEXT>'
    )
    assert extract_standard_text(root) == "STD"


def test_extract_standard_text_uses_bases_only(tmp_path):
    """POL-028: a ver="alt" variant is a second reading of the SAME sentence.
    Folding it into the dialect-classifier's text counts one sentence twice
    and mixes a secondary reading into the features."""
    root = ET.fromstring(
        '<TEXT xml:lang="ami" dialect="Coastal">'
        '<S id="1">'
        '<FORM kindOf="standard">fafahiyan</FORM>'
        '<FORM kindOf="standard" ver="alt">fafahian</FORM>'
        "</S></TEXT>"
    )
    assert extract_standard_text(root) == "fafahiyan"


def test_extract_standard_text_ignores_a_variant_only_sentence(tmp_path):
    root = ET.fromstring(
        '<TEXT xml:lang="ami" dialect="Coastal">'
        '<S id="1"><FORM kindOf="standard" ver="alt">fafahian</FORM></S>'
        "</TEXT>"
    )
    assert extract_standard_text(root) == ""

def test_codeanddocs_snapshot_is_not_a_training_document(tmp_path):
    _write(tmp_path, "C/XML/a.xml", _xml("ami", "Coastal", "fafa"))
    _write(tmp_path, "C/CodeAndDocs/pre_correction_snapshot/XML/a.xml",
           _xml("ami", "Coastal", "fafa"))
    docs, _ = iter_labeled_documents(tmp_path, "ami")
    assert [str(d.path.relative_to(tmp_path)) for d in docs] == ["C/XML/a.xml"]

def test_a_root_inside_codeanddocs_is_still_read(tmp_path):
    # builds that stage into CodeAndDocs/ and point the tool there must still work
    stage = tmp_path / "C" / "CodeAndDocs" / "Final_XML"
    _write(stage, "a.xml", _xml("ami", "Coastal", "fafa"))
    docs, _ = iter_labeled_documents(stage, "ami")
    assert len(docs) == 1

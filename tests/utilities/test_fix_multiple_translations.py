from lxml import etree

from QC.utilities.fix_multiple_translations import fix_file


XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def test_marks_non_primary_same_language_translations_as_alternates(tmp_path):
    path = tmp_path / "dictionary.xml"
    path.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<TEXT id="T" xml:lang="ami"><S id="S1">'
        '<FORM kindOf="original">sowal</FORM>'
        '<TRANSL xml:lang="eng">word</TRANSL>'
        '<TRANSL xml:lang="eng">speech</TRANSL>'
        '<TRANSL xml:lang="zho">詞</TRANSL>'
        '<TRANSL xml:lang="zho">話</TRANSL>'
        '</S></TEXT>\n',
        encoding="utf-8",
    )

    status, added, kept = fix_file(path)

    assert (status, added, kept) == ("changed", 2, 0)
    translations = etree.parse(str(path)).findall(".//TRANSL")
    assert [
        (
            transl.get(XML_LANG),
            transl.get("ver"),
        )
        for transl in translations
    ] == [
        ("eng", None),
        ("eng", "alt"),
        ("zho", None),
        ("zho", "alt"),
    ]
    assert fix_file(path) == ("unchanged", 0, 2)

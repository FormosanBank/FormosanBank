"""Regression expectations from the scans and retained CUV/KJV editions."""

from pathlib import Path

import pytest
from lxml import etree

from reference_translations import read_cuv, read_kjv

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def sentence(book, chapter, verse, *, baseline=False):
    root = HERE / "baseline" if baseline else ROOT / "XML"
    tree = etree.parse(str(root / f"Siraya/{book}/chapter{chapter}.xml"))
    return tree.find(f".//S[@id='verse{verse}']")


def translations(node, language):
    return [t for t in node.findall("TRANSL") if t.get(XML_LANG) == language]


def test_cuv_continuations_and_apparatus(tmp_path):
    source = tmp_path / "sample.usfm"
    source.write_text(
        "\\c 1\n\\v 1 開頭。\n\\q1 詩行。\n\\p 段落。\n\\m 續行。\n"
        "\\s1 新段\n\\r （路2‧1）\n\\p\n"
        "\\v 2 \\+pn 人名\\+pn*\\f - \\fr 1:2 \\ft 或譯：別名\\f*。\n",
        encoding="utf-8",
    )
    result = read_cuv(source)
    assert result[1, 1] == ("開頭。 詩行。 段落。 續行。", "")
    assert result[1, 2] == ("人名。", "Parallel passages: （路2‧1） / 或譯：別名")


@pytest.mark.parametrize("broken", ["\\q2 unhandled", "unmarked source text"])
def test_unparsed_source_does_not_silently_disappear(tmp_path, broken):
    source = tmp_path / "sample.usfm"
    source.write_text("\\c 1\n\\v 1 原文。\n" + broken + "\n")
    with pytest.raises(ValueError):
        read_cuv(source)


def test_real_cuv_poetry_and_four_prose_continuations():
    sources = HERE / "reference_translations/cmn-cu89t_usfm"
    matthew = read_cuv(sources / "70-MATcmn-cu89t.usfm")
    john = read_cuv(sources / "73-JHNcmn-cu89t.usfm")
    assert matthew[5, 3][0] == "虛心的人有福了！ 因為天國是他們的。"
    assert "大衛從烏利亞的妻子生所羅門" in matthew[1, 6][0]
    assert "耶穌說了這話，就離開他們隱藏了。" in john[12, 36][0]
    assert "我起先沒有將這事告訴你們，因為我與你們同在。" in john[16, 4][0]
    assert "我查不出他有甚麼罪來。" in john[18, 38][0]
    assert "兵丁果然做了這事。" in john[19, 24][0]
    assert (18, 11) not in matthew
    assert "人子來，為要拯救失喪的人" in matthew[18, 10][1]


def test_printed_john_split_keeps_the_complete_reference_once():
    left, right = sentence("John", 1, 38), sentence("John", 1, 39)
    kjv = read_kjv(HERE / "reference_translations/eng-kjv-nltk-gutenberg.tsv")
    english = [translations(s, "eng")[0].text for s in (left, right)]
    assert english[0].endswith("and saith unto them,")
    assert english[1].startswith("What seek ye?")
    assert " ".join(english) == kjv["John", 1, 38]
    chinese = [translations(s, "zho")[0].text for s in (left, right)]
    assert chinese[0] == "耶穌轉過身來，看見他們跟着，就問他們說："
    assert "你們要甚麼？" in chinese[1]


def test_prior_corrections_and_original_identity_survive():
    changed = set()
    for source in (HERE / "baseline").rglob("*.xml"):
        relative = source.relative_to(HERE / "baseline")
        old = etree.parse(str(source)).getroot()
        new = etree.parse(str(ROOT / "XML" / relative)).getroot()
        assert old.attrib == new.attrib
        assert [s.get("id") for s in old] == [s.get("id") for s in new]
        for before, after in zip(old, new):
            if before.find("FORM[@kindOf='original']").text != after.find("FORM[@kindOf='original']").text:
                changed.add((str(relative), before.get("id")))
    assert changed == {
        ('Siraya/John/chapter7.xml', 'verse39'),
        ('Siraya/Matthew/chapter26.xml', 'verse11'),
        ('Siraya/John/chapter5.xml', 'verse11'),
        ('Siraya/John/chapter8.xml', 'verse44'),
        ('Siraya/John/chapter20.xml', 'verse7'),
        ('Siraya/John/chapter11.xml', 'verse18'),
        ('Siraya/John/chapter12.xml', 'verse12'),
        ('Siraya/John/chapter18.xml', 'verse23'),
        ('Siraya/John/chapter5.xml', 'verse18'),
        ('Siraya/John/chapter5.xml', 'verse23'),
        ('Siraya/John/chapter5.xml', 'verse28'),
        ('Siraya/John/chapter5.xml', 'verse42'),
        ('Siraya/John/chapter6.xml', 'verse20'),
        ('Siraya/John/chapter6.xml', 'verse27'),
        ('Siraya/John/chapter7.xml', 'verse3'),
        ('Siraya/Matthew/chapter10.xml', 'verse42'),
        ('Siraya/Matthew/chapter12.xml', 'verse50'),
        ('Siraya/Matthew/chapter13.xml', 'verse58'),
        ('Siraya/Matthew/chapter14.xml', 'verse36'),
        ('Siraya/Matthew/chapter15.xml', 'verse39'),
        ('Siraya/Matthew/chapter16.xml', 'verse10'),
        ('Siraya/Matthew/chapter16.xml', 'verse28'),
        ('Siraya/Matthew/chapter17.xml', 'verse27'),
        ('Siraya/Matthew/chapter18.xml', 'verse28'),
        ('Siraya/Matthew/chapter18.xml', 'verse35'),
        ('Siraya/Matthew/chapter19.xml', 'verse30'),
        ('Siraya/Matthew/chapter2.xml', 'verse23'),
        ('Siraya/Matthew/chapter20.xml', 'verse34'),
        ('Siraya/Matthew/chapter21.xml', 'verse46'),
        ('Siraya/Matthew/chapter22.xml', 'verse2'),
        ('Siraya/Matthew/chapter22.xml', 'verse46'),
        ('Siraya/Matthew/chapter23.xml', 'verse14'),
        ('Siraya/Matthew/chapter23.xml', 'verse39'),
        ('Siraya/Matthew/chapter24.xml', 'verse19'),
        ('Siraya/Matthew/chapter24.xml', 'verse2'),
        ('Siraya/Matthew/chapter24.xml', 'verse51'),
        ('Siraya/Matthew/chapter25.xml', 'verse46'),
        ('Siraya/Matthew/chapter26.xml', 'verse71'),
        ('Siraya/Matthew/chapter26.xml', 'verse75'),
        ('Siraya/Matthew/chapter27.xml', 'verse53'),
        ('Siraya/Matthew/chapter27.xml', 'verse66'),
        ('Siraya/Matthew/chapter3.xml', 'verse17'),
        ('Siraya/Matthew/chapter4.xml', 'verse25'),
        ('Siraya/Matthew/chapter5.xml', 'verse48'),
        ('Siraya/Matthew/chapter6.xml', 'verse34'),
        ('Siraya/Matthew/chapter7.xml', 'verse29'),
        ('Siraya/Matthew/chapter8.xml', 'verse34'),
        ('Siraya/Matthew/chapter8.xml', 'verse4'),
        ('Siraya/Matthew/chapter9.xml', 'verse38'),
    }
    for tier in ("original", "standard"):
        opening = sentence("John", 1, 1).find(f"FORM[@kindOf='{tier}']").text
        assert "ki Alid" in opening and "æ'ïa-qua" in opening
        assert ("a-koumea" if tier == "original" else "akoumea") in opening
        rare = sentence("Matthew", 25, 11).find(f"FORM[@kindOf='{tier}']").text
        assert "kæuh-jnæ̈jna" in rare


def test_dutch_copies_removed_only_from_the_wrong_chapter():
    for verse in range(2, 28):
        assert len(translations(sentence("Matthew", 17, verse), "nld")) == 1
        retained = translations(sentence("Matthew", 18, verse), "nld")
        baseline = translations(sentence("Matthew", 18, verse, baseline=True), "nld")
        assert [t.text for t in retained] == [t.text for t in baseline]
    assert len(translations(sentence("John", 13, 16), "nld")) == 1
    relocated = translations(sentence("John", 13, 18), "nld")
    assert len(relocated) == 1 and relocated[0].get("ver") is None
    assert relocated[0].text.startswith("Ick en segghe niet ban u allen")
    assert len(translations(sentence("Matthew", 18, 1), "nld")) == 1
    assert "E dier selber uyre" not in translations(sentence("Matthew", 17, 27), "nld")[0].text


def test_scan_repairs_keep_verse_content_and_printed_punctuation():
    def original(book, chapter, verse):
        return sentence(book, chapter, verse).find("FORM[@kindOf='original']").text

    assert original("John", 7, 39).startswith(".. (")
    assert "ta atta" in original("John", 7, 39)
    assert "·" not in original("John", 7, 39)
    assert "ææ̈pag" in original("John", 5, 11)
    assert "äou-si" in original("John", 8, 44)
    assert "-lbæh" in original("John", 20, 7)
    assert original("Matthew", 26, 11).startswith("Ka ")
    assert "pæ-pæh" in original("John", 5, 18)
    assert "Rama ka" in original("John", 5, 23)
    assert "satkyttiæn" in original("John", 11, 18)
    assert "ni-k'mæ-'msing-koh" in original("John", 18, 23)
    assert "tæ'iä-papara" in original("John", 7, 3)
    assert original("Matthew", 15, 39).endswith("Magda-la.")
    assert "(sasasat ka) vahto" in original("Matthew", 24, 2)
    # These two imbalances are visible in the printed source itself.
    for verse in (28, 33):
        assert original("John", 12, verse) == sentence(
            "John", 12, verse, baseline=True
        ).find("FORM[@kindOf='original']").text


def test_reference_coverage_matches_every_printed_verse():
    paths = list((ROOT / "XML").rglob("*.xml"))
    counts = {"John": 0, "Matthew": 0}
    missing_chinese = set()
    for path in paths:
        chapter = int(path.stem.removeprefix("chapter"))
        for node in etree.parse(str(path)).findall(".//S"):
            counts[path.parent.name] += 1
            assert len(translations(node, "eng")) == 1
            if not translations(node, "zho"):
                missing_chinese.add((path.parent.name, chapter, int(node.get("id")[5:])))
            else:
                assert len(translations(node, "zho")) == 1
    assert len(paths) == 49 and counts == {"John": 880, "Matthew": 1071}
    assert missing_chinese == {("Matthew", 18, 11), ("Matthew", 23, 14), ("John", 5, 4), ("John", 7, 53)}

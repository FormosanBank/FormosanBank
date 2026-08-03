"""Tests for the gloss-scrape audit (G rules).

Two fixture corpora, both built from the scraping guide's deliberately
maximal example (`Pa~pa<mi>kat-en` — reduplication, infix, circumfix, clitic,
null morpheme, ungrammatical alternate):

- CLEAN_XML: every rule must be silent.
- BROKEN_XML: each rule fires, so a rule that stops working is detectable on
  its own rather than as a drop in an aggregate count.
"""
from pathlib import Path

import pytest
from lxml import etree

from QC.validation import _source_align
from QC.validation._finding import Severity
from QC.validation.rules import gloss_scrape


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

CLEAN_XML = """<?xml version="1.0" encoding="UTF-8"?>
<TEXT xml:lang="ami" citation="c" BibTeX_citation="b" copyright="c">
  <S id="s1">
    <FORM kindOf="original">Pa~pa&lt;mi&gt;kat-en k-u=ni na-a-pa paliding-∅!</FORM>
    <TRANSL kindOf="original" xml:lang="eng" notes="the causee is a little child">Walk with him!</TRANSL>
    <W id="s1w0">
      <FORM kindOf="original">Pa~pa&lt;mi&gt;kat-en</FORM>
      <TRANSL kindOf="original" xml:lang="eng">CAU~&lt;IMP&gt;walk-UV</TRANSL>
      <M id="s1w0m0"><FORM kindOf="original">Pa</FORM><TRANSL xml:lang="eng">CAU</TRANSL></M>
      <M id="s1w0m1"><FORM kindOf="original">-mi-</FORM><TRANSL xml:lang="eng">IMP</TRANSL></M>
      <M id="s1w0m2"><FORM kindOf="original">pakat</FORM><TRANSL xml:lang="eng">walk</TRANSL></M>
      <M id="s1w0m3"><FORM kindOf="original">en</FORM><TRANSL xml:lang="eng">UV</TRANSL></M>
    </W>
    <W id="s1w1">
      <FORM kindOf="original">k-u=ni</FORM>
      <TRANSL kindOf="original" xml:lang="eng">NOM-NCM=this</TRANSL>
      <M id="s1w1m0"><FORM kindOf="original">k</FORM><TRANSL xml:lang="eng">NOM</TRANSL></M>
      <M id="s1w1m1"><FORM kindOf="original">u</FORM><TRANSL xml:lang="eng">NCM</TRANSL></M>
      <M id="s1w1m2"><FORM kindOf="original">=ni</FORM><TRANSL xml:lang="eng">this</TRANSL></M>
    </W>
    <W id="s1w2">
      <FORM kindOf="original">paliding-∅</FORM>
      <TRANSL kindOf="original" xml:lang="eng">car-OBL</TRANSL>
      <M id="s1w2m0"><FORM kindOf="original">paliding</FORM><TRANSL xml:lang="eng">car</TRANSL></M>
      <M id="s1w2m1"><FORM kindOf="original">∅</FORM><TRANSL xml:lang="eng">OBL</TRANSL></M>
    </W>
  </S>
</TEXT>
"""

BROKEN_XML = """<?xml version="1.0" encoding="UTF-8"?>
<TEXT xml:lang="ami" citation="c" BibTeX_citation="b" copyright="c">
  <S id="b1">
    <FORM kindOf="original">Papamikaten kuni naapa paliding</FORM>
    <TRANSL kindOf="original" xml:lang="eng">Walk with him! (Wu 1995, p. 34)</TRANSL>
    <W id="b1w0">
      <FORM kindOf="original">Pa~pa&lt;mi&gt;kat-en</FORM>
      <TRANSL kindOf="original" xml:lang="eng">CAU-&lt;IMP&gt;walk-UV</TRANSL>
      <M id="b1w0m0"><FORM kindOf="original">Pa</FORM><TRANSL xml:lang="eng">CAU</TRANSL></M>
      <M id="b1w0m1"><FORM kindOf="original">-mi-</FORM><TRANSL xml:lang="eng">IMP</TRANSL></M>
      <M id="b1w0m2"><FORM kindOf="original">pa</FORM><TRANSL xml:lang="eng">walk</TRANSL></M>
      <M id="b1w0m3"><FORM kindOf="original">kat-en</FORM><TRANSL xml:lang="eng">UV</TRANSL></M>
    </W>
    <W id="b1w1">
      <FORM kindOf="original">ø-ci</FORM>
      <TRANSL kindOf="original" xml:lang="eng">NOM-PPN</TRANSL>
      <M id="b1w1m0"><FORM kindOf="original">ø</FORM><TRANSL xml:lang="eng">NCM</TRANSL></M>
      <M id="b1w1m1"><FORM kindOf="original">ci</FORM><TRANSL xml:lang="eng">PPN</TRANSL></M>
    </W>
    <W id="b1w2">
      <FORM kindOf="original">paliding</FORM>
      <TRANSL kindOf="original" xml:lang="eng">car-OBL</TRANSL>
    </W>
  </S>
</TEXT>
"""


def _tree(xml: str) -> etree._ElementTree:
    return etree.ElementTree(etree.fromstring(xml.encode("utf-8")))


def _run(rule, xml: str):
    return rule(_tree(xml), Path("fixture.xml"), None)


def _ids(findings) -> set[str]:
    return {f.rule_id for f in findings}


# --------------------------------------------------------------------------
# Clean corpus: every rule silent
# --------------------------------------------------------------------------

@pytest.mark.parametrize("rule", gloss_scrape.RULES, ids=lambda r: r.__name__)
def test_clean_corpus_is_silent(rule):
    assert _run(rule, CLEAN_XML) == []


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def test_marker_skeleton_keeps_only_notation():
    assert gloss_scrape.marker_skeleton("Pa~pa<mi>kat-en") == "~<>-"
    assert gloss_scrape.marker_skeleton("CAU~<IMP>walk-UV") == "~<>-"
    assert gloss_scrape.marker_skeleton("paliding") == ""


def test_gloss_units_counts_infix_plus_segments():
    assert gloss_scrape._gloss_units("CAU~<IMP>walk-UV") == 4
    assert gloss_scrape._gloss_units("NOM-NCM=this") == 3
    assert gloss_scrape._gloss_units("car") == 1


def test_edit_distance_le_1():
    assert gloss_scrape._edit_distance_le_1("NCM", "NOM")
    assert gloss_scrape._edit_distance_le_1("NOM", "NOMS")
    assert not gloss_scrape._edit_distance_le_1("NOM", "ERG")


# --------------------------------------------------------------------------
# Individual rules
# --------------------------------------------------------------------------

def test_g001_fires_on_structural_marker_mismatch():
    # W FORM 'paliding' (no markers) vs TRANSL 'car-OBL' (one '-').
    findings = _run(gloss_scrape.g001_marker_skeleton_parity, BROKEN_XML)
    assert [f.location for f in findings] == ["S=b1 W=b1w2"]
    assert findings[0].severity is Severity.HARD


def test_g007_fires_on_marker_type_only_mismatch():
    # FORM 'Pa~pa<mi>kat-en' ('~<>-') vs TRANSL 'CAU-<IMP>walk-UV' ('-<>-').
    findings = _run(gloss_scrape.g007_marker_type_mismatch, BROKEN_XML)
    assert [f.location for f in findings] == ["S=b1 W=b1w0"]
    assert findings[0].severity is Severity.SOFT


def test_g001_and_g007_are_disjoint():
    both = _run(gloss_scrape.g001_marker_skeleton_parity, BROKEN_XML)
    both += _run(gloss_scrape.g007_marker_type_mismatch, BROKEN_XML)
    locations = [f.location for f in both]
    assert len(locations) == len(set(locations))


def test_g002_fires_when_M_count_differs_from_gloss_units():
    findings = _run(gloss_scrape.g002_M_count_matches_gloss_units, BROKEN_XML)
    # b1w2 has 0 Ms but 'car-OBL' implies 2.
    assert "S=b1 W=b1w2" in [f.location for f in findings]


def test_g002_allows_monomorphemic_word_without_M():
    xml = """<TEXT><S id="s"><W id="w">
        <FORM kindOf="original">paliding</FORM>
        <TRANSL kindOf="original" xml:lang="eng">car</TRANSL>
    </W></S></TEXT>"""
    assert _run(gloss_scrape.g002_M_count_matches_gloss_units, xml) == []


def test_g003_fires_on_internal_dash_but_not_infix_or_affix():
    xml = """<TEXT><S id="s"><W id="w"><FORM kindOf="original">x</FORM>
        <M id="m0"><FORM kindOf="original">k-uda</FORM></M>
        <M id="m1"><FORM kindOf="original">-em-</FORM></M>
        <M id="m2"><FORM kindOf="original">-en</FORM></M>
        <M id="m3"><FORM kindOf="original">=cu</FORM></M>
    </W></S></TEXT>"""
    findings = _run(gloss_scrape.g003_internal_dash_in_M_FORM, xml)
    assert [f.location for f in findings] == ["W=w M=m0"]


def test_g004_fires_when_infix_root_not_rejoined():
    # 'Pa~pa<mi>kat-en' should yield root 'pakat'; broken has 'pa' and 'kat-en'.
    findings = _run(gloss_scrape.g004_infix_root_reconstructed, BROKEN_XML)
    assert [f.location for f in findings] == ["S=b1 W=b1w0"]
    assert "pakat" in findings[0].message


def test_g004_silent_when_root_present_case_insensitively():
    xml = """<TEXT><S id="s"><W id="w">
        <FORM kindOf="original">Pa&lt;mi&gt;kat</FORM>
        <M id="m0"><FORM kindOf="original">-mi-</FORM></M>
        <M id="m1"><FORM kindOf="original">pakat</FORM></M>
    </W></S></TEXT>"""
    assert _run(gloss_scrape.g004_infix_root_reconstructed, xml) == []


def test_g005_flags_rare_label_one_edit_from_frequent_one():
    ms = "".join(
        f'<M id="m{i}"><FORM kindOf="original">x</FORM>'
        f'<TRANSL xml:lang="eng">NOM</TRANSL></M>'
        for i in range(8)
    )
    xml = (
        f'<TEXT><S id="s"><W id="w"><FORM kindOf="original">x</FORM>{ms}'
        '<M id="odd"><FORM kindOf="original">x</FORM>'
        '<TRANSL xml:lang="eng">NCM</TRANSL></M></W></S></TEXT>'
    )
    findings = _run(gloss_scrape.g005_gloss_label_inventory, xml)
    assert [f.character for f in findings] == ["NCM"]
    assert findings[0].severity is Severity.WARN


def test_g006_flags_o_stroke_null_and_accepts_empty_set():
    findings = _run(gloss_scrape.g006_non_canonical_null_symbol, BROKEN_XML)
    locations = {f.location for f in findings}
    assert "W=b1w1 M=b1w1m0" in locations   # M FORM is exactly 'ø'
    assert "S=b1 W=b1w1" in locations       # W FORM 'ø-ci', variant beside '-'
    assert all(f.severity is Severity.HARD for f in findings)


def test_g006_ignores_o_stroke_inside_a_word():
    # No check may assume a character is absent from some language's orthography.
    xml = """<TEXT><S id="s"><W id="w">
        <FORM kindOf="original">baroøna</FORM></W></S></TEXT>"""
    assert _run(gloss_scrape.g006_non_canonical_null_symbol, xml) == []


def _mixed_retention_xml(retained: int, stripped: int) -> str:
    sentences = []
    for i in range(retained + stripped):
        s_form = "ma-kan tu" if i < retained else "makan tu"
        sentences.append(
            f'<S id="s{i}"><FORM kindOf="original">{s_form}</FORM>'
            f'<W id="w{i}"><FORM kindOf="original">ma-kan</FORM></W></S>'
        )
    return f"<TEXT>{''.join(sentences)}</TEXT>"


def test_g010_fires_only_on_a_mix():
    assert _run(gloss_scrape.g010_mixed_marker_retention, _mixed_retention_xml(6, 0)) == []
    assert _run(gloss_scrape.g010_mixed_marker_retention, _mixed_retention_xml(0, 6)) == []
    findings = _run(gloss_scrape.g010_mixed_marker_retention, _mixed_retention_xml(4, 2))
    assert len(findings) == 1
    assert "4/6 retain" in findings[0].message


def test_g010_ignores_sentences_whose_W_tier_has_no_markers():
    xml = (
        "<TEXT>"
        + "".join(
            f'<S id="s{i}"><FORM kindOf="original">makan tu</FORM>'
            f'<W id="w{i}"><FORM kindOf="original">makan</FORM></W></S>'
            for i in range(6)
        )
        + "</TEXT>"
    )
    assert _run(gloss_scrape.g010_mixed_marker_retention, xml) == []


def test_g011_fires_when_slash_at_both_tiers():
    xml = """<TEXT><S id="s">
        <FORM kindOf="original">an-ie/da-ie kuni</FORM>
        <W id="w"><FORM kindOf="original">an-ie/da-ie</FORM></W>
    </S></TEXT>"""
    findings = _run(gloss_scrape.g011_unsplit_slash_alternate, xml)
    assert [f.location for f in findings] == ["S=s"]


def test_g011_silent_when_slash_only_in_translation():
    xml = """<TEXT><S id="s">
        <FORM kindOf="original">anie kuni</FORM>
        <TRANSL xml:lang="eng">he came from/goes to the park</TRANSL>
        <W id="w"><FORM kindOf="original">anie</FORM></W>
    </S></TEXT>"""
    assert _run(gloss_scrape.g011_unsplit_slash_alternate, xml) == []


def test_g012_flags_trailing_citation_and_respects_notes():
    findings = _run(gloss_scrape.g012_trailing_paren_note_in_TRANSL, BROKEN_XML)
    assert len(findings) == 1
    assert "Wu 1995" in findings[0].message
    # CLEAN_XML carries the same commentary in a notes attribute instead.
    assert _run(gloss_scrape.g012_trailing_paren_note_in_TRANSL, CLEAN_XML) == []


# --------------------------------------------------------------------------
# Group C: source alignment
# --------------------------------------------------------------------------

SOURCE_TXT = """\
(1)
Pa~pa<mi>kat-en k-u=ni na-a-pa paliding-∅!
CAU~<IMP>walk-UV NOM-NCM=this SG-LNK-SG car-OBL
'Walk with him!'
'Drive this car!'

(2)
mi-kucakuc-ay ø-ci aki t-u kilang
AV-climb-FAC NOM-PPN Aki DAT-CM tree
'Aki climbed the tree.'
"""


def test_skeleton_discards_markers_and_case():
    assert _source_align.skeleton("mi-lingatu ø-ci aki") == "milingatuøciaki"
    assert _source_align.skeleton("MiLingatu") == "milingatu"


def test_find_example_regions_splits_on_numbered_labels():
    regions = _source_align.find_example_regions(SOURCE_TXT.splitlines())
    assert [r.label for r in regions] == ["(1)", "(2)"]
    assert regions[0].translations == ["Walk with him!", "Drive this car!"]


def _align_clean(tmp_path: Path, xml: str = CLEAN_XML):
    source = tmp_path / "paper.txt"
    source.write_text(SOURCE_TXT, encoding="utf-8")
    xml_path = tmp_path / "corpus.xml"
    xml_path.write_text(xml, encoding="utf-8")
    trees = [(xml_path, _tree(xml))]
    lines, extractor = _source_align.extract_lines(source)
    alignment = _source_align.align(trees, lines, extractor)
    return trees, alignment, source


def test_g021_reports_source_example_missing_from_xml(tmp_path):
    # CLEAN_XML contains example (1) only; (2) was dropped.
    trees, alignment, source = _align_clean(tmp_path)
    findings = _source_align.source_findings(trees, alignment, source)
    g021 = [f for f in findings if f.rule_id == "G021"]
    assert len(g021) == 1
    assert "(2)" in g021[0].message


def test_g020_reports_xml_sentence_absent_from_source(tmp_path):
    fabricated = CLEAN_XML.replace(
        "Pa~pa&lt;mi&gt;kat-en k-u=ni na-a-pa paliding-∅!",
        "zzzz qqqq wwww vvvv xxxx yyyy",
    )
    trees, alignment, source = _align_clean(tmp_path, fabricated)
    findings = _source_align.source_findings(trees, alignment, source)
    assert [f.rule_id for f in findings if f.rule_id == "G020"] == ["G020"]


def test_g023_always_reports_extraction_numbers(tmp_path):
    trees, alignment, source = _align_clean(tmp_path)
    findings = _source_align.source_findings(trees, alignment, source)
    g023 = [f for f in findings if f.rule_id == "G023"]
    assert len(g023) == 1
    assert "extractor=plaintext" in g023[0].message
    assert g023[0].severity is Severity.WARN


def test_g013_flags_collapsed_translations(tmp_path):
    trees, alignment, source = _align_clean(tmp_path)
    findings = _source_align.source_findings(trees, alignment, source)
    g013 = [f for f in findings if f.rule_id == "G013"]
    # Source example (1) offers two translations; CLEAN_XML keeps one.
    assert len(g013) == 1
    assert "Drive this car!" in g013[0].message


def test_g022_reports_characters_lost_against_source(tmp_path):
    stripped = CLEAN_XML.replace("paliding-∅", "paliding").replace(
        "<FORM kindOf=\"original\">∅</FORM>", "<FORM kindOf=\"original\">x</FORM>"
    )
    trees, alignment, source = _align_clean(tmp_path, stripped)
    findings = _source_align.source_findings(trees, alignment, source)
    g022 = [f for f in findings if f.rule_id == "G022"]
    assert g022, "expected the dropped ∅ to be reported"
    assert "U+2205" in g022[0].message


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def test_unparseable_xml_becomes_a_G000_finding(tmp_path):
    from QC.validation import audit_gloss_scrape

    bad = tmp_path / "bad.xml"
    bad.write_text('<TEXT xml:lang="ami" copyright""></TEXT>', encoding="utf-8")
    trees, findings = audit_gloss_scrape.load_trees([bad])
    assert trees == []
    assert [f.rule_id for f in findings] == ["G000"]
    assert findings[0].severity is Severity.HARD


def test_source_discovery_prefers_pdf_over_derived_text(tmp_path):
    from QC.validation import audit_gloss_scrape

    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "glossed-chunks.txt").write_text("x", encoding="utf-8")
    (tmp_path / "data" / "paper.pdf").write_bytes(b"%PDF-1.4")
    candidates = audit_gloss_scrape.discover_sources(tmp_path)
    assert candidates[0].name == "paper.pdf"


def test_audit_exits_zero_on_hard_findings_by_default(tmp_path):
    from QC.validation import audit_gloss_scrape

    xml_path = tmp_path / "corpus.xml"
    xml_path.write_text(BROKEN_XML, encoding="utf-8")
    code = audit_gloss_scrape.main([
        "--xml", str(xml_path), "--no-source",
        "--csv", str(tmp_path / "out.csv"),
    ])
    assert code == 0
    assert (tmp_path / "out.csv").exists()


def test_audit_exit_on_hard_flag_returns_one(tmp_path):
    from QC.validation import audit_gloss_scrape

    xml_path = tmp_path / "corpus.xml"
    xml_path.write_text(BROKEN_XML, encoding="utf-8")
    code = audit_gloss_scrape.main([
        "--xml", str(xml_path), "--no-source", "--exit-on-hard",
        "--csv", str(tmp_path / "out.csv"),
    ])
    assert code == 1

"""NTUFormosanCorpus writes its unknown-content markers as <UNCLEAR/>.

Maintainer's rulings, 2026-10-17, implemented by
Corpora/NTUFormosanCorpus/CodeAndDocs/pipeline/mark_unclear.py:

1. Untranscribed words (NTU's X / XX / XXX): "A. All tiers: sentence FORM, word
   FORM, word gloss, PHON; drop the M under it (no analysis exists, POL-057)".
2. Unknown glosses: "B. A, plus ? used as a placeholder inside a gloss", A =
   "Convert glosses that are exactly ? or ??". Placeholders inside a longer gloss
   are converted only where unclear_gloss_placeholders.tsv lists the gloss (the
   table ships empty).
3. "B. Glosses UNCLEAR; sentence translations omitted".
4. "if the S FORM is simply <UNCLEAR/>, no Ws. If the W FORM is <UNCLEAR />, no Ms
   under it."

The first group runs the step on small hand-written sentences; the second holds
the published XML to the rulings. NTU_XML_DIR points the second group at another
tree (e.g. the pre-change XML, on which these tests fail).
"""
from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CODEDOCS = ROOT / "Corpora" / "NTUFormosanCorpus" / "CodeAndDocs"
sys.path.insert(0, str(CODEDOCS / "pipeline"))

import mark_unclear as mu  # noqa: E402

NTU_XML = Path(os.environ.get("NTU_XML_DIR") or ROOT / "Corpora" / "NTUFormosanCorpus" / "XML")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

# The 13 words whose FORM is X but whose gloss is something else. Held unchanged
# (possible misalignments, not ruled on); a change to this list is a change to
# the corpus that should be looked at.
HELD = {
    "AtaNr-moving_Takun_S_106_W0": "FS",
    "AtaNr-proposal_Takun_S_143_W0": "??",
    "kkvNr_millet_Muu_S_56_W2": "??",
    "SaiNr-holiday_kalaeh a _oemaw_S_73_W2": "(Mandarin)",
    "SaiNr-holiday_kalaeh a _oemaw_S_78_W6": "after",
    "SaiNr-kathethel2_kalaeh a oemaw_S_1_W14": "(Mandarin)",
    "SaiNr-kathethel2_kalaeh a oemaw_S_351_W4": "is",
    "SaiNr-kathethel_parain a _oemaw_S_35_W4": "father",
    "Sainr-frog4_lalo a tahaeS_S_107_W0": "gaksa",
    "sdqCon-dialog1_ciwas_tiwas 2021s_S_118_W3": "PART",
    "sdqCon-dialog2_ciwas_tiwas 2021s_S_126_W3": "FS",
    "sdqCon-dialog2_ciwas_tiwas 2021s_S_87_W2": "NOM",
    "TsouConv-informants_S_137_W14": "FS",
}


# ------------------------------------------------------------- the step itself

SAMPLE = """<?xml version="1.0" ?>
<TEXT id="t" xml:lang="ami">
    <S id="s1">
        <FORM kindOf="original">piala haca, XX, aku lopas.</FORM>
        <PHON kindOf="original">piaɾa ħaʦa xx aku ɾopas</PHON>
        <FORM kindOf="standard">piala haca, XX, ako lopas.</FORM>
        <PHON kindOf="standard">piaɾa ħaʦa xx ako ɾopas</PHON>
        <TRANSL xml:lang="zho">只有</TRANSL>
        <TRANSL xml:lang="eng">?</TRANSL>
        <W id="s1_W0">
            <FORM kindOf="original">haca,</FORM>
            <TRANSL xml:lang="eng" kindOf="original">??</TRANSL>
            <M id="s1_W0M0">
                <FORM kindOf="original">haca,</FORM>
                <TRANSL xml:lang="eng" kindOf="original">？</TRANSL>
            </M>
        </W>
        <W id="s1_W1">
            <FORM kindOf="original">XX,</FORM>
            <PHON kindOf="original">xx</PHON>
            <TRANSL xml:lang="zho" kindOf="original">X</TRANSL>
            <TRANSL xml:lang="eng" kindOf="original">X</TRANSL>
            <M id="s1_W1M0">
                <FORM kindOf="original">XX,</FORM>
                <TRANSL xml:lang="eng" kindOf="original">X</TRANSL>
            </M>
        </W>
        <W id="s1_W2">
            <FORM kindOf="original">aku</FORM>
            <TRANSL xml:lang="eng" kindOf="original">1SG-?</TRANSL>
        </W>
        <W id="s1_W3">
            <FORM kindOf="original">X.</FORM>
            <TRANSL xml:lang="eng" kindOf="original">FS</TRANSL>
            <M id="s1_W3M0">
                <FORM kindOf="original">X.</FORM>
                <TRANSL xml:lang="eng" kindOf="original">FS</TRANSL>
            </M>
        </W>
    </S>
    <S id="s2">
        <FORM kindOf="original">XXX</FORM>
        <PHON kindOf="original">xxx</PHON>
        <TRANSL xml:lang="eng">XXX</TRANSL>
        <W id="s2_W0">
            <FORM kindOf="original">XXX</FORM>
            <TRANSL xml:lang="eng" kindOf="original">X</TRANSL>
        </W>
    </S>
</TEXT>"""


def _run(tmp_path, table_rows=None):
    xml_dir = tmp_path / "xml"
    xml_dir.mkdir()
    (xml_dir / "a.xml").write_text(SAMPLE, encoding="utf-8")
    table = tmp_path / "placeholders.tsv"
    table.write_text("gloss\tlang\n" + "".join(f"{g}\t{l}\n" for g, l in table_rows or []),
                     encoding="utf-8")
    assert mu.main(["--xml_dir", str(xml_dir), "--placeholders", str(table)]) == 0
    text = (xml_dir / "a.xml").read_text(encoding="utf-8")
    return text, {e.get("id"): e for e in ET.fromstring(text.split("\n", 1)[1]).iter() if e.get("id")}


def _inner(el):
    return (el.text or "") + "".join(ET.tostring(c, encoding="unicode") for c in el)


def test_untranscribed_word_in_every_tier(tmp_path):
    _, ids = _run(tmp_path)
    s1 = ids["s1"]
    forms = s1.findall("FORM")
    assert [_inner(f) for f in forms] == ["piala haca, <UNCLEAR />, aku lopas.",
                                          "piala haca, <UNCLEAR />, ako lopas."]
    assert [_inner(p) for p in s1.findall("PHON")] == ["piaɾa ħaʦa <UNCLEAR /> aku ɾopas",
                                                       "piaɾa ħaʦa <UNCLEAR /> ako ɾopas"]
    w = ids["s1_W1"]
    assert _inner(w.find("FORM")) == "<UNCLEAR />,"
    assert _inner(w.find("PHON")) == "<UNCLEAR />"
    assert [(t.get(XML_LANG), t.get("kindOf"), _inner(t)) for t in w.findall("TRANSL")] == [
        ("zho", "original", "<UNCLEAR />"), ("eng", "original", "<UNCLEAR />")]
    assert w.findall("M") == []


def test_unknown_glosses_and_sentence_translations(tmp_path):
    _, ids = _run(tmp_path)
    assert [t.get(XML_LANG) for t in ids["s1"].findall("TRANSL")] == ["zho"]   # eng "?" omitted
    assert _inner(ids["s1_W0"].find("TRANSL")) == "<UNCLEAR />"                 # ??
    assert _inner(ids["s1_W0M0"].find("TRANSL")) == "<UNCLEAR />"               # full-width ？
    assert _inner(ids["s1_W2"].find("TRANSL")) == "1SG-?"                       # placeholder, not listed


def test_sentence_that_is_only_unclear_has_no_words(tmp_path):
    _, ids = _run(tmp_path)
    s2 = ids["s2"]
    assert _inner(s2.find("FORM")) == "<UNCLEAR />"
    assert _inner(s2.find("PHON")) == "<UNCLEAR />"
    assert s2.findall("W") == [] and s2.findall("TRANSL") == []


def test_x_word_with_a_real_gloss_is_left_alone(tmp_path):
    _, ids = _run(tmp_path)
    w = ids["s1_W3"]
    assert w.find("FORM").text == "X." and w.find("TRANSL").text == "FS"
    assert len(w.findall("M")) == 1


def test_second_run_changes_nothing(tmp_path):
    text, _ = _run(tmp_path)
    table = tmp_path / "placeholders.tsv"
    assert mu.main(["--xml_dir", str(tmp_path / "xml"), "--placeholders", str(table)]) == 0
    assert (tmp_path / "xml" / "a.xml").read_text(encoding="utf-8") == text


def test_placeholder_table_row_converts_only_that_gloss(tmp_path):
    _, ids = _run(tmp_path, [("1SG-?", "eng")])
    assert _inner(ids["s1_W2"].find("TRANSL")) == "1SG-<UNCLEAR />"


def test_placeholder_table_row_is_language_specific(tmp_path):
    _, ids = _run(tmp_path, [("1SG-?", "zho")])
    assert _inner(ids["s1_W2"].find("TRANSL")) == "1SG-?"


def test_shipped_placeholder_table_is_empty():
    rows = [ln for ln in (CODEDOCS / "unclear_gloss_placeholders.tsv").read_text(encoding="utf-8").splitlines()
            if ln.strip()]
    assert rows == ["gloss\tlang"]


# ----------------------------------------------------------- the published XML

X_TOKEN = re.compile(r'(?<!\S)[.,!?;:"“”()]*X+[.,!?;:"“”()]*(?!\S)')
UNKNOWN = re.compile(r"^\s*[?？]{1,3}\s*$")


@pytest.fixture(scope="module")
def sentences():
    files = sorted(NTU_XML.rglob("*.xml"))
    assert files, f"no XML found under {NTU_XML}"
    return [s for path in files for s in ET.parse(path).getroot().iter("S")]


def _held(w):
    return w.get("id") in HELD


def test_no_x_token_left_in_a_sentence_form(sentences):
    hits = [(s.get("id"), f.text) for s in sentences for f in s.findall("FORM")
            if X_TOKEN.search("".join(f.itertext()))]
    assert hits == [], f"{len(hits)} S FORM(s) still hold an X token, e.g. {hits[:3]}"


def test_x_words_are_unclear_and_have_no_morphemes(sentences):
    bad = []
    for s in sentences:
        for w in s.findall("W"):
            if _held(w):
                continue
            if any(re.fullmatch(r'\s*[.,!?;:"“”()]*X+[.,!?;:"“”()]*\s*', f.text or "") and len(f) == 0
                   for f in w.findall("FORM")):
                bad.append(w.get("id"))
            if any(f.find("UNCLEAR") is not None for f in w.findall("FORM")) and w.findall("M"):
                bad.append(w.get("id") + " (has M)")
    assert bad == [], f"{len(bad)} X word(s) not converted, e.g. {bad[:5]}"


def test_no_gloss_is_only_a_question_mark(sentences):
    bad = [(n.get("id"), t.text) for s in sentences for w in s.findall("W") if not _held(w)
           for n in [w, *w.findall("M")] for t in n.findall("TRANSL")
           if len(t) == 0 and UNKNOWN.match(t.text or "")]
    assert bad == [], f"{len(bad)} W/M gloss(es) are still ?/??/???, e.g. {bad[:5]}"


def test_no_sentence_translation_is_only_a_marker(sentences):
    bad = [(s.get("id"), t.text) for s in sentences for t in s.findall("TRANSL")
           if re.fullmatch(r"\s*(?:[?？]{1,3}|X+)\s*", "".join(t.itertext()))]
    assert bad == [], f"S TRANSL that are only an unknown marker: {bad}"


def test_sentence_that_is_only_unclear_has_no_words_published(sentences):
    bad = []
    for s in sentences:
        f = next((f for f in s.findall("FORM") if f.get("kindOf") == "original" and f.get("ver") is None), None)
        if f is not None and f.find("UNCLEAR") is not None and s.findall("W"):
            rest = (f.text or "") + "".join(c.tail or "" for c in f)
            if not any(ch.isalnum() for ch in rest):
                bad.append(s.get("id"))
    assert bad == []


def test_held_words_are_unchanged(sentences):
    found = {w.get("id"): [t.text for t in w.findall("TRANSL")] for s in sentences for w in s.findall("W")
             if w.get("id") in HELD}
    assert set(found) == set(HELD)
    for wid, gloss in HELD.items():
        assert gloss in found[wid], (wid, found[wid])

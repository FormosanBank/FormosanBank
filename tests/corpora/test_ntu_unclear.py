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

Maintainer's rulings, 2026-10-18 (mark_unclear.py and strip_word_punctuation.py):

5. Word FORM punctuation, option "Bare <UNCLEAR/>": "Punctuation shouldn't be in W
   FORMs or M FORMs anyway. Delete everywhere in NTU." What is punctuation is
   decided per language in CodeAndDocs/word_form_characters.tsv.
6. The 13 X words with a real gloss: "FORM -> <UNCLEAR/>, keep the real gloss (and
   its morphemes)".
7. X as part of a word: "Convert the X part only (mi-<UNCLEAR/>)".

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
import strip_word_punctuation as swp  # noqa: E402

NTU_XML = Path(os.environ.get("NTU_XML_DIR") or ROOT / "Corpora" / "NTUFormosanCorpus" / "XML")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

# The 13 words whose FORM is X but whose gloss is something else. Ruling
# 2026-10-18: FORM -> <UNCLEAR/>, gloss and morphemes kept; a change to this list
# is a change to the corpus that should be looked at.
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
    assert _inner(w.find("FORM")) == "<UNCLEAR />"          # bare (ruling 2026-10-18)
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


def test_x_word_with_a_real_gloss_gets_an_unclear_form_only(tmp_path):
    _, ids = _run(tmp_path)
    w = ids["s1_W3"]
    assert _inner(w.find("FORM")) == "<UNCLEAR />" and w.find("TRANSL").text == "FS"
    assert [_inner(f) for f in w.find("M").findall("FORM")] == ["X."]     # M kept as is


def test_x_part_of_a_word(tmp_path):
    xml_dir = tmp_path / "xml"
    xml_dir.mkdir()
    (xml_dir / "a.xml").write_text("""<TEXT id="t" xml:lang="ami">
    <S id="s1">
        <FORM kindOf="original">kafana'an miXX, 我的XX在XX那邊 Xinyi</FORM>
        <W id="s1_W0">
            <FORM kindOf="original">mi-XX,</FORM>
            <TRANSL xml:lang="eng" kindOf="original">AF-XX</TRANSL>
            <M id="s1_W0M0"><FORM kindOf="original">XX,</FORM></M>
        </W>
        <W id="s1_W1"><FORM kindOf="original">Xinyi</FORM></W>
    </S>
</TEXT>""", encoding="utf-8")
    table = tmp_path / "placeholders.tsv"
    table.write_text("gloss\tlang\n", encoding="utf-8")
    assert mu.main(["--xml_dir", str(xml_dir), "--placeholders", str(table)]) == 0
    ids = {e.get("id"): e for e in ET.parse(xml_dir / "a.xml").getroot().iter() if e.get("id")}
    assert _inner(ids["s1"].find("FORM")) == "kafana'an miXX, 我的<UNCLEAR />在<UNCLEAR />那邊 Xinyi"
    assert _inner(ids["s1_W0"].find("FORM")) == "mi-<UNCLEAR />,"
    assert ids["s1_W0"].find("TRANSL").text == "AF-XX"                 # gloss not ruled on
    assert _inner(ids["s1_W0"].find("M/FORM")) == "XX,"                 # M not ruled on
    assert _inner(ids["s1_W1"].find("FORM")) == "Xinyi"


PUNCT_TABLE = """# comment
lang\tchar\tcodepoint\tclass\taction\tnote
ami\t,\tU+002C\tpunctuation\tdelete\t
ami\t.\tU+002E\tunclear\thold\t
ami\t'\tU+0027\tletter\tkeep\t
ami\t-\tU+002D\tmarker\tkeep\t
"""

PUNCT_SAMPLE = """<?xml version="1.0" ?>
<TEXT id="t" xml:lang="ami">
    <S id="s1">
        <FORM kindOf="original">haca, 'aca. , mi-<UNCLEAR/>,</FORM>
        <W id="s1_W0">
            <FORM kindOf="original">haca,</FORM>
            <FORM kindOf="standard" ver="alt">haca,</FORM>
            <M id="s1_W0M0"><FORM kindOf="original">haca,</FORM></M>
        </W>
        <W id="s1_W1"><FORM kindOf="original">'aca.</FORM></W>
        <W id="s1_W2"><FORM kindOf="original">,</FORM></W>
        <W id="s1_W3"><FORM kindOf="original">mi-<UNCLEAR/>,</FORM></W>
    </S>
</TEXT>"""


def _strip(tmp_path, sample=PUNCT_SAMPLE):
    xml_dir = tmp_path / "xml"
    xml_dir.mkdir()
    (xml_dir / "a.xml").write_text(sample, encoding="utf-8")
    table = tmp_path / "chars.tsv"
    table.write_text(PUNCT_TABLE, encoding="utf-8")
    rc = swp.main(["--xml_dir", str(xml_dir), "--table", str(table)])
    text = (xml_dir / "a.xml").read_text(encoding="utf-8")
    return rc, text, {e.get("id"): e for e in ET.fromstring(text.split("\n", 1)[1]).iter() if e.get("id")}


def test_word_punctuation_deleted_per_table(tmp_path):
    rc, _, ids = _strip(tmp_path)
    assert rc == 0
    assert [_inner(f) for f in ids["s1_W0"].findall("FORM")] == ["haca", "haca"]    # every tier and variant
    assert _inner(ids["s1_W0M0"].find("FORM")) == "haca"                              # M too
    assert _inner(ids["s1_W1"].find("FORM")) == "'aca."      # ' a letter, . held
    assert _inner(ids["s1_W2"].find("FORM")) == ","          # would be empty: left
    assert _inner(ids["s1_W3"].find("FORM")) == "mi-<UNCLEAR />"
    assert _inner(ids["s1"].find("FORM")) == "haca, 'aca. , mi-<UNCLEAR />,"         # S untouched


FINAL_TABLE = """lang\tchar\tcodepoint\tclass\taction\tnote
tsu\t.\tU+002E\tpunctuation\tfinal\t
tsu\t,\tU+002C\tpunctuation\tfinal\t
tsu\t?\tU+003F\tpunctuation\tfinal\t
tsu\t"\tU+0022\tpunctuation\tdelete\t
tsu\t'\tU+0027\tletter\tkeep\t
tsu\t-\tU+002D\tmarker\tkeep\t
tsu\t=\tU+003D\tmarker\tkeep\t
"""

FINAL_CASES = {   # FORM -> after the step (ruling 2026-10-18 on FORM-final punctuation)
    "zo.lu.shang.lai.a.": "zo.lu.shang.lai.a",     # inside dots stay, the final one goes
    "Lao.Jia": "Lao.Jia",
    "a,,": "a",                                    # the whole final run
    "kati...": "kati",
    'Y,M"': "Y,M",                                 # a 'delete' character ends the run too
    "wu-.": "wu-",                                 # left ending in a marker
    "umah.-": "umah.-",                            # '.' before a marker is not final
    "pa-pacay-?": "pa-pacay-?",                    # ? after - or = is an unknown morpheme
    "palrayngi=?.": "palrayngi=?",
    "?la-lasu.": "?la-lasu",
    "ulaqi'.": "ulaqi'",
    ".": ".",                                      # would be empty: left
}


def test_word_punctuation_form_final_only(tmp_path):
    words = "".join(f'<W id="w{i}"><FORM kindOf="original">{f}</FORM></W>' for i, f in enumerate(FINAL_CASES))
    sample = ('<?xml version="1.0" ?>\n<TEXT id="t" xml:lang="tsu"><S id="s"><FORM kindOf="original">x</FORM>'
              + words + '<W id="u"><FORM kindOf="original"><UNCLEAR/>=maku.</FORM></W></S></TEXT>')
    xml_dir = tmp_path / "xml"
    xml_dir.mkdir()
    (xml_dir / "a.xml").write_text(sample, encoding="utf-8")
    (tmp_path / "chars.tsv").write_text(FINAL_TABLE, encoding="utf-8")
    assert swp.main(["--xml_dir", str(xml_dir), "--table", str(tmp_path / "chars.tsv")]) == 0
    ids = {e.get("id"): e for e in ET.parse(xml_dir / "a.xml").getroot().iter() if e.get("id")}
    assert {f: _inner(ids[f"w{i}"].find("FORM")) for i, f in enumerate(FINAL_CASES)} == FINAL_CASES
    assert _inner(ids["u"].find("FORM")) == "<UNCLEAR />=maku"      # final after <UNCLEAR/>


def test_word_punctuation_second_run_changes_nothing(tmp_path):
    _, text, _ = _strip(tmp_path)
    assert swp.main(["--xml_dir", str(tmp_path / "xml"), "--table", str(tmp_path / "chars.tsv")]) == 0
    assert (tmp_path / "xml" / "a.xml").read_text(encoding="utf-8") == text


def test_word_punctuation_unlisted_character_stops(tmp_path):
    with pytest.raises(SystemExit):
        _strip(tmp_path, PUNCT_SAMPLE.replace("haca,</FORM>\n            <FORM", "haca;</FORM>\n            <FORM"))


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
def texts():
    files = sorted(NTU_XML.rglob("*.xml"))
    assert files, f"no XML found under {NTU_XML}"
    return [ET.parse(path).getroot() for path in files]


@pytest.fixture(scope="module")
def sentences(texts):
    return [s for t in texts for s in t.iter("S")]


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
            # "If the W FORM is <UNCLEAR />, no Ms": a FORM that is only the marker
            # (an X part, mi-<UNCLEAR/>, keeps its morphemes; ruling 2026-10-18).
            if any(_inner(f) == "<UNCLEAR />" for f in w.findall("FORM")) and w.findall("M"):
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


# ------------------------------------------- rulings of 2026-10-18, published XML

PARTIAL_X = {   # ruling 3: W id -> its original FORM as published
    "Amis_Conv-talking_tamih_panay_S_122_W10": "mi-<UNCLEAR />",
    "kkvNr_dailylife_Angai_S_9_W1": "<UNCLEAR />=maku",           # FORM-final '.' removed
    "kkvNr_family_Paicu_S_42_W1": "<UNCLEAR />=ci=kim",
    "kkvNr_family_Paicu_S_47_W1": "<UNCLEAR />=ci=kim",
    "RukaiNr-childhood_balenge_S_5_W0": "kia-<UNCLEAR />=aku",
    "SaiNr-frog6_kalaeh a _oemaw_S_47_W10": "<UNCLEAR />-ralom-an",
    "TsouConv-typhoon_S_326_W1": "mucian-shi-alishansiang-zuei-<UNCLEAR />",    # FORM-final '.' removed
}
# Word FORMs written only with a character to delete: deleting would empty them.
EMPTY_IF_DELETED = {"bnNr-frog_Ciang_S_64_W5", "bnNr-frog_Ciang_S_64_W5M0",
                    "bnNr-frog_Ciang_S_78_W8", "bnNr-frog_Ciang_S_78_W8M0"}
# Word FORMs written only with a FORM-final character (Bunun '.', glossed (咳嗽); Seediq ',',
# glossed PART): left, since deleting would empty them. Not ruled on; V164 flags them.
ONLY_PUNCTUATION = {"bnNr-frog_Ciang_S_34_W3", "bnNr-frog_Ciang_S_34_W3M0",
                    "bnNr-frog_Ciang_S_159_W0", "bnNr-frog_Ciang_S_159_W0M0",
                    "sdqNr-childhood_micang 2020s_S_185_W16", "sdqNr-childhood_micang 2020s_S_185_W16M0"}


@pytest.fixture(scope="module")
def char_table():
    return swp.load_table(CODEDOCS / "word_form_characters.tsv")


def test_no_deletable_punctuation_in_word_or_morpheme_forms(texts, char_table):
    bad, unlisted = [], set()
    for t in texts:
        lang = t.get(XML_LANG)
        for el in [*t.iter("W"), *t.iter("M")]:
            if el.get("id") in EMPTY_IF_DELETED:
                continue
            for f in el.findall("FORM"):
                for ch in "".join(f.itertext()):
                    if swp.is_content(ch):
                        continue
                    action = char_table.get((lang, ch))
                    if action is None:
                        unlisted.add((lang, ch))
                    elif action == "delete":
                        bad.append((el.get("id"), "".join(f.itertext())))
                        break
    assert unlisted == set(), f"characters missing from word_form_characters.tsv: {sorted(unlisted)}"
    assert bad == [], f"{len(bad)} W/M FORM(s) still hold punctuation to delete, e.g. {bad[:5]}"


def test_no_form_final_punctuation_in_word_or_morpheme_forms(texts, char_table):
    """Ruling 2026-10-18: the 'final' characters go from the end of a W/M FORM only."""
    bad = []
    for t in texts:
        lang = t.get(XML_LANG)
        for el in [*t.iter("W"), *t.iter("M")]:
            if el.get("id") in EMPTY_IF_DELETED | ONLY_PUNCTUATION:
                continue
            for f in el.findall("FORM"):
                last = (f[-1].tail if len(f) else f.text) or ""
                if swp.final_run_start(last, lang, char_table) < len(last):
                    bad.append((el.get("id"), "".join(f.itertext())))
    assert bad == [], f"{len(bad)} W/M FORM(s) still end in punctuation, e.g. {bad[:5]}"


INSIDE_WORD_DOTS = {   # "attempts to write multimorphemic Chinese words. We don't wnat to remove those periods."
    "None-1_S_93_W8": "Lao.Jia",
    "None-1_S_150_W0": "zo.lu.shang.lai.a",
    "RukaiNr-marriage ceremony_taugadha_S_177_W0": "tou.mu",
    "52_S_5_W1": "Sung.laoshi",
}


def test_inside_word_dots_stay(sentences):
    found = {w.get("id"): _inner(w.find("FORM")) for s in sentences for w in s.findall("W")
             if w.get("id") in INSIDE_WORD_DOTS}
    assert found == INSIDE_WORD_DOTS


def test_kavalan_percent_deleted(sentences):
    """Ruling 2026-10-18 on Kavalan s%, seme% (glossed FS): "the % should be deleted." """
    words = {w.get("id"): w for s in sentences for w in s.findall("W")
             if w.get("id") in ("KavNr-map_buya_S_6_W3", "KavNr-map_buya_S_26_W5")}
    assert {k: [_inner(f) for f in w.iter("FORM")] for k, w in words.items()} == {
        "KavNr-map_buya_S_6_W3": ["s"] * 4, "KavNr-map_buya_S_26_W5": ["seme"] * 4}


def test_gloss_label_in_a_form_is_unclear(texts):
    """Ruling 2026-10-18 on 'AV.kara-peen=kasu' (Sentences 3.json record 456, no reversal
    in the record): "If it is just for that word, then the FORM should carry <UNCLEAR/>"."""
    s = next(s for t in texts if t.get(XML_LANG) == "xnb" for s in t.iter("S")
             if s.get("id") == "3_S_456" and s.find("W/TRANSL") is not None)
    w = s.find("W")
    assert [_inner(f) for f in s.findall("FORM")] == ["<UNCLEAR />karapeenkasu pai'ici?"] * 2
    assert [_inner(f) for f in w.findall("FORM")] == ["<UNCLEAR />kara-peen=kasu"] * 2
    assert [_inner(f) for f in w.find("M").findall("FORM")] == ["<UNCLEAR />kara"] * 2
    assert [_inner(p) for p in w.findall("PHON")] == ["<UNCLEAR />ka[r|ɾ]apeenkasu"] * 2
    assert [t.text for t in w.findall("TRANSL")] == ["主焦.喝-多少=2SG.主格", "AV.drink-how.many=2SG.NOM"]
    labels = [(n.get("id"), "".join(f.itertext())) for t in texts for n in [*t.iter("W"), *t.iter("M")]
              for f in n.findall("FORM") if "".join(f.itertext()).startswith("AV.")]
    assert labels == []


def test_mark_unclear_replaces_the_listed_gloss_label(tmp_path):
    sample = """<?xml version="1.0" ?>
<TEXT id="t" xml:lang="xnb">
    <S id="3_S_456">
        <FORM kindOf="original">AV.karapeenkasu pai'ici?</FORM>
        <PHON kindOf="original">avka[r|ɾ]apeenkasu paiʔiʦi</PHON>
        <W id="3_S_456_W0">
            <FORM kindOf="original">AV.kara-peen=kasu</FORM>
            <PHON kindOf="original">avka[r|ɾ]apeenkasu</PHON>
            <M id="3_S_456_W0M0"><FORM kindOf="original">AV.kara</FORM><PHON kindOf="original">avka[r|ɾ]a</PHON></M>
            <M id="3_S_456_W0M1"><FORM kindOf="original">peen</FORM></M>
        </W>
        <W id="3_S_456_W1"><FORM kindOf="original">pai'ici?</FORM></W>
    </S>
</TEXT>"""
    xml_dir = tmp_path / "xml"
    xml_dir.mkdir()
    (xml_dir / "a.xml").write_text(sample, encoding="utf-8")
    for _ in range(2):    # idempotent
        assert mu.main(["--xml_dir", str(xml_dir), "--placeholders", str(tmp_path / "none.tsv")]) == 0
    ids = {e.get("id"): e for e in ET.parse(xml_dir / "a.xml").getroot().iter() if e.get("id")}
    assert _inner(ids["3_S_456"].find("FORM")) == "<UNCLEAR />karapeenkasu pai'ici?"
    assert _inner(ids["3_S_456"].find("PHON")) == "<UNCLEAR />ka[r|ɾ]apeenkasu paiʔiʦi"
    assert _inner(ids["3_S_456_W0"].find("FORM")) == "<UNCLEAR />kara-peen=kasu"
    assert _inner(ids["3_S_456_W0M0"].find("PHON")) == "<UNCLEAR />ka[r|ɾ]a"
    assert _inner(ids["3_S_456_W0M1"].find("FORM")) == "peen"


def test_untranscribed_word_forms_are_bare(sentences):
    bad = [(w.get("id"), _inner(f)) for s in sentences for w in s.findall("W") for f in w.findall("FORM")
           if f.find("UNCLEAR") is not None and not re.search(r"[^\W_]", "".join(f.itertext()))
           and _inner(f) != "<UNCLEAR />"]
    assert bad == [], f"{len(bad)} word FORM(s) of an untranscribed word are not a bare <UNCLEAR/>, e.g. {bad[:5]}"


def test_sentence_forms_keep_punctuation(sentences):
    s = next(s for s in sentences if s.get("id") == "SaiNr-holiday_kalaeh a _oemaw_S_78")
    assert _inner(s.find("FORM")) == "oh, isaa baiw ka isaa sipatabir <UNCLEAR />, si'aelen saboeh."


def test_x_words_with_a_real_gloss_have_an_unclear_form(sentences):
    words = {w.get("id"): w for s in sentences for w in s.findall("W") if w.get("id") in HELD}
    assert set(words) == set(HELD)
    for wid, w in words.items():
        assert [_inner(f) for f in w.findall("FORM")] == ["<UNCLEAR />"] * len(w.findall("FORM")) != [], wid
        assert w.findall("M"), wid                                        # morphemes kept


def test_x_part_of_a_word_published(sentences):
    words = {w.get("id"): w for s in sentences for w in s.findall("W") if w.get("id") in PARTIAL_X}
    assert set(words) == set(PARTIAL_X)
    for wid, form in PARTIAL_X.items():
        assert [_inner(f) for f in words[wid].findall("FORM")] == [form, form], wid
    s300 = next(s for s in sentences if s.get("id") == "sdqCon-dialog5_dakis_takun 2020s_S_300")
    assert [_inner(f) for f in s300.findall("FORM")] == ["我的<UNCLEAR />在<UNCLEAR />那邊"] * 2

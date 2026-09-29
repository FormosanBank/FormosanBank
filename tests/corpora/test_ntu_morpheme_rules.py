"""NTU morpheme rules ruled by the maintainer on 2026-09-28.

* Punctuation-only segments (drop_punctuation_morphemes.py): an unglossed one is
  deleted; a glossed one, where there are fewer glosses than segments, is
  deleted and its gloss shifted onto the next segment; with no segment after
  it, escalate.
* Unreconcilable morphemes (apply_prune_and_mirror.py): rebuilt per word from
  the word's own segmentation, with no glosses. Nothing is copied from another
  word. A glossed one-morpheme word keeps its own M.
* A word left bare by a gloss-shift repair (borrow_shift_blank_glosses.py)
  borrows a gloss only from the same language, only on one-sided evidence, and
  says so in a notes attribute.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pytest
from lxml import etree

CODEDOCS = (Path(__file__).resolve().parents[2]
            / "Corpora" / "NTUFormosanCorpus" / "CodeAndDocs")
sys.path.insert(0, str(CODEDOCS / "pipeline"))

import apply_prune_and_mirror as apm  # noqa: E402
import drop_punctuation_morphemes as dpm  # noqa: E402

XL = "{http://www.w3.org/XML/1998/namespace}lang"


def M(form, eng="", zho=""):
    t = "".join(f'<TRANSL xml:lang="{l}">{g}</TRANSL>' for l, g in (("eng", eng), ("zho", zho)) if g)
    return f'<M><FORM kindOf="original">{form}</FORM>{t}</M>'


def W(form, *ms, eng="", zho=""):
    t = "".join(f'<TRANSL xml:lang="{l}">{g}</TRANSL>' for l, g in (("eng", eng), ("zho", zho)) if g)
    return f'<W id="w"><FORM kindOf="original">{form}</FORM>{t}{"".join(ms)}</W>'


def parse(xml):
    return etree.fromstring(f'<root xmlns:xml="http://www.w3.org/XML/1998/namespace">{xml}</root>')[0]


def m_view(w):
    return [(apm.form_text(m), next((t.text for t in m.findall("TRANSL") if t.get(XL) == "eng"), None))
            for m in w.findall("M")]


# ------------------------------------------------------------ punctuation segments

def test_unglossed_punctuation_segment_is_deleted():
    w = parse(W("ta-,", M("ta", "LOC"), M(",")))
    assert dpm.repair_word(w, Counter(), [])
    assert m_view(w) == [("ta", "LOC")]


def test_glossed_punctuation_segment_hands_its_gloss_to_the_next_segment():
    w = parse(W(".-ta-an", M(".", "LOC"), M("ta", "see"), M("an")))
    assert dpm.repair_word(w, Counter(), [])
    assert m_view(w) == [("ta", "LOC"), ("an", "see")]


def test_glossed_final_punctuation_segment_is_escalated():
    esc = []
    w = parse(W("ta-.", M("ta"), M(".", "LOC")))
    assert not dpm.repair_word(w, Counter(), esc)
    assert esc and "no segment follows" in esc[0]["reason"]
    assert m_view(w) == [("ta", None), (".", "LOC")]


def test_punctuation_segment_when_every_segment_is_glossed_is_escalated():
    esc = []
    w = parse(W(".-ta", M(".", "LOC"), M("ta", "see")))
    assert not dpm.repair_word(w, Counter(), esc)
    assert "every segment is glossed" in esc[0]["reason"]


def test_a_clitic_whose_host_was_cut_off_keeps_its_boundary():
    """'na=,' (IRR=, its host cut off): the builder writes Ms 'na' and ','.
    Deleting ',' must leave 'na=' -- the corpus's form for a hostless clitic --
    or no M carries the W's '=' (V066, HARD). 12 Stories words hit this."""
    stats = Counter()
    w = parse(W("na=,", M("na", "IRR"), M(","), eng="IRR="))
    assert dpm.repair_word(w, stats, [])
    assert m_view(w) == [("na=", "IRR")]
    assert dpm.separators_before("na=,") == ["", "="]


def test_a_hyphen_before_the_punctuation_is_not_carried_over():
    w = parse(W("ta-,", M("ta", "LOC"), M(",")))
    assert dpm.repair_word(w, Counter(), [])
    assert m_view(w) == [("ta", "LOC")]


def test_the_boundary_is_kept_when_the_gloss_is_shifted_too():
    w = parse(W("x=.-ta-an", M("x"), M(".", "LOC"), M("ta", "see"), M("an")))
    assert dpm.repair_word(w, Counter(), [])
    assert m_view(w) == [("x=", None), ("ta", "LOC"), ("an", "see")]


def test_an_empty_form_shell_is_not_punctuation():
    """A form-less M is a shell from a surplus gloss piece; prune owns it."""
    esc = []
    w = parse(W("gi,", M("gi,", "CONJ"), M("", "LF")))
    assert not dpm.repair_word(w, Counter(), esc)
    assert esc == [] and len(w.findall("M")) == 2


def test_one_morpheme_word_is_not_touched():
    w = parse(W(",", M(",", "COMMA")))
    assert not dpm.repair_word(w, Counter(), [])


def test_the_absorbing_segment_ends_with_one_gloss_per_language():
    w = parse(W(".-ta", M(".", "LOC", "處格"), '<M><FORM kindOf="original">ta</FORM>'
                                               '<TRANSL xml:lang="eng">_</TRANSL></M>'))
    assert dpm.repair_word(w, Counter(), [])
    langs = [t.get(XL) for t in w.find("M").findall("TRANSL")]
    assert sorted(langs) == ["eng", "zho"]


# ------------------------------------------------------------ prune, per word

def S(form, *ws):
    return parse(f'<S id="s"><FORM kindOf="original">{form}</FORM>{"".join(ws)}</S>')


def test_only_the_unreconcilable_word_is_rebuilt_and_without_glosses():
    s = S("ku rakiyasanmu",
          W("ku", M("ku", "NOM"), eng="NOM"),
          W("rakiyas-an=mu", M("rakiyas", "climb"), M("an", "LF"), eng="climb-LF=1SG.GEN"))
    stats = Counter()
    assert apm.prune(s, stats)
    ku, verb = s.findall("W")
    assert m_view(ku) == [("ku", "NOM")]                      # untouched
    assert m_view(verb) == [("rakiyas", None), ("an", None), ("=mu", None)]   # clitic keeps '=' (V066)


def test_a_one_piece_word_with_a_multi_piece_gloss_gets_no_manufactured_m():
    s = S("ku", W("ku", M("ku", "climb"), M("", "LF"), eng="climb-LF"))
    apm.prune(s, Counter())
    assert s.find("W").findall("M") == []


def test_a_segmented_word_with_no_ms_gets_its_own_segmentation():
    s = S("maki", W("ma-ki", eng="AF-stay"))
    apm.prune(s, Counter())
    assert m_view(s.find("W")) == [("ma", None), ("ki", None)]


def test_no_morpheme_is_ever_copied_from_another_word():
    """The old donor path would have given 'ku' another word's glossed M."""
    assert not hasattr(apm, "collect_donors")
    s = S("ku", W("ku", M("ku", "climb"), M("", "LF"), eng="climb-LF"))
    apm.prune(s, Counter())
    assert all(not m.findall("TRANSL") for m in s.iter("M"))


def test_word_tier_still_withdrawn_when_it_does_not_account_for_the_sentence():
    s = S("su wahi", W("ulaqi", M("ulaqi", "child"), eng="child"))
    apm.prune(s, Counter())
    assert s.findall("W") == []


# ------------------------------------------------------------ borrowing for a shift blank

def _mini_corpus(tmp_path, other_ku: list):
    cd = tmp_path / "cd"
    (cd / "story" / "Atayal_X").mkdir(parents=True)
    rec = [7, {"gloss": [["kuing", "1SG.NEU", "1SG.中性格"], ["ku", "in", "在"],
                         ["nian", "house", "房子"], ["ragiax.", "", ""]], "s_end": True}]
    (cd / "story" / "Atayal_X" / "st.json").write_text(json.dumps({"glosses": [rec]}, ensure_ascii=False),
                                                         encoding="utf-8")
    sys.path.insert(0, str(CODEDOCS / "pipeline"))
    import gloss_shift as gs
    table = tmp_path / "t.tsv"
    row = {f: "" for f in gs.TABLE_FIELDS}
    row.update(source_file="story/Atayal_X/st.json", record_ids="7",
               record_sha256=gs.record_digest([rec]), tier="gloss", op="shift_right",
               i="1", j="3", status="accepted")
    table.write_text("\t".join(gs.TABLE_FIELDS) + "\n" + "\t".join(row[f] for f in gs.TABLE_FIELDS) + "\n",
                     encoding="utf-8")
    # The XML as the builder would emit it with the repair applied: ku bare.
    xml = tmp_path / "xml" / "Atayal"
    xml.mkdir(parents=True)
    words = ('<W id="a"><FORM kindOf="original">kuing</FORM><TRANSL xml:lang="eng">1SG.NEU</TRANSL></W>'
             '<W id="b"><FORM kindOf="original">ku</FORM><M id="bM0"><FORM kindOf="original">ku</FORM></M></W>'
             '<W id="c"><FORM kindOf="original">nian</FORM><TRANSL xml:lang="eng">in</TRANSL></W>')
    others = "".join(f'<S id="st_S_{100 + k}"><FORM kindOf="original">ku</FORM>'
                     f'<W id="o{k}"><FORM kindOf="original">ku</FORM><TRANSL xml:lang="eng">{g}</TRANSL></W></S>'
                     for k, g in enumerate(other_ku))
    (xml / "a.xml").write_text(f'<?xml version="1.0"?><TEXT id="t" xml:lang="tay">'
                               f'<S id="st_S_7"><FORM kindOf="original">kuing ku nian</FORM>{words}</S>'
                               f'{others}</TEXT>', encoding="utf-8")
    return cd, table, xml.parent


def _run_borrow(monkeypatch, cd, table, xmldir, tmp_path):
    monkeypatch.setenv("NTU_GLOSS_SHIFT_STATUSES", "accepted")
    import borrow_shift_blank_glosses as b
    monkeypatch.setattr(sys, "argv", ["b", "--xml_dir", str(xmldir), "--codedocs", str(cd),
                                      "--table", str(table), "--report", str(tmp_path / "r.tsv")])
    b.main()
    root = etree.parse(str(xmldir / "Atayal" / "a.xml")).getroot()
    return root.find(".//W[@id='b']"), (tmp_path / "r.tsv").read_text(encoding="utf-8")


def test_a_shift_blank_borrows_a_one_sided_same_language_gloss(tmp_path, monkeypatch):
    cd, table, xmldir = _mini_corpus(tmp_path, ["NOM"] * 9 + ["FS"])
    w, report = _run_borrow(monkeypatch, cd, table, xmldir, tmp_path)
    t = w.find("TRANSL")
    assert t.text == "NOM" and "borrowed" in t.get("notes")
    assert w.find("M/TRANSL").text == "NOM"          # the mirror M gets it too
    assert "borrowed 'NOM' (9/9)" in report          # FS is a placeholder, not evidence


def test_split_evidence_is_reported_not_borrowed(tmp_path, monkeypatch):
    cd, table, xmldir = _mini_corpus(tmp_path, ["NOM"] * 5 + ["in"] * 4)
    w, report = _run_borrow(monkeypatch, cd, table, xmldir, tmp_path)
    assert w.find("TRANSL") is None
    assert "not borrowed" in report


def test_blanks_are_found_through_chained_rows_over_overlapping_records(tmp_path):
    """Two rows on one sentence, the second over a subset of the first's
    records: the blanks must be computed on the composed result."""
    import borrow_shift_blank_glosses as b
    import gloss_shift as gs
    cd = tmp_path / "cd"
    (cd / "story" / "Kanakanavu_X").mkdir(parents=True)
    recs = [[1, {"gloss": [["a", "", ""], ["b", "X", "甲"]], "s_end": False}],
            [2, {"gloss": [["c", "Y", "乙"], ["d", "", ""]], "s_end": True}]]
    (cd / "story" / "Kanakanavu_X" / "st.json").write_text(json.dumps({"glosses": recs}, ensure_ascii=False),
                                                             encoding="utf-8")
    row = lambda **kw: {**{f: "" for f in gs.TABLE_FIELDS}, "source_file": "story/Kanakanavu_X/st.json",
                        "tier": "gloss", "status": "accepted", **kw}
    rows = [row(record_ids="1+2", record_sha256=gs.record_digest(recs), op="shift_left", i="0", j="2"),
            row(record_ids="2", record_sha256=gs.record_digest([recs[1]]), op="shift_right", i="0", j="1")]
    blanks = b.created_blanks(cd, rows)
    # after both rows: a=X, b=Y, c blank (was Y), d blank -> c is a shift blank in both columns
    assert sorted(blanks) == [("Kanakanavu", "st_S_1", "c", "eng"), ("Kanakanavu", "st_S_1", "c", "zho")]


def test_detector_skips_records_replaced_whole_by_p2_source_repairs():
    import find_gloss_shifts as fgs
    replaced = fgs.replaced_records(CODEDOCS)
    assert ("grammar/Kanakanavu_Kanakanavu/ap1.json", "78") in replaced


# ------------------------------------------------------------ rulings of 2026-09-29

def test_one_letter_bracket_markers_are_stripped_but_code_switch_tags_and_infixes_kept():
    import pipeline_stories as ps
    import pipeline_sentences as pse
    for strip in (ps.step5_strip_markup, pse.step5_strip_markup):
        assert strip("<A")[0] == "" and strip("M>")[0] == "" and strip("<X<A")[0] == ""
        assert strip("‘nay==(0.6)A>X>,_")[0] == "‘nay,"          # glued to a word
        assert strip("<L2Jding’ua")[0] == "ding’ua"               # code-switch tag: as before
        assert strip("s<en>aqay")[0] == "s<en>aqay"               # infix kept
        assert strip("<AF>climb", gloss=True)[0] == "<AF>climb"   # glosses untouched


def test_a_bc_restoration_stops_the_build_if_the_source_changed():
    from pipeline_grammar import apply_cell_restorations
    table = {"story/X/a.json": [(7, 0, 1, "M", "BC")]}
    recs = [[7, {"gloss": [["m", "M", "M"]]}]]
    assert apply_cell_restorations(recs, "story/X/a.json", table, {})[0][1]["gloss"][0][1] == "BC"
    with pytest.raises(RuntimeError, match="source drifted"):
        apply_cell_restorations([[7, {"gloss": [["m", "OH", "OH"]]}]], "story/X/a.json", table, {})

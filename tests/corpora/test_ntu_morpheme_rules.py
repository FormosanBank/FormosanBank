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


def test_each_gloss_goes_to_the_slot_of_its_own_language():
    """Found reviewing 2026-09-30: the old test (any Han in the English slot,
    none in the Chinese one) missed a cell with one stray piece of the other
    language, a Chinese gloss written in both slots, and a lone English gloss."""
    from pipeline_grammar import step1_realign
    assert step1_realign("IRR=go-處格", "非實現=移動-在") == ("非實現=移動-在", "IRR=go-處格")   # 34_S_8
    assert step1_realign("鉛", "鉛") == ("鉛", "")                                         # English slot emptied
    assert step1_realign("bring-PF", "") == ("", "bring-PF")                               # lone English
    assert step1_realign("<RED>-go", "") == ("", "<RED>-go")
    assert step1_realign("go", "去") == ("去", "go")                                        # whole-row swap, as before
    # a piece is never moved on its own, only whole words (maintainer, 2026-09-30)
    assert step1_realign("說-no.wonder=知識詞", "say-難怪=EVI") == ("說-no.wonder=知識詞", "say-難怪=EVI")
    # left alone: already right, a shared code, a name, a mostly-Chinese cell
    for z, e in [("主格", "NOM"), ("DM", "DM"), ("Saupu", "_"), ("PN", ""), ("長期-坐", "whole.time-坐"), ("3SG.屬格", "3SG.GEN")]:
        assert step1_realign(z, e) == (z, e), (z, e)


def test_a_reversal_against_its_line_needs_a_run_of_three_or_unmixed_glosses():
    """Maintainer, 2026-09-30: an isolated reversal (or a run of 2) is swapped
    only if neither gloss mixes the scripts; otherwise it takes a run of 3. A
    reversal is a word whose column order is the opposite of its line's."""
    from pipeline_grammar import step1_realign_sentence as realign
    ok, mixed = ("主格", "NOM"), ("IRR=go-處格", "非實現=移動-在")     # Chinese first; English first, mixed
    # an English-first line is the line's own order: every word exchanged
    assert realign([("NOM", "主格"), ("3SG.NOM", "3SG.主格")]) == [ok, ("3SG.主格", "3SG.NOM")]
    # 3.json record 22 (Kanakanavu): two against two, no majority -- each word by its own glosses
    line = [("CAUS-good-IMP", "使役-好-祈使"), ("水瓢", "bailer"), ("IRR", "非實現"), ("主焦-掉", "AF-fall")]
    assert realign(line) == [("使役-好-祈使", "CAUS-good-IMP"), ("水瓢", "bailer"),
                             ("非實現", "IRR"), ("主焦-掉", "AF-fall")]
    assert realign([ok, ok, mixed])[2] == mixed                                   # isolated, mixed: follows its line
    assert realign([ok, ok, ("NOM", "主格")])[2] == ok                             # isolated, unmixed: exchanged
    assert realign([ok] * 4 + [mixed, ("NOM", "主格"), ("go", "去")])[4] == mixed[::-1]   # run of 3
    assert realign([ok] * 5 + [mixed, ("NOM", "主格"), ok, ("go", "去")])[5] == mixed      # a word in line order ends a run
    assert realign([ok] * 4 + [mixed, ("", ""), ("NOM", "主格"), ("go", "去")])[4] == mixed[::-1]  # a bare word does not
    # English-first line, one word written Chinese first. A label such as 3SG in the
    # Chinese gloss is not mixing (maintainer, 2026-09-30): it goes to its own slots.
    eng_first = [("NOM", "主格"), ("go", "去"), ("see", "看")]
    assert realign(eng_first + [("3SG.主格", "3SG.NOM")])[3] == ("3SG.主格", "3SG.NOM")
    # an English word in the Chinese gloss is mixing, but the English itself is clean, so the
    # word goes to its own slots (maintainer, 2026-09-30, "Use the alternative": kavay)
    assert realign(eng_first + [("that.可見.遠指", "that.VIS.DIST")])[3] == ("that.可見.遠指", "that.VIS.DIST")
    # one crossed piece: exchanged, then to its own slots (3_S_28)
    assert realign([ok, ok, ("放-受焦=1SG.GEN", "put-PF=1SG.屬格")])[2] == ("放-受焦=1SG.屬格", "put-PF=1SG.GEN")
    # a Chinese piece in the English with no English counterpart to exchange: still follows its line
    assert realign([ok, ok, mixed])[2] == mixed
    assert realign([("鉛", "鉛")]) == [("鉛", "")]                                   # duplicate: not a move


def test_one_crossed_piece_is_exchanged_only_if_that_cleans_both_glosses():
    from pipeline_grammar import step1_realign_sentence as realign
    assert realign([("說-no.wonder=知識詞", "say-難怪=EVI")]) == [("說-難怪=知識詞", "say-no.wonder=EVI")]
    two = ("去-no.wonder=EVI-看-吃", "go-難怪=知識詞-see-eat")                  # two pieces crossed: left alone
    assert realign([("主格", "NOM"), two]) == [("主格", "NOM"), two]
    # would leave an English word in the Chinese gloss
    assert realign([("說-no.wonder=知識詞.that", "say-難怪=EVI")]) == [("說-no.wonder=知識詞.that", "say-難怪=EVI")]
    # a label in the crossed piece is fine (3_S_189 koo=pa=maku, once in its own slots)
    assert realign([("否定=持續=1SG.GEN", "NEG=CONT=1SG.屬格")]) == [("否定=持續=1SG.屬格", "NEG=CONT=1SG.GEN")]


def test_a_hyphen_inside_an_infix_bracket_joins_two_infixes():
    """Maintainer, 2026-09-30: '<in-i>' glossed '<PFV-PFV>' is two infixes."""
    from pipeline_grammar import SPLIT, _gloss_pieces, morpheme_count
    from utils import expand_infixes
    assert SPLIT.split("la<in-i>haib-an") == ["la<in-i>haib", "an"]
    assert morpheme_count("la<in-i>haib-an") == _gloss_pieces("<PFV-PFV>pass-LF") == 4
    assert apm.segment_from_form("la<in-i>haib-an") == ["-in-", "-i-", "lahaib", "an"]
    assert expand_infixes("la<in-i>haib", "<PFV-PFV>pass", "<完成貌-完成貌>經過") == [
        ("<in>", "<PFV>", "<完成貌>"), ("<i>", "<PFV>", "<完成貌>"), ("la-haib", "pass", "經過")]
    # a gloss bracket that does not split the same way keeps the bracket whole
    assert expand_infixes("la<in-i>haib", "<PFV>pass", "<完成貌>經過")[0] == ("<in-i>", "<PFV>", "<完成貌>")
    # and the later notation step converts each one to '-X-' (V067), reading the word the same way
    import convert_infix_notation as cin
    from lxml import etree
    m = etree.fromstring('<M><FORM kindOf="original">&lt;in&gt;</FORM></M>')
    assert cin._is_infix_m(m, "la<in-i>haib-an") is None


def test_the_same_english_in_both_slots_empties_the_chinese_slot():
    # Maintainer, 2026-09-30, on the 49 such words: "drop the copy". Labels,
    # placeholders and copies of the word itself are not English glosses.
    from pipeline_grammar import step1_realign_sentence as realign
    pairs = [("exhort-go", "exhort-go"), ("DM", "DM"), ("la", "la"), ("XX", "XX"), ("鉛", "鉛")]
    out = realign(pairs, forms=["ta-ila", "a", "la", "ma", "x"])
    assert out == [("", "exhort-go"), ("DM", "DM"), ("la", "la"), ("XX", "XX"), ("鉛", "")]
    assert realign(pairs[:1]) == [("exhort-go", "exhort-go")]      # no forms, no rule


def test_a_non_verbal_event_split_across_two_rows_is_dropped_whole():
    # Maintainer, 2026-09-30: "treat both halves as a mark".
    sys.path.insert(0, str(CODEDOCS / "pipeline"))
    import gloss_shift as gs
    from pipeline_stories import drop_split_events
    rows = [["...", "", ""], ["(PHONE", "_", "_"], ["RINGS)._", "", ""], ["at", "then", "然後"],
            ["((CLEAR", "", ""], ["THROAT)).\\", "", ""]]
    assert drop_split_events(rows, {}) == [["...", "", ""], ["._", "", ""], ["at", "then", "然後"], [".\\", "", ""]]
    # the transcript line writes the same event as two tokens
    assert drop_split_events(["..", "(WHITE", "NOISE).\\"], {}, tokens=True) == ["..", ".\\"]
    assert drop_split_events(["(COUGH)", "at"], {}, tokens=True) == ["(COUGH)", "at"]
    assert not any(gs.is_word(f) for f in ("(PHONE", "RINGS)._", "((CLEARS", "THROAT))"))


def test_x_glosses_become_x_and_mis_cased_labels_are_capitalized():
    # Maintainer, 2026-10-14: x/xx/XX (and XXX/XXXX) -> X; a gloss with a capital
    # letter that is an attested gloss (20+ in NTU) when fully capitalized -> capitals.
    from pipeline_grammar import normalize_gloss_cell as n
    assert [n(v) for v in ("x", "xx", "XX", "XXX", "XXXX", "X")] == ["X"] * 6
    # card xlong (2026-10-14, "yes, all of them"): runs of five or more, and [XXXX]
    assert [n(v) for v in ("XXXXX", "XXXXXXXX", "[XXXX]")] == ["X"] * 3
    assert n("[XX]") == "[XX]" and n("XXXXa") == "XXXXa"   # not covered by either ruling
    assert n("FiL") == "FIL" and n("Ncm") == "Ncm"     # NCM is not attested 20 times
    assert n("fil") == "fil"                           # no capital letter: left alone
    assert n("Han") == "Han"                           # held back: the ethnonym (payrange 漢人)


def test_a_stray_punctuation_token_is_joined_only_when_that_lines_the_words_up():
    from xml.etree import ElementTree as ET
    from pipeline_grammar import aligned_or_joined
    s = ET.fromstring('<S><FORM kindOf="original">gei ta chuanzhe .</FORM></S>')
    assert aligned_or_joined(s, ["gei", "ta", "chuanzhe"])
    assert s.find("FORM").text == "gei ta chuanzhe."
    s = ET.fromstring('<S><FORM kindOf="original">gei ta chuanzhe .</FORM></S>')
    assert not aligned_or_joined(s, ["gei", "chuanzhe"])
    assert s.find("FORM").text == "gei ta chuanzhe ."     # left as it was


def test_a_translation_wrapped_whole_in_one_quote_pair_is_unwrapped():
    # Maintainer, 2026-10-14: the four Saisiyat stories' habitual quotes come off
    # the English, and holiday's off the Chinese ("the same rules").
    from pipeline_grammar import unwrap_translation as u
    assert u('" dog also came to see ."') == "dog also came to see ."
    assert u('"The dog fell down".') == "The dog fell down."
    assert u("「從墓地帶回祭品。」") == "從墓地帶回祭品。"
    assert u('"A" and "B"') == '"A" and "B"'                 # two quotations: left alone
    assert u("「他說『走』」") == "「他說『走』」"              # a quotation inside: left alone
    assert u('He said "go".') == 'He said "go".'


def test_the_iu_terminal_is_stripped_once_the_lengthening_is_gone():
    # kkvNr_millet_Muu S_138: 'putu<vaka>va^kaan/==' left a '/' in the morpheme
    # the infix expansion built (V121).
    from pipeline_stories import step5_strip_markup
    assert step5_strip_markup("putu<vaka>va^kaan/==")[0] == "putu<vaka>vakaan"
    assert step5_strip_markup("/")[0] == "/"          # the split separator stays


def test_a_record_without_a_transcript_line_contributes_its_words():
    # Review page round 6, card noori: "apply the rule".
    from pipeline_stories import _merge
    rec = lambda i, ori, rows, end=False: [i, {"ori": ori, "gloss": rows, "s_end": end}]
    g = [rec(9, ["sa", "ka", "maungu"], [["sa", "", ""], ["ka", "", ""], ["maungu", "", ""]]),
         rec(10, [], [["...", "", ""], ["sa-pece", "", ""], ["<XkikayX>,_", "", ""]]),
         rec(11, ["..", "(COUGHS)"], [], True)]
    assert _merge(g, {})[1]["ori"] == ["sa", "ka", "maungu", "sapece", "kikay,", "..", "(COUGHS)"]
    # a line of annotations and labels alone is not a transcript line: nothing changes
    g = [rec(1, ["M:", "[@@]"], []), rec(2, [], [["ho", "", ""]], True)]
    assert _merge(g, {})[1]["ori"] == ["M:", "[@@]"]


def test_a_gloss_keeps_its_language_label_and_loses_other_bracketed_notes():
    # Review page round 7, card codeswitch: "Let's rewrite them as [Mandarin]
    # and [Japanese] though." Every other bracketed note still comes off.
    from pipeline_stories import step5_strip_markup
    gloss = lambda s: step5_strip_markup(s, gloss=True)[0]
    assert gloss("[Mandarin]") == "[Mandarin]"
    assert gloss("[Mandarin]matter") == "[Mandarin]matter"
    assert gloss("anyway[Japanese]") == "anyway[Japanese]"
    assert gloss("[Hakka]宣布") == "[Hakka]宣布"
    assert gloss("[Man]") == "" and gloss("[TVH1][u2]talk") == "talk"
    assert step5_strip_markup("[Mandarin]")[0] == "Mandarin"   # a form is not a gloss


def test_a_code_switched_word_without_english_is_glossed_with_its_language():
    # Review page round 9, cards unglossed ("approve") and cs-zho ("itself").
    sys.path.insert(0, str(CODEDOCS / "scripts"))
    from utils import code_switch_gloss, l2_letter
    from split_optional_parentheticals import _strip_parens
    assert l2_letter("<L2JkikayL2J>") == "J" and l2_letter("wei") is None
    assert code_switch_gloss("那我就", None, "", "") == ("那我就", "(Mandarin)")
    assert code_switch_gloss("wei", "M", "", "") == ("", "(Mandarin)")
    assert code_switch_gloss("明天", None, "明天", "tomorrow") == ("明天", "tomorrow")
    assert code_switch_gloss("cayna", "T", "", "") == ("", "")      # a tag the ruling did not name
    assert _strip_parens("(Mandarin)") == "(Mandarin)" and _strip_parens("(較好)") == "較好"


def test_a_transcribers_note_leaves_the_text_and_the_marker_of_japanese_is_a_tag():
    # Round 9, cards note ("Put it in the notes attribute") and nichi ("approve").
    from pipeline_stories import _SOURCE_NOTE, step5_strip_markup
    assert _SOURCE_NOTE.fullmatch("(需再確認)") and not _SOURCE_NOTE.fullmatch("(H)")
    assert step5_strip_markup("<日wa日>,\\") == ("wa,", True)
    assert step5_strip_markup("<日")[0] == "" and step5_strip_markup("日>")[0] == ""

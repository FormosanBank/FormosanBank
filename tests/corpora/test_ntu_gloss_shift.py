"""NTU gloss-shift repair: operations move cells, never edit them.

The NTU source JSONs contain sentences whose word glosses sit one word away
from the words they belong to (docs: CodeAndDocs/pipeline/gloss_shift.py).
They are corrected at load time from gloss_shift_repairs.tsv. These tests hold
the repair machinery to its contract:

* every operation except ``fill`` only moves existing cells, and the checker
  catches one that edits;
* preconditions are enforced (a shift needs a blank to consume; apparatus rows
  are stepped over and may not carry a gloss);
* a repair is pinned to the record it was written against;
* only ``accepted`` rows take effect by default;
* on the real source, the audit's test case (Atayal hunting3_Takun S_15) ends
  with ``rakiyas-an=mu`` glossed ``climb-LF=1SG.GEN``, and the detector finds
  the clitic-absorption case (dailylife3_Tauyu S_47) without being prompted.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

CODEDOCS = (Path(__file__).resolve().parents[2]
            / "Corpora" / "NTUFormosanCorpus" / "CodeAndDocs")
sys.path.insert(0, str(CODEDOCS / "pipeline"))

import gloss_shift as gs  # noqa: E402
import find_gloss_shifts as fgs  # noqa: E402

TAKUN = "story/Atayal_Mayrinax/AtaNr-hunting3_Takun.json"
TAUYU = "story/Atayal_Mayrinax/AtaNr-dailylife3_Tauyu.json"


def rows(*cells):
    return [list(c) for c in cells]


# ------------------------------------------------------------ operations

def test_shift_right_moves_every_cell_in_the_window_one_word_right():
    before = rows(["a", "A", "甲"], ["b", "C", "丙"], ["c", "D", "丁"], ["d", "", ""])
    after = gs.apply_op(before, gs.Op("gloss", "shift_right", 1, 3))
    assert [r[1] for r in after] == ["A", "", "C", "D"]
    assert [r[2] for r in after] == ["甲", "", "丙", "丁"]
    assert [r[0] for r in after] == ["a", "b", "c", "d"]


def test_shift_steps_over_apparatus_rows():
    before = rows(["a", "X", ""], ["...(1.4)", "", ""], ["b", "", ""])
    after = gs.apply_op(before, gs.Op("col1", "shift_right", 0, 2))
    assert [r[1] for r in after] == ["", "", "X"]


def test_apparatus_carrying_a_gloss_is_refused():
    before = rows(["a", "X", ""], ["...(1.4)", "Y", ""], ["b", "", ""])
    with pytest.raises(gs.RepairError, match="apparatus"):
        gs.apply_op(before, gs.Op("col1", "shift_right", 0, 2))


def test_shift_right_needs_a_blank_to_consume():
    before = rows(["a", "A", ""], ["b", "B", ""])
    with pytest.raises(gs.RepairError, match="blank"):
        gs.apply_op(before, gs.Op("col1", "shift_right", 0, 1))


def test_shift_left_removes_a_spurious_blank():
    before = rows(["a", "", ""], ["b", "A", ""], ["c", "B", ""])
    after = gs.apply_op(before, gs.Op("col1", "shift_left", 0, 2))
    assert [r[1] for r in after] == ["A", "B", ""]


def test_split_cuts_a_fused_gloss_and_drops_only_the_separator():
    before = rows(["al-an", "take-LF=1EPL.GEN", ""], ["niam", "ACC", ""],
                  ["su", "chief", ""], ["tumuk", "", ""])
    op = gs.Op("col1", "split", 0, 3, sep="=")
    after = gs.apply_op(before, op)
    assert [r[1] for r in after] == ["take-LF", "1EPL.GEN", "ACC", "chief"]
    gs.check_moved_not_edited(before, after, op)


def test_merge_rejoins_a_gloss_cut_at_a_marker():
    before = rows(["a", "take-LF", ""], ["b", "=1SG", ""], ["c", "ACC", ""], ["d", "x", ""])
    op = gs.Op("col1", "merge", 0, 3, sep="=")
    after = gs.apply_op(before, op)
    assert [r[1] for r in after] == ["take-LF=1SG", "ACC", "x", ""]
    gs.check_moved_not_edited(before, after, op)


def test_merge_without_a_marker_at_the_seam_is_refused():
    before = rows(["a", "take", ""], ["b", "LF", ""])
    with pytest.raises(gs.RepairError, match="seam"):
        gs.apply_op(before, gs.Op("col1", "merge", 0, 1, sep="="))


def test_swap_exchanges_the_two_gloss_columns():
    before = rows(["a", "甲", "A"], ["b", "乙", "B"])
    after = gs.apply_op(before, gs.Op("gloss", "swap", 0, 1))
    assert [r[1:] for r in after] == [["A", "甲"], ["B", "乙"]]


def test_fill_needs_a_reviewer():
    before = rows(["a", "", ""])
    with pytest.raises(gs.RepairError, match="reviewer"):
        gs.apply_op(before, gs.Op("col1", "fill", 0, 0, value="NOM"))
    after = gs.apply_op(before, gs.Op("col1", "fill", 0, 0, value="NOM", reviewer="JKH"))
    assert after[0][1] == "NOM"


def test_the_invariant_catches_an_edit():
    before = rows(["a", "A", ""], ["b", "", ""])
    edited = rows(["a", "", ""], ["b", "Z", ""])
    with pytest.raises(gs.RepairError, match="content changed"):
        gs.check_moved_not_edited(before, edited, gs.Op("col1", "shift_right", 0, 1))


def test_the_invariant_catches_a_column_the_op_should_not_touch():
    before = rows(["a", "A", "甲"], ["b", "", ""])
    after = rows(["a", "", "甲"], ["b", "A", "乙"])
    with pytest.raises(gs.RepairError, match="column 2 changed"):
        gs.check_moved_not_edited(before, after, gs.Op("col1", "shift_right", 0, 1))


def test_speaker_labels_and_lone_code_switch_tags_are_apparatus():
    assert not gs.is_word("F:")
    assert not gs.is_word("<L2J")
    assert not gs.is_word("...(1.4)")
    assert gs.is_word("rakiyas-an=mu.\\")


# ------------------------------------------------------------ evidence

def test_a_word_never_vouches_for_its_own_gloss():
    lex = gs.Lexicon()
    sentence = rows(["ku", "NOM", "主格"])
    lex.add_rows(sentence)
    assert gs.score(sentence, lex)["attested"] == 2
    assert gs.score(sentence, lex.without(sentence))["attested"] == 0


# ------------------------------------------------------------ the table

def _table_row(tmp_path, **over):
    base = {f: "" for f in gs.TABLE_FIELDS}
    base.update(over)
    path = tmp_path / "t.tsv"
    path.write_text("\t".join(gs.TABLE_FIELDS) + "\n"
                    + "\t".join(str(base[f]) for f in gs.TABLE_FIELDS) + "\n", encoding="utf-8")
    return path


def _takun_15():
    recs = gs.records_of(CODEDOCS / TAKUN)
    return recs, next(r for r in recs if r[0] == 15)


def test_only_accepted_rows_apply_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv("NTU_GLOSS_SHIFT_STATUSES", raising=False)
    path = _table_row(tmp_path, source_file=TAKUN, record_ids="15", status="proposed")
    assert gs.load_table(path) == []
    monkeypatch.setenv("NTU_GLOSS_SHIFT_STATUSES", "accepted,proposed")
    assert len(gs.load_table(path)) == 1


def test_audit_test_case_lands_climb_lf_on_rakiyas(tmp_path):
    recs, rec = _takun_15()
    path = _table_row(tmp_path, source_file=TAKUN, record_ids="15",
                      record_sha256=gs.record_digest([rec]), tier="gloss",
                      op="shift_right", i=3, j=7, status="accepted")
    stats: dict = {}
    out = gs.apply_to_records(recs, TAKUN, gs.load_table(path, {"accepted"}), stats)
    fixed = {r[0]: r[1] for r in next(r for r in out if r[0] == 15)[1]["gloss"]}
    assert fixed["rakiyas-an=mu.\\"] == "climb-LF=1SG.GEN"
    assert fixed["ku"] == "NOM"
    assert stats["gloss-shift repairs applied"] == 1
    # The source records themselves are untouched.
    assert next(r for r in recs if r[0] == 15)[1]["gloss"][6][1] == "climb-LF=1SG.GEN"


def test_a_drifted_source_fails_the_build(tmp_path):
    recs, _ = _takun_15()
    path = _table_row(tmp_path, source_file=TAKUN, record_ids="15", record_sha256="0" * 64,
                      tier="gloss", op="shift_right", i=3, j=7, status="accepted")
    with pytest.raises(gs.RepairError, match="drifted"):
        gs.apply_to_records(recs, TAKUN, gs.load_table(path, {"accepted"}), {})


def test_the_published_table_pins_the_current_source():
    """Every row, whatever its status, still matches the record it was written for."""
    for row in gs.load_table(gs.REPAIRS_TSV, {"accepted", "proposed", "withdrawn"}):
        recs = gs.records_of(CODEDOCS / row["source_file"])
        ids = row["record_ids"].split("+")
        target = [r for r in recs if str(r[0]) in ids]
        assert gs.record_digest(target) == row["record_sha256"], row


# ------------------------------------------------------------ the detector

def test_detector_finds_the_clitic_absorption_split():
    stats = fgs.Counter()
    found = {(Path(rel).stem, group[0][0]): chain
             for rel, group, _, chain in fgs.scan(CODEDOCS, "Atayal", stats)}
    chain = found[("AtaNr-dailylife3_Tauyu", 47)]
    op = chain[0][0]
    assert (op.op, op.tier, op.sep) == ("split", "gloss", "=")
    # And it proposes nothing for a sentence whose only gap is an unglossed 'XX'.
    assert ("AtaNr-hunting3_Takun", 22) not in found


def test_chained_rows_over_overlapping_records_are_pinned_to_the_source():
    """Two rows for one sentence: the second is checked against the source, not
    against the first row's output -- which is what the detector pins."""
    recs = [[1, {"gloss": [["a", "", ""], ["b", "X", ""]], "s_end": False}],
            [2, {"gloss": [["c", "Y", ""], ["d", "", ""]], "s_end": True}]]
    both = gs.record_digest(recs)
    table = [
        {**{f: "" for f in gs.TABLE_FIELDS}, "source_file": "s.json", "record_ids": "1+2",
         "record_sha256": both, "tier": "col1", "op": "shift_left", "i": "0", "j": "2"},
        {**{f: "" for f in gs.TABLE_FIELDS}, "source_file": "s.json", "record_ids": "2",
         "record_sha256": gs.record_digest([recs[1]]), "tier": "col1", "op": "shift_right",
         "i": "0", "j": "1"},
    ]
    out = gs.apply_to_records(recs, "story/s.json", table, {})
    assert [r[1] for r in out[0][1]["gloss"]] == ["X", "Y"]
    assert [r[1] for r in out[1][1]["gloss"]] == ["", ""]
    # The source records themselves are untouched.
    assert [r[1] for r in recs[1][1]["gloss"]] == ["Y", ""]


# ------------------------------------------------------------ blast radius

def _xml(sentences: dict) -> str:
    body = "".join(
        f'<S id="{sid}"><FORM kindOf="original">{w}</FORM>'
        f'<W id="{sid}_W0"><FORM kindOf="original">{w}</FORM>'
        f'<TRANSL xml:lang="eng">{g}</TRANSL>'
        f'<M id="{sid}_W0M0"><FORM kindOf="original">{w}</FORM>'
        f'<TRANSL xml:lang="eng">{mg}</TRANSL></M></W></S>'
        for sid, (w, g, mg) in sentences.items())
    return f'<?xml version="1.0"?><TEXT id="t" xml:lang="tay">{body}</TEXT>'


def _blast(tmp_path, candidate: dict, monkeypatch):
    sys.path.insert(0, str(CODEDOCS / "qa"))
    import gloss_shift_blast_radius as br
    src = tmp_path / "cd" / "story" / "Atayal_X"
    src.mkdir(parents=True)
    (src / "st.json").write_text('{"glosses": [[1, {"gloss": [["ku", "NOM", ""]], "s_end": true}],'
                                 ' [2, {"gloss": [["su", "ACC", ""]], "s_end": true}]]}', encoding="utf-8")
    table = _table_row(tmp_path, source_file="story/Atayal_X/st.json", record_ids="1",
                       status="accepted")
    base = {"st_S_1": ("ku", "NOM", "NOM"), "st_S_2": ("su", "ACC", "ACC")}
    for name, sents in (("base", base), ("cand", {**base, **candidate})):
        d = tmp_path / name / "Atayal"
        d.mkdir(parents=True)
        (d / "a.xml").write_text(_xml(sents), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["br", "--baseline", str(tmp_path / "base"),
                                      "--candidate", str(tmp_path / "cand"),
                                      "--codedocs", str(tmp_path / "cd"), "--table", str(table),
                                      "--report", str(tmp_path / "r.md")])
    return br.main(), (tmp_path / "r.md").read_text(encoding="utf-8")


def test_blast_radius_passes_a_change_confined_to_the_target(tmp_path, monkeypatch):
    rc, report = _blast(tmp_path, {"st_S_1": ("ku", "GEN", "GEN")}, monkeypatch)
    assert rc == 0
    assert "collateral sentences changed: 0" in report


def test_blast_radius_fails_on_a_change_outside_the_target(tmp_path, monkeypatch):
    rc, report = _blast(tmp_path, {"st_S_2": ("su", "GEN", "GEN")}, monkeypatch)
    assert rc == 1
    assert "collateral sentences changed: 1" in report
    assert "| `st_S_2` | Atayal/a.xml | NO |" in report


def test_blast_radius_names_an_m_tier_only_collateral_change(tmp_path, monkeypatch):
    rc, report = _blast(tmp_path, {"st_S_2": ("su", "ACC", "NOM")}, monkeypatch)
    assert rc == 1
    assert "(1 of them only in the M tier)" in report


def test_apparatus_patterns_match_the_builders():
    """gloss_shift copies step 15's patterns; a drift would move glosses onto
    rows the build drops, or onto labels it keeps as words."""
    import pipeline_stories as ps
    for name in ("_SPEAKER", "_PUNCT_ONLY", "_PAUSE", "_NONVERBAL"):
        assert getattr(gs, name).pattern == getattr(ps, name).pattern, name
    assert not gs.is_word("D:..")
    assert not gs.is_word("P:...(0.9)")


def test_a_single_column_repair_may_not_tear_a_known_pair_apart():
    lex = gs.Lexicon()
    lex.add_rows(rows(["pistunghaz", "hide", "躲藏"], ["i", "LOC", "處格"]))
    before = rows(["pistunghaz", "hide", "躲藏"], ["i,", "", ""])
    after = gs.apply_op(before, gs.Op("col2", "shift_right", 0, 1))
    assert not gs.improves(gs.score(before, lex), gs.score(after, lex))

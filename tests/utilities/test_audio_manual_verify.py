"""Tests for QC/utilities/audio_manual_verify.py.

The interactive loop is impractical to test end-to-end (real keypresses,
real audio player). We test the discrete pure pieces:

- apply_decision: mapping single chars to verdicts and loop actions
- prepare_working_list: merging suspect rows with prior verdicts
- first_unverified_index: resume support
- load_verdicts / write_verdicts: round-trip
- main(): end-to-end driven by mocked get_keypress / player
"""
import csv
import sys
from importlib import import_module
from pathlib import Path
from unittest import mock

import pytest


@pytest.fixture
def amv_module():
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    return import_module("QC.utilities.audio_manual_verify")


def _write_suspect_csv(path: Path, rows: list[dict]) -> None:
    cols = ["lang", "sentence_id", "audio_path", "transcript", "asr_hypothesis",
            "ctc_score", "wer", "cer", "pdm_score", "word",
            "triggers", "n_triggers", "worst_pct_rank", "suspicion"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for r in rows:
            writer.writerow({c: r.get(c, "") for c in cols})


def _sample_rows(n: int = 3) -> list[dict]:
    return [
        {"lang": "ami", "sentence_id": f"S_{i}", "audio_path": f"/fake/{i}.wav",
         "transcript": f"text {i}", "asr_hypothesis": "fake",
         "triggers": "wer", "n_triggers": "1",
         "worst_pct_rank": "1.0", "suspicion": str(99 - i)}
        for i in range(n)
    ]


# -----------------------------------------------------------------------------
# apply_decision
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("key,verdict,action", [
    ("c", "correct", "advance"),
    ("w", "wrong",   "advance"),
    ("u", "unclear", "advance"),
])
def test_apply_decision_verdicts(amv_module, key, verdict, action):
    row = {"sentence_id": "S_1"}
    result = amv_module.apply_decision(row, key)
    assert result == action
    assert row.get("verdict") == verdict


def test_apply_decision_skip_advances_without_verdict(amv_module):
    row = {"sentence_id": "S_1"}
    assert amv_module.apply_decision(row, "s") == "advance"
    assert "verdict" not in row or not row["verdict"]


def test_apply_decision_play_reprompts(amv_module):
    assert amv_module.apply_decision({}, "p") == "reprompt"


def test_apply_decision_note_handler(amv_module):
    assert amv_module.apply_decision({}, "n") == "note"


def test_apply_decision_back(amv_module):
    assert amv_module.apply_decision({}, "b") == "back"


def test_apply_decision_quit(amv_module):
    assert amv_module.apply_decision({}, "q") == "quit"


def test_apply_decision_unrecognized_returns_none(amv_module):
    assert amv_module.apply_decision({}, "x") is None
    assert amv_module.apply_decision({}, "") is None


# -----------------------------------------------------------------------------
# prepare_working_list / first_unverified_index / round-trip
# -----------------------------------------------------------------------------


def test_prepare_working_list_adds_verdict_columns(amv_module):
    susp = _sample_rows(2)
    susp_fields = list(susp[0].keys())
    working, fieldnames = amv_module.prepare_working_list(susp, susp_fields, {})
    assert "verdict" in fieldnames
    assert "notes" in fieldnames
    assert all("verdict" in r for r in working)


def test_prepare_working_list_preserves_prior_verdicts(amv_module):
    susp = _sample_rows(3)
    susp_fields = list(susp[0].keys())
    existing = {"S_1": {"sentence_id": "S_1", "verdict": "correct", "notes": "ok"}}
    working, _ = amv_module.prepare_working_list(susp, susp_fields, existing)
    by_id = {r["sentence_id"]: r for r in working}
    assert by_id["S_1"]["verdict"] == "correct"
    assert by_id["S_1"]["notes"] == "ok"
    assert by_id["S_0"]["verdict"] == ""


def test_first_unverified_resumes_after_verdicts(amv_module):
    working = [
        {"sentence_id": "S_0", "verdict": "correct"},
        {"sentence_id": "S_1", "verdict": "wrong"},
        {"sentence_id": "S_2", "verdict": ""},
        {"sentence_id": "S_3", "verdict": ""},
    ]
    assert amv_module.first_unverified_index(working) == 2


def test_first_unverified_returns_zero_when_all_blank(amv_module):
    working = [{"sentence_id": "S_0", "verdict": ""}, {"sentence_id": "S_1", "verdict": ""}]
    assert amv_module.first_unverified_index(working) == 0


def test_load_then_write_round_trip(amv_module, tmp_path):
    path = tmp_path / "verdicts.csv"
    rows = [
        {"sentence_id": "S_0", "verdict": "correct", "notes": "x"},
        {"sentence_id": "S_1", "verdict": "wrong", "notes": ""},
    ]
    amv_module.write_verdicts(path, rows, ["sentence_id", "verdict", "notes"])
    existing, all_rows = amv_module.load_verdicts(path)
    assert existing.keys() == {"S_0", "S_1"}
    assert len(all_rows) == 2


# -----------------------------------------------------------------------------
# End-to-end with mocked keypresses + player
# -----------------------------------------------------------------------------


def test_main_records_correct_then_quit(amv_module, tmp_path, monkeypatch):
    susp_csv = tmp_path / "suspect_audio.csv"
    verdicts_csv = tmp_path / "verdicts.csv"
    _write_suspect_csv(susp_csv, _sample_rows(2))

    keypress_iter = iter(["c", "q"])
    monkeypatch.setattr(amv_module, "get_keypress", lambda prompt: next(keypress_iter))
    monkeypatch.setattr(amv_module, "play", lambda *a, **kw: None)
    monkeypatch.setattr(amv_module, "get_player", lambda *a, **kw: ["echo"])

    rc = amv_module.main([
        "--suspicious", str(susp_csv),
        "--verdicts", str(verdicts_csv),
        "--auto-play", "no",
    ])
    assert rc == 0
    rows = list(csv.DictReader(verdicts_csv.open()))
    assert rows[0]["verdict"] == "correct"
    assert rows[1]["verdict"] in ("", None)


def test_main_resumes_from_first_unverified(amv_module, tmp_path, monkeypatch):
    susp_csv = tmp_path / "suspect_audio.csv"
    verdicts_csv = tmp_path / "verdicts.csv"
    _write_suspect_csv(susp_csv, _sample_rows(3))

    # Pre-populate verdicts so S_0 is already done.
    amv_module.write_verdicts(verdicts_csv,
                              [{"sentence_id": "S_0", "verdict": "correct", "notes": ""}],
                              ["sentence_id", "verdict", "notes"])

    seen = []

    def fake_keypress(prompt):
        # Always quit on first call; we record what entry was shown.
        return "q"

    def fake_display(idx, total, row):
        seen.append(row["sentence_id"])

    monkeypatch.setattr(amv_module, "get_keypress", fake_keypress)
    monkeypatch.setattr(amv_module, "play", lambda *a, **kw: None)
    monkeypatch.setattr(amv_module, "get_player", lambda *a, **kw: ["echo"])
    monkeypatch.setattr(amv_module, "display", fake_display)

    amv_module.main([
        "--suspicious", str(susp_csv),
        "--verdicts", str(verdicts_csv),
        "--auto-play", "no",
    ])
    # Should have resumed at S_1 (S_0 already verified), not S_0.
    assert seen and seen[0] == "S_1"


def test_main_back_navigates_backwards(amv_module, tmp_path, monkeypatch):
    susp_csv = tmp_path / "suspect_audio.csv"
    verdicts_csv = tmp_path / "verdicts.csv"
    _write_suspect_csv(susp_csv, _sample_rows(3))

    seen = []

    def fake_display(idx, total, row):
        seen.append(row["sentence_id"])

    keypresses = iter(["c", "b", "w", "q"])  # c on S_0, then back to S_0, set wrong, quit
    monkeypatch.setattr(amv_module, "get_keypress", lambda prompt: next(keypresses))
    monkeypatch.setattr(amv_module, "play", lambda *a, **kw: None)
    monkeypatch.setattr(amv_module, "get_player", lambda *a, **kw: ["echo"])
    monkeypatch.setattr(amv_module, "display", fake_display)

    amv_module.main([
        "--suspicious", str(susp_csv),
        "--verdicts", str(verdicts_csv),
        "--auto-play", "no",
    ])
    assert seen[0] == "S_0"
    assert seen[1] == "S_1"      # advanced after "c"
    assert seen[2] == "S_0"      # back to S_0 after "b"
    final = list(csv.DictReader(verdicts_csv.open()))
    assert final[0]["verdict"] == "wrong"  # overwritten by the second decision

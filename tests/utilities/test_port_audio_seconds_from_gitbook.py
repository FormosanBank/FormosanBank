# tests/utilities/test_port_audio_seconds_from_gitbook.py
import importlib.util
from pathlib import Path


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).resolve().parents[2] / "QC" / "utilities" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


port = _load("port_audio_seconds_from_gitbook")


def _v(t_count, u_count, t_sec, u_sec):
    return {"t_count": t_count, "u_count": u_count, "t_sec": t_sec, "u_sec": u_sec}


def test_direct_match_uses_gitbook_seconds_and_counts_as_anchor():
    gitbook = {("ami", "Coastal"): _v(10391, 0, 48072.0, 0.0)}
    rows, unmatched = port.build_port_rows(gitbook, {("ami", "Coastal")})
    assert unmatched == []
    r = rows[0]
    assert r["transcribed_audio_seconds"] == 48072.0
    # count_at_compute is the GITBOOK count (what the seconds were measured against)
    assert r["transcribed_audio_count"] == 10391


def test_single_dialect_reconciliation_blank_to_language_name():
    # Gitbook leaves single-dialect dialect blank; ours uses the language name.
    gitbook = {("ckv", ""): _v(10656, 0, 47203.0, 0.0)}
    rows, unmatched = port.build_port_rows(gitbook, {("ckv", "Kavalan")})
    assert unmatched == []
    r = rows[0]
    assert (r["language"], r["dialect"]) == ("ckv", "Kavalan")  # written under OUR label
    assert r["transcribed_audio_seconds"] == 47203.0
    assert r["transcribed_audio_count"] == 10656


def test_no_single_row_fallback_when_language_is_multi_dialect():
    # pwn has >1 row on the gitbook side, so a dialect we have but the gitbook
    # lacks must NOT be force-matched — it stays unmatched (-> flagged stale).
    gitbook = {("pwn", "Central"): _v(9778, 0, 33853.0, 0.0),
               ("pwn", "Eastern"): _v(9161, 0, 36134.0, 0.0)}
    our_keys = {("pwn", "Central"), ("pwn", "Northern")}
    rows, unmatched = port.build_port_rows(gitbook, our_keys)
    matched = {(r["language"], r["dialect"]) for r in rows}
    assert ("pwn", "Central") in matched
    assert ("pwn", "Northern") in unmatched


def test_untranscribed_seconds_ported_too():
    gitbook = {("tay", "Sekolik"): _v(3014, 33, 24420.9, 10685.4)}
    rows, _ = port.build_port_rows(gitbook, {("tay", "Sekolik")})
    r = rows[0]
    assert r["untranscribed_audio_seconds"] == 10685.4
    assert r["untranscribed_audio_count"] == 33

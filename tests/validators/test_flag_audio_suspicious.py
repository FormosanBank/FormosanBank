"""Tests for QC/validation/flag_audio_suspicious.py.

These are pure-Python tests — no heavy ML deps. We hand-build a small
scores CSV with known distributions and assert that flag() picks the
expected rows.
"""
import csv
import sys
from importlib import import_module
from pathlib import Path

import pytest


@pytest.fixture
def fas_module():
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    return import_module("QC.validation.flag_audio_suspicious")


def _write_scores(tmp_path: Path, rows: list[dict]) -> Path:
    cols = ["lang", "sentence_id", "audio_path", "transcript", "asr_hypothesis",
            "ctc_score", "wer", "cer", "pdm_score", "word"]
    path = tmp_path / "scores.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in cols})
    return path


def _make_rows(n: int = 20) -> list[dict]:
    """Build n rows where higher index = worse on every metric.

    ctc_score (higher is better) → decreasing with index
    pdm_score (higher is better) → decreasing with index
    wer (lower is better) → increasing with index
    cer (lower is better) → increasing with index
    """
    out = []
    for i in range(n):
        out.append({
            "lang": "ami",
            "sentence_id": f"S_{i:02d}",
            "audio_path": f"/audio/{i}.wav",
            "transcript": f"sentence {i}",
            "asr_hypothesis": "fake",
            "ctc_score": str(1.0 - i / n),
            "pdm_score": str(1.0 - i / n),
            "wer": str(i / n),
            "cer": str(i / n),
            "word": "",
        })
    return out


def test_default_worst_5pct_keeps_5pct(fas_module, tmp_path):
    rows = fas_module.load_scores(_write_scores(tmp_path, _make_rows(20)))
    flagged = fas_module.flag(rows, worst_pct=5.0, min_agreement=1)
    # 5% of 20 = 1 (k = max(1, int(20 * 0.05))). Each metric flags the worst entry.
    # min_agreement=1 means any single-metric hit qualifies.
    assert flagged, "expected at least one flagged entry"
    # The worst-on-all-metrics row is S_19 (highest index)
    assert flagged[0]["sentence_id"] == "S_19"


def test_min_agreement_3_requires_multi_metric_hits(fas_module, tmp_path):
    rows = fas_module.load_scores(_write_scores(tmp_path, _make_rows(20)))
    flagged_loose = fas_module.flag(rows, worst_pct=5.0, min_agreement=1)
    flagged_tight = fas_module.flag(rows, worst_pct=0.5, min_agreement=3)
    # tight selector should produce ≤ rows than the loose one
    assert len(flagged_tight) <= len(flagged_loose)


def test_sorted_worst_first(fas_module, tmp_path):
    rows = fas_module.load_scores(_write_scores(tmp_path, _make_rows(30)))
    flagged = fas_module.flag(rows, worst_pct=20.0, min_agreement=1)
    suspicions = [r["suspicion"] for r in flagged]
    assert suspicions == sorted(suspicions, reverse=True)


def test_each_row_has_triggers_metadata(fas_module, tmp_path):
    rows = fas_module.load_scores(_write_scores(tmp_path, _make_rows(20)))
    flagged = fas_module.flag(rows, worst_pct=10.0, min_agreement=1)
    for r in flagged:
        assert "triggers" in r
        assert "n_triggers" in r
        assert "worst_pct_rank" in r
        assert "suspicion" in r
        # word column preserved from input
        assert "word" in r


def test_per_language_independent_normalization(fas_module, tmp_path):
    """Two languages each get their own per-metric distribution."""
    rows_ami = _make_rows(10)
    rows_pwn = _make_rows(10)
    for r in rows_pwn:
        r["lang"] = "pwn"
        r["sentence_id"] = "PWN_" + r["sentence_id"]
    all_rows = fas_module.load_scores(_write_scores(tmp_path, rows_ami + rows_pwn))
    flagged = fas_module.flag(all_rows, worst_pct=20.0, min_agreement=1)
    langs = {r["lang"] for r in flagged}
    # We should see flagged rows from both languages, not just one.
    assert "ami" in langs
    assert "pwn" in langs


def test_emit_finding_per_suspicious_row(fas_module, tmp_path):
    """Each suspicious row emits one SOFT Finding (V120)."""
    rows = fas_module.load_scores(_write_scores(tmp_path, _make_rows(20)))
    flagged = fas_module.flag(rows, worst_pct=10.0, min_agreement=1)
    findings = fas_module.as_findings(flagged)
    assert len(findings) == len(flagged)
    from QC.validation._finding import Severity
    assert all(f.severity is Severity.SOFT for f in findings)
    assert all(f.rule_id == "V120" for f in findings)


def test_main_writes_suspect_audio_csv(fas_module, tmp_path):
    scores = _write_scores(tmp_path, _make_rows(20))
    out_csv = tmp_path / "suspect_audio.csv"
    rc = fas_module.main([
        "--scores", str(scores),
        "--out", str(out_csv),
        "--worst-pct", "10",
        "--min-agreement", "1",
    ])
    assert rc == 0
    assert out_csv.is_file()
    rows = list(csv.DictReader(out_csv.open()))
    assert rows  # at least one suspect

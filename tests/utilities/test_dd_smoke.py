"""Real-data smoke tests for the dialect detector.

These build per-language models from the published corpus and assert the
file-level (train=test) apparent accuracy stays at or above conservative
floors. They are skipped automatically when the corpus is absent. They are
slower than the synthetic unit tests because each ``build_model`` walks the
full ``Corpora`` tree.
"""
from pathlib import Path

import pytest

from QC.utilities.dialect_detector_pkg.model import build_model
from QC.utilities.dialect_detector_pkg.evaluate import evaluate_language

REPO = Path(__file__).resolve().parents[2]
CORP = REPO / "Corpora"
ORTH = REPO / "Orthographies" / "Ortho113"


@pytest.mark.skipif(not CORP.exists(), reason="corpus not present")
def test_rukai_separates_cleanly():
    model = build_model("dru", CORP, ORTH, top_n=2000)
    rep = evaluate_language("dru", model, CORP)
    assert rep["top1"] >= 0.95  # Rukai is orthographically distinct


@pytest.mark.skipif(not CORP.exists(), reason="corpus not present")
def test_amis_beats_baseline():
    model = build_model("ami", CORP, ORTH, top_n=2000)
    rep = evaluate_language("ami", model, CORP)
    assert rep["top1"] > 0.625  # must beat the char-only baseline (0.625)

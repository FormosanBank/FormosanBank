from QC.utilities.dialect_detector_pkg.evaluate import metrics_from_confusion, evaluate_language
from pathlib import Path


def test_evaluate_language_reports_top1_top2(tmp_path, monkeypatch):
    import QC.utilities.dialect_detector_pkg.candidates as cand
    monkeypatch.setattr(cand, "candidate_dialects", lambda lc: ["Alpha", "Beta"])
    import QC.utilities.dialect_detector_pkg.model as m
    monkeypatch.setattr(m, "language_name_for", lambda lc: "Toy")
    # reuse the toy builders from test_dd_model
    from tests.utilities.test_dd_model import _toy_tsv, _toy_corpus
    orth = tmp_path / "orth"; _toy_tsv(orth)
    corp = tmp_path / "corp"; _toy_corpus(corp)
    model = m.build_model("toy", corp, orth, top_n=100)
    rep = evaluate_language("toy", model, corp)
    assert rep["top1"] == 1.0
    assert rep["top2"] == 1.0
    assert set(rep["confusion"]) == {"Alpha", "Beta"}


def test_perfect_confusion_gives_one():
    conf = {"A": {"A": 5}, "B": {"B": 3}}
    mx = metrics_from_confusion(conf)
    assert mx["accuracy"] == 1.0
    assert mx["macro_f1"] == 1.0


def test_off_diagonal_lowers_scores():
    conf = {"A": {"A": 3, "B": 1}, "B": {"B": 4}}
    mx = metrics_from_confusion(conf)
    assert 0.0 < mx["accuracy"] < 1.0
    assert mx["macro_f1"] < 1.0

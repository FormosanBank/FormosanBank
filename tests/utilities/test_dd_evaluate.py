from QC.utilities.dialect_detector.evaluate import metrics_from_confusion, evaluate_language
from pathlib import Path


def test_evaluate_language_reports_top1_top2(tmp_path, monkeypatch):
    import QC.utilities.dialect_detector.candidates as cand
    monkeypatch.setattr(cand, "candidate_dialects", lambda lc: ["Alpha", "Beta"])
    import QC.utilities.dialect_detector.model as m
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


from QC.utilities.dialect_detector.evaluate import calibrate_threshold


def test_calibrate_commits_everything_when_all_correct():
    # all correct -> floor trivially met -> threshold at/below the lowest prob
    recs = [(0.9, True), (0.7, True), (0.55, True)]
    t = calibrate_threshold(recs, precision_floor=0.95)
    assert t <= 0.55  # commit all

def test_calibrate_picks_max_coverage_meeting_floor():
    # committing all -> acc 0.5 (<0.95); raising t to 0.8 -> acc 1.0, coverage 0.5
    recs = [(0.9, True), (0.8, True), (0.45, False), (0.40, False)]
    t = calibrate_threshold(recs, precision_floor=0.95)
    assert t == 0.8

def test_calibrate_infeasible_floor_stays_selective():
    recs = [(0.6, False), (0.5, False)]
    t = calibrate_threshold(recs, precision_floor=0.95)
    assert t >= 0.6  # cannot meet floor -> most selective (abstain-leaning)


from QC.utilities.dialect_detector.evaluate import cross_validate


def test_cross_validate_held_out_separates_toy(tmp_path, monkeypatch):
    import QC.utilities.dialect_detector.candidates as cand
    monkeypatch.setattr(cand, "candidate_dialects", lambda lc: ["Alpha", "Beta"])
    import QC.utilities.dialect_detector.model as m
    monkeypatch.setattr(m, "language_name_for", lambda lc: "Toy")
    from tests.utilities.test_dd_model import _toy_tsv, _toy_corpus
    orth = tmp_path / "orth"; _toy_tsv(orth)
    corp = tmp_path / "corp"; _toy_corpus(corp)
    rep = cross_validate("toy", corp, orth, k=2, top_n=100)
    assert rep["n"] == 8           # 4 Alpha + 4 Beta, all scored held-out
    assert rep["top1"] == 1.0      # separable -> held-out still perfect


def test_cross_validate_collects_unknown_holdout_for_kl(tmp_path, monkeypatch):
    import QC.utilities.dialect_detector.candidates as cand
    monkeypatch.setattr(cand, "candidate_dialects", lambda lc: ["Alpha", "Beta"])
    import QC.utilities.dialect_detector.model as m
    monkeypatch.setattr(m, "language_name_for", lambda lc: "Toy")
    from tests.utilities.test_dd_model import _toy_tsv, _toy_corpus
    orth = tmp_path / "orth"; _toy_tsv(orth)
    corp = tmp_path / "corp"; _toy_corpus(corp)
    extra = corp / "XML" / "u0.xml"
    extra.write_text(
        '<TEXT xml:lang="toy" dialect="unknown">'
        '<S id="1"><FORM kindOf="standard">vik fifa</FORM></S></TEXT>',
        encoding="utf-8",
    )
    rep = cross_validate("toy", corp, orth, k=2, top_n=100)
    assert len(rep["unknown_records_kl"]) == 1
    assert 0.0 <= rep["unknown_records_kl"][0] <= 1.0

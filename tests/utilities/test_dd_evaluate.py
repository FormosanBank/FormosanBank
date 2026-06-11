from QC.utilities.dialect_detector_pkg.evaluate import metrics_from_confusion


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

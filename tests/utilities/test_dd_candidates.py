from QC.utilities.dialect_detector_pkg.candidates import candidate_dialects, reconcile_label


def test_trv_candidates_include_truku_and_seediq_dialects():
    cands = candidate_dialects("trv")
    assert "Truku" in cands
    assert {"Duda", "Tegudaya", "DeluValley"} <= set(cands)
    assert "unknown" not in cands


def test_single_dialect_language_has_no_candidates():
    assert candidate_dialects("tao") == []   # Yami: single-dialect -> empty


def test_reconcile_exact_and_alias():
    cands = ["Nanwang", "Zhiben", "Xiqun", "Jianhe"]
    assert reconcile_label("Xiqun", cands) == "Xiqun"          # exact
    assert reconcile_label("Chulu", cands) == "Xiqun"          # alias (初鹿->西群)
    assert reconcile_label("NoSuchDialect", cands) is None
    # an alias whose target is not among these candidates also yields None
    assert reconcile_label("Toda", cands) is None              # Toda->Duda, not a Puyuma candidate

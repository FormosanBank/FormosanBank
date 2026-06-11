from pathlib import Path
from QC.utilities.dialect_detector_pkg.cli import main

def test_cli_predict_runs_and_reports(tmp_path, monkeypatch, capsys):
    import QC.utilities.dialect_detector_pkg.candidates as cand
    monkeypatch.setattr(cand, "candidate_dialects", lambda lc: ["Alpha", "Beta"])
    import QC.utilities.dialect_detector_pkg.model as m
    monkeypatch.setattr(m, "language_name_for", lambda lc: "Toy")
    monkeypatch.setattr(m, "IN_SCOPE_LANGS", ["toy"])
    from tests.utilities.test_dd_model import _toy_tsv, _toy_corpus
    orth = tmp_path / "orth"; _toy_tsv(orth)
    corp = tmp_path / "corp"; _toy_corpus(corp)
    models = tmp_path / "models"
    rc = main(["train", "--corpora_path", str(corp),
               "--orthographies", str(orth), "--models_dir", str(models)])
    assert rc == 0 and (models / "Toy.json").exists()
    target = corp / "XML" / "a0.xml"
    rc = main(["predict", "--path", str(target), "--models_dir", str(models)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Alpha" in out

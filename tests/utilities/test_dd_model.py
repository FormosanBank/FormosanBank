from pathlib import Path
from QC.utilities.dialect_detector_pkg.model import build_model, COMPONENTS, save_model, load_model


def _toy_tsv(orth: Path):
    orth.mkdir(parents=True, exist_ok=True)
    (orth / "Toy.tsv").write_text(
        "letter\tAlpha\tBeta\tdefault\n"
        "v\tv\tNA\tv\n" "f\tNA\tf\tf\n" "i\ti\ti\ti\n" "k\tk\tk\tk\n" "a\ta\ta\ta\n",
        encoding="utf-8")


def _toy_corpus(corp: Path):
    def w(rel, lang, dia, *txt):
        p = corp / rel; p.parent.mkdir(parents=True, exist_ok=True)
        forms = "".join(f'<S id="{i}"><FORM kindOf="standard">{t}</FORM></S>'
                        for i, t in enumerate(txt))
        p.write_text(f'<TEXT xml:lang="toy" dialect="{dia}">{forms}</TEXT>', encoding="utf-8")
    for n in range(4): w(f"XML/a{n}.xml", "toy", "Alpha", "vik va", "viva")
    for n in range(4): w(f"XML/b{n}.xml", "toy", "Beta", "fik fa", "fifa")


def test_build_model_learns_to_separate(tmp_path, monkeypatch):
    import QC.utilities.dialect_detector_pkg.candidates as cand
    monkeypatch.setattr(cand, "candidate_dialects", lambda lc: ["Alpha", "Beta"])
    import QC.utilities.dialect_detector_pkg.model as m
    monkeypatch.setattr(m, "language_name_for", lambda lc: "Toy")
    orth = tmp_path / "orth"; _toy_tsv(orth)
    corp = tmp_path / "corp"; _toy_corpus(corp)
    model = build_model("toy", corp, orth, top_n=100)
    assert model is not None
    assert model.components == COMPONENTS
    ranked = model.score_text("vik viva")
    assert ranked[0][0] == "Alpha"
    # symmetric case + a confident probability confirm the combiner separated the
    # classes at training time (not just the orthography component on one example).
    assert model.score_text("fik fifa")[0][0] == "Beta"
    assert ranked[0][1] > 0.9


def test_save_load_roundtrip_preserves_ranking(tmp_path, monkeypatch):
    import QC.utilities.dialect_detector_pkg.candidates as cand
    monkeypatch.setattr(cand, "candidate_dialects", lambda lc: ["Alpha", "Beta"])
    import QC.utilities.dialect_detector_pkg.model as m
    monkeypatch.setattr(m, "language_name_for", lambda lc: "Toy")
    orth = tmp_path / "orth"; _toy_tsv(orth)
    corp = tmp_path / "corp"; _toy_corpus(corp)
    model = build_model("toy", corp, orth, top_n=100)
    out = tmp_path / "Toy.json"
    save_model(model, out)
    loaded = load_model(out)
    assert loaded.dialects == model.dialects
    assert loaded.score_text("vik viva")[0][0] == model.score_text("vik viva")[0][0]

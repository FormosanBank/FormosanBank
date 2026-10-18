"""lint_hidden_tables.py: language data as Python literals is reported, docstrings and prose are not."""
import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("lint", REPO / "QC" / "validation" / "lint_hidden_tables.py")
lint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint)

VOCAB = frozenset({"maolah", "kako", "tayra", "wawa", "niyaro", "romiad"})


def test_counts_cjk_and_attested_words_outside_docstrings():
    source = '''"""Build Amis XML. Tayra kako maolah — a docstring is documentation, not data."""
OVERRIDES = {"s12": "maolah kako to wawa", "s13": "tayra ko wawa i niyaro'"}
TRANSLATIONS = {"s12": "我喜歡小孩", "s13": "小孩去部落"}
LOG = "wrote %d sentences to %s"
'''
    found = lint.data_tokens(source, VOCAB)
    assert found == {"maolah": 1, "kako": 1, "wawa": 2, "tayra": 1, "niyaro": 1, "我喜歡小孩": 1, "小孩去部落": 1}


def test_lint_corpus_lists_only_files_over_the_threshold(tmp_path):
    corpus = tmp_path / "C"
    (corpus / "CodeAndDocs").mkdir(parents=True)
    (corpus / "CodeAndDocs" / "build.py").write_text(
        "TABLE = {" + ", ".join(f'"s{i}": "maolah kako wawa"' for i in range(12)) + "}\n", encoding="utf-8")
    (corpus / "CodeAndDocs" / "tidy.py").write_text('MSG = "maolah"\n', encoding="utf-8")
    hits = lint.lint_corpus(corpus, threshold=30, vocab=VOCAB)
    assert [(p.name, n) for p, n, _s in hits] == [("build.py", 36)]
    assert hits[0][2][:3] == ["maolah", "kako", "wawa"]
    assert lint.lint_corpus(corpus, threshold=40, vocab=VOCAB) == []


def test_cli_always_exits_zero(tmp_path, capsys):
    corpus = tmp_path / "C"
    (corpus / "CodeAndDocs").mkdir(parents=True)
    (corpus / "XML").mkdir()
    (corpus / "CodeAndDocs" / "x.py").write_text('T = "' + "我 " * 40 + '"\n', encoding="utf-8")
    assert lint.main(["--corpus", str(corpus)]) == 0
    assert "x.py" in capsys.readouterr().out

"""Tests for QC/validation/validate_port_readiness.py.

The pre-port gate is a plain script usable without AI tooling; tests
build miniature corpus layouts under tmp_path (with their own git repo
where a check needs one) and assert on exit codes and P-rule markers.
"""
import subprocess
import sys
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "QC" / "validation" / "validate_port_readiness.py"
)
REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(corpus: Path, repo_root: Path | None = None) -> subprocess.CompletedProcess:
    argv = [sys.executable, str(SCRIPT), "--corpus_path", str(corpus),
            "--repo-root", str(repo_root or REPO_ROOT)]
    return subprocess.run(argv, capture_output=True, text=True)


def _git(corpus: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=corpus, capture_output=True, check=True)


def _mini_corpus(tmp_path: Path, dialect: str = "Nanwang") -> Path:
    corpus = tmp_path / "Formosan-Mini"
    (corpus / "XML").mkdir(parents=True)
    (corpus / "CodeAndDocs").mkdir()
    (corpus / "XML" / "a.xml").write_text(
        '<?xml version="1.0"?>\n'
        '<TEXT id="t" citation="c" BibTeX_citation="@b{t}" copyright="cc" '
        f'xml:lang="pyu" dialect="{dialect}">'
        '<S id="S1"><FORM kindOf="original">lima</FORM></S></TEXT>\n',
        encoding="utf-8")
    return corpus


def test_clean_corpus_exits_zero(tmp_path):
    proc = _run(_mini_corpus(tmp_path))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "0 HARD" in proc.stdout


def test_unknown_dialect_is_hard(tmp_path):
    proc = _run(_mini_corpus(tmp_path, dialect="Nanwan"))  # typo
    assert proc.returncode == 1
    assert "P003" in proc.stdout


def test_unknown_language_is_hard(tmp_path):
    corpus = _mini_corpus(tmp_path)
    text = (corpus / "XML" / "a.xml").read_text(encoding="utf-8")
    (corpus / "XML" / "a.xml").write_text(
        text.replace('xml:lang="pyu"', 'xml:lang="xxq"'), encoding="utf-8")
    proc = _run(corpus)
    assert proc.returncode == 1
    assert "P002" in proc.stdout


def test_tracked_private_content_is_hard(tmp_path):
    corpus = _mini_corpus(tmp_path)
    (corpus / "Private").mkdir()
    (corpus / "Private" / "source.pdf").write_text("secret", encoding="utf-8")
    _git(corpus, "init", "-q")
    _git(corpus, "add", "-A")
    proc = _run(corpus)
    assert proc.returncode == 1
    assert "P001" in proc.stdout


def test_untracked_private_content_not_hard(tmp_path):
    corpus = _mini_corpus(tmp_path)
    (corpus / "Private").mkdir()
    (corpus / "Private" / "source.pdf").write_text("secret", encoding="utf-8")
    (corpus / ".gitignore").write_text("Private/\n", encoding="utf-8")
    _git(corpus, "init", "-q")
    _git(corpus, "add", "-A")
    proc = _run(corpus)
    assert proc.returncode == 0, proc.stdout
    assert "P001 HARD" not in proc.stdout


def test_divergent_commit_pins_warn(tmp_path):
    corpus = _mini_corpus(tmp_path)
    (corpus / "README.md").write_text(
        "Reproduce against FormosanBank commit deadbeef1234567.\n",
        encoding="utf-8")
    (corpus / "CodeAndDocs" / "qc_status.json").write_text(
        '{"note": "pinned commit cafebabe7654321"}\n', encoding="utf-8")
    proc = _run(corpus)
    assert proc.returncode == 0, "P004 is WARN, must not block"
    assert "P004" in proc.stdout
    assert "different commits" in proc.stdout


def test_hex_without_commit_context_ignored(tmp_path):
    corpus = _mini_corpus(tmp_path)
    (corpus / "README.md").write_text(
        "The audio archive md5 is 0123456789abcdef, recorded for "
        "integrity verification only.\n", encoding="utf-8")
    proc = _run(corpus)
    assert "P004" not in proc.stdout


def test_conversion_table_reference_warns(tmp_path):
    corpus = _mini_corpus(tmp_path)
    (corpus / "CodeAndDocs" / "standardize.sh").write_text(
        "python QC/utilities/standardize.py --tsv_path "
        "Orthographies/ConversionTables/Puyuma_Cauquelin_113.tsv\n",
        encoding="utf-8")
    proc = _run(corpus)
    assert proc.returncode == 0
    assert "P006" in proc.stdout
    assert "Puyuma_Cauquelin_113.tsv" in proc.stdout


# ---------------------------------------------------------------------------
# 2026-10-17 (skills review E3): P004 and P006 false negatives/positives
# ---------------------------------------------------------------------------

def test_hash_inside_a_url_is_a_link_not_a_pin(tmp_path):
    """PR #170 linked an upstream data commit, PR #163 its own history; neither pins FormosanBank."""
    corpus = _mini_corpus(tmp_path)
    (corpus / "README.md").write_text(
        "Source data: the upstream commit at "
        "https://github.com/other/data/commit/0123456789abcdef0123456789abcdef01234567 .\n"
        "History: [the reproduction run](https://github.com/FormosanBank/FormosanBank/commit/"
        "fedcba9876543210fedcba9876543210fedcba98).\n",
        encoding="utf-8")
    proc = _run(corpus)
    assert "P004" not in proc.stdout, proc.stdout


def test_pin_outside_a_url_is_still_checked(tmp_path):
    corpus = _mini_corpus(tmp_path)
    (corpus / "README.md").write_text(
        "Built against FormosanBank commit 0123456789abcdef0123456789abcdef01234567.\n",
        encoding="utf-8")
    proc = _run(corpus)
    assert "P004" in proc.stdout and "not reachable" in proc.stdout, proc.stdout


def test_corpus_local_conversion_table_warns_too(tmp_path):
    """PRs #153 and #150 standardized through CodeAndDocs/<table>.tsv and got 0 WARN."""
    corpus = _mini_corpus(tmp_path)
    (corpus / "CodeAndDocs" / "generate_xml.sh").write_text(
        'python QC/utilities/standardize.py --tsv_path "$HERE/CodeAndDocs/Amis_local_113.tsv"\n',
        encoding="utf-8")
    proc = _run(corpus)
    assert proc.returncode == 0
    assert "P006" in proc.stdout
    assert "Amis_local_113.tsv" in proc.stdout and "corpus-local" in proc.stdout, proc.stdout

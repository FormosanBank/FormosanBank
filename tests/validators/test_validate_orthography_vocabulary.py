"""validate_orthography.py / validate_vocabulary.py: the SUMMARY line and exit status.

Both scripts are informational (always exit 0) and had no tests; a port audit
quotes their SUMMARY lines, so these pin what that line says in the three
cases that matter: corpus matches the reference, corpus differs from it, and
no reference exists for the group. The pickles are produced by the real
`orthography_extract.extract_orthographic_info` so the layout a run writes is
the layout the tests read.
"""
from __future__ import annotations

import pickle
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "QC" / "orthography"))
from orthography_extract import extract_orthographic_info  # noqa: E402

AMIS = ("o wawa no mita ko tayal a maolah to romi'ad i niyaro' ato sera ") * 12
# Same text with a letter the reference never uses, often enough to survive the
# >=5 occurrence filter inside extract_orthographic_info.
AMIS_WITH_BARRED_U = AMIS + ("ʉmah ʉmah ʉmah ") * 4


def _write_info(directory: Path, text: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "orthographic_info").open("wb") as fp:
        pickle.dump(extract_orthographic_info(text), fp)


def _run(script: str, o_info: Path, reference: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO / "QC" / "validation" / script),
         "--o_info", str(o_info), "--reference", str(reference)],
        capture_output=True, text=True, cwd=REPO,
    )


def _summary_lines(proc: subprocess.CompletedProcess, kind: str) -> list[str]:
    return [l for l in proc.stdout.splitlines() if l.startswith(f"SUMMARY {kind} | ")]


@pytest.fixture
def trees(tmp_path):
    """Dialect layout for Amis/Coastal, legacy flat layout for Thao."""
    o_info, reference = tmp_path / "extract_logs", tmp_path / "reference"
    _write_info(o_info / "Amis" / "Coastal", AMIS)
    _write_info(reference / "Amis" / "Coastal", AMIS)
    _write_info(o_info / "Thao", AMIS)
    _write_info(reference / "Thao", AMIS)
    return o_info, reference


def test_orthography_identical_corpus_gets_a_clean_summary_line(trees):
    o_info, reference = trees
    proc = _run("validate_orthography.py", o_info, reference)
    assert proc.returncode == 0, proc.stderr
    lines = _summary_lines(proc, "orthography")
    assert len(lines) == 2, proc.stdout
    amis = next(l for l in lines if "Amis / Coastal" in l)
    assert re.search(r"jaccard=1\.00 overlap=1\.00 cosine=1\.000", amis), amis
    assert "corpus_only=[] reference_only=[]" in amis
    assert amis.endswith("warnings=0")
    assert next(l for l in lines if "| Thao |" in l).endswith("warnings=0")
    assert (o_info / "Amis" / "Coastal" / "Amis_Coastal_frequency_comparison.png").is_file()


def test_orthography_extra_letter_warns_and_is_named_in_the_summary(trees):
    o_info, reference = trees
    _write_info(o_info / "Amis" / "Coastal", AMIS_WITH_BARRED_U)
    proc = _run("validate_orthography.py", o_info, reference)
    assert proc.returncode == 0, "informational: must still exit 0"
    amis = next(l for l in _summary_lines(proc, "orthography") if "Amis / Coastal" in l)
    assert "corpus_only=[ʉ]" in amis, amis
    assert "reference_only=[]" in amis
    assert not amis.endswith("warnings=0"), amis
    assert "WARNING: The disjunction of character sets" in proc.stdout


def test_orthography_missing_reference_is_reported_not_fatal(trees):
    o_info, reference = trees
    _write_info(o_info / "Amis" / "Southern", AMIS)   # no reference/Amis/Southern
    proc = _run("validate_orthography.py", o_info, reference)
    assert proc.returncode == 0
    assert "SUMMARY orthography | Amis / Southern | reference=missing | warnings=1" in proc.stdout
    assert "WARNING: No reference orthographic info found" in proc.stdout


def test_vocabulary_identical_corpus_gets_a_clean_summary_line(trees):
    o_info, reference = trees
    proc = _run("validate_vocabulary.py", o_info, reference)
    assert proc.returncode == 0, proc.stderr
    amis = next(l for l in _summary_lines(proc, "vocabulary") if "Amis / Coastal" in l)
    assert "top100_jaccard=1.00 overlap=1.00 | corpus_only=[] reference_only=[] | warnings=0" in amis
    assert "UserWarning" not in proc.stderr


def test_vocabulary_divergent_corpus_lists_the_words_on_each_side(trees):
    o_info, reference = trees
    _write_info(o_info / "Amis" / "Coastal", AMIS + ("fafahi kaying ") * 6)
    proc = _run("validate_vocabulary.py", o_info, reference)
    assert proc.returncode == 0
    amis = next(l for l in _summary_lines(proc, "vocabulary") if "Amis / Coastal" in l)
    assert "corpus_only=[fafahi kaying]" in amis, amis
    # Jaccard drops (13 shared / 15 union); overlap stays 1.00 because the corpus
    # vocabulary is a superset of the reference's, so exactly one warning.
    assert "top100_jaccard=0.88 overlap=1.00" in amis, amis
    assert amis.endswith("warnings=1"), amis
    assert "High-frequency words in corpus but not in reference" in proc.stderr


def test_vocabulary_missing_reference_is_reported_not_fatal(trees):
    o_info, reference = trees
    _write_info(o_info / "Amis" / "Southern", AMIS)
    proc = _run("validate_vocabulary.py", o_info, reference)
    assert proc.returncode == 0
    assert "SUMMARY vocabulary | Amis / Southern | reference=missing | warnings=1" in proc.stdout


# ---------------------------------------------------------------------------
# --quiet (hand-over answer Q4R2, 2026-10-17): the development output stays the
# default; the skills run --quiet and get only the group header, the metric
# lines, WARNING lines and the SUMMARY line.
# ---------------------------------------------------------------------------

def _run_quiet(script: str, o_info: Path, reference: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO / "QC" / "validation" / script),
         "--o_info", str(o_info), "--reference", str(reference), "--quiet"],
        capture_output=True, text=True, cwd=REPO,
    )


def test_orthography_default_output_keeps_the_development_detail(trees):
    o_info, reference = trees
    out = _run("validate_orthography.py", o_info, reference).stdout
    assert out.count("dict_keys([") == 4            # two pickles' key lists, per group, two groups
    assert any(l.startswith("{'") for l in out.splitlines()), "reference frequency table is printed by default"


def test_orthography_quiet_leaves_only_metrics_warnings_and_summary(trees):
    o_info, reference = trees
    _write_info(o_info / "Amis" / "Coastal", AMIS_WITH_BARRED_U)
    proc = _run_quiet("validate_orthography.py", o_info, reference)
    assert proc.returncode == 0, proc.stderr
    lines = proc.stdout.splitlines()
    assert "dict_keys([" not in proc.stdout
    assert not any(l.startswith("{'") for l in lines)
    assert "  --- Dialect: Coastal ---" in lines            # the group header stays: numbers need their group
    assert any(l.startswith("Jaccard Similarity of unique characters:") for l in lines)
    assert any(l.startswith("WARNING: The disjunction of character sets") for l in lines)
    assert sum(l.startswith("SUMMARY orthography | ") for l in lines) == 2
    assert "findfont" not in proc.stderr


def test_vocabulary_warning_text_names_words_not_character_sets(trees):
    o_info, reference = trees
    _write_info(o_info / "Amis" / "Coastal", AMIS + ("fafahi kaying ") * 6)
    proc = _run("validate_vocabulary.py", o_info, reference)
    assert "character sets" not in proc.stderr + proc.stdout
    assert "Top-100 word overlap with the reference is low (Jaccard < .975)." in proc.stderr
    assert "Jaccard Similarity of top-100 words: 0.88" in proc.stdout


def test_vocabulary_quiet_puts_warnings_on_stdout_as_plain_lines(trees):
    o_info, reference = trees
    _write_info(o_info / "Amis" / "Coastal", AMIS + ("fafahi kaying ") * 6)
    proc = _run_quiet("validate_vocabulary.py", o_info, reference)
    assert proc.returncode == 0, proc.stderr
    assert "WARNING: Top-100 word overlap with the reference is low (Jaccard < .975)." in proc.stdout
    assert "WARNING: High-frequency words in corpus but not in reference: ['fafahi', 'kaying']" in proc.stdout
    assert "UserWarning" not in proc.stderr and "findfont" not in proc.stderr
    assert any(l.startswith("SUMMARY vocabulary | Amis / Coastal |") for l in proc.stdout.splitlines())

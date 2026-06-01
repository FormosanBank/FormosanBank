"""Tests for QC/validation/validate_audio_quality.py.

The script ports Jacob Ye's `compute_metrics.py`. The heavy ML deps
(torch, torchaudio, allosaurus, Levenshtein, unidecode) are not assumed
to be installed in the test environment — we mock the model calls per
Open Question 2 in the B9.2 plan.

What we test directly (no mocks):
- corpus walking (collect_entries, collect_corpus)
- resumability (load_existing skips rows present in --out-csv)
- the pure helpers (levenshtein_distance, wer_cer, parse_metrics,
  clean_for_alignment)
- CSV-writing orchestration with mocked acoustic/pdm results
- the `--metrics ctc,wer,cer` selector skips the pdm column

What we mock:
- run_acoustic_pass and run_pdm_pass — replaced with deterministic
  fakes so we exercise the orchestration without loading wav2vec2 or
  Allosaurus.

What we skip:
- Anything that actually imports torch. If torch is unavailable, that
  test is skipped with a clear marker — caller (the B9.2 plan)
  acknowledges this is acceptable for the scaffolding pass.
"""
import csv
import subprocess
import sys
import xml.etree.ElementTree as ET
from importlib import import_module
from pathlib import Path
from unittest import mock

import pytest


VALIDATE_AUDIO_QUALITY = (
    Path(__file__).resolve().parents[2] / "QC" / "validation" / "validate_audio_quality.py"
)


@pytest.fixture
def vaq_module():
    """Import the validate_audio_quality module fresh per test."""
    # Make QC package importable when tests run.
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    mod = import_module("QC.validation.validate_audio_quality")
    return mod


def _make_corpus(tmp_path: Path, n_sentences: int = 3) -> tuple[Path, list[Path]]:
    """Create a corpus with <corpus>/XML/test.xml and <corpus>/Audio/<file>.wav."""
    corpus = tmp_path
    xml_dir = corpus / "XML"
    audio_dir = corpus / "Audio"
    xml_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)

    audio_files = []
    root = ET.Element("TEXT", attrib={
        "id": "TEST",
        "citation": "t",
        "BibTeX_citation": "@t{t}",
        "copyright": "t",
        "xml:lang": "ami",
    })
    for i in range(1, n_sentences + 1):
        s = ET.SubElement(root, "S", attrib={"id": f"S_{i}"})
        ET.SubElement(s, "FORM", attrib={"kindOf": "original"}).text = f"sentence {i}"
        fname = f"audio_{i}.wav"
        ET.SubElement(s, "AUDIO", attrib={"file": fname})
        a_path = audio_dir / fname
        a_path.write_bytes(b"FAKE_WAV")
        audio_files.append(a_path)
    ET.ElementTree(root).write(str(xml_dir / "test.xml"),
                                encoding="utf-8", xml_declaration=True)
    return corpus, audio_files


# -----------------------------------------------------------------------------
# Pure helpers
# -----------------------------------------------------------------------------


def test_parse_metrics_all(vaq_module):
    assert vaq_module.parse_metrics("all") == {"ctc", "wer", "cer", "pdm"}


def test_parse_metrics_subset(vaq_module):
    assert vaq_module.parse_metrics("ctc,wer,cer") == {"ctc", "wer", "cer"}


def test_levenshtein_basic(vaq_module):
    assert vaq_module.levenshtein_distance("kitten", "sitting") == 3
    assert vaq_module.levenshtein_distance("", "abc") == 3
    assert vaq_module.levenshtein_distance("abc", "abc") == 0


def test_wer_cer_basic(vaq_module):
    wer, cer = vaq_module.wer_cer("a b c", "a b c")
    assert wer == 0.0
    assert cer == 0.0
    wer, cer = vaq_module.wer_cer("a b c", "a b d")
    assert wer == pytest.approx(1/3)
    assert cer > 0


def test_wer_cer_empty_hyp(vaq_module):
    wer, cer = vaq_module.wer_cer("a b c", "")
    assert wer == 1.0
    assert cer == 1.0


def test_clean_for_alignment_strips_punct(vaq_module):
    out = vaq_module.clean_for_alignment("Hello, world!")
    assert "," not in out
    assert "!" not in out
    assert "hello" in out.lower()


# -----------------------------------------------------------------------------
# Corpus walking
# -----------------------------------------------------------------------------


def test_collect_corpus_walks_xml_subdir(tmp_path, vaq_module):
    corpus, audio_files = _make_corpus(tmp_path, n_sentences=3)
    entries = vaq_module.collect_corpus(corpus)
    assert len(entries) == 3
    assert {e["sentence_id"] for e in entries} == {"S_1", "S_2", "S_3"}
    for e in entries:
        assert e["lang"] == "ami"
        assert e["transcript"]
        assert Path(e["audio_path"]).is_file()


def test_collect_corpus_skips_when_audio_missing(tmp_path, vaq_module):
    corpus, audio_files = _make_corpus(tmp_path, n_sentences=2)
    # Delete one audio file
    audio_files[0].unlink()
    entries = vaq_module.collect_corpus(corpus)
    assert {e["sentence_id"] for e in entries} == {"S_2"}


def test_collect_corpus_blank_word_when_no_word_map(tmp_path, vaq_module):
    corpus, _ = _make_corpus(tmp_path, n_sentences=2)
    entries = vaq_module.collect_corpus(corpus, word_map=None)
    assert all(e["word"] == "" for e in entries)


# -----------------------------------------------------------------------------
# Resumability
# -----------------------------------------------------------------------------


def test_load_existing_skips_known_ids(tmp_path, vaq_module):
    out_csv = tmp_path / "scores.csv"
    out_csv.write_text("sentence_id\nS_1\nS_2\n", encoding="utf-8")
    assert vaq_module.load_existing(out_csv) == {"S_1", "S_2"}


def test_load_existing_returns_empty_for_missing_file(tmp_path, vaq_module):
    out_csv = tmp_path / "nope.csv"
    assert vaq_module.load_existing(out_csv) == set()


# -----------------------------------------------------------------------------
# write_rows orchestration with mocked metric outputs
# -----------------------------------------------------------------------------


def test_write_rows_emits_expected_columns_with_pdm(tmp_path, vaq_module):
    entries = [
        {"lang": "ami", "sentence_id": "S_1", "word": "",
         "audio_path": "/a.wav", "transcript": "hello"},
    ]
    acoustic = {"S_1": {"asr_hypothesis": "helo", "ctc_score": 0.42,
                        "wer": 0.5, "cer": 0.1}}
    pdm = {"S_1": {"pdm_score": 0.7}}
    out_csv = tmp_path / "scores.csv"
    vaq_module.write_rows(out_csv, entries, acoustic, pdm,
                          metrics={"ctc", "wer", "cer", "pdm"},
                          include_pdm=True)
    rows = list(csv.DictReader(out_csv.open()))
    assert rows[0]["pdm_score"] == "0.700000"
    assert rows[0]["ctc_score"] == "0.420000"
    assert rows[0]["wer"] == "0.500000"
    assert rows[0]["cer"] == "0.100000"
    assert rows[0]["asr_hypothesis"] == "helo"


def test_write_rows_omits_pdm_column_when_metric_not_requested(tmp_path, vaq_module):
    entries = [
        {"lang": "ami", "sentence_id": "S_1", "word": "",
         "audio_path": "/a.wav", "transcript": "hello"},
    ]
    acoustic = {"S_1": {"asr_hypothesis": "helo", "ctc_score": 0.42,
                        "wer": 0.5, "cer": 0.1}}
    out_csv = tmp_path / "scores_no_pdm.csv"
    vaq_module.write_rows(out_csv, entries, acoustic, {},
                          metrics={"ctc", "wer", "cer"},
                          include_pdm=False)
    rows = list(csv.DictReader(out_csv.open()))
    assert "pdm_score" not in rows[0], f"pdm_score column should be omitted; got cols {list(rows[0].keys())}"
    assert rows[0]["ctc_score"] == "0.420000"


# -----------------------------------------------------------------------------
# End-to-end with mocked heavy passes
# -----------------------------------------------------------------------------


def test_main_with_mocked_passes_produces_scores_csv(tmp_path, vaq_module, monkeypatch):
    """Mock both run_acoustic_pass and run_pdm_pass; verify the CLI
    orchestration produces a CSV with one row per sentence."""
    corpus, _ = _make_corpus(tmp_path, n_sentences=2)
    out_csv = tmp_path / "scores.csv"

    def fake_acoustic(entries, want_ctc, want_wer_cer, data_quality_eval_path=None):
        return {e["sentence_id"]: {"asr_hypothesis": "fake", "ctc_score": 0.1,
                                    "wer": 0.2, "cer": 0.3}
                for e in entries}

    def fake_pdm(entries, cache_path=None):
        return {e["sentence_id"]: {"pdm_score": 0.9} for e in entries}

    monkeypatch.setattr(vaq_module, "run_acoustic_pass", fake_acoustic)
    monkeypatch.setattr(vaq_module, "run_pdm_pass", fake_pdm)

    rc = vaq_module.main([
        "--corpus_path", str(corpus),
        "--out-csv", str(out_csv),
        "--metrics", "all",
    ])
    assert rc == 0
    rows = list(csv.DictReader(out_csv.open()))
    assert len(rows) == 2
    assert {r["sentence_id"] for r in rows} == {"S_1", "S_2"}
    assert all(r["asr_hypothesis"] == "fake" for r in rows)
    assert all(r["pdm_score"] == "0.900000" for r in rows)


def test_main_sample_5_returns_5(tmp_path, vaq_module, monkeypatch):
    """--sample 5 should keep at most 5 entries in the output CSV."""
    corpus, _ = _make_corpus(tmp_path, n_sentences=20)
    out_csv = tmp_path / "scores.csv"
    monkeypatch.setattr(vaq_module, "run_acoustic_pass",
                        lambda entries, **kw: {e["sentence_id"]: {} for e in entries})
    monkeypatch.setattr(vaq_module, "run_pdm_pass",
                        lambda entries, **kw: {e["sentence_id"]: {} for e in entries})
    rc = vaq_module.main([
        "--corpus_path", str(corpus),
        "--out-csv", str(out_csv),
        "--metrics", "all",
        "--sample", "5",
    ])
    assert rc == 0
    rows = list(csv.DictReader(out_csv.open()))
    assert len(rows) == 5


def test_main_resumes_after_partial_run(tmp_path, vaq_module, monkeypatch):
    """A second run with the same --out-csv should skip already-scored ids."""
    corpus, _ = _make_corpus(tmp_path, n_sentences=3)
    out_csv = tmp_path / "scores.csv"
    seen_in_pass = {"count": 0}

    def fake_pass(entries, **kw):
        seen_in_pass["count"] = len(entries)
        return {e["sentence_id"]: {} for e in entries}

    monkeypatch.setattr(vaq_module, "run_acoustic_pass", fake_pass)
    monkeypatch.setattr(vaq_module, "run_pdm_pass", fake_pass)

    # First run scores everything.
    vaq_module.main([
        "--corpus_path", str(corpus),
        "--out-csv", str(out_csv),
        "--metrics", "all",
    ])
    assert seen_in_pass["count"] == 3

    # Second run should see zero entries (all skipped).
    seen_in_pass["count"] = -1  # so we can tell whether the pass was even called
    vaq_module.main([
        "--corpus_path", str(corpus),
        "--out-csv", str(out_csv),
        "--metrics", "all",
    ])
    # Either the pass never ran (resumed with nothing to do) OR it ran with 0 entries.
    assert seen_in_pass["count"] in (-1, 0)


# -----------------------------------------------------------------------------
# Heavy-import smoke test: skipped if torch is missing
# -----------------------------------------------------------------------------


try:
    import torch  # noqa: F401
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


@pytest.mark.skipif(not HAS_TORCH, reason="torch not installed (heavy ML dep)")
def test_run_acoustic_pass_real_import_smoke(vaq_module, tmp_path):
    """If torch is available, verify run_acoustic_pass at least
    starts importing without raising. We don't actually run the model
    here; we use an empty entries list so the function returns the
    early-exit empty dict before touching any heavy code."""
    result = vaq_module.run_acoustic_pass([], want_ctc=False, want_wer_cer=False)
    assert result == {}

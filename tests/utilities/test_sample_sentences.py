"""Unit tests for QC/utilities/sample_sentences.py (B9.7 random sampler)."""
from pathlib import Path

from QC.utilities.sample_sentences import (
    collect_sentences,
    format_markdown,
    main,
)


def _write_corpus(root: Path, name: str, xml_files: dict[str, str]) -> None:
    """Helper: create <root>/<name>/XML/<filename>.xml for each entry."""
    xml_dir = root / name / "XML"
    xml_dir.mkdir(parents=True)
    for filename, content in xml_files.items():
        (xml_dir / filename).write_text(content, encoding="utf-8")


SIMPLE_XML = """<?xml version="1.0" encoding="utf-8"?>
<TEXT id="t1" citation="c" BibTeX_citation="@b{x}" copyright="cc" xml:lang="ami">
  <S id="S1">
    <FORM kindOf="original">Halo (orig).</FORM>
    <FORM kindOf="standard">Halo (std).</FORM>
    <TRANSL xml:lang="eng">Hello.</TRANSL>
    <TRANSL xml:lang="zho">你好。</TRANSL>
    <AUDIO file="s1.wav"/>
  </S>
  <S id="S2">
    <FORM kindOf="original">Solid.</FORM>
    <FORM kindOf="standard">Solid.</FORM>
    <TRANSL xml:lang="eng">Solid.</TRANSL>
  </S>
</TEXT>
"""


def test_collect_sentences_finds_S_elements_under_XML_subdir(tmp_path):
    """When `<corpus_path>/XML/` exists, walk only that subdir."""
    _write_corpus(tmp_path, "Test", {"a.xml": SIMPLE_XML})
    records = collect_sentences(tmp_path / "Test")
    assert len(records) == 2
    assert {r["s_id"] for r in records} == {"S1", "S2"}


def test_collect_sentences_falls_back_when_no_XML_subdir(tmp_path):
    """When `<corpus_path>/XML/` is absent, walk corpus_path in full."""
    (tmp_path / "loose.xml").write_text(SIMPLE_XML, encoding="utf-8")
    records = collect_sentences(tmp_path)
    assert len(records) == 2


def test_collect_sentences_captures_both_FORM_tiers(tmp_path):
    """Both original and standard FORM text are recorded per S."""
    _write_corpus(tmp_path, "Test", {"a.xml": SIMPLE_XML})
    records = collect_sentences(tmp_path / "Test")
    s1 = next(r for r in records if r["s_id"] == "S1")
    assert s1["forms"]["original"] == "Halo (orig)."
    assert s1["forms"]["standard"] == "Halo (std)."


def test_collect_sentences_captures_translations_by_language(tmp_path):
    """Multiple TRANSL elements with different xml:lang are indexed by lang."""
    _write_corpus(tmp_path, "Test", {"a.xml": SIMPLE_XML})
    records = collect_sentences(tmp_path / "Test")
    s1 = next(r for r in records if r["s_id"] == "S1")
    assert s1["translations"]["eng"] == "Hello."
    assert s1["translations"]["zho"] == "你好。"


def test_collect_sentences_captures_audio_files(tmp_path):
    """AUDIO/@file values are collected into the audio_files list."""
    _write_corpus(tmp_path, "Test", {"a.xml": SIMPLE_XML})
    records = collect_sentences(tmp_path / "Test")
    s1 = next(r for r in records if r["s_id"] == "S1")
    assert s1["audio_files"] == ["s1.wav"]


def test_collect_sentences_skips_parse_errors(tmp_path):
    """Files that fail XML parse are silently skipped."""
    _write_corpus(
        tmp_path,
        "Test",
        {"good.xml": SIMPLE_XML, "bad.xml": "this is not xml"},
    )
    records = collect_sentences(tmp_path / "Test")
    assert len(records) == 2


def test_format_markdown_includes_required_fields(tmp_path):
    """Markdown output mentions S id, language, file, FORM text, TRANSL."""
    _write_corpus(tmp_path, "Test", {"a.xml": SIMPLE_XML})
    records = collect_sentences(tmp_path / "Test")
    md = format_markdown(records, tmp_path / "Test")
    assert "`S1`" in md
    assert "ami" in md
    assert "Halo (orig)." in md
    assert "Halo (std)." in md
    assert "Hello." in md
    assert "你好。" in md
    assert "s1.wav" in md


def test_format_markdown_omits_standard_when_identical_to_original(tmp_path):
    """If standard tier is byte-equal to original, skip the redundant line."""
    _write_corpus(tmp_path, "Test", {"a.xml": SIMPLE_XML})
    records = collect_sentences(tmp_path / "Test")
    s2 = next(r for r in records if r["s_id"] == "S2")
    md = format_markdown([s2], tmp_path / "Test")
    assert "**Original:** Solid." in md
    assert "**Standard:**" not in md


def test_main_with_seed_is_reproducible(tmp_path, capsys):
    """Same seed produces same sample."""
    _write_corpus(tmp_path, "Test", {"a.xml": SIMPLE_XML})
    main(["--corpus_path", str(tmp_path / "Test"), "--n", "1", "--seed", "7"])
    first = capsys.readouterr().out
    main(["--corpus_path", str(tmp_path / "Test"), "--n", "1", "--seed", "7"])
    second = capsys.readouterr().out
    assert first == second


def test_main_caps_n_at_available_S_count(tmp_path, capsys):
    """Requesting more than available samples all available without error."""
    _write_corpus(tmp_path, "Test", {"a.xml": SIMPLE_XML})
    rc = main([
        "--corpus_path", str(tmp_path / "Test"),
        "--n", "100",
        "--seed", "1",
    ])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Sample size: **2**" in out


def test_main_returns_nonzero_when_corpus_empty(tmp_path, capsys):
    """Empty corpus exits nonzero with a clear stderr message."""
    (tmp_path / "Empty" / "XML").mkdir(parents=True)
    rc = main(["--corpus_path", str(tmp_path / "Empty"), "--n", "5"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "No <S> elements found" in err


def test_main_writes_output_file_when_requested(tmp_path):
    """--output writes to disk instead of stdout."""
    _write_corpus(tmp_path, "Test", {"a.xml": SIMPLE_XML})
    out_file = tmp_path / "report" / "sample.md"
    rc = main([
        "--corpus_path", str(tmp_path / "Test"),
        "--n", "1",
        "--seed", "3",
        "--output", str(out_file),
    ])
    assert rc == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "S id" in content

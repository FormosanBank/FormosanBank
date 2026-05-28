"""Smoke test: verify the test infrastructure is operational.

This test exists only to confirm that pytest discovers files, conftest
fixtures resolve, the fixtures directory is reachable, and the audio
factory produces a working file. Once real tests cover this ground
incidentally, the smoke test can be deleted (see Task 2)."""
from pathlib import Path


def test_repo_root_fixture_resolves(repo_root):
    assert repo_root.is_dir()
    assert (repo_root / "QC").is_dir(), "expected QC/ under repo root"


def test_fixtures_dir_resolves(fixtures_dir):
    assert fixtures_dir.is_dir()
    assert fixtures_dir.name == "fixtures"


def test_valid_minimal_xml_is_findable(valid_minimal_xml):
    assert valid_minimal_xml.is_file()
    assert valid_minimal_xml.read_text().startswith("<?xml")


def test_audio_factory_generates_a_wav(audio_file_factory):
    p: Path = audio_file_factory(duration_sec=0.1)
    assert p.is_file()
    assert p.suffix == ".wav"
    assert p.stat().st_size > 0

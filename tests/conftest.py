"""Shared fixtures for the FormosanBank test suite."""
import shutil
import sys
import wave
from pathlib import Path
from typing import Callable

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"

# Make tests/_helpers.py importable from every test file under tests/.
# Pytest's default "prepend" import mode adds each test FILE's directory
# to sys.path (so tests/cleaners/ for a test in that bucket), not tests/
# itself. Without this line, `from _helpers import ...` in a bucket file
# raises ModuleNotFoundError. Inserting tests/ directly fixes that
# without adding __init__.py files (which would change pytest's
# discovery behavior).
sys.path.insert(0, str(Path(__file__).resolve().parent))


@pytest.fixture
def repo_root() -> Path:
    """Path to the FormosanBank repo root. Available for future tests that
    need to address files outside tests/."""
    return REPO_ROOT


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def copy_fixture():
    """Return a helper that copies a fixture into dest_dir/XML/ for in-place mutation.

    Signature: `copy_fixture(src: Path, dest_dir: Path) -> Path`.

    - `src`: the source fixture under tests/fixtures/.
    - `dest_dir`: the COLLECTION root (typically `tmp_path`). The file is
      placed at `dest_dir/XML/<basename>`, and `dest_dir/XML/` is created
      if absent. Callers pass `dest_dir` (not `dest_dir/XML/`) to the QC
      script as `--corpora_path`: the script treats it as a collection
      root and enumerates its immediate children as corpus directories,
      then walks each one for files containing `XML` in the path.

    Returns the path to the placed copy so the caller can assert on its
    post-run state without re-reading the source-of-truth fixture.
    """
    def _copy(src: Path, dest_dir: Path) -> Path:
        target_dir = dest_dir / "XML"
        target_dir.mkdir(parents=True, exist_ok=True)
        copy = target_dir / src.name
        shutil.copy(src, copy)
        return copy
    return _copy


@pytest.fixture
def valid_minimal_xml(fixtures_dir) -> Path:
    return fixtures_dir / "valid_minimal.xml"


@pytest.fixture
def audio_file_factory(tmp_path) -> Callable[..., Path]:
    """Return a callable that generates a silent WAV at the given duration."""
    counter = 0
    def make(duration_sec: float = 1.0, sample_rate: int = 8000) -> Path:
        nonlocal counter
        counter += 1
        path = tmp_path / f"silent_{counter}_{duration_sec}s.wav"
        n_frames = int(duration_sec * sample_rate)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            w.writeframes(b"\x00\x00" * n_frames)
        return path
    return make

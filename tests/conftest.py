"""Shared fixtures for the FormosanBank test suite."""
import shutil
import wave
from pathlib import Path
from typing import Callable

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def copy_fixture():
    """Return a helper that copies a fixture into tmp_path/XML/ for in-place mutation.

    The QC scripts treat --corpora_path as a collection root and enumerate its
    immediate children as corpus directories. Placing the file in dest_dir/XML/
    means the script discovers it via the standard directory walk. The caller
    should pass dest_dir (the collection root) to --corpora_path.
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

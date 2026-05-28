"""Shared fixtures for the FormosanBank test suite."""
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
def valid_minimal_xml(fixtures_dir) -> Path:
    return fixtures_dir / "valid_minimal.xml"


@pytest.fixture
def audio_file_factory(tmp_path) -> Callable[..., Path]:
    """Return a callable that generates a silent WAV at the given duration."""
    def make(duration_sec: float = 1.0, sample_rate: int = 8000) -> Path:
        path = tmp_path / f"silent_{duration_sec}s.wav"
        n_frames = int(duration_sec * sample_rate)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            w.writeframes(b"\x00\x00" * n_frames)
        return path
    return make

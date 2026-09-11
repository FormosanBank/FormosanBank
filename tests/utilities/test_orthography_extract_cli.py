"""The orthography extractor's language allowlist comes from the registry.

`orthography_extract.py` kept its own list of Formosan languages and
validated `--language` against it. That list was a fourth hardcoded copy
of the code -> name table POL-039 exists to prevent, and it had gone
stale exactly the way POL-039 predicts: it was missing
`Babuza-Favorlang` and `Pazeh`, so the CLI rejected two languages that
`languages.csv` registers and that have published corpora. A corpus that
needed one of them had to bypass the CLI and call the module's internals
instead.

These tests pin the allowlist to `languages.csv` so the copy cannot come
back. They drive the real command line, because that is where the defect
lived -- the extraction functions were always reachable.
"""
import subprocess
import sys
from pathlib import Path

import pytest

from QC.corpus_counts import LANGUAGE_NAMES

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "QC" / "orthography" / "orthography_extract.py"
REJECTION = "Enter a valid Formosan language"


def _run(tmp_path: Path, language: str) -> subprocess.CompletedProcess:
    """Invoke the CLI against an empty but existing corpora path.

    The path check runs before the language check, so the directory has
    to exist for the language argument to be reached at all. With no XML
    under it the run finds nothing and exits cleanly, which is enough to
    tell "language accepted" from "language rejected".
    """
    return subprocess.run(
        [
            sys.executable, str(SCRIPT),
            "--corpora_path", str(tmp_path),
            "--corpus", "all",
            "--language", language,
            "--output_dir", str(tmp_path / "out"),
        ],
        capture_output=True, text=True, cwd=str(REPO_ROOT), check=False,
    )


@pytest.mark.parametrize("language", LANGUAGE_NAMES)
def test_cli_accepts_every_registered_language(tmp_path, language):
    result = _run(tmp_path, language)
    assert REJECTION not in result.stderr, (
        f"{language} is in languages.csv but the CLI rejected it:\n"
        f"{result.stderr}"
    )
    assert result.returncode == 0, result.stderr


def test_cli_accepts_the_two_languages_the_hardcoded_list_omitted(tmp_path):
    """The specific regression: both have published corpora."""
    for language in ("Babuza-Favorlang", "Pazeh"):
        assert language in LANGUAGE_NAMES
        assert REJECTION not in _run(tmp_path, language).stderr


def test_cli_still_rejects_an_unregistered_language(tmp_path):
    """Widening the allowlist must not turn it into no allowlist."""
    result = _run(tmp_path, "Klingon")
    assert result.returncode != 0
    assert REJECTION in result.stderr


def test_allowlist_is_not_restated_in_the_module():
    """Guard against the hardcoded copy being reintroduced.

    The module must reach the registry through `LANGUAGE_NAMES` and not
    spell any language name itself.
    """
    source = SCRIPT.read_text(encoding="utf-8")
    assert "LANGUAGE_NAMES" in source
    spelled = sorted(
        name for name in LANGUAGE_NAMES
        # 'All' is the CLI's own sentinel, not a language name.
        if name != "All" and f"'{name}'" in source or f'"{name}"' in source
    )
    assert not spelled, f"language names hardcoded in the extractor: {spelled}"


def test_truku_is_reachable_from_the_registry():
    """Truku is `trv` plus dialect, not its own ISO code, so it is the
    one name that cannot come from `languages.csv` alone. It must still
    be offered -- dropping it while replacing the hardcoded list would
    be a silent regression."""
    assert "Truku" in LANGUAGE_NAMES
    assert "Seediq" in LANGUAGE_NAMES

#!/usr/bin/env python3
"""Tests for check-venv.py hook."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).parent / "check-venv.py"

PASS = 0
FAIL = 0


def check(condition: bool, label: str) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"PASS: {label}")
    else:
        FAIL += 1
        print(f"FAIL: {label}")


def run_hook(project_dir: Path) -> tuple[int, str, str]:
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.returncode, proc.stdout, proc.stderr


def test_silent_when_venv_and_deps_ok() -> None:
    """If a usable .venv with required deps exists, the hook prints nothing."""
    # Use the FormosanBank repo's own .venv as a known-good fixture.
    formosanbank_root = Path(__file__).resolve().parents[2]
    code, out, _ = run_hook(formosanbank_root)
    check(code == 0, "silent OK -> exit 0")
    check(out.strip() == "", f"silent OK -> empty stdout (got: {out!r})")


def test_warns_when_venv_missing() -> None:
    """In a FormosanBank-ecosystem repo (marked by requirements.txt) with no .venv, warn."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "requirements.txt").touch()  # marker for FormosanBank heuristic
        code, out, _ = run_hook(root)
        # We don't fail-block on missing venv; just warn.
        check(code == 0, "missing venv -> exit 0 (warning only)")
        check("venv" in out.lower(), f"missing venv -> warning mentions venv (got: {out!r})")


def test_warns_when_venv_missing_python() -> None:
    """A .venv directory exists but bin/python3 doesn't."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "requirements.txt").touch()  # marker for FormosanBank heuristic
        (root / ".venv").mkdir()
        code, out, _ = run_hook(root)
        check(code == 0, "broken venv -> exit 0")
        check("python" in out.lower() or "venv" in out.lower(),
              f"broken venv -> warning (got: {out!r})")


def test_silent_in_non_formosanbank_dir() -> None:
    """If the directory doesn't look like a FormosanBank repo, don't warn even if .venv is missing."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # No requirements.txt / Corpora / XML / Final_XML — heuristic should not fire.
        code, out, _ = run_hook(root)
        check(code == 0, "non-FormosanBank dir -> exit 0")
        check(out.strip() == "",
              f"non-FormosanBank dir -> silent (got: {out!r})")


if __name__ == "__main__":
    test_silent_when_venv_and_deps_ok()
    test_warns_when_venv_missing()
    test_warns_when_venv_missing_python()
    test_silent_in_non_formosanbank_dir()
    print(f"\n{PASS} pass, {FAIL} fail")
    sys.exit(0 if FAIL == 0 else 1)

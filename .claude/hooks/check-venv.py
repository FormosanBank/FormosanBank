#!/usr/bin/env python3
"""SessionStart hook: verify .venv exists in project root and has expected deps.

Silent on success; prints a single-line warning to stdout on any problem so
Claude (reading session context) knows not to blindly invoke python commands
that will fail. Never fail-blocks the session start (always exits 0).
"""
import os
import subprocess
import sys
from pathlib import Path


# Load-bearing deps from FormosanBank/requirements.txt. Keep this list short:
# importing slow deps (e.g. matplotlib) adds session-start latency.
REQUIRED_IMPORTS = ["lxml", "pandas", "regex"]


def project_root() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env).resolve()
    return Path.cwd().resolve()


def warn(msg: str) -> None:
    """Single-line warning to stdout (becomes session context Claude reads)."""
    print(f"[venv-check] WARNING: {msg}")


def main() -> int:
    root = project_root()
    venv_python = root / ".venv" / "bin" / "python3"

    if not venv_python.exists():
        # Don't warn for arbitrary directories — only complain if this looks
        # like a FormosanBank-ecosystem repo (has requirements.txt OR Corpora/
        # OR XML/ — heuristic).
        if not _looks_like_formosanbank(root):
            return 0
        warn(
            f".venv/bin/python3 not found in {root}. "
            f"Run 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt' "
            f"(or invoke the setup-new-dev-repo skill for a fresh dev repo) "
            f"before running QC scripts."
        )
        return 0

    # Test that key deps import.
    import_check = "; ".join(f"import {m}" for m in REQUIRED_IMPORTS)
    proc = subprocess.run(
        [str(venv_python), "-c", import_check],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        # Stderr has the ImportError. Surface module name if possible.
        err = (proc.stderr or "").strip().splitlines()[-1] if proc.stderr else "import failed"
        warn(
            f".venv at {root}/.venv exists but a required dep is missing: {err}. "
            f"Run '.venv/bin/pip install -r requirements.txt'."
        )

    return 0


def _looks_like_formosanbank(root: Path) -> bool:
    """Heuristic: is this a FormosanBank-ecosystem repo worth warning about?"""
    if (root / "requirements.txt").exists():
        return True
    if (root / "Corpora").is_dir():
        return True
    if (root / "XML").is_dir() or (root / "Final_XML").is_dir():
        return True
    return False


if __name__ == "__main__":
    sys.exit(main())

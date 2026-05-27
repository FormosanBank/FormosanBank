#!/usr/bin/env python3
"""PreToolUse hook: block Edit/Write/MultiEdit/NotebookEdit on files under statistics/.

statistics/ is auto-managed by .github/workflows/corpus-metrics.yaml.
CLAUDE.md mandates "do not hand-edit"; this hook enforces it.
"""
import json
import os
import sys
from pathlib import Path


def repo_root() -> Path:
    """Resolve repo root from $CLAUDE_PROJECT_DIR, falling back to cwd."""
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env).resolve()
    return Path.cwd().resolve()


def is_under_statistics(file_path: str, root: Path) -> bool:
    """True if file_path resolves inside <root>/statistics/."""
    if not file_path:
        return False
    try:
        target = Path(file_path).resolve()
        protected = (root / "statistics").resolve()
        target.relative_to(protected)
        return True
    except (ValueError, OSError):
        return False


def collect_paths(tool_name: str, tool_input: dict) -> list[str]:
    """Return the file paths a given tool call would write to."""
    paths: list[str] = []
    if tool_name in ("Edit", "Write", "MultiEdit"):
        fp = tool_input.get("file_path")
        if fp:
            paths.append(fp)
    elif tool_name == "NotebookEdit":
        np = tool_input.get("notebook_path")
        if np:
            paths.append(np)
    return paths


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # Not JSON; don't block. The harness will continue.
        return 0

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}
    root = repo_root()

    for path in collect_paths(tool_name, tool_input):
        if is_under_statistics(path, root):
            print(
                f"Blocked: {path} is under statistics/.\n"
                f"This directory is auto-managed by .github/workflows/corpus-metrics.yaml. "
                f"Don't hand-edit. To change what gets committed, modify the workflow "
                f"or upstream data (QC/corpus_metrics.py etc.). If you have a genuine "
                f"reason to override, disable this hook in .claude/settings.local.json.",
                file=sys.stderr,
            )
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""PreToolUse hook: ask before tool calls that look like Private→FormosanBank leakage.

Two checks:

1. Bash: if a command mentions both `Private/` and `Corpora/` paths, ask
   before running. The main leak vector port-corpus-in is trying to prevent
   is a `cp Private/X Corpora/Y/`-style copy; substring matching catches
   that plus near-misses.

2. Edit/Write/MultiEdit/NotebookEdit: if the target file is under
   `<project>/Corpora/<X>/...` AND a file of the same basename exists under
   any sibling `<project_parent>/Formosan-*/Private/` dir, ask. Basename
   match isn't proof of leak (both can legitimately have a README.md) but
   it's worth a beat.

Intentionally "ask", not "deny": the operator decides. The deterministic
content-hash check in port-corpus-in.md Phase 4 is the backstop; this hook
is preventive defense-in-depth.

Always exits 0 (errors are swallowed so a bug here can't wedge the harness);
emits JSON `permissionDecision: "ask"` to surface to the user.
"""
import json
import os
import sys
from pathlib import Path
from typing import Any


def project_root() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env).resolve()
    return Path.cwd().resolve()


def emit_ask(reason: str) -> None:
    sys.stdout.write(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }))


def check_bash(command: str) -> str | None:
    if not command:
        return None
    if "Private/" in command and "Corpora/" in command:
        return (
            "Command mentions both `Private/` and `Corpora/` paths. Per "
            "port-corpus-in, nothing from a dev repo's `Private/` should "
            "land in the published `Corpora/`. Confirm this is intentional."
        )
    return None


def list_private_basenames(parent: Path) -> set[str]:
    """Basenames of every file under any sibling `Formosan-*/Private/` dir."""
    names: set[str] = set()
    try:
        for repo in parent.glob("Formosan-*"):
            priv = repo / "Private"
            if not priv.is_dir():
                continue
            for f in priv.rglob("*"):
                if f.is_file():
                    names.add(f.name)
    except OSError:
        pass
    return names


def check_edit(file_path: str, root: Path) -> str | None:
    if not file_path:
        return None
    try:
        target = Path(file_path).resolve()
    except (ValueError, OSError):
        return None
    corpora = (root / "Corpora").resolve()
    try:
        target.relative_to(corpora)
    except ValueError:
        return None
    priv_names = list_private_basenames(root.parent)
    if target.name in priv_names:
        return (
            f"Target `{target.name}` shares a basename with a file under a "
            f"sibling `Formosan-*/Private/` dir. May be a coincidence (both "
            f"repos can have README.md) or a private-content leak. Confirm."
        )
    return None


def collect_edit_path(tool_name: str, tool_input: Any) -> str:
    if not isinstance(tool_input, dict):
        return ""
    if tool_name in ("Edit", "Write", "MultiEdit"):
        return tool_input.get("file_path") or ""
    if tool_name == "NotebookEdit":
        return tool_input.get("notebook_path") or ""
    return ""


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}
    root = project_root()

    if tool_name == "Bash":
        command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
        reason = check_bash(command)
        if reason:
            emit_ask(reason)
        return 0

    if tool_name in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        fp = collect_edit_path(tool_name, tool_input)
        reason = check_edit(fp, root)
        if reason:
            emit_ask(reason)
        return 0

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        sys.stderr.write(f"check-private-leaks hook error: {e}\n")
        sys.exit(0)

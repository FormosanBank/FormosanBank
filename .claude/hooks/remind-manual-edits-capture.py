#!/usr/bin/env python3
"""PostToolUse hook: after Edit/Write/MultiEdit on published corpus XML,
remind the session that hand edits must be captured (POL-030).

Reads {"tool_name": str, "tool_input": dict} from stdin.
Exits 2 so the reminder on stderr is fed back to Claude (the edit has
already happened — this warns, it does not block). Exits 0 otherwise.

Scope: files matching Corpora/**/XML/**/*.xml. Direct hand edits to
published XML are lost on the next pipeline regeneration unless recorded
in that corpus's CodeAndDocs/manual_edits.xml via
QC/utilities/capture_manual_edits.py. Pipeline scripts write these files
via Bash, not Edit/Write, so this hook only fires on interactive edits.
"""
import json
import os
import sys
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env).resolve()
    return Path.cwd().resolve()


def is_published_corpus_xml(file_path: str, root: Path) -> bool:
    """True if file_path is an .xml file under <root>/Corpora/**/XML/."""
    if not file_path or not file_path.endswith(".xml"):
        return False
    try:
        target = Path(file_path).resolve()
        relative = target.relative_to((root / "Corpora").resolve())
    except (ValueError, OSError):
        return False
    return "XML" in relative.parts[:-1]


def collect_paths(tool_name: str, tool_input: Any) -> list[str]:
    paths: list[str] = []
    if not isinstance(tool_input, dict):
        return paths
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
        return 0

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}
    root = repo_root()

    for path in collect_paths(tool_name, tool_input):
        if is_published_corpus_xml(path, root):
            print(
                f"Reminder (POL-030): {path} is published corpus XML. "
                f"A direct hand edit here is LOST on the next pipeline "
                f"regeneration unless it is recorded. Before committing, run:\n"
                f"  python QC/utilities/capture_manual_edits.py "
                f"--corpora_path <that corpus's XML dir>\n"
                f"to record the edit in CodeAndDocs/manual_edits.xml. "
                f"(Also: never hand-edit standard FORMs or PHON — they are "
                f"regenerated; edit the original tier instead, POL-002/003.) "
                f"The edit itself went through; this is a reminder, not a block.",
                file=sys.stderr,
            )
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Tests for remind-manual-edits-capture.py hook. Hand-rolled PASS/FAIL
counter matching the repo's existing hook-test style."""
import json
import os
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).parent / "remind-manual-edits-capture.py"
REPO_ROOT = Path(__file__).resolve().parents[2]  # .claude/hooks/ -> repo root

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


def run_hook(payload: dict) -> tuple[int, str]:
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(REPO_ROOT)
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.returncode, proc.stderr


def main() -> int:
    corpus_xml = str(REPO_ROOT / "Corpora" / "ePark" / "XML" / "a.xml")
    nested_xml = str(
        REPO_ROOT / "Corpora" / "Wikipedias" / "XML" / "Amis" / "b.xml")
    code, err = run_hook(
        {"tool_name": "Edit", "tool_input": {"file_path": corpus_xml}})
    check(code == 2 and "capture_manual_edits" in err,
          "Edit on Corpora/*/XML/*.xml triggers reminder")
    check("not a block" in err, "reminder says it is not a block")

    code, err = run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": nested_xml}})
    check(code == 2, "Write on nested XML/<lang>/ file triggers reminder")

    code, _ = run_hook({
        "tool_name": "Edit",
        "tool_input": {"file_path": str(
            REPO_ROOT / "Corpora" / "ePark" / "CodeAndDocs" / "build.py")},
    })
    check(code == 0, "CodeAndDocs edits pass silently")

    code, _ = run_hook({
        "tool_name": "Edit",
        "tool_input": {"file_path": str(
            REPO_ROOT / "Corpora" / "ePark" / "XML" / "notes.md")},
    })
    check(code == 0, "non-.xml file under XML/ passes silently")

    code, _ = run_hook({
        "tool_name": "Edit",
        "tool_input": {"file_path": str(
            REPO_ROOT / "QC" / "cleaning" / "clean_xml.py")},
    })
    check(code == 0, "edits outside Corpora/ pass silently")

    code, _ = run_hook({"tool_name": "Bash", "tool_input": {"command": "ls"}})
    check(code == 0, "non-edit tools pass silently")

    proc = subprocess.run(
        [sys.executable, str(HOOK)], input="not json",
        capture_output=True, text=True)
    check(proc.returncode == 0, "malformed stdin passes silently")

    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())

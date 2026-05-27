#!/usr/bin/env python3
"""Tests for block-statistics-edits.py hook. Hand-rolled PASS/FAIL counter
matching the repo's existing test style (see QC/test_find_duplicate_sentences.py)."""
import json
import os
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).parent / "block-statistics-edits.py"
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


def run_hook(tool_input: dict) -> tuple[int, str]:
    """Run the hook with given input, return (exit_code, stderr)."""
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(REPO_ROOT)
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(tool_input),
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.returncode, proc.stderr


def test_blocks_edit_to_statistics() -> None:
    code, err = run_hook({
        "tool_name": "Edit",
        "tool_input": {"file_path": str(REPO_ROOT / "statistics/corpus_size_history.csv")},
    })
    check(code == 2, "blocks Edit on statistics/ file (exit 2)")
    check("statistics/" in err, "explanatory message mentions statistics/")


def test_blocks_write_to_statistics() -> None:
    code, _ = run_hook({
        "tool_name": "Write",
        "tool_input": {"file_path": str(REPO_ROOT / "statistics/new_chart.png")},
    })
    check(code == 2, "blocks Write on statistics/ file")


def test_blocks_multiedit_to_statistics() -> None:
    code, _ = run_hook({
        "tool_name": "MultiEdit",
        "tool_input": {"file_path": str(REPO_ROOT / "statistics/anything.csv")},
    })
    check(code == 2, "blocks MultiEdit on statistics/ file")


def test_blocks_notebookedit_to_statistics() -> None:
    code, _ = run_hook({
        "tool_name": "NotebookEdit",
        "tool_input": {"notebook_path": str(REPO_ROOT / "statistics/foo.ipynb")},
    })
    check(code == 2, "blocks NotebookEdit on statistics/ notebook")


def test_allows_edit_elsewhere() -> None:
    code, _ = run_hook({
        "tool_name": "Edit",
        "tool_input": {"file_path": str(REPO_ROOT / "QC/something.py")},
    })
    check(code == 0, "allows Edit on non-statistics file")


def test_allows_non_matching_tool() -> None:
    code, _ = run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": "ls"},
    })
    check(code == 0, "allows tools other than Edit/Write/MultiEdit/NotebookEdit")


def test_handles_invalid_json() -> None:
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(REPO_ROOT)
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json",
        capture_output=True,
        text=True,
        env=env,
    )
    check(proc.returncode == 0, "handles invalid JSON gracefully (exit 0)")


def test_handles_missing_file_path() -> None:
    code, _ = run_hook({
        "tool_name": "Edit",
        "tool_input": {},
    })
    check(code == 0, "handles missing file_path gracefully")


if __name__ == "__main__":
    test_blocks_edit_to_statistics()
    test_blocks_write_to_statistics()
    test_blocks_multiedit_to_statistics()
    test_blocks_notebookedit_to_statistics()
    test_allows_edit_elsewhere()
    test_allows_non_matching_tool()
    test_handles_invalid_json()
    test_handles_missing_file_path()
    print(f"\n{PASS} pass, {FAIL} fail")
    sys.exit(0 if FAIL == 0 else 1)

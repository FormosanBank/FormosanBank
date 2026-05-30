#!/usr/bin/env python3
"""Tests for check-private-leaks.py hook. Hand-rolled PASS/FAIL counter
matching the repo's existing test style (see test_block_statistics_edits.py)."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).parent / "check-private-leaks.py"
REPO_ROOT = Path(__file__).resolve().parents[2]

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


def run_hook(tool_input: dict, project_dir: str | None = None) -> tuple[int, str, str]:
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = project_dir or str(REPO_ROOT)
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(tool_input),
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.returncode, proc.stdout, proc.stderr


def parsed_decision(stdout: str) -> str:
    try:
        return json.loads(stdout).get("hookSpecificOutput", {}).get("permissionDecision", "")
    except (ValueError, TypeError):
        return ""


def test_bash_with_both_paths_asks() -> None:
    code, out, _ = run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": "cp Formosan-X/Private/secret.txt Corpora/X/"},
    })
    check(code == 0, "Bash double-path: exit 0")
    check(parsed_decision(out) == "ask", "Bash double-path: emits ask")


def test_bash_with_only_private_no_ask() -> None:
    code, out, _ = run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": "ls Formosan-X/Private/"},
    })
    check(code == 0 and parsed_decision(out) == "", "Bash Private-only: no ask")


def test_bash_with_only_corpora_no_ask() -> None:
    code, out, _ = run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": "ls Corpora/X/"},
    })
    check(code == 0 and parsed_decision(out) == "", "Bash Corpora-only: no ask")


def test_bash_with_neither_no_ask() -> None:
    code, out, _ = run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": "ls"},
    })
    check(code == 0 and parsed_decision(out) == "", "Bash neither: no ask")


def _make_layout(tmp: Path, target_name: str = "secret.txt", private_name: str = "secret.txt") -> tuple[Path, Path]:
    """Build a fake project tree with a sibling Formosan-X/Private/ dir.

    Returns (project_root, target_path).
    """
    project = tmp / "FakeFormosanBank"
    (project / "Corpora" / "X").mkdir(parents=True)
    sibling_priv = tmp / "Formosan-X" / "Private"
    sibling_priv.mkdir(parents=True)
    (sibling_priv / private_name).write_text("private!")
    target = project / "Corpora" / "X" / target_name
    target.write_text("public?")
    return project, target


def test_edit_basename_collision_asks() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project, target = _make_layout(Path(tmp))
        code, out, _ = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": str(target)}},
            project_dir=str(project),
        )
        check(code == 0, "Edit basename collision: exit 0")
        check(parsed_decision(out) == "ask", "Edit basename collision: emits ask")


def test_edit_no_basename_collision_no_ask() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project, target = _make_layout(Path(tmp), target_name="different.txt", private_name="secret.txt")
        code, out, _ = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": str(target)}},
            project_dir=str(project),
        )
        check(code == 0 and parsed_decision(out) == "", "Edit no collision: no ask")


def test_edit_outside_corpora_no_ask_even_with_collision() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "FakeFormosanBank"
        project.mkdir()
        sibling_priv = Path(tmp) / "Formosan-X" / "Private"
        sibling_priv.mkdir(parents=True)
        (sibling_priv / "README.md").write_text("private notes")
        target = project / "README.md"
        target.write_text("public readme")
        code, out, _ = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": str(target)}},
            project_dir=str(project),
        )
        check(code == 0 and parsed_decision(out) == "", "Edit outside Corpora: no ask even when basename collides")


def test_write_under_corpora_with_collision_asks() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project, target = _make_layout(Path(tmp), target_name="notes.md", private_name="notes.md")
        code, out, _ = run_hook(
            {"tool_name": "Write", "tool_input": {"file_path": str(target)}},
            project_dir=str(project),
        )
        check(code == 0 and parsed_decision(out) == "ask", "Write under Corpora with collision: ask")


def test_notebookedit_uses_notebook_path() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project, _ = _make_layout(Path(tmp), target_name="dummy.txt", private_name="analysis.ipynb")
        nb = project / "Corpora" / "X" / "analysis.ipynb"
        nb.write_text("{}")
        code, out, _ = run_hook(
            {"tool_name": "NotebookEdit", "tool_input": {"notebook_path": str(nb)}},
            project_dir=str(project),
        )
        check(code == 0 and parsed_decision(out) == "ask", "NotebookEdit reads notebook_path and asks on collision")


def test_no_sibling_private_dir_no_ask() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "FakeFormosanBank"
        (project / "Corpora" / "X").mkdir(parents=True)
        target = project / "Corpora" / "X" / "anything.txt"
        target.write_text("hi")
        code, out, _ = run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": str(target)}},
            project_dir=str(project),
        )
        check(code == 0 and parsed_decision(out) == "", "No sibling Private dir: no ask")


def test_unknown_tool_no_ask() -> None:
    code, out, _ = run_hook({"tool_name": "Read", "tool_input": {"file_path": "/etc/hosts"}})
    check(code == 0 and parsed_decision(out) == "", "non-matching tool: no ask")


def test_invalid_json_handled() -> None:
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(REPO_ROOT)
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json",
        capture_output=True,
        text=True,
        env=env,
    )
    check(proc.returncode == 0, "invalid JSON: exit 0")


def test_missing_file_path_handled() -> None:
    code, out, _ = run_hook({"tool_name": "Edit", "tool_input": {}})
    check(code == 0 and parsed_decision(out) == "", "missing file_path: no ask")


if __name__ == "__main__":
    test_bash_with_both_paths_asks()
    test_bash_with_only_private_no_ask()
    test_bash_with_only_corpora_no_ask()
    test_bash_with_neither_no_ask()
    test_edit_basename_collision_asks()
    test_edit_no_basename_collision_no_ask()
    test_edit_outside_corpora_no_ask_even_with_collision()
    test_write_under_corpora_with_collision_asks()
    test_notebookedit_uses_notebook_path()
    test_no_sibling_private_dir_no_ask()
    test_unknown_tool_no_ask()
    test_invalid_json_handled()
    test_missing_file_path_handled()
    print(f"\n{PASS} pass, {FAIL} fail")
    sys.exit(0 if FAIL == 0 else 1)

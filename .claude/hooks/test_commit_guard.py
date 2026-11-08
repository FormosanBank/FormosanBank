#!/usr/bin/env python3
"""Tests for .githooks/commit-msg. Hand-rolled PASS/FAIL counter matching the
other hook tests. Each case commits in a throwaway git repo."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / ".githooks" / "commit-msg"
PASS = 0
FAIL = 0


def check(condition: bool, label: str) -> None:
    global PASS, FAIL
    PASS, FAIL = (PASS + 1, FAIL) if condition else (PASS, FAIL + 1)
    print(("PASS: " if condition else "FAIL: ") + label)


def commit(paths: list[str], message: str) -> tuple[int, str]:
    repo = Path(tempfile.mkdtemp())
    try:
        run = lambda *a: subprocess.run(["git", *a], cwd=repo, capture_output=True, text=True)
        run("init", "-q")
        run("config", "user.email", "t@example.com")
        run("config", "user.name", "t")
        run("config", "commit.gpgsign", "false")
        hooks = repo / ".git" / "hooks"
        shutil.copy2(HOOK, hooks / "commit-msg")
        for p in paths:
            f = repo / p
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("x\n")
            run("add", p)
        proc = run("commit", "-q", "-m", message)
        return proc.returncode, proc.stderr
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def merge_case(edit_during_merge: bool) -> tuple[int, str]:
    """main changes a shared file (approved); a feature branch merges main in. Optionally the shared
    file is edited further during the merge, so it matches neither side."""
    repo = Path(tempfile.mkdtemp())
    try:
        run = lambda *a: subprocess.run(["git", *a], cwd=repo, capture_output=True, text=True)
        run("init", "-q", "-b", "main")
        for k, v in (("user.email", "t@example.com"), ("user.name", "t"), ("commit.gpgsign", "false")):
            run("config", k, v)
        shutil.copy2(HOOK, repo / ".git" / "hooks" / "commit-msg")
        ok = 'x\n\nShared-change-approved: maintainer 2026-10-17, "OK"'
        (repo / "QC").mkdir(); (repo / "QC" / "tool.py").write_text("v1\n"); run("add", "-A"); run("commit", "-q", "-m", "base" + ok)
        run("checkout", "-q", "-b", "feature")
        (repo / "Corpora").mkdir(); (repo / "Corpora" / "c.xml").write_text("c\n"); run("add", "-A"); run("commit", "-q", "-m", "corpus")
        run("checkout", "-q", "main")
        (repo / "QC" / "tool.py").write_text("v2\n"); run("add", "-A"); run("commit", "-q", "-m", "tool v2" + ok)
        run("checkout", "-q", "feature")
        run("merge", "--no-commit", "--no-ff", "main")
        if edit_during_merge:
            (repo / "QC" / "tool.py").write_text("v3\n"); run("add", "QC/tool.py")
        proc = run("commit", "-q", "-m", "Merge main into feature")
        return proc.returncode, proc.stderr
    finally:
        shutil.rmtree(repo, ignore_errors=True)


code, err = commit(["QC/utilities/add_phonology.py"], "change a tool")
check(code != 0 and "QC/utilities/add_phonology.py" in err, "shared tool without trailer is refused, naming the file")
code, _ = commit(["QC/utilities/add_phonology.py"],
                 'change a tool\n\nShared-change-approved: maintainer 2026-10-16, "OK"')
check(code == 0, "shared tool with the approval trailer is allowed")
code, _ = commit(["Corpora/ILRDF_Dicts/XML/Amis/Amis.xml", "tests/corpora/test_x.py",
                  "generate_xml_pending.txt", "claudeplans/note.md"], "corpus work")
check(code == 0, "corpus files, corpus tests, pending list and claudeplans need no approval")
code, err = commit(["rights_vocabulary.csv"], "vocabulary")
check(code != 0 and "rights_vocabulary.csv" in err, "a root CSV is a shared file")
code, err = commit(["POLICIES.md", "Corpora/X/README.md"], "policy + corpus")
check(code != 0 and "POLICIES.md" in err and "Corpora/X" not in err, "only the shared file is named")

code, err = merge_case(edit_during_merge=False)
check(code == 0, "a merge bringing in the other side's shared change unaltered needs no trailer")
code, err = merge_case(edit_during_merge=True)
check(code != 0 and "QC/tool.py" in err, "a merge whose shared file matches neither side is refused")

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)

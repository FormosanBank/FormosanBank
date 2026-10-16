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

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)

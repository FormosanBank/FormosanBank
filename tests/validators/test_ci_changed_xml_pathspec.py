"""The CI pathspec for "changed corpus XML" must mean what it says.

xml-validation.yaml and audio-validation.yaml select the files a PR touches
under `Corpora/<name>/XML/`. Both used `'Corpora/**/XML/**/*.xml'`, and in a
default git pathspec `*` matches `/` as well, so the pattern also selected
`Corpora/<name>/CodeAndDocs/pre_correction_snapshot/XML/...` -- POL-035
baselines, which are build inputs, not published data.

Validating a snapshot as if it were published raises HARD `V081`
(`text_id_unique_across_published_corpora`) against the very corpus it is the
baseline for, and an added file has an empty baseline, so every HARD finding
counts as new and blocks the PR. Two corpora already ship such a snapshot
(SEALS33, WakelinTexts); the third to add one hit it.

The fix is `:(glob)` magic, under which `*` stops at `/` and `**` does not.
These tests pin both the pattern and the behaviour.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ("xml-validation.yaml", "audio-validation.yaml")
EXPECTED = "':(glob)Corpora/*/XML/**/*.xml'"

CANONICAL = "Corpora/Example/XML/Amis/text.xml"
SNAPSHOT = "Corpora/Example/CodeAndDocs/pre_correction_snapshot/XML/Amis/text.xml"


def _workflow(name: str) -> str:
    return (REPO_ROOT / ".github/workflows" / name).read_text(encoding="utf-8")


@pytest.mark.parametrize("name", WORKFLOWS)
def test_workflow_uses_the_anchored_pathspec(name):
    text = _workflow(name)
    assert EXPECTED in text, (
        f"{name} should select changed corpus XML with {EXPECTED}"
    )


@pytest.mark.parametrize("name", WORKFLOWS)
def test_workflow_has_no_unanchored_corpora_pathspec(name):
    """`Corpora/**/XML/**` without :(glob) is the bug; it must not come back.

    Comment lines are skipped: both workflows quote the old pattern while
    explaining why it was wrong.
    """
    stray = [
        line.strip()
        for line in _workflow(name).splitlines()
        if not line.lstrip().startswith("#")
        and re.search(r"(?<!:\(glob\))'Corpora/\*\*/XML[^']*'", line)
    ]
    assert not stray, f"{name} still has an unanchored pathspec: {stray}"


def test_pathspec_selects_published_xml_and_not_a_snapshot(tmp_path):
    """The behaviour itself, against a real git index.

    Guards the semantics rather than the string: a rewrite that keeps the
    literal but changes the meaning still fails here.
    """
    run = lambda *a: subprocess.run(  # noqa: E731
        a, cwd=tmp_path, capture_output=True, text=True, check=True)
    run("git", "init", "-q")
    run("git", "config", "user.email", "t@t")
    run("git", "config", "user.name", "t")
    for rel in (CANONICAL, SNAPSHOT):
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("<TEXT/>", encoding="utf-8")
    run("git", "add", "-A")
    run("git", "commit", "-qm", "both")

    selected = run("git", "show", "--name-only", "--format=", "HEAD",
                   "--", ":(glob)Corpora/*/XML/**/*.xml").stdout.split()
    assert CANONICAL in selected, "published XML must be validated"
    assert SNAPSHOT not in selected, (
        "a POL-035 snapshot is a build input and must not be validated as "
        "published data"
    )


# By default git C-quotes a path with non-ASCII bytes
# ("Corpora/.../Cond\303\251.xml"), a name no file has. The validators read 0
# files from it and xml-validation's stage 1 passed 211 Wikipedia files it never
# opened; validate_glosses wrote no CSV and stage 2 crashed.
QUOTE_PATH_WORKFLOWS = WORKFLOWS + ("hf-audio-parity.yaml",)
NON_ASCII = "Corpora/Example/XML/Amis/Alpha_Condé.xml"


@pytest.mark.parametrize("name", QUOTE_PATH_WORKFLOWS)
def test_workflow_lists_changed_paths_unquoted(name):
    listings = [line for line in _workflow(name).splitlines()
                if "--name-only" in line and not line.lstrip().startswith("#")]
    assert listings and all("-c core.quotePath=false" in l for l in listings), (
        f"{name} must list changed paths with git -c core.quotePath=false"
    )


def test_non_ascii_path_is_listed_as_its_real_name(tmp_path):
    run = lambda *a: subprocess.run(  # noqa: E731
        a, cwd=tmp_path, capture_output=True, text=True, check=True)
    run("git", "init", "-q")
    run("git", "config", "user.email", "t@t")
    run("git", "config", "user.name", "t")
    target = tmp_path / NON_ASCII
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("<TEXT/>", encoding="utf-8")
    run("git", "add", "-A")
    run("git", "commit", "-qm", "one")

    listed = run("git", "-c", "core.quotePath=false", "show", "--name-only",
                 "--format=", "HEAD", "--", ":(glob)Corpora/*/XML/**/*.xml"
                 ).stdout.splitlines()
    assert listed == [NON_ASCII]
    assert (tmp_path / listed[0]).is_file()

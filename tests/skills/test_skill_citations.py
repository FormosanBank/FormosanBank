"""The five dev-repo skills cite real paths and real flags.

A skill is prose that names scripts, flags and files. Nothing ran against those
names until now, and the 2026-10-11 prompt audit found six of them wrong for
four months (a validate_glosses.py call that had failed argparse since June, a
deprecated --soft-csv flag, "DTD" for "XSD", a pointer to a skill that does
not exist); the October review found four more. Two checks:

* every repository path a skill or its templates name exists;
* every `--flag` on a command line that invokes a QC script is accepted by
  that script — by the subcommand it names, when it names one — as reported
  by `--help`.

Paths under claudeplans/ are not checked: that directory is working notes,
largely untracked by design (the decision log lives there), so CI cannot see
it. Placeholders (`<xml_path>`, `{{NAME}}`, globs) are skipped.
"""
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import pytest

from tests._helpers import REPO_ROOT

SKILLS_DIR = REPO_ROOT / ".claude" / "skills"
SKILLS = ("audit-dev-repo", "port-corpus-in", "run-qc-pipeline",
          "audit-gloss-scrape", "setup-new-dev-repo")

#: Repo-relative paths worth checking: a known top-level directory, then a
#: path with a file extension or a trailing slash.
PATH_RE = re.compile(
    r"(?<![\w/.-])((?:QC|tests|docs|Orthographies|statistics|Corpora|\.claude|\.github)"
    r"/[^\s`'\")\]]*)")
PLACEHOLDER_RE = re.compile(r"[<>{}*]|\.\.\.|…")
SCRIPT_RE = re.compile(r"(QC/[A-Za-z0-9_/]+\.py)")
MODULE_RE = re.compile(r"-m\s+(QC(?:\.[A-Za-z0-9_]+)+)")
FLAG_RE = re.compile(r"(?<![\w-])(--[a-z][a-z0-9_-]*)")
SUBCOMMANDS = ("by_path", "by_corpus", "by_language", "predict", "train",
               "evaluate", "crossvalidate")


def skill_files() -> list[Path]:
    files = []
    for skill in SKILLS:
        files.append(SKILLS_DIR / skill / "SKILL.md")
        files.extend(sorted((SKILLS_DIR / skill).glob("*.template.md")))
    return files


def cited_paths(text: str) -> set[str]:
    """Concrete repo-relative paths named anywhere in the text."""
    text = text.replace("<formosanbank_path>/", "").replace("$FB/", "")
    out = set()
    for match in PATH_RE.findall(text):
        path = match.rstrip(".,;:")
        if PLACEHOLDER_RE.search(path):
            continue      # <xml_path>, {{NAME}}, globs, ellipses
        if path.endswith("/"):
            path = path[:-1]
        out.add(path)
    return out


def cited_commands(text: str) -> dict[tuple[str, str], set[str]]:
    """{(script-or-module, subcommand): flags} for every QC invocation in a code block."""
    commands: dict[tuple[str, str], set[str]] = {}
    for block in re.findall(r"```(?:bash|sh)?\n(.*?)```", text, re.S):
        joined = re.sub(r"\\\n\s*", " ", block)           # shell continuations
        for line in joined.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = SCRIPT_RE.search(line) or MODULE_RE.search(line)
            if not match:
                continue
            target = match.group(1)
            rest = line[match.end():]
            tokens = rest.split()
            sub = tokens[0] if tokens and tokens[0] in SUBCOMMANDS else ""
            flags = set(FLAG_RE.findall(rest))
            commands.setdefault((target, sub), set()).update(flags)
    return commands


@lru_cache(maxsize=None)
def help_text(target: str, sub: str) -> str | None:
    """`--help` of a script (path) or module (dotted), with the subcommand if given."""
    if "/" in target:
        cmd = [sys.executable, str(REPO_ROOT / target)]
    else:
        cmd = [sys.executable, "-m", target]
    if sub:
        cmd.append(sub)
    cmd.append("--help")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                              cwd=REPO_ROOT, env={**__import__("os").environ,
                                                  "PYTHONPATH": str(REPO_ROOT)})
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout + proc.stderr


def stale_citations(text: str, repo_root: Path, help_lookup=help_text) -> list[str]:
    """Everything the text cites that does not hold: missing paths, unknown flags."""
    problems = []
    for path in sorted(cited_paths(text)):
        if path.startswith("claudeplans/"):
            continue
        if not (repo_root / path).exists():
            problems.append(f"path does not exist: {path}")
    for (target, sub), flags in sorted(cited_commands(text).items()):
        if "/" in target and not (repo_root / target).exists():
            continue  # already reported as a missing path
        text_help = help_lookup(target, sub)
        label = f"{target} {sub}".strip()
        if text_help is None:
            problems.append(f"`{label} --help` failed")
            continue
        for flag in sorted(flags):
            if flag not in text_help:
                problems.append(f"{label} does not accept {flag}")
    return problems


# ---------------------------------------------------------------------------
# the checker itself can go red
# ---------------------------------------------------------------------------

def test_checker_reports_a_missing_path_and_an_unknown_flag(tmp_path):
    (tmp_path / "QC" / "validation").mkdir(parents=True)
    (tmp_path / "QC" / "validation" / "validate_xml.py").write_text("", encoding="utf-8")
    text = (
        "Run `QC/validation/validate_xml.py` then read QC/validation/RULES.md and "
        "docs/gone.md.\n\n```bash\n"
        "python QC/validation/validate_xml.py by_path \\\n  --path <xml> --no-exit-on-hard --soft-csv out.csv\n"
        "python QC/utilities/missing_tool.py --anything\n"
        "```\n"
    )
    fake_help = lambda target, sub: "usage: validate_xml.py by_path --path PATH --no-exit-on-hard --csv CSV"
    assert stale_citations(text, tmp_path, fake_help) == [
        "path does not exist: QC/utilities/missing_tool.py",
        "path does not exist: QC/validation/RULES.md",
        "path does not exist: docs/gone.md",
        "QC/validation/validate_xml.py by_path does not accept --soft-csv",
    ]


def test_placeholders_and_claudeplans_are_not_checked(tmp_path):
    text = ("See <formosanbank_path>/QC/<tool>.py, claudeplans/audit-<Name>.md, "
            "tests/fixtures/*.xml and {{OUTPUT_DIR}}/QC/x.py.")
    assert stale_citations(text, tmp_path, lambda t, s: "") == []


# ---------------------------------------------------------------------------
# the real skills
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("skill_file", skill_files(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_skill_cites_only_real_paths_and_flags(skill_file):
    text = skill_file.read_text(encoding="utf-8")
    problems = stale_citations(text, REPO_ROOT)
    assert not problems, (
        f"{skill_file.relative_to(REPO_ROOT)} is stale:\n  " + "\n  ".join(problems)
    )

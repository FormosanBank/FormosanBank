"""POL-044 and POL-055: the two README sections every published corpus carries.

POL-044 (rights documentation) names `tests/corpora/test_rights_documentation.py`
as its implementation; that file never existed. POL-055 (corpus documentation)
says of its `Notes and Issues` section "Nothing lints the name today". This is
both lints:

* `## Rights` with a `**License:** <value>` line equal to the corpus XML's
  `@copyright` (one value across the corpus) and a `**Rights source:**` line;
* a heading named exactly `Notes and Issues` (POL-055: "The section is
  `Notes and Issues` in both places ... legacy spellings to migrate, not
  alternatives").

Legacy READMEs are listed in `readme_sections_pending.txt` at the repo root,
one `<corpus> <check>` pair per line, so a corpus that passes one check is still
held to it. The list only shrinks; a new or re-ported corpus is never added.
"""
import re
from xml.etree import ElementTree as ET

import pytest

from tests._helpers import REPO_ROOT

PENDING_FILE = REPO_ROOT / "readme_sections_pending.txt"
CHECKS = ("rights", "notes")

RIGHTS_HEADING_RE = re.compile(r"^##\s+Rights\s*$", re.M)
LICENSE_LINE_RE = re.compile(r"^\*\*License:\*\*\s*(.+?)\s*$", re.M)
SOURCE_LINE_RE = re.compile(r"^\*\*Rights source:\*\*\s*\S", re.M)
NOTES_HEADING_RE = re.compile(r"^#{1,6}\s+Notes and Issues\s*$", re.M)


def _pending() -> set[tuple[str, str]]:
    if not PENDING_FILE.exists():
        return set()
    pairs = set()
    for line in PENDING_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        corpus, _, check = line.partition(" ")
        pairs.add((corpus, check.strip()))
    return pairs


def _corpora() -> list[str]:
    root = REPO_ROOT / "Corpora"
    return sorted(d.name for d in root.iterdir() if (d / "XML").is_dir())


def _readme_text(corpus: str) -> str | None:
    for name in ("README.md", "readme.md"):
        path = REPO_ROOT / "Corpora" / corpus / name
        if path.exists():
            return path.read_text(encoding="utf-8")
    return None


def _copyrights(corpus: str) -> set[str]:
    """Every distinct TEXT/@copyright in the corpus's published XML."""
    values = set()
    for path in (REPO_ROOT / "Corpora" / corpus / "XML").rglob("*.xml"):
        if "CodeAndDocs" in path.parts:
            continue
        for _event, elem in ET.iterparse(path, events=("start",)):
            values.add((elem.get("copyright") or "").strip())
            break
    return values


def rights_problems(readme: str, copyrights: set[str]) -> list[str]:
    """POL-044: what is wrong with the Rights block, as a list (empty = fine)."""
    problems = []
    if not RIGHTS_HEADING_RE.search(readme):
        problems.append("no '## Rights' heading")
    match = LICENSE_LINE_RE.search(readme)
    if not match:
        problems.append("no '**License:** <value>' line")
    elif copyrights != {match.group(1)}:
        problems.append(
            f"License line says {match.group(1)!r} but the XML @copyright is "
            f"{sorted(copyrights)}"
        )
    if not SOURCE_LINE_RE.search(readme):
        problems.append("no '**Rights source:** <grantor>, <date>; evidence: ...' line")
    return problems


def notes_problems(readme: str) -> list[str]:
    """POL-055: the section must be headed exactly 'Notes and Issues'."""
    if NOTES_HEADING_RE.search(readme):
        return []
    legacy = re.findall(
        r"^#{1,6}\s+((?:Notes|Known|Major|Caveats?|Issues)[^\n]*)$", readme, re.M)
    hint = f" (found {legacy!r}; POL-055 names one spelling)" if legacy else ""
    return [f"no heading named exactly 'Notes and Issues'{hint}"]


CORPORA = _corpora()


def test_pending_list_names_real_corpora_and_checks():
    bad = sorted(
        f"{c} {k}" for c, k in _pending() if c not in CORPORA or k not in CHECKS)
    assert not bad, (
        f"readme_sections_pending.txt has lines that name no corpus or no "
        f"check {CHECKS}: {bad}. Remove them — the list only shrinks."
    )


def test_pending_list_has_no_passing_entries():
    """The list shrinks by itself rather than quietly going out of date."""
    stale = []
    for corpus, check in sorted(_pending()):
        readme = _readme_text(corpus)
        if readme is None:
            continue
        problems = (rights_problems(readme, _copyrights(corpus))
                    if check == "rights" else notes_problems(readme))
        if not problems:
            stale.append(f"{corpus} {check}")
    assert not stale, (
        f"readme_sections_pending.txt still lists checks that now pass: {stale}. "
        "Delete those lines."
    )


@pytest.mark.parametrize("corpus", CORPORA)
def test_readme_rights_block(corpus):
    readme = _readme_text(corpus)
    assert readme is not None, f"{corpus} has no README.md"
    problems = rights_problems(readme, _copyrights(corpus))
    if problems and (corpus, "rights") in _pending():
        pytest.skip(f"{corpus} rights block predates POL-044 (readme_sections_pending.txt)")
    assert not problems, (
        f"POL-044: {corpus}/README.md: " + "; ".join(problems) + ". The block is:\n"
        "## Rights\n**License:** <the XML @copyright>\n"
        "**Rights source:** <grantor>, <YYYY-MM-DD>; evidence: ask maintainer"
    )


@pytest.mark.parametrize("corpus", CORPORA)
def test_readme_notes_and_issues(corpus):
    readme = _readme_text(corpus)
    assert readme is not None, f"{corpus} has no README.md"
    problems = notes_problems(readme)
    if problems and (corpus, "notes") in _pending():
        pytest.skip(f"{corpus} predates POL-055's one name (readme_sections_pending.txt)")
    assert not problems, (
        f"POL-055: {corpus}/README.md: " + "; ".join(problems) +
        ". Rename the section to 'Notes and Issues' (write 'None known.' if empty)."
    )

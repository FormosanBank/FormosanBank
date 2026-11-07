"""POL-044, POL-052 and POL-055 (as amended 2026-10-18): the corpus README layout.

Each corpus README is the single copy of that corpus's documentation: the
documentation site renders it as the corpus page (docs/tools/prepare_site.py).
Its sections, in this order (maintainer, 2026-10-18):

    # <Corpus name>
    ## Languages and dialects
    ## Source
    ## Statistics                 (the site inserts the table here)
    ## How to cite
    ## License                    (POL-044's two structured lines live here)
    ## Notes and caveats          (POL-055; "None known." when empty)
    ## Reproduction and processing
    ### How to reproduce
    ### What each step does

Two checks per corpus:

* ``structure`` -- the headings above, each exactly once, in that order;
* ``rights`` -- under ``## License``, a ``**License:** <value>`` line equal to the
  corpus XML's ``@copyright`` (one value across the corpus) and a
  ``**Rights source:**`` line.

Corpora whose README cannot yet pass a check are listed in
``readme_sections_pending.txt`` at the repo root, one ``<corpus> <check>`` pair
per line. The list only shrinks; a new or re-ported corpus is never added.
"""
import sys
from xml.etree import ElementTree as ET

import pytest

from tests._helpers import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "docs" / "tools"))
from readme_layout import REQUIRED_HEADINGS, rights_problems, structure_problems  # noqa: E402

PENDING_FILE = REPO_ROOT / "readme_sections_pending.txt"
CHECKS = ("structure", "rights")

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


def _problems(corpus: str, check: str) -> list[str]:
    readme = _readme_text(corpus)
    if readme is None:
        return ["no README.md"]
    if check == "rights":
        return rights_problems(readme, _copyrights(corpus))
    return structure_problems(readme)


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
    stale = sorted(f"{c} {k}" for c, k in _pending() if not _problems(c, k))
    assert not stale, (
        f"readme_sections_pending.txt still lists checks that now pass: {stale}. "
        "Delete those lines."
    )


@pytest.mark.parametrize("corpus", CORPORA)
def test_readme_structure(corpus):
    problems = _problems(corpus, "structure")
    if problems and (corpus, "structure") in _pending():
        pytest.skip(f"{corpus}: README layout pending (readme_sections_pending.txt)")
    assert not problems, (
        f"{corpus}/README.md: " + "; ".join(problems) + ". Required, in order: "
        + ", ".join(REQUIRED_HEADINGS)
    )


@pytest.mark.parametrize("corpus", CORPORA)
def test_readme_license_block(corpus):
    problems = _problems(corpus, "rights")
    if problems and (corpus, "rights") in _pending():
        pytest.skip(f"{corpus}: rights block pending (readme_sections_pending.txt)")
    assert not problems, (
        f"POL-044: {corpus}/README.md: " + "; ".join(problems) + ". The block is:\n"
        "## License\n**License:** <the XML @copyright>\n"
        "**Rights source:** <grantor>, <YYYY-MM-DD>; evidence: ask maintainer"
    )

"""A published XML/ directory holds XML and nothing else.

Reports, logs, caches and editor backups that a tool writes next to the
files it processed are per-run output (POL-033) or scratch, never published
data; a stray file there is published alongside the corpus, copied by every
clone and, when it is a backup of an XML file, carries whatever the file said
at the time (ePark shipped a `Saaroa.xml.backup` with a superseded licence
until 2026-10-16). This checks the git-tracked contents of every corpus's
`XML/` tree, so untracked tool output on a working checkout does not fail it.

Corpora that predate the rule are listed in `xml_dir_pending.txt` at the repo
root. That list only shrinks: a corpus is removed when its stray files go.
"""
import subprocess

import pytest

from tests._helpers import REPO_ROOT

PENDING_FILE = REPO_ROOT / "xml_dir_pending.txt"
ALLOWED_SUFFIXES = (".xml",)
ALLOWED_NAMES = {".gitkeep"}


def _pending() -> set[str]:
    if not PENDING_FILE.exists():
        return set()
    return {
        line.strip()
        for line in PENDING_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def _corpora() -> list[str]:
    return sorted(d.name for d in (REPO_ROOT / "Corpora").iterdir() if d.is_dir())


def _tracked_under(rel_dir: str) -> list[str]:
    out = subprocess.run(
        ["git", "-c", "core.quotePath=false", "ls-files", "--", rel_dir],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    return [line for line in out.splitlines() if line]


def _stray(corpus: str) -> list[str]:
    return sorted(
        path for path in _tracked_under(f"Corpora/{corpus}/XML")
        if not path.endswith(ALLOWED_SUFFIXES)
        and path.rsplit("/", 1)[-1] not in ALLOWED_NAMES
    )


CORPORA = _corpora()


def test_pending_list_names_real_corpora():
    unknown = sorted(_pending() - set(CORPORA))
    assert not unknown, (
        f"xml_dir_pending.txt names corpora that do not exist: {unknown}. "
        "Remove the stale lines — the list only shrinks."
    )


def test_pending_list_has_no_clean_corpora():
    """The list shrinks by itself rather than quietly going out of date."""
    clean = sorted(c for c in _pending() if not _stray(c))
    assert not clean, (
        f"xml_dir_pending.txt still lists corpora whose XML/ is clean: {clean}. "
        "Delete those lines."
    )


@pytest.mark.parametrize("corpus", CORPORA)
def test_xml_dir_holds_only_xml(corpus):
    if not (REPO_ROOT / "Corpora" / corpus / "XML").is_dir():
        pytest.skip(f"{corpus} has no XML/ directory")
    stray = _stray(corpus)
    if stray and corpus in _pending():
        pytest.skip(f"{corpus} predates the rule (xml_dir_pending.txt): {len(stray)} stray files")
    assert not stray, (
        f"{corpus}/XML/ holds {len(stray)} non-XML file(s): {stray[:8]}"
        f"{' …' if len(stray) > 8 else ''}. Published XML/ carries only .xml; "
        "move reports and logs out (--log_dir / --warnings_dir) or delete them."
    )

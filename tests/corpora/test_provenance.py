"""POL-052: every corpus records which FormosanBank commit built its XML.

`CodeAndDocs/provenance.json` is provenance, not a build input: nothing reads
it to decide what to do, and a rebuild always runs with the tools in the
checkout it is invoked from. Its job is to make a rerun's diff readable — when
a shared tool changes, a corpus built before the change produces a diff that
has nothing to do with why it was rebuilt, and this file is what distinguishes
the two.

Corpora that predate POL-052 are listed in `provenance_pending.txt` at the repo
root. That list only shrinks: a new or rebuilt corpus ships the file instead.
"""
import json
import re

import pytest

from tests._helpers import REPO_ROOT

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
PENDING_FILE = REPO_ROOT / "provenance_pending.txt"


def _pending() -> set[str]:
    if not PENDING_FILE.exists():
        return set()
    lines = PENDING_FILE.read_text(encoding="utf-8").splitlines()
    return {
        line.strip() for line in lines
        if line.strip() and not line.lstrip().startswith("#")
    }


def _corpora() -> list[str]:
    root = REPO_ROOT / "Corpora"
    return sorted(d.name for d in root.iterdir() if d.is_dir())


def _readme(corpus: str):
    """A corpus README, whichever case it is spelled with."""
    base = REPO_ROOT / "Corpora" / corpus
    for name in ("README.md", "readme.md"):
        path = base / name
        if path.exists():
            return path
    return None


CORPORA = _corpora()


def test_pending_list_names_real_corpora():
    """A pending entry that no longer names a corpus hides a missing file."""
    unknown = sorted(_pending() - set(CORPORA))
    assert not unknown, (
        f"provenance_pending.txt names corpora that do not exist: {unknown}. "
        "Remove the stale lines — the list only shrinks."
    )


@pytest.mark.parametrize("corpus", CORPORA)
def test_corpus_records_build_provenance(corpus):
    """POL-052: CodeAndDocs/provenance.json exists and is well formed."""
    path = REPO_ROOT / "Corpora" / corpus / "CodeAndDocs" / "provenance.json"
    if not path.exists():
        if corpus in _pending():
            pytest.skip(f"{corpus} predates POL-052 (provenance_pending.txt)")
        pytest.fail(
            f"POL-052: {corpus} has no CodeAndDocs/provenance.json. Record the "
            "FormosanBank commit its published XML was built against, or — only "
            "for a corpus that predates the policy — add it to "
            "provenance_pending.txt."
        )

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        pytest.fail(f"{corpus}: provenance.json is not valid JSON: {exc}")

    assert isinstance(data, dict), f"{corpus}: provenance.json must be an object"
    commit = data.get("formosanbank_commit")
    assert commit, f"{corpus}: provenance.json has no 'formosanbank_commit'"
    assert isinstance(commit, str) and COMMIT_RE.match(commit), (
        f"{corpus}: 'formosanbank_commit' must be a full 40-character SHA, "
        f"got {commit!r}"
    )
    built = data.get("built")
    if built is not None:
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", str(built)), (
            f"{corpus}: 'built' must be YYYY-MM-DD, got {built!r}"
        )


@pytest.mark.parametrize("corpus", CORPORA)
def test_readme_links_provenance(corpus):
    """POL-052: the README links the file rather than repeating the SHA."""
    path = REPO_ROOT / "Corpora" / corpus / "CodeAndDocs" / "provenance.json"
    if not path.exists():
        pytest.skip(f"{corpus} has no provenance.json (see the test above)")
    readme = _readme(corpus)
    assert readme is not None, f"{corpus}: no README to link provenance.json from"
    text = readme.read_text(encoding="utf-8")
    assert "provenance.json" in text, (
        f"POL-052: {corpus}'s README does not mention "
        "CodeAndDocs/provenance.json. Link the file so there is one copy of the "
        "commit to keep current."
    )
    commit = json.loads(path.read_text(encoding="utf-8"))["formosanbank_commit"]
    assert commit not in text, (
        f"POL-052: {corpus}'s README transcribes the provenance SHA ({commit[:12]}"
        "...). Link provenance.json instead — a second copy drifts."
    )

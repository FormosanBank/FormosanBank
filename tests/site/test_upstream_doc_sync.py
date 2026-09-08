"""Drift guard: every synced GitBook page must match its upstream source.

The canonical files live in the FormosanBank repository; the GitBook
pages are generated copies (see sync_upstream_docs.py). These tests fail
when someone edits either side without re-running the sync. Each SKIPS
when no FormosanBank checkout with that source file is available (e.g.
this repo checked out standalone, or before an upstream branch merges).
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import sync_upstream_docs  # noqa: E402


@pytest.mark.parametrize(
    "doc", sync_upstream_docs.DOCS, ids=[d.name for d in sync_upstream_docs.DOCS]
)
def test_synced_page_matches_canonical(doc):
    formosanbank = sync_upstream_docs.default_formosanbank()
    source = doc.source_path(formosanbank)
    if not source.exists():
        pytest.skip(f"no sibling FormosanBank/{doc.source} to compare against")
    page = doc.page_path
    assert page.exists(), (
        f"{doc.page} missing — run: python sync_upstream_docs.py"
    )
    assert page.read_text(encoding="utf-8") == doc.render(formosanbank), (
        f"{doc.page} drifted from FormosanBank/{doc.source} — "
        "run: python sync_upstream_docs.py"
    )


def test_docs_have_unique_names_and_pages():
    names = [d.name for d in sync_upstream_docs.DOCS]
    pages = [d.page for d in sync_upstream_docs.DOCS]
    assert len(names) == len(set(names)), f"duplicate doc names: {names}"
    assert len(pages) == len(set(pages)), f"duplicate target pages: {pages}"


def test_sources_have_no_relative_markdown_links():
    """Sources are copied verbatim, so relative links would resolve wrong.

    A link written for the FormosanBank tree (e.g. `[x](QC/foo.py)`)
    points somewhere else entirely once the file is rendered inside the
    GitBook. Absolute http(s) links are fine.
    """
    import re

    formosanbank = sync_upstream_docs.default_formosanbank()
    # Code spans and fenced blocks are stripped first: regexes and shell
    # snippets routinely contain bracket/paren pairs that look like links
    # (e.g. the escaped character class `\\[a\\|b\\](?=i)` in POLICIES.md).
    fence = re.compile(r"^```.*?^```", re.S | re.M)
    code_span = re.compile(r"`[^`\n]*`")
    link = re.compile(r"\[[^\]]*\]\((?!https?://|#)([^)]+)\)")
    for doc in sync_upstream_docs.DOCS:
        source = doc.source_path(formosanbank)
        if not source.exists():
            continue
        text = source.read_text(encoding="utf-8")
        text = code_span.sub("", fence.sub("", text))
        found = link.findall(text)
        assert not found, (
            f"FormosanBank/{doc.source} contains relative Markdown links "
            f"that will not resolve in the GitBook: {found}"
        )

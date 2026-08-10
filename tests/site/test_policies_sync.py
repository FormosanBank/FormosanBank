"""Drift guard: the GitBook policies page must match FormosanBank/POLICIES.md.

The canonical file lives in the FormosanBank repository; the GitBook page
is a generated copy (see sync_policies.py). This test fails when someone
edits either side without re-running the sync. It SKIPS when no
FormosanBank checkout with a POLICIES.md is available (e.g. this repo
checked out standalone, or before the policies branch merges upstream).
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import sync_policies  # noqa: E402


def test_policies_page_matches_canonical():
    source = sync_policies.default_formosanbank() / "POLICIES.md"
    if not source.exists():
        pytest.skip("no sibling FormosanBank/POLICIES.md to compare against")
    page = sync_policies.PAGE
    assert page.exists(), (
        "policies page missing — run: python sync_policies.py"
    )
    assert page.read_text(encoding="utf-8") == sync_policies.render(source), (
        "policies page drifted from FormosanBank/POLICIES.md — "
        "run: python sync_policies.py"
    )

"""manage_corpus_pages: register a corpus page; lint registration and README layout."""

import pytest

import manage_corpus_pages as mcp

GOOD_README = """# Corpus

## Languages and dialects

Amis (`ami`), dialect unknown.

## Source

A book.

## Statistics

Generated.

## How to cite

X.

## License

**License:** CC BY 4.0
**Rights source:** Someone, 2026-01-01; evidence: ask maintainer

## Notes and caveats

None known.

## Reproduction and processing

### How to reproduce

Run it.

### What each step does

Steps.
"""


def _repo(tmp_path, corpora: dict[str, str]):
    for name, readme in corpora.items():
        (tmp_path / "Corpora" / name / "XML").mkdir(parents=True)
        (tmp_path / "Corpora" / name / "README.md").write_text(readme, encoding="utf-8")
    return tmp_path


def _row(corpus, slug):
    return {"corpus": corpus, "slug": slug, "nav_label": corpus, "descriptors": "", "zh_page": "", "pwn_page": ""}


def test_add_is_idempotent_and_refuses_duplicate_slug():
    rows = mcp.add([], "A", "a-page", "A")
    assert mcp.add(rows, "A", "other", "A") == rows
    with pytest.raises(ValueError, match="already used"):
        mcp.add(rows, "B", "A-PAGE", "B")


def test_check_clean(tmp_path):
    repo = _repo(tmp_path, {"A": GOOD_README})
    assert mcp.check(repo, [_row("A", "a")]) == []


def test_check_flags_unregistered_corpus_and_orphan_row(tmp_path):
    repo = _repo(tmp_path, {"A": GOOD_README, "B": GOOD_README})
    problems = mcp.check(repo, [_row("A", "a"), _row("Gone", "gone")])
    assert "B: no row in docs/site/corpus_pages.csv" in problems
    assert "Gone: row in corpus_pages.csv but no Corpora/Gone/XML" in problems


def test_check_flags_missing_section_and_wrong_order(tmp_path):
    no_notes = GOOD_README.replace("## Notes and caveats\n\nNone known.\n\n", "")
    swapped = GOOD_README.replace("## Source", "## TEMP").replace("## Languages and dialects", "## Source").replace("## TEMP", "## Languages and dialects")
    repo = _repo(tmp_path, {"A": no_notes, "B": swapped})
    problems = mcp.check(repo, [_row("A", "a"), _row("B", "b")])
    assert any(p.startswith("A: '## Notes and caveats' appears 0 times") for p in problems)
    assert any(p.startswith("B: headings out of order") for p in problems)


def test_pending_structure_entries_are_not_reported(tmp_path):
    repo = _repo(tmp_path, {"A": "# A\n\nOld layout.\n"})
    (repo / "readme_sections_pending.txt").write_text("A structure\n", encoding="utf-8")
    assert mcp.check(repo, [_row("A", "a")]) == []

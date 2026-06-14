import pytest

import manage_corpus_pages as mcp


def test_render_page_substitutes_title_only():
    tpl = "# {{TITLE}}\n\n{{DESCRIPTION}}\n"
    out = mcp.render_page(tpl, "My Corpus")
    assert "# My Corpus" in out
    assert "{{DESCRIPTION}}" in out  # prose left for the skill


def test_insert_nav_entry_appends_after_last_corpora_subbullet(gitbook):
    text = gitbook.summary.read_text(encoding="utf-8")
    out = mcp.insert_nav_entry(text, "newcorpus.md", "New Corpus")
    lines = out.splitlines()
    # inserted as an indented sub-bullet, immediately before Developers
    nav_idx = next(i for i, l in enumerate(lines) if "corpora/newcorpus.md" in l)
    dev_idx = next(i for i, l in enumerate(lines) if "developers/README.md" in l)
    assert lines[nav_idx].startswith("  * [New Corpus]")
    assert nav_idx < dev_idx
    # last existing sub-bullet (wikipedias) stays before the new one
    wiki_idx = next(i for i, l in enumerate(lines) if "corpora/wikipedias.md" in l)
    assert wiki_idx < nav_idx


def test_insert_nav_entry_idempotent(gitbook):
    text = gitbook.summary.read_text(encoding="utf-8")
    once = mcp.insert_nav_entry(text, "newcorpus.md", "New Corpus")
    twice = mcp.insert_nav_entry(once, "newcorpus.md", "New Corpus")
    assert once == twice


def test_insert_csv_to_md_entry_appends_before_close(gitbook):
    text = gitbook.stats_script.read_text(encoding="utf-8")
    out = mcp.insert_csv_to_md_entry(text, "NewCorpus", "newcorpus.md")
    assert "'NewCorpus_corpora_stats.csv': 'newcorpus.md'," in out
    # entry sits inside the dict, before its closing brace
    lines = out.splitlines()
    entry_idx = next(i for i, l in enumerate(lines) if "NewCorpus_corpora_stats.csv" in l)
    close_idx = next(i for i, l in enumerate(lines) if l.rstrip() == "}")
    assert entry_idx < close_idx
    # still valid Python
    ns = {}
    exec(out, ns)
    assert ns["CSV_TO_MD"]["NewCorpus_corpora_stats.csv"] == "newcorpus.md"


def test_insert_csv_to_md_entry_idempotent(gitbook):
    text = gitbook.stats_script.read_text(encoding="utf-8")
    once = mcp.insert_csv_to_md_entry(text, "NewCorpus", "newcorpus.md")
    twice = mcp.insert_csv_to_md_entry(once, "NewCorpus", "newcorpus.md")
    assert once == twice


def test_insert_readme_list_entry_appends_before_stats(gitbook):
    text = gitbook.corpora_readme.read_text(encoding="utf-8")
    out = mcp.insert_readme_list_entry(text, "newcorpus.md", "New Corpus", "(text, audio)")
    lines = out.splitlines()
    new_idx = next(i for i, l in enumerate(lines) if "](newcorpus.md)" in l)
    stats_idx = next(i for i, l in enumerate(lines) if "CORPUS STATS START" in l)
    wiki_idx = next(i for i, l in enumerate(lines) if "](wikipedias.md)" in l)
    assert lines[new_idx] == "* [New Corpus](newcorpus.md) (text, audio)"
    assert wiki_idx < new_idx < stats_idx


def test_insert_readme_list_entry_no_descriptors(gitbook):
    text = gitbook.corpora_readme.read_text(encoding="utf-8")
    out = mcp.insert_readme_list_entry(text, "newcorpus.md", "New Corpus", "")
    assert "* [New Corpus](newcorpus.md)\n" in out


def test_insert_readme_list_entry_idempotent(gitbook):
    text = gitbook.corpora_readme.read_text(encoding="utf-8")
    once = mcp.insert_readme_list_entry(text, "newcorpus.md", "New Corpus", "(text)")
    twice = mcp.insert_readme_list_entry(once, "newcorpus.md", "New Corpus", "(text)")
    assert once == twice


def test_cmd_add_wires_all_four_points(gitbook):
    rc = mcp.cmd_add(
        corpus="NewCorpus",
        slug="newcorpus.md",
        nav_label="New Corpus",
        title="New Corpus",
        template=str(gitbook.template),
        gitbook_root=str(gitbook.root),
        descriptors="(text, audio)",
    )
    assert rc == 0
    page = gitbook.pages / "newcorpus.md"
    assert page.exists()
    assert "# New Corpus" in page.read_text(encoding="utf-8")
    assert "{{DESCRIPTION}}" in page.read_text(encoding="utf-8")  # prose left
    assert "corpora/newcorpus.md" in gitbook.summary.read_text(encoding="utf-8")
    readme = gitbook.corpora_readme.read_text(encoding="utf-8")
    assert "* [New Corpus](newcorpus.md) (text, audio)" in readme
    assert "NewCorpus_corpora_stats.csv" in gitbook.stats_script.read_text(encoding="utf-8")


def test_cmd_add_is_idempotent(gitbook):
    kwargs = dict(
        corpus="NewCorpus", slug="newcorpus.md", nav_label="New Corpus",
        title="New Corpus", template=str(gitbook.template),
        gitbook_root=str(gitbook.root), descriptors="(text)",
    )
    assert mcp.cmd_add(**kwargs) == 0
    summary_after_1 = gitbook.summary.read_text(encoding="utf-8")
    script_after_1 = gitbook.stats_script.read_text(encoding="utf-8")
    readme_after_1 = gitbook.corpora_readme.read_text(encoding="utf-8")
    assert mcp.cmd_add(**kwargs) == 0  # second run: clean no-op
    assert gitbook.summary.read_text(encoding="utf-8") == summary_after_1
    assert gitbook.stats_script.read_text(encoding="utf-8") == script_after_1
    assert gitbook.corpora_readme.read_text(encoding="utf-8") == readme_after_1


def test_cmd_add_missing_template_errors(gitbook):
    with pytest.raises(FileNotFoundError):
        mcp.cmd_add(
            corpus="NewCorpus", slug="newcorpus.md", nav_label="New Corpus",
            title="New Corpus", template=str(gitbook.root / "nope.md"),
            gitbook_root=str(gitbook.root), descriptors="",
        )

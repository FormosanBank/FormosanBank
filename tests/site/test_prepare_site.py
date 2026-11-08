"""prepare_site: GitBook markup translation, link rewriting and page assembly.

The first four tests are Hunter Scheppat's, from GitBook PR #78 (f8e7d8f),
updated for the project Pages base URL and markdown-in-HTML admonitions.
"""

from pathlib import Path, PurePosixPath

import pytest

import prepare_site
from prepare_site import (
    build_path_map,
    transform_markdown,
    transform_summary,
)


def test_build_path_map_uses_index_and_casefolded_routes(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Home\n", encoding="utf-8")
    corpus_dir = tmp_path / "corpora"
    corpus_dir.mkdir()
    (corpus_dir / "RauDong.md").write_text("# Rau-Dong\n", encoding="utf-8")

    mapping = build_path_map(tmp_path)

    assert mapping[PurePosixPath("README.md")] == PurePosixPath("index.md")
    assert mapping[PurePosixPath("corpora/RauDong.md")] == PurePosixPath(
        "corpora/raudong.md"
    )


def test_transform_markdown_preserves_code_and_rewrites_page_links() -> None:
    mapping = {
        PurePosixPath("guide/README.md"): PurePosixPath("guide/index.md"),
        PurePosixPath("guide/page.md"): PurePosixPath("guide/page.md"),
    }
    source = """---
icon: hand-wave
---

# Page

The source file is `README.md`.

[Guide](README.md)
[Guide directory](./)

{% hint style="info" %}
Read this first.
{% endhint %}
"""

    transformed = transform_markdown(
        source,
        current_source=PurePosixPath("guide/page.md"),
        current_output=PurePosixPath("guide/page.md"),
        mapping=mapping,
        public_prefix="/",
    )

    assert "`README.md`" in transformed
    assert "[Guide](index.md)" in transformed
    assert "[Guide directory](index.md)" in transformed
    assert "icon: fontawesome/solid/hand" in transformed
    assert '<div class="admonition info" markdown>' in transformed
    assert "{%" not in transformed


def test_transform_markdown_rewrites_assets_and_old_domain() -> None:
    transformed = transform_markdown(
        '<img src="../../.gitbook/assets/example image.png">\n'
        "[Corpora](https://ai4commsci.gitbook.io/formosanbank/corpora)\n",
        current_source=PurePosixPath("nested/page.md"),
        current_output=PurePosixPath("nested/page.md"),
        mapping={PurePosixPath("nested/page.md"): PurePosixPath("nested/page.md")},
        public_prefix="/zh/",
    )

    assert 'src="/zh/assets/images/example image.png"' in transformed
    assert "https://formosanbank.github.io/FormosanBank/corpora" in transformed


def test_transform_summary_nests_gitbook_sections() -> None:
    transformed = transform_summary(
        """# Table of contents

* [Welcome](README.md)

## Background

* [Languages](background/languages.md)
  * [Details](background/details.md)
"""
    )

    assert "* [Welcome](README.md)" in transformed
    assert "* Background" in transformed
    assert "  * [Languages](background/languages.md)" in transformed
    assert "    * [Details](background/details.md)" in transformed


def _transform(source: str, page: str = "page.md", mapping=None, fallback=None) -> str:
    path = PurePosixPath(page)
    mapping = mapping if mapping is not None else {path: path}
    return transform_markdown(
        source,
        current_source=path,
        current_output=mapping.get(path, path),
        mapping=mapping,
        public_prefix="/FormosanBank/",
        fallback=fallback,
    )


def test_unknown_directive_raises() -> None:
    with pytest.raises(ValueError, match="unhandled GitBook directive"):
        _transform('# Page\n\n{% embed url="https://example.com" %}\n')


def test_directive_inside_code_is_left_alone() -> None:
    out = _transform('# Page\n\n```\n{% embed url="x" %}\n```\n')
    assert '{% embed url="x" %}' in out


def test_content_ref_blocks_are_removed_keeping_the_link() -> None:
    out = _transform(
        '# Page\n\n{% content-ref url="other.md" %}\n[other.md](other.md)\n{% endcontent-ref %}\n'
    )
    assert "{%" not in out and "[other.md](other.md)" in out


def test_html_links_become_directory_urls() -> None:
    mapping = {
        PurePosixPath("c/README.md"): PurePosixPath("c/index.md"),
        PurePosixPath("c/ci.md"): PurePosixPath("c/ci.md"),
    }
    out = _transform('# T\n\n<a href="ci.md#x">CI</a>\n', page="c/README.md", mapping=mapping)
    assert 'href="ci/#x"' in out


def test_line_starting_with_bare_hash_is_not_a_heading() -> None:
    out = _transform("# Title\n\nwrapped prose ending in PR\n#179 and more\n")
    assert "\\#179 and more" in out
    assert "# Title" in out


def test_missing_translated_page_falls_back_to_english() -> None:
    fallback = {PurePosixPath("extra/terms.md"): PurePosixPath("extra/terms.md")}
    out = _transform("# T\n\n[Terms](../extra/terms.md)\n", page="p/page.md", fallback=fallback)
    assert "[Terms](/FormosanBank/extra/terms/)" in out


def test_unknown_icon_is_dropped_known_icon_kept() -> None:
    assert "icon:" not in _transform("---\nicon: list-tree\n---\n\n# T\n")
    assert "icon: fontawesome/solid/hand" in _transform("---\nicon: hand-wave\n---\n\n# T\n")


def test_repo_links_point_at_github_or_site_pages(tmp_path: Path) -> None:
    (tmp_path / "Corpora" / "A" / "CodeAndDocs").mkdir(parents=True)
    text = (
        "[script](CodeAndDocs/run.sh) [dir](CodeAndDocs/) "
        "[`provenance.json`](CodeAndDocs/provenance.json) "
        "![fig](CodeAndDocs/fig.png) [other corpus](../B/README.md) "
        "[policy](../../POLICIES.md#pol-044) [web](https://example.com) [here](#notes)"
    )
    out = prepare_site.rewrite_repo_links(
        text,
        repo_path=PurePosixPath("Corpora/A/README.md"),
        page_source=PurePosixPath("the-bank-architecture/corpora/a.md"),
        site_pages={
            PurePosixPath("Corpora/B/README.md"): PurePosixPath("the-bank-architecture/corpora/b.md"),
            PurePosixPath("POLICIES.md"): PurePosixPath("the-bank-architecture/policies.md"),
        },
        repository_root=tmp_path,
    )
    blob = "https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/A/CodeAndDocs"
    assert f"[script]({blob}/run.sh)" in out
    assert "[dir](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/A/CodeAndDocs)" in out
    assert f"[`provenance.json`]({blob}/provenance.json)" in out
    assert "![fig](https://raw.githubusercontent.com/FormosanBank/FormosanBank/main/Corpora/A/CodeAndDocs/fig.png)" in out
    assert "[other corpus](b.md)" in out
    assert "[policy](../policies.md#pol-044)" in out
    assert "[web](https://example.com)" in out and "[here](#notes)" in out


def test_statistics_replace_placeholder_section() -> None:
    readme = "# C\n\n## Source\n\nS.\n\n## Statistics\n\nSee the site.\n\n## How to cite\n\nX.\n"
    out = prepare_site.insert_statistics(readme, "TABLE")
    assert "## Statistics\n\nTABLE\n\n## How to cite" in out
    assert "See the site." not in out


def test_statistics_inserted_before_first_section_when_absent() -> None:
    out = prepare_site.insert_statistics("# C\n\nIntro.\n\n## Rights\n\nR.\n", "TABLE")
    assert out.index("## Statistics") < out.index("## Rights")
    assert out.index("Intro.") < out.index("## Statistics")


def test_corpora_nav_lists_every_corpus_page() -> None:
    summary = (
        "* [Corpora](the-bank-architecture/corpora/README.md)\n"
        "  * [Old](the-bank-architecture/corpora/old.md)\n"
        "* [Developers](the-bank-architecture/developers/README.md)\n"
    )
    pages = [prepare_site.CorpusPage("A", "a-slug", "A label", "", "", "")]
    out = prepare_site.corpora_nav(summary, pages)
    assert "  * [A label](the-bank-architecture/corpora/a-slug.md)" in out
    assert "old.md" not in out and "* [Developers]" in out


def test_corpus_pages_csv_covers_every_corpus_once() -> None:
    root = Path(prepare_site.__file__).resolve().parents[2]
    pages = prepare_site.load_corpus_pages(root)
    names = [page.corpus for page in pages]
    corpora = sorted(p.name for p in (root / "Corpora").iterdir() if p.is_dir())
    assert sorted(names) == corpora
    assert len(set(page.slug.casefold() for page in pages)) == len(pages)

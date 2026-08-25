from pathlib import Path, PurePosixPath

from scripts.prepare_site import (
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
    assert '<div class="admonition info">' in transformed
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
    assert "https://formosanbank.github.io/corpora" in transformed


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

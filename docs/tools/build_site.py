#!/usr/bin/env python3
"""Build every edition of the documentation site and check the result.

    python docs/tools/build_site.py [--site-dir site]

1. ``prepare_site.prepare_site`` assembles each edition's Markdown under
   ``.build/`` and writes its MkDocs config.
2. properdocs builds each edition (``--strict``: a warning fails the build).
3. Editions whose language the theme doesn't know get their ``<html lang>``
   set (Paiwan ``pwn``, Amis ``ami``, Bunun ``bnn``).
4. ``check_site`` checks links, anchors, assets and page structure.
Any failure exits nonzero, so CI never deploys a broken site.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import check_site  # noqa: E402
import prepare_site  # noqa: E402

HTML_LANG = re.compile(r'<html lang="[^"]*"')


def set_html_lang(edition_dir: Path, lang: str, nested: list[Path]) -> int:
    """Set <html lang> on every page of one edition (not inside nested editions)."""
    changed = 0
    for page in edition_dir.rglob("*.html"):
        if any(page.is_relative_to(other) for other in nested):
            continue
        text = page.read_text(encoding="utf-8")
        new = HTML_LANG.sub(f'<html lang="{lang}"', text, count=1)
        if new != text:
            page.write_text(new, encoding="utf-8")
            changed += 1
    return changed


def count_pages(site_dir: Path) -> int:
    """HTML pages under ``site_dir``; refuses an empty or missing site.

    A link check over nothing finds nothing: without this, a build that wrote
    its pages elsewhere reported "link check clean" with 0 pages.
    """
    pages = sum(1 for _ in site_dir.rglob("*.html")) if site_dir.is_dir() else 0
    if pages == 0:
        raise SystemExit(f"no HTML pages in {site_dir}: the build wrote nothing there")
    return pages


def build(repository_root: Path, site_dir: Path, build_dir: Path) -> None:
    # Absolute paths: properdocs resolves a relative --site-dir against the
    # directory of its config file (.build/), not the current directory.
    repository_root, site_dir, build_dir = (p.resolve() for p in (repository_root, site_dir, build_dir))
    editions = prepare_site.prepare_site(repository_root, build_dir)
    if site_dir.exists():
        shutil.rmtree(site_dir)
    # The root edition first: building it cleans its output directory.
    editions.sort(key=lambda item: item[0].site_subdir != "")
    for edition, config in editions:
        target = site_dir / edition.site_subdir
        print(f"== building {edition.key} -> {target}", flush=True)
        subprocess.run(
            [sys.executable, "-m", "properdocs", "build", "--strict",
             "--config-file", str(config), "--site-dir", str(target)],
            check=True,
        )
    subdirs = [site_dir / e.site_subdir for e, _ in editions if e.site_subdir]
    for edition, _config in editions:
        if edition.theme_language == edition.html_lang:
            continue
        edition_dir = site_dir / edition.site_subdir
        nested = [d for d in subdirs if d != edition_dir and d.is_relative_to(edition_dir)]
        set_html_lang(edition_dir, edition.html_lang, nested)
    pages = count_pages(site_dir)
    errors = check_site.check_site(site_dir)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Built {len(editions)} edition(s), {pages} HTML pages; link check clean.")


def main() -> None:
    root = TOOLS.parents[1]
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--site-dir", type=Path, default=root / "site")
    parser.add_argument("--build-dir", type=Path, default=root / ".build")
    args = parser.parse_args()
    build(root, args.site_dir, args.build_dir)


if __name__ == "__main__":
    main()

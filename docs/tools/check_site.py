#!/usr/bin/env python3
"""Check generated HTML links, assets, anchors, and basic document structure."""

from __future__ import annotations

import argparse
import posixpath
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit


LOCAL_HOST = "formosanbank.github.io"
# The site is a project Pages site, served under /FormosanBank/. The built
# site directory corresponds to that path, so it is stripped before resolving.
BASE_PATH = "/FormosanBank"
LEGACY_SITE = "ai4commsci.gitbook.io/formosanbank"
REFERENCE_ATTRIBUTES = {
    "a": "href",
    "img": "src",
    "link": "href",
    "script": "src",
    "source": "src",
}


@dataclass
class Page:
    path: Path
    ids: set[str] = field(default_factory=set)
    duplicate_ids: set[str] = field(default_factory=set)
    references: list[str] = field(default_factory=list)
    h1_count: int = 0
    language: str | None = None
    images_without_alt: int = 0


class PageParser(HTMLParser):
    def __init__(self, path: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.page = Page(path)

    def handle_starttag(
        self, tag: str, attributes: list[tuple[str, str | None]]
    ) -> None:
        attrs = dict(attributes)
        element_id = attrs.get("id")
        if element_id:
            if element_id in self.page.ids:
                self.page.duplicate_ids.add(element_id)
            self.page.ids.add(element_id)
        if tag == "html":
            self.page.language = attrs.get("lang")
        if tag == "h1":
            self.page.h1_count += 1
        if tag == "img" and "alt" not in attrs:
            self.page.images_without_alt += 1
        reference_attribute = REFERENCE_ATTRIBUTES.get(tag)
        if reference_attribute and attrs.get(reference_attribute):
            self.page.references.append(attrs[reference_attribute] or "")


def parse_page(path: Path) -> Page:
    parser = PageParser(path)
    parser.feed(path.read_text(encoding="utf-8"))
    return parser.page


def resolve_target(site_root: Path, source: Path, reference: str) -> tuple[Path, str]:
    parsed = urlsplit(reference)
    if parsed.scheme in {"http", "https"} and parsed.netloc != LOCAL_HOST:
        raise ValueError("external")
    if parsed.netloc == LOCAL_HOST and parsed.path.startswith("/kakarayan/"):
        raise ValueError("external")
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        raise ValueError("external")
    if parsed.netloc and parsed.netloc != LOCAL_HOST:
        raise ValueError("external")

    if parsed.path.startswith("/") or parsed.netloc == LOCAL_HOST:
        path = parsed.path
        if path == BASE_PATH or path.startswith(BASE_PATH + "/"):
            path = path[len(BASE_PATH):]
        elif parsed.netloc == LOCAL_HOST or path.startswith("/"):
            raise ValueError("outside")
        relative = PurePosixPath(path.lstrip("/") or ".")
    else:
        source_relative = PurePosixPath(source.relative_to(site_root).as_posix())
        relative = PurePosixPath(
            posixpath.normpath(str(source_relative.parent / parsed.path))
        )
    if str(relative).startswith("../"):
        raise ValueError("outside")

    target = site_root / relative
    if parsed.path.endswith("/") or not parsed.path or str(relative) == ".":
        target /= "index.html"
    elif not target.exists() and not target.suffix:
        target /= "index.html"
    return target, unquote(parsed.fragment)


def check_site(site_root: Path) -> list[str]:
    pages = {path.resolve(): parse_page(path) for path in site_root.rglob("*.html")}
    errors: list[str] = []
    for path, page in sorted(pages.items()):
        display = path.relative_to(site_root)
        if page.duplicate_ids:
            errors.append(f"{display}: duplicate ids {sorted(page.duplicate_ids)}")
        if page.language is None:
            errors.append(f"{display}: missing html lang")
        if path.name != "404.html" and page.h1_count != 1:
            errors.append(f"{display}: expected one h1, found {page.h1_count}")
        if page.images_without_alt:
            errors.append(
                f"{display}: {page.images_without_alt} image(s) missing alt attributes"
            )

        document = path.read_text(encoding="utf-8")
        if LEGACY_SITE in document:
            errors.append(f"{display}: contains the legacy GitBook URL")
        if "{%" in document:
            errors.append(f"{display}: contains an unrendered GitBook directive")

        for reference in page.references:
            try:
                target, fragment = resolve_target(site_root, path, reference)
            except ValueError as error:
                if str(error) == "external":
                    continue
                errors.append(f"{display}: invalid local reference {reference!r}")
                continue
            if not target.exists():
                errors.append(f"{display}: missing target for {reference!r}")
                continue
            if fragment and not fragment.startswith("/") and target.suffix == ".html":
                target_page = pages.get(target.resolve())
                if target_page is None or fragment not in target_page.ids:
                    errors.append(f"{display}: missing anchor for {reference!r}")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site_root", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    site_root = args.site_root.resolve()
    errors = check_site(site_root)
    if errors:
        raise SystemExit("\n".join(errors))
    page_count = sum(1 for _ in site_root.rglob("*.html"))
    print(f"Checked {page_count} generated HTML pages")


if __name__ == "__main__":
    main()

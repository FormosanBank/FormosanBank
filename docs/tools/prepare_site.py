#!/usr/bin/env python3
"""Assemble the documentation site's Markdown sources for the static Pages build.

The site is built in two stages. This script assembles one Markdown tree per
edition under ``<output-root>/docs/<edition>/`` and writes one MkDocs config
per edition beside it; ``build_site.py`` then runs properdocs on each config
and checks the result.

Assembly reads every page from its canonical source, so nothing generated is
ever committed:

* ``docs/site/<edition source>/`` — hand-written pages (formerly the GitBook).
* ``Corpora/<corpus>/README.md`` — the single copy of each corpus's
  documentation (one page per row of ``docs/site/corpus_pages.csv``).
* ``POLICIES.md`` and ``AUDIO-PERMISSIONS.md`` — rendered as pages.
* ``statistics/*.csv`` — statistics tables, language pages and figures.

GitBook-only markup still present in the hand-written pages is translated
here; anything left unrecognised is an error rather than raw ``{% %}`` text
on a published page.
"""

from __future__ import annotations

import argparse
import csv
import posixpath
import re
import shutil
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit, urlunsplit

import yaml

OLD_SITE = "https://ai4commsci.gitbook.io/formosanbank"
NEW_SITE = "https://formosanbank.github.io/FormosanBank"
BASE_PATH = "/FormosanBank/"
REPO_URL = "https://github.com/FormosanBank/FormosanBank"
RAW_URL = "https://raw.githubusercontent.com/FormosanBank/FormosanBank/main"

CORPUS_PAGES_CSV = PurePosixPath("docs/site/corpus_pages.csv")
CORPORA_PAGE_DIR = PurePosixPath("the-bank-architecture/corpora")
POLICIES_PAGE = PurePosixPath("the-bank-architecture/policies.md")
AUDIO_POLICY_PAGE = PurePosixPath(
    "the-bank-architecture/developers/repository-contracts/audio-publication-policy.md"
)


@dataclass(frozen=True)
class Edition:
    key: str
    source: str | None  # hand-written source dir, relative to the repo root
    public_prefix: str  # absolute URL path the edition is served under
    html_lang: str  # value of <html lang>
    theme_language: str  # Material theme language (UI strings)
    label: str  # name in the language menu

    @property
    def site_subdir(self) -> str:
        """Directory under the built site ('' for the root edition)."""
        return self.public_prefix[len(BASE_PATH):].strip("/")


EDITIONS = (
    Edition("en", "docs/site/en-us", BASE_PATH, "en", "en", "English"),
    Edition("zh", "docs/site/zh-TW", f"{BASE_PATH}zh/", "zh-TW", "zh-TW", "繁體中文"),
    Edition("paiwan", "docs/site/pwn", f"{BASE_PATH}paiwan/", "pwn", "en", "Paiwan"),
    Edition("amis", None, f"{BASE_PATH}amis/", "ami", "en", "Amis"),
    Edition("bunun", None, f"{BASE_PATH}bunun/", "bnn", "en", "Bunun"),
)
EDITIONS_BY_KEY = {edition.key: edition for edition in EDITIONS}


@dataclass(frozen=True)
class CorpusPage:
    corpus: str  # directory name under Corpora/
    slug: str  # page file stem (kept from the GitBook so paths survive)
    nav_label: str
    descriptors: str
    zh_page: str  # file name of the old Mandarin corpus page, if any
    pwn_page: str  # file name of the old Paiwan corpus page, if any

    @property
    def source_path(self) -> PurePosixPath:
        """Where the page sits in the assembled English source tree."""
        return CORPORA_PAGE_DIR / f"{self.slug}.md"

    @property
    def url_path(self) -> str:
        """Absolute URL path of the published English page."""
        return f"{BASE_PATH}{CORPORA_PAGE_DIR}/{self.slug.casefold()}/"


def load_corpus_pages(repository_root: Path) -> list[CorpusPage]:
    with open(repository_root / CORPUS_PAGES_CSV, newline="", encoding="utf-8") as handle:
        return [CorpusPage(**row) for row in csv.DictReader(handle)]


# --------------------------------------------------------------------------
# GitBook markup and link rewriting (from Hunter Scheppat's PR #78)
# --------------------------------------------------------------------------

MARKDOWN_LINK = re.compile(
    r"(?P<prefix>!?\[[^\]\n]*\]\()"
    r"(?P<destination><[^>\n]+>|[^)\s\n]+)"
    r"(?P<suffix>(?:\s+[\"'][^\"'\n]*[\"'])?\))"
)
HTML_URL = re.compile(
    r"(?P<prefix>\b(?:href|src)=[\"'])(?P<destination>[^\"']+)(?P<suffix>[\"'])"
)
HINT_OPEN = re.compile(r'(?m)^(?P<indent>\s*){% hint style="(?P<style>[^\"]+)" %}\s*$')
HINT_CLOSE = re.compile(r"(?m)^(?P<indent>\s*){% endhint %}\s*$")
TAB_OPEN = re.compile(r'(?m)^(?P<indent>\s*){% tab title="(?P<title>[^\"]+)" %}\s*$')
CONTENT_REF_OPEN = re.compile(r'(?m)^\s*{% content-ref url="(?P<url>[^"]+)" %}\s*$')
DIRECTIVE_LINE = re.compile(
    r"(?m)^\s*{% (?:tabs|endtabs|endtab|endcontent-ref) %}\s*$"
)
LEFTOVER_DIRECTIVE = re.compile(r"{%.*?%}")
FENCE = re.compile(r"(?ms)^(?P<fence>`{3,}|~{3,}).*?^(?P=fence)\s*$")
INLINE_CODE = re.compile(r"`[^`\n]+`")

HINT_TITLES = {
    "danger": "Important",
    "info": "Note",
    "success": "Success",
    "warning": "Warning",
}

ICON_ALIASES = {
    "book-section": "book-open",
    "bullseye-arrow": "bullseye",
    "gauge-simple-min": "gauge-simple",
    "globe-pointer": "globe",
    "hand-wave": "hand",
    "police-box": "newspaper",
    "square-terminal": "terminal",
    "subtitles": "closed-captioning",
    "user-group-simple": "users",
    "waveform-lines": "wave-square",
}

SOURCE_LINK_FIXES = {
    "../FormosanBankGitbook/en-us/the-bank-architecture/formosanbank-xml-format.md": (
        "formosanbank-xml-format.md"
    ),
    "#the-less-than-form-greater-than-element": "#the-form-element",
}


def _material_icon_dir() -> Path | None:
    try:
        import material
    except ImportError:
        return None
    return Path(material.__file__).resolve().parent / "templates" / ".icons" / "fontawesome" / "solid"


MATERIAL_ICONS = _material_icon_dir()


def _icon_line(match: re.Match[str]) -> str:
    """GitBook icon names -> Font Awesome (free) names; drop icons the theme lacks.

    GitBook offers Font Awesome Pro icons; the theme ships only the free set.
    A missing icon is a decoration, so it is dropped rather than failing the
    build (the theme raises TemplateNotFound on an unknown icon).
    """
    name = ICON_ALIASES.get(match.group("icon"), match.group("icon"))
    if MATERIAL_ICONS is not None and not (MATERIAL_ICONS / f"{name}.svg").is_file():
        return ""
    return f"icon: fontawesome/solid/{name}\n"


def outside_code(text: str, transform) -> str:
    """Apply ``transform`` to ``text`` with fenced and inline code masked out.

    Code is swapped for placeholder tokens (no brackets or parentheses), so a
    link whose text is code -- ``[`provenance.json`](CodeAndDocs/...)`` --
    still matches the link pattern as one piece, while links and directives
    shown *inside* code examples are left alone.
    """
    saved: list[str] = []

    def mask(match: re.Match[str]) -> str:
        saved.append(match.group(0))
        return f"\x00{len(saved) - 1}\x00"

    masked = INLINE_CODE.sub(mask, FENCE.sub(mask, text))
    result = transform(masked)
    return re.sub("\x00(\\d+)\x00", lambda m: saved[int(m.group(1))], result)


def output_path(source_path: PurePosixPath) -> PurePosixPath:
    """Return a stable, URL-friendly output path for a source Markdown file."""
    if source_path.name == "SUMMARY.md":
        return source_path
    if source_path.name.casefold() == "readme.md":
        return source_path.with_name("index.md")
    return source_path.with_name(source_path.name.casefold())


def build_path_map(source_dir: Path) -> dict[PurePosixPath, PurePosixPath]:
    mapping: dict[PurePosixPath, PurePosixPath] = {}
    outputs: dict[PurePosixPath, PurePosixPath] = {}
    for path in sorted(source_dir.rglob("*.md")):
        source_relative = PurePosixPath(path.relative_to(source_dir).as_posix())
        target_relative = output_path(source_relative)
        if target_relative in outputs:
            first = outputs[target_relative]
            raise ValueError(
                f"case-folded output collision: {first} and {source_relative}"
            )
        mapping[source_relative] = target_relative
        outputs[target_relative] = source_relative
    return mapping


def _relative_source_target(
    current_source: PurePosixPath, destination: str
) -> PurePosixPath:
    normalized = posixpath.normpath(
        str(current_source.parent.joinpath(PurePosixPath(destination)))
    )
    return PurePosixPath(normalized)


def rewrite_destination(
    destination: str,
    *,
    current_source: PurePosixPath,
    current_output: PurePosixPath,
    mapping: dict[PurePosixPath, PurePosixPath],
    public_prefix: str,
    fallback: dict[PurePosixPath, PurePosixPath] | None = None,
    html: bool = False,
) -> str:
    """Rewrite one Markdown or HTML URL without changing prose or code examples.

    MkDocs converts ``.md`` links in Markdown but not inside raw HTML, so an
    HTML link (``html=True``) is written as the page's directory URL.

    ``fallback`` (source path -> output path of the English edition) catches
    links in a translated edition to pages it doesn't have: they go to the
    English page instead of nowhere.
    """
    enclosed = destination.startswith("<") and destination.endswith(">")
    raw = destination[1:-1] if enclosed else destination
    raw = raw.replace(OLD_SITE, NEW_SITE)

    asset_marker = ".gitbook/assets/"
    if asset_marker in raw:
        asset_name = raw.split(asset_marker, 1)[1]
        rewritten = f"{public_prefix}assets/images/{asset_name}"
        return f"<{rewritten}>" if enclosed else rewritten

    parsed = urlsplit(raw)
    if parsed.scheme or parsed.netloc or raw.startswith(("/", "#")):
        return f"<{raw}>" if enclosed else raw
    if not parsed.path:
        return destination

    source_target = _relative_source_target(current_source, parsed.path)
    target_output = mapping.get(source_target)
    if target_output is None:
        target_output = mapping.get(source_target / "README.md")
    if target_output is None and fallback:
        english = fallback.get(source_target) or fallback.get(source_target / "README.md")
        if english is not None:
            page = str(english.with_suffix("")).removesuffix("index").rstrip("/")
            url = f"{BASE_PATH}{page}/" if page else BASE_PATH
            rewritten = urlunsplit(("", "", url, parsed.query, parsed.fragment))
            return f"<{rewritten}>" if enclosed else rewritten
    if target_output is None:
        return f"<{raw}>" if enclosed else raw

    if html:
        relative = posixpath.relpath(_page_url(target_output), start=_page_url(current_output))
        relative = relative + "/" if relative != "." else "./"
    else:
        relative = posixpath.relpath(
            str(target_output), start=str(current_output.parent) or "."
        )
    rewritten = urlunsplit(("", "", relative, parsed.query, parsed.fragment))
    return f"<{rewritten}>" if enclosed else rewritten


def _page_url(output: PurePosixPath) -> str:
    """Directory URL (relative to the edition root) of a page's output file."""
    if output.suffix != ".md":
        return str(output)
    stem = output.with_suffix("")
    if stem.name == "index":
        stem = stem.parent
    return str(stem) if str(stem) != "." else "."


BARE_HASH_LINE = re.compile(r"(?m)^#(?=[^\s#])")


def transform_summary(text: str) -> str:
    """Convert GitBook section headings into literate-nav section entries."""
    output: list[str] = []
    in_section = False
    for line in text.splitlines():
        if line.startswith("## "):
            output.append(f"* {line[3:].strip()}")
            in_section = True
            continue
        if not line.strip():
            if output and output[-1] != "":
                output.append("")
            continue
        if in_section and re.match(r"^\s*\* ", line):
            line = f"  {line}"
        output.append(line.rstrip())

    compact: list[str] = []
    for line in output:
        if line == "" and compact and (
            compact[-1] == "" or compact[-1].lstrip().startswith("*")
        ):
            continue
        compact.append(line)
    return "\n".join(compact).rstrip() + "\n"


def transform_markdown(
    text: str,
    *,
    current_source: PurePosixPath,
    current_output: PurePosixPath,
    mapping: dict[PurePosixPath, PurePosixPath],
    public_prefix: str,
    fallback: dict[PurePosixPath, PurePosixPath] | None = None,
) -> str:
    """Translate the small GitBook extension surface used by this repository."""
    text = text.replace(OLD_SITE, NEW_SITE)
    for old_link, new_link in SOURCE_LINK_FIXES.items():
        text = text.replace(old_link, new_link)
    text = re.sub(r"(?m)^icon: (?P<icon>[a-z0-9-]+)\n", _icon_line, text)

    def hint_open(match: re.Match[str]) -> str:
        indent = match.group("indent")
        style = match.group("style").casefold()
        title = HINT_TITLES.get(style, style.title())
        return (
            f'{indent}<div class="admonition {style}" markdown>\n'
            f'{indent}<p class="admonition-title">{title}</p>\n'
        )

    def directives(segment: str) -> str:
        segment = HINT_OPEN.sub(hint_open, segment)
        segment = HINT_CLOSE.sub(lambda match: f'\n{match.group("indent")}</div>', segment)
        segment = TAB_OPEN.sub(
            lambda match: f'{match.group("indent")}#### {match.group("title")}', segment
        )
        segment = CONTENT_REF_OPEN.sub("", segment)
        return DIRECTIVE_LINE.sub("", segment)

    text = outside_code(text, directives)

    leftover = None

    def find_leftover(segment: str) -> str:
        nonlocal leftover
        match = LEFTOVER_DIRECTIVE.search(segment)
        if match and leftover is None:
            leftover = match.group(0)
        return segment

    outside_code(text, find_leftover)
    if leftover is not None:
        raise ValueError(
            f"unhandled GitBook directive {leftover!r} in {current_source}; "
            "translate it in prepare_site.transform_markdown"
        )

    def rewriter(html: bool):
        def rewrite(match: re.Match[str]) -> str:
            destination = rewrite_destination(
                match.group("destination"),
                current_source=current_source,
                current_output=current_output,
                mapping=mapping,
                public_prefix=public_prefix,
                fallback=fallback,
                html=html,
            )
            return f'{match.group("prefix")}{destination}{match.group("suffix")}'
        return rewrite

    def links(segment: str) -> str:
        # CommonMark (GitHub) needs a space after '#' for a heading; Python
        # Markdown does not. A wrapped line starting "#179" is prose.
        segment = BARE_HASH_LINE.sub(r"\\#", segment)
        segment = MARKDOWN_LINK.sub(rewriter(False), segment)
        return HTML_URL.sub(rewriter(True), segment)

    text = outside_code(text, links)
    if current_source.name == "SUMMARY.md":
        text = transform_summary(text)
    return "\n".join(line.rstrip() for line in text.splitlines()).rstrip() + "\n"


# --------------------------------------------------------------------------
# Pages assembled from canonical files elsewhere in the repository
# --------------------------------------------------------------------------


def rewrite_repo_links(
    text: str,
    *,
    repo_path: PurePosixPath,
    page_source: PurePosixPath,
    site_pages: dict[PurePosixPath, PurePosixPath],
    repository_root: Path,
) -> str:
    """Point relative links in a repository file at their published location.

    ``repo_path`` is where the file lives in the repository (for example
    ``Corpora/ePark/README.md``); ``page_source`` is where its page sits in the
    assembled site tree. A link to another file that has a page
    (``site_pages``: repository path -> site source path) becomes a link to
    that page; any other repository file becomes a GitHub link (raw for
    images, ``tree`` for directories, ``blob`` otherwise).
    """

    def rewrite(match: re.Match[str]) -> str:
        destination = match.group("destination")
        enclosed = destination.startswith("<") and destination.endswith(">")
        raw = destination[1:-1] if enclosed else destination
        parsed = urlsplit(raw)
        if parsed.scheme or parsed.netloc or raw.startswith(("/", "#")) or not parsed.path:
            return match.group(0)
        target = PurePosixPath(posixpath.normpath(str(repo_path.parent / parsed.path)))
        if str(target).startswith(".."):
            return match.group(0)
        if target in site_pages:
            relative = posixpath.relpath(str(site_pages[target]), str(page_source.parent))
            new = urlunsplit(("", "", relative, parsed.query, parsed.fragment))
        else:
            fragment = f"#{parsed.fragment}" if parsed.fragment else ""
            if match.group("prefix").startswith("!"):
                new = f"{RAW_URL}/{target}"
            elif (repository_root / target).is_dir():
                new = f"{REPO_URL}/tree/main/{target}{fragment}"
            else:
                new = f"{REPO_URL}/blob/main/{target}{fragment}"
        new = new.replace(" ", "%20")
        if enclosed:
            new = f"<{new}>"
        return f'{match.group("prefix")}{new}{match.group("suffix")}'

    return outside_code(
        text, lambda segment: HTML_URL.sub(rewrite, MARKDOWN_LINK.sub(rewrite, segment))
    )


STATISTICS_HEADING = re.compile(r"(?m)^## Statistics[ \t]*$")
LEVEL2_HEADING = re.compile(r"(?m)^## ")


def insert_statistics(readme: str, stats_markdown: str) -> str:
    """Put ``stats_markdown`` under the README's ``## Statistics`` heading.

    Whatever the README has under that heading is replaced (it is a
    placeholder for readers on GitHub). A README without the heading gets the
    section before its first ``##`` heading, or at the end.
    """
    body = f"\n\n{stats_markdown.strip()}\n\n"
    heading = STATISTICS_HEADING.search(readme)
    if heading:
        following = LEVEL2_HEADING.search(readme, heading.end())
        end = following.start() if following else len(readme)
        return readme[:heading.end()] + body + readme[end:]
    first = LEVEL2_HEADING.search(readme)
    section = f"## Statistics{body}"
    if first:
        return readme[:first.start()] + section + readme[first.start():]
    return readme.rstrip() + "\n\n" + section


def render_corpus_page(
    repository_root: Path,
    page: CorpusPage,
    stats_markdown: str,
    site_pages: dict[PurePosixPath, PurePosixPath],
) -> str:
    """The published page for one corpus: its README, with statistics inserted."""
    corpus_dir = repository_root / "Corpora" / page.corpus
    # Matched by listing, not by opening "README.md": the container's file
    # system is case-insensitive and Linux CI is not.
    names = [p.name for p in corpus_dir.iterdir() if p.name.casefold() == "readme.md"]
    if len(names) != 1:
        raise FileNotFoundError(f"{page.corpus}: expected one README.md, found {names}")
    text = (corpus_dir / names[0]).read_text(encoding="utf-8")
    text = rewrite_repo_links(
        text,
        repo_path=PurePosixPath("Corpora") / page.corpus / names[0],
        page_source=page.source_path,
        site_pages=site_pages,
        repository_root=repository_root,
    )
    return insert_statistics(text, stats_markdown)


@dataclass(frozen=True)
class IncludedDoc:
    source: str  # repository-root file
    page: PurePosixPath  # where it sits in the English site tree
    icon: str


INCLUDED_DOCS = (
    IncludedDoc("POLICIES.md", POLICIES_PAGE, "scale-balanced"),
    IncludedDoc("AUDIO-PERMISSIONS.md", AUDIO_POLICY_PAGE, "file-audio"),
)


def render_included_doc(
    repository_root: Path,
    doc: IncludedDoc,
    site_pages: dict[PurePosixPath, PurePosixPath],
) -> str:
    """Render a canonical repository file as a site page, with a provenance note."""
    body = (repository_root / doc.source).read_text(encoding="utf-8")
    body = rewrite_repo_links(
        body,
        repo_path=PurePosixPath(doc.source),
        page_source=doc.page,
        site_pages=site_pages,
        repository_root=repository_root,
    )
    note = (
        '!!! info "Generated page"\n'
        f"    This page is built from [`{doc.source}`]({REPO_URL}/blob/main/{doc.source}) "
        "every time the site is published. Edit that file, not this page.\n\n"
    )
    return f"---\nicon: {doc.icon}\n---\n\n{_after_title(body, note)}"


def _after_title(text: str, insertion: str) -> str:
    """Insert ``insertion`` after the first ``# `` heading line (or at the top)."""
    match = re.search(r"(?m)^# .*$", text)
    if not match:
        return insertion + text
    return text[:match.end()] + "\n\n" + insertion + text[match.end():].lstrip("\n")


CORPORA_NAV_ENTRY = re.compile(
    r"(?m)^(?P<indent>\s*)\* \[[^\]]+\]\(the-bank-architecture/corpora/README\.md\)\s*$"
)


def corpora_nav(summary: str, pages: list[CorpusPage]) -> str:
    """Replace the corpus sub-list under the Corpora nav entry with one entry per corpus."""
    match = CORPORA_NAV_ENTRY.search(summary)
    if not match:
        raise ValueError("SUMMARY.md has no Corpora entry to attach corpus pages to")
    indent = match.group("indent")
    child_indent = indent + "  "
    lines = summary[match.end():].split("\n")
    # lines[0] is the remainder of the matched line (empty)
    consumed = 1
    while consumed < len(lines) and lines[consumed].startswith(child_indent + "*"):
        consumed += 1
    generated = [
        f"{child_indent}* [{page.nav_label}]({page.source_path})" for page in pages
    ]
    rest = "\n".join(lines[consumed:])
    return summary[:match.end()] + "\n" + "\n".join(generated) + "\n" + rest


# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------


def copy_static_assets(static_root: Path, output_dir: Path) -> None:
    if not static_root.is_dir():
        return
    for source in sorted(static_root.rglob("*")):
        if not source.is_file():
            continue
        target = output_dir / source.relative_to(static_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def assemble_english_sources(repository_root: Path, staging: Path) -> None:
    """Write the generated English pages into the staging source tree."""
    import language_pages  # local modules in docs/tools
    import site_stats

    pages = load_corpus_pages(repository_root)
    site_pages = {
        PurePosixPath("Corpora") / page.corpus / "README.md": page.source_path
        for page in pages
    }
    site_pages.update({PurePosixPath(doc.source): doc.page for doc in INCLUDED_DOCS})

    stats = site_stats.load_stats(repository_root / "statistics")
    for page in pages:
        target = staging / page.source_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            render_corpus_page(
                repository_root, page, site_stats.corpus_table(stats, page.corpus), site_pages
            ),
            encoding="utf-8",
        )
    for doc in INCLUDED_DOCS:
        target = staging / doc.page
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_included_doc(repository_root, doc, site_pages), encoding="utf-8")

    history = language_pages.load_history(repository_root / "statistics" / "language_history.csv")
    languages = language_pages.write_language_pages(staging, stats, history, pages)
    figures = language_pages.write_main_figures(staging / CORPORA_PAGE_DIR / "figures", history)

    summary_path = staging / "SUMMARY.md"
    summary = corpora_nav(summary_path.read_text(encoding="utf-8"), pages)
    summary_path.write_text(language_pages.languages_nav(summary, languages), encoding="utf-8")
    index_path = staging / CORPORA_PAGE_DIR / "README.md"
    index_path.write_text(
        site_stats.fill_corpora_index(
            index_path.read_text(encoding="utf-8"), stats, pages,
            link=lambda name: f"../../{language_pages.LANGUAGES_DIR}/{language_pages.language_slug(name)}.md",
            figures=figures,
        ),
        encoding="utf-8",
    )


ENGLISH_PAGE_NOTE = (
    '!!! note "English version"\n'
    "    The current, complete version of this page is in English: "
    "[{label}]({url}).\n\n"
)


def assemble_translated_sources(
    repository_root: Path, staging: Path, edition: Edition
) -> None:
    """Old translated corpus pages get a link to the current English page."""
    column = {"zh": "zh_page", "paiwan": "pwn_page"}.get(edition.key)
    if column is None:
        return
    for page in load_corpus_pages(repository_root):
        name = getattr(page, column)
        if not name:
            continue
        matches = list(staging.rglob(name))
        if len(matches) != 1:
            raise FileNotFoundError(
                f"{edition.key}: expected one translated page named {name}, found {len(matches)}"
            )
        path = matches[0]
        note = ENGLISH_PAGE_NOTE.format(label=page.nav_label, url=f"{NEW_SITE}/{CORPORA_PAGE_DIR}/{page.slug.casefold()}/")
        path.write_text(_after_title(path.read_text(encoding="utf-8"), note), encoding="utf-8")


def stage_edition(repository_root: Path, staging: Path, edition: Edition) -> bool:
    """Assemble an edition's source tree in ``staging``. False if it has no pages."""
    if staging.exists():
        shutil.rmtree(staging)
    if edition.source is None:
        return False
    shutil.copytree(repository_root / edition.source, staging)
    if edition.key == "en":
        assemble_english_sources(repository_root, staging)
    else:
        assemble_translated_sources(repository_root, staging, edition)
    return True


def prepare_edition(
    staging: Path,
    output_dir: Path,
    edition: Edition,
    repository_root: Path,
    fallback: dict[PurePosixPath, PurePosixPath] | None = None,
) -> dict[PurePosixPath, PurePosixPath]:
    mapping = build_path_map(staging)
    for source_relative, target_relative in mapping.items():
        target = output_dir / target_relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            transform_markdown(
                (staging / source_relative).read_text(encoding="utf-8"),
                current_source=source_relative,
                current_output=target_relative,
                mapping=mapping,
                public_prefix=edition.public_prefix,
                fallback=fallback,
            ),
            encoding="utf-8",
        )
    asset_dir = staging / ".gitbook" / "assets"
    if asset_dir.is_dir():
        shutil.copytree(asset_dir, output_dir / "assets" / "images", dirs_exist_ok=True)
    # Other non-Markdown files (generated figures) keep their paths.
    for path in sorted(staging.rglob("*")):
        relative = path.relative_to(staging)
        if path.is_file() and path.suffix != ".md" and relative.parts[0] != ".gitbook":
            target = output_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    copy_static_assets(repository_root / "docs" / "theme" / "static", output_dir)
    return mapping


def edition_config(
    repository_root: Path, output_root: Path, edition: Edition, present: list[Edition]
) -> Path:
    """Write the MkDocs config for one edition and return its path."""
    base = yaml.safe_load((repository_root / "mkdocs.yml").read_text(encoding="utf-8"))
    base["site_url"] = f"https://formosanbank.github.io{edition.public_prefix}"
    base["docs_dir"] = str((output_root / "docs" / edition.key).resolve())
    base["theme"]["custom_dir"] = str((repository_root / "docs" / "theme" / "overrides").resolve())
    base["theme"]["language"] = edition.theme_language
    base.setdefault("extra", {})["alternate"] = [
        {"name": other.label, "link": other.public_prefix, "lang": other.html_lang}
        for other in present
    ]
    path = output_root / f"mkdocs.{edition.key}.yml"
    path.write_text(yaml.safe_dump(base, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def prepare_site(repository_root: Path, output_root: Path) -> list[tuple[Edition, Path]]:
    """Assemble every edition; return (edition, config path) for those with pages."""
    repository_root = repository_root.resolve()
    output_root = output_root.resolve()
    if output_root == repository_root or repository_root.is_relative_to(output_root):
        raise ValueError("output directory must not contain the repository")
    if len(output_root.parts) < 3:
        raise ValueError(f"refusing broad output directory: {output_root}")
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    present: list[Edition] = []
    english: dict[PurePosixPath, PurePosixPath] | None = None
    for edition in EDITIONS:  # English first: the others fall back to it
        staging = output_root / "staging" / edition.key
        if not stage_edition(repository_root, staging, edition):
            continue
        mapping = prepare_edition(
            staging, output_root / "docs" / edition.key, edition, repository_root,
            fallback=None if edition.key == "en" else english,
        )
        if edition.key == "en":
            english = mapping
        present.append(edition)
    return [
        (edition, edition_config(repository_root, output_root, edition, present))
        for edition in present
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--repository-root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--output-root", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for edition, config in prepare_site(args.repository_root, args.output_root):
        print(f"{edition.key}\t{config}")


if __name__ == "__main__":
    main()

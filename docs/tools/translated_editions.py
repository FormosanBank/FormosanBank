"""Translated editions of the site, built from approved translations only.

For each target language (translations.TARGETS) and each English page:

* the page is rebuilt from its approved units (translations.render_translated_page);
  a page appears only once its title is approved;
* where an old hand-translated page exists (docs/site/legacy_translated_pages.csv),
  it stays as it is until its replacement exists, and the replacement is written
  at the old page's path so links to it keep working;
* an edition with no hand-written pages (Amis, Bunun) exists once its home page
  is translated.

Generated English text on language pages is translated through the shared
label templates (site_labels); figures appear only when every label they show
is approved, and are then drawn with the translated labels.

This module also writes the data the translation tool pages read
(``translate/<language>/data.json``).
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path, PurePosixPath

import language_pages
import site_labels
import translations as tr

LEGACY_CSV = Path("docs/site/legacy_translated_pages.csv")
NAV_ENTRY = re.compile(r"^(?P<indent>\s*)\* \[(?P<label>[^\]]*)\]\((?P<path>[^)]+\.md)\)\s*$", re.M)
PLACEHOLDER = re.compile(r"\{(\w+)\}")


def load_legacy_map(repository_root: Path) -> dict[str, dict[str, str]]:
    """edition -> {english page -> legacy page}."""
    out: dict[str, dict[str, str]] = {}
    with open(repository_root / LEGACY_CSV, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            out.setdefault(row["edition"], {})[row["english_page"]] = row["legacy_page"]
    return out


def english_nav(summary: str) -> list[tuple[str, str]]:
    """(label, page path) for every page in the English SUMMARY, in order."""
    return [(m.group("label"), m.group("path")) for m in NAV_ENTRY.finditer(summary)]


def english_pages(staging_en: Path) -> dict[str, str]:
    """Every English page (path -> Markdown) except the nav file."""
    return {
        str(PurePosixPath(p.relative_to(staging_en).as_posix())): p.read_text(encoding="utf-8")
        for p in sorted(staging_en.rglob("*.md"))
        if p.name != "SUMMARY.md"
    }


def _template_pattern(template: str) -> re.Pattern:
    parts = PLACEHOLDER.split(template)
    regex = ""
    for i, part in enumerate(parts):
        regex += re.escape(part) if i % 2 == 0 else f"(?P<{part}>.+?)"
    return re.compile(f"^{regex}$")


TEMPLATES = [label for label in site_labels.labels() if PLACEHOLDER.search(label)]
TEMPLATE_PATTERNS = [(label, _template_pattern(label)) for label in TEMPLATES]


def expand_templates(units: list[str], approved: dict[str, str]) -> dict[str, str]:
    """Approved translations for units that instantiate an approved template.

    ``{language}`` values are themselves translated (and the unit is skipped if
    the language name is not); other values (numbers, corpus names) are kept.
    """
    t = site_labels.translator(approved)
    out: dict[str, str] = {}
    for unit in units:
        for label, pattern in TEMPLATE_PATTERNS:
            match = pattern.match(unit)
            if not match:
                continue
            values = dict(match.groupdict())
            if "language" in values:
                name = approved.get(values["language"])
                if name is None:
                    break
                values["language"] = name
            text = t(label, **values)
            if text is not None:
                out[unit] = text
            break
    return out


def figure_labels(approved: dict[str, str], title_label: str, **values) -> dict[str, str] | None:
    """Translated figure text, or None unless every piece of it is approved."""
    t = site_labels.translator(approved)
    pieces = {"title": t(title_label, **values), "ylabel": t("Words (log scale)")}
    for _field, label in language_pages.SERIES:
        pieces[label] = t(label)
    return pieces if all(v is not None for v in pieces.values()) else None


def build_edition(
    staging_en: Path,
    staging_ed: Path,
    target: tr.TargetLanguage,
    approved: dict[str, str],
    legacy: dict[str, str],
    history: list[dict],
) -> list[str]:
    """Write the generated pages of one edition into its staging tree.

    ``staging_ed`` already holds the edition's hand-written pages (or is empty).
    Returns the English page paths that got a generated page.
    """
    pages = english_pages(staging_en)
    nav = english_nav((staging_en / "SUMMARY.md").read_text(encoding="utf-8"))
    titles = {path: label for label, path in nav}
    built: list[str] = []
    for path, markdown in pages.items():
        units = tr.segments(markdown)
        page_approved = {**approved, **expand_templates(units, approved)}
        markdown = _translate_figures(markdown, path, staging_en, staging_ed, page_approved, history)
        english_url = f"{language_pages_base()}{_url_of(path)}"
        rendered = tr.render_translated_page(
            markdown, page_approved, skip_reproduction=target.formosan,
            english_url=english_url, english_title=titles.get(path, path),
        )
        if rendered is None:
            continue
        out_path = legacy.get(path, path)
        target_file = staging_ed / out_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(rendered, encoding="utf-8")
        built.append(path)
    if built:
        _write_nav(staging_ed, nav, built, legacy, approved)
    return built


def language_pages_base() -> str:
    import prepare_site
    return prepare_site.NEW_SITE + "/"


def _url_of(path: str) -> str:
    stem = PurePosixPath(path).with_suffix("")
    parts = list(stem.parts)
    if parts and parts[-1].casefold() == "readme":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].casefold()
    return "/".join(parts) + ("/" if parts else "")


IMAGE_LINE = re.compile(r"^!\[(?P<alt>[^\]]*)\]\((?P<src>figures/[^)]+\.svg)\)\s*$", re.M)


def _translate_figures(markdown, path, staging_en, staging_ed, approved, history) -> str:
    """Replace growth-figure images with translated versions, or drop them."""

    def replace(match: re.Match) -> str:
        alt = match.group("alt")
        alt_text = approved.get(alt) or expand_templates([alt], approved).get(alt)
        src = match.group("src")
        language = None
        if PurePosixPath(path).parts[0] == language_pages.LANGUAGES_DIR:
            for label in site_labels.labels():
                if alt == site_labels.FIGURE_ALT.format(language=label):
                    language = label
        title_label = site_labels.FIGURE_TITLE if language else (
            "All data except Wikipedias" if "without-wikipedias" in src else "All FormosanBank data")
        values = {"language": approved.get(language, "")} if language else {}
        labels = figure_labels(approved, title_label, **values)
        if alt_text is None or labels is None:
            return ""
        kwargs = {"language": language} if language else (
            {"exclude_corpora": language_pages.EXCLUDED_FROM_SECOND_FIGURE} if "without" in src else {})
        series = language_pages.growth_series(history, **kwargs)
        figure_path = staging_ed / PurePosixPath(path).parent / src
        figure_path.parent.mkdir(parents=True, exist_ok=True)
        figure_path.write_text(language_pages.render_growth_svg(series, labels["title"], labels), encoding="utf-8")
        return f"![{alt_text}]({src})"

    return IMAGE_LINE.sub(replace, markdown)


def _write_nav(staging_ed: Path, nav, built: list[str], legacy: dict[str, str], approved) -> None:
    summary_path = staging_ed / "SUMMARY.md"
    built_set = set(built)
    titles = {}
    for path in built:
        first = (staging_ed / legacy.get(path, path)).read_text(encoding="utf-8").split("\n", 1)[0]
        titles[path] = first.lstrip("# ").strip()
    if summary_path.is_file():
        summary = summary_path.read_text(encoding="utf-8")
        reverse = {v: k for k, v in legacy.items()}

        def relabel(m: re.Match) -> str:
            english = reverse.get(m.group("path"))
            if english in built_set:
                return f"{m.group('indent')}* [{titles[english]}]({m.group('path')})"
            return m.group(0)

        summary = NAV_ENTRY.sub(relabel, summary)
        extra = [p for _label, p in nav if p in built_set and p not in legacy]
        if extra:
            summary = summary.rstrip() + "\n\n" + "\n".join(f"* [{titles[p]}]({p})" for p in extra) + "\n"
    else:
        order = [p for _label, p in nav if p in built_set]
        lines = ["# Table of contents", ""]
        home = [p for p in order if p == "README.md"]
        lines += [f"* [{titles[p]}]({p})" for p in home + [p for p in order if p != "README.md"]]
        summary = "\n".join(lines) + "\n"
    summary_path.write_text(summary, encoding="utf-8")


# --------------------------------------------------------------------------
# Data for the translation tool pages
# --------------------------------------------------------------------------


def tool_data(staging_en: Path, target: tr.TargetLanguage, store: list[dict], mandarin: list[dict]) -> dict:
    labels = site_labels.labels()
    label_set = set(labels)
    nav = english_nav((staging_en / "SUMMARY.md").read_text(encoding="utf-8"))
    pages_md = english_pages(staging_en)
    order = [p for _l, p in nav if p in pages_md] + sorted(set(pages_md) - {p for _l, p in nav})
    pages = []
    all_units: set[str] = set(labels)
    for path in order:
        if PurePosixPath(path).parts[0] == language_pages.LANGUAGES_DIR:
            continue  # generated from labels only
        units = tr.segments(pages_md[path], skip_reproduction=target.formosan, exclude=label_set)
        if not units:
            continue
        title = next((label for label, p in nav if p == path), units[0])
        pages.append({"id": path, "title": title, "units": units})
        all_units.update(units)
    existing: dict[str, dict] = {}
    for row in sorted(store, key=lambda r: (r["approved"] == "yes", r["date"])):
        if row["english"] in all_units:
            existing[row["english"]] = {
                "translation": row["translation"], "approved": row["approved"] == "yes",
                "origin": row["origin"], "dialect": row["dialect"],
            }
    data = {
        "format": tr.PAYLOAD_FORMAT, "language": target.code, "language_name": target.name,
        "formosan": target.formosan, "labels": labels, "pages": pages, "existing": existing,
    }
    if target.formosan:
        zh = tr.approved_map(mandarin)
        data["mandarin"] = {u: zh[u] for u in all_units if u in zh}
    return data


def write_tool_data(staging_en: Path, repository_root: Path) -> None:
    mandarin = tr.load_store("zho", repository_root / "docs" / "translations")
    for target in tr.TARGETS:
        store = tr.load_store(target.code, repository_root / "docs" / "translations")
        out = staging_en / "translate" / target.name.casefold()
        out.mkdir(parents=True, exist_ok=True)
        (out / "data.json").write_text(
            json.dumps(tool_data(staging_en, target, store, mandarin), ensure_ascii=False),
            encoding="utf-8",
        )

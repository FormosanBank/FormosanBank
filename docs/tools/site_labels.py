"""The site's shared labels: text translated once and used on every page.

Maintainer, 2026-10-18: "For any language, we only need to know how to
translate standard section headings once (it then applies automatically
everywhere else). Likewise, we only need to know how to translate the headings
on tables and figures once, with that propagating."

The list is computed from the code and registries that produce the text
(README headings, statistics rows, figure text, language and dialect names,
menu sections), so it can't drift from what the pages show. A label with
``{placeholders}`` is a sentence template: translators keep the placeholders.
"""

from __future__ import annotations

import csv
import re

import language_pages
import readme_layout
import site_stats

REPO_ROOT = site_stats.REPO_ROOT

# Sentences on generated pages, as templates: defined where the page is
# written (language_pages), so a translated template always matches the page.
LANGUAGE_INTRO = language_pages.LANGUAGE_INTRO
LANGUAGE_INTRO_ONE = language_pages.LANGUAGE_INTRO_ONE
LANGUAGE_INTRO_TAIL = language_pages.LANGUAGE_INTRO_TAIL
DIALECTS_NOTE = language_pages.DIALECTS_NOTE
CORPUS_WORDS = language_pages.CORPUS_WORDS
GROWTH_CAPTION_STEPS = language_pages.GROWTH_CAPTION_STEPS
GROWTH_CAPTION_START = language_pages.GROWTH_CAPTION_START
FIGURE_TITLE = language_pages.FIGURE_TITLE
FIGURE_ALT = language_pages.FIGURE_ALT
FULL_PAGE_IN_ENGLISH = "The complete, current version of this page is in English:"

SECTION_LABELS = (
    "Statistics", "Dialects", "Corpora", "Growth over time", "Languages",
    "Corpus Statistics", "By language", "By dialect", "Language", "Words",
    "All FormosanBank data", "All data except Wikipedias", "Words (log scale)",
    "Background", "The Bank Architecture", "Additional Resources",
)


def _strip_indent(label: str) -> str:
    return label.replace(site_stats.INDENT, "").strip()


def labels() -> list[str]:
    out: list[str] = []
    out += [h.lstrip("#").strip() for h in readme_layout.REQUIRED_HEADINGS]
    out += [_strip_indent(label) for label, _value, _fmt in site_stats.ROW_DEFS]
    out += [label for _field, label in language_pages.SERIES]
    out += list(SECTION_LABELS)
    out += [LANGUAGE_INTRO, LANGUAGE_INTRO_ONE, LANGUAGE_INTRO_TAIL, DIALECTS_NOTE,
            CORPUS_WORDS, GROWTH_CAPTION_STEPS, GROWTH_CAPTION_START, FIGURE_TITLE, FIGURE_ALT, FULL_PAGE_IN_ENGLISH,
            site_stats.UNKNOWN_DIALECT, re.sub(r"[*`]", "", site_stats.NOT_YET_COMPUTED)]
    with open(REPO_ROOT / "languages.csv", newline="", encoding="utf-8") as handle:
        out += [row["Language"].strip() for row in csv.DictReader(handle)]
    out.append("Truku")
    with open(REPO_ROOT / "dialects.csv", newline="", encoding="utf-8") as handle:
        out += [row["Official"].strip() for row in csv.DictReader(handle) if row["Official"].strip()]
    seen: set[str] = set()
    unique = []
    for label in out:
        if label and label not in seen:
            seen.add(label)
            unique.append(label)
    return unique


def translator(approved: dict[str, str]):
    """t(label, **values): the approved translation with values filled in, or None."""
    def t(label: str, **values) -> str | None:
        text = approved.get(label)
        if text is None:
            return None
        try:
            return text.format(**values)
        except (KeyError, IndexError, ValueError):
            return None  # a translation that dropped or mangled a placeholder
    return t

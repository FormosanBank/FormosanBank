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

# Sentences on generated pages, as templates.
LANGUAGE_INTRO = "FormosanBank holds {words} words of {language}, in {count} corpora."
LANGUAGE_INTRO_ONE = "FormosanBank holds {words} words of {language}, in 1 corpus."
LANGUAGE_INTRO_TAIL = "These numbers are generated from the corpus statistics every time the site is published."
DIALECTS_NOTE = "One column per dialect; unknown is data whose source does not record the dialect."
CORPUS_WORDS = "{corpus}: {words} words"
GROWTH_CAPTION = (
    "Each step is a change to the published corpus on main, counted with today's counting rules. "
    "A line starts where its count first rises above zero."
)
FIGURE_TITLE = "{language}: words over time"
FIGURE_ALT = "Growth of {language} in FormosanBank: total, transcribed, segmented and glossed words over time, log scale"
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
            CORPUS_WORDS, GROWTH_CAPTION, FIGURE_TITLE, FIGURE_ALT, FULL_PAGE_IN_ENGLISH,
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

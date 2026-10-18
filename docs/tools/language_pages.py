"""Language pages and growth figures for the documentation site.

Generated when the site is built, never committed:

* ``languages/README.md`` -- every language with data, linked to its page;
* ``languages/<language>.md`` -- one per language: its statistics, a table per
  dialect when ``dialects.csv`` lists two or more dialects for it (files
  without a dialect are "unknown"), the corpora with data for it, and a growth
  figure;
* growth figures for the corpora index page: all data, and all data except
  the Wikipedias corpus.

Current numbers come from ``statistics/*_corpora_stats.csv`` (via site_stats);
growth over time from ``statistics/language_history.csv`` (written by
QC/language_history.py). Figures: x = time, y = words on a log scale, plot area
twice as tall as it is wide (maintainer, 2026-10-18), four lines.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import site_stats

SERIES = (
    ("words", "Total words"),
    ("transcribed_words", "Transcribed words"),
    ("segmented_words", "Segmented words"),
    ("glossed_words", "Glossed words"),
)
SERIES_COLORS = ("#2b5f8a", "#c0702b", "#3b8f5a", "#8a4f9e")
# Segmented and glossed counts are often equal; segmented is drawn as a wide,
# light band under the glossed line so neither hides the other.
SERIES_STYLES = (
    {"linewidth": 1.8},
    {"linewidth": 1.8},
    {"linewidth": 5.0, "alpha": 0.45},
    {"linewidth": 1.6},
)
EXCLUDED_FROM_SECOND_FIGURE = frozenset({"Wikipedias"})
LANGUAGES_DIR = "languages"


@dataclass(frozen=True)
class Point:
    date: dt.datetime
    values: dict[str, int]


def language_slug(name: str) -> str:
    return name.casefold().replace(" ", "-")


def load_history(path: Path) -> list[dict]:
    if not Path(path).is_file():
        return []
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def growth_series(
    history: list[dict],
    *,
    language: str | None = None,
    exclude_corpora: frozenset[str] = frozenset(),
) -> list[Point]:
    """One point per commit: the four counts summed over the selected rows.

    Every commit in the history gets a point (a language absent at a commit
    counts zero), so lines don't interpolate across commits that removed data.
    """
    order: list[str] = []
    dates: dict[str, str] = {}
    sums: dict[str, dict[str, int]] = defaultdict(lambda: dict.fromkeys(f for f, _ in SERIES))
    for row in history:
        commit = row["commit"]
        if commit not in dates:
            order.append(commit)
            dates[commit] = row["date"]
            sums[commit] = {f: 0 for f, _ in SERIES}
        if language is not None and row["language"] != language:
            continue
        if row["corpus"] in exclude_corpora:
            continue
        for field, _label in SERIES:
            sums[commit][field] += int(row[field])
    points = [Point(dt.datetime.fromisoformat(dates[c]), sums[c]) for c in order]
    if points:
        # Steps are drawn from each change to the next; carry the last state to
        # today so the most recent change is visible.
        last = points[-1]
        today = dt.datetime.now(last.date.tzinfo)
        if today > last.date:
            points.append(Point(today, dict(last.values)))
    return points


def render_growth_svg(series: list[Point], title: str, labels: dict[str, str] | None = None) -> str:
    """The growth figure as SVG text: log y axis, plot area height = 2 x width.

    ``labels`` translates the axis label ("ylabel") and the series names
    (keyed by their English names); translated editions pass it.
    """
    labels = labels or {}
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    matplotlib.rcParams["svg.hashsalt"] = "formosanbank"
    fig, ax = plt.subplots(figsize=(5.2, 9.4))
    ax.set_box_aspect(2)  # plot area: height / width = 2
    plotted = 0
    for (field, label), color, style in zip(SERIES, SERIES_COLORS, SERIES_STYLES):
        xs = [p.date for p in series]
        # log scale: a zero has no position, so it is a gap in the line
        ys = [p.values[field] if p.values[field] > 0 else float("nan") for p in series]
        if any(y == y for y in ys):  # at least one non-NaN
            ax.plot(xs, ys, label=labels.get(label, label), color=color, drawstyle="steps-post", **style)
            plotted += 1
    ax.set_yscale("log")
    ax.set_title(title, fontsize=12)
    ax.set_ylabel(labels.get("ylabel", "Words (log scale)"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 7)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    for tick in ax.get_xticklabels():
        tick.set_rotation(45)
        tick.set_horizontalalignment("right")
    ax.grid(True, which="major", color="#d8dee4", linewidth=0.6)
    if plotted:
        ax.legend(loc="upper left", fontsize=9, frameon=False)
    fig.tight_layout()
    buffer = io.StringIO()
    fig.savefig(buffer, format="svg", metadata={"Date": None})
    plt.close(fig)
    return buffer.getvalue()


def site_stats_relative(page) -> str:
    return f"the-bank-architecture/corpora/{page.slug}.md"


def language_page(
    language: str,
    stats_rows: list[dict],
    history: list[dict],
    corpus_pages: list,
    figure_name: str,
    multi: set[str],
) -> str:
    rows = [row for row in stats_rows if row["language_name"] == language]
    totals = site_stats.aggregate(rows, lambda _row: language)[language]
    by_corpus = site_stats.aggregate(rows, lambda row: row["corpus"])
    labels = {page.corpus: page for page in corpus_pages}
    lines = [
        f"# {language}",
        "",
        f"FormosanBank holds {site_stats.fmt_count(totals['word_count'])} words of {language}, "
        f"in {len(by_corpus)} corpus{'es' if len(by_corpus) != 1 else ''}. These numbers are "
        "generated from the corpus statistics every time the site is published.",
        "",
        "## Statistics",
        "",
        site_stats.markdown_table([language], [totals]),
        "",
    ]
    dialects = site_stats.dialect_table(stats_rows, language, multi=multi)
    if dialects:
        lines += [
            "## Dialects",
            "",
            "One column per dialect; *unknown* is data whose source does not record the dialect.",
            "",
            dialects,
            "",
        ]
    lines += ["## Corpora", ""]
    for corpus in sorted(by_corpus, key=lambda c: (-(by_corpus[c]["word_count"] or 0), c)):
        page = labels.get(corpus)
        name = f"[{page.nav_label}](../{site_stats_relative(page)})" if page else corpus
        lines.append(f"* {name}: {site_stats.fmt_count(by_corpus[corpus]['word_count'])} words")
    lines += [
        "",
        "## Growth over time",
        "",
        f"![Growth of {language} in FormosanBank: total, transcribed, segmented and glossed "
        f"words over time, log scale](figures/{figure_name})",
        "",
        "Each step is a change to the published corpus on `main`, counted with today's counting rules. "
        "A line starts where its count first rises above zero.",
        "",
    ]
    return "\n".join(lines)


def languages_index(stats_rows: list[dict], names: list[str]) -> str:
    totals = site_stats.aggregate(stats_rows, lambda row: row["language_name"])
    lines = [
        "# Languages",
        "",
        "Statistics and growth for each language in FormosanBank. Click a language for its page.",
        "",
        "| Language | Words | Corpora |",
        "| --- | ---: | ---: |",
    ]
    for name in sorted(names, key=lambda n: (-(totals[n]["word_count"] or 0), n)):
        corpora = len({row["corpus"] for row in stats_rows if row["language_name"] == name and row["word_count"]})
        lines.append(
            f"| [{name}]({language_slug(name)}.md) | {site_stats.fmt_count(totals[name]['word_count'])} | {corpora} |"
        )
    return "\n".join(lines) + "\n"


def write_language_pages(
    staging: Path, stats_rows: list[dict], history: list[dict], corpus_pages: list
) -> list[str]:
    """Write the language pages and figures into the English staging tree.

    Returns the language names, alphabetically (the nav order).
    """
    multi = site_stats.multi_dialect_languages()
    names = sorted(
        {row["language_name"] for row in stats_rows if row["word_count"]},
    )
    out = staging / LANGUAGES_DIR
    (out / "figures").mkdir(parents=True, exist_ok=True)
    for name in names:
        figure = f"{language_slug(name)}-growth.svg"
        (out / "figures" / figure).write_text(
            render_growth_svg(growth_series(history, language=name), f"{name}: words over time"),
            encoding="utf-8",
        )
        (out / f"{language_slug(name)}.md").write_text(
            language_page(name, stats_rows, history, corpus_pages, figure, multi), encoding="utf-8"
        )
    (out / "README.md").write_text(languages_index(stats_rows, names), encoding="utf-8")
    return names


def write_main_figures(figures_dir: Path, history: list[dict]) -> str:
    """Write the two corpus-wide figures; return the Markdown that shows them."""
    figures_dir.mkdir(parents=True, exist_ok=True)
    (figures_dir / "growth-all.svg").write_text(
        render_growth_svg(growth_series(history), "All FormosanBank data"), encoding="utf-8"
    )
    (figures_dir / "growth-without-wikipedias.svg").write_text(
        render_growth_svg(
            growth_series(history, exclude_corpora=EXCLUDED_FROM_SECOND_FIGURE),
            "All data except Wikipedias",
        ),
        encoding="utf-8",
    )
    return (
        "#### Growth over time\n\n"
        "Words over time, log scale; each step is a change to the published corpus on `main`, "
        "counted with today's counting rules. The second figure leaves out the Wikipedias corpus.\n\n"
        '<div class="fb-figure-pair" markdown>\n\n'
        "![All FormosanBank data: total, transcribed, segmented and glossed words over time](figures/growth-all.svg)\n"
        "![FormosanBank data except Wikipedias: total, transcribed, segmented and glossed words over time]"
        "(figures/growth-without-wikipedias.svg)\n\n"
        "</div>\n"
    )


LANGUAGES_NAV_ANCHOR = "* [Corpora](the-bank-architecture/corpora/README.md)"


def languages_nav(summary: str, names: list[str]) -> str:
    """Add a Languages entry (with one sub-entry per language) before Corpora."""
    import re

    match = re.search(r"(?m)^(?P<indent>\s*)\* \[[^\]]+\]\(the-bank-architecture/corpora/README\.md\)", summary)
    if not match:
        raise ValueError("SUMMARY.md has no Corpora entry to put Languages beside")
    indent = match.group("indent")
    entries = [f"{indent}* [Languages]({LANGUAGES_DIR}/README.md)"] + [
        f"{indent}  * [{name}]({LANGUAGES_DIR}/{language_slug(name)}.md)" for name in names
    ]
    return summary[: match.start()] + "\n".join(entries) + "\n" + summary[match.start():]

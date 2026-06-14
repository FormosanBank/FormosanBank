#!/usr/bin/env python3
"""Manage FormosanBank GitBook corpus pages.

Two subcommands:
  add    scaffold a new corpus page + nav entry + CSV_TO_MD stats-map entry
  check  drift lint: every shipped corpus is fully wired; no leftover
         placeholders; (informational) Coming-Soon drift + translation lag

The three integration points for a published corpus are:
  1. en-us/the-bank-architecture/corpora/<slug>          (the page)
  2. a sub-bullet in en-us/SUMMARY.md                    (the nav entry)
  3. a CSV_TO_MD entry in update_corpus_stats.py         (the stats map)
"""
import argparse
import re
import sys
from pathlib import Path

PLACEHOLDER_RE = re.compile(r"\{\{[A-Z_]+\}\}")
CORPORA_LINK = "the-bank-architecture/corpora/"


def render_page(template_text: str, title: str) -> str:
    """Substitute {{TITLE}} only; leave prose placeholders for the skill."""
    return template_text.replace("{{TITLE}}", title)


def insert_nav_entry(summary_text: str, slug: str, label: str) -> str:
    """Insert an indented Corpora sub-bullet for <slug> as the last sub-bullet.

    Idempotent: if a bullet already links to corpora/<slug>, returns unchanged.
    """
    link = f"{CORPORA_LINK}{slug}"
    if f"({link})" in summary_text:
        return summary_text
    lines = summary_text.splitlines(keepends=True)
    last_idx = None
    for i, line in enumerate(lines):
        # indented sub-bullet (excludes the top-level "* [Corpora]" line)
        if line[:1].isspace() and line.lstrip().startswith("*") and CORPORA_LINK in line:
            last_idx = i
    if last_idx is None:
        raise ValueError("Could not locate the Corpora sub-list in SUMMARY.md")
    indent = lines[last_idx][: len(lines[last_idx]) - len(lines[last_idx].lstrip())]
    entry = f"{indent}* [{label}]({link})\n"
    # ensure the anchor line ends with a newline before inserting after it
    if not lines[last_idx].endswith("\n"):
        lines[last_idx] = lines[last_idx] + "\n"
    lines.insert(last_idx + 1, entry)
    return "".join(lines)


def insert_csv_to_md_entry(script_text: str, fbdir: str, slug: str) -> str:
    """Append '<fbdir>_corpora_stats.csv': '<slug>', before CSV_TO_MD's close.

    Idempotent: if the key already exists, returns unchanged.
    """
    key = f"'{fbdir}_corpora_stats.csv'"
    if key in script_text:
        return script_text
    lines = script_text.splitlines(keepends=True)
    start = next((i for i, l in enumerate(lines) if l.startswith("CSV_TO_MD")), None)
    if start is None:
        raise ValueError("CSV_TO_MD not found in update_corpus_stats.py")
    close = next((i for i in range(start, len(lines)) if lines[i].rstrip() == "}"), None)
    if close is None:
        raise ValueError("CSV_TO_MD closing brace not found")
    lines.insert(close, f"    {key}: '{slug}',\n")
    return "".join(lines)


def insert_readme_list_entry(readme_text: str, slug: str, label: str,
                             descriptors: str = "") -> str:
    """Insert a corpus-list bullet into corpora/README.md before its stats block.

    Bullets look like: `* [ePark](epark.md) (text, audio, English, Mandarin)`.
    `descriptors` is the optional trailing parenthetical, passed verbatim.
    Idempotent: if a bullet already links to <slug>, returns unchanged.
    """
    if f"]({slug})" in readme_text:
        return readme_text
    lines = readme_text.splitlines(keepends=True)
    # restrict to the region before the stats markers (the list lives above them)
    stop = next((i for i, l in enumerate(lines) if "CORPUS STATS START" in l), len(lines))
    last_idx = None
    for i in range(stop):
        line = lines[i]
        if line.lstrip().startswith("*") and "](" in line and ".md)" in line:
            last_idx = i
    if last_idx is None:
        raise ValueError("Could not locate the corpus list in corpora/README.md")
    suffix = f" {descriptors}" if descriptors else ""
    entry = f"* [{label}]({slug}){suffix}\n"
    if not lines[last_idx].endswith("\n"):
        lines[last_idx] = lines[last_idx] + "\n"
    lines.insert(last_idx + 1, entry)
    return "".join(lines)


def cmd_add(corpus, slug, nav_label, title, template, gitbook_root, descriptors=""):
    """Wire a corpus's four integration points idempotently. Returns 0/exit code."""
    root = Path(gitbook_root)
    corpora_dir = root / "en-us" / "the-bank-architecture" / "corpora"
    page_path = corpora_dir / slug
    summary_path = root / "en-us" / "SUMMARY.md"
    readme_path = corpora_dir / "README.md"
    stats_script = root / "update_corpus_stats.py"

    report = []

    # 1. page
    if page_path.exists():
        report.append(("page", "already present"))
    else:
        template_text = Path(template).read_text(encoding="utf-8")  # raises if missing
        page_path.write_text(render_page(template_text, title), encoding="utf-8")
        report.append(("page", "created"))

    # 2. nav bullet in SUMMARY.md
    summary_text = summary_path.read_text(encoding="utf-8")
    new_summary = insert_nav_entry(summary_text, slug, nav_label)
    if new_summary != summary_text:
        summary_path.write_text(new_summary, encoding="utf-8")
        report.append(("nav", "created"))
    else:
        report.append(("nav", "already present"))

    # 3. corpus-list bullet in corpora/README.md
    readme_text = readme_path.read_text(encoding="utf-8")
    new_readme = insert_readme_list_entry(readme_text, slug, nav_label, descriptors)
    if new_readme != readme_text:
        readme_path.write_text(new_readme, encoding="utf-8")
        report.append(("readme_list", "created"))
    else:
        report.append(("readme_list", "already present"))

    # 4. CSV_TO_MD stats-map entry
    script_text = stats_script.read_text(encoding="utf-8")
    new_script = insert_csv_to_md_entry(script_text, corpus, slug)
    if new_script != script_text:
        stats_script.write_text(new_script, encoding="utf-8")
        report.append(("stats_map", "created"))
    else:
        report.append(("stats_map", "already present"))

    for name, status in report:
        print(f"  {name}: {status}")
    return 0

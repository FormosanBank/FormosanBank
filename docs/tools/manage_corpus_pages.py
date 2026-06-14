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


from dataclasses import dataclass, field


@dataclass
class CheckResult:
    integration_issues: list = field(default_factory=list)
    placeholder_issues: list = field(default_factory=list)
    stats_csv_issues: list = field(default_factory=list)  # informational (separate pipeline)
    coming_soon: list = field(default_factory=list)       # informational
    translation_lag: list = field(default_factory=list)   # informational

    @property
    def ok(self) -> bool:
        # only integration + placeholders gate
        return not self.integration_issues and not self.placeholder_issues


def find_shipped_corpora(corpora_path: Path) -> list:
    return sorted(
        d.name for d in corpora_path.iterdir()
        if d.is_dir() and (d / "XML").is_dir()
    )


def load_ignore(ignore_path) -> set:
    if not ignore_path:
        return set()
    p = Path(ignore_path)
    if not p.exists():
        return set()
    out = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.add(line)
    return out


def parse_csv_to_md(script_text: str) -> dict:
    result = {}
    in_dict = False
    for line in script_text.splitlines():
        if line.startswith("CSV_TO_MD"):
            in_dict = True
            continue
        if in_dict and line.rstrip() == "}":
            break
        if in_dict:
            m = re.search(r"'([^']+)'\s*:\s*'([^']+)'", line)
            if m:
                result[m.group(1)] = m.group(2)
    return result


def run_check(gitbook_root, corpora_path, ignore_path) -> CheckResult:
    root = Path(gitbook_root)
    corpora = Path(corpora_path)
    pages_dir = root / "en-us" / "the-bank-architecture" / "corpora"
    summary_text = (root / "en-us" / "SUMMARY.md").read_text(encoding="utf-8")
    readme_text = (pages_dir / "README.md").read_text(encoding="utf-8")
    csv_to_md = parse_csv_to_md(
        (root / "update_corpus_stats.py").read_text(encoding="utf-8")
    )
    ignore = load_ignore(ignore_path)
    statistics = root / "statistics"
    shipped = find_shipped_corpora(corpora)

    res = CheckResult()

    # 1. integration (gating) + stats-CSV presence (informational)
    for corpus in shipped:
        if corpus in ignore:
            continue
        csv_name = f"{corpus}_corpora_stats.csv"
        if not (statistics / csv_name).exists():
            res.stats_csv_issues.append(
                f"{corpus}: no stats CSV ({csv_name}) in statistics/ (synced separately)"
            )
        slug = csv_to_md.get(csv_name)
        if slug is None:
            res.integration_issues.append(
                f"{corpus}: no CSV_TO_MD entry for {csv_name}"
            )
            continue
        if not (pages_dir / slug).exists():
            res.integration_issues.append(
                f"{corpus}: mapped page {slug} does not exist"
            )
        if f"(the-bank-architecture/corpora/{slug})" not in summary_text:
            res.integration_issues.append(
                f"{corpus}: no SUMMARY.md nav entry for {slug}"
            )
        if f"]({slug})" not in readme_text:
            res.integration_issues.append(
                f"{corpus}: no corpora/README.md list entry for {slug}"
            )

    # 2. leftover placeholders in any corpus page
    for page in sorted(pages_dir.glob("*.md")):
        if PLACEHOLDER_RE.search(page.read_text(encoding="utf-8")):
            res.placeholder_issues.append(
                f"{page.name}: contains a leftover {{...}} placeholder"
            )

    # 3. coming-soon drift (informational)
    shipped_set = set(shipped)
    for md in sorted((root / "en-us").rglob("*.md")):
        for line in md.read_text(encoding="utf-8").splitlines():
            if "Coming Soon" in line:
                for corpus in shipped_set:
                    if corpus in line:
                        res.coming_soon.append(
                            f"{md.relative_to(root)}: 'Coming Soon' names shipped '{corpus}'"
                        )

    # 4. translation lag (informational): en-us pages missing from pwn / zh-TW
    en_pages = {p.name for p in pages_dir.glob("*.md")} - {"README.md"}
    for lang in ("pwn", "zh-TW"):
        lang_dir = root / lang / "the-bank-architecture" / "corpora"
        lang_pages = {p.name for p in lang_dir.glob("*.md")} if lang_dir.is_dir() else set()
        for missing in sorted(en_pages - lang_pages):
            res.translation_lag.append(f"{lang}: missing {missing}")

    return res

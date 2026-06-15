#!/usr/bin/env python3
"""Manage FormosanBank GitBook corpus pages.

Two subcommands:
  add    scaffold a new corpus page + nav entry + README list bullet
         + CSV_TO_MD stats-map entry
  check  drift lint: every shipped corpus is fully wired; no leftover
         placeholders; (informational) missing stats CSV, Coming-Soon
         drift, and translation lag

The four integration points for a published corpus are:
  1. en-us/the-bank-architecture/corpora/<slug>          (the page)
  2. a sub-bullet in en-us/SUMMARY.md                    (the nav entry)
  3. a bullet in en-us/the-bank-architecture/corpora/README.md  (corpus list)
  4. a CSV_TO_MD entry in update_corpus_stats.py         (the stats map)

The corpus-list page's aggregate stats table and each corpus page's stats
block are auto-filled by update_corpus_stats.py from point 4 once the
corpus's stats CSV exists; they are not edited here.
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
    # canonical CSVs live in the sibling FormosanBank/statistics, not the GitBook repo
    statistics = corpora.parent / "statistics"
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


def cmd_check(gitbook_root, corpora_path, ignore_path, strict) -> int:
    res = run_check(gitbook_root, corpora_path, ignore_path)

    def section(title, items):
        print(f"\n{title}: {len(items)}")
        for m in items:
            print(f"  - {m}")

    section("Integration issues (gating)", res.integration_issues)
    section("Leftover placeholders (gating)", res.placeholder_issues)
    section("Missing stats CSVs (informational; synced separately)", res.stats_csv_issues)
    section("Coming-Soon drift (informational)", res.coming_soon)
    section("Translation lag (informational)", res.translation_lag)

    if res.ok:
        print("\nOK: every shipped corpus is fully wired; no leftover placeholders.")
        return 0
    print("\nFAIL: integration drift detected.")
    return 1 if strict else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("add", help="scaffold a new corpus page + nav + stats-map entry")
    a.add_argument("--corpus", required=True, help="FormosanBank Corpora/ dir name")
    a.add_argument("--slug", required=True, help="page filename, e.g. my-corpus.md")
    a.add_argument("--nav-label", required=True, help="label shown in SUMMARY.md + README list")
    a.add_argument("--title", required=True, help="page H1")
    a.add_argument("--template", required=True, help="path to the page template")
    a.add_argument("--descriptors", default="",
                   help="trailing parenthetical for the README list bullet, "
                        "e.g. '(text, audio, English, Mandarin)'")
    a.add_argument("--gitbook-root", default=".", help="GitBook repo root")

    c = sub.add_parser("check", help="drift lint over shipped corpora")
    c.add_argument("--gitbook-root", default=".", help="GitBook repo root")
    c.add_argument("--corpora-path", default="../FormosanBank/Corpora",
                   help="FormosanBank Corpora/ directory")
    c.add_argument("--ignore", default=None,
                   help="path to ignore-list (default: <root>/corpus_pages_ignore.txt)")
    c.add_argument("--strict", action="store_true",
                   help="exit nonzero on integration drift")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "add":
        return cmd_add(
            corpus=args.corpus, slug=args.slug, nav_label=args.nav_label,
            title=args.title, template=args.template, gitbook_root=args.gitbook_root,
            descriptors=args.descriptors,
        )
    if args.command == "check":
        ignore = args.ignore
        if ignore is None:
            default_ignore = Path(args.gitbook_root) / "corpus_pages_ignore.txt"
            ignore = str(default_ignore) if default_ignore.exists() else None
        return cmd_check(
            gitbook_root=args.gitbook_root, corpora_path=args.corpora_path,
            ignore_path=ignore, strict=args.strict,
        )
    return 2


if __name__ == "__main__":
    sys.exit(main())

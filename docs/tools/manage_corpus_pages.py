#!/usr/bin/env python3
"""Register corpora on the documentation site, and lint that every corpus is there.

    python docs/tools/manage_corpus_pages.py add --corpus <Dir> --slug <slug> \\
        --nav-label "<menu label>" [--descriptors "text, audio, ..."]
    python docs/tools/manage_corpus_pages.py check [--strict]

A corpus page is its README (``Corpora/<Dir>/README.md``), rendered by
``prepare_site.py``. The only thing to register is one row in
``docs/site/corpus_pages.csv``: the page's slug (its URL), its label in the
site menu, and a short list of what it contains. The menu entry, the bullet on
the corpora index page and the statistics table all follow from that row, so
the four places a GitBook corpus page had to be wired into (page, menu, list,
stats map) are now one.

``check`` reports, and with ``--strict`` exits 1 on:
* a corpus directory with no row, or a row with no corpus directory;
* duplicate slugs;
* a README whose layout breaks the rules in readme_layout.py (headings,
  order, licence lines), unless readme_sections_pending.txt lists it.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO_ROOT = TOOLS.parents[1]
sys.path.insert(0, str(TOOLS))

import readme_layout  # noqa: E402

CSV_PATH = REPO_ROOT / "docs" / "site" / "corpus_pages.csv"
FIELDS = ("corpus", "slug", "nav_label", "descriptors", "zh_page", "pwn_page")


def read_rows(path: Path = CSV_PATH) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(rows: list[dict], path: Path = CSV_PATH) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def add(rows: list[dict], corpus: str, slug: str, nav_label: str, descriptors: str = "") -> list[dict]:
    """Append a row for ``corpus`` (idempotent; refuses a slug already in use)."""
    for row in rows:
        if row["corpus"] == corpus:
            return rows
        if row["slug"].casefold() == slug.casefold():
            raise ValueError(f"slug {slug!r} is already used by {row['corpus']}")
    return rows + [{
        "corpus": corpus, "slug": slug, "nav_label": nav_label,
        "descriptors": descriptors, "zh_page": "", "pwn_page": "",
    }]


def _pending(repo_root: Path) -> set[tuple[str, str]]:
    path = repo_root / "readme_sections_pending.txt"
    if not path.exists():
        return set()
    pairs = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            corpus, _, check = line.partition(" ")
            pairs.add((corpus, check.strip()))
    return pairs


def _readme(corpus_dir: Path) -> str | None:
    for path in corpus_dir.iterdir():
        if path.name.casefold() == "readme.md":
            return path.read_text(encoding="utf-8")
    return None


def check(repo_root: Path, rows: list[dict]) -> list[str]:
    corpora = sorted(
        d.name for d in (repo_root / "Corpora").iterdir() if (d / "XML").is_dir()
    )
    listed = [row["corpus"] for row in rows]
    problems = [f"{c}: no row in docs/site/corpus_pages.csv" for c in corpora if c not in listed]
    problems += [f"{c}: row in corpus_pages.csv but no Corpora/{c}/XML" for c in listed if c not in corpora]
    slugs = [row["slug"].casefold() for row in rows]
    problems += [f"slug {s!r} is used more than once" for s in sorted(set(slugs)) if slugs.count(s) > 1]
    pending = _pending(repo_root)
    for corpus in corpora:
        readme = _readme(repo_root / "Corpora" / corpus)
        if readme is None:
            problems.append(f"{corpus}: no README.md")
            continue
        if (corpus, "structure") not in pending:
            problems += [f"{corpus}: {p}" for p in readme_layout.structure_problems(readme)]
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    add_p = sub.add_parser("add", help="register a corpus page")
    add_p.add_argument("--corpus", required=True, help="directory name under Corpora/")
    add_p.add_argument("--slug", required=True, help="page URL slug, e.g. blust-thao-dictionary")
    add_p.add_argument("--nav-label", required=True)
    add_p.add_argument("--descriptors", default="")
    check_p = sub.add_parser("check", help="lint corpus registration and README layout")
    check_p.add_argument("--strict", action="store_true", help="exit 1 on any problem")
    args = parser.parse_args(argv)

    rows = read_rows()
    if args.command == "add":
        write_rows(add(rows, args.corpus, args.slug.removesuffix(".md"), args.nav_label, args.descriptors))
        print(f"{args.corpus}: registered in {CSV_PATH.relative_to(REPO_ROOT)}")
        return 0
    problems = check(REPO_ROOT, rows)
    for problem in problems:
        print(problem)
    print(f"{len(rows)} corpus page(s) registered; {len(problems)} problem(s)")
    return 1 if problems and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())

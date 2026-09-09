#!/usr/bin/env python3
"""Manage per-corpus HARD-finding waivers.

Two subcommands.

**propose** — turn a validator's findings CSV into waiver rows to fill in:

    python QC/validation/validate_text.py by_path --path Corpora/X/XML --csv /tmp/t.csv
    python QC/validation/waivers.py propose --csv /tmp/t.csv

Every unwaived HARD finding whose rule is waivable is appended to the owning
corpus's ``CodeAndDocs/qc_waivers.tsv`` with the reason set to ``TODO``. The
validators reject a ``TODO`` reason, so the run keeps failing until a human
writes why — the mechanical half is automated, the judgement half cannot be.

There is deliberately no flag that supplies a reason. The moment waiving is
one command with no typing, it stops being a decision.

**report** — every waiver in the bank, in one table:

    python QC/validation/waivers.py report

Scattered across thirty ``CodeAndDocs/`` directories, waivers are invisible in
aggregate; this is the view that keeps them honest.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from QC.validation._waivers import (  # noqa: E402
    COLUMNS,
    TODO_REASON,
    WAIVABLE_RULES,
    WaiverError,
    corpus_root_for,
    load_waivers,
    relative_xml_name,
    waiver_path,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _existing_keys(corpus_dir: Path) -> set[tuple[str, str, str]]:
    """Keys already present, read leniently.

    ``load_waivers`` refuses a TODO reason by design, but ``propose`` must be
    re-runnable while TODOs are outstanding without duplicating rows — so it
    reads the raw keys rather than the validated waivers.
    """
    path = waiver_path(corpus_dir)
    if not path.is_file():
        return set()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return {
            (
                (row.get("rule_id") or "").strip(),
                (row.get("file") or "").strip(),
                (row.get("location") or "").strip(),
            )
            for row in csv.DictReader(handle, delimiter="\t")
        }


def _append(corpus_dir: Path, rows: list[tuple[str, str, str]]) -> Path:
    path = waiver_path(corpus_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.is_file() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        if write_header:
            writer.writerow(COLUMNS)
        for rule_id, xml_file, location in rows:
            writer.writerow([rule_id, xml_file, location, TODO_REASON])
    return path


def propose(findings_csv: Path) -> int:
    with findings_csv.open(encoding="utf-8-sig", newline="") as handle:
        findings = list(csv.DictReader(handle))

    pending: dict[Path, list[tuple[str, str, str]]] = defaultdict(list)
    skipped: set[str] = set()
    for row in findings:
        if row.get("severity") != "HARD":
            continue
        rule_id = (row.get("rule_id") or "").strip()
        if rule_id not in WAIVABLE_RULES:
            skipped.add(rule_id)
            continue
        xml_path = Path(row["file"])
        corpus_dir = corpus_root_for(xml_path)
        if corpus_dir is None:
            print(
                f"no corpus (no CodeAndDocs/ ancestor) for {xml_path}; skipped",
                file=sys.stderr,
            )
            continue
        key = (rule_id, relative_xml_name(xml_path, corpus_dir),
               (row.get("location") or "").strip())
        if key in _existing_keys(corpus_dir) or key in pending[corpus_dir]:
            continue
        pending[corpus_dir].append(key)

    if skipped:
        print(
            "not waivable, fix instead: " + ", ".join(sorted(skipped)),
            file=sys.stderr,
        )
    if not pending:
        print("No new waivable HARD findings.")
        return 0

    total = 0
    for corpus_dir, rows in sorted(pending.items()):
        path = _append(corpus_dir, rows)
        total += len(rows)
        print(f"{path}: +{len(rows)} row(s)")
        for rule_id, xml_file, location in rows:
            print(f"    {rule_id}\t{xml_file}\t{location}\t{TODO_REASON}")
    print(
        f"\n{total} row(s) written with reason={TODO_REASON}. Replace every "
        "one with why the finding is accepted; validation fails until you do."
    )
    return 0


def report(repo_root: Path) -> int:
    corpora = repo_root / "Corpora"
    if not corpora.is_dir():
        print(f"no Corpora/ under {repo_root}", file=sys.stderr)
        return 2

    rows: list[tuple[str, str, str, str, str]] = []
    failed = False
    for corpus_dir in sorted(p for p in corpora.iterdir() if p.is_dir()):
        try:
            waivers = load_waivers(corpus_dir)
        except WaiverError as exc:
            print(f"{corpus_dir.name}: {exc}", file=sys.stderr)
            failed = True
            continue
        for waiver in waivers:
            rows.append((corpus_dir.name, waiver.rule_id, waiver.file,
                         waiver.location, waiver.reason))

    if not rows:
        print("No waivers in the bank.")
        return 1 if failed else 0

    widths = [max(len(r[i]) for r in rows) for i in range(4)]
    header = ("corpus", "rule", "file", "location")
    widths = [max(w, len(h)) for w, h in zip(widths, header, strict=True)]
    line = "  ".join(h.ljust(w) for h, w in zip(header, widths, strict=True))
    print(line + "  reason")
    print("-" * (len(line) + 8))
    for corpus, rule_id, xml_file, location, reason in rows:
        cells = [corpus, rule_id, xml_file, location]
        print("  ".join(c.ljust(w) for c, w in zip(cells, widths, strict=True))
              + "  " + reason)
    print(f"\n{len(rows)} waiver(s) across "
          f"{len({r[0] for r in rows})} corpus/corpora.")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_propose = sub.add_parser(
        "propose", help="append TODO waiver rows for unwaived HARD findings")
    p_propose.add_argument("--csv", type=Path, required=True,
                           help="a validator's findings CSV")

    p_report = sub.add_parser("report", help="every waiver in the bank")
    p_report.add_argument("--repo-root", type=Path, default=REPO_ROOT)

    args = parser.parse_args(argv)
    try:
        if args.command == "propose":
            return propose(args.csv)
        return report(args.repo_root)
    except WaiverError as exc:
        print(f"waiver error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

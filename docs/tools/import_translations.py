#!/usr/bin/env python3
"""Add a translator's saved work (the file they emailed) to the translation store.

    python docs/tools/import_translations.py <saved-work.json>            # report only
    python docs/tools/import_translations.py <saved-work.json> --apply    # write the store

The file comes from the site's translation pages (/translate/<language>/,
"Download my work"); text pasted from "Copy my work" can be saved to a file
and used the same way. The report says how many translations are new, how many
were already in the store, which English sentences are no longer on the site
(kept anyway: they are data), and anything that blocks the import (a newly
approved translation for a sentence already approved in another dialect).
Nothing is written without --apply, and nothing already in the store is ever
overwritten: every change is a new row.

After applying: commit docs/translations/<code>.tsv. Approved translations
appear on the site at the next build; approved Formosan translations become
FormosanBank GitBook corpus data the next time that corpus is built
(Corpora/FormosanBankGitBook/CodeAndDocs/generate_xml.sh).
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import translations as tr  # noqa: E402


def inventory_keys(repository_root: Path, target: tr.TargetLanguage) -> set[str]:
    """Every unit the site currently asks translators for, in this language."""
    import prepare_site
    import site_labels
    import translated_editions

    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp) / "en"
        prepare_site.stage_edition(repository_root, staging, prepare_site.EDITIONS_BY_KEY["en"])
        data = translated_editions.tool_data(staging, target, [], [])
    keys = set(site_labels.labels())
    for page in data["pages"]:
        keys.update(page["units"])
    return keys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", type=Path)
    parser.add_argument("--apply", action="store_true", help="write the store (default: report only)")
    args = parser.parse_args(argv)

    payload = tr.parse_payload(args.file.read_text(encoding="utf-8"))
    target = tr.TARGETS_BY_CODE[payload["language"]]
    store = tr.load_store(target.code)
    keys = inventory_keys(tr.REPO_ROOT, target)
    new_store, report = tr.merge_import(store, payload, keys)

    approved = sum(1 for row in report.new if row["approved"] == "yes")
    print(f"{target.name} translations from {payload['translator']!r} (dialect {payload.get('dialect', '')!r}):")
    print(f"  {len(payload['items'])} items in the file")
    print(f"  {len(report.new)} new rows ({approved} approved, {len(report.new) - approved} drafts)")
    print(f"  {report.unchanged} already in the store, unchanged")
    if report.unknown:
        print(f"  {len(report.unknown)} English sentences no longer on the site (kept as data):")
        for english in report.unknown[:20]:
            print(f"    - {english}")
    for message in report.errors:
        print(f"ERROR: {message}")
    if report.blocked:
        print(f"BLOCKED: {len(report.blocked)} approved translation(s) clash with another dialect:")
        for line in report.blocked:
            print(f"    - {line}")
        print("Nothing written. Decide which dialect the site shows, then re-run.")
    if not report.ok:
        return 1
    if args.apply:
        tr.save_store(target.code, new_store)
        print(f"Wrote {tr.store_path(target.code).relative_to(tr.REPO_ROOT)} ({len(new_store)} rows).")
    else:
        print("Report only. Re-run with --apply to write the store.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

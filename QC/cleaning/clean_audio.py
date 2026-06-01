"""clean_audio.py — remove broken <AUDIO> entries from XML (and optionally disk).

Consumes a `broken_audio.csv` produced by `QC/validation/validate_audio.py`
and removes each listed `<AUDIO>` element from its containing XML file.
Optionally also deletes the audio file from disk.

CLI shape:

    python QC/cleaning/clean_audio.py \\
        --corpus_path <corpus_root> \\
        --broken_csv  <path/to/broken_audio.csv> \\
        [--dry-run | --apply] \\
        [--also-delete-files]

Defaults: dry-run is ON (must pass --apply for changes to land). This
mirrors the convention of the in-place XML mutators in this repo and
avoids surprising operators who forget to inspect the diff first.

Layout convention (per the B9.2 plan): canonical XML files live under
`<corpus_path>/XML/` and audio files under `<corpus_path>/Audio/`. The
CSV's `xml_file` column carries an absolute path; the script trusts
that path and uses it directly.

Replaces the legacy `remove_non_working_audio.py`, which hardcoded the
ePark `Final_audio`/`Final_XML` paths, had no CLI, and silently failed
to delete audio files on disk.
"""
import argparse
import csv
import os
import sys
from collections import defaultdict
from pathlib import Path

from lxml import etree


def load_broken_csv(broken_csv: Path) -> list[dict]:
    """Read the broken_audio.csv into a list of dicts.

    Expected columns: xml_file, audio_file, kind. Extra columns are
    preserved. Empty file (header only) → empty list.
    """
    rows: list[dict] = []
    with open(broken_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def group_by_xml(rows: list[dict]) -> dict[Path, list[dict]]:
    """Group CSV rows by xml_file so we open each XML at most once."""
    out: dict[Path, list[dict]] = defaultdict(list)
    for row in rows:
        out[Path(row["xml_file"])].append(row)
    return out


def remove_audio_elements(
    xml_path: Path,
    audio_filenames: list[str],
) -> tuple[int, list[str]]:
    """Remove every `<AUDIO file="<name>">` whose name is in `audio_filenames`.

    Returns (n_removed, missing_targets) — missing_targets is the
    audio_filenames that were not found in the file (so the operator
    can investigate, rather than silently ignored).
    """
    tree = etree.parse(str(xml_path))
    root = tree.getroot()
    targets = set(audio_filenames)
    found: set[str] = set()
    n_removed = 0
    # iter() is safe for removal because we collect first, then remove.
    to_remove = [a for a in root.iter("AUDIO") if a.get("file") in targets]
    for elem in to_remove:
        found.add(elem.get("file"))
        parent = elem.getparent()
        if parent is not None:
            parent.remove(elem)
            n_removed += 1
    tree.write(str(xml_path), encoding="utf-8", xml_declaration=True)
    missing = sorted(targets - found)
    return n_removed, missing


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--corpus_path", required=True, type=Path,
                        help="root of the corpus; contains XML/ and Audio/")
    parser.add_argument("--broken_csv", required=True, type=Path,
                        help="path to broken_audio.csv from validate_audio.py")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", dest="apply", action="store_false",
                       help="print intended changes without modifying anything (default)")
    group.add_argument("--apply", dest="apply", action="store_true",
                       help="actually modify XMLs (and optionally disk)")
    parser.set_defaults(apply=False)
    parser.add_argument("--also-delete-files", action="store_true",
                        help="also delete the audio file from <corpus_path>/Audio/")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)

    if not args.broken_csv.is_file():
        print(f"ERROR: broken_csv not found: {args.broken_csv}", file=sys.stderr)
        return 2

    rows = load_broken_csv(args.broken_csv)
    if not rows:
        mode = "APPLY" if args.apply else "DRY-RUN"
        print(f"[{mode}] broken_audio.csv is empty — no-op.")
        return 0

    by_xml = group_by_xml(rows)
    audio_root = args.corpus_path / "Audio"

    mode = "APPLY" if args.apply else "DRY-RUN"
    total_audio_targets = sum(len(v) for v in by_xml.values())
    print(f"[{mode}] {total_audio_targets} <AUDIO> removal(s) across {len(by_xml)} XML file(s).")
    if not args.apply:
        print("[DRY-RUN] re-run with --apply to make changes.")

    n_removed_total = 0
    n_deleted_total = 0
    for xml_path, xml_rows in by_xml.items():
        audio_targets = [r["audio_file"] for r in xml_rows]
        kinds = [r.get("kind", "") for r in xml_rows]
        print(f"  {xml_path}")
        for fname, kind in zip(audio_targets, kinds):
            tag = f" [{kind}]" if kind else ""
            print(f"    - {fname}{tag}")

        if not args.apply:
            continue

        if not xml_path.is_file():
            print(f"    WARNING: XML file not found, skipping: {xml_path}", file=sys.stderr)
            continue

        n_removed, missing = remove_audio_elements(xml_path, audio_targets)
        n_removed_total += n_removed
        if missing:
            print(
                f"    WARNING: {len(missing)} target(s) not present in XML: {missing}",
                file=sys.stderr,
            )

        if args.also_delete_files:
            for fname in audio_targets:
                # Look for the audio file under <corpus_path>/Audio/ (recursive)
                # because corpora often nest by sub-corpus/language.
                deleted = False
                for candidate in audio_root.rglob(fname):
                    try:
                        os.remove(candidate)
                        n_deleted_total += 1
                        deleted = True
                    except OSError as e:
                        print(
                            f"    WARNING: failed to delete {candidate}: {e}",
                            file=sys.stderr,
                        )
                if not deleted:
                    print(
                        f"    WARNING: audio file not found under {audio_root}: {fname}",
                        file=sys.stderr,
                    )

    if args.apply:
        print(f"[APPLY] removed {n_removed_total} <AUDIO> element(s).")
        if args.also_delete_files:
            print(f"[APPLY] deleted {n_deleted_total} audio file(s) from disk.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

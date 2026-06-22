"""clean_audio.py — remove broken <AUDIO> entries from XML (and optionally disk).

Consumes a `broken_audio.csv` produced by `QC/validation/validate_audio.py`
and removes each listed `<AUDIO>` element from its containing XML file.
When the CSV includes `element_id`, `start`, and `end` locator columns,
the removal is scoped to that exact reference; legacy CSVs with only
`xml_file`, `audio_file`, and `kind` still fall back to filename matching.
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


def _row_label(row: dict) -> str:
    bits = [row.get("audio_file", "")]
    if row.get("element_id"):
        bits.append(f"id={row['element_id']}")
    if row.get("start") or row.get("end"):
        bits.append(f"{row.get('start', '')}-{row.get('end', '')}")
    return " ".join(bit for bit in bits if bit)


def _candidate_parents(root: etree._Element, row: dict) -> list[etree._Element]:
    element_id = row.get("element_id", "")
    if not element_id:
        return [root]
    if element_id == "TEXT":
        return [root]
    matches = [elem for elem in root.iter() if elem.get("id") == element_id]
    return matches


def _matches_audio_row(audio_elem: etree._Element, row: dict, root_audio: str | None) -> bool:
    audio_file = row.get("audio_file", "")
    if not audio_file:
        return False

    elem_file = audio_elem.get("file")
    if elem_file:
        if elem_file != audio_file:
            return False
    elif root_audio != audio_file:
        return False

    for attr in ("start", "end"):
        expected = row.get(attr, "")
        if expected and audio_elem.get(attr, "") != expected:
            return False

    return True


def remove_audio_elements(
    xml_path: Path,
    rows: list[dict],
) -> tuple[int, list[str]]:
    """Remove the listed `<AUDIO>` elements from an XML file.

    New `broken_audio.csv` rows carry element/range locators so duplicate
    references to the same filename are not all removed by accident. Older
    rows without locator columns intentionally preserve the historical
    filename-only behavior.

    Returns (n_removed, missing_targets) — missing_targets is the
    rows that were not found in the file (so the operator
    can investigate, rather than silently ignored).
    """
    tree = etree.parse(str(xml_path))
    root = tree.getroot()
    root_audio = root.get("audio")
    missing: list[str] = []
    n_removed = 0

    for row in rows:
        candidates: list[etree._Element] = []
        for parent in _candidate_parents(root, row):
            audio_iter = (
                parent.findall("AUDIO")
                if row.get("element_id") == "TEXT"
                else parent.iter("AUDIO")
            )
            candidates.extend(
                a for a in audio_iter
                if _matches_audio_row(a, row, root_audio)
            )

        if not candidates:
            missing.append(_row_label(row))
            continue

        for elem in candidates:
            parent = elem.getparent()
            if parent is not None:
                parent.remove(elem)
                n_removed += 1

    tree.write(str(xml_path), encoding="utf-8", xml_declaration=True)
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
        for row, kind in zip(xml_rows, kinds):
            tag = f" [{kind}]" if kind else ""
            print(f"    - {_row_label(row)}{tag}")

        if not args.apply:
            continue

        if not xml_path.is_file():
            print(f"    WARNING: XML file not found, skipping: {xml_path}", file=sys.stderr)
            continue

        n_removed, missing = remove_audio_elements(xml_path, xml_rows)
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

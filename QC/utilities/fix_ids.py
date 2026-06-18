"""fix_ids.py — renumber duplicate/gappy M ids by position within each W.

For every <W> in each target file, this rewrites the id of each <M>
child to <W.id>M<n> where n is the 1-based position of the <M> in
document order under that <W>. Useful for fixing V039 duplicate M-id
collisions (where the source pipeline reused an M id for two distinct
morphemes that happen to share a surface form) and gaps (M1, M2, M4
where M3 was elided).

Scope: M ids only. W and S ids are left alone. (If S/W collisions
appear in practice, broaden later — the algorithm transposes trivially
to either type.)

CLI mirrors validate_xml.py:
    fix_ids.py by_path     --path <file-or-dir>
    fix_ids.py by_corpus   --corpus <name> --corpora_path <path>
    fix_ids.py by_language --language <name> --corpora_path <path>

--dry-run: print the (file, old_id -> new_id) changes that WOULD be
made, without touching disk. Default is to write changes back in place.

--verbose: list every individual id change. Default summarizes per-file
change counts only.

Reuses validate_xml.py's discover_* helpers so corpus/language targeting
matches the validator's: canonical XML lives under <corpus>/XML/, working
files under CodeAndDocs/ are excluded.
"""
import argparse
import sys
from pathlib import Path

# Mirror validate_xml.py's repo-root-on-sys.path bootstrap so the
# `QC.*` package imports work whether this file is run as a script or
# imported as a module.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lxml import etree

from QC.validation.validate_xml import _resolve_target_files, parse_tree


def compute_m_id_changes(
    tree: etree._ElementTree,
) -> list[tuple[etree._Element, str, str]]:
    """Return (M_element, old_id, new_id) tuples for every M whose id
    would change under the renumber-by-position policy.

    For each W, the n-th M child (1-based, document order) is assigned
    new_id = f"{W.id}M{n}". An M whose current id already matches the
    computed new_id is NOT included. W elements without an id are
    skipped (the validator catches that case under V038-equivalent).
    """
    changes: list[tuple[etree._Element, str, str]] = []
    for w in tree.iter("W"):
        wid = w.get("id")
        if not wid:
            continue
        for n, m in enumerate(w.findall("M"), start=1):
            new_id = f"{wid}M{n}"
            old_id = m.get("id")
            if old_id != new_id:
                changes.append((m, old_id, new_id))
    return changes


def apply_m_id_changes(
    changes: list[tuple[etree._Element, str, str]],
) -> None:
    """Set each M element's id to its computed new value, in place."""
    for m, _old_id, new_id in changes:
        m.set("id", new_id)


def fix_file(
    path: Path, dry_run: bool, verbose: bool
) -> int:
    """Process one file. Return the number of id changes applied (or
    that would be applied under --dry-run).

    Files that fail to parse are reported to stderr and skipped (return
    0). Writing back is skipped entirely when there are zero changes,
    so untouched files are not rewritten (and not gratuitously
    reformatted by lxml).
    """
    try:
        tree = parse_tree(path)
    except etree.XMLSyntaxError as e:
        print(f"{path}: XML parse error — skipped: {e}", file=sys.stderr)
        return 0

    changes = compute_m_id_changes(tree)
    n = len(changes)
    if n == 0:
        return 0

    prefix = "[dry-run] " if dry_run else ""
    print(f"{prefix}{path}: {n} M id(s) renumbered")
    if verbose:
        for _m, old_id, new_id in changes:
            print(f"  {prefix}{old_id!r} -> {new_id!r}")

    if not dry_run:
        apply_m_id_changes(changes)
        # No pretty_print: preserve existing whitespace/indentation as
        # parsed. xml_declaration=True keeps the leading
        # <?xml version="1.0" encoding="utf-8"?> line.
        tree.write(
            str(path), xml_declaration=True, encoding="utf-8"
        )
    return n


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Renumber duplicate/gappy <M> ids within each <W>. "
            "Writes changes in place unless --dry-run is given."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned changes without modifying files.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="List each individual id change in addition to per-file counts.",
    )

    sub = parser.add_subparsers(dest="search_by", required=True)

    by_path = sub.add_parser("by_path")
    by_path.add_argument("--path", required=True, type=Path)

    by_corpus = sub.add_parser("by_corpus")
    by_corpus.add_argument("--corpus", required=True)
    by_corpus.add_argument("--corpora_path", required=True, type=Path)

    by_language = sub.add_parser("by_language")
    by_language.add_argument("--language", required=True)
    by_language.add_argument("--corpora_path", required=True, type=Path)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    targets = _resolve_target_files(args)
    if not targets:
        print("No XML files matched.", file=sys.stderr)
        return 0

    total_files_changed = 0
    total_changes = 0
    for path in targets:
        n = fix_file(path, dry_run=args.dry_run, verbose=args.verbose)
        if n:
            total_files_changed += 1
            total_changes += n

    prefix = "[dry-run] " if args.dry_run else ""
    print(
        f"{prefix}{total_changes} M id(s) renumbered across "
        f"{total_files_changed} file(s) ({len(targets)} scanned).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

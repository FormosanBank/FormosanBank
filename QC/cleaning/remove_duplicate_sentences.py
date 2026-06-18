#!/usr/bin/env python3
"""
remove_duplicate_sentences.py - Delete duplicate <S> elements from XML files.

IMPORTANT: This script modifies XML in place when --apply is passed.  Per repo
convention (CLAUDE.md: "clean_xml.py modify XML in place — diff before
committing"), always run with the default --dry-run first, inspect the planned
removals, then re-run with --apply only when satisfied.

Companion to QC/validation/validate_duplicate_sentences.py - uses the same
equivalence (whitespace-normalized, --tier-selected FORM text).

Determinism rule (B9.5 plan, OQ4):
  Within each duplicate group, keep the first occurrence by (file, S id) sort
  order; remove the rest.  This produces stable, reproducible results
  regardless of file walk order.

Scope (B9.5 plan, OQ3):
  --scope file (default):  only within-file duplicates are removed (HARD).
  --scope corpus:          within-corpus cross-file duplicates also removed.

Usage:

  # Plan what would be removed; nothing is written.
  python remove_duplicate_sentences.py by_path --path Corpora/ePark/XML

  # Apply changes after reviewing the dry-run output.
  python remove_duplicate_sentences.py by_path --path Corpora/ePark/XML --apply

  # Restrict to file-scope (default) or include cross-file dupes in the corpus
  python remove_duplicate_sentences.py by_path --path Corpora/ePark/XML \
      --scope corpus --apply
"""

import argparse
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

from lxml import etree

# Reuse the validator's normalize + extract logic so equivalence stays in sync.
_THIS = Path(__file__).resolve()
sys.path.insert(0, str(_THIS.parents[1] / "validation"))
from validate_duplicate_sentences import normalize_for_comparison  # noqa: E402


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------

def _extract_sentences_lxml(xml_path: str, kind_of: str):
    """Return [(s_id, normalized_text), ...].  Uses lxml so apply() can reuse
    the same parse without round-tripping."""
    out = []
    try:
        root = etree.parse(xml_path).getroot()
    except etree.XMLSyntaxError as e:
        print(f"  WARNING: could not parse {xml_path}: {e}", file=sys.stderr)
        return out
    for s in root.iter("S"):
        sid = s.get("id", "")
        for child in s:
            if child.tag == "FORM" and child.get("kindOf") == kind_of:
                norm = normalize_for_comparison(child.text or "")
                if norm:
                    out.append((sid, norm))
                break
    return out


def _collect_xml_files(root_path: str):
    p = Path(root_path)
    if p.is_file() and p.suffix.lower() == ".xml":
        return [p]
    if not p.is_dir():
        return []
    return sorted(p.rglob("*.xml"))


def plan_removals(root_path: str, scope: str = "file",
                  tier: str = "standard"):
    """Return a deterministic list of (abs_file_path, s_id) tuples to remove.

    Within each duplicate group, the first occurrence by (file, s_id) sort
    order is kept; later occurrences are scheduled for removal.

    scope="file":   only consider duplicates inside the same file.
    scope="corpus": consider duplicates across every file under root_path.
    """
    if scope not in ("file", "corpus"):
        raise ValueError(f"scope must be 'file' or 'corpus', got {scope!r}")

    xml_files = _collect_xml_files(root_path)

    removals: list[tuple[str, str]] = []

    if scope == "file":
        for xml_path in xml_files:
            by_text: dict[str, list[str]] = defaultdict(list)
            for sid, norm in _extract_sentences_lxml(str(xml_path), tier):
                by_text[norm].append(sid)
            for norm, sids in by_text.items():
                if len(sids) < 2:
                    continue
                sorted_sids = sorted(sids, key=_s_id_sort_key)
                # Keep first, remove rest.
                for sid in sorted_sids[1:]:
                    removals.append((str(xml_path.resolve()), sid))
    else:
        # corpus scope: build (norm_text -> [(file, sid), ...]) over all files.
        by_text: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for xml_path in xml_files:
            abs_path = str(xml_path.resolve())
            for sid, norm in _extract_sentences_lxml(str(xml_path), tier):
                by_text[norm].append((abs_path, sid))
        for norm, occs in by_text.items():
            if len(occs) < 2:
                continue
            sorted_occs = sorted(occs, key=lambda fs: (fs[0], _s_id_sort_key(fs[1])))
            # Keep first; schedule the rest for removal.
            for f, sid in sorted_occs[1:]:
                removals.append((f, sid))

    # Stable global order: by file path, then by s_id sort key.
    removals.sort(key=lambda fs: (fs[0], _s_id_sort_key(fs[1])))
    return removals


def _s_id_sort_key(sid: str):
    """Sort 'S_2' before 'S_10' by parsing the trailing integer if present."""
    m = re.match(r"^(.*?)(\d+)$", sid)
    if m:
        prefix, n = m.group(1), int(m.group(2))
        return (prefix, n)
    return (sid, 0)


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------

def apply_removals(removals):
    """Mutate XML files in place: delete each (file, s_id) in `removals`.

    Files are grouped so each XML is parsed and written exactly once.
    """
    by_file: dict[str, set[str]] = defaultdict(set)
    for f, sid in removals:
        by_file[f].add(sid)
    for f, sids_to_drop in by_file.items():
        try:
            tree = etree.parse(f)
        except etree.XMLSyntaxError as e:
            print(f"  WARNING: could not parse {f}: {e}", file=sys.stderr)
            continue
        root = tree.getroot()
        # Walk a list-copy because we mutate during iteration.
        for s in list(root.iter("S")):
            if s.get("id") in sids_to_drop:
                parent = s.getparent()
                if parent is not None:
                    parent.remove(s)
        tree.write(f, pretty_print=False, encoding="utf-8",
                   xml_declaration=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _resolve_scan_root(args, parser) -> str:
    if args.search_by == "by_path":
        if not args.path:
            parser.error("For 'by_path', --path is required.")
        return args.path
    if args.search_by == "by_corpus":
        if not args.corpora_path or not args.corpus:
            parser.error("For 'by_corpus', --corpora_path and --corpus are required.")
        return os.path.join(args.corpora_path, args.corpus)
    # by_language
    if not args.corpora_path:
        parser.error("For 'by_language', --corpora_path is required.")
    if not args.language:
        parser.error("For 'by_language', --language is required.")
    return args.corpora_path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Remove duplicate <S> elements from XML files. "
                    "Defaults to --dry-run; pass --apply to mutate files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("search_by",
                        choices=["by_path", "by_corpus", "by_language"],
                        help="Search mode.")
    parser.add_argument("--path", help="Path to XML file or directory (by_path).")
    parser.add_argument("--corpora_path",
                        help="Path to corpora directory (by_corpus / by_language).")
    parser.add_argument("--corpus", help="Corpus name (by_corpus).")
    parser.add_argument("--language", help="Language name (by_language).")
    parser.add_argument("--scope", choices=["file", "corpus"], default="file",
                        help="Duplicate scope (default: file).  'file' removes only "
                             "within-file duplicates (HARD); 'corpus' also removes "
                             "cross-file duplicates within the corpus root.")
    parser.add_argument("--tier", default="standard",
                        choices=["standard", "original"],
                        help='Value of FORM @kindOf to compare (default: standard).')
    parser.add_argument("--apply", action="store_true",
                        help="Actually modify files.  Default behavior is "
                             "--dry-run (print plan only).")

    args = parser.parse_args(argv)
    scan_root = _resolve_scan_root(args, parser)

    if args.search_by == "by_language":
        corpora_root = Path(scan_root).resolve()
        plan = []
        for corpus_dir in sorted(corpora_root.iterdir()):
            if not corpus_dir.is_dir():
                continue
            xml_dir = corpus_dir / "XML" / args.language
            if not xml_dir.is_dir():
                continue
            plan.extend(plan_removals(str(xml_dir), scope=args.scope, tier=args.tier))
    else:
        plan = plan_removals(scan_root, scope=args.scope, tier=args.tier)

    if not plan:
        print("No duplicate <S> elements found to remove.")
        return 0

    if not args.apply:
        print(f"[dry-run] Would remove {len(plan)} duplicate <S> element(s):")
        for f, sid in plan:
            print(f"  - {f}#{sid}")
        print("[dry-run] Re-run with --apply to actually modify files.")
        return 0

    print(f"Removing {len(plan)} duplicate <S> element(s)...")
    apply_removals(plan)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

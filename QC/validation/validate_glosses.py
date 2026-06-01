#!/usr/bin/env python3
"""validate_glosses.py — gloss-tier validator.

Stage-2 validator in the FormosanBank validation pipeline. Walks the
selected target (file, directory, corpus, or language), parses each
.xml with lxml, applies the rules registered under
QC/validation/rules/gloss.py, and emits:

- HARD/SOFT findings printed to stderr.
- Two legacy CSV artifacts for backward compatibility with prior callers:
  - validation_results.csv (W-count mismatches, from V060)
  - validation_m_mismatches.csv (M-count mismatches, from V061)
- Exit code 1 if any HARD findings; 0 otherwise.

CLI (matches the validate_xml.py / validate_text.py subparser pattern
as of 2026-06-01):
    validate_glosses.py by_path     --path <file-or-dir> [opts]
    validate_glosses.py by_corpus   --corpus <name> --corpora_path <path> [opts]
    validate_glosses.py by_language --language <code> --corpora_path <path> [opts]

Common opts: --check_morpho, --debug, --output_dir DIR.

The --check_morpho flag adds a legacy "has_morphemes" column to
validation_results.csv (T if every W has at least one M child, F
otherwise). It does not alter rule severity — V060 is still SOFT.
"""
import argparse
import csv
import re
import sys
from pathlib import Path

# When invoked as `python QC/validation/validate_glosses.py ...`, the
# repo root is not on sys.path. Add it so the QC.* package imports
# resolve correctly whether the file is run as a script or imported as
# a module.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lxml import etree

from QC.validation._finding import Finding, Severity
from QC.validation.rules import gloss as gloss_rules
from QC.validation.validate_xml import (
    discover_all_corpora_canonical_xml,
    discover_corpus_canonical_xml,
    discover_xml_files,
)


_XML_LANG_ATTR = "{http://www.w3.org/XML/1998/namespace}lang"


def _parse_w_mismatch_message(message: str) -> tuple[str, str] | None:
    """Pull (word_count, w_count) out of a V060 Finding message.

    Avoids re-walking the tree just to populate the legacy CSV. V060's
    message is the source of truth for the per-S counts.

    Returns (word_count, w_count) as strings, or None on parse failure
    (defensive — should not happen given the rule's stable format).
    """
    # Message format: "S id='...': W-count (N) does not match word-count (M) in ..."
    m = re.search(r"W-count \((\d+)\) does not match word-count \((\d+)\)", message)
    if not m:
        return None
    return (m.group(2), m.group(1))  # (word_count, w_count)


def _parse_m_mismatch_message(message: str) -> tuple[str, str, str] | None:
    """Pull (w_form, expected_m, actual_m) out of a V061 Finding message."""
    # Message format: "W id='...': M-count (A) does not match implied morpheme count (E) from FORM 'X'"
    m = re.search(
        r"M-count \((\d+)\) does not match implied morpheme count \((\d+)\) from FORM '(.*)'$",
        message,
    )
    if not m:
        return None
    return (m.group(3), m.group(2), m.group(1))  # (w_form, expected, actual)


def _extract_s_id_from_location(location: str | None) -> str:
    """Extract the S id from a finding's location field.

    V060's location is 'S=<id>'. V061's is 'S=<sid> W=<wid>' when both
    are known, or just 'W=<wid>'. Returns '' if no S id is present.
    """
    if not location:
        return ""
    m = re.search(r"S=([^\s]+)", location)
    return m.group(1) if m else ""


def _extract_w_id_from_location(location: str | None) -> str:
    """Extract the W id from a V061 finding's location field."""
    if not location:
        return ""
    m = re.search(r"W=([^\s]+)", location)
    return m.group(1) if m else ""


def _w_has_no_M(w: etree._Element) -> bool:
    """Return True if W has no M children. Used by --check_morpho."""
    return not any(child.tag == "M" for child in w)


def _build_check_morpho_index(tree: etree._ElementTree) -> dict[str, bool]:
    """Map S id -> True iff every W in S has at least one M child.

    Mirrors the pre-refactor has_morphemes='T'/'F' logic; the column
    value is 'T' when this returns True and 'F' otherwise. Used by the
    legacy CSV writer when --check_morpho is on.
    """
    out: dict[str, bool] = {}
    for s in tree.iter("S"):
        s_id = s.get("id") or ""
        if not s_id:
            continue
        any_w_without_m = any(_w_has_no_M(w) for w in s if w.tag == "W")
        out[s_id] = not any_w_without_m
    return out


def _process_file(
    xml_file: Path,
    check_morpho: bool,
    debug: bool,
) -> tuple[list[Finding], list[tuple], list[tuple]]:
    """Process one XML file. Returns (findings, w_rows, m_rows).

    w_rows: legacy validation_results.csv rows (filename, s_id, word_count,
            w_count [, has_morphemes when check_morpho]).
    m_rows: legacy validation_m_mismatches.csv rows
            (filename, s_id, w_id, w_form, expected_m_count, actual_m_count).
    """
    findings: list[Finding] = []
    w_rows: list[tuple] = []
    m_rows: list[tuple] = []

    try:
        tree = etree.parse(str(xml_file))
    except etree.XMLSyntaxError as e:
        print(f"Warning: Could not parse {xml_file}: {e}")
        return findings, w_rows, m_rows

    # Run every rule registered for gloss validation.
    for rule in gloss_rules.RULES:
        findings.extend(rule(tree, xml_file, None))

    # Pre-compute --check_morpho index (S -> all-W-have-M flag) so we
    # can both update w_rows and emit extra rows for "W with no M" S
    # elements that V060 does NOT flag (legacy behavior).
    if check_morpho:
        check_morpho_idx = _build_check_morpho_index(tree)
    else:
        check_morpho_idx = {}

    # Derive legacy CSV rows from the findings.
    s_ids_seen_in_w_rows: set[str] = set()
    for finding in findings:
        if finding.rule_id == "V060":
            parsed = _parse_w_mismatch_message(finding.message)
            if parsed is None:
                continue
            word_count, w_count = parsed
            s_id = _extract_s_id_from_location(finding.location)
            row_tuple = (str(xml_file), s_id, word_count, w_count)
            if check_morpho:
                hm = "T" if check_morpho_idx.get(s_id, True) else "F"
                w_rows.append((*row_tuple, hm))
            else:
                w_rows.append(row_tuple)
            s_ids_seen_in_w_rows.add(s_id)
        elif finding.rule_id == "V061":
            parsed = _parse_m_mismatch_message(finding.message)
            if parsed is None:
                continue
            w_form, expected, actual = parsed
            s_id = _extract_s_id_from_location(finding.location)
            w_id = _extract_w_id_from_location(finding.location)
            m_rows.append(
                (str(xml_file), s_id, w_id, w_form, expected, actual)
            )

    # Legacy --check_morpho path: also row-out S elements where V060 didn't
    # fire but at least one W lacks M children (has_morphemes='F').
    if check_morpho:
        for s_id, all_have_m in check_morpho_idx.items():
            if s_id in s_ids_seen_in_w_rows:
                continue
            if all_have_m:
                continue
            # Reconstruct word_count and w_count for the row.
            s_elem = tree.find(f".//S[@id='{s_id}']")
            if s_elem is None:
                continue
            text = gloss_rules._extract_s_direct_text(s_elem)
            word_count = gloss_rules._count_words(text)
            w_count = sum(1 for child in s_elem if child.tag == "W")
            w_rows.append((str(xml_file), s_id, str(word_count), str(w_count), "F"))

    if debug:
        for finding in findings:
            print(f"  [{finding.rule_id}] {finding.location}: {finding.message}")

    return findings, w_rows, m_rows


def _write_w_csv(path: Path, rows: list[tuple], check_morpho: bool) -> None:
    """Write validation_results.csv. Header always written; rows may be empty."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if check_morpho:
            writer.writerow(
                ["filename", "s_id", "word_count", "w_element_count", "has_morphemes"]
            )
        else:
            writer.writerow(["filename", "s_id", "word_count", "w_element_count"])
        writer.writerows(rows)


def _write_m_csv(path: Path, rows: list[tuple]) -> None:
    """Write validation_m_mismatches.csv. Header always written; rows may be empty."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "filename",
                "s_id",
                "w_id",
                "w_form",
                "expected_m_count",
                "actual_m_count",
            ]
        )
        writer.writerows(rows)


def _print_summary(findings: list[Finding]) -> None:
    """Print HARD/SOFT findings to stderr (per validate_xml.py convention)."""
    hard = [f for f in findings if f.severity is Severity.HARD]
    soft = [f for f in findings if f.severity is Severity.SOFT]
    print(f"\nHARD findings: {len(hard)}", file=sys.stderr)
    for f in hard:
        loc = f" [{f.location}]" if f.location else ""
        print(f"  [{f.rule_id}]{loc} {f.message}", file=sys.stderr)
    print(f"SOFT findings: {len(soft)}", file=sys.stderr)
    for f in soft:
        loc = f" [{f.location}]" if f.location else ""
        print(f"  [{f.rule_id}]{loc} {f.message}", file=sys.stderr)


def _add_common_flags(p: argparse.ArgumentParser, *, suppress: bool) -> None:
    """Register --check_morpho/--debug/--output_dir on a parser.

    suppress=True is used for subparsers (so the parent parser's value
    sticks when the user passes the flag BEFORE the subcommand). Same
    pattern as validate_xml.py's _add_common_flags_to_subparser.
    """
    default = argparse.SUPPRESS if suppress else False
    p.add_argument(
        "--check_morpho",
        action="store_true",
        default=default,
        help="Check if each W element has at least one M element (legacy "
             "column in validation_results.csv).",
    )
    p.add_argument(
        "--debug",
        action="store_true",
        default=default,
        help="Print one debug line per finding to stdout.",
    )
    p.add_argument(
        "--output_dir",
        default=argparse.SUPPRESS if suppress else None,
        help="Directory for validation CSV outputs. Defaults to the current "
             "working directory.",
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="FormosanBank gloss validator.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_glosses.py by_path     --path tests/fixtures/foo.xml
  python validate_glosses.py by_path     --path Corpora/ePark/XML --check_morpho
  python validate_glosses.py by_corpus   --corpus ePark --corpora_path Corpora
  python validate_glosses.py by_language --language ami  --corpora_path Corpora
        """,
    )
    _add_common_flags(parser, suppress=False)

    sub = parser.add_subparsers(dest="search_by", required=True)

    by_path = sub.add_parser("by_path", help="Validate a single XML file or a directory")
    by_path.add_argument("--path", required=True, type=Path)
    _add_common_flags(by_path, suppress=True)

    by_corpus = sub.add_parser("by_corpus", help="Validate one corpus's canonical XML/")
    by_corpus.add_argument("--corpus", required=True)
    by_corpus.add_argument("--corpora_path", required=True, type=Path)
    _add_common_flags(by_corpus, suppress=True)

    by_language = sub.add_parser("by_language", help="Validate every file in Corpora with matching xml:lang")
    by_language.add_argument("--language", required=True)
    by_language.add_argument("--corpora_path", required=True, type=Path)
    _add_common_flags(by_language, suppress=True)

    return parser


def _resolve_target_files(args: argparse.Namespace) -> list[Path]:
    if args.search_by == "by_path":
        return discover_xml_files(args.path)
    if args.search_by == "by_corpus":
        return discover_corpus_canonical_xml(args.corpora_path / args.corpus)
    if args.search_by == "by_language":
        files: list[Path] = []
        for path in discover_all_corpora_canonical_xml(args.corpora_path):
            try:
                tree = etree.parse(str(path))
            except etree.XMLSyntaxError:
                continue
            if tree.getroot().get(_XML_LANG_ATTR) == args.language:
                files.append(path)
        return files
    raise AssertionError(f"unknown search_by mode: {args.search_by}")


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)

    output_dir = Path(args.output_dir) if args.output_dir else Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)
    w_csv_file = output_dir / "validation_results.csv"
    m_csv_file = output_dir / "validation_m_mismatches.csv"

    print(f"Mode: {args.search_by}")
    print(f"Check morphemes (W missing M): {args.check_morpho}")
    print(f"W-mismatch output: {w_csv_file}")
    print(f"M-mismatch output: {m_csv_file}")
    print()

    xml_files = _resolve_target_files(args)
    if not xml_files:
        print("No XML files matched the selection.")
        # Still write the empty CSVs so downstream consumers see header-only files.
        _write_w_csv(w_csv_file, [], args.check_morpho)
        _write_m_csv(m_csv_file, [])
        return 0

    all_findings: list[Finding] = []
    all_w_rows: list[tuple] = []
    all_m_rows: list[tuple] = []

    for xml_file in xml_files:
        print(f"Processing: {xml_file}")
        findings, w_rows, m_rows = _process_file(
            xml_file, args.check_morpho, args.debug
        )
        if w_rows:
            print(f"  Found {len(w_rows)} W-count mismatch(es)")
        if m_rows:
            print(f"  Found {len(m_rows)} M-count mismatch(es)")
        all_findings.extend(findings)
        all_w_rows.extend(w_rows)
        all_m_rows.extend(m_rows)

    _write_w_csv(w_csv_file, all_w_rows, args.check_morpho)
    _write_m_csv(m_csv_file, all_m_rows)

    if all_w_rows:
        print(
            f"\nW-mismatch results saved to: {w_csv_file} "
            f"({len(all_w_rows)} error(s))"
        )
    else:
        print("\nNo W-count mismatches found.")

    if all_m_rows:
        print(
            f"M-mismatch results saved to: {m_csv_file} "
            f"({len(all_m_rows)} error(s))"
        )
    else:
        print("No M-count mismatches found.")

    print(f"\nValidation complete! Files processed: {len(xml_files)}")
    _print_summary(all_findings)

    has_hard = any(f.severity is Severity.HARD for f in all_findings)
    return 1 if has_hard else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""validate_glosses.py — gloss-tier validator.

Stage-2 validator in the FormosanBank validation pipeline. Walks the
selected target (file, directory, corpus, or language), parses each
.xml with lxml, applies the rules registered under
QC/validation/rules/gloss.py, and reports via the shared reporter
(QC/validation/_report.py):

- A compact per-rule count summary (HARD then SOFT) on the terminal.
- One findings CSV (all severities) carrying full per-finding context,
  whose path is printed. Detail no longer floods the terminal.
- Exit code 1 if any HARD findings; 0 otherwise (override with
  --no-exit-on-hard).

CLI (matches the validate_xml.py / validate_text.py subparser pattern):
    validate_glosses.py by_path     --path <file-or-dir> [opts]
    validate_glosses.py by_corpus   --corpus <name> --corpora_path <path> [opts]
    validate_glosses.py by_language --language <code> --corpora_path <path> [opts]

Common opts: --csv PATH (where the one findings CSV is written),
--output_dir DIR (directory for the findings CSV when --csv is not given;
retained for the run-qc-pipeline skill and CI), --debug, --no-exit-on-hard.

The findings CSV writes the finding's `location` (e.g. "S=<sid> W=<wid>")
verbatim, so sentence/word ids that contain spaces (NTU filenames do) are
preserved intact — superseding the old validation_results.csv /
validation_m_mismatches.csv, which re-parsed `location` and truncated such
ids at the first space.
"""
import argparse
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

from QC.validation._finding import Finding
from QC.validation._report import report_findings
from QC.validation.rules import gloss as gloss_rules
from QC.validation.validate_xml import (
    discover_all_corpora_canonical_xml,
    discover_corpus_canonical_xml,
    discover_xml_files,
)


_XML_LANG_ATTR = "{http://www.w3.org/XML/1998/namespace}lang"


def _process_file(xml_file: Path, debug: bool) -> list[Finding]:
    """Run every gloss rule against one XML file; return its findings."""
    try:
        tree = etree.parse(str(xml_file))
    except etree.XMLSyntaxError as e:
        print(f"Warning: Could not parse {xml_file}: {e}", file=sys.stderr)
        return []

    findings: list[Finding] = []
    for rule in gloss_rules.RULES:
        findings.extend(rule(tree, xml_file, None))

    if debug:
        for finding in findings:
            print(f"  [{finding.rule_id}] {finding.location}: {finding.message}")

    return findings


def _add_common_flags(p: argparse.ArgumentParser, *, suppress: bool) -> None:
    """Register --csv/--output_dir/--debug/--no-exit-on-hard on a parser.

    suppress=True is used for subparsers (so the parent parser's value
    sticks when the user passes the flag BEFORE the subcommand). Same
    pattern as validate_xml.py's _add_common_flags_to_subparser.
    """
    default = argparse.SUPPRESS if suppress else None
    p.add_argument(
        "--csv",
        dest="csv",
        type=Path,
        default=argparse.SUPPRESS if suppress else None,
        help="Path where ALL findings are written as one CSV. Defaults to "
             "<output_dir>/validate_glosses_findings.csv.",
    )
    p.add_argument(
        "--output_dir",
        default=default,
        help="Directory for the findings CSV when --csv is not given. "
             "Defaults to the current working directory's logs/.",
    )
    p.add_argument(
        "--debug",
        action="store_true",
        default=argparse.SUPPRESS if suppress else False,
        help="Print one debug line per finding to stdout.",
    )
    p.add_argument(
        "--no-exit-on-hard",
        action="store_true",
        default=argparse.SUPPRESS if suppress else False,
        help="Always exit 0, even if HARD findings are produced.",
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="FormosanBank gloss validator.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_glosses.py by_path     --path tests/fixtures/foo.xml
  python validate_glosses.py by_path     --path Corpora/ePark/XML
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
        files = discover_xml_files(args.path)
    elif args.search_by == "by_corpus":
        files = discover_corpus_canonical_xml(args.corpora_path / args.corpus)
    elif args.search_by == "by_language":
        files = []
        for path in discover_all_corpora_canonical_xml(args.corpora_path):
            try:
                tree = etree.parse(str(path))
            except etree.XMLSyntaxError:
                continue
            if tree.getroot().get(_XML_LANG_ATTR) == args.language:
                files.append(path)
    else:
        raise AssertionError(f"unknown search_by mode: {args.search_by}")
    # Defensive: only ever validate .xml files (a directory walk could in
    # principle surface a README or other non-XML; the discovery helpers
    # already filter, this guarantees it).
    return [f for f in files if f.suffix == ".xml"]


def _resolve_csv_path(args: argparse.Namespace) -> Path:
    if getattr(args, "csv", None):
        return args.csv
    base = Path(args.output_dir) if getattr(args, "output_dir", None) else Path("logs")
    return base / "validate_glosses_findings.csv"


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)

    csv_path = _resolve_csv_path(args)
    xml_files = _resolve_target_files(args)
    if not xml_files:
        print("No XML files matched the selection.")
        return 0

    all_findings: list[Finding] = []
    for xml_file in xml_files:
        all_findings.extend(_process_file(xml_file, getattr(args, "debug", False)))

    has_hard = report_findings(all_findings, csv_path, file_count=len(xml_files))
    if has_hard and not getattr(args, "no_exit_on_hard", False):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

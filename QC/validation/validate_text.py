"""validate_text.py — text-content validator for FormosanBank XML.

Stage 2 validator in the staged pipeline (per B9.3 architecture). Runs
the rules under QC/validation/rules/text.py against well-formed XML.
Replaces the legacy `validate_punct.py` and `non_ascii_counts.py`
single-purpose scripts.

CLI shape (mirrors validate_xml.py):
    validate_text.py by_path     --path <file-or-dir>
    validate_text.py by_corpus   --corpus <name> --corpora_path <path>
    validate_text.py by_language --language <name> --corpora_path <path>

Common flags (--soft-csv, --no-exit-on-hard, --verbose, --log_dir) may
appear either before or after the subcommand on the command line.

Exit code: 1 if any HARD findings; 0 otherwise. Override with
`--no-exit-on-hard`.
"""
import argparse
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

# Make the QC package importable when invoked as a script.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lxml import etree

from QC.validation._corpus_index import CorpusIndex
from QC.validation._finding import Finding, Severity, write_soft_csv
from QC.validation.rules import text as text_rules


_DEFAULT_CORPORA_ROOT = Path(__file__).resolve().parents[2] / "Corpora"


Rule = Callable[[etree._ElementTree, Path, CorpusIndex | None], list[Finding]]


def discover_xml_files(root: Path) -> list[Path]:
    """Return every .xml file under root, recursively."""
    if root.is_file():
        return [root] if root.suffix == ".xml" else []
    return sorted(p for p in root.rglob("*.xml"))


def discover_corpus_canonical_xml(corpus_root: Path) -> list[Path]:
    """Return canonical XML files (under <corpus_root>/XML/) for a corpus.

    Falls back to a full recursive walk if XML/ doesn't exist, matching
    the validate_xml.py convention.
    """
    xml_subdir = corpus_root / "XML"
    if xml_subdir.is_dir():
        return sorted(p for p in xml_subdir.rglob("*.xml"))
    return discover_xml_files(corpus_root)


def discover_all_corpora_canonical_xml(corpora_root: Path) -> list[Path]:
    if not corpora_root.is_dir():
        return []
    files: list[Path] = []
    for child in sorted(corpora_root.iterdir()):
        if child.is_dir():
            files.extend(discover_corpus_canonical_xml(child))
    return files


def parse_tree(path: Path) -> etree._ElementTree:
    return etree.parse(str(path))


def run_per_file_rules(
    tree: etree._ElementTree,
    path: Path,
    rules: Iterable[Rule],
    index: CorpusIndex | None,
) -> list[Finding]:
    out: list[Finding] = []
    for rule in rules:
        out.extend(rule(tree, path, index))
    return out


def _add_common_flags_to_subparser(p: argparse.ArgumentParser) -> None:
    p.add_argument("--verbose", action="store_true", default=argparse.SUPPRESS)
    p.add_argument("--log_dir", type=Path, default=argparse.SUPPRESS)
    p.add_argument(
        "--no-exit-on-hard",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Always exit 0, even if HARD findings are produced.",
    )
    p.add_argument(
        "--soft-csv",
        dest="soft_csv",
        type=Path,
        default=argparse.SUPPRESS,
        help="Path where SOFT findings are written as CSV.",
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FormosanBank text-content validator.")
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument("--log_dir", type=Path, default=None)
    parser.add_argument(
        "--no-exit-on-hard",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--soft-csv",
        dest="soft_csv",
        type=Path,
        default=Path("logs") / "validation_text_soft.csv",
    )

    sub = parser.add_subparsers(dest="search_by", required=True)

    by_path = sub.add_parser("by_path")
    by_path.add_argument("--path", required=True, type=Path)
    _add_common_flags_to_subparser(by_path)

    by_corpus = sub.add_parser("by_corpus")
    by_corpus.add_argument("--corpus", required=True)
    by_corpus.add_argument("--corpora_path", required=True, type=Path)
    _add_common_flags_to_subparser(by_corpus)

    by_language = sub.add_parser("by_language")
    by_language.add_argument("--language", required=True)
    by_language.add_argument("--corpora_path", required=True, type=Path)
    _add_common_flags_to_subparser(by_language)

    return parser


def _resolve_target_files(args: argparse.Namespace) -> list[Path]:
    if args.search_by == "by_path":
        return discover_xml_files(args.path)
    if args.search_by == "by_corpus":
        return discover_corpus_canonical_xml(args.corpora_path / args.corpus)
    if args.search_by == "by_language":
        files = []
        for path in discover_all_corpora_canonical_xml(args.corpora_path):
            try:
                tree = parse_tree(path)
                lang_attr = "{http://www.w3.org/XML/1998/namespace}lang"
                if tree.getroot().get(lang_attr) == args.language:
                    files.append(path)
            except etree.XMLSyntaxError:
                continue
        return files
    raise AssertionError(f"unknown search_by mode: {args.search_by}")


def _print_summary(findings: list[Finding]) -> None:
    """Emit per-rule findings + summary. Format mirrors validate_xml.py so
    callers / test helpers can reuse the same marker conventions.
    """
    hard = [f for f in findings if f.severity is Severity.HARD]
    soft = [f for f in findings if f.severity is Severity.SOFT]
    n = len(hard)
    print(f"Total issues found: {n}", file=sys.stderr)
    if n == 0:
        print("No issues found.", file=sys.stderr)
    else:
        paths_with_issues = sorted({str(f.path) for f in hard})
        print("Files with issues:", file=sys.stderr)
        for p in paths_with_issues:
            print(f"  {p}", file=sys.stderr)
        for f in hard:
            loc = f" [{f.location}]" if f.location else ""
            print(f"  [{f.rule_id}]{loc} {f.message}", file=sys.stderr)
    if soft:
        print("SOFT findings:", file=sys.stderr)
        for f in soft:
            loc = f" [{f.location}]" if f.location else ""
            lang = f" lang={f.language}" if f.language else ""
            print(
                f"  [{f.rule_id}]{loc}{lang} count={f.count}: {f.message}",
                file=sys.stderr,
            )


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)

    if args.verbose or args.log_dir is not None:
        print(
            "NOTE: --verbose and --log_dir are accepted by the CLI but not "
            "yet implemented by validate_text.py; their values are ignored.",
            file=sys.stderr,
        )

    targets = _resolve_target_files(args)

    all_findings: list[Finding] = []
    per_file_rules = text_rules.RULES

    for path in targets:
        try:
            tree = parse_tree(path)
        except etree.XMLSyntaxError as e:
            all_findings.append(Finding(
                rule_id="V000",
                severity=Severity.HARD,
                message=f"XML parse error: {e}",
                path=path,
            ))
            continue
        all_findings.extend(run_per_file_rules(tree, path, per_file_rules, index=None))

    _print_summary(all_findings)
    write_soft_csv(args.soft_csv, all_findings)

    has_hard = any(f.severity is Severity.HARD for f in all_findings)
    if has_hard and not args.no_exit_on_hard:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

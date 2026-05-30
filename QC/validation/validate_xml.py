"""validate_xml.py — modular FormosanBank XML validator.

Walks a target (by path, by corpus, or by language), parses each .xml
file once with lxml, applies the rules registered under
QC/validation/rules/{hard,soft,warn}.py, and emits HARD/WARN findings
to stderr and SOFT findings to a per-run CSV.

CLI shape (preserved from prior version):
    validate_xml.py by_path     --path <file-or-dir>
    validate_xml.py by_corpus   --corpus <name> --corpora_path <path>
    validate_xml.py by_language --language <name> --corpora_path <path>

Phase 1 (this commit): runner scaffolding only. No rules registered;
all input validates as clean. Subsequent commits add rules and the
CLI flags for the new behavior (--no-exit-on-hard, --soft-csv).
"""
import argparse
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

# When invoked as `python QC/validation/validate_xml.py ...`, the repo root
# is not on sys.path. Add it so the QC.* package imports resolve correctly
# whether the file is run as a script or imported as a module.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lxml import etree

from QC.validation._corpus_index import CorpusIndex
from QC.validation._finding import Finding, Severity
from QC.validation.rules import hard as hard_rules
from QC.validation.rules import soft as soft_rules
from QC.validation.rules import warn as warn_rules


Rule = Callable[[etree._ElementTree, Path, CorpusIndex | None], list[Finding]]


def discover_xml_files(root: Path) -> list[Path]:
    """Return every .xml file under root, recursively.

    Used for by_path, by_corpus, by_language modes uniformly. The
    caller assembles the right root (a single dir, a single file, or
    a filtered list).
    """
    if root.is_file():
        return [root] if root.suffix == ".xml" else []
    return sorted(p for p in root.rglob("*.xml"))


def parse_tree(path: Path) -> etree._ElementTree:
    """Parse a single XML file into an lxml ElementTree.

    No special error handling here: a parse failure raises and the
    runner reports it. Phase 4's DTD validation runs against the same
    parse output.
    """
    return etree.parse(str(path))


def run_per_file_rules(
    tree: etree._ElementTree,
    path: Path,
    rules: Iterable[Rule],
    index: CorpusIndex | None,
) -> list[Finding]:
    """Call each rule on this file's tree, return concatenated findings."""
    out: list[Finding] = []
    for rule in rules:
        out.extend(rule(tree, path, index))
    return out


def _add_common_flags(p: argparse.ArgumentParser) -> None:
    """Add flags shared by all subcommands (verbose, log_dir, no-exit-on-hard).

    These are added to each subparser rather than the parent so that callers
    can place them either before or after the subcommand name on the CLI.
    """
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--log_dir", type=Path, default=None)
    p.add_argument(
        "--no-exit-on-hard",
        action="store_true",
        help="Always exit 0, even if HARD findings are produced. "
             "Backward-compat for callers that depend on the legacy "
             "always-exit-0 behavior.",
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FormosanBank XML validator.")
    sub = parser.add_subparsers(dest="search_by", required=True)

    by_path = sub.add_parser("by_path")
    by_path.add_argument("--path", required=True, type=Path)
    _add_common_flags(by_path)

    by_corpus = sub.add_parser("by_corpus")
    by_corpus.add_argument("--corpus", required=True)
    by_corpus.add_argument("--corpora_path", required=True, type=Path)
    _add_common_flags(by_corpus)

    by_language = sub.add_parser("by_language")
    by_language.add_argument("--language", required=True)
    by_language.add_argument("--corpora_path", required=True, type=Path)
    _add_common_flags(by_language)

    return parser


def _resolve_target_files(args: argparse.Namespace) -> list[Path]:
    if args.search_by == "by_path":
        return discover_xml_files(args.path)
    if args.search_by == "by_corpus":
        return discover_xml_files(args.corpora_path / args.corpus)
    if args.search_by == "by_language":
        # Filter by xml:lang at parse time — fast scan of the root attribute.
        files = []
        for path in discover_xml_files(args.corpora_path):
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
    """Emit the summary tokens that test helpers match on.

    The token strings are preserved from the legacy validator because
    tests/validators/test_validate_xml.py asserts on
    `_is_clean` (looks for "total issues found: 0" + "no issues found")
    and `_has_finding` (looks for "files with issues" et al).

    Per-finding detail lines are also emitted so that `_has_rule_finding`
    marker checks (which look for rule-ID or message text) can match.
    """
    hard = [f for f in findings if f.severity is Severity.HARD]
    n = len(hard)
    print(f"Total issues found: {n}", file=sys.stderr)
    if n == 0:
        print("No issues found.", file=sys.stderr)
        return
    paths_with_issues = sorted({str(f.path) for f in hard})
    print("Files with issues:", file=sys.stderr)
    for p in paths_with_issues:
        print(f"  {p}", file=sys.stderr)
    for f in hard:
        loc = f" [{f.location}]" if f.location else ""
        print(f"  [{f.rule_id}]{loc} {f.message}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    targets = _resolve_target_files(args)

    all_findings: list[Finding] = []
    all_rules = (
        hard_rules.RULES + soft_rules.RULES + warn_rules.RULES
    )

    for path in targets:
        try:
            tree = parse_tree(path)
        except etree.XMLSyntaxError as e:
            # Parse failure is a HARD finding. Match the legacy message
            # shape so tests/validators/test_validate_xml.py's
            # NEGATIVE_MARKERS ("error", "invalid", ...) match.
            all_findings.append(Finding(
                rule_id="V000",
                severity=Severity.HARD,
                message=f"XML parse error: {e}",
                path=path,
            ))
            continue
        all_findings.extend(run_per_file_rules(tree, path, all_rules, index=None))

    _print_summary(all_findings)
    has_hard = any(f.severity is Severity.HARD for f in all_findings)
    if has_hard and not args.no_exit_on_hard:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

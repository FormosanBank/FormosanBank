#!/usr/bin/env python3
"""audit_gloss_scrape.py — pre-QC audit of a scraped gloss corpus.

Audits a scrape of morphosyntactically glossed text (a linguistics paper or
grammar whose interlinear examples were converted to FormosanBank XML) and
reports what a human reviewer should look at first.

Runs in a `Formosan-<Name>/` dev repo, BEFORE run-qc-pipeline and
audit-dev-repo. Read-only: it never modifies the XML or the source.

Two rule groups:
  - XML-internal gloss rules (QC/validation/rules/gloss_scrape.py), G001-G012.
  - Source alignment (QC/validation/_source_align.py), G013/G020-G023, which
    needs --source.

This tool is NOT a gate. Severity ranks triage priority; it exits 0 whatever
it finds, reserving a non-zero exit for its own failures (no XML found, an
unreadable source). --exit-on-hard is available for anyone who later wants
gating behaviour.

It deliberately does not wrap the existing validators. validate_xml.py,
validate_text.py and validate_glosses.py should be run directly, as their own
scripts, so their output is theirs and not a paraphrase of it.

CLI:
    audit_gloss_scrape.py --repo ../Formosan-Foo
    audit_gloss_scrape.py --xml path/to/xml --source path/to/paper.pdf
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lxml import etree  # noqa: E402

from QC.validation._finding import Finding, Severity  # noqa: E402
from QC.validation._report import report_findings  # noqa: E402
from QC.validation._source_align import (  # noqa: E402
    DEFAULT_THRESHOLD,
    G_SOURCE_TITLES,
    align,
    extract_lines,
    source_findings,
)
from QC.validation.rules import gloss_scrape  # noqa: E402

# Directories a dev repo conventionally builds its XML into.
_XML_DIR_CANDIDATES = ("Final_XML", "XML", "xml")
# Source documents live here, or at the repo root.
_SOURCE_DIR_CANDIDATES = ("data", "raw_data", "docs", "sources")
_NAME_RE = re.compile(r"^g(\d+)_(.+)$")


def _titles() -> dict[str, str]:
    """{rule_id: mnemonic}, derived from rule function names like the V rules."""
    titles = dict(G_SOURCE_TITLES)
    titles["G000"] = "xml_unparseable"
    for rule in gloss_scrape.RULES:
        match = _NAME_RE.match(rule.__name__)
        if match:
            titles[f"G{match.group(1)}"] = match.group(2)
    return titles


# ---------------------------------------------------------------------------
# Input discovery
# ---------------------------------------------------------------------------

def discover_xml(repo: Path) -> list[Path]:
    """XML files of a dev repo: a conventional build dir, else root *.xml."""
    for name in _XML_DIR_CANDIDATES:
        directory = repo / name
        if directory.is_dir():
            found = sorted(directory.rglob("*.xml"))
            if found:
                return found
    return sorted(repo.glob("*.xml"))


def discover_sources(repo: Path) -> list[Path]:
    """Candidate source documents, PDFs first.

    PDFs sort first because a PDF is normally the *true* source while a .txt
    beside it is normally the scraper's own intermediate. Auditing the XML
    against a scraper-produced intermediate validates the second hop of
    PDF -> text -> XML and silently trusts the first, which is where OCR and
    column-shredding damage happens. The caller is told which file was picked
    so it can be overridden.
    """
    roots = [repo] + [repo / d for d in _SOURCE_DIR_CANDIDATES]
    pdfs: list[Path] = []
    texts: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        pdfs.extend(sorted(root.glob("*.pdf")))
        texts.extend(sorted(root.glob("*.txt")))
    return pdfs + texts


# ---------------------------------------------------------------------------
# XML loading
# ---------------------------------------------------------------------------

def load_trees(xml_files: list[Path]) -> tuple[list[tuple[Path, etree._ElementTree]], list[Finding]]:
    """Parse each XML file, converting parse failures into G000 findings.

    A scrape is exactly the situation where malformed XML is likely (a
    hand-edited attribute, an unescaped '&'), so a parse failure is a finding
    to report rather than a crash to propagate.
    """
    trees: list[tuple[Path, etree._ElementTree]] = []
    findings: list[Finding] = []
    for xml_file in xml_files:
        try:
            trees.append((xml_file, etree.parse(str(xml_file))))
        except etree.XMLSyntaxError as exc:
            findings.append(Finding(
                rule_id="G000",
                severity=Severity.HARD,
                message=(
                    f"{xml_file.name} is not well-formed XML and could not be "
                    f"parsed, so no other rule could examine it: {exc}"
                ),
                path=xml_file,
                location="",
                line=getattr(exc, "lineno", None),
            ))
    return trees, findings


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pre-QC audit of a scraped, morphosyntactically glossed corpus.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python QC/validation/audit_gloss_scrape.py --repo ../Formosan-Amis-Pa-Verbs
  python QC/validation/audit_gloss_scrape.py --xml corpus.xml --source paper.pdf
  python QC/validation/audit_gloss_scrape.py --repo ../Formosan-Foo --no-source
        """,
    )
    parser.add_argument("--repo", type=Path, help="Dev repo root; XML and source are auto-discovered.")
    parser.add_argument("--xml", type=Path, help="XML file or directory (overrides --repo discovery).")
    parser.add_argument("--source", type=Path, help="Source .pdf or .txt (overrides --repo discovery).")
    parser.add_argument("--no-source", action="store_true", help="Skip Group C source alignment entirely.")
    parser.add_argument(
        "--threshold", type=int, default=DEFAULT_THRESHOLD,
        help=f"Fuzzy-match acceptance score, 0-100 (default {DEFAULT_THRESHOLD}).",
    )
    parser.add_argument("--csv", type=Path, help="Findings CSV path (default logs/audit_gloss_scrape_findings.csv).")
    parser.add_argument("--output_dir", type=Path, help="Directory for the findings CSV when --csv is not given.")
    parser.add_argument("--exit-on-hard", action="store_true", help="Exit 1 when HARD findings exist (off by default).")
    return parser


def _resolve_inputs(args: argparse.Namespace) -> tuple[list[Path], Path | None]:
    xml_files: list[Path] = []
    if args.xml:
        xml_files = sorted(args.xml.rglob("*.xml")) if args.xml.is_dir() else [args.xml]
    elif args.repo:
        xml_files = discover_xml(args.repo)

    source: Path | None = None
    if not args.no_source:
        if args.source:
            source = args.source
        elif args.repo:
            candidates = discover_sources(args.repo)
            source = candidates[0] if candidates else None
            if len(candidates) > 1:
                print(
                    "Source candidates found (using the first; override with --source):",
                    file=sys.stderr,
                )
                for candidate in candidates:
                    marker = "*" if candidate == source else " "
                    print(f"  {marker} {candidate}", file=sys.stderr)
    return xml_files, source


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    if not args.repo and not args.xml:
        print("error: one of --repo or --xml is required", file=sys.stderr)
        return 2

    xml_files, source = _resolve_inputs(args)
    if not xml_files:
        print("error: no XML files found", file=sys.stderr)
        return 2

    csv_path = args.csv or (
        (args.output_dir or Path("logs")) / "audit_gloss_scrape_findings.csv"
    )

    trees, findings = load_trees(xml_files)

    for path, tree in trees:
        for rule in gloss_scrape.RULES:
            findings.extend(rule(tree, path, None))

    if source is not None and trees:
        try:
            lines, extractor = extract_lines(source)
        except (RuntimeError, OSError) as exc:
            print(f"error: could not read source {source}: {exc}", file=sys.stderr)
            return 2
        alignment = align(trees, lines, extractor, threshold=args.threshold)
        findings.extend(source_findings(trees, alignment, source))
    elif source is None and not args.no_source:
        print(
            "warning: no source document found; Group C (source alignment) skipped. "
            "Fidelity to the original text was NOT checked.",
            file=sys.stderr,
        )

    has_hard = report_findings(
        findings, csv_path, file_count=len(xml_files), titles=_titles(),
    )
    if has_hard and args.exit_on_hard:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
validate_duplicate_sentences.py - Detect duplicate <S> sentences within a corpus.

Emits two severities of finding (per the B9.5 plan):
  HARD: two or more <S> elements within the SAME XML file whose chosen-tier
        FORM text matches (whitespace-normalized).  These almost always signal
        ingestion bugs.
  SOFT: two or more <S> elements in DIFFERENT files of the SAME corpus root
        whose chosen-tier FORM text matches.  These may be legitimate (same
        proverb in two stories) or a sign of duplicated source material.

Cross-corpus duplicate detection is *not* in scope here; for that, see
QC/utilities/find_duplicate_sentences.py.

Equivalence (resolved per B9.5 plan, open question 2):
  - Whitespace-normalized (collapse runs of whitespace, strip ends).
  - Case-sensitive.
  - Compared on the chosen tier (default kindOf="standard").

Usage (matches the by_path / by_corpus / by_language pattern used by other
validators in QC/validation/):

  # Scan a single path (file or directory) for duplicates.
  python validate_duplicate_sentences.py by_path --path Corpora/ePark/XML

  # Scan a single corpus folder by name (must be a sibling of Corpora/).
  python validate_duplicate_sentences.py by_corpus --corpora_path Corpora --corpus ePark

  # Scan every corpus under Corpora/ that contains <Language>/ XML files.
  python validate_duplicate_sentences.py by_language --corpora_path Corpora --language Paiwan

  # Choose tier for comparison (default: standard)
  python validate_duplicate_sentences.py by_path --path Corpora/ePark/XML --tier original

Output:
  - A CSV at --output (default: duplicate_sentences_findings.csv) with one row
    per (finding, occurrence) pair: severity, normalized_text, file, s_id.
  - A short summary printed to stdout.

Exit code is 0 even when findings exist; this validator is informational.
"""

import argparse
import csv
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_WS = re.compile(r"\s+")


def normalize_for_comparison(text: str) -> str:
    """Collapse runs of whitespace to a single space and strip ends.

    Does NOT lowercase.  Case-sensitivity is intentional per the B9.5 plan;
    cross-corpus tooling can still choose to lowercase if it wants to.
    """
    return _WS.sub(" ", text).strip()


def extract_sentences(xml_path: str, kind_of: str = "standard"):
    """Return [(s_id, raw_text), ...] for each <S> with a direct-child
    <FORM kindOf=kind_of> that has non-empty text after normalization.

    Mirrors the shape used by QC/utilities/find_duplicate_sentences.py.
    Skips files that can't be parsed (logs a WARNING to stderr).
    """
    out = []
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as e:
        print(f"  WARNING: could not parse {xml_path}: {e}", file=sys.stderr)
        return out
    for s in root.iter("S"):
        sid = s.get("id", "")
        for form in s:  # only direct children
            if form.tag == "FORM" and form.get("kindOf") == kind_of:
                text = form.text or ""
                if normalize_for_comparison(text):
                    out.append((sid, text))
                break  # at most one matching FORM per S
    return out


@dataclass(frozen=True)
class Occurrence:
    file: str          # path relative to scan root
    s_id: str
    raw_text: str      # text as it appeared, pre-normalization


@dataclass
class Finding:
    severity: str                          # "HARD" or "SOFT"
    normalized_text: str
    occurrences: list = field(default_factory=list)

    @property
    def s_ids(self):
        return [o.s_id for o in self.occurrences]


def _collect_xml_files(root_path: str):
    p = Path(root_path)
    if p.is_file() and p.suffix.lower() == ".xml":
        return [p]
    if not p.is_dir():
        return []
    return sorted(p.rglob("*.xml"))


def find_duplicates(root_path: str, kind_of: str = "standard"):
    """Walk root_path, build (normalized_text -> [Occurrence]) index, return
    Findings.  HARD when every occurrence in a group is in the same file; SOFT
    when the group spans multiple files.
    """
    root_p = Path(root_path).resolve()
    if root_p.is_file():
        rel_base = root_p.parent
    else:
        rel_base = root_p

    index: dict[str, list[Occurrence]] = defaultdict(list)
    for xml_path in _collect_xml_files(str(root_p)):
        rel = os.path.relpath(str(xml_path), str(rel_base))
        for sid, raw in extract_sentences(str(xml_path), kind_of=kind_of):
            norm = normalize_for_comparison(raw)
            if not norm:
                continue
            index[norm].append(Occurrence(file=rel, s_id=sid, raw_text=raw))

    findings: list[Finding] = []
    for norm_text, occs in index.items():
        if len(occs) < 2:
            continue
        files = {o.file for o in occs}
        severity = "HARD" if len(files) == 1 else "SOFT"
        findings.append(Finding(severity=severity, normalized_text=norm_text,
                                occurrences=list(occs)))

    # Stable order: severity (HARD first), then by text, then by first occurrence.
    findings.sort(key=lambda f: (0 if f.severity == "HARD" else 1,
                                 f.normalized_text,
                                 f.occurrences[0].file,
                                 f.occurrences[0].s_id))
    return findings


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
    # by_language scans the whole Corpora root but filters XML files later by language path component.
    return args.corpora_path


def _write_csv(findings, output_path: str):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["severity", "normalized_text", "file", "s_id", "raw_text"])
        for fnd in findings:
            for occ in fnd.occurrences:
                w.writerow([fnd.severity, fnd.normalized_text, occ.file,
                            occ.s_id, occ.raw_text])


def _summarize(findings):
    n_hard = sum(1 for f in findings if f.severity == "HARD")
    n_soft = sum(1 for f in findings if f.severity == "SOFT")
    n_hard_occ = sum(len(f.occurrences) for f in findings if f.severity == "HARD")
    n_soft_occ = sum(len(f.occurrences) for f in findings if f.severity == "SOFT")
    print(f"Duplicate sentence findings: HARD={n_hard} groups ({n_hard_occ} occurrences), "
          f"SOFT={n_soft} groups ({n_soft_occ} occurrences)")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect duplicate <S> sentences within a corpus.",
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
    parser.add_argument("--tier", default="standard",
                        choices=["standard", "original"],
                        help='Value of FORM @kindOf to compare (default: standard).')
    parser.add_argument("--output", default="duplicate_sentences_findings.csv",
                        help="CSV output path.")
    parser.add_argument("--verbose", action="store_true",
                        help="Print one line per finding to stdout.")

    args = parser.parse_args(argv)
    scan_root = _resolve_scan_root(args, parser)

    if args.search_by == "by_language":
        if not args.language:
            parser.error("For 'by_language', --language is required.")
        # Build a virtual scan: walk the corpora dir, keep only files under
        # */<language>/* (matching the existing find_duplicate_sentences.py
        # convention).  We delegate to find_duplicates per-corpus so HARD/SOFT
        # remains scoped within a corpus (cross-corpus is out of scope).
        corpora_root = Path(scan_root).resolve()
        findings = []
        for corpus_dir in sorted(corpora_root.iterdir()):
            if not corpus_dir.is_dir():
                continue
            xml_dir = corpus_dir / "XML" / args.language
            if not xml_dir.is_dir():
                continue
            findings.extend(find_duplicates(str(xml_dir), kind_of=args.tier))
    else:
        findings = find_duplicates(scan_root, kind_of=args.tier)

    _write_csv(findings, args.output)
    _summarize(findings)
    print(f"Findings CSV: {args.output}")

    if args.verbose:
        for fnd in findings:
            ids = ", ".join(f"{o.file}#{o.s_id}" for o in fnd.occurrences)
            preview = fnd.normalized_text[:80].replace("\n", " ")
            print(f"  {fnd.severity}  '{preview}'  [{ids}]")

    return 0


if __name__ == "__main__":
    sys.exit(main())

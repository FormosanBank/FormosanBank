#!/usr/bin/env python3
"""
validate_duplicate_sentences.py - Detect duplicate <S> sentences within a corpus.

Severity model (POL-022, ruled 2026-08-11):
  Every duplicate group is SOFT by default — narratives and spontaneous
  speech may legitimately repeat sentences, so the maintainer decides what
  repetition means for a given corpus. Whether a corpus *should* be
  duplicate-free is that corpus's own choice, expressed in its pipeline:
  reference resources (dictionaries, wordlists, grammar example
  collections) run a dedup step in CodeAndDocs/. When the corpus's
  pipeline declares dedup (detected by grepping CodeAndDocs/ for
  'remove_duplicate_sentences' or 'dedup'), every finding upgrades to
  HARD: dedup should have removed it, so a leftover duplicate signals a
  pipeline defect.

  The within-file vs cross-file distinction (formerly the HARD/SOFT axis)
  is preserved as the `scope` column for triage.

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

_DISC_HERE = Path(__file__).resolve()
if str(_DISC_HERE.parents[2]) not in sys.path:
    sys.path.insert(0, str(_DISC_HERE.parents[2]))
from QC.validation._discovery import discover_xml_files as _discover_xml_files  # noqa: E402


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
    severity: str                          # "HARD" or "SOFT" (POL-022)
    normalized_text: str
    occurrences: list = field(default_factory=list)
    scope: str = "within-file"             # "within-file" or "cross-file"

    @property
    def s_ids(self):
        return [o.s_id for o in self.occurrences]


def _collect_xml_files(root_path: str):
    p = Path(root_path)
    if p.is_file() and p.suffix.lower() == ".xml":
        return [p]
    if p.is_file():
        return []
    return _discover_xml_files(p)


# POL-022 (ruled 2026-08-11): whether duplicates are acceptable is a
# per-corpus decision expressed in that corpus's own pipeline — reference
# resources (dictionaries, wordlists, grammars) run a dedup step in
# CodeAndDocs/; narratives don't. The validator therefore reads the
# corpus's pipeline: if it declares dedup, leftover duplicates are HARD
# (the pipeline should have removed them); otherwise everything is SOFT
# and the maintainer decides.
_DEDUP_TOKEN_RE = re.compile(r"remove_duplicate_sentences|dedup", re.IGNORECASE)
_PIPELINE_SUFFIXES = {".sh", ".py", ".md", ".txt", ".json", ".yaml", ".yml", ""}


def dedup_in_pipeline(scan_root: str) -> bool:
    """True if the corpus owning scan_root declares a dedup step.

    Ascends from scan_root looking for a directory with a CodeAndDocs/
    sibling-or-child (the corpus root), then greps its script/doc files
    for a dedup mention ('remove_duplicate_sentences' or 'dedup').
    Returns False when no corpus root is found — e.g. a bare test dir.
    """
    current = Path(scan_root).resolve()
    if current.is_file():
        current = current.parent
    for _ in range(4):
        code_dir = current / "CodeAndDocs"
        if code_dir.is_dir():
            for path in sorted(code_dir.rglob("*")):
                if not path.is_file() or path.suffix.lower() not in _PIPELINE_SUFFIXES:
                    continue
                try:
                    if path.stat().st_size > 2_000_000:
                        continue
                    text = path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                if _DEDUP_TOKEN_RE.search(text):
                    return True
            return False
        if current.parent == current:
            break
        current = current.parent
    return False


def find_duplicates(root_path: str, kind_of: str = "standard",
                    dedup_expected: bool = False):
    """Walk root_path, build (normalized_text -> [Occurrence]) index, return
    Findings.

    Severity (POL-022): SOFT for every duplicate group by default — the
    maintainer decides what repetition means for this corpus. When
    ``dedup_expected`` is True (the corpus's CodeAndDocs pipeline declares
    a dedup step), every group upgrades to HARD: dedup should have removed
    it, so a leftover signals a pipeline defect. The within-file vs
    cross-file distinction is preserved as ``Finding.scope`` for triage.
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

    severity = "HARD" if dedup_expected else "SOFT"
    findings: list[Finding] = []
    for norm_text, occs in index.items():
        if len(occs) < 2:
            continue
        files = {o.file for o in occs}
        scope = "within-file" if len(files) == 1 else "cross-file"
        findings.append(Finding(severity=severity, normalized_text=norm_text,
                                occurrences=list(occs), scope=scope))

    # Stable order: within-file first, then by text, then first occurrence.
    findings.sort(key=lambda f: (0 if f.scope == "within-file" else 1,
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
        w.writerow(["severity", "scope", "normalized_text", "file", "s_id",
                    "raw_text"])
        for fnd in findings:
            for occ in fnd.occurrences:
                w.writerow([fnd.severity, fnd.scope, fnd.normalized_text,
                            occ.file, occ.s_id, occ.raw_text])


def _summarize(findings, dedup_expected: bool = False):
    n_within = sum(1 for f in findings if f.scope == "within-file")
    n_cross = sum(1 for f in findings if f.scope == "cross-file")
    severity = "HARD" if dedup_expected else "SOFT"
    note = (" (corpus pipeline declares dedup — leftovers are pipeline "
            "defects)" if dedup_expected else
            " (no dedup step declared — maintainer's call per POL-022)")
    print(f"Duplicate sentence findings [{severity}]{note}: "
          f"within-file={n_within} groups, cross-file={n_cross} groups")


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
        dedup_expected = False
        for corpus_dir in sorted(corpora_root.iterdir()):
            if not corpus_dir.is_dir():
                continue
            xml_dir = corpus_dir / "XML" / args.language
            if not xml_dir.is_dir():
                continue
            corpus_dedup = dedup_in_pipeline(str(xml_dir))
            dedup_expected = dedup_expected or corpus_dedup
            findings.extend(find_duplicates(str(xml_dir), kind_of=args.tier,
                                            dedup_expected=corpus_dedup))
    else:
        dedup_expected = dedup_in_pipeline(scan_root)
        findings = find_duplicates(scan_root, kind_of=args.tier,
                                   dedup_expected=dedup_expected)

    _write_csv(findings, args.output)
    _summarize(findings, dedup_expected=dedup_expected)
    print(f"Findings CSV: {args.output}")

    if args.verbose:
        for fnd in findings:
            ids = ", ".join(f"{o.file}#{o.s_id}" for o in fnd.occurrences)
            preview = fnd.normalized_text[:80].replace("\n", " ")
            print(f"  {fnd.severity}  '{preview}'  [{ids}]")

    return 0


if __name__ == "__main__":
    sys.exit(main())

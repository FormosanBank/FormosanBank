"""Pre-port consistency gate for a corpus (plain script, no AI required).

Run this before porting a corpus from its dev repo into Corpora/ (and
again on the ported copy). It mechanizes the port-blocking problems that
recent audits kept finding by hand (2026-08 audit season):

  P001 HARD  private material in the ported corpus: a directory whose name
             begins with "Private" inside a corpus under Corpora/ (or given
             --source), or, with --source <dev repo>, a file whose bytes equal
             a non-empty file under the dev repo's Private* directories.
             WARN when a ported file only shares its name with one. A dev
             repo's own Private/ is not checked: it may hold anything, and
             only what is ported matters.
  P002 HARD  TEXT/@xml:lang not a known Formosan ISO 639-3 code
  P003 HARD  TEXT/@dialect not canonical for the language per dialects.csv
             ("unknown" is allowed; missing dialect is reported)
  P004 WARN  commit-hash pins in README/reproducibility/qc_status files
             that disagree with each other or are unreachable in this
             repository (one dev repo shipped three different hashes)
  P005 WARN  corpus AUDIO count differs from statistics/audio_durations.csv
             (stale audio seconds; run refresh_audio_stats.py)
  P006 WARN  CodeAndDocs standardizes through a conversion table (any
             --tsv_path, not only Orthographies/ConversionTables/); remind to run
             validate_conversion_table.py on it before trusting the
             standard tier

Exit 1 iff any HARD finding. WARNs need human judgment and never block.

Usage:
    python QC/validation/validate_port_readiness.py --corpus_path <dir>
        [--repo-root <FormosanBank checkout>] [--source <dev repo>]

<dir> is the corpus root (the directory holding XML/ and CodeAndDocs/),
either a dev repo or Corpora/<Name>. Pass --source with the dev repo when
checking the ported copy, so P001 can compare against its Private* files.
"""
import argparse
import csv
import hashlib
import re
import subprocess
import sys
from pathlib import Path

from lxml import etree

_HERE = Path(__file__).resolve()
sys.path.insert(0, str(_HERE.parents[2]))

from QC.validation._dialect_inventory import (  # noqa: E402
    ISO_TO_LANGUAGE, UNKNOWN_DIALECT, valid_dialects,
)

_XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

# A pin looks like a 7-40 char hex string on a line that talks about
# commits/hashes/pinning. The context requirement keeps ordinary hex-ish
# tokens (checksums of audio files, IDs) from being read as repo pins.
_HASH_CONTEXT_RE = re.compile(r"commit|hash|\bpin|reproduc|checkout",
                              re.IGNORECASE)
_HEX_RE = re.compile(r"\b[0-9a-f]{7,40}\b")
# A hash inside a URL is a link (to upstream data, to the corpus's own
# history), not a pin of this repository: PR #170's upstream data link and
# PR #163's history links both tripped P004 before this.
_URL_RE = re.compile(r"https?://\S+|\]\([^)]*\)")
_PIN_FILE_GLOBS = ("README*", "readme*", "reproducibility*", "qc_status*")


class Report:
    def __init__(self) -> None:
        self.hard: list[str] = []
        self.warn: list[str] = []

    def add(self, rule: str, severity: str, message: str) -> None:
        line = f"{rule} {severity}: {message}"
        (self.hard if severity == "HARD" else self.warn).append(line)


def _xml_files(corpus_path: Path) -> list[Path]:
    xml_dir = corpus_path / "XML"
    root = xml_dir if xml_dir.is_dir() else corpus_path
    return sorted(p for p in root.rglob("*.xml"))


def _is_private_name(name: str) -> bool:
    # Private/, but also Private:Source/, Private-data/ and the like.
    return name.lower().startswith("private")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def check_private_not_ported(corpus_path: Path, source: Path | None,
                             report: Report) -> None:
    """P001: nothing private is in the ported corpus.

    Maintainer, 2026-11-09: "we should remove that gate. Instead, we should
    gate the port itself, ensuring that the Private folder and its content
    isn't ported." A dev repo's own Private/ is therefore not examined; the
    ported copy is.
    """
    ported = source is not None or corpus_path.parent.name == "Corpora"
    if not ported:
        return
    for path in sorted(corpus_path.rglob("*")):
        if path.is_dir() and _is_private_name(path.name):
            report.add("P001", "HARD",
                       f"private directory in the ported corpus: "
                       f"{path.relative_to(corpus_path)}")
    if source is None:
        return
    private_files = [f for d in sorted(source.iterdir())
                     if d.is_dir() and _is_private_name(d.name)
                     for f in sorted(d.rglob("*"))
                     if f.is_file() and f.stat().st_size > 0]   # an empty file carries no content
    if not private_files:
        return
    by_hash = {_sha256(f): f for f in private_files}
    by_name = {f.name: f for f in private_files}
    for path in sorted(corpus_path.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(corpus_path)
        match = by_hash.get(_sha256(path)) if path.stat().st_size > 0 else None
        if match is not None:
            report.add("P001", "HARD",
                       f"{relative} has the same content as "
                       f"{match.relative_to(source)} in the dev repo")
        elif path.name in by_name:
            report.add("P001", "WARN",
                       f"{relative} shares its name with "
                       f"{by_name[path.name].relative_to(source)} (different "
                       f"content); check it is not private")


def check_language_and_dialect(corpus_path: Path, report: Report) -> None:
    """P002/P003: xml:lang known; dialect canonical per dialects.csv."""
    seen: set[tuple[str, str]] = set()
    for path in _xml_files(corpus_path):
        try:
            root = etree.parse(str(path)).getroot()
        except etree.XMLSyntaxError as error:
            report.add("P002", "HARD", f"{path}: unparseable XML ({error})")
            continue
        for text_el in ([root] if root.tag == "TEXT"
                        else root.iter("TEXT")):
            lang = (text_el.get(_XML_LANG) or "").strip()
            dialect = (text_el.get("dialect") or "").strip()
            key = (lang, dialect)
            if key in seen:
                continue
            seen.add(key)
            if lang not in ISO_TO_LANGUAGE:
                report.add("P002", "HARD",
                           f"{path.name}: xml:lang={lang!r} is not a known "
                           f"Formosan ISO 639-3 code")
                continue
            allowed = valid_dialects(lang)
            if not dialect:
                report.add("P003", "HARD",
                           f"{path.name}: TEXT has no dialect attribute "
                           f"(use 'unknown' if unidentifiable)")
            elif dialect != UNKNOWN_DIALECT and allowed is not None \
                    and dialect not in allowed:
                report.add("P003", "HARD",
                           f"{path.name}: dialect={dialect!r} not canonical "
                           f"for {ISO_TO_LANGUAGE[lang]} per dialects.csv "
                           f"(allowed: {sorted(allowed)})")


def check_commit_pins(corpus_path: Path, repo_root: Path,
                      report: Report) -> None:
    """P004: commit pins agree with each other and exist in repo_root."""
    pins: dict[str, list[str]] = {}
    for pattern in _PIN_FILE_GLOBS:
        for path in list(corpus_path.glob(pattern)) + \
                list((corpus_path / "CodeAndDocs").glob(pattern)):
            try:
                lines = path.read_text(encoding="utf-8",
                                       errors="replace").splitlines()
            except OSError:
                continue
            for line in lines:
                if not _HASH_CONTEXT_RE.search(line):
                    continue
                for match in _HEX_RE.findall(_URL_RE.sub(" ", line)):
                    pins.setdefault(match, []).append(path.name)
    if not pins:
        return
    for pin, sources in sorted(pins.items()):
        exists = subprocess.run(
            ["git", "cat-file", "-e", f"{pin}^{{commit}}"],
            capture_output=True, cwd=repo_root,
        ).returncode == 0
        if not exists:
            report.add("P004", "WARN",
                       f"pinned commit {pin} (in {', '.join(sorted(set(sources)))}) "
                       f"is not reachable in {repo_root}")
    roots = {pin[:7] for pin in pins}
    if len(roots) > 1:
        detail = "; ".join(
            f"{pin} in {', '.join(sorted(set(srcs)))}"
            for pin, srcs in sorted(pins.items()))
        report.add("P004", "WARN",
                   f"documents pin {len(roots)} different commits — decide "
                   f"which is authoritative ({detail})")


def check_audio_stats(corpus_path: Path, repo_root: Path,
                      report: Report) -> None:
    """P005: AUDIO element count vs audio_durations.csv counts."""
    audio_count = 0
    for path in _xml_files(corpus_path):
        try:
            audio_count += len(etree.parse(str(path)).getroot().findall(".//AUDIO"))
        except etree.XMLSyntaxError:
            continue
    if audio_count == 0:
        return
    stats_path = repo_root / "statistics" / "audio_durations.csv"
    recorded = 0
    corpus_name = corpus_path.resolve().name
    if stats_path.exists():
        with open(stats_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("corpus") == corpus_name:
                    recorded += int(row.get("transcribed_audio_count") or 0)
                    recorded += int(row.get("untranscribed_audio_count") or 0)
    if recorded == 0:
        report.add("P005", "WARN",
                   f"corpus has {audio_count} AUDIO elements but no "
                   f"audio_durations.csv rows for {corpus_name!r}; run "
                   f"QC/utilities/refresh_audio_stats.py after porting")
    elif recorded != audio_count:
        report.add("P005", "WARN",
                   f"AUDIO count {audio_count} != audio_durations.csv "
                   f"count_at_compute {recorded} for {corpus_name!r} "
                   f"(stale seconds; run refresh_audio_stats.py)")


def check_conversion_tables(corpus_path: Path, report: Report) -> None:
    """P006: remind to validate any referenced conversion table."""
    code_dir = corpus_path / "CodeAndDocs"
    if not code_dir.is_dir():
        return
    referenced: set[str] = set()
    for path in code_dir.rglob("*"):
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        if path.suffix.lower() not in {".py", ".sh", ".md", ".txt", ".tsv",
                                       ".json", ".yaml", ".yml"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in re.findall(r"ConversionTables/([A-Za-z0-9_\- ]+\.tsv)",
                                text):
            referenced.add("ConversionTables/" + match)
        # A corpus-local table (--tsv_path CodeAndDocs/foo.tsv) escapes the
        # POL-056 sweep entirely, so it needs the reminder most: PRs #153 and
        # #150 passed with 0 WARN while standardizing through one.
        for match in re.findall(r"--tsv_path[ =]+[\"']?([^\s\"']+)", text):
            if "ConversionTables/" not in match:
                referenced.add(match)
    for table in sorted(referenced):
        local = "" if "ConversionTables/" in table else " (corpus-local: outside the POL-056 sweep)"
        report.add("P006", "WARN",
                   f"standardization uses {table}{local}; run "
                   f"QC/validation/validate_conversion_table.py on it before "
                   f"trusting the standard tier")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Pre-port consistency gate (no AI required)")
    parser.add_argument("--corpus_path", required=True, type=Path,
                        help="corpus root: the dir holding XML/ (dev repo "
                             "or Corpora/<Name>)")
    parser.add_argument("--repo-root", type=Path, default=_HERE.parents[2],
                        help="FormosanBank checkout for pin/audio checks "
                             "(default: this one)")
    parser.add_argument("--source", type=Path,
                        help="the dev repo the corpus was ported from: P001 "
                             "then checks that none of its Private* files "
                             "reached --corpus_path")
    args = parser.parse_args(argv)
    corpus_path = args.corpus_path.resolve()
    if not corpus_path.is_dir():
        print(f"Error: {corpus_path} is not a directory", file=sys.stderr)
        return 1
    source = args.source.resolve() if args.source else None
    if source is not None and not source.is_dir():
        print(f"Error: --source {source} is not a directory", file=sys.stderr)
        return 1

    report = Report()
    check_private_not_ported(corpus_path, source, report)
    check_language_and_dialect(corpus_path, report)
    check_commit_pins(corpus_path, args.repo_root, report)
    check_audio_stats(corpus_path, args.repo_root, report)
    check_conversion_tables(corpus_path, report)

    for line in report.hard + report.warn:
        print(line)
    print(f"port-readiness: {len(report.hard)} HARD, "
          f"{len(report.warn)} WARN")
    return 1 if report.hard else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Per-corpus waivers for HARD findings that a human has dispositioned.

A waiver says: *someone read this finding, decided the data is right, and
wrote down why.* It lives with the corpus, at the fixed path

    Corpora/<Name>/CodeAndDocs/qc_waivers.tsv

as a tab-separated file with a header and four columns:

    rule_id   file                          location   reason
    V129      Saisiyat/saisiyat_seals.xml   S=25       Neogrammarian reconstruction …

``file`` is relative to the corpus's ``XML/`` directory, so the key is stable
whatever the checkout path. A waiver matches a finding on
``(rule_id, file, location)`` and reclassifies it HARD -> WAIVED. Waived
findings are still reported and still written to the findings CSV; they simply
stop failing the build.

Three constraints keep the file from rotting into a blindfold:

1. **No wildcards.** Explicit keys only. ``V129 * *`` is how a whitelist
   becomes a way to stop looking.
2. **A waiver that matches nothing is not an error.** Fixing a finding must
   never cost a second edit to the waiver file: the risk here is a *new*
   HARD finding, not a disappearing one, and a rule that fails the build
   when you repair data is a barrier pointed the wrong way (maintainer,
   2026-09-09). ``apply_waivers`` still reports which waivers matched
   nothing so ``waivers.py prune`` can drop them on request -- the POL-030
   ``--prune`` shape, an explicit human action rather than a gate.
3. **A reason is mandatory.** Empty, whitespace, or a leftover ``TODO``
   placeholder is rejected. The reason is the only part of a waiver that a
   tool cannot generate, which is exactly why it is the part that counts.

Only rules in ``WAIVABLE_RULES`` may be waived. See its comment.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from QC.validation._finding import Finding, Severity

#: The fixed filename, inside the corpus's CodeAndDocs/. One path, so the
#: file is machine-findable and testable (the provenance.json precedent).
WAIVER_FILENAME = "qc_waivers.tsv"

COLUMNS = ("rule_id", "file", "location", "reason")

#: Placeholder written by ``waivers.py propose``; rejected until replaced.
TODO_REASON = "TODO"

#: Rules a waiver may cover.
#:
#: Only rules that encode a *judgement* about the source belong here. A
#: structural rule -- a schema violation, a malformed or duplicated id, a
#: broken tier relationship -- states a fact about the XML that is fixable by
#: definition, so a waiver there is always the wrong tool and would let broken
#: data ship behind a sentence of prose.
#:
#: V129 ('*' in any FORM) is the founding case: POL-016 excludes
#: source-ungrammatical examples at intake, so a '*' that survives into a
#: published FORM is notation -- most often a Neogrammarian reconstruction
#: label -- and only a human reading the source can tell the two apart.
#:
#: Adding an id here is a policy decision, not a convenience. Do it in a PR
#: that says which rule and why.
WAIVABLE_RULES = frozenset({"V129"})


class WaiverError(ValueError):
    """A waiver file is malformed, or waives something it may not."""


@dataclass(frozen=True)
class Waiver:
    rule_id: str
    file: str
    location: str
    reason: str
    source: Path
    line: int

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.rule_id, self.file, self.location)

    def describe(self) -> str:
        return f"{self.rule_id} {self.file} {self.location or '(file)'}"


def waiver_path(corpus_dir: Path) -> Path:
    """Where a corpus's waiver file lives, whether or not it exists."""
    return Path(corpus_dir) / "CodeAndDocs" / WAIVER_FILENAME


def corpus_root_for(xml_file: Path) -> Path | None:
    """The corpus directory owning ``xml_file``, or None.

    Walks up from the file looking for an ancestor with a ``CodeAndDocs/``
    sibling directory, which is what makes a directory a corpus. Works
    identically for by_path, by_corpus and by_language runs, and for a
    validator pointed at a single file deep inside ``XML/``.
    """
    for ancestor in Path(xml_file).resolve().parents:
        if (ancestor / "CodeAndDocs").is_dir():
            return ancestor
    return None


def relative_xml_name(xml_file: Path, corpus_dir: Path) -> str:
    """The waiver-file spelling of ``xml_file``: relative to the corpus XML/.

    Falls back to a path relative to the corpus directory when the file is
    not under ``XML/`` (nothing published looks like that, but a validator
    run against a scratch copy might).
    """
    resolved = Path(xml_file).resolve()
    xml_root = Path(corpus_dir) / "XML"
    for base in (xml_root, Path(corpus_dir)):
        try:
            return resolved.relative_to(base.resolve()).as_posix()
        except ValueError:
            continue
    return resolved.name


def load_waivers(corpus_dir: Path) -> list[Waiver]:
    """Read and validate one corpus's waiver file. Absent file -> []."""
    path = waiver_path(corpus_dir)
    if not path.is_file():
        return []

    waivers: list[Waiver] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise WaiverError(
                f"{path}: missing column(s) {', '.join(missing)}; "
                f"header must be {chr(9).join(COLUMNS)}"
            )
        for offset, row in enumerate(reader, start=2):
            rule_id = (row.get("rule_id") or "").strip()
            xml_file = (row.get("file") or "").strip()
            location = (row.get("location") or "").strip()
            reason = (row.get("reason") or "").strip()

            if not rule_id:
                raise WaiverError(f"{path}:{offset}: rule_id is required")
            if rule_id not in WAIVABLE_RULES:
                raise WaiverError(
                    f"{path}:{offset}: {rule_id} may not be waived. Waivable "
                    f"rules: {', '.join(sorted(WAIVABLE_RULES))}. A structural "
                    "finding is fixed, not waived; if this rule should become "
                    "waivable, say so in its own pull request."
                )
            if not xml_file:
                raise WaiverError(f"{path}:{offset}: file is required")
            if "*" in xml_file or "*" in location:
                raise WaiverError(
                    f"{path}:{offset}: wildcards are not allowed; waive an "
                    "exact (rule_id, file, location)"
                )
            if not reason or reason == TODO_REASON:
                raise WaiverError(
                    f"{path}:{offset}: {rule_id} {xml_file} {location} has no "
                    "reason. Say why this finding is accepted — a waiver "
                    "nobody justified is the thing this file exists to prevent."
                )
            waivers.append(
                Waiver(rule_id, xml_file, location, reason, path, offset)
            )

    seen: dict[tuple[str, str, str], int] = {}
    for waiver in waivers:
        if waiver.key in seen:
            raise WaiverError(
                f"{path}:{waiver.line}: duplicate waiver for "
                f"{waiver.describe()} (already at line {seen[waiver.key]})"
            )
        seen[waiver.key] = waiver.line
    return waivers


def _finding_key(finding: Finding, corpus_dir: Path) -> tuple[str, str, str]:
    return (
        finding.rule_id,
        relative_xml_name(finding.path, corpus_dir),
        finding.location or "",
    )


def apply_waivers(findings: list[Finding]) -> tuple[list[Finding], list[Waiver]]:
    """Reclassify waived HARD findings, and report waivers that matched nothing.

    Returns ``(findings, stale)`` where ``findings`` has every waived HARD
    finding rewritten to ``Severity.WAIVED`` (nothing is dropped) and
    ``stale`` lists waivers that matched no finding in this run.

    ``stale`` is informational: the reporter does not fail on it. It exists
    so ``waivers.py prune`` can offer to delete rows whose findings are gone.
    Note a waiver is "stale" only relative to the files this run covered — a
    run scoped to one language says nothing about another's waivers, which
    is why pruning is a deliberate command and never automatic.

    Waiver files are loaded once per corpus touched by the findings. A corpus
    with no waiver file contributes nothing and cannot go stale.
    """
    corpora: dict[Path, list[Waiver]] = {}
    for finding in findings:
        corpus_dir = corpus_root_for(finding.path)
        if corpus_dir is None or corpus_dir in corpora:
            continue
        corpora[corpus_dir] = load_waivers(corpus_dir)

    matched: set[tuple[Path, tuple[str, str, str]]] = set()
    out: list[Finding] = []
    for finding in findings:
        corpus_dir = corpus_root_for(finding.path)
        waivers = corpora.get(corpus_dir, []) if corpus_dir else []
        if finding.severity is Severity.HARD and waivers:
            key = _finding_key(finding, corpus_dir)
            if any(w.key == key for w in waivers):
                matched.add((corpus_dir, key))
                out.append(
                    Finding(
                        rule_id=finding.rule_id,
                        severity=Severity.WAIVED,
                        message=finding.message,
                        path=finding.path,
                        location=finding.location,
                        count=finding.count,
                        language=finding.language,
                        character=finding.character,
                        line=finding.line,
                    )
                )
                continue
        out.append(finding)

    stale = [
        waiver
        for corpus_dir, waivers in corpora.items()
        for waiver in waivers
        if (corpus_dir, waiver.key) not in matched
    ]
    return out, stale

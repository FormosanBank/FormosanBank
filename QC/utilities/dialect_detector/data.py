from __future__ import annotations

import csv
import fnmatch
import warnings
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from QC.corpus_counts import is_reproduction_path
from QC.utilities.dialect_detector import candidates
from QC.xml_forms import iter_base_forms

_XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
_UNLABELED = {"", "unknown"}
TRAINING_EXCLUSIONS = Path(__file__).with_name("training_exclusions.tsv")


def load_training_exclusions(path: Path = TRAINING_EXCLUSIONS) -> list[str]:
    """Path patterns (fnmatch, relative to the corpora root) for labelled files
    that must never be training documents. Each row of the TSV says why."""
    if not Path(path).exists():
        return []
    with open(path, encoding="utf-8", newline="") as fh:
        return [r["pattern"].strip() for r in csv.DictReader(fh, delimiter="\t")
                if (r.get("pattern") or "").strip()]


@dataclass(frozen=True)
class LabeledDoc:
    path: Path
    dialect: str   # reconciled candidate name (or raw, when in `dropped`)
    text: str


def xml_lang(root: ET.Element) -> str:
    return (root.get(_XML_LANG) or "").strip().lower()


def extract_standard_text(root: ET.Element) -> str:
    # Base FORMs only. A POL-028 ver="alt" variant is a second reading of
    # the same sentence, so folding it in would count that sentence twice
    # and mix a secondary spelling into the dialect features.
    parts = [
        f.text.strip()
        for s in root.findall(".//S")
        for f in iter_base_forms(s, "standard")
        if f.text and f.text.strip()
    ]
    return " ".join(parts).strip()


def _iter_text_roots(corpora_path: Path):
    for p in sorted(Path(corpora_path).rglob("*.xml")):
        # CodeAndDocs holds POL-035 snapshots: copies of published files that
        # would count twice and straddle cross-validation folds.
        if is_reproduction_path(p, root=corpora_path):
            continue
        try:
            root = ET.parse(p).getroot()
        except ET.ParseError:
            continue
        if root.tag == "TEXT":
            yield p, root


def iter_labeled_documents(
    corpora_path: Path, lang_code: str, exclusions: list[str] | None = None,
) -> tuple[list[LabeledDoc], list[LabeledDoc]]:
    """Return (kept, dropped). `kept` have a reconciled candidate dialect and a
    non-empty standard tier; `dropped` had a non-empty label that did not map to
    any candidate (recorded with the raw label for diagnostics). Files matching
    `exclusions` (default: training_exclusions.tsv) are skipped, with a warning
    giving the count."""
    if exclusions is None:
        exclusions = load_training_exclusions()
    cands = candidates.candidate_dialects(lang_code)
    kept: list[LabeledDoc] = []
    dropped: list[LabeledDoc] = []
    excluded = 0
    for path, root in _iter_text_roots(corpora_path):
        if xml_lang(root) != lang_code.lower():
            continue
        raw = (root.get("dialect") or "").strip()
        if raw in _UNLABELED:
            continue
        rel = path.relative_to(corpora_path).as_posix()
        if any(fnmatch.fnmatchcase(rel, pat) for pat in exclusions):
            excluded += 1
            continue
        text = extract_standard_text(root)
        if not text:
            continue
        canon = candidates.reconcile_label(raw, cands)
        if canon is None:
            dropped.append(LabeledDoc(path, raw, text))
        else:
            kept.append(LabeledDoc(path, canon, text))
    if excluded:
        warnings.warn(
            f"{lang_code}: {excluded} labelled file(s) left out of training by "
            f"{TRAINING_EXCLUSIONS.name}",
            RuntimeWarning,
            stacklevel=2,
        )
    return kept, dropped

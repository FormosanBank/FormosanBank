from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from QC.utilities.dialect_detector import candidates
from QC.xml_forms import iter_base_forms

_XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
_UNLABELED = {"", "unknown"}


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
        try:
            root = ET.parse(p).getroot()
        except ET.ParseError:
            continue
        if root.tag == "TEXT":
            yield p, root


def iter_labeled_documents(
    corpora_path: Path, lang_code: str
) -> tuple[list[LabeledDoc], list[LabeledDoc]]:
    """Return (kept, dropped). `kept` have a reconciled candidate dialect and a
    non-empty standard tier; `dropped` had a non-empty label that did not map to
    any candidate (recorded with the raw label for diagnostics)."""
    cands = candidates.candidate_dialects(lang_code)
    kept: list[LabeledDoc] = []
    dropped: list[LabeledDoc] = []
    for path, root in _iter_text_roots(corpora_path):
        if xml_lang(root) != lang_code.lower():
            continue
        raw = (root.get("dialect") or "").strip()
        if raw in _UNLABELED:
            continue
        text = extract_standard_text(root)
        if not text:
            continue
        canon = candidates.reconcile_label(raw, cands)
        if canon is None:
            dropped.append(LabeledDoc(path, raw, text))
        else:
            kept.append(LabeledDoc(path, canon, text))
    return kept, dropped

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from QC.utilities.dialect_detector import candidates

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
    parts = [
        f.text.strip()
        for s in root.findall(".//S")
        for f in s.findall("./FORM[@kindOf='standard']")
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


def iter_unknown_documents(corpora_path: Path, lang_code: str) -> list[LabeledDoc]:
    """Return same-language docs whose dialect is missing or marked unknown.

    These docs are excluded from supervised training, but they can be used to
    measure whether calibrated thresholds correctly abstain on held-out unknowns.
    """
    unknown: list[LabeledDoc] = []
    for path, root in _iter_text_roots(corpora_path):
        if xml_lang(root) != lang_code.lower():
            continue
        raw = (root.get("dialect") or "").strip()
        if raw not in _UNLABELED:
            continue
        text = extract_standard_text(root)
        if not text:
            continue
        unknown.append(LabeledDoc(path, "unknown", text))
    return unknown

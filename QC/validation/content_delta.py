#!/usr/bin/env python3
"""content_delta.py — what a PR removes, renames or relabels in published XML.

rights_delta.py compares one attribute, the licence, between the merge base
and the head and goes red for the maintainer to override. This does the same
for the content POL-037 and POL-051 protect and nothing checked at PR time:

  - TEXT ids removed (or renamed: the same sentences under a new id);
  - S ids removed inside a kept TEXT (or renumbered: the same original
    FORM text under new ids);
  - element counts per tier (S, W, M, TRANSL, AUDIO, PHON) that go DOWN;
  - TEXT/@dialect and TEXT/@copyright values that change.

The September re-port PRs supplied the cases: #179 rehashed all 98,837 ILRDF
ids; #157 dropped 8 published S undisclosed; #162 renamed all three Paiwan
Stories TEXT ids; #164 removed 144,436 AUDIO and 126,239 W; #166 removed
1,968 Dutch TRANSL; #199 deleted 88,677 original PHON and relabelled 62,484
Truku records dialect="unknown". Only 3 of 24 disclosed their removals.

Additions are reported and never red. Any removal, rename, renumbering,
count drop or relabelling exits 1; a legitimate one is merged by maintainer
override, as a licence change is. There is no label-based bypass.

    python QC/validation/content_delta.py --base /tmp/base/Corpora --head Corpora
    python QC/validation/content_delta.py --base … --head … --corpus ePark --corpus ILRDF_Dicts
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

TIERS = ("S", "W", "M", "TRANSL", "AUDIO", "PHON")
_XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


@dataclass
class TextRecord:
    dialect: str
    copyright: str
    language: str
    s_ids: list[str]
    s_texts: dict[str, str]          # S id -> normalized original FORM text
    counts: Counter = field(default_factory=Counter)

    @property
    def signature(self) -> str:
        """Content fingerprint: the ordered original sentences, ids ignored."""
        joined = "\n".join(self.s_texts[s] for s in self.s_ids)
        return hashlib.sha1(joined.encode("utf-8")).hexdigest()


def _original_text(s: etree._Element) -> str:
    for form in s.findall("FORM"):
        if form.get("kindOf") == "original" and form.get("ver") is None:
            return " ".join((form.text or "").split())
    for form in s.findall("FORM"):
        if form.get("ver") is None:
            return " ".join((form.text or "").split())
    return ""


def read_text(path: Path) -> tuple[str, TextRecord] | None:
    """(TEXT id, record) for one XML file, or None when it is not a TEXT."""
    tree = etree.parse(str(path))
    root = tree.getroot()
    if root.tag != "TEXT":
        return None
    counts: Counter = Counter()
    for elem in root.iter(*TIERS):
        counts[elem.tag] += 1
    s_ids, s_texts = [], {}
    for n, s in enumerate(root.iter("S")):
        s_id = s.get("id") or f"#{n}"
        s_ids.append(s_id)
        s_texts[s_id] = _original_text(s)
    text_id = root.get("id") or path.stem
    return text_id, TextRecord(
        dialect=(root.get("dialect") or "").strip(),
        copyright=(root.get("copyright") or "").strip(),
        language=(root.get(_XML_LANG) or "").strip(),
        s_ids=s_ids, s_texts=s_texts, counts=counts,
    )


def inventory(corpora_path: Path, corpora: set[str] | None = None) -> dict[str, dict[str, TextRecord]]:
    """{corpus: {TEXT id: record}} for every corpus that publishes XML."""
    out: dict[str, dict[str, TextRecord]] = {}
    for corpus_dir in sorted(Path(corpora_path).iterdir()):
        if corpora is not None and corpus_dir.name not in corpora:
            continue
        xml_dir = corpus_dir / "XML"
        if not xml_dir.is_dir():
            continue
        texts: dict[str, TextRecord] = {}
        for path in sorted(xml_dir.rglob("*.xml")):
            if "CodeAndDocs" in path.parts:
                continue
            try:
                parsed = read_text(path)
            except etree.XMLSyntaxError:
                continue   # the XML validator reports it
            if parsed is None:
                continue
            text_id, record = parsed
            key = text_id if text_id not in texts else f"{text_id}@{path.relative_to(xml_dir)}"
            texts[key] = record
        out[corpus_dir.name] = texts
    return out


@dataclass
class Change:
    corpus: str
    kind: str          # what happened
    detail: str        # ids / values
    count: int = 0
    red: bool = True   # removals, renames, relabellings are red; additions are not

    def line(self) -> str:
        flag = "RED " if self.red else "    "
        n = f" ×{self.count}" if self.count else ""
        return f"{flag}{self.corpus}: {self.kind}{n} — {self.detail}"


def _summ(ids: list[str], limit: int = 6) -> str:
    shown = ", ".join(ids[:limit])
    return shown + (f", … (+{len(ids) - limit})" if len(ids) > limit else "")


def compare_corpus(corpus: str, base: dict[str, TextRecord], head: dict[str, TextRecord]) -> list[Change]:
    changes: list[Change] = []
    base_ids, head_ids = set(base), set(head)

    # --- TEXT ids: removed, renamed (same content under a new id), added
    removed = sorted(base_ids - head_ids)
    added = sorted(head_ids - base_ids)
    head_sig = {head[t].signature: t for t in added}
    renamed = []
    for t in list(removed):
        other = head_sig.get(base[t].signature)
        if other is not None:
            renamed.append((t, other)); removed.remove(t); added.remove(other)
    if renamed:
        changes.append(Change(corpus, "TEXT ids renamed (same sentences)", _summ([f"{a} → {b}" for a, b in renamed]), len(renamed)))
    if removed:
        changes.append(Change(corpus, "TEXT ids removed", _summ(removed), len(removed)))
    if added:
        changes.append(Change(corpus, "TEXT ids added", _summ(added), len(added), red=False))

    # --- within kept (or renamed) TEXTs: S ids removed / renumbered, counts, dialect, copyright
    pairs = [(t, t) for t in sorted(base_ids & head_ids)] + renamed
    s_removed: list[str] = []
    s_renumbered = 0
    drops: Counter = Counter()
    gains: Counter = Counter()
    dialect_changes: list[str] = []
    copyright_changes: list[str] = []
    for b_id, h_id in pairs:
        b, h = base[b_id], head[h_id]
        gone = [s for s in b.s_ids if s not in h.s_texts]
        new = [s for s in h.s_ids if s not in b.s_texts]
        new_texts = Counter(h.s_texts[s] for s in new)
        for s in gone:
            if new_texts[b.s_texts[s]] > 0:
                new_texts[b.s_texts[s]] -= 1
                s_renumbered += 1
            else:
                s_removed.append(f"{b_id}/{s}")
        for tier in TIERS:
            diff = h.counts[tier] - b.counts[tier]
            if diff < 0:
                drops[tier] += -diff
            elif diff > 0:
                gains[tier] += diff
        if b.dialect != h.dialect:
            dialect_changes.append(f"{h_id}: {b.dialect or '(none)'} → {h.dialect or '(none)'}")
        if b.copyright != h.copyright:
            copyright_changes.append(f"{h_id}: {b.copyright!r} → {h.copyright!r}")
    if s_renumbered:
        changes.append(Change(corpus, "S ids renumbered (same text, new id)", "POL-037: ids are stable", s_renumbered))
    if s_removed:
        changes.append(Change(corpus, "S removed", _summ(s_removed), len(s_removed)))
    for tier in TIERS:
        if drops[tier]:
            changes.append(Change(corpus, f"{tier} count down", f"−{drops[tier]} across kept TEXTs", drops[tier]))
    for tier in TIERS:
        if gains[tier]:
            changes.append(Change(corpus, f"{tier} count up", f"+{gains[tier]} across kept TEXTs", gains[tier], red=False))
    if dialect_changes:
        changes.append(Change(corpus, "TEXT/@dialect changed", _summ(dialect_changes), len(dialect_changes)))
    if copyright_changes:
        changes.append(Change(corpus, "TEXT/@copyright changed", _summ(copyright_changes), len(copyright_changes)))
    return changes


def compare(base: dict[str, dict[str, TextRecord]], head: dict[str, dict[str, TextRecord]]) -> list[Change]:
    changes: list[Change] = []
    for corpus in sorted(set(base) | set(head)):
        if corpus not in head:
            changes.append(Change(corpus, "corpus removed", f"{len(base[corpus])} TEXT(s) gone", len(base[corpus])))
        elif corpus not in base:
            changes.append(Change(corpus, "corpus added", f"{len(head[corpus])} TEXT(s)", len(head[corpus]), red=False))
        else:
            changes.extend(compare_corpus(corpus, base[corpus], head[corpus]))
    return changes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True, type=Path, help="Corpora/ of the merge base")
    ap.add_argument("--head", required=True, type=Path, help="Corpora/ of the head")
    ap.add_argument("--corpus", action="append", default=None,
                    help="restrict to this corpus (repeatable); default: every corpus on either side")
    a = ap.parse_args(argv)
    only = set(a.corpus) if a.corpus else None
    changes = compare(inventory(a.base, only), inventory(a.head, only))
    if not changes:
        print("No published content removed, renamed or relabelled.")
        return 0
    red = [c for c in changes if c.red]
    print("Content changes between base and head (POL-037 ids, POL-051 removals):")
    for c in changes:
        print("  " + c.line())
    if not red:
        print("\nAdditions only; nothing to override.")
        return 0
    print(f"\n{len(red)} red line(s). A removal, rename, renumbering, count drop or relabelling "
          "is never routine: if it is intended and disclosed in the PR, a maintainer overrides "
          "this check; there is no label-based bypass.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

"""Shared helpers for the manual-edits capture/apply pair.

manual_edits.xml records hand edits to a corpus's XML as full <S> blocks
(see claudeplans/2026-06-15-manual-edits-reproducibility-design.md):

    <MANUAL_EDITS>
      <FILE path="Amis/story01.xml">
        <S id="...">...</S>                  upsert (replace-by-id or insert)
        <S id="..." after="...">...</S>      upsert of a NEW id, placement hint
        <S id="..." action="delete"/>        delete-by-id
      </FILE>
    </MANUAL_EDITS>

Recorded <S> blocks are stored on the strip() basis: all standard-tier
FORM and all PHON removed, because standardize.py / add_phonology.py
regenerate those tiers downstream (apply runs before them).
"""
from __future__ import annotations

import copy
import subprocess
from pathlib import Path

from lxml import etree

XML_LANG_ATTR = "{http://www.w3.org/XML/1998/namespace}lang"


# ----- path resolution -------------------------------------------------------

def default_manual_file(corpora_path) -> Path:
    """Default manual-edits file: <corpus-root>/CodeAndDocs/manual_edits.xml,
    i.e. a CodeAndDocs/ sibling of the XML directory given as corpora_path."""
    return Path(corpora_path).resolve().parent / "CodeAndDocs" / "manual_edits.xml"


def changelog_path(manual_file) -> Path:
    """Human-readable changelog path next to the manual file (.md suffix)."""
    return Path(manual_file).with_suffix(".md")


# ----- the strip()/canonical basis -------------------------------------------

def strip_s(s_elem: etree._Element) -> etree._Element:
    """Deep copy of <S> reduced to manual-relevant content: every standard-tier
    FORM and every PHON removed (S/W/M), and after/action attrs dropped."""
    el = copy.deepcopy(s_elem)
    el.attrib.pop("after", None)
    el.attrib.pop("action", None)
    for form in el.findall(".//FORM[@kindOf='standard']"):
        form.getparent().remove(form)
    for phon in el.findall(".//PHON"):
        phon.getparent().remove(phon)
    return el


def canonical_s(s_elem: etree._Element) -> str:
    """Canonical (c14n) string of an <S> on the strip() basis, for equality.

    Reparsed with remove_blank_text so indentation differences don't make two
    otherwise-identical blocks compare unequal.
    """
    stripped = strip_s(s_elem)
    reparsed = etree.fromstring(
        etree.tostring(stripped), parser=etree.XMLParser(remove_blank_text=True)
    )
    return etree.tostring(reparsed, method="c14n").decode("utf-8")


def render_s(s_elem: etree._Element) -> str:
    """One-line human rendering for the changelog: original FORM + TRANSLs."""
    parts: list[str] = []
    originals = s_elem.findall("FORM[@kindOf='original']")
    if not originals:
        originals = s_elem.findall("FORM")[:1]
    for form in originals:
        if form.text and form.text.strip():
            parts.append(form.text.strip())
    for tr in s_elem.findall("TRANSL"):
        lang = tr.get(XML_LANG_ATTR, "")
        text = (tr.text or "").strip()
        if text:
            parts.append(f"[{lang}] {text}")
    return " / ".join(parts)


# ----- manual-file model -----------------------------------------------------

def new_manual_root() -> etree._Element:
    """Return a fresh <MANUAL_EDITS> root element."""
    return etree.Element("MANUAL_EDITS")


def load_manual(manual_file):
    """Parse manual_edits.xml -> <MANUAL_EDITS> root, or None if absent."""
    p = Path(manual_file)
    if not p.exists():
        return None
    return etree.parse(str(p)).getroot()


def find_file_group(root, rel_path):
    """Return the <FILE> child whose path attr equals rel_path, or None."""
    for fe in root.findall("FILE"):
        if fe.get("path") == rel_path:
            return fe
    return None


def get_or_create_file_group(root, rel_path):
    """Return the <FILE> group for rel_path, creating it if absent."""
    fe = find_file_group(root, rel_path)
    if fe is None:
        fe = etree.SubElement(root, "FILE", {"path": rel_path})
    return fe


def upsert_record(file_group, s_record):
    """Replace the <S> with matching id, or append s_record if id is new."""
    sid = s_record.get("id")
    for existing in file_group.findall("S"):
        if existing.get("id") == sid:
            file_group.replace(existing, s_record)
            return
    file_group.append(s_record)


def remove_record(file_group, sid) -> bool:
    for existing in file_group.findall("S"):
        if existing.get("id") == sid:
            file_group.remove(existing)
            return True
    return False


def write_manual(root, manual_file):
    """Serialize the manual root, dropping empty <FILE> groups IN PLACE first (the passed-in root is mutated), then pretty-print to manual_file."""
    for fe in list(root.findall("FILE")):
        if not fe.findall("S"):
            root.remove(fe)
    p = Path(manual_file)
    p.parent.mkdir(parents=True, exist_ok=True)
    tree = etree.ElementTree(root)
    etree.indent(tree, space="    ")
    tree.write(str(p), xml_declaration=True, pretty_print=True, encoding="utf-8")


# ----- git access ------------------------------------------------------------

def git_root(path):
    """Top-level of the git work tree containing path (must be a directory), or None."""
    res = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        return None
    return Path(res.stdout.strip())


def git_ref_exists(repo_root, ref) -> bool:
    """True if ref resolves to a commit in the repo at repo_root."""
    res = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--verify", "--quiet",
         f"{ref}^{{commit}}"],
        capture_output=True, text=True,
    )
    return res.returncode == 0


def git_show(repo_root, ref, rel_path):
    """Bytes of <ref>:<rel_path>, or None if not present at that ref."""
    res = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{ref}:{rel_path}"],
        capture_output=True,
    )
    if res.returncode != 0:
        return None
    return res.stdout


# ----- changelog -------------------------------------------------------------

def write_changelog(entries, path):
    """Write the human-readable per-<S> changelog grouped by file.

    entries: list of dicts with keys file, sid, action, before, after
    (before/after are rendered strings or None). Regenerated every run; an
    empty list yields a header-only file (git no-ops when unchanged).
    """
    by_file: dict[str, list] = {}
    for e in entries:
        by_file.setdefault(e["file"], []).append(e)
    lines = ["# Manual edits changelog", ""]
    for f in sorted(by_file):
        lines.append(f"## {f}")
        lines.append("")
        for e in by_file[f]:
            lines.append(f"### {e['sid']} — {e['action']}")
            if e["before"] is not None:
                lines.append(f"- before: {e['before']}")
            if e["after"] is not None:
                lines.append(f"- after:  {e['after']}")
            lines.append("")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

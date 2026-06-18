#!/usr/bin/env python3
"""remove_annotation_codes.py

Remove three families of source-side transcription markup that the
parsers fused into the published text, leaving a ``notes`` breadcrumb
on each affected sentence.

1. **Bracketed annotation codes** -- the source writes elicitation /
   annotation codes inside square brackets, both inside wordforms
   (``na=unau[u1]``, ``i-tan[TVH1][u2]-ngadah``) and inside free
   translations (``Tahail[u1][A2][A3] [TVH4]ran into ...``). The
   parsers strip brackets from forms, fusing the codes into the words
   (``naunauu1``); in TRANSLs the brackets survive verbatim.
2. **Conversation-analysis overlap markers** -- Kavalan dialogs wrap
   overlapping speech in numbered brackets (``[1aw1]``, ``[2tu ...``),
   which bracket-stripping fuses into the words (``1aw1``, ``2tu``).
3. **Example numbers** -- the Grammar sources fuse the textbook's
   example number to the final word (``'esi tapininga sua cina.25``;
   the fusion is present in the source itself).

All FORM-side removals are *source-driven*: the source JSONs are
scanned for tokens carrying the bracket markup, and only the exact
fused variants derived from them are replaced in the XML (so clean
text can never be affected). TRANSL-side bracketed codes are removed
only for codes attested in the source inventory.

Per user policy (2026-06-11), removed codes are NOT preserved verbatim;
each affected sentence's S-level original FORM gains a ``notes``
breadcrumb ("... removed; consult the NTU Formosan Corpus source").

PHON of changed elements is regenerated through the Ortho113 mapping,
gated by the pre-change original-tier witness check (_phon_regen.py).
A file is rewritten only if its unmodified tree first re-serializes
byte-identically. Idempotent (replacements stop matching; notes are
appended only once).

Usage
-----
    python remove_annotation_codes.py            # corpus XML/ by default
    python remove_annotation_codes.py --dry-run
"""

import argparse
import collections
import json
import os
import re
import sys
from pathlib import Path

import lxml.etree as etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _phon_regen import language_of, load_mappings, convert  # noqa: E402

_CODE_RE = re.compile(r"\[([A-Za-z]{0,4}\d+)\]")
_OVERLAP_TOKEN_RE = re.compile(r"^\[?\d|\d\]?$")
_NOTE_SUFFIX = "consult the NTU Formosan Corpus source"

NOTE_CODES = f"annotation codes removed; {_NOTE_SUFFIX}"
NOTE_OVERLAP = f"overlap markers removed; {_NOTE_SUFFIX}"
NOTE_EXNUM = f"example number removed; {_NOTE_SUFFIX}"


def _strip_source_punct(tok):
    """Mirror the parsers' trailing-markup stripping for comparison."""
    return tok.rstrip("\\_,").rstrip()


def build_maps(codedocs_dir):
    """Scan source JSONs; return (token_map, code_set).

    token_map: fused-XML-token -> (cleaned token, note category)
    code_set: bracketed code strings attested in source (for TRANSL).
    """
    token_map = {}
    codes = set()

    def variants(tok):
        """XML token variants the parsers can produce from a source token.

        Covers the parsers' transformations independently and combined:
        bracket removal, trailing source markup (``\\``, ``_``, ``,``),
        sentence punctuation kept or dropped, and the S-level ori
        cleaning that strips ``=``/``-``/``.`` inside words.
        """
        base = tok.replace("[", "").replace("]", "")
        seeds = {base, _strip_source_punct(base)}
        for v in list(seeds):
            seeds.add(v.rstrip(".,!?"))
        out = set(seeds)
        for v in list(seeds):
            out.add(v.replace("=", "").replace("-", ""))
            out.add(v.replace("=", "").replace("-", "").replace(".", ""))
            out.add(v.replace("==", ""))
        # leading overlap digits are stripped by some pipeline paths
        for v in list(out):
            out.add(re.sub(r"^\d+", "", v))
        return {v for v in out if v}

    def add(tok):
        if "[" not in tok and "]" not in tok:
            return
        # classify on a probe stripped of trailing source markup
        # (tokens like 'yau1],\\' carry it AFTER the bracket)
        probe = tok.rstrip("\\").rstrip("_").rstrip(".,!?")
        if _CODE_RE.search(probe):
            for c in _CODE_RE.findall(probe):
                codes.add(c)
            cleaned = _CODE_RE.sub("", probe).replace("[", "").replace("]", "")
            note = NOTE_CODES
        elif _OVERLAP_TOKEN_RE.search(probe.strip("[]")) or re.match(r"^\[\d", probe) \
                or re.search(r"\d\]$", probe):
            inner = probe.replace("[", "").replace("]", "")
            cleaned = re.sub(r"^\d+", "", re.sub(r"\d+$", "", inner))
            note = NOTE_OVERLAP
        else:
            return
        cleaned = cleaned.strip("-=")
        if not re.search(r"[^\W\d]", cleaned, re.UNICODE):
            return  # nothing recoverable (marker-only token)
        cleaned_variants = variants(cleaned)
        for v in variants(tok):
            if not re.search(r"\d", v):
                continue
            # pair each residue variant with the cleaned variant produced
            # by the same transformation chain; fall back to the punct-
            # preserving pairing (residue keeps '.' -> cleaned keeps '.')
            tail = v[-1] if v and v[-1] in ".,!?" else ""
            target = None
            for cv in cleaned_variants:
                if tail and cv.endswith(tail):
                    target = cv
                    break
                if not tail and not (cv and cv[-1] in ".,!?"):
                    target = cv if target is None or len(cv) > len(target) else target
            if target is None and tail:
                target = cleaned + tail
            if target and v != target:
                token_map[v] = (target, note)

    for sub in ("grammar", "sentence", "story"):
        root = os.path.join(codedocs_dir, sub)
        if not os.path.isdir(root):
            continue
        for lang_dir in os.listdir(root):
            full = os.path.join(root, lang_dir)
            if not os.path.isdir(full):
                continue
            for fn in os.listdir(full):
                if not fn.endswith(".json"):
                    continue
                try:
                    data = json.load(open(os.path.join(full, fn)))
                except Exception:
                    continue
                for item in data.get("glosses", []):
                    payload = item[1]
                    for tok in payload.get("ori", []) or []:
                        if isinstance(tok, str):
                            add(tok)
                            # multi-word overlap spans ("[1sunis a yau1]")
                            # arrive as one string; map the pieces too
                            if " " in tok:
                                for piece in tok.split(" "):
                                    add(piece)
                    for trip in payload.get("gloss", []) or []:
                        if isinstance(trip, list) and trip and isinstance(trip[0], str):
                            add(trip[0])
                            if " " in trip[0]:
                                for piece in trip[0].split(" "):
                                    add(piece)
                            # morpheme pieces: M-level FORMs are the wordform
                            # split on -/=, so codes fuse per piece too
                            # (i-tan[TVH1][u2]-ngadah -> M piece tanTVH1u2)
                            for piece in re.split(r"[-=]", trip[0]):
                                if "[" in piece or "]" in piece:
                                    add(piece)
                    # codes can also appear only in the free translations
                    # (e.g. "#e Tahail[u1][A2][A3] [TVH4]ran into ...")
                    for free in payload.get("free", []) or []:
                        if isinstance(free, str):
                            for c in _CODE_RE.findall(free):
                                codes.add(c)
    return token_map, codes


def serialize(tree):
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def _tier(el, tag, kind):
    for c in el.findall(tag):
        if c.get("kindOf") == kind:
            return c
    return None


def _append_note(s_el, note, stats):
    fe = _tier(s_el, "FORM", "original")
    if fe is None:
        return
    cur = fe.get("notes")
    if cur:
        if note in cur:
            return
        fe.set("notes", f"{cur}; {note}")
    else:
        fe.set("notes", note)
    stats["notes added"] += 1


def fix_text(text, token_map):
    """Replace fused tokens; return (new_text, notes_triggered)."""
    if not text:
        return text, set()
    out, notes = [], set()
    for tok in text.split(" "):
        if tok in token_map:
            rep, note = token_map[tok]
            notes.add(note)
            out.append(rep)
        else:
            out.append(tok)
    return " ".join(out), notes


def strip_transl_codes(text, codes):
    """Remove bracketed/parenthesized attested codes from TRANSL text."""
    if not text or not ("[" in text or "(" in text):
        return text, False
    new = text
    for c in codes:
        new = new.replace(f"[{c}]", "").replace(f"({c})", "")
    if new == text:
        return text, False
    new = re.sub(r"  +", " ", new).strip()
    return new, True


_EXNUM_RE = re.compile(r"^(.*[^\d.]\.)(\d+)$")


def process_file(path, token_map, codes, is_grammar, dry_run, stats):
    original = open(path, "rb").read()
    tree = etree.parse(path)
    if serialize(tree) != original:
        stats["file skipped: round-trip guard"] += 1
        return False
    root = tree.getroot()
    mp = load_mappings(language_of(root))
    modified = False
    for s in root.iter("S"):
        s_notes = set()
        changed_parents = {}
        for el in [s] + s.findall(".//W") + s.findall(".//M"):
            forms = [c for c in el.findall("FORM")]
            el_changed = False
            for f in forms:
                if not (f.text or "").strip():
                    continue
                new, notes = fix_text(f.text, token_map)
                if is_grammar:
                    m = _EXNUM_RE.match(new.strip())
                    if m:
                        new = m.group(1)
                        notes = notes | {NOTE_EXNUM}
                if new != (f.text or "") and new.strip():
                    if el not in changed_parents:
                        of, op = _tier(el, "FORM", "original"), _tier(el, "PHON", "original")
                        changed_parents[el] = (
                            mp is not None and of is not None and op is not None
                            and (of.text or "").strip() and (op.text or "").strip()
                            and convert(of.text, mp) == op.text)
                    f.text = new
                    s_notes |= notes
                    stats[f"FORM cleaned ({el.tag})"] += 1
                    el_changed = True
            for t in el.findall("TRANSL"):
                new, hit = strip_transl_codes(t.text, codes)
                if hit and new:
                    t.text = new
                    s_notes.add(NOTE_CODES)
                    stats["TRANSL cleaned"] += 1
                    modified = True
            if el_changed:
                modified = True
        for el, witness in changed_parents.items():
            if not witness:
                stats["PHON left (witness failed/absent)"] += 1
                continue
            for kind in ("original", "standard"):
                fe, pe = _tier(el, "FORM", kind), _tier(el, "PHON", kind)
                if fe is not None and pe is not None and (fe.text or "").strip():
                    newp = convert(fe.text, mp)
                    if newp != pe.text:
                        pe.text = newp
                        stats["PHON regenerated"] += 1
        for note in sorted(s_notes):
            _append_note(s, note, stats)
            modified = True
    if modified and not dry_run:
        with open(path, "wb") as f:
            f.write(serialize(tree))
    return modified


def main():
    corpus = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml_dir", default=str(corpus / "XML"))
    ap.add_argument("--source_dir", default=str(corpus / "CodeAndDocs"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    token_map, codes = build_maps(args.source_dir)
    print(f"source inventory: {len(token_map)} fused-token mappings, "
          f"{len(codes)} bracketed codes")
    stats = collections.Counter()
    files = 0
    for dirpath, _, filenames in os.walk(args.xml_dir):
        for fn in sorted(filenames):
            if not fn.endswith(".xml"):
                continue
            path = os.path.join(dirpath, fn)
            is_grammar = f"{os.sep}Grammar{os.sep}" in path
            if process_file(path, token_map, codes, is_grammar,
                            args.dry_run, stats):
                files += 1
                print(f"  modified: {fn}")
    print(f"\nfiles {'that would be ' if args.dry_run else ''}modified: {files}")
    for k, v in stats.most_common():
        print(f"  {v:5d}  {k}")


if __name__ == "__main__":
    main()

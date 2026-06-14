#!/usr/bin/env python3
"""expand_word_level_alternatives.py

Expand a sentence whose word offers *whole-word* slash alternatives that
the parser mis-segmented at the morpheme tier.

Background
----------
Unlike the morpheme-scoped alternations handled by
``expand_slash_alternatives.py`` (step 16), a few words list several
complete alternative words separated by ``/`` and each alternative is
itself multi-morpheme, e.g. Rukai ``20200528-FW-Yongfu_S_7``::

    W FORM : ma-lrigi/ma-elre-elrenge/ma-adraw
    gloss  : STAT.RLS-be.smart/STAT.RLS-RED-be.tall/STAT.RLS-be.big
             狀態.實現.聰明/狀態.實現-重疊-高/狀態.實現-大
    free   : "Laucu is smart/tall/big."   (3-way; truncated to "smart" in XML)

The parser split on ``-`` and ``/`` together, so the morpheme tier is
nonsense (``lrigi/ma``, ``elrenge/ma``) and its slash count (2) disagrees
with the word-level count (3) -- which is exactly why step 16 refuses it.
But the *word-level* FORM/PHON/gloss split cleanly into N on ``/``, and
each alternative re-segments cleanly on ``-``, so the sentence can be
rebuilt one alternative per S.

Because these cases need per-sentence judgement (the published free
translation was truncated and must be restored; an occasional source typo
in the gloss must be repaired so the morphemes align), each is described
explicitly in ``CONFIG`` rather than inferred. Everything else -- the
``/`` split, the ``-`` re-segmentation, PHON (taken from the word's own
slashed PHON, no orthography mapping needed) -- is mechanical.

For each configured sentence the original element becomes alternative 1
and alternatives 2..N are inserted after it (id suffix ``-alt2``..``-altN``,
descendant ids rewritten). The mis-segmented morphemes are rebuilt from
each alternative's own FORM/PHON/gloss; AUDIO (if any) stays on
alternative 1.

A file is rewritten only if its unmodified tree first re-serializes
byte-identically (lxml, xml declaration, UTF-8). Idempotent (the outputs
contain no slash to re-expand).

Usage
-----
    python expand_word_level_alternatives.py
    python expand_word_level_alternatives.py --dry-run
"""

import argparse
import collections
import copy
import os
from pathlib import Path

import lxml.etree as etree

_XLANG = "{http://www.w3.org/XML/1998/namespace}lang"

# Per-sentence descriptions. free_translations: one {zho,eng} per
# alternative, in document order (restores the source's slash-separated
# free translation, which the published XML truncated to the first).
# gloss_fixes: literal substring replacements applied to a word-level gloss
# alternative *after* the '/' split, to repair source typos that would
# otherwise break '-' alignment.
CONFIG = [
    {
        "file": "Sentences/Rukai/Rukai.xml",
        "sid": "20200528-FW-Yongfu_S_7",
        "free_translations": [
            {"zho": "Laucu很聰明", "eng": "Laucu is smart"},
            {"zho": "Laucu很高", "eng": "Laucu is tall"},
            {"zho": "Laucu很大", "eng": "Laucu is big"},
        ],
        # source wrote 狀態.實現.聰明 with a '.' where the morpheme boundary
        # '-' was meant (cf. the sibling 狀態.實現-大); repair so STAT.RLS
        # and be.smart align as two morphemes.
        "gloss_fixes": {"狀態.實現.聰明": "狀態.實現-聰明"},
    },
]


def _lang(t):
    return t.get(_XLANG) or t.get("lang")


def _child(el, tag, attr, val):
    return next((c for c in el.findall(tag) if c.get(attr) == val), None)


def _split(text, n):
    parts = (text or "").split("/")
    if len(parts) != n:
        raise AssertionError(f"expected {n} '/'-parts in {text!r}, got {len(parts)}")
    return parts


def _rebuild_morphemes(w, fo, fs, po, ps, ge, gz, wid):
    """Reuse existing <M> elements as formatting templates; rebuild k of them."""
    pieces = [fo.split("-"), fs.split("-"), po.split("-"),
              ps.split("-"), ge.split("-"), gz.split("-")]
    k = len(pieces[0])
    if any(len(p) != k for p in pieces):
        raise AssertionError(f"morpheme counts disagree for {wid}: "
                             f"{[len(p) for p in pieces]}")
    templates = w.findall("M")
    inter_tail, last_tail = templates[0].tail, templates[-1].tail
    keep = templates[:k]
    for extra in templates[k:]:
        w.remove(extra)
    fo_p, fs_p, po_p, ps_p, ge_p, gz_p = pieces
    for j, m in enumerate(keep):
        _child(m, "FORM", "kindOf", "original").text = fo_p[j]
        _child(m, "FORM", "kindOf", "standard").text = fs_p[j]
        _child(m, "PHON", "kindOf", "original").text = po_p[j]
        _child(m, "PHON", "kindOf", "standard").text = ps_p[j]
        _child(m, "TRANSL", _XLANG, "eng").text = ge_p[j]
        _child(m, "TRANSL", _XLANG, "zho").text = gz_p[j]
        m.set("id", f"{wid}M{j + 1}")
        m.tail = inter_tail if j < k - 1 else last_tail


def _retarget(elem, old, new):
    for el in elem.iter():
        cid = el.get("id")
        if cid and cid.startswith(old):
            el.set("id", new + cid[len(old):])


def _apply_alt(s, w_index, i, N, splits, free, sform_tokens, sphon_tokens):
    w = s.findall("W")[w_index]
    wid = w.get("id")
    fo, fs, po, ps, ge, gz = (splits[k][i] for k in
                              ("fo", "fs", "po", "ps", "ge", "gz"))
    _child(w, "FORM", "kindOf", "original").text = fo
    _child(w, "FORM", "kindOf", "standard").text = fs
    _child(w, "PHON", "kindOf", "original").text = po
    _child(w, "PHON", "kindOf", "standard").text = ps
    _child(w, "TRANSL", _XLANG, "eng").text = ge
    _child(w, "TRANSL", _XLANG, "zho").text = gz
    _rebuild_morphemes(w, fo, fs, po, ps, ge, gz, wid)
    # sentence-level surface form: swap the slash token for this alternative's
    f_o = _child(s, "FORM", "kindOf", "original")
    f_s = _child(s, "FORM", "kindOf", "standard")
    p_o = _child(s, "PHON", "kindOf", "original")
    p_s = _child(s, "PHON", "kindOf", "standard")
    f_o.text = f_o.text.replace(sform_tokens["o"], fo.replace("-", ""))
    f_s.text = f_s.text.replace(sform_tokens["s"], fs.replace("-", ""))
    p_o.text = p_o.text.replace(sphon_tokens["o"], po.replace("-", ""))
    p_s.text = p_s.text.replace(sphon_tokens["s"], ps.replace("-", ""))
    _child(s, "TRANSL", _XLANG, "zho").text = free[i]["zho"]
    _child(s, "TRANSL", _XLANG, "eng").text = free[i]["eng"]


def serialize(tree):
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def _slash_in_forms(elem):
    return any(c.tag in ("FORM", "PHON") and c.text and "/" in c.text
               for c in elem.iter())


def process_file(path, entries, dry_run, stats):
    original = open(path, "rb").read()
    tree = etree.parse(path)
    if serialize(tree) != original:
        stats["file skipped: round-trip guard"] += 1
        return False
    root = tree.getroot()
    by_sid = {s.get("id"): s for s in root.iter("S")}
    modified = False
    for cfg in entries:
        s = by_sid.get(cfg["sid"])
        if s is None or _slash_in_forms(s) is False:
            continue
        ws = s.findall("W")
        w_index = next(i for i, w in enumerate(ws)
                       if "/" in (_child(w, "FORM", "kindOf", "original").text or ""))
        w = ws[w_index]
        N = len((_child(w, "FORM", "kindOf", "original").text or "").split("/"))
        free = cfg["free_translations"]
        if len(free) != N:
            raise AssertionError(f"{cfg['sid']}: {len(free)} translations for N={N}")

        def gloss_parts(lang):
            raw = _split(_child(w, "TRANSL", _XLANG, lang).text, N)
            return [cfg.get("gloss_fixes", {}).get(p, p) for p in raw]

        splits = {
            "fo": _split(_child(w, "FORM", "kindOf", "original").text, N),
            "fs": _split(_child(w, "FORM", "kindOf", "standard").text, N),
            "po": _split(_child(w, "PHON", "kindOf", "original").text, N),
            "ps": _split(_child(w, "PHON", "kindOf", "standard").text, N),
            "ge": gloss_parts("eng"),
            "gz": gloss_parts("zho"),
        }
        sform_tokens = {
            "o": _child(w, "FORM", "kindOf", "original").text.replace("-", ""),
            "s": _child(w, "FORM", "kindOf", "standard").text.replace("-", ""),
        }
        sphon_tokens = {
            "o": _child(w, "PHON", "kindOf", "original").text.replace("-", ""),
            "s": _child(w, "PHON", "kindOf", "standard").text.replace("-", ""),
        }
        parent = s.getparent()
        clones = []
        for i in range(1, N):
            clone = copy.deepcopy(s)
            for au in clone.findall(".//AUDIO"):
                au.getparent().remove(au)
            _retarget(clone, cfg["sid"], f"{cfg['sid']}-alt{i + 1}")
            _apply_alt(clone, w_index, i, N, splits, free, sform_tokens, sphon_tokens)
            clones.append(clone)
        _apply_alt(s, w_index, 0, N, splits, free, sform_tokens, sphon_tokens)
        for off, clone in enumerate(clones, start=1):
            parent.insert(parent.index(s) + off, clone)
        if _slash_in_forms(s) or any(_slash_in_forms(c) for c in clones):
            raise AssertionError(f"residual slash after expand in {cfg['sid']}")
        stats["sentences expanded"] += 1
        stats[f"readings produced (N={N})"] += N
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
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    by_file = collections.defaultdict(list)
    for cfg in CONFIG:
        by_file[cfg["file"]].append(cfg)

    stats = collections.Counter()
    files = 0
    for rel, entries in by_file.items():
        path = os.path.join(args.xml_dir, rel)
        if process_file(path, entries, args.dry_run, stats):
            files += 1
            print(f"  modified: {os.path.basename(path)}")
    print(f"\nfiles {'that would be ' if args.dry_run else ''}modified: {files}")
    for k, v in stats.most_common():
        print(f"  {v:5d}  {k}")


if __name__ == "__main__":
    main()

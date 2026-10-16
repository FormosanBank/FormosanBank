#!/usr/bin/env python3
"""Apply the maintainer's verdicts on sentences that share a FORM.

After the shared dedup, what is left are groups where two published sentences
have the same FORM and DIFFERENT glosses. The dedup cannot touch them - it
requires the gloss to match, so that homophones survive - and no rule can
settle them, because only a reader knows whether `dadu` "leader" and `dadu`
"correct" are two words or one word glossed twice.

So they were put on a review page and ruled one at a time. This applies those
rulings. Each is one of:

  keep-both     two words that happen to be spelt alike. Nothing to do; the
                entry stands as published.
  keep-first    one word, and the two glosses say the same thing, so only one
  keep-second   belongs in the corpus. The maintainer named which reading to
  keep-either   publish, or said it did not matter - `keep-either` keeps the
                first by (file, S id), which is the rule the shared dedup uses.
  merge-alt     one word whose two glosses each add something. One S, the other
                glosses joining it as ver="alt" TRANSLs (POL-025).
  merge-notes   as merge-alt, but the loser's parenthetical is an editorial
                remark rather than a translation, so it becomes a note on the
                survivor and the glosses then merge outright.
  delete-both   neither belongs in the corpus.

A ruling records the S ids and the glosses it was given on. If the build no
longer matches - a parse fix closed the group, or changed a gloss - the ruling
is REFUSED and reported rather than applied to sentences nobody looked at.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

from lxml import etree

RULINGS = Path(__file__).resolve().parent / "same-form-rulings.json"


def _gloss(s) -> list[str]:
    return [" ".join((t.text or "").split()) for t in s.findall("TRANSL")]


def _form(s) -> str:
    node = s.find('FORM[@kindOf="standard"]')
    if node is None or not (node.text or "").strip():
        node = s.find('FORM[@kindOf="original"]')
    return " ".join((node.text or "").split()) if node is not None else ""


def collect(root: Path):
    """Every S in the tree, grouped by FORM, in the review page's order."""
    trees: dict[Path, etree._ElementTree] = {}
    groups: dict[str, list] = collections.defaultdict(list)
    for path in sorted(root.glob("*.xml")):
        tree = etree.parse(str(path))
        trees[path] = tree
        for s in tree.getroot().findall("S"):
            key = _form(s)
            if key:
                groups[key].append((path, s))
    return trees, groups


def apply_ruling(ruling, members) -> tuple[str, set]:
    """Return (what happened, the set of paths that changed)."""
    action = ruling["action"]
    touched = set()
    if action == "keep-both":
        return "kept both", touched

    if action == "delete-both":
        losers = list(members)
    elif action in ("keep-first", "keep-either"):
        losers = members[1:]
    elif action == "keep-second":
        losers = [members[0]] + members[2:]
    elif action in ("merge-alt", "merge-notes"):
        losers = members[1:]
    else:
        raise SystemExit(f"unknown action {action!r} on {ruling['form']!r}")

    if action in ("merge-alt", "merge-notes"):
        keep_path, keep = members[0]
        if action == "merge-notes":
            # The maintainer's words on p.359 `da-rima matilaw`, where one
            # side reads `5,000 (function of /da/- unknown)` and the other
            # just `5,000`: "\"(function of /da/- unknown)\" should got into
            # a note. And then they merge, no need for ver=alt. Just combine
            # the notes."
            #
            # The parenthetical is the whole of the difference, and it is an
            # editorial remark rather than any part of the translation. Moving
            # it off the SURVIVOR leaves two identical glosses, so nothing
            # becomes a variant of anything.
            for transl in keep.findall("TRANSL"):
                trimmed, note = _split_trailing_parenthetical(
                    " ".join((transl.text or "").split()))
                if note:
                    transl.text = trimmed
                    _add_note(transl, note)
        have = set(_gloss(keep))
        for path, s in losers:
            for transl in s.findall("TRANSL"):
                text = " ".join((transl.text or "").split())
                if not text or text in have:
                    continue
                moved = etree.fromstring(etree.tostring(transl))
                moved.set("ver", "alt")
                keep.append(moved)
                have.add(text)
            touched.add(keep_path)

    for path, s in losers:
        s.getparent().remove(s)
        touched.add(path)
    return f"{action}: removed {len(losers)}", touched


def _split_trailing_parenthetical(text: str) -> tuple[str, str]:
    if text.endswith(")") and "(" in text:
        head, _, tail = text.rpartition("(")
        return head.strip(), tail[:-1].strip()
    return text, ""


def _add_note(node, note: str) -> None:
    if node is None or not note:
        return
    existing = node.get("notes")
    node.set("notes", f"{existing}; {note}" if existing else note)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, required=True)
    parser.add_argument("--rulings", type=Path, default=RULINGS)
    args = parser.parse_args()

    payload = json.loads(args.rulings.read_text(encoding="utf-8"))
    trees, groups = collect(args.path)

    applied = collections.Counter()
    refused = []
    already = 0
    changed: set = set()
    for ruling in payload["rulings"]:
        members = groups.get(ruling["form"], [])
        ids = [s.get("id") for _p, s in members]
        glosses = [_gloss(s) for _p, s in members]
        if glosses != ruling["glosses"]:
            # The GLOSSES are the identity, not the ids. An S id carries its
            # sense number within the page, so removing any sense renumbers
            # every later one on that page - and a verdict must not stop
            # applying because a neighbour three senses up was dropped. The
            # ids stay in the file as the audit trail of what was on screen.
            if len(members) < len(ruling["members"]):
                # Fewer sentences than were ruled on: this verdict has already
                # been carried out, here or by a rule upstream. Re-running the
                # step on a built tree is a normal thing to do and is not a
                # problem, so it is counted, not shouted about.
                already += 1
            else:
                refused.append((ruling["form"], glosses, ruling["glosses"]))
            continue
        what, touched = apply_ruling(ruling, members)
        applied[ruling["action"]] += 1
        changed |= touched

    for path in sorted(changed):
        trees[path].write(str(path), pretty_print=False, encoding="utf-8",
                          xml_declaration=True)

    # The retired verdicts are expectations now, not instructions: a rule
    # settles each of these, and if one comes back it is at minimum worth
    # flagging (maintainer, 2026-09-11).
    regressed = []
    for ruling in payload.get("settled_by_a_rule", []):
        members = groups.get(ruling["form"], [])
        if len(members) > 1:
            regressed.append((ruling["form"], ruling["action"],
                              ruling.get("retired_because", "")))

    total = sum(applied.values())
    print(f"apply_same_form_rulings: {total} of {len(payload['rulings'])} applied "
          f"{dict(applied)}"
          + (f"; {already} already settled" if already else ""))
    if refused:
        print(f"  REFUSED {len(refused)} - the build no longer matches the "
              f"state these were ruled on:", file=sys.stderr)
        for form, now, then in refused:
            print(f"    {form!r}\n      ruled on {then}\n      build has {now}",
                  file=sys.stderr)
        print("  A group that has collapsed to one sentence is no longer a "
              "question and needs no verdict; anything else wants a look.",
              file=sys.stderr)
    if regressed:
        print(f"  {len(regressed)} retired verdict(s) came BACK - a rule that was "
              f"settling these has stopped:", file=sys.stderr)
        for form, action, because in regressed:
            print(f"    {form!r} wanted {action}; {because}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

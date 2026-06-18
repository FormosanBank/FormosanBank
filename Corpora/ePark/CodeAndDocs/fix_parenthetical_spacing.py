#!/usr/bin/env python3
"""
Add the missing space around inline parentheticals in FORM and PHON elements.

The ePark source data frequently runs a word straight into a following
parenthetical gloss/alternate with no separating space, e.g.

    manokos(manakboz)        ->  manokos (manakboz)
    madagdag(apnezak) o ...  ->  madagdag (apnezak) o ...

This is present verbatim in the original ePark CSV/XML source (it is NOT
introduced by our processing), so it is corrected here as a deterministic,
reproducible pipeline step rather than by hand-editing the published XML.

Scope and rules (mirrors fix_question_mark_spacing.py):
  * Operates only on FORM and PHON element text. TRANSL is left untouched:
    the Chinese translations use parentheses under CJK typographic
    conventions (e.g. "Dahu(拉荷)") where a space is not wanted.
  * Adds one space before "(" when the preceding character is not already
    whitespace and not itself "(" (so "((kois)" -> " ((kois)", the source's
    own double-paren typo is preserved, only the word boundary is spaced).
  * Adds one space after ")" when the following character is a letter/digit
    (not whitespace and not closing punctuation), e.g. ")o" -> ") o".
  * Never inserts spaces *inside* the parentheses, and never touches a "("
    at the very start of the text.

Run AFTER fix_question_mark_spacing.py in the pipeline. Default is a dry run
that prints every proposed change; pass --apply to write files in place.
"""

import re
from pathlib import Path

from lxml import etree

# Add a space before "(" when the previous char is neither whitespace nor "(".
_SPACE_BEFORE_OPEN = re.compile(r"(?<=[^\s(])\(")
# Add a space after ")" when the next char is a "word" char (letter or digit).
# Excludes whitespace and closing punctuation so "(gloss)." / "(a)(b)" are safe.
_SPACE_AFTER_CLOSE = re.compile(r"\)(?=[^\s).,;:!?\"'’\]\}])")


def fix_parenthetical_spacing(text):
    """Insert the missing word/parenthetical boundary spaces. Idempotent."""
    if not text:
        return text
    text = _SPACE_BEFORE_OPEN.sub(" (", text)
    text = _SPACE_AFTER_CLOSE.sub(") ", text)
    return text


def process_xml_file(file_path, apply_changes):
    """Fix one file. Returns (n_changes, list_of_(before, after))."""
    try:
        # Match clean_xml.py's lxml parse/serialize exactly so re-writing a file
        # reproduces its existing formatting; the diff then shows only the text
        # edits below, not a whole-file reserialization (UTF-8 casing, self-close
        # spacing, indentation).
        tree = etree.parse(str(file_path))
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return 0, []

    changed = []
    for s in root.findall("S"):
        # Skip word-segmented (glossed) sentences. There the parenthetical is a
        # single word token in BOTH the S-level FORM and the W tier (e.g. one
        # <W> "apnezak(pepnezak)"), so they stay aligned. Inserting a space in
        # the S-FORM would split it into two whitespace tokens while the W tier
        # keeps one, breaking FORM<->W count alignment (validate_glosses V060).
        # These cases (all in jiu_jie_jiao_cai_nine_level_materials) are left
        # as-is on purpose; see README.
        if s.find("W") is not None:
            continue
        for element in s.iter():
            if element.tag in ("FORM", "PHON") and element.text:
                before = element.text
                after = fix_parenthetical_spacing(before)
                if before != after:
                    changed.append((before, after))
                    if apply_changes:
                        element.text = after

    if changed and apply_changes:
        tree.write(str(file_path), xml_declaration=True, pretty_print=True, encoding="utf-8")
    return len(changed), changed


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Add missing spaces around inline parentheticals in FORM/PHON."
    )
    parser.add_argument(
        "--final_xml_dir", default="Final_XML",
        help="Directory of XML files to process (default: Final_XML)",
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write changes in place. Without this flag, only previews them.",
    )
    parser.add_argument(
        "--show", type=int, default=20,
        help="Max number of before/after examples to print (default: 20)",
    )
    args = parser.parse_args()

    root_dir = Path(args.final_xml_dir)
    if not root_dir.exists():
        print(f"Error: Directory {root_dir} does not exist")
        return

    xml_files = sorted(root_dir.rglob("*.xml"))
    print(f"{'APPLY' if args.apply else 'DRY RUN'}: scanning {len(xml_files)} XML files in {root_dir}")

    total_changes = 0
    files_with_changes = 0
    shown = 0
    for xml_file in xml_files:
        n, changed = process_xml_file(xml_file, args.apply)
        if n:
            files_with_changes += 1
            total_changes += n
            for before, after in changed:
                if shown < args.show:
                    print(f"  [{xml_file.name}]")
                    print(f"    - {before}")
                    print(f"    + {after}")
                    shown += 1

    print("\nSummary:")
    print(f"  Files changed: {files_with_changes}/{len(xml_files)}")
    print(f"  FORM/PHON edits: {total_changes}")
    if not args.apply:
        print("  (dry run — no files written; re-run with --apply to write)")


if __name__ == "__main__":
    main()

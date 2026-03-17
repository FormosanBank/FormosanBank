#!/usr/bin/env python3
"""
find_duplicate_sentences.py

Check every <FORM kindOf="..."> that is a direct child of an <S> in a
chosen source corpus and find matching sentences in all other corpora under
the Corpora directory for the same language.

Output: a CSV with columns
    source_id, corpus, xml_file, match_id
"""

import argparse
import csv
import os
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


def extract_forms(xml_path: str, kind_of: str = "standard") -> list[tuple[str, str]]:
    """
    Return [(sentence_id, form_text), ...] for every <S> that has a direct-child
    <FORM kindOf=kind_of>.  Skips silently on parse errors.
    """
    results = []
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for s in root.iter("S"):
            sid = s.get("id", "")
            for form in s:          # only direct children
                if form.tag == "FORM" and form.get("kindOf") == kind_of:
                    text = (form.text or "").strip()
                    if text:
                        results.append((sid, text))
                    break           # at most one matching FORM per S
    except ET.ParseError as e:
        print(f"  WARNING: could not parse {xml_path}: {e}", file=sys.stderr)
    return results

# Keep the old name as an alias so the test file doesn't need updating
extract_standard_forms = lambda xml_path: extract_forms(xml_path, "standard")


def corpus_name(xml_path: str, corpora_root: str) -> str:
    """Derive the top-level corpus folder name from a full path."""
    rel = os.path.relpath(xml_path, corpora_root)
    return rel.split(os.sep)[0]


def main():
    parser = argparse.ArgumentParser(
        description="Find sentences from one corpus that are duplicated in others.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # Compare Glosbe Amis against all other Amis corpora (standard forms, default)
  python find_duplicate_sentences.py --source-corpus Glosbe --language Amis

  # Compare ePark Paiwan against all other Paiwan corpora
  python find_duplicate_sentences.py --source-corpus ePark --language Paiwan

  # Use original rather than standard forms
  python find_duplicate_sentences.py --source-corpus Glosbe --language Amis --kind-of original

  # Point directly at a specific XML file
  python find_duplicate_sentences.py --source-xml Corpora/Glosbe/XML/Amis/amis_glosbe.xml --language Amis
        """
    )
    parser.add_argument(
        "--corpora", default="Corpora",
        help="Path to the Corpora directory (default: Corpora)"
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--source-corpus",
        help="Name of the source corpus folder inside Corpora/ (e.g. Glosbe, ePark)."
    )
    source_group.add_argument(
        "--source-xml",
        help="Path to a specific source XML file to compare against all others."
    )
    parser.add_argument(
        "--language", required=True,
        help="Language folder name to compare within (e.g. Amis, Paiwan)."
    )
    parser.add_argument(
        "--kind-of", default="standard", dest="kind_of",
        help="Value of the kindOf attribute on <FORM> elements to compare (default: standard)."
    )
    parser.add_argument(
        "--output", default=None,
        help="Output CSV path (default: <source_corpus>_<language>_duplicates.csv)"
    )
    args = parser.parse_args()

    corpora_root = os.path.abspath(args.corpora)
    language = args.language

    # ------------------------------------------------------------------ #
    # Resolve source XML file(s)                                          #
    # ------------------------------------------------------------------ #
    if args.source_xml:
        source_xml_files = [os.path.abspath(args.source_xml)]
        source_corpus_name = os.path.basename(os.path.dirname(source_xml_files[0]))
        source_dir = os.path.dirname(source_xml_files[0])
    else:
        source_corpus_name = args.source_corpus
        source_dir = os.path.join(corpora_root, source_corpus_name, "XML", language)
        if not os.path.isdir(source_dir):
            sys.exit(f"ERROR: source directory not found: {source_dir}")
        source_xml_files = [
            os.path.join(source_dir, f)
            for f in os.listdir(source_dir)
            if f.endswith(".xml")
        ]
        if not source_xml_files:
            sys.exit(f"ERROR: no XML files found in {source_dir}")

    output_path = os.path.abspath(
        args.output or f"{source_corpus_name}_{language}_duplicates.csv"
    )

    # ------------------------------------------------------------------ #
    # Step 1: load all source sentences into a lookup dict text -> [ids]  #
    # ------------------------------------------------------------------ #
    print(f"Loading source sentences from {source_dir} ({args.kind_of} forms) …")
    source_index: dict[str, list[str]] = defaultdict(list)
    total_source = 0
    for xml_path in source_xml_files:
        for sid, text in extract_forms(xml_path, args.kind_of):
            source_index[text.lower()].append(sid)
            total_source += 1
    print(f"  {total_source} sentences indexed.")

    # ------------------------------------------------------------------ #
    # Step 2: collect every other */XML/<language>/*.xml                  #
    # ------------------------------------------------------------------ #
    print(f"Collecting XML/{language} files under {corpora_root} …")
    source_xml_set = set(os.path.normpath(p) for p in source_xml_files)
    other_xml_files = []
    for root_dir, dirs, files in os.walk(corpora_root):
        for fname in files:
            if not fname.endswith(".xml"):
                continue
            full = os.path.join(root_dir, fname)
            if os.path.normpath(full) in source_xml_set:
                continue        # skip the source file(s) themselves
            parts = Path(full).parts
            if language in parts:
                other_xml_files.append(full)

    print(f"  {len(other_xml_files)} files to scan.")

    # ------------------------------------------------------------------ #
    # Step 3: scan each file and record matches                           #
    # ------------------------------------------------------------------ #
    matches = []   # list of (source_id, corpus, xml_file, match_id)

    for i, xml_path in enumerate(sorted(other_xml_files), 1):
        if i % 200 == 0 or i == len(other_xml_files):
            print(f"  Scanning file {i}/{len(other_xml_files)} …")
        forms = extract_forms(xml_path, args.kind_of)
        if not forms:
            continue
        corp = corpus_name(xml_path, corpora_root)
        rel_path = os.path.relpath(xml_path, corpora_root)
        for sid, text in forms:
            key = text.lower()
            if key in source_index:
                for source_id in source_index[key]:
                    matches.append((source_id, corp, rel_path, sid))

    print(f"\n{len(matches)} duplicate sentence(s) found.")

    # ------------------------------------------------------------------ #
    # Step 4: write CSV                                                    #
    # ------------------------------------------------------------------ #
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source_id", "corpus", "xml_file", "match_id"])
        def sort_key(row):
            sid = row[0]
            parts = sid.rsplit("_", 1)
            try:
                return (parts[0], int(parts[1]))
            except (IndexError, ValueError):
                return (sid, 0)
        for row in sorted(matches, key=sort_key):
            writer.writerow(row)

    print(f"Log written to {output_path}")


if __name__ == "__main__":
    main()

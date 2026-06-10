"""Delete Wikipedia XML files whose <FORM> elements are all empty.

Some scraped Wikipedia articles produce XMLs with no usable Formosan content:
either the article was a "this page does not exist" placeholder, or the
text was entirely stripped by earlier cleaning steps (e.g. Chinese-only
content removed by remove_other_langs.py). Such files have FORM tags
present but with no text. They survive validate_xml.py only as V017 errors
and contribute nothing to the corpus.

This script walks an XML directory and deletes any .xml file in which
EVERY <FORM> element's text is empty (after stripping whitespace).
Files that have at least one non-empty FORM are left untouched.

Usage:
    python delete_empty_forms.py --corpora_path /path/to/XML

The path should point to the directory containing per-language subdirs
(e.g. Corpora/Wikipedias/XML), not an individual language subdir.
"""

import argparse
import os
import xml.etree.ElementTree as ET


def is_all_empty_forms(xml_path):
    """Return True if the file parses and every FORM element has empty text."""
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError:
        return False
    forms = list(tree.iter("FORM"))
    if not forms:
        return False
    return not any((f.text or "").strip() for f in forms)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--corpora_path", required=True,
                        help="Path to the XML directory (contains per-language subdirs)")
    args = parser.parse_args()

    if not os.path.isdir(args.corpora_path):
        parser.error(f"corpora_path does not exist or is not a directory: {args.corpora_path}")

    deleted = []
    for root, _, files in os.walk(args.corpora_path):
        for fname in files:
            if not fname.endswith(".xml"):
                continue
            path = os.path.join(root, fname)
            if is_all_empty_forms(path):
                os.remove(path)
                deleted.append(path)

    log_path = os.path.join(args.corpora_path, "delete_empty_forms.log")
    with open(log_path, "w", encoding="utf-8") as fh:
        fh.write(f"Deleted {len(deleted)} empty-FORM XML files:\n")
        for p in deleted:
            fh.write(f"  {p}\n")

    print(f"Deleted {len(deleted)} files. Log: {log_path}")


if __name__ == "__main__":
    main()

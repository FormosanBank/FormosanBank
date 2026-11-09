#!/usr/bin/env python3
"""Standardize with the shared tool, writing clitics as separate words in the
sentence-level standard FORM.

The source joins clitics to their host with '=' (hiyi=su). The shared
standardize.py deletes '=' from the sentence-level standard FORM, gluing the
clitic on (hiyisu). Here the clitics are separate words in the standard
sentence (hiyi su). The shared tool cannot do that yet, so this step:

  1. saves every sentence-level original FORM and replaces '=' with a space;
  2. runs QC/utilities/standardize.py with the shared Seediq_Tsukida_113.tsv;
  3. puts every sentence-level original FORM back exactly as saved.

Word and morpheme FORMs, and all glosses, keep '='. Step 3 refuses to run if
an original FORM is not what step 1 wrote, so the original tier can never be
left edited.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from lxml import etree


def sentence_originals(root):
    for sentence in root.iter("S"):
        form = sentence.find("FORM[@kindOf='original']")
        if form is not None:
            yield sentence.get("id"), form


def write(tree, path: Path, prettify) -> None:
    path.write_text(prettify(tree.getroot()), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("formosanbank", type=Path)
    parser.add_argument("xml_dir", type=Path)
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()
    sys.path.insert(0, str(args.formosanbank))
    from QC.utilities._prettify import prettify  # shared, mixed-content-safe

    paths = sorted(args.xml_dir.rglob("*.xml"))
    saved: dict[Path, dict[str, tuple[str, str]]] = {}
    for path in paths:
        tree = etree.parse(str(path))
        saved[path] = {}
        for sid, form in sentence_originals(tree.getroot()):
            if len(form):
                raise SystemExit(f"{sid}: sentence FORM has child elements; not handled")
            original = form.text or ""
            spaced = original.replace("=", " ")
            saved[path][sid] = (original, spaced)
            form.text = spaced
        write(tree, path, prettify)

    table = args.formosanbank / "Orthographies/ConversionTables/Seediq_Tsukida_113.tsv"
    subprocess.run([args.python, str(args.formosanbank / "QC/utilities/standardize.py"),
                    "--corpora_path", str(args.xml_dir), "--tsv_path", str(table),
                    "--target_column", "standard"], check=True)

    restored = 0
    for path in paths:
        tree = etree.parse(str(path))
        seen = set()
        for sid, form in sentence_originals(tree.getroot()):
            original, spaced = saved[path][sid]
            if (form.text or "") != spaced:
                raise SystemExit(f"{sid}: original FORM changed during standardization: {form.text!r}")
            form.text = original
            seen.add(sid)
            restored += original != spaced
        if seen != set(saved[path]):
            raise SystemExit(f"{path.name}: sentences added or lost during standardization")
        write(tree, path, prettify)
    print(f"standardize_with_clitic_spaces: {restored} sentence original(s) restored after standardization")


if __name__ == "__main__":
    main()

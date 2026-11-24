#!/usr/bin/env python3
"""Label Yedda's word and morpheme glosses kindOf="original".

This corpus has no standard gloss tier: Yedda glosses words in free prose
("weave net, actor voice (AV). The root is tjenun 'weave'."), not in gloss
codes, so there is nothing a code conversion could standardize. The prose
stays in the original tier only.

The kindOf="original" label on those glosses was previously written by
QC/glossing/apply_gloss_standard.py as a side effect of building the
standard tier. This step keeps the label without the standard tier, using
the same conditions as that tool:

* only TRANSL children of W and M (sentence translations are not glosses);
* only xml:lang "eng" or "zho";
* only glosses with text (a gloss that is just <UNCLEAR/> stays unlabelled);
* never a gloss with a ver= attribute (V022 allows one kindOf="original"
  gloss per language and is not ver-aware);
* never a gloss that already has a kindOf.

Run last, after add_phonology.py. Idempotent: a second run labels 0.
"""
from __future__ import annotations

import argparse
import pathlib
import xml.etree.ElementTree as ET

XMLLANG = "{http://www.w3.org/XML/1998/namespace}lang"
GLOSS_LANGS = {"eng", "zho"}


def label(root: ET.Element) -> int:
    n = 0
    for word in root.iter("W"):
        for parent in [word] + word.findall("M"):
            for transl in parent.findall("TRANSL"):
                text = (transl.text or "") + "".join(c.tail or "" for c in transl)
                if (transl.get("kindOf") is None and not transl.get("ver")
                        and transl.get(XMLLANG) in GLOSS_LANGS and text.strip()):
                    transl.set("kindOf", "original")
                    n += 1
    return n


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--corpora_path", required=True, help="the corpus's XML/ directory")
    a = ap.parse_args()
    for path in sorted(pathlib.Path(a.corpora_path).rglob("*.xml")):
        tree = ET.parse(path)
        n = label(tree.getroot())
        if n:
            tree.write(path, encoding="UTF-8", xml_declaration=True)
        print(f"{path.name}: {n} gloss(es) labelled kindOf=\"original\"")


if __name__ == "__main__":
    main()

"""Remove brackets from sentence-level standard FORMs (maintainer rulings, 2026-10-18).

* The infix angle brackets < > go from every sentence-level standard FORM (review page, V134).
  The original FORM keeps them as printed, and the morpheme tier carries -um- etc.
* The parentheses that shared cleaning writes in place of the printed square brackets of the
  pseudo-cleft clauses (examples 23a-d, the "clause_brackets" rows of notation_decisions.tsv) go
  from those sentences' standard FORMs: "drop the square brackets from standard".
"""

import csv
import sys
from pathlib import Path

from lxml import etree

CODEDOCS = Path(__file__).resolve().parents[1]


def clause_bracket_sentence_ids() -> set[str]:
    with (CODEDOCS / "notation_decisions.tsv").open(encoding="utf-8") as handle:
        return {
            row["unit_id"].replace("_U", "_S")
            for row in csv.DictReader(handle, delimiter="\t")
            if row["representation"] == "clause_brackets"
        }


def strip(path: Path) -> int:
    clause_ids = clause_bracket_sentence_ids()
    tree = etree.parse(str(path))
    changed = 0
    for sentence in tree.getroot().iter("S"):
        for form in sentence.findall("FORM[@kindOf='standard']"):
            if not form.text:
                continue
            text = form.text.replace("<", "").replace(">", "")
            if sentence.get("id") in clause_ids:
                text = text.replace("(", "").replace(")", "")
            if text != form.text:
                form.text = text
                changed += 1
    if changed:
        tree.write(str(path), encoding="UTF-8", xml_declaration=True)
    return changed


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print(f"{arg}: {strip(Path(arg))} standard S FORM(s) changed")

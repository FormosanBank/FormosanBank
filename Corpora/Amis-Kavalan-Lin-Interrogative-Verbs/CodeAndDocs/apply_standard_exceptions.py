"""Apply the maintainer-ruled exceptions to the standard tier, after standardize.py.

Editing the standard tier outside standardize.py is normally not done (POL-002:
all standard-tier cleaning lives in standardize.py). This step exists because of
one ruling, recorded verbatim in standard_tier_exceptions.tsv: example 14a,
which Lin cites from Wu (2006), is the only place the source writes `q`, a letter
Ortho94 does not have, so the shared Ortho94 -> Ortho113 table cannot convert it.
Usage: apply_standard_exceptions.py <FormosanBank root> [<XML root>]

Each row names one sentence and the exact original-tier text it expects. If the
original has drifted, or the letter to replace is absent from the sentence's
standard FORM, the step stops instead of guessing. The replacement is applied to
every standard FORM in that sentence (S, W and M). It must run before
add_phonology.py so the standard PHON is generated from the corrected FORMs.
"""
import csv
import sys
from pathlib import Path

from lxml import etree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FB = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT.parents[1]
XML = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else ROOT / "XML"  # generate_xml.sh passes its staging dir
sys.path.insert(0, str(FB))
from QC.utilities._prettify import prettify  # noqa: E402  shared, mixed-content-safe

TABLE = HERE / "standard_tier_exceptions.tsv"


def form_text(form):
    return "".join(form.itertext())


def main():
    rows = list(csv.DictReader(TABLE.open(encoding="utf-8"), delimiter="\t"))
    pending = {row["sentence_id"]: row for row in rows}
    for path in sorted(XML.rglob("*.xml")):
        tree = etree.parse(str(path))
        changed = False
        for sentence in tree.getroot().iter("S"):
            row = pending.pop(sentence.get("id"), None)
            if row is None:
                continue
            original = sentence.find("FORM[@kindOf='original']")
            if original is None or form_text(original) != row["expected_original"]:
                raise SystemExit(f"{row['sentence_id']}: original FORM is not the expected "
                                 f"{row['expected_original']!r}; refusing to edit the standard tier")
            top = sentence.find("FORM[@kindOf='standard']")
            if top is None or row["replace"] not in form_text(top):
                raise SystemExit(f"{row['sentence_id']}: {row['replace']!r} not in the standard FORM; nothing to apply")
            n = 0
            for form in sentence.iter("FORM"):
                if form.get("kindOf") == "standard" and form.text and row["replace"] in form.text:
                    n += form.text.count(row["replace"])
                    form.text = form.text.replace(row["replace"], row["with"])
            print(f"{row['sentence_id']}: {row['replace']!r} -> {row['with']!r} in {n} standard FORM position(s)")
            changed = True
        if changed:
            path.write_text(prettify(tree.getroot()), encoding="utf-8")
    if pending:
        raise SystemExit(f"sentences not found: {sorted(pending)}")


if __name__ == "__main__":
    main()

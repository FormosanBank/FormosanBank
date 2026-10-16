#!/usr/bin/env python3
"""Standardize the `ř` words whose modern equivalent is known.

Step 4 of generate_xml.sh. Runs AFTER standardize.py and BEFORE add_phonology.py,
and it edits the **standard** tier.

Why this exists at all. `ř` is a third liquid in the 1958 transcription, distinct
from `r` and `l`, and it is not a single modern phoneme: of the eleven words that
carry it, five reach an attested modern form and they do so three different ways
(`ařwa` -> `adoa` 'two' and `kařwan` -> `kadoan` 'other' via d, `ařima` ->
`alima` 'five' via l, `vařit` -> `vazit` and `sipřutan` -> `sipzotan` via z); the
other six reach nothing. A row in the conversion table asserts one
correspondence, and there is not one, so `Yami_Wakelin_113.tsv` has no `ř` row —
the letter passes through and stars in PHON, which is the honest signal. The five
words whose value IS known are fixed here instead, one word at a time.
See ../../../Orthographies/Wakelin/README.md.

⚠️ This edits the standard tier outside standardize.py, which POL-002 otherwise
reserves to that tool, and it does so on a maintainer ruling (2026-09-07) taken
with the cost understood. The cost is concrete: **a standalone `standardize.py`
run over this corpus silently reverts these five words**, because it regenerates
the standard tier from the original. Anyone re-standardizing WakelinTexts must
re-run this step, which is why it lives inside generate_xml.sh rather than being
something a person remembers.

The step is deliberately strict. Every row must match somewhere, and the number
of replacements is reported, so a table that has drifted from the data fails the
build instead of quietly doing nothing.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import xml.etree.ElementTree as ET

CODE_ROOT = Path(__file__).resolve().parent
BANK_ROOT = CODE_ROOT.parents[2]
sys.path.insert(0, str(BANK_ROOT))
from QC.utilities._prettify import prettify  # noqa: E402
from QC.utilities.standardize import apply_standard  # noqa: E402  (import guard only)


def load_words(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as handle:
        rows = [r for r in csv.DictReader(handle, delimiter="\t")
                if r.get("wakelin") and not r["wakelin"].startswith("#")]
    if not rows:
        raise SystemExit(f"{path}: no word rows")
    return rows


def conversion_pairs(table: Path) -> list[tuple[str, str]]:
    """The conversion table, in file order — order is significant."""
    with open(table, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [(r["original"], r.get("standard") or "") for r in reader if r["original"]]


def standard_form_of(word: str, pairs: list[tuple[str, str]]) -> str:
    """What standardize.py turns `word` into, so we can find it in the tier."""
    for original, replacement in pairs:
        word = word.replace(original, replacement)
    return word


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--xml-dir", default=str(CODE_ROOT.parent / "XML"))
    ap.add_argument("--words", default=str(CODE_ROOT / "r_caron_words.tsv"))
    ap.add_argument("--table", default=str(
        BANK_ROOT / "Orthographies" / "ConversionTables" / "Yami_Wakelin_113.tsv"))
    args = ap.parse_args()

    rows = load_words(Path(args.words))
    pairs = conversion_pairs(Path(args.table))
    # Longest first: `ařima` must not be clipped by a shorter row that is a
    # prefix of it. The table itself is order-sensitive; this list is not.
    plan = sorted(
        ((standard_form_of(r["wakelin"], pairs), r["standard"], r["wakelin"]) for r in rows),
        key=lambda item: -len(item[0]),
    )
    for before, after, source in plan:
        if before == after:
            raise SystemExit(
                f"{source}: standardization already yields {after!r}; "
                "the row is a no-op and should be removed"
            )

    counts = {source: 0 for _, _, source in plan}
    for path in sorted(Path(args.xml_dir).rglob("*.xml")):
        tree = ET.parse(path)
        root = tree.getroot()
        touched = False
        for form in root.iter("FORM"):
            if form.get("kindOf") != "standard" or not form.text:
                continue
            text = form.text
            for before, after, source in plan:
                if before in text:
                    counts[source] += text.count(before)
                    text = text.replace(before, after)
            if text != form.text:
                form.text = text
                touched = True
        if touched:
            path.write_text(prettify(root), encoding="utf-8")

    for _, _, source in plan:
        print(f"  {source}: {counts[source]} standard FORM replacements")
    missing = [s for s, n in counts.items() if n == 0]
    if missing:
        raise SystemExit(
            "these rows matched nothing in the standard tier: "
            + ", ".join(missing)
            + "\nEither the word is gone from the corpus or the conversion table "
              "changed what it standardizes to; fix r_caron_words.tsv."
        )
    print(f"  {sum(counts.values())} replacements across {len(plan)} words")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

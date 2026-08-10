#!/usr/bin/env python3
"""Repair the Ferrell question-mark/glottal-stop conflation, tier-aware.

In Ferrell's Paiwan orthography the character '?' is BOTH the glottal-stop
letter and question-mark punctuation, and the straight apostrophe appears in
the source only as a nested (single) quotation mark. The pipeline's blanket
mappings are right for the letters and wrong for the punctuation:

* standardize.py (Paiwan_Ferrell_113.tsv) maps every '?' to the standard
  glottal letter "'", turning question marks into glottals on the standard
  tier;
* add_phonology.py maps every original-tier '?' to IPA ʔ (Ferrell profile)
  and every standard-tier "'" to ʔ (Ortho113 profile), so question marks and
  quote apostrophes both surface as spurious glottal stops in PHON.

This script post-corrects both, deciding letter-vs-punctuation from the
ORIGINAL tier. The strongest signal is the English free translation: a '?'
in the TRANSL is unambiguously a question mark, so when a sentence's
original FORM and its TRANSL contain the SAME number of '?' (after
removing the translator-uncertainty marker '(?)' from the TRANSL), every
'?' in that sentence is taken to be a question mark. Two guards keep this
sound: the match is skipped when any M under the S contains '?' (a
word-internal glottal surfaces in its morpheme segmentation, proving the
FORM count includes a glottal), and M-tier characters are never affected.

Sentences that do not count-match fall back to context rules. Every '?' or
quote character in an original FORM is classified:

  QUOTE    an apostrophe/single-quote character — always punctuation.
  QPUNCT   a '?' that is punctuation: every '?' of a count-matched S (and
           of its W tokens), or one immediately followed by a quote
           character (question inside quoted speech), or string-final
           in an S FORM (sentences are always punctuated), or string-final
           in the LAST W of an S whose own final '?' is punctuation (the
           word carries the sentence's mark).
  GLOTTAL  every other '?' — including ALL '?' in M FORMs (morphemes never
           carry punctuation).

Then, for each S / W / M element (the k-th such character in the standard
FORM corresponds to the k-th in the original FORM — standardize maps '?' to
"'" one-for-one and passes quote characters through):

  1. the standard FORM is rewritten so QPUNCT positions read '?', GLOTTAL
     positions read "'", and QUOTE positions keep their source character
     (idempotent: every state is re-derived, none inferred from the last
     run's output);
  2. PHON is regenerated with add_phonology's own phonologize():
     original PHON from the original FORM with QPUNCT characters removed,
     standard PHON from the repaired standard FORM with QUOTE characters
     removed (the restored '?' is unmapped punctuation, which phonologize
     drops on its own).

Elements whose original/standard occurrence counts disagree are left
untouched and reported. String-final '?' on a non-final W (ambiguous:
glottal-final word vs. unpunctuated quote) is kept as GLOTTAL and reported
for manual review. Both reports go to --report_csv.

Run AFTER standardize.py and add_phonology.py (see README). Uses the same
profile machinery as add_phonology (dialect columns; the Ferrell 'default'
column covers dialect="unknown").
"""
from __future__ import annotations

import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from QC.utilities.add_phonology import load_profile, phonologize, prettify
from QC.validation._dialect_inventory import ISO_TO_LANGUAGE, standard_orthography

QUOTE_CHARS = {"'", "’", "‘"}  # straight + curly single quotes
SCAN_CHARS = QUOTE_CHARS | {"?"}

QUOTE, QPUNCT, GLOTTAL = "quote", "qpunct", "glottal"


def classify(text: str, tier: str, *, is_last_w: bool = False,
             s_final_is_punct: bool = False,
             all_question: bool = False) -> list[str]:
    """Classify each SCAN_CHARS occurrence in an original-tier text."""
    stripped = text.rstrip()
    final_index = len(stripped) - 1
    out = []
    for i, ch in enumerate(text):
        if ch not in SCAN_CHARS:
            continue
        if ch in QUOTE_CHARS:
            out.append(QUOTE)
        elif tier == "M":
            out.append(GLOTTAL)
        elif all_question:
            out.append(QPUNCT)
        elif i + 1 < len(text) and text[i + 1] in QUOTE_CHARS | {'"'}:
            out.append(QPUNCT)
        elif i == final_index and (tier == "S" or (is_last_w and s_final_is_punct)):
            out.append(QPUNCT)
        else:
            out.append(GLOTTAL)
    return out


def s_ends_in_question(text: str) -> bool:
    """True if an S original FORM's final '?' is sentence punctuation."""
    stripped = text.rstrip()
    if stripped.endswith('?"'):
        return True
    return stripped.endswith("?")


def repair_standard(std_text: str, flags: list[str]) -> str | None:
    """Rewrite the standard FORM per the original tier's classification.

    Returns None on occurrence-count mismatch (caller reports + skips).
    """
    out = []
    k = 0
    for ch in std_text:
        if ch in SCAN_CHARS:
            if k >= len(flags):
                return None
            if flags[k] == QPUNCT:
                out.append("?")
            elif flags[k] == GLOTTAL:
                out.append("'")
            else:  # QUOTE: keep the source's character as-is
                out.append(ch)
            k += 1
        else:
            out.append(ch)
    if k != len(flags):
        return None
    return "".join(out)


def masked(text: str, flags: list[str], drop: str) -> str:
    """Remove the SCAN_CHARS occurrences classified `drop` from text."""
    out = []
    k = 0
    for ch in text:
        if ch in SCAN_CHARS:
            if flags[k] == drop:
                k += 1
                continue
            k += 1
        out.append(ch)
    return "".join(out)


def set_phon(parent: ET.Element, form: ET.Element, kind: str, text: str) -> bool:
    phon = parent.find(f'PHON[@kindOf="{kind}"]')
    if phon is None:
        phon = ET.Element("PHON", {"kindOf": kind})
        parent.insert(list(parent).index(form) + 1, phon)
        phon.text = text
        return True
    if phon.text != text:
        phon.text = text
        return True
    return False


def process_file(path: Path, report: list, dry_run: bool) -> int:
    tree = ET.parse(path)
    root = tree.getroot()
    text_el = root if root.tag == "TEXT" else root.find(".//TEXT")
    language_code = (
        text_el.get("xml:lang", "")
        or text_el.get("{http://www.w3.org/XML/1998/namespace}lang", "")
        or text_el.get("lang", "")
    ).strip()
    language = ISO_TO_LANGUAGE.get(language_code, language_code)
    dialect = text_el.get("dialect", "").strip() or "default"

    ferrell = load_profile("Ferrell", language, dialect)
    ortho = load_profile(standard_orthography(language), language, dialect)
    if ferrell is None or ortho is None:
        raise ValueError(f"{path}: missing orthography profile for {language}")

    changed = 0
    for s in root.iter("S"):
        s_form = s.find('FORM[@kindOf="original"]')
        s_text = (s_form.text or "") if s_form is not None else ""
        s_punct = s_ends_in_question(s_text)
        ws = s.findall("W")
        # TRANSL count-match: same number of '?' in the original FORM and the
        # free translation (minus '(?)' uncertainty markers) => every '?' in
        # this sentence is a question mark. Skipped when any M carries '?'
        # (proof of a genuine glottal in the count).
        transls = s.findall("TRANSL")
        transl = next((t for t in transls
                       if t.get("{http://www.w3.org/XML/1998/namespace}lang") == "eng"),
                      transls[0] if transls else None)
        transl_q = ((transl.text or "").replace("(?)", "").count("?")
                    if transl is not None else 0)
        m_has_q = any("?" in (mf.text or "")
                      for w in ws for m in w.findall("M")
                      for mf in [m.find('FORM[@kindOf="original"]')]
                      if mf is not None)
        s_q = s_text.count("?")
        all_question = s_q > 0 and s_q == transl_q and not m_has_q
        elements = [(s, "S", False)]
        for w in ws:
            elements.append((w, "W", w is ws[-1]))
            elements.extend((m, "M", False) for m in w.findall("M"))
        for el, tier, is_last in elements:
            orig = el.find('FORM[@kindOf="original"]')
            std = el.find('FORM[@kindOf="standard"]')
            if orig is None or not orig.text:
                continue
            flags = classify(orig.text, tier, is_last_w=is_last,
                             s_final_is_punct=s_punct,
                             all_question=all_question)
            if (tier == "W" and not is_last and not all_question
                    and orig.text.rstrip().endswith("?")):
                # ambiguous: glottal-final word vs. unpunctuated quote
                report.append((path.name, s.get("id"), el.get("id"),
                               orig.text, "non-final W ends in '?'; kept as glottal"))
            new_std_text = None
            if std is not None and std.text:
                new_std_text = repair_standard(std.text, flags)
                if new_std_text is None:
                    report.append((path.name, s.get("id"), el.get("id"), orig.text,
                                   "original/standard '?'+quote count mismatch; skipped"))
                    continue
                if new_std_text != std.text:
                    std.text = new_std_text
                    changed += 1
            orig_phon = phonologize(masked(orig.text, flags, QPUNCT), ferrell)
            if set_phon(el, orig, "original", orig_phon):
                changed += 1
            if new_std_text is not None:
                # repair preserves occurrence count/positions, so the same
                # flags describe the repaired standard text
                std_phon = phonologize(masked(new_std_text, flags, QUOTE), ortho)
                if set_phon(el, std, "standard", std_phon):
                    changed += 1

    if changed and not dry_run:
        xml_string = prettify(root)
        xml_string = "\n".join(l for l in xml_string.split("\n") if l.strip())
        path.write_text(xml_string, encoding="utf-8")
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml_dir", type=Path,
                    default=Path(__file__).resolve().parent.parent / "XML")
    ap.add_argument("--report_csv", type=Path,
                    default=Path(__file__).resolve().parent / "fix_ferrell_report.csv")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(args.xml_dir.glob("*.xml"))
    if not files:
        print(f"No .xml in {args.xml_dir}", file=sys.stderr)
        return 1
    report: list = []
    total = touched = 0
    for path in files:
        n = process_file(path, report, args.dry_run)
        if n:
            touched += 1
            total += n
    verb = "would change" if args.dry_run else "changed"
    print(f"{verb} {total} FORM/PHON elements across {touched} of {len(files)} files")
    if not args.dry_run:
        with open(args.report_csv, "w", newline="", encoding="utf-8") as fh:
            wr = csv.writer(fh)
            wr.writerow(["file", "S_id", "el_id", "original_form", "note"])
            wr.writerows(report)
        print(f"wrote report: {args.report_csv} ({len(report)} rows)")
    else:
        for row in report[:20]:
            print("  REVIEW:", *row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

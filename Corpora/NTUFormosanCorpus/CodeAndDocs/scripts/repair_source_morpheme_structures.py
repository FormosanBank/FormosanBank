#!/usr/bin/env python3
"""Repair eight source-specific M-tier structures in the NTU XML.

The legacy parsers split hyphenated material before recognizing angle-bracket
infix notation. Four words therefore have a bracket opener in one M and the
closer in the next M. Their W tiers and source JSON rows are correct. This
script replaces only those four inferred M tiers with the FormosanBank
POL-014 representation: one ``-X-`` infix M and a root M with a hyphen at the
infixation point.

Two words carry a cross-token uncertainty span that the parser projected into
invalid M elements. Their source-backed W tiers remain intact, while each M
tier is represented as one explicit ``UNCLEAR`` mirror so the parsed sentence
does not pretend that the fragment has a recoverable morpheme analysis. A
Mandarin L2 span is non-morphemic source markup and has its inferred M children
removed. Nonlinguistic breath events are omitted earlier by the exact-digest
story repair registry.

One diagonally shifted source row preserves the segmented form and glosses in
adjacent cells, but the parser emits a single unsplit M. Its two source-backed
morphemes are restored here before the empty-morpheme cleanup can discard the
second slot.

Every target is keyed by generated path, W id, and expected W original FORM.
The script fails if any target is missing or has drifted. It is idempotent and
uses the same minidom serialization as the parser staging tree.
"""

import argparse
import copy
from pathlib import Path
import xml.etree.ElementTree as ET

from repair_empty_morphemes import _serialize

_XLANG = "{http://www.w3.org/XML/1998/namespace}lang"


REPAIRS = {
    (
        "Sentences/Bunun/Bunun.xml",
        "57_S_2_W1",
        "ta<in-i>nghaiu",
    ): [
        ("-in-i-", "<PFV-PFV>", "<完成貌-完成貌>"),
        ("ta-nghaiu", "steal", "偷"),
    ],
    (
        "Stories/Bunun/Bunun_bnNr-frog_Laniahu.xml",
        "bnNr-frog_Laniahu_S_158_W10",
        "la<in-i>haib-an",
    ): [
        ("-in-i-", "<PFV-PFV>", "<完成貌-完成貌>"),
        ("la-haib", "pass", "經過"),
        ("an", "LF", "處焦"),
    ],
    (
        "Stories/Bunun/Bunun_bnNr-frog_Laniahu.xml",
        "bnNr-frog_Laniahu_S_158_W12",
        "la<in-i>haib-an",
    ): [
        ("-in-i-", "<PFV-PFV>", "<完成貌-完成貌>"),
        ("la-haib", "pass", "經過"),
        ("an", "LF", "處焦"),
    ],
    (
        "Sentences/Rukai/Rukai.xml",
        "20200529-FW-Yongfu-2_S_21_W0",
        "ma-si<pe-pe>pelreng-aku",
    ): [
        ("ma", "STAT.RLS", "靜態.實現"),
        ("-pe-pe-", "<RED-RED>", "<重疊-重疊>"),
        ("si-pelreng", "sleep", "睡覺"),
        ("aku", "1S.BN", "第一人稱單數.附著主格"),
    ],
    (
        "Stories/Seediq/Seediq_sdqNr-mother_iwan 2020s.xml",
        "sdqNr-mother_iwan 2020s_S_32_W17",
        "kesun",
    ): [
        ("kesa", "say", "說"),
        ("un", "PF", "受焦"),
    ],
}


REMOVE_M = {
    (
        "Stories/Kanakanavu/Kanakanavu_kkvNr_dailylife_Angai.xml",
        "kkvNr_dailylife_Angai_S_11_W0",
        "L2M<jiuhaole>L2M",
    ),
}


UNCLEAR_M = {
    (
        "Stories/Kavalan/Kavalan_KavNr-pear_buya.xml",
        "KavNr-pear_buya_S_41_W0",
        "<P",
    ),
    (
        "Stories/Kavalan/Kavalan_KavNr-pear_buya.xml",
        "KavNr-pear_buya_S_41_W2",
        "P>-qanas-an",
    ),
}


def _original_form(elem):
    form = elem.find('./FORM[@kindOf="original"]')
    return "" if form is None else (form.text or "")


def _make_m(w_id, index, form_text, eng, zho):
    m = ET.Element("M", {"id": f"{w_id}M{index}"})
    for kind in ("original", "standard"):
        form = ET.SubElement(m, "FORM", {"kindOf": kind})
        form.text = form_text
    for lang, gloss in (("eng", eng), ("zho", zho)):
        transl = ET.SubElement(m, "TRANSL", {_XLANG: lang})
        transl.text = gloss
    return m


def _make_unclear_m(w):
    """Return a coarse M that preserves W evidence without guessing a form."""
    m = ET.Element("M", {"id": f"{w.get('id')}M1"})
    for child in w:
        if child.tag == "FORM":
            form = ET.SubElement(m, "FORM", dict(child.attrib))
            ET.SubElement(form, "UNCLEAR")
        elif child.tag in {"PHON", "TRANSL"}:
            m.append(copy.deepcopy(child))
    return m


def _has_unclear_m(w):
    ms = w.findall("M")
    if len(ms) != 1:
        return False
    forms = ms[0].findall("FORM")
    return (
        {form.get("kindOf") for form in forms} == {"original", "standard"}
        and all(not (form.text or "").strip() for form in forms)
        and all(form.find("UNCLEAR") is not None for form in forms)
    )


def _desired_signature(parts):
    return [(form, eng, zho) for form, eng, zho in parts]


def _actual_signature(w):
    out = []
    for m in w.findall("M"):
        glosses = {
            t.get(_XLANG): t.text or ""
            for t in m.findall("TRANSL")
        }
        out.append((_original_form(m), glosses.get("eng", ""), glosses.get("zho", "")))
    return out


def repair_tree(root, relative_path):
    targets = {
        key: parts for key, parts in REPAIRS.items() if key[0] == relative_path
    }
    removals = {key for key in REMOVE_M if key[0] == relative_path}
    unclear = {key for key in UNCLEAR_M if key[0] == relative_path}
    expected = len(targets) + len(removals) + len(unclear)
    if not expected:
        return 0, 0

    found = modified = 0
    for w in root.iter("W"):
        key = (relative_path, w.get("id") or "", _original_form(w))
        if key in targets:
            found += 1
            parts = targets[key]
            if _actual_signature(w) == _desired_signature(parts):
                continue
            for m in list(w.findall("M")):
                w.remove(m)
            for index, (form, eng, zho) in enumerate(parts, start=1):
                w.append(_make_m(w.get("id") or "", index, form, eng, zho))
            modified += 1
        elif key in removals:
            found += 1
            ms = list(w.findall("M"))
            if ms:
                for m in ms:
                    w.remove(m)
                modified += 1
        elif key in unclear:
            found += 1
            if _has_unclear_m(w):
                continue
            for m in list(w.findall("M")):
                w.remove(m)
            w.append(_make_unclear_m(w))
            modified += 1

    if found != expected:
        expected_keys = set(targets) | removals | unclear
        actual_keys = {
            (relative_path, w.get("id") or "", _original_form(w))
            for w in root.iter("W")
        }
        missing = sorted(expected_keys - actual_keys)
        raise RuntimeError(f"source M repair targets missing or drifted: {missing!r}")
    return found, modified


def repair_corpus(xml_dir, dry_run=False):
    xml_dir = Path(xml_dir)
    files_modified = targets_found = 0
    target_paths = (
        {key[0] for key in REPAIRS}
        | {key[0] for key in REMOVE_M}
        | {key[0] for key in UNCLEAR_M}
    )
    for relative_path in sorted(target_paths):
        path = xml_dir / relative_path
        if not path.is_file():
            raise RuntimeError(f"source M repair file missing: {path}")
        original = path.read_text(encoding="utf-8")
        root = ET.parse(path).getroot()
        if _serialize(copy.deepcopy(root)) != original:
            raise RuntimeError(f"source M repair round-trip guard failed: {path}")
        found, modified = repair_tree(root, relative_path)
        targets_found += found
        if modified:
            files_modified += 1
            if not dry_run:
                path.write_text(_serialize(root), encoding="utf-8")
    print(f"source M repair targets verified: {targets_found}")
    print(f"files {'that would be ' if dry_run else ''}modified: {files_modified}")
    return targets_found, files_modified


def main():
    default_xml = Path(__file__).resolve().parents[1] / "Final_XML"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml_dir", default=str(default_xml))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    repair_corpus(args.xml_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

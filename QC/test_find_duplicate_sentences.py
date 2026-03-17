#!/usr/bin/env python3
"""
Test for find_duplicate_sentences.py

Strategy: test the core extraction and matching logic directly (without
re-scanning the full 1,900-file corpus), using real Glosbe sentences planted
into an in-memory temporary XML file.

Tests:
  1. extract_standard_forms correctly reads S ids and FORM text
  2. Sentence lookup finds exact matches
  3. Case-insensitive matching works
  4. Sentences absent from Glosbe are not reported
  5. Non-direct-child FORMs (inside <W>) are ignored
"""

import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import defaultdict

# Import the module under test
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "QC", "utilities"))
from find_duplicate_sentences import extract_standard_forms

GLOSBE_XML = os.path.join(REPO, "Corpora", "Glosbe", "XML", "Amis", "amis_glosbe.xml")

PASS = 0
FAIL = 0

def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  PASS: {label}")
        PASS += 1
    else:
        print(f"  FAIL: {label}" + (f" — {detail}" if detail else ""))
        FAIL += 1


def make_xml(sentences: list[tuple[str, str]], include_word_level=False) -> str:
    """Build an XML string in the standard corpus format."""
    root = ET.Element("TEXT", attrib={"id": "TEST", "xml:lang": "ami"})
    for sid, text in sentences:
        s = ET.SubElement(root, "S", attrib={"id": sid})
        form = ET.SubElement(s, "FORM", attrib={"kindOf": "standard"})
        form.text = text
        if include_word_level:
            # Add a nested word-level FORM that should NOT be picked up
            w = ET.SubElement(s, "W")
            wf = ET.SubElement(w, "FORM", attrib={"kindOf": "standard"})
            wf.text = "SHOULD_NOT_MATCH"
    tree = ET.ElementTree(root)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as f:
        tree.write(f, encoding="unicode", xml_declaration=True)
        return f.name


def get_glosbe_sample(n=5) -> list[tuple[str, str]]:
    root = ET.parse(GLOSBE_XML).getroot()
    out = []
    for s in root.iter("S"):
        for form in s:
            if form.tag == "FORM" and form.get("kindOf") == "standard":
                text = (form.text or "").strip()
                if text:
                    out.append((s.get("id"), text))
        if len(out) >= n:
            break
    return out


def main():
    print("=== Tests for find_duplicate_sentences.py ===\n")

    # --- Test 1: extract_standard_forms round-trip ---
    print("Test 1: extract_standard_forms reads S ids and FORM text correctly")
    sentences = [("S_1", "Hello world"), ("S_2", "Another sentence"), ("S_3", "Third")]
    xml_path = make_xml(sentences)
    try:
        result = extract_standard_forms(xml_path)
        check("correct count", len(result) == 3, f"got {len(result)}")
        check("first id",   result[0][0] == "S_1")
        check("first text", result[0][1] == "Hello world")
        check("third id",   result[2][0] == "S_3")
    finally:
        os.remove(xml_path)

    # --- Test 2: matching real Glosbe sentences ---
    print("\nTest 2: real Glosbe sentences are matched correctly")
    planted = get_glosbe_sample(5)
    print(f"  Using {len(planted)} sentences from {GLOSBE_XML}")

    # Build Glosbe index (same logic as the script)
    glosbe_index: dict[str, list[str]] = defaultdict(list)
    for gid, text in extract_standard_forms(GLOSBE_XML):
        glosbe_index[text.lower()].append(gid)

    # Write planted sentences to a temp corpus XML
    corpus_sentences = [(f"TEST_{i}", text) for i, (_, text) in enumerate(planted, 1)]
    xml_path = make_xml(corpus_sentences)
    try:
        corpus_forms = extract_standard_forms(xml_path)
        matches = []
        for sid, text in corpus_forms:
            if text.lower() in glosbe_index:
                for gid in glosbe_index[text.lower()]:
                    matches.append((gid, sid))

        planted_gids = {gid for gid, _ in planted}
        found_gids   = {gid for gid, _ in matches}
        check("all 5 sentences found", planted_gids.issubset(found_gids),
              f"missing: {planted_gids - found_gids}")
        for i, (gid, _) in enumerate(planted, 1):
            hit = next(((g, s) for g, s in matches if g == gid), None)
            check(f"  {gid} -> TEST_{i}", hit is not None and hit[1] == f"TEST_{i}")
    finally:
        os.remove(xml_path)

    # --- Test 3: case-insensitive matching ---
    print("\nTest 3: case-insensitive matching")
    gid_sample, text_sample = planted[0]
    upper_xml = make_xml([("UPPER_1", text_sample.upper())])
    lower_xml = make_xml([("LOWER_1", text_sample.lower())])
    try:
        for label, path, match_id in [("uppercase", upper_xml, "UPPER_1"),
                                       ("lowercase", lower_xml, "LOWER_1")]:
            forms = extract_standard_forms(path)
            found = any(text.lower() in glosbe_index for _, text in forms)
            check(f"{label} variant of '{text_sample[:30]}...' matches", found)
    finally:
        os.remove(upper_xml)
        os.remove(lower_xml)

    # --- Test 4: non-Glosbe text is not matched ---
    print("\nTest 4: invented sentences produce no false positives")
    invented = [("INV_1", "Zxqwerty totally fake sentence that is not in any corpus."),
                ("INV_2", "Another completely made up string XYZ123.")]
    xml_path = make_xml(invented)
    try:
        forms = extract_standard_forms(xml_path)
        false_positives = [(sid, text) for sid, text in forms if text.lower() in glosbe_index]
        check("no false positives", len(false_positives) == 0,
              f"got: {false_positives}")
    finally:
        os.remove(xml_path)

    # --- Test 5: word-level FORMs are ignored ---
    print("\nTest 5: <FORM> inside <W> (non-direct child of <S>) is not extracted")
    xml_path = make_xml([("S_A", "A real sentence")], include_word_level=True)
    try:
        forms = extract_standard_forms(xml_path)
        texts = [t for _, t in forms]
        check("word-level FORM excluded", "SHOULD_NOT_MATCH" not in texts,
              f"texts: {texts}")
        check("sentence-level FORM included", "A real sentence" in texts)
    finally:
        os.remove(xml_path)

    # --- Summary ---
    print(f"\n{'='*40}")
    print(f"Results: {PASS} passed, {FAIL} failed.")
    if FAIL:
        sys.exit(1)


if __name__ == "__main__":
    main()

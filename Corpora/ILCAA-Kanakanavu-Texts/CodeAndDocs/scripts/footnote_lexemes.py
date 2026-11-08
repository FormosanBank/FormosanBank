"""Source-anchored lexical records from the book's explanatory footnotes."""

import hashlib
import json
from collections import Counter
from pathlib import Path

from lxml import etree

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
TEXT_ID = "ILCAA_KANAKANAVU_TEXTS_FOOTNOTE_LEXEMES"
FILENAME = "ILCAA_KanakanavuTexts_footnote_lexemes.xml"


def load_records(path: Path, notes: list[dict]) -> list[tuple[dict, dict]]:
    by_id = {note["footnote_id"]: note for note in notes}
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if Counter(row["footnote_id"] for row in rows) != Counter(by_id.keys()):
        raise ValueError("Footnote inventory does not match the extracted source")
    records = []
    ids = set()
    for row in rows:
        note = by_id[row["footnote_id"]]
        raw = note["footnote_raw"]
        if hashlib.sha256(raw.encode()).hexdigest() != row["note_sha256"]:
            raise ValueError(f"Changed source footnote: {row['footnote_id']}")
        if bool(row["records"]) != (row["disposition"] == "lexical_records"):
            raise ValueError(f"Inconsistent disposition: {row['footnote_id']}")
        for record in row["records"]:
            if record["id"] in ids:
                raise ValueError(f"Repeated lexical ID: {record['id']}")
            ids.add(record["id"])
            readings = [record["form"], *record["variants"]]
            evidence = readings + [t["text"] for t in record["translations"]]
            if any(not value or value not in raw for value in evidence):
                raise ValueError(f"Lexical text absent from source: {record['id']}")
            records.append((record, note))
    return records


def append_sentence(root, sid: str, source: str, record: dict, context: str):
    sentence = etree.SubElement(root, "S", id=sid, source=source)
    etree.SubElement(sentence, "FORM", kindOf="original", notes=context).text = record["form"]
    for variant in record["variants"]:
        etree.SubElement(sentence, "FORM", kindOf="original", ver="alt").text = variant
    languages = Counter()
    for translation in record["translations"]:
        attrs = {XML_LANG: translation["lang"]}
        if languages[translation["lang"]]:
            attrs["ver"] = "alt"
        etree.SubElement(sentence, "TRANSL", attrib=attrs).text = translation["text"]
        languages[translation["lang"]] += 1
    return sentence


def write_xml(folder: Path, records_path: Path, notes: list[dict], attributes: dict) -> Path:
    root = etree.Element("TEXT", attrib={
        **attributes,
        "id": TEXT_ID,
        "source": "Kanakanavu Texts (2026), explanatory footnotes; each S identifies its PDF page and note.",
    })
    for record, note in load_records(records_path, notes):
        append_sentence(root, f"{TEXT_ID}_{record['id']}",
                        f"PDF page {note['physical_page']}, footnote {note['footnote_number']}",
                        record, note["footnote_clean"])
    path = folder / FILENAME
    etree.ElementTree(root).write(str(path), encoding="UTF-8", xml_declaration=True, pretty_print=True)
    return path


def audit_xml(folder: Path, records_path: Path, notes: list[dict]) -> list[str]:
    expected = {f"{TEXT_ID}_{record['id']}": (record, note)
                for record, note in load_records(records_path, notes)}
    path = folder / FILENAME
    if not path.is_file():
        return ["Missing footnote lexical XML"]
    root = etree.parse(str(path)).getroot()
    sentences = {s.get("id"): s for s in root.findall("S")}
    findings = []
    if root.get("id") != TEXT_ID or root.get(XML_LANG) != "xnb" or root.get("dialect") != "Kanakanavu":
        findings.append("Footnote lexical TEXT identity differs")
    if len(sentences) != len(root.findall("S")) or sentences.keys() != expected.keys():
        findings.append("Footnote lexical sentence inventory differs")
    for sid, (record, note) in expected.items():
        if sid not in sentences:
            continue
        sentence = sentences[sid]
        forms = [(f.text, f.get("ver")) for f in sentence.findall("FORM[@kindOf='original']")]
        if forms != [(record["form"], None), *((v, "alt") for v in record["variants"])]:
            findings.append(f"{sid}: source FORM differs")
        translations = [(t.get(XML_LANG), t.text) for t in sentence.findall("TRANSL")]
        if translations != [(t["lang"], t["text"]) for t in record["translations"]]:
            findings.append(f"{sid}: source translation differs")
        if sentence.find("W") is not None:
            findings.append(f"{sid}: prose does not supply aligned W/M analysis")
        original = sentence.find("FORM[@kindOf='original']")
        if original is None or original.get("notes") != note["footnote_clean"]:
            findings.append(f"{sid}: source context differs")
    return findings

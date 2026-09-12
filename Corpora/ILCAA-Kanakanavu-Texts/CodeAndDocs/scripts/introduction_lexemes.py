"""Source-backed introduction examples, kept separate by transcription system."""

import hashlib
import json
from pathlib import Path

from lxml import etree

from footnote_lexemes import XML_LANG, append_sentence


def load_records(path: Path, workspace: Path) -> list[dict]:
    data = json.loads(path.read_text())
    pages = {}
    for page, expected in data["pages"].items():
        raw = (workspace / f"data/raw/text/pages/page_{int(page):04d}.txt").read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError(f"Changed introduction source page: {page}")
        pages[int(page)] = "".join(raw.decode().split())
    records = data["records"]
    by_id = {r["id"]: r for r in records}
    if len(by_id) != len(records):
        raise ValueError("Repeated introduction source ID")
    for r in records:
        page = pages[r["page"]]
        if "".join(r["raw_form"].split()) not in page:
            raise ValueError(f"Missing source form: {r['id']}")
        allowed = page
        if r["id"] in {"T1_Tsuchida1969_R05", "T1_Tsuchida1969_R09"}:
            allowed = allowed.replace("v́", "ɨ́")
        if r["raw_form"] == "kumakaɨn(ɨ)":
            allowed += "kumakaɨnɨ"  # Explicit optional echo vowel, POL-028.
        for value in [r["form"], *r["variants"], *(t["text"] for t in r["translations"])]:
            if "".join(value.split()) not in allowed:
                raise ValueError(f"Reading absent from source: {r['id']}: {value}")
        if r.get("word_gloss") and r["word_gloss"] not in page:
            raise ValueError(f"Analyzed gloss absent from source: {r['id']}")
        if "same_as" in r:
            target = by_id[r["same_as"]]
            if any(r[k] != target[k] for k in ("form", "variants", "translations", "profile", "language")):
                raise ValueError(f"Reference reuse changed: {r['id']}")
    return [r for r in records if "same_as" not in r]


def identity(record: dict) -> tuple[str, str, str]:
    language = "Saaroa" if record["language"] == "xsr" else "Kanakanavu"
    text_id = "ILCAA_KANAKANAVU_TEXTS_INTRO_" + record["profile"].upper()
    file = f"{language}/ILCAA_KanakanavuTexts_intro_{record['profile']}.xml"
    return text_id, f"{text_id}_{record['id']}", file


def build_trees(records: list[dict], attributes: dict) -> dict[str, etree._Element]:
    trees = {}
    for record in records:
        text_id, sid, file = identity(record)
        if file not in trees:
            trees[file] = etree.Element("TEXT", attrib={
                **attributes, "id": text_id, XML_LANG: record["language"],
                "dialect": file.split("/")[0],
                "source": f"Kanakanavu Texts (2026), supplementary examples; source transcription group {record['profile']}.",
            })
        sentence = append_sentence(trees[file], sid, f"PDF page {record['page']}; {record['id']}", record, record["notes"])
        if record.get("word_gloss"):
            word = etree.SubElement(sentence, "W", id=sid + "W001")
            etree.SubElement(word, "FORM", kindOf="original").text = record["form"]
            etree.SubElement(word, "TRANSL", attrib={XML_LANG: "eng", "kindOf": "original"}).text = record["word_gloss"]
            for i, source in enumerate(record["morphemes"], 1):
                morph = etree.SubElement(word, "M", id=f"{sid}W001M{i:03d}")
                etree.SubElement(morph, "FORM", kindOf="original").text = source["form"]
                etree.SubElement(morph, "TRANSL", attrib={XML_LANG: "eng", "kindOf": "original"}).text = source["gloss"]
    return trees


def write_xml(folder: Path, data_path: Path, workspace: Path, attributes: dict):
    records = load_records(data_path, workspace)
    paths, index, tokens = [], [], []
    for old in folder.glob("*/ILCAA_KanakanavuTexts_intro_*.xml"):
        old.unlink()
    for file, root in build_trees(records, attributes).items():
        path = folder / file
        path.parent.mkdir(parents=True, exist_ok=True)
        etree.ElementTree(root).write(str(path), encoding="UTF-8", xml_declaration=True, pretty_print=True)
        paths.append(path)
    for r in records:
        text_id, sid, file = identity(r)
        index.append({"xml_file": file, "text_id": text_id, "sentence_id": sid,
                      "unit_id": sid, "source_unit_id": r["id"],
                      "physical_page_start": r["page"], "physical_page_end": r["page"],
                      "quality_status": "source_lexical_record", "word_tier_included": bool(r.get("word_gloss")),
                      "morpheme_tier_included": bool(r.get("morphemes"))})
        if r.get("word_gloss"):
            for level, suffix, parent, form, gloss in [
                ("W", "W001", sid, r["form"], r["word_gloss"]),
                *(("M", f"W001M{i:03d}", sid + "W001", m["form"], m["gloss"])
                  for i, m in enumerate(r["morphemes"], 1)),
            ]:
                tokens.append({"xml_file": file, "sentence_id": sid, "element_type": level,
                               "element_id": sid + suffix, "parent_id": parent,
                               "source_token_clean": form, "gloss_token_clean": gloss,
                               "physical_page": r["page"]})
    return paths, index, tokens


def audit_xml(folder: Path, data_path: Path, workspace: Path, attributes: dict) -> list[str]:
    findings = []
    for file, expected in build_trees(load_records(data_path, workspace), attributes).items():
        path = folder / file
        if not path.is_file():
            findings.append(f"Missing introduction source file: {file}")
            continue
        actual = etree.parse(str(path), etree.XMLParser(remove_blank_text=True)).getroot()
        # Compare source structure only. Derived tiers, if present, belong to
        # shared tools and need their separate final-output review.
        for elem in actual.xpath(".//PHON | .//FORM[@kindOf='standard']"):
            elem.getparent().remove(elem)
        if etree.tostring(actual, method="c14n") != etree.tostring(expected, method="c14n"):
            findings.append(f"Introduction source readings or metadata differ: {file}")
    return findings

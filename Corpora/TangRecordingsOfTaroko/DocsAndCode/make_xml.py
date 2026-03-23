#!/usr/bin/env python3
"""
make_xml.py
Generate skeleton XML files (one per .wav file in Audio/) and write them to XML/.
The <TEXT> header attributes are left as empty placeholders to be filled in later.
"""

import json
import os
import re
from pathlib import Path
from xml.etree import ElementTree as ET

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR    = Path(__file__).parent
AUDIO_DIR     = SCRIPT_DIR / "Audio" / "Truku"
METADATA_DIR  = SCRIPT_DIR / "Metadata"
XML_DIR       = SCRIPT_DIR / "XML" / "Truku"

# ── Citation formatter ────────────────────────────────────────────────────────
def format_citation(credit_text):
    """Convert a PARADISEC creditText string to an APA-style citation."""
    # Extract unique person names ("First Last (role)" pattern)
    names = re.findall(r'([A-Z][^,(]+?) \(\w+\)', credit_text)
    seen, unique_names = set(), []
    for name in names:
        name = name.strip()
        if name not in seen:
            seen.add(name)
            unique_names.append(name)

    # Reformat as "Last, First"
    def invert(name):
        parts = name.split()
        return f"{parts[-1]}, {' '.join(parts[:-1])}" if len(parts) >= 2 else name
    author_str = "; ".join(invert(n) for n in unique_names)

    # Year
    year = (re.search(r'\b(\d{4})\b', credit_text) or type('', (), {'group': lambda *_: ''})()).group(1)

    # Title: text between "Year. " and the next "."
    title_match = re.search(r'\d{4}\.\s+(.+?)\.', credit_text)
    title = title_match.group(1).strip() if title_match else ""
    if title:
        title = title[0].upper() + title[1:]  # sentence case

    # DOI URL
    doi_match = re.search(r'(https?://\S+)', credit_text)
    doi = doi_match.group(1) if doi_match else ""

    return f"{author_str}. ({year}). {title}. Paradisec. {doi}"


def format_bibtex(credit_text):
    """Convert a PARADISEC creditText string to a BibTeX @misc entry."""
    # Reuse the same parsing as format_citation
    names = re.findall(r'([A-Z][^,(]+?) \(\w+\)', credit_text)
    seen, unique_names = set(), []
    for name in names:
        name = name.strip()
        if name not in seen:
            seen.add(name)
            unique_names.append(name)

    def invert(name):
        parts = name.split()
        return f"{parts[-1]}, {' '.join(parts[:-1])}" if len(parts) >= 2 else name
    author_str = " and ".join(invert(n) for n in unique_names)

    year = (re.search(r'\b(\d{4})\b', credit_text) or type('', (), {'group': lambda *_: ''})()).group(1)

    title_match = re.search(r'\d{4}\.\s+(.+?)\.', credit_text)
    title = title_match.group(1).strip() if title_match else ""
    if title:
        title = title[0].upper() + title[1:]

    doi_match = re.search(r'(https?://\S+)', credit_text)
    doi = doi_match.group(1) if doi_match else ""

    # BibTeX cite key: last name of first author (lowercase) + year + first word of title (lowercase)
    first_last = unique_names[0].split()[-1].lower() if unique_names else "unknown"
    title_word = re.sub(r'[^a-z]', '', title.split()[0].lower()) if title else "untitled"
    citekey = f"{first_last}{year}{title_word}"

    return (
        f"@misc{{{citekey}, "
        f"author = {{{author_str}}}, "
        f"title = {{{title}}}, "
        f"year = {{{year}}}, "
        f"publisher = {{Paradisec}}, "
        f"howpublished = {{\\url{{{doi}}}}}}}"
    )

def load_metadata():
    meta = {}
    for json_path in METADATA_DIR.glob("*-ro-crate-metadata.json"):
        with open(json_path, encoding="utf-8") as fh:
            data = json.load(fh)
        # prefix = first two dash-separated parts of the filename, e.g. "AIT1-001"
        prefix = "-".join(json_path.stem.split("-")[:2])
        meta[prefix] = data["metadata"]
    return meta

metadata = load_metadata()

# ── Create output directory if needed ─────────────────────────────────────────
XML_DIR.mkdir(exist_ok=True)

# ── Discover wav files ─────────────────────────────────────────────────────────
wav_files = sorted(AUDIO_DIR.glob("*.wav"))

if not wav_files:
    print("No .wav files found in Audio/")
else:
    for wav_path in wav_files:
        wav_name   = wav_path.name                      # e.g. AIT1-001-1.wav
        stem       = wav_path.stem                      # e.g. AIT1-001-1
        xml_path   = XML_DIR / f"{stem}.xml"

        # Derive item prefix and look up metadata
        prefix     = "-".join(stem.split("-")[:2])      # e.g. "AIT1-001"
        meta       = metadata.get(prefix, {})
        source     = meta.get("@id", "")
        citation   = format_citation(meta.get("creditText", ""))
        bibtex     = format_bibtex(meta.get("creditText", ""))

        # Build the XML tree
        text_elem = ET.Element("TEXT", attrib={
            "id":             stem,
            "xml:lang":       "trv",
            "dialect":        "Truku",
            "audio":          wav_name,
            "source":         source,
            "copyright":      "",
            "citation":       citation,
            "BibTeX_citation": bibtex,
        })
        text_elem.text = "\n    "                       # indent before AUDIO

        audio_elem = ET.SubElement(text_elem, "AUDIO", file=wav_name)
        audio_elem.tail = "\n"                          # newline after AUDIO

        tree = ET.ElementTree(text_elem)
        ET.indent(tree, space="    ")                   # pretty-print (Python ≥ 3.9)

        with open(xml_path, "w", encoding="utf-8") as fh:
            fh.write("<?xml version='1.0' encoding='UTF-8'?>\n")
            tree.write(fh, encoding="unicode", xml_declaration=False)
            fh.write("\n")

        print(f"  wrote {xml_path.relative_to(SCRIPT_DIR)}")

    print(f"\nDone — {len(wav_files)} XML file(s) written to XML/")

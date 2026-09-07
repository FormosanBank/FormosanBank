#!/usr/bin/env python3
"""
make_xml.py
Generate one XML file per recording (audio-only TEXT + AUDIO) and write them to
the corpus's XML/Truku/.

The recordings themselves are not an input. Every WAV in the four Paradisec
items is enumerated by the item metadata committed in Metadata/, so the corpus
rebuilds from this checkout alone (POL-048) without downloading a WAV.

Those four files are an *extract*, not the archive's own RO-Crate: each is a
single flattened entity wrapped as {"metadata": {...}}, with no @context and no
@graph, so every reference in it -- license, publisher, collector, root --
points at a node that was not kept. They are this corpus's only witness to
Paradisec, and nothing committed re-fetches or verifies them against it.
"""

import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR    = Path(__file__).resolve().parent
CORPUS_ROOT   = SCRIPT_DIR.parent
METADATA_DIR  = SCRIPT_DIR / "Metadata"
XML_DIR       = CORPUS_ROOT / "XML" / "Truku"

# The licence every TEXT carries. A constant because the committed metadata
# cannot supply it: its `license` is {"@id": "#license-3-a6e13b67"}, a reference
# into a graph the extract does not include. The value rests on Prof. Apay
# Tang's grant.
COPYRIGHT = "CC BY-NC"

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


def item_recordings(meta):
    """The WAV filenames the item's RO-Crate metadata enumerates."""
    return sorted(
        Path(part["@id"]).name
        for part in meta.get("hasPart", [])
        if str(part.get("@id", "")).lower().endswith(".wav")
    )

metadata = load_metadata()

# ── Create output directory if needed ─────────────────────────────────────────
XML_DIR.mkdir(parents=True, exist_ok=True)

# ── Discover the recordings from the committed metadata ───────────────────────
recordings = sorted(
    (wav_name, prefix)
    for prefix, meta in metadata.items()
    for wav_name in item_recordings(meta)
)

if not recordings:
    raise SystemExit("No recordings enumerated in Metadata/")

expected = {Path(wav_name).with_suffix(".xml").name for wav_name, _ in recordings}
stale = {path.name for path in XML_DIR.glob("*.xml")} - expected
if stale:
    raise SystemExit(f"XML/Truku/ holds files the metadata does not list: {sorted(stale)}")

for wav_name, prefix in recordings:
    stem     = Path(wav_name).stem                  # e.g. AIT1-001-1
    xml_path = XML_DIR / f"{stem}.xml"
    meta     = metadata[prefix]

    # Build the XML tree
    text_elem = ET.Element("TEXT", attrib={
        "id":             stem,
        "xml:lang":       "trv",
        "dialect":        "Truku",
        "audio":          wav_name,
        "source":         meta["@id"],
        "copyright":      COPYRIGHT,
        "citation":       format_citation(meta["creditText"]),
        "BibTeX_citation": format_bibtex(meta["creditText"]),
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

    print(f"  wrote {xml_path.relative_to(CORPUS_ROOT)}")

print(f"\nDone — {len(recordings)} XML file(s) written to XML/Truku/")

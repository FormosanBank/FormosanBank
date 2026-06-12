"""
Build FormosanBank XML for the NTU Paiwan data NOT already published as Y1 read-speech:
  - Y2 read-speech            (NTU_NewDownload/NTU_Y2/<subj>/*.eaf)           -> fully transcribed
  - Y1 spontaneous 1-min      (NTU_NewDownload/Y1 ELAN 1 min perfect .../*.eaf) -> two-file partial
  - Y2 spontaneous 1-min      (NTU_NewDownload/Y2 ELAN 1 min perfect .../*.eaf) -> two-file partial

Design / conventions:
  - Every public identifier (id, source, audio filename, S audio @file) uses the PUBLIC PSEUDONYM.
    Real names and NTU subject codes NEVER appear in the output (only public pseudonyms).
  - Faithful text: collapse internal whitespace/newlines only; PRESERVE the curly apostrophe
    U+2019 (the Paiwan glottal stop). Orthography normalisation is clean_xml's job, later.
  - Partial recordings use the two-file (WilangYutas) model: a transcribed-window file plus a
    <stem>_untranscribed.xml (TEXT + AUDIO, no S) pointing at the full recording.
  - Emits FORM kindOf="original" + AUDIO only. The standard tier and PHON are added later by
    standardize.py --copy and add_phonology.py (Phase 3), matching how Y1 was produced.

The real-name/code -> pseudonym map is the private CodeAndDocs/speaker_key.csv.
Output goes to a staging dir (default: new_xml/Paiwan/<Pseudonym>/) so nothing is clobbered.
"""
import argparse
import csv
import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

CITATION = ("Le Ferrand, É., Prud'hommeaux, E., Hartshorne, J. K., & Sung, L.-M. (2024). "
            "NTU Paiwan ASR Corpus. Electronic Resource.")
BIBTEX = ("@electronic{leferrand2024ntu, author = {Le Ferrand, {\\'E}ric and Prud'hommeaux, "
          "Emily and Hartshorne, Joshua K. and Sung, Li-May}, year = {2024}, "
          "title = {{NTU} {Paiwan} {ASR} Corpus},type = {Electronic Resource}}")

# The real-name -> pseudonym filename patterns live ONLY in the private speaker_key.csv (which is
# not part of the published corpus), so this script contains no real names and is safe to publish.
KEY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "speaker_key.csv")
_KEY_CACHE = None


def _load_key(key_path=None):
    """Return (patterns, dialects) from the private speaker key.

    patterns: list of (filename_regex, pseudonym), tried top-to-bottom.
    dialects: {pseudonym: dialect}.
    """
    global _KEY_CACHE
    if key_path is None and _KEY_CACHE is not None:
        return _KEY_CACHE
    path = key_path or KEY_PATH
    if not os.path.exists(path):
        raise SystemExit(
            f"speaker_key.csv not found at {path}.\nThis private real-name->pseudonym mapping is "
            "required to pseudonymise the NTU Paiwan sources; it lives in the private dev repo only."
        )
    patterns, dialects = [], {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader((ln for ln in f if not ln.startswith("#"))):
            patterns.append((row["filename_regex"], row["pseudonym"]))
            dialects[row["pseudonym"]] = row["dialect"]
    result = (patterns, dialects)
    if key_path is None:
        _KEY_CACHE = result
    return result


def load_dialects(key_path):
    """pseudonym -> dialect, from the private speaker key."""
    return _load_key(key_path)[1]


def resolve_speaker(stem):
    """Return (pseudonym, pseudonymized_stem) for a source filename stem, or (None, None)."""
    patterns, _ = _load_key()
    for pat, pseud in patterns:
        if re.search(pat, stem, flags=re.IGNORECASE):
            return pseud, re.sub(pat, pseud, stem, flags=re.IGNORECASE)
    return None, None


def clean_text(value):
    """Collapse whitespace/newlines; preserve all letters incl. U+2019 glottal stop."""
    return re.sub(r"\s+", " ", (value or "").replace("\xa0", " ")).strip()


def parse_eaf(path):
    """Return (audio_basename, [(start_s, end_s, text, ann_id), ...] sorted by start).

    Takes every time-aligned annotation that contains at least one letter. The letter
    requirement drops the numbering tier ("001", "002", ...) regardless of which ELAN
    tier name it carries -- necessary because the transcription vs numbering tier names
    are inconsistent across files (some put transcription on 'default', others on
    'default-cp').
    """
    root = ET.parse(path).getroot()
    media = root.find(".//MEDIA_DESCRIPTOR")
    audio = os.path.basename(media.get("MEDIA_URL")) if (media is not None and media.get("MEDIA_URL")) else None
    slots = {s.get("TIME_SLOT_ID"): int(s.get("TIME_VALUE"))
             for s in root.findall(".//TIME_SLOT") if s.get("TIME_VALUE") is not None}

    utts = []
    for a in root.findall(".//ALIGNABLE_ANNOTATION"):
        v = a.find("ANNOTATION_VALUE")
        text = clean_text(v.text if v is not None else "")
        if not text or not any(ch.isalpha() for ch in text):
            continue
        s = slots.get(a.get("TIME_SLOT_REF1"))
        e = slots.get(a.get("TIME_SLOT_REF2"))
        if s is None or e is None:
            continue
        utts.append((s / 1000.0, e / 1000.0, text, a.get("ANNOTATION_ID")))
    utts.sort(key=lambda u: (u[0], u[1]))
    return audio, utts


def _secs(x):
    return f"{x:.3f}"


def make_root(pseud, pseud_stem, audio_under, dialect):
    root = ET.Element("TEXT")
    root.set("id", f"NTU_Pwn_{pseud}_{pseud_stem}")
    root.set("xml:lang", "pwn")
    root.set("source", f"NTU Paiwan Data, Participant {pseud}, file {pseud_stem}")
    root.set("audio", audio_under)
    root.set("copyright", "CC-BY")
    root.set("citation", CITATION)
    root.set("BibTeX_citation", BIBTEX)
    root.set("dialect", dialect)
    return root


def build_transcribed(pseud, pseud_stem, dialect, utts):
    audio_under = pseud_stem.replace(" ", "_") + ".wav"
    root = make_root(pseud, pseud_stem, audio_under, dialect)
    for (s, e, text, ann_id) in utts:
        S = ET.SubElement(root, "S")
        S.set("id", ann_id)
        form = ET.SubElement(S, "FORM")
        form.set("kindOf", "original")
        form.text = text
        au = ET.SubElement(S, "AUDIO")
        au.set("start", _secs(s))
        au.set("end", _secs(e))
        au.set("file", f"{pseud_stem.replace(' ', '_')}_{ann_id}.wav")
    return root


def build_untranscribed(pseud, pseud_stem, dialect):
    audio_under = pseud_stem.replace(" ", "_") + ".wav"
    root = make_root(pseud, f"{pseud_stem}_untranscribed", audio_under, dialect)
    au = ET.SubElement(root, "AUDIO")
    au.set("file", audio_under)
    return root


def write_xml(root, out_dir, filename):
    os.makedirs(out_dir, exist_ok=True)
    rough = ET.tostring(root, "utf-8")
    pretty = minidom.parseString(rough).toprettyxml(indent="    ")
    with open(os.path.join(out_dir, filename), "w", encoding="utf-8") as fh:
        fh.write(pretty)


def process(eaf_path, dialects, out_root, partial):
    stem = os.path.splitext(os.path.basename(eaf_path))[0].strip()
    stem = re.sub(r"\s*1\s*min$", "", stem).strip()          # drop trailing " 1 min"
    pseud, pseud_stem = resolve_speaker(stem)
    if pseud is None:
        return ("UNRESOLVED", stem)
    audio, utts = parse_eaf(eaf_path)
    if not utts:
        return ("EMPTY", stem)
    # the pseudonymized output stem keeps the topic/code but swaps in the pseudonym
    pseud_stem = re.sub(r"\s+", " ", pseud_stem).strip()
    out_dir = os.path.join(out_root, "Paiwan", pseud)
    root = build_transcribed(pseud, pseud_stem, dialects[pseud], utts)
    write_xml(root, out_dir, pseud_stem.replace(" ", "_") + ".xml")
    if partial:
        unt = build_untranscribed(pseud, pseud_stem, dialects[pseud])
        write_xml(unt, out_dir, pseud_stem.replace(" ", "_") + "_untranscribed.xml")
    return ("OK", pseud)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(here)
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default=os.path.join(here, "speaker_key.csv"))
    ap.add_argument("--new-download", default=os.path.join(repo, "NTU_NewDownload"))
    ap.add_argument("--out", default=os.path.join(repo, "new_xml"))
    args = ap.parse_args()

    dialects = load_dialects(args.key)
    nd = args.new_download
    regions = [
        ("Y2 read-speech", os.path.join(nd, "NTU_Y2"), False, "*.eaf", True),
        ("Y1 spontaneous", os.path.join(nd, "Y1 ELAN 1 min perfect transcription"), True, "*.eaf", False),
        ("Y2 spontaneous", os.path.join(nd, "Y2 ELAN 1 min perfect transcription"), True, "*.eaf", False),
    ]
    summary = {}
    for name, base, partial, _pat, recursive in regions:
        eafs = []
        for dp, _dn, fns in os.walk(base):
            for fn in fns:
                if fn.lower().endswith(".eaf"):
                    eafs.append(os.path.join(dp, fn))
            if not recursive:
                break
        counts = {"OK": 0, "EMPTY": [], "UNRESOLVED": []}
        for p in sorted(eafs):
            status, info = process(p, dialects, args.out, partial)
            if status == "OK":
                counts["OK"] += 1
            else:
                counts[status].append(info)
        summary[name] = (len(eafs), counts)
        print(f"\n[{name}] {len(eafs)} eaf -> OK={counts['OK']} "
              f"EMPTY={len(counts['EMPTY'])} UNRESOLVED={len(counts['UNRESOLVED'])}")
        for k in ("EMPTY", "UNRESOLVED"):
            if counts[k]:
                print(f"   {k}: {counts[k]}")
    print(f"\nOutput under: {args.out}/Paiwan/<Pseudonym>/")


if __name__ == "__main__":
    main()

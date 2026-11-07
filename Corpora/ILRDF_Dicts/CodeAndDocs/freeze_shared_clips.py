#!/usr/bin/env python3
"""One-off: decide what happens to recordings that main (2024) attached to
several different sentences, and freeze it in source_data/shared_clips.json.

Not part of reproduction: run once against the built XML of a6e6aaa9d (the
last build before the decision); the build reads only the frozen table.

    python CodeAndDocs/freeze_shared_clips.py

A shared clip is one AUDIO (same url, start, end) on two or more S whose
original FORM differs -- validate_xml.py V162. In every case it is main's
recording (2024 url; the member files are byte-identical copies) kept because
the sentence has no usable 2026 recording of its own.

Maintainer ruling 2026-10-18, quoted: "2026 source decides; merge the 18
(Recommended) -- For the 267 different/related pairs, the recording stays on
the sentence the 2026 source attaches it to and the other loses it (if the
2026 source can't tell, it becomes untranscribed audio). The 18 variant/same
pairs are one sentence printed twice: merge each into one S like the earlier
duplicates (keep the first id; the other reading as an alternative), keeping
the recording. Every id disclosed."

Classes, on original FORMs lower-cased, '?' read as 'ʉ' (the source's
corruption of it) and punctuation removed, for the LEAST similar pair of a
group:  same      identical word sequence
        near      difflib ratio of the word sequences >= 0.8
        related   shared words >= half the shorter sentence
        different otherwise
"Which sentence the 2026 source attaches it to": the 2026 records carrying a
recording with the same SHA-256, mapped to their published ids.
"""
from __future__ import annotations

import collections
import difflib
import itertools
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import generate_xml as g
from audio_recordings import AudioTable
from ilrdf_source import (extract_sentences, load_audio_exclusions,
                          load_translation_exclusions, load_translation_overrides,
                          verify_and_load_snapshot)

OUT = g.SOURCE_DATA / "shared_clips.json"
RULING = (
    "Maintainer 2026-10-18: \"2026 source decides; merge the 18 (Recommended) -- For "
    "the 267 different/related pairs, the recording stays on the sentence the 2026 "
    "source attaches it to and the other loses it (if the 2026 source can't tell, it "
    "becomes untranscribed audio). The 18 variant/same pairs are one sentence printed "
    "twice: merge each into one S like the earlier duplicates (keep the first id; the "
    "other reading as an alternative), keeping the recording. Every id disclosed.\"")
RANK = {"same": 0, "near": 1, "related": 2, "different": 3}
_OPT = re.compile(r"-opt\d*$")


def words(text: str) -> list[str]:
    text = text.lower().replace("?", "ʉ")
    return re.sub(r"[^\w'ʼʉ^:]+", " ", text).split()


def pair_class(a: str, b: str) -> str:
    left, right = words(a), words(b)
    if left == right:
        return "same"
    if difflib.SequenceMatcher(None, left, right).ratio() >= 0.8:
        return "near"
    common = sum((collections.Counter(left) & collections.Counter(right)).values())
    if common / max(1, min(len(left), len(right))) >= 0.5:
        return "related"
    return "different"


def _number(identifier: str) -> int:
    return int(_OPT.sub("", identifier).rsplit("_", 1)[1])


def main() -> int:
    table = AudioTable()
    groups = []
    for path in sorted(g.XML_DIR.glob("*/*.xml")):
        if path.name.endswith("_dictionary.xml"):
            continue
        language = path.parent.name
        by_clip: dict[tuple, list[dict]] = collections.defaultdict(list)
        for s in ET.parse(path).getroot().iter("S"):
            audio = s.find("AUDIO")
            if audio is None:
                continue
            form = next(f for f in s.findall("FORM")
                        if f.get("kindOf") == "original" and f.get("ver") is None)
            by_clip[(audio.get("url"), audio.get("start"), audio.get("end"))].append(
                {"s_id": s.get("id"), "base_id": _OPT.sub("", s.get("id")),
                 "file": audio.get("file"), "text": " ".join((form.text or "").split())})
        for key, members in by_clip.items():
            if len({m["text"] for m in members}) > 1:
                groups.append({"language": language, "url": key[0], "start": key[1],
                               "end": key[2], "members": members})

    manifest = json.loads((g.SOURCE_DATA / "source_manifest.json").read_text(encoding="utf-8"))
    excluded = load_audio_exclusions(g.SOURCE_DATA / "audio_exclusions.json")
    overrides = load_translation_overrides(g.SOURCE_DATA / "translation_language_overrides.json")
    exclusions = load_translation_exclusions(g.SOURCE_DATA / "source_content_exclusions.json")
    owners: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    for language in sorted({grp["language"] for grp in groups}):
        snapshot = verify_and_load_snapshot(language, g.SNAPSHOT_DIR, manifest)
        untranslated: dict = {}
        sentences, _ = extract_sentences(language, snapshot, excluded, overrides, set(),
                                         exclusions, set(), untranslated=untranslated)
        published = {r["record_id"]: r["published_id"] for r in g._main_rows(language)
                     if r["status"] in ("kept", "merged-kept")}
        for record in [*sentences, *untranslated.values()]:
            for url in record.audio_urls:
                fp = table.by_url.get(url)
                if fp is not None and fp.sha256:
                    owners[(language, fp.sha256)].add(
                        published.get(record.identifier, record.identifier))

    out = []
    for grp in groups:
        language, members = grp["language"], grp["members"]
        sha = table.main_file(language, members[0]["file"]).sha256
        if any(table.main_file(language, m["file"]).sha256 != sha for m in members):
            raise ValueError(f"{grp['url']}: members are not byte-identical")
        cls = max((pair_class(a["text"], b["text"])
                   for a, b in itertools.combinations(members, 2)), key=RANK.get)
        attached = sorted(owners.get((language, sha), set()))
        inside = [m["base_id"] for m in members if m["base_id"] in attached]
        if cls in ("same", "near"):
            ordered = sorted(members, key=lambda m: _number(m["s_id"]))
            outcome = {"outcome": "merge", "keep": ordered[0]["base_id"],
                       "retire": [m["base_id"] for m in ordered[1:]]}
        elif len(inside) == 1:
            outcome = {"outcome": "keep on the sentence the 2026 source attaches it to",
                       "keep": inside[0]}
        elif attached and not inside:
            outcome = {"outcome": "the 2026 source attaches it to another sentence"}
        else:
            outcome = {"outcome": "untranscribed: the 2026 source cannot tell"}
        out.append({"language": language, "class": cls, "url": grp["url"],
                    "start": grp["start"], "end": grp["end"], "sha256": sha,
                    "attached_in_2026": attached, **outcome,
                    "members": [{k: m[k] for k in ("s_id", "base_id", "file", "text")}
                                for m in members]})
    out.sort(key=lambda o: (o["language"], o["members"][0]["s_id"]))
    OUT.write_text(json.dumps({"ruling": RULING, "groups": out}, ensure_ascii=False,
                              indent=1) + "\n", encoding="utf-8")
    tally = collections.Counter((o["class"], o["outcome"]) for o in out)
    print(f"wrote {OUT.name}: {len(out)} groups")
    for key, count in sorted(tally.items()):
        print(f"  {count:4d}  {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

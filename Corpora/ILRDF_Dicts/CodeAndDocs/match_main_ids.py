#!/usr/bin/env python3
"""Match main's 2024 sentences to 2026 source records; freeze the result.

POL-037, maintainer ruling 2026-10-15: "Keep main's ids for the 96,988 (frozen
in the ledger); GUID ids only for new records." This script does the matching
once and writes source_data/main_id_ledger.csv. The build reads that ledger
and never re-matches, so a rebuild cannot move an id.

Run deliberately, never from generate_xml.sh:

    python CodeAndDocs/match_main_ids.py            # report only
    python CodeAndDocs/match_main_ids.py --write    # rewrite the ledger

Matching, per main sentence (main's original FORM against the snapshot's raw
originalSentence of every sentence item):

  1. text: equal after normalisation (NFC; ʼ ’ ‘ -> '; whitespace runs
     collapsed to one space; outer space stripped).
  2. fallback, only when (1) finds nothing -- text changed upstream: an item
     whose Chinese translation is identical (NFKC, all whitespace removed) AND
     whose headword / explanation / example position equals the one encoded
     in main's old audio URL,
        .../Audio/<lang>/<headword>_{n}_@_<explanation>.<example>.mp3
  3. last resort, only when (1) and (2) find nothing and ZH_UNIQUE_FALLBACK
     is set: the one sentence item in the language whose Chinese translation
     is identical. This is what the 2026-10-15 review's matcher did (its
     96,988 count includes it); it catches upstream edits that also renamed
     the headword, so the position in the old URL no longer resolves --
     `O di'i nira cira.` (main, headword di'i) vs `O diʼiʼ nira cira.`
     (2026, same translation 他是她的性伴侶。).

The matched items' GUIDs name the 2026 record (generate_xml.py merges items
by text; every GUID belongs to exactly one record). Then:

  kept            one main id <-> one 2026 record. The record publishes under
                  the main id.
  merged-kept     several main ids -> one record (main published the same
  merged-retired  sentence 2-3 times; the 2026 source has it once). "Keep the
                  first id; merge translations": the lowest main id is kept,
                  the others retired.
  withdrawn       no 2026 record. Published as on main, from the POL-035
                  snapshot (maintainer: "Keep them (marked as from the 2024
                  scrape)").

A main id that reaches more than one 2026 record has no ruling; the script
reports it and refuses to write.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import io
import json
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import unquote

from ilrdf_source import (
    LANGUAGES,
    extract_sentences,
    load_audio_exclusions,
    load_translation_exclusions,
    load_translation_overrides,
    verify_and_load_snapshot,
)
import main_2024

BASE = Path(__file__).resolve().parent
SOURCE_DATA = BASE / "source_data"
LEDGER = SOURCE_DATA / "main_id_ledger.csv"
FIELDS = ["main_id", "language", "status", "published_id", "record_id",
          "source_guids", "matched_by"]
#: Step 3 above. Without it, 336 main sentences whose text was edited upstream
#: would be published twice: once as withdrawn (main's text) and once as a new
#: 2026 record with a new id.
ZH_UNIQUE_FALLBACK = True
_AUDIO_KEY = re.compile(r".*/Audio/[^/]+/(.*)_\{(\d+)\}_@_(\d+)\.(\d+)\.mp3$")


def norm_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value or "")
    value = value.replace("ʼ", "'").replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", value).strip()


def norm_zh(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value or ""))


def norm_headword(value: str) -> str:
    return re.sub(r"\d+$", "", norm_text(value).lower())


def audio_key(audio: list[dict[str, str]]):
    if not audio:
        return None
    match = _AUDIO_KEY.match(audio[0].get("url", ""))
    if match is None:
        return None
    return (norm_headword(unquote(match.group(1))), int(match.group(3)),
            int(match.group(4)))


def snapshot_items(snapshot: dict):
    """Every sentence item with its headword / explanation / example position."""
    for response in snapshot.get("responses", []):
        for word in response.get("words") or []:
            for e_index, explanation in enumerate(word.get("explanationItems") or [], 1):
                for s_index, item in enumerate(explanation.get("sentenceItems") or [], 1):
                    yield {
                        "guid": item["id"],
                        "text": norm_text(item.get("originalSentence") or ""),
                        "zh": norm_zh(item.get("chineseSentence") or ""),
                        "key": (norm_headword(word.get("name") or ""), e_index, s_index),
                    }


def match_language(language: str, manifest: dict) -> tuple[list[dict], Counter]:
    snapshot = verify_and_load_snapshot(language, SOURCE_DATA / "snapshots", manifest)
    untranslated: dict = {}
    records, _ = extract_sentences(
        language, snapshot,
        load_audio_exclusions(SOURCE_DATA / "audio_exclusions.json"),
        load_translation_overrides(SOURCE_DATA / "translation_language_overrides.json"),
        set(),
        load_translation_exclusions(SOURCE_DATA / "source_content_exclusions.json"),
        set(),
        untranslated=untranslated,
    )
    owner: dict[str, str] = {}
    for record in [*records, *untranslated.values()]:
        for guid in record.source_ids:
            if guid in owner and owner[guid] != record.identifier:
                raise ValueError(f"{language}: GUID {guid} in two records")
            owner[guid] = record.identifier
    guids_of = {r.identifier: sorted(r.source_ids) for r in [*records, *untranslated.values()]}

    by_text: dict[str, set[str]] = defaultdict(set)
    by_zh_key: dict[tuple, set[str]] = defaultdict(set)
    by_zh: dict[str, set[str]] = defaultdict(set)
    for item in snapshot_items(snapshot):
        by_text[item["text"]].add(item["guid"])
        by_zh_key[(item["zh"], item["key"])].add(item["guid"])
        by_zh[item["zh"]].add(item["guid"])

    _, mains = main_2024.load(language)
    rows: list[dict] = []
    counts: Counter = Counter()
    reached: dict[str, list] = {}
    for main in mains:
        guids = by_text.get(norm_text(main.original), set())
        how = "text"
        if not guids:
            how = "translation+position"
            key = audio_key(main.audio)
            zh = norm_zh(main.translations[0]["_text"]) if main.translations else ""
            guids = by_zh_key.get((zh, key), set()) if key and zh else set()
            if not guids and ZH_UNIQUE_FALLBACK and zh and len(by_zh.get(zh, ())) == 1:
                how = "translation (unique)"
                guids = by_zh[zh]
        record_ids = sorted({owner[g] for g in guids if g in owner})
        if not guids:
            how = ""
        reached[main.identifier] = record_ids
        rows.append({"main": main, "how": how, "records": record_ids})

    claims: dict[str, list] = defaultdict(list)
    for row in rows:
        if len(row["records"]) == 1:
            claims[row["records"][0]].append(row["main"])

    out: list[dict] = []
    for row in rows:
        main = row["main"]
        base = {"main_id": main.identifier, "language": language,
                "matched_by": row["how"]}
        if not row["records"]:
            counts["withdrawn"] += 1
            if row["how"]:
                counts["withdrawn: text matched an item outside every record"] += 1
            out.append({**base, "status": "withdrawn",
                        "published_id": main.identifier, "record_id": "",
                        "source_guids": "", "matched_by": ""})
            continue
        if len(row["records"]) > 1:
            counts["AMBIGUOUS: one main id -> several 2026 records"] += 1
            out.append({**base, "status": "AMBIGUOUS", "published_id": "",
                        "record_id": " ".join(row["records"]), "source_guids": ""})
            continue
        record_id = row["records"][0]
        group = sorted(claims[record_id], key=lambda m: m.number)
        guids = " ".join(guids_of[record_id])
        if len(group) == 1:
            status = "kept"
        elif group[0] is main:
            status = "merged-kept"
        else:
            status = "merged-retired"
        counts[status] += 1
        counts[f"{status} via {row['how']}"] += 1
        if status == "kept":
            counts["kept: untranslated record" if record_id in
                   {u.identifier for u in untranslated.values()} else
                   "kept: translated record"] += 1
        out.append({**base, "status": status,
                    "published_id": group[0].identifier,
                    "record_id": record_id, "source_guids": guids})
    groups = {r["record_id"] for r in out if r["status"] == "merged-kept"}
    counts["merged groups"] += len(groups)
    return out, counts


def render(rows: list[dict]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((SOURCE_DATA / "source_manifest.json").read_text(encoding="utf-8"))
    rows: list[dict] = []
    total: Counter = Counter()
    for language in LANGUAGES:
        out, counts = match_language(language, manifest)
        rows.extend(out)
        total.update(counts)
        print(f"{language}: {dict(sorted(counts.items()))}")
    print(f"TOTAL main ids: {len(rows)}")
    for key, value in sorted(total.items()):
        print(f"  {key}: {value}")
    if any(r["status"] == "AMBIGUOUS" for r in rows):
        print("refusing to write: ambiguous matches have no ruling", file=sys.stderr)
        return 1
    if args.write:
        LEDGER.write_text(render(rows), encoding="utf-8")
        print(f"wrote {LEDGER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate, restore, or audit canonical XML from committed ILRDF snapshots."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

from ilrdf_source import (
    LANGUAGES,
    XML_LANG,
    Sentence,
    extract_sentences,
    load_audio_exclusions,
    load_translation_exclusions,
    load_translation_overrides,
    root_attributes,
    verify_and_load_snapshot,
)
import main_2024
from audio_recordings import (AudioTable, audio_elements, choose, load_no_audio,
                              load_second_s)


BASE = Path(__file__).resolve().parent
SOURCE_DATA = BASE / "source_data"
SNAPSHOT_DIR = SOURCE_DATA / "snapshots"
XML_DIR = BASE.parent / "XML"


#: Frozen output of match_main_ids.py: which 2026 record keeps which main id.
MAIN_LEDGER_PATH = SOURCE_DATA / "main_id_ledger.csv"
RULINGS_PATH = SOURCE_DATA / "alternative_rulings.json"
REPAIRS_PATH = SOURCE_DATA / "source_repairs.json"
#: Published old->new id table (POL-037 / POL-051), written by the build.
OLD_TO_NEW_PATH = BASE / "old_to_new_ids.csv"

#: Every recording dropped or not used, written by the build.
AUDIO_LOG_PATH = BASE / "docs" / "audio_not_published.csv"
AUDIO_LOG_FIELDS = ["language", "s_id", "origin", "url", "file", "type", "village",
                    "outcome", "same_as", "same_as_village"]

#: S/@source on main sentences that are no longer in the 2026 source.
WITHDRAWN_SOURCE = (
    "ILRDF online dictionary, 2024 scrape (as published on FormosanBank before "
    "the 2026 rebuild); no longer in ILRDF's current dictionary"
)


@dataclass
class Published:
    """One S as generate_xml.py writes it (source tiers only)."""
    identifier: str
    original: str
    translations: list[tuple[str, str]] = field(default_factory=list)
    audio: list[dict[str, str]] = field(default_factory=list)
    source: str | None = None


def _norm_zh(value: str) -> str:
    import unicodedata
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value or ""))


def _main_rows(language: str) -> list[dict[str, str]]:
    with MAIN_LEDGER_PATH.open(encoding="utf-8", newline="") as handle:
        return [r for r in csv.DictReader(handle) if r["language"] == language]


def _withdrawn_by_repair() -> dict[str, dict]:
    payload = json.loads(REPAIRS_PATH.read_text(encoding="utf-8"))
    return {r["guid"]: r for r in payload["repairs"] if r.get("action") == "withdraw"}


def _recordings(language: str, identifier: str, urls: list[str],
                village_of: dict[str, str | None], main_audio: list[dict[str, str]],
                audio: tuple, counts: Counter) -> list[dict[str, str]]:
    """AUDIO attributes for one sentence (audio_recordings.py has the rules)."""
    table, second_s, no_audio, log = audio
    start = len(log)
    chosen = choose(language, identifier, urls, village_of, main_audio, table,
                    second_s, log, no_audio)
    for row in log[start:]:
        row["language"] = language
        counts[f"audio not published: {row['outcome']}"] += 1
    for item in chosen:
        counts[f"audio: {item.origin} recording"] += 1
    if len(chosen) > 1:
        counts["sentences with 2+ distinct recordings"] += 1
    return audio_elements(language, identifier, chosen, table)


def assemble(language: str, sentences: list[Sentence], untranslated: dict,
             counts: Counter, audio: tuple
             ) -> tuple[list[Published], list[dict[str, str]], dict, list[dict]]:
    """Map 2026 records onto main's ids and add main's withdrawn sentences.

    Returns (sentences to publish, untranscribed AUDIO, main TEXT attributes,
    old->new id rows).
    """
    main_attrs, mains = main_2024.load(language)
    main_by_id = {m.identifier: m for m in mains}
    rows = _main_rows(language)
    if {r["main_id"] for r in rows} != set(main_by_id):
        raise ValueError(f"{language}: main_id_ledger.csv does not cover main exactly")
    published_id: dict[str, str] = {}
    group: dict[str, list] = defaultdict(list)
    for row in rows:
        if row["status"] in ("kept", "merged-kept", "merged-retired"):
            group[row["record_id"]].append(main_by_id[row["main_id"]])
            if row["status"] != "merged-retired":
                published_id[row["record_id"]] = row["published_id"]
    withdraw = _withdrawn_by_repair()
    old_to_new: list[dict] = []
    for row in rows:
        if row["status"] == "merged-retired":
            old_to_new.append({
                "old_id": row["main_id"], "new_id": row["published_id"],
                "change": "retired: merged duplicate",
                "reason": "main published this sentence more than once; the 2026 "
                          "source has it once. Kept the lowest main id; its S "
                          "carries every distinct translation of the copies."})

    candidates = list(sentences)
    for record in untranslated.values():
        if record.identifier in published_id:
            candidates.append(record)
            counts["kept untranslated record (claimed by a main id)"] += 1
    out: list[Published] = []
    untranscribed: list[dict[str, str]] = []
    for record in candidates:
        identifier = published_id.get(record.identifier, record.identifier)
        copies = sorted(group.get(record.identifier, []), key=lambda m: m.number)
        translations = list(record.translations)
        if len(copies) > 1:
            seen = {_norm_zh(text) for _, text in translations}
            for copy in copies:
                for item in copy.translations:
                    if _norm_zh(item["_text"]) in seen or not item["_text"].strip():
                        continue
                    seen.add(_norm_zh(item["_text"]))
                    translations.append((item.get(XML_LANG, "zho"), item["_text"]))
                    counts["merged: translation added from a main copy"] += 1
        recordings = _recordings(
            language, identifier, record.audio_urls, record.audio_class,
            [dict(a) for m in copies for a in m.audio], audio, counts)
        hit = next((withdraw[g] for g in record.source_ids if g in withdraw), None)
        if hit is not None:
            for item in recordings:
                untranscribed.append({**item, "source": (
                    f"ILRDF example {identifier}; sentence withdrawn "
                    "(source_repairs.json: action withdraw)")})
            counts["withdrawn by repair ruling (recording -> untranscribed)"] += 1
            old_to_new.append({
                "old_id": identifier, "new_id": "",
                "change": "removed",
                "reason": hit["ruling"]})
            continue
        if identifier != record.identifier:
            counts["published under a main id"] += 1
        else:
            counts["published under a new GUID id"] += 1
        out.append(Published(identifier, record.original, translations, recordings))

    for row in rows:
        if row["status"] != "withdrawn":
            continue
        main = main_by_id[row["main_id"]]
        out.append(Published(
            main.identifier, main.original,
            [(t.get(XML_LANG, "zho"), t["_text"]) for t in main.translations],
            _recordings(language, main.identifier, [], {},
                        [dict(a) for a in main.audio], audio, counts),
            WITHDRAWN_SOURCE))
        counts["withdrawn main sentence published from the 2024 snapshot"] += 1
    out.sort(key=lambda p: (p.original.casefold(), p.original, p.identifier))
    return out, untranscribed, main_attrs, old_to_new


def _build_tree(language: str, records: list[Published], untranscribed: list[dict],
                attributes: dict[str, str]) -> ET.Element:
    root = ET.Element("TEXT", attributes)
    for item in untranscribed:
        ET.SubElement(root, "AUDIO", item)
    for record in records:
        attrs = {"id": record.identifier}
        if record.source:
            attrs["source"] = record.source
        element = ET.SubElement(root, "S", attrs)
        ET.SubElement(element, "FORM", {"kindOf": "original"}).text = record.original
        translation_counts: dict[str, int] = {}
        for lang_code, text in record.translations:
            attributes_ = {XML_LANG: lang_code}
            if translation_counts.get(lang_code, 0):
                attributes_["ver"] = "alt"
            translation_counts[lang_code] = translation_counts.get(lang_code, 0) + 1
            ET.SubElement(element, "TRANSL", attributes_).text = text
        for audio in record.audio:
            ET.SubElement(element, "AUDIO", audio)
    return root


def text_attributes(language: str, snapshot_date: str, main_attrs: dict[str, str]) -> dict[str, str]:
    """TEXT attributes; dialect and glottocode restored from main (ruling §7)."""
    attributes = root_attributes(language, snapshot_date)
    ordered: dict[str, str] = {}
    for key, value in attributes.items():
        ordered[key] = value
        if key == "dialect":
            ordered[key] = main_attrs.get("dialect") or value
            if main_attrs.get("glottocode"):
                ordered["glottocode"] = main_attrs["glottocode"]
    return ordered


def _write_tree(root: ET.Element, path: Path) -> None:
    ET.indent(root, space="    ")
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(
        path, encoding="utf-8", xml_declaration=True, short_empty_elements=True
    )
    with path.open("ab") as handle:
        handle.write(b"\n")


def write_old_to_new(rows: list[dict], path: Path) -> None:
    rows = sorted(rows, key=lambda r: (r["old_id"].rsplit("_", 1)[0],
                                       int(r["old_id"].rsplit("_", 1)[1])))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["old_id", "new_id", "change", "reason"],
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


LEDGER_PATH = SOURCE_DATA / "published_ids.csv"
MODES = ("generate", "audit", "ledger")
_SPLIT_SUFFIX = re.compile(r"-opt\d*$")
_GUID_IN_ID = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


@dataclass
class LedgerRow:
    """One published id, as declared in source_data/published_ids.csv."""
    identifier: str
    source_guids: set[str] = field(default_factory=set)
    status: str = "active"
    note: str = ""


def _parse_ledger(handle) -> dict[str, LedgerRow]:
    rows: dict[str, LedgerRow] = {}
    for record in csv.DictReader(handle):
        identifier = (record.get("id") or "").strip()
        if not identifier:
            continue
        rows[identifier] = LedgerRow(
            identifier=identifier,
            source_guids=set((record.get("source_guids") or "").split()),
            status=(record.get("status") or "active").strip() or "active",
            note=(record.get("note") or "").strip(),
        )
    return rows


def load_ledger(path: Path) -> dict[str, LedgerRow]:
    if not path.exists():
        raise ValueError(
            f"missing id ledger {path}; run `generate_xml.py ledger --write` "
            "and review the diff before committing it"
        )
    with path.open(encoding="utf-8", newline="") as handle:
        return _parse_ledger(handle)


def render_ledger(rows: dict[str, LedgerRow]) -> str:
    lines = ["id,source_guids,status,note"]
    for identifier in sorted(rows):
        row = rows[identifier]
        note = row.note.replace('"', "'")
        if "," in note:
            note = f'"{note}"'
        lines.append(
            f"{identifier},{' '.join(sorted(row.source_guids))},{row.status},{note}"
        )
    return "\n".join(lines) + "\n"


def _base_id(identifier: str) -> str:
    """A split child's id resolves to the source record it came from."""
    return _SPLIT_SUFFIX.sub("", identifier)


def audit_ids(
    ledger: dict[str, LedgerRow],
    xml_ids: set[str],
    extracted: dict[str, set[str]],
) -> list[str]:
    """Ids may be deleted or added, never silently changed.

    Fails on exactly three things:
      - an id declared active that is no longer in the XML
      - an id in the XML that the ledger does not declare
      - a ledger id whose source GUIDs no longer match the source
    """
    errors: list[str] = []
    for identifier, row in sorted(ledger.items()):
        if row.status == "active" and identifier not in xml_ids:
            errors.append(
                f"{identifier}: declared active but silently deleted from the "
                "XML; suppress it in the ledger if that is intended"
            )
    for identifier in sorted(xml_ids):
        if identifier not in ledger:
            errors.append(
                f"{identifier}: present in the XML but not in the ledger; add "
                "a row deliberately if this is a new or split record"
            )
    for identifier, row in sorted(ledger.items()):
        source = extracted.get(_base_id(identifier))
        if source is None or not row.source_guids:
            continue
        if row.source_guids != source:
            errors.append(
                f"{identifier}: source GUIDs changed "
                f"{sorted(row.source_guids)} -> {sorted(source)}; the id now "
                "points at different source material"
            )
    return errors


def _audit_structure(expected: ET.Element, path: Path) -> list[str]:
    """Structural checks that survive the drop of source-drift auditing."""
    if not path.exists():
        return [f"missing XML: {path}"]
    actual = ET.parse(path).getroot()
    errors: list[str] = []
    sentences = actual.findall("S")
    ids = [item.get("id") for item in sentences]
    if None in ids:
        errors.append("sentence without an id")
    if len(set(ids)) != len(ids):
        errors.append("duplicate sentence ids")
    for sentence in sentences:
        if sentence.find("FORM[@kindOf='original']") is None:
            errors.append(f"{sentence.get('id')}: no original FORM")
            break
    return errors


def _select_languages(requested: list[str] | None) -> list[str]:
    if not requested:
        return list(LANGUAGES)
    invalid = sorted(set(requested) - LANGUAGES.keys())
    if invalid:
        raise ValueError(f"unknown languages: {', '.join(invalid)}")
    return [language for language in LANGUAGES if language in requested]


def run(mode: str, languages: list[str], write_ledger: bool = False) -> int:
    manifest = json.loads((SOURCE_DATA / "source_manifest.json").read_text(encoding="utf-8"))
    snapshot_date = manifest["snapshot_commit_date"]
    excluded_audio = load_audio_exclusions(SOURCE_DATA / "audio_exclusions.json")
    overrides = load_translation_overrides(
        SOURCE_DATA / "translation_language_overrides.json"
    )
    exclusions = load_translation_exclusions(
        SOURCE_DATA / "source_content_exclusions.json"
    )
    used_overrides: set[tuple[str, str, str]] = set()
    used_exclusions: set[tuple[str, str, str]] = set()
    audit_errors: list[str] = []
    audio_owners: dict[str, set[tuple[str, str]]] = {}
    extracted: dict[str, set[str]] = {}
    xml_ids: set[str] = set()

    old_to_new: list[dict] = []
    totals: Counter = Counter()
    audio_log: list[dict[str, str]] = []
    audio = (AudioTable(), load_second_s(), load_no_audio(), audio_log)
    for language in languages:
        snapshot = verify_and_load_snapshot(language, SNAPSHOT_DIR, manifest)
        untranslated: dict = {}
        sentences, stats = extract_sentences(
            language,
            snapshot,
            excluded_audio,
            overrides,
            used_overrides,
            exclusions,
            used_exclusions,
            untranslated=untranslated,
        )
        counts: Counter = Counter()
        records, untranscribed, main_attrs, retired = assemble(
            language, sentences, untranslated, counts, audio)
        old_to_new.extend(retired)
        totals.update(counts)
        published_of = {}
        for row in _main_rows(language):
            if row["status"] in ("kept", "merged-kept"):
                published_of[row["record_id"]] = row["published_id"]
        for sentence in [*sentences, *untranslated.values()]:
            extracted[published_of.get(sentence.identifier, sentence.identifier)] = set(
                sentence.source_ids)
        for sentence in sentences:
            for url in sentence.audio_urls:
                audio_owners.setdefault(url, set()).add((language, sentence.original))
        path = XML_DIR / language / f"{language}.xml"
        if mode == "generate":
            expected = _build_tree(language, records, untranscribed,
                                   text_attributes(language, snapshot_date, main_attrs))
            _write_tree(expected, path)
        else:
            audit_errors.extend(
                f"{language}: {error}" for error in _audit_structure(None, path)
            )
            if path.exists():
                xml_ids.update(
                    item.get("id")
                    for item in ET.parse(path).getroot().findall("S")
                    if item.get("id")
                )
                for extra in sorted(path.parent.glob(f"{language}_*.xml")):
                    xml_ids.update(
                        item.get("id")
                        for item in ET.parse(extra).getroot().findall("S")
                        if item.get("id")
                    )
        print(f"{language}: {json.dumps(asdict(stats), sort_keys=True)}")
        print(f"{language}: {json.dumps(dict(sorted(counts.items())), ensure_ascii=False)}")

    if mode == "generate" and set(languages) == set(LANGUAGES):
        rulings = json.loads(RULINGS_PATH.read_text(encoding="utf-8"))["records"]
        for item in rulings:
            if not item["publish"]:
                old_to_new.append({
                    "old_id": item["main_id"], "new_id": "", "change": "removed",
                    "reason": "maintainer ruling 2026-10-16: the source prints "
                              "alternatives that cannot be published as one "
                              "sentence; its recording is published as "
                              "untranscribed audio"})
        write_old_to_new(old_to_new, OLD_TO_NEW_PATH)
        print(f"wrote {OLD_TO_NEW_PATH.name}: {len(old_to_new)} rows")
        AUDIO_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with AUDIO_LOG_PATH.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=AUDIO_LOG_FIELDS,
                                    lineterminator="\n")
            writer.writeheader()
            writer.writerows(audio_log)
        print(f"wrote {AUDIO_LOG_PATH.name}: {len(audio_log)} rows")
        print(f"TOTAL: {json.dumps(dict(sorted(totals.items())), ensure_ascii=False)}")

    relevant_overrides = {key for key in overrides if key[0] in languages}
    unused = sorted(relevant_overrides - used_overrides)
    if unused:
        audit_errors.extend(f"unused translation-language override: {key!r}" for key in unused)
    relevant_exclusions = {key for key in exclusions if key[0] in languages}
    unused_exclusions = sorted(relevant_exclusions - used_exclusions)
    if unused_exclusions:
        audit_errors.extend(
            f"unused source-content exclusion: {key!r}" for key in unused_exclusions
        )
    if mode == "ledger":
        # The ledger is a lockfile over the BUILT tree, not over extraction:
        # it has to cover split children (…_a) and dictionary entries (…_d…),
        # neither of which extract_sentences knows about. Its protection is
        # that it is committed and reviewed by diff -- a rebuild whose ids
        # differ from the committed ledger fails the audit.
        rows: dict[str, LedgerRow] = {}
        for path in sorted(XML_DIR.rglob("*.xml")):
            for item in ET.parse(path).getroot().findall("S"):
                identifier = item.get("id")
                if not identifier:
                    continue
                guids = extracted.get(_base_id(identifier))
                if guids is None:
                    match = _GUID_IN_ID.search(identifier)
                    guids = {match.group(0)} if match else set()
                rows[identifier] = LedgerRow(
                    identifier=identifier, source_guids=set(guids))
        if write_ledger:
            LEDGER_PATH.write_text(render_ledger(rows), encoding="utf-8")
            print(f"wrote {LEDGER_PATH} ({len(rows)} ids) — review the diff "
                  "before committing")
        else:
            print(f"{len(rows)} ids would be written to {LEDGER_PATH}")
        return 0

    if mode == "audit":
        audit_errors.extend(audit_ids(load_ledger(LEDGER_PATH), xml_ids, extracted))

    ambiguous_audio = {
        url: owners for url, owners in audio_owners.items() if len(owners) > 1
    }
    if ambiguous_audio:
        for url, owners in sorted(ambiguous_audio.items())[:20]:
            audit_errors.append(
                f"audio URL belongs to multiple sentence forms: {url!r} -> {sorted(owners)!r}"
            )
        if len(ambiguous_audio) > 20:
            audit_errors.append(
                f"{len(ambiguous_audio) - 20} additional ambiguous audio URLs omitted"
            )
    if audit_errors:
        print("Audit failed:", file=sys.stderr)
        for error in audit_errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    if mode == "audit":
        print(f"Audit passed: {len(xml_ids)} published ids across "
              f"{len(languages)} languages.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode", nargs="?", choices=MODES, default="generate"
    )
    parser.add_argument("--language", action="append", dest="languages")
    parser.add_argument(
        "--write", action="store_true",
        help="with mode 'ledger', rewrite source_data/published_ids.csv",
    )
    args = parser.parse_args()
    try:
        return run(args.mode, _select_languages(args.languages), args.write)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, ET.ParseError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

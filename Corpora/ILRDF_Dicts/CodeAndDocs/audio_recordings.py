"""Which recordings each published sentence carries, and what each file is called.

Reads the frozen fingerprint table source_data/audio_fingerprints.tsv (written
once by freeze_audio_fingerprints.py; the build never downloads anything).

Maintainer rulings applied here (2026-10-17, quoted):

  one S per recording  "A. One S per distinct recording; identical copies kept
                       once". Recordings are compared by SHA-256; the first S
                       keeps the existing id, the k-th distinct recording
                       (k >= 2) goes on <id>-opt, <id>-opt3 ... ("-opt, -opt3").
  Yami villages        "village in the file name" -- <base id>_<village>.<ext>
                       -- and "These will need to result in 3 S blocks each."
                       Order: 朗島 (main's recording is the 朗島 one, so it
                       keeps the existing id), 野銀, 漁人.
  file types           "Converting WebM: no, let's just make sure they are
                       named correctly." -- the extension is the real type.
  broken files         "Drop the audio for the 157 broken files (assuming
                       these don't exist in working format in either
                       source). Same for the 3 unreachable Paiwan files."
                       Broken = all-zero or unknown:0000000000000000. A
                       sentence whose only 2026 recordings are broken or
                       unreachable falls back to main's recording.

Main's recording (FormosanBank's 2024 publication) is used, verbatim and
under its existing file name, when the sentence has no working 2026
recording, when it is byte-identical to one of the 2026 recordings ("If it
is the same, then do same sentence: 2026 text under main's id"), and for the
sentences listed in source_data/audio_rulings.json ("Second S").
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
FINGERPRINTS_PATH = BASE / "source_data" / "audio_fingerprints.tsv"
AUDIO_RULINGS_PATH = BASE / "source_data" / "audio_rulings.json"

BROKEN_TYPES = {"all-zero", "unknown:0000000000000000"}
UNREACHABLE = "unreachable"
EXTENSIONS = {"mp3": "mp3", "webm": "webm", "mp4": "mp4", "wav": "wav"}
#: Yami recording order (ruling: 朗島 keeps the existing id).
YAMI_VILLAGES = ("朗島", "野銀", "漁人")


@dataclass(frozen=True)
class Fingerprint:
    kind: str
    language: str
    key: str
    file: str
    bytes: str
    sha256: str
    type: str
    main_file: str


@dataclass
class Recording:
    """One candidate recording of a sentence."""
    origin: str                      # "main" or "2026"
    sha256: str | None
    type: str                        # real type; "" for main's files
    attributes: dict[str, str] = field(default_factory=dict)  # main's AUDIO, verbatim
    url: str = ""
    village: str | None = None
    source_file: str = ""            # 2026: the name it was downloaded under


def split_id(base: str, offset: int) -> str:
    """POL-028 naming: the first keeps the id, then -opt, -opt3, ..."""
    if offset == 0:
        return base
    return f"{base}-opt" if offset == 1 else f"{base}-opt{offset + 1}"


class AudioTable:
    def __init__(self, path: Path = FINGERPRINTS_PATH):
        self.by_url: dict[str, Fingerprint] = {}
        self.main: dict[tuple[str, str], Fingerprint] = {}
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                item = Fingerprint(**row)
                if item.kind == "2026":
                    self.by_url[item.key] = item
                elif item.kind == "main":
                    key = (item.language, item.file)
                    if key in self.main:
                        raise ValueError(f"main file listed twice: {key}")
                    self.main[key] = item
                else:
                    raise ValueError(f"unknown kind {item.kind!r}")

    def recording(self, url: str) -> Fingerprint:
        try:
            return self.by_url[url]
        except KeyError:
            raise ValueError(f"no fingerprint for 2026 recording {url}") from None

    def main_file(self, language: str, name: str) -> Fingerprint | None:
        return self.main.get((language, name))


def load_second_s(path: Path = AUDIO_RULINGS_PATH) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return set(payload["second_s"]["main_ids"])


def load_no_audio(path: Path = AUDIO_RULINGS_PATH) -> set[str]:
    """Sentences ruled to carry no recording at all ("Drop the audio")."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return set(payload["no_audio"]["main_ids"])


NO_AUDIO_OUTCOME = ("not published: maintainer ruling 2026-10-16 \"Drop the audio\" "
                    "(source_data/audio_rulings.json, no_audio)")


def _village_rank(village: str | None) -> int:
    return YAMI_VILLAGES.index(village) if village in YAMI_VILLAGES else len(YAMI_VILLAGES)


def choose(language: str, identifier: str, urls: list[str], village_of: dict[str, str | None],
           main_audio: list[dict[str, str]], table: AudioTable, second_s: set[str],
           log: list[dict[str, str]], no_audio: set[str] = frozenset()) -> list[Recording]:
    """The distinct recordings of one sentence, in publication order.

    `log` receives one row per recording left out (broken, unreachable,
    identical copy, main's recording replaced by a 2026 one, ruled out).
    A sentence in `no_audio` gets no recording from any source.
    """
    if identifier in no_audio:
        for url in urls:
            fp = table.recording(url)
            log.append({"s_id": identifier, "origin": "2026", "url": url,
                        "file": fp.file, "type": fp.type,
                        "village": village_of.get(url) or "", "outcome": NO_AUDIO_OUTCOME})
        for attributes in main_audio:
            log.append({"s_id": identifier, "origin": "main",
                        "url": attributes.get("url", ""), "file": attributes.get("file", ""),
                        "type": "", "outcome": NO_AUDIO_OUTCOME})
        return []
    working: list[Recording] = []
    for url in urls:
        fp = table.recording(url)
        if fp.type in BROKEN_TYPES or fp.type == UNREACHABLE:
            log.append({"s_id": identifier, "origin": "2026", "url": url,
                        "file": fp.file, "type": fp.type,
                        "village": village_of.get(url) or "",
                        "outcome": "dropped: broken" if fp.type in BROKEN_TYPES
                        else "dropped: unreachable"})
            continue
        if fp.type == "same-as-main":
            kind = "same-as-main"
        elif fp.type in EXTENSIONS:
            kind = fp.type
        else:
            raise ValueError(f"{url}: unexpected type {fp.type!r}")
        working.append(Recording("2026", fp.sha256, kind, url=url,
                                 village=village_of.get(url), source_file=fp.file))
    if language == "Yami":
        working.sort(key=lambda r: _village_rank(r.village))   # stable: source order otherwise

    mains: list[Recording] = []
    for attributes in main_audio:
        fp = table.main_file(language, attributes.get("file", ""))
        mains.append(Recording("main", fp.sha256 if fp else None, "",
                               attributes=dict(attributes)))
    working_shas = {r.sha256 for r in working}
    if urls and not working and mains:
        log.append({"s_id": identifier, "origin": "main", "url": "", "file": "",
                    "type": "", "outcome": "every 2026 recording dropped: main's "
                    "recording used instead"})
    if not working or identifier in second_s:
        kept_mains = mains
    else:
        kept_mains = [m for m in mains if m.sha256 is not None and m.sha256 in working_shas]
        for m in mains:
            if m not in kept_mains:
                log.append({"s_id": identifier, "origin": "main", "url": m.attributes.get("url", ""),
                            "file": m.attributes.get("file", ""), "type": "",
                            "outcome": "main's recording not used: the 2026 source has a different one"})

    chosen: list[Recording] = []
    seen: dict[str, Recording] = {}
    for item in [*kept_mains, *working]:
        if item.sha256 is not None and item.sha256 in seen:
            kept = seen[item.sha256]
            log.append({"s_id": identifier, "origin": item.origin,
                        "url": item.url or item.attributes.get("url", ""),
                        "file": item.source_file or item.attributes.get("file", ""),
                        "type": item.type, "village": item.village or "",
                        "outcome": "identical copy: kept once",
                        "same_as": kept.url or kept.attributes.get("file", ""),
                        "same_as_village": kept.village or ""})
            continue
        if item.sha256 is not None:
            seen[item.sha256] = item
        chosen.append(item)
    return chosen


def audio_elements(language: str, identifier: str, chosen: list[Recording],
                   table: AudioTable) -> list[dict[str, str]]:
    """AUDIO attributes, in order; the k-th goes on split_id(identifier, k)."""
    out: list[dict[str, str]] = []
    per_village: dict[str, int] = {}
    for offset, item in enumerate(chosen):
        if item.origin == "main":
            out.append(dict(item.attributes))
            continue
        if item.type == "same-as-main":
            fp = table.recording(item.url)
            source = table.main_file(language, fp.main_file)
            raise ValueError(
                f"{identifier}: 2026 recording {item.url} is a copy of main's "
                f"{fp.main_file} (not downloaded, type unknown) but that file is "
                f"not this sentence's recording ({source})")
        extension = EXTENSIONS[item.type]
        if language == "Yami" and item.village:
            # NOT RULED (2026-10-17): a sentence can carry two different
            # recordings from the same village (the source lists it under two
            # headwords with different files). The ruled name
            # <id>_<village>.<ext> would then repeat; the second takes _2.
            per_village[item.village] = per_village.get(item.village, 0) + 1
            count = per_village[item.village]
            suffix = "" if count == 1 else f"_{count}"
            name = f"{identifier}_{item.village}{suffix}.{extension}"
        else:
            name = f"{split_id(identifier, offset)}.{extension}"
        out.append({"url": item.url, "file": name})
    return out

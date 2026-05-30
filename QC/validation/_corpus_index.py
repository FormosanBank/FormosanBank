"""CorpusIndex: the cross-file accumulator built in pass 1.

The validator runner makes one parse pass over every file in the
target, collecting per-file structured data into a CorpusIndex.
Pass 2 then applies cross-file rules (V081 id uniqueness, …) with
the populated index as their third argument.

Fields:
  ids: TEXT/@id -> list of (path, location-str). location-str is the
       in-file pinpoint (currently always "TEXT" for the root, but
       reserved for future per-W/per-M ids if those ever participate
       in cross-file uniqueness).
  langs: path -> resolved xml:lang for that file's <TEXT> root.
"""
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CorpusIndex:
    ids: dict[str, list[tuple[Path, str]]]
    langs: dict[Path, str]

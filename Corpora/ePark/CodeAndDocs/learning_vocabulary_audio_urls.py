#!/usr/bin/env python3
"""Normalize and migrate ePark learning-vocabulary audio URLs.

The received ``ePark_2/學習詞表`` CSV files preserve the source URLs as they
were delivered. In 2026 the former route stopped serving these assets, while
the current vocabulary app serves the same files from::

    https://ilrdc.tw/tow/2022/audio/word/34/07_27.wav

to::

    https://web.klokah.tw/vocabulary/audio/word/34/07-27.wav

The builder imports :func:`normalize_audio_url` so regenerated XML uses the
current route without rewriting the historical CSV snapshot. This module is
also the committed, reproducible migration for the already-published XML
(POL-030 and POL-038).
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from lxml import etree


LEGACY_PREFIX = "https://ilrdc.tw/tow/2022/audio/word/"
CURRENT_PREFIX = "https://web.klokah.tw/vocabulary/audio/word/"

_LEGACY_URL = re.compile(
    rf"^{re.escape(LEGACY_PREFIX)}"
    r"(?P<dialect>[0-9]{1,2})/"
    r"(?P<category>[0-9]{2})_(?P<item>[0-9]{2,3})\.wav$"
)
_CURRENT_URL = re.compile(
    rf"^{re.escape(CURRENT_PREFIX)}"
    r"(?P<dialect>[0-9]{1,2})/"
    r"(?P<category>[0-9]{2})-(?P<item>[0-9]{2,3})\.wav$"
)

DEFAULT_XML_ROOT = (
    Path(__file__).resolve().parents[1]
    / "XML"
    / "xue_xi_ci_biao_learning_vocabulary"
)


@dataclass(frozen=True)
class FileReport:
    """Counts observed while checking or migrating one XML file."""

    audio_elements: int
    legacy_urls: int
    current_urls: int


def normalize_audio_url(url: str) -> str:
    """Return the current Klokah URL for a retired vocabulary-audio URL.

    URLs for other ePark collections are returned unchanged. A URL under
    either vocabulary namespace must match its known shape so a new upstream
    change cannot silently produce another broken link.
    """

    legacy = _LEGACY_URL.fullmatch(url)
    if legacy:
        return (
            f"{CURRENT_PREFIX}{legacy['dialect']}/"
            f"{legacy['category']}-{legacy['item']}.wav"
        )

    if _CURRENT_URL.fullmatch(url):
        return url

    if url.startswith((LEGACY_PREFIX, CURRENT_PREFIX)):
        raise ValueError(f"Unexpected ePark learning-vocabulary audio URL: {url}")

    return url


def process_xml_file(path: Path, *, apply_changes: bool) -> FileReport:
    """Check one published XML file and optionally migrate its URL attributes."""

    tree = etree.parse(str(path))
    audio_elements = list(tree.getroot().iter("AUDIO"))
    legacy_urls = 0
    current_urls = 0

    for audio in audio_elements:
        url = audio.get("url")
        if not url:
            raise ValueError(f"AUDIO element without a URL in {path}")

        normalized = normalize_audio_url(url)
        if normalized != url:
            legacy_urls += 1
            if apply_changes:
                audio.set("url", normalized)
        elif _CURRENT_URL.fullmatch(url):
            current_urls += 1
        else:
            raise ValueError(f"Unexpected AUDIO URL in {path}: {url}")

    if legacy_urls and apply_changes:
        # Match the existing ePark lxml pipeline so only URL attributes change.
        tree.write(
            str(path),
            xml_declaration=True,
            pretty_print=True,
            encoding="utf-8",
        )

    return FileReport(
        audio_elements=len(audio_elements),
        legacy_urls=legacy_urls,
        current_urls=current_urls,
    )


def process_xml_root(xml_root: Path, *, apply_changes: bool) -> FileReport:
    """Check or migrate every XML file below the learning-vocabulary root."""

    xml_files = sorted(xml_root.rglob("*.xml"))
    if not xml_files:
        raise ValueError(f"No XML files found under {xml_root}")

    # Validate the complete inventory before writing any file. This prevents a
    # newly introduced URL shape from leaving a partially migrated directory.
    reports = [
        process_xml_file(path, apply_changes=False) for path in xml_files
    ]
    if apply_changes:
        for path in xml_files:
            process_xml_file(path, apply_changes=True)
    return FileReport(
        audio_elements=sum(report.audio_elements for report in reports),
        legacy_urls=sum(report.legacy_urls for report in reports),
        current_urls=sum(report.current_urls for report in reports),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate retired ePark learning-vocabulary AUDIO URLs."
    )
    parser.add_argument(
        "--xml-root",
        type=Path,
        default=DEFAULT_XML_ROOT,
        help=f"XML directory to scan (default: {DEFAULT_XML_ROOT})",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Write normalized URLs in place.",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="Fail if any retired URL remains.",
    )
    args = parser.parse_args()

    try:
        report = process_xml_root(args.xml_root, apply_changes=args.apply)
    except (OSError, ValueError, etree.XMLSyntaxError) as exc:
        parser.exit(1, f"error: {exc}\n")

    print(f"AUDIO elements: {report.audio_elements}")
    print(f"Current URLs: {report.current_urls}")
    print(f"Retired URLs: {report.legacy_urls}")

    if args.apply:
        print(f"Updated URLs: {report.legacy_urls}")
    elif report.legacy_urls:
        print("Dry run only. Re-run with --apply to migrate these URLs.")

    if args.check and report.legacy_urls:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

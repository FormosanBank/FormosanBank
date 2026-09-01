#!/usr/bin/env python3
"""Fetch the SEALS 33 national-languages page into a structured snapshot."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag


SOURCE_URL = "https://sites.google.com/view/seals33/national-languages?authuser=0"
CODEDOCS_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = CODEDOCS_ROOT / "data" / "source_snapshot.json"
USER_AGENT = "FormosanBank-SEALS33-source-audit/1.0"


class SourceStructureError(RuntimeError):
    """Raised when the live page no longer has the audited structure."""


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value.replace("\xa0", " "))
    return re.sub(r"\s+", " ", value).strip()


def node_text(node: Tag) -> str:
    return normalize_text(node.get_text("", strip=False))


def node_strings(node: Tag) -> list[str]:
    return [normalize_text(value) for value in node.stripped_strings]


def content_blocks(soup: BeautifulSoup) -> list[Tag]:
    return [
        block
        for block in soup.select("div.tyJCtd")
        if normalize_text(block.get_text("", strip=False))
    ]


def find_block(blocks: list[Tag], *needles: str) -> Tag:
    matches = []
    for block in blocks:
        text = normalize_text(block.get_text("", strip=False))
        if all(needle in text for needle in needles):
            matches.append(block)
    if len(matches) != 1:
        raise SourceStructureError(
            f"expected one content block for {needles!r}; found {len(matches)}"
        )
    return matches[0]


def paragraphs(block: Tag) -> list[Tag]:
    return [node for node in block.find_all("p") if node_text(node)]


def heading(block: Tag) -> Tag:
    node = block.find(["h1", "h2", "h3"])
    if node is None:
        raise SourceStructureError("expected heading in source block")
    return node


def split_parallel(node: Tag) -> tuple[str, str]:
    parts = node_strings(node)
    if len(parts) != 2:
        raise SourceStructureError(
            f"expected English and Mandarin strings; found {parts!r}"
        )
    return parts[0], parts[1]


def make_row(
    source_row: int,
    *,
    zho: str,
    xsy: str,
    trv: str,
    eng: str | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "source_row": source_row,
        "zho": normalize_text(zho),
        "xsy": normalize_text(xsy),
        "trv": normalize_text(trv),
    }
    if eng is not None:
        row["eng"] = normalize_text(eng)
    if not all(row.get(key) for key in ("zho", "xsy", "trv")):
        raise SourceStructureError(f"source row {source_row} has a blank field")
    return row


def parse_page(html: str) -> tuple[list[dict[str, Any]], list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    blocks = content_blocks(soup)

    b1 = find_block(blocks, "國家語言專區", "Patis sskari kari qnlhangan")
    b2 = find_block(blocks, "第三十三屆東南亞語言學學會年會", "Tg33 Pprngagan")
    b3 = find_block(blocks, "2024 年 6 月 15 日", "Kndalax")
    b4 = find_block(blocks, "集思台大會議中心", "Pssliyan:")
    b5 = find_block(blocks, "簡介", "Pgklaan")
    b6 = find_block(blocks, "東南亞是一個語言多樣性", "Austroasiatic")
    b7 = find_block(blocks, "1990年", "Knkawas 1990")
    b8 = find_block(blocks, "kapanpanabih", "Yencumin Taywang")
    b9 = find_block(blocks, "20個國家", "Seediq mptuumal")
    b10 = find_block(blocks, "113年6月15日", "Tg1")
    b11 = find_block(blocks, "What word class are negators", "Book Launch")
    b15 = find_block(blocks, "113年6月16日", "Tg2")
    b16 = find_block(blocks, "Prosodic realization", "Word stress in Yami")
    b23 = find_block(blocks, "113年6月17日", "Tg3")
    b24 = find_block(blocks, "Reconstructing antepenultimate", "Cliticization")
    b29 = find_block(blocks, "指導單位", "kamatortoroe")

    rows: list[dict[str, Any]] = []

    parts = node_strings(heading(b1))
    if len(parts) != 6:
        raise SourceStructureError(f"unexpected row 1 heading: {parts!r}")
    rows.append(
        make_row(
            1,
            zho=parts[0],
            xsy=f"{parts[1]} {''.join(parts[2:5])}",
            trv=parts[5],
        )
    )

    parts = node_strings(heading(b2))
    if len(parts) != 3:
        raise SourceStructureError(f"unexpected row 2 heading: {parts!r}")
    rows.append(make_row(2, zho=parts[0], xsy=parts[1], trv=parts[2]))

    parts = paragraphs(b3)
    if len(parts) != 5:
        raise SourceStructureError("unexpected date block")
    rows.append(
        make_row(
            3,
            zho=node_text(parts[0]),
            xsy=f"{node_text(parts[1])} {node_text(parts[2])}",
            trv=f"{node_text(parts[3])} {node_text(parts[4])}",
        )
    )

    parts = paragraphs(b4)
    if len(parts) != 3:
        raise SourceStructureError("unexpected location block")
    rows.append(
        make_row(4, zho=node_text(parts[0]), xsy=node_text(parts[1]), trv=node_text(parts[2]))
    )

    parts = node_strings(heading(b5))
    if len(parts) != 3:
        raise SourceStructureError(f"unexpected row 5 heading: {parts!r}")
    rows.append(make_row(5, zho=parts[0], xsy=parts[1], trv=parts[2]))

    parts = paragraphs(b6)
    if len(parts) != 3:
        raise SourceStructureError("unexpected introduction block")
    rows.append(
        make_row(6, zho=node_text(parts[0]), xsy=node_text(parts[1]), trv=node_text(parts[2]))
    )

    parts = paragraphs(b7)
    if len(parts) != 3:
        raise SourceStructureError("unexpected history block")
    rows.append(
        make_row(7, zho=node_text(parts[0]), xsy=node_text(parts[1]), trv=node_text(parts[2]))
    )

    parts = node_strings(heading(b8))
    if len(parts) != 12:
        raise SourceStructureError(f"unexpected row 8 heading: {parts!r}")
    rows.append(
        make_row(
            8,
            zho="".join(parts[:5]),
            xsy=f"{' '.join(parts[5:8])} {parts[8]}{parts[9]}",
            trv=f"{parts[10]} {parts[11]}",
        )
    )

    parts = paragraphs(b9)
    if len(parts) != 6:
        raise SourceStructureError("unexpected conference-summary block")
    rows.append(
        make_row(
            9,
            zho=f"{node_text(parts[0])} {node_text(parts[1])}",
            xsy=f"{node_text(parts[2])} {node_text(parts[3])}",
            trv=f"{node_text(parts[4])} {node_text(parts[5])}",
        )
    )

    def add_day_heading(source_row: int, block: Tag) -> None:
        day_parts = paragraphs(block)
        if len(day_parts) != 3:
            raise SourceStructureError(f"unexpected day heading for row {source_row}")
        rows.append(
            make_row(
                source_row,
                zho=node_text(day_parts[0]),
                xsy=node_text(day_parts[1]),
                trv=node_text(day_parts[2]),
            )
        )

    add_day_heading(10, b10)

    parts = paragraphs(b11)
    if len(parts) != 17:
        raise SourceStructureError("unexpected first-day program block")
    eng, zho = split_parallel(parts[1])
    rows.append(make_row(11, eng=eng, zho=zho, xsy=node_text(parts[2]), trv=node_text(parts[3])))
    eng, zho = split_parallel(parts[5])
    rows.append(make_row(12, eng=eng, zho=zho, xsy=node_text(parts[6]), trv=node_text(parts[7])))
    eng, zho = split_parallel(parts[9])
    rows.append(make_row(13, eng=eng, zho=zho, xsy=node_text(parts[10]), trv=node_text(parts[11])))
    rows.append(
        make_row(
            14,
            eng=node_text(parts[12]),
            zho=node_text(parts[13]),
            xsy=node_text(parts[14]),
            trv=node_text(parts[15]),
        )
    )
    excluded_presenters = [
        node_text(parts[0]),
        node_text(parts[4]),
        node_text(parts[8]),
        node_text(parts[16]),
    ]

    add_day_heading(15, b15)
    parts = paragraphs(b16)
    if len(parts) != 35:
        raise SourceStructureError("unexpected second-day program block")
    for offset in range(7):
        base = offset * 5
        rows.append(
            make_row(
                16 + offset,
                eng=node_text(parts[base + 1]),
                zho=node_text(parts[base + 2]),
                xsy=node_text(parts[base + 3]),
                trv=node_text(parts[base + 4]),
            )
        )
        excluded_presenters.append(node_text(parts[base]))

    add_day_heading(23, b23)
    parts = paragraphs(b24)
    if len(parts) != 25:
        raise SourceStructureError("unexpected third-day program block")
    for offset in range(5):
        base = offset * 5
        rows.append(
            make_row(
                24 + offset,
                eng=node_text(parts[base + 1]),
                zho=node_text(parts[base + 2]),
                xsy=node_text(parts[base + 3]),
                trv=node_text(parts[base + 4]),
            )
        )
        excluded_presenters.append(node_text(parts[base]))

    parts = node_strings(paragraphs(b29)[0])
    if len(parts) != 4:
        raise SourceStructureError(f"unexpected row 29 footer: {parts!r}")
    rows.append(make_row(29, zho=parts[0], xsy=parts[1], trv=f"{parts[2]} {parts[3]}"))

    expected_ids = list(range(1, 30))
    actual_ids = [row["source_row"] for row in rows]
    if actual_ids != expected_ids:
        raise SourceStructureError(f"unexpected source-row sequence: {actual_ids}")
    if sum("eng" in row for row in rows) != 16:
        raise SourceStructureError("expected 16 English program-title translations")
    if len(excluded_presenters) != 16:
        raise SourceStructureError("expected 16 excluded presenter blocks")
    return rows, excluded_presenters


def fetch_source() -> str:
    response = requests.get(
        SOURCE_URL,
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    return response.text


def rows_digest(rows: list[dict[str, Any]]) -> str:
    payload = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def make_snapshot(html: str) -> dict[str, Any]:
    rows, presenters = parse_page(html)
    return {
        "schema_version": 1,
        "source_url": SOURCE_URL,
        "retrieved_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "rows_sha256": rows_digest(rows),
        "rows": rows,
        "excluded_presenter_blocks": presenters,
        "excluded_non_corpus_sections": [
            "navigation and page controls",
            "language legend",
            "presenter names and affiliations",
            "organizer list",
            "contact address",
            "site footer and copyright notice",
        ],
    }


def serialized(snapshot: dict[str, Any]) -> str:
    return json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare live structured rows with the committed snapshot",
    )
    args = parser.parse_args()

    live = make_snapshot(fetch_source())
    if args.check:
        committed = json.loads(args.output.read_text(encoding="utf-8"))
        comparable_keys = ("rows", "excluded_presenter_blocks", "excluded_non_corpus_sections")
        before = {key: committed[key] for key in comparable_keys}
        after = {key: live[key] for key in comparable_keys}
        if before != after:
            diff = difflib.unified_diff(
                serialized(before).splitlines(),
                serialized(after).splitlines(),
                fromfile="committed snapshot",
                tofile="live source",
                lineterm="",
            )
            print("\n".join(diff))
            return 1
        print(f"live source matches {len(live['rows'])} committed rows")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(serialized(live), encoding="utf-8")
    print(f"wrote {len(live['rows'])} rows to {args.output}")
    print(f"rows sha256: {live['rows_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

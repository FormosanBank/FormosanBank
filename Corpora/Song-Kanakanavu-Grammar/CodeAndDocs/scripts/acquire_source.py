#!/usr/bin/env python3
"""Acquire the complete official Alilin page-image book and text reference."""

from __future__ import annotations

import argparse
import html
import json
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from lxml import etree
from PIL import Image


BASE_URL = "https://alilin.cip.gov.tw/ebook/5949734115b6abe6caf971"
EXPECTED_PAGES = 268


def fetch(url: str) -> bytes:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.content


def page_assets(page: int, directory: Path) -> tuple[int, Path, list[dict[str, object]]]:
    image_path = directory / f"{page:03d}.jpg"
    image_path.write_bytes(fetch(f"{BASE_URL}/books/images/2/{page}.jpg"))
    xml = etree.fromstring(fetch(f"{BASE_URL}/iPhone/text/{page}.xml"))
    text_rows = []
    for node in xml.findall(".//TS"):
        text_rows.append(
            {
                "x": int(node.get("X", "0")),
                "y": int(node.get("Y", "0")),
                "w": int(node.get("W", "0")),
                "h": int(node.get("H", "0")),
                "text": html.unescape("".join(node.itertext())),
            }
        )
    return page, image_path, text_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--text-jsonl", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()

    manifest = etree.fromstring(fetch(f"{BASE_URL}/iPhone/ibook.xml"))
    total = int(manifest.findtext("total", "0"))
    if total != EXPECTED_PAGES:
        raise ValueError(f"Expected {EXPECTED_PAGES} pages, found {total}")

    with tempfile.TemporaryDirectory(prefix="kanakanavu-source-") as temp:
        directory = Path(temp)
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            assets = list(pool.map(lambda page: page_assets(page, directory), range(1, total + 1)))
        assets.sort()

        images = [Image.open(path).convert("RGB") for _, path, _ in assets]
        args.pdf.parent.mkdir(parents=True, exist_ok=True)
        images[0].save(args.pdf, save_all=True, append_images=images[1:], resolution=150.0)
        for image in images:
            image.close()

        args.text_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with args.text_jsonl.open("w", encoding="utf-8") as handle:
            for page, _, rows in assets:
                handle.write(json.dumps({"page": page, "rows": rows}, ensure_ascii=False) + "\n")

    print(f"Acquired {total} official page images and text XML layers.")


if __name__ == "__main__":
    main()

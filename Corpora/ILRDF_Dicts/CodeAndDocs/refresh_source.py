#!/usr/bin/env python3
"""Refresh committed ILRDF API snapshots without pickle or PDF caches.

This is an explicit network maintenance command, not part of reproduction.
Every headword query must succeed before a language snapshot is replaced.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import random
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ilrdf_source import LANGUAGES


BASE = Path(__file__).resolve().parent
SOURCE_DATA = BASE / "source_data"
API_BASE = "https://e-dictionary.ilrdf.org.tw"
SYMBOL_URL = f"{API_BASE}/api/app/dictionary/get-symbol"
LIST_URL = f"{API_BASE}/api/app/dictionary/get-list-by-symbol"
SEARCH_URL = f"{API_BASE}/api/app/dictionary/search-aPI"
TRIBE_CODES = {
    "Amis": "2", "Atayal": "6", "Paiwan": "24", "Bunun": "22",
    "Puyuma": "38", "Rukai": "28", "Tsou": "35", "Saisiyat": "13",
    "Yami": "42", "Thao": "14", "Kavalan": "34", "Truku": "33",
    "Sakizaya": "43", "Seediq": "16", "Saaroa": "37", "Kanakanavu": "36",
}
TRIBE_IDS = {
    "Amis": "e68273b9-1f2b-4c42-8d95-f52189ab24b7",
    "Atayal": "fc76ed97-0dd8-4587-82ad-7a6dbe125001",
    "Paiwan": "19c77a3b-3a81-496f-b0f4-afe6d9155edd",
    "Bunun": "865a96e3-3384-45b3-8bd0-e1f799b75515",
    "Puyuma": "2b339669-0e2f-4466-a9ab-5ff94ada152c",
    "Rukai": "4d9deb77-0d3d-4dfc-b254-332366c05822",
    "Tsou": "96466fa9-2d4c-468e-a5bf-cc09f3ffd9b8",
    "Saisiyat": "6e1dd000-c02c-444f-a3bc-dc7b964c7063",
    "Yami": "8273d01c-43b8-484c-8b41-b622b569cfb6",
    "Thao": "0105ce5e-00ea-4155-80c9-a8360e69ad11",
    "Kavalan": "c5974f37-b49d-466a-ab24-6893ab4ef6a5",
    "Truku": "5de0d885-90c6-4440-a095-8dc69cf87764",
    "Sakizaya": "8c6fdba1-a241-47ec-9c5f-ad7e79a80d2e",
    "Seediq": "886cbf63-07e4-4d25-8266-5dd3e9174cfc",
    "Saaroa": "8d663fca-4770-4507-961b-fc6a1b9b8e03",
    "Kanakanavu": "80269ed5-9298-4aaa-8cef-a51960151e26",
}


def post_json(url: str, payload: dict[str, Any], retries: int = 4) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "FormosanBank-source-refresh/1"},
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urlopen(request, timeout=45) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}")
                value = json.loads(response.read())
                if not isinstance(value, dict):
                    raise ValueError("API response is not an object")
                return value
        except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError) as error:
            last_error = error
            if attempt + 1 < retries:
                time.sleep((2**attempt) + random.random() / 4)
    raise RuntimeError(f"request failed after {retries} attempts: {last_error}")


def enumerate_headwords(language: str) -> list[str]:
    tribe_id = TRIBE_IDS[language]
    symbols = post_json(SYMBOL_URL, {"tribeId": tribe_id})["data"]["items"]
    names: set[str] = set()
    for symbol in symbols:
        symbol_id = symbol.get("id")
        if not symbol_id:
            continue
        response = post_json(LIST_URL, {"tribeId": tribe_id, "symbolId": symbol_id})
        for item in response.get("data", {}).get("wordItems", []):
            name = item.get("name")
            if isinstance(name, str):
                names.add(name)
    if not names:
        raise RuntimeError(f"{language}: symbol enumeration returned no headwords")
    return sorted(names)


def fetch_headword(language: str, query: str) -> list[dict[str, Any]]:
    response = post_json(
        SEARCH_URL,
        {
            "format": 2,
            "tribesCode": TRIBE_CODES[language],
            "keyword": query,
            "page": 1,
            "pageSize": 1000,
        },
    )
    words = response.get("word")
    if not isinstance(words, list):
        raise ValueError(f"{language} {query!r}: search response has no word list")
    return words


def capture_language(language: str, workers: int, retrieved_on: str) -> dict[str, Any]:
    headwords = enumerate_headwords(language)
    responses: dict[str, list[dict[str, Any]]] = {}
    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(fetch_headword, language, query): query for query in headwords
        }
        completed = 0
        for future in as_completed(futures):
            query = futures[future]
            try:
                responses[query] = future.result()
            except Exception as error:  # Preserve each failed query for the abort report.
                failures.append(f"{query!r}: {error}")
            completed += 1
            if completed % 500 == 0 or completed == len(headwords):
                print(f"{language}: {completed}/{len(headwords)} queries")
    if failures:
        preview = "\n".join(failures[:20])
        raise RuntimeError(f"{language}: {len(failures)} failed queries; snapshot unchanged\n{preview}")
    return {
        "language": language,
        "responses": [
            {"query": query, "words": responses[query]} for query in sorted(responses)
        ],
        "retrieved_on": retrieved_on,
        "schema_version": 2,
        "snapshot_origin": "live ILRDF API",
    }


def deterministic_json(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def deterministic_gzip(raw: bytes) -> bytes:
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, compresslevel=9, mtime=0) as handle:
        handle.write(raw)
    return buffer.getvalue()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def refresh(language_names: list[str], workers: int, retrieved_on: str) -> None:
    manifest_path = SOURCE_DATA / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = {item["language"]: item for item in manifest["languages"]}
    for language in language_names:
        payload = capture_language(language, workers, retrieved_on)
        raw = deterministic_json(payload)
        compressed = deterministic_gzip(raw)
        snapshot_path = SOURCE_DATA / "snapshots" / f"{language}.json.gz"
        atomic_write(snapshot_path, compressed)
        entries[language] = {
            "file": f"snapshots/{language}.json.gz",
            "language": language,
            "queries": len(payload["responses"]),
            "retrieved_on": retrieved_on,
            "sha256": hashlib.sha256(compressed).hexdigest(),
            "uncompressed_sha256": hashlib.sha256(raw).hexdigest(),
        }
        print(f"{language}: snapshot prepared with zero query failures")
    manifest["languages"] = [entries[language] for language in LANGUAGES]
    manifest["last_refresh_date"] = retrieved_on
    manifest["schema_version"] = 2
    atomic_write(manifest_path, deterministic_json(manifest))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", action="append", choices=tuple(LANGUAGES))
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--date", default=date.today().isoformat(), dest="retrieved_on")
    args = parser.parse_args()
    if not 1 <= args.workers <= 32:
        parser.error("--workers must be between 1 and 32")
    refresh(args.language or list(LANGUAGES), args.workers, args.retrieved_on)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

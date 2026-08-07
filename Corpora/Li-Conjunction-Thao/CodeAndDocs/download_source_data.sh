#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANU_DIR="$ROOT_DIR/Private/source/anu"
LOG_DIR="$ROOT_DIR/logs"

mkdir -p "$ANU_DIR" "$LOG_DIR" "$ROOT_DIR/intermediate"

curl -L --fail --output "$ANU_DIR/openresearch_item.html" \
  "https://openresearch-repository.anu.edu.au/items/8bfb8bf0-2f58-4eae-947c-bf9af50faf9f"

curl -L --fail --output "$ANU_DIR/openresearch_item_api.json" \
  "https://openresearch-repository.anu.edu.au/server/api/core/items/8bfb8bf0-2f58-4eae-947c-bf9af50faf9f"

curl -L --fail --output "$ANU_DIR/openresearch_bundles_api.json" \
  "https://openresearch-repository.anu.edu.au/server/api/core/items/8bfb8bf0-2f58-4eae-947c-bf9af50faf9f/bundles?size=9999"

curl -L --fail --output "$ANU_DIR/openresearch_original_bitstreams_api.json" \
  "https://openresearch-repository.anu.edu.au/server/api/core/bundles/6e5f8f35-e109-481d-84aa-54029c0f690a/bitstreams"

curl -L --fail --output "$ANU_DIR/openresearch_text_bitstreams_api.json" \
  "https://openresearch-repository.anu.edu.au/server/api/core/bundles/351928d4-2772-46fe-b671-5cd26992f6a9/bitstreams"

curl -L --fail --output "$ANU_DIR/Papers from 12-ICAL, Volume 2.pdf" \
  "https://openresearch-repository.anu.edu.au/server/api/core/bitstreams/03580672-2578-4cda-b6fd-782515304d30/content"

curl -L --fail --output "$ANU_DIR/Papers from 12-ICAL, Volume 2.pdf.txt" \
  "https://openresearch-repository.anu.edu.au/server/api/core/bitstreams/b909810a-eb5e-44c9-bfb9-bd7688a7e9e5/content"

find "$ROOT_DIR/Private/source/anu" -maxdepth 1 -type f -print0 | sort -z | xargs -0 file > "$LOG_DIR/source_file_types.txt"
find "$ROOT_DIR/Private/source/anu" -maxdepth 1 -type f -print0 | sort -z | xargs -0 shasum -a 256 > "$LOG_DIR/source_sha256.txt"
find "$ROOT_DIR/Private/source/anu" -maxdepth 1 -type f -print0 | sort -z | xargs -0 wc -c > "$LOG_DIR/source_size_bytes.txt"

if command -v pdfinfo >/dev/null 2>&1; then
  pdfinfo "$ANU_DIR/Papers from 12-ICAL, Volume 2.pdf" > "$LOG_DIR/anu_pdfinfo.txt"
fi

if command -v pdftotext >/dev/null 2>&1; then
  pdftotext -f 394 -l 402 -layout "$ANU_DIR/Papers from 12-ICAL, Volume 2.pdf" \
    "$ROOT_DIR/intermediate/article_pages_394_402_layout.txt"
  pdftotext -f 394 -l 402 "$ANU_DIR/Papers from 12-ICAL, Volume 2.pdf" \
    "$ROOT_DIR/intermediate/article_pages_394_402_plain.txt"
fi

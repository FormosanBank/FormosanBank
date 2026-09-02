#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
DEST_DIR="$ROOT/Private/source"
SCAN="$DEST_DIR/akiw_2012_sakizaya_affixes_scan.pdf"
OCR="$DEST_DIR/akiw_2012_sakizaya_affixes_acrobat_ocr.pdf"
SCAN_URL='https://storage.app.basecamp.com/3340659/blobs/f831b4fa-58ee-11f1-b147-0242ac120003/download/The%20study%20of%20affixes%20in%20Sakizaya.pdf'
OCR_URL='https://storage.app.basecamp.com/3340659/blobs/c2d7cf14-6498-11f1-835f-0242ac120003/download/paper2.pdf'
SCAN_SHA=fab787faf0e32cd087ba3dc222734132ad4213ca0804b8d5b32a318e66fbbbee
OCR_SHA=6b33e4d3a2a81b309d748a0dfbcb700160beb976916add3fde234e70b903d712

mkdir -p "$DEST_DIR"
if [[ -n "${SOURCE_DIR:-}" ]]; then
  cp "$SOURCE_DIR/akiw_2012_sakizaya_affixes_scan.pdf" "$SCAN"
  cp "$SOURCE_DIR/akiw_2012_sakizaya_affixes_acrobat_ocr.pdf" "$OCR"
elif [[ ! -f "$SCAN" || ! -f "$OCR" ]]; then
  command -v basecamp >/dev/null || { echo 'The authenticated Basecamp CLI is required.' >&2; exit 2; }
  TEMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/sakizaya-source.XXXXXX")
  trap 'rm -rf -- "$TEMP_DIR"' EXIT
  basecamp files download "$SCAN_URL" --out "$TEMP_DIR"
  basecamp files download "$OCR_URL" --out "$TEMP_DIR"
  mv "$TEMP_DIR/The study of affixes in Sakizaya.pdf" "$SCAN"
  mv "$TEMP_DIR/paper2.pdf" "$OCR"
fi

[[ "$(wc -c < "$SCAN" | tr -d ' ')" == 80792946 ]] || { echo 'Scan byte-count mismatch' >&2; exit 1; }
[[ "$(shasum -a 256 "$SCAN" | awk '{print $1}')" == "$SCAN_SHA" ]] || { echo 'Scan checksum mismatch' >&2; exit 1; }
[[ "$(wc -c < "$OCR" | tr -d ' ')" == 69142227 ]] || { echo 'OCR byte-count mismatch' >&2; exit 1; }
[[ "$(shasum -a 256 "$OCR" | awk '{print $1}')" == "$OCR_SHA" ]] || { echo 'OCR checksum mismatch' >&2; exit 1; }
printf 'sources_verified=%s\n' "$DEST_DIR"

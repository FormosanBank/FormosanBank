#!/usr/bin/env bash
set -euo pipefail

CODE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON:-python3}"
MANIFEST="$CODE_ROOT/data/source_manifest.json"
DEST_DIR="$CODE_ROOT/Private/source"

manifest_value() {
  "$PYTHON_BIN" -c "import json; print(json.load(open('$MANIFEST'))['$1'])"
}

URL="$(manifest_value url)"
FILENAME="$(manifest_value filename)"
EXPECTED_SHA256="$(manifest_value sha256)"
EXPECTED_BYTES="$(manifest_value bytes)"
EXPECTED_PAGES="$(manifest_value pages)"
DEST="$DEST_DIR/$FILENAME"

mkdir -p "$DEST_DIR"
TEMP_FILE="$(mktemp "$DEST_DIR/.source.XXXXXX")"
trap 'rm -f "$TEMP_FILE"' EXIT

curl --fail --location --output "$TEMP_FILE" "$URL"
ACTUAL_SHA256="$(shasum -a 256 "$TEMP_FILE" | cut -d' ' -f1)"
ACTUAL_BYTES="$(wc -c < "$TEMP_FILE" | tr -d ' ')"
ACTUAL_PAGES="$(pdfinfo "$TEMP_FILE" | awk '/^Pages:/ {print $2}')"

if [[ "$ACTUAL_SHA256" != "$EXPECTED_SHA256" ]]; then
  echo "Source SHA-256 mismatch" >&2
  exit 1
fi
if [[ "$ACTUAL_BYTES" != "$EXPECTED_BYTES" ]]; then
  echo "Source byte-count mismatch" >&2
  exit 1
fi
if [[ "$ACTUAL_PAGES" != "$EXPECTED_PAGES" ]]; then
  echo "Source page-count mismatch" >&2
  exit 1
fi

mv "$TEMP_FILE" "$DEST"
trap - EXIT
echo "Downloaded and verified $DEST"

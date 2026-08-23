#!/usr/bin/env bash
# Rebuild Nowbucyang-Truku-Thesis from its reviewed public source-tier snapshot.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPUS_DIR="$(dirname "$SCRIPT_DIR")"
BANK_ROOT="${1:-$(cd "$CORPUS_DIR/../.." && pwd)}"
SNAPSHOT_DIR="$SCRIPT_DIR/source_snapshot"
OUTPUT_XML="$CORPUS_DIR/XML/Truku/Hsu_Lowking_Truku_WordFormation_2008.xml"

if [ -z "${PYTHON:-}" ]; then
    PYTHON="$BANK_ROOT/.venv/bin/python"
    if [ ! -x "$PYTHON" ]; then
        PYTHON="python3"
    fi
fi

if [ ! -f "$SNAPSHOT_DIR/Truku/Hsu_Lowking_Truku_WordFormation_2008.xml" ]; then
    echo "missing source-tier snapshot under $SNAPSHOT_DIR" >&2
    exit 1
fi

BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/nowbucyang-truku.XXXXXX")"
cleanup() {
    rm -rf "$BUILD_DIR"
}
trap cleanup EXIT

cp -R "$SNAPSHOT_DIR/." "$BUILD_DIR/"

"$PYTHON" "$BANK_ROOT/QC/cleaning/clean_xml.py" \
    --corpora_path "$BUILD_DIR"
"$PYTHON" "$BANK_ROOT/QC/utilities/standardize.py" \
    --tsv_path "$BANK_ROOT/Orthographies/ConversionTables/Seediq_94_113.tsv" \
    --target_column Truku \
    --corpora_path "$BUILD_DIR"
"$PYTHON" "$BANK_ROOT/QC/utilities/add_phonology.py" \
    --orthography Ortho94 \
    --target_column Truku \
    --corpora_path "$BUILD_DIR"

mkdir -p "$(dirname "$OUTPUT_XML")"
cp "$BUILD_DIR/Truku/Hsu_Lowking_Truku_WordFormation_2008.xml" "$OUTPUT_XML"

echo "rebuilt $OUTPUT_XML"

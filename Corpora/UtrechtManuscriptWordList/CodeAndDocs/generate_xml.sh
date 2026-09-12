#!/usr/bin/env bash
# POL-047 entry point: source -> published XML/. Build only; no validators.
set -euo pipefail

CODE_DOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPUS="$(dirname "$CODE_DOCS")"
PYTHON_BIN="${PYTHON:-python3}"

# POL-052: note the tools this run used, without depending on them.
HERE="$(git -C "$CODE_DOCS" rev-parse HEAD 2>/dev/null || echo unknown)"
RECORDED="$("$PYTHON_BIN" -c 'import json,sys;print(json.load(open(sys.argv[1]))["formosanbank_commit"])' \
  "$CODE_DOCS/provenance.json" 2>/dev/null || echo unknown)"
if [ "$HERE" != "$RECORDED" ]; then
  echo "note: building at $HERE; provenance.json records $RECORDED" >&2
fi

# Step 1 reads the committed pdftotext extraction, so the build needs no PDF
# and no poppler (POL-048). Pass --pdf to re-extract from the source instead.
"$PYTHON_BIN" "$CODE_DOCS/extract_source.py" --tsv "$CODE_DOCS/source/pdftotext.tsv"
"$PYTHON_BIN" "$CODE_DOCS/reconcile_predecessor.py"
"$PYTHON_BIN" "$CODE_DOCS/generate_xml.py"

# Steps 4 and 5 of the canonical pipeline -- standardize.py and add_phonology.py
# -- are deliberately absent; see "Reproducibility" in the corpus README.

BUILD_TMP="$(mktemp -d)"
trap 'rm -rf -- "$BUILD_TMP"' EXIT
"$PYTHON_BIN" "$CODE_DOCS/generate_xml.py" --output "$BUILD_TMP/Utrecht_Manuscript.xml"
cmp "$CORPUS/XML/Siraya/Utrecht_Manuscript.xml" "$BUILD_TMP/Utrecht_Manuscript.xml"
echo "Determinism check passed."

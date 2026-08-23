#!/usr/bin/env bash
set -euo pipefail

CODE_DOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPUS="$(dirname "$CODE_DOCS")"
PYTHON_BIN="${PYTHON:-python3}"

"$PYTHON_BIN" "$CODE_DOCS/extract_source.py"
"$PYTHON_BIN" "$CODE_DOCS/reconcile_predecessor.py"
"$PYTHON_BIN" "$CODE_DOCS/generate_xml.py"
"$PYTHON_BIN" "$CODE_DOCS/audit_source_alignment.py"

BUILD_TMP="$(mktemp -d)"
trap 'rm -rf -- "$BUILD_TMP"' EXIT
"$PYTHON_BIN" "$CODE_DOCS/generate_xml.py" --output "$BUILD_TMP/Utrecht_Manuscript.xml"
cmp "$CORPUS/XML/Siraya/Utrecht_Manuscript.xml" "$BUILD_TMP/Utrecht_Manuscript.xml"
echo "Determinism check passed."

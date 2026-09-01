#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPUS_DIR="$(dirname "$SCRIPT_DIR")"

if [ -z "${PYTHON:-}" ]; then
    PYTHON="python3"
fi

"$PYTHON" "$SCRIPT_DIR/build_lexical_xml.py"
"$PYTHON" "$SCRIPT_DIR/audit_source_coverage.py"

echo "Rebuilt and verified $CORPUS_DIR/XML"
